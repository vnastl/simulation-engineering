"""ColumnToText: the owned per-variable text renderer (CODEBOOK playbook §4.1).

One small, library-independent object per survey column. It knows how to turn
one respondent's raw value (a code, a number, a missing) into a phrase, and how
to wrap that phrase into a line of persona text. Nothing downstream is coupled
to a third-party class; the survey knowledge (value maps, descriptions, question
wording, missing semantics) is the expensive asset and lives in plain objects we
own (schema.py).

The split is the point (§4.1): `render_value` is the one fixed job (raw value ->
its label); `phrasing` decides how that label becomes a line.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Union

import math


# --- phrasings: (col, rendered_value) -> one line --------------------------
# A phrasing is just a function with this signature; write whatever a column
# needs. We keep three; the persona composer mostly uses `phrase_value_only`
# inside a sectioned layout, because a battery-heavy survey reads as boilerplate
# if every cell is a full sentence (§4.1, "the per-column default degrades in
# aggregate").

def phrase_statement(col: "ColumnToText", v: str) -> str:
    return f"The {col.short_description} is: {v}."


def phrase_value_only(col: "ColumnToText", v: str) -> str:
    return v


def phrase_qa(col: "ColumnToText", v: str) -> str:
    return f"Q: {col.question_text or col.short_description}\nA: {v}"


def _is_nan(value) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


@dataclass(frozen=True)
class ColumnToText:
    """Render one survey column for one respondent.

    Fields mirror the playbook §4.1 object, plus light grouping metadata
    (section / battery / scale_label) used by the sectioned persona composer.
    `value_map` is a {code: label} dict OR a callable fn(value)->str.
    """

    name: str                                   # column code in the raw table
    short_description: str                      # compact noun phrase, e.g. "high salary as a draw"
    question_text: str = ""                     # preserved question wording, lightly cleaned (§1.4)
    value_map: Optional[Union[dict, Callable]] = None   # {code: label} or fn(value)->str
    missing_value_fill: str = "No answer"       # shown for unmapped / NaN (§3.3)
    phrasing: Callable = phrase_value_only

    # grouping / provenance (used by the composer & trace, not by render_value)
    section: str = ""                           # questionnaire section header
    battery: str = ""                           # battery id (shared stem), "" if standalone
    battery_stem: str = ""                       # human stem for the battery block
    scale_label: str = ""                       # e.g. "5-point agree/disagree" (shown once per battery)
    origin: str = "elicited"                    # "elicited" | "metadata" (frame-supplied demographic)
    is_verdict_battery: bool = False             # statement rated on an agree/satisfaction/importance scale

    def render_value(self, value) -> str:
        """Raw value -> its label, no sentence. NaN -> missing_value_fill."""
        if _is_nan(value):
            return self.missing_value_fill
        if callable(self.value_map):
            return self.value_map(value)
        if self.value_map is not None:
            # codes can arrive as float (1.0) from SPSS; try both forms.
            if value in self.value_map:
                return self.value_map[value]
            for k in (_as_int(value), float(value) if _isnum(value) else value):
                if k in self.value_map:
                    return self.value_map[k]
            return self.missing_value_fill
        return str(value)

    def get_text(self, value) -> str:
        """Raw value -> full line via this column's phrasing."""
        return self.phrasing(self, self.render_value(value))

    def is_present(self, value) -> bool:
        """True if the respondent gave a real answer (not NaN / unmapped sentinel)."""
        if _is_nan(value):
            return False
        if isinstance(self.value_map, dict):
            return (value in self.value_map) or (_as_int(value) in self.value_map)
        return True


def _isnum(v) -> bool:
    return isinstance(v, (int, float)) and not (isinstance(v, float) and math.isnan(v))


def _as_int(v):
    try:
        if _isnum(v) and float(v).is_integer():
            return int(v)
    except (ValueError, TypeError):
        pass
    return v
