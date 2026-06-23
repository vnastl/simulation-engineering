# Persona → simulation tasks: a survey-agnostic playbook

How to turn **personas + the survey's own published analysis** into
**micro→macro simulation tasks**: prompts an LLM can answer, paired with
scoring rubrics and **data-derived answer keys**, so you can measure how
faithfully a model reproduces the surveyed population. Written for an agent
doing this for an arbitrary survey and its paper(s).

**Scope.** This picks up exactly where the persona playbook stops (it
produced the text; this turns the text into tasks). It is about *defining*
the tasks and their answer keys — the prompts, the conditioning, the
rubrics, the frozen estimates. **Running the model and scoring its output is
deliberately the one slot you leave open**, and rendering any of it as HTML
is the trace playbook's job. No survey-specific assumptions: which outcomes
exist, which sub-populations are interesting, and where the "ground truth"
lives all vary, so the method below is about *what to decide and how to keep
it honest*, not fixed tasks to copy.

---

## 0. The mental model

You are building two artifacts, and — as in the persona playbook — they are
separate concerns:

1. **Declarative task definitions.** Per *theme*: the population it is about,
   the **conditioning** set (what the model is shown), the **held-out**
   outcome items (what it must predict), the prompt wording, and the
   **rubric** (the dimensions, and how a free answer is scored). This is the
   survey-specific asset you own — keep it in plain data/objects, like the
   value maps in the persona playbook.

2. **An estimator + validator.** Reads the *raw* data with the same loader
   the persona pipeline uses, computes the per-sub-population **answer keys**,
   **validates your variable definitions against the paper's own published
   numbers first**, then **freezes** the estimates to a reviewable artifact.

Each theme spawns **three task shapes**, and they test different things:

- **MICRO — representational accuracy.** Show one respondent's conditioning
  persona; ask for free prose about a held-out outcome; score the prose.
- **MACRO prose — external + internal consistency.** Ask the same question
  about *two sub-populations*; score with the *same* rubric, comparatively.
  External = vs. the survey; internal = vs. the aggregate of your micro answers.
- **MACRO number — external + internal consistency on the next token.** Ask for the
  explicit percentages (a digit answer / a distribution over categories).
  External = vs. the survey; internal = vs. the aggregate of your micro answers.

The data flow:

```
paper + persona pipeline ──pick──▶ themes (outcome + sub-population split)
raw data ──estimate & VALIDATE──▶ frozen answer keys ──assemble──▶ task defs ──▶ micro / macro-prose / macro-number
            (against the paper's OWN numbers)  (per-group, per-item, +significance)        (model call = the open slot)
```

The hard parts, in order of how much *silent* damage they cause — the ones
that error out you'll fix anyway; these ship wrong and look right:

- **(A) The answer key can be confidently wrong.** If a variable definition
  is off, your "ground truth" is wrong and *everything* graded against it is
  wrong — silently. The defense is to reproduce the paper's own numbers
  before trusting any number the paper doesn't print (§2.1).
- **(B) Leakage makes the micro task trivial.** Show the model anything that
  reveals the held-out outcome and it "predicts" perfectly while measuring
  nothing. Assert against it (§1.3).
- **(C) Spurious precision invents findings.** A sub-population gap reported
  as a *direction* when it is not statistically significant is a fabricated
  result. Gate on a real test (§3.4).
- **(D) Editorialized item wording self-contradicts.** Paraphrasing or
  negating the survey's statements, then tagging them with the *original's*
  answer, produces rubrics that say the opposite of what you mean (§3.2).
- **(E) The study's sample sizes leak into the prompt.** N is a hint the
  model should never get; keep it out of everything model-facing (§4).

---

## 1. Choose what to ask — and what to hold out

### 1.1 Pick an outcome the paper discusses but never tabulates for your split

The point of the exercise is numbers that are **real but not in the paper**.
So inventory how the paper reports things, and pick the gap:

