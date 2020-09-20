""" Q.Workflow (desktop/mobile)

Prerequisites:
    * Have a Python 3 environment available to you (possibly by using a
      virtual environment: https://virtualenv.pypa.io/en/stable/).
    * Run pip install -r requirements.txt with this directory as your root.

    * Copy q_workflow_settings.py.template into q_workflow_settings.py and
      mood for your needs.
    * Create an SSO application at developers.eveonline.com with the scopes
      from g_client_scope list declared in q_workflow_settings.py and the
      callback URL "https://localhost/callback/".
      Note: never use localhost as a callback in released applications.

To run this example, make sure you have completed the prerequisites and then
run the following command from this directory as the root:

>>> python eve_sde_tools.py
>>> python q_workflow.py --pilot="Qandra Si" --online --cache_dir=~/.q_industrialist

Requires application scopes:
    * esi-assets.read_corporation_assets.v1 - Requires role(s): Director
"""
import sys
import json
import requests

import eve_esi_interface as esi

import q_workflow_settings
import q_industrialist_settings
import eve_esi_tools
import eve_sde_tools
import console_app
import render_html_workflow

from __init__ import __version__


def __get_blueprints_containers_with_data_loading(
        # esi input & output
        esi_interface,
        # настройки
        factory_settings,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        corp_assets_data):
    # esi input
    interface = esi_interface["interface"]
    corporation_id = esi_interface["corporation_id"]
    corporation_name = esi_interface["corporation_name"]
    # esi output
    esi_interface["corp_ass_names_data"] = []
    esi_interface["foreign_structures_data"] = {}

    # input setings
    hangars_filter = factory_settings["blueprints_hangars"]
    # output factory containers
    factory_containers = {
        "station_id": factory_settings["station_id"] if "station_id" in factory_settings else None,
        "station_name": factory_settings["station_name"] if "station_name" in factory_settings else None,
        "station_foreign": None,
        "containers": None
    }

    # пытаемся определить недостающее звено, либо station_id, либо station_name (если неизвестны)
    if not (factory_containers["station_id"] is None):
        station_id = factory_containers["station_id"]
        factory_containers["station_foreign"] = next((a for a in corp_assets_data if a["item_id"] == int(station_id)), None) is None

        # поиск контейнеров на станции station_id в ангарах hangars_filter
        factory_containers["containers"] = eve_esi_tools.find_containers_in_hangars(
            station_id,
            hangars_filter,
            sde_type_ids,
            corp_assets_data)

        esi_interface["corp_ass_names_data"] = []
        corp_ass_named_ids = [bc["id"] for bc in factory_containers["containers"]]
        if not factory_containers["station_foreign"]:
            corp_ass_named_ids.append(station_id)
            station_name = next((an for an in esi_interface["corp_ass_names_data"] if an["item_id"] == station_id), None)

        if len(corp_ass_named_ids) > 0:
            # Requires role(s): Director
            esi_interface["corp_ass_names_data"] = interface.get_esi_data(
                "corporations/{}/assets/names/".format(corporation_id),
                json.dumps(corp_ass_named_ids, indent=0, sort_keys=False))
        print("\n'{}' corporation has {} custom asset's names".format(corporation_name, len(esi_interface["corp_ass_names_data"])))
        sys.stdout.flush()

        if factory_containers["station_foreign"]:
            # поиск одной единственной станции, которая не принадлежат корпорации (на них имеется офис,
            # но самой станции в ассетах нет)
            esi_interface["foreign_structures_data"] = {}
            foreign_structures_ids = [station_id]
            foreign_structures_forbidden_ids = []
            if len(foreign_structures_ids) > 0:
                # Requires: access token
                for structure_id in foreign_structures_ids:
                    try:
                        universe_structure_data = interface.get_esi_data(
                            "universe/structures/{}/".format(structure_id))
                        esi_interface["foreign_structures_data"].update({str(structure_id): universe_structure_data})
                    except requests.exceptions.HTTPError as err:
                        status_code = err.response.status_code
                        if status_code == 403:  # это нормально, что часть структур со временем могут оказаться Forbidden
                            foreign_structures_forbidden_ids.append(structure_id)
                        else:
                            raise
                    except:
                        print(sys.exc_info())
                        raise
            print("\n'{}' corporation has offices in {} foreign stations".format(corporation_name, len(esi_interface["foreign_structures_data"])))
            if len(foreign_structures_forbidden_ids) > 0:
                print("\n'{}' corporation has offices in {} forbidden stations : {}".format(corporation_name, len(foreign_structures_forbidden_ids), foreign_structures_forbidden_ids))
            sys.stdout.flush()

            if str(station_id) in esi_interface["foreign_structures_data"]:
                station_name = esi_interface["foreign_structures_data"][str(station_id)]["name"]

        # вывод на экран найденных station_id и station_name
        if station_name is None:
            raise Exception('Not found station name for factory {}!!!'.format(station_id))

    elif not (factory_containers["station_name"] is None):
        station_name = factory_containers["station_name"]

        esi_interface["corp_ass_names_data"] = []
        corp_ass_named_ids = eve_esi_tools.get_assets_named_ids(corp_assets_data)
        if len(corp_ass_named_ids) > 0:
            # Requires role(s): Director
            esi_interface["corp_ass_names_data"] = interface.get_esi_data(
                "corporations/{}/assets/names/".format(corporation_id),
                json.dumps(corp_ass_named_ids, indent=0, sort_keys=False))
        print("\n'{}' corporation has {} custom asset's names".format(corporation_name, len(esi_interface["corp_ass_names_data"])))
        sys.stdout.flush()

        station_id = next((an for an in esi_interface["corp_ass_names_data"] if an["name"] == station_name), None)
        factory_containers["station_foreign"] = station_id is None

        if factory_containers["station_foreign"]:
            # поиск тех станций, которые не принадлежат корпорации (на них имеется офис, но самой станции в ассетах нет)
            esi_interface["foreign_structures_data"] = {}
            foreign_structures_ids = eve_esi_tools.get_foreign_structures_ids(corp_assets_data)
            foreign_structures_forbidden_ids = []
            if len(foreign_structures_ids) > 0:
                # Requires: access token
                for structure_id in foreign_structures_ids:
                    try:
                        universe_structure_data = interface.get_esi_data(
                            "universe/structures/{}/".format(structure_id))
                        esi_interface["foreign_structures_data"].update({str(structure_id): universe_structure_data})
                    except requests.exceptions.HTTPError as err:
                        status_code = err.response.status_code
                        if status_code == 403:  # это нормально, что часть структур со временем могут оказаться Forbidden
                            foreign_structures_forbidden_ids.append(structure_id)
                        else:
                            raise
                    except:
                        print(sys.exc_info())
                        raise
            print("\n'{}' corporation has offices in {} foreign stations".format(corporation_name, len(esi_interface["foreign_structures_data"])))
            if len(foreign_structures_forbidden_ids) > 0:
                print("\n'{}' corporation has offices in {} forbidden stations : {}".format(corporation_name, len(foreign_structures_forbidden_ids), foreign_structures_forbidden_ids))
            sys.stdout.flush()

            __foreign_keys = esi_interface["foreign_structures_data"].keys()
            for __foreign_id in __foreign_keys:
                __foreign_dict = esi_interface["foreign_structures_data"][str(__foreign_id)]
                if __foreign_dict["name"] == station_name:
                    station_id = int(__foreign_id)
                    break

        # вывод на экран найденных station_id и station_name
        if station_id is None:
            raise Exception('Not found station identity for factory {}!!!'.format(station_name))

        # поиск контейнеров на станции station_id в ангарах hangars_filter
        factory_containers["containers"] = eve_esi_tools.find_containers_in_hangars(
            station_id,
            hangars_filter,
            sde_type_ids,
            corp_assets_data)

    else:
        raise Exception('Not found station identity and name!!!')

    factory_containers["station_id"] = station_id
    factory_containers["station_name"] = station_name

    # получение названий контейнеров и сохранение из в списке контейнеров
    for __cont_dict in factory_containers["containers"]:
        __item_id = __cont_dict["id"]
        __item_name = next((an for an in esi_interface["corp_ass_names_data"] if an["item_id"] == __item_id), None)
        if not (__item_name is None):
            __cont_dict["name"] = __item_name["name"]

    return factory_containers


