""" Q.Accounting (desktop/mobile)

Prerequisites:
    * Have a Python 3 environment available to you (possibly by using a
      virtual environment: https://virtualenv.pypa.io/en/stable/).
    * Run pip install -r requirements.txt with this directory as your root.

    * Copy q_industrialist_settings.py.template into q_industrialist_settings.py and
      mood for your needs.
    * Create an SSO application at developers.eveonline.com with the scopes
      from g_client_scope list declared in q_industrialist_settings.py and the
      callback URL "https://localhost/callback/".
      Note: never use localhost as a callback in released applications.

To run this example, make sure you have completed the prerequisites and then
run the following command from this directory as the root:

>>> python q_shareholders.py --pilot1="Qandra Si" --pilot2="Your Name" --online --cache_dir=~/.q_industrialist

Required application scopes:
    * esi-assets.read_corporation_assets.v1 - Requires role(s): Director
    * esi-universe.read_structures.v1 - Requires: access token
    * esi-wallet.read_corporation_wallets.v1 - Requires one of: Accountant, Junior_Accountant
    * esi-industry.read_corporation_jobs.v1 - Requires role(s): Factory_Manager
    * esi-contracts.read_corporation_contracts.v1 - Requires: access token
"""
import json
import sys
import requests

import console_app
import eve_esi_interface as esi
import eve_esi_tools
import q_industrialist_settings
import render_html_shareholders

from __init__ import __version__


def main():
    # работа с параметрами командной строки, получение настроек запуска программы, как то: работа в offline-режиме,
    # имя пилота ранее зарегистрированного и для которого имеется аутентификационный токен, регистрация нового и т.д.
    argv_prms = console_app.get_argv_prms()

    various_characters_data = {}
    various_corporations_data = {}
    for pilot_name in argv_prms["character_names"]:
        # настройка Eve Online ESI Swagger interface
        auth = esi.EveESIAuth(
            '{}/auth_cache'.format(argv_prms["workspace_cache_files_dir"]),
            debug=True)
        client = esi.EveESIClient(
            auth,
            keep_alive=True,
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

        various_characters_data.update({str(character_id): character_data})
        various_corporations_data.update({str(corporation_id): corporation_data})

        for shareholder in corp_shareholders_data:
            # Получение сведений о пилотах, имеющих акции корпорации
            corp_id = None
            if shareholder['shareholder_type'] == 'character':
                pilot_id = shareholder['shareholder_id']
                if str(pilot_id) in various_characters_data:  # пилот м.б. быть в списке с dict=None
                    __pilot_dict = various_characters_data.get(str(pilot_id))
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
            if corp_id:
                if str(corp_id) not in various_corporations_data:
                    # Public information about a character
                    corp_data = interface.get_esi_data(
                        "corporations/{}/".format(corp_id),
                        fully_trust_cache=True)
                    various_corporations_data.update({str(corp_id): corp_data})
            sys.stdout.flush()

        shareholders_data = {
            "corporation": corporation_data,
            "shareholders": corp_shareholders_data,
            "characters": various_characters_data,
            "corporations": various_corporations_data,
        }
        eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_shareholders_data.{}".format(corporation_name), shareholders_data)

        # Построение дерева shareholders-ов:
        print("\nBuilding shareholders report...")
        sys.stdout.flush()
        render_html_shareholders.dump_shareholders_into_report(
            # путь, где будет сохранён отчёт
            argv_prms["workspace_cache_files_dir"],
            # данные, полученные в результате анализа и перекомпоновки входных списков
            shareholders_data)

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nDone")


if __name__ == "__main__":
    main()
