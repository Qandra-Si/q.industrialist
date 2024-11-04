""" Router and Conveyor tools and utils
"""
import typing
from enum import Enum
import math
import datetime
import itertools

import eve_efficiency
import postgresql_interface as db


def coalesce(*arg):
  for el in arg:
    if el is not None:
      return el
  return None


# Списки output задают те предметы, которые крафтятся на тех или иных станциях/структурах:
#  * output_market_groups - список номеров market_group_id (предполагается обработка всех вложенных подгрупп)
#  * output_groups - список номеров group_id групп
#  * output_categories - список номеров category_id категорий
#  * output_types - индивидуальный список type_id предметов, которые добавляются к спискам output
#  * except_output_types - индивидуальный список type_id предметов, которые удаляются из списка output
# перекомпоновка output_types, output_market_groups, output_groups и except_output_types в set(output)
def combine_router_outputs(routes, sde_groups, sde_type_ids, sde_market_groups):
    # см. аналогичную реализацию в db_swagger_dictionary.get_type_ids_by_params
    for r in routes:
        r['output'] = r.get('output_types', [])
        gg: typing.Set[int] = set()
        mg: typing.Set[int] = set()
        if r.get('output_groups'):
            gg = set(r['output_groups'])
        if r.get('output_categories'):
            cc: typing.Set[int] = set(r['output_categories'])
            gg |= set([int(_[0]) for _ in sde_groups.items() if _[1].get('categoryID', -1) in cc])
        if r.get('output_market_groups'):
            mg: typing.Set[int] = set(r['output_market_groups'])
            while True:
                mgg: typing.Set[int] = set([int(_[0]) for _ in sde_market_groups.items() if _[1].get('parentGroupID', -1) in mg])
                if not mgg - mg: break
                mg |= mgg
        if gg or mg:
            r['output'].extend([int(_[0]) for _ in sde_type_ids.items() if _[1].get('groupID', -1) in gg or \
                                                                           _[1].get('marketGroupID', -1) in mg])
        if r.get('except_output_types'):
            r['output'] = set(r['output']) - set(r['except_output_types'])
        else:
            r['output'] = set(r['output'])


class RouterSettings:
    def __init__(self):
        # параметры работы конвейера
        self.station: str = ''
        self.desc: str = ''
        # список type_id продуктов текущего router-а
        self.output: typing.List[int] = []
        self.cached_output: typing.Dict[int, db.QSwaggerTypeId] = {}


class ConveyorSettings: pass  # forward declaration
class ConveyorDictionary: pass  # forward declaration
class ConveyorIndustryAnalysis: pass  # forward declaration
class ConveyorManufacturingProductAnalysis: pass  # forward declaration


class ConveyorSettingsContainer:
    def __init__(self,
                 settings: ConveyorSettings,
                 corporation: db.QSwaggerCorporation,
                 container: db.QSwaggerCorporationAssetsItem):
        self.settings: ConveyorSettings = settings
        self.corporation: db.QSwaggerCorporation = corporation
        self.container: db.QSwaggerCorporationAssetsItem = container
        self.station_id: typing.Optional[int] = container.station_id

    @property
    def container_id(self) -> int:
        return self.container.item_id

    @property
    def container_name(self) -> str:
        return self.container.name


class ConveyorSettingsPriorityContainer(ConveyorSettingsContainer):
    def __init__(self,
                 priority: int,
                 settings: ConveyorSettings,
                 corporation: db.QSwaggerCorporation,
                 container: db.QSwaggerCorporationAssetsItem):
        super().__init__(settings, corporation, container)
        self.priority: int = priority


class ConveyorSettingsSaleContainer(ConveyorSettingsContainer):
    def __init__(self,
                 settings: ConveyorSettings,
                 trade_corporation: db.QSwaggerCorporation,
                 container: db.QSwaggerCorporationAssetsItem):
        super().__init__(settings, trade_corporation, container)
        self.trade_corporation: db.QSwaggerCorporation = trade_corporation


class ConveyorPlace(Enum):
    STOCK = 0  # сток конвейера
    CONVEYOR = 1  # место, где лежат чертежи конвейера
    OUTPUT = 2  # выход конвейера
    ADDITIONAL_BLUEPRINTS = 3  # место, где лежат дополнительные чертежи конвейера
    REACT_FORMULAS = 4  # коробки с формулами реакций (аналог additional_blueprints, но на других станциях)
    SALE_STOCK = 5  # коробки с продуктами на продажу (аналог output, но уже рассортированный)
    EXCLUDE = 6  # коробки с предметами игроков, и иные запреты анализа коробок конвейером
    OTHER = 7  # все прочие места, где этот предмет встречается (м.б. карго кораблей и т.п.)


T = typing.TypeVar('T')


class ConveyorPlaces(typing.Generic[T]):
    def __init__(self) -> None:
        self.stock: typing.Dict[int, typing.List[T]] = {}
        self.conveyor: typing.Dict[int, typing.List[T]] = {}
        self.output: typing.Dict[int, typing.List[T]] = {}
        self.additional_blueprints: typing.Dict[int, typing.List[T]] = {}
        self.react_formulas: typing.Dict[int, typing.List[T]] = {}
        self.sale_stock: typing.Dict[int, typing.List[T]] = {}
        self.exclude: typing.Dict[int, typing.List[T]] = {}
        self.other: typing.Dict[int, typing.List[T]] = {}

    def get_with_unique_items(
            self,
            type_id: int,
            places: typing.List[ConveyorPlace],
            station_id: typing.Optional[int] = None) -> typing.List[T]:
        res: typing.List[T] = []
        ids: typing.Set[int] = set()

        def push(elem: T) -> None:
            key_val: int = elem.item_id  # getattr(elem, attr_name)
            if key_val not in ids:
                ids.add(key_val)
                res.append(elem)

        def find(x: typing.Dict[int, typing.List[T]]) -> None:
            for _ in x.get(type_id, []):
                if station_id is not None and _.station_id != station_id: continue
                push(_)

        if ConveyorPlace.STOCK in places:
            find(self.stock)
        if ConveyorPlace.CONVEYOR in places:
            find(self.conveyor)
        if ConveyorPlace.OUTPUT in places:
            find(self.output)
        if ConveyorPlace.ADDITIONAL_BLUEPRINTS in places:
            find(self.additional_blueprints)
        if ConveyorPlace.REACT_FORMULAS in places:
            find(self.react_formulas)
        if ConveyorPlace.SALE_STOCK in places:
            find(self.sale_stock)
        if ConveyorPlace.EXCLUDE in places:
            find(self.exclude)
        if ConveyorPlace.OTHER in places:
            find(self.other)
        return res


class ConveyorJobPlace(Enum):
    BLUEPRINT = 1  # место, где лежал запущенный чертёж
    OUTPUT = 2  # выход производственной работы
    EXCLUDE = 3  # коробки с предметами игроков, и иные запреты анализа коробок конвейером
    OTHER = 4  # все прочие места, куда предмет производится (м.б. ненастроенные названия коробок)


class ConveyorJobPlaces:
    class Data:
        def __init__(self):
            self.blueprint: typing.Dict[int, typing.List[db.QSwaggerCorporationIndustryJob]] = {}
            self.output: typing.Dict[int, typing.List[db.QSwaggerCorporationIndustryJob]] = {}
            self.exclude: typing.Dict[int, typing.List[db.QSwaggerCorporationIndustryJob]] = {}
            self.other: typing.Dict[int, typing.List[db.QSwaggerCorporationIndustryJob]] = {}

    def __init__(self) -> None:
        self.by_blueprints = ConveyorJobPlaces.Data()
        self.by_products = ConveyorJobPlaces.Data()

    def get_with_unique_items(
            self,
            blueprint_type_id: typing.Optional[int],
            product_type_id: typing.Optional[int],
            places: typing.List[ConveyorJobPlace],
            activity: typing.Optional[db.QSwaggerActivityCode] = None,
            facility_id: typing.Optional[int] = None) -> typing.List[db.QSwaggerCorporationIndustryJob]:
        res: typing.List[db.QSwaggerCorporationIndustryJob] = []
        ids: typing.Set[int] = set()

        def push(elem: T) -> None:
            key_val: int = elem.job_id
            if key_val not in ids:
                ids.add(key_val)
                res.append(elem)

        def find(x: typing.Dict[int, typing.List[db.QSwaggerCorporationIndustryJob]],
                 y: typing.Dict[int, typing.List[db.QSwaggerCorporationIndustryJob]]) -> None:
            if blueprint_type_id is not None:
                for _ in x.get(blueprint_type_id, []):
                    if facility_id is not None and _.facility_id != facility_id: continue
                    if activity is not None and _.activity != activity: continue
                    push(_)
            if product_type_id is not None:
                for _ in y.get(product_type_id, []):
                    if facility_id is not None and _.facility_id != facility_id: continue
                    if activity is not None and _.activity != activity: continue
                    push(_)

        if ConveyorJobPlace.BLUEPRINT in places:
            find(self.by_blueprints.blueprint, self.by_products.blueprint)
        if ConveyorJobPlace.OUTPUT in places:
            find(self.by_blueprints.output, self.by_products.output)
        if ConveyorJobPlace.EXCLUDE in places:
            find(self.by_blueprints.exclude, self.by_products.exclude)
        if ConveyorJobPlace.OTHER in places:
            find(self.by_blueprints.other, self.by_products.other)
        return res


class ConveyorOrderPlace(Enum):
    SELL = 0  # ордер на продажу
    BUY = 1  # ордер на закупку


class ConveyorOrderPlaces:
    def __init__(self) -> None:
        self.sell: typing.Dict[int, typing.List[db.QSwaggerCorporationOrder]] = {}
        self.buy: typing.Dict[int, typing.List[db.QSwaggerCorporationOrder]] = {}

    def get_with_unique_items(
            self,
            type_id: int,
            places: typing.List[ConveyorOrderPlace],
            market_id: typing.Optional[int] = None) -> typing.List[db.QSwaggerCorporationOrder]:
        res: typing.List[db.QSwaggerCorporationOrder] = []
        ids: typing.Set[int] = set()

        def push(elem: db.QSwaggerCorporationOrder) -> None:
            key_val: int = elem.order_id
            if key_val not in ids:
                ids.add(key_val)
                res.append(elem)

        def find(x: typing.Dict[int, typing.List[db.QSwaggerCorporationOrder]]) -> None:
            for _ in x.get(type_id, []):
                if market_id is not None and _.location_id != market_id: continue
                push(_)

        if ConveyorOrderPlace.SELL in places:
            find(self.sell)
        if ConveyorOrderPlace.BUY in places:
            find(self.buy)
        return res


class ConveyorSettings:
    def __init__(self, corporation: db.QSwaggerCorporation):
        # параметры работы конвейера
        self.corporation: db.QSwaggerCorporation = corporation
        self.fixed_number_of_runs: typing.Optional[int] = None
        self.same_stock_container: bool = False
        self.activities: typing.List[db.QSwaggerActivityCode] = [db.QSwaggerActivityCode.MANUFACTURING]
        self.conveyor_with_reactions: bool = False
        # контейнеры с чертежами, со стоком, с формулами, исключённых из поиска и т.п.
        self.containers_sources: typing.List[ConveyorSettingsPriorityContainer] = []  # station:container:priority
        self.containers_stocks: typing.List[ConveyorSettingsContainer] = []  # station:container
        self.containers_output: typing.List[ConveyorSettingsContainer] = []  # station:container
        self.containers_additional_blueprints: typing.List[ConveyorSettingsContainer] = []  # station:container
        self.containers_react_formulas: typing.List[ConveyorSettingsContainer] = []  # station:container
        self.containers_exclude: typing.List[ConveyorSettingsContainer] = []  # station:container
        # параметры поведения конвейера (связь с торговой деятельностью, влияние её поведения на работу производства)
        self.trade_corporations: typing.List[db.QSwaggerCorporation] = []
        self.containers_sale_stocks: typing.List[ConveyorSettingsSaleContainer] = []  # station:container:trade_corporation
        # параметры поведения конвейера (расчёт копирки)
        self.calculate_requirements: bool = False
        self.requirements_sold_threshold: float = 0.2
        # идентификаторы контейнеров с чертежами, со стоком, с формулами, исключённых из поиска и т.п.
        self.sources_locations: typing.Set[int] = set()
        self.stocks_locations: typing.Set[int] = set()
        self.output_locations: typing.Set[int] = set()
        self.additional_blueprints_locations: typing.Set[int] = set()
        self.react_formulas_locations: typing.Set[int] = set()
        self.exclude_locations: typing.Set[int] = set()
        self.sale_stocks_locations: typing.Set[int] = set()
        # индексированные по типам предметов набора данных
        self.assets = ConveyorPlaces[db.QSwaggerCorporationAssetsItem]()
        self.blueprints = ConveyorPlaces[db.QSwaggerCorporationBlueprint]()
        self.industry_jobs = ConveyorJobPlaces()
        self.orders = ConveyorOrderPlaces()

    @staticmethod
    def __separate(x: typing.Dict[int, typing.List[typing.Any]], type_id: int, elem: typing.Any):
        in_cache: typing.List[typing.Any] = x.get(type_id)
        if not in_cache:
            x[type_id] = [elem]
        else:
            in_cache.append(elem)

    def recalc_container_locations(self):
        self.sources_locations = set([_.container_id for _ in self.containers_sources])
        self.stocks_locations = set([_.container_id for _ in self.containers_stocks])
        self.output_locations = set([_.container_id for _ in self.containers_output])
        self.additional_blueprints_locations = set([_.container_id for _ in self.containers_additional_blueprints])
        self.react_formulas_locations = set([_.container_id for _ in self.containers_react_formulas])
        self.exclude_locations = set([_.container_id for _ in self.containers_exclude])
        self.sale_stocks_locations = set([_.container_id for _ in self.containers_sale_stocks])
        # ---
        self.separate_assets()
        self.separate_blueprints()
        self.separate_industry_jobs()
        self.separate_orders()

    def separate_assets(self):
        for a in self.corporation.assets.values():
            found: bool = False
            if a.location_id in self.stocks_locations:
                self.__separate(self.assets.stock, a.type_id, a)
                found = True
            if a.location_id in self.sources_locations:
                self.__separate(self.assets.conveyor, a.type_id, a)
                found = True
            if a.location_id in self.output_locations:
                self.__separate(self.assets.output, a.type_id, a)
                found = True
            if a.location_id in self.additional_blueprints_locations:
                self.__separate(self.assets.additional_blueprints, a.type_id, a)
                found = True
            if a.location_id in self.react_formulas_locations:
                self.__separate(self.assets.react_formulas, a.type_id, a)
                found = True
            if a.location_id in self.sale_stocks_locations:
                self.__separate(self.assets.sale_stock, a.type_id, a)
                found = True
            if not found:
                self.__separate(self.assets.other, a.type_id, a)

    def separate_blueprints(self):
        for b in self.corporation.blueprints.values():
            found: bool = False
            if b.location_id in self.stocks_locations:
                self.__separate(self.blueprints.stock, b.type_id, b)
                found = True
            if b.location_id in self.sources_locations:
                self.__separate(self.blueprints.conveyor, b.type_id, b)
                found = True
            if b.location_id in self.output_locations:
                self.__separate(self.blueprints.output, b.type_id, b)
                found = True
            if b.location_id in self.additional_blueprints_locations:
                self.__separate(self.blueprints.additional_blueprints, b.type_id, b)
                found = True
            if b.location_id in self.react_formulas_locations:
                self.__separate(self.blueprints.react_formulas, b.type_id, b)
                found = True
            if b.location_id in self.sale_stocks_locations:
                self.__separate(self.blueprints.sale_stock, b.type_id, b)
                found = True
            if not found:
                self.__separate(self.blueprints.other, b.type_id, b)

    def separate_industry_jobs(self):
        for j in self.corporation.industry_jobs_active.values():
            found: bool = False
            # информации о стоке нет (пропускаем)
            # if j.blueprint_location_id in self.stocks_locations:
            #     self.__separate(self.job_products.stock, j.product_type_id, j)
            if j.blueprint_location_id in self.sources_locations or \
               j.blueprint_location_id in self.additional_blueprints_locations or \
               j.blueprint_location_id in self.react_formulas_locations:
                self.__separate(self.industry_jobs.by_products.blueprint, j.product_type_id, j)
                self.__separate(self.industry_jobs.by_blueprints.blueprint, j.blueprint_type_id, j)
                found = True
            if j.output_location_id in self.output_locations or \
               j.output_location_id in self.sale_stocks_locations:
                self.__separate(self.industry_jobs.by_products.output, j.product_type_id, j)
                self.__separate(self.industry_jobs.by_blueprints.output, j.blueprint_type_id, j)
                found = True
            if not found:
                self.__separate(self.industry_jobs.by_products.other, j.product_type_id, j)
                self.__separate(self.industry_jobs.by_blueprints.other, j.blueprint_type_id, j)

    def separate_orders(self):
        for corporation in self.trade_corporations:
            for o in corporation.orders.values():
                if o.is_buy_order:
                    self.__separate(self.orders.buy, o.type_id, o)
                else:
                    self.__separate(self.orders.sell, o.type_id, o)


def get_blueprints_grouped_by(
        blueprints: typing.List[db.QSwaggerCorporationBlueprint],
        group_by_type_id: bool = True,
        group_by_station: bool = True,
        group_by_me: bool = True,
        group_by_te: bool = False,
        group_by_runs: bool = True) \
        -> typing.Dict[typing.Tuple[int, int, int, int, int], typing.List[db.QSwaggerCorporationBlueprint]]:
    grouped: typing.Dict[typing.Tuple[int, int, int, int, int], typing.List[db.QSwaggerCorporationBlueprint]] = {}
    for b in blueprints:
        type_id: int = b.type_id if group_by_type_id else 0
        station_id: int = b.station_id if group_by_station else 0
        me: int = b.material_efficiency if group_by_me else -1
        te: int = b.time_efficiency if group_by_te else -1
        runs: int = b.runs if group_by_runs else -10
        key: typing.Tuple[int, int, int, int, int] = type_id, station_id, me, te, runs
        g0: typing.List[db.QSwaggerCorporationBlueprint] = grouped.get(key)
        if not g0:
            grouped[key] = []
            g0 = grouped.get(key)
        g0.append(b)
    return grouped


