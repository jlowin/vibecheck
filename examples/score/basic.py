"""Rate data on an ordered scale.

`score` answers "where on this scale?" You pass levels ordered from lowest to highest
and get back a float position on that scale. A list of level descriptions is numbered
from 0, so three levels make a scale from 0 to 2.

The position is the probability-weighted average of the levels, so it can land between
two of them. A score of 1.2 means the model is split between levels 1 and 2 and leans
toward 1. Compare it against a cutoff the way you would any other number.

The model treats the levels as an ordered scale, so always list them from lowest to
highest.

This script rates three bugs for severity. The misaligned logo scores 0 and the total
login outage scores 2. The Safari crash has a workaround, since Chrome works, but the
model leans a little toward blocking, so it lands just above 1.

Run it with `uv run examples/score/basic.py` after setting `TYPESAFE_API_KEY`.
"""

from vibecheck.sync import score

levels = [
    "Cosmetic; no impact on functionality",
    "Broken, but a workaround exists",
    "Blocking; no workaround",
]
bugs = [
    "The logo is two pixels off-center on the pricing page.",
    "The export button crashes settings in Safari. Chrome works fine.",
    "Nobody can log in. The auth service returns 500 for every request.",
]

for bug in bugs:
    severity = score("How severe is this bug?", levels, bug)
    print(f"{bug!r}\n  → {severity:.2f}\n")
