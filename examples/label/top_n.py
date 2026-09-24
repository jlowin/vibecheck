"""threshold and limit control how many labels come back.

An option makes the list when its probability is at least `threshold` (0.5 by default), and `limit`
caps the list. With threshold=0 and limit=2 you always get the two most likely options.
"""

from vibecheck.sync import label

topics = ["pricing", "security", "layoffs", "sports", "weather"]
articles = [
    "Acme raised prices 15%, disclosed a data breach, and announced layoffs.",
    "A local bakery is celebrating its 50th anniversary this weekend.",
]

for article in articles:
    top_two = label(
        "Which topics does this article cover?", topics, article, threshold=0, limit=2
    )
    print(f"{article!r}\n  → {top_two}\n")