def get_asset_items_grouped_by(
        asset_items: typing.List[db.QSwaggerCorporationAssetsItem],
        group_by_type_id: bool = True,
        group_by_station: bool = True) \
        -> typing.Dict[typing.Tuple[int, int], typing.List[db.QSwaggerCorporationAssetsItem]]:
    grouped: typing.Dict[typing.Tuple[int, int], typing.List[db.QSwaggerCorporationAssetsItem]] = {}
    for b in asset_items:
        type_id: int = b.type_id if group_by_type_id else 0
        station_id: int = b.station_id if group_by_station else 0
        key: typing.Tuple[int, int] = type_id, station_id
        g0: typing.List[db.QSwaggerCorporationAssetsItem] = grouped.get(key)
        if not g0:
            grouped[key] = []
            g0 = grouped.get(key)
        g0.append(b)
    return grouped


def get_jobs_grouped_by(
        jobs: typing.List[db.QSwaggerCorporationIndustryJob],
        group_by_product: bool = True,
        group_by_activity: bool = False) \
        -> typing.Dict[typing.Tuple[int, int], typing.List[db.QSwaggerCorporationIndustryJob]]:
    grouped: typing.Dict[typing.Tuple[int, int], typing.List[db.QSwaggerCorporationIndustryJob]] = {}
    for j in jobs:
        product_type_id: int = j.product_type_id if group_by_product else 0
        activity: int = j.activity.to_int() if group_by_activity else 0
        key: typing.Tuple[int, int] = product_type_id, activity
        g0: typing.List[db.QSwaggerCorporationIndustryJob] = grouped.get(key)
        if not g0:
            grouped[key] = []
            g0 = grouped.get(key)
        g0.append(j)
    return grouped


def get_product_quantity(
        activity_id: int,
        product_type_id: int,
        blueprint: db.QSwaggerBlueprint) -> typing.Optional[int]:
    activity = blueprint.get_activity(activity_id=activity_id)
    if activity is None:  # новый тип чертежа, которого ещё нет в БД
        return None
    if db.QSwaggerActivityCode.MANUFACTURING.to_int() == activity_id:
        manufacturing: db.QSwaggerBlueprintManufacturing = activity
        return manufacturing.quantity
    elif db.QSwaggerActivityCode.INVENTION.to_int() == activity_id:
        invention: db.QSwaggerBlueprintInvention = activity
        return next((p.quantity for p in invention.products if p.product_id == product_type_id), 1)
    elif db.QSwaggerActivityCode.COPYING.to_int() == activity_id:
        return 1  # copying: db.QSwaggerBlueprintCopying = activity
    elif db.QSwaggerActivityCode.RESEARCH_MATERIAL.to_int() == activity_id:
        return 1  # research_material: db.QSwaggerBlueprintResearchMaterial = activity
    elif db.QSwaggerActivityCode.RESEARCH_TIME.to_int() == activity_id:
        return 1  # research_time: db.QSwaggerBlueprintResearchTime = activity
    elif db.QSwaggerActivityCode.REACTION.to_int() == activity_id:
        reaction: db.QSwaggerBlueprintReaction = activity
        return reaction.quantity


class DecryptorCode(Enum):
    ACCELERANT = 34201
    ATTAINMENT = 34202
    AUGMENTATION = 34203
    OPTIMIZED_ATTAINMENT = 34207
    OPTIMIZED_AUGMENTATION = 34208
    PARITY = 34204
    PROCESS = 34205
    SYMMETRY = 34206

    def to_int(self) -> int:
        return int(self.value)

    @staticmethod
    def from_decryptor(decryptor_type: db.QSwaggerTypeId):
        if decryptor_type.type_id == 34201:
            return DecryptorCode.ACCELERANT
        elif decryptor_type.type_id == 34202:
            return DecryptorCode.ATTAINMENT
        elif decryptor_type.type_id == 34203:
            return DecryptorCode.AUGMENTATION
        elif decryptor_type.type_id == 34207:
            return DecryptorCode.OPTIMIZED_ATTAINMENT
        elif decryptor_type.type_id == 34208:
            return DecryptorCode.OPTIMIZED_AUGMENTATION
        elif decryptor_type.type_id == 34204:
            return DecryptorCode.PARITY
        elif decryptor_type.type_id == 34205:
            return DecryptorCode.PROCESS
        elif decryptor_type.type_id == 34206:
            return DecryptorCode.SYMMETRY
        else:
            raise Exception("Unknown decryptor")


class DecryptorDetails:
    def __init__(self, decryptor_type: db.QSwaggerTypeId):
        self.__code: DecryptorCode = DecryptorCode.from_decryptor(decryptor_type)
        self.__type: db.QSwaggerTypeId = decryptor_type
        self.__probability: float = 0.0  # вероятность успеха
        self.__runs: int = 0  # число прогонов проекта
        self.__material: float = 0.0  # экономия материалов при производстве
        self.__time: float = 0.0  # экономия времени производства

        if self.__code == DecryptorCode.ACCELERANT:  # Accelerant Decryptor
            self.__probability: float = +0.20  # +20%
            self.__runs: int = +1  # +1 прогона
            self.__material: float = -0.02  # +2%
            self.__time: float = +0.10  # +10%
        elif self.__code == DecryptorCode.ATTAINMENT:  # Attainment Decryptor
            self.__probability: float = +0.80  # +80%
            self.__runs: int = +4  # +4 прогона
            self.__material: float = -0.01  # -1%
            self.__time: float = +0.04  # +4%
        elif self.__code == DecryptorCode.AUGMENTATION:  # Augmentation Decryptor
            self.__probability: float = -0.40  # -40%
            self.__runs: int = +9  # +9 прогона
            self.__material: float = -0.02  # -2%
            self.__time: float = +0.02  # +2%
        elif self.__code == DecryptorCode.OPTIMIZED_ATTAINMENT:  # Optimized Attainment Decryptor
            self.__probability: float = +0.90  # +90%
            self.__runs: int = 2  # +2 прогона
            self.__material: float = -0.01  # -1%
            self.__time: float = -0.02  # -2%
        elif self.__code == DecryptorCode.OPTIMIZED_AUGMENTATION:  # Optimized Augmentation Decryptor
            self.__probability: float = -0.10  # -10%
            self.__runs: int = 7  # +7 прогонов
            self.__material: float = +0.02  # +2%
            self.__time: float = 0.00  # 0%
        elif self.__code == DecryptorCode.PARITY:  # Parity Decryptor
            self.__probability: float = +0.50  # +50%
            self.__runs: int = 3  # +3 прогона
            self.__material: float = +0.01  # +1%
            self.__time: float = -0.02  # -2%
        elif self.__code == DecryptorCode.PROCESS:  # Process Decryptor
            self.__probability: float = +0.10  # +10%
            self.__runs: int = 0  # не меняется
            self.__material: float = +0.03  # +3%
            self.__time: float = +0.06  # +6%
        elif self.__code == DecryptorCode.SYMMETRY:  # Symmetry Decryptor
            self.__probability: float = 0.0  # не меняется
            self.__runs: int = +2  # +2 прогона
            self.__material: float = +0.01  # +1%
            self.__time: float = +0.08  # +8%

    @property
    def code(self) -> DecryptorCode:
        return self.__code

    @property
    def type(self) -> db.QSwaggerTypeId:
        return self.__type

    @property
    def probability(self) -> float:
        return self.__probability

    @property
    def runs(self) -> int:
        return self.__runs

    @property
    def material_efficiency(self) -> float:
        return self.__material

    @property
    def time_efficiency(self) -> float:
        return self.__time


def which_decryptor_applies_to_blueprint__static_variant(
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        # продукт для проверки (внимание! чертежи плохо каталогизированы, market-группы часто не заданы,
        # или отсутствуют у T2-чертежей)
        product_type: db.QSwaggerTypeId) -> typing.Optional[typing.Tuple[DecryptorDetails, bool]]:  # bool: required
    decryptor_required: bool = False
    decryptor_type: typing.Optional[db.QSwaggerTypeId] = None
    market_group: typing.Optional[db.QSwaggerMarketGroup] = qid.there_is_market_group_in_chain(
        product_type,
        {4, 1111, 1112, 9})
    if market_group:
        if market_group.group_id == 4:  # Ships (соответствует Ships=204 в чертежах)
            decryptor_type = qid.get_type_id(34201)  # Accelerant Decryptor
        elif market_group.group_id == 1111:  # Rigs (соответствует Ship Modifications=943 в чертежах)
            decryptor_type = qid.get_type_id(34206)  # Symmetry Decryptor
        elif market_group.group_id == 1112:  # Subsystems (соответствует Ship Ancient Relics=1909 в чертежах)
            decryptor_type = qid.get_type_id(34204)  # Parity Decryptor
        elif market_group.group_id == 9:  # Ship Equipment (соответствует Ship Equipment=209 в чертежах)
            # тут только капитальные модули (риги проверены выше)
            if product_type.name[:8] == 'Capital ':
                decryptor_required = True
                decryptor_type = qid.get_type_id(34207)  # Optimized Attainment Decryptor
            elif product_type.group:
                if product_type.group.name == 'Capital' or product_type.group.name == 'Extra Large':
                    decryptor_required = True
                    decryptor_type = qid.get_type_id(34207)  # Optimized Attainment Decryptor
        else:
            raise Exception("This shouldn't have happened")
    if decryptor_type:
        return DecryptorDetails(decryptor_type), decryptor_required
    else:
        return None


def which_decryptor_applies_to_blueprint__formula_variant(
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        # продукт для проверки по спискам conveyor_best_formulas
        product_type: db.QSwaggerTypeId) -> typing.Optional[typing.Tuple[DecryptorDetails, bool]]:  # bool: required
    conveyor_best_formula: typing.Optional[db.QSwaggerConveyorBestFormula] = qid.get_conveyor_best_formula(product_type.type_id)
    # если есть предварительно рассчитанная conveyor-формула, то выбираем именно её (с неё точно всё в порядке, все
    # варианты расчётов можно проверить и убедиться в правильности)
    if conveyor_best_formula:
        decryptor_type: typing.Optional[db.QSwaggerTypeId] = conveyor_best_formula.decryptor_type
        if decryptor_type:
            return DecryptorDetails(decryptor_type), conveyor_best_formula.decryptor_required
        else:
            return None
    # если conveyor-формулы готовой нет, то скорее всего предмет не является Tech II, тогда выбираем декриптор
    # с помощью старого алгоритма (правила принятые в ri4)
    return which_decryptor_applies_to_blueprint__static_variant(qid, product_type)


def which_decryptor_applies_to_blueprint(
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        # продукт для проверки (внимание! чертежи плохо каталогизированы, market-группы часто не заданы,
        # или отсутствуют у T2-чертежей)
        product_type: db.QSwaggerTypeId) -> typing.Optional[typing.Tuple[DecryptorDetails, bool]]:  # bool: required
    # return which_decryptor_applies_to_blueprint__static_variant(qid, product_type)
    return which_decryptor_applies_to_blueprint__formula_variant(qid, product_type)


# blueprints_details: подробности о чертежах этого типа [{"q": -1, "r": -1}, {"q": 2, "r": -1}, {"q": -2, "r": 179}]
# метод возвращает список tuple: [{"id": 11399, "q": 11, "qmin": 11"}] с учётом ME
# при is_blueprint_copy=True tuple={"r":?}, при False tuple={"r":?,"q":?}
# fixed_number_of_runs учитывается только для оригиналов, т.е. для is_blueprint_copy=False
def get_materials_list(
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        # настройки генерации отчёта
        conveyor_settings: ConveyorSettings,
        # список чертежей для которых необходимо рассчитать потребность в материалах
        blueprints: typing.List[db.QSwaggerCorporationBlueprint],
        fixed_number_of_runs: typing.Optional[int] = None) \
        -> typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerOptionalMaterial]]:
    # список материалов по набору чертежей с учётом ME
    materials_list_with_efficiency: typing.Dict[db.QSwaggerActivity, typing.Dict[int, db.QSwaggerOptionalMaterial]] = {}

    def push_into(__a: db.QSwaggerActivity, __m: db.QSwaggerMaterial, __q: int, __o: bool) -> None:
        __in_cache205: typing.Dict[int, db.QSwaggerMaterial] = materials_list_with_efficiency.get(__a)
        if not __in_cache205:
            materials_list_with_efficiency[__a] = {}
            __in_cache205 = materials_list_with_efficiency.get(__a)
        __in_cache209: db.QSwaggerMaterial = __in_cache205.get(__m.material_id)
        if not __in_cache209:
            __in_cache205[__m.material_id] = db.QSwaggerOptionalMaterial(__m.material_type, __q, __o)
        else:
            __in_cache209.increment_quantity(__q)

    # перебираем все активности и все чертежи
    for a in conveyor_settings.activities:
        for b in blueprints:
            activity = b.blueprint_type.get_activity(activity_id=a.to_int())
            if not activity: continue
            # получаем справочную информацию по этому типу чертежа для выбранной активности
            materials: db.QSwaggerActivityMaterials = activity.materials
            if not materials: continue
            # расчёт кол-ва ранов для этого чертежа
            if b.is_copy:
                quantity_of_runs = b.runs
                quantity_of_blueprints = 1
            else:
                quantity_of_blueprints = b.quantity if b.quantity > 0 else 1
                quantity_of_runs = fixed_number_of_runs if fixed_number_of_runs else 1
                # умножение на количество оригиналов будет выполнено позже...
            # перебираем все материалы и считаем кол-во с учётом me
            for m in materials.materials:
                # расчёт кол-ва материала с учётом эффективности производства
                industry_input = eve_efficiency.get_industry_material_efficiency(
                    str(a),
                    quantity_of_runs,
                    m.quantity,  # сведения из чертежа
                    b.material_efficiency)  # сведения из корпоративного чертежа
                # выход готовой продукции с одного запуска по N ранов умножаем на кол-во чертежей
                industry_input *= quantity_of_blueprints
                # сохранение информации в справочник материалов
                push_into(activity, m, industry_input, False)
            # ---
            if a == db.QSwaggerActivityCode.INVENTION:
                # Добавляем декрипторы (замечения и ограничения):
                # - всегда все хулы запускаются с декриптором Accelerant Decryptor
                # - всегда все риги запускаются с декриптором Symmetry Decryptor
                # - всегда все T3 технологии запускаются с декриптором Parity Decryptor
                # - всегда все модули запускаются без декрипторов
                # - для запуска модулей скилы должны быть не меньше 2х, для запуска хулов и риг скилы должны быть
                # в 3 и выше. Если ваши скилы меньше - лучше запускайте ресерч или ждите задач по копирке. Будьте
                # внимательны, игнорируя эти замечения вы сильно усложняете работу производственников.
                invention: db.QSwaggerBlueprintInvention = activity
                # считаем, что какие бы варианты чертежей не инвентились, все они будут одного типа
                product_blueprint_id: int = invention.products[0].product_id
                product_blueprint_type: db.QSwaggerBlueprint = qid.get_blueprint(product_blueprint_id)
                if product_blueprint_type and product_blueprint_type.manufacturing:
                    decryptor_details: typing.Optional[typing.Tuple[DecryptorDetails, bool]] = None
                    if b.blueprint_type.manufacturing:
                        decryptor_details = which_decryptor_applies_to_blueprint(
                            qid,
                            # чертёж: b.blueprint_type.blueprint_type
                            product_blueprint_type.manufacturing.product_type)
                    if decryptor_details is not None:
                        # расчёт кол-ва декрипторов с учётом эффективности производства
                        industry_input = eve_efficiency.get_industry_material_efficiency(
                            str(a),
                            quantity_of_runs,
                            1,  # всегда один декриптор
                            b.material_efficiency)  # сведения из корпоративного чертежа
                        # выход готовой продукции с одного запуска по N ранов умножаем на кол-во чертежей
                        industry_input *= quantity_of_blueprints
                        # сохранение информации в справочник материалов
                        push_into(
                            activity,
                            db.QSwaggerMaterial(decryptor_details[0].type, 0),
                            industry_input,
                            not decryptor_details[1])
    # ---
    result: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerOptionalMaterial]] = {}
    for activity in materials_list_with_efficiency.keys():
        mm: typing.Dict[int, db.QSwaggerOptionalMaterial] = materials_list_with_efficiency.get(activity)
        result[activity] = [m for m in mm.values()]
    return result


