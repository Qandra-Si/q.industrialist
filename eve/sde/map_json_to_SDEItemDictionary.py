from typing import Dict

from eve.sde.SDEItem import SDEItem


def map_json_to_sde_item_dictionary(json: Dict[str, Dict]) -> Dict[int, SDEItem]:
    return {int(k): SDEItem.from_dict(v) for (k, v) in json.items()}
