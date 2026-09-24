"""`label` returns every option that applies, most likely first.

Run it with `uv run examples/label.py` after setting `TYPESAFE_API_KEY`.
"""

from vibecheck.sync import label

topics = ["pricing", "security", "layoffs", "sports", "weather"]
articles = [
    "Acme raised prices 15%, disclosed a data breach, and announced layoffs.",
    "The Tigers won in extra innings after a rain delay of nearly two hours.",
    "A local bakery is celebrating its 50th anniversary this weekend.",
]

print("Each option is judged on its own, so zero, one, or many can apply")
for article in articles:
    found = label("Which topics does this article cover?", topics, article)
    print(f"  {article!r}")
    print(f"    → {found}")
print()

print("threshold=0 with limit=2 returns the two most likely options, however unlikely")
for article in articles:
    top_two = label(
        "Which topics does this article cover?", topics, article, threshold=0, limit=2
    )
    print(f"  {article!r}")
    print(f"    → {top_two}")
print()

print("probabilities=True returns the labels and every option's probability")
found, probabilities = label(
    "Which topics does this article cover?",
    topics,
    articles[0],
    probabilities=True,
)
print(f"  {articles[0]!r}")
print(f"    → {found}")
for option, p in probabilities.items():
    print(f"      {option:<10} {'█' * round(p * 30):<30} {p:.2f}")
