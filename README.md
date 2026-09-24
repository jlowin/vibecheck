# vibecheck

**The easiest decisions your code will ever make.**

vibecheck turns decision models into simple building blocks for Python.

Decision models such as [Jev](https://typesafe.ai) are a new kind of AI model built for judgment calls. They answer typed questions (yes or no, pick one, rate on a scale) in a fraction of a second, for a fraction of a cent, with a probability attached to every answer.

vibecheck puts all of that one function call away. Each call returns a plain Python value, with no prompts to template, no text to parse, and no agents to configure:

```python
from vibecheck.sync import check

ticket = "Third outage this month. Fix it by Friday or we're moving to another vendor."

if check("Is the customer threatening to cancel?", ticket):
    print("Escalating to the account team")
```

vibecheck has four functions: `check` answers yes or no, `classify` picks one option, `label` picks every option that applies, and `score` rates on a scale. Judgment calls, as function calls.

## Why vibecheck

- 🍀 **Simple**: one function call, one plain Python value.
- 🎛️ **Powerful**: probabilities, thresholds, and "unsure" answers when you need them, out of the way when you don't.
- ⚡ **Efficient**: batching lets you ask ten questions about the same data for about the cost of one.
- 🐍 **Pythonic**: a DSL that feels familiar, even the first time you use it.

## Installation

```bash
uv add vibecheck-py
```

The package is published as `vibecheck-py` and imported as `vibecheck`.

vibecheck reads your API key from the environment. Get one at [console.typesafe.ai](https://console.typesafe.ai), or use any compatible provider (see [Configuration](#configuration)):

```bash
export TYPESAFE_API_KEY=...
```

## Functions

Each function answers a different kind of question:

| Function | Asks | Returns |
|---|---|---|
| `check` | Is this true? | `bool` |
| `classify` | Which one of these? | one option |
| `label` | Which of these apply? | a list of options |
| `score` | Where on this scale? | a `float` |

These functions are async by default, and the examples below use them that way. The blocking versions in `vibecheck.sync`, used in the example at the top of this page, take exactly the same arguments:

```python
from vibecheck.sync import check, classify, label, score
```

### Check

`check` asks a yes/no question and returns a `bool`, which makes it the natural fit for guard clauses and `if` statements.

```python
from vibecheck import check

message = "I've asked three times now. Can I please talk to a real person?"

if await check("Is the customer asking for a human?", message):
    print("Routing to an agent")
```

The model answers with the probability that the answer is yes, and `check` returns `True` when that probability is at least 0.5. When a false yes would be expensive, such as paging someone at 3 a.m. or issuing a refund, raise the bar with `threshold`:

```python
from vibecheck import check

alert = "Error rate on checkout spiked to 40% in the last five minutes."

if await check("Is this a production outage?", alert, threshold=0.9):
    print("Paging on-call")
```

Some decisions deserve a third outcome: act when the model is confident, drop it when the model is confident in the other direction, and ask a person about everything in between. Pass a `(low, high)` pair as the threshold, and `check` returns `None` when the probability of yes falls between the two. Here, a probability of 0.9 or more is `True`, less than 0.3 is `False`, and anything in the middle is `None`:

```python
from vibecheck import check

alert = "The export button crashes settings in Safari. Chrome works fine."

match await check("Is this a production outage?", alert, threshold=(0.3, 0.9)):
    case True:
        print("Paging on-call")
    case False:
        print("Archiving")
    case None:
        print("Sending to a person for review")
```

Handle a three-way check with `match` rather than `if`. `None` is falsy, so an `if` would quietly treat "unsure" as "no".

### Classify

`classify` picks exactly one of your options and returns it:

```python
from vibecheck import classify

ticket = "My running shoes arrived in the wrong size. Can I swap them for a 10?"

team = await classify("Which team should handle this?", ["returns", "shipping", "billing"], ticket)
```

`team` is `"returns"`. Because `classify` always picks one of your options, give it a way out when your list might not cover every case. An `"other"` option works well.

### Label

`label` returns every option that applies, most likely first. The model judges each option on its own, so an article can be about pricing *and* security, or about nothing on your list at all:

```python
from vibecheck import label

article = "Acme raised prices 15%, disclosed a data breach, and announced layoffs."

topics = await label(
    "Which topics does this article cover?",
    ["pricing", "security", "layoffs", "sports"],
    article,
)
```

`topics` holds `"pricing"`, `"security"`, and `"layoffs"`, ordered by how likely each one is. An option makes the list when its probability is at least `threshold`, which defaults to 0.5, and `limit` caps how many come back. To get exactly the two most likely options regardless of their probability, set both:

```python
from vibecheck import label

article = "Acme raised prices 15%, disclosed a data breach, and announced layoffs."

top_two = await label(
    "Which topics does this article cover?",
    ["pricing", "security", "layoffs", "sports"],
    article,
    threshold=0,
    limit=2,
)
```

### Score

`score` rates the data on ordered levels, listed from lowest to highest, and returns a position on that scale. The position is the probability-weighted average of the levels, so it can land between two of them: `1.4` means the model is split between levels 1 and 2 and leans toward 1.

The simplest scale is a list of level descriptions, numbered from 0:

```python
from vibecheck import score

report = "The export button crashes settings in Safari. Chrome works fine."

severity = await score(
    "How severe is this bug?",
    ["Cosmetic; no impact on functionality", "Broken, but a workaround exists", "Blocking; no workaround"],
    report,
)

if severity >= 1.5:
    print("Escalating")
```

To get the answer in your own units, use numbers as the levels. A range or a list of numbers gives undescribed levels, and a dict gives each number a description:

```python
from vibecheck import score

review = "Solid product, arrived late, support was slow to respond."

stars = await score("How satisfied is this customer?", range(1, 6), review)

described_stars = await score(
    "How satisfied is this customer?",
    {1: "Angry; wants a refund", 3: "Mixed", 5: "Delighted; would recommend"},
    review,
)
```

Both return a value between 1 and 5. Decision models read questions literally, so described levels give better answers than bare numbers.

## Options

`classify` and `label` send the model a list of options, and each option needs a text label the model can read. Plain strings are their own labels. When a name alone could be ambiguous, pass a dict instead: the keys are the options, and the values describe when each one applies. The model reads those descriptions, which makes them the place to settle edge cases:

```python
from vibecheck import classify

ticket = "I was charged twice for order A-104."

team = await classify(
    "Which team should handle this?",
    {
        "returns": "Exchanges, wrong or damaged items",
        "shipping": "Delivery status, delays, lost packages",
        "billing": "Charges, invoices, refunds, payment problems",
    },
    ticket,
)
```

Options don't have to be strings. vibecheck gives each option a label, sends the labels, and hands back the original object, so you can choose between functions and call the one the model picks:

```python
from vibecheck import classify


def refund(ticket: str) -> None:
    """Customer wants money back for a charge or order."""
    print("Refunding")


def reset_password(ticket: str) -> None:
    """Customer is locked out or can't sign in."""
    print("Sending a reset link")


def escalate(ticket: str) -> None:
    """Anything else, or anything that needs a human."""
    print("Escalating")


ticket = "I can't log in and I've tried the reset link twice."

handler = await classify("How should we handle this ticket?", [refund, reset_password, escalate], ticket)
handler(ticket)
```

An `Enum` class works as a list of options too, and you get a member back:

```python
from enum import Enum

from vibecheck import classify


class Sentiment(Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


mood = await classify("What is the tone of this review?", Sentiment, "Honestly? Fine. It works.")
```

Here is how each kind of option becomes a label and a description:

| Option | Label | Description |
|---|---|---|
| `str` | the string | the dict value, if you passed a dict |
| Enum member | its value if that's a string, otherwise its name | the dict value, if you passed a dict |
| function or class | `__name__` | the first line of its docstring, unless you passed a dict value |
| anything else | `str(value)` | the dict value, if you passed a dict |

Two options that end up with the same label raise a `ValueError` before any request is sent, because the answer couldn't be mapped back to one of them.

## Data

The data comes last, and it can be whatever you already have. A string is sent as-is. A dict or list is sent as structured JSON, so its field names give the model context. A Pydantic model or dataclass is converted to a dict first, and anything else goes through `str()`:

```python
from dataclasses import dataclass

from vibecheck import check


@dataclass
class Order:
    id: str
    charges: list[float]
    customer_message: str


order = Order(id="A-104", charges=[49.0, 49.0], customer_message="I was charged twice!")

if await check("Did the customer ask for a refund?", order):
    print("Refund requested")
```

Structure helps more than volume. Accuracy drops as the data fills up with irrelevant detail, so send the fields a question needs rather than your whole database row.

When a question stands on its own, leave the data out:

```python
from vibecheck import classify

kind = await classify("What is Harry Potter?", ["book series", "person", "city"])
```

## Good Questions

Decision models are at their best on quick, common-sense judgments about text: intent, tone, topic, urgency, relevance, whether a statement is true of a document. A good question is one a sharp colleague could answer at a glance.

They read questions literally. If you find yourself explaining what you really meant, that explanation belongs in the question itself or in your option descriptions.

Arithmetic, counting, and date comparisons belong in code. A decision model recognizes the shape of an answer rather than computing it, so to count matching items, [filter](#filter) them and take the length. Decision models also don't generate text; when you need a reply written, use a language model.

Once a question works well, give it a name the way you would any other piece of logic. It's an ordinary function with an ordinary signature, you test it the way you test everything else, and swapping it for a heuristic later is a one-line change:

```python
from vibecheck import check


async def needs_reply_today(ticket: str) -> bool:
    return await check("Does this ticket need a reply today?", ticket, threshold=0.7)
```

## Probabilities

Every answer starts as a probability, and sometimes you want the number as well as the decision. Pass `probabilities=True` to any function and you get a pair: the answer, exactly as you'd get it without the flag, and the probabilities behind it.

```python
from vibecheck import check, classify

ticket = "Wrong size arrived, and I still haven't seen the refund for my last return."

urgent, p = await check("Is this urgent?", ticket, probabilities=True)

team, distribution = await classify(
    "Which team should handle this?",
    ["returns", "shipping", "billing"],
    ticket,
    probabilities=True,
)
```

The second element depends on the function:

| Function | Probabilities |
|---|---|
| `check` | the probability of yes, as a `float` |
| `classify` | a dict of every option and its probability, summing to 1 |
| `label` | a dict of every option and its probability, each judged on its own |
| `score` | a dict of every level and its probability |

The pair is a `Decision` named tuple, so `.answer` and `.probabilities` work as well as unpacking.

A close runner-up is often the most useful signal you have. When the top two options are nearly tied, the model is telling you the case is ambiguous, and a person should look:

```python
from vibecheck import classify

ticket = "Wrong size arrived, and I still haven't seen the refund for my last return."

team, distribution = await classify(
    "Which team should handle this?",
    ["returns", "shipping", "billing"],
    ticket,
    probabilities=True,
)
best, runner_up = sorted(distribution.values(), reverse=True)[:2]

if best - runner_up < 0.3:
    print("Too close to call; sending to triage")
else:
    print(f"Assigning to {team}")
```

## Many Items

`filter` and `group` apply a decision to a whole list, the way their Python namesakes do. Each item gets its own request, and the requests run concurrently: 16 at a time by default, adjustable with `max_concurrency`.

These examples call the functions through the module, because `from vibecheck import filter` would hide Python's built-in `filter`.

### Filter

`vibecheck.filter` keeps the items where the answer to a yes/no question is yes, in their original order:

```python
import vibecheck

tickets = [
    "Refund my duplicate charge, please.",
    "Where is my package? It's a week late.",
    "I want my money back for this broken lamp.",
]

refunds = await vibecheck.filter("Is the customer asking for their money back?", tickets)
```

`refunds` holds the first and third tickets. `threshold` works the same way as in `check`, and `probabilities=True` pairs the kept items with every item's probability of yes.

### Group

`vibecheck.group` classifies each item and returns a dict mapping each option to its items. Every option appears as a key, in the order you gave them, even when no item landed there:

```python
import vibecheck

tickets = [
    "Refund my duplicate charge, please.",
    "Where is my package? It's a week late.",
    "Love the new design, thanks!",
]

by_team = await vibecheck.group(
    "Which team should handle this?",
    ["returns", "shipping", "billing", "other"],
    tickets,
)
```

## Many Questions

Decision models read the data once and answer every question about it in parallel. Ten questions about one ticket take about as long as one, and cost little more. In a test with a 5,000-token document, 100 questions asked together gave the same answers as 100 separate requests, for about 1% of the tokens.

vibecheck gives you two ways to ask many questions about the same data in one request: a batch for questions you write inline, and a schema for a set of questions you'll ask again and again.

### Batches

A batch collects questions about one piece of data and sends them all as a single request when the block ends:

```python
import vibecheck

ticket = "I was charged twice and nobody has answered my last two emails. Fix this or I'm cancelling."

async with vibecheck.batch(ticket) as b:
    team = b.classify("Which team should handle this?", ["returns", "shipping", "billing"])
    cancelling = b.check("Is the customer threatening to cancel?")
    urgency = b.score("How urgent is this?", range(1, 6))

print(team.result(), cancelling.result(), urgency.result())
```

Every question in the batch shares the data you passed to `batch`, and each one keeps its own instructions and answer type. The answers are available once the block ends. Calling `.result()` inside the block raises an error, and so does using an answer as a condition without calling `.result()`.

### Schemas

When the same set of questions comes up again and again, describe them as a class and fill it with `assess`. Each field becomes one question, all asked in one request, and you get back an instance with every field filled in:

```python
from dataclasses import dataclass
from typing import Annotated, Literal

from vibecheck import assess


@dataclass
class Triage:
    team: Literal["returns", "shipping", "billing"]
    urgent: Annotated[bool, "Does this need a reply today?"]
    frustration: Annotated[float, "How frustrated is the customer?", ["calm", "annoyed", "angry"]]
    topics: list[Literal["refund", "delivery", "account"]]


ticket = "I was charged twice for order A-104 and nobody has answered my emails. Refund the duplicate NOW."

triage = await assess("Triage this support ticket", Triage, ticket)
```

`triage` comes back as something like `Triage(team='billing', urgent=True, frustration=2.0, topics=['refund'])`. The field's type decides which function asks it, and `Annotated` metadata says how to ask:

| Field type | Function | Needs |
|---|---|---|
| `bool` | `check` | nothing |
| `Literal[...]` or an `Enum` | `classify` | nothing |
| any other type | `classify` | a list or dict of options in `Annotated` |
| `float` or `int` | `score` | levels in `Annotated`; `int` rounds the position |
| `list[...]` | `label` | `Literal` or `Enum` items, or options in `Annotated` |

A string in `Annotated` is that field's question. Without one, the field's name is used, so `urgent` alone would be asked as "urgent". The question you pass to `assess` is shared context, and the model sees it alongside every field's question. Dataclasses, Pydantic models, `TypedDict`, and `NamedTuple` all work, with no base class or decorator required.

## Sync and Async

The functions in `vibecheck.sync` take exactly the same arguments and block until the answer arrives, which suits scripts and other synchronous code:

```python
from vibecheck import sync

ticket = "Third outage this month. Fix it by Friday or we're moving to another vendor."

if sync.check("Is the customer threatening to cancel?", ticket):
    print("Escalating to the account team")
```

Batches work with both `async with` and a plain `with`.

Forgetting `await` doesn't fail silently. Writing `if check(...)` without `await` raises a `TypeError` that tells you to add it, instead of treating the pending result as true. The async functions return real coroutines, so they also work with `asyncio.run`, `asyncio.gather`, and task groups.

## Configuration

The default backend speaks TypeSafe's System One API and honors the TypeSafe SDK's environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `TYPESAFE_API_KEY` | none | API key (required) |
| `TYPESAFE_DEFAULT_MODEL` | `jev-latest` | Model name or alias |
| `TYPESAFE_BASE_URL` | `https://api.typesafe.ai` | API endpoint |

Any server that speaks TypeSafe's API works with just a new base URL. Vercel AI Gateway, for example, serves Jev without a TypeSafe account:

```
TYPESAFE_BASE_URL=https://ai-gateway.vercel.sh/typesafe
TYPESAFE_API_KEY=<your AI Gateway key>
TYPESAFE_DEFAULT_MODEL=typesafe-ai/jev
```

Every function also accepts `model=` to pin a version for one call. Pin a versioned model such as `jev-1.13.0` once you've tuned thresholds against it, because `jev-latest` moves when a new release ships.

### Backends

A backend sends vibecheck's questions to a decision model and translates the answers back into Python values. The default, `TypeSafeBackend`, speaks TypeSafe's API through the official SDK. To configure the SDK's clients yourself, pass them to a `TypeSafeBackend`, then use it for a single call with `backend=` or for every call with `set_default_backend()`:

```python
from typesafe_sdk import AsyncTypeSafeClient, TypeSafeClient

from vibecheck import TypeSafeBackend, set_default_backend

set_default_backend(
    TypeSafeBackend(client=TypeSafeClient(timeout=30), async_client=AsyncTypeSafeClient(timeout=30))
)
```

### Testing

Code that makes decisions deserves tests that don't touch the network. `vibecheck.testing.FakeBackend` answers every question with a function you provide and records each request it receives:

```python
from vibecheck import sync
from vibecheck.testing import FakeBackend, yes

backend = FakeBackend(respond=lambda state, name, question: yes(0.9))

assert sync.check("Is this urgent?", "The site is down!", backend=backend)
assert backend.calls[0].state == "The site is down!"
```

## Reference

Every function takes the question first and the data last, accepts `model=` and `backend=`, and returns an `(answer, probabilities)` pair when you pass `probabilities=True`. For `filter` and `group`, the probabilities are a list with one entry per item.

```python
await check(question, data=None, *, threshold=0.5)                       # bool, or bool | None with a (low, high) threshold
await classify(question, options, data=None)                             # one option
await label(question, options, data=None, *, threshold=0.5, limit=None)  # list of options, most likely first
await score(question, levels, data=None)                                 # float
await assess(question, schema, data=None, *, threshold=0.5)              # an instance of schema

await vibecheck.filter(question, items, *, threshold=0.5, max_concurrency=16)  # the items that passed
await vibecheck.group(question, options, items, *, max_concurrency=16)         # dict of option -> items

async with vibecheck.batch(data) as b:  # b.check, b.classify, b.label, b.score, b.assess
    ...
```

`vibecheck.sync` has the same functions, blocking instead of async.

- **Options** can be a list, a dict of option to description, or an `Enum` class.
- **Levels** can be a list of descriptions (numbered from 0), a list or range of numbers, or a dict of number to description, ordered from lowest to highest.
- **Limits** come from the API: a question takes 2 to 255 options, and a scale takes 2 to 10 levels. vibecheck checks both before sending a request.