- The paper usually reports marginals along just *one or two* cuts — typically
  a single common demographic (sex, race/ethnicity, age, …) or the whole
  sample — plus a few headline regressions. Pick a **sub-population split it
  does *not* cross-tabulate**: whichever common characteristic the paper left
  un-crossed (it varies by paper — if it tabled everything by sex, split on
  race or age; if by race, split on something else). Its regression tables
  don't count: odds ratios with "coefficients not shown" are not descriptive
  percentages.
- **Confirm the absence**, everywhere: tables, *figure* bars, body text,
  appendices. If the number is in a figure, it's in the paper.
- **Confirm the estimability**: the split must have enough respondents per
  cell to estimate reliably, and the outcome must be a clean variable in the
  raw data. A gap that's real and absent-from-the-paper but only estimable at
  a very low sample size is not worth a task.

A healthy theme: an outcome the paper *discusses* (so the task is grounded in
the literature) whose *sub-population numbers* it never gives (so the task is
non-trivial) and that the raw data *can* deliver (so the answer key is solid).

### 1.2 The three shapes, and what each is for

One theme, three prompts (per IDEAS-style framing):

| shape | input the model sees | output asked for | what it tests |
|---|---|---|---|
| **micro** | one respondent's conditioning persona | free prose about the held-out outcome | representational accuracy of one unit |
| **macro prose** | two sub-population descriptions (by definition, not by size) | free prose comparing them | external consistency (vs. survey) + internal (vs. your micro aggregate) |
| **macro number** | the same two sub-populations | explicit % (digits / a distribution) | external consistency on the next token + internal (vs. your micro aggregate) |

The macro-prose rubric must **reuse the micro rubric's dimensions** (§3.4) —
that overlap is the whole point: it lets you compare an individual-level
elicitation to a population-level one on the same axes.

### 1.3 The conditioning set: apt, leak-free, and distinct across themes

Three decisions, each easy to get subtly wrong:

- **Apt.** Condition on what is *plausibly predictive* of the outcome, not
  reflexively on whatever section sits nearest in the persona. Choose the
  features theory or prior work says should drive *that* outcome; keep the
  cheap, always-relevant background (demographics) and choose the rest
  deliberately.
