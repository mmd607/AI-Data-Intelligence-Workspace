"""The offline provider — deterministic, template-based, no network call, no API key.

This is the default provider (`APP_AI_PROVIDER=offline`), satisfying
`02_DOCS/PRODUCT_SPEC.md` principle 4 ("the application must remain useful without an
external LLM provider") outright. It is also structurally immune to prompt injection
(`01_PHASES/PHASE_05_AI_ANALYTICS/PHASE_PROMPT.md` section 15): every sentence is built by
plain Python string interpolation into fixed templates that only ever read specific,
named fields out of the `evidence` dict — there is no "interpretation" step where a
dataset-derived string could be mistaken for an instruction, because nothing here ever
executes or follows the *content* of a string, it only ever displays it as a quoted value.

The `evidence` dict must include an internal `"_intent"` key (not real evidence, a
routing hint set by `service.py`) selecting which template to render — see
`evidence.py` for the exact shape built per intent.
"""

from typing import Any

from app.ai.provider import AIProvider, ProviderResult

NAME = "offline"


class OfflineProvider(AIProvider):
    name = NAME

    def is_available(self) -> tuple[bool, str | None]:
        return True, None  # always available — no configuration, no network dependency

    def generate(
        self, system_instructions: str, evidence: dict[str, Any], user_request: str
    ) -> ProviderResult:
        intent = evidence.get("_intent")
        renderer = _RENDERERS.get(intent, _render_unknown_intent)
        text = renderer(evidence)
        return ProviderResult(text=text, provider=NAME, model=None)


def _render_dataset_summary(evidence: dict[str, Any]) -> str:
    rows = evidence["row_count"]
    cols = evidence["column_count"]
    missing_pct = evidence["missing_percentage"]
    dup_pct = evidence["duplicate_row_percentage"]
    severities = evidence["quality_severity_counts"]
    finding_count = evidence["quality_finding_count"]

    lines = [
        f"FACT: This dataset has {rows} rows and {cols} columns.",
        f"FACT: {missing_pct}% of all cells are missing, and {dup_pct}% of rows are exact "
        "duplicates.",
    ]
    if finding_count == 0:
        lines.append("FACT: No data-quality findings were reported.")
    else:
        lines.append(
            f"FACT: {finding_count} data-quality finding(s) were reported "
            f"({severities.get('critical', 0)} critical, {severities.get('warning', 0)} "
            f"warning, {severities.get('info', 0)} info)."
        )
    lines.append(
        "INTERPRETATION: The dataset's purpose or business meaning is not stated in the "
        "available evidence, so no claim is made about what it represents beyond its "
        "structure and quality."
    )
    return " ".join(lines)


def _render_quality_explanation(evidence: dict[str, Any]) -> str:
    findings = evidence["findings"]
    if not findings:
        return "FACT: No data-quality findings were reported for this dataset."

    lines = [f"FACT: {evidence['finding_count']} data-quality finding(s) were reported."]
    for finding in findings[:10]:
        column = f" in column '{finding['column']}'" if finding.get("column") else ""
        lines.append(f"FACT ({finding['severity']}){column}: {finding['message']}")
    lines.append(
        "INTERPRETATION: These findings describe patterns in the data as computed; "
        "whether they matter depends on the intended use of the dataset, which is not "
        "stated in the available evidence."
    )
    return " ".join(lines)


