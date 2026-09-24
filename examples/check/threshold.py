"""A higher threshold means a yes has to be more certain.

`check` returns True when the probability of yes is at least `threshold`, which defaults to 0.5.
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
