# Women Engineering Students' Workplace Experiences — survey → persona → simulation tasks

**Survey.** Women Engineering Students' Workplace
Experiences: Impact on Career Intentions, 2004–2005, Bagilhole, Dainty, Neale, Powell; ESRC RES‑000‑23‑0426.

**Database.** UK Data Service Study [5723](https://datacatalogue.ukdataservice.ac.uk/studies/study/5723#details)
on the [UK Data Service](https://datacatalogue.ukdataservice.ac.uk/).

**Data.** A SPSS file `.sav` (used here), `.dta` (Stata), `.tab` (tab) file 804 respondents × 86 variables, alongside a PDF document giving the codebook and questionnaire. Interviews transcripts as `.rtf`, alongside a PDF guide for the interviews.

This is a **prototype** for **raw survey data + a codebook → a persona → micro/macro simulation tasks**. A persona is a natural-language profile of one respondent answers; the tasks ask a model to give:
- **micro prose** — free-text prediction for one respondent, scored against a rubric;
- **macro prose** — free-text prediction across two sub-populations, scored against a rubric;
- **macro numerics** — explicit percentages, scored against data-derived, **survey-weighted** estimates.

**Overview.** Open [`outputs/trace/trace.html`](outputs/trace/trace.html) for a walk-through of the current status, including the task layer on one record (§4).

**Code.** The preprocessing pipeline (codebook→persona, task building, rendering) lives in
[`pipeline/`](pipeline/).

For the full pipeline, file layout, and how to run it, see [`AGENT_README.md`](AGENT_README.md).
