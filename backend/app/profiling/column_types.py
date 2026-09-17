"""Conservative semantic type classification for a single column.

Per `01_PHASES/PHASE_03_DATA_PROFILING_VISUALIZATION/PHASE_PROMPT.md`: "Do not make
aggressive semantic assumptions. If a type cannot be reliably inferred, preserve the raw
pandas classification and mark semantic interpretation conservatively." The raw pandas
dtype (`column.dtype`) is always reported alongside the semantic type on `ColumnProfile`
(`schemas.py`) — this module only adds a best-effort, deterministic *interpretation* on
top of it, never replaces it.
"""

import re

import pandas as pd
from pandas.api import types as pdtypes

from app.profiling.schemas import SemanticType

_DATETIME_PARSE_SUCCESS_THRESHOLD = 0.9
_PLAIN_INTEGER_RE = re.compile(r"^-?\d+$")
_TEXT_UNIQUE_RATIO_THRESHOLD = 0.95
_TEXT_MIN_UNIQUE_COUNT = 20


def _looks_like_plain_integers(non_null: pd.Series) -> bool:
    """True if the large majority of values are bare integers (`"42"`, not `"2024-01-01"`).

    Guards against `pandas.to_datetime` happily reinterpreting integer-looking strings as
    dates (e.g. epoch-like or ambiguous numeric strings), which would be an aggressive,
    likely-wrong semantic assumption.
    """
    if non_null.empty:
        return False
    sample = non_null.astype(str).head(200)
    matches = sample.str.match(_PLAIN_INTEGER_RE)
    return bool(matches.mean() >= _DATETIME_PARSE_SUCCESS_THRESHOLD)


def _is_datetime_like(non_null: pd.Series) -> bool:
    if non_null.empty:
        return False
    if _looks_like_plain_integers(non_null):
        return False
    parsed = pd.to_datetime(non_null, errors="coerce", format="mixed")
    success_ratio = parsed.notna().mean()
    return bool(success_ratio >= _DATETIME_PARSE_SUCCESS_THRESHOLD)


def detect_semantic_type(series: pd.Series, row_count: int) -> SemanticType:
    """Deterministic, conservative semantic classification.

    Order of checks: boolean and numeric dtypes are unambiguous and checked first;
    datetime dtype (rare from a plain CSV read, but handled) is checked next; everything
    else (`object` dtype) is probed for a high-confidence datetime match, then split
    between categorical and text by cardinality, falling back to `UNKNOWN` only if none
    of the above confidently apply.
    """
    if pdtypes.is_bool_dtype(series):
        return SemanticType.BOOLEAN

    if pdtypes.is_numeric_dtype(series):
        return SemanticType.NUMERIC

    if pdtypes.is_datetime64_any_dtype(series):
        return SemanticType.DATETIME

    non_null = series.dropna()

    if pdtypes.is_object_dtype(series) or pdtypes.is_string_dtype(series):
        if _is_datetime_like(non_null):
            return SemanticType.DATETIME

        if row_count == 0:
            return SemanticType.CATEGORICAL

        unique_count = int(non_null.nunique())
        unique_ratio = unique_count / row_count if row_count else 0.0
        if unique_ratio >= _TEXT_UNIQUE_RATIO_THRESHOLD and unique_count >= _TEXT_MIN_UNIQUE_COUNT:
            return SemanticType.TEXT
        return SemanticType.CATEGORICAL

    # Anything else (e.g. a dtype pandas itself couldn't cleanly resolve) — conservative
    # fallback per the phase prompt's explicit instruction, rather than guessing.
    return SemanticType.UNKNOWN
