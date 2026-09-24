"""Choose a function, then call it.

Options can be any object. vibecheck gives each one a text label for the model and hands
back the original object as the answer. When the options are functions, the answer is a
function you can call, so `classify` becomes dispatch: the model picks the handler and
your code runs it.

The model reads each function's name, its full signature, and its whole docstring. Write
the docstring the way you'd tell a colleague when that function is the right one to
call, because that explanation is what the model uses to choose. Include a catch-all
like `escalate` so a ticket that fits nothing has somewhere sensible to go.

This script sends three tickets through three handlers. The locked-out customer gets
`reset_password`, the duplicate charge gets `refund`, and the complaint about the CEO
fits neither, so it goes to `escalate`.

Run it with `uv run examples/classify/functions.py` after setting `TYPESAFE_API_KEY`.
"""

from vibecheck.sync import classify


def refund(ticket: str) -> str:
    """Customer wants money back for a charge or order.

    Covers duplicate charges, cancelled orders, and items returned for a refund. If the
    customer wants a replacement rather than their money, this is the wrong handler.
    """
    return "Refunding"


def reset_password(ticket: str) -> str:
    """Customer is locked out or can't sign in.

    Covers forgotten passwords, expired reset links, and accounts locked after too many
    attempts. A customer who can sign in but wants to change their email is not locked
    out.
    """
    return "Sending a reset link"


def escalate(ticket: str) -> str:
    """Anything else, or anything that needs a human.

    Use this for complaints, legal threats, press inquiries, and any ticket the other
    handlers don't clearly cover. When in doubt, escalate.
    """
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
