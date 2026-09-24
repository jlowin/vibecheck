"""Give classify a way out when your options might not cover every case.

classify always picks one of your options, so without "other" an off-topic ticket would still land
on a team.
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
