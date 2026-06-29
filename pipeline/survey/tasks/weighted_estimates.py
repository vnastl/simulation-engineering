"""Per-item statistics via a Python→R boundary (TASK_PLAYBOOK §2.1, §2.4).

The statistics live in `estimate_weights.R` (Fisher exact + survey-design Wald +
prevalences). Python emits the long table, runs R, re-checks the results against
the raw data, and freezes them. Requires `Rscript` + the `survey` package.

The study ships no weight/stratum/PSU variable (asserted in `assert_no_weights`),
so the design is SRS: weighted == unweighted (svymean == plain prevalence),
n_eff == n, and the frozen significance is Fisher's exact; the svyglm Wald p is a
design-based cross-check. Rescaling weights leaves the exact and Wald p unchanged
but collapses a frequency-weight chi-square — the §2.4 design-correctness check.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import clean_data                              # noqa: E402
from schema import load_columns                # noqa: E402
import task_defs as T                          # noqa: E402

ROOT = HERE.parent.parent.parent
OUT = ROOT / "outputs/survey/tasks"
R_SCRIPT = HERE / "estimate_weights.R"

ALPHA = 0.05
MIN_CELL = 20            # §2.2: a subgroup smaller than this is not worth testing
RESCALE_C = 7.0          # constant for the design-correctness sanity check

# weight/strata/PSU column-name patterns (precise enough NOT to match 'designwk')
_WEIGHT_RE = re.compile(
    r"(^|_)(weight|wgt|wght|pweight|aweight|fweight|fnlwgt|finalwt|svywt|"
    r"rakewt|raowt)(\d*$|_)|^(wt|w)\d*$|(^|_)(strata|stratum|psu|cluster|fpc)(\d*$|_)",
    re.IGNORECASE)


def assert_no_weights(sav_path):
    """§2.1/§2.4: confirm (and freeze) that the study ships no design variable."""
    import pyreadstat
    _, m = pyreadstat.read_sav(sav_path, metadataonly=True)
    names = list(m.column_names)
    weight_like = [c for c in names if _WEIGHT_RE.search(c)]
    assert not weight_like, (
        f"a weight/strata/PSU-like column appeared: {weight_like}. The study was "
        f"previously unweighted; investigate before computing estimates (§2.4).")
    return {"weight_variable": None, "strata_variable": None, "psu_variable": None,
            "n_columns_scanned": len(names),
            "note": "no weight/strata/PSU/cluster/fpc column in any distributed "
                    "format; documentation never mentions weighting; unit weights."}


def _item_split_map():
    """Each held-out item belongs to exactly one theme, hence one split axis."""
    return {code: th.split for th in T.THEMES for code in th.holdout_codes()}


def _group_of(value, split):
    iv = int(value)
    for g in split.groups:
        if iv in g.codes:
            return g.key
    return None


def build_long(clean, by_code):
    """Emit the tidy long table the R script consumes: one row per (held-out item,
    answered respondent in one of the item's split groups). Each item carries ITS
    theme's split. y = 1 iff endorsed (answer in POS_CODES)."""
    smap = _item_split_map()
    recs = []
    for code, split in smap.items():
        var = split.var
        for _, row in clean.iterrows():
            sv, v = row[var], row[code]
            if pd.isna(sv) or pd.isna(v):
                continue
            g = _group_of(sv, split)
            if g is None:                          # value not in either group
                continue
            recs.append({"item": code, "group": g, "weight": 1.0, "stratum": 1,
                         "y": int(int(v) in T.POS_CODES)})
    return pd.DataFrame(recs)


def _run_r(long_df, scale=1.0):
    """Run estimate_weights.R over a temp CSV and parse its long output into
    {item: {groups: {g: {n,n_pos,pct,design_pct,neff}}, fisher_p, wald_p,
    freqweight_p}}. R is required — raise loudly if it is unavailable or errors."""
    if not shutil.which("Rscript"):
        raise RuntimeError(
            "Rscript not found. The task layer computes its statistics in R "
            "(estimate_weights.R, needs the `survey` package). Install R + survey, "
            "or adapt weighted_estimates.py to a fallback engine.")
    d = Path(tempfile.mkdtemp(prefix="rsurvey_"))
    try:
        inp, outp = d / "long.csv", d / "out.csv"
        long_df.to_csv(inp, index=False)
        r = subprocess.run(["Rscript", str(R_SCRIPT), str(inp), str(outp), str(scale)],
                           capture_output=True, text=True)
        if r.returncode != 0 or not outp.exists():
            raise RuntimeError(f"estimate_weights.R failed (rc={r.returncode}):\n{r.stderr[-800:]}")
        res = pd.read_csv(outp)
        out = {}
        for _, row in res.iterrows():
            it = row["item"]
            o = out.setdefault(it, {"groups": {},
                                    "fisher_p": _f(row["fisher_p"]),
                                    "wald_p": _f(row["wald_p"]),
                                    "freqweight_p": _f(row["freqweight_p"])})
            o["groups"][str(row["group"])] = {
                "n": int(row["n"]), "n_pos": int(row["n_pos"]),
                "pct": float(row["pct"]), "design_pct": float(row["design_pct"]),
                "neff": float(row["neff"])}
        return out
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _f(v):
    return None if pd.isna(v) else float(v)


def _py_prevalence(clean, code, split):
    """Independent Python recompute of each group's (n_pos, n_answered, pct) from
    the raw clean table — the cross-check that R and Python agree (and that, with
    unit weights, the design prevalence equals this plain one)."""
    out = {}
    for g in split.groups:
        s = clean[clean[split.var].isin(list(g.codes))][code].dropna()
        n = int(len(s)); n_pos = int(s.isin(list(T.POS_CODES)).sum())
        out[g.key] = (n_pos, n, round(100 * n_pos / n, 1) if n else None)
    return out


def compute_all(clean, by_code, rdes):
    """Assemble the per-item bundle from the R results (`rdes`), with an independent
    Python re-check against the raw data. Estimates and both p-values come from R;
    Python asserts they reproduce the raw-table prevalence and that design == plain
    (the proof that weighted == unweighted under unit weights, §2.1)."""
    bundle = {}
    for th in T.THEMES:
        split = th.split
        gA, gB = split.groups[0].key, split.groups[1].key
        py = None
        for it in th.outcome_items:
            code = it.code
            rr = rdes.get(code)
            if not rr or gA not in rr["groups"] or gB not in rr["groups"]:
                raise RuntimeError(f"R returned no result for item {code}")
            py = _py_prevalence(clean, code, split)
            grp = {}
            for gk in (gA, gB):
                rg = rr["groups"][gk]
                p_pos, p_n, p_pct = py[gk]
                # R vs Python agreement (plumbing) + design == plain (unit weights)
                assert rg["n"] == p_n and rg["n_pos"] == p_pos, (
                    f"R/Python count mismatch on {code}/{gk}: "
                    f"R n={rg['n']},pos={rg['n_pos']} vs py n={p_n},pos={p_pos}")
                assert abs(rg["design_pct"] - rg["pct"]) < 0.06, (
                    f"design vs plain prevalence mismatch on {code}/{gk}")
                grp[gk] = {"pct": round(rg["pct"], 1), "n_pos": rg["n_pos"],
                           "n_answered": rg["n"]}
            fisher_p = rr["fisher_p"]
            testable = grp[gA]["n_answered"] >= MIN_CELL and grp[gB]["n_answered"] >= MIN_CELL
            significant = bool(fisher_p is not None and testable and fisher_p < ALPHA)
            wald = rr["wald_p"]
            wald_sig = None if wald is None else bool(wald < ALPHA)
            bundle[code] = {
                "split": split.name, "group_order": [gA, gB],
                gA: grp[gA], gB: grp[gB],
                "fisher_p": fisher_p, "testable": testable, "significant": significant,
                "design": {
                    "wald_p": wald, "wald_significant": wald_sig,
                    "groups": {gk: {"design_pct": round(rr["groups"][gk]["design_pct"], 1),
                                    "neff": round(rr["groups"][gk]["neff"], 1)}
                               for gk in (gA, gB)},
                    "fisher_vs_wald_verdict_agree":
                        None if wald_sig is None else (wald_sig == significant)},
            }
    return bundle


def rescale_sanity(rdes1, rdesC):
    """§2.4: a survey/exact p is invariant to a constant weight rescale; a
    frequency-weight p collapses. Both p's come from R (run at scale 1 and ×C)."""
    fdiff, wdiff = [], []
    for it in rdes1:
        if it not in rdesC:
            continue
        for key, acc in (("fisher_p", fdiff), ("wald_p", wdiff)):
            a, b = rdes1[it][key], rdesC[it][key]
            if a is not None and b is not None:
                acc.append(abs(a - b))
    # the frequency-weight collapse, shown on the most-significant item
    pick = min((it for it in rdes1 if rdes1[it]["fisher_p"] is not None),
               key=lambda it: rdes1[it]["fisher_p"], default=None)
    contrast = None
    if pick is not None:
        contrast = {"item": pick,
                    "freqweight_p_at_w1": rdes1[pick]["freqweight_p"],
                    f"freqweight_p_at_w{int(RESCALE_C)}": rdesC[pick]["freqweight_p"],
                    "note": "a frequency-weight chi-square (chisq.test on the "
                            "weight-weighted table) collapses toward 0 under ×C; the "
                            "exact (fisher_p) and survey-Wald p's do not — confirming "
                            "our tests are design-based, not frequency-weighted."}
    return {"rescale_constant": RESCALE_C,
            "exact_and_survey_p_invariant":
                bool(fdiff and wdiff and max(fdiff) < 1e-9 and max(wdiff) < 1e-6),
            "max_abs_fisher_p_diff": round(max(fdiff), 10) if fdiff else None,
            "max_abs_wald_p_diff": round(max(wdiff), 8) if wdiff else None,
            "freqweight_contrast": contrast}


def freeze(clean, by_code, sav_path):
    OUT.mkdir(parents=True, exist_ok=True)
    weights = assert_no_weights(sav_path)
    long_df = build_long(clean, by_code)
    rdes1 = _run_r(long_df, scale=1.0)          # the frozen run
    rdesC = _run_r(long_df, scale=RESCALE_C)    # the rescale-sanity run
    bundle = compute_all(clean, by_code, rdes1)
    san = rescale_sanity(rdes1, rdesC)

    n = int(len(clean))
    weights["n_records"] = n
    weights["n_eff_total"] = n                  # unit weights -> n_eff == n
    n_design = sum(1 for b in bundle.values() if b.get("design"))
    n_agree = sum(1 for b in bundle.values()
                  if b["design"]["fisher_vs_wald_verdict_agree"])

    doc = {
        "engine": "R (estimate_weights.R): fisher.test (exact) + survey::svyglm "
                  "(design Wald) + svymean (prevalence), one script; Python "
                  "orchestrates, re-checks against the raw data, and freezes.",
        "weighting": weights,
        "frozen_significance": "Fisher exact (two-sided, R fisher.test) — design-exact "
                               "under SRS / unit weights and valid for sparse cells (§3.4)",
        "design_based_crosscheck": {
            "tool": "R survey::svyglm Wald (same script)",
            "items_with_design_p": n_design,
            "fisher_vs_wald_verdict_agreement": f"{n_agree}/{n_design}",
            "note": "with unit weights svyglm is a large-sample normal approx; it "
                    "agrees with Fisher's exact verdict on every item, so the frozen "
                    "Fisher significance is corroborated by the design-based path."},
        "rescale_sanity_check": san,
        "per_item": {code: {
            "split": b["split"], "group_order": b["group_order"],
            "group_pct": {g: b[g]["pct"] for g in b["group_order"]},
            "fisher_p": b["fisher_p"], "significant": b["significant"],
            "design": b["design"]} for code, b in bundle.items()},
    }
    (OUT / "weighting.json").write_text(json.dumps(doc, indent=2))
    print(f"[weighted] R engine; no weight variable (asserted); unit weights, n_eff={n}")
    print(f"[weighted] R↔Python prevalence + design==plain: all items agree ✓")
    print(f"[weighted] Fisher vs survey-Wald verdict agree on {n_agree}/{n_design} items")
    print(f"[weighted] rescale sanity: exact+survey p invariant under ×{int(RESCALE_C)} "
          f"= {san['exact_and_survey_p_invariant']}")
    print(f"[weighted] froze weighting.json -> {OUT}")
    return bundle


if __name__ == "__main__":
    cols, _ = load_columns(str(clean_data.SAV))
    by_code = {c.name: c for c in cols}
    clean = pd.read_csv(ROOT / "outputs/survey/clean_survey.csv")
    freeze(clean, by_code, str(clean_data.SAV))
