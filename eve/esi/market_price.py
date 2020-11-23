from dataclasses import dataclass


@dataclass
class MarketPrice:
    adjusted_price: float
    average_price: float
    type_id: int
