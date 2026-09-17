"""Dataset-level profile: orchestrates per-column profiling plus dataset-wide facts."""

from datetime import UTC, datetime

import pandas as pd

from app.profiling.column_profile import profile_column
from app.profiling.schemas import DatasetProfile, MissingValueSummary


def build_dataset_profile(dataset_id: str, df: pd.DataFrame) -> DatasetProfile:
    row_count = int(len(df))
    column_count = int(len(df.columns))
    total_cells = row_count * column_count

    total_missing_cells = int(df.isna().sum().sum()) if column_count else 0
    columns_with_missing = int((df.isna().sum() > 0).sum()) if column_count else 0
    duplicate_row_count = int(df.duplicated().sum()) if row_count else 0

    columns = [profile_column(df[column], row_count) for column in df.columns]

    return DatasetProfile(
        dataset_id=dataset_id,
        row_count=row_count,
        column_count=column_count,
        memory_usage_bytes=int(df.memory_usage(deep=True).sum()),
        duplicate_row_count=duplicate_row_count,
        duplicate_row_percentage=(
            round((duplicate_row_count / row_count) * 100, 4) if row_count else 0.0
        ),
        missing=MissingValueSummary(
            total_missing_cells=total_missing_cells,
            missing_percentage=(
                round((total_missing_cells / total_cells) * 100, 4) if total_cells else 0.0
            ),
            columns_with_missing=columns_with_missing,
        ),
        columns=columns,
        generated_at=datetime.now(UTC),
    )
