"""probabilities=True returns the answer and every option's probability.

The probabilities sum to 1. When the top two are close, the case is ambiguous and a person should look.
"""

from vibecheck.sync import classify

tickets = [
    "I was charged twice for order A-104.",
    "Wrong size arrived, and I still haven't seen the refund for my last return.",
]

for ticket in tickets:
    team, distribution = classify(
        "Which team should handle this?",
        ["returns", "shipping", "billing"],
        ticket,
        probabilities=True,
    )
    print(f"{ticket!r}\n  → {team}")
    for option, p in distribution.items():
        print(f"    {option:<10} {'█' * round(p * 30):<30} {p:.2f}")
    best, runner_up = sorted(distribution.values(), reverse=True)[:2]
    print(f"    margin over the runner-up: {best - runner_up:.2f}\n")
