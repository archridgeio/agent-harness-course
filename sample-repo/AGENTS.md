# AGENTS.md — inventory sample project

## Commands
- Run tests: `python -m pytest -q` from the `sample-repo/` folder.

## Conventions
- Python 3.10+, standard library only. No new dependencies.
- Money is rounded to 2 decimals with `round(x, 2)`.
- Raise `ValueError` with a short message for bad input; never return None for errors.

## Gotchas
- `tests/conftest.py` adds this folder to `sys.path`; run pytest from `sample-repo/`.
- Keep functions pure; `Stock` is the only stateful class.

## When you change code
- Run the tests before saying you are done, and quote the pass/fail line.
