# Codebook → persona text: a survey-agnostic playbook

How to go from **raw survey data + its documentation** to a **persona**: a
faithful natural-language description of one respondent, assembled from
their answers, that an LLM can read. Written for an agent doing this for
an arbitrary survey.

**Scope.** This is only about producing the *text*. What you do with the
persona afterwards — ask the model for a prediction, have it write prose,
condition a simulation — is out of scope and deliberately not assumed
here. No survey-specific assumptions either: column-code formats,
sentinel conventions, value schemes, and even *where the codebook lives*
all vary, so the method below is about *what to look for and decide*, not
fixed patterns to copy.

---

## 0. The mental model

You are building two artifacts, and they are separate concerns — keep
them separate:

1. **A per-variable text renderer.** For each column, an object that
   knows how to turn one respondent's raw value (a code, a number, a
   free-text string, a missing) into a phrase (`"Employed full time"`,
   `"42 years old"`, `"Prefer not to say"`). Call it a `ColumnToText`.
   It carries **both** a compact `short_description` *and* the
   **preserved (cleaned) question text** — see §1.4 and §4.1.

2. **A data-cleaning layer.** Loads the raw file, selects the columns you
   want in the persona, applies missing-value policy, and writes a clean
   table the renderer runs over. (If a downstream task needs extras — an
   outcome column, survey weights — add them here, but that is
   task-specific and out of scope.)

The data flow:

```
documentation ───assemble──▶ variable lookup table ──refine──▶ ColumnToText defs (one per column)
(embedded metadata and/or     (code, description,                │
 PDF codebook, + instrument)   question, value labels)           │
raw data ─────────clean─────▶ clean table (sentinels→NaN, ──────┘──render──▶ "The age is: 42 years old. The ..."
                               columns selected)                            (one persona per respondent)
```

The hard parts, roughly in order of how much *silent* damage they cause —
the ones that error out you'll fix anyway; these are the ones that ship
wrong and look right:

- **(A) Knowing where each piece of truth lives.** You need three
  different things per variable — *descriptions*, *value maps*, and
  *question wording* — and they usually live in different places. The
  obvious source, a PDF codebook, is frequently the *worst* place to get
  value maps. Decide your sources before you write a parser (§1.1).
- **(B) Missing values are the crux.** "No answer" codes are inconsistent
  *within a single survey*, your data loader may silently destroy the
  distinctions between them before you ever touch the data, and they have
  to be handled at two separate layers. This is the single largest source
  of silent bugs (§3).
- **(C) Codebooks under-specify the values a variable can take**, in more
  ways than you'll anticipate. The defense is reconciling the codebook
  against the actual data, on every column (§2.1).
- **(D) If you must parse a PDF codebook, it's written for humans
  skimming, not for parsers** — and LLMs asked to read it fabricate
  fluently (§1.3, §1.5).

---

## 1. Sources → a lookup table

### 1.1 First decide where each piece of truth lives

A persona needs three pieces of per-variable knowledge, and they rarely
all come from one file. Inventory what you have *before* writing any
parser, and pick a source for each:

- **Value maps** (code → label, or how to format a number) — the
  expensive, error-prone part. **Look in the data file first.**
  Statistical formats — Stata `.dta`, SPSS `.sav`, SAS — embed variable
  labels and value labels as machine-readable metadata, and a "codebook
  PDF" is very often just a *printed dump of exactly that metadata*. When
  the embedded metadata exists it is authoritative and already
  structured: use it, and **do not re-derive value codes from the PDF.**
  PDF value-code parsing is slow, and LLM parsing of it is
  hallucination-prone — you'd be reconstructing, with errors, data you
  already have cleanly.
- **Short descriptions** (what the variable *measures*) — usually the
  embedded variable label or the codebook's label column. Terse and
  survey-ese; you'll clean it later (§1.5).
- **Question wording** (how it was actually asked) — the piece the data
  file usually *lacks*. It typically lives in a **separate instrument /
  questionnaire document**, not the codebook. Preserve it: the exact
  wording disambiguates what a variable measures far better than a terse
  label, and an LLM reads the question+answer form more reliably (§1.4).
