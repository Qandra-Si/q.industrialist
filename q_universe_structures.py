""" Q.Universe Structures (desktop/mobile)

Prerequisites:
    * Have a Python 3 environment available to you (possibly by using a
      virtual environment: https://virtualenv.pypa.io/en/stable/).
    * Run pip install -r requirements.txt with this directory as your root.

    * Copy q_industrialist_settings.py.template into q_industrialist_settings.py and
      mood for your needs.
    * Copy q_blueprints_settings.py.template into q_blueprints_settings.py and
      mood for your needs.
    * Create an SSO application at developers.eveonline.com with the scopes
      from g_client_scope list declared in q_industrialist_settings.py and the
      callback URL "https://localhost/callback/".
      Note: never use localhost as a callback in released applications.

To run this example, make sure you have completed the prerequisites and then
run the following command from this directory as the root:

>>> python q_universe_structures.py --pilot1="Qandra Si" --pilot2="Your Name" --online --cache_dir=~/.q_industrialist

Required application scopes:
    * esi-universe.read_structures.v1 - Requires: access token
"""
import sys
import requests

import eve_esi_interface as esi
import postgresql_interface as db

import console_app
import q_industrialist_settings

from __init__ import __version__


def get_db_connection():
    qidb = db.QIndustrialistDatabase("universe_structures", debug=False)
    qidb.connect(q_industrialist_settings.g_database)
    return qidb


def actualize_universe_structure(interface, dbstructures, structure_id):
    try:
        # Requires: access token
        universe_structure_data = interface.get_esi_data(
            "universe/structures/{}/".format(structure_id),
            fully_trust_cache=True)
        # сохраняем в БД данные о структуре
        dbstructures.insert_universe_structure(
            structure_id,
            universe_structure_data
        )
    except requests.exceptions.HTTPError as err:
        status_code = err.response.status_code
        if status_code == 403:  # это нормально, что часть структур со временем могут оказаться Forbidden
            pass
        else:
            # print(sys.exc_info())
            raise
    except:
        print(sys.exc_info())
        raise


def main():
    qidb = None
    dbstructures = None
    first_time = True

    # работа с параметрами командной строки, получение настроек запуска программы, как то: работа в offline-режиме,
    # имя пилота ранее зарегистрированного и для которого имеется аутентификационный токен, регистрация нового и т.д.
    argv_prms = console_app.get_argv_prms()

    for pilot_name in argv_prms["character_names"]:
        # настройка Eve Online ESI Swagger interface
        auth = esi.EveESIAuth(
            '{}/auth_cache'.format(argv_prms["workspace_cache_files_dir"]),
            debug=True)
        client = esi.EveESIClient(
            auth,
            debug=False,
            logger=True,
            user_agent='Q.Industrialist v{ver}'.format(ver=__version__))
        interface = esi.EveOnlineInterface(
            client,
            q_industrialist_settings.g_client_scope,
            cache_dir='{}/esi_cache'.format(argv_prms["workspace_cache_files_dir"]),
            offline_mode=argv_prms["offline_mode"])

        authz = interface.authenticate(pilot_name)
        character_id = authz["character_id"]
        character_name = authz["character_name"]

        # Public information about a character
        character_data = interface.get_esi_data(
            "characters/{}/".format(character_id),
            fully_trust_cache=True)
        # Public information about a corporation
        corporation_data = interface.get_esi_data(
            "corporations/{}/".format(character_data["corporation_id"]),
            fully_trust_cache=True)

        corporation_id = character_data["corporation_id"]
        corporation_name = corporation_data["name"]
        print("\n{} is from '{}' corporation".format(character_name, corporation_name))
        sys.stdout.flush()

        # подключаемся к БД для сохранения данных о структурах
        if qidb is None:
            qidb = get_db_connection()
            dbstructures = db.QUniverseStructures(qidb)

        # один раз для первого пилота (его аутентификационного токена) читаем данные
        # с серверов ССР по публичным структурам

        if first_time:
            first_time = False

            # Requires: access token
            universe_structures_data = interface.get_esi_paged_data('universe/structures/')
            universe_structures_new = dbstructures.get_absent_structure_ids(universe_structures_data)
            print("{} of {} new public structures found in the universe\n".format(len(universe_structures_new), len(universe_structures_data)))
            sys.stdout.flush()

            for structure_id in universe_structures_new:
                actualize_universe_structure(interface, dbstructures, structure_id[0])
            sys.stdout.flush()

        # приступаем к загрузке корпоративных данных

        # Requires role(s): Station_Manager
        corp_structures_data = interface.get_esi_paged_data(
            "corporations/{}/structures/".format(corporation_id))
        corp_structures_ids = [s["structure_id"] for s in corp_structures_data]
        if not corp_structures_ids:
            print("'{}' corporation has no any structures\n".format(corporation_name))
            sys.stdout.flush()
        else:
            corp_structures_newA = dbstructures.get_absent_structure_ids(corp_structures_ids)
            corp_structures_newA = [id[0] for id in corp_structures_newA]
            corp_structures_newB = dbstructures.get_absent_corporation_structure_ids(corp_structures_ids)
            corp_structures_newB = [id[0] for id in corp_structures_newB]
            corp_structures_new = corp_structures_newA[:]
            corp_structures_new.extend(corp_structures_newB)
            corp_structures_new = list(dict.fromkeys(corp_structures_new))

            print("'{}' corporation has {} of {} new structures\n".format(corporation_name, len(corp_structures_new), len(corp_structures_ids)))
            sys.stdout.flush()

            # выше были найдены идентификаторы тех структур, которых нет либо в universe_structures, либо
            # нет в corporation_structures, теперь добавляем отсутствующие данные в БД
            for structure_id in corp_structures_newA:
                actualize_universe_structure(interface, dbstructures, structure_id)
            for structure_data in corp_structures_data:
                if structure_data["structure_id"] in corp_structures_newB:
                    dbstructures.insert_corporation_structure(structure_data)
            sys.stdout.flush()

    if not (qidb is None):
        qidb.commit()
        if not (dbstructures is None):
            del dbstructures
        del qidb

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nDone")


if __name__ == "__main__":
    main()
