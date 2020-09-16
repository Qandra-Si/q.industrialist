""" Q.Preloader (desktop/mobile)

Prerequisites:
    * Create an SSO application at developers.eveonline.com with the scope
      "esi-characters.read_blueprints.v1" and the callback URL
      "https://localhost/callback/". Note: never use localhost as a callback
      in released applications.
    * Have a Python 3 environment available to you (possibly by using a
      virtual environment: https://virtualenv.pypa.io/en/stable/).
    * Run pip install -r requirements.txt with this directory as your root.
    * Copy q_industrialist_settings.py.template into q_industrialist_settings.py and
      mood for your needs.

To run this example, make sure you have completed the prerequisites and then
run the following command from this directory as the root:

>>> python eve_sde_tools.py
>>> python q_preloader.py

Required application scopes:
    * esi-assets.read_corporation_assets.v1 - Requires role(s): Director
    * esi-corporations.read_blueprints.v1 - Requires role(s): Director
    * esi-industry.read_corporation_jobs.v1 - Requires role(s): Factory_Manager
    * esi-contracts.read_corporation_contracts.v1 - Requires: access token
    * esi-wallet.read_corporation_wallets.v1 - Requires one of: Accountant, Junior_Accountant
    * esi-corporations.read_structures.v1 - Requires role(s): Station_Manager
    * esi-corporations.read_starbases.v1 - Requires role(s): Director
    * esi-corporations.read_facilities.v1 - Requires role(s): Factory_Manager
    * esi-planets.read_customs_offices.v1 - Requires role(s): Director
"""
import sys
import json
import requests

import eve_esi_interface as esi

import eve_esi_tools
import eve_sde_tools
import console_app
import q_industrialist_settings

from __init__ import __version__


