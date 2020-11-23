from typing import List, Dict

from eve.esi import MarketPrice


def map_market_price_list_to_dict(item_list: List[Dict]) -> Dict[int, MarketPrice]:
    result: Dict[int, MarketPrice] = {}
    for item in item_list:
        price_item = MarketPrice(
            adjusted_price=item.get("adjusted_price", 0),
            average_price=item.get("average_price", 0),
            type_id=item.get("type_id", 0)
        )
        result[price_item.type_id] = price_item
    return result
