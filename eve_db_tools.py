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
        :param at: дата/время последней актуализации кешированных данных (хранящихся в БД)
        """
        self.db: bool = db
        self.esi: bool = esi
        self.obj: typing.Any = obj
        self.at: datetime.datetime = at

    def store(self, db, esi, obj, at):
        self.db: bool = db
        self.esi: bool = esi
        self.obj: typing.Any = obj
        self.at: datetime.datetime = at


class QDatabaseTools:
    character_timedelta = datetime.timedelta(days=3)
    corporation_timedelta = datetime.timedelta(days=5)

    def __init__(self, module_name, debug):
        """ constructor

        :param module_name: name of Q.Industrialist' module
        :param debug: debug mode to show SQL queries
        """
        self.qidb = db.QIndustrialistDatabase(module_name, debug=True)  # debug)
        self.qidb.connect(q_industrialist_settings.g_database)

        self.dbswagger = db.QSwaggerInterface(self.qidb)

        self.esiswagger = None
        self.eve_now = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)

        self.__cached_characters: typing.Dict[int, QEntity] = {}
        self.__cached_corporations: typing.Dict[int, QEntity] = {}
        self.__cached_stations: typing.Dict[int, typing.Any] = {}
        self.__cached_structures: typing.Dict[int, typing.Any] = {}
        self.prepare_cache()

    def __del__(self):
        """ destructor
        """
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

    # -------------------------------------------------------------------------
    # characters/{character_id}/
    # -------------------------------------------------------------------------

    def load_character_from_esi(self, character_id, fully_trust_cache=True):
        # Public information about a character
        data = self.esiswagger.get_esi_data(
            "characters/{}/".format(character_id),
            fully_trust_cache=fully_trust_cache)
        updated_at = self.esiswagger.last_modified
        return data, updated_at

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
            return in_cache.obj
        elif (in_cache.at + self.character_timedelta) < self.eve_now:
            reload_esi = True
        # ---
        # загружаем данные с серверов CCP или загружаем данные из БД
        if reload_esi:
            data, updated_at = self.load_character_from_esi(
                character_id,
                fully_trust_cache=in_cache is None
            )
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
        return data

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/
    # -------------------------------------------------------------------------

    def load_corporation_from_esi(self, corporation_id, fully_trust_cache=True):
        # Public information about a corporation
        data = self.esiswagger.get_esi_data(
            "corporations/{}/".format(corporation_id),
            fully_trust_cache=fully_trust_cache)
        updated_at = self.esiswagger.last_modified
        return data, updated_at

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
            return in_cache.obj
        elif (in_cache.at + self.corporation_timedelta) < self.eve_now:
            reload_esi = True
        # ---
        # загружаем данные с серверов CCP или загружаем данные из БД
        if reload_esi:
            data, updated_at = self.load_corporation_from_esi(
                corporation_id,
                fully_trust_cache=in_cache is None
            )
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

        #   # сохраняем сопутствующие данные в БД
        #   self.actualize_character(corporation_data['ceo_id'])
        #   if corporation_data['creator_id'] != 1:  # EVE System
        #       self.actualize_character(corporation_data['creator_id'])
        #   if 'home_station_id' in corporation_data:
        #       self.actualize_station_or_structure(
        #           corporation_data['home_station_id'],
        #           skip_corporation=True  # чтобы программа не зациклилась
        #       )

        return data

    def actualize_corporation2(self, _corporation_id, need_data=False):
        corporation_id: int = int(_corporation_id)
        in_cache = self.__cached_corporations.get(corporation_id)
        if not in_cache:
            # Public information about a corporation
            corporation_data = self.esiswagger.get_esi_data(
                "corporations/{}/".format(corporation_id),
                fully_trust_cache=True)
            corporation_updated_at = self.esiswagger.last_modified
            # сохраняем данные в БД
            self.dbswagger.insert_corporation(
                corporation_id,
                corporation_data,
                corporation_updated_at
            )
            # сохраняем данные в кеше
            self.__cached_corporations[corporation_id] = QEntity(
                True, True, corporation_data, corporation_updated_at)
            return corporation_data
        elif not need_data:
            return None
        elif in_cache.obj:
            return in_cache.obj
        else:
            # есть в кеше, но данных нет (видимо хранится только id)
            corporation_data, corporation_updated_at = self.dbswagger.select_corporation(corporation_id)
            self.__cached_corporations[corporation_id].store(
                True, True, corporation_data, corporation_updated_at)
            # Внимание! в этой точке надо проверить дату-время последнего обновления информации,
            # и обновить устаревшие данные
            return corporation_data

    # -------------------------------------------------------------------------
    # universe/stations/{station_id}/
    # -------------------------------------------------------------------------

    def actualize_universe_station(self, station_id):
        try:
            if not (station_id in self.__cached_stations):
                # Requires: access token
                universe_station_data = self.esiswagger.get_esi_data(
                    "universe/stations/{}/".format(station_id),
                    fully_trust_cache=True)
                # сохраняем данные в БД
                self.dbswagger.insert_universe_station(
                    universe_station_data,
                    self.esiswagger.last_modified
                )
                # сохраняем данные в кеше
                self.__cached_stations[station_id] = universe_station_data
                return universe_station_data
            else:
                return self.__cached_stations.get(station_id)
        except requests.exceptions.HTTPError as err:
            status_code = err.response.status_code
            if status_code == 403:  # это нормально, что часть станций со временем могут оказаться Forbidden
                pass
                return None
            else:
                # print(sys.exc_info())
                raise
        except:
            print(sys.exc_info())
            raise

    # -------------------------------------------------------------------------
    # universe/structures/{structure_id}/
    # -------------------------------------------------------------------------

    def actualize_universe_structure(self, structure_id):
        try:
            if not (structure_id in self.__cached_structures):
                # Requires: access token
                universe_structure_data = self.esiswagger.get_esi_data(
                    "universe/structures/{}/".format(structure_id),
                    fully_trust_cache=True)
                # сохраняем данные в БД
                self.dbswagger.insert_universe_structure(
                    structure_id,
                    universe_structure_data,
                    self.esiswagger.last_modified
                )
                # сохраняем данные в кеше
                self.__cached_structures[structure_id] = universe_structure_data
                return universe_structure_data
            else:
                return self.__cached_structures.get(structure_id)
        except requests.exceptions.HTTPError as err:
            status_code = err.response.status_code
            if status_code == 403:  # это нормально, что часть структур со временем могут оказаться Forbidden
                pass
                return None
            else:
                # print(sys.exc_info())
                raise
        except:
            print(sys.exc_info())
            raise

    # -------------------------------------------------------------------------
    # universe/structures/
    # -------------------------------------------------------------------------

    def actualize_universe_structures(self):
        # Requires: access token
        universe_structures_data = self.esiswagger.get_esi_paged_data('universe/structures/')

        universe_structures_updated = self.esiswagger.is_last_data_updated
        if not universe_structures_updated:
            return universe_structures_data, 0

        universe_structures_new = self.dbswagger.get_absent_universe_structure_ids(
            universe_structures_data
        )
        universe_structures_new = [id[0] for id in universe_structures_new]

        # universe_structures_data = [1035620655696, 1035660997658, 1035620697572, ... ]
        # universe_structures_new = [1035620655696]

        for structure_id in universe_structures_new:
            self.actualize_universe_structure(structure_id)
        self.qidb.commit()

        return universe_structures_data, len(universe_structures_new)

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/structures/
    # -------------------------------------------------------------------------

    def actualize_corporation_structures(self, corporation_id):
        # Requires role(s): Station_Manager
        corp_structures_data = self.esiswagger.get_esi_paged_data(
            "corporations/{}/structures/".format(corporation_id))

        corp_structures_updated = self.esiswagger.is_last_data_updated
        if not corp_structures_updated:
            return corp_structures_data, 0
        corp_structures_updated_at = self.esiswagger.last_modified

        corp_structures_ids = [s["structure_id"] for s in corp_structures_data]
        if not corp_structures_ids:
            return corp_structures_data, 0

        corp_structures_newA = self.dbswagger.get_absent_universe_structure_ids(corp_structures_ids)
        corp_structures_newA = [id[0] for id in corp_structures_newA]
        corp_structures_newB = self.dbswagger.get_absent_corporation_structure_ids(corp_structures_ids)
        corp_structures_newB = [id[0] for id in corp_structures_newB]
        corp_structures_new = corp_structures_newA[:]
        corp_structures_new.extend(corp_structures_newB)
        corp_structures_new = list(dict.fromkeys(corp_structures_new))

        # corp_structures_ids = [1035620655696,1035660997658,1035620697572]
        # corp_structures_newA = [1035660997658]
        # corp_structures_newB = [1035620655696,1035660997658]
        # corp_structures_new = [1035620655696,1035660997658]

        # выше были найдены идентификаторы тех структур, которых нет либо в universe_structures, либо
        # нет в corporation_structures, теперь добавляем отсутствующие данные в БД
        for structure_id in corp_structures_newA:
            self.actualize_universe_structure(structure_id)
        for structure_data in corp_structures_data:
            if structure_data["structure_id"] in corp_structures_newB:
                self.dbswagger.insert_corporation_structure(structure_data, corp_structures_updated_at)
        self.dbswagger.mark_corporation_structures_updated(corp_structures_ids, corp_structures_updated_at)
        self.qidb.commit()

        return corp_structures_data, len(corp_structures_new)

    # -------------------------------------------------------------------------
    # universe/stations/{station_id}/
    # universe/structures/{structure_id}/
    # -------------------------------------------------------------------------

    def actualize_station_or_structure(self, location_id, skip_corporation=False):
        owner_id = None
        if location_id >= 1000000000:
            structure_data = self.actualize_universe_structure(location_id)
            if structure_data:
                owner_id = structure_data['owner_id']
        else:
            station_data = self.actualize_universe_station(location_id)
            if station_data:
                owner_id = station_data['owner']
        if not skip_corporation and owner_id:
            self.actualize_corporation(owner_id)

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