- **Missing-value definitions** (which codes count as "no answer") — the
  statistical formats above usually declare these *per variable* as
  structured metadata too (SPSS `missing_ranges`, Stata extended missings
  `.a`–`.z`, SAS special missings), not as label strings. When present they
  are the cleanest source for the per-(column, code) missing set (§3.1) —
  inventory them in the same pass as the value maps, and confirm they survive
  the read (§3.2).

So the first task is not "parse the PDF." It is: **inventory your inputs
and map each piece of needed knowledge to its best source.** A common,
healthy outcome: value maps + descriptions come from the embedded
metadata; question wording comes from the questionnaire document; the
codebook PDF is used only as a human-readable cross-check, never parsed
for codes.

### 1.2 The intermediate artifact: a flat lookup table

Whatever the sources, converge them into one **lookup table** before
writing any renderer — one row per variable:

| column code | short_description | question_text | value_labels |
|---|---|---|---|

This table is reviewable, diffable, and re-generatable. Keep this seam:
assemble the table from your sources, then turn the table into code as a
separate pass. It is also where you record, per variable, the transform
type (§2.3) and the missing-value codes you detect (§3.1).

### 1.3 The PDF-parsing path (only if there is no embedded metadata)

If — and only if — you have no structured metadata and must recover value
maps from a PDF codebook, treat the entry as a small **state machine of
line types**, not a regular grammar. Find the survey's **variable-code
pattern first** — it's the one stable anchor on the page (some prefix +
digits, a running ID, etc.). Then classify each line relative to it:

- **Variable header** — the code, often with an inline label.
- **Label** — frequently ALL-CAPS, and it may sit on lines *before or
  after* the code. Collect a small window around the header.
- **Question text** — mixed-case prose, often introduced by `Question:`.
  Accumulate until a section marker.
- **Section / stop markers** — `Value Labels`, `Universe`,
  `Randomization`, etc. These bound the question and start the
  value-label block.
- **Value-label rows** — `<code> <label>` pairs.
- **Noise** — page headers/footers, field-boundary rulers.

The exact tokens differ per codebook; discover them by reading a few
pages, not by assuming. The PDF gotchas to expect, and the fixes:

- **Page headers/footers leak into labels.** A running header (often
  ALL-CAPS, next to a variable) gets swept into the label. Fix: an
  explicit reject-regex for the header/footer patterns, applied *before*
  label assembly, plus a contamination check that drops any label still
  containing those tokens.
- **Labels are not human-readable as-is.** Expect ALL-CAPS, truncation,
  survey shorthand, revision markers (`(r)`, `[revised]`), status
  prefixes. Strip the notation, then Title-Case (keeping
  articles/prepositions lowercase). Reject anything too short or clearly
  internal.
- **Label vs. question confusion.** A "label" that starts with an
  interrogative (*What/How/Do/Would…*) is really question text — reject
  it as a label. Conversely you can *derive* a description by stripping
  interrogative lead-ins from the question, applied iteratively.
- **Line-break artifacts.** De-hyphenate (`self-\nplacement`) and join
  wrapped lines before classifying.
- **Duplicate entries.** The same code can appear on several pages. First
  occurrence wins; later ones only *fill gaps*, never overwrite.
- **Always have a priority order with a fallback** so you never emit
  empty: cleaned label (if sane length, not a question, not technical) →
  question-derived phrase → whatever description already existed.

### 1.4 Preserve the question wording (and reassemble it for grids)

The `short_description` noun phrase is lossy: the exact question wording —
response framing, time window, who/what it is about — often disambiguates
what a variable actually measures, and an LLM reads the *question +
answer* form more reliably than a terse label. So capture the question
text into its **own column** in the lookup table and carry it onto the
renderer object (§4.1) — a separate field from `short_description`, not a
replacement for it. Two things make this trickier than it looks:

