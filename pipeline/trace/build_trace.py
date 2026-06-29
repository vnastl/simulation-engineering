"""Single-record trace -> one self-contained HTML (TRACE_PLAYBOOK).

Walks ONE survey respondent AND one interview unit through the real pipeline and
renders every stage. Read-only: every value comes from the SAME functions the
real run calls (load_columns, clean_data, build_personas.compose, the interview
synthesize renderers), sliced to one record. No logic is re-implemented here.

Because the two arms share the schema (INTERVIEW playbook §8), one trace carries
both, side by side. Sections per arm:
  1 Variables  2 Intermediate steps  3 Persona  4 Task (DRAFT, not designed here)
The interview arm inserts the full thematic prose between 1 and 2 (TRACE §"When
the record is a transcript").

Degrades gracefully: if the coded interview records are absent, the interview arm
renders a labelled warning placeholder so the structure is always visible.
"""
from __future__ import annotations

import html
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent / "survey"))
sys.path.insert(0, str(HERE.parent / "survey" / "tasks"))
sys.path.insert(0, str(HERE.parent / "interviews"))

import pandas as pd  # noqa: E402
from schema import load_columns, SECTION_ORDER, SEC_E, classify_sentinel  # noqa: E402
import clean_data  # noqa: E402
import build_personas  # noqa: E402
import task_defs as TD  # noqa: E402  (survey task layer; THEMES here ≠ registry.THEMES)
import build_tasks as BT  # noqa: E402
from registry import THEMES  # noqa: E402

OUT = ROOT / "outputs/trace"
SURVEY_OUT = ROOT / "outputs/survey"
INT_OUT = ROOT / "outputs/interviews"

PALETTE = """
  --bg:#fbfaf5; --surface:#f6f1e8; --surface2:#faf6ef; --ink:#22304a; --muted:#5e6b7a;
  --camel:#b89b72; --camel-soft:#e0d2b8; --mauve:#9b7e8e; --slate:#6d7a89;
  --good:#5f7355; --warn:#9a6b4f;
"""

