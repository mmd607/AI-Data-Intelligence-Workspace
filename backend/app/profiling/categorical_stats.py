"""Deterministic statistics for a categorical/text-like column.

Percentages in `ValueFrequency` are relative to the dataset's total row count (matching
`ColumnProfile.null_percentage`/`unique_percentage`), not just the non-null count — so a
value's percentage plus the column's null percentage plus other values' percentages sum
to a consistent, comparable 100%.
"""

import pandas as pd

from app.profiling.schemas import CategoricalColumnStats, ValueFrequency

_TOP_VALUES_LIMIT = 10


def compute_categorical_stats(series: pd.Series, row_count: int) -> CategoricalColumnStats:
    non_null = series.dropna()
    value_counts = non_null.value_counts()  # deterministic: pure function of the input

    top_values = [
        ValueFrequency(
            value=str(value),
            count=int(count),
            percentage=round((count / row_count) * 100, 4) if row_count else 0.0,
        )
        for value, count in value_counts.head(_TOP_VALUES_LIMIT).items()
    ]

    rare_value_count = int((value_counts == 1).sum())

    return CategoricalColumnStats(
        cardinality=int(non_null.nunique()),
        top_values=top_values,
        rare_value_count=rare_value_count,
    )
