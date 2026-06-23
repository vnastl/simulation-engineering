# Transcript → coded persona text: an interview-agnostic playbook

How to go from **semi-structured interview transcripts + a target schema** to a
**coded record per participant** — each value backed by a verbatim quote and a
confidence — that renders to a persona and/or an evaluation set. The companion to
`CODEBOOK_TO_TEXT_PLAYBOOK.md`: that one turns a survey codebook into persona text;
this one codes free prose into the *same* kind of text, in the *same* schema, so
the two are comparable. References below of the form "(§X there)" point to the
codebook playbook.

**Scope.** Only about producing the *coded text + linked prose*. What you do with
it — predict, evaluate, simulate — is out of scope and deliberately not assumed.
No study-specific assumptions either: what a "unit" is (a person, a session, a
case), the transcript format, the value schemes, and even *whether a target schema
already exists* all vary, so the method below is about *what to decide and verify*,
not fixed patterns to copy.

---

## 0. The mental model

You are building two artifacts, and they are separate concerns — keep them
separate:

1. **A per-construct coder.** For each target variable, a step that turns one
   unit's transcript into a value in the schema's space **plus the verbatim
   evidence and a confidence**. It is the analogue of the codebook playbook's
   `ColumnToText` (§4.1 there) — but the value is *judged from prose*, not looked
   up, so it can be wrong, and it must show its work.
2. **A registry / coding layer.** Who the unit is, what is known *for free* from
   metadata, which transcript files belong to whom, and the document → text read.

The data flow:

```
target schema ───────────────┐
(reuse a survey codebook, or  │
 derive from the guide)       ├─code─▶ per-construct values ──verify──▶ reconciled ──render──▶ persona
registry (unit, free codes,   │       (+ evidence, confidence)          record                + eval pairs
 session→unit map) ───────────┤
transcripts (→ text, turns) ──┘
```

The hard parts, in order of how much *silent* damage they cause — the ones that
error out you'll fix anyway; these ship wrong and look right:

- **(A) Coding into the wrong schema, or no schema.** Nothing to look a value up
  in — you decide *what space to code into* before you code, and reuse one if it
  exists (§1).
- **(B) Fabrication.** An LLM asked to code prose invents fluent quotes and
  confident codes; without a quote-presence + support check it ships wrong (§5.1).
  This is the single largest source of silent bugs.
- **(C) Elicitation / volunteer bias.** The transcript holds only what the subject
  *volunteered or was prompted on*, so *aggregate* marginals are biased even when
  every per-record code is right (§5.3).
- **(D) Attribution & provenance.** Mis-attributing group talk to one speaker, a
  value the interviewer planted (§3), or a code with no traceable quote — each is
  unrecoverable later (§3, §5.4).
- **(E) Verification is subtractive — budget from the reconciled record, not the
  raw pass.** The passes in §5 routinely *remove* codes the coder emitted: the
  quote-presence check drops unfindable quotes, and low-confidence fields that
  can't be re-supported on a blind re-read fall away. Plan coverage from the
  *reconciled* record, never the first coder pass — and treat a verification stage
  that changes almost nothing as a sign the guard isn't biting, not proof the
  coder was clean.

---

## 1. The target schema — decide before coding

A code is meaningless without a space it lives in. Decide that space first.

- **Reuse an existing codebook if one exists.** If a survey (or a prior wave, or
  any structured instrument) covers the same constructs, code into *its* variables
  and value-labels — the artifact the codebook playbook produces (its §1.2 lookup
  table). Then a coded transcript is directly comparable to a survey record and
  shares the *same* renderer (§7). This is the single highest-leverage decision: it
  turns "qualitative notes" into data in a known space, and a value coded from
  prose lands in exactly the survey's label space.
- **Otherwise derive the schema from the interview guide.** The guide's topics and
  questions *are* your variables; define a small value scheme per construct (an
  ordinal scale, a category set, yes/no) and freeze it as a codebook — one row per
  variable: `var, description, topic, value-labels, scale type`. (Everything the
  codebook playbook says about value maps, ordinal endpoints, and "don't know" as a
  real category applies here too.)
