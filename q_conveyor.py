""" Q.Conveyor (desktop/mobile)

Prerequisites:
    * Have a Python 3 environment available to you (possibly by using a
      virtual environment: https://virtualenv.pypa.io/en/stable/).
    * Run pip install -r requirements.txt with this directory as your root.

    * Copy q_industrialist_settings.py.template into q_industrialist_settings.py and
      mood for your needs.
    * Copy q_conveyor_settings.py.template into q_conveyor_settings.py and
      mood for your needs.
    * Create an SSO application at developers.eveonline.com with the scopes
      from g_client_scope list declared in q_industrialist_settings.py and the
      callback URL "https://localhost/callback/".
      Note: never use localhost as a callback in released applications.

To run this example, make sure you have completed the prerequisites and then
run the following command from this directory as the root:

>>> python eve_sde_tools.py --cache_dir=~/.q_industrialist
>>> python q_conveyor.py --pilot="Qandra Si" --online --cache_dir=~/.q_industrialist

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

import eve_esi_tools
import eve_sde_tools
import console_app
import render_html_conveyor
import q_industrialist_settings
import q_conveyor_settings

from __init__ import __version__


def get_corp_bp_loc_data(corp_blueprints_data, corp_industry_jobs_data):
    """
    Построение иерархических списков БПО и БПЦ, хранящихся в корпоративных ангарах
    """
    corp_bp_loc_data = {}
    for bp in corp_blueprints_data:
        loc_id = int(bp["location_id"])
        loc_flag = str(bp["location_flag"])
        blueprint_id = int(bp["item_id"])
        # особенность : чертежи могут отсутствовать в assets по указанному location_id, при этом чертёж будет в
        # blueprints, но его location_id будет указывать на станцию, а не на контейнер, в то же время в industrial
        # jobs этот же самый чертёж будет находиться в списке и иметь blueprint_location_id который указывает на
        # искомый контейнер
        __job_dict = next((j for j in corp_industry_jobs_data if j['blueprint_id'] == int(blueprint_id)), None)
        if not (__job_dict is None):
            loc_id = __job_dict["blueprint_location_id"]
        # { "1033160348166": { "CorpSAG3": {} } }
        if not (str(loc_id) in corp_bp_loc_data):
            corp_bp_loc_data.update({str(loc_id): {loc_flag: {}}})
        elif not (loc_flag in corp_bp_loc_data[str(loc_id)]):
            corp_bp_loc_data[str(loc_id)].update({loc_flag: {}})
        __bp2 = corp_bp_loc_data[str(loc_id)][loc_flag]
        # { "1033160348166": { "CorpSAG3": {"30014": {}} } }
        type_id = int(bp["type_id"])
        if not (type_id in __bp2):
            __bp2.update({type_id: {}})
        # { "1033160348166": { "CorpSAG3": {"30014": { "o_10_20": {} } } } }
        quantity = int(bp["quantity"])
        is_blueprint_copy = quantity < -1
        bp_type = 'c' if is_blueprint_copy else 'o'
        material_efficiency = int(bp["material_efficiency"])
        time_efficiency = int(bp["time_efficiency"])
        bp_status = eve_esi_tools.get_blueprint_progress_status(corp_industry_jobs_data, blueprint_id)
        bp_key = '{bpt}_{me}_{te}_{st}'.format(
            bpt=bp_type,
            me=material_efficiency,
            te=time_efficiency,
            st="" if bp_status is None else bp_status[:2])
        runs = int(bp["runs"])
        quantity_or_runs = runs if is_blueprint_copy else quantity if quantity > 0 else 1
        # { "1033160348166": { "CorpSAG3": {"30014": { "o_10_20": { "cp":false,"me":10,..., [] } } } } }
        if not (bp_key in __bp2[type_id]):
            __bp2[type_id].update({bp_key: {
                "cp": is_blueprint_copy,
                "me": material_efficiency,
                "te": time_efficiency,
                "qr": quantity_or_runs,
                "st": bp_status,
                "itm": []
            }})
        else:
            __bp2[type_id][bp_key]["qr"] = __bp2[type_id][bp_key]["qr"] + quantity_or_runs
        # { "1033160348166": { "CorpSAG3": {"30014": { "o_10_20": { "cp":false,"me":10,..., [{"id":?,"q":?,"r":?}, {...}] } } } } }
        __itm_dict = {
            "id": blueprint_id,
            "q": quantity,
            "r": runs
        }
        if not (__job_dict is None):
            __itm_dict.update({"jc": __job_dict["cost"]})
        __bp2[type_id][bp_key]["itm"].append(__itm_dict)
    return corp_bp_loc_data


def get_corp_ass_loc_data(corp_assets_data, containers_filter=None):
    """
    Построение списка модулей и ресуров, которые имеются в распоряжении корпорации и
    которые предназначены для использования в чертежах
    """
    corp_ass_loc_data = {}
    for a in corp_assets_data:
        type_id = int(a["type_id"])
        # if materials_for_bps.count(type_id) > 0:
        loc_flag = str(a["location_flag"])
        if not (loc_flag == "Unlocked"):
            continue  # пропускаем дронов в дронбеях, патроны в карго и т.п. (раньше пропускались корабли в ангарах)
        loc_id = int(a["location_id"])
        if not (containers_filter is None):
            if not (loc_id in containers_filter):
                continue  # пропускаем все контейнеры, кроме тех, откуда ведётся производство
        quantity = int(a["quantity"])
        # { "CorpSAG6": {} }
        if not (str(loc_flag) in corp_ass_loc_data):
            corp_ass_loc_data.update({str(loc_flag): {}})
        __a1 = corp_ass_loc_data[str(loc_flag)]
        # { "CorpSAG6": {"1033692665735": {} } }
        if not (str(loc_id) in __a1):
            __a1.update({str(loc_id): {}})
        __a2 = __a1[str(loc_id)]
        # { "CorpSAG6": {"1033692665735": { "2488": <quantity> } } }
        if not (type_id in __a2):
            __a2.update({type_id: quantity})
        else:
            __a2[type_id] = quantity + __a2[type_id]
    return corp_ass_loc_data


def register_conveyor_entity(
        # conveyor_entities - список экземпляров конвейеров
        # conveyor_entity_num - номер конвейера в списке экземпляров
        conveyor_entities,
        conveyor_entity_num,
        # location_id - расположение чертежей (может быть либо номером контейнера, либо номером станции)
        # universe_location - сведения о местоположении локации во вселенной (сведения о станции)
        location_id,
        universe_location,
        # blueprints_settings - сведения о том, как используются чертежи
        # stock_settings - сведения о том, гда находится сток чертежей
        blueprints_settings,
        stock_settings,
        # esi данные, загруженные с серверов CCP
        corp_ass_names_data):
    same_stock_container = stock_settings.get('same_stock_container', False)
    fixed_number_of_runs = blueprints_settings.get('fixed_number_of_runs', None)
    # пытаемся найти возможно уже существующий экземпляр конвейера
    station_id = universe_location["station_id"]
    conveyor_entity = next((id for id in conveyor_entities if (id["station_id"] == station_id) and (id["num"] == conveyor_entity_num)), None)
    if conveyor_entity is None:
        conveyor_entity = {
            "num": conveyor_entity_num,
            "blueprints": []
        }
        conveyor_entity.update(universe_location)
        if not same_stock_container:
            conveyor_entity.update({
                "stock": []
            })
        conveyor_entities.append(conveyor_entity)
    # добавляем к текущей станции контейнер с чертежами
    container_dict = {
        "id": location_id,
        "name": next((n["name"] for n in corp_ass_names_data if n['item_id'] == location_id), None)
    }
    # добаляем в свойства контейнера фиксированное кол-во запусков чертежей из настроек
    if not (fixed_number_of_runs is None):
        container_dict.update({
            "fixed_number_of_runs": fixed_number_of_runs
        })
    # сохраняем признак того, что контейнер являются стоком материалов
    if same_stock_container:
        container_dict.update({
            "same_stock_container": True
        })
    # если "контейнер" является офисом с ангаром, то сохраняем информацию о номере ангара
    if "hangar_num" in universe_location:
        container_dict.update({
            "hangar_num": universe_location["hangar_num"]
        })
    conveyor_entity["blueprints"].append(container_dict)
    return conveyor_entity


def get_location_dict(
        # справочник-сведения о том, где искать чертежи и метариалы
        settings,
        # esi данные, загруженные с серверов CCP
        sde_inv_names,
        sde_inv_items,
        corp_assets_tree,
        corp_ass_names_data,
        foreign_structures_data):
    loc_dicts = []
    # находим ангары, в которых расположены чертежи
    if "hangars" in settings:
        for bch in settings["hangars"]:
            station_name = bch["station_name"]
            hangar_num = bch["hangar_num"]
            station_id = next((an for an in corp_ass_names_data if an["name"] == station_name), None)
            station_foreign = station_id is None
            # поиск тех станций, которые не принадлежат корпорации (на них имеется офис,
            # но самой станции в ассетах нет)
            if station_foreign:
                __foreign_keys = foreign_structures_data.keys()
                for __foreign_id in __foreign_keys:
                    __foreign_dict = foreign_structures_data[str(__foreign_id)]
                    if __foreign_dict["name"] == station_name:
                        station_id = int(__foreign_id)
                        break
            # если не удалось по названию станции найти её в корпассетах, то это м.б. ошибка в настройках
            if station_id is None:
                print('ERROR: Not found station identity for factory: ', station_name)
                continue
            loc_dict = eve_esi_tools.get_universe_location_by_item(
                station_id,
                sde_inv_names,
                sde_inv_items,
                corp_assets_tree,
                corp_ass_names_data,
                foreign_structures_data
            )
            # определяем номер офиса на найденной станции
            office_ids = corp_assets_tree.get(str(station_id), None)
            loc_dict.update({
                'place_id': office_ids['items'][0] if len(office_ids['items']) == 1 else station_id,
                'hangar_num': hangar_num,
            })
            loc_dicts.extend([loc_dict])
    # кешируем список шаблонов названий контейнеров, которые следует исключить из списка
    exclude_container_tmplts = settings.get("exclude_container_names", [])
    exclude_container_ids = []
    for tmplt in exclude_container_tmplts:
        exclude_container_ids.extend([n["item_id"] for n in corp_ass_names_data if re.search(tmplt, n['name'])])
    # находим контейнеры по заданным названиям
    if "container_names" in settings:
        for tmplt in settings["container_names"]:
            tmp_loc_dicts = []
            # пропускаем контейнеры, их которых нельзя доставать чертежи для достройки недостающих материалов
            container_ids = [n["item_id"] for n in corp_ass_names_data if re.search(tmplt, n['name']) and not (n["item_id"] in exclude_container_ids)]
            # находим станцию, где расположены найденные контейнеры
            for cid in container_ids:
                loc_dict = eve_esi_tools.get_universe_location_by_item(
                    cid,
                    sde_inv_names,
                    sde_inv_items,
                    corp_assets_tree,
                    corp_ass_names_data,
                    foreign_structures_data
                )
                if "station_id" in loc_dict:
                    loc_dict.update({'place_id': cid})
                    tmp_loc_dicts.extend([loc_dict])
            # если не удалось по названию станции найти её в корпассетах, то это м.б. ошибка в настройках
            if not tmp_loc_dicts:
                print('ERROR: Not found station identity for containers:', tmplt)
                continue
            loc_dicts.extend(tmp_loc_dicts)
    return loc_dicts


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

    authz = interface.authenticate(argv_prms["character_names"][0])
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

    sde_type_ids = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "typeIDs")
    sde_inv_names = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "invNames")
    sde_inv_items = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "invItems")
    sde_market_groups = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "marketGroups")
    sde_bp_materials = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "blueprints")
    sde_icon_ids = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "iconIDs")

    # Построение списка модулей и ресурсов, которые используются в производстве
    materials_for_bps = eve_sde_tools.get_materials_for_blueprints(sde_bp_materials)
    research_materials_for_bps = eve_sde_tools.get_research_materials_for_blueprints(sde_bp_materials)

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

    corp_ass_names_data = []
    corp_ass_named_ids = eve_esi_tools.get_assets_named_ids(corp_assets_data)
    if len(corp_ass_named_ids) > 0:
        # Requires role(s): Director
        corp_ass_names_data = interface.get_esi_data(
            "corporations/{}/assets/names/".format(corporation_id),
            json.dumps(corp_ass_named_ids, indent=0, sort_keys=False))
    print("\n'{}' corporation has {} custom asset's names".format(corporation_name, len(corp_ass_names_data)))
    sys.stdout.flush()

    # Построение иерархических списков БПО и БПЦ, хранящихся в корпоративных ангарах
    corp_bp_loc_data = get_corp_bp_loc_data(corp_blueprints_data, corp_industry_jobs_data)
    eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_bp_loc_data", corp_bp_loc_data)

    # Построение списка модулей и ресуров, которые имеются в распоряжении корпорации и
    # которые предназначены для использования в чертежах
    corp_ass_loc_data = get_corp_ass_loc_data(corp_assets_data, containers_filter=None)
    eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_ass_loc_data", corp_ass_loc_data)

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
    eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_assets_tree", corp_assets_tree)

    # Поиск контейнеров, которые участвуют в производстве
    conveyor_entities = []
    for __manuf_dict in enumerate(q_conveyor_settings.g_manufacturing):
        conveyor_entity_num = __manuf_dict[0]
        blueprints_settings = __manuf_dict[1]["blueprints"]
        materials_settings = __manuf_dict[1]["materials"]
        # кешируем признак того, что контейнеры являются стоком материалов
        same_stock_container = materials_settings.get("same_stock_container", False)
        # станция, ангары, контейнеры
        #   или находим ангары, в которых расположены чертежи
        #   или находим контейнеры по заданным названиям
        blueprint_locations = get_location_dict(
            blueprints_settings,
            sde_inv_names,
            sde_inv_items,
            corp_assets_tree,
            corp_ass_names_data,
            foreign_structures_data
        )
        if not blueprint_locations:
            print('ERROR: Not found location by settings: ', __manuf_dict[1]["blueprints"])
            continue
        for loc_dict in blueprint_locations:
            location_id = loc_dict["place_id"]  # номер контейнера или номер офиса на станции
            station_id = loc_dict["station_id"]
            conveyor_entity = register_conveyor_entity(
                conveyor_entities,
                conveyor_entity_num,
                location_id,
                loc_dict,
                blueprints_settings,
                materials_settings,
                corp_ass_names_data
            )
            if not same_stock_container:
                material_locations = get_location_dict(
                    materials_settings,
                    sde_inv_names,
                    sde_inv_items,
                    corp_assets_tree,
                    corp_ass_names_data,
                    foreign_structures_data
                )
                # на этой же станции находим контейнер со стоком материалов
                for stock_dict in material_locations:
                    stock_id = stock_dict["place_id"]  # номер контейнера или номер офиса на станции
                    if stock_dict.get("station_id", -1) == station_id:
                        # если "контейнер" является офисом с ангаром, то сохраняем информацию о номере ангара
                        container_stock_dict = {
                            "id": stock_id,
                            "name": next((n["name"] for n in corp_ass_names_data if n['item_id'] == stock_id), None)
                        }
                        if "hangar_num" in stock_dict:
                            container_stock_dict.update({
                                "hangar_num": stock_dict["hangar_num"]
                            })
                        conveyor_entity["stock"].append(container_stock_dict)
    # print("conveyor_entities:", conveyor_entities)  # TODO: debug

    # перечисляем станции и контейнеры, которые были найдены
    print('\nFound conveyor containters and station ids...')
    for ce in conveyor_entities:
        print('  {} = {}'.format(ce["station_id"], ce["station"]))
        for cec in ce["blueprints"]:
            print('    {} = {}'.format(cec["id"], cec["name"]))
        if "stock" in ce:
            for ces in ce["stock"]:
                print('    {} = {}'.format(ces["id"], ces["name"]))
    sys.stdout.flush()

    print("\nBuilding report...")
    sys.stdout.flush()

    render_html_conveyor.dump_conveyor_into_report(
        # путь, где будет сохранён отчёт
        argv_prms["workspace_cache_files_dir"],
        # настройки генерации отчёта
        conveyor_entities,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        sde_icon_ids,
        # esi данные, загруженные с серверов CCP
        corp_industry_jobs_data,
        corp_ass_names_data,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_ass_loc_data,
        corp_bp_loc_data,
        corp_assets_tree,
        materials_for_bps,
        research_materials_for_bps)

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nDone")


if __name__ == "__main__":
    main()
