"""Backends send vibecheck's questions to a decision model and translate the answers back."""

from __future__ import annotations

import asyncio
import threading
import weakref
from collections.abc import Mapping
from typing import Protocol

from typesafe_sdk import (
    AsyncTypeSafeClient,
    Choice,
    ChoiceAnswer,
    Noul,
    NoulAnswer,
    Score,
    ScoreAnswer,
    SystemOneResponse,
    TypeSafeClient,
)
from typesafe_sdk import Question as TypeSafeQuestion

from vibecheck._questions import (
    Answer,
    Content,
    Pick,
    PickAnswer,
    Question,
    RateAnswer,
    YesNo,
    YesNoAnswer,
)

__all__ = [
    "Backend",
    "TypeSafeBackend",
    "get_default_backend",
    "set_default_backend",
]


class Backend(Protocol):
    """Anything that can answer a set of questions about one piece of content."""

    def evaluate(
        self,
        state: Content,
        questions: Mapping[str, Question],
        *,
        model: str | None = None,
    ) -> dict[str, Answer]: ...

    async def aevaluate(
        self,
        state: Content,
        questions: Mapping[str, Question],
        *,
        model: str | None = None,
    ) -> dict[str, Answer]: ...


class TypeSafeBackend:
    """Speaks TypeSafe's System One API (`POST /v1/systemone`).

    Any compatible server works: TypeSafe itself, Vercel AI Gateway's `/typesafe` endpoint, or LangSmith's LLM
    gateway. Configure it with the SDK's environment variables (`TYPESAFE_API_KEY`, `TYPESAFE_BASE_URL`,
    `TYPESAFE_DEFAULT_MODEL`) or pass clients explicitly.
    """

    def __init__(
        self,
        client: TypeSafeClient | None = None,
        async_client: AsyncTypeSafeClient | None = None,
    ) -> None:
        self._client = client
        self._async_client = async_client
        self._async_clients: weakref.WeakKeyDictionary[
            asyncio.AbstractEventLoop, AsyncTypeSafeClient
        ] = weakref.WeakKeyDictionary()
        self._lock = threading.Lock()

    def _sync_client(self) -> TypeSafeClient:
        with self._lock:
            if self._client is None:
                self._client = TypeSafeClient()
            return self._client

    def _loop_client(self) -> AsyncTypeSafeClient:
        if self._async_client is not None:
            return self._async_client
        loop = asyncio.get_running_loop()
        client = self._async_clients.get(loop)
        if client is None:
            client = AsyncTypeSafeClient()
            self._async_clients[loop] = client
        return client

    def evaluate(
        self,
        state: Content,
        questions: Mapping[str, Question],
        *,
        model: str | None = None,
    ) -> dict[str, Answer]:
        response = self._sync_client().system_one(
            state, _to_wire(questions), model=model
        )
        return _from_wire(response)

    async def aevaluate(
        self,
        state: Content,
        questions: Mapping[str, Question],
        *,
        model: str | None = None,
    ) -> dict[str, Answer]:
        response = await self._loop_client().system_one(
            state, _to_wire(questions), model=model
        )
        return _from_wire(response)


def _to_wire(questions: Mapping[str, Question]) -> dict[str, TypeSafeQuestion]:
    wire: dict[str, TypeSafeQuestion] = {}
    for name, question in questions.items():
        if isinstance(question, YesNo):
            wire[name] = Noul(instructions=question.instructions)
        elif isinstance(question, Pick):
            wire[name] = Choice(
                instructions=question.instructions, criteria=dict(question.options)
            )
        else:
            wire[name] = Score(
                instructions=question.instructions, criteria=list(question.levels)
            )
    return wire


def _from_wire(response: SystemOneResponse) -> dict[str, Answer]:
    answers: dict[str, Answer] = {}
    for name, answer in response.answers.items():
        if isinstance(answer, NoulAnswer):
            answers[name] = YesNoAnswer(probability=answer.noul)
        elif isinstance(answer, ChoiceAnswer):
            answers[name] = PickAnswer(probabilities=dict(answer.probabilities))
        elif isinstance(answer, ScoreAnswer):
            levels = sorted(answer.probabilities)
            answers[name] = RateAnswer(
                probabilities=[answer.probabilities[level] for level in levels]
            )
    return answers


_default_backend: Backend | None = None


def get_default_backend() -> Backend:
    """The backend used when a call doesn't pass one. Defaults to a `TypeSafeBackend`."""
    global _default_backend
    if _default_backend is None:
        _default_backend = TypeSafeBackend()
    return _default_backend


def set_default_backend(backend: Backend | None) -> None:
    """Replace the default backend. Pass `None` to go back to a fresh `TypeSafeBackend`."""
    global _default_backend
    _default_backend = backend
