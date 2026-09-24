"""See how confident the choice was.

Pass `probabilities=True` and `classify` returns a `Decision` pair: the chosen option,
and a dict of every option and its probability. The options are mutually exclusive, so
the probabilities sum to 1.

The distribution tells you what the answer alone can't. The most useful signal is the
margin between the top two options. A wide margin is a clear call; a narrow one means
the case sits between two categories, and it's often worth sending to a person.

This script classifies two tickets and draws each distribution as a bar chart. The
double charge goes to billing with nearly all the probability. The second ticket
mentions both a wrong size and a missing refund, and the margin line shows how clearly
the model still favors one team.

Run it with `uv run examples/classify/probabilities.py` after setting `TYPESAFE_API_KEY`.
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