class ConveyorCorporationStockMaterials:
    def __init__(self):
        # материалы сгруппированы по станциям, т.е. чтобы получить информацию об имеющемся кол-ве материалов, надо
        # знать идентификатор станции
        self.stock_materials: typing.Dict[int, typing.Dict[int, db.QSwaggerMaterial]] = {}  # station:type_id:material
        self.conveyor_settings: typing.Optional[ConveyorSettings] = None

    def calc(self,
             # данные корпорации для подсчёта кол-ва материалов
             corporation: db.QSwaggerCorporation,
             # настройки генерации отчёта
             conveyor_settings: ConveyorSettings) \
            -> typing.Dict[int, typing.Dict[int, db.QSwaggerMaterial]]:
        del self.stock_materials
        self.conveyor_settings = conveyor_settings
        # проверка правильности входных данных
        if not self.conveyor_settings.corporation.corporation_id == corporation.corporation_id:
            raise Exception("Incompatible conveyor settings and corporation data")
        self.stock_materials: typing.Dict[int, typing.Dict[int, db.QSwaggerMaterial]] = {}
        # перебираем ассеты, ищем материалы
        for type_id, aa in conveyor_settings.assets.stock.items():
            station_ids: typing.Set[int] = set([_.station_id for _ in aa])
            for station_id in station_ids:
                quantity: int = sum([_.quantity for _ in aa if _.station_id == station_id])
                s: typing.Dict[int, db.QSwaggerMaterial] = self.stock_materials.get(station_id)
                if not s:
                    self.stock_materials[station_id] = {}
                    s = self.stock_materials.get(station_id)
                m = s.get(type_id)
                if m:
                    m.increment_quantity(quantity)
                else:
                    s[type_id] = db.QSwaggerMaterial(aa[0].item_type, quantity)
        return self.stock_materials

    class CheckEnoughResult:
        def __init__(self,
                     enough: bool,
                     max_possible: typing.Optional[int],
                     not_available: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerOptionalMaterial]]):
            self.non_decryptors_missing: bool = not enough
            self.decryptors_missing: typing.Optional[bool] = None
            self.decryptors_optional: typing.Optional[bool] = None
            self.max_possible: typing.Optional[int] = max_possible
            self.not_available: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerOptionalMaterial]] = not_available

        @property
        def enough(self):
            if self.non_decryptors_missing:
                return False
            elif self.decryptors_optional is None or self.decryptors_optional:
                return True
            else:
                return False

        @property
        def only_optional_decryptors_missing(self):
            if self.non_decryptors_missing:
                return False
            else:
                return self.decryptors_missing and self.decryptors_optional

    def check_enough_materials_at_station(
            self,
            # идентификатор станции на которой в коробках стока находятся материалы
            station_id: int,
            # материалы в списке не должны дублироваться (их необходимо суммировать до проверки)
            required_materials: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerOptionalMaterial]]) \
            -> CheckEnoughResult:
        available_materials: typing.Dict[int, db.QSwaggerMaterial] = self.stock_materials.get(station_id)
        if not available_materials:
            if not required_materials:
                return ConveyorCorporationStockMaterials.CheckEnoughResult(True, None, {})
            else:
                return ConveyorCorporationStockMaterials.CheckEnoughResult(False, 0, required_materials)

        result: ConveyorCorporationStockMaterials.CheckEnoughResult = \
            ConveyorCorporationStockMaterials.CheckEnoughResult(True, -1, {})

        def push(a338: db.QSwaggerActivity, m338: db.QSwaggerOptionalMaterial, q338: int) -> bool:
            m340: db.QSwaggerOptionalMaterial = db.QSwaggerOptionalMaterial(m338.material_type, q338, m338.optional)
            mm334: typing.List[db.QSwaggerOptionalMaterial] = result.not_available.get(a338)
            if mm334 is None:
                result.not_available[a338] = [m340]
            else:
                mm334.append(m340)
            is_decryptor: bool = m338.material_type.market_group_id == 1873
            if is_decryptor:
                result.decryptors_missing = True
                result.decryptors_optional = m340.optional
            else:
                result.non_decryptors_missing = True
            return is_decryptor

        for activity, materials in required_materials.items():
            for r in materials:
                # получаем материал в стоке
                a = available_materials.get(r.material_id)
                # определяем, достаточно ли имеющегося кол-ва материалов?
                if not a:
                    if push(activity, r, r.quantity):
                        # отсутствие декрипторов не мешает запуску работы
                        continue
                    else:
                        result.max_possible = 0
                elif a.quantity < r.quantity:
                    if push(activity, r, r.quantity - a.quantity):
                        # отсутствие декрипторов не мешает запуску работы
                        continue
                    else:
                        result.max_possible = 0
                # определяем максимально возможное кол-во производственных запусков для этого списка потребностей
                if result.max_possible in (0, 1):
                    pass
                elif result.max_possible < 0:
                    result.max_possible = a.quantity // r.quantity
                else:
                    result.max_possible = min(result.max_possible, a.quantity // r.quantity)
        return result

    def check_enough_materials_everywhere(
            self,
            # материалы в списке не должны дублироваться (их необходимо суммировать до проверки)
            required_materials: typing.List[db.QSwaggerMaterial]) -> bool:
        for r in required_materials:
            required_quantity: int = r.quantity
            for station_id in self.stock_materials.keys():
                available_materials: typing.Dict[int, db.QSwaggerMaterial] = self.stock_materials.get(station_id)
                a = available_materials.get(r.material_id)
                if not a: continue
                required_quantity -= a.quantity
                if required_quantity <= 0: break
            if required_quantity > 0:
                return False
        return True


def calc_available_materials(conveyor_settings: typing.List[ConveyorSettings]) \
        -> typing.Dict[ConveyorSettings, ConveyorCorporationStockMaterials]:
    # считаем количество доступных материалов в стоках выбранных конвейеров
    available_materials: typing.Dict[ConveyorSettings, ConveyorCorporationStockMaterials] = {}
    for s in conveyor_settings:
        a: ConveyorCorporationStockMaterials = ConveyorCorporationStockMaterials()
        a.calc(s.corporation, s)
        available_materials[s] = a
    return available_materials


class ConveyorMaterialRequirements:
    class StackOfBlueprints:
        def __init__(self, name: str, station_id: int, runs: int, me: int, te: int, group: typing.List[db.QSwaggerCorporationBlueprint]):
            self.name: str = name
            self.station_id: int = station_id
            self.runs: int = runs
            self.me: int = me
            self.te: int = te
            self.group: typing.List[db.QSwaggerCorporationBlueprint] = group
            self.max_possible_for_single: int = 0
            self.required_materials_for_single: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerOptionalMaterial]] = {}
            self.run_possible: bool = False
            self.only_optional_decryptors_missing_for_stack: bool = True
            self.required_materials_for_stack: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerOptionalMaterial]] = {}
            self.not_available_materials_for_stack: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerOptionalMaterial]] = {}
            self.conveyor_formula: typing.Optional[db.QSwaggerConveyorFormula] = None

        @property
        def is_unprofitable(self) -> typing.Optional[bool]:
            if self.conveyor_formula and self.conveyor_formula.single_product_profit is not None:
                return self.conveyor_formula.single_product_profit < 0.01
            return None

        def apply_materials_info(self,
                                 materials_for_single: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerOptionalMaterial]],
                                 enough_for_single: ConveyorCorporationStockMaterials.CheckEnoughResult,
                                 materials_for_stack: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerOptionalMaterial]],
                                 enough_for_stack: ConveyorCorporationStockMaterials.CheckEnoughResult):
            del self.required_materials_for_single
            del self.required_materials_for_stack
            del self.not_available_materials_for_stack
            # ---
            self.max_possible_for_single = enough_for_single.max_possible
            self.required_materials_for_single = materials_for_single
            # ---
            self.run_possible = enough_for_single.enough
            self.only_optional_decryptors_missing_for_stack = enough_for_stack.only_optional_decryptors_missing
            self.required_materials_for_stack = materials_for_stack
            self.not_available_materials_for_stack = enough_for_stack.not_available

    def __init__(self):
        self.conveyor_settings: typing.Optional[ConveyorSettings] = None
        self.blueprints: typing.List[db.QSwaggerCorporationBlueprint] = []
        self.__grouped: typing.Dict[typing.Tuple[int, int, int, int], typing.List[db.QSwaggerCorporationBlueprint]] = {}
        self.__grouped_and_sorted: typing.List[ConveyorMaterialRequirements.StackOfBlueprints] = []

    def calc(
            self,
            # данные (справочники)
            qid: db.QSwaggerDictionary,
            # анализ чертежей на предмет перепроизводства и нерентабельности
            industry_analysis: ConveyorIndustryAnalysis,
            # настройки генерации отчёта
            conveyor_settings: ConveyorSettings,
            # ассеты стока (материалы для расчёта возможностей и потребностей конвейера
            available_materials: ConveyorCorporationStockMaterials,
            # список чертежей, которые необходимо обработать
            ready_blueprints: typing.List[db.QSwaggerCorporationBlueprint]) \
            -> typing.List[StackOfBlueprints]:
        del self.__grouped_and_sorted
        del self.__grouped
        del self.blueprints
        # входной набор чертежей для проверки потребностей в материалах
        self.blueprints: typing.List[db.QSwaggerCorporationBlueprint] = ready_blueprints
        # группируем чертежи по типу, me и runs кодам, чтобы получить уникальные сочетания с количествами
        self.__grouped: typing.Dict[typing.Tuple[int, int, int, int, int], typing.List[db.QSwaggerCorporationBlueprint]] = \
            get_blueprints_grouped_by(  # type_id:station:me:te:runs
                self.blueprints,
                group_by_type_id=True,
                group_by_station=True,
                group_by_me=True,
                group_by_te=True,
                group_by_runs=True)
        # сортируем уже сгруппированные чертежи
        self.__grouped_and_sorted: typing.List[ConveyorMaterialRequirements.StackOfBlueprints] = []
        for key in self.__grouped.keys():
            group: typing.List[db.QSwaggerCorporationBlueprint] = self.__grouped.get(key)
            self.__grouped_and_sorted.append(
                ConveyorMaterialRequirements.StackOfBlueprints(
                    group[0].blueprint_type.blueprint_type.name,
                    group[0].station_id,
                    group[0].runs,
                    group[0].material_efficiency,
                    group[0].time_efficiency,
                    group))
        self.__grouped_and_sorted.sort(key=lambda x: (x.name, x.runs, -x.me))  # name:runs:me (длительность произв.)
        # рассчитываем потребности в материалах
        # все чертежи собраны в стеки по одному типу название:длительность_производства (name:runs:me)
        for stack in self.__grouped_and_sorted:
            b0: db.QSwaggerCorporationBlueprint = stack.group[0]
            """
            print(f"{b0.blueprint_type.blueprint_type.name} ({b0.type_id})"
                  f" x{len(stack.group)}"
                  f" {b0.material_efficiency}me"
                  f" {b0.runs}runs"
                  f" at {b0.station_id}"
                  # f"\n{[_.item_id for _ in stack.group]}"
                  "\n")
            """
            # вычисляем минимально необходимое кол-во материалов для работ хотя-бы по одному чертежу
            materials_single: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerOptionalMaterial]] = \
                get_materials_list(
                    qid,
                    conveyor_settings,
                    [b0],
                    conveyor_settings.fixed_number_of_runs)
            # считаем общее количество материалов для работ по стеку чертежей
            materials_stack: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerOptionalMaterial]] = \
                get_materials_list(
                    qid,
                    conveyor_settings,
                    stack.group,
                    conveyor_settings.fixed_number_of_runs)
            # проверка доступности материалов имеющихся в стоке
            enough_for_single: ConveyorCorporationStockMaterials.CheckEnoughResult = \
                available_materials.check_enough_materials_at_station(b0.station_id, materials_single)
            enough_for_stack: ConveyorCorporationStockMaterials.CheckEnoughResult = \
                available_materials.check_enough_materials_at_station(b0.station_id, materials_stack)
            # сохранение результатов расчёта в стеке чертежей
            stack.apply_materials_info(materials_single, enough_for_single, materials_stack, enough_for_stack)
            # получение conveyor-формул для проверки профитности/нерентабельности производства
            if b0.is_copy:
                manufacturing_analysis: typing.Optional[ConveyorManufacturingProductAnalysis] = \
                    industry_analysis.manufacturing_analysis.get(b0.type_id)
                if manufacturing_analysis and manufacturing_analysis.product and manufacturing_analysis.product.product_tier1:
                    stack.conveyor_formula = manufacturing_analysis.product.get_manufacturing_conveyor_formula(
                        60003760,  # Jita trade hub id
                        b0.type_id,
                        b0.runs,  # валидно только при b0.is_copy==True
                        b0.material_efficiency,
                        b0.time_efficiency)
        return self.__grouped_and_sorted


def calc_corp_conveyor(
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        # анализ чертежей на предмет перепроизводства и нерентабельности
        industry_analysis: ConveyorIndustryAnalysis,
        # настройки генерации отчёта
        router_settings: typing.List[RouterSettings],
        conveyor_settings: ConveyorSettings,
        # ассеты стока (материалы для расчёта возможностей и потребностей конвейера
        available_materials: ConveyorCorporationStockMaterials,
        # список чертежей, которые нобходимо обработать
        ready_blueprints: typing.List[db.QSwaggerCorporationBlueprint]) \
        -> typing.List[ConveyorMaterialRequirements.StackOfBlueprints]:
    # готовимся к расчёту потребностей для заданного кол-ва чертежей
    requirements: ConveyorMaterialRequirements = ConveyorMaterialRequirements()
    # группируем чертежи по типу, me и runs кодам, чтобы получить уникальные сочетания с количествами
    # рассчитываем потребности в материалах
    # все чертежи собраны в стеки по одному типу название:длительность_производства (name:runs:me)
    grouped_and_sorted: typing.List[ConveyorMaterialRequirements.StackOfBlueprints] = requirements.calc(
        qid,
        industry_analysis,
        conveyor_settings,
        available_materials,
        ready_blueprints
    )
    return grouped_and_sorted


def get_router_details(
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        # настройки генерации отчёта
        router_settings: RouterSettings,
        conveyor_settings: typing.List[ConveyorSettings]) \
        -> typing.Tuple[db.QSwaggerStation, db.QSwaggerCorporation, typing.Set[int], typing.Set[int]]:
    # определяем станцию, корпорацию и стоки конвейера соответствующего роутеру
    station: db.QSwaggerStation = qid.get_station_by_name(router_settings.station)
    if not station:
        raise Exception("Invalid router settings with unknown station")
    station_id: int = station.station_id
    containers_stocks: typing.Set[int] = set()
    containers_output: typing.Set[int] = set()
    corporation: typing.Optional[db.QSwaggerCorporation] = None
    for cs in conveyor_settings:
        for c in cs.containers_stocks:
            if c.station_id == station_id:
                containers_stocks.add(c.container_id)
                if corporation and not corporation == c.corporation:
                    raise Exception(
                        f"There are multiple routes for multiple corporations {corporation.corporation_name} and {c.corporation.corporation_name}")
                corporation = c.corporation
        for c in cs.containers_output:
            if c.station_id == station_id:
                containers_output.add(c.container_id)
                if corporation and not corporation == c.corporation:
                    raise Exception(
                        f"There are multiple routes for multiple corporations {corporation.corporation_name} and {c.corporation.corporation_name}")
                corporation = c.corporation
    if not corporation and conveyor_settings:
        corporation = conveyor_settings[0].corporation  # TODO: костыль (иногда из ассетов пропадают офисы, как быть?)
    if not corporation:
        raise Exception("Invalid router settings without corporation' conveyor settings")
    return station, corporation, containers_stocks, containers_output


class ConveyorRouterAssets:
    def __init__(self):
        self.corporation: typing.Optional[db.QSwaggerCorporation] = None
        self.station: typing.Optional[db.QSwaggerStation] = None
        self.router_settings: typing.Optional[RouterSettings] = None
        self.conveyor_settings: typing.List[ConveyorSettings] = []
        self.activities: typing.Set[db.QSwaggerActivityCode] = set()

    @staticmethod
    def prepare_calc0(
            # данные (справочники)
            qid: db.QSwaggerDictionary,
            # настройки генерации отчёта
            router_settings: RouterSettings,
            conveyor_settings: typing.List[ConveyorSettings]) \
            -> typing.Tuple[typing.Set[db.QSwaggerActivityCode], typing.List[ConveyorSettings]]:
        # надо определиться, является ли конвейер manufacturing или reaction
        activities: typing.Set[db.QSwaggerActivityCode] = set()
        if router_settings.output:
            # если список производства задан, то это "внешняя станция" со своими настройками производства
            for b in qid.sde_blueprints.values():
                if b.manufacturing and b.manufacturing.product_id in router_settings.output:
                    activities.add(db.QSwaggerActivityCode.MANUFACTURING)
                if b.reaction and b.reaction.product_id in router_settings.output:
                    activities.add(db.QSwaggerActivityCode.REACTION)
        else:
            # если список производства не задан, то это основная станция на которой производится всё, кроме
            # перечисленного (хотя при наличии чертежей, можно запускать что угодно вообще, и реакции?)
            activities.add(db.QSwaggerActivityCode.MANUFACTURING)
        local_conveyor_settings: typing.List[ConveyorSettings] = []
        for cs in conveyor_settings:
            # также можно проверять: if not _.corporation.corporation_id == corporation.corporation_id: continue
            if db.QSwaggerActivityCode.REACTION in cs.activities:
                if db.QSwaggerActivityCode.REACTION in activities:
                    # local_conveyor_settings.append(cs)
                    # continue
                    # Внимание! это неподдерживаемый способ настройки конвейера
                    pass
            if db.QSwaggerActivityCode.MANUFACTURING in cs.activities:
                if db.QSwaggerActivityCode.MANUFACTURING in activities:
                    local_conveyor_settings.append(cs)
                    continue
                if cs.conveyor_with_reactions and db.QSwaggerActivityCode.REACTION in activities:
                    local_conveyor_settings.append(cs)
                    continue
        if not local_conveyor_settings:
            raise Exception("There is router settings not complementary with conveyor settings")
        return activities, local_conveyor_settings

    def prepare_calc1(
            self,
            # данные (справочники)
            qid: db.QSwaggerDictionary,
            # данные корпорации для подсчёта кол-ва материалов
            corporation: db.QSwaggerCorporation,
            # настройки генерации отчёта
            _conveyor_settings: typing.List[ConveyorSettings],
            _router_settings: RouterSettings,
            # список активностей, которые выполняются для получения продуктов роутера
            _activities: typing.Set[db.QSwaggerActivityCode]) \
            -> typing.Tuple[db.QSwaggerStation, db.QSwaggerCorporation, typing.Set[int], typing.Set[int]]:
        del self.activities
        del self.conveyor_settings
        # ---
        self.corporation: db.QSwaggerCorporation = corporation
        self.station: db.QSwaggerStation = None
        self.router_settings: RouterSettings = _router_settings
        self.conveyor_settings: typing.List[ConveyorSettings] = _conveyor_settings[:]
        self.activities: typing.Set[db.QSwaggerActivityCode] = _activities
        # ---
        # проверка правильности входных данных
        if next((_ for _ in self.conveyor_settings
                 if not _.corporation.corporation_id == self.corporation.corporation_id), None) is not None:
            raise Exception("Incompatible conveyor settings and corporation data")
        # определяем станцию, корпорацию и стоки конвейера соответствующего роутеру
        router_details: typing.Tuple[db.QSwaggerStation, db.QSwaggerCorporation, typing.Set[int], typing.Set[int]] = \
            get_router_details(qid, self.router_settings, self.conveyor_settings)
        return router_details

    @staticmethod
    def calc2(
            a: db.QSwaggerCorporationAssetsItem,
            router_settings: RouterSettings,
            station_id: int,
            containers_exclude: typing.Set[int],
            # настраиваемое поведение калькулятора, который компонует список предметов, сортируя их на "в нужной ли он
            # коробке" или "в неправильной"?
            valid_containers: typing.Set[int],
            valid_items: typing.Dict[int, db.QSwaggerTypeId],
            ready_items: typing.Dict[int, db.QSwaggerMaterial],
            lost_items: typing.Dict[int, typing.List[db.QSwaggerCorporationAssetsItem]]):
        if not a.station_id == station_id: return
        if a.location_id in containers_exclude: return
        # проверям "заблудился" ли материал/продукт, или лежит на своём месте?
        type_id: int = a.type_id
        correct_container: bool = a.location_id in valid_containers
        correct_item: bool = True
        # если output не сконфигурирован, то на станции производится вся возможная продукция (кроме тех, что
        # сконфигурированы на других станциях)
        if router_settings.output:
            if type_id not in valid_items:
                correct_item = False
        elif not correct_container:
            return
        # ---
        if not correct_container and not correct_item:
            return
        elif correct_container and correct_item:
            p = ready_items.get(a.type_id)
            if p:
                p.increment_quantity(a.quantity)
            else:
                ready_items[a.type_id] = db.QSwaggerMaterial(a.item_type, a.quantity)
        else:
            p = lost_items.get(a.type_id)
            if p:
                p.append(a)
            else:
                lost_items[a.type_id] = [a]


