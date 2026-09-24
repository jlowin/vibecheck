"""Raise the threshold when a false yes is expensive.

By default, `check` returns `True` when the probability of yes is at least 0.5, which
suits most decisions. Some decisions cost more when they're wrong in one direction:
paging someone at 3 a.m. for something that isn't an outage burns trust fast, so you
want a yes only when the model is sure. `threshold=0.9` means `check` returns `True`
only when the probability of yes is at least 0.9.

The threshold changes only your decision. The model sees the same question and returns
the same probability either way; you're choosing how much evidence your code needs
before it acts.

This script runs three alerts through the same question. A full checkout outage clears
the 0.9 bar. A 40% error spike looks like an outage without being certain, so it falls
short here even though it would pass at 0.5. A Safari-only bug is clearly not an outage.

Run it with `uv run examples/check/threshold.py` after setting `TYPESAFE_API_KEY`.
"""

from vibecheck.sync import check

alerts = [
    "Checkout is down for every customer; all requests return 500.",
    "Error rate on checkout spiked to 40% in the last five minutes.",
    "The export button crashes settings in Safari. Chrome works fine.",
]

for alert in alerts:
    page = check("Is this a production outage?", alert, threshold=0.9)
    print(f"{alert!r}\n  page on-call? {page}\n")
