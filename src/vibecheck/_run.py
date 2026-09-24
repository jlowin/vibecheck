"""Send plans to a backend, one piece of data per request."""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine, Generator, Sequence
from concurrent.futures import ThreadPoolExecutor
from typing import Any, NoReturn, TypeVar

from pydantic import BaseModel
from pydantic_core import PydanticSerializationError, to_jsonable_python

from vibecheck._plans import Decision, Plan
from vibecheck._questions import Content
from vibecheck.backends import Backend, get_default_backend

T = TypeVar("T")

DEFAULT_MAX_CONCURRENCY = 16


def to_state(data: object) -> Content:
    """Turn the caller's data into content a decision model can read."""
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    if isinstance(data, BaseModel):
        return data.model_dump(mode="json")
    try:
        jsonable = to_jsonable_python(data)
    except PydanticSerializationError:
        return str(data)
    if isinstance(jsonable, (dict, list)):
        return jsonable
    return str(data)


class Pending(Coroutine[Any, Any, T]):
    """The result of an async vibecheck call: a coroutine that must be awaited.

    It works anywhere a coroutine does, including `asyncio.run` and `asyncio.create_task`. Using it as a
    condition without `await` raises instead of silently counting as true.
    """

    __slots__ = ("_coroutine",)

    def __init__(self, coroutine: Coroutine[Any, Any, T]) -> None:
        self._coroutine = coroutine

    def __await__(self) -> Generator[Any, None, T]:
        return self._coroutine.__await__()

    def send(self, value: Any) -> Any:
        return self._coroutine.send(value)

    def throw(self, typ: Any, val: Any = None, tb: Any = None) -> Any:
        if val is None and tb is None:
            return self._coroutine.throw(typ)
        return self._coroutine.throw(typ, val, tb)

    def close(self) -> None:
        self._coroutine.close()

    def __bool__(self) -> NoReturn:
        self._coroutine.close()
        raise TypeError(
            "vibecheck calls are async and must be awaited: write `if await check(...)`, "
            "or use the blocking versions in `vibecheck.sync`"
        )


def run(
    plan: Plan,
    data: object,
    *,
    probabilities: bool,
    model: str | None,
    backend: Backend | None,
) -> Any:
    answers = (backend or get_default_backend()).evaluate(
        to_state(data), plan.questions, model=model
    )
    return plan.finish(answers, probabilities=probabilities)


async def arun(
    plan: Plan,
    data: object,
    *,
    probabilities: bool,
    model: str | None,
    backend: Backend | None,
) -> Any:
    answers = await (backend or get_default_backend()).aevaluate(
        to_state(data), plan.questions, model=model
    )
    return plan.finish(answers, probabilities=probabilities)


def run_each(
    plan: Plan,
    items: Sequence[object],
    *,
    model: str | None,
    backend: Backend | None,
    max_concurrency: int,
) -> list[Any]:
    """Run a plan once per item, concurrently, returning `Decision`s in item order."""
    if not items:
        return []
    with ThreadPoolExecutor(max_workers=min(max_concurrency, len(items))) as pool:
        return list(
            pool.map(
                lambda item: run(
                    plan, item, probabilities=True, model=model, backend=backend
                ),
                items,
            )
        )


async def arun_each(
    plan: Plan,
    items: Sequence[object],
    *,
    model: str | None,
    backend: Backend | None,
    max_concurrency: int,
) -> list[Any]:
    """Run a plan once per item, concurrently, returning `Decision`s in item order."""
    semaphore = asyncio.Semaphore(max_concurrency)

    async def one(item: object) -> Any:
        async with semaphore:
            return await arun(
                plan, item, probabilities=True, model=model, backend=backend
            )

    return list(await asyncio.gather(*(one(item) for item in items)))


def kept(
    items: Sequence[object],
    decisions: Sequence[Decision[Any, Any]],
    *,
    probabilities: bool,
) -> Any:
    """`filter`'s result: the items whose answer was yes, and optionally each item's probability."""
    passing = [
        item for item, decision in zip(items, decisions, strict=True) if decision.answer
    ]
    if probabilities:
        return Decision(passing, [decision.probabilities for decision in decisions])
    return passing


def grouped(
    options: Sequence[Any],
    items: Sequence[object],
    decisions: Sequence[Decision[Any, Any]],
    *,
    probabilities: bool,
) -> Any:
    """`group`'s result: every option mapped to its items, and optionally each item's probabilities."""
    groups: dict[Any, list[object]] = {option: [] for option in options}
    for item, decision in zip(items, decisions, strict=True):
        groups[decision.answer].append(item)
    if probabilities:
        return Decision(groups, [decision.probabilities for decision in decisions])
    return groups
