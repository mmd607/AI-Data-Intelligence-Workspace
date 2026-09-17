"""Tests for the offline provider: always available, renders each intent deterministically,
and never fabricates a value beyond what's in the evidence dict."""

from app.ai.providers.offline import OfflineProvider


def test_always_available() -> None:
    provider = OfflineProvider()
    available, reason = provider.is_available()
    assert available is True
    assert reason is None


def test_dataset_summary_renders_known_facts() -> None:
    provider = OfflineProvider()
    evidence = {
        "_intent": "dataset_summary",
        "row_count": 100,
        "column_count": 5,
        "missing_percentage": 2.5,
        "duplicate_row_percentage": 1.0,
        "quality_finding_count": 2,
        "quality_severity_counts": {"warning": 2},
    }
    result = provider.generate("system", evidence, "explain")
    assert "100" in result.text
    assert "5" in result.text
    assert "2.5" in result.text
    assert result.provider == "offline"
    assert result.model is None


def test_dataset_summary_with_no_quality_findings() -> None:
    provider = OfflineProvider()
    evidence = {
        "_intent": "dataset_summary",
        "row_count": 50,
        "column_count": 3,
        "missing_percentage": 0.0,
        "duplicate_row_percentage": 0.0,
        "quality_finding_count": 0,
        "quality_severity_counts": {},
    }
    result = provider.generate("system", evidence, "explain")
    assert "No data-quality findings were reported." in result.text


def test_quality_explanation_lists_findings() -> None:
    provider = OfflineProvider()
    evidence = {
        "_intent": "quality_explanation",
        "finding_count": 1,
        "findings": [
            {
                "code": "duplicate_rows",
                "severity": "warning",
                "column": None,
                "message": "1 duplicate row(s) found.",
                "metric": 1,
            }
        ],
    }
    result = provider.generate("system", evidence, "explain")
    assert "1 duplicate row(s) found." in result.text


def test_quality_explanation_with_no_findings() -> None:
    provider = OfflineProvider()
    evidence = {"_intent": "quality_explanation", "finding_count": 0, "findings": []}
    result = provider.generate("system", evidence, "explain")
    assert "No data-quality findings" in result.text


def test_column_insight_numeric() -> None:
    provider = OfflineProvider()
    evidence = {
        "_intent": "column_insight",
        "column_name": "age",
        "pandas_dtype": "float64",
        "semantic_type": "numeric",
        "null_percentage": 5.0,
        "unique_percentage": 90.0,
        "numeric_stats": {"min": 18, "max": 65, "mean": 35.2, "median": 34.0, "std": 10.1},
        "categorical_stats": None,
        "datetime_stats": None,
    }
    result = provider.generate("system", evidence, "explain")
    assert "age" in result.text
    assert "35.2" in result.text
    assert "This represents the customer" not in result.text  # never asserts unverified meaning


def test_column_insight_categorical() -> None:
    provider = OfflineProvider()
    evidence = {
        "_intent": "column_insight",
        "column_name": "category",
        "pandas_dtype": "object",
        "semantic_type": "categorical",
        "null_percentage": 0.0,
        "unique_percentage": 30.0,
        "numeric_stats": None,
        "categorical_stats": {
            "cardinality": 3,
            "top_values": [{"value": "A", "percentage": 50.0}],
        },
        "datetime_stats": None,
    }
    result = provider.generate("system", evidence, "explain")
    assert "'A'" in result.text
    assert "cardinality is 3" in result.text


def test_column_insight_datetime() -> None:
    provider = OfflineProvider()
    evidence = {
        "_intent": "column_insight",
        "column_name": "signup_date",
        "pandas_dtype": "datetime64[ns]",
        "semantic_type": "datetime",
        "null_percentage": 0.0,
        "unique_percentage": 90.0,
        "numeric_stats": None,
        "categorical_stats": None,
        "datetime_stats": {"min_date": "2020-01-01", "max_date": "2020-12-31"},
    }
    result = provider.generate("system", evidence, "explain")
    assert "2020-01-01" in result.text
    assert "2020-12-31" in result.text


def test_column_insight_does_not_assume_domain_meaning() -> None:
    provider = OfflineProvider()
    evidence = {
        "_intent": "column_insight",
        "column_name": "customer_age",
        "pandas_dtype": "int64",
        "semantic_type": "numeric",
        "null_percentage": 0.0,
        "unique_percentage": 80.0,
        "numeric_stats": {"min": 18, "max": 90, "mean": 40.0, "median": 39.0, "std": 12.0},
        "categorical_stats": None,
        "datetime_stats": None,
    }
    result = provider.generate("system", evidence, "explain")
    assert "not confirmed by the available evidence" in result.text


