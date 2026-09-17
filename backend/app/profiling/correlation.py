"""Deterministic Pearson correlation between numeric column pairs.

Missing values are handled pairwise: for each column pair, rows where either value is
null are dropped before computing the coefficient (not a single dataset-wide dropna,
which would needlessly discard usable pairs). A pair is only included if it has at least
`minimum_observations` overlapping non-null rows and a well-defined coefficient (not NaN,
which happens when one column has zero variance in the overlapping subset) — an
insufficient pair is skipped, not fabricated. If the dataset doesn't have at least two
numeric columns, or every pair turns out to have insufficient overlapping data, the
result is an explicit `"insufficient_data"` status, never a failure and never a silently
empty-looking success.
"""

import warnings
from datetime import UTC, datetime
from itertools import combinations

import pandas as pd

from app.profiling.schemas import CorrelationPair, CorrelationResult

DEFAULT_MINIMUM_OBSERVATIONS = 3


def compute_correlation(
    dataset_id: str,
    df: pd.DataFrame,
    minimum_observations: int = DEFAULT_MINIMUM_OBSERVATIONS,
) -> CorrelationResult:
    numeric_columns = [
        c
        for c in df.columns
        if pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c])
    ]

    generated_at = datetime.now(UTC)

    if len(numeric_columns) < 2:
        return CorrelationResult(
            dataset_id=dataset_id,
            method="pearson",
            minimum_observations=minimum_observations,
            eligible_columns=numeric_columns,
            pairs=[],
            status="insufficient_data",
            message=(
                f"At least 2 numeric columns are required for correlation; found "
                f"{len(numeric_columns)}."
            ),
            generated_at=generated_at,
        )

    pairs: list[CorrelationPair] = []
    # Deterministic ordering: original column order, then itertools.combinations' own
    # stable (i, j) with i < j ordering.
    for col_a, col_b in combinations(numeric_columns, 2):
        paired = df[[col_a, col_b]].dropna()
        if len(paired) < minimum_observations:
            continue
        # A zero-variance column legitimately produces a NaN coefficient (division by a
        # zero standard deviation); that's an expected, handled outcome (the pair is
        # skipped below), not a real runtime problem, so the warning is suppressed here.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            coefficient = paired[col_a].corr(paired[col_b], method="pearson")
        if coefficient is None or pd.isna(coefficient):
            continue
        pairs.append(
            CorrelationPair(
                column_a=col_a,
                column_b=col_b,
                coefficient=round(float(coefficient), 6),
                observations=len(paired),
            )
        )

    if not pairs:
        return CorrelationResult(
            dataset_id=dataset_id,
            method="pearson",
            minimum_observations=minimum_observations,
            eligible_columns=numeric_columns,
            pairs=[],
            status="insufficient_data",
            message=(
                "No numeric column pair had at least "
                f"{minimum_observations} overlapping non-null observations with a "
                "well-defined correlation."
            ),
            generated_at=generated_at,
        )

    return CorrelationResult(
        dataset_id=dataset_id,
        method="pearson",
        minimum_observations=minimum_observations,
        eligible_columns=numeric_columns,
        pairs=pairs,
        status="computed",
        message=None,
        generated_at=generated_at,
    )
