"""
get_db_connection - подключается к БД
auth_pilot_by_name - подключается к ESI Swagger Interface
actualize_xxx - загружает с серверов CCP xxx-данные, например actualize_character,
                и сохраняет полученные данные в БД, если требуется
"""
import sys
import requests
import typing

import eve_esi_interface as esi
import postgresql_interface as db

import q_industrialist_settings

from __init__ import __version__


class QDatabaseTools:
    def __init__(self, module_name, debug):
        """ constructor

        :param module_name: name of Q.Industrialist' module
        :param debug: debug mode to show SQL queries
        """
        self.qidb = db.QIndustrialistDatabase(module_name, debug=debug)
        self.qidb.connect(q_industrialist_settings.g_database)

        self.dbswagger = db.QSwaggerInterface(self.qidb)

        self.esiswagger = None

        self.__cached_characters: typing.Dict[int, typing.Any] = {}
        self.__cached_corporations: typing.Dict[int, typing.Any] = {}
        self.__cached_stations: typing.Dict[int, typing.Any] = {}
        self.__cached_structures: typing.Dict[int, typing.Any] = {}

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
    # characters/{character_id}/
    # -------------------------------------------------------------------------

    def actualize_character(self, character_id):
        if not (character_id in self.__cached_characters):
            # Public information about a character
            character_data = self.esiswagger.get_esi_data(
                "characters/{}/".format(character_id),
                fully_trust_cache=True)
            # сохраняем данные в БД
            self.dbswagger.insert_character(
                character_id,
                character_data,
                self.esiswagger.last_modified
            )
            # сохраняем данные в кеше
            self.__cached_characters[character_id] = character_data
            return character_data
        else:
            return self.__cached_characters.get(character_id)

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/
    # -------------------------------------------------------------------------

    def actualize_corporation(self, corporation_id):
        if not (corporation_id in self.__cached_corporations):
            # Public information about a corporation
            corporation_data = self.esiswagger.get_esi_data(
                "corporations/{}/".format(corporation_id),
                fully_trust_cache=True)
            # сохраняем данные в БД
            self.dbswagger.insert_corporation(
                corporation_id,
                corporation_data,
                self.esiswagger.last_modified
            )
            # сохраняем сопутствующие данные в БД
            self.actualize_character(corporation_data['ceo_id'])
            if corporation_data['creator_id'] != 1:  # EVE System
                self.actualize_character(corporation_data['creator_id'])
            if 'home_station_id' in corporation_data:
                self.actualize_station_or_structure(
                    corporation_data['home_station_id'],
                    skip_corporation=True
                )
            # сохраняем данные в кеше
            self.__cached_stations[corporation_id] = corporation_data
            return corporation_data
        else:
            return self.__cached_corporations.get(corporation_id)

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
