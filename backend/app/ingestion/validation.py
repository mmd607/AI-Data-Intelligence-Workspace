"""Pre-parse validation: filename/extension, size, and filename sanitization.

Path-traversal defense is structural, not a validation rule: dataset storage never uses
the client-supplied filename to build a filesystem path (see `storage.py` — it always
uses a server-generated dataset id). `sanitize_filename` here only produces a safe
*display* value; it is never trusted as a path component.
"""

from pathlib import PurePosixPath, PureWindowsPath

from app.ingestion.errors import IngestionError

ALLOWED_EXTENSIONS = {".csv"}


def sanitize_filename(filename: str | None) -> str:
    """Strip any path components (POSIX or Windows separators) and return a bare name.

    Guards against a client sending e.g. `../../etc/passwd` or `..\\..\\evil.csv` as the
    claimed filename — the returned value is safe to store as a display string, but is
    still never used to construct a filesystem path (see `storage.py`).
    """
    if not filename or not filename.strip():
        raise IngestionError(
            code="missing_filename",
            message="No filename was provided with the upload.",
            status_code=400,
        )
    # Strip components for both path styles regardless of the host OS, since the client
    # may be on either platform.
    name = PureWindowsPath(filename).name
    name = PurePosixPath(name).name
    if not name:
        raise IngestionError(
            code="missing_filename",
            message="No filename was provided with the upload.",
            status_code=400,
        )
    return name


def validate_extension(sanitized_filename: str) -> None:
    has_extension = "." in sanitized_filename
    suffix = "." + sanitized_filename.rsplit(".", 1)[-1].lower() if has_extension else ""
    if suffix not in ALLOWED_EXTENSIONS:
        raise IngestionError(
            code="unsupported_file_type",
            message=(
                f"Unsupported file type '{suffix or 'unknown'}'. Only .csv files are "
                "currently supported."
            ),
            status_code=400,
        )


def validate_size(size_bytes: int, max_bytes: int) -> None:
    if size_bytes == 0:
        raise IngestionError(
            code="empty_file",
            message="The uploaded file is empty.",
            status_code=400,
        )
    if size_bytes > max_bytes:
        raise IngestionError(
            code="file_too_large",
            message=f"The uploaded file ({size_bytes} bytes) exceeds the {max_bytes} byte limit.",
            status_code=413,
        )
