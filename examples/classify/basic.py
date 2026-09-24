"""Pick exactly one option.

`classify` answers "which one of these?" You pass a question, a list of options, and the
data, and you get back the option the model thinks most likely. It always returns
exactly one, which makes it a natural fit for routing: which team, which queue, which
handler.

The model reads the option names, so they matter. Short, distinct names like "returns",
"shipping", and "billing" work well. When a name alone could be ambiguous, describe it,
as `descriptions.py` shows.

This script routes three support tickets. The wrong size goes to returns, the double
charge to billing, and the missing package to shipping.

Run it with `uv run examples/classify/basic.py` after setting `TYPESAFE_API_KEY`.
"""

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