- **Leak-free.** The held-out outcome — *and anything that reveals it* — must
  not appear in what the model is shown. Compose the conditioning persona
  from an explicit **allow-list of sections**, and **assert** that no held-out
  item is inside a shown section. This is the §2.1-style cheap exhaustive
  check, for tasks: it should come back empty, and that empty result is the
  confirmation. (A near-leak — a variable strongly correlated with the
  outcome but not the outcome — is allowed; that's just a good predictor.)
- **Distinct across themes — because the outcomes are.** Always pick the set
  that best predicts *that theme's* outcome — the *Apt* goal above, aimed high
  every time; this is not a spread from strong to weak predictors. Since the
  **outcomes differ** theme to theme (§1.1), their best predictors differ too,
  so the **non-demographic conditioning comes out different** across the suite
  as a *consequence* — demographics may be the only block shared. Reusing one
  conditioning block (demographics + the same extra section) for every theme is
  asking one task N times, and usually means some theme isn't on its best
  predictors.

State all three choices explicitly per theme; they *are* the task.

---

## 2. The answer key — get the numbers right, then freeze

### 2.1 Validate your variable definitions against the paper *before* trusting your new numbers

This is the single highest-leverage step, and the analog of the persona
playbook's §2.1 reconciliation. Your new cross-tabs are only as trustworthy
as the variable definitions behind them — and a wrong definition fails
silently. So **first reproduce numbers the paper *does* print**:

- Recompute the paper's **sample size(s)** and a handful of its **marginals**
  (a Table-1 row or two, a headline percentage) from the raw data, and print
  them next to the published figures.
- If they match, your at-risk filter, your outcome coding, and your
  missing-value handling are right, and the *new* split inherits that
  credibility. If they don't, fix the definition before computing anything
  the paper can't check.
- **Weighting:** the paper's descriptives are usually survey-weighted; the
  personas (and thus your task population) are usually unweighted individual
  records. Decide which you report — unweighted is design-consistent with the
  personas — and *document it*; it explains the few-point offsets and keeps
  the validation honest rather than alarming.

Treat a mismatch as a stop-and-investigate, exactly like an unexplained value
code in the persona playbook.

### 2.2 Pin the population precisely — it is usually nested

Papers restrict their sample in layers — an eligible group, then a sub-set
meeting some exposure or behavior criterion, then a still narrower sub-set —
and different analyses use different layers. Write **each layer's definition**
down to the predicate, reproduce **each** layer's N (§2.1), and state which
layer each task uses. Describe the population to the reader by this
*definition* — never let its *size* become part of a prompt (§4).

### 2.3 Derive item-level keys from the data, not the documentation

When an outcome is "scored" (a knowledge test, a constructed index), you need
the per-item key (which response is "correct"/counts). **Recover it from the
data, not by hand-reading a PDF** (which the persona playbook warns is
hallucination-prone): brute-force the key that **reconstructs the survey's own
published component score exactly**, and assert zero mismatches over the whole
table. That both *gives* you the key and *proves* it. Where the survey's
derived score doesn't decompose to a fixed key, fall back to the instrument's
stated answers — and flag that item as instrument-keyed, not data-validated.

### 2.4 Freeze the estimates

Sub-population estimates are non-deterministic to *re-derive by hand* and
easy to drift, so treat them like the persona playbook treats LLM passes:
compute once, **freeze to a reviewable artifact** (per group, per rubric item:
the prevalence, the denominator, the significance), commit it as the source of
truth, and have the trace and any scorer *read* it rather than recompute. The
estimator stays runnable, but the frozen file is what the tasks point at.

---

## 3. Rubrics

### 3.1 Multi-dimensional, group→item — not a summary score

Prose is multi-dimensional, so a rubric that collapses an outcome to one
number throws away most of what the prose said. **Hold out every individual
outcome item in the category and score each**, grouped for legibility
(*hybrid groups+items*: a method-knowledge group lists its individual
true/false items; a behavior group lists each method). The micro answer key
is the respondent's *true value per item*; the macro answer key is each
item's *prevalence per sub-population* (§3.4). Keep a single summary % only
for the **number** task — that's the one place a headline belongs.

### 3.2 Verbatim wording; keep four things separate

For any item where a *claim* meets a *truth value*, four facts are distinct
and must stay visibly distinct — conflating any two is the bug:

1. the **statement** (use the survey's *verbatim* wording — never paraphrase
   or negate it),
2. the **respondent's answer** (render it as a reply: *answered "False"*,
   not a bare `False`),
3. the **correct answer**, if you show it (label it as such: *(correct:
   False)*),
4. the derived **verdict** (*knows it / gets it wrong*).

The classic self-own is to *negate the stem but keep the original's tag* — a
statement reworded to its opposite yet still labelled with the un-negated
answer — so the line asserts the reverse of the truth. (Same proposition-vs-
verdict trap the persona playbook flags for rendering; here it bites in the
rubric and the macro answer key too.)

### 3.3 Score prose asymmetrically, by salience

A paragraph won't mention every item, so **score only the items the prose
makes a claim about**, and report **coverage** (claimed ÷ total) separately.
Give each item a *salient* ("pos") state — *uses* the method / *knows* the
fact / *holds* the attitude — and weight a claim by crossing **what the prose
did** with **the truth**:

| prose did ↓ / truth → | salient (pos) | non-salient (neg) |
|---|---|---|
| **asserts the salient state** | **+2** informative hit | −1 false positive |
| **asserts its absence** | −1 denied a real one | +1 stated correct negative |
| **stays silent** | 0 recall miss (↓ coverage) | **+0.25** credit-by-omission |

