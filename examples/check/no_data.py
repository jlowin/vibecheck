"""Ask a question that doesn't need any data.

The data argument is optional. When a question stands on its own, such as a fact about
the world, leave the data out and the model answers from what it already knows.

Keep these to common knowledge a sharp colleague would know offhand. Decision models
make quick judgments; they don't look anything up, and arithmetic, counting, and date
comparisons belong in your code.

This script asks three general-knowledge questions. Paris is the capital of France and
the Pacific is the largest ocean, so both come back `True`. A tomato is botanically a
fruit, so the vegetable question comes back `False`.

Run it with `uv run examples/check/no_data.py` after setting `TYPESAFE_API_KEY`.
"""

from vibecheck.sync import check

questions = [
    "Is Paris the capital of France?",
    "Is a tomato a vegetable, botanically speaking?",
    "Is the Pacific the largest ocean on Earth?",
]

for question in questions:
    print(f"{question}\n  → {check(question)}\n")