class ConveyorRouterInputMaterials(ConveyorRouterAssets):
    def __init__(self, index: int):
        super().__init__()
        self.index: int = index
        self.valid_materials: typing.Dict[int, db.QSwaggerTypeId] = {}  # type_id:material
        self.input_materials: typing.Dict[int, db.QSwaggerMaterial] = {}  # type_id:material
        self.lost_materials: typing.Dict[int, typing.List[db.QSwaggerCorporationAssetsItem]] = {}  # type_id:list(assets)

    def calc(self,
             # данные (справочники)
             qid: db.QSwaggerDictionary,
             # данные корпорации для подсчёта кол-ва материалов
             corporation: db.QSwaggerCorporation,
             # настройки генерации отчёта
             conveyor_settings: typing.List[ConveyorSettings],
             router_settings: RouterSettings,
             # список активностей, которые выполняются для получения продуктов роутера
             activities: typing.Set[db.QSwaggerActivityCode]) -> None:
        self.valid_materials: typing.Dict[int, db.QSwaggerTypeId] = {}
        self.input_materials: typing.Dict[int, db.QSwaggerMaterial] = {}
        self.lost_materials: typing.Dict[int, typing.List[db.QSwaggerCorporationAssetsItem]] = {}
        # определяем станцию, корпорацию и стоки конвейера соответствующего роутеру
        router_details: typing.Tuple[db.QSwaggerStation, db.QSwaggerCorporation, typing.Set[int], typing.Set[int]] = \
            self.prepare_calc1(qid, corporation, conveyor_settings, router_settings, activities)
        self.station: db.QSwaggerStation = router_details[0]
        if corporation.corporation_id != router_details[1].corporation_id:
            raise Exception("Something wrong: incompatible corporations for conveyor/router settings")
        containers_stocks: typing.Set[int] = router_details[2]
        # containers_output: typing.Set[int] = router_details[3]
        containers_exclude: typing.Set[int] = set([_.container_id for x in conveyor_settings for _ in x.containers_exclude])
        # если список output сконфигурирован, то имеет место быть станция из настроек router-а
        for product_type_id in router_settings.output:
            product_activities: typing.List[db.QSwaggerActivity] = qid.get_activities_by_product(product_type_id)
            if not product_activities: continue
            for a in product_activities:
                if a.code in activities:
                    mats: db.QSwaggerActivityMaterials = a.materials
                    for m in mats.materials:
                        if m.material_id not in self.valid_materials:
                            self.valid_materials[m.material_id] = m.material_type
        # перебираем ассеты, ищем вход производства (сток материалов)
        if containers_stocks:
            station_id: int = self.station.station_id
            for a in corporation.assets.values():
                # проверям "заблудился" ли материал, или лежит на своём месте?
                ConveyorRouterAssets.calc2(
                    a,
                    router_settings,
                    station_id,
                    containers_exclude,
                    containers_stocks,
                    self.valid_materials,
                    self.input_materials,
                    self.lost_materials)


def calc_router_materials(
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        # настройки генерации отчёта
        router_settings: typing.List[RouterSettings],
        conveyor_settings: typing.List[ConveyorSettings]) \
        -> typing.Dict[RouterSettings, ConveyorRouterInputMaterials]:
    if not conveyor_settings or not router_settings:
        return {}
    # проверям, что конвейер - поддерживается только одна производственная корпорация
    corporation: db.QSwaggerCorporation = conveyor_settings[0].corporation
    if next((_ for _ in conveyor_settings if not _.corporation.corporation_id == corporation.corporation_id), None) is not None:
        raise Exception("Unsupported multi-corporation conveyor")
    # считаем количество готовых материалов на выбранных станциях
    ready_materials: typing.Dict[RouterSettings, ConveyorRouterInputMaterials] = {}
    for index, rs in enumerate(router_settings):
        # получаем настройки для рассчёта
        activities, local_conveyor_settings = ConveyorRouterAssets.prepare_calc0(qid, rs, conveyor_settings)
        if not local_conveyor_settings: continue
        # выполняем расчёт
        m: ConveyorRouterInputMaterials = ConveyorRouterInputMaterials(index)
        m.calc(qid, corporation, local_conveyor_settings, rs, activities)
        ready_materials[rs] = m
    return ready_materials


class ConveyorCorporationOutputProducts(ConveyorRouterAssets):
    def __init__(self, index: int):
        super().__init__()
        self.index: int = index
        self.valid_products: typing.Dict[int, db.QSwaggerTypeId] = {}  # type_id:product
        self.output_products: typing.Dict[int, db.QSwaggerMaterial] = {}  # type_id:product
        self.lost_products: typing.Dict[int, typing.List[db.QSwaggerCorporationAssetsItem]] = {}  # type_id:list(assets)

    def calc(self,
             # данные (справочники)
             qid: db.QSwaggerDictionary,
             # данные корпорации для подсчёта кол-ва материалов
             corporation: db.QSwaggerCorporation,
             # настройки генерации отчёта
             conveyor_settings: typing.List[ConveyorSettings],
             router_settings: RouterSettings,
             # список активностей, которые выполняются для получения продуктов роутера
             activities: typing.Set[db.QSwaggerActivityCode]) -> None:
        self.valid_products: typing.Dict[int, db.QSwaggerTypeId] = {}
        self.output_products: typing.Dict[int, db.QSwaggerMaterial] = {}
        self.lost_products: typing.Dict[int, typing.List[db.QSwaggerCorporationAssetsItem]] = {}
        # определяем станцию, корпорацию и стоки конвейера соответствующего роутеру
        router_details: typing.Tuple[db.QSwaggerStation, db.QSwaggerCorporation, typing.Set[int], typing.Set[int]] = \
            self.prepare_calc1(qid, corporation, conveyor_settings, router_settings, activities)
        self.station: db.QSwaggerStation = router_details[0]
        if corporation.corporation_id != router_details[1].corporation_id:
            raise Exception("Something wrong: incompatible corporations for conveyor/router settings")
        # containers_stocks: typing.Set[int] = router_details[2]
        containers_output: typing.Set[int] = router_details[3]
        containers_exclude: typing.Set[int] = set([_.container_id for x in conveyor_settings for _ in x.containers_exclude])
        # если список output сконфигурирован, то имеет место быть станция из настроек router-а
        for product_type_id in router_settings.output:
            self.valid_products[product_type_id] = qid.get_type_id(product_type_id)
        # перебираем ассеты, ищем продукты производства
        if containers_output:
            station_id: int = self.station.station_id
            for a in corporation.assets.values():
                # проверям "заблудился" ли продукт, или лежит на своём месте?
                ConveyorRouterAssets.calc2(
                    a,
                    router_settings,
                    station_id,
                    containers_exclude,
                    containers_output,
                    self.valid_products,
                    self.output_products,
                    self.lost_products)


def calc_router_products(
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        # настройки генерации отчёта
        router_settings: typing.List[RouterSettings],
        conveyor_settings: typing.List[ConveyorSettings]) \
        -> typing.Dict[RouterSettings, ConveyorCorporationOutputProducts]:
    if not conveyor_settings or not router_settings:
        return {}
    # проверям, что конвейер - поддерживается только одна производственная корпорация
    corporation: db.QSwaggerCorporation = conveyor_settings[0].corporation
    if next((_ for _ in conveyor_settings if not _.corporation.corporation_id == corporation.corporation_id), None) is not None:
        raise Exception("Unsupported multi-corporation conveyor")
    # считаем количество готовых продуктов на выбранных станциях
    ready_products: typing.Dict[RouterSettings, ConveyorCorporationOutputProducts] = {}
    for index, rs in enumerate(router_settings):
        # получаем настройки для рассчёта
        activities, local_conveyor_settings = ConveyorRouterAssets.prepare_calc0(qid, rs, conveyor_settings)
        if not local_conveyor_settings: continue
        # выполняем расчёт
        a: ConveyorCorporationOutputProducts = ConveyorCorporationOutputProducts(index)
        a.calc(qid, corporation, local_conveyor_settings, rs, activities)
        ready_products[rs] = a
    return ready_products


def get_min_max_time(
        activities: typing.List[db.QSwaggerActivityCode],
        stack: ConveyorMaterialRequirements.StackOfBlueprints) -> typing.Tuple[int, int]:
    min_time, max_time = None, None

    def apply(min_t: int, max_t: int, t: int) -> typing.Tuple[int, int]:
        if min_t is None:
            min_t = t
            max_t = t
        else:
            min_t = min(min_t, t)
            max_t = max(max_t, t)
        return min_t, max_t

    for b in stack.group:
        if db.QSwaggerActivityCode.MANUFACTURING in activities and b.blueprint_type.manufacturing:
            activity: db.QSwaggerBlueprintManufacturing = b.blueprint_type.manufacturing
            # считаем бонус чертежа (накладываем TE чертежа на БП)
            __stage1: float = float(activity.time * (100 - b.time_efficiency) / 100.0)
            # навыки и импланты (базовые навыки начинающего производственника, который "ничего не умеет делать")
            __stage2: float = float(__stage1 * (100.0 - 31.5) / 100.0)
            # # учитываем бонус установленного модификатора
            __stage3: float = float(__stage2 * (100.0 - 42.0) / 100.0)
            # учитываем бонус профиля сооружения
            __stage4: float = float(__stage3 * (100.0 - 30.0) / 100.0)
            # округляем вещественное число до старшего целого
            __stage5: int = int(float(__stage4 + 0.99))
            # умножаем на кол-во прогонов
            __stageX: int = __stage5 * b.runs
            # считаем min/max
            min_time, max_time = apply(min_time, max_time, __stageX)
        if db.QSwaggerActivityCode.INVENTION in activities and b.blueprint_type.invention:
            activity: db.QSwaggerBlueprintInvention = b.blueprint_type.invention
            # навыки и импланты (базовые навыки начинающего производственника, который "ничего не умеет делать")
            __stage1: float = float(activity.time * (100.0 - 9.0) / 100.0)
            # учитываем бонус профиля сооружения
            __stage2: float = float(__stage1 * (100.0 - 30.0) / 100.0)
            # округляем вещественное число до старшего целого
            __stage3: int = int(float(__stage2 + 0.99))
            # умножаем на кол-во прогонов
            __stageX: int = __stage3 * b.runs
            # считаем min/max
            min_time, max_time = apply(min_time, max_time, __stageX)
        if db.QSwaggerActivityCode.REACTION in activities and b.blueprint_type.reaction:
            activity: db.QSwaggerBlueprintReaction = b.blueprint_type.reaction
            # навыки и импланты (базовые навыки начинающего производственника, который "ничего не умеет делать")
            __stage1: float = float(activity.time * (100.0 - 16.0) / 100.0)
            # учитываем бонус установленного модификатора
            __stage2: float = float(__stage1 * (100.0 - 22.0) / 100.0)
            # учитываем бонус профиля сооружения
            __stage3: float = float(__stage2 * (100.0 - 25.0) / 100.0)
            # округляем вещественное число до старшего целого
            __stage4: int = int(float(__stage3 + 0.99))
            # умножаем на кол-во прогонов
            __stageX: int = __stage4 * b.runs
            # считаем min/max
            min_time, max_time = apply(min_time, max_time, __stageX)
        if b.is_original:
            for a in [db.QSwaggerActivityCode.COPYING,
                      db.QSwaggerActivityCode.RESEARCH_TIME,
                      db.QSwaggerActivityCode.RESEARCH_MATERIAL]:
                if a not in activities: continue
                activity: db.QSwaggerActivity = b.blueprint_type.get_activity(a.to_int())
                if not activity: continue
                # навыки и импланты (базовые навыки начинающего производственника, который "ничего не умеет делать")
                __stage1: float = float(activity.time * (100.0 - 27.2) / 100.0)
                # учитываем бонус профиля сооружения
                __stage2: float = float(__stage1 * (100.0 - 30.0) / 100.0)
                # округляем вещественное число до старшего целого
                __stage3: int = int(float(__stage2 + 0.99))
                # умножаем на кол-во прогонов
                __stageX: int = __stage3  # нельзя умножать на runs, оно равно -1
                # считаем min/max
                min_time, max_time = apply(min_time, max_time, __stageX)
    return min_time, max_time


def get_conveyor_table_sort_data(
        priority: int,
        activities: typing.List[db.QSwaggerActivityCode],
        row_num: typing.Optional[int],
        duration: typing.Optional[typing.Tuple[int, int]]):
    sort = {'p': priority, 'a': [_.to_int() for _ in activities]}
    if row_num is not None:
        sort.update({'n': row_num + 1})  # не м.б. 0, т.к. 0 зарезервирован для banner-а
    if duration is not None:
        if duration[0] == duration[1]:  # 0-min, 1-max
            sort.update({'d': duration[0]})
        else:
            sort.update({'d1': duration[0], 'd2': duration[1]})
    elif row_num is not None:
        sort.update({'lp': 1})   # нижняя часть (несортируемая)
    return sort


def get_single_run_output_quantity(
        product_type_id: int,
        activity_id: int,
        # данные (справочники)
        qid: db.QSwaggerDictionary) -> int:
    single_run_output: int = 1
    activities: typing.List[db.QSwaggerActivity] = qid.get_activities_by_product(product_type_id)
    if activities:
        activity: db.QSwaggerActivity = next((_ for _ in activities if _.code.value == activity_id), None)
        if activity:
            if hasattr(activity, 'products'):
                pp: typing.List[db.QSwaggerInventionProduct] = getattr(activity, 'products')
                single_run_output = pp[0].quantity
            elif hasattr(activity, 'product'):
                p: db.QSwaggerProduct = getattr(activity, 'product')
                single_run_output = p.quantity
    return single_run_output


def get_activity_by_product(
        qid: db.QSwaggerDictionary,
        product_id: int,
        conveyor_settings: ConveyorSettings) -> typing.Optional[db.QSwaggerActivity]:
    variants: typing.Optional[typing.List[db.QSwaggerActivity]] = qid.get_activities_by_product(product_id)
    if variants is not None:
        for activity in variants:
            if activity.code in conveyor_settings.activities:
                return activity
            elif conveyor_settings.conveyor_with_reactions and activity.code == db.QSwaggerActivityCode.REACTION:
                return activity
    return None