The asymmetry is the point: **up-weight an asserted true positive** (+2,
double the +1 for a stated true negative) and **down-weight credit won by
silence** (+0.25) — otherwise a paragraph that names the few salient items
banks free "true negatives" for everything it never mentions. Keep the
weights in **one place** so they're tunable.

### 3.4 The macro rubric mirrors the micro one — and is gated on significance

The macro-prose rubric is the *same* group→item table, now with each item's
prevalence in the two sub-populations. Score the model's **direction** claim
("group A higher") — but **only credit it where the gap is statistically
significant** (a real two-sample test: exact tests for sparse proportion
cells, Welch for means; don't hand-roll a normal approximation when a library
is present). A non-significant gap's answer key is "about equal." For the
**number** task, give the *actual* estimates **and a significance flag**, so a
non-significant difference is never read as real. Report honestly: a gap that
doesn't reach significance is reported as not reaching it.

### 3.5 Two kinds of consistency

The macro tasks buy two checks; render what each needs:

- **External consistency** — macro answer vs. the survey's sub-population
  truth (the frozen estimates).
- **Internal consistency** — macro answer vs. the *aggregate of the model's
  own micro answers* over that sub-population. Emit the per-group, per-item
  distribution so this comparison is possible without re-running anything.

---

## 4. Hygiene — the silent-bug guards

- **Never let the study's sample sizes reach the model.** The model-facing
  text is *conditioning persona + question* only. Describe a population by its
  **definition**, never its size; keep N (and per-cell denominators) in
  developer docs and the scorer-only answer-key tables. Verify it: grep the
  rendered task for `N=` and for the known counts; expect zero.
- **Assert no leakage** (§1.3), every build — it's free and it's the thing
  most likely to silently invalidate the micro task.
- **Show, don't run.** If the pipeline doesn't call a model, don't fabricate a
  model answer: render the **answer key** (the held-out ground truth, the
  frozen estimates) and mark the model's output an explicit, labelled slot.
  The task layer is *declarative*; the model call plugs into that slot without
  touching the persona or the estimates.
- **One pass = one concern; freeze.** Validation, estimation, rubric
  definition, and rendering are separate steps over reviewable artifacts —
  exactly as the persona playbook insists. Re-running an estimate against a
  frozen answer key instead of the raw data silently corrupts it.

---

## 5. Checklist for a new survey/paper

1. [ ] **Pick themes**: an outcome the paper *discusses* but whose
       **sub-population cross-tab it never prints**, on a split with adequate
       cell sizes and a clean source variable (§1.1).
2. [ ] **Validate against the paper first**: reproduce its sample N and a few
       marginals from the raw data before trusting any new number; document
       weighting (§2.1). Pin the (nested) population to a predicate (§2.2).
3. [ ] **Per theme, decide conditioning vs. held-out**: pick the conditioning
       set that *best predicts that outcome* (always aim high), and an explicit
       allow-list of shown sections; **assert** no held-out item is shown.
       Because the outcomes differ, the non-demographic conditioning ends up
       differing across the suite (demographics may be the shared base) — don't
       ask one task N times (§1.3).
4. [ ] **Build the rubric multi-dimensionally** (group→item, not a summary
       score); keep statement / answer / correct-answer / verdict separate and
       the wording **verbatim** (§3.1–§3.2).
5. [ ] **Derive scored-item keys from the data** (reconstruct the survey's own
       component score, 0 mismatches); flag any instrument-keyed fallbacks
       (§2.3).
6. [ ] **Define the prose scoring** (salience-weighted, asymmetric, coverage
       reported), with the weights in one place (§3.3).
7. [ ] **Compute & freeze the answer keys** per group/item, with a real
       **significance** test; mirror the rubric into the macro tasks and gate
       direction on significance (§2.4, §3.4).
8. [ ] **Three shapes per theme** (micro / macro-prose / macro-number),
       sharing the rubric dimensions; leave the model call an explicit slot
       (§1.2, §4).
9. [ ] **Hygiene sweep**: no sample sizes in any prompt; no leakage; show
       don't run; estimates frozen and read-only (§4).
