""" Q.Preloader (desktop/mobile)

Prerequisites:
    * Have a Python 3 environment available to you (possibly by using a
      virtual environment: https://virtualenv.pypa.io/en/stable/).
    * Run pip install -r requirements.txt --user with this directory.
      or
      Run pip install -r requirements.txt with this directory as your root.

    * Copy q_industrialist_settings.py.template into q_industrialist_settings.py and
      mood for your needs.
    * Create an SSO application at developers.eveonline.com with the scopes
      from g_client_scope list declared in q_industrialist_settings.py and the
      callback URL "https://localhost/callback/".
      Note: never use localhost as a callback in released applications.

To run this example, make sure you have completed the prerequisites and then
run the following command from this directory as the root:

>>> python q_preloader.py --pilot="Qandra Si" --cache_dir=~/.q_industrialist

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
import q_market_analyzer_settings

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
    print("\nStarting preload commonly used data...\n")

    try:
        eve_market_prices_data = None
        various_characters_data = {}
        various_corporations_data = {}
        markets_analyzer_first_time = True
        for pilot_name in argv_prms["character_names"]:
            # настройка Eve Online ESI Swagger interface
            auth = esi.EveESIAuth(
                '{}/auth_cache'.format(argv_prms["workspace_cache_files_dir"]),
                debug=True)
            client = esi.EveESIClient(
                auth,
                keep_alive=True,
                debug=argv_prms["verbose_mode"],
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
                "characters/{}/".format(character_id),
                fully_trust_cache=True)
            # Public information about a corporation
            corporation_data = interface.get_esi_data(
                "corporations/{}/".format(character_data["corporation_id"]),
                fully_trust_cache=True)

            corporation_id = character_data["corporation_id"]
            corporation_name = corporation_data["name"]
            print("{} is from '{}' corporation\n".format(character_name, corporation_name))
            sys.stdout.flush()

            various_characters_data.update({str(character_id): character_data})
            various_corporations_data.update({str(corporation_id): corporation_data})

            if eve_market_prices_data is None:
                try:
                    # Public information about market prices
                    eve_market_prices_data = interface.get_esi_paged_data("markets/prices/")
                    print("\nEVE market has {} prices".format(len(eve_market_prices_data) if not (eve_market_prices_data is None) else 0))
                    sys.stdout.flush()
                except requests.exceptions.HTTPError as err:
                    status_code = err.response.status_code
                    if status_code == 404:  # 2020.12.03 поломался доступ к ценам маркета (ССР-шники "внесли правки")
                        eve_market_prices_data = []
                    else:
                        raise
                except:
                    print(sys.exc_info())
                    raise

            try:
                # Requires role(s): Accountant, Junior_Accountant
                corp_wallets_data = interface.get_esi_paged_data(
                    "corporations/{}/wallets/".format(corporation_id))
                print("'{}' corporation has {} wallet divisions\n".format(corporation_name, len(corp_wallets_data)))
                sys.stdout.flush()
            except requests.exceptions.HTTPError as err:
                status_code = err.response.status_code
                if status_code == 500:  # 2021.01.28 поломался доступ к кошелькам, Internal Server Error
                    corp_wallets_data = []
                else:
                    raise
            except:
                print(sys.exc_info())
                raise

            # Requires role(s): Accountant, Junior_Accountant
            corp_wallet_journal_data = [None, None, None, None, None, None, None]
            for w in corp_wallets_data:
                division = w["division"]
                try:
                    corp_wallet_journal_data[division-1] = interface.get_esi_paged_data(
                        "corporations/{}/wallets/{}/journal/".format(corporation_id, division))
                    print("'{}' corporation has {} wallet#{} transactions\n".format(corporation_name, len(corp_wallet_journal_data[division-1]), division))
                    sys.stdout.flush()
                except requests.exceptions.HTTPError as err:
                    status_code = err.response.status_code
                    if status_code == 404:  # 2020.11.26 поломался доступ к журналу кошелька (ССР-шники "внесли правки")
                        corp_wallet_journal_data[division-1] = None
                    elif status_code == 500:  # 2021.01.28 поломался доступ к кошелькам, Internal Server Error
                        corp_wallet_journal_data[division-1] = None
                    else:
                        raise
                except:
                    print(sys.exc_info())
                    raise

            # Requires one of the following EVE corporation role(s): Director
            corp_divisions_data = interface.get_esi_data(
                "corporations/{}/divisions/".format(corporation_id),
                fully_trust_cache=True)
            print("'{}' corporation has {} hangar and {} wallet names\n".format(corporation_name, len(corp_divisions_data["hangar"]) if "hangar" in corp_divisions_data else 0, len(corp_divisions_data["wallet"]) if "wallet" in corp_divisions_data else 0))
            sys.stdout.flush()

            try:
                # Requires role(s): Director
                corp_shareholders_data = interface.get_esi_paged_data(
                    "corporations/{}/shareholders/".format(corporation_id))
                print("'{}' corporation has {} shareholders\n".format(corporation_name, len(corp_shareholders_data)))
                sys.stdout.flush()
            except requests.exceptions.HTTPError as err:
                status_code = err.response.status_code
                if status_code == 500:  # 2021.01.28 поломался доступ к кошелькам, Internal Server Error
                    corp_shareholders_data = []
                else:
                    raise
            except:
                print(sys.exc_info())
                raise

            for shareholder in corp_shareholders_data:
                # Получение сведений о пилотах, имеющих акции корпорации
                corp_id = None
                if shareholder['shareholder_type'] == 'character':
                    pilot_id = shareholder['shareholder_id']
                    if str(pilot_id) in various_characters_data:  # пилот м.б. быть в списке с dict=None
                        __pilot_dict = various_characters_data[str(pilot_id)]
                        if __pilot_dict:
                            corp_id = __pilot_dict.get("corporation_id")
                    else:
                        try:
                            # Public information about a character
                            pilot_data = interface.get_esi_data(
                                "characters/{}/".format(pilot_id),
                                fully_trust_cache=True)
                            corp_id = pilot_data["corporation_id"]
                            various_characters_data.update({str(pilot_id): pilot_data})
                        except requests.exceptions.HTTPError as err:
                            status_code = err.response.status_code
                            if status_code == 404:  # 404 Client Error: Not Found ('Character has been deleted!')
                                various_characters_data.update({str(pilot_id): None})
                            else:
                                print(sys.exc_info())
                                raise
                        except:
                            print(sys.exc_info())
                            raise
                        sys.stdout.flush()
                elif shareholder['shareholder_type'] == 'corporation':
                    corp_id = shareholder['shareholder_id']
                # Получение сведений о корпорациях, которым принадлежат акции, либо в которых состоят пилоты
                if corp_id and (str(corp_id) not in various_corporations_data):
                    # Public information about a corporation
                    corp_data = interface.get_esi_data(
                        "corporations/{}/".format(corp_id),
                        fully_trust_cache=True)
                    various_corporations_data.update({str(corp_id): corp_data})
                sys.stdout.flush()

            # Requires role(s): Director
            corp_assets_data = interface.get_esi_paged_data(
                "corporations/{}/assets/".format(corporation_id))
            print("'{}' corporation has {} assets\n".format(corporation_name, len(corp_assets_data)))
            sys.stdout.flush()

            # Requires role(s): Director
            corp_blueprints_data = interface.get_esi_paged_data(
                "corporations/{}/blueprints/".format(corporation_id))
            print("'{}' corporation has {} blueprints\n".format(corporation_name, len(corp_blueprints_data)))
            sys.stdout.flush()

            # Requires role(s): Factory_Manager
            corp_industry_jobs_data = interface.get_esi_paged_data(
                "corporations/{}/industry/jobs/".format(corporation_id))
            print("'{}' corporation has {} industry jobs\n".format(corporation_name, len(corp_industry_jobs_data)))
            sys.stdout.flush()

            # # Requires role(s): Station_Manager
            # corp_structures_data = interface.get_esi_paged_data(
            #     "corporations/{}/structures/".format(corporation_id))
            # print("'{}' corporation has {} structures\n".format(corporation_name, len(corp_structures_data)))
            # sys.stdout.flush()

            # # Requires role(s): Director
            # corp_starbases_data = interface.get_esi_paged_data(
            #     "corporations/{}/starbases/".format(corporation_id))
            # print("'{}' corporation has {} starbases\n".format(corporation_name, len(corp_starbases_data)))
            # sys.stdout.flush()

            # # Requires role(s): Factory_Manager
            # corp_facilities_data = interface.get_esi_paged_data(
            #     "corporations/{}/facilities/".format(corporation_id))
            # print("'{}' corporation has {} facilities\n".format(corporation_name, len(corp_facilities_data)))
            # sys.stdout.flush()

            # # Requires role(s): Director
            # corp_customs_offices_data = interface.get_esi_paged_data(
            #     "corporations/{}/customs_offices/".format(corporation_id))
            # print("'{}' corporation has {} customs offices\n".format(corporation_name, len(corp_customs_offices_data)))
            # sys.stdout.flush()

            # Получение названий контейнеров, станций, и т.п. - всё что переименовывается ingame
            corp_ass_named_ids = eve_esi_tools.get_assets_named_ids(corp_assets_data)
            # Requires role(s): Director
            corp_ass_names_data = interface.get_esi_piece_data(
                "corporations/{}/assets/names/".format(corporation_id),
                corp_ass_named_ids)
            print("\n'{}' corporation has {} custom asset's names".format(corporation_name, len(corp_ass_names_data)))
            sys.stdout.flush()
            del corp_ass_named_ids

            # Поиск тех станций, которые не принадлежат корпорации (на них имеется офис, но самой станции в ассетах нет)
            foreign_structures_data = {}
            foreign_structures_ids = eve_esi_tools.get_foreign_structures_ids(corp_assets_data)
            foreign_structures_forbidden_ids = []
            if len(foreign_structures_ids) > 0:
                # Requires: access token
                for structure_id in foreign_structures_ids:
                    try:
                        universe_structure_data = interface.get_esi_data(
                            "universe/structures/{}/".format(structure_id),
                            fully_trust_cache=True)
                        foreign_structures_data.update({str(structure_id): universe_structure_data})
                    except requests.exceptions.HTTPError as err:
                        status_code = err.response.status_code
                        if status_code == 403:  # это нормально, что часть структур со временем могут оказаться Forbidden
                            foreign_structures_forbidden_ids.append(structure_id)
                        else:
                            # print(sys.exc_info())
                            raise
                    except:
                        print(sys.exc_info())
                        raise
            print("'{}' corporation has offices in {} foreign stations\n".format(corporation_name, len(foreign_structures_data)))
            if len(foreign_structures_forbidden_ids) > 0:
                print("'{}' corporation has offices in {} forbidden stations : {}\n".format(corporation_name, len(foreign_structures_forbidden_ids), foreign_structures_forbidden_ids))
            sys.stdout.flush()

            # Requires role(s): access token
            corp_contracts_data = interface.get_esi_paged_data(
                "corporations/{}/contracts/".format(corporation_id))
            print("'{}' corporation has {} contracts\n".format(corporation_name, len(corp_contracts_data)))
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
                    if c["type"] != "item_exchange":
                        continue
                    # пропускаем контракты на продажу, которые выставили не мы
                    # эту настройку лучше не трогать, т.к. во FRT например 12'000 контрактов, следовательно
                    # это повлечёт загрузку 12'000 items и 12'000 issuers
                    if c['issuer_corporation_id'] != corporation_id:
                        continue
                    contract_id = c["contract_id"]
                    try:
                        __contract_items = interface.get_esi_data(
                            "corporations/{}/contracts/{}/items/".format(corporation_id, contract_id),
                            fully_trust_cache=True)
                        corp_contract_items_len += len(__contract_items)
                        corp_contract_items_data.append({str(contract_id): __contract_items})
                    except requests.exceptions.HTTPError as err:
                        status_code = err.response.status_code
                        if status_code == 404:  # это нормально, что часть доп.инфы по контрактам может быть не найдена!
                            corp_contract_items_not_found.append(contract_id)
                        else:
                            # print(sys.exc_info())
                            raise
                    except:
                        print(sys.exc_info())
                        raise
                    # Получение сведений о пилотах, вовлечённых в работу с контрактом
                    issuer_id = c["issuer_id"]
                    if str(issuer_id) not in various_characters_data:
                        try:
                            # Public information about a character
                            issuer_data = interface.get_esi_data(
                                "characters/{}/".format(issuer_id),
                                fully_trust_cache=True)
                            various_characters_data.update({str(issuer_id): issuer_data})
                        except requests.exceptions.HTTPError as err:
                            status_code = err.response.status_code
                            if status_code == 404:  # 404 Client Error: Not Found ('Character has been deleted!')
                                various_characters_data.update({str(issuer_id): None})
                            else:
                                print(sys.exc_info())
                                raise
                        except:
                            print(sys.exc_info())
                            raise
                    sys.stdout.flush()
            eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_contract_items_data.{}".format(corporation_name), corp_contract_items_data)

            print("'{}' corporation has {} items in contracts\n".format(corporation_name, corp_contract_items_len))
            if len(corp_contract_items_not_found) > 0:
                print("'{}' corporation has {} contracts without details : {}\n".format(corporation_name, len(corp_contract_items_not_found), corp_contract_items_not_found))
            sys.stdout.flush()

            # Requires: public access
            # НЕЛЬЗЯ СЮДА ДОБАВЛЯТЬ РЕГИОНЫ БЕЗ СОГЛАСОВАНИЯ С ССР, ИНАЧЕ БУДЕТ БАН: You have been banned from using ESI. Please contact Technical Support. (support@eveonline.com)
            #if markets_analyzer_first_time:
            #    markets_analyzer_first_time = False
            #    sde_inv_names = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "invNames")
            #    market_regions = [(int(id), sde_inv_names[id]) for id in sde_inv_names if
            #                      sde_inv_names[id] in q_market_analyzer_settings.g_regions]
            #    del sde_inv_names
            #    try:
            #        # Public information about market prices
            #        for (region_id, region_name) in market_regions:
            #            markets_region_orders = interface.get_esi_paged_data(
            #                "markets/{}/orders/".format(region_id))
            #            print("\n{} market has {} orders".format(
            #                region_name, len(markets_region_orders) if markets_region_orders else 0))
            #            sys.stdout.flush()
            #            del markets_region_orders
            #    except requests.exceptions.HTTPError as err:
            #        status_code = err.response.status_code
            #        if status_code == 404:  # 2020.12.03 поломался доступ к ценам маркета (ССР-шники "внесли правки")
            #            pass
            #        else:
            #            raise
            #    except:
            #        print(sys.exc_info())
            #        raise
            #    del market_regions

        eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "various_characters_data", various_characters_data)

        # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
        print("\nDone\n")
    except:
        print(sys.exc_info())
        sys.exit(1)  # errno.h : EPERM=1 /* Operation not permitted */
    sys.exit(0)  # code 0, all ok


if __name__ == "__main__":
    main()
