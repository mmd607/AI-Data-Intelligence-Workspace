"""Deterministic descriptive statistics for a numeric column.

Design note: descriptive statistics (min/max/mean/median/std/quartiles) are computed over
the **finite** subset of non-null values. Infinite values are counted separately
(`infinite_count`) and flagged as a data-quality finding (`quality.py`) rather than being
allowed to propagate `inf`/`-inf`/`NaN` into the JSON response — those aren't valid JSON
number tokens, and letting one infinite value silently turn every descriptive statistic
into `inf` would misrepresent the rest of an otherwise well-behaved column. Zero/negative
counts are computed over *all* non-null values (a `0` or a `-inf` is still meaningfully
zero/negative).
"""

import numpy as np
import pandas as pd

from app.profiling.schemas import NumericColumnStats


def _safe_float(value: float) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)


def compute_numeric_stats(series: pd.Series) -> NumericColumnStats:
    non_null = series.dropna()
    is_finite = np.isfinite(non_null.astype("float64"))
    finite = non_null[is_finite]

    if finite.empty:
        min_v = max_v = mean_v = median_v = std_v = q1_v = q3_v = iqr_v = None
    else:
        q1_raw = float(finite.quantile(0.25))
        q3_raw = float(finite.quantile(0.75))
        min_v = _safe_float(finite.min())
        max_v = _safe_float(finite.max())
        mean_v = _safe_float(finite.mean())
        median_v = _safe_float(finite.median())
        std_v = _safe_float(finite.std()) if len(finite) > 1 else None
        q1_v = _safe_float(q1_raw)
        q3_v = _safe_float(q3_raw)
        iqr_v = _safe_float(q3_raw - q1_raw)

    return NumericColumnStats(
        min=min_v,
        max=max_v,
        mean=mean_v,
        median=median_v,
        std=std_v,
        q1=q1_v,
        q3=q3_v,
        iqr=iqr_v,
        zero_count=int((non_null == 0).sum()),
        negative_count=int((non_null < 0).sum()),
        infinite_count=int((~is_finite).sum()),
    )
