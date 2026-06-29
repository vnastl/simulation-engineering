"""Rubrics & scorers (TASK_PLAYBOOK §3).

Three scorers, one per task shape, sharing the SAME group→item dimensions (the
held-out outcome items from task_defs). They are *runnable* — the open slot in
this pipeline is the model call, not the scorer (§4 "show, don't run"): nothing
here fabricates a model answer; `build_tasks.py` renders the rubric and the
frozen answer key and leaves the model's answer + score an explicit slot. These
functions are what a downstream harness would call once a model answer exists.

Design points the playbook insists on:

  * Multi-dimensional, group→item — never a single summary score (§3.1). Each
    held-out item is scored; only the NUMBER task carries a headline %.
  * Statement / answer / correct-answer / verdict stay separate (§3.2) — enforced
    upstream by pulling the verbatim statement from the persona's ColumnToText and
    keeping the truth value as a separate field.
  * Prose scored asymmetrically by salience, weights in ONE place (§3.3).
  * Macro direction credited ONLY where the gap is significant (§3.4).
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# §3.3 — the salience-weighted asymmetric weights for MICRO prose, in one place.
# Rows = what the prose did about an item; cols = the item's truth for this
# respondent (pos = salient state holds; neg = it does not).
#
#                              truth pos        truth neg
#   asserts salient state      +2 (hit)         -1 (false positive)
#   asserts its absence        -1 (denied real) +1 (correct negative)
#   stays silent                0 (recall miss)  +0.25 (credit by omission)
#
# The asymmetry is the point: an asserted true positive (+2) is worth double a
# stated true negative (+1), and credit won by silence (+0.25) is heavily
# discounted, so a paragraph cannot bank free "true negatives" for everything it
# never mentions.
PROSE_WEIGHTS = {
    ("assert_pos", "pos"): +2.0,
    ("assert_pos", "neg"): -1.0,
    ("assert_neg", "pos"): -1.0,
    ("assert_neg", "neg"): +1.0,
    ("silent",     "pos"):  0.0,
    ("silent",     "neg"): +0.25,
}
PROSE_CLAIMS = ("assert_pos", "assert_neg", "silent")

# §3.4 — direction-claim weights for MACRO prose, in one place. The "truth" is
# the frozen direction, which is "about_equal" whenever the gap is NOT
# significant (so a non-significant gap can never be scored as real).
DIRECTION_WEIGHTS = {
    # claim matches a significant gap's direction
    ("match", "significant"): +1.0,
    # claim asserts a direction the data does not support (wrong way, or a
    # direction asserted where the truth is "about equal")
    ("wrong", "significant"): -1.0,
    ("wrong", "about_equal"): -1.0,
    # claim says "about equal" and the truth is "about equal"
    ("match", "about_equal"): +1.0,
    # silence on an item
    ("silent", "significant"):  0.0,
    ("silent", "about_equal"): +0.25,
}


def score_micro_prose(claims: dict, truths: dict) -> dict:
    """MICRO representational-accuracy score for one respondent (§3.1, §3.3).

    claims:  {item_code: "assert_pos"|"assert_neg"|"silent"} — what the model's
             prose claimed about each held-out item (parsed from the free text).
    truths:  {item_code: "pos"|"neg"} — this respondent's *true* value per item
             (the micro answer key; held out from the persona).

    Returns the summed salience score, plus coverage (claimed ÷ total) reported
    SEPARATELY (§3.3 — a paragraph won't mention every item).
    """
    total, claimed = 0.0, 0
    per_item = {}
    for code, truth in truths.items():
        claim = claims.get(code, "silent")
        if claim not in PROSE_CLAIMS:
            raise ValueError(f"bad claim {claim!r} for {code}")
        w = PROSE_WEIGHTS[(claim, truth)]
        per_item[code] = {"claim": claim, "truth": truth, "weight": w}
        total += w
        if claim != "silent":
            claimed += 1
    n = len(truths)
    return {"score": round(total, 3), "n_items": n,
            "coverage": round(claimed / n, 3) if n else 0.0,
            "per_item": per_item}


def score_macro_prose(direction_claims: dict, key_directions: dict) -> dict:
    """MACRO external-consistency score on direction (§3.4).

    direction_claims: {item_code: groupA|groupB|"about_equal"|"silent"} — which
                      population the model said is higher (or that they are equal).
                      Group keys are the theme's split (sex / university / discipline).
    key_directions:   {item_code: {"direction": groupA|groupB|"about_equal",
                                   "significant": bool}} — the frozen answer key.

    A direction claim is credited only where the gap is significant; a
    non-significant gap's key direction is "about_equal" (§3.4).
    """
    total, claimed = 0.0, 0
    per_item = {}
    for code, kd in key_directions.items():
        sig = kd["significant"]
        truth_dir = kd["direction"] if sig else "about_equal"
        truth_kind = "significant" if sig else "about_equal"
        claim = direction_claims.get(code, "silent")
        if claim == "silent":
            kind = "silent"
        elif claim == truth_dir:
            kind = "match"
        else:
            kind = "wrong"
        w = DIRECTION_WEIGHTS[(kind, truth_kind)]
        per_item[code] = {"claim": claim, "truth_direction": truth_dir,
                          "significant": sig, "kind": kind, "weight": w}
        total += w
        if claim != "silent":
            claimed += 1
    n = len(key_directions)
    return {"score": round(total, 3), "n_items": n,
            "coverage": round(claimed / n, 3) if n else 0.0,
            "per_item": per_item}


def score_macro_number(pct_claims: dict, key_estimates: dict) -> dict:
    """MACRO external-consistency on the next token: the explicit percentages.

    pct_claims:    {item_code: {groupA: p, groupB: p}} — model %s (0–100).
    key_estimates: {item_code: {"group_order": [gA, gB],
                                "groups": {gA: {"pct":..}, gB: {"pct":..}},
                                "significant": bool, "direction": ...}} — frozen.
                   Group keys are the theme's split (sex / university / discipline).

    Returns per-item absolute error per group, the model's implied direction, and
    whether it respected significance (claiming a gap only where one is real).
    This is an error metric, not a salience rubric — the number task is the one
    place a headline belongs (§3.1).
    """
    per_item, abs_errs = {}, []
    for code, ke in key_estimates.items():
        gA, gB = ke["group_order"]
        rec = {}
        for g in (gA, gB):
            true_p = ke["groups"][g]["pct"]
            claim_p = pct_claims.get(code, {}).get(g)
            err = None if claim_p is None else round(abs(claim_p - true_p), 1)
            if err is not None:
                abs_errs.append(err)
            rec[g] = {"model_pct": claim_p, "true_pct": true_p, "abs_error": err}
        # model's implied direction vs the key (significance-aware)
        cm = pct_claims.get(code, {})
        if cm.get(gA) is not None and cm.get(gB) is not None:
            diff = cm[gA] - cm[gB]
            model_dir = "about_equal" if abs(diff) < 1e-9 else (gA if diff > 0 else gB)
        else:
            model_dir = None
        true_dir = ke["direction"] if ke["significant"] else "about_equal"
        rec["model_direction"] = model_dir
        rec["true_direction"] = true_dir
        rec["direction_ok"] = (model_dir == true_dir) if model_dir else None
        per_item[code] = rec
    mae = round(sum(abs_errs) / len(abs_errs), 2) if abs_errs else None
    return {"mean_abs_error_pct": mae, "n_compared": len(abs_errs), "per_item": per_item}


# §3.5 — internal consistency is computed by the SAME comparators above, with the
# "key" replaced by the aggregate of the model's own micro answers over the
# subgroup. build_tasks emits the per-group/per-item structure so this needs no
# re-run; the comparison itself is a downstream step once micro answers exist.
