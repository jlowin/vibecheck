"""score rates data on ordered levels, lowest first, and returns a position on the scale.

A list of level descriptions is numbered from 0. The position is the probability-weighted average
of the levels, so it can land between two of them.
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
