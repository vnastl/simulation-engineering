"""Registry + addressability tiering (INTERVIEW playbook §2, §3, §4).

LINKAGE (§2): construct-level only. The transcripts are anonymised (pseudonyms;
[company]/[town] redactions) and carry no shared id with the 804-row survey, so
we can compare *distributions* and reuse the *schema*, but we cannot join
individuals. A pseudonym in a transcript is NOT a join key.

REGISTRY (§3): unit -> {free metadata codes, session file, coding eligibility}.
The one free, high-confidence metadata fact here is gender=female: the whole
qualitative sample is women second-year engineering students (study design /
abstract). Everything else about a unit is a construct to be *coded from prose*,
not assumed from the frame.

Coding eligibility, set from the extraction format (§3 attribution rule):
  * primary           -- verbatim individual interview: code it, Subject-turn quotes.
  * notes_nonverbatim -- interviewer's prose notes (5 units): describes the
                         participant but has NO verbatim Subject turns, so it can
                         supply codes only as low-confidence, quote-free metadata-
                         style evidence; never a verbatim Subject quote (§5.1).
  * supporting_only   -- focus groups: many named speakers, attribution unreliable;
                         use as supporting evidence with speaker tags, not primary.

ADDRESSABILITY (§4): tier every survey variable from the interview GUIDE (not the
transcripts), so a 0%-coverage variable in an *unaddressed* tier is expected, not
a bug, and confident codes are expected where coverage should be high.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "outputs/interviews"

# --- Addressability tiers, authored from the four interview guides in the user
# guide (Non-placement / Pre-placement / Placement / Post-placement focus group).
# Keys are survey variable codes; see ../survey/schema.py for meanings.
TIERS = {
    "metadata": [
        # known for the whole qualitative sample, or stated in the opening round
        "gender",          # female by design (free, high confidence)
    ],
    "strong": [
        # the guide asks about these directly; expect a supporting Subject quote
        # -- reasons / influences for choosing engineering (Q1 battery)
        "highsal", "interest", "challeng", "special", "mathsci", "knowledg",
        "family", "hobbies", "gooddeg", "varied",
        "mother", "father", "careers", "teacher", "nobody",
        # encouragement / discouragement (asked: "did anyone encourage/discourage you")
        "discoura", "whodisc",
        # school type, prior work experience -> school
        "school",
        # placement decision + reasons (heavily probed across all guides)
        "placemen", "experien", "money", "educatio", "jobprosp", "jobdecid",
        "industry", "perdevel", "unigrade", "apptheor", "finalyr", "indchart",
        "placothe", "wkexp", "placloca", "breaked", "finuni", "nogain",
        "noappeal", "noaccept", "noplaoth",
        # future career intentions (Q9 / Q12)
        "carpath", "workrole",
        # course/learning-environment experience (Q4 views, Q5 satisfaction)
        "practica", "pleased", "relevanc", "competit", "Mconfid", "Fhelp",
        "interper", "quality", "supplect", "supppers", "groupwk", "friends",
        "practwk", "designwk", "variety",
    ],
    "weak": [
        # touched only indirectly; codeable sometimes, low confidence, else null
        "curricul", "deadline", "assess", "teachhrs", "coursewk", "theory",
        "furstudy", "studarea", "charship",
        # job-choice factors (Q11) -- come up via career talk but rarely as a rating
        "salary", "location", "workenv", "people", "travel", "benefits",
        "training", "promot", "equalopp", "flexible", "childcar",
        "dept", "uni",   # course/uni are stated, but as prose not the survey code
        "year",          # year/stage is stated, but as prose not the survey code
    ],
    "unaddressed": [
        # the guide never probes these; the survey is the only source -- don't fake
        "insight", "encourag",          # engineering insight course (Q2)
        "age", "ethnic", "religion",    # demographics not asked in the interviews
    ],
}


# --- Recurring-question themes (§7): coarser than variables, each maps to a
# SUBSET of the schema. Used (a) in the coder prompt to organise the read, and
# (b) to assemble the full verbatim "thematic prose" layer per unit.
THEMES = {
    "route_into_engineering": {
        "label": "Route into engineering — why they chose it, and who influenced them",
        "vars": ["highsal", "interest", "challeng", "special", "mathsci",
                 "knowledg", "family", "hobbies", "gooddeg", "varied", "mother",
                 "father", "careers", "teacher", "nobody", "discoura", "whodisc",
                 "school"],
    },
    "course_experience": {
        "label": "Experience of the engineering degree and learning environment",
        "vars": ["practica", "curricul", "pleased", "relevanc", "competit",
                 "Mconfid", "Fhelp", "deadline", "assess", "interper", "quality",
                 "supplect", "supppers", "groupwk", "teachhrs", "friends",
                 "coursewk", "theory", "practwk", "designwk", "variety"],
    },
    "placement_decision": {
        "label": "The industrial placement — whether and why to go (or not)",
        "vars": ["placemen", "experien", "money", "educatio", "jobprosp",
                 "jobdecid", "industry", "perdevel", "unigrade", "apptheor",
                 "finalyr", "indchart", "placothe", "wkexp", "placloca",
                 "breaked", "finuni", "nogain", "noappeal", "noaccept", "noplaoth"],
    },
    "future_intentions": {
        "label": "Future career intentions and what matters in a job",
        "vars": ["carpath", "workrole", "furstudy", "studarea", "charship",
                 "salary", "location", "workenv", "people", "travel", "benefits",
                 "training", "promot", "equalopp", "flexible", "childcar"],
    },
}


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    idx = json.loads((OUT / "transcript_index.json").read_text())

    elig = {"interview": "primary",
            "interview_notes": "notes_nonverbatim",
            "focus_group": "supporting_only"}

    units = []
    for r in idx:
        units.append({
            "unit_id": r["unit_id"],
            "file": r["file"],
            "kind": r["kind"],
            "format": r["format"],
            "coding_eligibility": elig[r["kind"]],
            "n_subject_turns": r["n_subject_turns"],
            "metadata_codes": {           # free, high-confidence (§3)
                "gender": {"code": 2, "label": "female", "confidence": "high",
                            "provenance": "metadata-derived",
                            "basis": "study design: qualitative sample is women "
                                     "second-year engineering students"},
            },
        })

    var_to_tier = {v: t for t, vs in TIERS.items() for v in vs}
    registry = {
        "linkage": "construct-level only (anonymised transcripts; no survey join key)",
        "n_units": len(units),
        "by_eligibility": {
            e: [u["unit_id"] for u in units if u["coding_eligibility"] == e]
            for e in ("primary", "notes_nonverbatim", "supporting_only")},
        "units": units,
    }
    (OUT / "registry.json").write_text(json.dumps(registry, indent=2, ensure_ascii=False))
    (OUT / "addressability.json").write_text(json.dumps(
        {"tiers": TIERS, "var_to_tier": var_to_tier,
         "themes": THEMES,
         "note": "tiered from the interview guides, not the transcripts (§4)"},
        indent=2, ensure_ascii=False))

    n = {e: len(v) for e, v in registry["by_eligibility"].items()}
    print(f"[registry] {len(units)} units. eligibility: {n}")
    print(f"[registry] addressability: " +
          ", ".join(f"{t}={len(vs)}" for t, vs in TIERS.items()))
    return registry


if __name__ == "__main__":
    build()
