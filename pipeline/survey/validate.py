"""Validate the value maps against an independent oracle (CODEBOOK playbook §6).

pyreadstat can decode the .sav natively (read with apply_value_formats=True).
Render every categorical cell through OUR ColumnToText maps and diff against that
native decode over the whole 804x85 table.

Honesty about what this proves (§6): our maps and the native decode both read the
*same* embedded labels, so a zero-mismatch diff validates PLUMBING (float-vs-int
key coercion, lookup, missing handling, our label-typo fix) -- not the semantic
correctness of the labels themselves. Semantic confidence comes from the
reconciliation against the data (§2.1, in clean_data.py) and from reading whole
personas end-to-end. We report the diff for what it is.
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import pyreadstat

from schema import load_columns, LABEL_FIXES
import clean_data

SAV = str(clean_data.SAV)


def _is_nan(v):
    return v is None or (isinstance(v, float) and math.isnan(v))


def validate():
    cols, meta = load_columns(SAV)
    # native decode: pyreadstat applies the embedded value labels itself.
    df_lab, _ = pyreadstat.read_sav(SAV, user_missing=True, apply_value_formats=True)
    df_raw, _ = pyreadstat.read_sav(SAV, user_missing=True)

    total, mism = 0, []
    for c in cols:
        if not isinstance(c.value_map, dict):
            continue
        for i in range(len(df_raw)):
            raw = df_raw[c.name].iloc[i]
            native = df_lab[c.name].iloc[i]
            # native gives the label string for labelled codes, else the raw number.
            if _is_nan(raw):
                continue
            code = int(raw) if float(raw).is_integer() else raw
            if code not in c.value_map:
                continue  # sentinel -> our side returns missing fill; skip (not a label)
            total += 1
            ours = c.render_value(raw)
            nat = LABEL_FIXES.get(str(native), str(native))
            if ours != nat:
                mism.append((c.name, i, code, ours, nat))

    print(f"[validate] categorical cells checked vs native decode: {total}")
    print(f"[validate] mismatches: {len(mism)}")
    if mism:
        for m in mism[:20]:
            print("   ", m)
    print("[validate] NOTE: maps share the embedded source with the native decode,"
          " so this confirms PLUMBING, not label meaning (§6).")
    return len(mism)


if __name__ == "__main__":
    n = validate()
    raise SystemExit(1 if n else 0)
