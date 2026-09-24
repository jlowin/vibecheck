"""Leave the data out when the question stands on its own."""

from vibecheck.sync import check

questions = [
    "Is Paris the capital of France?",
    "Is a tomato a vegetable, botanically speaking?",
    "Is Python a compiled language?",
]

for question in questions:
    print(f"{question}\n  → {check(question)}\n")