class ConveyorManufacturingAnalysis:
    def __init__(self,
                 qid: db.QSwaggerDictionary,
                 manufacturing_conveyor: ConveyorSettings,
                 blueprint_tier1: typing.Optional[db.QSwaggerBlueprint] = None,
                 activity_tier1: typing.Optional[db.QSwaggerBlueprintManufacturing] = None,
                 product_tier1: typing.Optional[db.QSwaggerTypeId] = None):
        # T2/T3-чертёж полученный в результате invent-а (продукт invent-а)
        self.blueprint_tier1: typing.Optional[db.QSwaggerBlueprint] = None
        # параметры T2/T3-производства по чертежу полученному invent-ом
        self.activity_tier1: typing.Optional[db.QSwaggerBlueprintManufacturing] = None
        # продукт T2/T3-производства
        self.product_tier1: typing.Optional[db.QSwaggerProduct] = None
        # различные варианты конструирования объекта
        if blueprint_tier1 or activity_tier1:
            if blueprint_tier1:
                self.blueprint_tier1 = blueprint_tier1
                self.activity_tier1 = blueprint_tier1.manufacturing
            elif activity_tier1:
                self.activity_tier1 = activity_tier1
                self.blueprint_tier1 = activity_tier1.blueprint
            if self.activity_tier1 is None or self.blueprint_tier1 is None: return
            self.product_tier1: db.QSwaggerProduct = self.activity_tier1.product
        elif product_tier1:
            self.product_tier1: db.QSwaggerProduct = db.QSwaggerProduct(product_tier1, 0)
            self.activity_tier1 = get_activity_by_product(qid, self.product_tier1.product_id, manufacturing_conveyor)
            if self.activity_tier1:
                self.blueprint_tier1 = self.activity_tier1.blueprint

        # подсчёт кол-ва предметов в ассетах
        self.product_tier1_in_assets: typing.List[db.QSwaggerCorporationAssetsItem] = \
            manufacturing_conveyor.assets.get_with_unique_items(
                self.product_tier1.product_id, [
                    ConveyorPlace.STOCK,
                    ConveyorPlace.OUTPUT,
                    ConveyorPlace.SALE_STOCK,
                ])
        self.product_tier1_num_in_assets: int = sum([_.quantity for _ in self.product_tier1_in_assets])
        # подсчёт кол-ва чертежей для производства этого типа предмета
        if self.blueprint_tier1:
            blueprint_ids: typing.List[db.QSwaggerCorporationAssetsItem] = \
                manufacturing_conveyor.assets.get_with_unique_items(
                    self.blueprint_tier1.type_id, [
                        ConveyorPlace.CONVEYOR,
                    ])
            blueprint_ids: typing.Set[int] = set([_.item_id for _ in blueprint_ids])
            self.product_tier1_in_blueprints: typing.List[db.QSwaggerCorporationBlueprint] = \
                [_[1] for _ in manufacturing_conveyor.corporation.blueprints.items() if _[0] in blueprint_ids]
            # TODO: здесь нет фильтрации уже запущенных в работу чертежей
            # self.product_tier1_in_blueprints: typing.List[db.QSwaggerCorporationBlueprint] = \
            #     manufacturing_conveyor.blueprints.get_with_unique_items(
            #         self.blueprint_tier1.type_id, [
            #             ConveyorPlace.CONVEYOR,
            #         ])
        else:
            self.product_tier1_in_blueprints: typing.List[db.QSwaggerCorporationBlueprint] = []
        self.product_tier1_num_in_blueprints: int = sum([1 if _.is_copy else max(_.quantity, 1)
                                                         for _ in self.product_tier1_in_blueprints])
        self.product_tier1_num_in_blueprint_runs: int = sum([_.runs for _ in self.product_tier1_in_blueprints])
        # подсчёт количества производимых сейчас предметов
        if self.blueprint_tier1:
            self.product_tier1_in_jobs: typing.List[db.QSwaggerCorporationIndustryJob] = \
                manufacturing_conveyor.industry_jobs.get_with_unique_items(
                    self.blueprint_tier1.type_id,
                    self.product_tier1.product_id,
                    places=[ConveyorJobPlace.BLUEPRINT, ConveyorJobPlace.OUTPUT],
                    activity=db.QSwaggerActivityCode.MANUFACTURING)
        else:
            self.product_tier1_in_jobs: typing.List[db.QSwaggerCorporationIndustryJob] = []
        self.product_tier1_num_in_jobs: int = self.product_tier1.quantity * sum([_.runs for _ in self.product_tier1_in_jobs])
        # подсчёт количества продаваемых сейчас предметов
        self.product_tier1_in_sell: typing.List[db.QSwaggerCorporationOrder] = \
            manufacturing_conveyor.orders.get_with_unique_items(
                self.product_tier1.product_id, [
                    ConveyorOrderPlace.SELL
                ])
        self.product_tier1_num_in_sell: int = sum([_.volume_remain for _ in self.product_tier1_in_sell])
        # если не задан лимит, то оверстока нет
        self.product_tier1_limit: typing.Optional[int] = None
        self.product_tier1_overstock: bool = False
        # проверка избыточного количества продукта
        self.product_tier1_limits: typing.Optional[typing.List[db.QSwaggerConveyorLimit]] = \
            qid.get_conveyor_limits(self.product_tier1.product_id)
        if self.product_tier1_limits:
            self.product_tier1_limit = sum([_.approximate for _ in self.product_tier1_limits])
            self.product_tier1_overstock = self.num_ready >= self.product_tier1_limit
        # поиск формулы производства для этого предмета
        self.product_tier1_best_formula: typing.Optional[db.QSwaggerConveyorBestFormula] = \
            qid.get_conveyor_best_formula(self.product_tier1.product_id)
        # поиск conveyor-формул для этого типа предмета
        self.product_tier1_conveyor_formulas: typing.Optional[typing.List[db.QSwaggerConveyorFormula]] = \
            qid.get_conveyor_formulas(self.product_tier1.product_id)

    @classmethod
    def from_blueprint_tier1(
            cls,
            qid: db.QSwaggerDictionary,
            manufacturing_conveyor: ConveyorSettings,
            blueprint_tier1: typing.Optional[db.QSwaggerBlueprint],
            activity_tier1: typing.Optional[db.QSwaggerBlueprintManufacturing]):
        return cls(qid, manufacturing_conveyor, blueprint_tier1=blueprint_tier1, activity_tier1=activity_tier1)

    @classmethod
    def from_product_tier1(
            cls,
            qid: db.QSwaggerDictionary,
            manufacturing_conveyor: ConveyorSettings,
            product_tier1: db.QSwaggerTypeId):
        return cls(qid, manufacturing_conveyor, product_tier1=product_tier1)

    @property
    def num_ready(self) -> int:
        # подсчёт кол-ва предметов в ассетах, в производстве и продаже
        return self.product_tier1_num_in_assets + self.product_tier1_num_in_jobs + self.product_tier1_num_in_sell

    @property
    def num_prepared(self) -> int:
        # подсчёт кол-ва готовых чертежей для производства этого продукта (в кол-ве ранов)
        return self.product_tier1_num_in_blueprint_runs

    def get_manufacturing_conveyor_formula(self,
                                           trade_hub_id: int,
                                           blueprint_type_id: int,
                                           runs: int, me: int, te: int) -> \
            typing.Optional[db.QSwaggerConveyorFormula]:
        if not self.product_tier1_conveyor_formulas:
            return None
        res: typing.Optional[db.QSwaggerConveyorFormula] = next((
            _ for _ in self.product_tier1_conveyor_formulas
            if _.blueprint_type_id == blueprint_type_id and
               _.customized_runs == runs and
               _.material_efficiency == me and
               _.time_efficiency == te and
               _.trade_hub_id == trade_hub_id
        ), None)
        return res


class ConveyorManufacturingProductAnalysis:
    def __init__(self):
        self.product: typing.Optional[ConveyorManufacturingAnalysis] = None

    def analyse_manufacturing(self,
                              qid: db.QSwaggerDictionary,
                              blueprint: typing.Optional[db.QSwaggerBlueprint],
                              activity: typing.Optional[db.QSwaggerActivity],
                              manufacturing_conveyor: ConveyorSettings) -> None:
        self.product = None
        if manufacturing_conveyor is None: return
        if activity and not isinstance(activity, db.QSwaggerBlueprintManufacturing): return
        if db.QSwaggerActivityCode.MANUFACTURING not in manufacturing_conveyor.activities: return
        self.product = ConveyorManufacturingAnalysis.from_blueprint_tier1(
            qid, manufacturing_conveyor, blueprint, activity)

    def analyse_product(self,
                        qid: db.QSwaggerDictionary,
                        product_type: db.QSwaggerTypeId,
                        manufacturing_conveyor: ConveyorSettings):
        self.product = None
        if manufacturing_conveyor is None: return
        self.product = ConveyorManufacturingAnalysis.from_product_tier1(
            qid, manufacturing_conveyor, product_type)


class ConveyorInventAnalysis:
    def __init__(self,
                 qid: db.QSwaggerDictionary,
                 activity_tier1: db.QSwaggerActivity,
                 product_tier1: db.QSwaggerInventionProduct,
                 manufacturing_conveyor: typing.Optional[ConveyorSettings]):
        # параметры invent-а
        self.activity_tier1: db.QSwaggerActivity = activity_tier1
        # продукт invent-а (чертёж, который будет получен)
        self.product_tier1: db.QSwaggerInventionProduct = product_tier1
        # T2/T3-чертёж полученный в результате invent-а (продукт invent-а)
        self.blueprint_tier1: typing.Optional[db.QSwaggerBlueprint] = qid.get_blueprint(self.product_tier1.product_id)
        # анализ следующего уровня производства
        self.__analysis_tier2: ConveyorManufacturingProductAnalysis = ConveyorManufacturingProductAnalysis()
        self.__analysis_tier2.analyse_manufacturing(qid, self.blueprint_tier1, None, manufacturing_conveyor)

    @property
    def analysis_tier2(self) -> ConveyorManufacturingProductAnalysis:
        return self.__analysis_tier2

    @property
    def activity_tier2(self) -> typing.Optional[db.QSwaggerBlueprintManufacturing]:
        # параметры T2/T3-производства по чертежу полученному invent-ом
        if not self.__analysis_tier2.product: return None
        return self.__analysis_tier2.product.activity_tier1

    @property
    def product_tier2(self) -> typing.Optional[db.QSwaggerProduct]:
        if not self.__analysis_tier2.product: return None
        return self.__analysis_tier2.product.product_tier1

    #
    # === следующие поля известны только при product_tier2 not None ===
    #

    """
    корпассеты типа продукта T2/T3-производства (либо в стоке конвейера, либо в output-конвейера, либо
    уже подготовлены к продаже)
    """
    @property
    def product_tier2_in_assets(self) -> typing.Optional[typing.List[db.QSwaggerCorporationAssetsItem]]:
        if not self.__analysis_tier2.product: return None
        return self.__analysis_tier2.product.product_tier1_in_assets

    @property
    def product_tier2_num_in_assets(self) -> int:
        if not self.__analysis_tier2.product: return 0
        return self.__analysis_tier2.product.product_tier1_num_in_assets

    """
    корп.чертежи типа продукта T2/T3-производства (в коробках конвейера)
    """
    @property
    def product_tier2_in_blueprints(self) -> typing.Optional[typing.List[db.QSwaggerCorporationBlueprint]]:
        if not self.__analysis_tier2.product: return None
        return self.__analysis_tier2.product.product_tier1_in_blueprints

    @property
    def product_tier2_num_in_blueprints(self) -> int:
        if not self.__analysis_tier2.product: return 0
        return self.__analysis_tier2.product.product_tier1_num_in_blueprints

    @property
    def product_tier2_num_in_blueprint_runs(self) -> int:
        if not self.__analysis_tier2.product: return 0
        return self.__analysis_tier2.product.product_tier1_num_in_blueprint_runs

    """
    работки типа T2/T3-производства (запущенные из коробок конвейера, или с выходом в output-конвейера)
    """
    @property
    def product_tier2_in_jobs(self) -> typing.Optional[typing.List[db.QSwaggerCorporationIndustryJob]]:
        if not self.__analysis_tier2.product: return None
        return self.__analysis_tier2.product.product_tier1_in_jobs

    @property
    def product_tier2_num_in_jobs(self) -> int:
        if not self.__analysis_tier2.product: return 0
        return self.__analysis_tier2.product.product_tier1_num_in_jobs

    """
    работки типа T2/T3-производства (запущенные из коробок конвейера, или с выходом в output-конвейера)
    """
    @property
    def product_tier2_in_sell(self) -> typing.Optional[typing.List[db.QSwaggerCorporationOrder]]:
        if not self.__analysis_tier2.product: return None
        return self.__analysis_tier2.product.product_tier1_in_sell

    @property
    def product_tier2_num_in_sell(self) -> int:
        if not self.__analysis_tier2.product: return 0
        return self.__analysis_tier2.product.product_tier1_num_in_sell

    """
    ограничение производства предмета (не должно производиться больше, чем выставлено на продажу)
    """
    @property
    def product_tier2_limit(self) -> typing.Optional[int]:
        if not self.__analysis_tier2.product: return None
        return self.__analysis_tier2.product.product_tier1_limit

    """
    признак того, что продукта уже избыточное количество
    """
    @property
    def product_tier2_overstock(self) -> typing.Optional[bool]:
        if not self.__analysis_tier2.product: return None
        if self.product_tier2_limit:
            return (self.num_ready + self.num_prepared) >= self.product_tier2_limit
        else:
            return None

    """
    подсчёт кол-ва предметов в ассетах, в производстве и продаже
    """
    @property
    def num_ready(self) -> int:
        if not self.__analysis_tier2.product: return 0
        return self.__analysis_tier2.product.num_ready

    @property
    def num_prepared(self) -> int:
        if not self.__analysis_tier2.product: return 0
        return self.__analysis_tier2.product.num_prepared

    """
    conveyor-формула производства предмета
    """
    @property
    def product_tier2_best_formula(self) -> typing.Optional[db.QSwaggerConveyorBestFormula]:
        if not self.__analysis_tier2.product: return None
        return self.__analysis_tier2.product.product_tier1_best_formula


class ConveyorInventProductsAnalysis:
    def __init__(self):
        self.products: typing.Optional[typing.List[ConveyorInventAnalysis]] = None

    def analyse_invent(self,
                       qid: db.QSwaggerDictionary,
                       invent_conveyor: ConveyorSettings,
                       all_possible_conveyors: typing.List[ConveyorSettings],
                       activity_tier1: db.QSwaggerActivity) -> None:
        self.products = None
        if not isinstance(activity_tier1, db.QSwaggerBlueprintInvention): return
        if db.QSwaggerActivityCode.INVENTION not in invent_conveyor.activities: return
        manufacturing_conveyor: typing.Optional[ConveyorSettings] = next((
            _ for _ in all_possible_conveyors
            if _.corporation.corporation_id == invent_conveyor.corporation.corporation_id and
            db.QSwaggerActivityCode.MANUFACTURING in _.activities), None)
        if not manufacturing_conveyor: return
        self.products = []
        for product_tier1 in activity_tier1.products:
            self.products.append(ConveyorInventAnalysis(qid, activity_tier1, product_tier1, manufacturing_conveyor))

    def is_all_variants_overstock(self) -> typing.Optional[bool]:
        overstock: typing.Optional[bool] = None
        if self.products is not None:
            for ia in self.products:
                if ia.product_tier2 is None: continue
                # проверка общего количества продуктов, имеющихся в ассетах, в производстве, и продаже
                if ia.product_tier2_overstock:
                    overstock = True
                else:
                    overstock = False
                    break
        return overstock


class ConveyorCopyingAnalysis:
    def __init__(self,
                 qid: db.QSwaggerDictionary,
                 invention_conveyor: ConveyorSettings,
                 manufacturing_conveyor: ConveyorSettings,
                 blueprint_tier1: typing.Optional[db.QSwaggerBlueprint] = None,
                 activity_tier1: typing.Optional[db.QSwaggerBlueprintCopying] = None,
                 product_tier1: typing.Optional[db.QSwaggerBlueprint] = None):
        # копия T1-чертёжа полученная в результате копирки (продукт copying-а)
        self.blueprint_tier1: typing.Optional[db.QSwaggerBlueprint] = None
        # параметры T1-копирки чертежа
        self.activity_tier1: typing.Optional[db.QSwaggerBlueprintCopying] = None
        # продукт T1-копирки (должен быть тот же самый чертёж, если это не Taipan Blueprint)
        self.product_tier1: typing.Optional[db.QSwaggerBlueprint] = None
        # различные варианты конструирования объекта
        if blueprint_tier1 or activity_tier1:
            if blueprint_tier1:
                self.blueprint_tier1 = blueprint_tier1
                self.activity_tier1 = blueprint_tier1.copying
            elif activity_tier1:
                self.activity_tier1 = activity_tier1
                self.blueprint_tier1 = activity_tier1.blueprint
            if self.activity_tier1 is None or self.blueprint_tier1 is None: return
            self.product_tier1: db.QSwaggerBlueprint = self.activity_tier1.blueprint  # здесь должен был быть продукт
        elif product_tier1:
            self.product_tier1: db.QSwaggerBlueprint = product_tier1
            self.activity_tier1 = self.product_tier1.copying
            if self.activity_tier1:
                self.blueprint_tier1 = self.activity_tier1.blueprint
        # подсчёт кол-ва копий в ассетах
        self.product_tier1_in_copies: typing.List[db.QSwaggerCorporationBlueprint] = \
            invention_conveyor.blueprints.get_with_unique_items(
                self.product_tier1.type_id,
                places=[ConveyorPlace.CONVEYOR])
        self.product_tier1_in_copies = [_ for _ in self.product_tier1_in_copies if _.is_copy]
        self.product_tier1_num_in_copies: int = sum([1 for _ in self.product_tier1_in_copies])
        self.product_tier1_num_in_copy_runs: int = sum([_.runs for _ in self.product_tier1_in_copies])
        # подсчёт кол-ва оригиналов в ассетах
        self.product_tier1_in_originals: typing.List[db.QSwaggerCorporationBlueprint] = \
            manufacturing_conveyor.blueprints.get_with_unique_items(
                self.product_tier1.type_id,
                places=[ConveyorPlace.ADDITIONAL_BLUEPRINTS])
        self.product_tier1_in_originals = [_ for _ in self.product_tier1_in_originals if _.is_original]
        self.product_tier1_num_in_originals: int = \
            sum([1 if _.quantity < 0 else _.quantity for _ in self.product_tier1_in_originals])
        # подсчёт количества производимых сейчас предметов
        self.product_tier1_in_jobs: typing.List[db.QSwaggerCorporationIndustryJob] = []
        if self.blueprint_tier1:
            self.product_tier1_in_jobs = invention_conveyor.industry_jobs.get_with_unique_items(
                self.blueprint_tier1.type_id,
                self.product_tier1.type_id,
                places=[ConveyorJobPlace.BLUEPRINT, ConveyorJobPlace.OTHER],  # TODO: костыль, тут надо проверять выходную коробку у работок
                activity=db.QSwaggerActivityCode.COPYING)
        self.product_tier1_num_in_jobs: int = sum([1 for _ in self.product_tier1_in_jobs])
        self.product_tier1_num_in_job_runs: int = sum([_.runs for _ in self.product_tier1_in_jobs])

        # анализ следующего уровня производства
        self.__analysis_tier2: typing.Optional[ConveyorInventProductsAnalysis] = None
        # проверяем, что копия инвентится
        if self.product_tier1.invention:
            self.__analysis_tier2 = ConveyorInventProductsAnalysis()
            self.__analysis_tier2.analyse_invent(
                qid,
                invention_conveyor,
                [manufacturing_conveyor],
                self.product_tier1.invention)

    def analysis_tier3(self, type_id: int) -> typing.Optional[ConveyorManufacturingProductAnalysis]:
        for p in self.__analysis_tier2.products:
            if type_id == p.product_tier1.product_id:
                return p.analysis_tier2
        return None

    @property
    def analysis_tier2(self) -> ConveyorInventProductsAnalysis:
        return self.__analysis_tier2

    #
    # === следующие поля известны только при product_tier2 not None ===
    #

    """
    подсчёт кол-ва предметов в ассетах, в производстве и продаже
    """
    """
    @property
    def num_ready(self) -> int:
        if not self.__analysis_tier2.product: return 0
        return self.__analysis_tier2.product.num_ready

    @property
    def num_prepared(self) -> int:
        if not self.__analysis_tier2.product: return 0
        return self.__analysis_tier2.product.num_prepared
    """

    @classmethod
    def from_blueprint_tier1(
            cls,
            qid: db.QSwaggerDictionary,
            invention_conveyor: ConveyorSettings,
            manufacturing_conveyor: ConveyorSettings,
            blueprint_tier1: typing.Optional[db.QSwaggerBlueprint],
            activity_tier1: typing.Optional[db.QSwaggerBlueprintCopying]):
        return cls(
            qid,
            invention_conveyor,
            manufacturing_conveyor,
            blueprint_tier1=blueprint_tier1,
            activity_tier1=activity_tier1)

    @classmethod
    def from_product_tier1(
            cls,
            qid: db.QSwaggerDictionary,
            invention_conveyor: ConveyorSettings,
            manufacturing_conveyor: ConveyorSettings,
            product_tier1: db.QSwaggerBlueprint):
        return cls(
            qid,
            invention_conveyor,
            manufacturing_conveyor,
            product_tier1=product_tier1)


