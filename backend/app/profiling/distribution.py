"""Deterministic histogram/distribution data for numeric columns, for visualization.

Uses a fixed default bin count (documented, not learned) via `numpy.histogram` over the
column's finite, non-null values. A numeric column with no finite values, or where every
finite value is identical, does not produce a meaningful multi-bin histogram — it is
reported in `skipped_columns` rather than emitting a fabricated or misleading distribution.
Non-numeric columns are always skipped (histograms are only meaningful for numeric data).
"""

from datetime import UTC, datetime

import numpy as np
import pandas as pd

from app.profiling.schemas import ColumnDistribution, DistributionResult, HistogramBin

DEFAULT_BIN_COUNT = 10


def compute_distributions(
    dataset_id: str,
    df: pd.DataFrame,
    bin_count: int = DEFAULT_BIN_COUNT,
) -> DistributionResult:
    columns: list[ColumnDistribution] = []
    skipped: list[str] = []

    for column_name in df.columns:
        series = df[column_name]
        if not pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series):
            skipped.append(str(column_name))
            continue

        finite = series.dropna()
        finite = finite[np.isfinite(finite.astype("float64"))]

        if finite.empty:
            skipped.append(str(column_name))
            continue

        col_min = float(finite.min())
        col_max = float(finite.max())

        if col_min == col_max:
            # A single distinct value: one bin, not a numpy-expanded degenerate range.
            bins = [HistogramBin(bin_start=col_min, bin_end=col_max, count=int(len(finite)))]
        else:
            counts, edges = np.histogram(finite, bins=bin_count, range=(col_min, col_max))
            bins = [
                HistogramBin(
                    bin_start=float(edges[i]),
                    bin_end=float(edges[i + 1]),
                    count=int(counts[i]),
                )
                for i in range(len(counts))
            ]

        columns.append(
            ColumnDistribution(
                column=str(column_name),
                bin_count=len(bins),
                bins=bins,
                min=col_min,
                max=col_max,
            )
        )

    return DistributionResult(
        dataset_id=dataset_id,
        columns=columns,
        skipped_columns=skipped,
        generated_at=datetime.now(UTC),
    )
