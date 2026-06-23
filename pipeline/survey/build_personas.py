"""Compose personas (CODEBOOK playbook §4): every selected column rendered and
joined, for each of the 804 respondents.

Composition choices, made deliberately (§4.1):

  * Sectioned, compact layout. A survey that is mostly batteries reads as clumsy
    boilerplate if every cell is a full sentence, so we use section headers + a
    "description: value" line per field (phrase_value_only wrapped by grouping),
    mirroring the questionnaire's own structure.
  * Battery stem stated once per block, with the response scale named once
    (§1.4 grid reassembly: stem once, not repeated across sub-items, not dropped).
  * Render present fields only (skip-heavy survey: Q7/Q8 branch, gated follow-ups)
    and account for the dropped ones separately, distinguishing "left blank" from
    "not applicable" (§4.1, §3.3).
  * Verdict honesty (§4.2): battery lines are "<statement>: <stance>" under a stem
    that names the scale, so a rating is never mistaken for a fact.

Outputs (outputs/survey/):
  personas/persona_<ID>.txt   -- the plain persona (what a model is shown)
  personas.jsonl              -- machine artifact: per-respondent fields + provenance
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

from schema import (SPECS, ID_COL, load_columns, classify_sentinel,
                    SECTION_ORDER, SEC_E, SECTION_TOPIC)
import clean_data

OUT = clean_data.OUT


def _present(col, raw_code):
    return col.is_present(raw_code)


def compose(cols, raw_row):
    """Return (persona_text, field_records, dropped_records) for one respondent.

    Layout: "## <topic>" headers and flat "Label: value" lines (no section
    letters, no bullets); battery items sit under a one-line stem that names the
    rating scale. Present-only (skip-heavy survey).
    """
    lines = [f"SURVEY RESPONDENT #{int(raw_row[ID_COL])} "
             f"(Women Engineering Students' Workplace Experiences, UKDA SN 5723)", ""]

    fields, dropped = [], []

    for section in SECTION_ORDER:
        sec_cols = [c for c in cols if c.section == section]
        if not sec_cols:
            continue
        block = []
        i = 0
        while i < len(sec_cols):
            c = sec_cols[i]
            if c.battery:
                bat = c.battery
                members = [m for m in sec_cols if m.battery == bat]
                present = [(m, raw_row[m.name]) for m in members if _present(m, raw_row[m.name])]
                for m in members:
                    code = raw_row[m.name]
                    rec = _rec(m, code, present=_present(m, code))
                    (fields if rec["present"] else dropped).append(rec)
                if present:
                    block.append(f"{c.battery_stem} ({c.scale_label}):")
                    for m, code in present:
                        block.append(f"{_cap(m.short_description)}: {_capval(m.render_value(code))}")
                i += 1
                while i < len(sec_cols) and sec_cols[i].battery == bat:
                    i += 1
            else:
                code = raw_row[c.name]
                if _present(c, code):
                    block.append(f"{_cap(c.short_description)}: {_capval(c.render_value(code))}")
                    fields.append(_rec(c, code, present=True))
                else:
                    dropped.append(_rec(c, code, present=False))
                i += 1
        if block:
            lines.append(f"## {SECTION_TOPIC[section]}")
            lines.extend(block)
            lines.append("")

    # dropped-field accounting (§4.1): distinguish not-applicable from blank
    n_na = sum(1 for d in dropped if d["missing_reason"].startswith("not applicable"))
    n_blank = len(dropped) - n_na
    lines.append(f"[Not stated: {n_blank} item(s) left blank; {n_na} item(s) "
                 f"not applicable / filtered out by a branch.]")
    return "\n".join(lines), fields, dropped


def _rec(col, raw_code, present):
    r = {
        "var": col.name, "section": col.section, "battery": col.battery,
        "description": col.short_description, "question": col.question_text,
        "origin": col.origin, "present": present,
    }
    if present:
        r["code"] = _norm(raw_code)
        r["label"] = col.render_value(raw_code)
    else:
        r["code"] = _norm(raw_code)
        r["missing_reason"] = classify_sentinel(raw_code, col)
    return r


def _norm(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return int(v) if isinstance(v, float) and v.is_integer() else v


def _cap(s):
    return s[0].upper() + s[1:] if s else s


def _capval(s):
    """Capitalise only the first letter of a rendered value (display only;
    underlying codebook label unchanged), so 'female'/'disagree' read cleanly
    while 'NH White'-style internal caps and 'PhD' survive."""
    s = str(s)
    return s[0].upper() + s[1:] if s else s


def build():
    clean, raw, cols, meta = clean_data.build()
    pdir = OUT / "personas"
    pdir.mkdir(parents=True, exist_ok=True)
    jsonl = []
    for _, row in raw.iterrows():
        text, fields, dropped = compose(cols, row)
        rid = int(row[ID_COL])
        (pdir / f"persona_{rid:03d}.txt").write_text(text)
        jsonl.append({"id": rid, "persona_text": text,
                      "fields": fields, "dropped": dropped})
    with open(OUT / "personas.jsonl", "w") as f:
        for r in jsonl:
            f.write(json.dumps(r, default=str) + "\n")

    n_fields = [len(r["fields"]) for r in jsonl]
    print(f"[personas] wrote {len(jsonl)} personas -> {pdir}")
    print(f"[personas] answered fields per persona: "
          f"min={min(n_fields)} max={max(n_fields)} mean={sum(n_fields)/len(n_fields):.1f}")
    return jsonl, cols, meta


if __name__ == "__main__":
    build()
