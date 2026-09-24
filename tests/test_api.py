import asyncio
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Any, Literal, NamedTuple, TypedDict

import pytest
from pydantic import BaseModel

import vibecheck
from vibecheck import Decision, sync
from vibecheck._questions import Pick, Rate, YesNo
from vibecheck.testing import FakeBackend, pick, rate, yes


def always(answer):
    return FakeBackend(respond=lambda state, name, question: answer)


def labels_backend(probabilities: dict[str, float]) -> FakeBackend:
    """Answers each label's yes/no question with its probability from `probabilities`."""

    def respond(state, name, question):
        return yes(probabilities[question.instructions["label"]])

    return FakeBackend(respond=respond)


def typed_backend() -> FakeBackend:
    """Yes/no: 0.9. Pick one: the second option. Scales: 40% on level 1, 60% on level 2."""

    def respond(state, name, question):
        if isinstance(question, YesNo):
            return yes(0.9)
        if isinstance(question, Pick):
            return pick(
                **{
                    label: 1.0 if i == 1 else 0.0
                    for i, label in enumerate(question.options)
                }
            )
        return rate(0.0, 0.4, 0.6)

    return FakeBackend(respond=respond)


class Sentiment(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


def refund(ticket: str) -> None:
    """Customer wants money back.

    Includes duplicate charges.
    """


def escalate(ticket: str) -> None:
    """Anything else."""


class TestCheck:
    @pytest.mark.parametrize(
        ("probability", "threshold", "expected"),
        [(0.9, 0.5, True), (0.5, 0.5, True), (0.4, 0.5, False), (0.8, 0.9, False)],
    )
    def test_threshold(self, probability, threshold, expected):
        backend = always(yes(probability))
        assert sync.check("q?", "x", threshold=threshold, backend=backend) is expected

    @pytest.mark.parametrize(
        ("probability", "expected"),
        [(0.95, True), (0.9, True), (0.5, None), (0.3, None), (0.1, False)],
    )
    def test_threshold_band_is_three_way(self, probability, expected):
        backend = always(yes(probability))
        assert sync.check("q?", "x", threshold=(0.3, 0.9), backend=backend) is expected

    def test_probabilities_pair_the_answer_with_p_yes(self):
        result = sync.check("q?", "x", probabilities=True, backend=always(yes(0.2)))
        assert result == Decision(False, 0.2)
        answer, p = result
        assert (answer, p) == (False, 0.2)

    def test_question_is_instructions_and_data_is_state(self):
        backend = always(yes())
        sync.check("Is this urgent?", "the ticket", backend=backend)
        assert backend.calls[0].state == "the ticket"
        assert backend.calls[0].questions == {
            "answer": YesNo(instructions="Is this urgent?")
        }

    def test_data_is_optional(self):
        backend = always(yes())
        sync.check("Is Paris the capital of France?", backend=backend)
        assert backend.calls[0].state == ""

    def test_model_name_is_forwarded(self):
        backend = always(yes())
        sync.check("q?", "x", model="jev-1.13.0", backend=backend)
        assert backend.calls[0].model == "jev-1.13.0"

    def test_question_must_come_first(self):
        data_first: Any = {"ticket": "hi"}
        with pytest.raises(TypeError, match="question comes first"):
            sync.check(data_first, "Is this urgent?", backend=always(yes()))

    def test_empty_question_rejected(self):
        with pytest.raises(ValueError, match="empty"):
            sync.check("  ", "x", backend=always(yes()))

    @pytest.mark.parametrize("threshold", [1.5, -0.1, (0.9, 0.3), (0.1, 0.2, 0.3)])
    def test_invalid_threshold(self, threshold):
        with pytest.raises(ValueError):
            sync.check("q?", "x", threshold=threshold, backend=always(yes()))


class TestData:
    @dataclass
    class Order:
        id: str
        charges: list[float]

    class Ticket(BaseModel):
        subject: str

    class Opaque:
        def __str__(self) -> str:
            return "opaque object"

    @pytest.mark.parametrize(
        ("data", "state"),
        [
            ({"a": 1}, {"a": 1}),
            ([1, 2], [1, 2]),
            (Order(id="A-1", charges=[49.0]), {"id": "A-1", "charges": [49.0]}),
            (Ticket(subject="hi"), {"subject": "hi"}),
            (Opaque(), "opaque object"),
            (42, "42"),
        ],
    )
    def test_serialization(self, data, state):
        backend = always(yes())
        sync.check("q?", data, backend=backend)
        assert backend.calls[0].state == state


class TestClassify:
    def test_list_returns_option(self):
        backend = always(pick(returns=0.2, billing=0.8))
        assert (
            sync.classify("Team?", ["returns", "billing"], "x", backend=backend)
            == "billing"
        )

    def test_dict_sends_descriptions(self):
        backend = always(pick(returns=1.0, billing=0.0))
        sync.classify(
            "Team?",
            {"returns": "Exchanges", "billing": "Charges"},
            "x",
            backend=backend,
        )
        question = backend.calls[0].questions["answer"]
        assert isinstance(question, Pick)
        assert question.options == {"returns": "Exchanges", "billing": "Charges"}

    def test_enum_class_returns_member(self):
        backend = always(pick(positive=0.1, negative=0.9))
        assert (
            sync.classify("Tone?", Sentiment, "x", backend=backend)
            is Sentiment.NEGATIVE
        )

    def test_functions_are_labelled_by_name_and_described_by_signature_and_docstring(
        self,
    ):
        backend = always(pick(refund=0.9, escalate=0.1))
        handler = sync.classify(
            "How to handle?", [refund, escalate], "x", backend=backend
        )
        question = backend.calls[0].questions["answer"]
        assert handler is refund
        assert question.options == {
            "refund": {
                "signature": "refund(ticket: str) -> None",
                "docstring": "Customer wants money back.\n\nIncludes duplicate charges.",
            },
            "escalate": {
                "signature": "escalate(ticket: str) -> None",
                "docstring": "Anything else.",
            },
        }

    def test_classes_are_described_by_init_signature_and_docstring(self):
        class Refund:
            """Money back for a charge."""

            def __init__(self, order_id: str, amount: float) -> None: ...

        class Escalate:
            """Anything else."""

            def __init__(self, reason: str) -> None: ...

        backend = always(pick(Refund=0.9, Escalate=0.1))
        assert (
            sync.classify("How to handle?", [Refund, Escalate], "x", backend=backend)
            is Refund
        )
        question = backend.calls[0].questions["answer"]
        assert question.options["Refund"] == {
            "signature": "Refund(order_id: str, amount: float) -> None",
            "docstring": "Money back for a charge.",
        }

    def test_function_without_docstring_is_described_by_signature(self):
        def archive(ticket: str) -> None: ...

        backend = always(pick(archive=0.9, escalate=0.1))
        sync.classify("How to handle?", [archive, escalate], "x", backend=backend)
        question = backend.calls[0].questions["answer"]
        assert question.options["archive"] == {
            "signature": "archive(ticket: str) -> None"
        }

    def test_dict_value_overrides_function_description(self):
        backend = always(pick(refund=0.9, escalate=0.1))
        sync.classify(
            "How to handle?",
            {refund: "Money back", escalate: "Everything else"},
            "x",
            backend=backend,
        )
        question = backend.calls[0].questions["answer"]
        assert question.options == {
            "refund": "Money back",
            "escalate": "Everything else",
        }

    def test_non_string_values_are_restored(self):
        backend = always(pick(**{"2024": 0.3, "2025": 0.7}))
        assert sync.classify("Year?", [2024, 2025], "x", backend=backend) == 2025

    def test_probabilities_are_keyed_by_option(self):
        backend = always(pick(positive=0.1, negative=0.9))
        team, dist = sync.classify(
            "Tone?", Sentiment, "x", probabilities=True, backend=backend
        )
        assert team is Sentiment.NEGATIVE
        assert dist == {Sentiment.POSITIVE: 0.1, Sentiment.NEGATIVE: 0.9}

    def test_duplicate_labels_rejected(self):
        with pytest.raises(ValueError, match="share the label"):
            sync.classify("q?", ["a", "a"], "x", backend=always(pick()))

    def test_single_string_options_rejected(self):
        with pytest.raises(TypeError, match="single string"):
            sync.classify("q?", "abc", "x", backend=always(pick()))

    @pytest.mark.parametrize("options", [["only"], [str(i) for i in range(256)]])
    def test_option_count_limits(self, options):
        with pytest.raises(ValueError, match="options"):
            sync.classify("q?", options, "x", backend=always(pick()))


TOPICS = ("pricing", "security", "layoffs", "roadmap")
TOPIC_PROBABILITIES = {"pricing": 0.6, "security": 0.95, "layoffs": 0.1, "roadmap": 0.7}
TICKETS = ("refund me", "where is my package", "refund please", "thanks!")


class TestLabel:
    def test_returns_labels_above_threshold_most_likely_first(self):
        backend = labels_backend(TOPIC_PROBABILITIES)
        assert sync.label("Topics?", TOPICS, "doc", backend=backend) == [
            "security",
            "roadmap",
            "pricing",
        ]

    def test_threshold(self):
        backend = labels_backend(TOPIC_PROBABILITIES)
        result = sync.label("Topics?", TOPICS, "doc", threshold=0.8, backend=backend)
        assert result == ["security"]

    def test_limit(self):
        backend = labels_backend(TOPIC_PROBABILITIES)
        result = sync.label("Topics?", TOPICS, "doc", limit=2, backend=backend)
        assert result == ["security", "roadmap"]

    def test_limit_with_zero_threshold_gives_exactly_n(self):
        backend = labels_backend(
            {"pricing": 0.2, "security": 0.1, "layoffs": 0.05, "roadmap": 0.3}
        )
        result = sync.label(
            "Topics?", TOPICS, "doc", threshold=0, limit=2, backend=backend
        )
        assert result == ["roadmap", "pricing"]

    def test_probabilities_cover_every_option(self):
        backend = labels_backend(TOPIC_PROBABILITIES)
        tags, dist = sync.label(
            "Topics?", TOPICS, "doc", probabilities=True, backend=backend
        )
        assert tags == ["security", "roadmap", "pricing"]
        assert dist == TOPIC_PROBABILITIES

    def test_one_request_with_one_yes_no_per_option(self):
        backend = labels_backend(TOPIC_PROBABILITIES)
        sync.label(
            "Topics?",
            {"pricing": "Costs and plans", "security": None},
            "doc",
            backend=backend,
        )
        assert len(backend.calls) == 1
        assert list(backend.calls[0].questions.values()) == [
            YesNo(
                instructions={
                    "question": "Topics?",
                    "label": "pricing",
                    "description": "Costs and plans",
                }
            ),
            YesNo(instructions={"question": "Topics?", "label": "security"}),
        ]

    def test_invalid_limit(self):
        with pytest.raises(ValueError, match="limit"):
            sync.label(
                "q?",
                TOPICS,
                "doc",
                limit=0,
                backend=labels_backend(TOPIC_PROBABILITIES),
            )


class TestScore:
    def test_described_levels_return_position(self):
        backend = always(rate(0.0, 0.5, 0.5))
        assert (
            sync.score("Severity?", ["low", "mid", "high"], "x", backend=backend) == 1.5
        )

    def test_sends_levels_in_order(self):
        backend = always(rate(1.0, 0.0, 0.0))
        sync.score("Severity?", ["low", "mid", "high"], "x", backend=backend)
        assert backend.calls[0].questions["answer"] == Rate(
            instructions="Severity?", levels=["low", "mid", "high"]
        )

    @pytest.mark.parametrize(
        ("levels", "probabilities", "expected"),
        [
            (range(1, 6), (0, 0, 0, 0.5, 0.5), 4.5),
            ({1: "angry", 5: "happy"}, (0.25, 0.75), 4.0),
            ([0.0, 0.25, 1.0], (0.0, 0.0, 1.0), 1.0),
        ],
    )
    def test_answers_in_the_levels_units(self, levels, probabilities, expected):
        backend = always(rate(*probabilities))
        assert sync.score("Rate?", levels, "x", backend=backend) == pytest.approx(
            expected
        )

    def test_probabilities_are_keyed_by_level(self):
        backend = always(rate(0.1, 0.7, 0.2))
        position, dist = sync.score(
            "Rate?", range(1, 4), "x", probabilities=True, backend=backend
        )
        assert position == pytest.approx(2.1)
        assert dist == {1: 0.1, 2: 0.7, 3: 0.2}

    def test_dict_levels_are_sorted(self):
        backend = always(rate(1.0, 0.0))
        sync.score("Rate?", {5: "happy", 1: "angry"}, "x", backend=backend)
        assert backend.calls[0].questions["answer"].levels == ["angry", "happy"]

    @pytest.mark.parametrize("levels", [["one"], [str(i) for i in range(11)]])
    def test_level_count_limits(self, levels):
        with pytest.raises(ValueError, match="levels"):
            sync.score("q?", levels, "x", backend=always(rate()))

    def test_numeric_levels_must_increase(self):
        with pytest.raises(ValueError, match="lowest to highest"):
            sync.score("q?", [1.0, 0.5], "x", backend=always(rate()))


@dataclass
class TriageDataclass:
    team: Literal["returns", "billing"]
    urgent: Annotated[bool, "Does this need a reply today?"]
    frustration: Annotated[float, "How frustrated?", ["calm", "annoyed", "angry"]]


class TriagePydantic(BaseModel):
    team: Literal["returns", "billing"]
    urgent: Annotated[bool, "Does this need a reply today?"]
    frustration: Annotated[float, "How frustrated?", ["calm", "annoyed", "angry"]]


class TriageTuple(NamedTuple):
    team: Literal["returns", "billing"]
    urgent: Annotated[bool, "Does this need a reply today?"]
    frustration: Annotated[float, "How frustrated?", ["calm", "annoyed", "angry"]]


class TriageDict(TypedDict):
    team: Literal["returns", "billing"]
    urgent: Annotated[bool, "Does this need a reply today?"]
    frustration: Annotated[float, "How frustrated?", ["calm", "annoyed", "angry"]]


class TestAssess:
    @pytest.mark.parametrize("schema", [TriageDataclass, TriagePydantic, TriageTuple])
    def test_fills_every_field(self, schema):
        result = sync.assess("Triage this", schema, "x", backend=typed_backend())
        assert isinstance(result, schema)
        assert (result.team, result.urgent) == ("billing", True)
        assert result.frustration == pytest.approx(1.6)

    def test_typeddict_returns_dict(self):
        result = sync.assess("Triage this", TriageDict, "x", backend=typed_backend())
        assert result == {
            "team": "billing",
            "urgent": True,
            "frustration": pytest.approx(1.6),
        }

    def test_one_request_with_shared_task(self):
        backend = typed_backend()
        sync.assess("Triage this ticket", TriageDataclass, "x", backend=backend)
        assert len(backend.calls) == 1
        assert backend.calls[0].questions["urgent.answer"] == YesNo(
            instructions={
                "task": "Triage this ticket",
                "question": "Does this need a reply today?",
            }
        )

    def test_field_name_is_the_default_question(self):
        backend = typed_backend()
        sync.assess("Triage this", TriageDataclass, "x", backend=backend)
        instructions = backend.calls[0].questions["team.answer"].instructions
        assert isinstance(instructions, Mapping)
        assert instructions["question"] == "team"

    @pytest.mark.parametrize(
        ("returns", "expected"), [(float, pytest.approx(1.6)), (int, 2)]
    )
    def test_number_field_type_decides_rounding(self, returns, expected):
        @dataclass
        class Rating:
            level: Annotated[returns, ["calm", "annoyed", "angry"]]

        assert (
            sync.assess("Rate", Rating, "x", backend=typed_backend()).level == expected
        )

    def test_list_field_is_a_label(self):
        @dataclass
        class Topics:
            covered: list[Literal["pricing", "security"]]

        backend = typed_backend()
        result = sync.assess("Topics", Topics, "x", backend=backend)
        assert result.covered == ["pricing", "security"]
        assert sorted(backend.calls[0].questions) == ["covered.o0", "covered.o1"]

    def test_annotated_options_on_a_plain_field_classify(self):
        @dataclass
        class Route:
            handler: Annotated[object, "How to handle this?", [refund, escalate]]

        assert (
            sync.assess("Route", Route, "x", backend=typed_backend()).handler
            is escalate
        )

    def test_enum_field(self):
        @dataclass
        class Tone:
            sentiment: Sentiment

        assert (
            sync.assess("Tone", Tone, "x", backend=typed_backend()).sentiment
            is Sentiment.NEGATIVE
        )

    def test_probabilities_are_keyed_by_field(self):
        result = sync.assess(
            "Triage", TriageDataclass, "x", probabilities=True, backend=typed_backend()
        )
        assert result.probabilities["urgent"] == 0.9
        assert result.probabilities["team"] == {"returns": 0.0, "billing": 1.0}

    def test_number_field_needs_levels(self):
        @dataclass
        class Bad:
            size: float

        with pytest.raises(TypeError, match="Bad.size"):
            sync.assess("q", Bad, "x", backend=typed_backend())

    def test_unsupported_field(self):
        @dataclass
        class Bad:
            name: str

        with pytest.raises(TypeError, match="Bad.name"):
            sync.assess("q", Bad, "x", backend=typed_backend())

    def test_rejects_non_model(self):
        with pytest.raises(TypeError, match="model class"):
            sync.assess("q", int, "x", backend=typed_backend())


def refund_backend() -> FakeBackend:
    return FakeBackend(
        respond=lambda state, name, question: yes(0.9 if "refund" in state else 0.1)
    )


class TestFilter:
    def test_keeps_matching_items_in_order(self):
        backend = refund_backend()
        assert sync.filter("Refund?", TICKETS, backend=backend) == [
            "refund me",
            "refund please",
        ]
        assert len(backend.calls) == len(TICKETS)

    def test_threshold(self):
        assert (
            sync.filter("Refund?", TICKETS, threshold=0.95, backend=refund_backend())
            == []
        )

    def test_probabilities_cover_every_item(self):
        kept, probabilities = sync.filter(
            "Refund?", TICKETS, probabilities=True, backend=refund_backend()
        )
        assert kept == ["refund me", "refund please"]
        assert probabilities == [0.9, 0.1, 0.9, 0.1]

    def test_empty(self):
        assert sync.filter("q?", [], backend=refund_backend()) == []


class TestGroup:
    def test_buckets_every_option_in_order(self):
        backend = FakeBackend(
            respond=lambda state, name, question: pick(
                billing=1.0 if "charge" in state else 0.0,
                shipping=0.0 if "charge" in state else 1.0,
                returns=0.0,
            )
        )
        result = sync.group(
            "Which team?",
            ["returns", "billing", "shipping"],
            ["double charge", "late box", "charge"],
            backend=backend,
        )
        assert result == {
            "returns": [],
            "billing": ["double charge", "charge"],
            "shipping": ["late box"],
        }
        assert list(result) == ["returns", "billing", "shipping"]

    def test_probabilities_cover_every_item(self):
        backend = always(pick(a=0.8, b=0.2))
        groups, probabilities = sync.group(
            "q?", ["a", "b"], ["x", "y"], probabilities=True, backend=backend
        )
        assert groups == {"a": ["x", "y"], "b": []}
        assert probabilities == [{"a": 0.8, "b": 0.2}, {"a": 0.8, "b": 0.2}]

    def test_generator_options(self):
        backend = always(pick(a=0.8, b=0.2))
        result = sync.group("q?", (o for o in ["a", "b"]), ["x"], backend=backend)
        assert result == {"a": ["x"], "b": []}


class TestBatch:
    def test_sends_one_request_for_the_data(self):
        backend = typed_backend()
        with vibecheck.batch("the ticket", backend=backend) as b:
            team = b.classify("Which team?", ["returns", "billing"])
            urgent = b.check("Is this urgent?")
            tone = b.score("How frustrated?", ["calm", "annoyed", "angry"])
        assert len(backend.calls) == 1
        assert backend.calls[0].state == "the ticket"
        assert (team.result(), urgent.result()) == ("billing", True)
        assert tone.result() == pytest.approx(1.6)

    def test_each_question_keeps_its_own_instructions(self):
        backend = typed_backend()
        with vibecheck.batch("x", backend=backend) as b:
            b.check("First?")
            b.check("Second?")
        questions = backend.calls[0].questions
        assert [q.instructions for q in questions.values()] == ["First?", "Second?"]

    async def test_async(self):
        backend = typed_backend()
        async with vibecheck.batch("x", backend=backend) as b:
            urgent = b.check("Is this urgent?", probabilities=True)
            tags = b.label("Topics?", ["a", "b"])
        assert urgent.result() == Decision(True, 0.9)
        assert tags.result() == ["a", "b"]
        assert len(backend.calls) == 1

    def test_assess_in_a_batch(self):
        backend = typed_backend()
        with vibecheck.batch("x", backend=backend) as b:
            triage = b.assess("Triage", TriageDataclass)
            angry = b.check("Is the customer angry?")
        assert triage.result().team == "billing"
        assert angry.result() is True
        assert len(backend.calls) == 1

    def test_reading_early_raises(self):
        with vibecheck.batch("x", backend=typed_backend()) as b:
            urgent = b.check("q?")
            with pytest.raises(RuntimeError, match="isn't ready"):
                urgent.result()

    def test_using_a_deferred_as_a_condition_raises(self):
        with vibecheck.batch("x", backend=typed_backend()) as b:
            urgent = b.check("q?")
            with pytest.raises(TypeError, match=r"\.result\(\)"):
                bool(urgent)

    def test_error_in_block_sends_nothing(self):
        backend = typed_backend()
        with (
            pytest.raises(ZeroDivisionError),
            vibecheck.batch("x", backend=backend) as b,
        ):
            b.check("q?")
            raise ZeroDivisionError
        assert backend.calls == []

    def test_empty_batch_sends_nothing(self):
        backend = typed_backend()
        with vibecheck.batch("x", backend=backend):
            pass
        assert backend.calls == []

    def test_cannot_add_after_sending(self):
        with vibecheck.batch("x", backend=typed_backend()) as b:
            b.check("q?")
        with pytest.raises(RuntimeError, match="already been sent"):
            b.check("another?")


class TestAsync:
    async def test_verbs_are_awaitable(self):
        backend = typed_backend()
        assert await vibecheck.check("q?", "x", backend=backend) is True
        assert await vibecheck.classify("q?", ["a", "b"], "x", backend=backend) == "b"
        assert await vibecheck.label("q?", ["a", "b"], "x", backend=backend) == [
            "a",
            "b",
        ]
        assert await vibecheck.score(
            "q?", ["l", "m", "h"], "x", backend=backend
        ) == pytest.approx(1.6)
        assert (
            await vibecheck.assess("q", TriageDataclass, "x", backend=backend)
        ).team == "billing"

    async def test_filter_and_group(self):
        assert await vibecheck.filter(
            "Refund?", ["refund", "hi"], backend=refund_backend()
        ) == ["refund"]
        groups = await vibecheck.group(
            "q?", ["a", "b"], ["x"], backend=always(pick(a=0.9, b=0.1))
        )
        assert groups == {"a": ["x"], "b": []}

    async def test_gather(self):
        backend = typed_backend()
        a, b = await asyncio.gather(
            vibecheck.check("q?", "x", backend=backend),
            vibecheck.check("q?", "y", backend=backend),
        )
        assert (a, b) == (True, True)

    def test_asyncio_run(self):
        assert asyncio.run(vibecheck.check("q?", "x", backend=typed_backend())) is True

    async def test_create_task(self):
        task = asyncio.create_task(vibecheck.check("q?", "x", backend=typed_backend()))
        assert await task is True

    def test_forgetting_await_raises(self):
        with pytest.raises(TypeError, match="must be awaited"):
            if vibecheck.check("Urgent?", "x", backend=typed_backend()):
                pass