CSS = """
* { box-sizing: border-box; }
body { background: var(--bg); color: var(--ink); margin: 0;
  font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
.wrap { max-width: 1180px; margin: 0 auto; padding: 28px 26px 80px; }
h1 { font-size: 25px; margin: 0 0 4px; letter-spacing: .2px; }
.subtitle { color: var(--muted); font-size: 14.5px; margin: 0 0 18px; }
.meta { background: var(--surface2); border: 1px solid var(--camel-soft); border-radius: 8px;
  padding: 12px 16px; font-size: 13.5px; margin: 0 0 22px; }
.meta b { color: var(--slate); }
.section { margin: 0 0 26px; }
.section > h2 { font-size: 18px; border-bottom: 2px solid var(--camel); padding-bottom: 6px;
  margin: 24px 0 12px; color: var(--ink); }
.panels { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; align-items: start; }
@media (max-width: 980px){ .panels { grid-template-columns: 1fr; } }
.panel { background: var(--surface); border: 1px solid var(--camel-soft); border-radius: 10px;
  padding: 6px 16px 16px; }
.panel > h4 { font-size: 14px; color: var(--ink); margin: 12px 0 2px; }
.panel > .armhdr { font-size: 12px; color: var(--muted); margin: 0 0 10px; }
.stagelbl { font-size: 12.5px; color: var(--slate); font-weight: 600; text-transform: uppercase;
  letter-spacing: .5px; margin: 14px 0 6px; }
table { border-collapse: collapse; width: 100%; font-size: 13px; margin: 6px 0 10px; }
th, td { text-align: left; padding: 4px 8px; border-bottom: 1px solid var(--camel-soft);
  vertical-align: top; }
th { color: var(--muted); font-weight: 600; }
td.code { font-family: ui-monospace, "SF Mono", Menlo, monospace; color: var(--mauve); white-space: nowrap; }
td.arrow { color: var(--camel); text-align: center; }
pre { background: var(--surface2); border: 1px solid var(--camel-soft); border-radius: 8px;
  padding: 12px 14px; white-space: pre-wrap; font-size: 12.5px;
  font-family: ui-monospace, "SF Mono", Menlo, monospace; line-height: 1.5; }
.box { border-radius: 8px; padding: 11px 14px; margin: 10px 0; font-size: 13px; }
.draft { background: #f3ecdf; border: 1px dashed var(--camel); color: #6b5836; }
.warn { background: #f4e7df; border: 1px solid var(--warn); color: var(--warn); }
.slot { background: #efe7f0; border: 1px dashed var(--mauve); color: #5b4756; }
.keyonly { background: #eef0ee; border: 1px solid var(--good); }
.keyonly > .lbl, .modelfacing > .lbl { font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .5px; display: block; margin-bottom: 5px; }
.keyonly > .lbl { color: var(--good); }
.modelfacing { background: var(--surface2); border: 1px solid var(--camel-soft); border-radius: 8px;
  padding: 10px 14px; margin: 10px 0; }
.modelfacing > .lbl { color: var(--slate); }
.themecard { border: 1px solid var(--camel-soft); border-radius: 9px; margin: 12px 0; padding: 2px 12px 10px; }
.themecard > h5 { font-size: 13.5px; margin: 10px 0 2px; color: var(--ink); }
.pos { color: var(--good); font-weight:600; } .neg { color: var(--muted); }
.sig { color: var(--warn); font-weight:600; } .nsig { color: var(--muted); }
.tag { display: inline-block; font-size: 11px; padding: 1px 7px; border-radius: 10px;
  border: 1px solid var(--camel-soft); color: var(--slate); background: var(--surface2); margin-left: 4px; }
.conf-high { color: var(--good); } .conf-medium { color: var(--camel); } .conf-low { color: var(--warn); }
details { margin: 6px 0; border: 1px solid var(--camel-soft); border-radius: 7px;
  background: var(--surface2); padding: 4px 10px; }
summary { cursor: pointer; font-size: 13px; color: var(--slate); font-weight: 600; }
blockquote { margin: 6px 0 6px 4px; padding: 3px 0 3px 12px; border-left: 3px solid var(--camel-soft);
  color: #44506a; font-size: 12.5px; }
.qline { margin: 8px 0 2px; font-size: 12.5px; color: var(--muted); }
.small { font-size: 12px; color: var(--muted); }
"""


def esc(s):
    return html.escape(str(s), quote=True)


def _is_nan(v):
    return v is None or (isinstance(v, float) and math.isnan(v))


# ----- survey arm: one function per stage (returns the panel's inner HTML) -----
def survey_variables(cols, raw):
    H = ["<table><tr><th>var</th><th>question (as asked in the survey)</th>"
         "<th>description (noun phrase)</th><th>raw code</th></tr>"]
    for c in cols:
        v = raw[c.name]
        H.append(f"<tr><td class='code'>{esc(c.name)}</td>"
                 f"<td class='small'>{esc(c.question_text or '—')}</td>"
                 f"<td>{esc(c.short_description)}</td>"
                 f"<td class='code'>{esc('' if _is_nan(v) else int(v))}</td></tr>")
    return "".join(H) + "</table>"


def survey_intermediate(cols, raw, clean):
    H = ["<p class='small'>Per (column, code): a labelled code renders to its label; "
         "an unlabelled code is a sentinel → NaN (shown for honesty as its missing flavour).</p>",
         "<table><tr><th>var</th><th>raw</th><th></th><th>cleaned</th>"
         "<th>rendered / missing flavour</th></tr>"]
    for c in cols:
        rv = raw[c.name]; cv = clean[c.name]
        present = c.is_present(rv)
        rendered = c.render_value(rv) if present else classify_sentinel(rv, c)
        cleaned = "" if _is_nan(cv) else int(cv)
        H.append(f"<tr><td class='code'>{esc(c.name)}</td><td class='code'>"
                 f"{esc('' if _is_nan(rv) else int(rv))}</td><td class='arrow'>→</td>"
                 f"<td class='code'>{esc(cleaned)}</td><td>{esc(rendered)}</td></tr>")
    return "".join(H) + "</table>"


