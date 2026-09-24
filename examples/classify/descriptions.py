"""A dict of options describes when each one applies.

The model reads the descriptions, which makes them the place to settle edge cases. Here, refunds
go to billing even when they involve a returned item.
"""

from vibecheck.sync import classify

teams = {
    "returns": "Exchanges, and wrong or damaged items",
    "shipping": "Delivery status, delays, and lost packages",
    "billing": "Charges, invoices, and every refund, including refunds for returned items",
}

tickets = [
    "My running shoes arrived in the wrong size. Can I swap them for a 10?",
    "I sent the lamp back two weeks ago. Where's my refund?",
    "Tracking says delivered but there's nothing on my porch.",
]

for ticket in tickets:
    team = classify("Which team should handle this?", teams, ticket)
    print(f"{ticket!r}\n  → {team}\n")
