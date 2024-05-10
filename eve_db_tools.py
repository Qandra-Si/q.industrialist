"""
get_db_connection - подключается к БД
auth_pilot_by_name - подключается к ESI Swagger Interface
actualize_xxx - загружает с серверов CCP xxx-данные, например actualize_character,
                и сохраняет полученные данные в БД, если требуется
"""
import sys
import requests
import typing
import datetime
import pytz
import math

import eve_esi_interface as esi
import postgresql_interface as db

from __init__ import __version__


def is_dicts_equal_by_keys(dict1, dict2, keys):
    for key in keys:
        if key in dict1:
            if not (key in dict2):
                return False
        else:
            if not (key in dict2):
                continue
        x = dict1[key]
        y = dict2[key]
        if isinstance(x, float) or isinstance(y, float):
            # 5.0 и 4.99 - False (разные), а 5.0 и 4.999 - True (одинаковые)
            same: bool = math.isclose(x, y, abs_tol=0.00999)
            if not same:
                return False
        elif x != y:
            return False
    return True


class QEntity:
    def __init__(self, db, esi, obj, at):
        """ данные объекта, хранящеося в индексированном справочнике в памяти

        :param db: признак того, что данные имеются в БД (известно, что объект с таким id есть в БД)
        :param esi: признак того, что данные получены с серверов CCP
        :param obj: данные, м.б. None, если не загружены ни с сервера, ни из БД
        :param ext: данные, которые опосредовано связаны с объектом (не загружены с сервера CCP)
        :param at: дата/время последней актуализации кешированных данных (хранящихся в БД)
        """
        self.db: bool = db
        self.esi: bool = esi
        self.obj: typing.Any = obj
        self.ext = None
        self.at: datetime.datetime = at

    def store(self, db, esi, obj, at):
        self.db: bool = db
        self.esi: bool = esi
        self.obj: typing.Any = obj
        self.at: datetime.datetime = at

    def store_ext(self, ext: dict):
        if self.ext:
            self.ext.update(ext)
        else:
            self.ext = ext

    def compare_ext(self, key: str, val) -> bool:
        if val is not None:
            if not self.ext or (self.ext.get(key) != val):
                return False
        else:
            if self.ext and (self.ext.get(key) is not None):
                return False
        return True

    def is_obj_equal(self, data):
        for key in self.obj:
            if not (key in data):
                return False
            elif (data[key] != self.obj[key]):
                return False
        return True

    def is_obj_equal_by_keys(self, data, keys):
        return is_dicts_equal_by_keys(self.obj, data, keys)


class QEntityDepth:
    def __init__(self):
        """ сведения о вложенности данных для отслеживания глубины спуска по зависимостям, с тем, чтобы
        не сталкиваться с ситуацией, когда загрузка данных о корпорации приводит к загрузке данных о
        домашке корпорации, которая в свою очередь снова может привести к загрузке данных о корпорации
        """
        self.urls: typing.List[str] = []

    def push(self, url: str):
        if url in self.urls:
            return False
        self.urls.append(url)
        return True

    def pop(self):
        self.urls.pop()


