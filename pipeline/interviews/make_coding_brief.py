"""Generate the coding brief: the survey schema rendered as a prompt-friendly
artifact a coder agent reads (INTERVIEW playbook §1 -- reuse the survey codebook
as the target schema; coders may emit ONLY codes from its value-labels).

Writes:
  outputs/interviews/coding_brief.json  -- machine artifact for agents/scripts
  outputs/interviews/coding_brief.md    -- human-readable version
Each variable carries: code, description, question wording, addressability tier,
and the EXACT allowed {code: label} options (so a coder cannot invent a code).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent / "survey"))
sys.path.insert(0, str(HERE))

from schema import load_columns, SECTION_ORDER  # noqa: E402
from registry import TIERS  # noqa: E402
import clean_data  # noqa: E402

OUT = ROOT / "outputs/interviews"


def build():
    cols, _ = load_columns(str(clean_data.SAV))
    var_to_tier = {v: t for t, vs in TIERS.items() for v in vs}

    brief = []
    for c in cols:
        tier = var_to_tier.get(c.name, "weak")
        if tier == "unaddressed":
            continue  # do not ask coders for variables the guide never probes (§4)
        opts = (c.value_map if isinstance(c.value_map, dict) else {})
        brief.append({
            "var": c.name,
            "section": c.section,
            "battery_stem": c.battery_stem,
            "description": c.short_description,
            "question": c.question_text,
            "tier": tier,
            "scale": c.scale_label,
            "allowed_values": {str(k): v for k, v in opts.items()},
        })

    (OUT / "coding_brief.json").write_text(json.dumps(brief, indent=1, ensure_ascii=False))

    # human-readable
    lines = ["# Interview coding brief — target = the 5723 survey schema",
             "",
             "Code each VERBATIM-supported construct into the value-labels below. "
             "Emit ONLY a listed code. Null over guess. `unaddressed` variables "
             "(engineering-insight course, age, ethnicity, religion) are omitted: "
             "the interview guide never probes them.", ""]
    by_sec = {}
    for b in brief:
        by_sec.setdefault(b["section"], []).append(b)
    for sec in SECTION_ORDER:
        if sec not in by_sec:
            continue
        lines.append(f"\n## {sec}")
        for b in by_sec[sec]:
            opts = "; ".join(f"{k}={v}" for k, v in b["allowed_values"].items())
            stem = f" [{b['battery_stem']}]" if b["battery_stem"] else ""
            lines.append(f"- **{b['var']}** ({b['tier']}) — {b['description']}{stem}")
            lines.append(f"    Q: {b['question']}")
            lines.append(f"    values: {opts}")
    (OUT / "coding_brief.md").write_text("\n".join(lines))

    from collections import Counter
    tc = Counter(b["tier"] for b in brief)
    print(f"[brief] {len(brief)} addressable variables -> coding_brief.json/.md")
    print(f"[brief] tiers: {dict(tc)}")
    return brief


if __name__ == "__main__":
    build()
