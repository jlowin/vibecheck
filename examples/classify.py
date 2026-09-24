"""`classify` picks exactly one of your options and returns it.

Run it with `uv run examples/classify.py` after setting `TYPESAFE_API_KEY`.
"""

from enum import Enum

from vibecheck.sync import classify

tickets = [
    "My running shoes arrived in the wrong size. Can I swap them for a 10?",
    "I was charged twice for order A-104.",
    "Tracking says delivered but there's nothing on my porch.",
]

print("Options can be plain strings")
for ticket in tickets:
    team = classify(
        "Which team should handle this?", ["returns", "shipping", "billing"], ticket
    )
    print(f"  {ticket!r}")
    print(f"    → {team}")
print()

print("A dict describes when each option applies")
teams = {
    "returns": "Exchanges, wrong or damaged items",
    "shipping": "Delivery status, delays, lost packages",
    "billing": "Charges, invoices, refunds, payment problems",
}
for ticket in tickets:
    print(f"  {ticket!r}")
    print(f"    → {classify('Which team should handle this?', teams, ticket)}")
print()


def refund(ticket: str) -> str:
    """Customer wants money back for a charge or order."""
    return "Refunding"


def reset_password(ticket: str) -> str:
    """Customer is locked out or can't sign in."""
    return "Sending a reset link"


def escalate(ticket: str) -> str:
    """Anything else, or anything that needs a human."""
    return "Escalating"


print("Options can be functions, so you can call the one the model picks")
for ticket in [
    "I can't log in and I've tried the reset link twice.",
    "Please refund my duplicate charge.",
    "Your CEO should be ashamed of this company.",
]:
    handler = classify(
        "How should we handle this ticket?", [refund, reset_password, escalate], ticket
    )
    print(f"  {ticket!r}")
    print(f"    → {handler.__name__}(): {handler(ticket)}")
print()


class Sentiment(Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


print("An Enum class works as a list of options, and you get a member back")
mood = classify(
    "What is the tone of this review?", Sentiment, "Honestly? Fine. It works."
)
print(f"  'Honestly? Fine. It works.'  →  {mood}")
print()

print("probabilities=True returns the answer and every option's probability")
ticket = "Wrong size arrived, and I still haven't seen the refund for my last return."
team, distribution = classify(
    "Which team should handle this?",
    ["returns", "shipping", "billing"],
    ticket,
    probabilities=True,
)
print(f"  {ticket!r}")
print(f"    → {team}")
for option, p in distribution.items():
    print(f"      {option:<10} {'█' * round(p * 30):<30} {p:.2f}")
best, runner_up = sorted(distribution.values(), reverse=True)[:2]
verdict = "too close to call" if best - runner_up < 0.3 else "clear winner"
print(f"    Margin over the runner-up: {best - runner_up:.2f}, {verdict}")
print()

print("Leave the data out when the question stands on its own")
kind = classify("What is Harry Potter?", ["book series", "person", "city"])
print(f"  What is Harry Potter?  →  {kind}")
