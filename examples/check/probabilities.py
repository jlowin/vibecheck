"""probabilities=True returns the answer and the probability of yes."""

from vibecheck.sync import check

messages = [
    "This is the third time I've been charged twice. Unbelievable.",
    "Quick question: do you ship to Canada?",
    "Not thrilled the package was late, but it's fine.",
]

for message in messages:
    angry, p = check("Is the customer angry?", message, probabilities=True)
    print(f"{message!r}\n  → {angry}  (p = {p:.2f})\n")