- **It usually comes from the instrument, not the codebook**, so you have
  to align instrument item numbers (`Q11a`, `S5`) to data column codes
  (`q11a`, `s5a`). Mostly mechanical, but expect mismatches: derived /
  recoded variables have no instrument item (leave their question empty
  and fall back to the description), and screener items may map to
  recoded demographics. And when the stored variable label *contradicts* the
  instrument item — the instrument asked "which course", the column was
  recoded into "which institution" — trust the **stored label** for what the
  variable measures: it describes what is actually in the column, while the
  instrument describes what was *asked*, which may not be what was *kept*. Use
  the instrument for question wording, but don't let it override the column.
- **Grid / matrix questions** (one stem, many sub-items a, b, c…) must be
  reassembled so each sub-item's question stands alone: merge the stem
  into each sub-item. Naive extraction either drops the stem (losing the
  meaning — a bare sub-item like "*…how likely is it?*" is useless without
  its stem "*If you did `<X>`…*") or repeats it verbatim across every
  sub-item (bloating the persona). Decide deliberately which you want:
  faithful repetition, or the stem stated once per block.

Clean the question text *lightly* — convert from ALL-CAPS, expand survey
shorthand, join wrapped lines, drop interviewer/programming notes and
`[fills]` — but **keep the wording and meaning intact.** This is a light
cleanup, not the aggressive noun-phrase compression you apply to
descriptions.

### 1.5 LLM passes: reformulate descriptions; verify extractions against source

Two distinct LLM uses, each kept as its own pass (one concern per pass):

- **Reformulate descriptions.** After assembly, many descriptions still
  read like survey-ese (`Q07a: BC know: no sex`). Batch a few dozen at a
  time as a JSON array `[{"id","description"}]`, return a JSON array
  (cheap; keeps ids aligned). Tight prompt: *"concise noun phrase, a few
  words, lowercase; describe what the column measures, not the survey
  wording; strip colon-separated question fragments; keep already-good
  ones unchanged; return ONLY the JSON array."* If you also LLM-clean the
  **question text**, do it as a *separate* pass with a different prompt:
  *"fix casing and expand shorthand, but preserve wording and meaning
  verbatim; do not summarize or shorten."* Never let the noun-phrase pass
  touch the question field, or you'll compress away the detail you kept
  it for. (You don't have to *batch* this: when **you** are the agent and have
  the whole survey, instrument, and value labels in context, author each
  concise noun phrase directly in source as you build the lookup table — no
  id-misalignment, no blind hallucination, and the non-determinism disappears.
  Same freeze discipline; only the *authoring* step differs. Prefer inline for
  a few hundred variables you can hold in context; reach for the batch pass
  when the count makes per-variable attention impractical.)
- **Extract / parse hard entries — and verify against the source.** When
  regex can't recover a usable label/values for a messy entry, or when
  you're pulling question wording out of an awkward (e.g. two-column)
  instrument PDF, hand the raw text block to an LLM for structured JSON.
  **This is where you must add a verification pass.** LLM extraction of
  wording does not fail loudly — it fabricates *fluently*: it will invent
  a plausible answer-stem, or quietly drop a conditional qualifier, and
  the output looks confident and correct. A cheap second pass that
  re-reads the *same source* and checks each extracted field for invented
  or dropped content is **not optional** — it is the difference between
  "looks right" and "is right." Keep LLM parsing a *targeted fallback*
  for entries that fail validation, not the primary path for whole
  codebooks.

**LLM passes are non-deterministic → run once and freeze.** Run it,
eyeball the diff, commit the output as the source of truth, archive the
script. When editing descriptions in place, edit by byte offset working
*backwards* through the file (so earlier offsets stay valid), preserve
the original quote style, and write a backup. Re-running a freeze step
against the current source of truth (instead of a clean input) silently
corrupts it — guard against running steps in the wrong order.

---

## 2. Getting the values right

### 2.1 The catch-all: reconcile the codebook against the actual data

**Codebooks routinely do not list every value a column can take, and they
under-specify in more ways than you'll guess up front.** This is a major
source of silent bugs: a value with no label renders as a bare number or
falls through to the missing filler, and nothing errors. The reliable
defense, run on *every* column:

```python
observed = set(df[col].dropna().unique())
listed   = set(codebook_value_labels[col])   # from your lookup table
missing  = observed - listed                 # values the codebook never explained
unused   = listed - observed                 # labels that never occur (often fine)
```

