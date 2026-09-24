"""label returns every option that applies, most likely first.

Each option is judged on its own, so zero, one, or many can apply.
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
