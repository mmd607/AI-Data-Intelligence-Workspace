"""Filesystem storage: raw file + JSON metadata sidecar per dataset.

Resolves `02_DOCS/decisions/DECISIONS_LOG.md` ADR-005 for Phase 02: no database. Layout is
`<base_dir>/<dataset_id>/original.csv` and `<base_dir>/<dataset_id>/metadata.json`.

Security note: `dataset_id` is always server-generated as a UUID4 (see
`app/api/datasets.py`), never derived from client input on write. On *read*, however,
`dataset_id` originates from a URL path parameter and is attacker-controlled — e.g.
`GET /api/v1/datasets/..%5c..%5csome-dir` reaches this class with a `dataset_id` containing
path separators. `pathlib` does not collapse `..` segments itself, but the OS does at the
syscall level (`Path.exists()`, `open()`, ...), so joining an unvalidated `dataset_id`
directly onto `base_dir` is a real path-traversal primitive, not merely a theoretical one.
`_dataset_dir` therefore rejects any id containing anything other than letters, digits,
hyphens, or underscores — a real UUID4 always matches this, `/`, `\\`, and `.` (so also
`..`) never do — and treats a rejected id as not found *before* it is ever joined into a
filesystem path. This is the structural defense, not `validation.py`'s filename
sanitization (which only produces a safe *display* string for the originally uploaded
filename, unrelated to `dataset_id`).
"""

import json
import re
from pathlib import Path

_VALID_DATASET_ID = re.compile(r"^[A-Za-z0-9_-]+$")


class StorageService:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _dataset_dir(self, dataset_id: str) -> Path | None:
        """The dataset's directory, or `None` if `dataset_id` contains anything other than
        letters, digits, hyphens, or underscores (real UUID4 ids always qualify).

        Returning `None` (rather than raising) lets every read path treat a malformed id
        exactly like a nonexistent dataset — no filesystem call is ever made with it.
        """
        if not _VALID_DATASET_ID.match(dataset_id):
            return None
        return self.base_dir / dataset_id

    @staticmethod
    def _invalid_dataset_id_error(dataset_id: str) -> ValueError:
        return ValueError(
            f"dataset_id must contain only letters, digits, hyphens, or underscores; "
            f"got {dataset_id!r}"
        )

    def save_raw_file(self, dataset_id: str, raw_bytes: bytes) -> Path:
        dataset_dir = self._dataset_dir(dataset_id)
        if dataset_dir is None:
            raise self._invalid_dataset_id_error(dataset_id)
        dataset_dir.mkdir(parents=True, exist_ok=True)
        path = dataset_dir / "original.csv"
        path.write_bytes(raw_bytes)
        return path

    def write_metadata(self, dataset_id: str, metadata: dict) -> None:
        dataset_dir = self._dataset_dir(dataset_id)
        if dataset_dir is None:
            raise self._invalid_dataset_id_error(dataset_id)
        dataset_dir.mkdir(parents=True, exist_ok=True)
        (dataset_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

    def read_metadata(self, dataset_id: str) -> dict | None:
        dataset_dir = self._dataset_dir(dataset_id)
        if dataset_dir is None:
            return None
        path = dataset_dir / "metadata.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def get_raw_file_path(self, dataset_id: str) -> Path | None:
        """Path to the stored raw file, or `None` if the dataset doesn't exist.

        Added in Phase 03 so the profiling module can read the dataset directly (via
        `pandas.read_csv`) without duplicating storage logic — accessed through this
        public method, never by reaching into `StorageService`'s internals, per
        `02_DOCS/ARCHITECTURE.md` "Module Boundaries".
        """
        dataset_dir = self._dataset_dir(dataset_id)
        if dataset_dir is None:
            return None
        path = dataset_dir / "original.csv"
        return path if path.exists() else None

    def list_metadata(self) -> list[dict]:
        if not self.base_dir.exists():
            return []
        results = []
        for child in sorted(self.base_dir.iterdir()):
            meta_path = child / "metadata.json"
            if meta_path.exists():
                results.append(json.loads(meta_path.read_text()))
        return results
