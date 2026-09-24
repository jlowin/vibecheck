"""Describe each option to settle the edge cases.

Option names carry a lot of meaning, but they can't carry your team's rules. A refund
for a returned item could reasonably belong to returns or to billing, and the name alone
won't tell the model which one your company means. Pass a dict instead of a list: the
keys are the options, and the values describe when each one applies. The model reads
every description, and the answer is still one of the keys.

Descriptions are where your policy lives. When the model makes a call you disagree with,
the fix is usually a sharper description rather than a different question.

This script writes the rule "billing handles every refund" into the billing description.
The lamp refund therefore goes to billing even though it involves a returned item, while
the size exchange still goes to returns.

Run it with `uv run examples/classify/descriptions.py` after setting `TYPESAFE_API_KEY`.
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
