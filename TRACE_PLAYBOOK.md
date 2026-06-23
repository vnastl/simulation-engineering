# Record → trace HTML: a survey-agnostic playbook

How to walk **one record** through the pipeline and render every stage —
its variables, the steps in between, the persona, and the task — as a
**single self-contained HTML file** a reader can open and follow on one
concrete example (mirrored to stdout as plain text). Written for an agent
doing this for an arbitrary survey and pipeline.

**Scope.** This is only about *showing* the pipeline on one record,
read-only: every value displayed comes from the same functions the real
run calls, sliced to a single unit — the trace re-implements no logic and
changes no data. No survey-specific assumptions either: what counts as a
"record" (a respondent, a row, an entity), the column-code formats, the
value schemes, and which "stages" exist all vary, so the sections below
are about *what to render and why*, not fixed names to copy.

## Ground rules

- **Read-only.** Every number, string, and transformation shown must come from
  the *same* functions the real run calls — load the same config, the same
  helpers, the same transforms, then slice to one record. No re-implementing
  logic in the trace; if a value appears here it should be traceable to a real
  call.
- **One file, no external assets.** Inline the CSS. Open it from a file:// path
  with no network.
- **Pick one record, say why.** Default to an interesting one (e.g. the largest
  change between input and outcome); allow an override flag to pin a specific
  id. State the selection rule and the id at the top.
- **Degrade gracefully.** If an input (a data mount, a cache) is missing, render
  the stage anyway with a clearly-labelled placeholder + a warning box, so the
  structure is always visible.

## Sections, in this order

> **Two arms in one trace → organise section-major, not arm-major.** When the
> pipeline has two arms that share a schema (e.g. a survey arm and a transcript
> arm; INTERVIEW playbook §8), make each *stage* a joint top-level heading
> (Variables, Intermediate, Persona, Task) with the two arms as panels *within*
> it — not two independent columns each running 1→4. The reason to co-locate the
> arms is to compare the **same stage** across them; arm-major hides exactly that.
> An asymmetric stage (e.g. the transcript arm's thematic-prose stage, which the
> survey arm lacks) lives inside that arm's panel for the relevant section.

### 1. Variables
The picked record's **raw input fields**, as a `variable → value` table. Show
the values verbatim, before any cleaning or mapping. Include a short header
block naming the run config (dataset, unit, target/outcome, key parameters).
When a variable carries **both** a preserved question wording and a derived short
description (codebook playbook §1.4), show **both** as separate columns — they are
different fields, and collapsing them into one (rendering only the noun phrase)
hides what was actually asked.

### 2. Intermediate steps
The **transformations between raw input and the model-facing representation**,
one stage per heading, each showing its actual input and output for this record.
Show the arithmetic / mapping explicitly (e.g. raw value → cleaned → normalised
→ derived quantity), not just the final number. One subsection per stage so a
reader can follow the chain end-to-end.

### 3. Persona
The **human-readable profile text composed from the variables** — i.e. exactly
what a model would be shown, rendered by the real composer function. Show it as
a text block. Note which raw fields map into it and which are dropped
(unmapped / missing / refused), so §3 is clearly derived from §1.

### 4. Task (prompting)
How the persona + intermediate quantities get assembled into a **task / prompt**.
If the pipeline has a task layer (see TASK_PLAYBOOK.md), render its *real*
artifacts for this record: the **conditioning view** the model is shown, the
**prompt(s)**, the **rubric**, and the frozen **answer key** — with only the parts
the pipeline doesn't produce (typically the model's own answer and its score) left
as a clearly-marked slot. Where a task is **not yet designed**, render a labelled
**DRAFT placeholder box** instead (a slot, not invented text). Either way the
section is extensible: new task variants get added here without touching §1–§3.

Two things to keep honest — §4 is where it is most tempting to fabricate:

- **Show, don't run.** If the pipeline does not call a model, do not invent a
  model answer. Render the answer key (the held-out ground truth) and mark the
  model's output explicitly *not run*. *(A short verdict/output row is fine **only
  if** the pipeline really produces one.)*
- **Don't leak.** The model-facing text (conditioning view + prompt) must contain
  nothing the task holds out, and **no sample sizes**. Keep answer-key-only
  material — estimates, denominators, correct answers — visually separate from the
  prompt, so a reader can't mistake the scorer's view for the model's.

### When the record is a transcript (interview / open-ended)

The same four stages apply, but §1 is the raw transcript and §2 is prose→codes.
Insert a stage between them — the **full thematic prose**: the complete answer to
each recurring question (the whole answer *after probing*), shown verbatim, each
labelled with the recurring question and the **subset of coded variables** it
informs. It is what §2's codes are drawn from, so a reader sees the full text
behind each coded snippet — and that one theme's answer routinely backs several
codes at once, sometimes carrying rich material no code captures. Put each theme's
answer in a collapsible `<details>` (they are long). See
`INTERVIEW_TO_TEXT_PLAYBOOK.md` §7.

## Style

- Plain semantic HTML + a small inline `<style>`. Headings numbered as above,
  `key → value` tables for variables, `<pre>` blocks for persona/prompt text,
  collapsible `<details>` for anything long.
- Distinct, labelled callout boxes for **warnings** (missing input) and
  **DRAFT** (not-yet-designed slots) so a reader instantly sees what is real vs.
  placeholder.
- Self-documenting header: which script generated it, which record, and the
  selection rule.
- **Header naming.** Open with an `<h1>` and a one-line subtitle in this exact
  shape:
  - `<study short name> pipeline trace — one respondent`
  - `<full study title> (<nickname / archive handle>) — <pipeline description>`

  The H1 carries the short or familiar name; the subtitle gives the full formal
  title, the study's nickname or archive handle in parentheses, then a dash-led
  description of what the pipeline does. Example: *Fog Zone pipeline trace — one
  respondent* / *2009 Survey of Unmarried Young Adults' Contraceptive Knowledge &
  Practices ("The Fog Zone") — codebook→persona pipeline + micro→macro task
  layer*.

### Colors

Light, muted, classic palette — soft off-white background, cream/sand surfaces,
deep-navy text, camel borders and accents, with dusty-mauve and slate for
secondary tones. Nothing saturated or bright.

```
  --bg:#fbfaf5; --surface:#f6f1e8; --surface2:#faf6ef; --ink:#22304a; --muted:#5e6b7a;
  --camel:#b89b72; --camel-soft:#e0d2b8; --mauve:#9b7e8e; --slate:#6d7a89;
  --good:#5f7355; --warn:#9a6b4f;
```