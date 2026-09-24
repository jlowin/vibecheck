"""Ask many questions about the same data in one request."""

from __future__ import annotations

from collections.abc import Iterable
from types import TracebackType
from typing import Any, Generic, Literal, NoReturn, Self, TypeVar, overload

from vibecheck import _plans
from vibecheck._plans import Decision, Plan, Threshold
from vibecheck._run import to_state
from vibecheck.backends import Backend, get_default_backend

T = TypeVar("T")
M = TypeVar("M")


class Deferred(Generic[T]):
    """An answer from a batch, available once the batch's block has ended."""

    __slots__ = ("_ready", "_value")

    def __init__(self) -> None:
        self._ready = False
        self._value: Any = None

    def result(self) -> T:
        if not self._ready:
            raise RuntimeError(
                "this answer isn't ready: a batch sends its questions when its `with` block ends, "
                "so read results after the block"
            )
        return self._value

    def _set(self, value: Any) -> None:
        self._value = value
        self._ready = True

    def __bool__(self) -> NoReturn:
        raise TypeError(
            "a batch answer isn't a value yet; call .result() after the block"
        )


class Batch:
    """Ask many questions about the same data, sent as one request when the block ends.

    Works with `with` in synchronous code and `async with` in async code. Every question in a batch is about
    the data passed to `batch()`; each one keeps its own instructions and answer type.
    """

    def __init__(
        self,
        data: object = None,
        *,
        model: str | None = None,
        backend: Backend | None = None,
    ) -> None:
        self._data = data
        self._model = model
        self._backend = backend
        self._entries: list[tuple[Plan, bool, Deferred[Any]]] = []
        self._sent = False

    @overload
    def check(
        self,
        question: str,
        *,
        threshold: float = 0.5,
        probabilities: Literal[False] = False,
    ) -> Deferred[bool]: ...
    @overload
    def check(
        self,
        question: str,
        *,
        threshold: tuple[float, float],
        probabilities: Literal[False] = False,
    ) -> Deferred[bool | None]: ...
    @overload
    def check(
        self,
        question: str,
        *,
        threshold: float = 0.5,
        probabilities: Literal[True],
    ) -> Deferred[Decision[bool, float]]: ...
    @overload
    def check(
        self,
        question: str,
        *,
        threshold: tuple[float, float],
        probabilities: Literal[True],
    ) -> Deferred[Decision[bool | None, float]]: ...
    def check(
        self,
        question: str,
        *,
        threshold: Threshold = 0.5,
        probabilities: bool = False,
    ) -> Deferred[Any]:
        return self._add(_plans.check(question, threshold=threshold), probabilities)

    @overload
    def classify(
        self,
        question: str,
        options: Iterable[T],
        *,
        probabilities: Literal[False] = False,
    ) -> Deferred[T]: ...
    @overload
    def classify(
        self,
        question: str,
        options: Iterable[T],
        *,
        probabilities: Literal[True],
    ) -> Deferred[Decision[T, dict[T, float]]]: ...
    def classify(
        self,
        question: str,
        options: Iterable[Any],
        *,
        probabilities: bool = False,
    ) -> Deferred[Any]:
        return self._add(_plans.classify(question, options), probabilities)

    @overload
    def label(
        self,
        question: str,
        options: Iterable[T],
        *,
        threshold: float = 0.5,
        limit: int | None = None,
        probabilities: Literal[False] = False,
    ) -> Deferred[list[T]]: ...
    @overload
    def label(
        self,
        question: str,
        options: Iterable[T],
        *,
        threshold: float = 0.5,
        limit: int | None = None,
        probabilities: Literal[True],
    ) -> Deferred[Decision[list[T], dict[T, float]]]: ...
    def label(
        self,
        question: str,
        options: Iterable[Any],
        *,
        threshold: float = 0.5,
        limit: int | None = None,
        probabilities: bool = False,
    ) -> Deferred[Any]:
        plan = _plans.label(question, options, threshold=threshold, limit=limit)
        return self._add(plan, probabilities)

    @overload
    def score(
        self,
        question: str,
        levels: Iterable[Any],
        *,
        probabilities: Literal[False] = False,
    ) -> Deferred[float]: ...
    @overload
    def score(
        self,
        question: str,
        levels: Iterable[Any],
        *,
        probabilities: Literal[True],
    ) -> Deferred[Decision[float, dict[float, float]]]: ...
    def score(
        self,
        question: str,
        levels: Iterable[Any],
        *,
        probabilities: bool = False,
    ) -> Deferred[Any]:
        return self._add(_plans.score(question, levels), probabilities)

    @overload
    def assess(
        self,
        question: str,
        schema: type[M],
        *,
        threshold: float = 0.5,
        probabilities: Literal[False] = False,
    ) -> Deferred[M]: ...
    @overload
    def assess(
        self,
        question: str,
        schema: type[M],
        *,
        threshold: float = 0.5,
        probabilities: Literal[True],
    ) -> Deferred[Decision[M, dict[str, Any]]]: ...
    def assess(
        self,
        question: str,
        schema: type[Any],
        *,
        threshold: float = 0.5,
        probabilities: bool = False,
    ) -> Deferred[Any]:
        plan = _plans.assess(question, schema, threshold=threshold)
        return self._add(plan, probabilities)

    def _add(self, plan: Plan, probabilities: bool) -> Deferred[Any]:
        if self._sent:
            raise RuntimeError("this batch has already been sent; start a new batch")
        deferred: Deferred[Any] = Deferred()
        self._entries.append(
            (plan.prefixed(f"q{len(self._entries)}"), probabilities, deferred)
        )
        return deferred

    def _questions(self) -> dict[str, Any]:
        return {
            name: question
            for plan, _, _ in self._entries
            for name, question in plan.questions.items()
        }

    def _resolve(self, answers: _plans.Answers) -> None:
        for plan, probabilities, deferred in self._entries:
            deferred._set(plan.finish(answers, probabilities=probabilities))

    def send(self) -> None:
        """Send every question in one request. Leaving a `with` block calls this for you."""
        self._sent = True
        if not self._entries:
            return
        backend = self._backend or get_default_backend()
        answers = backend.evaluate(
            to_state(self._data), self._questions(), model=self._model
        )
        self._resolve(answers)

    async def asend(self) -> None:
        """Send every question in one request. Leaving an `async with` block calls this for you."""
        self._sent = True
        if not self._entries:
            return
        backend = self._backend or get_default_backend()
        answers = await backend.aevaluate(
            to_state(self._data), self._questions(), model=self._model
        )
        self._resolve(answers)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is None:
            self.send()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is None:
            await self.asend()
