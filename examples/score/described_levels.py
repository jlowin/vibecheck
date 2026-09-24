"""Score in your own units, with a description for each level.

A dict of number to description combines both approaches: your units, and words that
tell the model what each number means. You don't have to describe every number.
Anchoring a few points, such as the two ends and the middle, is enough for the model to
place an answer anywhere on the scale.

Decision models read questions literally, so these anchors usually improve the answer.
Here, "3: Mixed" shows the model what a middling review looks like.

This script rates the same three reviews as `numeric_levels.py`. The ends don't move,
but the mixed review now scores 3, the level described as mixed, instead of the lower
score it got from bare numbers.

Run it with `uv run examples/score/described_levels.py` after setting `TYPESAFE_API_KEY`.
"""

from vibecheck.sync import score

levels = {1: "Angry; wants a refund", 3: "Mixed", 5: "Delighted; would recommend"}
reviews = [
    "Solid product, arrived late, support was slow to respond.",
    "Absolutely love it. Bought a second one for my sister.",
    "Broke after two days. I want a refund.",
]

for review in reviews:
    stars = score("How satisfied is this customer?", levels, review)
    print(f"{review!r}\n  → {stars:.1f} stars\n")
