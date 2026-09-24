"""A (low, high) threshold returns None when the model is unsure.

At or above 0.9 is True, below 0.3 is False, and anything in between is None.
Use `match` rather than `if`, because None is falsy.
"""

from vibecheck.sync import check

alerts = [
    "Checkout is down for every customer; all requests return 500.",
    "Error rate on checkout spiked to 40% in the last five minutes.",
    "The export button crashes settings in Safari. Chrome works fine.",
]

for alert in alerts:
    match check("Is this a production outage?", alert, threshold=(0.3, 0.9)):
        case True:
            action = "page on-call"
        case False:
            action = "archive"
        case None:
            action = "send to a person"
    print(f"{alert!r}\n  → {action}\n")
