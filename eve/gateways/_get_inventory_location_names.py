from typing import Dict

import eve_sde_tools


class GetInventoryLocationNamesGateway:
    _cache_dir: str

    def __init__(self, cache_dir: str):
        self._cache_dir = cache_dir

    def names(self) -> Dict[int, str]:
        data: Dict[str, str] = eve_sde_tools.read_converted(self._cache_dir, "invNames")
        return {int(k): v for k, v in data.items()}
