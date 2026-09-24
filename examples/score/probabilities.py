"""See the distribution behind a score.

Pass `probabilities=True` and `score` returns a `Decision` pair: the position, and a
dict of each level and its probability. The position is the weighted average of that
distribution.

The distribution shows what the average hides. A score of 1.0 could mean the model is
sure of level 1, or split evenly between levels 0 and 2, and only the distribution tells
those cases apart. A wide spread means the case is ambiguous.

This script scores the Safari bug from `basic.py` and draws each level's probability.
Most of the weight sits on "broken, but a workaround exists", with some on "blocking",
which is why the position lands just above 1.

Run it with `uv run examples/score/probabilities.py` after setting `TYPESAFE_API_KEY`.
"""

from vibecheck.sync import score

levels = [
    "Cosmetic; no impact on functionality",
    "Broken, but a workaround exists",
    "Blocking; no workaround",
]
bug = "The export button crashes settings in Safari. Chrome works fine."

severity, probabilities = score(
    "How severe is this bug?", levels, bug, probabilities=True
)
print(f"{bug!r}\n  → {severity:.2f}")
for level, p in probabilities.items():
    print(f"    {level}  {levels[int(level)]:<38} {'█' * round(p * 30):<30} {p:.2f}")
