"""Classify without any data.

Like every vibecheck function, `classify` treats the data as optional. When the question
stands on its own, leave the data out and the model answers from general knowledge. The
options still constrain the answer, so you always get one of them back.

Put everything the model needs into the question. Here the subject is part of the
question itself, and the phrase "most commonly known as" tells the model which meaning
to prefer.

This script classifies two ambiguous names. Harry Potter could be a book series or a
person, and Mercury could be a planet, an element, or a god. The model picks the
everyday meanings: book series and planet.

Run it with `uv run examples/classify/no_data.py` after setting `TYPESAFE_API_KEY`.
"""

from vibecheck.sync import classify

things = {
    "Harry Potter": ["book series", "person", "city"],
    "Mercury": ["planet", "element", "Roman god"],
}

for thing, options in things.items():
    kind = classify(f"What is {thing} most commonly known as?", options)
    print(f"{thing}\n  → {kind}\n")
