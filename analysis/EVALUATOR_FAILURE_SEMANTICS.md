# Evaluator-failure scoring semantics: current behavior

This note documents the current behavior on `main` at
`7b4f25fac082bf90c8f1c0892b531e0a2d911027`. It is a reproducer and
design note, not a proposed scoring policy.

## Current paths

`MetricsAggregator._calculate_category_scores()` uses a result's confidence
as its weight only when confidence is positive. A score carrying
`confidence == 0.0` receives weight `1.0`.

Current evaluator exception paths differ:

- `ReadabilityQuality` returns `quality_score=0.5, confidence=0.0`.
- `DocumentationQuality` returns `quality_score=0.5, confidence=0.0`.
- `CodeStyleQuality` substitutes an LLM score of `0.5`, combines it with
  static analysis, then reports zero confidence.
- `AlgorithmAppropriatenessQuality`, `SolverChoiceQuality`, and
  `PETScBestPracticesQuality` return `quality_score=None, confidence=0.0`.
- Unhandled exceptions from concurrent LLM evaluators are omitted from
  `all_results` by the pipeline.

These states consequently have different scoring semantics: a numeric fallback
with zero confidence is included at unit weight; a missing score is skipped; an
uncaught evaluator exception produces no result entry.

## Threshold reproducer

The companion script constructs a baseline in which every scored category is
86.0. With the configured tier threshold, the composite is 86.0 and the tier is
GOLD.

Replacing one readability result with the evaluator's current exception
fallback (`score=0.50, confidence=0.0`) changes the code-quality category to:

```text
(0.50 * 1.0 + 0.86 * 0.9 + 0.86 * 0.9) / (1.0 + 0.9 + 0.9)
= 0.731428...
```

With the repository's 15% code-quality weight, the composite becomes
approximately 84.0714, which is SILVER under the configured 85-point GOLD
threshold.

Representing the same failed evaluator with `quality_score=None` instead
causes it to be skipped by the current aggregator. In the reproducer, the
remaining two code-quality scores stay at 86.0 and the composite remains 86.0.

## Interpretation

The observed tier depends on the evaluator's failure representation, not only
on the candidate code. The repository currently has more than one failure
representation for LLM-backed quality evaluators.

A policy decision is needed before changing production scoring. Possible
questions include whether an unavailable evaluator should:

- reduce evaluation coverage while leaving the available-score estimate intact;
- withhold a category or tier;
- contribute a defined fallback score;
- trigger a deterministic fallback evaluator;
- produce an explicit incomplete-evaluation state.

The reproducer intentionally leaves that policy open.
