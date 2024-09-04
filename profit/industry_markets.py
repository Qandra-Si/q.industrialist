# -*- encoding: utf-8 -*-
import math
import typing


def eve_ceiling(isk: float) -> float:
    if isk < 100.0: isk = round(isk, 2)
    elif isk < 1000.0: isk = math.ceil(isk * 10.0) / 10.0
    elif isk < 10000.0: isk = math.ceil(isk)
    elif isk < 100000.0: isk = round(isk, -1)
    elif isk < 1000000.0: isk = round(isk, -2)
    elif isk < 10000000.0: isk = round(isk, -3)
    elif isk < 100000000.0: isk = round(isk, -4)  # 25990000.00 -> 25990000.00
    elif isk < 1000000000.0: isk = round(isk, -5)
    elif isk < 10000000000.0: isk = round(isk, -6)
    elif isk < 100000000000.0: isk = round(isk, -7)
    elif isk < 1000000000000.0: isk = round(isk, -8)
    elif isk < 10000000000000.0: isk = round(isk, -9)
    else: assert 0
    return isk


def eve_ceiling_change_by_point(isk: float, points: int) -> float:
    assert points == +1 or points == -1
    # изменить цену в рыночном формате EVE Online на один пункт (вверх pips=+1, вниз pips=-1)
    if isk < 100.0: pip = 0.01  # 99.99 -> 0.01
    elif isk < 1000.0: pip = 0.1  # 999.90 -> 0.1
    elif isk < 10000.0: pip = 1.0  # 9999 -> 1
    elif isk < 100000.0: pip = 10.0  # 99990 -> 10
    elif isk < 1000000.0: pip = 100.0  # 999900 -> 100
    elif isk < 10000000.0: pip = 1000.0  # 9999000 -> 1000
    elif isk < 100000000.0: pip = 10000.0  # ...
    elif isk < 1000000000.0: pip = 100000.0
    elif isk < 10000000000.0: pip = 1000000.0
    elif isk < 100000000000.0: pip = 10000000.0
    elif isk < 1000000000000.0: pip = 100000000.0
    elif isk < 10000000000000.0: pip = 1000000000.0
    else: assert 0
    return eve_ceiling(isk + pip * points)


class QMarketOrder:
    def __init__(self, order_dict):
        self.min_volume: int = order_dict['min_volume']
        self.price: float = order_dict['price']
        self.volume_remain: int = order_dict['volume_remain']


class QMarketOrders:
    class Orders:
        def __init__(self):
            self.sell: typing.List[QMarketOrder] = []
            self.buy: typing.List[QMarketOrder] = []

        @property
        def min_sell_order(self) -> typing.Optional[QMarketOrder]:
            if not self.sell:
                return None
            return self.sell[0]

        @property
        def max_buy_order(self) -> typing.Optional[QMarketOrder]:
            if not self.buy:
                return None
            return self.buy[0]

    def __init__(self, location_id: int):
        self.__location_id: int = location_id
        # type_id, buy_orders, sell_orders
        self.__market_orders: typing.Dict[int, QMarketOrders.Orders] = {}

    @staticmethod
    def region_the_forge_id() -> int:
        # 10000002=The Forge region
        return 10000002

    @staticmethod
    def location_jita4_4_id() -> int:
        # 60003760: "Jita IV - Moon 4 - Caldari Navy Assembly Plant"
        return 60003760

    @property
    def location_id(self) -> int:
        return self.__location_id

    def get_orders(self, type_id: int) -> typing.Optional[Orders]:
        orders: typing.Optional[QMarketOrders.Orders] = self.__market_orders.get(type_id)
        return orders

    def get_buy_orders(self, type_id: int) -> typing.Optional[typing.List[QMarketOrder]]:
        orders: typing.Optional[QMarketOrders.Orders] = self.__market_orders.get(type_id)
        if not orders:
            return None
        else:
            return orders.buy

    def get_sell_orders(self, type_id: int) -> typing.Optional[typing.List[QMarketOrder]]:
        orders: typing.Optional[QMarketOrders.Orders] = self.__market_orders.get(type_id)
        if not orders:
            return None
        else:
            return orders.sell

    def get_min_sell_order(self, type_id: int) -> typing.Optional[QMarketOrder]:
        orders: typing.Optional[QMarketOrders.Orders] = self.__market_orders.get(type_id)
        if not orders or not orders.sell:
            return None
        return orders.sell[0]

    def get_max_buy_order(self, type_id: int) -> typing.Optional[QMarketOrder]:
        orders: typing.Optional[QMarketOrders.Orders] = self.__market_orders.get(type_id)
        if not orders or not orders.buy:
            return None
        return orders.buy[0]

    def load_orders(self, eve_orders_data) -> int:
        num_orders: int = 0
        for o in eve_orders_data:
            if o['location_id'] == self.__location_id:
                num_orders += 1
                type_id: int = o['type_id']
                orders: typing.Optional[QMarketOrders.Orders] = self.__market_orders.get(type_id)
                if not orders:
                    orders = QMarketOrders.Orders()
                    self.__market_orders[type_id] = orders
                if o['is_buy_order']:
                    orders.buy.append(QMarketOrder(o))
                else:
                    orders.sell.append(QMarketOrder(o))
        for o in self.__market_orders.values():
            # продажу сортируем по возрастанию цены - в топе самая низкая закупочная цена
            o.sell.sort(key=lambda x: x.price)
            # покупку сортируем по убыванию цены - в топе самая высокая закупочная цена
            o.buy.sort(key=lambda x: x.price, reverse=True)
        return num_orders
