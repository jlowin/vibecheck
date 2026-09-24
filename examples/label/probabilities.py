"""See the probability of each label.

Pass `probabilities=True` and `label` returns a `Decision` pair: the labels, and a dict
of every option and its probability. Each option is judged independently, so the
probabilities don't sum to 1. Several options can be near 1 at once, and all of them can
be near 0.

This is how you tune `threshold` for your data. Look at the probabilities for a few real
examples, then set the threshold between the options you want and the ones you don't.

This script tags one article. Pricing and security are stated outright and score high.
Layoffs is only implied by "analysts expect cuts", so it lands lower, and sports and
weather sit near zero.

Run it with `uv run examples/label/probabilities.py` after setting `TYPESAFE_API_KEY`.
"""

from vibecheck.sync import label

topics = ["pricing", "security", "layoffs", "sports", "weather"]
article = "Acme raised prices 15% and disclosed a data breach. Analysts expect cuts."

found, probabilities = label(
    "Which topics does this article cover?", topics, article, probabilities=True
)
print(f"{article!r}\n  → {found}")
for option, p in probabilities.items():
    print(f"    {option:<10} {'█' * round(p * 30):<30} {p:.2f}")