def survey_persona(cols, raw):
    text, fields, dropped = build_personas.compose(cols, raw)
    n_na = sum(1 for d in dropped if d['missing_reason'].startswith('not applicable'))
    return (f"<p class='small'>{len(fields)} fields rendered; {len(dropped)-n_na} left blank, "
            f"{n_na} not applicable (dropped, present-only).</p><pre>{esc(text)}</pre>")


SLOT = ('<div class="box slot"><b>MODEL OUTPUT + SCORE — open slot.</b> '
        'This pipeline does not call a model (TASK_PLAYBOOK §4 "show, don\'t run"). '
        'A model answer would be scored here by the runnable scorer '
        '(<span class="code">rubric.{fn}</span>) against the answer key on the left; '
        'we render the key and leave the answer + score explicitly <b>not run</b>.</div>')


def _key_dir_class(direction, significant):
    return ("sig", direction) if significant else ("nsig", "about equal (n.s.)")


def survey_task(by_code, raw_row, forbidden, tasks, keys, themes):
    """§4 — render the REAL task artifacts for this respondent (TRACE §4).

    Model-facing material (conditioning persona + prompts) is boxed apart from
    answer-key-only material (estimates, denominators, correct answers) so a reader
    cannot mistake the scorer's view for the model's. The model's answer + score is
    an explicit open slot.
    """
    H = [f"<p class='small'>The §3 persona is the conditioning base. Each theme holds out a "
         f"different outcome battery and splits the population on a <b>different axis</b> "
         f"(§1.3) — three the study foregrounds: <b>industrial placement</b>, "
         f"<b>university type</b> and <b>engineering discipline</b>. Populations are named "
         f"by definition, never by size (§4); the answer keys are validated against the "
         f"report's printed marginals (jobdecid 87%/93% female, industry 94%; see "
         f"<span class='code'>answer_keys.json → validation</span>). Three shapes per theme: "
         f"<i>micro</i> (this respondent), <i>macro-prose</i>, <i>macro-number</i>.</p>"]

    for ti, theme in enumerate(themes):
        t = tasks["themes"][theme.key]
        kt = keys["themes"][theme.key]
        sp = t["split"]
        gA, gB = sp["group_order"]
        glabel = {g["key"]: g["label"] for g in kt["split"]["groups"]}
        micro = BT.render_micro(theme, raw_row, by_code, forbidden)
        holdout = theme.holdout_codes()
        open_first = " open" if ti == 0 else ""

        # held-out items: this respondent's true value (scorer-only micro key)
        mk_rows = []
        for it in theme.outcome_items:
            tr = micro["answer_key"]["held_out_truth"][it.code]
            if tr["answered"]:
                pos = "<span class='pos'>pos ✓</span>" if tr["pos"] else "<span class='neg'>neg</span>"
                ans = f"answered “{esc(tr['respondent_answer'])}” → {pos}"
            else:
                ans = "<span class='small'>not answered</span>"
            mk_rows.append(f"<tr><td class='code'>{esc(it.code)}</td>"
                           f"<td class='small'>{esc(by_code[it.code].question_text)}</td>"
                           f"<td>{ans}</td></tr>")

        # macro answer key: group %s, p, significance, keyed direction
        mac_rows = []
        for it in kt["items"]:
            mk = t["shapes"]["macro_prose"]["answer_key"][it["code"]]
            cls, lbl = _key_dir_class(mk["direction"], it["significant"])
            p = it["p_value"]
            mac_rows.append(
                f"<tr><td class='code'>{esc(it['code'])}</td>"
                f"<td>{esc(it['groups'][gA]['pct'])}%</td>"
                f"<td>{esc(it['groups'][gB]['pct'])}%</td>"
                f"<td class='small'>{('%.4f'%p) if p is not None else 'n/a'}</td>"
                f"<td class='{cls}'>{esc(lbl)}</td></tr>")

        # which group this respondent falls in, on THIS theme's axis (may be neither —
        # e.g. a two-discipline split covers only part of the sample)
        my_group = micro["answer_key"].get("respondent_group")
        my_group_lbl = (glabel.get(my_group) if my_group
                        else "not in either group — micro shown for illustration")

        H.append(
            f"<details class='themecard'{open_first}><summary><b>Theme {ti+1} — "
            f"{esc(theme.title)}</b> <span class='tag'>split: {esc(sp['axis'])}</span> "
            f"<span class='tag'>{len(holdout)} held-out items</span></summary>"
            f"<p class='small'><b>Split ({esc(sp['axis'])}):</b> "
            f"<b>{esc(glabel.get(gA, gA))}</b> ({esc(sp['A_population'])}) vs "
            f"<b>{esc(glabel.get(gB, gB))}</b> ({esc(sp['B_population'])}) — a cut the report "
            f"does not print for this outcome. <b>Held out:</b> {esc(theme.outcome_group)}.</p>"
            f"<p class='small'><b>Grounding:</b> {esc(theme.paper_grounding[:260])}…</p>"

            # ---- MICRO ----
            f"<h5>micro — representational accuracy (this respondent — {esc(my_group_lbl)})</h5>"
            f"<div class='modelfacing'><span class='lbl'>Model sees — conditioning + prompt</span>"
            f"<p class='small'>Conditioning = the §3 persona restricted to "
            f"<b>{micro['n_conditioning_fields']}</b> apt fields "
            f"({esc(theme.conditioning_rationale[:130])}…); the held-out items are removed. "
            f"<details><summary>show this respondent's conditioning view</summary>"
            f"<pre>{esc(micro['conditioning_persona'])}</pre></details></p>"
            f"<details><summary>show the micro prompt</summary><pre>{esc(theme.micro_prompt.replace('{persona}', '«persona above»'))}</pre></details></div>"
            f"<div class='box keyonly'><span class='lbl'>Answer key — scorer only, held out from the model</span>"
            f"<table><tr><th>item</th><th>statement (verbatim)</th><th>this respondent's truth</th></tr>"
            f"{''.join(mk_rows)}</table></div>"
            + SLOT.format(fn="score_micro_prose")

            # ---- MACRO ----
            + f"<h5>macro — external + internal consistency (populations by {esc(sp['axis'])})</h5>"
            f"<div class='modelfacing'><span class='lbl'>Model sees — prompt (populations by definition)</span>"
            f"<details><summary>macro-prose prompt</summary><pre>{esc(t['shapes']['macro_prose']['model_facing']['prompt'])}</pre></details>"
            f"<details><summary>macro-number prompt</summary><pre>{esc(t['shapes']['macro_number']['model_facing']['prompt'])}</pre></details></div>"
            f"<div class='box keyonly'><span class='lbl'>Answer key — scorer only (frozen estimates; direction gated on significance §3.4)</span>"
            f"<table><tr><th>item</th><th>{esc(glabel.get(gA, gA))} %</th>"
            f"<th>{esc(glabel.get(gB, gB))} %</th><th>Fisher p</th><th>keyed direction</th></tr>"
            f"{''.join(mac_rows)}</table>"
            f"<p class='small'>A non-significant gap is keyed <i>about equal</i>, so the scorer "
            f"never credits a fabricated direction. Significance is <b>Fisher exact</b> — "
            f"design-exact here because the study ships <b>no survey weight</b> (the design is "
            f"simple random sampling, n_eff = n).</p></div>"
            + SLOT.format(fn="score_macro_prose / score_macro_number")
            + "</details>")
    return "".join(H)


