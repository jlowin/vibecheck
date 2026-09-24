"""`assess` fills a class with answers, one question per field, in one request.

Run it with `uv run examples/assess.py` after setting `TYPESAFE_API_KEY`.
"""

from dataclasses import asdict, dataclass
from typing import Annotated, Literal

from pydantic import BaseModel

from vibecheck.sync import assess


@dataclass
class Triage:
    team: Literal["returns", "shipping", "billing"]
    urgent: Annotated[bool, "Does this need a reply today?"]
    frustration: Annotated[
        float, "How frustrated is the customer?", ["calm", "annoyed", "angry"]
    ]
    topics: list[Literal["refund", "delivery", "account"]]


tickets = [
    "I was charged twice for order A-104 and nobody has answered my emails. Refund the duplicate NOW.",
    "Hi! My package seems to be stuck in Memphis. No rush, just curious when it'll arrive.",
]

print("A dataclass: each field's type decides which kind of question it asks")
for ticket in tickets:
    triage = assess("Triage this support ticket", Triage, ticket)
    print(f"  {ticket!r}")
    for name, value in asdict(triage).items():
        print(f"    {name:<12} {value}")
print()


class Review(BaseModel):
    recommends: Annotated[bool, "Would the reviewer recommend this product?"]
    stars: Annotated[int, "How many stars would this review give?", range(1, 6)]
    mentions: Annotated[
        list[str],
        "Which aspects does the review mention?",
        ["price", "quality", "shipping", "support"],
    ]


review = "Great quality for the price. Took three weeks to arrive, though."

print("A Pydantic model works the same way")
print(f"  {review!r}")
result = assess("Analyze this product review", Review, review)
for name, value in result.model_dump().items():
    print(f"    {name:<12} {value}")
