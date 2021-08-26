""" Q.Industrialist (desktop/mobile)
"""
from datetime import datetime


# 10000002=The Forge region
def get_the_forge_region_id():
    return 10000002


# 60003760: "Jita IV - Moon 4 - Caldari Navy Assembly Plant"
def get_jita_trade_hub_station_id():
    return 60003760


def load_market_history_data(esi_interface, product_type_id, region):
    # Public information about market prices
    markets_region_orders_data = esi_interface.get_esi_paged_data(
        "markets/{}/orders/?type_id={}&order_type=all".format(region, product_type_id),
        fully_trust_cache=True
    )
    return markets_region_orders_data


def get_last_month_market_history_data(history_data):
    __now = datetime.now()
    return [h for h in history_data if (__now - datetime.fromisoformat(h["date"])).days <= 31]


def get_last_week_market_history_data(history_data):
    __now = datetime.now()
    return [h for h in history_data if (__now - datetime.fromisoformat(h["date"])).days <= 7]


def load_market_orders_data(esi_interface, product_type_id, region):
    # Public information about market prices
    markets_region_history_data = esi_interface.get_esi_data(
        "markets/{}/history/?type_id={}".format(region, product_type_id),
        fully_trust_cache=True)
    return markets_region_history_data


def get_buy_sell_prices_from_orders(orders_data, location_id):
    sell_prices = [o["price"] for o in orders_data if (o["location_id"] == location_id) and not o["is_buy_order"]]
    buy_prices = [o["price"] for o in orders_data if (o["location_id"] == location_id) and o["is_buy_order"]]
    return sell_prices, buy_prices


def load_market_data(esi_interface, product_type_id, region):
    __markets_orders_data = load_market_history_data(esi_interface, product_type_id, region)
    __markets_history_data = load_market_orders_data(esi_interface, product_type_id, region)
    return __markets_orders_data, __markets_history_data


def get_market_analytics(markets_orders_data, markets_history_data, trade_hub):
    __sell_prices, __buy_prices = get_buy_sell_prices_from_orders(markets_orders_data, trade_hub)

    # список от CCP упорядочен по датам
    __month_history_data = get_last_month_market_history_data(markets_history_data)
    __week_history_data = get_last_week_market_history_data(__month_history_data)
    __last_known_data = markets_history_data[-1:][0] if markets_history_data else None

    __month_volume = sum([h["volume"] for h in __month_history_data])  # сумма (список кол-во сделок по дням)
    __month_avg_isk = sum([h["average"] * h["volume"] for h in __month_history_data])  # средний объём isk за последний месяц
    __week_volume = sum([h["volume"] for h in __week_history_data])  # сумма (кол-во сделок по дням)
    __week_avg_isk = sum([h["average"] * h["volume"] for h in __week_history_data])  # средний объём isk за последнюю неделю

    __market_dict = {
        "orders": {
        },
        "month": {
            "sum_volume": __month_volume,
            "avg_isk": __month_avg_isk
        },
        "week": {
            "sum_volume": __week_volume,
            "avg_isk": __week_avg_isk
        },
        "last_known": __last_known_data
    }

    if __sell_prices:
        __market_dict["orders"].update({"sell": min(__sell_prices)})
    if __buy_prices:
        __market_dict["orders"].update({"buy": max(__buy_prices)})

    return __market_dict


def get_current_market_prices(market_dict):
    orders = market_dict["orders"]
    last_history = market_dict["last_known"]

    # из sell:buy приоритетно берём lo и high (если в стакане есть ставки покупки/продажи), а avg из last-а
    __lo = orders["buy"] if "buy" in orders else None
    __hi = orders["sell"] if "sell" in orders else None
    __avg = None
    # если текущих ставок купли/продажи нет, то берём данные из последней записи по маркету
    if not (last_history is None):
        __avg = last_history["average"]
        if __lo is None:
            __lo = last_history["lowest"]
        if __hi is None:
            __hi = last_history["highest"]

    return {"lo": __lo, "hi": __hi, "avg": __avg}