`missing` is your work list. Don't pre-judge which columns are "simple."

One nuance worth knowing: **what this reconciliation catches depends on
whether your value-map source is independent of the data.** If you
hand-parsed value labels from a PDF, the diff *discovers* real gaps
(parser misses, dropped categories). If you took the value labels from
the data file's *own* embedded metadata (§1.1), the diff mostly
*validates* — it should come back nearly empty, and that empty result is
itself the confirmation. Either way it earns its keep, because it also
surfaces the **high-cardinality / continuous** columns (many observed
values, ≤ a couple of labels), which is exactly the signal you need for
the next step. (The same independence caveat governs the validation oracle in
§6: when your map and the library's native decode read the *same* embedded
labels, their diff checks plumbing, not meaning — see §6.)

### 2.2 Common shapes the gaps take, and how to resolve each

These recur often enough to name, but expect others:

- **Continuous / high-cardinality** (ages, amounts, counts, ratings,
  durations). The codebook gives a *range* or nothing; `observed` has
  many distinct values. **Don't enumerate** — use a format function
  (`lambda x: f"{int(x)} years old"`). Watch for **top-coding** (a single
  high code meaning "X or more") — a plain format reads it literally;
  special-case the cap if it matters.
- **A few genuinely missing labels on an otherwise categorical column.**
  The PDF dropped them or the parser lost them. **Recover the meaning** —
  re-parse that variable's block (LLM or by hand), confirm against the
  data's frequencies, then add the entries. Don't guess from the number
  alone: a value could be a real category *or* a sentinel.
- **A count with a long thin tail.** Map the head explicitly and
  **collapse the tail into an umbrella bucket** ("N or more"). Make sure
  nothing downstream assumes exact counts.
- **Out-of-range "no answer" codes (sentinels).** Refused, Don't know,
  Inapplicable, breakoff, coding error. Conventions vary widely —
  negatives, high codes (7/8/9, 97/98/99), blanks — and, importantly,
  vary *within one survey* too. Handle at two layers (§3).
- **Derived / summary variables with their own sentinels.** Variables the
  survey *computed* often carry non-standard codes meaning "missing in
  one of the source items." They won't match the survey's usual sentinel
  set — reconcile them per-variable.

When a value in `missing` doesn't fit any known shape, **stop and
investigate that variable specifically** rather than letting it render
raw.

**Triage by occurrence count.** A code appearing thousands of times is usually
a real category the codebook dropped; a code appearing *once or twice* and
outside the variable's documented range is usually a data-entry glitch — an
out-of-scale value, or an option the item never offered. Confirm the option
count against the instrument before deciding (an item that offered only N
answers cannot have answer N+1).

**Then freeze the verdict as an assertion, not just a fix.** Once every code in
`missing` is explained — real category, known sentinel, or glitch — record the
expected/known unexplained codes as an explicit allow-list and **assert that
`observed − listed` equals exactly that set**. A *new* unexplained code in a
refreshed wave or a re-export then fails loudly at load instead of silently
rendering raw or falling through to the missing filler. This turns the
one-time reconciliation (§2.1) into a standing regression guard; freeze the
allow-list alongside your maps (§1.5).

### 2.3 Classify the transform type from the data, not the name

Each column becomes one of a few transform types (§4.2), and the
classification drives whether you write a `dict` or a format function.
**Decide it from the observed value set + the value-label table — never
from the variable's name or description.** A field called "frequency of
…", "number of …", or "age group" can easily be a small *ordinal
categorical* scale, and the wording will lead you to write a format
function for something that wants a dict (or vice-versa). Cardinality is
the tell: a handful of distinct values with labels → categorical; many
distinct values on a continuum with no/range labels → continuous; a count
with a thin tail → dict + umbrella. Check, don't infer from the name.

---

## 3. Missing values: the crux (map *and* clean)

A "no answer" code is the highest-yield place to introduce a silent bug,
for three independent reasons. Get all three right.

### 3.1 Conventions vary *within* a survey — detect missingness from the label, per variable

