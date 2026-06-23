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
  804 rows × 86 variables.
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

## Outputs (`outputs/`)

```
survey/personas/persona_NNN.txt   804 survey personas
survey/personas.jsonl             machine artifact (+ provenance)
survey/{clean_survey,raw_codes}.csv, reconciliation.json
interviews/personas_plain/<u>.txt        coded personas (survey-comparable)
interviews/personas_enriched/<u>.md      + quote + confidence/verification
interviews/thematic_prose/<u>.md         full verbatim answer per theme
interviews/coded_records.jsonl, coding/{raw,checked,verify,final}/
interviews/reconciliation_vs_survey.json
trace/trace.html                  single-record trace, both arms
```
