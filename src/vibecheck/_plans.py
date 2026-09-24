"""Compile each verb's arguments into questions for a decision model, and decode the answers."""

from __future__ import annotations

import dataclasses
import inspect
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from itertools import pairwise
from typing import (
    Annotated,
    Any,
    Generic,
    Literal,
    NamedTuple,
    TypeAlias,
    TypeVar,
    get_args,
    get_origin,
    get_type_hints,
    is_typeddict,
)

from pydantic import BaseModel

from vibecheck._questions import (
    Answer,
    Content,
    Pick,
    PickAnswer,
    Question,
    Rate,
    RateAnswer,
    YesNo,
    YesNoAnswer,
)

A = TypeVar("A")
P = TypeVar("P")

MIN_OPTIONS = 2
MAX_OPTIONS = 255
MIN_LEVELS = 2
MAX_LEVELS = 10

KEY = "answer"

Threshold: TypeAlias = float | tuple[float, float]
Answers: TypeAlias = Mapping[str, Answer]


class Decision(NamedTuple, Generic[A, P]):
    """An answer, and the probabilities behind it."""

    answer: A
    probabilities: P


@dataclass(frozen=True)
class Plan:
    """The questions to send, and how to decode the model's answers.

    `decide` produces the answer a verb returns. `explain` produces the probabilities behind it.
    """

    questions: Mapping[str, Question]
    decide: Callable[[Answers], Any]
    explain: Callable[[Answers], Any]

    def finish(self, answers: Answers, *, probabilities: bool) -> Any:
        answer = self.decide(answers)
        if probabilities:
            return Decision(answer, self.explain(answers))
        return answer

    def prefixed(self, prefix: str) -> Plan:
        """The same plan with its question names namespaced, so plans can share one request."""
        head = f"{prefix}."

        def view(answers: Answers) -> Answers:
            return {
                name[len(head) :]: answer
                for name, answer in answers.items()
                if name.startswith(head)
            }

        return Plan(
            questions={head + name: q for name, q in self.questions.items()},
            decide=lambda answers: self.decide(view(answers)),
            explain=lambda answers: self.explain(view(answers)),
        )


def check(question: str, *, threshold: Threshold) -> Plan:
    return _check(_question(question), threshold)


def classify(question: str, options: Iterable[Any]) -> Plan:
    return _classify(_question(question), options)


def label(
    question: str, options: Iterable[Any], *, threshold: float, limit: int | None
) -> Plan:
    return _label(_question(question), options, threshold=threshold, limit=limit)


def score(question: str, levels: Iterable[Any]) -> Plan:
    return _score(_question(question), levels, returns=float)


def assess(question: str, model: type, *, threshold: float) -> Plan:
    task = _question(question)
    if not is_model(model):
        raise TypeError(
            f"assess() takes a model class (a dataclass, Pydantic model, TypedDict, or NamedTuple), "
            f"got {model!r}"
        )
    fields = {
        name: _field(model, name, annotation, task, threshold).prefixed(name)
        for name, annotation in _model_fields(model)
    }
    if not fields:
        raise TypeError(f"{model.__name__} has no fields to ask about")
    return Plan(
        questions={k: q for plan in fields.values() for k, q in plan.questions.items()},
        decide=lambda answers: model(
            **{name: plan.decide(answers) for name, plan in fields.items()}
        ),
        explain=lambda answers: {
            name: plan.explain(answers) for name, plan in fields.items()
        },
    )


def option_values(options: Iterable[Any]) -> list[Any]:
    """The caller's options, in order, after validation."""
    return [option for _, option, _ in _options(options)]


def _question(question: object) -> str:
    if not isinstance(question, str):
        raise TypeError(
            f"the question must be a string, got {type(question).__name__}; "
            "the question comes first and the data last"
        )
    if not question.strip():
        raise ValueError("the question can't be empty")
    return question


def _check(instructions: Content, threshold: Threshold) -> Plan:
    low, high = _band(threshold)

    def probability(answers: Answers) -> float:
        answer = answers[KEY]
        assert isinstance(answer, YesNoAnswer)
        return answer.probability

    def decide(answers: Answers) -> bool | None:
        p = probability(answers)
        if p >= high:
            return True
        if p < low:
            return False
        return None

    return Plan({KEY: YesNo(instructions=instructions)}, decide, probability)