class ConveyorCopyingProductsAnalysis:
    def __init__(self):
        self.product: typing.Optional[ConveyorCopyingAnalysis] = None

    def analyse_copying(self,
                        qid: db.QSwaggerDictionary,
                        blueprint: typing.Optional[db.QSwaggerBlueprint],
                        activity: typing.Optional[db.QSwaggerActivity],
                        invention_conveyor: ConveyorSettings,
                        manufacturing_conveyor: ConveyorSettings) -> None:
        self.product = None
        if invention_conveyor is None or manufacturing_conveyor is None: return
        if activity and not isinstance(activity, db.QSwaggerBlueprintCopying): return
        if db.QSwaggerActivityCode.INVENTION not in invention_conveyor.activities: return
        if db.QSwaggerActivityCode.MANUFACTURING not in manufacturing_conveyor.activities: return
        self.product = ConveyorCopyingAnalysis.from_blueprint_tier1(
            qid,
            invention_conveyor,
            manufacturing_conveyor,
            blueprint,
            activity)

    def analyse_product(self,
                        qid: db.QSwaggerDictionary,
                        product_type: db.QSwaggerBlueprint,
                        invention_conveyor: ConveyorSettings,
                        manufacturing_conveyor: ConveyorSettings):
        self.product = None
        if invention_conveyor is None: return
        self.product = ConveyorCopyingAnalysis.from_product_tier1(
            qid,
            invention_conveyor,
            manufacturing_conveyor,
            product_type)


class ConveyorIndustryAnalysis:
    def __init__(self):
        # индексируется значениями типа [33082] для tier1-чертежа типа 'Taipan Blueprint'
        # хранит значения типа [33082] для tier1-чертежей типа 'Taipan Blueprint' (а в SDE ошибка! там указан 33081)
        self.copying_analysis: typing.Dict[int, ConveyorCopyingProductsAnalysis] = {}
        # индексируется значениями типа 691 для чертежей типа 'Rifter Blueprint'
        #  хранит список чертежей типа [11372,11401] для tier1-чертежей типа ['Wolf Blueprint','Jaguar Blueprint']
        #  а также список продуктов типа [11371,11400] для tier2-продуктов типа ['Wolf','Jaguar']
        self.invent_analysis: typing.Dict[int, ConveyorInventProductsAnalysis] = {}
        # индексируется значениями типа 42891 для tier1-чертежей типа 'Capital Industrial Core II Blueprint'
        # хранит значения типа 42890 для tier1-продуктов типа 'Capital Industrial Core II'
        self.manufacturing_analysis: typing.Dict[int, ConveyorManufacturingProductAnalysis] = {}

    def push_into_copying(
            self,
            # данные (справочники)
            qid: db.QSwaggerDictionary,
            global_dictionary: ConveyorDictionary,
            # настройки текущего конвейера и список чертежей для анализа
            invention_conveyor: ConveyorSettings,
            manufacturing_conveyor: ConveyorSettings,
            # производственная активность для расчёта
            activity_tier1: db.QSwaggerBlueprintCopying) -> typing.Optional[ConveyorCopyingProductsAnalysis]:
        if not activity_tier1: return None
        copying_analysis: ConveyorCopyingProductsAnalysis = self.copying_analysis.get(activity_tier1.blueprint.type_id)
        if copying_analysis: return copying_analysis
        copying_analysis: ConveyorCopyingProductsAnalysis = ConveyorCopyingProductsAnalysis()
        copying_analysis.analyse_copying(
            qid,
            activity_tier1.blueprint,
            activity_tier1,
            invention_conveyor,
            manufacturing_conveyor)
        if not copying_analysis.product:
            del copying_analysis
            return None
        else:
            # сохраняем результаты анализа для повторного использования
            self.__push_into_copying_stage(
                global_dictionary,
                activity_tier1.blueprint.type_id,
                copying_analysis)
            return copying_analysis

    def __push_into_copying_stage(
            self,
            global_dictionary: ConveyorDictionary,
            type_id: int,
            copying_analysis: ConveyorCopyingProductsAnalysis) -> None:
        # сохраняем результаты анализа для повторного использования
        if not self.copying_analysis.get(type_id):
            self.copying_analysis[type_id] = copying_analysis
            if copying_analysis.product.product_tier1:
                # сохраняем в глобальный справочник идентификатор продукта копирки
                global_dictionary.load_type_ids({copying_analysis.product.product_tier1.type_id})
                # пополняем справочник инвентом (через связь уже готового анализа)
                invent_analysis: ConveyorInventProductsAnalysis = copying_analysis.product.analysis_tier2
                self.__push_into_invent_stage2(
                    global_dictionary,
                    copying_analysis.product.product_tier1.type_id,
                    invent_analysis)

    def push_into_invent(
            self,
            # данные (справочники)
            qid: db.QSwaggerDictionary,
            global_dictionary: ConveyorDictionary,
            # настройки генерации отчёта
            all_possible_conveyors: typing.List[ConveyorSettings],
            # настройки текущего конвейера и список чертежей для анализа
            settings: ConveyorSettings,
            # производственная активность для расчёта
            activity_tier1: db.QSwaggerBlueprintInvention) -> typing.Optional[ConveyorInventProductsAnalysis]:
        if not activity_tier1: return None
        invent_analysis: ConveyorInventProductsAnalysis = self.invent_analysis.get(activity_tier1.blueprint.type_id)
        if invent_analysis: return invent_analysis
        invent_analysis: ConveyorInventProductsAnalysis = ConveyorInventProductsAnalysis()
        invent_analysis.analyse_invent(
            qid,
            settings,
            all_possible_conveyors,
            activity_tier1)
        if not invent_analysis.products:
            del invent_analysis
            return None
        else:
            # сохраняем результаты анализа для повторного использования
            self.__push_into_invent_stage2(
                global_dictionary,
                activity_tier1.blueprint.type_id,
                invent_analysis)
            return invent_analysis

    def __push_into_invent_stage2(
            self,
            global_dictionary: ConveyorDictionary,
            type_id: int,
            invent_analysis: ConveyorInventProductsAnalysis) -> None:
        # сохраняем результаты анализа для повторного использования
        if not self.invent_analysis.get(type_id):
            self.invent_analysis[type_id] = invent_analysis
            for ia in invent_analysis.products:
                if ia.product_tier2 is None: continue
                # сохраняем в глобальный справочник идентификаторы продуктов инвента
                global_dictionary.load_type_ids({ia.product_tier2.product_id})
                # пополняем справочник перепроизводства продуктом инвента (через связь уже готового анализа)
                manufacturing_analysis: ConveyorManufacturingProductAnalysis = ia.analysis_tier2
                self.__push_into_manufacturing_stage2(
                    global_dictionary,
                    manufacturing_analysis.product.blueprint_tier1.type_id,
                    manufacturing_analysis)

    def push_into_manufacturing(
            self,
            # данные (справочники)
            qid: db.QSwaggerDictionary,
            global_dictionary: ConveyorDictionary,
            # настройки текущего конвейера и список чертежей для анализа
            settings: ConveyorSettings,
            # производственная активность для расчёта
            activity_tier1: db.QSwaggerBlueprintManufacturing) -> typing.Optional[ConveyorManufacturingProductAnalysis]:
        if not activity_tier1: return None
        manufacturing_analysis: ConveyorManufacturingProductAnalysis = \
            self.manufacturing_analysis.get(activity_tier1.blueprint.type_id)
        if manufacturing_analysis: return manufacturing_analysis
        manufacturing_analysis: ConveyorManufacturingProductAnalysis = ConveyorManufacturingProductAnalysis()
        manufacturing_analysis.analyse_manufacturing(
            qid,
            activity_tier1.blueprint,
            activity_tier1,  # можно передать None
            settings)
        if not manufacturing_analysis.product:
            del manufacturing_analysis
            return None
        else:
            # сохраняем разультаты анализа для повторного использования
            self.__push_into_manufacturing_stage2(
                global_dictionary,
                activity_tier1.blueprint.type_id,
                manufacturing_analysis)
            return manufacturing_analysis

    def __push_into_manufacturing_stage2(
            self,
            global_dictionary: ConveyorDictionary,
            type_id: int,
            manufacturing_analysis: ConveyorManufacturingProductAnalysis) -> None:
        # сохраняем разультаты анализа для повторного использования
        if not self.manufacturing_analysis.get(type_id):
            self.manufacturing_analysis[type_id] = manufacturing_analysis
            if manufacturing_analysis.product.product_tier1:
                # сохраняем в глобальный справочник идентификаторы продуктов инвента
                global_dictionary.load_type_ids({manufacturing_analysis.product.product_tier1.product_id})

    def analyse_industry(
            self,
            # данные (справочники)
            qid: db.QSwaggerDictionary,
            global_dictionary: ConveyorDictionary,
            # настройки генерации отчёта
            all_possible_conveyors: typing.List[ConveyorSettings],
            # настройки текущего конвейера и список чертежей для анализа
            settings: ConveyorSettings,
            possible_blueprints: typing.List[db.QSwaggerCorporationBlueprint]):
        # self.copying_analysis.clear()
        # self.invent_analysis.clear()
        # self.manufacturing_analysis.clear()
        if db.QSwaggerActivityCode.INVENTION in settings.activities:
            for b in possible_blueprints:
                if not b.blueprint_type.invention: continue
                activity_tier1: db.QSwaggerBlueprintInvention = b.blueprint_type.invention
                self.push_into_invent(
                    qid,
                    global_dictionary,
                    all_possible_conveyors,
                    settings,
                    activity_tier1)
        if db.QSwaggerActivityCode.MANUFACTURING in settings.activities:
            for b in possible_blueprints:
                if not b.blueprint_type.manufacturing: continue
                activity_tier1: db.QSwaggerBlueprintManufacturing = b.blueprint_type.manufacturing
                self.push_into_manufacturing(
                    qid,
                    global_dictionary,
                    settings,
                    activity_tier1)

    def is_all_variants_overstock(self, type_id: int, settings: ConveyorSettings) -> typing.Optional[bool]:
        all_variants_overstock: typing.Optional[bool] = None
        if db.QSwaggerActivityCode.INVENTION in settings.activities:
            invent_analysis: typing.Optional[ConveyorInventProductsAnalysis] = self.invent_analysis.get(type_id)
            if invent_analysis:
                all_variants_overstock = invent_analysis.is_all_variants_overstock()
        if not all_variants_overstock:
            if db.QSwaggerActivityCode.MANUFACTURING in settings.activities:
                manufacturing_analysis: typing.Optional[ConveyorManufacturingProductAnalysis] = \
                    self.manufacturing_analysis.get(type_id)
                if manufacturing_analysis and \
                   manufacturing_analysis.product and \
                   manufacturing_analysis.product.product_tier1:
                    all_variants_overstock = manufacturing_analysis.product.product_tier1_overstock
        return all_variants_overstock

    def is_all_variants_unprofitable(self, type_id: int, settings: ConveyorSettings) -> typing.Optional[bool]:
        all_variants_unprofitable: typing.Optional[bool] = None
        """
        if db.QSwaggerActivityCode.INVENTION in settings.activities:
            invent_analysis: typing.Optional[ConveyorInventProductsAnalysis] = self.invent_analysis.get(type_id)
            if invent_analysis:
                all_variants_unprofitable = invent_analysis.is_all_variants_overstock()
        """
        return all_variants_unprofitable


