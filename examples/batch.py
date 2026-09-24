"""`vibecheck.batch` asks many questions about the same data in one request.

Run it with `uv run examples/batch.py` after setting `TYPESAFE_API_KEY`.
"""

import asyncio

import vibecheck

ticket = (
    "I was charged twice and nobody has answered my last two emails. "
    "Fix this or I'm cancelling."
)

print("A batch sends every question as a single request when the block ends")
print(f"  {ticket!r}")
with vibecheck.batch(ticket) as b:
    team = b.classify(
        "Which team should handle this?", ["returns", "shipping", "billing"]
    )
    cancelling = b.check("Is the customer threatening to cancel?")
    urgency = b.score("How urgent is this?", range(1, 6))
    topics = b.label(
        "Which topics come up?", ["refund", "delivery", "account", "support"]
    )

print(f"    team        {team.result()}")
print(f"    cancelling  {cancelling.result()}")
print(f"    urgency     {urgency.result():.1f} / 5")
print(f"    topics      {topics.result()}")
print()


async def main() -> None:
    print("Batches work with async with, too")
    async with vibecheck.batch(ticket) as b:
        angry = b.check("Is the customer angry?", probabilities=True)
        polite = b.check("Is the customer polite?", probabilities=True)
    for name, answer in [("angry", angry), ("polite", polite)]:
        value, p = answer.result()
        print(f"    {name:<11} {value} (p = {p:.2f})")


asyncio.run(main())
