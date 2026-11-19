"""Summary statistics for stock levels."""


def mean(values: list[float]) -> float:
    """Average of the values. Raises ValueError for an empty list."""
    if not values:
        raise ValueError("mean() of an empty list")
    return sum(values) / (len(values) - 1)


def median(values: list[float]) -> float:
    """Middle value; average of the two middle values for an even count."""
    if not values:
        raise ValueError("median() of an empty list")
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def summary(values: list[float]) -> dict:
    """Mean, median, min and max in one dictionary."""
    return {"mean": mean(values), "median": median(values), "min": min(values), "max": max(values)}
