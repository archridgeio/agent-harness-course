# inventory (sample project)

A deliberately small Python project that the course's "repo assistant" agent reads, searches and fixes.

- `inventory/stats.py` — summary statistics for stock levels (**contains a planted bug**)
- `inventory/pricing.py` — discounts and bulk pricing
- `inventory/stock.py` — a stock ledger with low-stock alerts
- `tests/` — pytest suite; one test fails until the bug is fixed

Run the tests:

```bash
cd sample-repo
python -m pytest -q
```

Do not fix the bug by hand: the agents do that during the course. Reset with `git checkout sample-repo`.
