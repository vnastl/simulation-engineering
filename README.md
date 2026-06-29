# Women Engineering Students' Workplace Experiences — survey → persona → simulation tasks

**Survey.** Women Engineering Students' Workplace
Experiences: Impact on Career Intentions, 2004–2005, Bagilhole, Dainty, Neale, Powell; ESRC RES‑000‑23‑0426.

**Database.** UK Data Service Study [5723](https://datacatalogue.ukdataservice.ac.uk/studies/study/5723#details)
on the [UK Data Service](https://datacatalogue.ukdataservice.ac.uk/).

**Data.** A SPSS file `.sav` (used here), `.dta` (Stata), `.tab` (tab) file 804 respondents × 86 variables, alongside a PDF document giving the codebook and questionnaire. Interviews transcripts as `.rtf`, alongside a PDF guide for the interviews.

This is a **prototype** for **raw survey data + a codebook → a persona → micro/macro simulation tasks** (prompts + scoring rubrics + data-derived answer keys, grounded in the related paper). The three task themes each split the population on a **different** structural axis — **industrial placement**, **university type** (pre/post‑1992), and **engineering discipline** — each chosen so the source *discusses* the outcome but never reports its direction by that split (verified by an adversarial disclosure check; sex was dropped because the paper states the by‑sex directions outright). The answer keys are validated against the survey's own [ESRC End-of-Award Report](downloads/q5723uguide.pdf) (embedded in the user guide, RES‑000‑23‑0426).

**Tasks.** [`TASK.md`](TASK.md) is the consolidated task spec — per theme: population (split), conditioning, prose rubric, and the number-task headline %s. (Generated from the frozen answer keys.)

**Overview.** Open [`outputs/trace/trace.html`](outputs/trace/trace.html) for a walk-through of the current status, including the task layer on one record (§4).

**Code.** The preprocessing pipeline (codebook→persona, task building, rendering) lives in
[`pipeline/`](pipeline/).

For the full pipeline, file layout, and how to run it, see [`AGENT_README.md`](AGENT_README.md).
