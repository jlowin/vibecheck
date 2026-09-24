"""Pick every option that applies.

`label` is the multi-answer sibling of `classify`. Where `classify` forces one choice,
`label` judges each option on its own and returns every option that applies, most likely
first. That's the right shape for tags and topics, where an article can cover several
subjects on your list, or none of them.

Because each option gets its own yes/no judgment, an empty list is a real answer:
nothing on the list applies.

This script tags three articles. The business story gets three topics, the baseball game
gets two (sports, and weather for the rain delay), and the bakery anniversary gets none.

Run it with `uv run examples/label/basic.py` after setting `TYPESAFE_API_KEY`.
"""

from vibecheck.sync import label

topics = ["pricing", "security", "layoffs", "sports", "weather"]
articles = [
    "Acme raised prices 15%, disclosed a data breach, and announced layoffs.",
    "The Tigers won in extra innings after a rain delay of nearly two hours.",
    "A local bakery is celebrating its 50th anniversary this weekend.",
]

for article in articles:
    found = label("Which topics does this article cover?", topics, article)
    print(f"{article!r}\n  → {found}\n")
