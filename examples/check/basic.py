"""Ask a yes/no question and get a bool.

`check` is the simplest decision in vibecheck. You ask a question about some data, the
model answers with the probability that the answer is yes, and `check` turns that
probability into `True` or `False`. The result drops straight into an `if` statement.

Write the question the way you'd ask a colleague glancing at the data. Decision models
read questions literally, so "Is the customer asking for a human?" works better than a
terse label like "escalation?".

This script checks two support messages. The first asks for a person and the second says
thanks, so you'll see `True` and then `False`.

Run it with `uv run examples/check/basic.py` after setting `TYPESAFE_API_KEY`.
"""

from vibecheck.sync import check

messages = [
    "I've asked three times now. Can I please talk to a real person?",
    "Thanks, that fixed it!",
]

for message in messages:
    wants_human = check("Is the customer asking for a human?", message)
    print(f"{message!r}\n  → {wants_human}\n")
