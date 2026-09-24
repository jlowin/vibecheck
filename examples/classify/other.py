"""Give classify a way out.

`classify` always returns one of your options, even when none of them fits. Route a
thank-you note with only "returns", "shipping", and "billing" and it still lands on one
of those teams, because the model has to pick something. When your options might not
cover every case, add a catch-all such as "other". It gives the model an honest answer
for the cases your list didn't anticipate, and gives your code one place to handle them.

This script routes three messages. The double charge goes to billing, while the thank-
you note and the job inquiry both go to other.

Run it with `uv run examples/classify/other.py` after setting `TYPESAFE_API_KEY`.
"""

from vibecheck.sync import classify

tickets = [
    "I was charged twice for order A-104.",
    "Love the new design, thanks!",
    "Do you have any openings for a warehouse job?",
]

for ticket in tickets:
    team = classify(
        "Which team should handle this?",
        ["returns", "shipping", "billing", "other"],
        ticket,
    )
    print(f"{ticket!r}\n  → {team}\n")