def interview_task(theme0, by_code, rec, forbidden):
    """§4 for the interview arm — the coded persona is a drop-in for the SAME task
    layer (shared schema). The macro answer keys are survey-derived; interview
    marginals are volunteer-biased, so interview responses are not used as a key."""
    if rec is None:
        return WARN.format("Coded record not yet produced — run synthesize.py, then rebuild.")
    return (
        "<p class='small'>The coded persona plugs into the <b>same</b> micro task as the "
        "survey arm (shared schema, same rubric, same survey-derived answer keys). "
        "Conditioning = the coded persona restricted to a theme's allow-list, held-out "
        "items removed; the model's answer + score is the same open slot.</p>"
        "<div class='box keyonly'><span class='lbl'>Why no macro answer key here</span>"
        "<p class='small'>The macro tasks compare survey populations (by placement / university / "
        "discipline) and their answer keys are the survey's frozen estimates. The interview "
        "arm is women-only and its marginals are volunteer-biased (AGENT_README §5.3/§8), so "
        "interview responses are <b>not</b> used as an answer key; the survey arm owns the "
        "frozen estimates.</p></div>"
        + '<div class="box slot"><b>MODEL OUTPUT + SCORE — open slot (not run).</b> '
        'Same scorer, same held-out design as the survey micro task.</div>')


