# -*- encoding: utf-8 -*-
import typing
import datetime
import pytz

from .db_swagger_cache import *
from .db_swagger_translator import QSwaggerTranslator


class QSwaggerDictionary:
    def __init__(self, qit: QSwaggerTranslator):
        self.__qit: QSwaggerTranslator = qit
        # справочники
        self.eve_now = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
        self.sde_lifetime: typing.Dict[typing.Tuple[str, int], datetime.datetime] = {}  # what:corporation_id
        self.sde_market_groups: typing.Dict[int, QSwaggerMarketGroup] = {}
        self.sde_categories: typing.Dict[int, QSwaggerCategory] = {}
        self.sde_groups: typing.Dict[int, QSwaggerGroup] = {}
        self.sde_type_ids: typing.Dict[int, QSwaggerTypeId] = {}
        self.sde_blueprints: typing.Dict[int, QSwaggerBlueprint] = {}
        self.sde_activities: typing.Dict[int, typing.List[QSwaggerActivity]] = {}  # id=product_id
        # публичные сведения (пилоты, структуры, станции)
        self.characters: typing.Dict[int, QSwaggerCharacter] = {}
        self.stations: typing.Dict[int, QSwaggerStation] = {}
        # корпоративные ассеты и данные
        self.corporations: typing.Dict[int, QSwaggerCorporation] = {}

    def __del__(self):
        # корпоративные ассеты и данные
        del self.corporations
        # публичные сведения (пилоты, структуры, станции)
        del self.stations
        del self.characters
        # справочники
        del self.sde_activities
        del self.sde_blueprints
        del self.sde_type_ids
        del self.sde_groups
        del self.sde_categories
        del self.sde_market_groups
        del self.sde_lifetime

    def disconnect_from_translator(self):
        # после отключения использовать load_xxx методы запрещено
        self.__qit = None

    def load_lifetime(self, corporation_ids: typing.List[int]) -> typing.Dict[typing.Tuple[str, int], datetime.datetime]:
        self.sde_lifetime = self.__qit.get_lifetime(corporation_ids)
        return self.sde_lifetime

    def get_market_group(self, market_group_id: int) -> typing.Optional[QSwaggerMarketGroup]:
        cached_market_group: QSwaggerMarketGroup = self.sde_market_groups.get(market_group_id)
        return cached_market_group

    def load_market_groups(self) -> typing.Dict[int, QSwaggerMarketGroup]:
        if self.sde_market_groups:
            # на элементы этого справочника ссылаются другие справочники (недопустимо подменять справочник в рантайме)
            raise Exception("Unable to load market groups twice")
        self.sde_market_groups = self.__qit.get_market_groups()
        return self.sde_market_groups

    def get_category(self, category_id: int) -> typing.Optional[QSwaggerCategory]:
        cached_category: QSwaggerCategory = self.sde_categories.get(category_id)
        return cached_category

    def load_universe_categories(self) -> typing.Dict[int, QSwaggerCategory]:
        if self.sde_categories:
            # на элементы этого справочника ссылаются другие справочники (недопустимо подменять справочник в рантайме)
            raise Exception("Unable to load categories twice")
        self.sde_categories = self.__qit.get_universe_categories()
        return self.sde_categories

    def get_group(self, group_id: int) -> typing.Optional[QSwaggerGroup]:
        cached_group: QSwaggerGroup = self.sde_groups.get(group_id)
        return cached_group

    def load_universe_groups(self) -> typing.Dict[int, QSwaggerGroup]:
        if self.sde_groups:
            # на элементы этого справочника ссылаются другие справочники (недопустимо подменять справочник в рантайме)
            raise Exception("Unable to load groups twice")
        if not self.sde_categories:  # загружайте предварительно категории
            raise Exception("You should load universe categories firstly")
        self.sde_groups = self.__qit.get_universe_groups(
            # справочники
            self.sde_categories
        )
        return self.sde_groups

    def get_type_id(self, type_id: int) -> typing.Optional[QSwaggerTypeId]:
        cached_type_id: QSwaggerTypeId = self.sde_type_ids.get(type_id)
        return cached_type_id

    def load_published_type_ids(self) -> typing.Dict[int, QSwaggerTypeId]:
        if self.sde_type_ids:
            # на элементы этого справочника ссылаются другие справочники (недопустимо подменять справочник в рантайме)
            raise Exception("Unable to load type ids twice")
        self.sde_type_ids = self.__qit.get_type_ids(
            # справочники
            self.sde_market_groups,
            self.sde_groups,
            only_published=True)
        return self.sde_type_ids

    def load_all_known_type_ids(self) -> typing.Dict[int, QSwaggerTypeId]:
        if self.sde_type_ids:
            # на элементы этого справочника ссылаются другие справочники (недопустимо подменять справочник в рантайме)
            raise Exception("Unable to load type ids twice")
        self.sde_type_ids = self.__qit.get_type_ids(
            # справочники
            self.sde_market_groups,
            self.sde_groups,
            only_published=False)
        return self.sde_type_ids

    def get_blueprint(self, blueprint_type_id: int) -> typing.Optional[QSwaggerBlueprint]:
        cached_blueprint: QSwaggerBlueprint = self.sde_blueprints.get(blueprint_type_id)
        return cached_blueprint

    def get_activities_by_product(self, product_type_id: int) -> typing.Optional[typing.List[QSwaggerActivity]]:
        cached_activities: typing.List[QSwaggerActivity] = self.sde_activities.get(product_type_id)
        return cached_activities

    def load_blueprints(self) -> typing.Dict[int, QSwaggerBlueprint]:
        if self.sde_blueprints:
            # на элементы этого справочника ссылаются другие справочники (недопустимо подменять справочник в рантайме)
            raise Exception("Unable to load blueprints twice")
        self.sde_blueprints = self.__qit.get_blueprints(
            # справочники
            self.sde_type_ids)

        def push(type_id: int, activity: QSwaggerActivity) -> None:
            l = self.sde_activities.get(type_id)
            if not l:
                self.sde_activities[type_id] = [activity]
            else:
                l.append(activity)

        for b in self.sde_blueprints.values():
            if b.manufacturing:
                push(b.manufacturing.product_id, b.manufacturing)
            if b.invention:
                for p in b.invention.products:
                    push(p.product_id, b.invention)
            if b.copying:
                push(b.copying.product_id, b.copying)
            if b.reaction:
                push(b.reaction.product_id, b.reaction)
        return self.sde_blueprints

    def get_corporation(self, corporation_id: int) -> typing.Optional[QSwaggerCorporation]:
        cached_corporation: typing.Optional[QSwaggerCorporation] = self.corporations.get(corporation_id)
        return cached_corporation

    def get_corporation_by_name(self, corporation_name: str) -> typing.Optional[QSwaggerCorporation]:
        cached_corporation: typing.Optional[QSwaggerCorporation] = next((c for c in self.corporations.values() if c.corporation_name == corporation_name), None)
        return cached_corporation

    def load_corporation(self, corporation_name: str) -> typing.Optional[QSwaggerCorporation]:
        # поиск ранее загруженной корпорации
        cached_corporation: typing.Optional[QSwaggerCorporation] = self.get_corporation_by_name(corporation_name)
        if cached_corporation:
            return cached_corporation
        # загрузка сведений о корпорации из БД
        corporation_id: int = self.__qit.get_corporation_id(corporation_name)
        if not corporation_id:
            # raise Exception(
            #     "There are no corporation '{}' in the database, please preload data".format(corporation_name))
            return None
        # сохранение загруженных сведений о корпорации в кеш
        cached_corporation: QSwaggerCorporation = QSwaggerCorporation(corporation_id, corporation_name)
        self.corporations[corporation_id] = cached_corporation
        return cached_corporation

    def get_character(self, character_id: int) -> typing.Optional[QSwaggerCharacter]:
        cached_character: typing.Optional[QSwaggerCharacter] = self.corporations.get(character_id)
        return cached_character

    def get_character_by_name(self, character_name: str) -> typing.Optional[QSwaggerCharacter]:
        cached_character: typing.Optional[QSwaggerCharacter] = next((c for c in self.characters.values() if c.character_name == character_name), None)
        return cached_character

    def load_character(self, character_name: str) -> typing.Optional[QSwaggerCharacter]:
        # поиск ранее загруженного пилота
        cached_character: typing.Optional[QSwaggerCharacter] = self.get_character_by_name(character_name)
        if cached_character:
            return cached_character
        # загрузка сведений о пилоте из БД
        cached_character: typing.Optional[QSwaggerCharacter] = self.__qit.get_character(character_name)
        if not cached_character:
            # raise Exception(
            #     "There are no character '{}' in the database, please preload data".format(character_name))
            return None
        # сохранение загруженных сведений о пилоте в кеш
        self.characters[cached_character.character_id] = cached_character
        return cached_character

    def get_station(self, station_id: int) -> typing.Optional[QSwaggerStation]:
        cached_station: typing.Optional[QSwaggerStation] = self.stations.get(station_id)
        return cached_station

    def get_station_by_name(self, station_name: str) -> typing.Optional[QSwaggerStation]:
        cached_station: typing.Optional[QSwaggerStation] = next((s for s in self.stations.values() if s.station_name == station_name), None)
        return cached_station

    def load_stations(
            self,
            station_ids: typing.Union[typing.List[int], typing.Set[int]]) -> typing.Dict[int, QSwaggerStation]:
        # поиск ранее загруженной станции (структуры, фабрики)
        if isinstance(station_ids, list):
            ids: typing.List[int] = list(set(station_ids) - self.stations.keys())
        elif isinstance(station_ids, set):
            ids: typing.List[int] = list(station_ids - self.stations.keys())
        else:
            raise Exception("Unable to determine type of station ids")
        # проверка исключений
        if not ids:
            return {}
        # загрузка сведений о станции из БД
        cached_stations: typing.Dict[int, QSwaggerStation] = self.__qit.get_stations(ids, self.sde_type_ids)
        if not cached_stations:
            # raise Exception(
            #     "There are no station '{}' in the database, please preload data".format(station_name))
            return {}
        # сохранение загруженных сведений о станции в кеш
        for s in cached_stations.values():
            self.stations[s.station_id] = s
        return cached_stations

    def load_station_by_name(self, station_name: str) -> typing.Optional[QSwaggerStation]:
        # поиск ранее загруженной станции (структуры, фабрики)
        cached_station: typing.Optional[QSwaggerStation] = next((s for s in self.stations.values() if s.station_name == station_name), None)
        if cached_station:
            return cached_station
        # загрузка сведений о станции из БД
        cached_station: typing.Optional[QSwaggerStation] = self.__qit.get_station(station_name, self.sde_type_ids)
        if not cached_station:
            # raise Exception(
            #     "There are no station '{}' in the database, please preload data".format(station_name))
            return None
        # сохранение загруженных сведений о станции в кеш
        self.stations[cached_station.station_id] = cached_station
        return cached_station

    def load_corporation_assets(
            self,
            corporation: QSwaggerCorporation,
            load_unknown_type_assets=False,
            load_asseted_blueprints=False) -> typing.Dict[int, QSwaggerCorporationAssetsItem]:
        if not isinstance(corporation, QSwaggerCorporation):
            raise Exception("Illegal corporation descriptor")
        corporation.assets = self.__qit.get_corporation_assets(
            # идентификаторы
            corporation.corporation_id,
            # справочники
            self.sde_type_ids,
            # настройки
            load_unknown_type_assets=load_unknown_type_assets,
            load_asseted_blueprints=load_asseted_blueprints)
        # поиск Secure Containers, Audit Log Containers, Freight Containers, Standard Containers, Station Containers
        corporation.container_ids = [
            int(a.item_id)
            for a in corporation.assets.values()
            # 12 = Cargo Container
            # 448 = Audit Log Secure Container
            # 649 Freight Container
            # исправь также get_corporation_container_places
            if a.item_type and a.item_type.group_id in {12, 448, 649}]
        return corporation.assets

    def load_corporation_blueprints(
            self,
            corporation: QSwaggerCorporation,
            load_unknown_type_blueprints=False) -> typing.Dict[int, QSwaggerCorporationBlueprint]:
        if not isinstance(corporation, QSwaggerCorporation):
            raise Exception("Illegal corporation descriptor")
        corporation.blueprints = self.__qit.get_corporation_blueprints(
            # идентификаторы
            corporation.corporation_id,
            # справочники
            self.sde_blueprints,
            # настройки
            load_unknown_type_blueprints=load_unknown_type_blueprints)
        return corporation.blueprints

    def load_corporation_container_places(
            self,
            corporation: QSwaggerCorporation) -> None:
        if not isinstance(corporation, QSwaggerCorporation):
            raise Exception("Illegal corporation descriptor")
        if not corporation.assets and not corporation.blueprints:  # загружайте как минимум ассеты
            raise Exception("You should load assets firstly")
        self.__qit.get_corporation_container_places(
            # идентификаторы
            corporation.corporation_id,
            # справочники
            corporation.assets,
            corporation.blueprints)

    def load_corporation_industry_jobs_active(
            self,
            corporation: QSwaggerCorporation,
            load_unknown_type_blueprints=False) -> typing.Dict[int, QSwaggerCorporationIndustryJob]:
        if not isinstance(corporation, QSwaggerCorporation):
            raise Exception("Illegal corporation descriptor")
        corporation.industry_jobs_active = self.__qit.get_corporation_industry_jobs_active(
            # идентификаторы
            corporation.corporation_id,
            # справочники
            self.sde_type_ids,
            self.sde_blueprints,
            # публичные сведения (пилоты, структуры, станции)
            self.characters,
            self.stations,
            # корпоративные ассеты и данные
            corporation.assets,
            corporation.blueprints,
            # настройки
            load_unknown_type_blueprints=load_unknown_type_blueprints)
        return corporation.industry_jobs_active

    def load_corporation_industry_jobs_completed(
            self,
            corporation: QSwaggerCorporation,
            load_unknown_type_blueprints=False) -> typing.Dict[int, QSwaggerCorporationIndustryJob]:
        if not isinstance(corporation, QSwaggerCorporation):
            raise Exception("Illegal corporation descriptor")
        corporation.industry_jobs_completed = self.__qit.get_corporation_industry_jobs_completed(
            # идентификаторы
            corporation.corporation_id,
            # справочники
            self.sde_type_ids,
            self.sde_blueprints,
            # публичные сведения (пилоты, структуры, станции)
            self.characters,
            self.stations,
            # корпоративные ассеты и данные
            corporation.assets,
            corporation.blueprints,
            # настройки
            load_unknown_type_blueprints=load_unknown_type_blueprints)
        return corporation.industry_jobs_completed

    def load_corporation_orders_active(
            self,
            corporation: QSwaggerCorporation) -> typing.Dict[int, QSwaggerCorporationOrder]:
        if not isinstance(corporation, QSwaggerCorporation):
            raise Exception("Illegal corporation descriptor")
        corporation.orders = self.__qit.get_corporation_orders_active(
            # идентификаторы
            corporation.corporation_id,
            # справочники
            self.sde_type_ids,
            # публичные сведения (пилоты, структуры, станции)
            self.characters,
            self.stations)
        return corporation.orders

    def load_corporation_stations(
            self,
            corporation: QSwaggerCorporation) -> typing.Dict[int, QSwaggerStation]:
        if not isinstance(corporation, QSwaggerCorporation):
            raise Exception("Illegal corporation descriptor")
        if not corporation.assets and not corporation.blueprints:  # загружайте как минимум ассеты
            raise Exception("You should load assets firstly")
        assets_stations: typing.Set[int] = set()
        if corporation.assets:
            assets_stations = set([a.station_id for a in corporation.assets.values() if a.station_id is not None])
        blueprints_stations: typing.Set[int] = set()
        if corporation.blueprints:
            blueprints_stations = set([b.station_id for b in corporation.blueprints.values() if b.station_id is not None])
        market_stations: typing.Set[int] = set()
        if corporation.orders:
            market_stations = set([o.location_id for o in corporation.orders.values() if o.location_id is not None])
        station_ids: typing.Set[int] = assets_stations | blueprints_stations | market_stations
        return self.load_stations(station_ids)

    def get_market_group_chain(self, item_type: QSwaggerTypeId) -> typing.List[int]:
        chain: typing.List[int] = []
        market_group_id: typing.Optional[int] = item_type.market_group_id
        while market_group_id is not None:
            chain.append(market_group_id)
            market_group: QSwaggerMarketGroup = self.get_market_group(market_group_id)
            if not market_group: break
            market_group_id = market_group.parent_id
        return chain

    def there_is_market_group_in_chain(
            self,
            item_type: QSwaggerTypeId,
            market_group_ids: typing.Set[int]) -> typing.Optional[QSwaggerMarketGroup]:
        chain: typing.List[int] = []
        market_group_id: typing.Optional[int] = item_type.market_group_id
        while market_group_id is not None:
            market_group: QSwaggerMarketGroup = self.get_market_group(market_group_id)
            if not market_group: break
            if market_group_id in market_group_ids:
                return market_group
            market_group_id = market_group.parent_id
        return None