def _classify(instructions: Content, options: Iterable[Any]) -> Plan:
    choices = _options(options)
    by_label = {label: option for label, option, _ in choices}

    def distribution(answers: Answers) -> Mapping[str, float]:
        answer = answers[KEY]
        assert isinstance(answer, PickAnswer)
        return answer.probabilities

    def decide(answers: Answers) -> Any:
        dist = distribution(answers)
        return by_label[max(by_label, key=lambda label: dist.get(label, 0.0))]

    def explain(answers: Answers) -> dict[Any, float]:
        dist = distribution(answers)
        return {option: dist.get(label, 0.0) for label, option in by_label.items()}

    question = Pick(
        instructions=instructions,
        options={label: description for label, _, description in choices},
    )
    return Plan({KEY: question}, decide, explain)


def _label(
    instructions: Content,
    options: Iterable[Any],
    *,
    threshold: float,
    limit: int | None,
) -> Plan:
    if not isinstance(threshold, (int, float)) or not 0 <= threshold <= 1:
        raise ValueError("a label threshold must be a number between 0 and 1")
    if limit is not None and limit < 1:
        raise ValueError("limit must be at least 1")
    choices = _options(options)
    questions = {
        f"o{i}": YesNo(
            instructions=_merge(instructions, label=label, description=description)
        )
        for i, (label, _, description) in enumerate(choices)
    }

    def probabilities(answers: Answers) -> list[tuple[Any, float]]:
        pairs = []
        for i, (_, option, _) in enumerate(choices):
            answer = answers[f"o{i}"]
            assert isinstance(answer, YesNoAnswer)
            pairs.append((option, answer.probability))
        return pairs

    def decide(answers: Answers) -> list[Any]:
        ranked = sorted(probabilities(answers), key=lambda pair: pair[1], reverse=True)
        chosen = [option for option, p in ranked if p >= threshold]
        return chosen[:limit] if limit is not None else chosen

    def explain(answers: Answers) -> dict[Any, float]:
        return dict(probabilities(answers))

    return Plan(questions, decide, explain)


def _score(instructions: Content, levels: Iterable[Any], *, returns: type) -> Plan:
    values, descriptions = _levels(levels)

    def distribution(answers: Answers) -> Sequence[float]:
        answer = answers[KEY]
        assert isinstance(answer, RateAnswer)
        return answer.probabilities

    def decide(answers: Answers) -> float:
        dist = distribution(answers)
        total = sum(dist) or 1.0
        position = sum(v * p for v, p in zip(values, dist, strict=True)) / total
        return round(position) if returns is int else round(position, 6)

    def explain(answers: Answers) -> dict[float, float]:
        return dict(zip(values, distribution(answers), strict=True))

    return Plan(
        {KEY: Rate(instructions=instructions, levels=descriptions)}, decide, explain
    )


def _field(
    model: type, name: str, annotation: Any, task: str, threshold: float
) -> Plan:
    base, metadata = _unwrap(annotation)
    field_question = next(
        (m for m in metadata if isinstance(m, str)), name.replace("_", " ")
    )
    instructions: Content = {"task": task, "question": field_question}
    spec = next(
        (m for m in metadata if isinstance(m, (Mapping, range, list, tuple))), None
    )
    origin = get_origin(base)

    if base is bool:
        return _check(instructions, threshold)
    if base in (float, int):
        if spec is None:
            raise TypeError(
                f"{model.__name__}.{name}: a number field needs its levels, e.g. "
                'Annotated[float, "How severe?", ["low", "medium", "high"]]'
            )
        return _score(instructions, spec, returns=base)
    if origin is list:
        (item,) = get_args(base) or (Any,)
        options = spec if spec is not None else _options_from_type(item)
        if options is None:
            raise TypeError(
                f"{model.__name__}.{name}: a list field needs its options, as Literal[...], an Enum, "
                "or an annotation"
            )
        return _label(instructions, options, threshold=threshold, limit=None)
    if spec is not None:
        return _classify(instructions, spec)
    options = _options_from_type(base)
    if options is not None:
        return _classify(instructions, options)
    raise TypeError(
        f"{model.__name__}.{name}: can't ask for {base!r}. Use bool, Literal[...], an Enum, "
        "list[...] of those, or Annotated[..., <options or levels>]"
    )


def _options_from_type(tp: Any) -> list[Any] | None:
    if get_origin(tp) is Literal:
        return list(get_args(tp))
    if isinstance(tp, type) and issubclass(tp, Enum):
        return list(tp)
    return None