# ----- interview arm: one function per stage -----
def interview_variables(tr):
    turns_html = "\n".join(
        f"<b>{esc(t['role'])}:</b> {esc(t['text'])}" for t in tr["turns"][:60])
    return (f"<p class='small'>{tr['n_turns']} turns, {tr['n_subject_turns']} Subject turns "
            f"({tr['kind']}, {tr['format']} format).</p>"
            f"<details><summary>Show transcript turns (first 60)</summary>"
            f"<pre>{turns_html}</pre></details>")


def interview_intermediate(rec, tr, cols):
    from synthesize import theme_exchanges
    H = ['<div class="stagelbl">Stage A · full thematic prose '
         '(the interview exchange per recurring question)</div>']
    for t in theme_exchanges(rec, tr["turns"]):
        ex = []
        for e in t["exchanges"]:
            if e["question"]:
                ex.append(f"<p class='qline'><b>Interviewer —</b> {esc(e['question'])}</p>")
            ex.append(f"<blockquote><b>{esc(e['speaker'])} —</b> {esc(e['answer'])}</blockquote>")
        H.append(f"<details><summary>{esc(t['label'])} "
                 f"<span class='tag'>{len(t['related_vars'])} coded vars</span></summary>"
                 f"{''.join(ex)}</details>")
    H.append('<div class="stagelbl">Stage B · prose → codes + verification</div>')
    H.append("<table><tr><th>var</th><th>code → label</th><th>conf</th>"
             "<th>verification</th><th>verbatim evidence</th></tr>")
    for c in cols:
        f = rec["fields"].get(c.name)
        if not f:
            continue
        ev = f.get("evidence", "")
        H.append(f"<tr><td class='code'>{esc(c.name)}</td>"
                 f"<td>{esc(f['code'])} → {esc(c.render_value(f['code']))}</td>"
                 f"<td class='conf-{f['confidence']}'>{esc(f['confidence'])}</td>"
                 f"<td class='small'>{esc(f.get('verification',''))}</td>"
                 f"<td><blockquote>{esc(ev) if ev else '<span class=small>(metadata)</span>'}</blockquote></td></tr>")
    return "".join(H) + "</table>"


def interview_persona(rec, cols):
    from synthesize import render_plain
    plain = render_plain(rec, cols)
    return (f"<p class='small'>{len(rec['fields'])} coded fields, rendered through the "
            f"SAME ColumnToText the survey uses (§7).</p><pre>{esc(plain)}</pre>")


WARN = '<div class="box warn">{}</div>'


