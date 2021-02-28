"""
get_db_connection - подключается к БД
auth_pilot_by_name - подключается к ESI Swagger Interface
actualize_xxx - загружает с серверов CCP xxx-данные, например actualize_character,
                и сохраняет полученные данные в БД, если требуется
"""
import sys
import requests

import eve_esi_interface as esi
import postgresql_interface as db

import q_industrialist_settings

from __init__ import __version__


def get_db_connection(module_name, debug):
    qidb = db.QIndustrialistDatabase(module_name, debug=debug)
    qidb.connect(q_industrialist_settings.g_database)
    dbswagger = db.QSwaggerInterface(qidb)
    return qidb, dbswagger


def auth_pilot_by_name(pilot_name, offline_mode, cache_files_dir):
    # настройка Eve Online ESI Swagger interface
    auth = esi.EveESIAuth(
        '{}/auth_cache'.format(cache_files_dir),
        debug=True)
    client = esi.EveESIClient(
        auth,
        debug=False,
        logger=True,
        user_agent='Q.Industrialist v{ver}'.format(ver=__version__))
    interface = esi.EveOnlineInterface(
        client,
        q_industrialist_settings.g_client_scope,
        cache_dir='{}/esi_cache'.format(cache_files_dir),
        offline_mode=offline_mode)

    authz = interface.authenticate(pilot_name)
    # character_id = authz["character_id"]
    # character_name = authz["character_name"]
    return interface, authz


def actualize_character(interface, dbswagger, character_id):
    # Public information about a character
    character_data = interface.get_esi_data(
        "characters/{}/".format(character_id),
        fully_trust_cache=True)
    return character_data


def actualize_corporation(interface, dbswagger, corporation_id):
    # Public information about a corporation
    corporation_data = interface.get_esi_data(
        "corporations/{}/".format(corporation_id),
        fully_trust_cache=True)
    return corporation_data


def actualize_universe_structure(interface, dbswagger, structure_id):
    try:
        # Requires: access token
        universe_structure_data = interface.get_esi_data(
            "universe/structures/{}/".format(structure_id),
            fully_trust_cache=True)
        # сохраняем в БД данные о структуре
        dbswagger.insert_universe_structure(
            structure_id,
            universe_structure_data
        )
        return universe_structure_data
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


def actualize_universe_structures(interface, dbswagger):
    # Requires: access token
    universe_structures_data = interface.get_esi_paged_data('universe/structures/')
    universe_structures_new = dbswagger.get_absent_universe_structure_ids(universe_structures_data)
    universe_structures_new = [id[0] for id in universe_structures_new]

    # universe_structures_data = [1035620655696, 1035660997658, 1035620697572, ... ]
    # universe_structures_new = [1035620655696]

    for structure_id in universe_structures_new:
        actualize_universe_structure(interface, dbswagger, structure_id)
    dbswagger.mark_universe_structures_updated(universe_structures_data)

    return universe_structures_data, universe_structures_new


def actualize_corporation_structures(interface, dbswagger, corporation_id):
    # Requires role(s): Station_Manager
    corp_structures_data = interface.get_esi_paged_data(
        "corporations/{}/structures/".format(corporation_id))
    corp_structures_ids = [s["structure_id"] for s in corp_structures_data]
    if not corp_structures_ids:
        return corp_structures_data, []
    else:
        corp_structures_newA = dbswagger.get_absent_universe_structure_ids(corp_structures_ids)
        corp_structures_newA = [id[0] for id in corp_structures_newA]
        corp_structures_newB = dbswagger.get_absent_corporation_structure_ids(corp_structures_ids)
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
            actualize_universe_structure(interface, dbswagger, structure_id)
        for structure_data in corp_structures_data:
            if structure_data["structure_id"] in corp_structures_newB:
                dbswagger.insert_corporation_structure(structure_data)
        dbswagger.mark_corporation_structures_updated(corp_structures_ids)

        return corp_structures_data, corp_structures_new
