"""Return None when the model is unsure, and let a person decide.

A single threshold forces every case into yes or no. Often the right behavior has three
outcomes: act on clear yeses, drop clear nos, and send the uncertain middle to a human.
Pass a `(low, high)` pair as the threshold and `check` does this for you. A probability
of `high` or more returns `True`, anything below `low` returns `False`, and anything in
between returns `None`.

Handle the result with `match` rather than `if`. `None` is falsy, so an `if` would
quietly treat "unsure" as "no", which hides exactly the cases you wanted a person to
see.

This script sends the alerts from `threshold.py` through a threshold of `(0.3, 0.9)`.
The full outage pages on-call, the Safari bug is archived, and the ambiguous error spike
goes to a person.

Run it with `uv run examples/check/three_way.py` after setting `TYPESAFE_API_KEY`.
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
