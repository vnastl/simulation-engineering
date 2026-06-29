# SN 5723 → personas: pipeline

Turns **UK Data Service Study 5723** — *Women Engineering Students' Workplace
Experiences: Impact on Career Intentions, 2004–2005* (Bagilhole, Dainty, Neale,
Powell; ESRC RES‑000‑23‑0426) — into per‑respondent **personas**, following the
three playbooks in this directory.

The study is mixed‑methods. Both arms are processed:

| Arm | Source | n | Playbook | Output |
|---|---|---|---|---|
| **Survey** | email questionnaire (`.sav`/`.dta`/`.tab`) | 804 | `CODEBOOK_TO_TEXT_PLAYBOOK.md` | one persona per respondent (deterministic) |
| **Interviews** | 72 transcripts + 2 focus groups (`.rtf`) | 72 coded | `INTERVIEW_TO_TEXT_PLAYBOOK.md` | one coded persona per unit (LLM‑coded + verified) |
| **Trace** | one record of each | — | `TRACE_PLAYBOOK.md` | `outputs/trace/trace.html` |

## Which file is what (INSTRUCTIONS.md step 1)

Each `M_5723*.zip` is the **same survey** in a different format, bundled with the
**same documentation** and the **same qualitative corpus**:

- **Raw survey data**: `women_engineering_students_workplace_experiences.sav`
  (SPSS — used here, richest embedded metadata), `.dta` (Stata), `.tab` (tab).
  804 rows × 86 variables. *(The ESRC report cites "89 variables": the deposited
  86 = ID + the 85 questionnaire items, matching the instrument exactly; the
  3-variable difference is the personal/identifying fields the questionnaire
  collected but the archive removed for anonymity — the prize-draw contact details
  and the free-text "additional comments" box, which the report states were
  "separated" and "removed ... immediately to ensure anonymity". None affect any
  answer key.)*
- **Codebook**: the value maps + variable labels live as **embedded metadata
  inside the `.sav`** (authoritative). `…_UKDA_Data_Dictionary.rtf` is a printed
  dump of exactly that metadata; `q5723uguide.pdf` is the **user guide** holding
  the **questionnaire instrument** + the four interview guides; `q5723ulist.*` is
  a variable list. We take value maps from the `.sav`, never re‑typed from a PDF
  (CODEBOOK §1.1).
- **Interviews**: `SN5723int01–72.rtf` (transcripts), `SN5723fg01–02.rtf` (focus
  groups).

## Survey arm (deterministic)

`pipeline/survey/`

- `column_to_text.py` — the owned `ColumnToText` renderer (§4.1).
- `schema.py` — the lookup table as data: authored short descriptions + section/
  battery grouping + missing semantics; value maps & question wording loaded from
  the `.sav` (§1.1). Frozen sentinel allow‑list (§2.2).
- `clean_data.py` — preserving load, round‑trip missing check (§3.2), reconcile
  `observed − listed` against the allow‑list (asserts; §2.1/§2.2), sentinels→NaN.
- `build_personas.py` — sectioned, present‑only composer (§4.1); 804 personas.
- `validate.py` — diff every categorical cell vs pyreadstat's native decode
  (§6 — confirms plumbing, not meaning, since both read the same embedded labels).

**Sentinels (the crux, §3).** No SPSS user‑missing ranges are declared, so
missingness is decided **per (column, code) from the label**: any code without a
value label is missing. Three flavours, kept distinct for honest display:
`0` = left blank, `9` = not applicable (branch filter — e.g. Q7 reasons‑for is
N/A for non‑placement students), stray `2`/`42`/`3` = out‑of‑range. `9` is a
*real* "don't know" on `carpath`, so the rule is genuinely per‑variable.

Run: `cd pipeline/survey && python3 build_personas.py && python3 validate.py`

## Interview arm (LLM‑coded into the survey schema)

`pipeline/interviews/`

