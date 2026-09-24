"""`check` asks a yes/no question and returns a bool.

Run it with `uv run examples/check.py` after setting `TYPESAFE_API_KEY`.
"""

from vibecheck.sync import check

ticket = (
    "I was charged twice for order A-104 and nobody has answered my last two emails. "
    "Refund the duplicate or I'm cancelling my subscription."
)
alerts = [
    "Checkout is down for every customer; all requests return 500.",
    "Error rate on checkout spiked to 40% in the last five minutes.",
    "The export button crashes settings in Safari. Chrome works fine.",
]

print("A plain check returns True or False")
cancelling = check("Is the customer threatening to cancel?", ticket)
print(f"  Is the customer threatening to cancel?  {cancelling}")
print()

print("A higher threshold means a yes has to be more certain")
for alert in alerts:
    paging, p = check(
        "Is this a production outage?", alert, threshold=0.9, probabilities=True
    )
    print(f"  {alert!r}")
    print(f"    Page on-call?  {paging} (p = {p:.2f})")
print()

print("A (low, high) threshold returns None when the model is unsure")
for alert in alerts:
    match check("Is this a production outage?", alert, threshold=(0.3, 0.9)):
        case True:
            action = "page on-call"
        case False:
            action = "archive"
        case None:
            action = "send to a person"
    print(f"  {alert!r}")
    print(f"    → {action}")
print()

print("probabilities=True returns the answer and the probability of yes")
angry, p = check("Is the customer angry?", ticket, probabilities=True)
print(f"  Is the customer angry?  {angry} (p = {p:.2f})")
print()

print("Leave the data out when the question stands on its own")
print(f"  Is Paris the capital of France?  {check('Is Paris the capital of France?')}")
