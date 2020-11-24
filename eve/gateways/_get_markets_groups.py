from typing import Dict, Any

import eve_sde_tools
from eve.domain import MarketGroup


class GetMarketGroupsGateway:
    _cache_dir: str

    def __init__(self, cache_dir: str):
        self._cache_dir = cache_dir

    def market_groups(self) -> Dict[int, MarketGroup]:
        data = eve_sde_tools.read_converted(self._cache_dir, "marketGroups")
        return {int(k): self._map_dict_to_market_group(k, v) for k, v in data.items()}

    @staticmethod
    def _map_dict_to_market_group(group_id: str, src: Dict[str, Any]):
        return MarketGroup(
            group_id=int(group_id),
            icon_id=src.get("iconID", 0),
            name=src.get("nameID", {}),
            parent_group_id=src.get("parentGroupID", None)
        )
