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
import json
import sys

import requests

import console_app
import eve_esi_interface as esi
import eve_esi_tools
import eve_sde_tools
import q_industrialist_settings
from __init__ import __version__
from render_html import dump_accounting_into_report


def __build_accounting_append(
        __type_id,
        __quantity,
        __group_id,
        __group_name,
        sde_type_ids,
        __cas1_stat_flag,
        __ca5_station_flag):
    if not (str(__group_id) in __ca5_station_flag):
        __ca5_station_flag.update({str(__group_id): {"group": __group_name, "volume": 0, "cost": 0}})
    __ca6_group = __ca5_station_flag[str(__group_id)]  # верим в лучшее, данные по маркету тут должны быть...
    __type_dict = sde_type_ids[str(__type_id)]
    if "basePrice" in __type_dict:
        __sum = __type_dict["basePrice"] * __quantity
        __ca6_group["cost"] += __sum
        __cas1_stat_flag["cost"] += __sum
    if "volume" in __type_dict:
        __sum = __type_dict["volume"] * __quantity
        __ca6_group["volume"] += __sum
        __cas1_stat_flag["volume"] += __sum


def __build_accounting_nested(
        itm_id,
        sde_type_ids,
        sde_market_groups,
        corp_assets_tree,
        corp_assets_data,
        __cas1_stat_flag,
        __ca5_station_flag):
    __item_dict = next((a for a in corp_assets_data if a['item_id'] == int(itm_id)), None)
    if not (__item_dict is None):
        __type_id = int(__item_dict["type_id"])
        __quantity = int(__item_dict["quantity"])
        # __location_flag = __item_dict["location_flag"]
        __group_id = eve_sde_tools.get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, __type_id)
        if not (__group_id is None):
            __build_accounting_append(
                __type_id,
                __quantity,
                __group_id,
                sde_market_groups[str(__group_id)]["nameID"]["en"],
                sde_type_ids,
                __cas1_stat_flag,
                __ca5_station_flag)
    if str(itm_id) in corp_assets_tree:
        __cat1 = corp_assets_tree[str(itm_id)]
        if "items" in __cat1:
            for __itm_id in __cat1["items"]:
                __build_accounting_nested(
                    __itm_id,
                    sde_type_ids,
                    sde_market_groups,
                    corp_assets_tree,
                    corp_assets_data,
                    __cas1_stat_flag,
                    __ca5_station_flag)
    return


def __build_accounting_register_flag(
        __location_flag,
        __ca1_region,
        __ca3_station,
        corp_accounting_stat):
    if __ca1_region["flags"].count(__location_flag) == 0:
        __ca1_region["flags"].append(__location_flag)
    __ca4_station_flags = __ca3_station["flags"]
    if not (__location_flag in __ca4_station_flags):
        __ca4_station_flags.update({__location_flag: {}})
    __ca5_station_flag = __ca4_station_flags[__location_flag]
    if not (__location_flag in corp_accounting_stat):
        corp_accounting_stat.update({__location_flag: {"volume": 0, "cost": 0}})
    __cas1_stat_flag = corp_accounting_stat[__location_flag]
    return __ca5_station_flag, __cas1_stat_flag


def __build_accounting_register_region(
        region_id,
        region_name,
        loc_id,
        loc_name,
        corp_accounting_tree):
    if not (str(region_id) in corp_accounting_tree):
        corp_accounting_tree.update({str(region_id): {"region": region_name, "systems": {}, "flags": []}})
    __ca1_region = corp_accounting_tree[str(region_id)]
    __ca1_region["systems"].update({str(loc_id): {"loc_name": loc_name, "items": {}}})
    __ca2_system = __ca1_region["systems"][str(loc_id)]
    return __ca1_region, __ca2_system


def __build_accounting_station(
        loc_id,
        corp_assets_data,
        corp_accounting_stat,
        corp_assets_tree,
        sde_type_ids,
        sde_market_groups,
        __ca1_region,
        __ca3_station):
    for a in corp_assets_data:
        if int(a["location_id"]) == int(loc_id):
            __location_flag = a["location_flag"]
            __ca5_station_flag, __cas1_stat_flag = __build_accounting_register_flag(
                __location_flag,
                __ca1_region,
                __ca3_station,
                corp_accounting_stat)
            __build_accounting_nested(
                int(loc_id),
                sde_type_ids,
                sde_market_groups,
                corp_assets_tree,
                corp_assets_data,
                __cas1_stat_flag,
                __ca5_station_flag)


