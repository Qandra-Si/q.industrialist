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

            # Requires: access token
            universe_structures_stat = dbtools.actualize_universe_structures()
            if universe_structures_stat is None:
                print("Universe public structures has no updates\n")
            else:
                print("{} new of {} public structures found in the universe\n".
                      format(universe_structures_stat[1], universe_structures_stat[0]))
            sys.stdout.flush()

            # Requires: public access
            markets_prices_updated = dbtools.actualize_markets_prices()
            print("Markets prices has {} updates\n".format('no' if markets_prices_updated is None else markets_prices_updated))
            sys.stdout.flush()

            # Requires: public access
            for region in q_industrialist_settings.g_market_hubs:
                found_market_orders = dbtools.actualize_trade_hubs_market_orders(region['region'], region['trade_hubs'])
                print("'{}' market orders has {} updates\n".format(region['region'], 'no' if found_market_orders is None else found_market_orders))
                sys.stdout.flush()

            # Requires: public access
            for structure in q_industrialist_settings.g_market_structures:
                if structure.get("corporation_name", None) is None:
                    found_market_orders = dbtools.actualize_markets_structures_prices(structure.get("structure_id"))
                    print("'{}' market orders has {} updates\n".format(structure.get("structure_id"), 'no' if found_market_orders is None else found_market_orders))
                    sys.stdout.flush()

        # Requires: public access
        for structure in q_industrialist_settings.g_market_structures:
            if structure.get("corporation_name") == corporation_name:
                found_market_orders = dbtools.actualize_markets_structures_prices(structure.get("structure_id"))
                print("'{}' market orders has {} updates\n".format(structure.get("structure_id"), 'no' if found_market_orders is None else found_market_orders))
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
        known_asset_items = dbtools.actualize_corporation_assets(corporation_id)
        print("'{}' corporation has {} asset items\n".
              format(corporation_name, 'no updates in' if known_asset_items is None else known_asset_items))
        sys.stdout.flush()

        # Requires role(s): Director
        known_blueprints = dbtools.actualize_corporation_blueprints(corporation_id)
        print("'{}' corporation has {} blueprints\n".
              format(corporation_name, 'no updates in' if known_blueprints is None else known_blueprints))
        sys.stdout.flush()

        # Requires role(s): Factory_Manager
        corp_industry_stat = dbtools.actualize_corporation_industry_jobs(corporation_id)
        if corp_industry_stat is None:
            print("'{}' corporation has no update in industry jobs\n".format(corporation_name))
        else:
            print("'{}' corporation has {} active of {} total industry jobs\n".
                  format(corporation_name, corp_industry_stat[1], corp_industry_stat[0]))
        sys.stdout.flush()

        # Requires role(s): Accountant, Junior_Accountant
        corp_made_new_payments = dbtools.actualize_corporation_wallet_journals(corporation_id)
        print("'{}' corporation made {} new payments\n".
              format(corporation_name, corp_made_new_payments))
        sys.stdout.flush()

        # Requires role(s): Accountant, Junior_Accountant
        corp_made_new_transactions = dbtools.actualize_corporation_wallet_transactions(corporation_id)
        print("'{}' corporation made {} new transactions\n".
              format(corporation_name, corp_made_new_transactions))
        sys.stdout.flush()

        # Requires role(s): Accountant, Trader
        corp_orders_stat = dbtools.actualize_corporation_orders(corporation_id)
        if corp_orders_stat is None:
            print("'{}' corporation has no update in orders\n".format(corporation_name))
        else:
            print("'{}' corporation has {} active and {} finished orders\n".
                  format(corporation_name, corp_orders_stat[0], corp_orders_stat[1]))
        sys.stdout.flush()

        # Пытаемся отследить и сохраняем связи между чертежами и работами
        dbtools.link_blueprints_and_jobs(corporation_id)
        print("'{}' corporation link blueprints and jobs completed\n".
              format(corporation_name))

    # Public information about type_id
    actualized_type_ids = dbtools.actualize_type_ids()
    if actualized_type_ids is None:
        print("No new items found in the University\n")
    else:
        print("{} new items found in the University and actualized:\n".format(len(actualized_type_ids)))
        for item in actualized_type_ids:
            print(" * {} with type_id={}\n".format(item['name'], item['type_id']))
    sys.stdout.flush()

    del dbtools

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nDone")


if __name__ == "__main__":
    # mem = memory_usage(main, max_usage=True)
    # print("Memory used: {}Mb".format(mem))
    main()  # 121.4Mb

