"""`score` rates data on ordered levels and returns a position on that scale.

Run it with `uv run examples/score.py` after setting `TYPESAFE_API_KEY`.
"""

from vibecheck.sync import score

bugs = [
    "The logo is two pixels off-center on the pricing page.",
    "The export button crashes settings in Safari. Chrome works fine.",
    "Nobody can log in. The auth service returns 500 for every request.",
]
reviews = [
    "Solid product, arrived late, support was slow to respond.",
    "Absolutely love it. Bought a second one for my sister.",
    "Broke after two days. I want a refund.",
]

print("A list of level descriptions is numbered from 0")
severity_levels = [
    "Cosmetic; no impact on functionality",
    "Broken, but a workaround exists",
    "Blocking; no workaround",
]
for bug in bugs:
    severity = score("How severe is this bug?", severity_levels, bug)
    print(f"  {bug!r}")
    print(f"    → {severity:.2f}")
print()

print("A range gives the answer in your own units")
for review in reviews:
    stars = score("How satisfied is this customer?", range(1, 6), review)
    print(f"  {review!r}")
    print(f"    → {stars:.1f} stars")
print()

print("A dict of number to description does both")
described = {1: "Angry; wants a refund", 3: "Mixed", 5: "Delighted; would recommend"}
for review in reviews:
    stars = score("How satisfied is this customer?", described, review)
    print(f"  {review!r}")
    print(f"    → {stars:.1f} stars")
print()

print("probabilities=True returns the position and every level's probability")
severity, probabilities = score(
    "How severe is this bug?",
    severity_levels,
    bugs[1],
    probabilities=True,
)
print(f"  {bugs[1]!r}")
print(f"    → {severity:.2f}")
for level, p in probabilities.items():
    print(f"      {level}  {'█' * round(p * 30):<30} {p:.2f}")