def _band(threshold: object) -> tuple[float, float]:
    if isinstance(threshold, tuple):
        if len(threshold) != 2:
            raise ValueError("a threshold band is a pair: (low, high)")
        low, high = threshold
        if not 0 <= low <= high <= 1:
            raise ValueError("a threshold band needs 0 <= low <= high <= 1")
        return float(low), float(high)
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        raise TypeError("threshold must be a number or a (low, high) pair")
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    return float(threshold), float(threshold)


def _options(options: Iterable[Any]) -> list[tuple[str, Any, Content | None]]:
    """Each option's label, the option itself, and its description."""
    if isinstance(options, str):
        raise TypeError(
            "options can't be a single string; pass a list, e.g. ['yes', 'no']"
        )
    descriptions: Mapping[Any, Any] = options if isinstance(options, Mapping) else {}
    values = list(options)
    if not MIN_OPTIONS <= len(values) <= MAX_OPTIONS:
        raise ValueError(
            f"pass {MIN_OPTIONS} to {MAX_OPTIONS} options, got {len(values)}"
        )
    seen: set[str] = set()
    result = []
    for option in values:
        label, default = _label_for(option)
        if label in seen:
            raise ValueError(
                f"two options share the label {label!r}; the answer couldn't be mapped back"
            )
        seen.add(label)
        given = descriptions.get(option)
        result.append(
            (label, option, _content(given) if given is not None else default)
        )
    return result


def _levels(levels: Iterable[Any]) -> tuple[list[Any], list[Content]]:
    if isinstance(levels, str):
        raise TypeError("levels can't be a single string; pass a list of levels")
    values: list[Any]
    descriptions: list[Content]
    if isinstance(levels, Mapping):
        if not all(_is_number(k) for k in levels):
            raise TypeError("a dict of levels maps numbers to descriptions")
        ordered = sorted(levels.items())
        values = [k for k, _ in ordered]
        descriptions = [_content(v) for _, v in ordered]
    else:
        items = list(levels)
        if all(_is_number(v) for v in items):
            values = items
            descriptions = [str(v) for v in items]
        else:
            values = list(range(len(items)))
            descriptions = [_content(v) for v in items]
    if not MIN_LEVELS <= len(values) <= MAX_LEVELS:
        raise ValueError(
            f"a scale needs {MIN_LEVELS} to {MAX_LEVELS} levels, got {len(values)}"
        )
    if any(b <= a for a, b in pairwise(values)):
        raise ValueError("levels must go from lowest to highest, with no repeats")
    return values, descriptions


def _merge(instructions: Content, **extra: Content | None) -> Content:
    base: dict[str, Any] = (
        dict(instructions)
        if isinstance(instructions, Mapping)
        else {"question": instructions}
    )
    base.update({key: value for key, value in extra.items() if value is not None})
    return base


def is_model(spec: object) -> bool:
    if not isinstance(spec, type) or issubclass(spec, Enum) or spec is bool:
        return False
    return (
        issubclass(spec, BaseModel)
        or dataclasses.is_dataclass(spec)
        or is_typeddict(spec)
        or (issubclass(spec, tuple) and "_fields" in vars(spec))
    )


def _model_fields(model: type) -> list[tuple[str, Any]]:
    hints = get_type_hints(model, include_extras=True)
    if issubclass(model, BaseModel):
        names = list(model.model_fields)
    elif dataclasses.is_dataclass(model):
        names = [f.name for f in dataclasses.fields(model)]
    else:
        names = list(hints)
    return [(name, hints[name]) for name in names]


def _unwrap(annotation: Any) -> tuple[Any, tuple[Any, ...]]:
    if get_origin(annotation) is Annotated:
        base, *metadata = get_args(annotation)
        return base, tuple(metadata)
    return annotation, ()


def _label_for(option: Any) -> tuple[str, Content | None]:
    """The text label sent for an option, and a default description if the option carries one."""
    if isinstance(option, str):
        return option, None
    if isinstance(option, Enum):
        return (option.value if isinstance(option.value, str) else option.name), None
    if inspect.isroutine(option) or inspect.isclass(option):
        doc = inspect.getdoc(option)
        return option.__name__, (doc.strip().splitlines()[0] if doc else None)
    return str(option), None


def _content(value: Any) -> Content:
    if isinstance(value, (str, Mapping)) or (
        isinstance(value, Sequence) and not isinstance(value, str)
    ):
        return value
    return str(value)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