class ConveyorDemands:
    class Corrected:
        def __init__(self, requirement: db.QSwaggerConveyorRequirement):
            self.requirement = db.QSwaggerConveyorRequirement = requirement
            self.analysis_tier1: typing.Optional[ConveyorManufacturingAnalysis] = None
            self.analysis_tier2: typing.Optional[ConveyorInventAnalysis] = None
            self.analysis_tier3: typing.Optional[ConveyorCopyingAnalysis] = None

    def __init__(self,
                 # данные (справочники)
                 qid: db.QSwaggerDictionary,
                 global_dictionary: ConveyorDictionary,
                 # настройки генерации отчёта
                 all_possible_conveyors: typing.List[ConveyorSettings],
                 # анализ чертежей на предмет перепроизводства
                 industry_analysis: ConveyorIndustryAnalysis,
                 # настройки генерации отчёта
                 manufacturing_conveyor: ConveyorSettings,
                 invention_conveyor: ConveyorSettings):  # rest_threshold: typing.Optional[float] = None
        self.conveyor_requirements: typing.List[ConveyorDemands.Corrected] = \
            [ConveyorDemands.Corrected(_) for _ in qid.conveyor_requirements.values()]
        # пересчёт потребностей конвейера с учётом данных об анализе перепроизводства
        self.recalc(
            qid,
            global_dictionary,
            all_possible_conveyors,
            industry_analysis,
            manufacturing_conveyor,
            invention_conveyor)
        # ---
        self.ordered_demand: typing.List[ConveyorDemands.Corrected] = \
            [_ for _ in self.conveyor_requirements if _.requirement.rest_percent < 1.0]
        self.ordered_overstock: typing.List[ConveyorDemands.Corrected] = \
            [_ for _ in self.conveyor_requirements if _.requirement.rest_percent >= 1.0]
        self.ordered_demand.sort(key=lambda x: x.requirement.rest_percent)
        self.ordered_overstock.sort(key=lambda x: x.requirement.rest_percent, reverse=True)

    def recalc(self,
               # данные (справочники)
               qid: db.QSwaggerDictionary,
               global_dictionary: ConveyorDictionary,
               # настройки генерации отчёта
               all_possible_conveyors: typing.List[ConveyorSettings],
               # анализ чертежей на предмет перепроизводства
               industry_analysis: ConveyorIndustryAnalysis,
               # настройки генерации отчёта
               manufacturing_conveyor: ConveyorSettings,
               invention_conveyor: ConveyorSettings) -> None:
        for r in self.conveyor_requirements:
            methods_1tier: typing.Optional[typing.List[db.QSwaggerActivity]] = \
                qid.get_activities_by_product(r.requirement.type_id)
            if not methods_1tier: continue
            # проверка, можно ли произвести данный вид продукции?
            manufacturing_activity_1tier: typing.Optional[db.QSwaggerBlueprintManufacturing] = \
                next((_ for _ in methods_1tier if _.code == db.QSwaggerActivityCode.MANUFACTURING), None)
            if not manufacturing_activity_1tier: continue
            # проверка, надо ли инвентить этот чертёж?
            if invention_conveyor:
                methods_2tier: typing.Optional[typing.List[db.QSwaggerActivity]] = \
                    qid.get_activities_by_product(manufacturing_activity_1tier.blueprint.type_id)
                if methods_2tier:
                    invent_activity_2tier: typing.Optional[db.QSwaggerBlueprintInvention] = \
                        next((_ for _ in methods_2tier if _.code == db.QSwaggerActivityCode.INVENTION), None)
                    if invent_activity_2tier:
                        # проверка, можно ли копировать этот чертёж?
                        # TODO: проверить, что у нас имеются оригиналы этого типа чертежа?
                        methods_3tier: typing.Optional[typing.List[db.QSwaggerActivity]] = \
                            qid.get_activities_by_product(invent_activity_2tier.blueprint.type_id)
                        if methods_3tier:
                            copying_activity_3tier: typing.Optional[db.QSwaggerBlueprintCopying] = \
                                next((_ for _ in methods_3tier if _.code == db.QSwaggerActivityCode.COPYING), None)
                            if copying_activity_3tier:
                                r.analysis_tier3 = self.produce_analysis_tier3(
                                    qid,
                                    global_dictionary,
                                    manufacturing_conveyor,
                                    invention_conveyor,
                                    industry_analysis,
                                    copying_activity_3tier)
                        r.analysis_tier2 = self.produce_analysis_tier2(
                            qid,
                            global_dictionary,
                            all_possible_conveyors,
                            invention_conveyor,
                            industry_analysis,
                            r.requirement.type_id,
                            invent_activity_2tier)
            if not r.analysis_tier2:
                r.analysis_tier1 = self.produce_analysis_tier1(
                    qid,
                    global_dictionary,
                    manufacturing_conveyor,
                    industry_analysis,
                    manufacturing_activity_1tier)

            if r.analysis_tier2:
                r.requirement.recalc_rest_percent(r.analysis_tier2.num_ready, r.analysis_tier2.num_prepared)
            elif r.analysis_tier1:
                r.requirement.recalc_rest_percent(r.analysis_tier1.num_ready)

    @staticmethod
    def produce_analysis_tier3(
            # данные (справочники)
            qid: db.QSwaggerDictionary,
            global_dictionary: ConveyorDictionary,
            # настройки генерации отчёта
            manufacturing_conveyor: ConveyorSettings,
            invention_conveyor: ConveyorSettings,
            # анализ чертежей на предмет перепроизводства
            industry_analysis: ConveyorIndustryAnalysis,
            # данные для расчёта
            copying_activity_3tier: db.QSwaggerBlueprintCopying) -> \
            typing.Optional[ConveyorCopyingAnalysis]:
        # поиск готового расчёта
        ca: typing.Optional[ConveyorCopyingProductsAnalysis] = \
            industry_analysis.copying_analysis.get(copying_activity_3tier.blueprint.type_id)
        # проверка, что расчёт корректен
        if ca and ca.product and ca.product.product_tier1:
            return ca.product
        else:
            # анализируем чертежи на предмет перепроизводства
            ca: typing.Optional[ConveyorCopyingProductsAnalysis] = \
                industry_analysis.push_into_copying(
                    qid,
                    global_dictionary,
                    invention_conveyor,
                    manufacturing_conveyor,
                    copying_activity_3tier)
            if ca and ca.product and ca.product.product_tier1:
                return ca.product
        return None

    @staticmethod
    def produce_analysis_tier2(
            # данные (справочники)
            qid: db.QSwaggerDictionary,
            global_dictionary: ConveyorDictionary,
            # настройки генерации отчёта
            all_possible_conveyors: typing.List[ConveyorSettings],
            invention_conveyor: ConveyorSettings,
            # анализ чертежей на предмет перепроизводства
            industry_analysis: ConveyorIndustryAnalysis,
            # данные для расчёта
            product_type_id: int,
            invent_activity_2tier: db.QSwaggerBlueprintInvention) -> \
            typing.Optional[ConveyorInventAnalysis]:
        # поиск готового расчёта
        ia: typing.Optional[ConveyorInventProductsAnalysis] = \
            industry_analysis.invent_analysis.get(invent_activity_2tier.blueprint.type_id)
        if ia:
            if len(ia.products) == 1:
                return ia.products[0]
            else:
                for iaN in ia.products:
                    if iaN.product_tier2 is None: continue
                    if iaN.product_tier2.product_id != product_type_id: continue
                    return iaN
        else:
            # анализируем чертежи на предмет перепроизводства
            ia: typing.Optional[ConveyorInventProductsAnalysis] = \
                industry_analysis.push_into_invent(
                    qid,
                    global_dictionary,
                    all_possible_conveyors,
                    invention_conveyor,
                    invent_activity_2tier)
            if ia:
                if len(ia.products) == 1:
                    return ia.products[0]
                else:
                    for iaN in ia.products:
                        if iaN.product_tier2 is None: continue
                        if iaN.product_tier2.product_id != product_type_id: continue
                        return iaN
        return None

    @staticmethod
    def produce_analysis_tier1(
            # данные (справочники)
            qid: db.QSwaggerDictionary,
            global_dictionary: ConveyorDictionary,
            # настройки генерации отчёта
            manufacturing_conveyor: ConveyorSettings,
            # анализ чертежей на предмет перепроизводства
            industry_analysis: ConveyorIndustryAnalysis,
            # данные для рассчёта
            manufacturing_activity_1tier: db.QSwaggerBlueprintManufacturing) -> \
            typing.Optional[ConveyorManufacturingAnalysis]:
        # поиск готового расчёта
        ma: typing.Optional[ConveyorManufacturingProductAnalysis] = \
            industry_analysis.manufacturing_analysis.get(manufacturing_activity_1tier.blueprint.type_id)
        # проверка, что расчёт корректен
        if ma and ma.product and ma.product.product_tier1:
            return ma.product
        else:
            # анализируем чертежи на предмет перепроизводства
            ma: typing.Optional[ConveyorManufacturingProductAnalysis] = \
                industry_analysis.push_into_manufacturing(
                    qid,
                    global_dictionary,
                    manufacturing_conveyor,
                    manufacturing_activity_1tier)
            if ma and ma.product and ma.product.product_tier1:
                return ma.product
        return None

    class InventPlan:
        def __init__(self,
                     copied_bpc: db.QSwaggerBlueprint,
                     copying: db.QSwaggerBlueprintCopying,
                     invention: db.QSwaggerBlueprintInvention,
                     invented_product: db.QSwaggerInventionProduct,
                     invented_bpc: db.QSwaggerBlueprint,
                     decryptor_details: typing.Optional[DecryptorDetails],
                     decryptor_required: typing.Optional[bool]):
            self.copied_bpc: db.QSwaggerBlueprint = copied_bpc
            self.copying: db.QSwaggerBlueprintCopying = copying
            self.invention: db.QSwaggerBlueprintInvention = invention
            self.invented_product: db.QSwaggerInventionProduct = invented_product
            self.invented_bpc: db.QSwaggerBlueprint = invented_bpc
            self.decryptor_details: typing.Optional[DecryptorDetails] = decryptor_details
            self.decryptor_required: typing.Optional[bool] = decryptor_required
            self.invention_days_max: int = 0
            self.invent_1x1_run_time: float = 0.0
            self.max_invent_runs_per_days: int = 0
            self.invent_1xN_probability: float = 0.0
            self.invent_Cx1_runs: float = 0.0
            self.copy_CxN_runs: int = 0
            self.copy_CxN_duration: float = 0.0

    @staticmethod
    def calculate_invent_plan(
            # данные (справочники)
            qid: db.QSwaggerDictionary,
            # данные для расчёта
            product: Corrected,
            # настройки генерации отчёта
            manufacturing_conveyor: ConveyorSettings) -> typing.Optional[InventPlan]:
        # подсчёт имеющегося количества продукции
        num_prepared: typing.Optional[int] = None
        overstock: bool = False

        if product.analysis_tier2:
            num_ready: int = product.analysis_tier2.num_ready
            num_prepared: int = product.analysis_tier2.num_prepared
            # если произведено излишнее количество продукции, то invent не считаем
            if (num_ready + num_prepared) > 0 and product.analysis_tier2.product_tier2_overstock:
                overstock = True
        elif product.analysis_tier1:
            num_ready: int = product.analysis_tier1.num_ready
            # если произведено излишнее количество продукции, то invent не считаем
            if num_ready > 0 and product.analysis_tier1.product_tier1_overstock:
                overstock = True

        # если произошло перепроизводство - инвент не считаем
        if overstock:
            return None
        if product.requirement.rest_percent > manufacturing_conveyor.requirements_sold_threshold:
            return None
        # если производство, наличие и торговля продуктом не рассчитаны, то пропускаем
        if not product.analysis_tier2 or not product.analysis_tier3:
            return None
        # если копирка или инвент для этого продукта уже выполнялись, то пропускаем его
        # следующий анализ будет производиться только когда ни научки, ни чертежей для этого продукта нет
        if num_prepared:
            return None
        if product.analysis_tier3.product_tier1_num_in_copy_runs:
            return None
        if product.analysis_tier3.product_tier1_num_in_jobs:
            return None

        # получаем сведения о чертежах для копирки и для инвента
        copied_bpc: db.QSwaggerBlueprint = product.analysis_tier3.product_tier1
        copying: typing.Optional[db.QSwaggerBlueprintCopying] = product.analysis_tier3.activity_tier1
        invention: typing.Optional[db.QSwaggerBlueprintInvention] = product.analysis_tier2.activity_tier1
        if not copied_bpc or not copying or not invention:
            return None

        invented_product: typing.Optional[db.QSwaggerInventionProduct] = next((
            _ for _ in invention.products
            if _.product_id == product.analysis_tier2.analysis_tier2.product.blueprint_tier1.type_id),
            None)
        invented_bpc = product.analysis_tier2.activity_tier2.blueprint

        # если чертежей для копирки и для инвента в реестре не имеется, то пропускаем расчёт инвента
        if not invented_product or not invented_bpc:
            return None

        # ------------------------------------------------------
        # выбор декриптора для инвента
        # ------------------------------------------------------

        decryptor_probability: float = 0.0
        decryptor_runs: int = 0
        decryptor_time: float = 0.0
        decryptor_required: typing.Optional[bool] = None

        # выбираем декриптор
        decryptor_details: typing.Optional[typing.Tuple[DecryptorDetails, bool]] = which_decryptor_applies_to_blueprint(
            qid,
            # чертёж: coalesce(copied_bpc.blueprint_type, invented_bpc.blueprint_type)
            invented_bpc.manufacturing.product_type)
        # выполняем coalesce для параметров декриптора
        if decryptor_details is not None:
            decryptor_probability: float = decryptor_details[0].probability  # +?% вероятность успеха
            decryptor_runs: int = decryptor_details[0].runs  # +? число прогонов проекта
            decryptor_time: float = decryptor_details[0].time_efficiency  # +?% экономия времени производства
            decryptor_required: bool = decryptor_details[1]

        # ------------------------------------------------------
        # расчёт плана инвента
        # ------------------------------------------------------

        invent_plan: ConveyorDemands.InventPlan = ConveyorDemands.InventPlan(
            copied_bpc,
            copying,
            invention,
            invented_product,
            invented_bpc,
            None if decryptor_required is None else decryptor_details[0],
            decryptor_required)

        # ------------------------------------------------------
        # расчёт длительности инвента
        # ------------------------------------------------------

        # выбираем максимальную длительность инвента для данного вида продукта:
        #  * все батлы и батлкрузеры инвентим не дольше, чем 4 суток
        #  * все остальные предметы не дольше 2х суток
        product_market_group: typing.Optional[db.QSwaggerMarketGroup] = \
            qid.there_is_market_group_in_chain(
                invented_bpc.manufacturing.product.product_type,
                {1374,  # Battlecruisers (копирка 1:29, инвент 1д 02:28 => 4 суток для 3х прогонов)
                 1376,  # Battleships (копирка 2:33, инвент 1д 07:44 => 4 суток для 3х прогонов)
                 1080,  # Marauders (копирка 1:47, инвент 1д 07:44 => 2 суток для 1х прогона)
                 })
        if product_market_group:
            if product_market_group.group_id == 1080:
                # марадёры слишком дорогие в постройке, поэтому 1 сутки округлятся до минимальной
                # длительности с тем, чтобы скрафтилось точное количество кораблей в производстве
                invent_plan.invention_days_max = 1
            else:
                invent_plan.invention_days_max = 4
        else:
            invent_plan.invention_days_max = 2

        # ------------------------------------------------------
        # расчёт количество прогонов инвента
        # ------------------------------------------------------

        # считаем длительность инвента одной копии с одним прогоном
        # 30% бонус сооружения, 15% навыки и импланты (минимально необходимый уровень)
        invent_plan.invent_1x1_run_time = ((invention.time * (1 - 0.3)) * (1 - 0.15))
        # считаем кол-во прогонов копий чертежей, которые необходимо выбрать при копирке
        # (относительно 2х суток)
        invent_plan.max_invent_runs_per_days = math.floor(
            (86400 * invent_plan.invention_days_max) / invent_plan.invent_1x1_run_time)
        invent_plan.max_invent_runs_per_days = max(1, invent_plan.max_invent_runs_per_days)

        # ------------------------------------------------------
        # определение вероятности успеха инвента
        # ------------------------------------------------------

        """
        * 18% jump freighters; 22% battleships; 26% cruisers, BCs, industrial, mining barges;
          30% frigate hull, destroyer hull; 34% modules, ammo, drones, rigs
        * Tech 3 cruiser hulls and subsystems have 22%, 30% or 34% chance depending on artifact used
        * Tech 3 destroyer hulls have 26%, 35% or 39% chance depending on artifact used
        ---
        рекомендации к минимальным скилам: 3+3+3 (27..30% навыки и импланты)
        ---
        Invention_Chance =
          Base_Chance *
          (1 + ((Encryption_Skill_Level / 40) +
                ((Datacore_1_Skill_Level + Datacore_2_Skill_Level) / 30)
               )
          ) * Decryptor_Modifier
        """
        invent_plan.invent_1xN_probability = \
            invented_product.probability * \
            1.275 * \
            (1.0 + decryptor_probability)
        """
        limit                   N runs        + decryptor_runs
        ---------  -------------------  ----------------------
        200 need                    10                    10+1
        100%                 200/10=20            200/11=18.18
        43%        20/43%=46.14 copies  18.18/43%=34.95 copies
        ---------  -------------------  ----------------------
        2 need                       1                     1+1
        100%                     2/1=2                   2/2=1
        43%          2/43%=4.65 copies       1/43%=2.33 copies
        ---------  -------------------  ----------------------
        5 need                       1                     1+1
        100%                     5/1=5                 5/2=2.5
        43%         5/43%=11.63 copies     2.5/43%=5.81 copies
        ---------  -------------------  ----------------------
        10 need                      1
        100%                   10/1=10
        48%        10/48%=20.83 copies
        ---------  -------------------------------------------
        140'000 need                                      10+0
        100%                            140'000/(10*5'000)=2.8
        48%               (140'000/(10*5'000))/43%=6.51 copies
        ---------  -------------------------------------------
        """

        # -----------------------------------------------------
        # расчёт ориентировочного кол-ва Т2-продукции из копий
        # ------------------------------------------------------

        # учитываем вероятность успеха инвента T2 чертежей и считаем ориентировочное количество
        # T2-продукции, которая может быть получена из C копий с 1 прогонами:
        invent_plan.invent_Cx1_runs = \
            (math.ceil(
                product.requirement.limit /
                ((invented_product.quantity + decryptor_runs) * invented_bpc.manufacturing.quantity)
            )) / \
            invent_plan.invent_1xN_probability

        # ------------------------------------------------------
        # расчёт количества копий чертежей/штук по N прогонов
        # ------------------------------------------------------

        # поскольку нам необходимо произвести X единиц продукции (в соответствии с ограничениями
        # на производство), то считаем количество копий чертежей/штук по N прогонов
        invent_plan.copy_CxN_runs = math.floor(invent_plan.invent_Cx1_runs / invent_plan.max_invent_runs_per_days)
        invent_plan.copy_CxN_runs = max(1, invent_plan.copy_CxN_runs)

        # ------------------------------------------------------
        # учёт исключительной ситуации (1 копия с min прогонами)
        # ------------------------------------------------------

        if invent_plan.copy_CxN_runs == 1:
            invent_plan.max_invent_runs_per_days = math.floor(invent_plan.invent_Cx1_runs)

        # ------------------------------------------------------
        # расчёт длительности копирки одной копии с N прогонами
        # ------------------------------------------------------

        # 30% бонус сооружения, 36.3% навыки и импланты (минимально необходимый уровень)
        invent_plan.copy_CxN_duration = (
            (invent_plan.copy_CxN_runs * invent_plan.max_invent_runs_per_days * invent_plan.copying.time * (1 - 0.3)) *
            (1 - 0.363)
        )

        return invent_plan


class ManufacturingPlan:
    def __init__(self, product_type_id: int):
        self.product_type_id: int = product_type_id
        self.data: typing.List[ConveyorMaterialRequirements.StackOfBlueprints] = []


