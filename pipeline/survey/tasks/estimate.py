"""Estimator + validator (TASK_PLAYBOOK §2) — derive the answer keys, validate
them, then FREEZE.

Reads the persona pipeline's own clean table (the frozen output of the *same*
loader the personas use — §2.4 "have the trace and any scorer read it rather than
recompute") and the .sav embedded value maps (via schema.load_columns), computes
the per-sub-population answer keys for every held-out outcome item, runs a real
two-sample significance test, and writes a single reviewable artifact that the
tasks and the trace point at.

VALIDATION (§2.1) — reproduce the numbers the source *does* print.
Two documents exist, and they are different. The journal paper (Powell et al.
2009) is qualitative (women-only interviews) and prints no survey numbers. But
the survey's quantitative results were written up in the **ESRC End-of-Award
Report (RES-000-23-0426)**, embedded in `downloads/q5723uguide.pdf` (the
"Research Report", pp. 23–34). That report DOES print survey marginals, and we
reproduce them here as the §2.1 reconciliation (`_validate_against_report`):
  * `jobdecid` (Q7E, "go on placement to help decide what to do after uni"):
    report says 87% of students agreed, women significantly more (93%). We get
    86.8% overall, 92.8% female — a decimal-level match that confirms the Q7
    coding, the missing-value handling, AND the by-group prevalence method behind
    every answer key.
  * `industry` (Q7F, "to get an idea of what industry is really like"): report
    94%; we get 93.9%.
  * Sample size N = 804 (asserted); subgroup denominators reproduced.
The report's **Table 1** (female% 37–52%, under-21% 94/41 by university) describes
the undergraduate **population/frame**, not the 804-respondent analysis sample
(they do not match it — confirmed), so it is contextual, not a validation target.
WHICH SPLIT IS THE GAP: an adversarial disclosure check (both sources, item by
item) confirmed each theme's split is one the sources do NOT report for its
outcome — degree-views by **placement**, influences by **university**, job-factors
by **discipline**. Sex was dropped: the sources state the by-sex directions outright
(see task_defs.py "WHY NOT SEX"). Coding is also validated upstream:
pipeline/survey/validate.py diffs every categorical cell against pyreadstat's
native decode.

WEIGHTING (§2.1 / §2.4). The study ships **no survey weight variable** (86
columns, none a design weight). Every respondent carries weight 1, so the
weighted estimate the playbook asks for *is* the unweighted estimate, the
effective sample size n_eff = (Σw)²/Σw² = n exactly (asserted), and the
design-based variance the playbook routes through R's `survey` reduces to
simple-random-sampling inference. We therefore use a library exact test directly
— **Fisher's exact** for the 2×2 proportion cells (§3.4 "exact tests for sparse
proportion cells ... don't hand-roll a normal approximation when a library is
present") — and document the equivalence rather than stand up an R boundary that
would return the same p on unit weights.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))          # pipeline/survey on path
import clean_data                              # noqa: E402  (same loader the personas use)
from schema import load_columns                # noqa: E402

import task_defs as T                          # noqa: E402
import weighted_estimates as W                 # noqa: E402  (design-based significance §2.4)

ROOT = HERE.parent.parent.parent
SURVEY_OUT = ROOT / "outputs/survey"
OUT = SURVEY_OUT / "tasks"

# Significance source-of-truth lives in weighted_estimates (the design-based
# module): the frozen test is Fisher exact (design-exact under SRS / unit weights,
# valid for sparse cells), corroborated by R survey::svyglm Wald. Reuse its
# constants so there is one definition.
ALPHA = W.ALPHA
MIN_CELL = W.MIN_CELL


def _load():
    """cols (with value maps from the .sav) + the frozen clean table."""
    cols, _ = load_columns(str(clean_data.SAV))
    by_code = {c.name: c for c in cols}
    clean = pd.read_csv(SURVEY_OUT / "clean_survey.csv")
    return by_code, clean


def _group_mask(clean, var, codes):
    return clean[var].isin(list(codes))


# Survey marginals the ESRC End-of-Award Report (RES-000-23-0426, in
# downloads/q5723uguide.pdf pp. 27–29) prints — our §2.1 reconciliation targets.
PUBLISHED = [
    {"var": "jobdecid", "scope": "all", "published_pct": 87,
     "source": "report p.27: '87% of students agreed they wanted to go on "
               "placement to help them decide what to do after university'"},
    {"var": "jobdecid", "scope": "female", "published_pct": 93,
     "source": "report p.28: 'female students were significantly more likely to agree (93%)'"},
    {"var": "industry", "scope": "all", "published_pct": 94,
     "source": "report p.29: '94% of male and female students agreed that they "
               "wanted to go on placement to get an idea of what industry is really like'"},
]


def _agree_pct(clean, var, scope):
    df = clean if scope == "all" else clean[_group_mask(clean, "gender", {2} if scope == "female" else {1})]
    s = df[var].dropna()
    n = int(s.isin([1, 2, 3, 4, 5]).sum())      # answered on the 5-point scale
    pos = int(s.isin(list(T.POS_CODES)).sum())
    return (round(100.0 * pos / n, 1) if n else None), n


def _validate_against_report(clean, tol=1.5):
    """§2.1: reproduce the report's published survey marginals from the raw data."""
    rows = []
    for t in PUBLISHED:
        got, n = _agree_pct(clean, t["var"], t["scope"])
        ok = got is not None and abs(got - t["published_pct"]) <= tol
        rows.append({**t, "reproduced_pct": got, "n_answered": n,
                     "within_tol": ok, "abs_diff": None if got is None else round(abs(got - t["published_pct"]), 1)})
        assert ok, (f"published marginal not reproduced: {t['var']}/{t['scope']} "
                    f"report={t['published_pct']}% got={got}% (tol={tol}). Investigate "
                    f"variable coding before trusting the new split (§2.1).")
    return rows