def pick_survey_id(clean_df):
    counts = clean_df.drop(columns=["ID"]).notna().sum(axis=1)
    return int(clean_df.loc[counts.idxmax(), "ID"])


def pick_interview_unit():
    fin = INT_OUT / "coding/final"
    best, best_score = None, -1
    if fin.exists():
        for p in sorted(fin.glob("int*.json")):
            rec = json.loads(p.read_text())
            score = sum(1 for f in rec["fields"].values() if f["confidence"] == "high")
            if score > best_score:
                best, best_score = rec["unit_id"], score
    return best or "int01"


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    cols, _ = load_columns(str(clean_data.SAV))
    raw_df = pd.read_csv(SURVEY_OUT / "raw_codes.csv")
    clean_df = pd.read_csv(SURVEY_OUT / "clean_survey.csv")

    sid = pick_survey_id(clean_df)
    unit = pick_interview_unit()

    raw = raw_df[raw_df.ID == sid].iloc[0]
    clean = clean_df[clean_df.ID == sid].iloc[0]

    # task layer artifacts (degrade gracefully if not yet built — TRACE ground rule)
    by_code = {c.name: c for c in cols}
    TASK_OUT = SURVEY_OUT / "tasks"
    tasks = json.loads((TASK_OUT / "tasks.json").read_text()) if (TASK_OUT / "tasks.json").exists() else None
    task_keys = json.loads((TASK_OUT / "answer_keys.json").read_text()) if (TASK_OUT / "answer_keys.json").exists() else None
    forbidden = BT._forbidden_size_tokens(task_keys) if task_keys else set()
    tr_path = INT_OUT / "transcripts" / f"{unit}.json"
    fin_path = INT_OUT / "coding/final" / f"{unit}.json"
    tr = json.loads(tr_path.read_text()) if tr_path.exists() else None
    rec = json.loads(fin_path.read_text()) if fin_path.exists() else None

    meta = (f"<div class='meta'><b>Study:</b> UK Data Service SN 5723 — "
            f"Women Engineering Students' Workplace Experiences: Impact on Career "
            f"Intentions, 2004–2005 (Bagilhole, Dainty, Neale, Powell). &nbsp; "
            f"<b>Units:</b> survey n=804, interviews n=72 (+2 focus groups). &nbsp; "
            f"<b>This trace:</b> two records walked side by side per stage — survey "
            f"respondent #{sid} (most-answered) via the codebook→persona pipeline, and "
            f"interview {unit.upper()} (most high-confidence codes) via the "
            f"transcript→coded-persona pipeline. Construct-level only (no survey↔interview "
            f"join). &nbsp; <b>Generated by:</b> pipeline/trace/build_trace.py (read-only).</div>")

    # each stage: (title, survey-panel-html, interview-panel-html)
    no_tr = WARN.format("Transcript missing — interview arm unavailable.")
    no_rec = WARN.format("Coded record not yet produced — run synthesize.py, then rebuild.")
    stages = [
        ("1 · Variables (raw input)",
         survey_variables(cols, raw),
         interview_variables(tr) if tr else no_tr),
        ("2 · Intermediate steps",
         survey_intermediate(cols, raw, clean),
         interview_intermediate(rec, tr, cols) if rec and tr else no_rec),
        ("3 · Persona",
         survey_persona(cols, raw),
         interview_persona(rec, cols) if rec else no_rec),
        ("4 · Task (prompting)",
         survey_task(by_code, raw, forbidden, tasks, task_keys, TD.THEMES) if tasks and task_keys
         else WARN.format("Task layer not built — run pipeline/survey/tasks/estimate.py "
                          "then build_tasks.py, then rebuild."),
         interview_task(TD.THEMES[0], by_code, rec, forbidden)),
    ]
    sv_hdr = (f"<h4>Survey · respondent #{sid}</h4>"
              f"<div class='armhdr'>codebook → persona (deterministic). "
              f"Selection: respondent answering the most items.</div>")
    iv_hdr = (f"<h4>Interview · {unit.upper()}</h4>"
              f"<div class='armhdr'>transcript → coded persona (LLM-coded + verified). "
              f"Selection: most high-confidence codes.</div>")

    body = []
    for title, sv, iv in stages:
        body.append(
            f'<div class="section"><h2>{title}</h2><div class="panels">'
            f'<div class="panel">{sv_hdr}{sv}</div>'
            f'<div class="panel">{iv_hdr}{iv}</div>'
            f'</div></div>')

    doc = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SN5723 pipeline trace — one respondent</title>
