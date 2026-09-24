"""A dict of number to description gives your own units and tells the model what they mean.

Decision models read questions literally, so described levels give better answers than bare numbers.
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