def __get_monthly_manufacturing_scheduler(
        # настройки
        scheduler_job_settings,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_named_type_ids,
        sde_bp_materials,
        # esi данные, загруженные с серверов CCP
        corp_blueprints_data,
        corp_industry_jobs_data,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        factory_containers):
    # конвертация ETF в список item-ов
    scheduler = {
        "monthly_jobs": [],
        "scheduled_blueprints": [],
        "factory_containers": factory_containers,
    }

    def push_into_scheduled_blueprints(type_id, quantity, name):
        __sb_dict = next((sb for sb in scheduler["scheduled_blueprints"] if sb["type_id"] == type_id), None)
        if __sb_dict is None:
            __sb_dict = {"type_id": type_id, "quantity": int(quantity), "name": name}
            scheduler["scheduled_blueprints"].append(__sb_dict)
        else:
            __sb_dict["quantity"] += int(quantity)

    # конвертация ETF в список item-ов
    for ship in scheduler_job_settings:
        __eft = ship["eft"]
        __total_quantity = ship["quantity"]
        __converted = eve_sde_tools.get_items_list_from_eft(__eft, sde_named_type_ids)
        __converted.update({"quantity": __total_quantity})
        if not (__converted["ship"] is None):
            __blueprint_type_id, __dummy0 = eve_sde_tools.get_blueprint_type_id_by_product_id(
                __converted["ship"]["type_id"],
                sde_bp_materials
            )
            __converted["ship"]["blueprint_type_id"] = __blueprint_type_id
        __converted["items"].sort(key=lambda i: i["name"])
        for __item_dict in __converted["items"]:
            __item_type_id = __item_dict["type_id"]
            __blueprint_type_id, __dummy0 = eve_sde_tools.get_blueprint_type_id_by_product_id(
                __item_type_id,
                sde_bp_materials
            )
            __item_dict["blueprint_type_id"] = __blueprint_type_id
        scheduler["monthly_jobs"].append(__converted)

    # формирование списка чертежей, которые необходимы для постройки запланированного кол-ва фитов
    for job in scheduler["monthly_jobs"]:
        __ship = job["ship"]
        __total_quantity = job["quantity"]
        __items = job["items"]
        # добавляем в список БПЦ чертёж хула корабля (это может быть и БПО в итоге...)
        if not (__ship is None):
            if ("blueprint_type_id" in __ship) and not (__ship["blueprint_type_id"] is None):
                push_into_scheduled_blueprints(__ship["blueprint_type_id"], __total_quantity, __ship["name"])
        # подсчитываем количество БПЦ, необходимых для постройки T2-модулей этого фита
        __bpc_for_fit = [{"id": i["blueprint_type_id"], "q": __total_quantity * i["quantity"], "nm": i["name"]}
                         for i in __items if
                         ("blueprint_type_id" in i) and not (i["blueprint_type_id"] is None) and
                         ("metaGroupID" in i["details"]) and
                         (i["details"]["metaGroupID"] == 2)]
        for bpc in __bpc_for_fit:
            push_into_scheduled_blueprints(bpc["id"], bpc["q"], bpc["nm"])
    return scheduler


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

    sde_type_ids = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "typeIDs")
    sde_bp_materials = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "blueprints")

    sde_named_type_ids = eve_sde_tools.convert_sde_type_ids(sde_type_ids)

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

    # для того, чтобы получить названия коробок и в каком ангаре они расположены, надо загрузить
    # данные по ассетам, т.к. только в этих данных можно учитывая иерархию пересчитать коробки
    # в нужном ангаре

    # Requires role(s): Director
    corp_assets_data = interface.get_esi_paged_data(
        "corporations/{}/assets/".format(corporation_id))
    print("\n'{}' corporation has {} assets".format(corporation_name, len(corp_assets_data)))
    sys.stdout.flush()

    esi_interface = {
        "interface": interface,
        "corporation_id": corporation_id,
        "corporation_name": corporation_name,
        "corp_ass_names_data": None,
        "foreign_structures_data": None
    }
    factory_containers = __get_blueprints_containers_with_data_loading(
        esi_interface,
        q_workflow_settings.g_monthly_jobs["factory"],
        sde_type_ids,
        corp_assets_data
    )
    print('\nFound factory station {} with containers in hangars...'.format(factory_containers["station_name"]))
    print('  {} = {}'.format(factory_containers["station_id"], factory_containers["station_name"]))
    print('  blueprint hangars = {}'.format(q_workflow_settings.g_monthly_jobs["factory"]["blueprints_hangars"]))
    print('  blueprint containers = {}'.format(len([fc["id"] for fc in factory_containers["containers"]])))
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

    # формирование набора данных для построения отчёта
    corp_manufacturing_scheduler = __get_monthly_manufacturing_scheduler(
        # настройки
        q_workflow_settings.g_monthly_jobs["jobs"],
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_named_type_ids,
        sde_bp_materials,
        # esi данные, загруженные с серверов CCP
        corp_blueprints_data,
        corp_industry_jobs_data,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        factory_containers
    )
    eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_manufacturing_scheduler", corp_manufacturing_scheduler)

    print("\nBuilding report...")
    sys.stdout.flush()

    render_html_workflow.dump_workflow_into_report(
        # путь, где будет сохранён отчёт
        argv_prms["workspace_cache_files_dir"],
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_manufacturing_scheduler
    )

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nDone")


if __name__ == "__main__":
    main()
