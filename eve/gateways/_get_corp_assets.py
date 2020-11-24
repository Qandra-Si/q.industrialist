from typing import List

from eve.domain import Asset
from eve_esi_interface import EveOnlineInterface


class GetCorpAssetsGateway:
    _eve_interface: EveOnlineInterface
    _corporation_id: int

    def __init__(self, eve_interface: EveOnlineInterface, corporation_id: int):
        self._eve_interface = eve_interface
        self._corporation_id = corporation_id
        pass

    def assets(self) -> List[Asset]:
        url = "corporations/{}/assets/".format(self._corporation_id)
        data = self._eve_interface.get_esi_paged_data(url)
        return [Asset.from_dict(x) for x in data]
