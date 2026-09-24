"""classify picks exactly one of your options and returns it."""

from vibecheck.sync import classify

tickets = [
    "My running shoes arrived in the wrong size. Can I swap them for a 10?",
    "I was charged twice for order A-104.",
    "Tracking says delivered but there's nothing on my porch.",
]

for ticket in tickets:
    team = classify(
        "Which team should handle this?", ["returns", "shipping", "billing"], ticket
    )
    print(f"{ticket!r}\n  → {team}\n")