def test_correlation_explanation_never_asserts_causation() -> None:
    provider = OfflineProvider()
    evidence = {
        "_intent": "correlation_explanation",
        "status": "computed",
        "message": None,
        "pairs": [{"column_a": "x", "column_b": "y", "coefficient": 0.82, "observations": 100}],
    }
    result = provider.generate("system", evidence, "explain")
    assert "0.82" in result.text
    assert "does not imply causation" in result.text
    assert " causes " not in result.text.lower()


def test_correlation_explanation_no_computable_pairs() -> None:
    provider = OfflineProvider()
    evidence = {
        "_intent": "correlation_explanation",
        "status": "computed",
        "message": None,
        "pairs": [],
    }
    result = provider.generate("system", evidence, "explain")
    assert "No numeric column pairs had a computable correlation." in result.text


def test_correlation_strength_descriptions_span_the_full_range() -> None:
    provider = OfflineProvider()
    cases = [(0.75, "strong"), (0.5, "moderate"), (0.3, "weak"), (0.05, "very weak")]
    for coefficient, expected in cases:
        evidence = {
            "_intent": "correlation_explanation",
            "status": "computed",
            "message": None,
            "pairs": [
                {"column_a": "x", "column_b": "y", "coefficient": coefficient, "observations": 50}
            ],
        }
        result = provider.generate("system", evidence, "explain")
        assert expected in result.text


def test_correlation_insufficient_data_reports_message_only() -> None:
    provider = OfflineProvider()
    evidence = {
        "_intent": "correlation_explanation",
        "status": "insufficient_data",
        "message": "At least 2 numeric columns are required.",
        "pairs": [],
    }
    result = provider.generate("system", evidence, "explain")
    assert "At least 2 numeric columns" in result.text


def test_ml_explanation_preserves_exact_metric_values() -> None:
    provider = OfflineProvider()
    evidence = {
        "_intent": "ml_explanation",
        "task_type": "regression",
        "target_column": "price",
        "model_name": "linear_regression",
        "feature_columns": ["a", "b"],
        "train_size": 80,
        "test_size_actual": 20,
        "metrics": {"rmse": 123.456, "r2": 0.789},
        "unavailable_metrics": {},
        "warnings": [],
    }
    result = provider.generate("system", evidence, "explain")
    assert "123.456" in result.text
    assert "0.789" in result.text
    # The template explicitly declines to make a production-readiness claim, rather than
    # asserting one either way.
    assert "no claim is made" in result.text.lower()


def test_ml_explanation_includes_unavailable_metrics_and_warnings() -> None:
    provider = OfflineProvider()
    evidence = {
        "_intent": "ml_explanation",
        "task_type": "classification",
        "target_column": "outcome",
        "model_name": "logistic_regression",
        "feature_columns": ["a", "b"],
        "train_size": 80,
        "test_size_actual": 20,
        "metrics": {"accuracy": 0.9},
        "unavailable_metrics": {"roc_auc": "target is not binary"},
        "warnings": ["High cardinality categorical feature 'b' was one-hot encoded."],
    }
    result = provider.generate("system", evidence, "explain")
    assert "roc_auc was not computed — target is not binary" in result.text
    assert "High cardinality categorical feature 'b' was one-hot encoded." in result.text


def test_query_explanation_category_with_no_resolved_answer() -> None:
    provider = OfflineProvider()
    evidence = {"_intent": "query", "question_category": "explanation", "resolved_answer": None}
    result = provider.generate("system", evidence, "what are the quality issues?")
    assert "does not contain enough information to answer this specific question" in result.text


def test_query_unsupported_reports_insufficient_evidence() -> None:
    provider = OfflineProvider()
    evidence = {"_intent": "query", "question_category": "unsupported", "resolved_answer": None}
    result = provider.generate("system", evidence, "what is the weather")
    assert "does not contain enough information" in result.text


def test_query_deterministic_lookup_echoes_resolved_answer() -> None:
    provider = OfflineProvider()
    evidence = {
        "_intent": "query",
        "question_category": "deterministic_lookup",
        "resolved_answer": "3 rows are duplicated.",
    }
    result = provider.generate("system", evidence, "how many duplicates?")
    assert "3 rows are duplicated." in result.text


def test_unknown_intent_does_not_crash() -> None:
    provider = OfflineProvider()
    result = provider.generate("system", {"_intent": "something_new"}, "explain")
    assert "does not contain enough information" in result.text
