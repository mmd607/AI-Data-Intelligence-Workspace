"""Per-column profiling: dispatches to the right statistics module based on the column's
detected semantic type, plus the common facts every column gets regardless of type.
"""

from typing import Any

import pandas as pd

from app.profiling.categorical_stats import compute_categorical_stats
from app.profiling.column_types import detect_semantic_type
from app.profiling.datetime_stats import compute_datetime_stats
from app.profiling.numeric_stats import compute_numeric_stats
from app.profiling.schemas import ColumnProfile, SemanticType

_SAMPLE_VALUES_LIMIT = 5


def _json_safe(value: Any) -> Any:
    """Convert a single sample value to a plain, JSON-serializable Python value.

    `pandas.Series.tolist()` (used by `_sample_values` below) already converts
    int64/float64/bool NumPy scalars to native Python `int`/`float`/`bool` — so the only
    non-native type that can actually reach here is `pandas.Timestamp`, produced when
    `.tolist()` is called on a genuinely `datetime64`-dtyped column (rare from a plain CSV
    read, but a real case — see `column_types.py`'s `is_datetime64_any_dtype` branch).
    Anything else falls back to `str()`, conservatively, rather than guessing a JSON type.
    """
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value if isinstance(value, int | float | bool | str) else str(value)


def _sample_values(series: pd.Series) -> list[Any]:
    non_null = series.dropna()
    return [_json_safe(v) for v in non_null.head(_SAMPLE_VALUES_LIMIT).tolist()]


def profile_column(series: pd.Series, row_count: int) -> ColumnProfile:
    null_count = int(series.isna().sum())
    non_null_count = row_count - null_count
    unique_count = int(series.dropna().nunique())
    semantic_type = detect_semantic_type(series, row_count)

    numeric_stats = categorical_stats = datetime_stats = None
    if semantic_type == SemanticType.NUMERIC:
        numeric_stats = compute_numeric_stats(series)
    elif semantic_type in (SemanticType.CATEGORICAL, SemanticType.TEXT):
        categorical_stats = compute_categorical_stats(series, row_count)
    elif semantic_type == SemanticType.DATETIME:
        datetime_stats = compute_datetime_stats(series)
    # BOOLEAN and UNKNOWN: only the common fields below apply.

    return ColumnProfile(
        name=str(series.name),
        pandas_dtype=str(series.dtype),
        semantic_type=semantic_type,
        null_count=null_count,
        null_percentage=round((null_count / row_count) * 100, 4) if row_count else 0.0,
        unique_count=unique_count,
        unique_percentage=(
            round((unique_count / non_null_count) * 100, 4) if non_null_count else 0.0
        ),
        sample_values=_sample_values(series),
        numeric_stats=numeric_stats,
        categorical_stats=categorical_stats,
        datetime_stats=datetime_stats,
    )
