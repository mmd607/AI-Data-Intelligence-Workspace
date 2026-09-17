"""Dataset ingestion endpoints.

Thin router per `02_DOCS/ARCHITECTURE.md` "Module Boundaries": validates/shapes only,
all logic lives in `app.ingestion`.
"""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, UploadFile

from app.config import Settings, get_settings
from app.ingestion.errors import IngestionError
from app.ingestion.parsing import parse_csv
from app.ingestion.schemas import DatasetMetadata, DatasetSummary
from app.ingestion.storage import StorageService
from app.ingestion.validation import sanitize_filename, validate_extension, validate_size

router = APIRouter(prefix="/datasets", tags=["datasets"])


def get_storage_service(settings: Settings = Depends(get_settings)) -> StorageService:
    """A fresh `StorageService` per request, pointed at the configured data directory.

    Overridable in tests via `app.dependency_overrides[get_storage_service]` for full
    filesystem isolation from the real local `backend/data/uploads/` directory.
    """
    return StorageService(base_dir=Path(settings.data_dir))


@router.post("", response_model=DatasetMetadata, status_code=201)
async def upload_dataset(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    storage: StorageService = Depends(get_storage_service),
) -> DatasetMetadata:
    original_filename = sanitize_filename(file.filename)
    validate_extension(original_filename)

    raw_bytes = await file.read()
    validate_size(len(raw_bytes), settings.max_upload_size_bytes)

    parsed = parse_csv(raw_bytes)

    dataset_id = str(uuid4())
    metadata = DatasetMetadata(
        id=dataset_id,
        original_filename=original_filename,
        uploaded_at=datetime.now(UTC),
        size_bytes=len(raw_bytes),
        row_count=parsed.row_count,
        column_count=parsed.column_count,
        columns=parsed.columns,
        missing_value_count=parsed.missing_value_count,
        duplicate_row_count=parsed.duplicate_row_count,
    )

    storage.save_raw_file(dataset_id, raw_bytes)
    storage.write_metadata(dataset_id, metadata.model_dump(mode="json"))

    return metadata


@router.get("", response_model=list[DatasetSummary])
def list_datasets(storage: StorageService = Depends(get_storage_service)) -> list[DatasetSummary]:
    return [DatasetSummary(**record) for record in storage.list_metadata()]


@router.get("/{dataset_id}", response_model=DatasetMetadata)
def get_dataset(
    dataset_id: str,
    storage: StorageService = Depends(get_storage_service),
) -> DatasetMetadata:
    record = storage.read_metadata(dataset_id)
    if record is None:
        raise IngestionError(
            code="dataset_not_found",
            message=f"No dataset with id '{dataset_id}'.",
            status_code=404,
        )
    return DatasetMetadata(**record)
