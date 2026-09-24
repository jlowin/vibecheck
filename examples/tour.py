"""A quick tour of vibecheck against a live decision model.

Run with `uv run python examples/tour.py`. It uses the TypeSafe SDK's environment variables:
`TYPESAFE_API_KEY`, and optionally `TYPESAFE_BASE_URL` and `TYPESAFE_DEFAULT_MODEL`.
"""

import asyncio
from dataclasses import dataclass
from typing import Annotated, Literal

import vibecheck
from vibecheck import assess, check, classify, filter, group, label, score, sync

TICKET = (
    "I was charged twice for order A-104 and nobody has answered my last two emails. "
    "Refund the duplicate NOW or I'm cancelling my subscription."
)
BUG = (
    "The export button crashes settings in Safari. It works in Chrome, "
    "but some customers only use Safari."
)
ARTICLE = (
    "Acme Corp announced a 15% price increase for its enterprise plan, citing rising cloud "
    "costs. The company also disclosed a data breach affecting 20,000 customer records and said "
    "it would lay off 8% of its workforce."
)
TICKETS = [
    "Refund my duplicate charge, please.",
    "Where is my package? It's a week late.",
    "I want my money back for this broken lamp.",
    "Love the new design, thanks!",
]


def refund(ticket: str) -> None:
    """Customer wants money back for a charge or order."""


def reset_password(ticket: str) -> None:
    """Customer is locked out or can't sign in."""


def escalate(ticket: str) -> None:
    """Anything else, or anything that needs a human."""


@dataclass
class Triage:
    team: Literal["returns", "shipping", "billing"]
    urgent: Annotated[bool, "Does this need a reply today?"]
    frustration: Annotated[
        float, "How frustrated is the customer?", ["calm", "annoyed", "angry"]
    ]


def show(label: str, value: object) -> None:
    print(f"{label:<22} {value!r}")


async def main() -> None:
    show("check", await check("Is the customer threatening to cancel?", TICKET))
    show(
        "check, three-way",
        await check("Is this a production outage?", BUG, threshold=(0.3, 0.9)),
    )
    show(
        "check, probabilities",
        await check("Is the customer angry?", TICKET, probabilities=True),
    )
    show(
        "classify",
        await classify(
            "Which team should handle this?", ["returns", "shipping", "billing"], TICKET
        ),
    )
    handler = await classify(
        "How should we handle this?", [refund, reset_password, escalate], TICKET
    )
    show("classify functions", handler.__name__)
    show(
        "label",
        await label(
            "Which topics does this article cover?",
            ["pricing", "security", "layoffs", "sports", "weather"],
            ARTICLE,
        ),
    )
    show(
        "label, probabilities",
        await label(
            "Which topics does this article cover?",
            ["pricing", "security", "layoffs", "sports", "weather"],
            ARTICLE,
            probabilities=True,
        ),
    )
    show(
        "score",
        await score(
            "How severe is this bug?",
            ["cosmetic", "broken, with a workaround", "blocking"],
            BUG,
        ),
    )
    show("score, range", await score("How urgent is this?", range(1, 6), TICKET))
    show(
        "no data",
        await classify("What is Harry Potter?", ["book series", "person", "city"]),
    )
    show("assess", await assess("Triage this support ticket", Triage, TICKET))
    show(
        "filter", await filter("Is the customer asking for their money back?", TICKETS)
    )
    show(
        "group",
        await group(
            "Which team should handle this?",
            ["returns", "shipping", "billing", "other"],
            TICKETS,
        ),
    )

    async with vibecheck.batch(TICKET) as b:
        team = b.classify(
            "Which team should handle this?", ["returns", "shipping", "billing"]
        )
        cancel = b.check("Is the customer threatening to cancel?")
        urgency = b.score("How urgent is this?", range(1, 6))
    show("batch", (team.result(), cancel.result(), urgency.result()))


if __name__ == "__main__":
    asyncio.run(main())
    show("sync", sync.check("Is the customer angry?", TICKET))
