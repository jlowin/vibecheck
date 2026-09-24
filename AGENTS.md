# vibecheck

vibecheck is a small Python library for putting decision-model judgments into ordinary control flow. It is not an agent framework. Keep the public API simple: a question and optional data produce a typed Python answer with little setup.

## Sources of truth

- `README.md` is the user documentation and a working-backwards specification for the intended API. Update it first when changing the public design.
- `.agents/skills/vibecheck/SKILL.md` teaches coding agents when and how to use the library. Keep its signatures, kwargs, examples, and decision advice consistent with the README and implementation.
- `src/vibecheck/` is the implementation; `tests/` records executable behavior. Resolve any mismatch among these files as part of the change.

When changing public behavior, configuration, or recommended usage, review and update **both** the README and the skill in the same change. If a code change leaves their text accurate, verify that explicitly before finishing. Do not add a new feature only to the code or document behavior that the code does not support.

## Working in this repo

- The package is published as `vibecheck-py` and imported as `vibecheck`. The top-level decision functions are async; `vibecheck.sync` provides blocking equivalents.
- Use `uv` for the project environment. Run focused tests with `uv run pytest` and lint with `uv run ruff check .` when relevant.
- Use `vibecheck.testing.FakeBackend` for deterministic tests. Live model calls require credentials and should be reserved for judgment quality checks that need them.
- Favor clear questions, explicit option boundaries, and ordinary Python for deterministic work. Preserve the low-ceremony API rather than adding agent orchestration around it.
