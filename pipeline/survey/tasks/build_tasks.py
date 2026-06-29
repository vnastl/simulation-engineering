"""Assemble the task layer (TASK_PLAYBOOK §1.2, §4) and run the hygiene guards.

Combines the declarative task defs (task_defs), the frozen answer keys
(estimate.py output), the rubric dimensions (rubric), and the *real* persona
composer (build_personas.compose) into **three task shapes per theme**
(micro / macro-prose / macro-number), and writes a reviewable artifact in which
the **model-facing** text (conditioning persona + prompt) is kept visibly
separate from the **answer-key-only** material (estimates, denominators, correct
answers) — so a reader can never mistake the scorer's view for the model's (§4).

Two guards run on every build, both of which should come back EMPTY (§4):
  * LEAK (§1.3): assert no held-out outcome item appears in a theme's conditioning
    allow-list. The empty intersection IS the confirmation.
  * SAMPLE SIZE (§4): assert no study/subgroup count and no "N=" reaches any
    model-facing string (the conditioning persona or any prompt). Populations are
    described to the model by definition, never by size.

The model call is the one open slot (§4 "show, don't run"): we render the answer
key and leave the model's answer + score an explicit, labelled slot. The scorers
in rubric.py are runnable, but nothing here invokes them on a fabricated answer.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import clean_data                              # noqa: E402
import build_personas                          # noqa: E402
from schema import load_columns                # noqa: E402

import task_defs as T                          # noqa: E402
import rubric                                   # noqa: E402  (scoring weights for the spec doc)

ROOT = HERE.parent.parent.parent
SURVEY_OUT = ROOT / "outputs/survey"
OUT = SURVEY_OUT / "tasks"

# Tokens that must never reach the model (§4): study N, every split's group
# denominators, every per-item answered-N/n_pos, and a literal "N=".
def _forbidden_size_tokens(keys: dict) -> set:
    toks = {"804"}
    for t in keys["themes"].values():
        for g in t["split"]["groups"]:
            toks.add(str(g["n"]))                    # each split group's total size
        for it in t["items"]:
            for g in it["groups"].values():
                toks.add(str(g["n_answered"]))
                toks.add(str(g["n_pos"]))
    # Floor at 40: model-facing text only ever contains small numbers — Likert
    # codes/years (≤5) and age bands (≤30+) in the persona, and "5-point scale" in
    # the prompts — never a number in [6, 150). Every genuine population/denominator
    # size is well above 40 (female n≈171, male n≈610, study 804), so the floor
    # catches all of them while never false-positiving on persona content. (Small
    # per-item n_pos like 11/37 fall below the floor, but they are counts that
    # cannot appear in any model-facing string anyway.)
    return {tk for tk in toks if tk.isdigit() and int(tk) >= 40}


def assert_no_sizes(text: str, forbidden: set, where: str):
    if "N=" in text:
        raise AssertionError(f"sample-size token 'N=' leaked into model-facing text ({where})")
    for tok in forbidden:
        if re.search(rf"(?<!\d){re.escape(tok)}(?!\d)", text):
            raise AssertionError(
                f"sample-size token {tok!r} leaked into model-facing text ({where})")


def conditioning_cols(theme, by_code):
    """The ColumnToText objects for the theme's conditioning allow-list, in the
    canonical column order (so the composer renders them sectioned)."""
    allow = set(theme.conditioning)
    return [by_code[c] for c in by_code if c in allow]


def assert_leakfree(theme):
    """§1.3 — held-out ∩ conditioning must be empty. The empty set is the proof.
    (Column existence is checked separately in build() against `by_code`.)"""
    holdout = set(theme.holdout_codes())
    shown = set(theme.conditioning)
    leak = holdout & shown
    assert not leak, f"LEAK on theme {theme.key}: held-out item(s) {sorted(leak)} are shown"


def render_micro(theme, raw_row, by_code, forbidden):
    """Render ONE respondent's micro task: the conditioning persona (real composer,
    conditioning vars only) + the filled prompt. Returns model-facing text and the
    held-out answer key for that respondent (kept separate)."""
    cond = conditioning_cols(theme, by_code)
    persona, fields, dropped = build_personas.compose(cond, raw_row)
    # The composer's first line carries the archival record ID ("SURVEY RESPONDENT
    # #523 (...)"). That ID is admin metadata, not a conditioning feature, and must
    # not reach the model (§4: keep admin/identifier material out of the prompt; it
    # also collides with frequency counts). Replace it with a neutral header — a
    # task-layer transform over the real composer output, not a re-implementation.
    _lines = persona.split("\n")
    _lines[0] = "Profile of one engineering / design & technology student:"
    persona = "\n".join(_lines)
    prompt = theme.micro_prompt.format(persona=persona)
    assert_no_sizes(persona, forbidden, f"{theme.key}/micro/persona")
    # the prompt minus the {persona} fill must also be size-free
    assert_no_sizes(theme.micro_prompt.replace("{persona}", ""), forbidden,
                    f"{theme.key}/micro/prompt")
    rid = int(raw_row["ID"])
    sv = raw_row[theme.split.var]
    group = None if pd.isna(sv) else next(
        (g.key for g in theme.split.groups if int(sv) in g.codes), None)
    answer_key = {
        "respondent_id": rid,
        "respondent_group": group,           # this respondent's group on the theme's axis
        "held_out_truth": {
            it.code: _respondent_item_truth(it, raw_row, by_code)
            for it in theme.outcome_items},
    }
    return {"model_facing_prompt": prompt,
            "conditioning_persona": persona,
            "n_conditioning_fields": len(fields),
            "answer_key": answer_key}


def _respondent_item_truth(item, raw_row, by_code):
    col = by_code[item.code]
    v = raw_row[item.code]
    present = col.is_present(v)
    if not present:
        return {"answered": False, "pos": None,
                "respondent_answer": "not answered"}
    iv = int(v)
    return {"answered": True,
            "pos": iv in T.POS_CODES,                       # the salient-state truth
            "respondent_answer": col.render_value(iv),       # rendered as their reply (§3.2)
            "raw_code": iv}


def macro_definitions(theme):
    """(groupA definition, groupB definition) for THIS theme's split — model-facing,
    by definition never size (§4)."""
    a, b = theme.split.groups
    return a.definition, b.definition


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    by_code, _ = _by_code()
    raw_df = pd.read_csv(SURVEY_OUT / "raw_codes.csv")
    keys = json.loads((OUT / "answer_keys.json").read_text())
    forbidden = _forbidden_size_tokens(keys)

    cards = {"splits_note": "each theme splits the population on a DIFFERENT axis "
                            "(sex / university / discipline), §1.3; populations named "
                            "by definition, never by size (§4)",
             "endorsement_cut": T.POS_CUT_NOTE,
             "themes": {}}

    for theme in T.THEMES:
        assert_leakfree(theme)
        for c in set(theme.holdout_codes()) | set(theme.conditioning):
            assert c in by_code, f"unknown column {c!r} in theme {theme.key}"

        split = theme.split
        gA, gB = split.groups[0].key, split.groups[1].key
        A_def, B_def = macro_definitions(theme)
        key_items = {it["code"]: it for it in keys["themes"][theme.key]["items"]}

        # rubric dimensions: verbatim statement from the SAME ColumnToText (§3.2)
        rubric_items = []
        for it in theme.outcome_items:
            col = by_code[it.code]
            rubric_items.append({
                "code": it.code,
                "statement": col.question_text or col.short_description,  # verbatim
                "scale": col.scale_label,
                "salient_state_pos": it.pos_state,
                "non_salient_neg": it.neg_state,
            })

        # macro answer keys (scorer-only): group-keyed %s, p, direction gated on sig
        macro_key = {}
        for it in theme.outcome_items:
            ki = key_items[it.code]
            macro_key[it.code] = {
                "split_axis": split.name,
                "group_order": [gA, gB],
                "groups": {gA: {"pct": ki["groups"][gA]["pct"]},
                           gB: {"pct": ki["groups"][gB]["pct"]}},
                "p_value": ki["p_value"],
                "significant": ki["significant"],
                # direction the scorer credits — "about_equal" unless significant (§3.4)
                "direction": ki["keyed_direction"],
                "raw_direction_if_ignoring_significance": ki["raw_direction"],
                "design_crosscheck": ki.get("design_crosscheck"),
            }

        # macro prompts, filled by DEFINITION (§4)
        macro_prose = theme.macro_prose_prompt.format(A=A_def, B=B_def)
        macro_number = theme.macro_number_prompt.format(A=A_def, B=B_def)
        assert_no_sizes(macro_prose, forbidden, f"{theme.key}/macro_prose")
        assert_no_sizes(macro_number, forbidden, f"{theme.key}/macro_number")

        cards["themes"][theme.key] = {
            "title": theme.title,
            "split": {"axis": split.name, "var": split.var,
                      "A_population": A_def, "B_population": B_def,
                      "group_order": [gA, gB],
                      "rationale": split.rationale},
            "paper_grounding": theme.paper_grounding,
            "outcome_group": theme.outcome_group,
            "conditioning_rationale": theme.conditioning_rationale,
            "conditioning_vars": list(theme.conditioning),
            "held_out_vars": theme.holdout_codes(),
            "rubric": {"dimensions": rubric_items,
                       "prose_scoring": "salience-weighted, asymmetric; weights in "
                                        "rubric.PROSE_WEIGHTS; coverage reported "
                                        "separately (§3.3)"},
            "shapes": {
                "micro": {
                    "tests": "representational accuracy of one respondent (§1.2)",
                    "model_facing": {
                        "conditioning": "this respondent's persona, restricted to the "
                                        "conditioning allow-list (rendered per-record "
                                        "by build_tasks.render_micro)",
                        "prompt_template": theme.micro_prompt},
                    "answer_key": "per respondent: held-out true value per item "
                                  "(outputs/survey/tasks/micro_keys.json)",
                    "scorer": "rubric.score_micro_prose",
                    "model_output": "OPEN SLOT — not run in this pipeline (§4)"},
                "macro_prose": {
                    "tests": "external consistency (vs survey) + internal (vs micro "
                             "aggregate) on direction (§1.2, §3.5)",
                    "model_facing": {"prompt": macro_prose},
                    "answer_key": macro_key,
                    "scorer": "rubric.score_macro_prose",
                    "model_output": "OPEN SLOT — not run in this pipeline (§4)"},
                "macro_number": {
                    "tests": "external + internal consistency on the explicit % (§1.2)",
                    "model_facing": {"prompt": macro_number},
                    "answer_key": macro_key,
                    "scorer": "rubric.score_macro_number",
                    "model_output": "OPEN SLOT — not run in this pipeline (§4)"},
            },
        }

    (OUT / "tasks.json").write_text(json.dumps(cards, indent=2))
    _write_cards_md(cards, keys)
    _write_task_md(cards, keys)

    # final hygiene confirmation across every model-facing string in the artifact
    n_leak = _sweep_model_facing(cards, forbidden)
    print(f"[tasks] {len(cards['themes'])} themes × 3 shapes assembled -> {OUT/'tasks.json'}")
    print(f"[tasks] leak guard: held-out ∩ conditioning empty for all themes ✓")
    print(f"[tasks] sample-size guard: 0 forbidden tokens across "
          f"{n_leak} model-facing strings ✓")
    print(f"[tasks] cards -> {OUT/'cards'}")
    print(f"[tasks] consolidated spec -> {ROOT/'TASK.md'}")
    return cards


def _sweep_model_facing(cards, forbidden):
    """Re-scan every model-facing string (defence in depth, §4 'grep ... expect zero')."""
    n = 0
    for tk, t in cards["themes"].items():
        for shape, sh in t["shapes"].items():
            mf = sh["model_facing"]
            for v in mf.values():
                assert_no_sizes(str(v), forbidden, f"{tk}/{shape}")
                n += 1
    return n


def _by_code():
    cols, meta = load_columns(str(clean_data.SAV))
    return {c.name: c for c in cols}, meta


def _prose_weights_table():
    w = rubric.PROSE_WEIGHTS
    return [
        "| prose did ↓ / truth → | salient (pos) | non-salient (neg) |",
        "|---|---|---|",
        f"| **asserts the salient state** | **{w[('assert_pos','pos')]:+g}** informative hit "
        f"| {w[('assert_pos','neg')]:+g} false positive |",
        f"| **asserts its absence** | {w[('assert_neg','pos')]:+g} denied a real one "
        f"| {w[('assert_neg','neg')]:+g} stated correct negative |",
        f"| **stays silent** | {w[('silent','pos')]:+g} recall miss (↓ coverage) "
        f"| **{w[('silent','neg')]:+g}** credit-by-omission |",
    ]


def _write_task_md(cards, keys):
    """Generate the consolidated top-level TASK.md (design + answer-key spec).

    Pulled from the frozen artifacts so it never drifts. Developer/scorer view —
    it carries the held-out estimates and Ns, which are NEVER shown to the model.
    Per theme: population (split), conditioning, prose rubric, number-task headline.
    """
    L = [
        "# Task layer — micro→macro simulation tasks",
        "",
        "_Generated by `pipeline/survey/tasks/build_tasks.py` from the frozen answer "
        "keys (`outputs/survey/tasks/`). This is a **design + answer-key** document "
        "(developer/scorer view): it shows held-out estimates and sample sizes, which "
        "are **never** shown to the model._",
        "",
        "Each survey respondent is rendered as a persona; the task layer turns those "
        "personas into prompts that measure how faithfully an LLM reproduces the "
        "surveyed population. There are **three themes**; each holds out one outcome "
        "battery and compares two sub-populations on a **different axis** "
        "(TASK_PLAYBOOK §1.3 — sex, university type, engineering discipline).",
        "",
        "## The three shapes (per theme)",
        "",
        "- **micro** — show one respondent's conditioning persona; ask for free prose "
        "about the held-out outcome; score the prose against *that respondent's* true "
        "per-item values.",
        "- **macro-prose** — name the two sub-populations *by definition*; ask for a "
        "prose comparison; score the **direction** claim per item.",
        "- **macro-number** — same two sub-populations; ask for explicit **percentages** "
        "per group per item; score against the frozen estimates.",
        "",
        "The model call is an **open slot** — this pipeline renders the tasks and answer "
        "keys but does not run a model (§4 \"show, don't run\"); the scorers in "
        "`rubric.py` are runnable.",
        "",
        "## Prose scoring (micro) — salience-weighted, asymmetric",
        "",
        "Only items the prose makes a claim about are scored; **coverage** (claimed ÷ "
        "total) is reported separately. The asymmetry up-weights an asserted true "
        "positive and discounts credit won by silence:",
        "",
        *_prose_weights_table(),
        "",
        "## Direction scoring (macro-prose) — gated on significance",
        "",
        "Each held-out item is scored on the model's **direction** claim ("
        "\"group A higher\"), credited **+1 only where the by-group gap is statistically "
        "significant** (Fisher exact, p<0.05). A non-significant gap's key is "
        "*about equal*, and asserting a direction there is penalised −1 — so the scorer "
        "never credits a fabricated direction (§3.4).",
        "",
        "## Significance & weighting",
        "",
        "Significance is **Fisher's exact test** (two-sided) on the 2×2 endorsed×group "
        "cell. The study ships **no survey weight**, so the design is simple random "
        "sampling (n_eff = n) and Fisher is design-exact; a design-based "
        "`R survey::svyglm` Wald cross-check agrees on **all 29 items** "
        "(`weighting.json`). An item counts as *endorsed* when answered 4–5 on its "
        "5-point scale. The keys are validated against the survey's own **ESRC "
        "End-of-Award Report** (jobdecid 87% / 93% female, industry 94%, reproduced to "
        "the decimal — `answer_keys.json → validation`).",
        "",
    ]

    for ti, tk in enumerate(cards["themes"], 1):
        t = cards["themes"][tk]
        kt = keys["themes"][tk]
        sp = t["split"]
        gA, gB = sp["group_order"]
        glabel = {g["key"]: g["label"] for g in kt["split"]["groups"]}
        gn = {g["key"]: g["n"] for g in kt["split"]["groups"]}
        mk = t["shapes"]["macro_prose"]["answer_key"]

        L += [
            "---", "",
            f"# Theme {ti} — {t['title']}", "",
            f"**Held-out outcome:** {t['outcome_group']}.", "",
            f"_{t['paper_grounding']}_", "",

            f"## Population (split: {sp['axis']})", "",
            f"- **A — {glabel[gA]}:** {sp['A_population']}",
            f"- **B — {glabel[gB]}:** {sp['B_population']}",
            "",
            f"_{sp['rationale']}_",
            "",
            f"Scorer-only group sizes: **{glabel[gA]}** n={gn[gA]}, "
            f"**{glabel[gB]}** n={gn[gB]} (never shown to the model — populations are "
            f"named by definition, §4).",
            "",

            "## Conditioning (shown in the micro persona)", "",
            t["conditioning_rationale"], "",
            f"Conditioning vars: `{'`, `'.join(t['conditioning_vars'])}`.  "
            f"Held-out (removed from the persona): `{'`, `'.join(t['held_out_vars'])}`.",
            "",

            "## Prose rubric (held-out items = rubric dimensions)", "",
            "Shared by the micro task (scored by salience, above) and the macro-prose "
            "task (scored on direction). Statements are **verbatim** from the survey "
            "instrument.", "",
            "| item | statement (verbatim) | salient \"pos\" state |",
            "|---|---|---|",
        ]
        for d in t["rubric"]["dimensions"]:
            L.append(f"| `{d['code']}` | {d['statement']} | {d['salient_state_pos']} |")

        L += [
            "",
            "## Number-task headline (explicit %s the model must produce)", "",
            f"The macro-number task asks for the % of each population who endorse each "
            f"item. These frozen estimates are the answer key; *direction* is keyed "
            f"only where significant.", "",
            f"| item | {glabel[gA]} % | {glabel[gB]} % | Fisher p | significant | keyed direction |",
            "|---|---|---|---|---|---|",
        ]
        for it in kt["items"]:
            p = it["p_value"]
            L.append(
                f"| `{it['code']}` | {it['groups'][gA]['pct']} | {it['groups'][gB]['pct']} "
                f"| {('%.4f' % p) if p is not None else 'n/a'} "
                f"| {'**yes**' if it['significant'] else 'no'} "
                f"| {mk[it['code']]['direction']} |")
        L.append("")

    (ROOT / "TASK.md").write_text("\n".join(L))


def _write_cards_md(cards, keys):
    """One markdown card per theme: model-facing prompts + the separated answer
    key. Scorer-side, so Ns are allowed."""
    cdir = OUT / "cards"
    cdir.mkdir(parents=True, exist_ok=True)
    for stale in cdir.glob("*.md"):           # drop cards for removed/renamed themes
        if stale.stem not in cards["themes"]:
            stale.unlink()
    for tk, t in cards["themes"].items():
        kt = keys["themes"][tk]
        sp = t["split"]
        gA, gB = sp["group_order"]
        gA_lbl = next(g["label"] for g in kt["split"]["groups"] if g["key"] == gA)
        gB_lbl = next(g["label"] for g in kt["split"]["groups"] if g["key"] == gB)
        L = [f"# Task theme — {t['title']}", "",
             f"**Split axis:** {sp['axis']} — **{gA_lbl}** ({sp['A_population']}) vs "
             f"**{gB_lbl}** ({sp['B_population']}).  \n_{sp['rationale']}_", "",
             f"**Outcome (held out):** {t['outcome_group']}", "",
             f"**Paper grounding.** {t['paper_grounding']}", "",
             f"**Conditioning (shown in micro persona).** {t['conditioning_rationale']}", "",
             f"Conditioning vars: `{'`, `'.join(t['conditioning_vars'])}`", "",
             f"Held-out vars: `{'`, `'.join(t['held_out_vars'])}`", "",
             "## Rubric dimensions (verbatim statements)", ""]
        for d in t["rubric"]["dimensions"]:
            L.append(f"- `{d['code']}` — \"{d['statement']}\"  \n"
                     f"  salient (pos): *{d['salient_state_pos']}*")
        L += ["", "## Model-facing prompts", "",
              "### micro (per respondent — persona prepended)", "",
              "```", t["shapes"]["micro"]["model_facing"]["prompt_template"], "```", "",
              "### macro — prose", "", "```",
              t["shapes"]["macro_prose"]["model_facing"]["prompt"], "```", "",
              "### macro — number", "", "```",
              t["shapes"]["macro_number"]["model_facing"]["prompt"], "```", "",
              "## Answer key — SCORER ONLY (not shown to the model)", "",
              f"| item | {gA_lbl} % | {gB_lbl} % | p | significant | keyed direction |",
              "|---|---|---|---|---|---|"]
        for it in kt["items"]:
            mk = t["shapes"]["macro_prose"]["answer_key"][it["code"]]
            p = it["p_value"]
            L.append(f"| `{it['code']}` | {it['groups'][gA]['pct']} "
                     f"| {it['groups'][gB]['pct']} "
                     f"| {('%.4f'%p) if p is not None else 'n/a'} "
                     f"| {'yes' if it['significant'] else 'no'} "
                     f"| {mk['direction']} |")
        L += ["", f"Denominators (scorer-only): {gA_lbl} n="
              f"{kt['split']['groups'][0]['n']}, {gB_lbl} n={kt['split']['groups'][1]['n']}.",
              f"Endorsement cut: {cards['endorsement_cut']}.", ""]
        (cdir / f"{tk}.md").write_text("\n".join(L))


if __name__ == "__main__":
    build()
