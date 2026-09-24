from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TypeAlias

JSON: TypeAlias = (
    str | int | float | bool | None | Sequence["JSON"] | Mapping[str, "JSON"]
)
"""A JSON-compatible value."""

Content: TypeAlias = str | Sequence[JSON] | Mapping[str, JSON]
"""Text or structured JSON that a decision model can read."""


@dataclass(frozen=True)
class YesNo:
    """A yes/no question. The model answers with the probability of yes."""

    instructions: Content


@dataclass(frozen=True)
class Pick:
    """Pick one of several unordered options, keyed by label."""

    instructions: Content
    options: Mapping[str, Content | None]


@dataclass(frozen=True)
class Rate:
    """Rate against ordered levels, described from lowest to highest."""

    instructions: Content
    levels: Sequence[Content]


Question: TypeAlias = YesNo | Pick | Rate


@dataclass(frozen=True)
class YesNoAnswer:
    probability: float
    """Probability of yes, from 0 to 1."""


@dataclass(frozen=True)
class PickAnswer:
    probabilities: Mapping[str, float]
    """Probability of each option, keyed by label."""


@dataclass(frozen=True)
class RateAnswer:
    probabilities: Sequence[float]
    """Probability of each level, in level order."""


Answer: TypeAlias = YesNoAnswer | PickAnswer | RateAnswer