def validate(clean) -> dict:
    """§2.1: reproduce what is reproducible; record what the paper cannot check."""
    n = int(len(clean))
    assert n == 804, f"expected N=804 (study 5723), got {n}"
    sex = clean["gender"]
    n_female = int((sex == 2).sum())
    n_male = int((sex == 1).sum())
    n_missing = int(sex.isna().sum())
    assert n_female + n_male + n_missing == n
    # unit-weight design assumption, made explicit & checkable (§2.4):
    w = np.ones(n)
    n_eff = (w.sum() ** 2) / (w ** 2).sum()
    assert abs(n_eff - n) < 1e-9, "n_eff must equal n under unit weights"
    report_marginals = _validate_against_report(clean)
    # per-theme split group sizes (each theme cuts on a different axis, §1.3)
    split_denoms = {}
    for th in T.THEMES:
        s = th.split
        allcodes = {c for g in s.groups for c in g.codes}
        split_denoms[th.key] = {
            "axis": s.name, "var": s.var,
            "groups": {g.key: int(_group_mask(clean, s.var, g.codes).sum()) for g in s.groups},
            "not_in_either": int((~clean[s.var].isin(list(allcodes))).sum())}
    return {
        "reproduced_sample_size": {"expected": 804, "got": n, "match": True},
        "split_denominators_per_theme": split_denoms,
        "report_marginals_reproduced": report_marginals,
        "weighting": {"weight_variable": None,
                      "note": "study ships no design weight; every respondent "
                              "weight = 1; weighted estimate == unweighted "
                              "(proven: R survey::svymean reproduces the unweighted "
                              "prevalence); n_eff = (Σw)²/Σw² == n. Full design-based "
                              "provenance + rescale sanity check in weighting.json "
                              "(§2.4).",
                      "n_eff": round(n_eff, 4)},
        "source_cross_tab_validation": {
            "journal_paper": "Powell et al. (2009) — qualitative, prints no survey "
                             "numbers (the women-only interview arm).",
            "esrc_report": "RES-000-23-0426 (downloads/q5723uguide.pdf pp.23–34) — "
                           "prints survey marginals; reproduced above "
                           "(report_marginals_reproduced) as the §2.1 reconciliation.",
            "per_theme_split_is_the_gap": {
                "_verified_by": "adversarial disclosure check (both sources, item by "
                    "item, with a skeptic stage hunting for covering statements).",
                "degree_experience": "split on PLACEMENT; report discusses placement "
                    "heavily and the Q4 degree-views, but attributes their directions "
                    "to sex/discipline/university, never to placement status.",
                "routes_in": "split on UNIVERSITY; report makes the pre/post-1992 "
                    "divide its headline finding but never cross-tabulates the Q1 "
                    "influence battery by university.",
                "job_values": "split on DISCIPLINE; report cross-tabulates Q11 "
                    "job-factors by university (and other outcomes by department) "
                    "but never the job-factors by discipline.",
                "_sex_dropped": "sex FAILED the check — sources state the by-sex "
                    "directions outright (Fhelp 'women received more help ... the "
                    "survey showed this'; competitiveness 'not conclusive')."},
            "upstream_coding_check": "pipeline/survey/validate.py diffs every categorical "
                                     "cell against the .sav native decode."},
        "significance_test": "Fisher exact (two-sided) on the 2×2 endorsed×group cell — "
                             "design-exact under SRS / unit weights and valid for "
                             "sparse cells (§3.4); corroborated item-by-item by the "
                             "design-based R survey::svyglm Wald (weighting.json, §2.4).",
        "endorsement_cut": T.POS_CUT_NOTE,
        "min_subgroup_cell_for_testing": MIN_CELL,
    }


