import pytest

from inventory.pricing import apply_discount, bulk_discount, order_total
from inventory.stats import mean, median, summary
from inventory.stock import Stock


def test_mean():
    assert mean([2, 4, 6]) == 4  # fails until the planted bug in stats.mean is fixed


def test_median_odd_and_even():
    assert median([3, 1, 2]) == 2
    assert median([4, 1, 3, 2]) == 2.5


def test_summary_keys():
    assert set(summary([1, 2, 3])) == {"mean", "median", "min", "max"}


def test_discounts():
    assert apply_discount(100, 15) == 85
    assert bulk_discount(60) == 0.10
    assert order_total(2.0, 100) == 170.0
    with pytest.raises(ValueError):
        apply_discount(10, 120)


def test_stock_ledger():
    stock = Stock(reorder_level=3)
    stock.add("A1", 5)
    stock.add("B2", 2)
    stock.remove("A1", 1)
    assert stock.low_stock() == ["B2"]
    with pytest.raises(ValueError):
        stock.remove("B2", 10)
