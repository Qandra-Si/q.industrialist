""" Q.Capital (desktop/mobile)

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

$ chcp 65001 & @rem on Windows only!
$ python eve_sde_tools.py --cache_dir=~/.q_industrialist
$ python q_capital.py --pilot="Qandra Si" --online --cache_dir=~/.q_industrialist

Requires application scopes:
    * esi-industry.read_corporation_jobs.v1 - Requires role(s): Factory_Manager
    * esi-assets.read_corporation_assets.v1 - Requires role(s): Director
    * esi-corporations.read_blueprints.v1 - Requires role(s): Director
"""
import sys
import json
import requests
import re

import eve_esi_interface as esi

import q_industrialist_settings
import q_capital_settings
import eve_esi_tools
import eve_sde_tools
import console_app
import render_html_capital_da8c005

from __init__ import __version__


def main():
    # работа с параметрами командной строки, получение настроек запуска программы, как то: работа в offline-режиме,
    # имя пилота ранее зарегистрированного и для которого имеется аутентификационный токен, регистрация нового и т.д.
    argv_prms = console_app.get_argv_prms()

    sde_type_ids = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "typeIDs")
    sde_inv_items = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "invItems")
    sde_market_groups = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "marketGroups")
    sde_bp_materials = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "blueprints")
    sde_icon_ids = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "iconIDs")

    # удаление из списка чертежей тех, которые не published (надо соединить typeIDs и blueprints, отбросив часть)
    for t in [t for t in sde_type_ids if t in sde_bp_materials.keys() and sde_type_ids[t].get('published')==False]:
        del sde_bp_materials[t]

    # настройка Eve Online ESI Swagger interface
    eve_market_prices_data = None
    total_assets_data = []
    total_blueprints_data = []
    total_industry_jobs_data = []
    total_ass_names_data = []
    for pilot_name in argv_prms["character_names"]:
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
            offline_mode=argv_prms["offline_mode"])

        authz = interface.authenticate(pilot_name)
        character_id = authz["character_id"]
        character_name = authz["character_name"]

        # Public information about a character
        character_data = interface.get_esi_data(
            "characters/{}/".format(character_id),
            fully_trust_cache=True)
        if not character_data:
            continue
        # Public information about a corporation
        corporation_data = interface.get_esi_data(
            "corporations/{}/".format(character_data["corporation_id"]),
            fully_trust_cache=True)

        corporation_id = character_data["corporation_id"]
        corporation_name = corporation_data["name"]
        print("\n{} is from '{}' corporation".format(character_name, corporation_name))
        sys.stdout.flush()

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

        # Requires role(s): Director
        corp_assets_data = interface.get_esi_paged_data(
            "corporations/{}/assets/".format(corporation_id))
        print("\n'{}' corporation has {} assets".format(corporation_name, len(corp_assets_data) if corp_assets_data else "no"))
        sys.stdout.flush()

        # Requires role(s): Director
        corp_blueprints_data = interface.get_esi_paged_data(
            "corporations/{}/blueprints/".format(corporation_id))
        print("\n'{}' corporation has {} blueprints".format(corporation_name, len(corp_blueprints_data) if corp_blueprints_data else "no"))
        sys.stdout.flush()

        # Requires role(s): Factory_Manager
        corp_industry_jobs_data = interface.get_esi_paged_data(
            "corporations/{}/industry/jobs/".format(corporation_id))
        print("\n'{}' corporation has {} industry jobs".format(corporation_name, len(corp_industry_jobs_data) if corp_industry_jobs_data else "no"))
        sys.stdout.flush()

        # Получение названий контейнеров, станций, и т.п. - всё что переименовывается ingame
        corp_ass_named_ids = eve_esi_tools.get_assets_named_ids(corp_assets_data)
        # Requires role(s): Director
        corp_ass_names_data = interface.get_esi_piece_data(
            "corporations/{}/assets/names/".format(corporation_id),
            corp_ass_named_ids)
        print("\n'{}' corporation has {} custom asset's names".format(corporation_name, len(corp_ass_names_data) if corp_ass_names_data else "no"))
        sys.stdout.flush()
        del corp_ass_named_ids

        if corp_assets_data:
            total_assets_data.extend(corp_assets_data)
        if corp_blueprints_data:
            total_blueprints_data.extend(corp_blueprints_data)
        if corp_industry_jobs_data:
            total_industry_jobs_data.extend(corp_industry_jobs_data)
        if corp_ass_names_data:
            total_ass_names_data.extend(corp_ass_names_data)

    # инициализируем корабли Ночного цеха
    q_capital_settings.init_night_factory_rest_ships(q_capital_settings.g_night_factory_rest_ships)

    # находим контейнеры по заданным названиям
    for ro in q_capital_settings.g_report_options:
        if "container_templates" in ro:
            for tmplt in ro["container_templates"]:
                containers = [n["item_id"] for n in total_ass_names_data if re.search(tmplt, n['name'])]
                for id in containers:
                    ro["blueprints"].append(
                        {"id": id, "name": next((n["name"] for n in total_ass_names_data if n['item_id'] == id), None)})
                    ro["stock"].append(
                        {"id": id, "name": next((n["name"] for n in total_ass_names_data if n['item_id'] == id), None)})

        # перечисляем станции и контейнеры, которые были найдены
        print('\nFound report containters and station ids for {}...'.format(ro["product"]))
        for bpl in ro["blueprints"]:
            print('  {} = {} (blueprints)'.format(bpl["id"], bpl.get("name", bpl.get("flag"))))
        for stk in ro["stock"]:
            print('  {} = {} (stock)'.format(stk["id"], stk.get("name", stk.get("flag"))))

        print("\nBuilding report...")
        sys.stdout.flush()

        render_html_capital_da8c005.dump_capital_into_report(
            # путь, где будет сохранён отчёт
            argv_prms["workspace_cache_files_dir"],
            # настройки генерации отчёта
            ro,
            # sde данные, загруженные из .converted_xxx.json файлов
            sde_type_ids,
            sde_bp_materials,
            sde_market_groups,
            sde_icon_ids,
            # esi данные, загруженные с серверов CCP
            total_assets_data,
            total_industry_jobs_data,
            total_blueprints_data,
            eve_market_prices_data)

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nDone")


if __name__ == "__main__":
    main()
