"""Tests for `load_dataframe`, including the out-of-band corruption/removal edge cases
its own docstring documents (metadata present but raw file missing, or raw file
corrupted after upload) — realistic failure modes, not contrived ones.
"""

from pathlib import Path

import pytest

from app.ingestion.storage import StorageService
from app.profiling.errors import ProfilingError
from app.profiling.loader import load_dataframe


@pytest.fixture
def storage(tmp_path: Path) -> StorageService:
    return StorageService(base_dir=tmp_path / "uploads")


def test_loads_a_real_dataset(storage: StorageService) -> None:
    storage.save_raw_file("ds1", b"a,b\n1,2\n3,4\n")
    storage.write_metadata("ds1", {"id": "ds1"})

    df = load_dataframe("ds1", storage)
    assert list(df.columns) == ["a", "b"]
    assert len(df) == 2


def test_unknown_dataset_id_raises_not_found(storage: StorageService) -> None:
    with pytest.raises(ProfilingError) as exc_info:
        load_dataframe("does-not-exist", storage)
    assert exc_info.value.code == "dataset_not_found"
    assert exc_info.value.status_code == 404


def test_metadata_present_but_raw_file_missing_raises_not_found(storage: StorageService) -> None:
    # Simulates the raw file having been deleted out-of-band while metadata.json remains.
    storage.write_metadata("ds1", {"id": "ds1"})

    with pytest.raises(ProfilingError) as exc_info:
        load_dataframe("ds1", storage)
    assert exc_info.value.code == "dataset_not_found"


def test_corrupted_raw_file_raises_dataset_unreadable(storage: StorageService) -> None:
    # Simulates the stored CSV having been corrupted/truncated after a valid upload.
    storage.save_raw_file("ds1", b"")  # now empty on disk, despite valid metadata
    storage.write_metadata("ds1", {"id": "ds1"})

    with pytest.raises(ProfilingError) as exc_info:
        load_dataframe("ds1", storage)
    assert exc_info.value.code == "dataset_unreadable"
    assert exc_info.value.status_code == 400


def test_malformed_raw_file_raises_dataset_unreadable(storage: StorageService) -> None:
    # A row with more fields than the header, inconsistent with the surrounding rows,
    # reliably triggers pandas' C-engine ParserError (matching the Phase 02 fixture).
    malformed = b"id,name,age\n1,Alice,34\n2,Bob,29,extra,fields,here\n3,Carol,41\n"
    storage.save_raw_file("ds1", malformed)
    storage.write_metadata("ds1", {"id": "ds1"})

    with pytest.raises(ProfilingError) as exc_info:
        load_dataframe("ds1", storage)
    assert exc_info.value.code == "dataset_unreadable"