1. `extract.py` — RTF → text preserving `Interviewer:`/`Subject:` turns; detects
   three formats (tagged / alternating / interviewer‑notes). 67 verbatim
   interviews, 5 notes‑based (non‑verbatim), 2 focus groups (supporting‑only).
2. `registry.py` — construct‑level linkage (no survey join); free metadata
   (`gender=female`); addressability tiers + recurring‑question themes from the
   guides (§3,§4,§7).
3. `make_coding_brief.py` — the survey schema as a coder‑facing brief (allowed
   values per variable; `unaddressed` variables omitted).
4. `wf_code.js` (Workflow) — one coder agent per unit → `coding/raw/<u>.json`
   (codes + verbatim Subject‑turn evidence + confidence + skip reasons + themes).
5. `quote_check.py` — **deterministic** quote‑presence gate, run FIRST (§5.1):
   canonicalise both sides, drop quotes not found or interviewer‑planted.
6. `wf_verify.js` (Workflow) — adversarial re‑read (drop/correct/downgrade) +
   blind second pass on low‑confidence fields (§5.1, §5.2).
7. `synthesize.py` — merge the passes (§5.2/§5.5), render plain + enriched
   personas through the **same** `ColumnToText`, thematic prose, and reconcile the
   coded distribution vs the survey, elicitation‑matched (§5.3, §8).

**Trust.** Every prose code carries a verbatim Subject‑turn quote, a confidence,
and a verification status. Agent‑vs‑agent agreement is *reproducibility*, not
accuracy; aggregate interview marginals are volunteer‑biased and are reported as
such, never as prevalence (§5.3, §8). A blind human spot‑check remains the only
calibration of accuracy and is left as the documented next step.

## Task layer (micro→macro simulation tasks)

`pipeline/survey/tasks/` — turns the personas into LLM **simulation tasks** with
scoring rubrics and **data-derived answer keys**, per `TASK_PLAYBOOK.md`. Two
sources ground it: the journal paper (Powell, Bagilhole & Dainty 2009, *How Women
Engineers Do and Undo Gender*) is **qualitative** (women-only interviews, no survey
numbers) and supplies the themes; the survey's quantitative write-up is the **ESRC
End-of-Award Report (RES-000-23-0426)** embedded in `downloads/q5723uguide.pdf`
(pp. 23–34). The report states the survey "was distributed to all male and female
undergraduates ... to allow a comparison between the experiences of men and women
students". Each theme splits on a DIFFERENT structural axis (§1.3 — three views of
the *same* cut would not be), and crucially **each split is one the sources do NOT
report for that outcome (§1.1)** — verified by an adversarial **disclosure check**
that read both the paper and the full report, item by item, with a skeptic stage
hunting for any covering statement. **Sex was dropped**: the check found it
contaminated — the qualitative paper is *about* by-sex differences and states them
outright (e.g. the report verbatim: women "received more help ... than their male
counterparts. The survey showed this"; competitiveness "not conclusive" by sex), and
there is no clean sex theme (significant by-sex gaps are all on items the paper
telegraphs). `estimate.py` reproduces the report's printed marginals (jobdecid 87% /
93% female, industry 94%) to the decimal as the §2.1 validation.

Three themes, each holding out a battery the source discusses, splitting on a
distinct axis whose **direction is not in the sources**, conditioning on a distinct
apt set (§1.3):

| theme | split axis | held-out outcome | conditioning (micro persona) | signal |
|---|---|---|---|---|
| **Experiences of the degree** | **industrial placement** (gone/intending vs not) | Q4 degree-views (practical work, difficulty, relevance, deadlines, pleased, interpersonal skills) | demographics + Q1 influences + course satisfaction + future plans | **5/7** differ — placement students more pleased & develop interpersonal skills; non-placement find it harder / less relevant |
| **Routes into engineering** | **university** (pre/post-1992) | Q1 influences battery (15 items) | demographics + decision context + future intentions | **9/15** differ — pre-1992 drawn by maths/science/challenge; post-1992 "nobody encouraged" |
| **What matters in a future job** | **discipline** (civil & building vs design & technology — a 2-department head-to-head, both pre-1992) | Q11 job-factor battery (11 items) | demographics + future plans + placement block | **3/11** — civil rate location, company-car benefits & training higher (site-based construction rewards) |

