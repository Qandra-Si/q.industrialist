""" Q.Universe Markets Updater (desktop/mobile)

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
>>> python q_universe_preloader.py --pilot="Qandra Si" --online --cache_dir=~/.q_industrialist

Required application scopes:
    * esi-markets.structure_markets.v1 - Requires one of the following EVE corporation role(s): Accountant, Trader
"""
import sys

import eve_db_tools
import console_app
from memory_profiler import memory_usage

import q_industrialist_settings


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

            # Requires: public access
            #markets_prices_updated = dbtools.actualize_markets_prices()
            #print("Markets prices has {} updates\n".format('no' if markets_prices_updated is None else markets_prices_updated))
            #sys.stdout.flush()

            # Requires: public access
            if dbtools.is_market_regions_history_refreshed():
                for region in q_industrialist_settings.g_market_regions:
                    market_region_history_updates = dbtools.actualize_market_region_history(region)
                    print("Region '{}' has {} market history updates\n".
                          format(region, 'no' if market_region_history_updates is None else market_region_history_updates))
                    sys.stdout.flush()

    del dbtools

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nDone")


if __name__ == "__main__":
    mem = memory_usage(main, max_usage=True)
    print("Memory used: {}Mb".format(mem))
    #main()  # 75.4Mb, 0m2.712s
