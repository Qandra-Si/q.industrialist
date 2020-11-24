from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Asset:
    is_blueprint_copy: bool
    is_singleton: bool
    item_id: int
    location_flag: str
    location_id: int
    location_type: str
    quantity: int
    type_id: int

    @staticmethod
    def from_dict(src: Dict[str, Any]):
        return Asset(
            is_blueprint_copy=src.get("is_blueprint_copy", False),
            is_singleton=src.get("is_singleton", False),
            item_id=src["item_id"],
            location_flag=src["location_flag"],
            location_id=src["location_id"],
            location_type=src["location_type"],
            quantity=src["quantity"],
            type_id=src["type_id"],
        )