def _render_column_insight(evidence: dict[str, Any]) -> str:
    name = evidence["column_name"]
    semantic_type = evidence["semantic_type"]
    null_pct = evidence["null_percentage"]
    unique_pct = evidence["unique_percentage"]

    lines = [
        f"FACT: The column is named '{name}' and its values were classified as "
        f"{semantic_type} (raw type: {evidence['pandas_dtype']}).",
        f"FACT: {null_pct}% of its values are missing, and {unique_pct}% of its non-null "
        "values are unique.",
    ]
    if evidence.get("numeric_stats"):
        s = evidence["numeric_stats"]
        lines.append(
            f"FACT: Numeric summary — min={s['min']}, max={s['max']}, mean={s['mean']}, "
            f"median={s['median']}, std={s['std']}."
        )
    if evidence.get("categorical_stats"):
        s = evidence["categorical_stats"]
        top = s["top_values"][0] if s["top_values"] else None
        if top:
            lines.append(
                f"FACT: The most common value is '{top['value']}' "
                f"({top['percentage']}% of rows); cardinality is {s['cardinality']}."
            )
    if evidence.get("datetime_stats"):
        s = evidence["datetime_stats"]
        lines.append(f"FACT: Date range — {s['min_date']} to {s['max_date']}.")

    lines.append(
        f"INTERPRETATION: The name '{name}' may suggest a real-world meaning, but that "
        "meaning is not confirmed by the available evidence, so only its statistical "
        "properties are described here."
    )
    return " ".join(lines)


def _render_correlation_explanation(evidence: dict[str, Any]) -> str:
    if evidence["status"] == "insufficient_data":
        return f"FACT: {evidence['message']}"

    pairs = evidence["pairs"]
    if not pairs:
        return "FACT: No numeric column pairs had a computable correlation."

    lines = [f"FACT: Pearson correlation was computed for {len(pairs)} column pair(s)."]
    for pair in pairs[:5]:
        strength = _describe_correlation_strength(pair["coefficient"])
        lines.append(
            f"FACT: '{pair['column_a']}' and '{pair['column_b']}' have a Pearson "
            f"correlation of {pair['coefficient']} ({pair['observations']} observations) "
            f"— a {strength} linear association."
        )
    lines.append(
        "INTERPRETATION: Correlation does not imply causation — these values describe a "
        "statistical association only, not a causal relationship."
    )
    return " ".join(lines)


def _describe_correlation_strength(coefficient: float) -> str:
    magnitude = abs(coefficient)
    if magnitude >= 0.7:
        strength = "strong"
    elif magnitude >= 0.4:
        strength = "moderate"
    elif magnitude >= 0.2:
        strength = "weak"
    else:
        strength = "very weak or negligible"
    direction = "positive" if coefficient >= 0 else "negative"
    return f"{strength} {direction}"


def _render_ml_explanation(evidence: dict[str, Any]) -> str:
    lines = [
        f"FACT: A {evidence['task_type']} model ('{evidence['model_name']}') was trained "
        f"to predict '{evidence['target_column']}' using {len(evidence['feature_columns'])} "
        f"feature column(s), with {evidence['train_size']} training rows and "
        f"{evidence['test_size_actual']} test rows.",
    ]
    for metric_name, value in evidence["metrics"].items():
        lines.append(f"FACT: {metric_name} = {value}.")
    for metric_name, reason in evidence.get("unavailable_metrics", {}).items():
        lines.append(f"FACT: {metric_name} was not computed — {reason}")
    if evidence.get("warnings"):
        lines.append("FACT: Reported warnings — " + "; ".join(evidence["warnings"]))
    lines.append(
        "INTERPRETATION: These are baseline metrics only. No claim is made about whether "
        "this model is production-ready or better than any other approach beyond the "
        "reported numbers — see the reported limitations."
    )
    return " ".join(lines)


def _render_query(evidence: dict[str, Any]) -> str:
    category = evidence["question_category"]
    if category == "unsupported":
        return (
            "The available dataset evidence does not contain enough information to "
            "determine this."
        )
    resolved = evidence.get("resolved_answer")
    if resolved:
        return f"FACT: {resolved}"
    return (
        "The available dataset evidence does not contain enough information to answer "
        "this specific question precisely."
    )


def _render_unknown_intent(evidence: dict[str, Any]) -> str:
    return "The available dataset evidence does not contain enough information to determine this."


_RENDERERS = {
    "dataset_summary": _render_dataset_summary,
    "quality_explanation": _render_quality_explanation,
    "column_insight": _render_column_insight,
    "correlation_explanation": _render_correlation_explanation,
    "ml_explanation": _render_ml_explanation,
    "query": _render_query,
}
