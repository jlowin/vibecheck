"""Get the probability behind a yes/no answer.

Every answer from a decision model starts as a probability. `check` normally turns it
into a bool for you; pass `probabilities=True` and you get both. The result is a
`Decision` pair of the answer, exactly as you'd get it without the flag, and the
probability of yes as a float.

Reach for the number when the decision alone isn't enough: to log how close your cases
run to the threshold, to sort by it, or to tune the threshold against real data.
Decision models such as Jev are trained to be calibrated, so a probability of 0.8 should
mean yes about four times out of five.

This script asks whether three customers are angry. The furious one comes back near 1
and the neutral question near 0. The mildly annoyed customer lands low but clearly above
zero, the kind of nuance a bare bool throws away.

Run it with `uv run examples/check/probabilities.py` after setting `TYPESAFE_API_KEY`.
"""

from vibecheck.sync import check

messages = [
    "This is the third time I've been charged twice. Unbelievable.",
    "Quick question: do you ship to Canada?",
    "Not thrilled the package was late, but it's fine.",
]

for message in messages:
    angry, p = check("Is the customer angry?", message, probabilities=True)
    print(f"{message!r}\n  → {angry}  (p = {p:.2f})\n")
