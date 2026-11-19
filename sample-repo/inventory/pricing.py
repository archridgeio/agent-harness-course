"""Discounts and bulk pricing."""

BULK_TIERS = [(100, 0.15), (50, 0.10), (10, 0.05)]  # (minimum quantity, discount)


def apply_discount(price: float, percent: float) -> float:
    """Price after a percentage discount, rounded to 2 decimals. percent must be 0-100."""
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    return round(price * (1 - percent / 100), 2)


def bulk_discount(quantity: int) -> float:
    """Discount rate for an order quantity, using the highest tier reached."""
    for minimum, rate in BULK_TIERS:
        if quantity >= minimum:
            return rate
    return 0.0


def order_total(unit_price: float, quantity: int) -> float:
    """Total for an order after the bulk discount."""
    return round(unit_price * quantity * (1 - bulk_discount(quantity)), 2)
