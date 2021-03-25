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

import eve_esi_interface as esi
import postgresql_interface as db

import q_industrialist_settings

from __init__ import __version__


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

    def is_obj_equal(self, data):
        for key in self.obj:
            if (key in data) and (data[key] != self.obj[key]):
                return False
        return True

    def is_obj_equal_by_keys(self, data, keys):
        for key in keys:
            if key in data:
                if not (key in self.obj):
                    return False
                elif data[key] != self.obj[key]:
                    return False
            else:
                if not (key in self.obj):
                    pass
                elif data[key] != self.obj[key]:
                    return False
        return True


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
    corporation_industry_job_diff = ['status']

    def __init__(self, module_name, debug):
        """ constructor

        :param module_name: name of Q.Industrialist' module
        :param debug: debug mode to show SQL queries
        """
        self.qidb = db.QIndustrialistDatabase(module_name, debug=debug)
        self.qidb.connect(q_industrialist_settings.g_database)

        self.dbswagger = db.QSwaggerInterface(self.qidb)

        self.esiswagger = None
        self.eve_now = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)

        self.__cached_characters: typing.Dict[int, QEntity] = {}
        self.__cached_corporations: typing.Dict[int, QEntity] = {}
        self.__cached_stations: typing.Dict[int, QEntity] = {}
        self.__cached_structures: typing.Dict[int, QEntity] = {}
        self.__cached_corporation_structures: typing.Dict[int, QEntity] = {}
        self.__cached_corporation_assets: typing.Dict[int, typing.Dict[int, QEntity]] = {}
        self.__cached_corporation_blueprints: typing.Dict[int, typing.Dict[int, QEntity]] = {}
        self.__cached_corporation_industry_jobs: typing.Dict[int, typing.Dict[int, QEntity]] = {}
        self.prepare_cache()

        self.depth = QEntityDepth()

    def __del__(self):
        """ destructor
        """
        del self.depth

        del self.__cached_corporation_industry_jobs
        del self.__cached_corporation_blueprints
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

    def auth_pilot_by_name(self, pilot_name, offline_mode, cache_files_dir):
        # настройка Eve Online ESI Swagger interface
        auth = esi.EveESIAuth(
            '{}/auth_cache'.format(cache_files_dir),
            debug=True)
        client = esi.EveESIClient(
            auth,
            debug=False,
            logger=True,
            user_agent='Q.Industrialist v{ver}'.format(ver=__version__))
        self.esiswagger = esi.EveOnlineInterface(
            client,
            q_industrialist_settings.g_client_scope,
            cache_dir='{}/esi_cache'.format(cache_files_dir),
            offline_mode=offline_mode)

        authz = self.esiswagger.authenticate(pilot_name)
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

    def get_corp_cache(self, cache, corporation_id):
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

    # -------------------------------------------------------------------------
    # e v e   s w a g g e r   i n t e r f a c e
    # -------------------------------------------------------------------------

    def load_from_esi(self, url: str, fully_trust_cache=False):
        data = self.esiswagger.get_esi_data(
            url,
            fully_trust_cache=fully_trust_cache)
        updated_at = self.esiswagger.last_modified
        return data, updated_at

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

    def get_character_url(self, character_id: int):
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
            # Public information about a character
            url: str = self.get_character_url(character_id)
            data, updated_at = self.load_from_esi(url, fully_trust_cache=in_cache is None)
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

    def get_corporation_url(self, corporation_id: int):
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
            data, updated_at = self.load_from_esi(url, fully_trust_cache=in_cache is None)
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

    def get_universe_station_url(self, station_id: int):
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
            data, updated_at = self.load_from_esi(url, fully_trust_cache=in_cache is None)
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

    def get_universe_structure_url(self, structure_id: int):
        # Requires: access token
        return "universe/structures/{structure_id}/".format(structure_id=structure_id)

    def load_universe_structure_from_esi(self, structure_id, fully_trust_cache=True):
        try:
            # Requires: access token
            url: str = self.get_universe_structure_url(structure_id)
            data, updated_at = self.load_from_esi(url, fully_trust_cache=fully_trust_cache)
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
            return data, 0

        data_new = self.dbswagger.get_absent_universe_structure_ids(data)
        data_new = [id[0] for id in data_new]

        # data = [1035620655696, 1035660997658, 1035620697572, ... ]
        # data_new = [1035620655696]

        for structure_id in data_new:
            self.actualize_universe_structure(structure_id, need_data=False)
        self.qidb.commit()

        return data, len(data_new)

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/structures/
    # -------------------------------------------------------------------------

    def get_corporation_structures_url(self, corporation_id: int):
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
    # corporations/{corporation_id}/assets/
    # -------------------------------------------------------------------------

    def get_corporation_assets_url(self, corporation_id: int):
        # Requires role(s): Director
        return "corporations/{corporation_id}/assets/".format(corporation_id=corporation_id)

    def actualize_corporation_asset_item_details(self, item_data, need_data=False):
        type_id: int = int(item_data['type_id'])
        if type_id == 27:  # Office
            location_id: int = int(item_data['location_id'])
            self.actualize_station_or_structure(location_id, need_data=need_data)

    def actualize_corporation_asset_item(self, corporation_id: int, item_data, updated_at):
        item_id: int = int(item_data['item_id'])
        corp_cache = self.get_corp_cache(self.__cached_corporation_assets, corporation_id)
        in_cache = corp_cache.get(item_id)
        # 1. либо данных нет в кеше
        # 2. если данные с таким id существуют, то проверяем изменились ли они в кеше
        #    если данные изменились, то надо также обновить их в БД
        data_equal: bool = False
        if not in_cache:
            pass
        elif in_cache.obj:
            data_equal = in_cache.is_obj_equal_by_keys(item_data, self.corporation_asset_diff)
        # ---
        # из соображений о том, что корпоративные ассеты может читать только пилот с ролью корпорации,
        # выполняем обновление сведений как о структурах и станциях, где расположены офисы (и т.п.), а в случае
        # необходимости подгружаем данные из БД
        self.actualize_corporation_asset_item_details(item_data, need_data=True)
        # данные с серверов CCP уже загружены, в случае необходимости обновляем данные в БД
        if data_equal:
            return
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
        data, updated_at, is_updated = self.load_from_esi_paged_data(url)
        if self.esiswagger.offline_mode:
            updated_at = self.eve_now
        elif not is_updated:
            return data

        # список ассетов имеющихся у корпорации, хранящихся в БД, в кеше, а также новых и исчезнувших
        corp_cache = self.__cached_corporation_assets.get(corporation_id)
        ids_from_esi, ids_in_cache, new_ids, deleted_ids = self.get_cache_status(
            corp_cache,
            data, 'item_id',
            debug=False  # corporation_id == 98150545
        )
        if not ids_from_esi:
            return data

        if self.depth.push(url):
            for item_data in data:
                self.actualize_corporation_asset_item(corporation_id, item_data, updated_at)
            self.depth.pop()

        # параметр updated_at меняется в случае, если меняются данные корпоративной структуры, т.ч. не
        # использует массовое обновление всех корпоративных структур, а лишь удаляем исчезнувшие
        self.dbswagger.delete_obsolete_corporation_assets(deleted_ids)
        self.qidb.commit()

        return data

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

    def get_corporation_blueprints_url(self, corporation_id: int):
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
        if self.esiswagger.offline_mode:
            updated_at = self.eve_now
        elif not is_updated:
            return data

        # подгружаем данные из БД в кеш с тем, чтобы сравнить данные в кеше и данные от ССР
        self.prepare_corp_cache(
            self.dbswagger.get_exist_corporation_blueprints(corporation_id),
            self.__cached_corporation_blueprints,
            'item_id',
            None
        )

        # список ассетов имеющихся у корпорации, хранящихся в БД, в кеше, а также новых и исчезнувших
        corp_cache = self.__cached_corporation_blueprints.get(corporation_id)
        ids_from_esi, ids_in_cache, new_ids, deleted_ids = self.get_cache_status(
            corp_cache,
            data, 'item_id',
            debug=False  # corporation_id == 98150545
        )
        if not ids_from_esi:
            return data

        if self.depth.push(url):
            for item_data in data:
                self.actualize_corporation_blueprint_item(corporation_id, item_data, updated_at)
            self.depth.pop()

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

        return data

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/industry/jobs/
    # -------------------------------------------------------------------------

    def get_corporation_industry_jobs_url(self, corporation_id: int):
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
            if in_cache.obj['status'] == 'delivered':
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
        if self.esiswagger.offline_mode:
            updated_at = self.eve_now
        elif not is_updated:
            return data

        # подгружаем данные из БД в кеш с тем, чтобы сравнить данные в кеше и данные от ССР
        oldest_delivered_job = None
        for job_data in data:
            if job_data['status'] != 'delivered':
                continue
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
        if self.depth.push(url):
            for job_data in data:
                self.actualize_corporation_industry_job_item(corporation_id, job_data, updated_at)
            self.depth.pop()
        self.qidb.commit()

        return data

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/blueprints/
    # corporations/{corporation_id}/industry/jobs/
    # -------------------------------------------------------------------------

    def link_blueprints_and_jobs(self, _corporation_id):
        corporation_id: int = int(_corporation_id)

        actualized_jobs = []
        actualized_bpcs = []

        corp_cache_j = self.get_corp_cache(self.__cached_corporation_industry_jobs, corporation_id)
        corp_cache_b = self.get_corp_cache(self.__cached_corporation_blueprints, corporation_id)

        if corp_cache_j:
            for job_id in corp_cache_j:
                in_cache = corp_cache_j.get(job_id)
                if not in_cache.ext:  # признак того, что данные считаны из БД в кеш и не менялись
                    continue
                if not (in_cache.obj['activity_id'] in (5,8)):  # copy & invent
                    continue
                #if in_cache.obj['status'] != 'delivered':  # добавляем в таблицу только законченные работы
                #    continue
                # just_added: (в БД job-а нет), но это предположительно!
                # changed: изменился status у job-а
                if in_cache.ext.get('just_added', False) or in_cache.ext.get('changed', False):
                    # пропускаем jobs, по которым нет данных о расположении фабрики
                    facility_id: int = int(in_cache.obj['facility_id'])
                    system_id = self.get_system_id_of_station_or_structure(facility_id)
                    if not system_id:
                        continue
                    actualized_jobs.append(in_cache.obj)
                    actualized_jobs[-1].update({'ext': {'system_id': system_id}})
                    # пытаемся получить информацию по me и te чертежа, который используется в работе
                    # (такой подход имеет смысл только при отслеживании параметров БПО, которые
                    # "не кончаются" и как правило лежат в одном и том же контейнере, т.ч. долгое
                    # время известны в ассетах корпорации)
                    bp_in_cache = corp_cache_b.get(int(in_cache.obj['blueprint_id']))
                    if not (bp_in_cache is None):
                        actualized_jobs[-1]['ext'].update({
                            'bp_te': bp_in_cache.obj['time_efficiency'],
                            'bp_me': bp_in_cache.obj['material_efficiency'],
                        })
                    # debug:
                    print('JOB JOB JOB', actualized_jobs[-1])

        if corp_cache_b:
            for item_id in corp_cache_b:
                in_cache = corp_cache_b.get(item_id)
                if not in_cache.ext:  # признак того, что данные считаны из БД в кеш и не менялись
                    continue
                if in_cache.obj['quantity'] != -2:  # ищем только копии, как продукты copy & invent
                    continue
                # just_added: (в БД чертежа нет), но это предположительно!
                # changed: изменился status у чертежа
                # deleted: чертёж исчез из портассетов (использован, удалён, перемещён, передан)
                if in_cache.ext.get('just_added', False) or in_cache.ext.get('changed', False) or in_cache.ext.get('deleted', False):
                    # пропускаем БП, по которым нет данных о расположении
                    system_id = self.get_system_id_of_item(corporation_id, in_cache.obj['location_id'])
                    if not system_id:
                        continue
                    actualized_bpcs.append(in_cache.obj)
                    actualized_bpcs[-1].update({'ext': {'system_id': system_id}})
                    # debug:
                    print('BPC BPC BPC', actualized_bpcs[-1])

        del corp_cache_b
        del corp_cache_j
        return

        # сохраняем в БД только что найденные чертежи и работы, оставляем их там "мариноваться"
        # до тех пор, пока у ним не подгрузятся стоимость выполненных работ и все прочие данные
        self.dbswagger.insert_into_blueprint_costs(
            corporation_id,
            actualized_jobs, self.eve_now,
            actualized_bpcs, self.eve_now)
        self.qidb.commit()

        del actualized_jobs
        del actualized_bpcs

        # вычитываем необъединённые чертежи и ищем им парные работы по копирке, объединяем их
        self.dbswagger.link_blueprint_copies_with_jobs()
        self.qidb.commit()

        self.dbswagger.link_blueprint_invents_with_jobs()
