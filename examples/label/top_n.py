"""Control how many labels come back.

Two arguments shape the list `label` returns. An option makes the list when its
probability of applying is at least `threshold`, which defaults to 0.5, and `limit` caps
the list's length, keeping the most likely options.

Combine them to always get a fixed number of labels. With `threshold=0` every option
qualifies, and `limit=2` keeps the two most likely. That suits a UI with a fixed number
of tag slots. It also always fills those slots, even when nothing fits well.

This script asks for the top two topics for two articles. The business story returns two
of its three real topics. The bakery story, which matched nothing in `basic.py`, still
returns two labels: the least unlikely options, rather than good ones.

Run it with `uv run examples/label/top_n.py` after setting `TYPESAFE_API_KEY`.
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
