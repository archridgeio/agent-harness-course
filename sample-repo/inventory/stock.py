"""A stock ledger with low-stock alerts."""

from dataclasses import dataclass, field


@dataclass
class Stock:
    reorder_level: int = 5
    levels: dict[str, int] = field(default_factory=dict)

    def add(self, sku: str, quantity: int) -> int:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        self.levels[sku] = self.levels.get(sku, 0) + quantity
        return self.levels[sku]

    def remove(self, sku: str, quantity: int) -> int:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        current = self.levels.get(sku, 0)
        if quantity > current:
            raise ValueError(f"only {current} of {sku} in stock")
        self.levels[sku] = current - quantity
        return self.levels[sku]

    def low_stock(self) -> list[str]:
        """SKUs at or below the reorder level, sorted."""
        return sorted(sku for sku, qty in self.levels.items() if qty <= self.reorder_level)
