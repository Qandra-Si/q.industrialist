""" Q.Accounting (desktop/mobile)

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
>>> python q_accounting.py

Required application scopes:
    * esi-assets.read_corporation_assets.v1 - Requires role(s): Director
    * esi-universe.read_structures.v1 - Requires: access token
"""
import sys
import json
import requests

import eve_esi_interface as esi

import q_industrialist_settings
import eve_esi_tools
import eve_sde_tools
import console_app
from render_html import dump_accounting_into_report

from __init__ import __version__


def __build_accounting(
        sde_type_ids,
        sde_inv_names,
        sde_inv_items,
        sde_market_groups,
        corp_ass_names_data,
        foreign_structures_data,
        corp_assets_tree,
        corp_assets_data):
    if not ("roots" in corp_assets_tree):
        return None
    corp_accounting_stat = {}
    corp_accounting_tree = {}
    __roots = corp_assets_tree["roots"]
    for loc_id in __roots:
        region_id, region_name, loc_name, foreign = eve_esi_tools.get_assets_location_name(
            loc_id,
            sde_inv_names,
            sde_inv_items,
            corp_ass_names_data,
            foreign_structures_data)
        if not (region_id is None):
            if not (str(region_id) in corp_accounting_tree):
                corp_accounting_tree.update({str(region_id): {"region": region_name, "systems": {}, "flags": []}})
            __ca1 = corp_accounting_tree[str(region_id)]
            __ca1["systems"].update({str(loc_id): {"loc_name": loc_name, "foreign": foreign, "items": {}}})
            __ca2 = __ca1["systems"][str(loc_id)]
            for itm in corp_assets_tree[str(loc_id)]["items"]:
                __itm = str(itm)
                __ca2["items"].update({__itm: {"type_id": corp_assets_tree[__itm]["type_id"]}})
                __dummy1, __dummy2, loc_name, foreign = eve_esi_tools.get_assets_location_name(
                    itm,
                    sde_inv_names,
                    sde_inv_items,
                    corp_ass_names_data,
                    foreign_structures_data)
                __ca3 = __ca2["items"][__itm]
                __ca3.update({"loc_name": loc_name, "foreign": foreign, "flags": {}})
                for a in corp_assets_data:
                    if str(a["location_id"]) == __itm:
                        __location_flag = a["location_flag"]
                        __type_id = a["type_id"]
                        __group_id = eve_sde_tools.get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, __type_id)
                        if __group_id is None:
                            continue
                        if __ca1["flags"].count(__location_flag) == 0:
                            __ca1["flags"].append(__location_flag)
                        __ca4 = __ca3["flags"]
                        if not (__location_flag in __ca4):
                            __ca4.update({__location_flag: {}})
                        __ca5 = __ca4[__location_flag]
                        if not (str(__group_id) in __ca5):
                            __ca5.update({str(__group_id): {"group": sde_market_groups[str(__group_id)]["nameID"]["en"],
                                                            "volume": 0,
                                                            "cost": 0}})
                        if not (__location_flag in corp_accounting_stat):
                            corp_accounting_stat.update({__location_flag: {"volume": 0, "cost": 0}})
                        __cas1 = corp_accounting_stat[__location_flag]
                        __ca6 = __ca5[str(__group_id)]  # верим в лучшее, данные по маркету тут должны быть...
                        __type_dict = sde_type_ids[str(__type_id)]
                        if "basePrice" in __type_dict:
                            __sum = __type_dict["basePrice"] * a["quantity"]
                            __ca6["cost"] = __ca6["cost"] + __sum
                            __cas1["cost"] = __cas1["cost"] + __sum
                        if "volume" in __type_dict:
                            __sum = __type_dict["volume"] * a["quantity"]
                            __ca6["volume"] = __ca6["volume"] + __sum
                            __cas1["volume"] = __cas1["volume"] + __sum
        else:
            corp_accounting_tree.update({str(loc_id): {"loc_name": loc_name, "foreign": foreign}})
    return corp_accounting_stat, corp_accounting_tree


def main():
    # работа с параметрами командной строки, получение настроек запуска программы, как то: работа в offline-режиме,
    # имя пилота ранее зарегистрированного и для которого имеется аутентификационный токен, регистрация нового и т.д.
    argv_prms = console_app.get_argv_prms()

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

    authz = interface.authenticate(argv_prms["character_name"])
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

    sde_type_ids = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "typeIDs")
    sde_inv_names = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "invNames")
    sde_inv_items = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "invItems")
    sde_market_groups = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "marketGroups")

    # Requires role(s): Director
    corp_assets_data = interface.get_esi_paged_data(
        "corporations/{}/assets/".format(corporation_id))
    print("\n'{}' corporation has {} assets".format(corporation_name, len(corp_assets_data)))
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

    # # Public information with list of public structures
    # universe_structures_data = eve_esi_interface.get_esi_data(
    #     access_token,
    #     "universe/structures/")
    # print("\nFound {} public structures in universe".format(len(universe_structures_data)))
    # sys.stdout.flush()

    # Построение дерева ассетов, с узлави в роли станций и систем, и листьями в роли хранящихся
    # элементов, в виде:
    # { location1: {items:[item1,item2,...],type_id,location_id},
    #   location2: {items:[item3],type_id} }
    corp_assets_tree = eve_esi_tools.get_assets_tree(corp_assets_data, foreign_structures_data, sde_inv_items, virtual_hierarchy_by_corpsag=True)
    eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_assets_tree", corp_assets_tree)

    # Построение дерева имущества (сводная информация, учитывающая объёмы и ориентировочную стоимость asset-ов)
    corp_accounting_stat, corp_accounting_tree = __build_accounting(
        sde_type_ids,
        sde_inv_names,
        sde_inv_items,
        sde_market_groups,
        corp_ass_names_data,
        foreign_structures_data,
        corp_assets_tree,
        corp_assets_data)
    eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_accounting_stat", corp_accounting_stat)
    eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_accounting_tree", corp_accounting_tree)

    # Построение списка модулей и ресуров, которые имеются в распоряжении корпорации и
    # которые предназначены для использования в чертежах
    corp_ass_loc_data = eve_esi_tools.get_corp_ass_loc_data(corp_assets_data)
    eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_ass_loc_data", corp_ass_loc_data)

    # Построение дерева asset-ов:
    print("\nBuilding accounting report...")
    sys.stdout.flush()
    dump_accounting_into_report(
        # путь, где будет сохранён отчёт
        argv_prms["workspace_cache_files_dir"],
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_accounting_stat,
        corp_accounting_tree)

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nDone")


if __name__ == "__main__":
    main()
