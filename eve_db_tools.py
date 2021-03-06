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

    def __init__(self, module_name, debug):
        """ constructor

        :param module_name: name of Q.Industrialist' module
        :param debug: debug mode to show SQL queries
        """
        self.qidb = db.QIndustrialistDatabase(module_name, debug=debug)  # True)  # debug)
        self.qidb.connect(q_industrialist_settings.g_database)

        self.dbswagger = db.QSwaggerInterface(self.qidb)

        self.esiswagger = None
        self.eve_now = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)

        self.__cached_characters: typing.Dict[int, QEntity] = {}
        self.__cached_corporations: typing.Dict[int, QEntity] = {}
        self.__cached_stations: typing.Dict[int, QEntity] = {}
        self.__cached_structures: typing.Dict[int, QEntity] = {}
        self.__cached_corporation_structures: typing.Dict[int, QEntity] = {}
        self.prepare_cache()

        self.depth = QEntityDepth()

    def __del__(self):
        """ destructor
        """
        del self.depth

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

    # -------------------------------------------------------------------------
    # e v e   s w a g g e r   i n t e r f a c e
    # -------------------------------------------------------------------------

    def load_from_esi(self, url: str, fully_trust_cache=True):
        data = self.esiswagger.get_esi_data(
            url,
            fully_trust_cache=fully_trust_cache)
        updated_at = self.esiswagger.last_modified
        return data, updated_at

    def load_from_esi_paged_data(self, url: str, fully_trust_cache=True):
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
            # сохраняем данные в БД, при этом актуализируем дату последней работы с esi
            if updated_at < self.eve_now:
                updated_at = self.eve_now
            self.dbswagger.insert_or_update_character(character_id, data, updated_at)
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
            # сохраняем данные в БД, при этом актуализируем дату последней работы с esi
            if updated_at < self.eve_now:
                updated_at = self.eve_now
            self.dbswagger.insert_or_update_corporation(corporation_id, data, updated_at)
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
            # сохраняем данные в БД, при этом актуализируем дату последней работы с esi
            if updated_at < self.eve_now:
                updated_at = self.eve_now
            self.dbswagger.insert_or_update_universe_station(data, updated_at)
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
            # сохраняем данные в БД, при этом актуализируем дату последней работы с esi
            if updated_at < self.eve_now:
                updated_at = self.eve_now
            self.dbswagger.insert_or_update_universe_structure(structure_id, data, forbidden, updated_at)
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
        # 2. если данные с таким id существуют, но внешнему коду не интересны сами данные, то выход выход
        # 3. либо данные в текущую сессию работы программы уже загружались
        # 4. данные с таким id существуют, но самих данных нет (видимо хранится только id вместе с at)
        #    проверяем дату-время последнего обновления информации, и обновляем устаревшие данные
        data_equal: bool = False
        if not in_cache:
            data_equal = False
        elif in_cache.obj:
            data_equal = True
            for key in in_cache.obj:
                if (key in structure_data) and (structure_data[key] != in_cache.obj[key]):
                    data_equal = False
                    break
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
        data, updated_at, is_updated = self.load_from_esi_paged_data(url)

        is_updated = self.esiswagger.is_last_data_updated
        if not is_updated:
            return data, 0

        # список структур имеющихся у корпорации
        ids_from_esi: typing.List[int] = [int(s["structure_id"]) for s in data]
        if not ids_from_esi:
            return data, 0
        # кешированный, м.б. устаревший список корпоративных структур
        ids_in_cache: typing.List[int] = [id for id in self.__cached_corporation_structures.keys()]
        # список структур, появившихся у корпорации и отсутствующих в кеше (в базе данных)
        new_ids: typing.List[int] = [id for id in ids_from_esi if not self.__cached_corporation_structures.get(id)]
        # список корпоративных структур, которых больше нет у корпорации (кеш устарел и база данных устарела)
        deleted_ids: typing.List[int] = [id for id in ids_in_cache if not (id in ids_from_esi)]

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

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/assets/
    # -------------------------------------------------------------------------

    def actualize_corporation_assets(self, corporation_id):
        # Requires role(s): Director
        corp_assets_data = self.esiswagger.get_esi_paged_data(
            "corporations/{}/assets/".format(corporation_id))

        corp_assets_updated = self.esiswagger.is_last_data_updated
        if not corp_assets_updated:
            return corp_assets_data
        corp_assets_updated_at = self.esiswagger.last_modified

        self.dbswagger.clear_corporation_assets(corporation_id)
        for assets_data in corp_assets_data:
            type_id = assets_data['type_id']

            # пропускаем все ассеты, которые не являются офисами (экономим время на работу с БД,
            # пока такая работа не сделана по-нормальному)
            if type_id != 27:
                continue

            self.dbswagger.insert_corporation_assets(assets_data, corporation_id, corp_assets_updated_at)
            location_id = assets_data['location_id']
            if type_id == 27:  # Office
                self.actualize_station_or_structure(location_id)
        self.qidb.commit()

        return corp_assets_data
