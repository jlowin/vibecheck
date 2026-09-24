"""Leave the data out when the question stands on its own."""

from vibecheck.sync import classify

things = {
    "Harry Potter": ["book series", "person", "city"],
    "Mercury": ["planet", "element", "Roman god"],
}

for thing, options in things.items():
    kind = classify(f"What is {thing} most commonly known as?", options)
    print(f"{thing}\n  → {kind}\n")