- Either way, **freeze the schema first.** Coders read it and may emit *only* codes
  from its value-labels — never an invented code or label. Export it as a
  standalone, reviewable artifact (the codebook playbook's seam: schema as data,
  code as a separate pass).

## 2. Linkage — record-level or construct-level?

Determine explicitly whether transcripts link to other data at the **record
level** (a shared id you can join on) or only at the **construct level** (same
population and instrument, no shared id). Transcripts are usually
anonymised/pseudonymous → **no record link** → you can compare *distributions* and
reuse the *schema*, but you cannot join individuals. State which you have; it
bounds everything downstream. **A name in a file-list is not a join key:** don't
assume a pseudonym or filename links to a row in an anonymous dataset; it usually
doesn't. A construct-level link supports comparison and calibration (§8), never a
per-person merge.

## 3. Sources → free metadata vs. prose, and the registry

The codebook playbook decides *where each piece of truth lives*; so do you, but the
split is sharper here: some fields are *known* from metadata, the rest are *judged*
from prose, and they carry different trust.

- **Free metadata.** A file-list / registry usually carries per-unit facts:
  pseudonym, demographic strata, interview type or wave, which session files belong
  to whom. These become codes with **high confidence and no prose** — keep them in
  a separate lane from prose-coded fields. (They are the interview analogue of the
  *frame-supplied facts* the codebook playbook keeps in the persona, always-present
  and never an unanswered branch (§4.1 there) — and selected, never blanket-dropped,
  with a **metadata-derived** tag (§5 there): known, not reported.)
- **Build the unit registry first:** `unit → {metadata codes, session files}`. One
  person may have several sessions; map them.
- **Attribution rule.** Code from **individual interviews**. In group sessions
  (focus groups) speaker attribution is unreliable — use them only as *supporting*
  evidence with explicit speaker tags, or exclude them. Attributing one speaker's
  words to another is a silent, uncorrectable error.
- **Code the answer, not the question.** Preserving turns exposes a trap the
  quote-presence check (§5.1) cannot see: a leading prompt — *"So you'd say cost was
  the main barrier?"* / *"yeah"* — plants the value, and a verbatim *"yeah"* looks
  like clean evidence for a code the subject never volunteered. The evidence quote
  must come from the **Subject** turn and stand on its own; an affirmation whose
  content lives only in the preceding **Interviewer** turn is interviewer-attributed
  — downgrade it or null it. This is the within-transcript cousin of the
  group-session mis-attribution rule above: the words are real, but the *source of
  the proposition* is wrong.
- **Extraction.** Convert the source documents (RTF/DOCX/PDF) → text *preserving
  speaker turns* — the `Interviewer:` / `Subject:` structure is signal (who is
  asked vs. who answers). Normalise lightly; keep wording **verbatim** so quotes
  survive the round trip (§5.1).