It is tempting to learn "this survey uses 7/8/9 for refused/DK/NA" and
blanket-map those numbers. Don't. In real surveys the convention varies
*across variables within the same file*: some variables encode "Refused"
as a proper out-of-range/extended-missing code, while others keep it as
an ordinary code (`9 = Refused`) — **and that same number is a real
category on other variables** (`9 = "Books"`). A global `code 9 →
missing` rule therefore corrupts data silently.

**First, check for embedded missing-value *definitions*.** The statistical
formats §1.1 tells you to prefer usually also declare, *per variable*, which
codes are missing — SPSS `missing_ranges`, Stata extended missings
(`.a`–`.z`), SAS special missings. These are machine-readable and already
encode the within-variable inconsistency above at the level of (column, code),
with **no label parsing**: the format itself marks `9` missing on one variable
and a real category on another. Where they exist they are your *primary*
source — a code in a declared missing range is missing, full stop.

The robust rule, when no embedded declaration covers the code: **decide
missingness from the value *label*, per
(column, code)** — normalize the label and match it against a set like
`{refused, don't know, dk, na, n/a, not applicable, no answer, skipped,
breakoff, …}`. The number alone tells you nothing; the label does. Record
the resulting per-column "missing codes" set in your lookup table so both
layers below can use it.

### 3.2 Your loader may destroy the distinction before you see it

Before you write any policy, **verify how missing values survive the
read.** Many data loaders, at their *default* settings, collapse every
flavor of missing — Refused, Don't know, Not applicable, system-missing —
into a single `NaN`. If that happens you have lost, at load time, the very
distinction the next step tells you to preserve, and no amount of
downstream policy can recover it.

So round-trip one known sentinel of each flavor: read it, and confirm you
can still tell Refused from Don't-know from system-missing. If the
convenient read flattened them, find the loader flag that preserves them
(e.g. read raw codes, or a "keep extended/ user missing" option) and use
*that* as your canonical read. This one check, done early, prevents a
whole class of "where did the 'Refused's go?" bugs.

### 3.3 Two layers, two decisions

Once the distinctions survive the read, a "no answer" code has two
independent jobs — conflating them is the classic bug:

- **At the renderer:** keep the distinctions in the value map so a
  displayed value is honest, and set `missing_value_fill` for anything
  unmapped (e.g. `"Refused / Don't know / Inapplicable"`).
- **At the data layer:** decide whether the value counts as *present*. A
  common choice is to map every sentinel (and every per-variable literal
  missing code from §3.1) to `NaN` so downstream code treats missingness
  uniformly.

A value can be *shown* in the persona (`"Prefer not to say"`) and still be
*recorded* as missing — two separate decisions, made in two places.

### 3.4 Rule of thumb

> Few distinct values you can name → **dict**.
> Many values on a continuum → **format function**.
> A count with a rare tail → **dict + umbrella bucket**.
> Unsure continuous vs categorical → **decide from the observed values,
> not the variable's name**.
> "No answer" codes → **detect from the label, per variable; show for
> display, NaN for math**.
> Embedded missing-value declarations exist → **use them as the
> per-(column, code) source; label-match only what they don't cover (§3.1)**.
> Sentinel distinctions matter → **confirm the loader didn't flatten them
> at read time**.
> A value the codebook never explains → **stop and reconcile against the
> data before shipping a map**.

---

## 4. Turning a variable into text: the ColumnToText pattern

### 4.1 The reusable object (library-independent)

You don't need a library for this. The logic is small and worth owning
directly, so nothing downstream is coupled to a third-party class. A
column renderer is a few fields and two methods:

