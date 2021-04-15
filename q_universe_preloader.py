﻿""" Q.Universe Structures (desktop/mobile)

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

>>> python eve_sde_tools.py --cache_dir=~/.q_industrialist
>>> python q_dictionaries.py --cache_dir=~/.q_industrialist
>>> python q_universe_preloader.py --pilot1="Qandra Si" --pilot2="Your Name" --online --cache_dir=~/.q_industrialist

Required application scopes:
    * esi-universe.read_structures.v1 - Requires: access token
    * esi-corporations.read_structures.v1 - Requires role(s): Station_Manager
    * esi-assets.read_corporation_assets.v1 - Requires role(s): Director
    * esi-corporations.read_blueprints.v1 - Requires role(s): Director
    * esi-industry.read_corporation_jobs.v1 - Requires role(s): Factory_Manager
    * esi-wallet.read_corporation_wallets.v1 - Requires one of: Accountant, Junior_Accountant
"""
import sys

import eve_db_tools
import console_app
# from memory_profiler import memory_usage


def main():
    # подключаемся к БД для сохранения данных, которые будут получены из ESI Swagger Interface
    dbtools = eve_db_tools.QDatabaseTools("universe_structures", debug=False)
    first_time = True

    # работа с параметрами командной строки, получение настроек запуска программы, как то: работа в offline-режиме,
    # имя пилота ранее зарегистрированного и для которого имеется аутентификационный токен, регистрация нового и т.д.
    argv_prms = console_app.get_argv_prms()

    for pilot_name in argv_prms["character_names"]:
        # настройка Eve Online ESI Swagger interface
        authz = dbtools.auth_pilot_by_name(
            pilot_name,
            argv_prms["offline_mode"],
            argv_prms["workspace_cache_files_dir"])
        character_id = authz["character_id"]
        character_name = authz["character_name"]

        # Public information about a character
        character_data = dbtools.actualize_character(character_id, True)
        # Public information about a corporation
        corporation_id = character_data["corporation_id"]
        corporation_data = dbtools.actualize_corporation(corporation_id, True)

        corporation_name = corporation_data["name"]
        print("\n{} is from '{}' corporation".format(character_name, corporation_name))
        sys.stdout.flush()

        # один раз для первого пилота (его аутентификационного токена) читаем данные
        # с серверов CCP по публичным структурам

        if first_time:
            first_time = False

            # Requires: access token
            universe_structures_data, universe_structures_new = dbtools.actualize_universe_structures()
            print("{} of {} new public structures found in the universe\n".
                  format(universe_structures_new, len(universe_structures_data)))
            sys.stdout.flush()

        # приступаем к загрузке корпоративных данных

        # Requires role(s): Station_Manager
        corp_structures_data, corp_structures_new = dbtools.actualize_corporation_structures(corporation_id)
        if not corp_structures_data:
            print("'{}' corporation has no any structures\n".format(corporation_name))
        else:
            print("'{}' corporation has {} of {} new structures\n".
                  format(corporation_name, corp_structures_new, len(corp_structures_data)))
        sys.stdout.flush()

        # Requires role(s): Director
        corp_assets_data = dbtools.actualize_corporation_assets(corporation_id)
        print("'{}' corporation has {} asset items\n".
              format(corporation_name, len(corp_assets_data)))
        sys.stdout.flush()

        # Requires role(s): Director
        corp_blueprints_data = dbtools.actualize_corporation_blueprints(corporation_id)
        print("'{}' corporation has {} blueprints\n".
              format(corporation_name, len(corp_blueprints_data)))
        sys.stdout.flush()

        # Requires role(s): Factory_Manager
        corp_industry_jobs_data = dbtools.actualize_corporation_industry_jobs(corporation_id)
        print("'{}' corporation has {} active industry jobs\n".
              format(corporation_name, len([j for j in corp_industry_jobs_data if j['status'] == 'active'])))
        sys.stdout.flush()

        # Requires role(s): Accountant, Junior_Accountant
        corp_made_new_payments = dbtools.actualize_corporation_wallet_journals(corporation_id)
        print("'{}' corporation made {} new payments\n".
              format(corporation_name, corp_made_new_payments))
        sys.stdout.flush()

        # Пытаемся отследить и сохраняем связи между чертежами и работами
        dbtools.link_blueprints_and_jobs(corporation_id)
        print("'{}' corporation link blueprints and jobs completed\n".
              format(corporation_name))

    del dbtools

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nDone")


if __name__ == "__main__":
    # mem = memory_usage(main, max_usage=True)
    # print("Memory used: {}Mb".format(mem))
    main()  # 121.4Mb
