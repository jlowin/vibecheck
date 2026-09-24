"""A yes/no question returns a bool."""

from vibecheck.sync import check

messages = [
    "I've asked three times now. Can I please talk to a real person?",
    "Thanks, that fixed it!",
]

for message in messages:
    wants_human = check("Is the customer asking for a human?", message)
    print(f"{message!r}\n  → {wants_human}\n")
