---
name: vibecheck
description: Use vibecheck-py to put decision models such as Jev into Python code for typed judgments. Apply when implementing or reviewing code that uses vibecheck for yes/no decisions, classification, labeling, scoring, or repeated judgments.
---

# Use vibecheck

The package is installed as `vibecheck-py` and imported as `vibecheck`. The repository's `README.md` has longer examples; the signatures and behavior here match `src/vibecheck/`.

## Imports, calling convention, and shared kwargs

`from vibecheck import check, classify, label, score, assess` imports async functions: `await` their results. They return a `Pending` coroutine; using one as a Boolean without awaiting raises `TypeError`. `from vibecheck import sync` exposes blocking versions with the **same arguments and results**. Use `import vibecheck` for `filter` and `group` to avoid shadowing Python built-ins. The question is first; optional `data` is last among positional arguments for single decisions. If omitted, the model gets an empty state. Strings are sent as text; dicts and lists as structured JSON; Pydantic models and dataclasses are converted to structured data.

Every top-level decision function accepts these keyword-only arguments:

| Kwarg | Default | Meaning |
| --- | --- | --- |
| `probabilities: bool` | `False` | Return `Decision(answer, probabilities)` instead of the plain answer. It is a named tuple with `.answer`, `.probabilities`, and unpacking. The probability shape varies by function below. |
| `model: str \| None` | `None` | Override the backend's model for this call. |
| `backend: Backend \| None` | `None` | Use this backend for this call; otherwise use `get_default_backend()`. |

The other kwargs belong only to the functions that list them. In particular, `classify`, `score`, and `group` have no `threshold` kwarg.

## One decision

```python
await check(question, data=None, *, threshold=0.5, probabilities=False, model=None, backend=None)
await classify(question, options, data=None, *, probabilities=False, model=None, backend=None)
await label(question, options, data=None, *, threshold=0.5, limit=None, probabilities=False, model=None, backend=None)
await score(question, levels, data=None, *, probabilities=False, model=None, backend=None)
await assess(question, schema, data=None, *, threshold=0.5, probabilities=False, model=None, backend=None)
```

| Function | Answer | `Decision.probabilities` when requested |
| --- | --- | --- |
| `check` | `bool`; `bool \| None` with a threshold pair | Probability of yes, `float` |
| `classify` | Exactly one original option | `{option: probability}`; values sum to 1 |
| `label` | Zero or more original options, most likely first | `{option: probability}`; options judged independently |
| `score` | Probability-weighted position, `float` | `{numeric_level: probability}` |
| `assess` | Filled instance of `schema` | `{field_name: field_probabilities}` |

### `check`

`threshold` is a number in `[0, 1]`, default 0.5. Return `True` when the probability of yes is at least the threshold. A `(low, high)` pair returns `False` below `low`, `True` at or above `high`, and `None` between them. Handle `None` as a separate outcome, rather than treating it as false.

### `classify`

`options` is a list or iterable of choices, an Enum class, or `{option: description}`. The function always picks one; add an `other` or escalation option if the set may be incomplete. It returns the original option object, including an Enum member or function if those were supplied. There is no threshold or abstain kwarg.

### `label`

`options` has the same forms as `classify`. Each option gets a separate yes/no judgment, so the answer may be empty. `threshold` is the minimum probability for inclusion, default 0.5, from 0 to 1. `limit` is a positive cap on the number returned, or `None` for no cap. For the top two regardless of probability, use `threshold=0, limit=2`. Returned options are sorted by probability, highest first.

### `score`

`levels` is 2–10 levels ordered low to high. Pass a list of descriptions (numbered from 0), numeric levels such as `range(1, 6)`, or `{number: description}` (sorted by numeric key). The result is a weighted position and can fall between levels. Descriptions give the model clearer criteria than bare numbers. There is no threshold kwarg.

### `assess`

`schema` must be a dataclass, Pydantic model, `TypedDict`, or `NamedTuple` class with fields. The call asks one question per field in a single request and returns an instance of that schema. The top-level `question` is shared task context. `threshold`, default 0.5, applies to Boolean and list fields.

| Field type | Decision | `Annotated` metadata needed |
| --- | --- | --- |
| `bool` | `check` | None |
| `Literal[...]` or `Enum` | `classify` | None |
| Other scalar type | `classify` | Options |
| `float` or `int` | `score`; `int` rounds the position | Levels |
| `list[Literal[...]]` or `list[Enum]` | `label` | None |
| Other `list[...]` | `label` | Options |

The first string in `Annotated` supplies the field question; otherwise vibecheck uses the field name with underscores changed to spaces. A list, tuple, range, or dict in `Annotated` supplies options or levels. For example:

