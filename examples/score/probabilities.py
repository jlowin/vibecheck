"""probabilities=True returns the position and every level's probability."""

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
