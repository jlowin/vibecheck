import json
from typing import Any

import httpx2
from typesafe_sdk import AsyncTypeSafeClient, RetryPolicy, TypeSafeClient

import vibecheck
from vibecheck import TypeSafeBackend, sync
from vibecheck._questions import Pick, PickAnswer, Rate, RateAnswer, YesNo, YesNoAnswer

QUESTIONS = {
    "refund": YesNo(instructions="Refund?"),
    "team": Pick(instructions="Team?", options={"billing": "Charges", "returns": None}),
    "urgency": Rate(instructions="How urgent?", levels=["low", "high"]),
}

RESPONSE: dict[str, Any] = {
    "model": "jev-1.13.0",
    "answers": {
        "refund": {"type": "noul", "noul": 0.9},
        "team": {
            "type": "choice",
            "choice": "billing",
            "confidence": 0.8,
            "probabilities": {"billing": 0.9, "returns": 0.1},
        },
        "urgency": {
            "type": "score",
            "score": 0.75,
            "confidence": 0.5,
            "legend": {"0": "low", "1": "high"},
            "probabilities": {"1": 0.75, "0": 0.25},
        },
    },
    "usage": {"input_tokens": 10, "output_tokens": 3},
}


def single(answer: dict) -> dict:
    return {**RESPONSE, "answers": {"answer": answer}}


def handler(requests: list[dict], response: dict):
    def handle(request: httpx2.Request) -> httpx2.Response:
        requests.append(json.loads(request.content))
        return httpx2.Response(200, json=response)

    return handle


def sync_backend(requests: list[dict], response: dict = RESPONSE) -> TypeSafeBackend:
    client = TypeSafeClient(
        api_key="test-key",
        base_url="https://decisions.test",
        transport=httpx2.MockTransport(handler(requests, response)),
        retry=RetryPolicy(max_retries=0),
    )
    return TypeSafeBackend(client=client)


def test_request_uses_typesafe_wire_format():
    requests: list[dict] = []
    sync_backend(requests).evaluate({"ticket": "hi"}, QUESTIONS, model="jev-latest")
    assert requests == [
        {
            "model": "jev-latest",
            "state": {"ticket": "hi"},
            "questions": {
                "refund": {"type": "noul", "instructions": "Refund?"},
                "team": {
                    "type": "choice",
                    "instructions": "Team?",
                    "criteria": {"billing": "Charges", "returns": None},
                },
                "urgency": {
                    "type": "score",
                    "instructions": "How urgent?",
                    "criteria": ["low", "high"],
                },
            },
        }
    ]


def test_answers_are_translated_back():
    answers = sync_backend([]).evaluate("hi", QUESTIONS)
    assert answers == {
        "refund": YesNoAnswer(probability=0.9),
        "team": PickAnswer(probabilities={"billing": 0.9, "returns": 0.1}),
        "urgency": RateAnswer(probabilities=[0.25, 0.75]),
    }


def test_end_to_end_through_the_sdk():
    requests: list[dict] = []
    backend = sync_backend(requests, single(RESPONSE["answers"]["urgency"]))
    result = sync.score("How urgent?", ["low", "high"], "hi", backend=backend)
    assert result == 0.75
    assert requests[0]["questions"]["answer"]["type"] == "score"


async def test_async_backend():
    requests: list[dict] = []
    client = AsyncTypeSafeClient(
        api_key="test-key",
        base_url="https://decisions.test",
        transport=httpx2.MockTransport(
            handler(requests, single({"type": "noul", "noul": 0.2}))
        ),
        retry=RetryPolicy(max_retries=0),
    )
    backend = TypeSafeBackend(async_client=client)
    result = await vibecheck.check("Refund?", "hi", backend=backend)
    assert result is False
    assert len(requests) == 1
