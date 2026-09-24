"""`vibecheck.group` classifies each item and returns a dict of option to items.

Each item gets its own request, and the requests run concurrently.

Run it with `uv run examples/group.py` after setting `TYPESAFE_API_KEY`.
"""

from vibecheck import sync

tickets = [
    "Refund my duplicate charge, please.",
    "Where is my package? It's a week late.",
    "Love the new design, thanks!",
    "The box was crushed and the mug inside is broken.",
    "Why was I billed for a plan I cancelled?",
]

print("Every option appears as a key, even when no item landed there")
by_team = sync.group(
    "Which team should handle this?",
    ["returns", "shipping", "billing", "legal", "other"],
    tickets,
)
for team, items in by_team.items():
    print(f"  {team}")
    for ticket in items:
        print(f"    {ticket!r}")
    if not items:
        print("    (none)")
print()

print("probabilities=True also returns each item's distribution over the options")
by_team, distributions = sync.group(
    "Which team should handle this?",
    ["returns", "shipping", "billing", "other"],
    tickets,
    probabilities=True,
)
for ticket, distribution in zip(tickets, distributions, strict=True):
    best = max(distribution, key=distribution.__getitem__)
    print(f"  {best:<9} {distribution[best]:.2f}  {ticket!r}")
