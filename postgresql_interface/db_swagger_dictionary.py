# -*- encoding: utf-8 -*-
import typing

from .db_swagger_cache import *
from .db_swagger_translator import QSwaggerTranslator


class QSwaggerDictionary:
    def __init__(self, qit: QSwaggerTranslator):
        self.__qit: QSwaggerTranslator = qit
        # справочники
        self.sde_market_groups: typing.Dict[int, QSwaggerMarketGroup] = {}
        self.sde_type_ids: typing.Dict[int, QSwaggerTypeId] = {}
        self.sde_blueprints: typing.Dict[int, QSwaggerBlueprint] = {}
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
        del self.sde_blueprints
        del self.sde_type_ids
        del self.sde_market_groups

    def disconnect_from_translator(self):
        # после отключения использовать load_xxx методы запрещено
        self.__qit = None

    def load_market_groups(self) -> typing.Dict[int, QSwaggerMarketGroup]:
        if self.sde_market_groups:
            # на элементы этого справочника ссылаются другие справочники (недопустимо подменять справочник в рантайме)
            raise Exception("Unable to load market groups twice")
        self.sde_market_groups = self.__qit.get_market_groups()
        return self.sde_market_groups

    def get_type_id(self, type_id: int) -> typing.Optional[QSwaggerTypeId]:
        cached_type_id: QSwaggerTypeId = self.sde_type_ids.get(type_id)
        return cached_type_id

    def load_published_type_ids(self) -> typing.Dict[int, QSwaggerTypeId]:
        if self.sde_type_ids:
            # на элементы этого справочника ссылаются другие справочники (недопустимо подменять справочник в рантайме)
            raise Exception("Unable to load type ids twice")
        self.sde_type_ids = self.__qit.get_published_type_ids()
        return self.sde_type_ids

    def load_blueprints(self) -> typing.Dict[int, QSwaggerBlueprint]:
        if self.sde_blueprints:
            # на элементы этого справочника ссылаются другие справочники (недопустимо подменять справочник в рантайме)
            raise Exception("Unable to load blueprints twice")
        self.sde_blueprints = self.__qit.get_blueprints(
            # справочники
            self.sde_type_ids)
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

    def load_station(self, station_name: str) -> typing.Optional[QSwaggerStation]:
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
        corporation.container_ids = [int(a.item_id) for a in corporation.assets.values() if a.item_type and a.item_type.market_group_id in {1651, 1652, 1653, 1657, 1658}]
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

    def load_corporation_industry_jobs(
            self,
            corporation: QSwaggerCorporation,
            load_unknown_type_blueprints=False) -> typing.Dict[int, QSwaggerCorporationIndustryJob]:
        if not isinstance(corporation, QSwaggerCorporation):
            raise Exception("Illegal corporation descriptor")
        corporation.industry_jobs = self.__qit.get_corporation_industry_jobs(
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
        return corporation.industry_jobs