def _item_key(clean, by_code, item, brec, split):
    """Per-(group, item) macro key + the 5-category distribution, for THIS theme's
    split axis.

    Prevalence (% endorsed), answered-N per group, the full 1–5 distribution, the
    frozen Fisher-exact p + significance, and BOTH a `raw_direction` (which group is
    higher, regardless of significance) and a `keyed_direction` (the value the
    scorer credits — "about_equal" unless the gap is significant, §3.4). The
    significance + design-based cross-check come from `brec` (weighted_estimates),
    so there is a single significance source. `group_order` names the two groups
    (group_order[0] is the direction reference).

    Denominator note (§2.2): n_answered counts respondents whose answer is in 1–5;
    any sentinel (code 0/9, or an out-of-range code lacking a .sav value label) was
    already mapped to NaN by clean_data.py's label-based missing handling, so it is
    correctly excluded here rather than counted as "not endorsed".
    """
    code = item.code
    col = by_code[code]
    gA, gB = split.groups[0].key, split.groups[1].key
    groups = {gA: brec[gA], gB: brec[gB]}

    dist = {}
    for g in split.groups:
        answered = clean[_group_mask(clean, split.var, g.codes)][code].dropna()
        n_ans = int(len(answered))
        d = {}
        for codeval in (1, 2, 3, 4, 5):
            c = int((answered == codeval).sum())
            label = (col.value_map.get(codeval, str(codeval))
                     if isinstance(col.value_map, dict) else str(codeval))
            d[label] = {"code": codeval, "n": c,
                        "pct": round(100.0 * c / n_ans, 1) if n_ans else None}
        dist[g.key] = d

    p = brec["fisher_p"]
    significant = brec["significant"]
    aPct, bPct = groups[gA]["pct"], groups[gB]["pct"]
    if aPct is None or bPct is None or abs(aPct - bPct) < 1e-9:
        raw_direction = "about_equal"
    else:
        raw_direction = gA if aPct > bPct else gB
    keyed_direction = raw_direction if significant else "about_equal"
    return {
        "code": code,
        "statement": col.question_text or col.short_description,   # verbatim (§3.2)
        "short_description": col.short_description,
        "scale": col.scale_label,
        "pos_state": item.pos_state,
        "endorsed_means": T.POS_CUT_NOTE,
        "split_axis": split.name,
        "group_order": [gA, gB],
        "groups": groups,
        "p_value": None if p is None else float(p),
        "test": "fisher_exact_two_sided" if brec["testable"] else "not_tested_small_cell",
        "significant": significant,
        "keyed_direction": keyed_direction,        # what the scorer credits (gated)
        "raw_direction": raw_direction,            # which group is higher, ignoring significance
        "design_crosscheck": brec.get("design"),   # R survey Wald p, n_eff (§2.4)
        "distribution": dist,
    }