```python
from dataclasses import dataclass
from typing import Callable

# A phrasing maps (column, rendered_value) -> one sentence. It is just a
# function with this signature, so write whatever a column needs.
def phrase_statement(col, v):  return f"The {col.short_description} is: {v}."
def phrase_value_only(col, v): return v
def phrase_qa(col, v):         return f"Question: {col.question_text or col.short_description}\nAnswer: {v}"

@dataclass(frozen=True)                    # frozen -> hashable, safe to cache
class ColumnToText:
    name: str                              # column code in the raw table
    short_description: str                 # compact noun phrase, e.g. "age"
    question_text: str = ""                # preserved question, lightly cleaned (§1.4)
    value_map: dict | Callable = None      # {code: label} or fn(value) -> str
    missing_value_fill: str = "N/A"
    phrasing: Callable = phrase_statement

    def render_value(self, value) -> str:  # raw value -> its label, no sentence
        if value is None or (isinstance(value, float) and value != value):  # NaN
            return self.missing_value_fill
        if callable(self.value_map):
            return self.value_map(value)
        if self.value_map is not None:
            return self.value_map.get(value, self.missing_value_fill)
        return str(value)

    def get_text(self, value) -> str:      # raw value -> full sentence
        return self.phrasing(self, self.render_value(value))
```

The split is the point: `render_value` is the one fixed job (raw value →
its label), and `phrasing` decides how that label becomes a sentence.
`phrase_statement` is the default; assign another per column when it
doesn't fit — an answer to a question (`phrase_qa`), standalone free text
(`phrase_value_only`), or any custom shape you write.

A persona is every selected column rendered and joined. Each column
carries its own phrasing, so the default just works:

```python
text = " ".join(c.get_text(row[c.name]) for c in cols)
# "The age is: 42 years old. The highest level of education is: ..."
```

To A/B a *whole-persona* style without touching any definition, apply a
phrasing over the public `render_value` directly — that's exactly what
`get_text` does internally, just with a different phrasing:

```python
text = "\n".join(phrase_qa(c, c.render_value(row[c.name])) for c in cols)
# "Question: How old are you?\nAnswer: 42 years old\n..."
```

**The per-column default degrades in aggregate.** `phrase_statement` reads
fine for one variable, but a survey is mostly *batteries* — attitude grids,
rating scales, knowledge items — and the same `"The {desc} is: {v}."` frame
stamped across a dozen sub-items reads as clumsy boilerplate and bloats the
persona. Judge phrasing on a *whole rendered persona*, not one line: a frame
invisible once is grating at ×15. When many fields share a frame, prefer a
compact layout — section headers plus a `Description: value` line per field (a
`phrase_value_only` wrapped by the grouping), mirroring the survey's own
structure — over a full sentence per cell. It is a whole-persona phrasing
choice (the A/B-over-`render_value` seam above), so you can switch without
touching any column definition.

**One composition decision that matters: skip-heavy surveys flood with
N/A.** Most respondents skip most branches, so "render every column" can
produce a wall of `N/A`. Prefer rendering only the *present* fields in the
persona body and accounting for the dropped ones separately (so the
persona states only what is known). But treat this as a judgment, not a
reflex: a `"Don't know"` on a *knowledge* item is signal you may want to
keep, whereas a skip-pattern `"Not applicable"` carries no information.
Decide drop-vs-keep per the downstream use, and make it explicit. One class
sits outside this judgment: **frame-supplied facts** (age band, gender, site,
wave, stratum) are known from metadata with certainty and have no skip or
refusal flavour — they are always *present*. The drop-vs-keep-on-missing
reasoning applies only to *elicited* answers; never drop a frame fact as if it
were an unanswered branch.

That's the entire reusable core: per column, a value map, a missing-value
fill, and a phrasing. It stops at the text — the persona is the output.
Keeping `question_text` on the object means the question form costs
nothing at build time.

### 4.2 The transform types (covers most variables)

| Type | `value_map` | Renders |
|---|---|---|
| **Categorical** | `dict` code→label | "…is: Employed full time." |
| **Numeric / continuous** | `lambda` | "…is: 42 years old." |
| **Open-ended text** | `callable` cleaner | echoes free text, normalizes sentinels |
| **Derived / composite** | `dict` (own sentinels) | "…is: Upper-middle income bracket." |

Open-ended handler — a subtlety: free-text columns load as `str`, so a
numeric sentinel arrives as a literal string (`-1` → `"-1"`). Normalize
both forms:

```python
def _open_ended_text(x):
    return "Prefer not to say" if str(x).strip() in ("-1", "-1.0") else str(x)
```

