"""Reproduce current PETScAgent-Bench evaluator-failure scoring semantics.

This is a research reproducer only. It does not propose a scoring policy.
"""

from src.evaluators.base import EvaluationResult, EvaluatorType
from src.metrics.aggregation import MetricsAggregator


def quality(name: str, score: float | None, confidence: float) -> EvaluationResult:
    return EvaluationResult(
        evaluator_name=name,
        evaluator_type=EvaluatorType.QUALITY,
        passed=None if score is None else score >= 0.7,
        quality_score=score,
        confidence=confidence,
        evaluation_method="llm_reproducer",
    )


def metric(name: str, score: float) -> EvaluationResult:
    return EvaluationResult(
        evaluator_name=name,
        evaluator_type=EvaluatorType.METRIC,
        passed=True,
        normalized_score=score,
        confidence=1.0,
    )


def scenario(code_quality: list[EvaluationResult]):
    results = [
        metric("numerical_accuracy", 0.86),
        metric("execution_time", 0.86),
        *code_quality,
        quality("algorithm_appropriateness", 0.86, 0.9),
        quality("solver_choice", 0.86, 0.9),
        quality("petsc_best_practices", 0.86, 0.9),
        quality("error_handling", 0.86, 1.0),
        quality("parallel_awareness", 0.86, 0.8),
    ]
    return MetricsAggregator().aggregate(results)


def main() -> None:
    baseline = scenario([
        quality("readability", 0.86, 0.9),
        quality("code_style", 0.86, 0.9),
        quality("documentation", 0.86, 0.9),
    ])
    one_llm_failure = scenario([
        # Current ReadabilityQuality exception fallback:
        quality("readability", 0.50, 0.0),
        quality("code_style", 0.86, 0.9),
        quality("documentation", 0.86, 0.9),
    ])
    unavailable = scenario([
        # Semantics used by several other LLM evaluators on exception:
        quality("readability", None, 0.0),
        quality("code_style", 0.86, 0.9),
        quality("documentation", 0.86, 0.9),
    ])

    for label, result in (
        ("baseline", baseline),
        ("fallback_score_confidence_zero", one_llm_failure),
        ("unavailable_score_confidence_zero", unavailable),
    ):
        print(
            label,
            {
                "code_quality": result.category_scores.code_quality,
                "composite": result.composite_score,
                "tier": result.overall_tier,
            },
        )


if __name__ == "__main__":
    main()