def _micro_keys(clean, by_code, theme):
    """Per-respondent held-out truth for the theme (the micro answer key, §3.1).

    Compact: {id, group, items:{code:{raw, pos}}}. `group` is the respondent's
    group on THIS theme's split axis (or null if not in either group). Labels are
    derivable from the same ColumnToText at read time, so we don't duplicate them.
    """
    out = []
    holdout = theme.holdout_codes()
    split = theme.split
    for _, row in clean.iterrows():
        sv = row[split.var]
        group = None if pd.isna(sv) else W._group_of(sv, split)
        items = {}
        for code in holdout:
            v = row[code]
            if pd.isna(v):
                items[code] = {"raw": None, "pos": None}      # held out but unanswered
            else:
                iv = int(v)
                items[code] = {"raw": iv, "pos": iv in T.POS_CODES}
        out.append({"id": int(row["ID"]), "group": group, "items": items})
    return out


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    by_code, clean = _load()
    val = validate(clean)

    # design-based significance + weighting provenance (runs the R survey boundary,
    # freezes weighting.json, returns the per-item significance bundle) — §2.4.
    bundle = W.freeze(clean, by_code, str(clean_data.SAV))

    themes_out = {}
    micro_out = {}
    for theme in T.THEMES:
        split = theme.split
        denoms = val["split_denominators_per_theme"][theme.key]["groups"]
        items = [_item_key(clean, by_code, it, bundle[it.code], split)
                 for it in theme.outcome_items]
        themes_out[theme.key] = {
            "title": theme.title,
            "outcome_group": theme.outcome_group,
            "split": {"var": split.var, "name": split.name,
                      "groups": [{"key": g.key, "label": g.label,
                                  "definition": g.definition, "n": denoms[g.key]}
                                 for g in split.groups]},
            "items": items,
        }
        micro_out[theme.key] = _micro_keys(clean, by_code, theme)

    keys = {
        "study": "UKDA SN 5723 — Women Engineering Students' Workplace Experiences, 2004–2005",
        "paper": "Powell, Bagilhole & Dainty (2009), 'How Women Engineers Do and Undo "
                 "Gender', Gender, Work & Organization 16(4)",
        "frozen_by": "pipeline/survey/tasks/estimate.py",
        "validation": val,
        "splits": {th.key: {"var": th.split.var, "name": th.split.name}
                   for th in T.THEMES},
        "themes": themes_out,
    }
    (OUT / "answer_keys.json").write_text(json.dumps(keys, indent=2))
    (OUT / "micro_keys.json").write_text(json.dumps(micro_out))   # compact; per-respondent

    # console summary (no model-facing text here — developer view, N allowed)
    print(f"[estimate] N={val['reproduced_sample_size']['got']}")
    for r in val["report_marginals_reproduced"]:
        print(f"[estimate] §2.1 report check: {r['var']}/{r['scope']} "
              f"reproduced={r['reproduced_pct']}% vs published={r['published_pct']}% "
              f"(Δ={r['abs_diff']}) {'✓' if r['within_tol'] else '✗'}")
    for tk, t in themes_out.items():
        sig = sum(1 for it in t["items"] if it["significant"])
        gs = "/".join(f"{g['key']}={g['n']}" for g in t["split"]["groups"])
        print(f"[estimate] theme {tk:18} split={t['split']['name']:22} ({gs}) "
              f"items={len(t['items'])} significant={sig}")
    print(f"[estimate] froze answer_keys.json + micro_keys.json -> {OUT}")
    return keys


if __name__ == "__main__":
    build()
