"""Score in your own units with a range of numbers.

When a scale already has natural numbers, such as a 1-to-5 star rating, pass them as the
levels. A `range` or a list of numbers works, and the result comes back in those units,
so a score over `range(1, 6)` is a float between 1 and 5.

Bare numbers give the model less to go on than descriptions, because it has to infer
what 2 stars means compared with 4. Compare this script's output with
`described_levels.py`, which scores the same reviews.

This script rates three reviews from 1 to 5. The delighted customer scores 5 and the
broken product scores 1. The mixed review lands around 2.

Run it with `uv run examples/score/numeric_levels.py` after setting `TYPESAFE_API_KEY`.
"""

from vibecheck.sync import score

reviews = [
    "Solid product, arrived late, support was slow to respond.",
    "Absolutely love it. Bought a second one for my sister.",
    "Broke after two days. I want a refund.",
]

for review in reviews:
    stars = score("How satisfied is this customer?", range(1, 6), review)
    print(f"{review!r}\n  → {stars:.1f} stars\n")
