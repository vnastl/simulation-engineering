"""Survey schema = the lookup table as data (CODEBOOK playbook §1.2).

One row per variable. The split of sources (§1.1) is respected:

  * value maps  -> loaded from the SPSS .sav embedded metadata (authoritative,
                   machine-readable). NEVER re-typed here, to avoid transcription
                   error. (§1.1: "use it, and do not re-derive value codes.")
  * question wording -> derived from the embedded variable label (which on this
                   survey carries the full item text, e.g. "1A I was attracted
                   to engineering ..."), lightly cleaned (§1.4).
  * short descriptions / section & battery grouping / missing semantics ->
                   AUTHORED here inline, because the whole instrument fits in
                   context (§1.5 inline-authoring path: no id-misalignment, no
                   blind hallucination, deterministic).

This module owns the survey-specific asset (§4.3). The renderer (column_to_text)
is trivial and swappable around it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import pyreadstat

from column_to_text import ColumnToText, phrase_value_only

# --- scale labels shared across batteries (shown once per block) -----------
AGREE5 = "5-point scale, strongly disagree → strongly agree"
SATIS5 = "5-point scale, very dissatisfied → very satisfied"
IMPORT5 = "5-point scale, very unimportant → very important"

SEC_A = "A. Choosing engineering"
SEC_B = "B. Experiences of higher education"
SEC_C = "C. Industrial placement"
SEC_D = "D. Future in engineering"
SEC_E = "E. About the respondent"


@dataclass
class Spec:
    """Authored per-variable metadata (everything NOT taken from the .sav)."""
    short_description: str
    section: str
    battery: str = ""
    battery_stem: str = ""
    scale_label: str = ""
    origin: str = "elicited"
    is_verdict_battery: bool = False


# A battery helper to cut repetition.
def _bat(short, section, battery, stem, scale):
    return Spec(short, section, battery=battery, battery_stem=stem,
               scale_label=scale, is_verdict_battery=True)


_Q1 = lambda s: _bat(s, SEC_A, "q1_influences",
                     "Influences on the decision to study engineering", AGREE5)
_Q4 = lambda s: _bat(s, SEC_B, "q4_degree_views",
                     "Level of agreement with statements about the degree", AGREE5)
_Q5 = lambda s: _bat(s, SEC_B, "q5_satisfaction",
                     "Satisfaction with aspects of the course", SATIS5)
_Q7 = lambda s: _bat(s, SEC_C, "q7_reasons_for",
                     "Reasons for wanting to go on placement", AGREE5)
_Q8 = lambda s: _bat(s, SEC_C, "q8_reasons_against",
                     "Reasons for not going on placement", AGREE5)
_Q11 = lambda s: _bat(s, SEC_D, "q11_job_factors",
                      "Importance of factors when choosing a job", IMPORT5)


# Authored specs, in questionnaire order. Keys are the .sav column codes.
SPECS: dict[str, Spec] = {
    # --- Section A: Q1 influences battery (A-O) ---
    "highsal":  _Q1("high salary as a draw to engineering"),
    "interest": _Q1("the chance to do interesting work"),
    "challeng": _Q1("wanting the challenge of solving problems"),
    "special":  _Q1("using science and maths without specialising"),
    "mathsci":  _Q1("being good at maths and science at school"),
    "knowledg": _Q1("choosing engineering with little knowledge of the job"),
    "family":   _Q1("having a family member in the industry"),
    "hobbies":  _Q1("having technical hobbies and interests"),
    "gooddeg":  _Q1("engineering as a good degree to hold regardless"),
    "varied":   _Q1("engineering's appeal as a varied field"),
    "mother":   _Q1("mother's encouragement to study engineering"),
    "father":   _Q1("father's encouragement to study engineering"),
    "careers":  _Q1("careers advisor's encouragement"),
    "teacher":  _Q1("school teacher's encouragement"),
    "nobody":   _Q1("nobody encouraged the choice"),
    # --- Section A: Q2/Q3 ---
    "insight":  Spec("ever attended an engineering insight course", SEC_A),
    "encourag": Spec("whether the insight course encouraged studying engineering", SEC_A),
    "discoura": Spec("whether anyone discouraged studying engineering", SEC_A),
    "whodisc":  Spec("who discouraged studying engineering", SEC_A),
    # --- Section B: Q4 degree-views battery (A-J) ---
    "practica": _Q4("the level of practical work being just right"),
    "curricul": _Q4("the curriculum being harder than expected"),
    "pleased":  _Q4("being pleased with the choice to study engineering"),
    "relevanc": _Q4("difficulty seeing the relevance of some modules"),
    "competit": _Q4("engineering students being competitive"),
    "Mconfid":  _Q4("male students being more confident in class"),
    "Fhelp":    _Q4("female students getting more help in class"),
    "deadline": _Q4("always having competing deadlines"),
    "assess":   _Q4("the coursework/exam balance being just right"),
    "interper": _Q4("the course developing interpersonal skills"),
    # --- Section B: Q5 satisfaction battery (A-K) ---
    "quality":  _Q5("quality of lectures"),
    "supplect": _Q5("support from lecturers"),
    "supppers": _Q5("support from a personal tutor"),
    "groupwk":  _Q5("group work"),
    "teachhrs": _Q5("number of teaching hours"),
    "friends":  _Q5("the friends made on the course"),
    "coursewk": _Q5("quantity of coursework"),
    "theory":   _Q5("theory work"),
    "practwk":  _Q5("practical work"),
    "designwk": _Q5("design work"),
    "variety":  _Q5("variety of subjects covered"),
    # --- Section C: Q6 + Q7 reasons-for battery (A-K) + L other ---
    "placemen": Spec("whether they have gone / intend to go on placement", SEC_C),
    "experien": _Q7("for the work experience"),
    "money":    _Q7("because of needing the money"),
    "educatio": _Q7("for a break from education"),
    "jobprosp": _Q7("to improve job chances after university"),
    "jobdecid": _Q7("to help decide a future direction"),
    "industry": _Q7("to see what industry is really like"),
    "perdevel": _Q7("for personal development"),
    "unigrade": _Q7("to improve grades on returning to university"),
    "apptheor": _Q7("to apply theory learnt at university"),
    "finalyr":  _Q7("to help choose a final-year project"),
    "indchart": _Q7("because it counts towards Chartership"),
    "placothe": Spec("additional reason for wanting placement", SEC_C),
    # --- Section C: Q8 reasons-against battery (A-G) + H other ---
    "wkexp":    _Q8("already having work experience"),
    "placloca": _Q8("no placement available in a suitable location"),
    "breaked":  _Q8("fear of returning to education after a break"),
    "finuni":   _Q8("wanting to finish university sooner and start earning"),
    "nogain":   _Q8("seeing nothing to be gained from a placement"),
    "noappeal": _Q8("no available placement appealing"),
    "noaccept": _Q8("having applied but not been accepted"),
    "noplaoth": Spec("additional reason for not going on placement", SEC_C),
    # --- Section D: Q9-Q13 ---
    "carpath":  Spec("preferred area of engineering to specialise in", SEC_D),
    "furstudy": Spec("whether they would like to go on to further study", SEC_D),
    "studarea": Spec("intended area of further study", SEC_D),
    "salary":   _Q11("salary"),
    "location": _Q11("location"),
    "workenv":  _Q11("work environment"),
    "people":   _Q11("the people worked with"),
    "travel":   _Q11("opportunities to travel"),
    "benefits": _Q11("benefits such as a company car"),
    "training": _Q11("training opportunities"),
    "promot":   _Q11("opportunities for promotion"),
    "equalopp": _Q11("equal-opportunities policies"),
    "flexible": _Q11("opportunities for flexible working"),
    "childcar": _Q11("childcare policies"),
    "workrole": Spec("preferred future work role", SEC_D),
    "charship": Spec("importance of gaining Chartership", SEC_D),
    # --- Section E: demographics ---
    "gender":   Spec("gender", SEC_E, origin="metadata"),
    "age":      Spec("age band", SEC_E, origin="metadata"),
    "ethnic":   Spec("ethnic group", SEC_E, origin="metadata"),
    "religion": Spec("religion", SEC_E, origin="metadata"),
    "school":   Spec("type of secondary school attended", SEC_E, origin="metadata"),
    "year":     Spec("year of study", SEC_E, origin="metadata"),
    "dept":     Spec("department", SEC_E, origin="metadata"),
    "uni":      Spec("university type (pre- or post-1992)", SEC_E, origin="metadata"),
}

ID_COL = "ID"

# --- Reconciliation allow-list (§2.2): the unexplained codes we have
# investigated and accepted as sentinels. Freezing it as an assertion turns the
# one-time reconciliation into a standing regression guard: a NEW unexplained
# code in a re-export fails loudly instead of rendering raw.
#   0  -> left blank / no answer (the depositor's recode of an empty cell)
#   9  -> not applicable: the item was filtered out by a branch
#          (Q7 if not on placement; Q8 if on placement; encourag/whodisc/studarea
#           gated by their yes/no parent). 9 is a *real* label on carpath
#          ("don't know") and is therefore NOT a sentinel there.
#   2  -> out-of-range on a Yes/No item (questionnaire offered only Yes/No)
#   42 -> data-entry glitch on `teacher` (1-5 scale; appears once)
#   3  -> out-of-range on `school` (only Mixed/Single sex offered; appears once)
SENTINEL_ALLOW: dict[str, set] = {c: {0, 9} for c in SPECS}
SENTINEL_ALLOW["teacher"] = {0, 42}
SENTINEL_ALLOW["school"] = {0, 3}
# Yes/No items additionally see a stray "2".
for c in ("insight", "encourag", "discoura", "placemen", "furstudy"):
    SENTINEL_ALLOW[c] |= {2}


def classify_sentinel(raw_code, col: "ColumnToText") -> str:
    """Honest display flavour for a dropped/missing raw value (§3.3)."""
    import math
    if raw_code is None or (isinstance(raw_code, float) and math.isnan(raw_code)):
        return "no answer (system-missing)"
    code = int(raw_code) if float(raw_code).is_integer() else raw_code
    if code == 9:
        return "not applicable (filtered out by a branch)"
    if code == 0:
        return "left blank / no answer"
    return f"out-of-range code {code} (treated as no answer)"


def _clean_question(label: str) -> str:
    """Derive question wording from the embedded variable label (§1.4 light clean).

    The label carries the item number then the question, e.g.
    '1A  I was attracted to engineering/design & technology because of the high
    salary'. Strip the leading item code; fix two depositor typos; keep wording.
    """
    if not label:
        return ""
    # strip a leading item code like "1A", "11K", "6", "14" (+ following spaces)
    q = re.sub(r"^\s*\d+\s*[A-Za-z]?\s+", "", label).strip()
    q = q.replace("challeng of", "challenge of")              # typo in `challeng`
    q = q.replace("satisifaction", "satisfaction")            # typo in Q5 labels
    q = q.replace("important not unimportant", "important nor unimportant")
    return q


# Documented fixes for obvious typos in the embedded VALUE labels (not a
# re-derivation, §1.1 -- the codes/mapping are untouched; only an ungrammatical
# midpoint label is corrected for readability). Applied verbatim, frozen here.
LABEL_FIXES = {
    "neither important not unimportant": "neither important nor unimportant",
}


def load_columns(sav_path: str):
    """Build the list of ColumnToText objects, merging authored specs with the
    embedded value maps + question wording. Returns (cols, meta).
    """
    _, meta = pyreadstat.read_sav(sav_path, metadataonly=True)
    vvl = meta.variable_value_labels
    labels = meta.column_names_to_labels

    cols = []
    for code, spec in SPECS.items():
        raw_map = vvl.get(code, {})
        # coerce float keys (1.0) to int (1) so lookups are clean; fix label typos.
        value_map = {int(k) if float(k).is_integer() else k: LABEL_FIXES.get(v, v)
                     for k, v in raw_map.items()}
        # missing fill: branched batteries default to "Not applicable"; others "No answer".
        fill = "No answer"
        cols.append(ColumnToText(
            name=code,
            short_description=spec.short_description,
            question_text=_clean_question(labels.get(code, "")),
            value_map=value_map,
            missing_value_fill=fill,
            phrasing=phrase_value_only,
            section=spec.section,
            battery=spec.battery,
            battery_stem=spec.battery_stem,
            scale_label=spec.scale_label,
            origin=spec.origin,
            is_verdict_battery=spec.is_verdict_battery,
        ))
    return cols, meta


# Section order for rendering
SECTION_ORDER = [SEC_E, SEC_A, SEC_B, SEC_C, SEC_D]

# Clean topic titles for persona headers ("## <topic>", no "A./B." letter prefix).
SECTION_TOPIC = {
    SEC_E: "Demographics & background",
    SEC_A: "Choosing engineering",
    SEC_B: "Experiences of higher education",
    SEC_C: "Industrial placement",
    SEC_D: "Future in engineering",
}
