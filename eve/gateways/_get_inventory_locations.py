from typing import Dict, Any

import eve_sde_tools
from eve.domain import InventoryLocation


class GetInventoryLocationGateway:
    _cache_dir: str

    def __init__(self, cache_dir: str):
        self._cache_dir = cache_dir

    def get_inventory_locations(self) -> Dict[int, InventoryLocation]:
        data = eve_sde_tools.read_converted(self._cache_dir, "invItems")
        return {int(k): self._map_dict_to_inventory_location(v) for (k, v) in data.items()}

    @staticmethod
    def _map_dict_to_inventory_location(src: Dict[str, Any]) -> InventoryLocation:
        return InventoryLocation(
            parent_location_id=src.get("locationID", 0),
            type_id=src.get("typeID", 0),
        )