def main():
    try:
        # работа с параметрами командной строки, получение настроек запуска программы, как то: имена пилотов ранее
        # зарегистрированных и для которыйх имеется аутентификационные токены, регистрация нового и т.д.
        # настройка offline_mode игнорируется, скрипт всегда работает в --online режиме
        argv_prms = console_app.get_argv_prms()
    except:
        sys.exit(22)  # Unit errno.h : EINVAL=22 /* Invalid argument */

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nStarting preload commonly used data...")

    try:
        eve_market_prices_data = None
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
                offline_mode=False)  # здесь обычно находится параметр argv_prms["offline_mode"]

            authz = interface.authenticate(pilot_name)
            character_id = authz["character_id"]
            character_name = authz["character_name"]

            # Public information about a character
            character_data = interface.get_esi_data(
                "characters/{}/".format(character_id))
            # Public information about a corporation
            corporation_data = interface.get_esi_data(
                "corporations/{}/".format(character_data["corporation_id"]))

            corporation_id = character_data["corporation_id"]
            corporation_name = corporation_data["name"]
            print("\n{} is from '{}' corporation".format(character_name, corporation_name))
            sys.stdout.flush()

            if eve_market_prices_data is None:
                # Public information about market prices
                eve_market_prices_data = interface.get_esi_data("markets/prices/")
                print("\nEVE market has {} prices".format(len(eve_market_prices_data)))
                sys.stdout.flush()

            # Requires role(s): Director
            corp_wallets_data = interface.get_esi_paged_data(
                "corporations/{}/wallets/".format(corporation_id))
            print("\n'{}' corporation has {} wallet divisions".format(corporation_name, len(corp_wallets_data)))
            sys.stdout.flush()

            # Requires role(s): Director
            corp_assets_data = interface.get_esi_paged_data(
                "corporations/{}/assets/".format(corporation_id))
            print("\n'{}' corporation has {} assets".format(corporation_name, len(corp_assets_data)))
            sys.stdout.flush()

            # Requires role(s): Director
            corp_blueprints_data = interface.get_esi_paged_data(
                "corporations/{}/blueprints/".format(corporation_id))
            print("\n'{}' corporation has {} blueprints".format(corporation_name, len(corp_blueprints_data)))
            sys.stdout.flush()

            # Requires role(s): Factory_Manager
            corp_industry_jobs_data = interface.get_esi_paged_data(
                "corporations/{}/industry/jobs/".format(corporation_id))
            print("\n'{}' corporation has {} industry jobs".format(corporation_name, len(corp_industry_jobs_data)))
            sys.stdout.flush()

            # Requires role(s): Station_Manager
            corp_structures_data = interface.get_esi_paged_data(
                "corporations/{}/structures/".format(corporation_id))
            print("\n'{}' corporation has {} structures".format(corporation_name, len(corp_structures_data)))
            sys.stdout.flush()

            # Requires role(s): Director
            corp_starbases_data = interface.get_esi_paged_data(
                "corporations/{}/starbases/".format(corporation_id))
            print("\n'{}' corporation has {} starbases".format(corporation_name, len(corp_starbases_data)))
            sys.stdout.flush()

            # Requires role(s): Factory_Manager
            corp_facilities_data = interface.get_esi_paged_data(
                "corporations/{}/facilities/".format(corporation_id))
            print("\n'{}' corporation has {} facilities".format(corporation_name, len(corp_facilities_data)))
            sys.stdout.flush()

            # Requires role(s): Director
            corp_customs_offices_data = interface.get_esi_paged_data(
                "corporations/{}/customs_offices/".format(corporation_id))
            print("\n'{}' corporation has {} customs offices".format(corporation_name, len(corp_customs_offices_data)))
            sys.stdout.flush()

            # Получение названий контейнеров, станций, кошельков, и т.п. - всё что переименовывается ingame
            corp_ass_names_data = []
            corp_ass_named_ids = eve_esi_tools.get_assets_named_ids(corp_assets_data)
            if len(corp_ass_named_ids) > 0:
                # Requires role(s): Director
                corp_ass_names_data = interface.get_esi_data(
                    "corporations/{}/assets/names/".format(corporation_id),
                    json.dumps(corp_ass_named_ids, indent=0, sort_keys=False))
            print("\n'{}' corporation has {} custom asset's names".format(corporation_name, len(corp_ass_names_data)))
            sys.stdout.flush()

            # Поиск тех станций, которые не принадлежат корпорации (на них имеется офис, но самой станции в ассетах нет)
            foreign_structures_data = {}
            foreign_structures_ids = eve_esi_tools.get_foreign_structures_ids(corp_assets_data)
            foreign_structures_forbidden_ids = []
            if len(foreign_structures_ids) > 0:
                # Requires: access token
                for structure_id in foreign_structures_ids:
                    try:
                        universe_structure_data = interface.get_esi_data(
                            "universe/structures/{}/".format(structure_id))
                        foreign_structures_data.update({str(structure_id): universe_structure_data})
                    except requests.exceptions.HTTPError as err:
                        status_code = err.response.status_code
                        if status_code == 403:  # это нормально, что часть структур со временем могут оказаться Forbidden
                            foreign_structures_forbidden_ids.append(structure_id)
                        else:
                            raise
                    except:
                        print(sys.exc_info())
                        raise
            print("\n'{}' corporation has offices in {} foreign stations".format(corporation_name, len(foreign_structures_data)))
            if len(foreign_structures_forbidden_ids) > 0:
                print("\n'{}' corporation has offices in {} forbidden stations : {}".format(corporation_name, len(foreign_structures_forbidden_ids), foreign_structures_forbidden_ids))
            sys.stdout.flush()

            # Requires role(s): access token
            corp_contracts_data = interface.get_esi_paged_data(
                "corporations/{}/contracts/".format(corporation_id))
            print("\n'{}' corporation has {} contracts".format(corporation_name, len(corp_contracts_data)))
            sys.stdout.flush()

            # Получение подробной информации о каждому из контракту в списке
            corp_contract_items_data = []
            corp_contract_items_len = 0
            corp_contract_items_not_found = []
            if len(corp_contracts_data) > 0:
                # Requires: access token
                for c in corp_contracts_data:
                    # для удалённых контрактов нельзя загрузить items (см. ниже 404-ошибку), поэтому пропускаем запись
                    if c["status"] == "deleted":
                        continue
                    # в рамках работы с чертежами, нас интересует только набор контрактов, в которых продаются чертежи
                    # ищем публичные контракты типа "обмен предметами"
                    if (c["availability"] != "public") or (c["type"] != "item_exchange"):
                        continue
                    contract_id = c["contract_id"]
                    try:
                        __contract_items = interface.get_esi_data(
                            "corporations/{}/contracts/{}/items/".format(corporation_id, contract_id))
                        corp_contract_items_len += len(__contract_items)
                        corp_contract_items_data.append({str(contract_id): __contract_items})
                    except requests.exceptions.HTTPError as err:
                        status_code = err.response.status_code
                        if status_code == 404:  # это нормально, что часть доп.инфы по контрактам может быть не найдена!
                            corp_contract_items_not_found.append(contract_id)
                        else:
                            raise
                    except:
                        print(sys.exc_info())
                        raise
            eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_contract_items_data.{}".format(corporation_name), corp_contract_items_data)

            print("\n'{}' corporation has {} items in contracts".format(corporation_name, corp_contract_items_len))
            if len(corp_contract_items_not_found) > 0:
                print("\n'{}' corporation has {} contracts without details : {}".format(corporation_name, len(corp_contract_items_not_found), corp_contract_items_not_found))
            sys.stdout.flush()

        # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
        print("\nDone")
    except:
        sys.exit(1)  # errno.h : EPERM=1 /* Operation not permitted */
    sys.exit(0)  # code 0, all ok


if __name__ == "__main__":
    main()
