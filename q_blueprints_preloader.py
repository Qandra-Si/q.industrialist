""" Q.Individualist preloader (desktop/mobile)

Prerequisites:
    * Have a Python 3 environment available to you (possibly by using a
      virtual environment: https://virtualenv.pypa.io/en/stable/).
    * Run pip install -r requirements.txt --user with this directory.
      or
      Run pip install -r requirements.txt with this directory as your root.

    * Copy q_individualist_settings.py.template into q_individualist_settings.py and
      mood for your needs.
    * Create an SSO application at developers.eveonline.com with the scopes
      from g_client_scope list declared in q_individualist_settings.py and the
      callback URL "https://localhost/callback/".
      Note: never use localhost as a callback in released applications.

To run this example, make sure you have completed the prerequisites and then
run the following command from this directory as the root:

$ chcp 65001 & @rem on Windows only!
$ python eve_sde_tools.py --cache_dir=~/.q_individualist
$ python q_dictionaries.py --category=all --cache_dir=~/.q_individualist
$ python q_wallet_preloader.py --pilot="Qandra Si" --pilot="Your Name" --online --cache_dir=~/.q_individualist

Required application scopes:
    * esi-characters.read_blueprints.v1 - Requires: access token
"""
import sys

import eve_db_tools
import console_app
# from memory_profiler import memory_usage

import q_individualist_settings


def main():
    # подключаемся к БД для сохранения данных, которые будут получены из ESI Swagger Interface
    dbtools = eve_db_tools.QDatabaseTools(
        "blueprints_preloader",
        q_individualist_settings.g_client_scope,
        q_individualist_settings.g_database,
        debug=False
    )
    first_time = True

    # работа с параметрами командной строки, получение настроек запуска программы, как то: работа в offline-режиме,
    # имя пилота ранее зарегистрированного и для которого имеется аутентификационный токен, регистрация нового и т.д.
    argv_prms = console_app.get_argv_prms()

    for pilot_num, pilot_name in enumerate(argv_prms["character_names"]):
        # настройка Eve Online ESI Swagger interface
        authz = dbtools.auth_pilot_by_name(
            pilot_name,
            argv_prms["offline_mode"],
            argv_prms["workspace_cache_files_dir"],
            q_individualist_settings.g_client_id,  # токен приложения Q.Individualist
            q_individualist_settings.g_client_restrict_tls13
        )
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

        # приступаем к загрузке индивидуальных данных пилота

        # Requires: access token
        made_new_payments = dbtools.actualize_character_wallet_journals(character_id)
        print("'{}' made {} new payments\n".
              format(character_name, made_new_payments))
        sys.stdout.flush()

        # Requires: access token
        made_new_transactions = dbtools.actualize_character_wallet_transactions(character_id)
        print("'{}' made {} new transactions\n".
              format(character_name, made_new_transactions))
        sys.stdout.flush()

        ## Requires: access token
        #known_asset_items = dbtools.actualize_character_assets(character_id)
        #print("'{}' has {} asset items\n".
        #      format(character_name, 'no updates in' if known_asset_items is None else known_asset_items))
        #sys.stdout.flush()

        # Requires: access token
        known_blueprints = dbtools.actualize_character_blueprints(character_id)
        print("'{}' has {} blueprints\n".
              format(character_name, 'no updates in' if known_blueprints is None else known_blueprints))
        sys.stdout.flush()

        # Requires: access token
        industry_stat = dbtools.actualize_character_industry_jobs(character_id)
        if industry_stat is None:
            print("'{}' has no update in industry jobs\n".format(character_name))
        else:
            print("'{}' has {} active of {} total industry jobs\n".
                  format(character_name, industry_stat[1], industry_stat[0]))
        sys.stdout.flush()

    sys.stdout.flush()

    del dbtools

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nDone")


if __name__ == "__main__":
    # mem = memory_usage(main, max_usage=True)
    # print("Memory used: {}Mb".format(mem))
    main()  # 121.4Mb