Ordinal/Likert scales are just categorical dicts — but **label the
endpoints in full** and leave interior points as numbers (`1:'Strongly
agree'`, `2:'2'`, …, `7:'Strongly disagree'`). The LLM interprets the
scale fine and you avoid inventing labels for interior points. Don't
"reverse-code" in the map; pass raw values through and let the labels
carry the direction.

**A value that is a *verdict* needs a phrasing that marks it as the
respondent's reply — not the proposition's truth.** When a categorical's
labels are themselves truth-values or stances — `True/False`,
`Correct/Incorrect`, `Agree/Disagree` — and the description reads as a
proposition (*"belief that <claim>"*, *"<claim> is the case"*), the default
`"{description}: {value}"` is ambiguous: *"Belief that <claim>: False"* can
mean *the claim is false* **or** *the respondent answered "False."*
Render these from the **statement the respondent rated plus their reply**,
reusing the preserved question wording (§1.4) via a per-column phrasing
(§4.1): *Rated the statement "<claim>" as False.* (or a `Q:/A:` pair) — never
a bare `proposition: True`. Keep the statement **verbatim**: paraphrasing or
negating the stem and then tagging it with the *original's* correct answer
produces self-contradicting text (a stem reworded to its negation but still
tagged with the un-negated answer says the opposite of what you mean). The
tell is simply that the label is a *verdict*, not a *category* — `Employed
full time` never clashes, `True` always can. This same proposition-vs-verdict
clash reappears anywhere downstream that co-locates a claim with a truth
value (e.g. a scoring rubric): keep the *statement*, the *respondent's
answer*, and any *correct answer* as three separately-labelled things.

### 4.3 Keep ownership where it matters

The reusable, survey-specific asset is your **value maps, descriptions,
question text, and missing-value semantics** — keep them in plain
data/objects you own. The rendering class around them is trivial and
swappable; the survey knowledge is the expensive part to rebuild, so
don't bury it inside a third-party type.

---

## 5. The data-cleaning layer

Renderer logic is per-value; this layer is per-table:

1. **Load raw, preserving missing distinctions.** Use the loader settings
   you validated in §3.2 — not the convenient default — so Refused / DK /
   NA survive as distinguishable values, and coerce types early so
   sentinel handling is uniform.
2. **Select** the columns you want in the persona, plus a respondent id.
   Don't carry the whole instrument. Drop pure survey machinery — admin /
   weighting / variance-estimation (design weights, replicate ids, a stratum
   code that only encodes variance) and pure-duplicate-recodes. But **don't
   blanket-drop a field just because it came from the sample frame**:
   frame-supplied demographics (age band, gender, site, wave, recruitment
   stratum) are facts *about the respondent*, which is exactly what a persona
   states — keep them, and tag them **metadata-derived** (§4.3) so a consumer
   can tell a frame fact from an elicited answer. The test is not "did it come
   from the design" but "does it describe the respondent, or only the survey's
   mechanics."
3. **Sentinels → NaN** using the per-column missing-code set from §3.1
   (both the survey's out-of-range sentinels *and* the per-variable
   literal missing codes), so missing values render as
   `missing_value_fill` (or get dropped, §4.1), never as raw codes.
4. **Open-ended merge.** Free-text answers often ship in a *separate*
   file (sometimes one sheet/table per variable) — merge on respondent id
   with a left join into a second table alongside the numeric one.
5. Write the clean table(s); the renderer runs over them downstream.

The only missing-value policy the renderer itself needs is **NaN → filler
text** (§3.3, §4.1). Anything more — an outcome column to keep, weights to
apply, rows to drop or score — belongs to the downstream task, not here.
Keeping it out is what makes the persona layer reusable across surveys.

---

## 6. Validate, then freeze

