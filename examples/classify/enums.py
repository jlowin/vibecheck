"""An Enum class works as a list of options, and you get a member back."""

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