- **Expect format heterogeneity *within one corpus* — detect per file, not once.**
  A single deposit can mix turn formats: cleanly tagged (`Subject:\t…`), *alternating*
  (tagged `Interviewer:` turns with the subject's replies as untagged lines between
  them), and — the trap — **interviewer *notes*: prose summaries with no Subject
  turns at all.** A notes unit cannot supply a verbatim Subject-turn quote, so it
  breaks the very evidence rule the whole §5.1 trust model rests on. Treat it as its
  own class alongside focus groups: tag it **non-verbatim**, cap its confidence,
  draw "evidence" from the notes text (the interviewer's paraphrase, never the
  subject's words), and use it only as supporting/low-confidence material — never as
  a source of verbatim Subject quotes. Detect the format on each file before parsing
  it; a single global parser silently drops the alternating and notes units.

## 4. Addressability — what the prose can and can't reach

Before coding, tier every target variable, from the interview **guide** (not the
transcripts):

- **metadata** — fixed from the registry, no prose.
- **strong** — the guide asks about it directly; expect a supporting quote.
- **weak** — touched only indirectly; codeable sometimes, low confidence, else
  null.
- **unaddressed** — the guide never probes it; the survey is the only source, don't
  fake it.

This sets expectations (a 0%-coverage variable in the *unaddressed* tier is not a
bug) and tells you where confident codes should exist. It is the interview analogue
of reconciling the codebook against the data (codebook playbook §2.1): it tells you
where coverage *should* be high, so a gap there is a real signal.

---

## 5. The crux — verification (coding from prose fails silently)

This is where transcript→text differs most from codebook→text. The codebook side
looks values up in clean metadata; here every value is a *judgment*, so the whole
section the codebook playbook spends on missing values, this one spends on trust.
Get all of it.

### 5.1 Fabrication — quote-presence + support, or leave null

An LLM asked to code prose does not fail loudly; it invents a plausible quote and a
confident code (the same fluent fabrication the codebook playbook warns about for
LLM extraction of wording from awkward source PDFs, §1.5 there — but now it is your
*primary* path, not a targeted fallback, so the guard must be standing). Defences,
all required, **and run in order — deterministic first, LLM second**:

- **Every code carries a VERBATIM evidence quote** copied from the transcript
  (never paraphrased), tagged with the source file and taken from the **Subject**
  turn (§3).
- **Deterministic quote-presence check — run it first.** It is cheap and catches
  the most confident fabrications, so drop any field whose quote isn't in the
  transcript *before* the expensive re-read sees it; reversed, the LLM re-read can
  "confirm" a code against a quote that was never on the page (it reasons about the
  words, not their presence). **Normalise both sides before matching, or the check
  eats true quotes:** the quote came through extraction (§3), which inserts speaker
  tags, and the coder may have straightened curly quotes or dropped a bracketed
  fill — a raw substring test then flags *genuine* quotes as fabrications, and a
  presence check that throws false positives gets switched off, leaving the primary
  failure mode (§0, B) unguarded. Match on a *canonicalised* form of both: fold
  whitespace runs, unify quote and dash glyphs, strip inserted speaker tags, match
  case-insensitively, still allowing `…` for elided gaps. Track the drop rate; a
  sudden spike usually means the canonical form drifted from the extractor, not
  that the coder started lying. **A *low* presence drop, though, is not the "guard
  isn't biting" smell of §0(E)** — presence and support are different failure
  modes. The presence check catches only *fabrication / paraphrase* (the quote
  isn't on the page), and a capable coder handed the transcript and told to copy
  exactly will copy faithfully, so a near-zero presence drop is the *expected* good
  case. The §0(E) "changes almost nothing → guard not biting" heuristic belongs to
  the **support** check below (adversarial re-read), where near-zero change really
  is suspicious. Confirm the presence check is alive by spot-checking it rejects a
  known-bad quote — not by demanding a high drop rate.
- **Adversarial re-read — on the survivors.** A second agent re-reads the *same*
  transcript and, per field, checks the quote supports the *assigned* code (not a
  neighbouring one); default to skepticism. Apply corrections; downgrade thin
  support. This is the *support* check (does the quote mean what the code says),
  distinct from the presence check above (is the quote on the page).
- **Leave null rather than guess.** Skipping is correct and expected — a coded
  field is a claim you must back with words on the page.

### 5.2 Blind second pass for low-confidence — reproducibility, not accuracy

Re-code the low-confidence fields with a fresh coder that **does not see the first
code**. Agree (exact, or within one point on an ordinal scale) → promote
confidence; disagree → keep but flag with the alternative; the second pass finds
nothing → keep low, flag. This measures *reproducibility between independent
passes* — useful, but it is **not** validation against truth (§8).

**Fix the blind-pass scope *after* the adversarial pass, not before — the order
bites.** The adversarial re-read (§5.1) *downgrades* confidence on thinly-supported
codes, so it changes which fields count as low-confidence. If the blind pass chose
its targets from the pre-adversarial confidences, every field the adversarial pass
*later* pushed to low was never in the blind pass's scope — and naively it then
looks "not re-supported by the blind pass" when in truth it was simply never
re-coded. So compute the low-confidence set from the *post-adversarial* record, and
keep two distinct flags: **"blind tried and failed to re-support"** (a real
reproducibility signal) versus **"never in blind scope"** (a scheduling artifact,
not evidence). Conflating them silently inflates the apparent non-reproducibility
rate and mis-reads §5.2's calibration extremes.

**Agreement between two LLM passes is correlated, not independent.** The adversarial
re-read (§5.1) and this blind pass share the same model priors, so a *systematic*
error — an ambiguous schema label, a stem both passes read the same wrong way, a
construct the guide framed misleadingly — produces confident agreement that is
confidently wrong. Promotion to high confidence therefore certifies reproducibility,
never correctness, and the bias survives all of §5.1–5.2 untouched. This is exactly
why the human spot-check (§8) is non-optional rather than a nicety: it is the only
pass whose blind spots differ from the coder's.

**Read the non-resupport rate as a tier-calibration signal.** On a genuinely
low-confidence tier, expect a substantial fraction to fail re-support on a fresh
blind read — that is the tier working as designed, not a failure. The extremes are
the diagnostic: if the blind pass *re-supports almost everything*, the first pass
mislabelled solid codes as low-confidence; if it *re-supports almost nothing*, the
first pass was guessing. Track the agreement rate as a property of the coder, and
recalibrate what "low" means before trusting the promotions (§8).

### 5.3 Elicitation / volunteer bias — per-record sound, marginals biased

The transcript records only what the subject *volunteered or was prompted on*. So
the coded marginal over-represents salient and positive cases, and **silence is not
"disagree."** Consequences:

- **Per-record codes (with quotes) are sound; aggregate marginals are biased.** Say
  so wherever you report a marginal.
- **When comparing to a forced-choice survey, match the elicitation:** restrict the
  survey to *salient* responders — drop the neutral midpoint and "don't know",
  condition on the relevant branch (only those who took a path are asked why they
  took it) — and compare against the *salient* (confident) codes. This converts
  artefact gaps into agreement and isolates the real ones.
- **Salient-matching answers a narrower question — say which one.** Restricting the
  survey to salient responders also discards the population marginal: you are now
  testing whether the interview agrees with the survey *among people who would have
  volunteered*, not whether it recovers the survey's distribution over *everyone*.
  That is the right test for coding fidelity and the wrong one for prevalence.
  Report matched agreement as evidence the codes are sound, never as the corpus's
  marginal — the corpus cannot give you that marginal.
- **Factual-presence items can't be reweighted to match.** "A close contact has
  experience X", "ever did Y" — the interview captures the YES cases and stays
  silent on the rest; no survey matching fixes that. Flag those variables; trust
  their per-record codes, not their marginals.

### 5.4 Confidence & provenance are mandatory, not optional

Unlike a categorical lookup from a clean file, a prose code is a judgment, so every
field carries: **code, confidence (high/medium/low), verification status, and the
quote(s).** The codebook playbook needs none of this — its frame-supplied facts are
known from metadata with certainty and carry no evidence (§4.1, §5 there). A prose
code is the opposite: the quote and confidence are the *load-bearing* part of its
trust, so tag it **prose-derived** (against the **metadata-derived** tag the
codebook playbook puts on its free facts, §5 there) and make it show them.
**No confidence + provenance, no evaluation:** downstream can only filter to a
reliable subset (high + medium, dropping contested and unsupported-on-reread) if
every field carries it. Without it the codes browse but don't evaluate.

### 5.5 Within-transcript contradiction — resolve it, don't average it

Prose is not a single forced choice; one subject can support two codes across turns
(an early stance softened later, a general claim with a personal exception). The
schema still wants one value, so make the resolution explicit rather than letting
the coder grab the first or most fluent hit.

- **Collect all supporting quotes before assigning**, not just the first match. A
  construct with quotes pointing at two codes is the signal, not noise.
- **Prefer the considered over the offhand, the specific over the general, the
  later over the earlier** when a subject visibly revises — and record the loser.
  Carry the runner-up code + quote in the field's provenance (§5.4) so the
  contradiction survives, mark confidence no higher than medium, and flag it for
  the spot-check (§8).
- **Never blend.** Splitting the difference on an ordinal scale invents a midpoint
  nobody said; that is fabrication (§5.1) wearing a number.

---

## 6. Skips — "not discussed" ≠ "covered by another variable"

When a construct isn't coded, the coder must say *why*: genuinely **not
discussed**, or **covered by `<var>`** — the subject's view is captured on a
neighbouring item (a specific reason folded into a broader statement, the same
opinion coded next door). Aggregate the reasons: variables routinely marked
"covered by" are not gaps, just folded in. This is the interview analogue of the
codebook's `observed − listed` reconciliation (§2.1 there) — it stops a low
coverage count from being read as a lost answer, and like that reconciliation it is
cheap insurance run on every variable.

---

## 7. Render — reuse the ColumnToText pattern

Because prose codes live in the target schema, they render through the **same**
per-construct renderer the survey uses (the codebook playbook's §4.1 class) — a
prose code and a survey code produce the same label. Produce two personas:

- **plain** — `Description: value`, code-only, byte-comparable to a survey persona
  (a drop-in for the same downstream). Use the same sectioned layout the codebook
  playbook recommends for battery-heavy surveys (§4.1 there).
- **enriched** — the same, plus the linked quote(s) and a confidence/verification
  tag per line, for inspection and as the evaluation source.

Group by section; render present fields only (skip-heavy, like a real survey). Keep
a normalised JSON (`var → {code, rendered, confidence, verification, evidence}`) as
the machine artifact. The renderer is trivial and shared. **The owned asset is the
coding** — the reused value maps plus the per-field judgments, quotes, and
confidences (the codebook playbook's §4.3 ownership rule).

**Beyond the codes: keep the full prose per recurring question.** A semi-structured
guide asks the same underlying question several ways and *probes*; the subject's
complete answer — the initial response *and* every probe — is richer than any
single coded value and worth keeping as its own layer. Define a small set of
**recurring-question themes**, coarser than the variables — each theme maps to a
**subset** of the coded variables — and for each, capture the **whole verbatim
answer span, after probing**, linked to that subset. This is a third artifact
beside the plain and enriched personas: the codes are the structured signal; the
thematic prose is the full text a model can read for context — *related* to the
codes but not reducible to them (a theme's answer routinely carries material no
variable captures, and the same span backs several codes at once). Verify the spans
are verbatim with the same quote-presence check (§5.1), store them keyed by theme
with their related-variable subset, and reconcile against the coding: a code with no
quote inside its theme's prose, or a theme rich in content but empty of codes, is a
flag worth reading.

**Render the prose as the reconstructed exchange, not a list of quotes.** "The
whole answer after probing" *is* a question→answer exchange, and it reads as one
only if you render it as one: map each verbatim Subject quote back to the turn it
came from and prepend the preceding **Interviewer** turn, so each theme is the
recurring question followed by the subject's full answer (several probes → several
exchanges, in transcript order). A bare list of quote fragments — even correctly
verbatim ones — reads as disconnected snippets, not an interview, and drops the
question each answer was given to. (When a quote maps to no Subject turn — e.g.
interviewer-notes units, which carry no Subject turns to reconstruct an exchange
from — render the verbatim spans as plain paragraphs instead; such units should
already carry the non-verbatim tag from §3.)

---

## 8. Validate, then freeze

- **No human gold standard ≠ validated.** Agent-vs-agent agreement (re-coding,
  multi-pass) measures *reproducibility*, not accuracy (§5.2). For accuracy, a
  **human spot-check** is the calibration step — and two conditions decide whether
  it works. **Make it blind:** the human re-codes from the transcript *without
  seeing the assigned code or its quote*, or they grade the LLM's reasoning, anchor
  to it, and you measure agreement-with-the-machine again instead of
  agreement-with-the-page. **Treat it as a sample, not a verdict:** it is a finite
  stratified sample that estimates *what each confidence tier is worth* (the high
  tier's hit rate, the medium tier's), with its own sampling error — size each
  stratum for a usable interval and report tier hit-rates, not a single pass/fail.
  It calibrates the tiers; it does not bless individual records outside the sample.
- **Reconcile the coded distribution against any independent target** (a parallel
  survey, elicitation-matched per §5.3). Use it to surface systematic bias and
  mis-coding — not to bless individual records. (The codebook playbook's validation
  oracle has an independence caveat, §6 there; yours is even weaker — the only
  independent oracle is a human.)
- **Fan out + verify, then freeze.** One coder per unit; the verification passes
  above; commit the frozen coding as source of truth; **preserve provenance** (the
  raw coder output, the verifier verdicts, the second-pass). Re-running synthesis is
  deterministic; the LLM coding is frozen — re-running coders against the frozen
  output silently corrupts it (the codebook playbook's "run once and freeze" rule,
  §1.5 there, applies here verbatim).
- **Build a single-record trace** that shows transcript → codes + snippets →
  persona for one unit. It is the artifact a reader trusts and a probe that catches
  coding-layer bugs on one readable example. When the survey arm has a trace too,
  put them side by side: the schema is shared, so one trace can carry both.

---

## 9. Rule of thumb

> Coding into a space that already exists → **reuse the survey's value-labels; a
> prose code then renders like a survey code**.
> No schema yet → **derive it from the interview guide; freeze before coding**.
> A code with no verbatim Subject-turn quote → **drop it; coding is a claim you back
> with words**.
> A quote not found in the (canonicalised) transcript → **fabrication; drop it**.
> An affirmation whose content is only in the interviewer's turn → **the interviewer
> coded it, not the subject; downgrade or null**.
> Low confidence → **re-code blind; agree to promote, disagree to flag, silence to
> keep-low**.
> A subject who says X then ¬X → **resolve, keep the runner-up in provenance; never
> average to a midpoint nobody said**.
> A clean per-record code but a surprising marginal → **suspect volunteer bias, not
> a finding; match elicitation before comparing, and only for fidelity, not
> prevalence**.
> A 0% variable → **check the addressability tier before calling it a gap; it may be
> unaddressed, or covered by a neighbour**.
> "Validated" from agent agreement → **that is reproducibility; accuracy needs a
> blind human spot-check, read as a tier-calibration sample**.

---

## 10. Checklist for a new corpus

1. [ ] **Pick the target schema** — reuse a parallel codebook if one exists; else
       derive it from the interview guide; freeze it (§1).
2. [ ] **Settle linkage** — record-level join or construct-level comparison only
       (§2).
3. [ ] **Build the registry** — unit → metadata codes (free, high-confidence) +
       session files; map sessions to units (§3).
4. [ ] **Extract transcripts** (→ text, speaker turns); set the group-session
       policy (exclude / supporting-only) (§3).
5. [ ] **Tier addressability** (metadata / strong / weak / unaddressed) from the
       guide (§4).
6. [ ] **Code per unit** into the schema — verbatim Subject-turn evidence +
       confidence; null over guess; skip-reasons distinguish "covered by" from
       "not discussed" (§5, §6).
7. [ ] **Verify** — *canonicalise* transcript + quote before the deterministic
       presence check (fold whitespace, unify glyphs, strip speaker tags, match
       case-insensitively), then adversarial re-read + blind second pass on
       low-confidence; resolve within-transcript contradictions, keeping the
       runner-up in provenance (§5.1, §5.2, §5.5). Expect the reliable set to shrink
       (§0, E).
8. [ ] **Merge metadata + prose; render** plain + enriched personas; write the
       normalised JSON, plus the **full thematic prose** per recurring-question
       theme (the whole answer after probing) linked to its variable subset (§7).
9. [ ] **Reconcile** the distribution vs an independent target, elicitation-matched;
       flag factual-presence items (§5.3, §8).
10. [ ] **Blind human spot-check** stratified by confidence, read as a tier-
        calibration sample; **freeze**; preserve provenance; build the single-record
        trace (§8).
