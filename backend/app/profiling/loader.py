"""Loads a dataset's DataFrame for profiling, given a dataset id.

Reuses Phase 02's `StorageService` through its public interface only
(`get_raw_file_path`/`read_metadata`) — this module never touches ingestion's internals.
No caching layer: each call re-reads the file from disk. Acceptable for a local-first v1
with no dataset-size ceiling problem yet (`02_DOCS/ARCHITECTURE.md` "Performance &
Scalability Notes"); revisit if profiling becomes a hot path.
"""

import pandas as pd

from app.ingestion.storage import StorageService
from app.profiling.errors import ProfilingError


def load_dataframe(dataset_id: str, storage: StorageService) -> pd.DataFrame:
    """Load the dataset's DataFrame, or raise a structured `ProfilingError`.

    Raises:
        ProfilingError: `dataset_not_found` (404) if no such dataset exists,
            `dataset_unreadable` (400) if the stored file can no longer be parsed as CSV
            (should not happen in practice, since Phase 02 validates on upload, but the
            file is re-read from disk on every profiling call, so this guards against it
            having been corrupted/removed out-of-band).
    """
    metadata = storage.read_metadata(dataset_id)
    if metadata is None:
        raise ProfilingError(
            code="dataset_not_found",
            message=f"No dataset with id '{dataset_id}'.",
            status_code=404,
        )

    path = storage.get_raw_file_path(dataset_id)
    if path is None:
        raise ProfilingError(
            code="dataset_not_found",
            message=f"No dataset with id '{dataset_id}'.",
            status_code=404,
        )

    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError as exc:
        raise ProfilingError(
            code="dataset_unreadable",
            message="The stored dataset has no header/columns and cannot be profiled.",
            status_code=400,
        ) from exc
    except pd.errors.ParserError as exc:
        raise ProfilingError(
            code="dataset_unreadable",
            message=f"The stored dataset could not be parsed: {exc}",
            status_code=400,
        ) from exc