```python
from dataclasses import dataclass
from typing import Annotated, Literal
from vibecheck import assess

@dataclass
class Triage:
    team: Literal["billing", "support", "other"]
    urgent: Annotated[bool, "Does this need a reply today?"]
    severity: Annotated[float, "How severe is this?", ["minor", "workaround", "blocking"]]
    topics: list[Literal["billing", "login", "delivery"]]

triage = await assess("Triage this ticket", Triage, ticket)
```

## Option and data rules

Choices may be strings, Enum members, functions, classes, or other hashable objects. The text sent to the model is the string itself, an Enum's string value (otherwise its name), a function/class `__name__`, or `str(option)`. A function/class uses its first docstring line as a default description. A dict value overrides that description and is the place to define boundaries. Pass 2–255 options with distinct text labels; duplicate labels raise `ValueError`. A single string is not an options collection.

Keep data focused on the question. A structured dict or model preserves useful field names. Don't ask a decision model to perform arithmetic or generate prose; use Python or a language model for those tasks.

## One question per item

```python
await vibecheck.filter(question, items, *, threshold=0.5, probabilities=False, model=None, backend=None, max_concurrency=16)
await vibecheck.group(question, options, items, *, probabilities=False, model=None, backend=None, max_concurrency=16)
```

- `filter` keeps items whose yes/no answer passes `threshold`, preserving original order. `threshold` accepts one numeric value, **not** a `(low, high)` pair. With probabilities, the second result is a list of yes probabilities for **all input items**, in input order.
- `group` classifies each item and returns `{option: [items]}`. Every option appears as a key in the supplied order, even if its group is empty. With probabilities, the second result is a list of option distributions for **all input items**, in input order. Its `options` follow the `classify` rules.
- Each item triggers a separate request. Requests run concurrently; `max_concurrency` limits simultaneous work. The default is 16 for both functions.

## Several questions about one item: `batch`

```python
vibecheck.batch(data=None, *, model=None, backend=None)
b.check(question, *, threshold=0.5, probabilities=False)
b.classify(question, options, *, probabilities=False)
b.label(question, options, *, threshold=0.5, limit=None, probabilities=False)
b.score(question, levels, *, probabilities=False)
b.assess(question, schema, *, threshold=0.5, probabilities=False)
```

`batch` is a `Batch` class exposed as `vibecheck.batch` and `vibecheck.sync.batch`. Its methods use the shared `data`, `model`, and `backend` given to the constructor; they have no per-question kwargs for those. Each method returns a `Deferred` value with `.result()`. Leaving `with` or `async with` sends all questions in one request. Read `.result()` only after the block; inside it, the answer is not ready. Manual sending is available with `b.send()` or `await b.asend()`; send a batch once.

```python
import vibecheck

async with vibecheck.batch(ticket) as b:
    team = b.classify("Which team?", ["billing", "support", "other"])
    urgent = b.check("Does this need a reply today?")

print(team.result(), urgent.result())
```

## Backend configuration and test helpers

```python
TypeSafeBackend(client=None, async_client=None)
get_default_backend()
set_default_backend(backend)  # pass None to reset
FakeBackend(respond=...)      # from vibecheck.testing
yes(probability=1.0)
pick(**probabilities)
rate(*probabilities)
```

`TypeSafeBackend` is the default and uses TypeSafe's System One API. It reads `TYPESAFE_API_KEY` (required), `TYPESAFE_BASE_URL` (default `https://api.typesafe.ai`), and `TYPESAFE_DEFAULT_MODEL` (default `jev-latest`) through the SDK. `TypeSafeBackend(client=None, async_client=None)` accepts configured TypeSafe SDK clients. `get_default_backend()` returns the current backend. `set_default_backend(backend)` replaces it globally; `set_default_backend(None)` resets it. A custom `Backend` implements both `evaluate(state, questions, *, model=None)` and `aevaluate(state, questions, *, model=None)`.

`vibecheck.testing.FakeBackend(respond=...)` avoids network calls and records `calls`. Its callback receives `(state, name, question)` and returns an answer. Without a callback, it returns uniform probabilities. The helpers are `yes(probability=1.0)`, `pick(**probabilities)`, and `rate(*probabilities)` for yes/no, choice, and ordered-level answers. Use `backend=` on the call under test so a test does not change global configuration.

```python
from vibecheck.sync import check
from vibecheck.testing import FakeBackend, yes

backend = FakeBackend(respond=lambda state, name, question: yes(0.9))
assert check("Is this urgent?", "The site is down", backend=backend)
assert backend.calls[0].state == "The site is down"
```
