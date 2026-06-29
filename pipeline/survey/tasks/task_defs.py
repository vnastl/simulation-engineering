"""Declarative task definitions (TASK_PLAYBOOK §0, §1) — the survey-specific asset.

This is the plain-data layer the playbook tells you to *own*: per theme, the
population split, the **conditioning** allow-list (what the micro persona shows),
the **held-out** outcome items (what the model must predict), the prompt wording,
and the pointer to the rubric dimensions. No estimates here — those are derived
from the raw data and frozen by `estimate.py`; no rendering here — that is
`build_tasks.py`. Keeping this declarative is the §0 separation of concerns.

Grounding (INSTRUCTIONS step 2 — "grounded in the related papers").
TWO sources matter, and they play different roles:
  * The journal paper in `publications/` — **Powell, Bagilhole & Dainty (2009),
    "How Women Engineers Do and Undo Gender" (Gender, Work & Organization 16(4))**
    — is *qualitative* (women-only interviews) and prints **no survey numbers**.
    It supplies the *themes* and the *sub-population of interest*: it is entirely
    about how women, versus the male majority, experience engineering.
  * The survey's quantitative results were written up in the **ESRC End-of-Award
    Report (RES-000-23-0426)**, embedded in `downloads/q5723uguide.pdf`
    (pp. 23–34). That report DOES print survey marginals, and it names the three
    axes that structure the population: it makes "a significant difference between
    students studying at a pre- and post-1992 **university**" its headline finding,
    repeatedly singles out **discipline** (Objective 4 — disciplinary sub-cultures),
    and states the survey "was distributed to all male and female undergraduates ...
    to allow a comparison between the experiences of men and women students" (**sex**).

EACH THEME SPLITS ON A DIFFERENT STRUCTURAL AXIS (§1.3 — distinct structure per
theme, because the outcomes differ; three views of the *same* cut would not be):
  * Experiences of the engineering degree → **industrial placement** (the study's
    key transitional stage; does going on placement reshape how a student views
    their degree?).
  * Routes into engineering → **university** (the report's headline divide; two
    intakes, different routes in; richest cut — 9/15 influences differ).
  * What matters in a job → **discipline** (job rewards track the field's industry;
    a two-department head-to-head — civil & building vs design & technology).

Each split is one the sources do NOT report for that outcome (§1.1) — verified by
an adversarial disclosure check that read BOTH the paper and the ESRC report,
item by item, with a skeptic stage hunting for any covering statement. The report
tables placement-uptake and job-factors by university, and several outcomes by
department, but never the degree-views by placement, the influence battery by
university, nor the job-factors by discipline. So every answer key is "real but not
in the source". (Sex was the obvious axis but FAILED the check — see the "WHY NOT
SEX" note below.) `estimate.py` still reproduces the report's printed marginals
(jobdecid 87%/93% female; industry 94%) to the decimal as the §2.1 validation —
confirming the coding behind the (split-agnostic) by-group method.

Splits are defined as `Split`/`Group` objects below and attached to each theme;
the estimator, scorers and trace all read `theme.split`, so adding a theme on a new
axis needs no change to them.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# --- the dichotomisation cut, in one place (TASK_PLAYBOOK §3.3 "weights in one
# place"; here the *cut* that defines the salient/"pos" state). Every outcome
# item sits on a 5-point scale whose top two points are the salient endorsement:
# AGREE5 -> agree/strongly agree; IMPORT5 -> important/very important.
POS_CODES = frozenset({4, 5})
POS_CUT_NOTE = ("an item counts as endorsed ('pos') when the respondent answered "
                "4 or 5 on its 5-point scale (agree/strongly agree, or "
                "important/very important)")


# --- the population splits (TASK_PLAYBOOK §1.2, §1.3; §4: describe by definition,
# never by size). EACH THEME SPLITS ON A DIFFERENT AXIS — three structural axes
# the study/report foreground: industrial placement (the key transitional stage),
# pre/post-1992 university, and engineering discipline. Using one axis for all
# themes would give three views of the SAME cut; §1.3 wants the structure distinct
# because the outcomes are.
#
# WHY NOT SEX. Sex was the obvious axis, but an adversarial disclosure check
# against BOTH sources (the Powell 2009 paper AND the ESRC report in the user
# guide) found it CONTAMINATED: the qualitative paper is *about* by-sex differences,
# so it states the directions outright. For the classroom items the report verbatim
# says "Women engineering students overwhelmingly found that ... their gender was
# ... likely to ensure that they received more help ... than their male
# counterparts. The survey showed this..." (female-help direction disclosed) and
# "male and female students found engineering to be competitive, however this
# finding is not conclusive" (the null-by-sex direction disclosed). A task whose
# answer is printed in the source fails §1.1. And there is no *clean* sex theme: the
# only significant by-sex gaps are on gender-loaded items the paper telegraphs,
# while neutral outcomes show no by-sex difference. So sex is dropped.
#
# `definition` strings are MODEL-FACING — they name the population by its character,
# never its N. `codes` is the set of raw .sav codes in each group; the first group
# is the "direction" reference.
@dataclass(frozen=True)
class Group:
    key: str
    codes: frozenset
    label: str
    definition: str            # MODEL-FACING (macro tasks): by definition, never size


@dataclass(frozen=True)
class Split:
    var: str                   # the .sav column the split is on
    name: str                  # human axis name, e.g. "industrial placement"
    groups: tuple              # (Group, Group) — group[0] is the direction reference
    rationale: str = ""        # why this axis fits this theme (developer doc)


SPLIT_PLACEMENT = Split(
    var="placemen", name="industrial placement",
    groups=(
        Group("placement", frozenset({1}), "placement",
              "engineering students who have gone, or intend to go, on an industrial "
              "placement"),
        Group("no_placement", frozenset({0}), "no placement",
              "engineering students who do not go on an industrial placement"),
    ),
    rationale="The industrial placement is the study's KEY transitional stage ('"
              "usually women's first major contact with the engineering sector'); the "
              "whole project compares placement vs non-placement students. Whether a "
              "student goes on placement plausibly reshapes how they view their "
              "degree. The report discusses placement heavily but NEVER breaks down "
              "the Q4 degree-experience items by placement status — verified clean by "
              "the disclosure check.")

SPLIT_UNIVERSITY = Split(
    var="uni", name="university type",
    groups=(
        Group("pre1992", frozenset({1}), "pre-1992 university",
              "students at a pre-1992, traditional research-intensive university "
              "(mostly post-A-level entrants)"),
        Group("post1992", frozenset({2}), "post-1992 university",
              "students at a post-1992, former-polytechnic university with a more "
              "vocational intake (more mature and part-time students)"),
    ),
    rationale="The report's headline finding is the 'significant difference between "
              "students studying at a pre- and post-1992 university'; the two intakes "
              "follow different routes into engineering. The report cross-tabulates "
              "placement and job-factors by university but NEVER the Q1 influence "
              "battery — so the by-university routes-in cut is the gap (§1.1). "
              "Empirically the richest split for this outcome (9/15 items differ).")

# The discipline split is a clean TWO-department head-to-head (NOT one-vs-rest):
# Civil & Building (3) vs Design & Technology (7) — two named, comparably sized
# disciplines that actually differ. Both are ~100 students at the SAME pre-1992
# university (Loughborough), so the contrast is discipline, NOT institution. Every
# other department falls in neither group; crucially the post-1992 'School of
# Technology' (dept 8) is excluded — it is 100% Glamorgan, so any pairing with it
# would secretly be the university split (which routes_in already uses). These are
# the two disciplines the report singles out, at opposite ends of the engineering-
# culture range: construction/site-based vs studio/product design.
#   3 = Civil & Building Engineering  (n=97,  pre-1992 Loughborough)  -> civil
#   7 = Design & Technology           (n=102, pre-1992 Loughborough)  -> design_tech
SPLIT_DISCIPLINE = Split(
    var="dept", name="engineering discipline",
    groups=(
        Group("civil", frozenset({3}), "civil & building engineering",
              "students in the civil & building engineering department "
              "(construction-oriented engineering)"),
        Group("design_tech", frozenset({7}), "design & technology",
              "students in the design & technology department (design- and "
              "product-oriented engineering)"),
    ),
    rationale="A clean two-discipline head-to-head: civil & building (site-based, "
              "location-dependent, company-car construction culture) vs design & "
              "technology (studio / product design). Both ~100 students at the same "
              "pre-1992 university, so the cut is discipline not institution. The report "
              "singles out both disciplines but NEVER splits the Q11 job-factors by "
              "discipline — so the cut is the gap (§1.1). Empirically civil students "
              "rate location, company-car benefits and training higher.")


@dataclass(frozen=True)
class Item:
    """One held-out outcome item = one rubric dimension (TASK_PLAYBOOK §3.1).

    `code` is the .sav column. The *verbatim statement* and *scale* are NOT copied
    here — they are pulled from the same ColumnToText the persona uses
    (build_tasks), so the rubric and the persona can never disagree on wording
    (§3.2 verbatim). `pos_state` is the salience label (§3.3): the short phrase for
    the respondent being in the salient state, used by the prose rubric.
    """
    code: str
    pos_state: str          # e.g. "agrees male students are more confident in class"
    neg_state: str          # e.g. "disagrees / is neutral"


@dataclass(frozen=True)
class Theme:
    key: str
    title: str
    split: Split                         # the population axis for THIS theme (§1.3)
    paper_grounding: str                 # which part of Powell et al. (2009) motivates it
    outcome_group: str                   # human label for the held-out battery
    outcome_items: tuple                 # tuple[Item] — the rubric dimensions
    conditioning: tuple                  # tuple[str] — allow-list of shown item codes (micro persona)
    conditioning_rationale: str          # why this set is *apt* (§1.3)
    micro_prompt: str                    # model-facing; {persona} is filled in
    macro_prose_prompt: str              # model-facing; {A},{B} filled with definitions
    macro_number_prompt: str             # model-facing; {A},{B} filled with definitions

    def holdout_codes(self):
        return [it.code for it in self.outcome_items]


# --------------------------------------------------------------------------
# Shared conditioning blocks (explicit code lists -> auditable for the leak
# assertion in build_tasks; §1.3 "explicit allow-list ... assert no held-out
# item is shown"). DEMOG is the only block shared across themes (§1.3:
# "demographics may be the only block shared"); the rest differ because the
# outcomes differ.
DEMOG = ("gender", "age", "ethnic", "religion", "school", "year", "dept", "uni")

# Q1 influence battery — why the student chose engineering (15 items). The outcome
# of the routes-in theme; reused here as conditioning for the degree-experience
# theme (a different theme, so no within-theme leak).
Q1_INFLUENCES = ("highsal", "interest", "challeng", "special", "mathsci", "knowledg",
                 "family", "hobbies", "gooddeg", "varied", "mother", "father",
                 "careers", "teacher", "nobody")

# course-satisfaction block (Q5).
Q5_SATISFACTION = ("quality", "supplect", "supppers", "groupwk", "teachhrs",
                   "friends", "coursewk", "theory", "practwk", "designwk", "variety")

# decision-context block (insight course + who discouraged) — apt for "what
# routed you in", and distinct items from the Q1 influence battery (a near-leak,
# explicitly allowed by §1.3, not a leak).
DECISION_CONTEXT = ("insight", "encourag", "discoura", "whodisc")

# forward-looking block — future plans, shared by the two future-oriented themes.
FUTURE = ("carpath", "furstudy", "studarea", "workrole", "charship")

# placement block — Q6 + the Q7/Q8 placement-motivation batteries; apt for what a
# student will later value in a job, and distinct from the Q11 job-factor battery.
PLACEMENT = ("placemen",
             "experien", "money", "educatio", "jobprosp", "jobdecid", "industry",
             "perdevel", "unigrade", "apptheor", "finalyr", "indchart",
             "wkexp", "placloca", "breaked", "finuni", "nogain", "noappeal", "noaccept")


def _agree_items(pairs):
    return tuple(Item(c, f"agrees that {p}", "disagrees or is neutral") for c, p in pairs)


def _import_items(pairs):
    return tuple(Item(c, f"rates {p} important", "rates it unimportant or neutral")
                 for c, p in pairs)


# ==========================================================================
# THEME 1 — Experiences of the engineering degree, by industrial placement
# The study's core design contrast is placement vs non-placement (the industrial
# placement is "a key transitional stage ... usually women's first major contact
# with the engineering sector"). Q4 asks all students to rate their degree
# experience. The report discusses placement heavily but NEVER breaks down these
# degree-view items by placement status — verified clean by the disclosure check.
T1 = Theme(
    key="degree_experience",
    title="Experiences of the engineering degree",
    split=SPLIT_PLACEMENT,
    paper_grounding=(
        "Split: industrial placement (gone/intending vs not). The placement is the "
        "study's central transitional stage — the ESRC report (pp.15, 17) targets it as "
        "'usually women's first major contact with the engineering sector and ... a key "
        "transitional stage', and the entire project contrasts placement with "
        "non-placement students (Objectives 1–2). Going on placement plausibly reshapes "
        "how a student views their degree — its difficulty, the relevance of modules, "
        "whether it builds interpersonal skills, whether they are pleased with the "
        "choice. The report discusses placement extensively (reasons for/against, "
        "transition to work) and discusses these Q4 degree-views (curriculum, relevance, "
        "assessment, theory) — but it attributes their *directions* to sex, discipline "
        "and university, NEVER to placement status. The by-placement breakdown of the "
        "degree experience is therefore the gap (§1.1), verified absent from both "
        "sources by an adversarial disclosure check."),
    outcome_group="Experiences of the engineering degree (views of the course)",
    outcome_items=_agree_items([
        ("practica", "the level of practical work on the course is just right"),
        ("curricul", "the engineering curriculum was more difficult than expected"),
        ("pleased", "they are pleased they chose to study engineering"),
        ("relevanc", "it is difficult to understand the relevance of some modules"),
        ("deadline", "they always have competing deadlines"),
        ("assess", "the coursework/exam balance in assessment is just right"),
        ("interper", "the course develops interpersonal skills"),
    ]),
    conditioning=DEMOG + ("placemen",) + Q1_INFLUENCES + Q5_SATISFACTION + FUTURE,
    conditioning_rationale=(
        "Background (including whether they go on placement — the split), why they "
        "chose engineering (Q1 influences), how satisfied they are with the course "
        "(Q5), and where they intend to head. Who the student is, what drew them in and "
        "how they rate the teaching are the apt predictors of how they view the degree; "
        "the Q4 degree-view statements themselves are held out. The Q5 satisfaction "
        "items are a near-leak (correlated with course views, distinct columns) — "
        "allowed by §1.3."),
    micro_prompt=(
        "Below is a profile of one engineering / design & technology student, "
        "covering their background, why they chose engineering, how satisfied they are "
        "with the course, and their future intentions.\n\n"
        "{persona}\n\n"
        "Based only on this profile, predict how this student would rate each of the "
        "following statements about their degree, on a scale from strongly disagree to "
        "strongly agree:\n"
        "  (a) The level of practical work on the course is just right.\n"
        "  (b) The engineering curriculum is more difficult than I expected.\n"
        "  (c) I am pleased I chose to study engineering.\n"
        "  (d) It is difficult to understand the relevance of some modules.\n"
        "  (e) We always have competing deadlines.\n"
        "  (f) The balance between coursework and exams is just right.\n"
        "  (g) The course develops interpersonal skills.\n\n"
        "Write a short paragraph. For each statement, say whether you expect the "
        "student to agree or disagree, and why."),
    macro_prose_prompt=(
        "Consider two populations of engineering / design & technology students:\n"
        "  A: {A}\n  B: {B}\n\n"
        "In a paragraph, compare how these two populations would rate the following "
        "statements about their degree, and say which population is more likely to "
        "agree with each:\n"
        "  (a) The level of practical work on the course is just right.\n"
        "  (b) The engineering curriculum is more difficult than I expected.\n"
        "  (c) I am pleased I chose to study engineering.\n"
        "  (d) It is difficult to understand the relevance of some modules.\n"
        "  (e) We always have competing deadlines.\n"
        "  (f) The balance between coursework and exams is just right.\n"
        "  (g) The course develops interpersonal skills."),
    macro_number_prompt=(
        "Consider two populations of engineering / design & technology students:\n"
        "  A: {A}\n  B: {B}\n\n"
        "For each statement below, estimate the percentage of EACH population who "
        "would agree (answer 'agree' or 'strongly agree' on a 5-point scale). Give "
        "two percentages per statement:\n"
        "  (a) The level of practical work on the course is just right.\n"
        "  (b) The engineering curriculum is more difficult than I expected.\n"
        "  (c) I am pleased I chose to study engineering.\n"
        "  (d) It is difficult to understand the relevance of some modules.\n"
        "  (e) We always have competing deadlines.\n"
        "  (f) The balance between coursework and exams is just right.\n"
        "  (g) The course develops interpersonal skills."),
)

# ==========================================================================
# THEME 2 — Routes into engineering (influences / socialisation)
# Powell et al. (2009) frames women's entry through "early differential
# socialization", "technical hobbies", and "support from family, friends and
# professional engineers"; the 'anti-woman' section ties identity to "technical
# hobbies and the choices they have made during their education". The Q1 battery
# operationalises exactly these influences; the by-sex split is never tabulated.
T2 = Theme(
    key="routes_in",
    title="Routes into engineering",
    split=SPLIT_UNIVERSITY,
    paper_grounding=(
        "Split: university type (pre- vs post-1992). The ESRC report (RES-000-23-0426, "
        "p.27, p.20) makes the pre/post-1992 divide its HEADLINE finding — 'a significant "
        "difference between students studying at a pre- and post-1992 university', the "
        "post-1992 intake being more mature/part-time with 'different priorities and "
        "experiences'. Two intakes follow different ROUTES into engineering: the "
        "traditional pre-1992 cohort (mostly young post-A-level) vs the vocational "
        "post-1992 cohort. The report cross-tabulates placement and job-factors by "
        "university but NEVER the Q1 influence battery, so the by-university breakdown of "
        "*why students chose engineering* is the gap (§1.1). Powell et al. (2009, "
        "pp. 415–421) supply the conceptual frame (entry is shaped by socialisation, "
        "hobbies and encouragement); empirically university is the richest cut here "
        "(9/15 influences differ — pre-1992 students far more drawn by maths/science, "
        "challenge and 'a good degree', post-1992 more likely that 'nobody encouraged' "
        "them)."),
    outcome_group="Influences on the decision to study engineering",
    outcome_items=_agree_items([
        ("highsal", "the high salary attracted them to engineering"),
        ("interest", "the chance to do interesting work attracted them"),
        ("challeng", "wanting the challenge of solving problems attracted them"),
        ("special", "using science and maths without specialising attracted them"),
        ("mathsci", "being good at maths and science at school attracted them"),
        ("knowledg", "they chose engineering with little knowledge of the job"),
        ("family", "a family member in the industry informed the choice"),
        ("hobbies", "their hobbies and interests are of a technical nature"),
        ("gooddeg", "engineering is a good degree to hold regardless"),
        ("varied", "engineering's varied nature attracted them"),
        ("mother", "their mother encouraged them to study engineering"),
        ("father", "their father encouraged them to study engineering"),
        ("careers", "a careers advisor encouraged them"),
        ("teacher", "a school teacher encouraged them"),
        ("nobody", "nobody encouraged the choice"),
    ]),
    conditioning=DEMOG + DECISION_CONTEXT + FUTURE,
    conditioning_rationale=(
        "Background, the decision context (whether they attended an engineering "
        "insight course, whether/who discouraged them), and where they intend to go "
        "next (further study, preferred role, Chartership, specialism). Who the "
        "student is and how engaged they are with the engineering decision predict "
        "what drew them in; the specific Q1 influences are held out. The decision-"
        "context items are distinct columns from the Q1 battery — a correlated "
        "predictor, not the outcome (§1.3)."),
    micro_prompt=(
        "Below is a profile of one engineering / design & technology student, "
        "covering their background, the context of their decision to study "
        "engineering, and their future intentions.\n\n"
        "{persona}\n\n"
        "Based only on this profile, predict what influenced this student's decision "
        "to study engineering. For each of these possible influences, say whether you "
        "expect it applied to them (they would agree) or not, and why: high salary; "
        "interesting work; the challenge of problem-solving; using science & maths "
        "without specialising; being good at maths/science at school; choosing with "
        "little knowledge of the job; a family member in industry; technical hobbies; "
        "it being a good degree to hold; its varied nature; encouragement from mother, "
        "from father, from a careers advisor, from a teacher; or nobody encouraging "
        "them. Write a short paragraph."),
    macro_prose_prompt=(
        "Consider two populations of engineering / design & technology students:\n"
        "  A: {A}\n  B: {B}\n\n"
        "In a paragraph, compare what influenced these two populations' decision to "
        "study engineering, and for each influence say which population is more likely "
        "to agree it applied to them: high salary; interesting work; the challenge of "
        "problem-solving; using science & maths without specialising; being good at "
        "maths/science at school; choosing with little knowledge of the job; a family "
        "member in industry; technical hobbies; it being a good degree to hold; its "
        "varied nature; encouragement from mother, from father, from a careers "
        "advisor, from a teacher; nobody encouraging them."),
    macro_number_prompt=(
        "Consider two populations of engineering / design & technology students:\n"
        "  A: {A}\n  B: {B}\n\n"
        "For each influence below, estimate the percentage of EACH population who "
        "would agree it applied to their decision to study engineering (answer 'agree' "
        "or 'strongly agree' on a 5-point scale). Give two percentages per influence: "
        "high salary; interesting work; the challenge of problem-solving; using "
        "science & maths without specialising; being good at maths/science at school; "
        "choosing with little knowledge of the job; a family member in industry; "
        "technical hobbies; a good degree to hold; varied nature; encouragement from "
        "mother, from father, from a careers advisor, from a teacher; nobody "
        "encouraging them."),
)

# ==========================================================================
# THEME 3 — What matters in a future job (job values)
# Powell et al. (2009) ties women's position to "their relation to the domestic
# sphere", to promotion ("may cost these women in terms of promotion") and to the
# widespread "formal implementation of equality policies". The Q11 battery rates
# exactly these job factors (childcare, flexible working, equal-opportunities,
# promotion, ...); the by-sex breakdown is never tabulated.
T3 = Theme(
    key="job_values",
    title="What matters in a future job",
    split=SPLIT_DISCIPLINE,
    paper_grounding=(
        "Split: engineering discipline — a clean two-department head-to-head, civil & "
        "building engineering vs design & technology (both ~100 students at the same "
        "pre-1992 university, so the cut is discipline not institution). The study's "
        "Objective 4 is explicitly about disciplinary sub-cultures — 'distinct aspects "
        "of different engineering workplaces and cultures' (report p.16) — and the "
        "report singles out BOTH of these disciplines (civil/building on practical-work "
        "satisfaction; design & technology as distinctive on several outcomes). What a "
        "student values in a job tracks the industry their field leads to: civil is the "
        "archetypal site-based, location-dependent, company-car construction culture, "
        "design & technology a studio/product-design culture. The ESRC report (p.27) "
        "cross-tabulates the Q11 job-factors by UNIVERSITY, but NEVER by discipline — so "
        "the by-discipline breakdown is the gap (§1.1, verified by the disclosure "
        "check). Empirically, civil students rate location, company-car benefits and "
        "training markedly higher than design & technology students. (Powell et al. "
        "2009 supply the domestic-sphere / equal-opportunities frame for the battery.)"),
    outcome_group="Importance of factors when choosing a job",
    outcome_items=_import_items([
        ("salary", "salary"),
        ("location", "location"),
        ("workenv", "the work environment"),
        ("people", "the people they work with"),
        ("travel", "opportunities to travel"),
        ("benefits", "benefits such as a company car"),
        ("training", "training opportunities"),
        ("promot", "opportunities for promotion"),
        ("equalopp", "equal-opportunities policies"),
        ("flexible", "opportunities for flexible working"),
        ("childcar", "childcare policies"),
    ]),
    conditioning=DEMOG + FUTURE + PLACEMENT,
    conditioning_rationale=(
        "Background, future plans (further study, preferred role, Chartership, "
        "specialism), and the placement block (whether they went on placement and "
        "what they sought from / avoided about it). What a student wants from "
        "industrial placement and where they intend to head are the apt predictors "
        "of what they will value in a job; the Q11 job-acceptance factors themselves "
        "are held out. Placement motivations are distinct columns from the Q11 "
        "battery — correlated predictors, not the outcome (§1.3)."),
    micro_prompt=(
        "Below is a profile of one engineering / design & technology student, "
        "covering their background, their industrial-placement experience and "
        "motivations, and their future intentions.\n\n"
        "{persona}\n\n"
        "Based only on this profile, predict which factors this student would rate as "
        "important when choosing a job. For each factor, say whether you expect them "
        "to rate it important or not, and why: salary; location; work environment; the "
        "people they work with; opportunities to travel; benefits like a company car; "
        "training opportunities; opportunities for promotion; equal-opportunities "
        "policies; flexible working; childcare policies. Write a short paragraph."),
    macro_prose_prompt=(
        "Consider two populations of engineering / design & technology students:\n"
        "  A: {A}\n  B: {B}\n\n"
        "In a paragraph, compare which job factors these two populations would rate as "
        "important when choosing a job, and for each factor say which population is "
        "more likely to rate it important: salary; location; work environment; the "
        "people they work with; opportunities to travel; benefits like a company car; "
        "training opportunities; opportunities for promotion; equal-opportunities "
        "policies; flexible working; childcare policies."),
    macro_number_prompt=(
        "Consider two populations of engineering / design & technology students:\n"
        "  A: {A}\n  B: {B}\n\n"
        "For each job factor below, estimate the percentage of EACH population who "
        "would rate it important (answer 'important' or 'very important' on a 5-point "
        "scale). Give two percentages per factor: salary; location; work environment; "
        "the people they work with; opportunities to travel; benefits like a company "
        "car; training opportunities; opportunities for promotion; equal-opportunities "
        "policies; flexible working; childcare policies."),
)

THEMES = (T1, T2, T3)