<style>:root {{{PALETTE}}}{CSS}</style></head><body><div class="wrap">
<h1>Women Engineering Students pipeline trace — one respondent</h1>
<p class="subtitle">Women Engineering Students' Workplace Experiences: Impact on Career
Intentions, 2004–2005 (UKDA SN 5723) — codebook→persona pipeline + transcript→coded-persona pipeline + micro→macro task layer</p>
{meta}
{''.join(body)}
</div></body></html>"""
    path = OUT / "trace.html"
    path.write_text(doc)

    # plain-text mirror (TRACE ground rule: "mirrored to stdout as plain text")
    raw = raw_df[raw_df.ID == sid].iloc[0]
    survey_text, sfields, sdropped = build_personas.compose(cols, raw)
    txt = [f"SN5723 PIPELINE TRACE — survey #{sid} & interview {unit}", "=" * 64, "",
           "SURVEY ARM — §3 persona (codebook→persona):", "", survey_text, ""]
    if tasks and task_keys:
        txt += ["=" * 64, "",
                f"SURVEY ARM — §4 task layer (micro→macro), respondent #{sid}:",
                "(each theme splits the population on a DIFFERENT axis, §1.3)", ""]
        for theme in TD.THEMES:
            t = tasks["themes"][theme.key]
            kt = task_keys["themes"][theme.key]
            sp = t["split"]
            gA, gB = sp["group_order"]
            glabel = {g["key"]: g["label"] for g in kt["split"]["groups"]}
            micro = BT.render_micro(theme, raw, by_code, forbidden)
            txt.append(f"— Theme: {theme.title}  [split: {sp['axis']} — "
                       f"{glabel.get(gA,gA)} vs {glabel.get(gB,gB)}]  (held out: {theme.outcome_group})")
            for it in kt["items"]:
                tr = micro["answer_key"]["held_out_truth"][it["code"]]
                truth = (f"this respondent: {tr['respondent_answer']} "
                         f"({'pos' if tr['pos'] else 'neg'})") if tr["answered"] else "this respondent: n/a"
                sig = "sig" if it["significant"] else "n.s.→about-equal"
                mk = t["shapes"]["macro_prose"]["answer_key"][it["code"]]
                txt.append(f"   {it['code']:9} {glabel.get(gA,gA)[:8]}={it['groups'][gA]['pct']}% "
                           f"{glabel.get(gB,gB)[:8]}={it['groups'][gB]['pct']}% "
                           f"[{sig}, dir={mk['direction']}]  | {truth}")
            txt.append("   (micro/macro-prose/macro-number prompts in outputs/survey/tasks/tasks.json; "
                       "model answer + score = OPEN SLOT, not run)")
            txt.append("")
    txt += ["=" * 64, "", f"INTERVIEW ARM — {unit.upper()} §3 persona (transcript→codes→persona):", ""]
    fin = INT_OUT / "coding/final" / f"{unit}.json"
    if fin.exists():
        from synthesize import render_plain
        txt.append(render_plain(json.loads(fin.read_text()), cols))
    txt_path = OUT / "trace.txt"
    txt_path.write_text("\n".join(txt))

    print(f"[trace] survey #{sid}, interview {unit} -> {path}")
    print(f"[trace] plain-text mirror -> {txt_path}")
    return path


if __name__ == "__main__":
    build()
