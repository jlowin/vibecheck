"""The blocking API: `from vibecheck.sync import check, classify, label, score, ...`.

Same functions and arguments as the async API, for scripts and other synchronous code.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Literal, TypeVar, overload

from vibecheck import _plans
from vibecheck._batch import Batch as batch
from vibecheck._plans import Decision, Threshold
from vibecheck._run import (
    DEFAULT_MAX_CONCURRENCY,
    grouped,
    kept,
    run,
    run_each,
)
from vibecheck.backends import Backend

T = TypeVar("T")
O = TypeVar("O")
M = TypeVar("M")


@overload
def check(
    question: str,
    data: object = None,
    *,
    threshold: float = 0.5,
    probabilities: Literal[False] = False,
    model: str | None = None,
    backend: Backend | None = None,
) -> bool: ...
@overload
def check(
    question: str,
    data: object = None,
    *,
    threshold: tuple[float, float],
    probabilities: Literal[False] = False,
    model: str | None = None,
    backend: Backend | None = None,
) -> bool | None: ...
@overload
def check(
    question: str,
    data: object = None,
    *,
    threshold: float = 0.5,
    probabilities: Literal[True],
    model: str | None = None,
    backend: Backend | None = None,
) -> Decision[bool, float]: ...
@overload
def check(
    question: str,
    data: object = None,
    *,
    threshold: tuple[float, float],
    probabilities: Literal[True],
    model: str | None = None,
    backend: Backend | None = None,
) -> Decision[bool | None, float]: ...
def check(
    question: str,
    data: object = None,
    *,
    threshold: Threshold = 0.5,
    probabilities: bool = False,
    model: str | None = None,
    backend: Backend | None = None,
) -> Any:
    """Ask a yes/no question about `data`.

    Returns `True` or `False`. With a `(low, high)` threshold, returns `None` when the probability of yes falls
    between them.
    """
    plan = _plans.check(question, threshold=threshold)
    return run(plan, data, probabilities=probabilities, model=model, backend=backend)


@overload
def classify(
    question: str,
    options: Iterable[T],
    data: object = None,
    *,
    probabilities: Literal[False] = False,
    model: str | None = None,
    backend: Backend | None = None,
) -> T: ...
@overload
def classify(
    question: str,
    options: Iterable[T],
    data: object = None,
    *,
    probabilities: Literal[True],
    model: str | None = None,
    backend: Backend | None = None,
) -> Decision[T, dict[T, float]]: ...
def classify(
    question: str,
    options: Iterable[Any],
    data: object = None,
    *,
    probabilities: bool = False,
    model: str | None = None,
    backend: Backend | None = None,
) -> Any:
    """Pick exactly one of `options` for `data`.

    Options can be a list, a dict of option -> description, or an Enum class.
    """
    plan = _plans.classify(question, options)
    return run(plan, data, probabilities=probabilities, model=model, backend=backend)


@overload
def label(
    question: str,
    options: Iterable[T],
    data: object = None,
    *,
    threshold: float = 0.5,
    limit: int | None = None,
    probabilities: Literal[False] = False,
    model: str | None = None,
    backend: Backend | None = None,
) -> list[T]: ...
@overload
def label(
    question: str,
    options: Iterable[T],
    data: object = None,
    *,
    threshold: float = 0.5,
    limit: int | None = None,
    probabilities: Literal[True],
    model: str | None = None,
    backend: Backend | None = None,
) -> Decision[list[T], dict[T, float]]: ...
def label(
    question: str,
    options: Iterable[Any],
    data: object = None,
    *,
    threshold: float = 0.5,
    limit: int | None = None,
    probabilities: bool = False,
    model: str | None = None,
    backend: Backend | None = None,
) -> Any:
    """Pick every option that applies to `data`: zero or more, most likely first.

    Each option is judged on its own. `threshold` is the probability an option needs, and `limit` caps how many
    come back.
    """
    plan = _plans.label(question, options, threshold=threshold, limit=limit)
    return run(plan, data, probabilities=probabilities, model=model, backend=backend)


@overload
def score(
    question: str,
    levels: Iterable[Any],
    data: object = None,
    *,
    probabilities: Literal[False] = False,
    model: str | None = None,
    backend: Backend | None = None,
) -> float: ...
@overload
def score(
    question: str,
    levels: Iterable[Any],
    data: object = None,
    *,
    probabilities: Literal[True],
    model: str | None = None,
    backend: Backend | None = None,
) -> Decision[float, dict[float, float]]: ...
def score(
    question: str,
    levels: Iterable[Any],
    data: object = None,
    *,
    probabilities: bool = False,
    model: str | None = None,
    backend: Backend | None = None,
) -> Any:
    """Rate `data` on ordered levels, listed from lowest to highest.

    Levels can be a list of descriptions (numbered from 0), a list or range of numbers, or a dict of
    number -> description. Returns the probability-weighted position, in the levels' units.
    """
    plan = _plans.score(question, levels)
    return run(plan, data, probabilities=probabilities, model=model, backend=backend)


@overload
def assess(
    question: str,
    schema: type[M],
    data: object = None,
    *,
    threshold: float = 0.5,
    probabilities: Literal[False] = False,
    model: str | None = None,
    backend: Backend | None = None,
) -> M: ...
@overload
def assess(
    question: str,
    schema: type[M],
    data: object = None,
    *,
    threshold: float = 0.5,
    probabilities: Literal[True],
    model: str | None = None,
    backend: Backend | None = None,
) -> Decision[M, dict[str, Any]]: ...
def assess(
    question: str,
    schema: type[Any],
    data: object = None,
    *,
    threshold: float = 0.5,
    probabilities: bool = False,
    model: str | None = None,
    backend: Backend | None = None,
) -> Any:
    """Fill every field of a model class from `data`, in one request.

    Each field is one question. Its type picks the kind of question, and `Annotated` metadata says how to ask.
    """
    plan = _plans.assess(question, schema, threshold=threshold)
    return run(plan, data, probabilities=probabilities, model=model, backend=backend)


@overload
def filter(
    question: str,
    items: Iterable[T],
    *,
    threshold: float = 0.5,
    probabilities: Literal[False] = False,
    model: str | None = None,
    backend: Backend | None = None,
    max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
) -> list[T]: ...
@overload
def filter(
    question: str,
    items: Iterable[T],
    *,
    threshold: float = 0.5,
    probabilities: Literal[True],
    model: str | None = None,
    backend: Backend | None = None,
    max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
) -> Decision[list[T], list[float]]: ...
def filter(
    question: str,
    items: Iterable[Any],
    *,
    threshold: float = 0.5,
    probabilities: bool = False,
    model: str | None = None,
    backend: Backend | None = None,
    max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
) -> Any:
    """Keep the items where the answer to a yes/no question is yes, in their original order.

    Each item is its own request, and the requests run concurrently.
    """
    if isinstance(threshold, tuple):
        raise TypeError("filter takes a single threshold, not a (low, high) band")
    plan = _plans.check(question, threshold=threshold)
    values = list(items)

    decisions = run_each(
        plan, values, model=model, backend=backend, max_concurrency=max_concurrency
    )
    return kept(values, decisions, probabilities=probabilities)


@overload
def group(
    question: str,
    options: Iterable[O],
    items: Iterable[T],
    *,
    probabilities: Literal[False] = False,
    model: str | None = None,
    backend: Backend | None = None,
    max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
) -> dict[O, list[T]]: ...
@overload
def group(
    question: str,
    options: Iterable[O],
    items: Iterable[T],
    *,
    probabilities: Literal[True],
    model: str | None = None,
    backend: Backend | None = None,
    max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
) -> Decision[dict[O, list[T]], list[dict[O, float]]]: ...
def group(
    question: str,
    options: Iterable[Any],
    items: Iterable[Any],
    *,
    probabilities: bool = False,
    model: str | None = None,
    backend: Backend | None = None,
    max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
) -> Any:
    """Sort items into buckets: classify each item, then group items by their answer.

    Every option appears as a key, in order, even if no item landed there. Each item is its own request, and the
    requests run concurrently.
    """
    if not isinstance(options, (Mapping, type)):
        options = list(options)
    choices = _plans.option_values(options)
    plan = _plans.classify(question, options)
    values = list(items)

    decisions = run_each(
        plan, values, model=model, backend=backend, max_concurrency=max_concurrency
    )
    return grouped(choices, values, decisions, probabilities=probabilities)


__all__ = [
    "Decision",
    "assess",
    "batch",
    "check",
    "classify",
    "filter",
    "group",
    "label",
    "score",
]
