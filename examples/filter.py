"""`vibecheck.filter` keeps the items where a yes/no question is answered yes.

Each item gets its own request, and the requests run concurrently.

Run it with `uv run examples/filter.py` after setting `TYPESAFE_API_KEY`.
"""

from vibecheck import sync

tickets = [
    "Refund my duplicate charge, please.",
    "Where is my package? It's a week late.",
    "I want my money back for this broken lamp.",
    "Love the new design, thanks!",
    "Can I get store credit instead of the replacement?",
]

print("filter keeps the matching items, in their original order")
refunds = sync.filter("Is the customer asking for their money back?", tickets)
for ticket in refunds:
    print(f"  {ticket!r}")
print()

print("A lower threshold casts a wider net")
refunds = sync.filter(
    "Is the customer asking for their money back?", tickets, threshold=0.1
)
for ticket in refunds:
    print(f"  {ticket!r}")
print()

print("probabilities=True also returns every item's probability of yes")
refunds, probabilities = sync.filter(
    "Is the customer asking for their money back?",
    tickets,
    probabilities=True,
)
for ticket, p in zip(tickets, probabilities, strict=True):
    kept = "✓" if ticket in refunds else " "
    print(f"  {kept} {p:.2f}  {ticket!r}")
