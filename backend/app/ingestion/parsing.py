"""Deterministic CSV parsing and structural fact extraction.

Everything here is a pure function of the input bytes — same file in, same
`ParsedDataset` out, every time (`02_DOCS/TESTING_STRATEGY.md` §5 determinism
requirement). No profiling/quality logic lives here — see the module docstring in
`app/ingestion/__init__.py`.
"""

import io
import string
from dataclasses import dataclass

import pandas as pd

from app.ingestion.errors import IngestionError
from app.ingestion.schemas import ColumnInfo

_DECODE_ENCODINGS = ("utf-8-sig", "utf-8", "latin-1")
_BINARY_SNIFF_SAMPLE_SIZE = 4096
_BINARY_NON_PRINTABLE_RATIO_THRESHOLD = 0.30


@dataclass(frozen=True)
class ParsedDataset:
    row_count: int
    column_count: int
    columns: list[ColumnInfo]
    missing_value_count: int
    duplicate_row_count: int


def _decode(raw_bytes: bytes) -> str:
    """Try common text encodings; `latin-1` always succeeds, so this never raises from
    decoding alone — the binary-content check below is what actually rejects junk.
    """
    for encoding in _DECODE_ENCODINGS:
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    # Unreachable in practice (latin-1 accepts any byte sequence) — kept as a safety net.
    raise IngestionError(
        code="undecodable_content",
        message="The file could not be decoded as text.",
        status_code=400,
    )


def _reject_if_binary(text: str) -> None:
    """Lightweight MIME/type-spoofing guard (`02_DOCS/ARCHITECTURE.md` "Security &
    Privacy"): a file renamed to `.csv` that is actually binary (an image, executable,
    etc.) decodes as text "successfully" via latin-1 but is mostly non-printable/contains
    NUL bytes — reject it before attempting a CSV parse, without adding a
    content-sniffing dependency.
    """
    sample = text[:_BINARY_SNIFF_SAMPLE_SIZE]
    if not sample:
        return
    if "\x00" in sample:
        raise IngestionError(
            code="unsupported_content",
            message="The file does not look like a text CSV file.",
            status_code=400,
        )
    non_printable = sum(1 for ch in sample if ch not in string.printable)
    if (non_printable / len(sample)) > _BINARY_NON_PRINTABLE_RATIO_THRESHOLD:
        raise IngestionError(
            code="unsupported_content",
            message="The file does not look like a text CSV file.",
            status_code=400,
        )


def parse_csv(raw_bytes: bytes) -> ParsedDataset:
    """Parse raw CSV bytes into structural facts, or raise `IngestionError`.

    Raises:
        IngestionError: `empty_file` (no bytes or no header/columns),
            `unsupported_content` (binary content), `malformed_csv` (unparseable CSV).
    """
    if len(raw_bytes) == 0:
        raise IngestionError(
            code="empty_file",
            message="The uploaded file is empty.",
            status_code=400,
        )

    text = _decode(raw_bytes)
    _reject_if_binary(text)

    try:
        df = pd.read_csv(io.StringIO(text))
    except pd.errors.EmptyDataError as exc:
        raise IngestionError(
            code="empty_file",
            message="The CSV file has no header/columns.",
            status_code=400,
        ) from exc
    except pd.errors.ParserError as exc:
        raise IngestionError(
            code="malformed_csv",
            message=f"The CSV file could not be parsed: {exc}",
            status_code=400,
        ) from exc

    columns = [ColumnInfo(name=str(column), dtype=str(df[column].dtype)) for column in df.columns]

    return ParsedDataset(
        row_count=int(len(df)),
        column_count=int(len(df.columns)),
        columns=columns,
        missing_value_count=int(df.isna().sum().sum()),
        duplicate_row_count=int(df.duplicated().sum()),
    )
