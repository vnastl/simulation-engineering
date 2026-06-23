"""Cleaning layer (CODEBOOK playbook §5): per-table, not per-value.

  1. Load raw preserving missing distinctions (§3.2). The survey declares no
     SPSS user-missing ranges, so its sentinels (0, 9, 2, ...) live as ordinary
     numeric codes; they survive any read. We read with user_missing=True as the
     canonical read and round-trip a known sentinel to prove nothing flattened.
  2. Reconcile observed - listed against the frozen SENTINEL_ALLOW (§2.1/§2.2):
     a NEW unexplained code fails loudly here instead of rendering raw.
  3. Sentinels -> NaN per (column, code): any code with no value label is NaN.
  4. Write the clean table + a raw-codes table (the composer needs the raw code
     to classify *why* a field is missing -- blank vs not-applicable, §3.3).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

from schema import SPECS, SENTINEL_ALLOW, ID_COL, load_columns

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SAV = ROOT / "data/UKDA-5723-spss/spss/spss12/women_engineering_students_workplace_experiences.sav"
OUT = ROOT / "outputs/survey"


def _int_or_nan(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return np.nan
    return int(v) if float(v).is_integer() else v


def verify_missing_survives(df, meta):
    """§3.2 round-trip: confirm the read kept sentinel codes distinguishable."""
    checks = {
        "9 present on Q7 (reasons-for, branch N/A)": int((df["experien"] == 9).sum()),
        "9 present on Q8 (reasons-against, branch N/A)": int((df["wkexp"] == 9).sum()),
        "0 present on a Likert item (blank)": int((df["highsal"] == 0).sum()),
        "2 present on a Yes/No item (out-of-range)": int((df["placemen"] == 2).sum()),
    }
    for k, v in checks.items():
        assert v > 0, f"loader flattened missing? expected >0 for: {k}"
    return checks


def reconcile(df, cols):
    """§2.1/§2.2: observed - listed must equal the frozen allow-list per column."""
    report = {}
    for c in cols:
        s = df[c.name]
        observed = {_int_or_nan(x) for x in s.dropna().unique()}
        observed = {x for x in observed if not (isinstance(x, float) and math.isnan(x))}
        listed = set(c.value_map.keys()) if isinstance(c.value_map, dict) else set()
        unexplained = {x for x in (observed - listed)}
        allow = SENTINEL_ALLOW.get(c.name, set())
        extra = unexplained - allow            # codes we did NOT anticipate -> fail
        report[c.name] = sorted(unexplained, key=lambda z: (isinstance(z, str), z))
        assert not extra, (
            f"NEW unexplained code(s) {sorted(extra)} on '{c.name}' "
            f"(observed={sorted(observed)}, allowed sentinels={sorted(allow)}). "
            f"Investigate before shipping (CODEBOOK playbook §2.2).")
    return report


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    cols, meta = load_columns(str(SAV))
    df, _ = pyreadstat.read_sav(str(SAV), user_missing=True)

    rt = verify_missing_survives(df, meta)
    recon = reconcile(df, cols)

    keep = [ID_COL] + [c.name for c in cols]
    raw = df[keep].copy()
    raw[ID_COL] = raw[ID_COL].astype(int)

    # Sentinels -> NaN, per (column, code): any code lacking a value label is NaN.
    clean = raw.copy()
    for c in cols:
        valid = set(c.value_map.keys()) if isinstance(c.value_map, dict) else None
        if valid is not None:
            clean[c.name] = raw[c.name].map(lambda v, _ok=valid: (
                _int_or_nan(v) if _int_or_nan(v) in _ok else np.nan))

    # round the raw codes to ints (keep NaN) for a clean trace
    for c in cols:
        raw[c.name] = raw[c.name].map(_int_or_nan)

    clean.to_csv(OUT / "clean_survey.csv", index=False)
    raw.to_csv(OUT / "raw_codes.csv", index=False)
    (OUT / "reconciliation.json").write_text(json.dumps(
        {"round_trip": rt,
         "unexplained_codes_per_column": recon,
         "n_rows": int(len(df)), "n_cols_persona": len(cols)},
        indent=2, default=str))
    print(f"[clean] rows={len(df)} persona-cols={len(cols)}")
    print(f"[clean] round-trip sentinel check: {rt}")
    n_extra = {k: v for k, v in recon.items() if v}
    print(f"[clean] columns with sentinels reconciled: {len(n_extra)}/{len(cols)} "
          f"(all within frozen allow-list)")
    print(f"[clean] wrote clean_survey.csv, raw_codes.csv, reconciliation.json -> {OUT}")
    return clean, raw, cols, meta


if __name__ == "__main__":
    build()
