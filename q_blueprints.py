""" Q.Blueprints (desktop/mobile)

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
>>> python q_blueprints.py

Required application scopes:
    * esi-assets.read_corporation_assets.v1 - Requires role(s): Director
    * esi-corporations.read_blueprints.v1 - Requires role(s): Director
    * esi-industry.read_corporation_jobs.v1 - Requires role(s): Factory_Manager
"""
import sys
import json
import requests

import eve_esi_interface as esi

import eve_esi_tools
import eve_sde_tools
import console_app
import q_industrialist_settings
from render_html import dump_blueprints_into_report

from __init__ import __version__


def __build_blueprints(
        corp_blueprints_data,
        corp_industry_jobs_data,
        eve_market_prices_data,
        sde_type_ids,
        sde_inv_names,
        sde_inv_items,
        corp_assets_tree,
        corp_ass_names_data,
        foreign_structures_data):
    blueprints = []
    blueprints_locations = {}
    for __blueprint_dict in corp_blueprints_data:
        # A range of numbers with a minimum of -2 and no maximum value where -1 is an original and -2 is a copy.
        # It can be a positive integer if it is a stack of blueprint originals fresh from the market (e.g. no
        # activities performed on them yet).
        __quantity = __blueprint_dict["quantity"]
        __is_blueprint_copy = __quantity == -2
        if __is_blueprint_copy:
            continue
        __blueprint_id = __blueprint_dict["item_id"]
        __type_id = __blueprint_dict["type_id"]
        __type_desc = sde_type_ids[str(__type_id)]
        __location_id = __blueprint_dict["location_id"]
        __blueprint = {
            "item_id": __blueprint_id,
            "type_id": __type_id,
            "name": __type_desc["name"]["en"],
            "me": __blueprint_dict["material_efficiency"],
            "te": __blueprint_dict["time_efficiency"],
            "q": 1 if __quantity == -1 else __quantity,
            "loc": __location_id,
            "flag": __blueprint_dict["location_flag"]
        }
        # если чертёж в единичном экземпляре, не stacked, смотрим что с ним происходит? (jobs?)
        if __quantity == -1:
            __job_dict = next((j for j in corp_industry_jobs_data if j['blueprint_id'] == int(__blueprint_id)), None)
            if not (__job_dict is None):
                __blueprint.update({
                    "st": __job_dict["status"],
                    "act": __job_dict["activity_id"]
                })
        # выясняем стоимость чертежа
        __price_dict = next((p for p in eve_market_prices_data if p['type_id'] == int(__type_id)), None)
        if not (__price_dict is None):
            if "average_price" in __price_dict:
                __blueprint.update({"average_price": __price_dict["average_price"]})
            elif "adjusted_price" in __price_dict:
                __blueprint.update({"adjusted_price": __price_dict["adjusted_price"]})
            elif "basePrice" in __type_desc:
                __blueprint.update({"base_price": __type_desc["basePrice"]})
        elif "basePrice" in __type_desc:
            __blueprint.update({"base_price": __type_desc["basePrice"]})
        # осуществляем поиск местоположения чертежа
        if not (str(__location_id) in blueprints_locations):
            __root_location_id = __prev_location_id = int(__location_id)
            __assets_roots = corp_assets_tree["roots"]
            while True:
                if __root_location_id in __assets_roots:
                    break
                if str(__root_location_id) in corp_assets_tree:
                    a = corp_assets_tree[str(__root_location_id)]
                    if "location_id" in a:
                        __prev_location_id = int(__root_location_id)
                        __root_location_id = int(a["location_id"])
                    else:
                        break
            # определяем регион и солнечную систему, где расположен чертёж
            region_id, region_name, loc_name, __dummy0 = eve_esi_tools.get_assets_location_name(
                int(__root_location_id),
                sde_inv_names,
                sde_inv_items,
                corp_ass_names_data,
                foreign_structures_data)
            if not (region_id is None):
                __loc_dict = {"region_id": region_id, "region": region_name, "solar": loc_name}
                if __prev_location_id != __root_location_id:
                    __dummy1, __dummy2, loc_name, foreign = eve_esi_tools.get_assets_location_name(
                        int(__prev_location_id),
                        sde_inv_names,
                        sde_inv_items,
                        corp_ass_names_data,
                        foreign_structures_data)
                    __loc_dict.update({"station": loc_name, "foreign": foreign})
                blueprints_locations.update({str(__location_id): __loc_dict})
        # добавляем собранную информацию в список чертежей
        blueprints.append(__blueprint)
    return blueprints, blueprints_locations


def main():
    # работа с параметрами командной строки, получение настроек запуска программы, как то: работа в offline-режиме,
    # имя пилота ранее зарегистрированного и для которого имеется аутентификационный токен, регистрация нового и т.д.
    argv_prms = console_app.get_argv_prms()

    sde_type_ids = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "typeIDs")
    sde_inv_names = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "invNames")
    sde_inv_items = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "invItems")

    corps_blueprints = {}
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
            offline_mode=argv_prms["offline_mode"])

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

        # Получение названий контейнеров, станций, и т.п. - всё что переименовывается ingame
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

        # Построение дерева ассетов, с узлави в роли станций и систем, и листьями в роли хранящихся
        # элементов, в виде:
        # { location1: {items:[item1,item2,...],type_id,location_id},
        #   location2: {items:[item3],type_id} }
        corp_assets_tree = eve_esi_tools.get_assets_tree(corp_assets_data, foreign_structures_data, sde_inv_items, virtual_hierarchy_by_corpsag=False)
        eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_assets_tree.{}".format(corporation_name), corp_assets_tree)

        # Построение дерева имущества (сводная информация, учитывающая объёмы и ориентировочную стоимость asset-ов)
        print("\nBuilding {} blueprints stat...".format(corporation_name))
        sys.stdout.flush()
        corp_blueprints, blueprints_locations = __build_blueprints(
            corp_blueprints_data,
            corp_industry_jobs_data,
            eve_market_prices_data,
            sde_type_ids,
            sde_inv_names,
            sde_inv_items,
            corp_assets_tree,
            corp_ass_names_data,
            foreign_structures_data)
        corp_blueprints.sort(key=lambda bp: bp["name"])

        corps_blueprints.update({str(corporation_id): {
            "corporation": corporation_name,
            "blueprints": corp_blueprints,
            "locations": blueprints_locations
        }})

    eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corps_blueprints", corps_blueprints)

    print("\nBuilding blueprints report...")
    sys.stdout.flush()

    dump_blueprints_into_report(
        # путь, где будет сохранён отчёт
        argv_prms["workspace_cache_files_dir"],
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corps_blueprints
    )

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nDone")


if __name__ == "__main__":
    main()