class QDatabaseTools:
    character_timedelta = datetime.timedelta(days=3)
    corporation_timedelta = datetime.timedelta(days=5)
    universe_station_timedelta = datetime.timedelta(days=7)
    universe_structure_timedelta = datetime.timedelta(days=3)
    corporation_structure_diff = ['corporation_id', 'profile_id']
    corporation_asset_diff = ['quantity', 'location_id', 'location_type', 'location_flag', 'is_singleton']
    corporation_blueprint_diff = ['type_id', 'location_id', 'location_flag', 'quantity', 'time_efficiency',
                                  'material_efficiency', 'runs']
    character_blueprint_diff = ['type_id', 'location_id', 'location_flag', 'quantity', 'time_efficiency',
                                'material_efficiency', 'runs']
    corporation_industry_job_diff = ['status']
    character_industry_job_diff = ['status']
    market_order_diff = ['price', 'volume_remain']
    markets_prices_diff = ['adjusted_price', 'average_price']

    def __init__(self, module_name, client_scope, database_prms, debug):
        """ constructor

        :param module_name: name of Q.Industrialist' module
        :param debug: debug mode to show SQL queries
        """
        self.qidb = db.QIndustrialistDatabase(module_name, debug=debug)
        self.qidb.connect(database_prms)

        self.dbswagger = db.QSwaggerInterface(self.qidb)

        self.esiswagger = None
        self.eve_now = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)

        self.__client_scope = client_scope

        self.__cached_characters: typing.Dict[int, QEntity] = {}
        self.__cached_corporations: typing.Dict[int, QEntity] = {}
        self.__cached_stations: typing.Dict[int, QEntity] = {}
        self.__cached_structures: typing.Dict[int, QEntity] = {}
        self.__cached_corporation_structures: typing.Dict[int, QEntity] = {}
        self.__cached_corporation_assets: typing.Dict[int, typing.Dict[int, QEntity]] = {}
        self.__cached_corporation_assets_names: typing.Dict[int,  typing.Dict[int, str]] = {}
        self.__cached_corporation_blueprints: typing.Dict[int, typing.Dict[int, QEntity]] = {}
        self.__cached_character_blueprints: typing.Dict[int, typing.Dict[int, QEntity]] = {}
        self.__cached_corporation_industry_jobs: typing.Dict[int, typing.Dict[int, QEntity]] = {}
        self.__cached_character_industry_jobs: typing.Dict[int, typing.Dict[int, QEntity]] = {}
        self.__cached_corporation_orders: typing.Dict[int, typing.Dict[int, QEntity]] = {}
        self.__cached_markets_prices: typing.Dict[int, QEntity] = {}
        self.__cached_category_ids: typing.Set[int] = set()
        self.__cached_group_ids: typing.Set[int] = set()
        self.__cached_market_group_ids: typing.Set[int] = set()
        self.__cached_type_ids: typing.Set[int] = set()
        self.__universe_items_with_names: typing.Set[int] = set()
        self.prepare_cache()

        self.depth = QEntityDepth()

    def __del__(self):
        """ destructor
        """
        del self.depth

        del self.__universe_items_with_names
        del self.__cached_type_ids
        del self.__cached_market_group_ids
        del self.__cached_group_ids
        del self.__cached_category_ids
        del self.__cached_markets_prices
        del self.__cached_corporation_orders
        del self.__cached_character_industry_jobs
        del self.__cached_corporation_industry_jobs
        del self.__cached_character_blueprints
        del self.__cached_corporation_blueprints
        del self.__cached_corporation_assets_names
        del self.__cached_corporation_assets
        del self.__cached_corporation_structures
        del self.__cached_structures
        del self.__cached_stations
        del self.__cached_corporations
        del self.__cached_characters

        del self.esiswagger

        del self.dbswagger

        self.qidb.commit()
        self.qidb.disconnect()
        del self.qidb

    def auth_pilot_by_name(self, pilot_name, offline_mode, cache_files_dir, client_id=None):
        # настройка Eve Online ESI Swagger interface
        auth = esi.EveESIAuth(
            '{}/auth_cache'.format(cache_files_dir),
            debug=True)
        client = esi.EveESIClient(
            auth,
            keep_alive=True,
            debug=False,
            logger=True,
            user_agent='Q.Industrialist v{ver}'.format(ver=__version__))
        self.esiswagger = esi.EveOnlineInterface(
            client,
            self.__client_scope,
            cache_dir='{}/esi_cache'.format(cache_files_dir),
            offline_mode=offline_mode)

        authz = self.esiswagger.authenticate(pilot_name, client_id)
        # character_id = authz["character_id"]
        # character_name = authz["character_name"]
        return authz

    # -------------------------------------------------------------------------
    # c a c h e
    # -------------------------------------------------------------------------

    def prepare_cache(self):
        rows = self.dbswagger.get_exist_character_ids()
        for row in rows:
            self.__cached_characters[row[0]] = QEntity(True, False, None, row[1].replace(tzinfo=pytz.UTC))

        rows = self.dbswagger.get_exist_corporation_ids()
        for row in rows:
            self.__cached_corporations[row[0]] = QEntity(True, False, None, row[1].replace(tzinfo=pytz.UTC))

        rows = self.dbswagger.get_exist_universe_station_ids()
        for row in rows:
            self.__cached_stations[row[0]] = QEntity(True, False, None, row[1].replace(tzinfo=pytz.UTC))

        rows = self.dbswagger.get_exist_universe_structure_ids()
        for row in rows:
            self.__cached_structures[row[0]] = QEntity(True, False, None, row[1].replace(tzinfo=pytz.UTC))

        rows = self.dbswagger.get_exist_corporation_structures()
        for row in rows:
            structure_id = row['structure_id']
            updated_at = row['ext']['updated_at'].replace(tzinfo=pytz.UTC)
            del row['ext']
            self.__cached_corporation_structures[structure_id] = QEntity(True, False, row, updated_at)

        self.prepare_corp_cache(
            self.dbswagger.get_exist_corporation_assets(),
            self.__cached_corporation_assets,
            'item_id',
            None
        )

        rows = self.dbswagger.get_exist_corporation_assets_names()
        if rows:
            prev_corporation_id = None
            corporation_cache = None
            for row in rows:
                item_id: int = row[0]
                corporation_id: int = row[1]
                if prev_corporation_id != corporation_id:
                    corporation_cache = self.get_corp_cache(self.__cached_corporation_assets_names, corporation_id)
                    prev_corporation_id = corporation_id
                corporation_cache[item_id] = row[2]

        rows = self.dbswagger.get_last_known_markets_prices()
        if rows:
            for row in rows:
                type_id = row['type_id']
                updated_at = row['ext']['updated_at'].replace(tzinfo=pytz.UTC)
                del row['ext']
                self.__cached_markets_prices[type_id] = QEntity(True, False, row, updated_at)

        # загрузка из БД type_ids, market_group_ids, group_ids, category_ids (в таблицах в БД таких данных может быть
        # больше, чем может выдать ESI, т.к. БД может хранить устаревшие non published товары)
        self.prepare_goods_dictionaries()

    def prepare_goods_dictionaries(self):
        rows = self.dbswagger.get_exist_category_ids()
        if rows:
            self.__cached_category_ids: typing.Set[int] = set([row[0] for row in rows])

        rows = self.dbswagger.get_exist_group_ids()
        if rows:
            self.__cached_group_ids: typing.Set[int] = set([row[0] for row in rows])

        rows = self.dbswagger.get_exist_market_group_ids()
        if rows:
            self.__cached_market_group_ids: typing.Set[int] = set([row[0] for row in rows])

        rows = self.dbswagger.get_exist_type_ids()
        if rows:
            self.__cached_type_ids: typing.Set[int] = set([row[0] for row in rows])

        rows = self.dbswagger.get_universe_items_with_names()
        if rows:
            self.__universe_items_with_names: typing.Set[int] = set([row[0] for row in rows])

    @staticmethod
    def get_corp_cache(cache, corporation_id):
        corp_cache = cache.get(corporation_id)
        if not corp_cache:
            cache[corporation_id] = {}
            corp_cache = cache.get(corporation_id)
        return corp_cache

    def prepare_corp_cache(self, rows, cache, row_key, datetime_keys):
        for row in rows:
            row_id: int = int(row[row_key])
            ext = row['ext']
            updated_at = ext['updated_at'].replace(tzinfo=pytz.UTC)
            corporation_id: int = int(ext['corporation_id'])
            del ext['updated_at']
            del ext['corporation_id']
            del row['ext']
            if datetime_keys:
                for dtkey in datetime_keys:
                    if dtkey in row:
                        row[dtkey].replace(tzinfo=pytz.UTC)
            corp_cache = self.get_corp_cache(cache, corporation_id)
            corp_cache[row_id] = QEntity(True, False, row, updated_at)
            if ext == {}:
                del ext
            else:
                corp_cache[row_id].store_ext(ext)

    def get_cache_status(self, cache, data, data_key, filter_val=None, filter_key=None, debug=False):
        # список элементов (ассетов или структур) имеющихся у корпорации
        ids_from_esi: typing.List[int] = [int(s[data_key]) for s in data]
        if not ids_from_esi:
            return None, None, None, None
        # кешированный, м.б. устаревший список корпоративных элементов
        if not cache:
            ids_in_cache: typing.List[int] = []
            new_ids: typing.List[int] = [id for id in ids_from_esi]
            deleted_ids: typing.List[int] = []
        else:
            if filter_key and filter_val:
                ids_in_cache: typing.List[int] = [id for id in cache.keys() if cache[id].obj[filter_key] == filter_val]
            else:
                ids_in_cache: typing.List[int] = [id for id in cache.keys()]
            # список элементов, появившихся у корпорации и отсутствующих в кеше (в базе данных)
            new_ids: typing.List[int] = [id for id in ids_from_esi if not cache.get(id)]
            # список корпоративных элементов, которых больше нет у корпорации (кеш устарел и база данных устарела)
            deleted_ids: typing.List[int] = [id for id in ids_in_cache if not (id in ids_from_esi)]
        if debug:
            print(' == ids_from_esi', ids_from_esi)
            print(' == ids_in_cache', ids_in_cache)
            print(' == new_ids     ', new_ids)
            print(' == deleted_ids ', deleted_ids)
        return ids_from_esi, ids_in_cache, new_ids, deleted_ids

    @staticmethod
    def get_pers_cache(cache, character_id):
        pers_cache = cache.get(character_id)
        if not pers_cache:
            cache[character_id] = {}
            pers_cache = cache.get(character_id)
        return pers_cache

    def prepare_pers_cache(self, rows, cache, row_key, datetime_keys):
        for row in rows:
            row_id: int = int(row[row_key])
            ext = row['ext']
            updated_at = ext['updated_at'].replace(tzinfo=pytz.UTC)
            character_id: int = int(ext['character_id'])
            del ext['updated_at']
            del ext['character_id']
            del row['ext']
            if datetime_keys:
                for dtkey in datetime_keys:
                    if dtkey in row:
                        row[dtkey].replace(tzinfo=pytz.UTC)
            pers_cache = self.get_pers_cache(cache, character_id)
            pers_cache[row_id] = QEntity(True, False, row, updated_at)
            if ext == {}:
                del ext
            else:
                pers_cache[row_id].store_ext(ext)

    # -------------------------------------------------------------------------
    # e v e   s w a g g e r   i n t e r f a c e
    # -------------------------------------------------------------------------

    def load_from_esi(self, url: str, fully_trust_cache=False, body=None):
        data = self.esiswagger.get_esi_data(
            url,
            fully_trust_cache=fully_trust_cache)
        updated_at = self.esiswagger.last_modified
        is_updated = self.esiswagger.is_last_data_updated
        return data, updated_at, is_updated

    def load_from_esi_piece_data(self, url: str, body: typing.List[int], fully_trust_cache=False):
        data = self.esiswagger.get_esi_piece_data(
            url,
            body,
            fully_trust_cache=fully_trust_cache)
        updated_at = self.esiswagger.last_modified
        is_updated = self.esiswagger.is_last_data_updated
        return data, updated_at, is_updated

    def load_from_esi_paged_data(self, url: str, fully_trust_cache=False):
        data = self.esiswagger.get_esi_paged_data(
            url,
            fully_trust_cache=fully_trust_cache)
        updated_at = self.esiswagger.last_modified
        is_updated = self.esiswagger.is_last_data_updated
        return data, updated_at, is_updated

    # -------------------------------------------------------------------------
    # characters/{character_id}/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_character_url(character_id: int) -> str:
        # Public information about a character
        return "characters/{character_id}/".format(character_id=character_id)

    def actualize_character_details(self, character_id: int, character_data, need_data=False):
        # проверяем, возможно ли зацикливание при загрузке сопутствующих данных?
        url: str = self.get_character_url(character_id)
        if self.depth.push(url):
            # сохраняем сопутствующие данные в БД
            self.actualize_corporation(character_data['corporation_id'], need_data=need_data)
            self.depth.pop()

    def actualize_character(self, _character_id, need_data=False):
        character_id: int = int(_character_id)
        # откидываем  "пилотов" типа 'Secure Commerce Commission' = 1000132
        # или всякую непись 'Areyara Kogachi' = 3004093
        if character_id < 90000000:
            return None
        in_cache = self.__cached_characters.get(character_id)
        # 1. либо данных нет в кеше
        # 2. если данные с таким id существуют, но внешнему коду не интересны сами данные, то выход выход
        # 3. либо данные в текущую сессию работы программы уже загружались
        # 4. данные с таким id существуют, но самих данных нет (видимо хранится только id вместе с at)
        #    проверяем дату-время последнего обновления информации, и обновляем устаревшие данные
        reload_esi: bool = False
        if not in_cache:
            reload_esi = True
        elif not need_data:
            return None
        elif in_cache.obj:
            self.actualize_character_details(character_id, in_cache.obj, need_data=True)
            return in_cache.obj
        elif (in_cache.at + self.character_timedelta) < self.eve_now:
            reload_esi = True
        # ---
        # загружаем данные с серверов CCP или загружаем данные из БД
        if reload_esi:
            try:
                # Public information about a character
                url: str = self.get_character_url(character_id)
                data, updated_at, is_updated = self.load_from_esi(url, fully_trust_cache=in_cache is None)
                if data:
                    # сохраняем данные в БД, при этом актуализируем дату последней работы с esi
                    if updated_at < self.eve_now:
                        updated_at = self.eve_now
                    self.dbswagger.insert_or_update_character(character_id, data, updated_at)
                else:
                    # если из кеша (с диска) не удалось в offline режиме считать данные, читаем из БД
                    data, updated_at = self.dbswagger.select_character(character_id)
                    if not data:
                        return None
                    reload_esi = False
            except requests.exceptions.HTTPError as err:
                status_code = err.response.status_code
                if status_code == 404:
                    # 404 Client Error: Not Found ('Character has been deleted!')
                    # это нормально, что часть пилотов со временем могут оказаться Not Found
                    return None
                else:
                    # print(sys.exc_info())
                    raise
            except:
                print(sys.exc_info())
                raise
        else:
            data, updated_at = self.dbswagger.select_character(character_id)
        # сохраняем данные в кеше
        if not in_cache:
            self.__cached_characters[character_id] = QEntity(True, True, data, updated_at)
        else:
            in_cache.store(True, reload_esi, data, updated_at)
        self.actualize_character_details(character_id, data, need_data=need_data)
        return data

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_corporation_url(corporation_id: int) -> str:
        # Public information about a corporation
        return "corporations/{corporation_id}/".format(corporation_id=corporation_id)

    def actualize_corporation_details(self, corporation_id: int, corporation_data, need_data=False):
        # проверяем, возможно ли зацикливание при загрузке сопутствующих данных?
        url: str = self.get_corporation_url(corporation_id)
        if self.depth.push(url):
            # сохраняем сопутствующие данные в БД
            if corporation_data['ceo_id'] != 1:  # EVE System
                self.actualize_character(corporation_data['ceo_id'], need_data=need_data)
            if corporation_data['creator_id'] != 1:  # EVE System
                self.actualize_character(corporation_data['creator_id'], need_data=need_data)
            if 'home_station_id' in corporation_data:
                self.actualize_station_or_structure(
                    corporation_data['home_station_id'],
                    need_data=need_data
                )
            self.depth.pop()

    def actualize_corporation(self, _corporation_id, need_data=False):
        corporation_id: int = int(_corporation_id)
        in_cache = self.__cached_corporations.get(corporation_id)
        # 1. либо данных нет в кеше
        # 2. если данные с таким id существуют, но внешнему коду не интересны сами данные, то выход выход
        # 3. либо данные в текущую сессию работы программы уже загружались
        # 4. данные с таким id существуют, но самих данных нет (видимо хранится только id вместе с at)
        #    проверяем дату-время последнего обновления информации, и обновляем устаревшие данные
        reload_esi: bool = False
        if not in_cache:
            reload_esi = True
        elif not need_data:
            return None
        elif in_cache.obj:
            self.actualize_corporation_details(corporation_id, in_cache.obj, need_data=True)
            return in_cache.obj
        elif (in_cache.at + self.corporation_timedelta) < self.eve_now:
            reload_esi = True
        # ---
        # загружаем данные с серверов CCP или загружаем данные из БД
        if reload_esi:
            # Public information about a corporation
            url: str = self.get_corporation_url(corporation_id)
            data, updated_at, is_updated = self.load_from_esi(url, fully_trust_cache=in_cache is None)
            if data:
                # сохраняем данные в БД, при этом актуализируем дату последней работы с esi
                if updated_at < self.eve_now:
                    updated_at = self.eve_now
                self.dbswagger.insert_or_update_corporation(corporation_id, data, updated_at)
            else:
                # если из кеша (с диска) не удалось в offline режиме считать данные, читаем из БД
                data, updated_at = self.dbswagger.select_corporation(corporation_id)
                if not data:
                    return None
                reload_esi = False
        else:
            data, updated_at = self.dbswagger.select_corporation(corporation_id)
        # сохраняем данные в кеше
        if not in_cache:
            self.__cached_corporations[corporation_id] = QEntity(True, True, data, updated_at)
        else:
            in_cache.store(True, reload_esi, data, updated_at)
        self.actualize_corporation_details(corporation_id, data, need_data=need_data)
        return data

    # -------------------------------------------------------------------------
    # universe/stations/{station_id}/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_universe_station_url(station_id: int) -> str:
        # Public information about a universe_station
        return "universe/stations/{station_id}/".format(station_id=station_id)

    def actualize_universe_station_details(self, station_data, need_data=False):
        # здесь загружается только корпорация-владелец станции, которой может и не быть,
        # чтобы не усложнять проверки и вхолостую не гонять push/pop - сперва проверим owner-а
        owner_id = station_data.get('owner', None)
        if owner_id:
            # проверяем, возможно ли зацикливание при загрузке сопутствующих данных?
            url: str = self.get_universe_station_url(station_data['station_id'])
            if self.depth.push(url):
                # сохраняем сопутствующие данные в БД
                self.actualize_corporation(owner_id, need_data=need_data)
                self.depth.pop()

    def actualize_universe_station(self, _station_id, need_data=False):
        station_id: int = int(_station_id)
        in_cache = self.__cached_stations.get(station_id)
        # 1. либо данных нет в кеше
        # 2. если данные с таким id существуют, но внешнему коду не интересны сами данные, то выход выход
        # 3. либо данные в текущую сессию работы программы уже загружались
        # 4. данные с таким id существуют, но самих данных нет (видимо хранится только id вместе с at)
        #    проверяем дату-время последнего обновления информации, и обновляем устаревшие данные
        reload_esi: bool = False
        if not in_cache:
            reload_esi = True
        elif not need_data:
            return None
        elif in_cache.obj:
            self.actualize_universe_station_details(in_cache.obj, need_data=True)
            return in_cache.obj
        elif (in_cache.at + self.universe_station_timedelta) < self.eve_now:
            reload_esi = True
        # ---
        # загружаем данные с серверов CCP или загружаем данные из БД
        if reload_esi:
            # Public information about a universe_station
            url: str = self.get_universe_station_url(station_id)
            data, updated_at, is_updated = self.load_from_esi(url, fully_trust_cache=in_cache is None)
            if data:
                # сохраняем данные в БД, при этом актуализируем дату последней работы с esi
                if updated_at < self.eve_now:
                    updated_at = self.eve_now
                self.dbswagger.insert_or_update_universe_station(data, updated_at)
            else:
                # если из кеша (с диска) не удалось в offline режиме считать данные, читаем из БД
                data, updated_at = self.dbswagger.select_universe_station(station_id)
                if not data:
                    return None
                reload_esi = False
        else:
            data, updated_at = self.dbswagger.select_universe_station(station_id)
        # сохраняем данные в кеше
        if not in_cache:
            self.__cached_stations[station_id] = QEntity(True, True, data, updated_at)
        else:
            in_cache.store(True, reload_esi, data, updated_at)
        self.actualize_universe_station_details(data, need_data=need_data)
        return data

    # -------------------------------------------------------------------------
    # universe/structures/{structure_id}/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_universe_structure_url(structure_id: int) -> str:
        # Requires: access token
        return "universe/structures/{structure_id}/".format(structure_id=structure_id)

    def load_universe_structure_from_esi(self, structure_id, fully_trust_cache=True):
        try:
            # Requires: access token
            url: str = self.get_universe_structure_url(structure_id)
            data, updated_at, is_updated = self.load_from_esi(url, fully_trust_cache=fully_trust_cache)
            return data, False, updated_at
        except requests.exceptions.HTTPError as err:
            status_code = err.response.status_code
            if status_code == 403:
                # это нормально, что часть структур со временем могут оказаться Forbidden
                return None, True, self.eve_now
            else:
                # print(sys.exc_info())
                raise
        except:
            print(sys.exc_info())
            raise

    def actualize_universe_structure_details(self, structure_id: int, structure_data, need_data=False):
        # проверяем, возможно ли зацикливание при загрузке сопутствующих данных?
        url: str = self.get_universe_structure_url(structure_id)
        if self.depth.push(url):
            # сохраняем сопутствующие данные в БД
            self.actualize_corporation(structure_data['owner_id'], need_data=need_data)
            self.depth.pop()

    def actualize_universe_structure(self, _structure_id, need_data=False):
        structure_id: int = int(_structure_id)
        in_cache = self.__cached_structures.get(structure_id)
        # 1. либо данных нет в кеше
        # 2. если данные с таким id существуют, но внешнему коду не интересны сами данные, то выход выход
        # 3. либо данные в текущую сессию работы программы уже загружались
        # 4. данные с таким id существуют, но самих данных нет (видимо хранится только id вместе с at)
        #    проверяем дату-время последнего обновления информации, и обновляем устаревшие данные
        reload_esi: bool = False
        if not in_cache:
            reload_esi = True
        elif not need_data:
            return None
        elif in_cache.obj:
            self.actualize_universe_structure_details(structure_id, in_cache.obj, need_data=True)
            return in_cache.obj
        elif in_cache.ext and in_cache.ext.get('forbidden'):
            return None
        elif (in_cache.at + self.universe_structure_timedelta) < self.eve_now:
            reload_esi = True
        # ---
        # загружаем данные с серверов CCP или загружаем данные из БД
        if reload_esi:
            data, forbidden, updated_at = self.load_universe_structure_from_esi(
                structure_id,
                fully_trust_cache=in_cache is None
            )
            if data:
                # сохраняем данные в БД, при этом актуализируем дату последней работы с esi
                if updated_at < self.eve_now:
                    updated_at = self.eve_now
                self.dbswagger.insert_or_update_universe_structure(structure_id, data, forbidden, updated_at)
            else:
                # если из кеша (с диска) не удалось в offline режиме считать данные, читаем из БД
                data, forbidden, updated_at = self.dbswagger.select_universe_structure(structure_id)
                if not data:
                    # если и из БД не удалось считать данные, то при загрузке corporation orders (после длительного
                    # простоя, когда структура стала forbidden), в эту точку для одной и той же станции можем начать
                    # попадать многократно, что плохо, потому как каждый такой ордер будет сопровождаться бесконечными
                    # запросами по ESI, - сохраняем в кеше data=None
                    if not in_cache:
                        self.__cached_structures[structure_id] = QEntity(True, True, None, self.eve_now)
                        self.__cached_structures[structure_id].store_ext({'forbidden': True})
                    else:
                        in_cache.store_ext({'forbidden': True})
                    return None
                reload_esi = False
        else:
            data, forbidden, updated_at = self.dbswagger.select_universe_structure(structure_id)
        # сохраняем данные в кеше
        if not in_cache:
            self.__cached_structures[structure_id] = QEntity(True, True, data, updated_at)
            if forbidden:
                self.__cached_structures[structure_id].store_ext({'forbidden': True})
        else:
            in_cache.store(True, reload_esi, data, updated_at)
            if forbidden:
                in_cache.store_ext({'forbidden': True})
        if data:
            self.actualize_universe_structure_details(structure_id, data, need_data=need_data)
        return data

    # -------------------------------------------------------------------------
    # universe/structures/
    # -------------------------------------------------------------------------

    def actualize_universe_structures(self):
        # Requires: access token
        data = self.esiswagger.get_esi_paged_data('universe/structures/')

        updated_at = self.esiswagger.is_last_data_updated
        if not updated_at:
            return None

        data_new = self.dbswagger.get_absent_universe_structure_ids(data)
        data_new = [id[0] for id in data_new]

        # data = [1035620655696, 1035660997658, 1035620697572, ... ]
        # data_new = [1035620655696]

        for structure_id in data_new:
            self.actualize_universe_structure(structure_id, need_data=False)
        self.qidb.commit()

        data_len: int = len(data)
        data_new_len: int = len(data_new)

        del data_new
        del data

        return data_len, data_new_len

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/structures/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_corporation_structures_url(corporation_id: int) -> str:
        # Requires role(s): Station_Manager
        return "corporations/{corporation_id}/structures/".format(corporation_id=corporation_id)

    def actualize_corporation_structure_details(self, structure_data, need_data=False):
        # проверяем, возможно ли зацикливание при загрузке сопутствующих данных?
        structure_id: int = int(structure_data['structure_id'])
        # в данном случае объектом self.depth не пользуемся, т.к. он был настроен ранее, при загрузке
        # списка всех корпоративных структур
        # сохраняем сопутствующие данные в БД
        self.actualize_universe_structure(structure_id, need_data=need_data)
        self.actualize_corporation(structure_data['corporation_id'], need_data=need_data)

    def actualize_corporation_structure(self, structure_data, updated_at):
        structure_id: int = int(structure_data['structure_id'])
        in_cache = self.__cached_corporation_structures.get(structure_id)
        # 1. либо данных нет в кеше
        # 2. если данные с таким id существуют, то проверяем изменились ли они в кеше
        #    если данные изменились, то надо также обновить их в БД
        data_equal: bool = False
        if not in_cache:
            pass
        elif in_cache.obj:
            data_equal = in_cache.is_obj_equal_by_keys(structure_data, self.corporation_structure_diff)
        # ---
        # из соображений о том, что корпоративные структуры может читать только пилот с ролью корпорации,
        # выполняем обновление сведений как о universe_structure, так и о корпорации (либо актуализируем, либо
        # подгружаем из БД)
        self.actualize_corporation_structure_details(structure_data, need_data=True)
        # данные с серверов CCP уже загружены, в случае необходимости обновляем данные в БД
        if data_equal:
            return
        self.dbswagger.insert_or_update_corporation_structure(structure_data, updated_at)
        # сохраняем данные в кеше
        if not in_cache:
            self.__cached_corporation_structures[structure_id] = QEntity(True, True, structure_data, updated_at)
        else:
            in_cache.store(True, True, structure_data, updated_at)

    def actualize_corporation_structures(self, _corporation_id):
        corporation_id: int = int(_corporation_id)

        # Requires role(s): Station_Manager
        url: str = self.get_corporation_structures_url(corporation_id)
        data, updated_at, is_updated = self.load_from_esi_paged_data(url, fully_trust_cache=True)
        if not is_updated:
            return data, 0

        # список структур имеющихся у корпорации, хранящихся в БД, в кеше, а также новых и исчезнувших
        ids_from_esi, ids_in_cache, new_ids, deleted_ids = self.get_cache_status(
            self.__cached_corporation_structures,
            data, 'structure_id',
            corporation_id, 'corporation_id'
        )
        if not ids_from_esi:
            return data, 0

        # выше были найдены идентификаторы тех структур, которых нет либо в universe_structures, либо
        # нет в corporation_structures, теперь добавляем отсутствующие данные в БД
        if self.depth.push(url):
            for structure_data in data:
                self.actualize_corporation_structure(structure_data, updated_at)
            self.depth.pop()
        # параметр updated_at меняется в случае, если меняются данные корпоративной структуры, т.ч. не
        # использует массовое обновление всех корпоративных структур, а лишь удаляем исчезнувшие
        self.dbswagger.mark_corporation_structures_updated(corporation_id, deleted_ids, None)
        self.qidb.commit()

        return data, len(new_ids)

    # -------------------------------------------------------------------------
    # universe/stations/{station_id}/
    # universe/structures/{structure_id}/
    # -------------------------------------------------------------------------

    def actualize_station_or_structure(self, location_id, need_data=False):
        if location_id >= 1000000000:
            self.actualize_universe_structure(location_id, need_data=need_data)
        else:
            self.actualize_universe_station(location_id, need_data=need_data)

    def get_system_id_of_station_or_structure(self, location_id):
        system_id = None
        if location_id >= 1000000000:
            structure = self.__cached_structures.get(location_id)
            if not structure or not structure.obj or not ('solar_system_id' in structure.obj):
                self.actualize_universe_structure(location_id, False)
                structure = self.__cached_structures.get(location_id)
            if structure and structure.obj:
                system_id = structure.obj.get('solar_system_id', None)
                del structure
        else:
            station = self.__cached_stations.get(location_id)
            if not station or not station.obj or not ('system_id' in station.obj):
                self.actualize_universe_station(location_id, False)
                station = self.__cached_stations.get(location_id)
            if station and station.obj:
                system_id = station.obj.get('system_id', None)
                del station
        return system_id

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/assets/names/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_corporation_assets_names_url(corporation_id: int) -> str:
        # Requires role(s): Director
        return "corporations/{corporation_id}/assets/names/".format(corporation_id=corporation_id)

    def can_assets_item_be_renamed(self, item_data) -> bool:
        # пропускаем экземпляры контейнеров, сложенные в стопки (у них нет уник. id и названий тоже не будет)
        is_singleton: bool = item_data['is_singleton']
        if not is_singleton:
            return False
        # пропускаем дронов в дронбеях, патроны в карго, корабли в ангарах и т.п.
        location_flag: str = item_data['location_flag']
        if location_flag[:-1] != 'CorpSAG':  # and location_flag != 'Unlocked' and location_flag != 'AutoFit':
            return False
        type_id: int = item_data['type_id']
        return type_id in self.__universe_items_with_names

    def load_corporation_assets_names_from_esi(self, corporation_id: int):
        # получение названий контейнеров, станций, и т.п. - всё что переименовывается ingame
        corp_cache = self.__cached_corporation_assets.get(corporation_id)
        item_ids: typing.List[int] = []

        for (item_id, in_cache) in corp_cache.items():
            if not self.can_assets_item_be_renamed(in_cache.obj):
                continue
            item_ids.append(item_id)
        del corp_cache

        # Requires role(s): Director
        url: str = self.get_corporation_assets_names_url(corporation_id)
        data, updated_at, is_updated = self.load_from_esi_piece_data(url, item_ids)
        del item_ids

        if data is None:
            return None
        if self.esiswagger.offline_mode:
            pass
        elif not is_updated:
            return None

        corp_names_cache = self.get_corp_cache(self.__cached_corporation_assets_names, corporation_id)
        corp_names_cache.clear()
        for itm in data:
            # { "item_id": 1035960770272, "name": "[prod] conveyor 2" },..
            item_id: int = itm['item_id']
            corp_names_cache[item_id] = itm['name']
        del data

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/assets/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_corporation_assets_url(corporation_id: int) -> str:
        # Requires role(s): Director
        return "corporations/{corporation_id}/assets/".format(corporation_id=corporation_id)

    def actualize_corporation_asset_item_details(self, item_data, need_data=False):
        # добавление в БД возможно отсутствующего типа товара
        type_id: int = int(item_data['type_id'])
        if type_id not in self.__cached_type_ids:
            url: str = self.get_type_id_url(type_id)
            if self.depth.push(url):
                self.actualize_type_id(type_id)
                self.depth.pop()
        # актуализация прочей информации об ассетах
        if type_id == 27:  # Office
            location_id: int = int(item_data['location_id'])
            self.actualize_station_or_structure(location_id, need_data=need_data)

    def actualize_corporation_asset_item(self, corporation_id: int, item_data, updated_at):
        item_id: int = int(item_data['item_id'])
        corp_cache = self.get_corp_cache(self.__cached_corporation_assets, corporation_id)
        in_cache = corp_cache.get(item_id)
        # ---
        item_possible_be_renamed: bool = self.can_assets_item_be_renamed(item_data)
        in_cache_item_name = None
        if item_possible_be_renamed:
            corp_names_cache = self.get_corp_cache(self.__cached_corporation_assets_names, corporation_id)
            in_cache_item_name = corp_names_cache.get(item_id)
        # 1. либо данных нет в кеше
        # 2. если данные с таким id существуют, то проверяем изменились ли они в кеше
        #    если данные изменились, то надо также обновить их в БД
        data_equal: bool = False
        if not in_cache:
            pass
        elif in_cache.obj:
            data_equal = in_cache.is_obj_equal_by_keys(item_data, self.corporation_asset_diff)
            # дополнительно: если у item-а присутствует наименование, то сравниванием с тем, который имеется в БД
            if item_possible_be_renamed:
                if data_equal:
                    data_equal = in_cache.compare_ext('name', in_cache_item_name)
                if not data_equal:
                    if in_cache_item_name:
                        in_cache.store_ext({'name': in_cache_item_name})
                    elif in_cache.ext and 'name' in in_cache.ext:
                        del in_cache.ext['name']
        # ---
        # из соображений о том, что корпоративные ассеты может читать только пилот с ролью корпорации,
        # выполняем обновление сведений как о структурах и станциях, где расположены офисы (и т.п.), а в случае
        # необходимости подгружаем данные из БД
        self.actualize_corporation_asset_item_details(item_data, need_data=True)
        # данные с серверов CCP уже загружены, в случае необходимости обновляем данные в БД
        if data_equal:
            return
        elif in_cache_item_name:
            item_data['name'] = in_cache_item_name
        self.dbswagger.insert_or_update_corporation_assets(item_data, corporation_id, updated_at)
        # сохраняем данные в кеше
        if not in_cache:
            corp_cache[item_id] = QEntity(True, True, item_data, updated_at)
        else:
            in_cache.store(True, True, item_data, updated_at)

    def actualize_corporation_assets(self, _corporation_id):
        corporation_id: int = int(_corporation_id)

        # Requires role(s): Director
        url: str = self.get_corporation_assets_url(corporation_id)
        try:
            data, updated_at, is_updated = self.load_from_esi_paged_data(url)
        except requests.exceptions.HTTPError as err:
            status_code = err.response.status_code
            if status_code == 404:  # это нормально, CCP используют 404-ответ при удалении route из swagger
                return None
            raise

        if data is None:
            return None
        if self.esiswagger.offline_mode:
            updated_at = self.eve_now
        elif not is_updated:
            return None

        # список ассетов имеющихся у корпорации, хранящихся в БД, в кеше, а также новых и исчезнувших
        corp_cache = self.__cached_corporation_assets.get(corporation_id)
        ids_from_esi, ids_in_cache, new_ids, deleted_ids = self.get_cache_status(
            corp_cache,
            data, 'item_id',
            debug=False  # corporation_id == 98150545
        )
        if not ids_from_esi:
            del data
            return None

        # получение названий контейнеров, станций, и т.п. - всё что переименовывается ingame
        self.load_corporation_assets_names_from_esi(corporation_id)

        known_asset_items: int = len(data)
        if self.depth.push(url):
            for item_data in data:
                item_id: int = item_data['item_id']
                self.actualize_corporation_asset_item(corporation_id, item_data, updated_at)
            self.depth.pop()
        del data

        # параметр updated_at меняется в случае, если меняются данные корпоративной структуры, т.ч. не
        # использует массовое обновление всех корпоративных структур, а лишь удаляем исчезнувшие
        self.dbswagger.delete_obsolete_corporation_assets(deleted_ids)
        self.qidb.commit()

        return known_asset_items

    def get_system_id_of_item(self, _corporation_id: int, _item_id: int):
        corporation_id: int = int(_corporation_id)
        item_id: int = int(_item_id)
        system_id = None

        corp_cache = self.__cached_corporation_assets.get(corporation_id)
        if corp_cache:
            # получение информации о регионе, солнечной системе и т.п. (поиск исходного root-а)
            location_id: int = -1
            while True:
                in_cache = corp_cache.get(item_id)
                if not in_cache or not in_cache.obj:
                    break
                location_id = int(in_cache.obj['location_id'])
                location_type: str = in_cache.obj['location_type']
                if location_type == 'station':
                    system_id = self.get_system_id_of_station_or_structure(location_id)
                    break
                elif location_type == 'solar_system':
                    system_id = location_id
                    break
                else:
                    location_flag: str = in_cache.obj['location_flag']
                    if location_flag == 'OfficeFolder' or location_flag == 'CorpDeliveries':
                        system_id = self.get_system_id_of_station_or_structure(location_id)
                        break
                item_id = location_id
            if location_id > 0:
                # сюда можем попасть случайно: возможно, что location_id не станция!
                system_id = self.get_system_id_of_station_or_structure(location_id)
            del corp_cache

        return system_id

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/blueprints/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_corporation_blueprints_url(corporation_id: int) -> str:
        # Requires role(s): Director
        return "corporations/{corporation_id}/blueprints/".format(corporation_id=corporation_id)

    def actualize_corporation_blueprint_item_details(self, item_data, need_data=False):
        location_flag: str = item_data['location_flag']
        if location_flag == 'CorpDeliveries':  # Station or Structure
            location_id: int = int(item_data['location_id'])
            self.actualize_station_or_structure(location_id, need_data=need_data)

    def actualize_corporation_blueprint_item(self, corporation_id: int, item_data, updated_at):
        item_id: int = int(item_data['item_id'])
        corp_cache = self.get_corp_cache(self.__cached_corporation_blueprints, corporation_id)
        in_cache = corp_cache.get(item_id)
        # 1. либо данных нет в кеше
        # 2. если данные с таким id существуют, то проверяем изменились ли они в кеше
        #    если данные изменились, то надо также обновить их в БД
        data_equal: bool = False
        if not in_cache:
            pass
        elif in_cache.obj:
            data_equal = in_cache.is_obj_equal_by_keys(item_data, self.corporation_blueprint_diff)
        # ---
        # из соображений о том, что корпоративные чертежи может читать только пилот с ролью корпорации,
        # выполняем обновление сведений как о структурах и станциях, где расположены офисы (и т.п.), а в случае
        # необходимости подгружаем данные из БД
        self.actualize_corporation_blueprint_item_details(item_data, need_data=not data_equal)
        # данные с серверов CCP уже загружены, в случае необходимости обновляем данные в БД
        if data_equal:
            return
        self.dbswagger.insert_or_update_corporation_blueprints(item_data, corporation_id, updated_at)
        # сохраняем данные в кеше
        if not in_cache:
            corp_cache[item_id] = QEntity(True, True, item_data, updated_at)
            in_cache = corp_cache.get(item_id)
            in_cache.store_ext({'just_added': True})  # добавлен в кеш и в БД (ранее отсутствовал)
        else:
            in_cache.store(True, True, item_data, updated_at)
            in_cache.store_ext({'changed': True})  # был в кеше, а значит и в БД (обновлён и там и тут)

    def actualize_corporation_blueprints(self, _corporation_id):
        corporation_id: int = int(_corporation_id)

        # Requires role(s): Director
        url: str = self.get_corporation_blueprints_url(corporation_id)
        data, updated_at, is_updated = self.load_from_esi_paged_data(url)

        if data is None:
            return None
        if self.esiswagger.offline_mode:
            updated_at = self.eve_now
        elif not is_updated:
            return None

        # подгружаем данные из БД в кеш с тем, чтобы сравнить данные в кеше и данные от ССР
        self.prepare_corp_cache(
            self.dbswagger.get_exist_corporation_blueprints(corporation_id),
            self.__cached_corporation_blueprints,
            'item_id',
            None
        )

        # список чертежей имеющихся у корпорации, хранящихся в БД, в кеше, а также новых и исчезнувших
        corp_cache = self.__cached_corporation_blueprints.get(corporation_id)
        ids_from_esi, ids_in_cache, new_ids, deleted_ids = self.get_cache_status(
            corp_cache,
            data, 'item_id',
            debug=False  # corporation_id == 98150545
        )
        if not ids_from_esi:
            del data
            return None

        known_blueprints: int = len(data)
        if self.depth.push(url):
            for item_data in data:
                self.actualize_corporation_blueprint_item(corporation_id, item_data, updated_at)
            self.depth.pop()
        del data

        # параметр updated_at меняется в случае, если меняются данные корпоративной структуры, т.ч. не
        # использует массовое обновление всех корпоративных структур, а лишь удаляем исчезнувшие
        self.dbswagger.delete_obsolete_corporation_blueprints(deleted_ids)
        self.qidb.commit()

        # отмечаем, что часть данных в кеше осталась, но из БД уже удалена (т.е. ранее информация была
        # считана из БД, но с серверов ССР чертежи исчезли) - их могут удалить, могут переложить в
        # личный ангар, могут использовать или передать в имущество другой корпорации и т.п. (т.е. быть
        # может в будущем эти чертежи снова появятся в корпангарах)
        for item_id in deleted_ids:
            in_cache = corp_cache.get(int(item_id))
            if in_cache:
                in_cache.store_ext({'deleted': True})

        return known_blueprints

    # -------------------------------------------------------------------------
    # /characters/{character_id}/blueprints/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_character_blueprints_url(character_id: int) -> str:
        # Requires: access token
        return "characters/{character_id}/blueprints/".format(
            character_id=character_id
        )

    def actualize_character_blueprint_item_details(self, item_data, need_data=False):
        # location_flag: str = item_data['location_flag']
        # if location_flag == 'CorpDeliveries':  # Station or Structure
        #     location_id: int = int(item_data['location_id'])
        #     self.actualize_station_or_structure(location_id, need_data=need_data)
        pass

    def actualize_character_blueprint_item(self, character_id: int, item_data, updated_at):
        item_id: int = int(item_data['item_id'])
        pers_cache = self.get_pers_cache(self.__cached_character_blueprints, character_id)
        in_cache = pers_cache.get(item_id)
        # 1. либо данных нет в кеше
        # 2. если данные с таким id существуют, то проверяем изменились ли они в кеше
        #    если данные изменились, то надо также обновить их в БД
        data_equal: bool = False
        if not in_cache:
            pass
        elif in_cache.obj:
            data_equal = in_cache.is_obj_equal_by_keys(item_data, self.character_blueprint_diff)
        # ---
        # из соображений о том, что корпоративные чертежи может читать только пилот с ролью корпорации,
        # выполняем обновление сведений как о структурах и станциях, где расположены офисы (и т.п.), а в случае
        # необходимости подгружаем данные из БД
        self.actualize_character_blueprint_item_details(item_data, need_data=not data_equal)
        # данные с серверов CCP уже загружены, в случае необходимости обновляем данные в БД
        if data_equal:
            return
        self.dbswagger.insert_or_update_character_blueprints(item_data, character_id, updated_at)
        # сохраняем данные в кеше
        if not in_cache:
            pers_cache[item_id] = QEntity(True, True, item_data, updated_at)
            in_cache = pers_cache.get(item_id)
            in_cache.store_ext({'just_added': True})  # добавлен в кеш и в БД (ранее отсутствовал)
        else:
            in_cache.store(True, True, item_data, updated_at)
            in_cache.store_ext({'changed': True})  # был в кеше, а значит и в БД (обновлён и там и тут)

    def actualize_character_blueprints(self, _character_id):
        character_id: int = int(_character_id)

        # Requires role(s): access token
        url: str = self.get_character_blueprints_url(character_id)
        data, updated_at, is_updated = self.load_from_esi_paged_data(url)

        if data is None:
            return None
        elif self.esiswagger.offline_mode:
            updated_at = self.eve_now
        elif not is_updated:
            return None

        # подгружаем данные из БД в кеш с тем, чтобы сравнить данные в кеше и данные от ССР
        self.prepare_pers_cache(
            self.dbswagger.get_exist_character_blueprints(character_id),
            self.__cached_character_blueprints,
            'item_id',
            None
        )

        # список чертежей имеющихся у пилота, хранящихся в БД, в кеше, а также новых и исчезнувших
        pers_cache = self.__cached_character_blueprints.get(character_id)
        ids_from_esi, ids_in_cache, new_ids, deleted_ids = self.get_cache_status(
            pers_cache,
            data, 'item_id',
            debug=False
        )
        if not ids_from_esi:
            del data
            del pers_cache
            return None

        # важно убедиться, что перед добавлением данных в БД, в связанной таблице есть пилот
        self.actualize_character(character_id, need_data=True)

        known_blueprints: int = len(data)
        if self.depth.push(url):
            for item_data in data:
                self.actualize_character_blueprint_item(character_id, item_data, updated_at)
            self.depth.pop()
        del data

        # параметр updated_at меняется в случае, если меняются данные коробки, т.ч. не
        # использует массовое обновление всех коробок, а лишь удаляем исчезнувшие
        self.dbswagger.delete_obsolete_character_blueprints(deleted_ids)
        self.qidb.commit()

        # отмечаем, что часть данных в кеше осталась, но из БД уже удалена (т.е. ранее информация была
        # считана из БД, но с серверов ССР чертежи исчезли) - их могут удалить, могут переложить в
        # корп ангар, могут использовать и т.п. (т.е. быть может в будущем эти чертежи снова появятся
        # в личных коробках)
        for item_id in deleted_ids:
            in_cache = pers_cache.get(int(item_id))
            if in_cache:
                in_cache.store_ext({'deleted': True})

        return known_blueprints

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/industry/jobs/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_corporation_industry_jobs_url(corporation_id: int) -> str:
        # Requires role(s): Director
        return "corporations/{corporation_id}/industry/jobs/?include_completed=true".format(corporation_id=corporation_id)

    def actualize_corporation_industry_job_item_details(self, job_data, need_data=False):
        self.actualize_station_or_structure(job_data['facility_id'], need_data=need_data)
        self.actualize_character(job_data['installer_id'], need_data=need_data)
        completed_character_id = job_data.get('completed_character_id')
        if completed_character_id:
            self.actualize_character(job_data['completed_character_id'], need_data=need_data)

    def actualize_corporation_industry_job_item(self, corporation_id: int, job_data, updated_at):
        job_id: int = int(job_data['job_id'])
        corp_cache = self.get_corp_cache(self.__cached_corporation_industry_jobs, corporation_id)
        in_cache = corp_cache.get(job_id)
        # 1. либо данных нет в кеше
        # 2. если данные с таким id существуют, то проверяем изменились ли они в кеше
        #    если данные изменились, то надо также обновить их в БД
        data_equal: bool = False
        if not in_cache:
            pass
        elif in_cache.obj:
            if in_cache.obj['status'] in ('delivered', 'cancelled'):
                data_equal = True  # в БД уже хранятся актуальные данные!
            else:
                data_equal = in_cache.is_obj_equal_by_keys(job_data, self.corporation_industry_job_diff)
        # ---
        # из соображений о том, что корпоративные чертежи может читать только пилот с ролью корпорации,
        # выполняем обновление сведений как о структурах и станциях, так и у частниках производства, а в случае
        # необходимости подгружаем данные из БД
        self.actualize_corporation_industry_job_item_details(job_data, need_data=not data_equal)
        # данные с серверов CCP уже загружены, в случае необходимости обновляем данные в БД
        if data_equal:
            return
        self.dbswagger.insert_or_update_corporation_industry_jobs(job_data, corporation_id, updated_at)
        # сохраняем данные в кеше
        if not in_cache:
            corp_cache[job_id] = QEntity(True, True, job_data, updated_at)
            in_cache = corp_cache.get(job_id)
            in_cache.store_ext({'just_added': True})  # добавлен в кеш и в БД (ранее отсутствовал)
        else:
            in_cache.store(True, True, job_data, updated_at)
            in_cache.store_ext({'changed': True})  # был в кеше, а значит и в БД (обновлён и там и тут)

    def actualize_corporation_industry_jobs(self, _corporation_id):
        corporation_id: int = int(_corporation_id)

        # Requires role(s): Director
        url: str = self.get_corporation_industry_jobs_url(corporation_id)
        data, updated_at, is_updated = self.load_from_esi_paged_data(url)

        if data is None:
            return None
        if self.esiswagger.offline_mode:
            updated_at = self.eve_now
        elif not is_updated:
            return None

        # подгружаем данные из БД в кеш с тем, чтобы сравнить данные в кеше и данные от ССР
        oldest_delivered_job = None
        for job_data in data:
            if job_data['status'] in ('delivered', 'cancelled'):
                job_id: int = int(job_data['job_id'])
                if not oldest_delivered_job:
                    oldest_delivered_job = job_id
                elif oldest_delivered_job > job_id:
                    oldest_delivered_job = job_id

        self.prepare_corp_cache(
            self.dbswagger.get_exist_corporation_industry_jobs(corporation_id, oldest_delivered_job),
            self.__cached_corporation_industry_jobs,
            'job_id',
            ['start_date', 'end_date', 'completed_date', 'pause_date']
        )

        # актуализация (добавление и обновление) производственных работ
        known_industry_jobs: int = len(data)
        active_industry_jobs: int = len([j for j in data if j['status'] == 'active'])
        if self.depth.push(url):
            for job_data in data:
                self.actualize_corporation_industry_job_item(corporation_id, job_data, updated_at)
            self.depth.pop()
        self.qidb.commit()
        del data

        # удаление устаревших работ
        self.dbswagger.discard_obsolete_corporation_jobs()

        return known_industry_jobs, active_industry_jobs

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/blueprints/
    # corporations/{corporation_id}/industry/jobs/
    # -------------------------------------------------------------------------

    def link_blueprints_and_jobs(self, _corporation_id):
        # сохранённые в БД только что найденные чертежи и работы остаются там "мариноваться"
        # до тех пор, пока у ним не подгрузятся стоимость выполненных работ и все прочие
        # данные (солнечная система, me/te чертежей и т.п.)
        self.dbswagger.link_wallet_journals_with_jobs()
        self.qidb.commit()

        # вычитываем необъединённые чертежи и ищем им парные работы по копирке, объединяем их
        self.dbswagger.link_blueprint_copies_with_jobs()
        self.qidb.commit()

        self.dbswagger.link_blueprint_invents_with_jobs()
        self.qidb.commit()

    # -------------------------------------------------------------------------
    # characters/{character_id}/industry/jobs/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_character_industry_jobs_url(character_id: int) -> str:
        # Requires role(s): access token
        return "characters/{character_id}/industry/jobs/?include_completed=true".format(character_id=character_id)

    def actualize_character_industry_job_item_details(self, job_data, need_data=False):
        self.actualize_station_or_structure(job_data['facility_id'], need_data=need_data)
        self.actualize_character(job_data['installer_id'], need_data=need_data)
        completed_character_id = job_data.get('completed_character_id')
        if completed_character_id:
            self.actualize_character(job_data['completed_character_id'], need_data=need_data)

    def actualize_character_industry_job_item(self, character_id: int, job_data, updated_at):
        job_id: int = int(job_data['job_id'])
        pers_cache = self.get_pers_cache(self.__cached_character_industry_jobs, character_id)
        in_cache = pers_cache.get(job_id)
        # 1. либо данных нет в кеше
        # 2. если данные с таким id существуют, то проверяем изменились ли они в кеше
        #    если данные изменились, то надо также обновить их в БД
        data_equal: bool = False
        if not in_cache:
            pass
        elif in_cache.obj:
            if in_cache.obj['status'] in ('delivered', 'cancelled'):
                data_equal = True  # в БД уже хранятся актуальные данные!
            else:
                data_equal = in_cache.is_obj_equal_by_keys(job_data, self.character_industry_job_diff)
        # ---
        # выполняем обновление сведений как о структурах и станциях, так и у частниках производства, а в случае
        # необходимости подгружаем данные из БД
        self.actualize_character_industry_job_item_details(job_data, need_data=not data_equal)
        # данные с серверов CCP уже загружены, в случае необходимости обновляем данные в БД
        if data_equal:
            return
        self.dbswagger.insert_or_update_character_industry_jobs(job_data, character_id, updated_at)
        # сохраняем данные в кеше
        if not in_cache:
            pers_cache[job_id] = QEntity(True, True, job_data, updated_at)
            in_cache = pers_cache.get(job_id)
            in_cache.store_ext({'just_added': True})  # добавлен в кеш и в БД (ранее отсутствовал)
        else:
            in_cache.store(True, True, job_data, updated_at)
            in_cache.store_ext({'changed': True})  # был в кеше, а значит и в БД (обновлён и там и тут)

    def actualize_character_industry_jobs(self, _character_id):
        character_id: int = int(_character_id)

        # Requires role(s): access token
        url: str = self.get_character_industry_jobs_url(character_id)
        data, updated_at, is_updated = self.load_from_esi_paged_data(url)

        if data is None:
            return None
        if self.esiswagger.offline_mode:
            updated_at = self.eve_now
        elif not is_updated:
            return None

        # подгружаем данные из БД в кеш с тем, чтобы сравнить данные в кеше и данные от ССР
        oldest_delivered_job = None
        for job_data in data:
            if job_data['status'] in ('delivered', 'cancelled'):
                job_id: int = int(job_data['job_id'])
                if not oldest_delivered_job:
                    oldest_delivered_job = job_id
                elif oldest_delivered_job > job_id:
                    oldest_delivered_job = job_id

        self.prepare_pers_cache(
            self.dbswagger.get_exist_character_industry_jobs(character_id, oldest_delivered_job),
            self.__cached_character_industry_jobs,
            'job_id',
            ['start_date', 'end_date', 'completed_date', 'pause_date']
        )

        # актуализация (добавление и обновление) производственных работ
        known_industry_jobs: int = len(data)
        active_industry_jobs: int = len([j for j in data if j['status'] == 'active'])
        if self.depth.push(url):
            for job_data in data:
                self.actualize_character_industry_job_item(character_id, job_data, updated_at)
            self.depth.pop()
        self.qidb.commit()
        del data

        return known_industry_jobs, active_industry_jobs

    # -------------------------------------------------------------------------
    # /corporations/{corporation_id}/wallets/{division}/journal/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_corporation_wallets_division_journal_url(corporation_id: int, division: int) -> str:
        # Requires role(s): Accountant, Junior_Accountant
        return "corporations/{corporation_id}/wallets/{division}/journal/".format(
            corporation_id=corporation_id,
            division=division
        )

    def actualize_corporation_wallet_journal_item_details(self, journal_data, need_data=False):
        context_id_type = journal_data.get('context_id_type')
        if context_id_type and (context_id_type == 'market_transaction_id'):
            # идентификатор пилота, который осуществляет торговые операции на рынке
            second_party_id = journal_data['second_party_id']
            if second_party_id:
                self.actualize_character(journal_data['second_party_id'], need_data=need_data)

    def actualize_corporation_wallet_journals(self, _corporation_id):
        corporation_id: int = int(_corporation_id)
        corp_made_new_payments: int = 0
        db_data_loaded: bool = False
        dbdivisions = None

        # Requires role(s): Accountant, Junior_Accountant
        for division in range(1, 8):
            url: str = self.get_corporation_wallets_division_journal_url(corporation_id, division)
            data, updated_at, is_updated = self.load_from_esi_paged_data(url)
            if self.esiswagger.offline_mode:
                updated_at = self.eve_now
            elif not is_updated:
                continue

            # загрузка данных из БД
            if not db_data_loaded:
                dbdivisions = self.dbswagger.get_last_known_corporation_wallet_journal_ids(corporation_id)
                db_data_loaded = True

            # чтобы не мусорить в консоль лишними отладочными данными (их и так идёт целый поток) - отключаем отладку
            db_debug: bool = self.dbswagger.db.debug
            if db_debug:
                self.dbswagger.db.disable_debug()

            # актуализация (добавление) операций в корпоративном кошельке
            last_known_id = -1 if (dbdivisions is None) or not dbdivisions else next((j[0] for j in dbdivisions if j[1] == int(division)), -1)
            for journal_data in data:
                if journal_data['id'] > last_known_id:
                    corp_made_new_payments += 1
                    self.actualize_corporation_wallet_journal_item_details(journal_data, False)
                    self.dbswagger.insert_corporation_wallet_journals(
                        journal_data,
                        corporation_id,
                        division,
                        updated_at
                    )

            # если отладвка была отключена, то включаем её
            if db_debug:
                self.dbswagger.db.enable_debug()

            del data
        self.qidb.commit()

        if dbdivisions:
            del dbdivisions

        return corp_made_new_payments

    # -------------------------------------------------------------------------
    # /characters/{character_id}/wallet/journal/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_character_wallet_journal_url(character_id: int) -> str:
        # Requires: access token
        return "characters/{character_id}/wallet/journal/".format(
            character_id=character_id
        )

    def actualize_character_wallet_journal_item_details(self, journal_data, need_data=False):
        context_id_type = journal_data.get('context_id_type')
        if context_id_type and (context_id_type == 'market_transaction_id'):
            # идентификатор пилота, который осуществляет торговые операции на рынке
            second_party_id = journal_data['second_party_id']
            if second_party_id:
                self.actualize_character(journal_data['second_party_id'], need_data=need_data)

    def actualize_character_wallet_journals(self, _character_id):
        character_id: int = int(_character_id)
        made_new_payments: int = 0

        # Requires role(s): access token
        url: str = self.get_character_wallet_journal_url(character_id)
        data, updated_at, is_updated = self.load_from_esi_paged_data(url)
        if data is None:
            return None
        elif self.esiswagger.offline_mode:
            updated_at = self.eve_now
        elif not is_updated:
            return None

        # загрузка данных из БД
        last_known_id = self.dbswagger.get_last_known_character_wallet_journal_id(character_id)

        # чтобы не мусорить в консоль лишними отладочными данными (их и так идёт целый поток) - отключаем отладку
        db_debug: bool = self.dbswagger.db.debug
        if db_debug:
            self.dbswagger.db.disable_debug()

        # важно убедиться, что перед добавлением данных в БД, в связанной таблице есть пилот
        self.actualize_character(character_id, need_data=True)

        # актуализация (добавление) операций в корпоративном кошельке
        for journal_data in data:
            if last_known_id is None or (journal_data['id'] > last_known_id):
                made_new_payments += 1
                self.actualize_character_wallet_journal_item_details(journal_data, False)
                self.dbswagger.insert_character_wallet_journals(
                    journal_data,
                    character_id,
                    updated_at
                )

        del data

        # если отладвка была отключена, то включаем её
        if db_debug:
            self.dbswagger.db.enable_debug()

        self.qidb.commit()

        return made_new_payments

    # -------------------------------------------------------------------------
    # /corporations/{corporation_id}/wallets/{division}/transactions/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_corporation_wallets_division_transactions_url(corporation_id: int, division: int) -> str:
        # Requires role(s): Accountant, Junior_Accountant
        return "corporations/{corporation_id}/wallets/{division}/transactions/".format(
            corporation_id=corporation_id,
            division=division
        )

    def actualize_corporation_wallet_transaction_details(self, transaction_data, need_data=False):
        location_id: int = int(transaction_data['location_id'])
        self.actualize_station_or_structure(location_id, need_data=need_data)

    def actualize_corporation_wallet_transactions(self, _corporation_id):
        corporation_id: int = int(_corporation_id)
        corp_made_new_transactions: int = 0
        db_data_loaded: bool = False
        dbdivisions = None

        # Requires role(s): Accountant, Junior_Accountant
        for division in range(1, 8):
            url: str = self.get_corporation_wallets_division_transactions_url(corporation_id, division)
            data, updated_at, is_updated = self.load_from_esi_paged_data(url)
            if self.esiswagger.offline_mode:
                updated_at = self.eve_now
            elif not is_updated:
                continue

            # загрузка данных из БД
            if not db_data_loaded:
                dbdivisions = self.dbswagger.get_last_known_corporation_wallet_transactions_ids(corporation_id)
                db_data_loaded = True

            # чтобы не мусорить в консоль лишними отладочными данными (их и так идёт целый поток) - отключаем отладку
            db_debug: bool = self.dbswagger.db.debug
            if db_debug:
                self.dbswagger.db.disable_debug()

            # актуализация (добавление) операций в корпоративном кошельке
            last_known_id = -1 if (dbdivisions is None) or not dbdivisions else next((j[0] for j in dbdivisions if j[1] == int(division)), -1)
            for transactions_data in data:
                if transactions_data['transaction_id'] > last_known_id:
                    corp_made_new_transactions += 1
                    self.actualize_corporation_wallet_transaction_details(transactions_data, False)
                    self.dbswagger.insert_corporation_wallet_transactions(
                        transactions_data,
                        corporation_id,
                        division,
                        updated_at
                    )

            # если отладвка была отключена, то включаем её
            if db_debug:
                self.dbswagger.db.enable_debug()

            del data
        self.qidb.commit()

        if dbdivisions:
            del dbdivisions

        return corp_made_new_transactions

    # -------------------------------------------------------------------------
    # /characters/{character_id}/wallet/transactions/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_character_wallet_transactions_url(character_id: int) -> str:
        # Requires: access token
        return "characters/{character_id}/wallet/transactions/".format(
            character_id=character_id
        )

    def actualize_character_wallet_transaction_details(self, transaction_data, need_data=False):
        location_id: int = int(transaction_data['location_id'])
        self.actualize_station_or_structure(location_id, need_data=need_data)

    def actualize_character_wallet_transactions(self, _character_id):
        character_id: int = int(_character_id)
        made_new_transactions: int = 0

        # Requires: access token
        url: str = self.get_character_wallet_transactions_url(character_id)
        data, updated_at, is_updated = self.load_from_esi_paged_data(url)
        if data is None:
            return None
        if self.esiswagger.offline_mode:
            updated_at = self.eve_now
        elif not is_updated:
            return None

        # загрузка данных из БД
        last_known_id = self.dbswagger.get_last_known_character_wallet_transaction_id(character_id)

        # чтобы не мусорить в консоль лишними отладочными данными (их и так идёт целый поток) - отключаем отладку
        db_debug: bool = self.dbswagger.db.debug
        if db_debug:
            self.dbswagger.db.disable_debug()

        # важно убедиться, что перед добавлением данных в БД, в связанной таблице есть пилот
        self.actualize_character(character_id, need_data=True)

        # актуализация (добавление) операций в корпоративном кошельке
        for transactions_data in data:
            if last_known_id is None or (transactions_data['transaction_id'] > last_known_id):
                made_new_transactions += 1
                self.actualize_character_wallet_transaction_details(transactions_data, False)
                self.dbswagger.insert_character_wallet_transactions(
                    transactions_data,
                    character_id,
                    updated_at
                )

        del data

        # если отладвка была отключена, то включаем её
        if db_debug:
            self.dbswagger.db.enable_debug()

        self.qidb.commit()

        return made_new_transactions

    # -------------------------------------------------------------------------
    # /corporations/{corporation_id}/orders/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_corporation_orders_url(corporation_id: int) -> str:
        # Requires one of the following EVE corporation role(s): Accountant, Trader
        return "corporations/{corporation_id}/orders/".format(corporation_id=corporation_id)

    @staticmethod
    def get_corporation_orders_history_url(corporation_id: int) -> str:
        # Requires one of the following EVE corporation role(s): Accountant, Trader
        return "corporations/{corporation_id}/orders/history/".format(corporation_id=corporation_id)

    def actualize_corporation_order_item_details(self, order_data, need_data=False):
        self.actualize_station_or_structure(order_data['location_id'], need_data=need_data)
        self.actualize_character(order_data['issued_by'], need_data=need_data)

    def actualize_corporation_order_item(self, corporation_id: int, order_data, history, updated_at):
        order_id: int = int(order_data['order_id'])
        corp_cache = self.get_corp_cache(self.__cached_corporation_orders, corporation_id)
        in_cache = corp_cache.get(order_id)
        # 1. либо данных нет в кеше
        # 2. если данные с таким id существуют, то проверяем изменились ли они в кеше
        #    если данные изменились, то надо также обновить их в БД
        data_equal: bool = False
        if not in_cache:
            pass
        elif in_cache.obj:
            data_equal = in_cache.is_obj_equal_by_keys(order_data, self.market_order_diff)
        # ---
        # если все позиции в order-е закрыты, то откуда бы ни пришли данные, они должны стать архивными
        #if (order_data['volume_remain'] == 0):
        #    data_equal = False
        #    history = True
        # данные с серверов CCP уже загружены, в случае необходимости обновляем данные в БД
        if data_equal:
            return
        # из соображений о том, что market ордера может читать только пилот с ролью корпорации,
        # выполняем обновление сведений как о структурах и станциях, так и у частниках торговли, а в случае
        # необходимости подгружаем данные из БД
        self.actualize_corporation_order_item_details(order_data, need_data=not data_equal)
        self.dbswagger.insert_or_update_corporation_orders(order_data, corporation_id, history, updated_at)
        # сохраняем данные в кеше
        if not in_cache:
            corp_cache[order_id] = QEntity(True, True, order_data, updated_at)
            in_cache = corp_cache.get(order_id)
            in_cache.store_ext({'just_added': True})  # добавлен в кеш и в БД (ранее отсутствовал)
        else:
            in_cache.store(True, True, order_data, updated_at)
            in_cache.store_ext({'changed': True})  # был в кеше, а значит и в БД (обновлён и там и тут)

    def actualize_corporation_orders(self, _corporation_id):
        corporation_id: int = int(_corporation_id)
        corp_has_active_orders: int = 0
        corp_has_finished_orders: int = 0

        # Requires role(s): Accountant, Trader
        active_url: str = self.get_corporation_orders_url(corporation_id)
        active_data, active_updated_at, active_is_updated = self.load_from_esi_paged_data(active_url)
        history_url: str = self.get_corporation_orders_history_url(corporation_id)
        history_data, history_updated_at, history_is_updated = self.load_from_esi_paged_data(history_url)
        if self.esiswagger.offline_mode:
            active_updated_at = self.eve_now
            history_updated_at = self.eve_now
            active_is_updated = True
            history_is_updated = True
        #elif not active_is_updated and not history_is_updated:
        #    return None

        if active_is_updated:
            # подгружаем данные из БД в кеш с тем, чтобы сравнить данные в кеше и данные от ССР
            self.prepare_corp_cache(
                self.dbswagger.get_active_corporation_orders(corporation_id),
                self.__cached_corporation_orders,
                'order_id',
                ['issued']
            )

            # актуализация (добавление и обновление) market order-ов
            if self.depth.push(active_url):
                for order_data in active_data:
                    corp_has_active_orders += 1
                    self.actualize_corporation_order_item(corporation_id, order_data, False, active_updated_at)
                self.depth.pop()
            self.qidb.commit()

            # актуализировать ЗДЕСЬ устаревшие market order-а, которые активный в БД, но отсутствуют в esi НЕЛЬЗЯ!
            # поcкольку отсутствует актуальная информация о market order-е (м.б. изменено volume_remain, а м.б. изменён price)
            # ...заказчиваем сохранение (обновление) актуальных market order-ов

        if history_is_updated and history_data:
            # составляем список history market order-ов, ищем те, что отсутствуют в БД
            # из предположения, что они были были размещены и быстро выполнены, и сразу попали в history, минуя active
            history_order_ids: typing.List[int] = []
            for order_data in history_data:
                order_id: int = int(order_data['order_id'])
                history_order_ids.append(order_id)

            # обращаемся в БД за списком тех market order-ов, которые отсутствуют в БД
            absent_db_ids: typing.List[int] = self.dbswagger.get_absent_corporation_orders_history(
                corporation_id,
                history_order_ids)

            # поиск в esi-списке тех market order-ов, которых нет среди history в БД
            if self.depth.push(history_url):
                for order_id in absent_db_ids:
                    order_data = next((o for o in history_data if o['order_id'] == order_id), None)
                    if order_data:
                        corp_has_finished_orders += 1
                        self.actualize_corporation_order_item(corporation_id, order_data, True, history_updated_at)
                self.depth.pop()
            self.qidb.commit()

            del absent_db_ids
            del history_order_ids

        if active_is_updated and history_is_updated:
            # данные по ордерам из БД в кеш уже подгружены и актуализированы с теми, что пришли от ССР
            # т.е. уже был вызван метод self.prepare_corp_cache...
            active_order_ids = [int(o['order_id']) for o in active_data]
            history_order_ids = [int(o['order_id']) for o in history_data]
            corp_cache = self.get_corp_cache(self.__cached_corporation_orders, corporation_id)
            obsolete_order_ids = set(corp_cache.keys()) - set(active_order_ids) - set(history_order_ids)
            if obsolete_order_ids:
                self.dbswagger.discard_absent_corporation_orders(corporation_id, list(obsolete_order_ids))

        del history_data
        del active_data

        # синхронизация данных в таблице esi_trade_hub_history (с сохранением
        # накопленных данных, по сведениям из таблицы esi_corporation_orders)
        self.dbswagger.sync_market_location_history_with_corp_orders_by_corp(corporation_id)

        # удаление устаревших ордеров
        self.dbswagger.discard_obsolete_corporation_orders()

        return corp_has_active_orders, corp_has_finished_orders

    # -------------------------------------------------------------------------
    # /markets/prices/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_markets_prices_url() -> str:
        # Requires: public access
        return "markets/prices/"

    def actualize_markets_prices(self):
        url: str = self.get_markets_prices_url()
        data, updated_at, is_updated = self.load_from_esi_paged_data(url)
        if data is None:
            return None
        if self.esiswagger.offline_mode:
            updated_at = self.eve_now
        elif not is_updated:
            return None

        # чтобы не мусорить в консоль лишними отладочными данными (их и так идёт целый поток) - отключаем отладку
        db_debug: bool = self.dbswagger.db.debug
        if db_debug:
            self.dbswagger.db.disable_debug()

        # актуализация (добавление) narket цен в БД
        markets_prices_updated: int = 0
        for price_data in data:
            # актуализация кеша (сравнение данных в кеше для минимизации обращений к БД)
            type_id: int = price_data['type_id']
            in_cache = self.__cached_markets_prices.get(type_id)
            if not in_cache:
                self.__cached_markets_prices[type_id] = QEntity(True, True, price_data, updated_at)
            elif not in_cache.is_obj_equal_by_keys(price_data, self.markets_prices_diff):
                in_cache.store(True, True, price_data, updated_at)
            else:
                continue
            # добавление в БД возможно отсутствующего типа товара
            if type_id not in self.__cached_type_ids:
                url: str = self.get_type_id_url(type_id)
                if self.depth.push(url):
                    self.actualize_type_id(type_id)
                    self.depth.pop()
            # отправка в БД цену товара
            self.dbswagger.insert_or_update_markets_price(price_data, updated_at)
            # подсчёт статистики
            markets_prices_updated += 1

        self.qidb.commit()

        # если отладка была отключена, то включаем её
        if db_debug:
            self.dbswagger.db.enable_debug()

        del data

        return markets_prices_updated

    # -------------------------------------------------------------------------
    # /markets/{region_id}/history/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_markets_region_history_url(region_id: int, type_id: int) -> str:
        # Requires: public access
        return "markets/{region_id}/history/?type_id={type_id}".format(region_id=region_id, type_id=type_id)

    def is_market_regions_history_refreshed(self):
        if self.esiswagger.offline_mode:
            return False
        else:
            url: str = self.get_markets_region_history_url(10000002, 34)  # 'The Forge' = 10000002, 'Tritanium' = 34
            data, updated_at, is_updated = self.load_from_esi(url)
            if data:
                del data
            return is_updated

    def actualize_market_region_history(self, region: str):
        region_id = self.dbswagger.select_region_id_by_name(region)  # 'The Forge' = 10000002
        if region_id is None:
            return None
        type_ids = self.dbswagger.select_market_type_ids(region_id)
        if type_ids is None:
            return None

        market_region_history_updates = None
        for _type_id in type_ids:
            type_id: int = int(_type_id[0])
            last_known_date = None if _type_id[1] is None else _type_id[1]  # datetime.date(2020, 07, 01)
            url: str = self.get_markets_region_history_url(region_id, type_id)

            try:
                data, updated_at, is_updated = self.load_from_esi(url)
            except requests.exceptions.HTTPError as err:
                status_code = err.response.status_code
                if status_code == 404:
                    # это странно, но часть item_types может быть Not Found
                    # либо не найден регион (ошибка в настройках, или изменения в игре)
                    continue
                else:
                    # print(sys.exc_info())
                    # raise
                    continue  # продолжить загрузку очень важно!
            except:
                # print(sys.exc_info())
                # raise
                continue  # продолжить загрузку очень важно!

            if data is None:
                continue
            if self.esiswagger.offline_mode:
                updated_at = self.eve_now
            elif not is_updated:
                if (region_id == 10000002) and (type_id == 34):  # 'The Forge' = 10000002, 'Tritanium' = 34
                    pass
                else:
                    continue

            # чтобы не мусорить в консоль лишними отладочными данными (их и так идёт целый поток) - отключаем отладку
            db_debug: bool = self.dbswagger.db.debug
            if db_debug:
                self.dbswagger.db.disable_debug()

            # актуализация (добавление) narket цен в БД
            for market_data in data:
                market_date = datetime.datetime.strptime(market_data['date'], '%Y-%m-%d').date()  # '2020-07-01'
                if last_known_date is None or (market_date > last_known_date):
                    # подсчёт статистики
                    if market_region_history_updates is None:
                        market_region_history_updates = 1
                    else:
                        market_region_history_updates += 1
                    # отправка в БД
                    self.dbswagger.insert_or_update_region_market_history(region_id, type_id, market_data, updated_at)

            self.qidb.commit()

            # если отладка была отключена, то включаем её
            if db_debug:
                self.dbswagger.db.enable_debug()

            del data

        del type_ids

        return market_region_history_updates

    # -------------------------------------------------------------------------
    # /markets/structures/{structure_id}/
    # /markets/{region_id}/orders/
    # -------------------------------------------------------------------------

    def actualize_trade_hub_market_orders(self, trade_hub_id: int, orders_data, updated_at):
        # актуализируем станцию/структуру в БД
        self.actualize_station_or_structure(trade_hub_id, need_data=False)

        # повторно проходимся по списку ордеров, то теперь уже сохраняем его в БД "напрямую" как есть
        __cached_trade_hub_orders: typing.Dict[int, typing.Any] = {}
        __cached_trade_hub_orders = self.dbswagger.get_market_location_orders_to_compare(trade_hub_id)
        order_ids_in_cache: typing.Set[int] = set(__cached_trade_hub_orders.keys())
        type_ids_in_cache: typing.Set[int] = set()

        # актуализация (добавление) market ордеров в БД
        updated_market_orders: int = 0
        for order_data in orders_data:
            # поиск например Jita Trade Hub среди всех ордеров региона
            # для структур эта проверка не актуальна, но набор данных у структур имеет тот же формат
            location_id: int = order_data['location_id']
            if not (location_id == trade_hub_id):  # 'Jita IV - Moon 4 - Caldari Navy Assembly Plant' = 60003760
                continue
            # актуализация содержимого БД
            type_id: int = order_data['type_id']
            order_id: int = order_data['order_id']
            # этот ордер не должен быть удалён, т.к. он всё ещё в маркете
            if order_id in order_ids_in_cache:
                order_ids_in_cache.remove(order_id)
            # проверяем изменился ли ордер? если не изменился, то переходим к следующему
            in_cache = __cached_trade_hub_orders.get(order_id)
            if not in_cache:
                pass
            elif is_dicts_equal_by_keys(in_cache, order_data, self.market_order_diff):
                continue
            # добавление в БД возможно отсутствующего типа товара
            if type_id not in self.__cached_type_ids:
                url: str = self.get_type_id_url(type_id)
                if self.depth.push(url):
                    self.actualize_type_id(type_id)
                    self.depth.pop()
            # добавляем новый или корректируем изменённый ордер в БД
            self.dbswagger.insert_or_update_market_location_order(trade_hub_id, order_data, updated_at)
            # подсчёт статистики
            updated_market_orders += 1
            if type_id not in type_ids_in_cache:
                type_ids_in_cache.add(type_id)

        found_market_goods: int = len(type_ids_in_cache)

        # поскорее очищаем память, данные уже в БД
        del type_ids_in_cache
        del __cached_trade_hub_orders

        # удаление из БД записей, по которым в маркете отсутствуют данные
        for _order_id in order_ids_in_cache:
            order_id: int = int(_order_id)
            self.dbswagger.delete_market_location_order(trade_hub_id, order_id)
            # подсчёт статистики
            updated_market_orders += 1

        # очищаем память, данные удалены из БД
        del order_ids_in_cache

        # синхронизация данных в таблице esi_trade_hub_prices (с сохранением
        # накопленных данных, по сведениям из таблицы esi_trade_hub_orders)
        self.dbswagger.sync_market_location_prices_with_orders(trade_hub_id)

        # синхронизация данных в таблице esi_trade_hub_history (с сохранением
        # накопленных данных, по сведениям из таблицы esi_trade_hub_orders)
        self.dbswagger.sync_market_location_history_with_orders(trade_hub_id)

        # синхронизация данных в таблице esi_trade_hub_history (с сохранением
        # накопленных данных, по сведениям из таблицы esi_corporation_orders)
        self.dbswagger.sync_market_location_history_with_corp_orders_by_loc(trade_hub_id)

        return found_market_goods, updated_market_orders

    # -------------------------------------------------------------------------
    # /markets/structures/{structure_id}/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_markets_structures_url(structure_id: int) -> str:
        # Requires: access token
        return "markets/structures/{structure_id}/".format(structure_id=structure_id)

    def actualize_markets_structures_prices(self, structure_id: int):
        url: str = self.get_markets_structures_url(structure_id)

        try:
            data, updated_at, is_updated = self.load_from_esi_paged_data(url)
        except requests.exceptions.HTTPError as err:
            status_code = err.response.status_code
            if status_code == 404:  # Not Found (спилили структурку?)
                return None, None
            elif status_code == 403:  # Forbidden (у этой корпорации нет доступа к этой структуре?)
                return None, None
            else:
                # print(sys.exc_info())
                # raise
                return None, None
        except:
            # print(sys.exc_info())
            # raise
            return None, None  # продолжить загрузку очень важно!

        if data is None:
            return None, None
        if self.esiswagger.offline_mode:
            updated_at = self.eve_now
        elif not is_updated:
            return None, None

        # актуализируем данные по структуре (загружем по ESI или из БД, например её название)
        self.actualize_universe_structure(structure_id, True)

        # чтобы не мусорить в консоль лишними отладочными данными (их и так идёт целый поток) - отключаем отладку
        db_debug: bool = self.dbswagger.db.debug
        if db_debug:
            self.dbswagger.db.disable_debug()

        # актуализация (добавление) market цен в БД
        found_market_goods, updated_market_orders = self.actualize_trade_hub_market_orders(structure_id, data, updated_at)

        # стараемся пораньше очистить память
        del data

        self.qidb.commit()

        # если отладка была отключена, то включаем её
        if db_debug:
            self.dbswagger.db.enable_debug()

        return found_market_goods, updated_market_orders

    # -------------------------------------------------------------------------
    # /markets/{region_id}/orders/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_markets_region_orders_url(region_id: int, order_type: str = 'all', type_id=None) -> str:
        # Requires: access token
        # 'The Forge' = 10000002
        # 'Tritanium' = 34
        if type_id is None:
            # Официально так: if you query without type_id, we always return both buy and sell orders
            # В действительности: order_type учитывается, так что подставляем его в параметры! но требуется контроль после получения данных от ССР
            if order_type == 'all':
                return "markets/{region_id}/orders/".format(region_id=region_id)
            else:
                return "markets/{region_id}/orders/?order_type={order_type}".format(region_id=region_id, order_type=order_type)
        elif order_type == 'all':
            return "markets/{region_id}/orders/?type_id={type_id}".format(region_id=region_id, type_id=type_id)
        else:
            return "markets/{region_id}/orders/?order_type={order_type}&type_id={type_id}".format(region_id=region_id, order_type=order_type, type_id=type_id)

    def actualize_trade_hubs_market_orders(self, region: str, trade_hubs):
        region_id = self.dbswagger.select_region_id_by_name(region)  # 'The Forge' = 10000002
        if region_id is None:
            return None, None

        trade_hub_ids = []
        for hub in trade_hubs:
            station_id = self.dbswagger.select_station_id_by_name(hub)  # 'Jita IV - Moon 4 - Caldari Navy Assembly Plant' = 60003760
            if not (station_id is None):
                trade_hub_ids.append(station_id)
        if not trade_hub_ids:
            return None, None

        url: str = self.get_markets_region_orders_url(region_id)
        try:
            data, updated_at, is_updated = self.load_from_esi_paged_data(url)
        except requests.exceptions.HTTPError as err:
            status_code = err.response.status_code
            if status_code == 404:
                # 'error': 'Region not found!' (опечатка в настройках, или изменение в игре)
                return None, None
            else:
                # print(sys.exc_info())
                raise
        except:
            print(sys.exc_info())
            raise

        if data is None:
            return None, None
        if self.esiswagger.offline_mode:
            updated_at = self.eve_now
        elif not is_updated:
            return None, None

        # чтобы не мусорить в консоль лишними отладочными данными (их и так идёт целый поток) - отключаем отладку
        db_debug: bool = self.dbswagger.db.debug
        if db_debug:
            self.dbswagger.db.disable_debug()

        # перебираем список торговых хабов в этом регионе
        found_market_goods: int = 0
        updated_market_orders: int = 0
        for _trade_hub_id in trade_hub_ids:
            trade_hub_id: int = int(_trade_hub_id)
            found, updated = self.actualize_trade_hub_market_orders(trade_hub_id, data, updated_at)
            if found and updated:
                found_market_goods += found
                updated_market_orders += updated

        # стараемся пораньше очистить память, т.к. загруженный кусок данных по Jita Trage Hub занимает большее 1.5 Гб
        del data

        self.qidb.commit()

        # если отладка была отключена, то включаем её
        if db_debug:
            self.dbswagger.db.enable_debug()

        return found_market_goods, updated_market_orders

    # -------------------------------------------------------------------------
    # /universe/categories/
    # /universe/categories/{category_id}/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_category_id_url(category_id: int) -> str:
        # Requires: piblic access
        return "universe/categories/{category_id}/".format(category_id=category_id)

    def actualize_category_id(self, category_id: int):
        # проверяем только то, что группа/категория присутствует в БД по указанному идентификатору
        # исходим из того, что группы/категории не модифицируются CCP-шниками, только добавляются
        if category_id in self.__cached_category_ids:
            return None
        # ---
        url: str = self.get_category_id_url(category_id)
        try:
            data, updated_at, is_updated = self.load_from_esi(url)
        except requests.exceptions.HTTPError as err:
            status_code = err.response.status_code
            if status_code == 404:
                # поступаем аналогично алгоритму в actualize_type_id, где часть item_types может быть Not Found, хотя
                # они есть в ассетах, а с 2022-10-14 хранение данных в таблице eve_sde_type_ids перманентно (ранее при
                # обновлении sde данные из таблицы полностью удалялись), т.о. часть type_ids хранится
                # вечно, даже будучи удалена из ESI
                # помечаем такой group_id признаком not published, тогда же он перестанет попадать сюда впредь
                self.dbswagger.update_category_id_as_not_published(category_id)
                # сохраняем идентификатор загруженных и добавленных в БД данных
                self.__cached_category_ids.add(category_id)
                return None
            else:
                # print(sys.exc_info())
                # raise
                return None  # продолжить загрузку очень важно!
        except:
            # print(sys.exc_info())
            # raise
            return None  # продолжить загрузку очень важно!

        if data is None:
            return None

        # сперва добавляем категорию, а потом в неё добавляем связанные с нею группы
        self.dbswagger.insert_or_update_category_id(data)

        # сохраняем идентификатор загруженных и добавленных в БД данных
        self.__cached_category_ids.add(category_id)

        # поскольку мы оказались в этом методе, то это новая категория группы товаров
        # прочие группы в этой же категории отсутствуют в БД, а мы знаем их номера - тоже добавляем их в БД
        for group_id in data['groups']:
            # проверяем, возможно ли зацикливание при загрузке сопутствующих данных?
            url: str = self.get_group_id_url(group_id)
            if self.depth.push(url):
                self.actualize_group_id(group_id)
                self.depth.pop()

        return data

    # -------------------------------------------------------------------------
    # /universe/groups/
    # /universe/groups/{group_id}/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_group_id_url(group_id: int) -> str:
        # Requires: piblic access
        return "universe/groups/{group_id}/".format(group_id=group_id)

    def actualize_group_id_details(self, group_id_data) -> None:
        # сохраняем сопутствующие данные в БД
        # проверяем, возможно ли зацикливание при загрузке сопутствующих данных?
        category_id: int = group_id_data['category_id']
        url: str = self.get_category_id_url(category_id)
        if self.depth.push(url):
            self.actualize_category_id(category_id)
            self.depth.pop()

    def actualize_group_id(self, group_id: int) -> None:
        # проверяем только то, что группа/категория присутствует в БД по указанному идентификатору
        # исходим из того, что группы/категории не модифицируются CCP-шниками, только добавляются
        if group_id in self.__cached_group_ids:
            return
        # ---
        url: str = self.get_group_id_url(group_id)
        try:
            data, updated_at, is_updated = self.load_from_esi(url)
        except requests.exceptions.HTTPError as err:
            status_code = err.response.status_code
            if status_code == 404:
                # поступаем аналогично алгоритму в actualize_type_id, где часть item_types может быть Not Found, хотя
                # они есть в ассетах, а с 2022-10-14 хранение данных в таблице eve_sde_type_ids перманентно (ранее при
                # обновлении sde данные из таблицы полностью удалялись), т.о. часть type_ids хранится
                # вечно, даже будучи удалена из ESI
                # помечаем такой group_id признаком not published, тогда же он перестанет попадать сюда впредь
                self.dbswagger.update_group_id_as_not_published(group_id)
                # сохраняем идентификатор загруженных и добавленных в БД данных
                self.__cached_group_ids.add(group_id)
                return
            else:
                # print(sys.exc_info())
                # raise
                return  # продолжить загрузку очень важно!
        except:
            # print(sys.exc_info())
            # raise
            return  # продолжить загрузку очень важно!

        if data is None:
            return

        # сперва актуализируем связанные данные, с тем чтобы они автоматически добавились в БД до того, как будет
        # произведена попытка добавления товара без соответствующих групп и ограничений на связанные ключи
        self.actualize_group_id_details(data)
        # добавляем данные по новомй группе в БД
        self.dbswagger.insert_or_update_group_id(data)

        # сохраняем идентификатор загруженных и добавленных в БД данных
        self.__cached_group_ids.add(group_id)

        # поскольку мы оказались в этом методе, то это новая группа товаров
        # прочие товары в этой же группе отсутствуют в БД, а мы знаем их номера - тоже добавляем их в БД
        for type_id in data['types']:
            if type_id not in self.__cached_type_ids:
                # проверяем, возможно ли зацикливание при загрузке сопутствующих данных?
                url: str = self.get_type_id_url(type_id)
                if self.depth.push(url):
                    self.actualize_type_id(type_id)
                    self.depth.pop()

        del data

    # -------------------------------------------------------------------------
    # /markets/groups/
    # /markets/groups/{market_group_id}/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_market_group_id_url(market_group_id: int) -> str:
        # Requires: piblic access
        return "markets/groups/{market_group_id}/".format(market_group_id=market_group_id)

    def actualize_market_group_id_details(self, market_group_id_data) -> None:
        # сохраняем сопутствующие данные в БД
        if 'parent_group_id' in market_group_id_data:
            # проверяем, возможно ли зацикливание при загрузке сопутствующих данных?
            parent_group_id: int = market_group_id_data['parent_group_id']
            url: str = self.get_market_group_id_url(parent_group_id)
            if self.depth.push(url):
                self.actualize_market_group_id(parent_group_id)
                self.depth.pop()

    def actualize_market_group_id(self, market_group_id: int) -> None:
        # проверяем только то, что группа/категория присутствует в БД по указанному идентификатору
        # исходим из того, что группы/категории не модифицируются CCP-шниками, только добавляются
        if market_group_id in self.__cached_market_group_ids:
            return
        # ---
        url: str = self.get_market_group_id_url(market_group_id)
        try:
            data, updated_at, is_updated = self.load_from_esi(url)
        except requests.exceptions.HTTPError as err:
            status_code = err.response.status_code
            if status_code == 404:
                return
            else:
                # сохраняем идентификатор загруженных и добавленных в БД данных (больше в этот метод входить не надо)
                self.__cached_market_group_ids.add(market_group_id)
                # print(sys.exc_info())
                # raise
                return  # продолжить загрузку очень важно!
        except:
            # print(sys.exc_info())
            # raise
            return  # продолжить загрузку очень важно!

        if data is None:
            return

        # сперва актуализируем связанные данные, с тем чтобы они автоматически добавились в БД до того, как будет
        # произведена попытка добавления товара без соответствующих групп и ограничений на связанные ключи
        self.actualize_market_group_id_details(data)
        # добавляем данные по новому предмету в БД
        self.dbswagger.insert_or_update_market_group_id(data)

        # сохраняем идентификатор загруженных и добавленных в БД данных
        self.__cached_market_group_ids.add(market_group_id)

        # поскольку мы оказались в этом методе, то это новая группа товаров
        # прочие товары в этой же группе отсутствуют в БД, а мы знаем их номера - тоже добавляем их в БД
        for type_id in data['types']:
            if type_id not in self.__cached_type_ids:
                # проверяем, возможно ли зацикливание при загрузке сопутствующих данных?
                url: str = self.get_type_id_url(type_id)
                if self.depth.push(url):
                    self.actualize_type_id(type_id)
                    self.depth.pop()

        del data

    # -------------------------------------------------------------------------
    # /universe/types/
    # /universe/types/{type_id}/
    # -------------------------------------------------------------------------

    @staticmethod
    def get_types_url() -> str:
        # Requires: piblic access
        return "universe/types/"

    @staticmethod
    def get_type_id_url(type_id: int) -> str:
        # Requires: piblic access
        return "universe/types/{type_id}/".format(type_id=type_id)

    def actualize_type_id_details(self, type_id_data) -> None:
        # сохраняем сопутствующие данные в БД
        # проверяем, возможно ли зацикливание при загрузке сопутствующих данных?
        group_id: int = type_id_data['group_id']
        url: str = self.get_group_id_url(group_id)
        if self.depth.push(url):
            self.actualize_group_id(type_id_data['group_id'])
            self.depth.pop()
        if 'market_group_id' in type_id_data:
            # проверяем, возможно ли зацикливание при загрузке сопутствующих данных?
            market_group_id: int = type_id_data['market_group_id']
            url: str = self.get_market_group_id_url(market_group_id)
            if self.depth.push(url):
                self.actualize_market_group_id(market_group_id)
                self.depth.pop()

    def actualize_type_id(self, type_id: int):
        # проверяем только то, что группа/категория присутствует в БД по указанному идентификатору
        # исходим из того, что группы/категории не модифицируются CCP-шниками, только добавляются
        if type_id in self.__cached_type_ids:
            return None
        # ---
        url: str = self.get_type_id_url(type_id)
        try:
            data, updated_at, is_updated = self.load_from_esi(url)
        except requests.exceptions.HTTPError as err:
            status_code = err.response.status_code
            if status_code == 404:
                # НЕ странно, часть item_types может быть Not Found, хотя они есть в ассетах
                # с 2022-10-14 хранение данных в таблице eve_sde_type_ids перманентно (ранее при
                # обновлении sde данные из таблицы полностью удалялись), т.о. часть type_ids хранится
                # вечно, даже будучи удалена из ESI
                # помечаем такой type_id признаком not published, тогда же он перестанет попадать сюда впредь
                self.dbswagger.update_type_id_as_not_published(type_id)
                # сохраняем идентификатор загруженных и добавленных в БД данных
                self.__cached_type_ids.add(type_id)
                return None
            else:
                # print(sys.exc_info())
                # raise
                return None  # продолжить загрузку очень важно!
        except:
            # print(sys.exc_info())
            # raise
            return None  # продолжить загрузку очень важно!

        if data is None:
            return None

        # сперва актуализируем связанные данные, с тем чтобы они автоматически добавились в БД до того, как будет
        # произведена попытка добавления товара без соответствующих групп и ограничений на связанные ключи
        self.actualize_type_id_details(data)
        # добавляем данные по новому предмету в БД
        self.dbswagger.insert_or_update_type_id(type_id, data, updated_at)

        # сохраняем идентификатор загруженных и добавленных в БД данных
        self.__cached_type_ids.add(type_id)

        return data

    def actualize_type_ids(self, full_database_upgrade: bool = True) -> int:
        # Внимание! установка full_database_upgrade=False не защищает от возможной длительной работы этого метода при
        #           обновлении всех справочников в БД (например когда справочник был обновлён из q_dictionaries.py)
        #           (здесь этот параметр скорее имеет отладочное применение)
        # ---
        # сначала проверяем содержимое БД и актуализируем её
        # получаем либо весь набор type_ids (если есть маркер type_id=-1, свидетельствующий о
        # полном устаревании данных), либо получаем лишь те записи, у которых нет известного параметра
        # packaged_volume (а он есть даже у элемента '#System', и равен 0)
        obsolete_type_ids = self.dbswagger.get_obsolete_type_ids_from_dictionary()
        # получаем отсутствющие в БД типы элементов, например подарочные наборы,
        # которые внезапно появились в ассетах
        absent_type_ids = self.dbswagger.select_unknown_type_ids()  # 59978 = 'Amarr Foundation Day Pants Crate'
        # если содержимое БД не содержит неактуальную информацию, то обращаемся к ESI для полчения type_ids
        known_type_ids = None
        if not obsolete_type_ids and not absent_type_ids:
            url: str = self.get_types_url()
            known_type_ids, updated_at, is_updated = self.load_from_esi_paged_data(url)

            if known_type_ids is None:
                return 0
            if self.esiswagger.offline_mode:
                pass
            elif not is_updated:
                return 0

        # получение набора type_ids по которым надо запросить информацию с ESI
        type_ids_to_renew: typing.Set[int] = set()
        obsolete_type_ids_marker = False
        if obsolete_type_ids:
            type_ids_to_renew |= set(obsolete_type_ids)
            del obsolete_type_ids
            obsolete_type_ids_marker = True
        if absent_type_ids:
            type_ids_to_renew |= set(absent_type_ids)
            del absent_type_ids
        if known_type_ids:
            type_ids_to_renew |= set(known_type_ids)
            del known_type_ids

        quantity_of_actualized_type_ids: int = 0
        if full_database_upgrade:
            # будем заниматься ПОЛНОЙ перезагрузкой справочных данных по товарам, поэтому стираем все идентификаторы
            self.__cached_type_ids.clear()
            self.__cached_market_group_ids.clear()
            self.__cached_group_ids.clear()
            self.__cached_category_ids.clear()
        else:
            # обновляем только те данные, которых не хватает (помечены устаревшими, или же появились откуда-то)
            self.__cached_type_ids -= type_ids_to_renew
        quantity_of_actualized_type_ids = len(self.__cached_type_ids)

        for type_id in type_ids_to_renew:
            if type_id not in self.__cached_type_ids:
                url: str = self.get_type_id_url(type_id)
                if self.depth.push(url):
                    self.actualize_type_id(type_id)
                    self.depth.pop()
        quantity_of_actualized_type_ids = len(self.__cached_type_ids) - quantity_of_actualized_type_ids

        del type_ids_to_renew

        # удаляем из БД маркер "Waiting automatic data update from ESI"
        if obsolete_type_ids_marker:
            self.dbswagger.remove_obsolete_type_ids_marker_from_dictionary()

        # commit выплолняется даже при пустом actualized_type_ids, т.к. устаревшие элементы
        # отправляются в not published без попадания в actialized-список
        self.qidb.commit()

        # загрузка из БД type_ids, market_group_ids, group_ids, category_ids (в таблицах в БД таких данных может быть
        # больше, чем может выдать ESI, т.к. БД может хранить устаревшие non published товары)
        self.prepare_goods_dictionaries()

        return quantity_of_actualized_type_ids
