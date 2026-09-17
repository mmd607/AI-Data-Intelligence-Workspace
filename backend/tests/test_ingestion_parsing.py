"""Unit tests for CSV parsing and structural fact extraction — golden-value tests against
fixtures with deliberately known characteristics, per `02_DOCS/TESTING_STRATEGY.md` §5.
"""

import pytest

from app.ingestion.errors import IngestionError
from app.ingestion.parsing import parse_csv
from tests.conftest import FIXTURES_DIR, generate_large_csv_bytes


def _read(name: str) -> bytes:
    return (FIXTURES_DIR / name).read_bytes()


class TestParseCsvValid:
    def test_valid_csv_row_and_column_counts(self) -> None:
        result = parse_csv(_read("valid.csv"))
        assert result.row_count == 3
        assert result.column_count == 4
        assert [c.name for c in result.columns] == ["id", "name", "age", "city"]

    def test_valid_csv_has_zero_missing_and_zero_duplicates(self) -> None:
        result = parse_csv(_read("valid.csv"))
        assert result.missing_value_count == 0
        assert result.duplicate_row_count == 0

    def test_header_only_csv_is_valid_with_zero_rows(self) -> None:
        result = parse_csv(_read("header_only.csv"))
        assert result.row_count == 0
        assert result.column_count == 4

    def test_parsing_is_deterministic(self) -> None:
        raw = _read("valid.csv")
        first = parse_csv(raw)
        second = parse_csv(raw)
        assert first == second


class TestParseCsvMissingValues:
    def test_missing_value_count_matches_known_fixture(self) -> None:
        # backend/tests/fixtures/missing_values.csv has exactly 4 blank cells.
        result = parse_csv(_read("missing_values.csv"))
        assert result.missing_value_count == 4
        assert result.row_count == 4


class TestParseCsvDuplicateRows:
    def test_duplicate_row_count_matches_known_fixture(self) -> None:
        # backend/tests/fixtures/duplicate_rows.csv: 1 duplicate of "Bob" + 2 duplicates
        # of "Carol" = 3 rows beyond their first occurrence.
        result = parse_csv(_read("duplicate_rows.csv"))
        assert result.duplicate_row_count == 3
        assert result.row_count == 6


class TestParseCsvMixedTypes:
    def test_mixed_type_column_is_reported_not_rejected(self) -> None:
        result = parse_csv(_read("mixed_types.csv"))
        value_column = next(c for c in result.columns if c.name == "value")
        assert value_column.dtype == "object"
        assert result.row_count == 4


class TestParseCsvErrors:
    def test_empty_bytes_raises_empty_file(self) -> None:
        with pytest.raises(IngestionError) as exc_info:
            parse_csv(b"")
        assert exc_info.value.code == "empty_file"
        assert exc_info.value.status_code == 400

    def test_zero_byte_fixture_raises_empty_file(self) -> None:
        with pytest.raises(IngestionError) as exc_info:
            parse_csv(_read("empty.csv"))
        assert exc_info.value.code == "empty_file"

    def test_malformed_csv_raises_malformed_csv(self) -> None:
        with pytest.raises(IngestionError) as exc_info:
            parse_csv(_read("malformed.csv"))
        assert exc_info.value.code == "malformed_csv"
        assert exc_info.value.status_code == 400

    def test_binary_content_raises_unsupported_content(self) -> None:
        binary_bytes = bytes(range(256)) * 4  # mostly non-printable, includes NUL bytes
        with pytest.raises(IngestionError) as exc_info:
            parse_csv(binary_bytes)
        assert exc_info.value.code == "unsupported_content"
        assert exc_info.value.status_code == 400


class TestParseCsvLargeIsh:
    def test_large_ish_csv_parses_correctly_and_reasonably_fast(self) -> None:
        raw = generate_large_csv_bytes(num_rows=5000)
        result = parse_csv(raw)
        assert result.row_count == 5000
        assert result.column_count == 3
        assert result.missing_value_count == 0
        assert result.duplicate_row_count == 0