- `task_defs.py` — the owned declarative asset: the per-theme `Split`/`Group`
  objects, the held-out items
  (with salient/"pos" states), the conditioning allow-lists, and the model-facing
  prompts. Three shapes per theme (§1.2): **micro** (one respondent's persona →
  free prose), **macro-prose** (compare the two populations), **macro-number**
  (explicit %s).
- `estimate.py` — estimator + validator (§2). Reproduces N=804 and each theme's
  split-group denominators, and reproduces the ESRC report's printed marginals as
  the §2.1 reconciliation (coding also validated upstream by `validate.py`). Per
  item, per group (on the theme's split axis): prevalence (% answered 4–5), the
  frozen **Fisher-exact** two-sided significance + flag, and `keyed_direction`
  (gated) + `raw_direction`. Reads `theme.split`, so it is split-agnostic. Freezes
  `answer_keys.json` + `micro_keys.json`.
- `weighted_estimates.py` → `estimate_weights.R` — the design-based-variance
  **language boundary** the playbook (§2.4) names. The study ships **no survey
  weight / stratum / PSU** (asserted here, so a re-export that added one fails
  loudly), so the design is SRS: weighted == unweighted (proven — `svymean`
  reproduces the unweighted prevalence), n_eff = (Σw)²/Σw² == n, and Fisher exact
  is the design-exact test (valid for the sparse cells, §3.4). R `survey::svyglm`
  Wald is computed as the **design-based cross-check** (agrees with Fisher's
  significant/not verdict on **29/29** items) and the playbook's **rescale sanity
  check** runs (survey p invariant under ×7; a frequency-weight test's p collapses
  5e-9→1e-53). Frozen to `weighting.json`. *(Needs `Rscript` + the `survey`
  package; falls back to recording the cross-check as unavailable, Fisher still
  frozen.)*
- `rubric.py` — the scorers (§3): micro prose is **salience-weighted &
  asymmetric** (weights in one place); macro prose credits a **direction** only
  where the gap is **significant** (§3.4 — a non-significant gap is keyed "about
  equal", so no fabricated direction); macro number is an error metric. Runnable,
  but the model call is the **one open slot** (§4 "show, don't run") — nothing
  fabricates a model answer.
- `build_tasks.py` — assembles the three shapes, renders the micro conditioning
  view through the **real** persona composer (restricted to the allow-list, record
  ID stripped), and runs two guards that must come back empty every build:
  **leak** (held-out ∩ conditioning == ∅) and **sample-size** (no study/subgroup
  count, no `N=`, in any model-facing string). Writes `tasks.json` + `cards/*.md`.

Run: `cd pipeline/survey/tasks && python3 estimate.py && python3 build_tasks.py`

## Outputs (`outputs/`)

```
survey/personas/persona_NNN.txt   804 survey personas
survey/personas.jsonl             machine artifact (+ provenance)
survey/{clean_survey,raw_codes}.csv, reconciliation.json
survey/tasks/answer_keys.json     frozen per-group estimates + significance (scorer truth)
survey/tasks/weighting.json       design-based variance provenance + rescale sanity check
survey/tasks/micro_keys.json      per-respondent held-out truth (compact)
survey/tasks/tasks.json           3 themes × 3 shapes: model-facing prompts + answer keys
survey/tasks/cards/<theme>.md     human-readable task cards
interviews/personas_plain/<u>.txt        coded personas (survey-comparable)
interviews/personas_enriched/<u>.md      + quote + confidence/verification
interviews/thematic_prose/<u>.md         full verbatim answer per theme
interviews/coded_records.jsonl, coding/{raw,checked,verify,final}/
interviews/reconciliation_vs_survey.json
trace/trace.html                  single-record trace, both arms, all four stages
```
