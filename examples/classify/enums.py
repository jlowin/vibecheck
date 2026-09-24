"""Use an Enum as the list of options.

If your code already models the categories as an `Enum`, pass the class itself as the
options. The model sees each member's value as its label (or its name, when the value
isn't a string), and you get a member back, so the answer plugs straight into code that
already expects that type.

This script classifies the tone of three reviews into a `Sentiment` enum. You'll see
`Sentiment.POSITIVE`, `Sentiment.NEUTRAL`, and `Sentiment.NEGATIVE`.

Run it with `uv run examples/classify/enums.py` after setting `TYPESAFE_API_KEY`.
"""

from enum import Enum

from vibecheck.sync import classify


class Sentiment(Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


reviews = [
    "Absolutely love it. Bought a second one for my sister.",
    "Honestly? Fine. It works.",
    "Broke after two days.",
]

for review in reviews:
    mood = classify("What is the tone of this review?", Sentiment, review)
    print(f"{review!r}\n  → {mood}\n")