- **Cross-check your value maps against an independent oracle — and know what
  the diff proves.** If the data came from a statistical format, its library
  can decode value labels natively (e.g. read the file *with* categoricals
  applied). Render every categorical cell through your maps and diff against
  that native decode over the *whole* table — cheap, exhaustive, catches any
  map you got subtly wrong in seconds. **But the diff is only as independent as
  its sources** (the same nuance as §2.1): when your map and the native decode
  both read the *same* embedded labels, it exhaustively validates **plumbing**
  — float-vs-int key coercion, key lookup, missing handling, phrasing — but a
  *semantically* wrong label is wrong in both and the diff still comes back
  clean. It is a genuine **semantic** check only when your value-map is
  independently derived (e.g. hand-parsed from a PDF, §1.3) and the native
  decode is the second opinion. Treat a zero-mismatch diff over
  embedded-metadata maps as "the wiring is correct," not "the labels are
  right"; get semantic confidence from reconciliation against an independent
  source (§2.1) and from reading whole personas (below).
- **Build the single-record trace first, not last.** Stand up the trace — one
  respondent rendered through the *real* functions, showing source → code →
  label per field — *before* the batch run. Early, it is your cheapest plumbing
  probe (does load, value map, missing fill, and phrasing compose on one
  inspectable record?); later, unchanged, it becomes the human-facing
  deliverable. One artifact, two payoffs.
- **Read a handful of full personas end-to-end.** Bare numbers, `N/A`
  floods, or a raw sentinel showing through *anywhere* mean a value map is
  incomplete or a missing code went undetected — go back to §2.1 / §3.1.
  Also watch for a *verdict read as a fact*: a line like *"belief that X:
  False"* where the `False` is the respondent's answer, not a claim that X
  is false — fix the phrasing, not the data (§4.2).
- **Intermediate artifacts are checkpoints, not throwaways.**
  sources → lookup table → renderer defs. Each is reviewable and
  re-runnable in isolation.
- **One pass = one concern.** Parsing, description-rewriting, question
  cleanup, reordering, and cross-file syncing are separate steps. Don't
  fuse them.
- **LLM passes are non-deterministic → run once and freeze** (§1.5).
  Commit the output as source of truth; re-running against that output
  instead of a clean input silently corrupts it.
- **Keep parallel files from drifting.** If descriptions live in more than
  one place, have a sync script scrape one into the other rather than
  hand-editing both.
- **Adding one variable later doesn't need the pipeline:** write the
  renderer block directly, add the code+description to the column list,
  regenerate the clean table. The pipeline is for the *initial* build.

---

## 7. Checklist for a new survey

1. [ ] **Inventory the inputs and assign sources** (§1.1): value maps and
       descriptions usually from the data file's embedded metadata;
       question wording from a separate instrument. Only parse the
       codebook PDF for value codes if there is no embedded metadata.
2. [ ] **Verify the loader preserves missing distinctions** (§3.2) —
       round-trip one Refused / DK / NA / system-missing before anything
       else. Use the preserving read as canonical.
3. [ ] Assemble the **lookup table** (code, description, question text,
       value labels). Preserve question wording in its own column; merge
       grid stems into sub-items (§1.4).
4. [ ] LLM-reformulate descriptions in one batch pass; if you used an LLM
       to extract wording, **verify it against the source** (§1.5);
       eyeball; freeze.
5. [ ] **Reconcile every column against the data** (`observed - listed`,
       §2.1) and **classify each transform type from the data, not the
       name** (§2.3).
6. [ ] **Detect missing codes per (column, code)** — embedded missing-value
       declarations first, label-matching as fallback (§3.1); handle
       continuous (format fn), counts (umbrella), sentinels (map + NaN),
       open-ended (str-sentinel cleaner), derived (own sentinels).
7. [ ] Write renderer defs (own the §4.1 class — no library needed).
       Carry both `short_description` and `question_text`.
8. [ ] Build the cleaning layer: preserving load, select columns,
       sentinels→NaN. When selecting, **keep frame-supplied demographics**
       (age band, gender, site, wave) as persona fields, tagged
       metadata-derived; drop only pure survey machinery (weights / replicate
       ids / admin / duplicate recodes) (§5). Decide the persona's drop-vs-keep
       policy for missing answers (§4.1).
9. [ ] **Validate against the library's native decode** — remembering it
       checks *plumbing* not *meaning* when your map shares the embedded
       source (§6) — and **read a handful of personas** end-to-end. Any bare
       number, `N/A` flood, or raw sentinel → a map is incomplete; go back to
       §2.1/§3.1.
