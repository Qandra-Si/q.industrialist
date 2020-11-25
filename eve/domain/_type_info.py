from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


@dataclass
class TypeInfo:
    type_id: int
    published: bool
    volume: float
    basePrice: Optional[float]
    market_group_id: Optional[int]
    meta_group_id: Optional[int]
    icon_id: Optional[int]
    name: Dict[str, str]


class TypeIds(Enum):
    HANGAR_CONTAINER = 41567
    SOLAR_SYSTEM = 5
