"""Tests for the service orchestration layer: disabled mode, unavailable provider,
provider runtime errors, and the fact that `computed` is always returned regardless of
whether AI narration succeeded — using the mocked `FakeProvider`, never a real provider.
"""

import pandas as pd

from app.ai import service
from app.ai.errors import AIError
from app.ai.schemas import AIAnalyzeRequest, AICapability, AIQueryRequest
from tests.conftest import FakeProvider


def _df() -> pd.DataFrame:
    return pd.DataFrame(
        {"age": [25, 30, 35, 40, 22, 22, 60, 35, 29, 50], "category": ["A", "B"] * 5}
    )


class TestDisabledMode:
    def test_analyze_returns_computed_data_with_no_explanation(self) -> None:
        response = service.analyze(
            "ds1", _df(), AIAnalyzeRequest(capability=AICapability.DATASET_SUMMARY), provider=None
        )
        assert response.available is False
        assert response.reason == "AI features are disabled."
        assert response.ai_explanation is None
        assert response.computed["row_count"] == 10  # deterministic data still present

    def test_query_returns_computed_data_with_no_explanation(self) -> None:
        response = service.query(
            "ds1", _df(), AIQueryRequest(question="How many duplicates?"), provider=None
        )
        assert response.available is False
        assert response.ai_explanation is None
        assert "resolved_answer" in response.computed


class TestUnavailableProvider:
    def test_provider_configured_but_unavailable_is_reported_clearly(self) -> None:
        provider = FakeProvider(available=False, unavailable_reason="missing API key")
        response = service.analyze(
            "ds1", _df(), AIAnalyzeRequest(capability=AICapability.DATASET_SUMMARY), provider
        )
        assert response.available is False
        assert response.reason == "missing API key"
        assert response.computed["row_count"] == 10


class TestProviderRuntimeErrors:
    def test_provider_error_does_not_crash_and_computed_survives(self) -> None:
        provider = FakeProvider(
            raise_error=AIError(code="ai_provider_timeout", message="timed out")
        )
        response = service.analyze(
            "ds1", _df(), AIAnalyzeRequest(capability=AICapability.DATASET_SUMMARY), provider
        )
        assert response.available is False
        assert response.reason == "timed out"
        assert response.ai_explanation is None
        assert response.computed["row_count"] == 10


class TestSuccessfulGeneration:
    def test_analyze_returns_ai_explanation_when_provider_succeeds(self) -> None:
        provider = FakeProvider(fixed_text="A narrative explanation.")
        response = service.analyze(
            "ds1", _df(), AIAnalyzeRequest(capability=AICapability.DATASET_SUMMARY), provider
        )
        assert response.available is True
        assert response.ai_explanation.text == "A narrative explanation."
        assert response.ai_explanation.source == "ai_generated"

    def test_column_insight_requires_column_name(self) -> None:
        provider = FakeProvider()
        try:
            request = AIAnalyzeRequest(capability=AICapability.COLUMN_INSIGHT)
            service.analyze("ds1", _df(), request, provider)
            raise AssertionError("expected AIError")
        except AIError as exc:
            assert exc.code == "column_name_required"

    def test_quality_explanation_capability_returns_findings(self) -> None:
        provider = FakeProvider()
        request = AIAnalyzeRequest(capability=AICapability.QUALITY_EXPLANATION)
        response = service.analyze("ds1", _df(), request, provider)
        assert "finding_count" in response.computed

    def test_evidence_sources_are_capability_specific(self) -> None:
        provider = FakeProvider()
        request = AIAnalyzeRequest(capability=AICapability.CORRELATION_EXPLANATION)
        response = service.analyze("ds1", _df(), request, provider)
        assert response.evidence_sources == ["correlation_report"]

    def test_limitations_mention_causation_for_correlation(self) -> None:
        provider = FakeProvider()
        request = AIAnalyzeRequest(capability=AICapability.CORRELATION_EXPLANATION)
        response = service.analyze("ds1", _df(), request, provider)
        assert any("causation" in limitation for limitation in response.limitations)


class TestQueryEvidenceContext:
    def test_explanation_category_includes_dataset_context(self) -> None:
        provider = FakeProvider()
        request = AIQueryRequest(question="What are the main data-quality issues?")
        service.query("ds1", _df(), request, provider)
        assert "context" in provider.last_evidence

    def test_deterministic_lookup_does_not_need_extra_context(self) -> None:
        provider = FakeProvider()
        request = AIQueryRequest(question="How many rows are duplicated?")
        service.query("ds1", _df(), request, provider)
        assert "context" not in provider.last_evidence
