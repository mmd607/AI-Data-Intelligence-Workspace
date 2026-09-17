"""THE GROUNDING GUARANTEE (mandatory test category, per
`01_PHASES/PHASE_05_AI_ANALYTICS/PHASE_PROMPT.md` section 22).

Proves that even when the AI provider returns text that flatly contradicts the real,
deterministic evidence, the response's `computed` field — the authoritative value — is
never altered. The LLM may narrate; it cannot become the source of truth. Every test here
uses `FakeProvider` configured to return a deliberately wrong/fabricated answer.
"""

import pandas as pd

from app.ai import service
from app.ai.schemas import AIAnalyzeRequest, AICapability, AIQueryRequest
from tests.conftest import FakeProvider


def test_fabricated_dataset_summary_does_not_alter_computed_row_count() -> None:
    df = pd.DataFrame({"a": range(42)})  # a real, known row count: 42
    provider = FakeProvider(fixed_text="FABRICATED: this dataset actually has 999 rows.")

    response = service.analyze(
        "ds1", df, AIAnalyzeRequest(capability=AICapability.DATASET_SUMMARY), provider
    )

    # The provider's text can say anything — but the structured, authoritative value
    # must remain exactly what was actually computed.
    assert response.computed["row_count"] == 42
    assert response.ai_explanation.text == "FABRICATED: this dataset actually has 999 rows."


def test_fabricated_numeric_stat_does_not_alter_computed_mean() -> None:
    df = pd.DataFrame({"value": [10.0, 20.0, 30.0, 40.0, 50.0]})  # real mean = 30.0
    provider = FakeProvider(fixed_text="FABRICATED: the mean of value is 51.2, not 30.")

    response = service.analyze(
        "ds1",
        df,
        AIAnalyzeRequest(capability=AICapability.COLUMN_INSIGHT, column_name="value"),
        provider,
    )

    assert response.computed["numeric_stats"]["mean"] == 30.0


def test_fabricated_correlation_coefficient_does_not_alter_computed_value() -> None:
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10]})  # real correlation = 1.0
    provider = FakeProvider(fixed_text="FABRICATED: the correlation is actually -0.3.")

    response = service.analyze(
        "ds1", df, AIAnalyzeRequest(capability=AICapability.CORRELATION_EXPLANATION), provider
    )

    assert response.computed["pairs"][0]["coefficient"] == 1.0


def test_fabricated_ml_metric_does_not_alter_computed_metrics() -> None:
    real_ml_result = {
        "task_type": "regression",
        "target_column": "price",
        "model_name": "linear_regression",
        "feature_columns": ["a"],
        "train_size": 80,
        "test_size_actual": 20,
        "metrics": {"rmse": 12.34, "r2": 0.91},
    }
    provider = FakeProvider(fixed_text="FABRICATED: the model actually achieved r2 = 0.99.")

    response = service.analyze(
        "ds1",
        pd.DataFrame({"a": range(100)}),
        AIAnalyzeRequest(capability=AICapability.ML_EXPLANATION, ml_result=real_ml_result),
        provider,
    )

    assert response.computed["metrics"] == {"rmse": 12.34, "r2": 0.91}
    assert response.computed["metrics"]["r2"] != 0.99


def test_fabricated_deterministic_answer_does_not_alter_computed_resolved_answer() -> None:
    df = pd.DataFrame({"a": [1, 1, 2, 3]})  # 1 real duplicate row
    provider = FakeProvider(fixed_text="FABRICATED: there are actually 500 duplicate rows.")

    response = service.query(
        "ds1", df, AIQueryRequest(question="How many rows are duplicated?"), provider
    )

    assert "1 row(s)" in response.computed["resolved_answer"]
    assert response.question_category.value == "deterministic_lookup"


def test_repeated_calls_with_a_fabricating_provider_always_preserve_the_same_evidence() -> None:
    """Determinism + grounding together: the evidence-building layer must produce
    reproducible output for the same input, regardless of what the (mocked, fabricating)
    provider does on each call."""
    df = pd.DataFrame({"value": [1.0, 2.0, 3.0, 4.0]})
    provider = FakeProvider(
        fixed_text="FABRICATED: whatever, some different wrong number each time."
    )

    request = AIAnalyzeRequest(capability=AICapability.COLUMN_INSIGHT, column_name="value")
    first = service.analyze("ds1", df, request, provider)
    second = service.analyze("ds1", df, request, provider)

    assert first.computed == second.computed
    assert first.computed["numeric_stats"]["mean"] == 2.5


def test_provider_cannot_inject_new_keys_into_computed() -> None:
    """The provider only ever returns narrative text (`ProviderResult.text`) — there is no
    code path by which it could add or modify keys in `computed`, since `computed` is
    built and frozen before `generate()` is ever called."""
    df = pd.DataFrame({"a": range(10)})
    provider = FakeProvider(fixed_text="ignored")

    response = service.analyze(
        "ds1", df, AIAnalyzeRequest(capability=AICapability.DATASET_SUMMARY), provider
    )

    expected_keys = {
        "dataset_id",
        "row_count",
        "column_count",
        "missing_percentage",
        "duplicate_row_percentage",
        "quality_finding_count",
        "quality_severity_counts",
        "columns",
    }
    assert set(response.computed.keys()) == expected_keys
