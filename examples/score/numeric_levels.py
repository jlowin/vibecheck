"""A range or a list of numbers gives the answer in your own units."""

from vibecheck.sync import score

reviews = [
    "Solid product, arrived late, support was slow to respond.",
    "Absolutely love it. Bought a second one for my sister.",
    "Broke after two days. I want a refund.",
]

for review in reviews:
    stars = score("How satisfied is this customer?", range(1, 6), review)
    print(f"{review!r}\n  → {stars:.1f} stars\n")
