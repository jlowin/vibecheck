"""Test helpers: a backend that answers from your own function instead of a model."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

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

__all__ = ["Call", "FakeBackend", "pick", "rate", "yes"]


@dataclass(frozen=True)
class Call:
    """One request the fake backend received."""

    state: Content
    questions: Mapping[str, Question]
    model: str | None


def _uniform(question: Question) -> Answer:
    if isinstance(question, YesNo):
        return YesNoAnswer(probability=0.5)
    if isinstance(question, Pick):
        n = len(question.options)
        return PickAnswer(probabilities={label: 1 / n for label in question.options})
    n = len(question.levels)
    return RateAnswer(probabilities=[1 / n] * n)


@dataclass
class FakeBackend:
    """Answers every question with `respond(state, name, question)` and records each request.

    Without `respond`, yes/no questions get 0.5 and every option or level is equally likely.
    """

    respond: Callable[[Content, str, Question], Answer] = lambda state, name, question: (
        _uniform(question)
    )
    calls: list[Call] = field(default_factory=list)

    def evaluate(
        self,
        state: Content,
        questions: Mapping[str, Question],
        *,
        model: str | None = None,
    ) -> dict[str, Answer]:
        self.calls.append(Call(state=state, questions=dict(questions), model=model))
        return {
            name: self.respond(state, name, question)
            for name, question in questions.items()
        }

    async def aevaluate(
        self,
        state: Content,
        questions: Mapping[str, Question],
        *,
        model: str | None = None,
    ) -> dict[str, Answer]:
        return self.evaluate(state, questions, model=model)


def yes(probability: float = 1.0) -> YesNoAnswer:
    return YesNoAnswer(probability=probability)


def pick(**probabilities: float) -> PickAnswer:
    return PickAnswer(probabilities=probabilities)


def rate(*probabilities: float) -> RateAnswer:
    return RateAnswer(probabilities=list(probabilities))
