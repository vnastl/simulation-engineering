"""Deterministic quote-presence check (INTERVIEW playbook §5.1) — run FIRST,
before the adversarial re-read. It is cheap and catches the most confident
fabrications; reversed, an LLM re-read can "confirm" a code against a quote that
was never on the page.

Canonicalise BOTH sides before matching, or the check eats true quotes (§5.1):
fold whitespace, unify quote/dash glyphs, strip speaker tags, lowercase, and
allow "…" to stand for an elided gap. We also enforce the source rule: for a
verbatim interview the evidence must sit inside a *Subject* turn (not the
interviewer's). Notes-based units match against the Notes text.

Reads:  outputs/interviews/coding/raw/<unit>.json   (coder output)
        outputs/interviews/transcripts/<unit>.json   (turns)
Writes: outputs/interviews/coding/checked/<unit>.json (codes kept + drops logged)
        outputs/interviews/coding/quote_check_report.json
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "outputs/interviews"
RAW = OUT / "coding/raw"
CHK = OUT / "coding/checked"


def canon(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    # unify quote and dash glyphs
    for a, b in [("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'),
                 ("–", "-"), ("—", "-"), ("‑", "-"), (" ", " ")]:
        s = s.replace(a, b)
    s = s.lower()
    # strip inserted speaker tags
    s = re.sub(r"\b(interviewer|subject|notes|interviewer\s*\d)\s*:", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def quote_in(quote: str, haystack: str) -> bool:
    """True if every '…'-separated verbatim fragment appears, in order."""
    q = canon(quote)
    if not q:
        return False
    parts = [p.strip() for p in re.split(r"\s*\.{2,}\s*|\s*…\s*", q) if p.strip()]
    if not parts:
        return False
    pos = 0
    for p in parts:
        idx = haystack.find(p, pos)
        if idx < 0:
            return False
        pos = idx + len(p)
    return True


def check_unit(unit: str):
    raw = json.loads((RAW / f"{unit}.json").read_text())
    tr = json.loads((OUT / "transcripts" / f"{unit}.json").read_text())
    verbatim = raw.get("verbatim", True)

    subject_text = canon(" ".join(t["text"] for t in tr["turns"]
                                  if t["role"] in ("Subject", "Notes")))
    full_text = canon(" ".join(t["text"] for t in tr["turns"]))

    kept, drops = [], []
    for c in raw.get("codes", []):
        q = c.get("evidence_quote", "")
        in_subject = quote_in(q, subject_text)
        in_full = quote_in(q, full_text)
        if in_subject:
            kept.append(c)
        elif in_full and not verbatim:
            kept.append(c)            # notes-based: subject/notes already merged
        else:
            reason = ("quote not found in transcript" if not in_full
                      else "quote only in Interviewer turn (interviewer-planted)")
            drops.append({**c, "_drop_reason": reason})

    # theme quotes: verify verbatim too (§7)
    themes_checked = []
    for th in raw.get("themes", []):
        good = [aq for aq in th.get("answer_quotes", []) if quote_in(aq, full_text)]
        themes_checked.append({"theme": th["theme"], "answer_quotes": good,
                               "n_dropped": len(th.get("answer_quotes", [])) - len(good)})

    out = {**raw, "codes": kept, "themes": themes_checked,
           "_quote_check": {"n_codes_in": len(raw.get("codes", [])),
                            "n_codes_kept": len(kept), "n_dropped": len(drops),
                            "drops": drops}}
    CHK.mkdir(parents=True, exist_ok=True)
    (CHK / f"{unit}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    return out["_quote_check"]


def run(units=None):
    if units is None:
        units = sorted(p.stem for p in RAW.glob("*.json"))
    report = {}
    tot_in = tot_kept = tot_drop = 0
    for u in units:
        r = check_unit(u)
        report[u] = r
        tot_in += r["n_codes_in"]; tot_kept += r["n_codes_kept"]; tot_drop += r["n_dropped"]
    drop_rate = tot_drop / tot_in if tot_in else 0
    summary = {"n_units": len(units), "codes_in": tot_in, "codes_kept": tot_kept,
               "codes_dropped": tot_drop, "drop_rate": round(drop_rate, 4)}
    (OUT / "coding/quote_check_report.json").write_text(
        json.dumps({"summary": summary, "per_unit": report}, indent=2))
    print(f"[quote_check] units={len(units)} codes_in={tot_in} kept={tot_kept} "
          f"dropped={tot_drop} ({drop_rate:.1%})")
    return summary


if __name__ == "__main__":
    import sys
    run(sys.argv[1:] or None)
