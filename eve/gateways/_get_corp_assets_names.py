import json
from typing import List, Dict

import eve_esi_tools
from eve.domain import AssetName, Asset
from eve_esi_interface import EveOnlineInterface


class GetCorpAssetsNamesGateway:
    _eve_interface: EveOnlineInterface
    _corporation_id: int

    def __init__(self, eve_interface: EveOnlineInterface, corporation_id: int):
        self._eve_interface = eve_interface
        self._corporation_id = corporation_id
        pass

    def asets_name(self, corp_assets_data: List[Asset]) -> List[AssetName]:
        ids = eve_esi_tools.get_assets_named_ids(corp_assets_data)

        if len(ids) == 0: return []

        # Requires role(s): Director
        data = self._eve_interface.get_esi_data(
            "corporations/{}/assets/names/".format(self._corporation_id),
            json.dumps(ids, indent=0, sort_keys=False)
        )
        return [self._map_dict_to_asset_name(item) for item in data]

    @staticmethod
    def _map_dict_to_asset_name(item: Dict) -> AssetName:
        return AssetName(
            item_id=item.get("item_id", 0),
            name=item.get("name", "")
        )
