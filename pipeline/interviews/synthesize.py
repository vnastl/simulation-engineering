"""Synthesis (INTERVIEW playbook §5.2, §5.5, §7, §8).

Deterministic. Merges the three LLM passes into one reconciled record per unit,
then renders through the SAME ColumnToText the survey uses (so a prose code and a
survey code produce the same label, §7), plus the thematic-prose layer.

Inputs per unit:
  coding/checked/<u>.json   quote-checked codes (deterministic §5.1 already applied)
  coding/verify/<u>.adv.json   adversarial verdicts (drop/correct/downgrade)
  coding/verify/<u>.blind.json blind re-codes of low-confidence fields

Pass logic:
  * adversarial: verdict "unsupported" -> drop; "wrong_code" -> correct; apply
    any confidence downgrade.
  * blind second pass (§5.2): for a low-confidence field, agree (exact, or within
    one point on an ordinal Likert) -> promote to medium; disagree -> keep + flag
    alternative; blind found nothing -> keep low, flag. This measures
    reproducibility, NOT accuracy.
  * within-unit contradiction (§5.5): if >1 surviving code for a var, keep the
    higher-confidence / later one, record the runner-up in provenance; never average.
  * merge free metadata (gender=female, §3) as high-confidence, prose-free.

Outputs (outputs/interviews/):
  coding/final/<u>.json           reconciled record (machine artifact)
  personas_plain/<u>.txt          code-only persona, survey-comparable
  personas_enriched/<u>.md        + quote + confidence/verification per line
  thematic_prose/<u>.md           full verbatim answer per recurring-question theme
  coded_records.jsonl             all reconciled records
  reconciliation_vs_survey.json   elicitation-matched distribution comparison (§5.3)
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent / "survey"))
sys.path.insert(0, str(HERE))

from schema import load_columns, SECTION_ORDER, SEC_E, SECTION_TOPIC  # noqa: E402
import clean_data  # noqa: E402
from registry import THEMES, TIERS  # noqa: E402
from quote_check import canon, quote_in  # noqa: E402

OUT_TRANSCRIPTS = None  # set in build()

OUT = ROOT / "outputs/interviews"
CHK = OUT / "coding/checked"
VER = OUT / "coding/verify"
FIN = OUT / "coding/final"

CONF_RANK = {"low": 0, "medium": 1, "high": 2}


def _load(path):
    return json.loads(path.read_text()) if path.exists() else None


def _is_ordinal(col):
    return bool(col.scale_label)  # battery Likert items are ordinal


def reconcile_unit(unit, by_code):
    checked = _load(CHK / f"{unit}.json")
    if checked is None:
        return None
    adv = _load(VER / f"{unit}.adv.json") or {"verdicts": []}
    blind = _load(VER / f"{unit}.blind.json") or {"recodes": []}

    codes = checked.get("codes", [])
    verdicts = adv.get("verdicts", [])
    # align verdicts to codes by position, fallback by var
    by_pos = verdicts if len(verdicts) == len(codes) else None
    by_var_v = defaultdict(list)
    for v in verdicts:
        by_var_v[v.get("var")].append(v)

    fields = {}      # var -> reconciled field
    runners = defaultdict(list)
    for i, c in enumerate(codes):
        var = c["var"]
        v = by_pos[i] if by_pos else (by_var_v[var].pop(0) if by_var_v[var] else None)
        verdict = (v or {}).get("verdict", "supported")
        if verdict == "unsupported":
            continue
        code, label = c["code"], c.get("label")
        conf = c.get("confidence", "medium")
        if verdict == "wrong_code" and (v or {}).get("corrected_code") is not None:
            code = v["corrected_code"]
            label = v.get("corrected_label") or label
        if (v or {}).get("corrected_confidence"):
            conf = v["corrected_confidence"]
        field = {
            "var": var, "code": code, "label": label, "confidence": conf,
            "verification": "adversarial-" + verdict,
            "evidence": c.get("evidence_quote", ""),
            "evidence_role": c.get("evidence_role", "Subject"),
            "theme": c.get("theme", ""),
            "reasoning": c.get("reasoning", ""),
            "provenance": "prose-derived", "flags": [],
        }
        if var in fields:  # within-unit contradiction (§5.5)
            cur = fields[var]
            keep, drop = ((field, cur) if CONF_RANK.get(conf, 1) >= CONF_RANK.get(cur["confidence"], 1)
                          else (cur, field))
            runners[var].append({"code": drop["code"], "label": drop["label"],
                                  "evidence": drop["evidence"]})
            keep["flags"] = list(set(keep.get("flags", []) + ["within-unit-contradiction"]))
            keep["confidence"] = "medium" if keep["confidence"] == "high" else keep["confidence"]
            fields[var] = keep
        else:
            fields[var] = field

    # blind second pass (§5.2): only over fields that are still low-confidence.
    # The blind agent chose its scope from the *checked* (pre-adversarial)
    # confidences, so distinguish "blind tried and failed" from "never in scope
    # because the adversarial pass downgraded it to low after the fact".
    blind_scope = {c["var"] for c in codes if c.get("confidence") == "low"}
    recodes = {r["var"]: r for r in blind.get("recodes", [])}
    for var, f in fields.items():
        if f["confidence"] != "low":
            continue
        r = recodes.get(var)
        if not r or r.get("code") is None:
            f["flags"].append("blind-no-resupport" if var in blind_scope
                              else "low-not-blind-rechecked")
            continue
        col = by_code.get(var)
        agree = (r["code"] == f["code"]) or (
            col and _is_ordinal(col) and abs(int(r["code"]) - int(f["code"])) <= 1)
        if agree:
            f["confidence"] = "medium"
            f["verification"] += "; blind-agree"
        else:
            f["flags"].append("blind-disagree")
            f["alt"] = {"code": r["code"], "label": r.get("label"),
                        "evidence": r.get("evidence_quote", "")}

    for var in runners:
        if var in fields:
            fields[var]["runner_up"] = runners[var]

    # free metadata (§3): gender=female, high-confidence, prose-free
    fields.setdefault("gender", {
        "var": "gender", "code": 2, "label": "female", "confidence": "high",
        "verification": "metadata", "evidence": "", "evidence_role": "metadata",
        "theme": "", "reasoning": "study design: qualitative sample is women "
        "second-year engineering students", "provenance": "metadata-derived",
        "flags": []})

    rec = {"unit_id": unit, "verbatim": checked.get("verbatim", True),
           "placement_status": checked.get("placement_status"),
           "fields": fields,
           "skips": checked.get("skips", []),
           "themes": checked.get("themes", [])}
    FIN.mkdir(parents=True, exist_ok=True)
    (FIN / f"{unit}.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False))
    return rec


# ---- rendering: reuse the survey ColumnToText + sectioned layout (§7) ----
def _row_from_fields(fields):
    return {v: f["code"] for v, f in fields.items()}


def _capval(s):
    s = str(s)
    return s[0].upper() + s[1:] if s else s


def render_plain(rec, cols):
    """Coded persona in the same layout as a survey persona (§7): "## <topic>"
    headers, flat "Label: value" lines (no section letters, no bullets)."""
    row = _row_from_fields(rec["fields"])
    lines = [f"INTERVIEW {rec['unit_id'].upper()} — coded persona "
             f"(transcript→codes; construct-level, not survey-linked)", "",
             f"Placement status: {rec.get('placement_status')}.", ""]
    for section in SECTION_ORDER:
        sec_cols = [c for c in cols if c.section == section and c.name in rec["fields"]]
        if not sec_cols:
            continue
        block = []
        seen_bat = set()
        for c in sec_cols:
            if c.battery and c.battery not in seen_bat:
                seen_bat.add(c.battery)
                members = [m for m in sec_cols if m.battery == c.battery]
                block.append(f"{c.battery_stem} ({c.scale_label}):")
                for m in members:
                    block.append(f"{_cap(m.short_description)}: {_capval(m.render_value(row[m.name]))}")
            elif not c.battery:
                block.append(f"{_cap(c.short_description)}: {_capval(c.render_value(row[c.name]))}")
        if block:
            lines.append(f"## {SECTION_TOPIC[section]}")
            lines += block + [""]
    return "\n".join(lines)


def render_enriched(rec, cols):
    by_code = {c.name: c for c in cols}
    lines = [f"# Interview {rec['unit_id'].upper()} — enriched coded persona", "",
             f"*Placement status: {rec.get('placement_status')}. "
             f"Linkage: construct-level (no survey join). "
             f"{'Verbatim transcript' if rec['verbatim'] else 'INTERVIEWER NOTES (non-verbatim)'}.*", ""]
    for section in SECTION_ORDER:
        sec = [c for c in cols if c.section == section and c.name in rec["fields"]]
        if not sec:
            continue
        lines.append(f"## {SECTION_TOPIC[section]}")
        for c in sec:
            f = rec["fields"][c.name]
            tag = f"`{f['confidence']}` / {f['verification']} / {f['provenance']}"
            line = f"- **{c.short_description}**: {c.render_value(f['code'])}  ({tag})"
            lines.append(line)
            if f.get("evidence"):
                lines.append(f"    > “{f['evidence']}”")
            if f.get("flags"):
                lines.append(f"    - flags: {', '.join(f['flags'])}")
            if f.get("alt"):
                lines.append(f"    - blind-pass alternative: {f['alt'].get('label')} "
                             f"(“{f['alt'].get('evidence','')}”)")
        lines.append("")
    return "\n".join(lines)


def _find_subject_turn(quote, turns):
    """Index of the Subject/Notes turn whose (canonicalised) text contains the
    quote, else None."""
    cq = quote
    for i, t in enumerate(turns):
        if t["role"] in ("Subject", "Notes") and quote_in(cq, canon(t["text"])):
            return i
    return None


def theme_exchanges(rec, turns):
    """Reconstruct, per recurring-question theme, the actual interview exchanges
    behind the coded evidence (TRACE §'When the record is a transcript', §7):
    the recurring question(s) and the subject's WHOLE answer after probing,
    verbatim — not a disconnected list of quotes. Each Subject answer is paired
    with its preceding Interviewer question; multiple probes appear as multiple
    exchanges in transcript order."""
    out = []
    for th in rec.get("themes", []):
        meta = THEMES.get(th["theme"], {})
        rel = [v for v in meta.get("vars", []) if v in rec["fields"]]
        # map each verbatim answer-quote back to the Subject turn it came from
        subj_idxs = []
        for q in th.get("answer_quotes", []):
            idx = _find_subject_turn(q, turns)
            if idx is not None and idx not in subj_idxs:
                subj_idxs.append(idx)
        subj_idxs.sort()
        exchanges = []
        for si in subj_idxs:
            qi = next((j for j in range(si - 1, -1, -1)
                       if turns[j]["role"] == "Interviewer"), None)
            exchanges.append({
                "question": turns[qi]["text"] if qi is not None else None,
                "speaker": turns[si]["role"],
                "answer": turns[si]["text"],
            })
        if not exchanges:   # notes-based, or quotes that didn't map to a turn
            exchanges = [{"question": None, "speaker": "Notes", "answer": q}
                         for q in th.get("answer_quotes", [])]
        out.append({"theme": th["theme"], "label": meta.get("label", th["theme"]),
                    "related_vars": rel, "exchanges": exchanges})
    return out


def render_thematic(rec, turns):
    ex = theme_exchanges(rec, turns)
    lines = [f"# Interview {rec['unit_id'].upper()} — thematic prose", "",
             "*The full answer to each recurring interview question, after probing — "
             "shown as the verbatim exchange and linked to the variables it informs.*", ""]
    for t in ex:
        lines.append(f"## {t['label']}")
        lines.append(f"*Coded variables informed by this theme ({len(t['related_vars'])}): "
                     f"{', '.join(t['related_vars']) if t['related_vars'] else 'none'}*")
        lines.append("")
        for e in t["exchanges"]:
            if e["question"]:
                lines.append(f"**Interviewer —** {e['question']}")
                lines.append("")
            lines.append(f"**{e['speaker']} —** {e['answer']}")
            lines.append("")
    return "\n".join(lines)


def _cap(s):
    return s[0].upper() + s[1:] if s else s


# ---- reconcile coded distribution vs survey (§5.3) ----
def reconcile_vs_survey(records, cols):
    import pandas as pd
    clean = pd.read_csv(ROOT / "outputs/survey/clean_survey.csv")
    by_code = {c.name: c for c in cols}
    # key variables that are addressable & comparable
    KEYS = ["placemen", "carpath", "workrole", "interest", "challeng", "family",
            "pleased", "discoura", "school"]
    out = {}
    for var in KEYS:
        col = by_code[var]
        coded = [f for r in records for f in [r["fields"].get(var)] if f]
        # SALIENT coded marginal = confident (high/medium) codes only (§5.3)
        salient = [f for f in coded if f["confidence"] in ("high", "medium")]
        cm = Counter(by_code[var].render_value(f["code"]) for f in salient)
        n_coded = sum(cm.values())
        # survey marginal (full population, present answers)
        sm = Counter()
        for v in clean[var].dropna():
            sm[col.render_value(int(v))] += 1
        out[var] = {
            "description": col.short_description,
            "addressability_tier": next((t for t, vs in TIERS.items() if var in vs), "?"),
            "interview_n_confident": n_coded,
            "interview_salient_pct": {k: round(100*v/n_coded, 1) for k, v in cm.most_common()} if n_coded else {},
            "survey_pct": {k: round(100*v/sum(sm.values()), 1) for k, v in sm.most_common()},
            "note": "interview marginals are volunteer-biased; compare salient codes "
                    "to salient survey responders, never as a prevalence estimate (§5.3)",
        }
    (OUT / "reconciliation_vs_survey.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    return out


def build():
    cols, _ = load_columns(str(clean_data.SAV))
    by_code = {c.name: c for c in cols}
    units = sorted(p.stem for p in CHK.glob("*.json"))

    for d in ("personas_plain", "personas_enriched", "thematic_prose"):
        (OUT / d).mkdir(parents=True, exist_ok=True)

    records, jsonl = [], []
    for u in units:
        rec = reconcile_unit(u, by_code)
        if rec is None:
            continue
        records.append(rec)
        turns = json.loads((OUT / "transcripts" / f"{u}.json").read_text())["turns"]
        (OUT / "personas_plain" / f"{u}.txt").write_text(render_plain(rec, cols))
        (OUT / "personas_enriched" / f"{u}.md").write_text(render_enriched(rec, cols))
        (OUT / "thematic_prose" / f"{u}.md").write_text(render_thematic(rec, turns))
        jsonl.append(rec)

    with open(OUT / "coded_records.jsonl", "w") as f:
        for r in jsonl:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")

    recon = reconcile_vs_survey(records, cols)

    n_fields = [len(r["fields"]) for r in records]
    conf = Counter(f["confidence"] for r in records for f in r["fields"].values())
    print(f"[synthesize] reconciled {len(records)} units")
    print(f"[synthesize] coded fields per unit: min={min(n_fields)} "
          f"max={max(n_fields)} mean={sum(n_fields)/len(n_fields):.1f}")
    print(f"[synthesize] confidence mix: {dict(conf)}")
    print(f"[synthesize] reconciled vs survey on {len(recon)} key variables")
    return records, cols


if __name__ == "__main__":
    build()