class ConveyorCalculations:
    class NthPriority:
        def __init__(self, corporation: db.QSwaggerCorporation):
            self.corporation: db.QSwaggerCorporation = corporation
            self.corp_containers: typing.List[ConveyorSettingsPriorityContainer] = []
            # список контейнеров с чертежами для производства
            self.containers: typing.List[ConveyorSettingsPriorityContainer] = []
            self.container_ids: typing.Set[int] = set()
            # список чертежей, находящихся в этих контейнерах
            self.blueprints: typing.List[db.QSwaggerCorporationBlueprint] = []
            # текущие работы (запущенные из этих контейнеров)
            self.active_jobs: typing.List[db.QSwaggerCorporationIndustryJob] = []
            # отсев чертежей находящихся в завершённых работах
            self.completed_jobs: typing.List[db.QSwaggerCorporationIndustryJob] = []
            # список тех чертежей, запуск которых невозможен
            self.active_blueprint_ids: typing.Set[int] = set()
            # чертежи, которые подходят к текущей activity конвейера (могут быть запущены)
            self.possible_blueprints: typing.List[db.QSwaggerCorporationBlueprint] = []
            # чертежи, которые не подходят к текущей activity конвейера
            self.lost_blueprints: typing.List[db.QSwaggerCorporationBlueprint] = []
            # 2024-05-07 выяснилась проблема: CCP отдают отчёт со сведениями о чертежах в котором чертёж есть,
            # и отдают его 2 дня подряд... а в коробке (в игре) чертежа на самом деле нет, в отчёте с ассетами
            # чертежа тоже нет, ...вот такие фантомные чертежи мешаются в процессе расчётов (фильтрую чертежи более
            # актуальными ассетами)
            self.phantom_blueprints: typing.List[db.QSwaggerCorporationBlueprint] = []
            self.phantom_blueprint_ids: typing.Set[int] = set()
            # список потенциально-задействованных в текущем конвейере материалов (по типу производства)
            self.involved_materials: typing.Set[int] = set()
            #  список "залётных" предметов (материалов и продуктов), которые упали не в ту коробку
            self.lost_asset_items: typing.List[db.QSwaggerCorporationAssetsItem] = []
            #
            # следующие поля валидны и рассчитаны для чертежей из списка [possible_blueprints]
            #
            # материалы, и потребности конвейера (для чертежей, запуск которых возможен)
            self.stock_materials: typing.Optional[ConveyorCorporationStockMaterials] = None
            self.requirements: typing.Optional[typing.List[ConveyorMaterialRequirements.StackOfBlueprints]] = None

        def calc_stage1(
                self,
                # данные (справочники)
                qid: db.QSwaggerDictionary,
                global_dictionary: ConveyorDictionary,
                # анализ чертежей на предмет перепроизводства и нерентабельности
                industry_analysis: ConveyorIndustryAnalysis,
                # настройки генерации отчёта
                settings: ConveyorSettings,
                router_settings: typing.List[RouterSettings],
                all_possible_conveyors: typing.List[ConveyorSettings],
                # список доступных материалов в стоках конвейеров
                available_materials: typing.Dict[ConveyorSettings, ConveyorCorporationStockMaterials],
                # список продукции для производства без учёта приоритетов (список сквозной)
                manufacturing_plan: typing.Dict[int, ManufacturingPlan]):
            # инициализируем интервал отсеивания фантомных чертежей из списка corporation blueprints
            phantom_timedelta = datetime.timedelta(hours=3)

            # получаем список контейнеров с чертежами для производства
            self.container_ids: typing.Set[int] = set([_.container_id for _ in self.corp_containers])
            # получаем список чертежей, находящихся в этих контейнерах
            self.blueprints: typing.List[db.QSwaggerCorporationBlueprint] = \
                [b for b in self.corporation.blueprints.values() if b.location_id in self.container_ids]
            # проверяем текущие работы (запущенные из этих контейнеров),
            # если чертёж находится в активных работах, то им пользоваться нельзя
            self.active_jobs: typing.List[db.QSwaggerCorporationIndustryJob] = \
                [j for j in self.corporation.industry_jobs_active.values()
                 if j.blueprint_location_id in self.container_ids]
            # также, если чертёж находится в завершённых работах, то им тоже пользоваться нельзя
            self.completed_jobs: typing.List[db.QSwaggerCorporationIndustryJob] = \
                [j for j in self.corporation.industry_jobs_completed.values() if
                 j.blueprint_location_id in self.container_ids]
            # составляем новый (уменьшенный) список тех чертежей, запуск которых невозможен
            self.active_blueprint_ids: typing.Set[int] = \
                set([j.blueprint_id for j in self.active_jobs])
            # сохраняем в глобальный справочник идентификаторы предметов для работы с ними динамическим образом
            global_dictionary.load_type_ids(set([_.type_id for _ in self.blueprints]))
            global_dictionary.load_type_ids(set([_.blueprint_type_id for _ in self.active_jobs]))
            global_dictionary.load_type_ids(set([_.product_type_id for _ in self.active_jobs]))
            global_dictionary.load_type_ids(set([_.blueprint_type_id for _ in self.completed_jobs]))
            global_dictionary.load_type_ids(set([_.product_type_id for _ in self.completed_jobs]))
            # отсеиваем те чертежи, которые не подходят к текущей activity конвейера
            self.possible_blueprints: typing.List[db.QSwaggerCorporationBlueprint] = []
            self.lost_blueprints: typing.List[db.QSwaggerCorporationBlueprint] = []
            for b in self.blueprints:
                possible: bool = False
                lost: bool = False
                for _a in settings.activities:
                    a: db.QSwaggerActivityCode = _a
                    # проверка, что в коробку research не попали копии
                    if b.is_copy and a in (db.QSwaggerActivityCode.COPYING,
                                           db.QSwaggerActivityCode.RESEARCH_TIME,
                                           db.QSwaggerActivityCode.RESEARCH_MATERIAL):
                        lost, possible = True, False
                        break
                    # проверка, что в коробку invent не попали оригиналы
                    if b.is_original and a == db.QSwaggerActivityCode.INVENTION:
                        lost, possible = True, False
                        break
                    # проверка, что чертёж имеет смысл исследовать
                    if a in (db.QSwaggerActivityCode.RESEARCH_TIME,
                             db.QSwaggerActivityCode.RESEARCH_MATERIAL):
                        if b.time_efficiency == 20 and b.material_efficiency == 10:
                            lost, possible = True, False
                            break
                    # проверка, что в БД есть сведения о чертеже
                    if b.blueprint_type is None:
                        lost, possible = True, False
                        break
                    # проверка, что чертёж можно запускать в работу с выбранной activity
                    activity = b.blueprint_type.get_activity(activity_id=a.to_int())
                    if activity:
                        if b.item_id not in self.active_blueprint_ids:
                            possible = True
                    else:
                        lost = True
                if possible:
                    self.possible_blueprints.append(b)
                elif lost:
                    self.lost_blueprints.append(b)
            # 2024-05-07 выяснилась проблема: CCP отдают отчёт со сведениями о чертежах в котором чертёж есть,
            # и отдают его 2 дня подряд... а в коробке (в игре) чертежа на самом деле нет, в отчёте с ассетами
            # чертежа тоже нет, ...вот такие фантомные чертежи мешаются в процессе расчётов (фильтрую чертежи более
            # актуальными ассетами)
            self.phantom_blueprints: typing.List[db.QSwaggerCorporationBlueprint] = []
            if self.possible_blueprints:
                # внимание! для поиска фантомных чертежей ассеты должны загружаться вместе с чертежами, т.е.
                # при загрузке ассетов надо использовать флаг load_asseted_blueprints=True
                self.phantom_blueprint_ids: typing.Set[int] = set()
                for p in self.possible_blueprints:
                    a: db.QSwaggerCorporationAssetsItem = self.corporation.assets.get(p.item_id)
                    if a is not None: continue
                    # если в ассетах чертежа нет, то это плохой признак
                    # надо решать дилемму: чертежа уже нет, или всё ещё нет?
                    b: db.QSwaggerCorporationBlueprint = self.corporation.blueprints.get(p.item_id)
                    if (b.updated_at + phantom_timedelta) < qid.eve_now:
                        self.phantom_blueprint_ids.add(b.item_id)
                        self.phantom_blueprints.append(b)
                # корректируем список возможных к постройке чертежей (вычитаем фантомные)
                if self.phantom_blueprint_ids:
                    self.possible_blueprints: typing.List[db.QSwaggerCorporationBlueprint] = \
                        [b for b in self.possible_blueprints if b.item_id not in self.phantom_blueprint_ids]
            # составляем список "залётных" чертежей, которые упали не в ту коробку
            if self.lost_blueprints:
                self.lost_blueprints: typing.List[db.QSwaggerCorporationBlueprint] = \
                    [b for b in self.lost_blueprints if b.item_id not in self.active_blueprint_ids]
            # составляем список потенциально-задействованных в текущем конвейере материалов (по типу производства)
            self.involved_materials = set(
                itertools.chain.from_iterable([global_dictionary.involved_materials[_] for _ in settings.activities]))
            # надо придумать как от избавиться от костыля (в коробке с инвентом хранятся ассеты для копирки)
            if db.QSwaggerActivityCode.INVENTION in settings.activities:
                self.involved_materials |= global_dictionary.involved_materials[db.QSwaggerActivityCode.COPYING]
            # составляем список "залётных" предметов (материалов и продуктов), которые упали не в ту коробку
            self.lost_asset_items: typing.List[db.QSwaggerCorporationAssetsItem] = []
            for _a in self.corporation.assets.values():
                a: db.QSwaggerCorporationAssetsItem = _a
                if a.location_id not in self.container_ids: continue
                # проверка справочника категорий/групп, к которым относятся чертежи
                if a.item_type.group and a.item_type.group.category_id == 9: continue  # 9 = Blueprints
                # не всякий чертёж есть в blueprints (м.б. только в assets), т.ч. проверяем цепочку market_groups
                if settings.same_stock_container:
                    # в случае, если коробка является стоком, то в ней разрешено держать все возможные предметы,
                    # соответствующие текущей activity
                    if a.type_id in self.involved_materials:
                        continue
                    elif db.QSwaggerActivityCode.INVENTION in settings.activities:
                        if a.item_type.group_id == 1304:  # 1304 = Generic Decryptor
                            continue
                # если коробка не является стоком, то в ней ничего не должно валяться, кроме чертежей
                # (конвейер не свалка, д.б. порядок)
                self.lost_asset_items.append(a)
            # расчёт кол-ва материалов, и потребностей конвейера (для чертежей, запуск которых возможен)
            if self.possible_blueprints:
                # анализируем чертежи на предмет перепроизводства (список possible чертежей не сокращаем)
                industry_analysis.analyse_industry(
                    qid,
                    global_dictionary,
                    all_possible_conveyors,
                    settings,
                    self.possible_blueprints)
                # получаем количество материалов в стоке выбранного конвейера
                self.stock_materials: ConveyorCorporationStockMaterials = available_materials.get(settings)
                # считаем потребности конвейера
                self.requirements: typing.List[ConveyorMaterialRequirements.StackOfBlueprints] = \
                    calc_corp_conveyor(
                        # данные (справочники)
                        qid,
                        # анализ чертежей на предмет перепроизводства и нерентабельности
                        industry_analysis,
                        # настройки генерации отчёта
                        router_settings,
                        settings,
                        # ассеты стока (материалы для расчёта возможностей и потребностей конвейера
                        self.stock_materials,
                        # список чертежей, которые необходимо обработать
                        self.possible_blueprints)
                # сохраняем в глобальный справочник идентификаторы предметов для работы с ними динамическим образом
                global_dictionary.load_requirements(self.requirements)

    class Prioritized:
        def __init__(self, corporation: db.QSwaggerCorporation, conveyor_settings: ConveyorSettings):
            self.conveyor_settings: ConveyorSettings = conveyor_settings
            self.data: ConveyorCalculations.NthPriority = ConveyorCalculations.NthPriority(corporation)

    def __init__(self):
        # инициализируем основные дескрипторы для расчётов
        self.corporation: typing.Optional[db.QSwaggerCorporation] = None
        # контейнеры, сгруппированные по приоритетам
        # (справочник по номерам приоритетов и типам конвейера)
        self.prioritized: typing.Dict[int, typing.Dict[ConveyorSettings, ConveyorCalculations.Prioritized]] = {}
        # план производства составленный из списка чертежей за вычетом настроек лимита (перепроизводства)
        # (справочник по типам конвейера и номерам продуктов)
        self.manufacturing_plan: typing.Dict[ConveyorSettings, typing.Dict[int, ConveyorCalculations.ManufacturingPlan]] = {}

    def calc_corp_conveyors(
            self,
            # данные (справочники)
            qid: db.QSwaggerDictionary,
            global_dictionary: ConveyorDictionary,
            # анализ чертежей на предмет перепроизводства
            industry_analysis: ConveyorIndustryAnalysis,
            # настройки генерации отчёта
            router_settings: typing.List[RouterSettings],
            conveyor_settings: typing.List[ConveyorSettings],
            # список доступных материалов в стоках конвейеров
            available_materials: typing.Dict[ConveyorSettings, ConveyorCorporationStockMaterials]) -> None:
        # проверка, пусты ли настройки конвейера?
        if len(conveyor_settings) == 0: return

        # проверка, принадлежат ли настройки конвейера лишь одной корпорации?
        # если нет, то... надо добавить здесь какой-то сворачиваемый список?
        corporations: typing.Set[int] = set([s.corporation.corporation_id for s in conveyor_settings])
        if not len(corporations) == 1:
            raise Exception("Unsupported mode: multiple corporations in a single conveyor")
        # получаем ссылку на единственную корпорацию
        self.corporation: db.QSwaggerCorporation = conveyor_settings[0].corporation

        # группируем контейнеры по приоритетам
        self.prioritized: typing.Dict[int, typing.Dict[ConveyorSettings, ConveyorCalculations.Prioritized]] = {}
        for s in conveyor_settings:
            for container in s.containers_sources:
                p0: typing.Optional[typing.Dict[ConveyorSettings, ConveyorCalculations.Prioritized]] = \
                    self.prioritized.get(container.priority)
                if not p0:
                    self.prioritized[container.priority] = {}
                    p0: typing.Optional[typing.Dict[ConveyorSettings, ConveyorCalculations.Prioritized]] = \
                        self.prioritized.get(container.priority)
                p1: typing.Optional[ConveyorCalculations.Prioritized] = p0.get(s)
                if not p1:
                    p1: ConveyorCalculations.Prioritized = ConveyorCalculations.Prioritized(self.corporation, s)
                    p0[s] = p1
                p1.data.corp_containers.append(container)

        # группируем продукция конвейеров без учёта производства
        self.manufacturing_plan: typing.Dict[ConveyorSettings, typing.Dict[int, ConveyorCalculations.ManufacturingPlan]] = {}
        for s in conveyor_settings:
            self.manufacturing_plan[s] = {}

        # перебираем сгруппированные преоритизированные группы
        for priority in sorted(self.prioritized.keys()):
            p0 = self.prioritized.get(priority)
            for p1 in p0.values():
                p1.data.calc_stage1(
                    qid,
                    global_dictionary,
                    industry_analysis,
                    p1.conveyor_settings,
                    router_settings,
                    conveyor_settings,
                    available_materials,
                    self.manufacturing_plan[p1.conveyor_settings])


# ConveyorDictionary - долговременный справочник материалов конвейера, хранится долго и накапливает информацию из
# экземпляров QSwaggerTypeId
class ConveyorDictionary:
    def __init__(self, qid: db.QSwaggerDictionary):
        # сохраняем ссылку на ПОЛНЫЙ справочник загруженный из БД
        self.qid: db.QSwaggerDictionary = qid
        # подготовка списка-справочника, который будет хранить идентификаторы всех продуктов, используемых конвейером
        self.materials: typing.Set[int] = set()
        # подготовка списка-справочника, который будет хранить используемые материалы в различных activity (скопом)
        self.involved_materials: typing.Dict[db.QSwaggerActivityCode, typing.Set[int]] = {}
        self._fill_involved_materials()

    def __del__(self):
        # уничтожаем свой список-справочник, остальные (не наши) не трогаем
        del self.materials

    def _fill_involved_materials(self):
        self.involved_materials: typing.Dict[db.QSwaggerActivityCode, typing.Set[int]] = {
            db.QSwaggerActivityCode.MANUFACTURING: set(),
            db.QSwaggerActivityCode.INVENTION: set(),
            db.QSwaggerActivityCode.COPYING: set(),
            db.QSwaggerActivityCode.RESEARCH_MATERIAL: set(),
            db.QSwaggerActivityCode.RESEARCH_TIME: set(),
            db.QSwaggerActivityCode.REACTION: set()
        }
        for by_products in self.qid.sde_activities.values():
            for activity in by_products:
                ids: typing.Set[int] = set([_.material_id for _ in activity.materials.materials])
                if isinstance(activity, db.QSwaggerBlueprintManufacturing):
                    a: db.QSwaggerActivityCode = db.QSwaggerActivityCode.MANUFACTURING
                elif isinstance(activity, db.QSwaggerBlueprintInvention):
                    a: db.QSwaggerActivityCode = db.QSwaggerActivityCode.INVENTION
                elif isinstance(activity, db.QSwaggerBlueprintCopying):
                    a: db.QSwaggerActivityCode = db.QSwaggerActivityCode.COPYING
                elif isinstance(activity, db.QSwaggerBlueprintResearchMaterial):
                    a: db.QSwaggerActivityCode = db.QSwaggerActivityCode.RESEARCH_MATERIAL
                elif isinstance(activity, db.QSwaggerBlueprintResearchTime):
                    a: db.QSwaggerActivityCode = db.QSwaggerActivityCode.RESEARCH_TIME
                elif isinstance(activity, db.QSwaggerBlueprintReaction):
                    a: db.QSwaggerActivityCode = db.QSwaggerActivityCode.REACTION
                else:
                    raise Exception("Unknown type of activity")
                involved: typing.Set[int] = self.involved_materials.get(a)
                involved.update(ids)

    def load_router_settings(self, router_settings: typing.List[RouterSettings]) -> None:
        for r in router_settings:
            self.materials = self.materials | set(r.output)

    def load_type_ids(self, type_ids: typing.Set[int]):
        self.materials = self.materials | set(type_ids)

    def load_available_materials(self, available_materials: typing.Dict[ConveyorSettings, ConveyorCorporationStockMaterials]):
        for stocks in available_materials.values():
            for materials in stocks.stock_materials.values():
                self.load_type_ids(materials.keys())

    def load_ready_products(self, ready_products: typing.Dict[RouterSettings, ConveyorCorporationOutputProducts]):
        for products in ready_products.values():
            self.load_type_ids(products.output_products.keys())
            self.load_type_ids(products.lost_products.keys())

    def load_requirements(self, requirements: typing.List[ConveyorMaterialRequirements.StackOfBlueprints]):
        for stack in requirements:
            for materials in stack.required_materials_for_single.values():
                self.load_type_ids(set([_.material_id for _ in materials]))

    def load_demands(self, demands: ConveyorDemands):
        self.load_type_ids(set([_.requirement.type_id for _ in demands.conveyor_requirements]))
