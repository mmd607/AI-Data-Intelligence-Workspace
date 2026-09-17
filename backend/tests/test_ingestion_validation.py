"""Unit tests for pre-parse validation: filename sanitization, extension, and size."""

import pytest

from app.ingestion.errors import IngestionError
from app.ingestion.validation import sanitize_filename, validate_extension, validate_size


class TestSanitizeFilename:
    def test_returns_bare_name_unchanged(self) -> None:
        assert sanitize_filename("data.csv") == "data.csv"

    def test_strips_posix_path_traversal(self) -> None:
        assert sanitize_filename("../../etc/passwd.csv") == "passwd.csv"

    def test_strips_windows_path_traversal(self) -> None:
        assert sanitize_filename("..\\..\\windows\\evil.csv") == "evil.csv"

    def test_result_never_contains_a_path_separator(self) -> None:
        result = sanitize_filename("a/b/c/../../d.csv")
        assert "/" not in result
        assert "\\" not in result

    def test_none_filename_raises(self) -> None:
        with pytest.raises(IngestionError) as exc_info:
            sanitize_filename(None)
        assert exc_info.value.code == "missing_filename"
        assert exc_info.value.status_code == 400

    def test_blank_filename_raises(self) -> None:
        with pytest.raises(IngestionError) as exc_info:
            sanitize_filename("   ")
        assert exc_info.value.code == "missing_filename"


class TestValidateExtension:
    def test_accepts_csv(self) -> None:
        validate_extension("data.csv")  # does not raise

    def test_accepts_csv_case_insensitively(self) -> None:
        validate_extension("DATA.CSV")  # does not raise

    def test_rejects_unsupported_extension(self) -> None:
        with pytest.raises(IngestionError) as exc_info:
            validate_extension("data.json")
        assert exc_info.value.code == "unsupported_file_type"
        assert exc_info.value.status_code == 400

    def test_rejects_no_extension(self) -> None:
        with pytest.raises(IngestionError) as exc_info:
            validate_extension("data")
        assert exc_info.value.code == "unsupported_file_type"

    def test_rejects_disguised_binary(self) -> None:
        with pytest.raises(IngestionError) as exc_info:
            validate_extension("totally-a-csv.exe")
        assert exc_info.value.code == "unsupported_file_type"


class TestValidateSize:
    def test_accepts_within_limit(self) -> None:
        validate_size(100, max_bytes=1000)  # does not raise

    def test_rejects_zero_bytes(self) -> None:
        with pytest.raises(IngestionError) as exc_info:
            validate_size(0, max_bytes=1000)
        assert exc_info.value.code == "empty_file"
        assert exc_info.value.status_code == 400

    def test_rejects_over_limit(self) -> None:
        with pytest.raises(IngestionError) as exc_info:
            validate_size(1001, max_bytes=1000)
        assert exc_info.value.code == "file_too_large"
        assert exc_info.value.status_code == 413

    def test_accepts_exactly_at_limit(self) -> None:
        validate_size(1000, max_bytes=1000)  # does not raise