def __build_accounting(
        sde_type_ids,
        sde_inv_names,
        sde_inv_items,
        sde_market_groups,
        corp_ass_names_data,
        foreign_structures_data,
        foreign_structures_forbidden_ids,
        corp_assets_tree,
        corp_assets_data):
    if not ("roots" in corp_assets_tree):
        return None
    corp_accounting_stat = {}
    corp_accounting_tree = {}
    __roots = corp_assets_tree["roots"]
    for loc_id in __roots:
        region_id, region_name, loc_name, __dummy0 = eve_esi_tools.get_assets_location_name(
            loc_id,
            sde_inv_names,
            sde_inv_items,
            corp_ass_names_data,
            foreign_structures_data)
        if not (region_id is None):
            __ca1_region, __ca2_system = __build_accounting_register_region(
                region_id,
                region_name,
                loc_id,
                loc_name,
                corp_accounting_tree)
            for itm in corp_assets_tree[str(loc_id)]["items"]:
                __itm = str(itm)
                __ca2_system["items"].update({__itm: {"type_id": corp_assets_tree[__itm]["type_id"]}})
                __dummy1, __dummy2, loc_name, foreign = eve_esi_tools.get_assets_location_name(
                    itm,
                    sde_inv_names,
                    sde_inv_items,
                    corp_ass_names_data,
                    foreign_structures_data)
                __ca3_station = __ca2_system["items"][__itm]
                __ca3_station.update({"loc_name": loc_name, "foreign": foreign, "flags": {}})
                # имущество собственных станций и таможек тоже учитываем в сводной статистике
                if not foreign:
                    __item_dict = next((a for a in corp_assets_data if a['item_id'] == int(itm)), None)
                    if not (__item_dict is None):  # может попастся NPC-станция, пропускаем, это точно не наше имущество
                        __location_flag = __item_dict["location_flag"]
                        if __location_flag == "AutoFit":
                            __ca5_station_flag, __cas1_stat_flag = __build_accounting_register_flag(
                                __location_flag,
                                __ca1_region,
                                __ca3_station,
                                corp_accounting_stat)
                            __type_id = int(__item_dict["type_id"])
                            __group_id = eve_sde_tools.get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, __type_id)
                            if not (__group_id is None):
                                __build_accounting_append(
                                    __type_id,
                                    1,
                                    __group_id,
                                    sde_market_groups[str(__group_id)]["nameID"]["en"],
                                    sde_type_ids,
                                    __cas1_stat_flag,
                                    __ca5_station_flag)
                # на текущей станции получаем все location_flag и собираем сводную статистику по каждой группе
                __build_accounting_station(
                    itm,
                    corp_assets_data,
                    corp_accounting_stat,
                    corp_assets_tree,
                    sde_type_ids,
                    sde_market_groups,
                    __ca1_region,
                    __ca3_station)
        else:
            # не удалось получить сведения о регионе, - это неспроста, скорее всего на эту стуктуру у корпы forbidden
            if int(loc_id) in foreign_structures_forbidden_ids:
                __ca1_region, __ca2_system = __build_accounting_register_region(
                    0,  # "(none)"
                    "Forbidden",
                    0,
                    "(no data)",
                    corp_accounting_tree)
                __ca2_system["items"].update({str(loc_id): {"type_id": None}})
                __ca3_station = __ca2_system["items"][str(loc_id)]
                __ca3_station.update({"loc_name": str(loc_id), "foreign": True, "forbidden": True, "flags": {}})
            else:
                __ca1_region, __ca2_system = __build_accounting_register_region(
                    3006,  # "Unknown"
                    "Unknown",
                    0,
                    "(no data)",
                    corp_accounting_tree)
                __ca2_system["items"].update({str(loc_id): {"type_id": None}})
                __ca3_station = __ca2_system["items"][str(loc_id)]
                __ca3_station.update({"loc_name": str(loc_id), "foreign": True, "flags": {}})
            # на текущей станции получаем все location_flag и собираем сводную статистику по каждой группе
            __build_accounting_station(
                loc_id,
                corp_assets_data,
                corp_accounting_stat,
                corp_assets_tree,
                sde_type_ids,
                sde_market_groups,
                __ca1_region,
                __ca3_station)
    return corp_accounting_stat, corp_accounting_tree


def main():
    # работа с параметрами командной строки, получение настроек запуска программы, как то: работа в offline-режиме,
    # имя пилота ранее зарегистрированного и для которого имеется аутентификационный токен, регистрация нового и т.д.
    argv_prms = console_app.get_argv_prms()

    sde_type_ids = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "typeIDs")
    sde_inv_names = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "invNames")
    sde_inv_items = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "invItems")
    sde_market_groups = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "marketGroups")

    corps_accounting = {}
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

        # Построение дерева ассетов, с узлави в роли станций и систем, и листьями в роли хранящихся
        # элементов, в виде:
        # { location1: {items:[item1,item2,...],type_id,location_id},
        #   location2: {items:[item3],type_id} }
        corp_assets_tree = eve_esi_tools.get_assets_tree(corp_assets_data, foreign_structures_data, sde_inv_items, virtual_hierarchy_by_corpsag=False)
        eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_assets_tree.{}".format(corporation_name), corp_assets_tree)

        # Построение дерева имущества (сводная информация, учитывающая объёмы и ориентировочную стоимость asset-ов)
        corp_accounting_stat, corp_accounting_tree = __build_accounting(
            sde_type_ids,
            sde_inv_names,
            sde_inv_items,
            sde_market_groups,
            corp_ass_names_data,
            foreign_structures_data,
            foreign_structures_forbidden_ids,
            corp_assets_tree,
            corp_assets_data)
        eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_accounting_stat.{}".format(corporation_name), corp_accounting_stat)
        eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_accounting_tree.{}".format(corporation_name), corp_accounting_tree)

        corps_accounting.update({str(corporation_id): {
            "corporation": corporation_name,
            "stat": corp_accounting_stat,
            "tree": corp_accounting_tree
        }})

    eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corps_accounting", corps_accounting)

    # Построение дерева asset-ов:
    print("\nBuilding accounting report...")
    sys.stdout.flush()
    dump_accounting_into_report(
        # путь, где будет сохранён отчёт
        argv_prms["workspace_cache_files_dir"],
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corps_accounting)

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nDone")


if __name__ == "__main__":
    main()
