"""Options can be functions, so you can call the one the model picks.

Each function's name is its label, and the model reads its full signature and docstring.
"""

from vibecheck.sync import classify


def refund(ticket: str) -> str:
    """Customer wants money back for a charge or order."""
    return "Refunding"


def reset_password(ticket: str) -> str:
    """Customer is locked out or can't sign in."""
    return "Sending a reset link"


def escalate(ticket: str) -> str:
    """Anything else, or anything that needs a human."""
    return "Escalating to a person"


tickets = [
    "I can't log in and I've tried the reset link twice.",
    "Please refund my duplicate charge.",
    "Your CEO should be ashamed of this company.",
]

for ticket in tickets:
    handler = classify(
        "How should we handle this ticket?", [refund, reset_password, escalate], ticket
    )
    print(f"{ticket!r}\n  → {handler.__name__}(): {handler(ticket)}\n")
