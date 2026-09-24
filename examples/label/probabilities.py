"""probabilities=True returns the labels and every option's probability.

Each option is judged on its own, so the probabilities don't sum to 1.
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
