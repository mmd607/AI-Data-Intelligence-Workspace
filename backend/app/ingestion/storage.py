"""Filesystem storage: raw file + JSON metadata sidecar per dataset.

Resolves `02_DOCS/decisions/DECISIONS_LOG.md` ADR-005 for Phase 02: no database. Layout is
`<base_dir>/<dataset_id>/original.csv` and `<base_dir>/<dataset_id>/metadata.json`.

Security note: `dataset_id` is always server-generated (see `app/api/datasets.py`),
**never** derived from client input — this is what actually prevents path traversal,
structurally, regardless of what filename a client claims (`validation.py` only sanitizes
that filename for *display*, not for path construction).
"""

import json
from pathlib import Path


class StorageService:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _dataset_dir(self, dataset_id: str) -> Path:
        return self.base_dir / dataset_id

    def save_raw_file(self, dataset_id: str, raw_bytes: bytes) -> Path:
        dataset_dir = self._dataset_dir(dataset_id)
        dataset_dir.mkdir(parents=True, exist_ok=True)
        path = dataset_dir / "original.csv"
        path.write_bytes(raw_bytes)
        return path

    def write_metadata(self, dataset_id: str, metadata: dict) -> None:
        dataset_dir = self._dataset_dir(dataset_id)
        dataset_dir.mkdir(parents=True, exist_ok=True)
        (dataset_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

    def read_metadata(self, dataset_id: str) -> dict | None:
        path = self._dataset_dir(dataset_id) / "metadata.json"
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
        path = self._dataset_dir(dataset_id) / "original.csv"
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
