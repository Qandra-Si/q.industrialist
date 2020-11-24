from typing import Dict

import eve_sde_tools
from eve.domain import TypeInfo


class GetTypeInfoGateway:
    _cache_dir: str

    def __init__(self, cache_dir: str):
        self._cache_dir = cache_dir

    def type_info(self) -> Dict[int, TypeInfo]:
        data: Dict[str, Dict] = eve_sde_tools.read_converted(self._cache_dir, "typeIDs")
        return {int(type_id): self._map_dict_to_type_info(type_id, info) for type_id, info in data.items()}

    @staticmethod
    def _map_dict_to_type_info(type_id: str, src: Dict):
        return TypeInfo(
            type_id=int(type_id),
            published=src.get("published", False),
            volume=src.get("volume", 0),
            basePrice=src.get("basePrice", None),
            market_group_id=src.get("marketGroupID", None),
            meta_group_id=src.get("metaGroupID", None),
            icon_id=src.get("iconID", None),
            name=src.get("name", {})
        )
