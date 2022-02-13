""" Q.Workflow (desktop/mobile)

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

$ chcp 65001 & @rem on Windows only!
$ python eve_sde_tools.py
$ python q_workflow.py --pilot="Qandra Si" --online --cache_dir=~/.q_industrialist

Requires application scopes:
    * esi-assets.read_corporation_assets.v1 - Requires role(s): Director
"""
import sys
import json
import requests

import eve_esi_interface as esi
import postgresql_interface as db

import q_industrialist_settings
import eve_esi_tools
import eve_sde_tools
import console_app
import render_html_workflow
import render_html_industry

from __init__ import __version__


g_module_default_settings = {
    # either "station_id" or "station_name" is required
    # if "station_id" is unknown, then the names of stations and structures will be
    # additionally loaded (too slow, please identify and set "station_id")
    "factory:station_id": 60003760,
    "factory:station_name": "Jita IV - Moon 4 - Caldari Navy Assembly Plant",
    # hangar, which stores blueprint copies to build T2 modules
    "factory:blueprints_hangars": [1],

    # номера контейнеров, в которых располагаются чертежи для конвейера
    # устарело, не используется: "industry:conveyor_boxes": [],
}
g_module_default_types = {
    "factory:station_id2": int,
    "factory:station_name2": str,
    "factory:blueprints_hangars2": list,

    "factory:station_id3": int,
    "factory:station_name3": str,
    "factory:blueprints_hangars3": list,

    "factory:station_id4": int,
    "factory:station_name4": str,
    "factory:blueprints_hangars4": list,

    "factory:station_id5": int,
    "factory:station_name5": str,
    "factory:blueprints_hangars5": list,
}


def __get_blueprints_containers(
        # настройки
        module_settings,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_inv_names,
        # esi данные, загруженные с серверов CCP
        corp_assets_data,
        foreign_structures_data,
        corp_ass_names_data):
    search_settings = []
    for station_num in range(1, 6):
        station_num_str = '' if station_num == 1 else str(station_num)
        # input setings
        hangars_filter = module_settings.get("factory:blueprints_hangars"+station_num_str, None)
        if hangars_filter is None:
            continue
        # output factory containers
        factory_containers = {
            "station_id": module_settings.get("factory:station_id"+station_num_str, None),
            "station_name": module_settings.get("factory:station_name"+station_num_str, None),
            "user_data": {"station_num": station_num},
            "station_foreign": None,
            "hangars_filter": hangars_filter,
            "containers": None
        }
        if (factory_containers['station_id'] is None) and (factory_containers['station_name'] is None):
            continue
        search_settings.append(factory_containers)
    factories_containers = eve_esi_tools.get_containers_on_stations(
        search_settings,
        sde_type_ids,
        sde_inv_names,
        corp_assets_data,
        foreign_structures_data,
        corp_ass_names_data,
        throw_when_not_found=False
    )
    return factories_containers


def __get_monthly_manufacturing_scheduler(
        # настройки
        scheduler_job_settings,
        db_factory_containers,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_named_type_ids,
        sde_bp_materials,
        sde_market_groups,
        # esi данные, загруженные с серверов CCP
        corp_blueprints_data,
        corp_industry_jobs_data,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        factories_containers):
    # конвертация ETF в список item-ов
    scheduler = {
        "monthly_jobs": [],
        "scheduled_blueprints": [],
        "factories_containers": factories_containers,
        "factory_repository": [],
        "factory_blueprints": [],
        "missing_blueprints": [],
        "overplus_blueprints": [],
        "loaded_blueprints": len(corp_blueprints_data)
    }
    scheduled_blueprints = scheduler["scheduled_blueprints"]
    factory_blueprints = scheduler["factory_blueprints"]
    missing_blueprints = scheduler["missing_blueprints"]
    overplus_blueprints = scheduler["overplus_blueprints"]

    def push_into_scheduled_blueprints(type_id, quantity, name, product_type_id, conveyor_flag):
        __sbd227 = next((sb for sb in scheduled_blueprints if sb["type_id"] == type_id), None)
        if __sbd227 is None:
            __sbd227 = {"type_id": type_id,
                        "name": eve_sde_tools.get_item_name_by_type_id(sde_type_ids, type_id),
                        "product": {"scheduled_quantity": 0,
                                    "conveyor_quantity": 0,
                                    "name": name,
                                    "type_id": product_type_id}}
            if conveyor_flag:
                __sbd227["product"]["conveyor_quantity"] += int(quantity)
            else:
                __sbd227["product"]["scheduled_quantity"] += int(quantity)
            # получаем данные по чертежу, - продукция, кол-во производимой продукции, материалы
            __ptid227, __pq227, __pm227 = \
                eve_sde_tools.get_manufacturing_product_by_blueprint_type_id(type_id, sde_bp_materials)
            if not (__ptid227 is None):
                if __ptid227 != product_type_id:
                    raise Exception('Unable to match product {} and blueprint()!!!'.format(product_type_id, type_id))
                __sbd227["products_per_run"] = __pq227
                __sbd227["manufacturing"] = {"materials": __pm227}
            scheduled_blueprints.append(__sbd227)
        else:
            if conveyor_flag:
                __sbd227["product"]["conveyor_quantity"] += int(quantity)
            else:
                __sbd227["product"]["scheduled_quantity"] += int(quantity)

    def push_into_factory_blueprints(type_id, runs):
        __fbd235 = next((fb for fb in factory_blueprints if fb["type_id"] == type_id), None)
        if __fbd235 is None:
            __fbd235 = {"type_id": type_id,
                        "runs": int(runs),
                        "quantity": 1,
                        # "name": name,
                        # "meta_group": meta_group
                        }
            factory_blueprints.append(__fbd235)
        else:
            __fbd235["runs"] += int(runs)
            __fbd235["quantity"] += 1

    # конвертация ETF в список item-ов
    for ship in scheduler_job_settings:
        __eft = ship["eft"]
        __total_quantity = ship["quantity"]
        __conveyor_flag = ship["conveyor"]
        __converted = eve_sde_tools.get_items_list_from_eft(__eft, sde_named_type_ids)
        __converted.update({"quantity": __total_quantity, "conveyor": __conveyor_flag})
        if not (__converted["ship"] is None):
            __blueprint_type_id, __blueprint_dict = eve_sde_tools.get_blueprint_type_id_by_product_id(
                __converted["ship"]["type_id"],
                sde_bp_materials
            )
            __converted["ship"].update({"blueprint": {
                "type_id": __blueprint_type_id,
                # "manufacturing": __blueprint_dict["activities"]["manufacturing"]
            }})
        __converted["items"].sort(key=lambda i: i["name"])
        for __item_dict in __converted["items"]:
            __item_type_id = __item_dict["type_id"]
            __blueprint_type_id, __blueprint_dict = eve_sde_tools.get_blueprint_type_id_by_product_id(
                __item_type_id,
                sde_bp_materials
            )
            if not (__blueprint_type_id is None) and ("manufacturing" in __blueprint_dict["activities"]):
                __item_dict.update({"blueprint": {
                    "type_id": __blueprint_type_id,
                    # "manufacturing": __blueprint_dict["activities"]["manufacturing"]
                }})
        scheduler["monthly_jobs"].append(__converted)

    # формирование списка чертежей, которые необходимы для постройки запланированного кол-ва фитов
    for job in scheduler["monthly_jobs"]:
        __ship = job["ship"]
        __total_quantity = job["quantity"]
        __conveyor_flag = job["conveyor"]
        __items = job["items"]
        # добавляем в список БПЦ чертёж хула корабля (это может быть и БПО в итоге...)
        if not (__ship is None):
            if "blueprint" in __ship:
                push_into_scheduled_blueprints(
                    __ship["blueprint"]["type_id"],
                    __total_quantity,
                    __ship["name"],
                    __ship["type_id"],
                    __conveyor_flag
                )
        # подсчитываем количество БПЦ, необходимых для постройки T2-модулей этого фита
        __bpc_for_fit = [{"id": i["blueprint"]["type_id"],
                          "q": __total_quantity * i["quantity"],
                          "nm": i["name"],
                          "prod": i["type_id"]}
                         for i in __items if
                         ("blueprint" in i) and
                         ("metaGroupID" in i["details"]) and
                         (i["details"]["metaGroupID"] == 2)]
        for bpc in __bpc_for_fit:
            push_into_scheduled_blueprints(
                bpc["id"],
                bpc["q"],
                bpc["nm"],
                bpc["prod"],
                __conveyor_flag
            )

    # формирование списка чертежей имеющихся на станции в указанных контейнерах
    factory_container_ids = []
    for factory_containers in factories_containers:
        factory_container_ids.extend([fc["id"] for fc in factory_containers["containers"]])
    db_factory_container_ids = [dbfc["id"] for dbfc in db_factory_containers if dbfc["active"] and not dbfc["disabled"]]
    # A range of numbers with a minimum of -2 and no maximum value where -1 is an original and -2 is a copy.
    # It can be a positive integer if it is a stack of blueprint originals fresh from the market (e.g. no
    # activities performed on them yet).
    scheduler["factory_repository"] = [bp for bp in corp_blueprints_data if
                                       (bp["location_id"] in factory_container_ids) and  # real ids
                                       (bp["location_id"] in db_factory_container_ids) and  # ids from database settings (filter for real ids)
                                       (bp["quantity"] == -2)]

    # формирование сводного списка чертежей фабрики, с суммарным кол-вом run-ов
    factory_repository = scheduler["factory_repository"]
    for bp in factory_repository:
        __blueprint_type_id = bp["type_id"]
        push_into_factory_blueprints(__blueprint_type_id, bp["runs"])
    # получение названий чертежей и сохранение их в сводном списке чертежей фабрики
    for bp in factory_blueprints:
        __blueprint_type_id = bp["type_id"]
        __product_type_id, __dummy0, __dummy1 = \
            eve_sde_tools.get_manufacturing_product_by_blueprint_type_id(__blueprint_type_id, sde_bp_materials)
        bp["name"] = eve_sde_tools.get_item_name_by_type_id(sde_type_ids, __blueprint_type_id)
        bp["product_type_id"] = __product_type_id
        # на станции может быть куча всяких БПЦ, нас будут интересовать только Т2 БПЦ
        if not (str(__blueprint_type_id) in sde_type_ids):
            continue
        __item_dict = sde_type_ids[str(__blueprint_type_id)]
        bp["meta_group"] = int(__item_dict["metaGroupID"]) if "metaGroupID" in __item_dict else None

    # расчёт кол-ва run-ов с учётом кратности run-ов T2-чертежей (в списке scheduled_blueprints)
    for __sb_dict in scheduled_blueprints:
        __blueprint_type_id = __sb_dict["type_id"]
        __scheduled_products = __sb_dict["product"]["scheduled_quantity"]
        __product_type_id = __sb_dict["product"]["type_id"]
        __products_per_run = __sb_dict["products_per_run"]
        # получаем список market-груп, которым принадлежит продукт
        __market_groups_chain = eve_sde_tools.get_market_groups_chain_by_type_id(
            sde_type_ids,
            sde_market_groups,
            __product_type_id)
        __market_groups = set(__market_groups_chain)
        # в расчётах учитывается правило: Т2 модули - 10 ранов, все хулы - 4 рана, все риги - 3 рана (см. 1_industry.py)
        __blueprint_copy_runs = 10  # Ship Equipment, Drones, Ammunition & Charges, ...
        if 4 in __market_groups:  # Ships
            __blueprint_copy_runs = 4
        elif 955 in __market_groups:  # Ship and Module Modifications
            __blueprint_copy_runs = 3
        __single_run_quantity = __blueprint_copy_runs * __products_per_run
        __scheduled_blueprints_quantity = \
            int(__scheduled_products + __single_run_quantity - 1) // int(__single_run_quantity)
        # сохраняем кол-во БПЦ по правилу выше
        # внимание! на самом деле это магическое число зависит от точных знаний - сколько прогонов
        # может быть у чертежа? но это "рекомендуемое" число, и вовсе не факт, что так и будет...
        __sb_dict["blueprints_quantity"] = __scheduled_blueprints_quantity
        # тот самый "магический" множитель - кол-во прогонов на чертёж (ожидаемое)
        __sb_dict["blueprint_copy_runs"] = __blueprint_copy_runs

    # формирование списка недостающих чертежей
    for __sb_dict in scheduled_blueprints:
        # получаем данные по чертежу, запланированному к использованию
        __blueprint_type_id = __sb_dict["type_id"]
        __product_type_id = __sb_dict["product"]["type_id"]
        __scheduled_products = __sb_dict["product"]["scheduled_quantity"]
        __conveyor_products = __sb_dict["product"]["conveyor_quantity"]
        __products_per_run = __sb_dict["products_per_run"]
        __blueprint_copy_runs = __sb_dict["blueprint_copy_runs"]
        __single_run_quantity = __blueprint_copy_runs * __products_per_run
        # получаем данные по имеющимся чертежам
        __exist = [fb for fb in factory_blueprints if fb["type_id"] == __blueprint_type_id]
        # суммируем прогоны чертежей и переводим их в количество продуктов, которые м.б. построено
        __exist_runs = sum([fb["runs"] for fb in __exist])  # напр. 3 рана...
        __exist_run_products = __exist_runs * __products_per_run  # ...по 1000 шт продукции, итого 3000 продукций
        # расчитываем недостающее кол-во чертежей
        __all_products = __scheduled_products + __conveyor_products
        if __exist_run_products >= __all_products:
            __missing_scheduled = 0
            __missing_conveyor = 0
        elif __exist_run_products >= __scheduled_products:
            __missing_scheduled = 0
            __rest_products = __scheduled_products - __exist_run_products
            __missing_conveyor = (__rest_products + __conveyor_products + __single_run_quantity - 1) // __single_run_quantity
        else:
            __rest_products = __scheduled_products - __exist_run_products  # 182 need - 110 exist => 72 rest
            __missing_scheduled = (__rest_products + __single_run_quantity - 1) // __single_run_quantity  # (72+9)/10=8
            __rest_products = __single_run_quantity - __rest_products % __single_run_quantity  # 10-(72%10)=8
            if __conveyor_products >= __rest_products:  # (11-8+9)/10=1
                __missing_conveyor = (__conveyor_products - __rest_products + __single_run_quantity - 1) // __single_run_quantity
            else:  # 7<8 => 0
                __missing_conveyor = 0

        #print(__sb_dict["name"],
        #      "scheduled=", __all_products,
        #      ",  per run=", __blueprint_copy_runs, '*', __products_per_run,
        #      ",  required=", __sb_dict["blueprints_quantity"],
        #      ",  missing=", __missing_blueprints,
        #      ",  exist=", [fb["runs"] for fb in __exist], "*", __products_per_run,
        #      ",  ex_runs=", __exist_runs)
        # отправка данных для формирования отчёта
        missing_blueprints.append({
            "type_id": __blueprint_type_id,
            "name": __sb_dict["name"],
            "product_type_id": __product_type_id,
            "missing_scheduled_blueprints": __missing_scheduled,  # подразумевается как недостающее scheduled' кол-во
            "missing_conveyor_blueprints": __missing_conveyor,  # подразумевается как недостающее conveyor' кол-во
            "available_quantity": (__exist_run_products + __single_run_quantity - 1) // __single_run_quantity,
            "scheduled_quantity": (__scheduled_products + __single_run_quantity - 1) // __single_run_quantity,
            "conveyor_quantity": (__conveyor_products + __single_run_quantity - 1) // __single_run_quantity
        })

    # формирование списка избыточных чертежей
    scheduled_blueprint_type_ids = [int(sb["type_id"]) for sb in scheduled_blueprints]
    for __fb_dict in factory_blueprints:
        __blueprint_type_id = __fb_dict["type_id"]
        __meta_group = __fb_dict["meta_group"]
        __product_type_id = __fb_dict["product_type_id"]
        # на станции может быть куча всяких БПЦ, нам интересуют излишки только Т2 чертежей
        if __meta_group is None:
            continue
        elif int(__meta_group) != 2:
            continue
        # если БПЦ с указанным типом вовсе отсутствует в списке требуемых для постройки, то сразу
        # создаём запись об излишках, где все чертежи этого типа будут лишними
        if not (__blueprint_type_id in scheduled_blueprint_type_ids):
            overplus_blueprints.append({
                "type_id": __blueprint_type_id,
                "name": __fb_dict["name"],
                "product_type_id": __product_type_id,
                "unnecessary_quantity": __fb_dict["quantity"],
                "all_of_them": True  # признак, что все чертежи этого типа - лишние
            })

    return scheduler


def __get_db_connection():
    qidb = db.QIndustrialistDatabase("workflow", debug=True)
    qidb.connect(q_industrialist_settings.g_database)
    return qidb


def __actualize_factory_containers(db_factory_containers, real_factory_containers, station_num):
    # "containers": [
    #    {"id": 1032456650838,
    #     "type_id": 33011,
    #     "name": "t2 fit 2"},... ]
    qidb = None
    default_active = 't' if len(db_factory_containers) == 0 else 'f'
    for fc in real_factory_containers:
        db_fc = next((c for c in db_factory_containers if int(c["id"]) == int(fc["id"])), None)
        if (db_fc is None) or \
                ("name" in fc) and (db_fc["name"] != fc["name"]) or \
                db_fc["disabled"]:
            if qidb is None:
                qidb = __get_db_connection()
            if db_fc is None:
                qidb.execute(  # контейнер с заданным id отсутствует в БД - добавляем выключенным
                    "INSERT INTO workflow_factory_containers(wfc_id,wfc_name,wfc_active,wfc_station_num) "
                    "VALUES(%s,%s,%s,%s);",
                    fc["id"], fc["name"] if "name" in fc else None, default_active, station_num)
                db_factory_containers.append({
                    "id": fc["id"],
                    "name": fc["name"] if "name" in fc else None,
                    "active": default_active,
                    "disabled": False,
                    "station_num": station_num,
                    "processed": True})
            elif ("name" in fc) and (db_fc["name"] != fc["name"]):
                if db_fc["disabled"]:
                    if qidb is None:
                        qidb = __get_db_connection()
                    qidb.execute(  # контейнер был переименован и вернулся в ангар (раньше там отсутствовал)
                        "UPDATE workflow_factory_containers SET wfc_name=%s,wfc_disabled=FALSE WHERE wfc_id=%s;",
                        fc["name"], fc["id"])
                    db_fc["disabled"] = False
                else:
                    if qidb is None:
                        qidb = __get_db_connection()
                    qidb.execute(  # контейнер был переименован
                        "UPDATE workflow_factory_containers SET wfc_name=%s WHERE wfc_id=%s;",
                        fc["name"], fc["id"])
                db_fc["name"] = fc["name"]
            elif db_fc["disabled"]:
                if qidb is None:
                    qidb = __get_db_connection()
                qidb.execute(  # контейнер вернулся в ангар (раньше там отсутствовал)
                    "UPDATE workflow_factory_containers SET wfc_disabled=FALSE WHERE wfc_id=%s;",
                    fc["id"])
                db_fc["disabled"] = False
        if not (db_fc is None):
            if db_fc['station_num'] != station_num:
                if qidb is None:
                    qidb = __get_db_connection()
                qidb.execute(  # контейнер перемещён на другую станцию (раньше обнаруживался на другой)
                    "UPDATE workflow_factory_containers SET wfc_station_num=%s WHERE wfc_id=%s;",
                    station_num, db_fc["id"])
                db_fc["station_num"] = station_num
            db_fc.update({"processed": True})
    if len(db_factory_containers) > 0:
        for db_fc in db_factory_containers:
            # пропускаем актуализированные контейнеры (имеющиеся сейчас в ангарах)
            if "processed" in db_fc:
                continue
            # пропускаем контейнеры других станций
            if db_fc['station_num'] != station_num:
                continue
            # пропускаем уже помеченные "отсутствующими" контейнеры
            if db_fc["disabled"]:
                continue
            if qidb is None:
                qidb = __get_db_connection()
            print(db_fc)
            qidb.execute(  # контейнер исчез из ангара (помечаем "отсутствующим", оставляем в БД)
                "UPDATE workflow_factory_containers SET wfc_disabled=TRUE WHERE wfc_id=%s;",
                db_fc["id"])
            db_fc["disabled"] = True
    if not (qidb is None):
        qidb.commit()
        del qidb


def __build_industry(
        # настройки
        qidb,
        module_settings,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        sde_named_type_ids,
        # esi данные, загруженные с серверов CCP
        corp_industry_jobs_data):
    corp_industry_stat = {
        "new_jobs_found": 0,
        "current_month": -1,
        "conveyor_scheduled_products": [],
        "workflow_industry_jobs": [],
        "workflow_last_industry_jobs": [],
        "conveyor_market_groups": {}
    }

    def push_into_conveyor_market_groups(__market_group_id):
        if corp_industry_stat["conveyor_market_groups"].get(str(__market_group_id), None) is None:
            corp_industry_stat["conveyor_market_groups"].update({
                str(__market_group_id): eve_sde_tools.get_market_group_name_by_id(sde_market_groups, __market_group_id)
            })

    # получаем текущий месяц с помощью sql-запроса
    db_current_month = qidb.select_one_row("SELECT EXTRACT(MONTH FROM CURRENT_DATE)")
    corp_industry_stat["current_month"] = int(db_current_month[0])

    # сохраняем данные по производству в БД
    wij = db.QWorkflowIndustryJobs(qidb)
    corp_industry_stat["new_jobs_found"] = wij.actualize(corp_industry_jobs_data, sde_bp_materials)
    del wij

    db_conveyor_jobs = qidb.select_all_rows(
        "SELECT wmj_quantity,wmj_eft "
        "FROM workflow_monthly_jobs "
        "WHERE wmj_active AND wmj_conveyor;")

    # конвертация ETF в список item-ов
    conveyor_product_type_ids = []
    conveyor_scheduled_products = []
    for job in db_conveyor_jobs:
        __total_quantity = job[0]
        __eft = job[1]
        __converted = eve_sde_tools.get_items_list_from_eft(__eft, sde_named_type_ids)
        __converted.update({"quantity": __total_quantity})
        if not (__converted["ship"] is None):
            __product_type_id = __converted["ship"]["type_id"]
            if conveyor_product_type_ids.count(__product_type_id) == 0:
                conveyor_product_type_ids.append(__product_type_id)
                __market_group_id = eve_sde_tools.get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, __product_type_id)
                push_into_conveyor_market_groups(__market_group_id)
                conveyor_scheduled_products.append({
                    "name": __converted["ship"]["name"],
                    "type_id": __product_type_id,
                    "quantity": __total_quantity,
                    "market": __market_group_id
                })
            else:
                __job_dict = next((j for j in conveyor_scheduled_products if j["type_id"] == __product_type_id), None)
                __job_dict["quantity"] += __total_quantity
        for __item_dict in __converted["items"]:
            __product_type_id = __item_dict["type_id"]
            if conveyor_product_type_ids.count(__product_type_id) == 0:
                conveyor_product_type_ids.append(__product_type_id)
                __market_group_id = eve_sde_tools.get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, __product_type_id)
                push_into_conveyor_market_groups(__market_group_id)
                conveyor_scheduled_products.append({
                    "name": __item_dict["name"],
                    "type_id": __product_type_id,
                    "quantity": __total_quantity * __item_dict["quantity"],
                    "market": __market_group_id
                })
            else:
                __job_dict = next((j for j in conveyor_scheduled_products if j["type_id"] == __product_type_id), None)
                __job_dict["quantity"] += __total_quantity * __item_dict["quantity"]
    corp_industry_stat["conveyor_scheduled_products"] = conveyor_scheduled_products

    # выбираем накопленные данные по производству из БД
    if conveyor_product_type_ids:
        db_workflow_industry_jobs = qidb.select_all_rows(
            "SELECT ptid,SUM(cst),SUM(prdcts),mnth "
            "FROM (SELECT "
            "  ecj.ecj_product_type_id AS ptid,"
            "  ecj.ecj_cost AS cst,"
            "  ecj.ecj_runs*coalesce(pi.sdebp_quantity,1) AS prdcts,"
            "  EXTRACT(MONTH FROM ecj.ecj_end_date) AS mnth"
            " FROM qi.esi_corporation_industry_jobs ecj"
            "   LEFT OUTER JOIN qi.eve_sde_blueprint_products pi ON ("
            "     pi.sdebp_activity=1 AND"
            "     pi.sdebp_blueprint_type_id=ecj.ecj_blueprint_type_id AND"
            "     pi.sdebp_product_id=ecj.ecj_product_type_id"
            "   )"
            " WHERE ecj.ecj_activity_id=1 AND"
            "  ecj.ecj_product_type_id=ANY(%s) AND"
            "  ecj.ecj_end_date > (current_date - interval '93' day)"
            ") AS a "
            "WHERE mnth=%s OR mnth=%s OR mnth=%s "
            "GROUP BY 1,4 "
            "ORDER BY 1;",
            conveyor_product_type_ids,
            int(db_current_month[0]),  # january=1, december=12
            int((db_current_month[0]-2+12)%12+1),
            int((db_current_month[0]-3+12)%12+1)
        )
        corp_industry_stat["workflow_industry_jobs"] = [{
            "ptid": wij[0],
            "cost": wij[1],
            "products": wij[2],
            "month": int(wij[3])
        } for wij in db_workflow_industry_jobs]
        del db_workflow_industry_jobs

        # выбираем накопленные данные по производству из БД (за последние 30 дней)
        db_workflow_last_industry_jobs = qidb.select_all_rows(
            "SELECT"
            " ecj.ecj_product_type_id,"
            " SUM(ecj.ecj_runs*coalesce(pi.sdebp_quantity,1)) "
            "FROM qi.esi_corporation_industry_jobs ecj"
            " LEFT OUTER JOIN qi.eve_sde_blueprint_products pi ON ("
            "  pi.sdebp_activity=1 AND"
            "  pi.sdebp_blueprint_type_id=ecj.ecj_blueprint_type_id AND"
            "  pi.sdebp_product_id=ecj.ecj_product_type_id"
            " )"
            "WHERE ecj.ecj_activity_id=1 AND"
            " ecj.ecj_product_type_id=ANY(%s) AND"
            " ecj.ecj_end_date > (current_date - interval '30' day) "
            "GROUP BY 1;",
            conveyor_product_type_ids)
        corp_industry_stat["workflow_last_industry_jobs"] = [{
            "ptid": wij[0],
            "products": wij[1]
        } for wij in db_workflow_last_industry_jobs]
        del db_workflow_last_industry_jobs
    del conveyor_product_type_ids

    return corp_industry_stat


def main():
    qidb = __get_db_connection()
    try:
        module_settings = qidb.load_module_settings(g_module_default_settings, g_module_default_types)
        db_monthly_jobs = qidb.select_all_rows(
            "SELECT wmj_quantity,wmj_eft,wmj_conveyor "
            "FROM workflow_monthly_jobs "
            "WHERE wmj_active;")
        db_factory_containers = qidb.select_all_rows(
            "SELECT wfc_id,wfc_name,wfc_active,wfc_disabled,wfc_station_num "
            "FROM workflow_factory_containers;")

        db_monthly_jobs = [{"eft": wmj[1], "quantity": wmj[0], "conveyor": bool(wmj[2])} for wmj in db_monthly_jobs]
        db_factory_containers = [{"id": wfc[0], "name": wfc[1], "active": wfc[2], "disabled": wfc[3], "station_num": wfc[4]} for wfc in db_factory_containers]

        # работа с параметрами командной строки, получение настроек запуска программы, как то: работа в offline-режиме,
        # имя пилота ранее зарегистрированного и для которого имеется аутентификационный токен, регистрация нового и т.д.
        argv_prms = console_app.get_argv_prms()

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
            offline_mode=argv_prms["offline_mode"])

        authz = interface.authenticate(argv_prms["character_names"][0])
        character_id = authz["character_id"]
        character_name = authz["character_name"]

        sde_type_ids = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "typeIDs")
        sde_inv_names = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "invNames")
        sde_bp_materials = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "blueprints")
        sde_market_groups = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "marketGroups")
        sde_named_type_ids = eve_sde_tools.convert_sde_type_ids(sde_type_ids)

        # удаление из списка чертежей тех, которые не published (надо соединить typeIDs и blueprints, отбросив часть)
        for t in [t for t in sde_type_ids if t in sde_bp_materials.keys() and sde_type_ids[t].get('published')==False]:
            del sde_bp_materials[t]

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

        # Requires role(s): Factory_Manager
        corp_industry_jobs_data = interface.get_esi_paged_data(
            "corporations/{}/industry/jobs/".format(corporation_id))
        print("\n'{}' corporation has {} industry jobs".format(corporation_name, len(corp_industry_jobs_data)))
        sys.stdout.flush()

        # строим данные для генерации отчёта
        corp_industry_stat = __build_industry(
            # настройки и подключение к БД
            qidb,
            module_settings,
            # sde данные, загруженные из .converted_xxx.json файлов
            sde_type_ids,
            sde_bp_materials,
            sde_market_groups,
            sde_named_type_ids,
            # esi данные, загруженные с серверов CCP
            corp_industry_jobs_data)
        eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_industry_stat", corp_industry_stat)
    except:
        print(sys.exc_info())
        sys.exit(1)  # errno.h : EPERM=1 /* Operation not permitted */
    del qidb

    # вывод отчёта на экран
    print("\n'{}' corporation has {} new jobs since last update".format(corporation_name, corp_industry_stat["new_jobs_found"]))
    sys.stdout.flush()

    # для того, чтобы получить названия коробок и в каком ангаре они расположены, надо загрузить
    # данные по ассетам, т.к. только в этих данных можно учитывая иерархию пересчитать коробки
    # в нужном ангаре

    # Requires role(s): Director
    corp_assets_data = interface.get_esi_paged_data(
        "corporations/{}/assets/".format(corporation_id))
    print("\n'{}' corporation has {} assets".format(corporation_name, len(corp_assets_data)))
    sys.stdout.flush()

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
                    raise
            except:
                print(sys.exc_info())
                raise
    print(
        "\n'{}' corporation has offices in {} foreign stations".format(corporation_name, len(foreign_structures_data)))
    if len(foreign_structures_forbidden_ids) > 0:
        print("\n'{}' corporation has offices in {} forbidden stations : {}".format(corporation_name, len(
            foreign_structures_forbidden_ids), foreign_structures_forbidden_ids))
    sys.stdout.flush()

    factories_containers = __get_blueprints_containers(
        module_settings,
        sde_type_ids,
        sde_inv_names,
        corp_assets_data,
        foreign_structures_data,
        corp_ass_names_data
    )
    # обновление данных в БД (названия контейнеров, и первичное автозаполнение)
    for factory_containers in factories_containers:
        station_num = factory_containers["station_num"]
        __actualize_factory_containers(db_factory_containers, factory_containers["containers"], station_num)

        print('\nFound factory station {} with containers in hangars...'.format(factory_containers["station_name"]))
        print('  {} = {}'.format(factory_containers["station_id"], factory_containers["station_name"]))
        print('  blueprint hangars = {}'.format(factory_containers["hangars_filter"]))
        print('  blueprint containers = {}'.format(len(factory_containers["containers"])))
        print('  database containers = {}'.format(len([dfc["id"] for dfc in db_factory_containers if dfc['station_num'] == station_num])))
    sys.stdout.flush()

    # Requires role(s): Director
    corp_blueprints_data = interface.get_esi_paged_data(
        "corporations/{}/blueprints/".format(corporation_id))
    print("\n'{}' corporation has {} blueprints".format(corporation_name, len(corp_blueprints_data)))
    sys.stdout.flush()

    # формирование набора данных для построения отчёта
    corp_manufacturing_scheduler = __get_monthly_manufacturing_scheduler(
        # данные полученные из БД
        db_monthly_jobs,
        db_factory_containers,
        # sde данные загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_named_type_ids,
        sde_bp_materials,
        sde_market_groups,
        # esi данные загруженные с серверов CCP
        corp_blueprints_data,
        corp_industry_jobs_data,
        # данные полученные в результате анализа и перекомпоновки входных списков
        factories_containers
    )
    eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_manufacturing_scheduler", corp_manufacturing_scheduler)

    print('\nFound in {} stations...'.format(len(factories_containers)))
    print('  scheduled blueprints = {}'.format(len(corp_manufacturing_scheduler["scheduled_blueprints"])))
    print('  factory repository = {}'.format(len(corp_manufacturing_scheduler["factory_repository"])))
    print('  factory blueprints = {}'.format(len(corp_manufacturing_scheduler["factory_blueprints"])))
    sys.stdout.flush()

    print("\nBuilding workflow report...")
    sys.stdout.flush()

    render_html_workflow.dump_workflow_into_report(
        # путь, где будет сохранён отчёт
        argv_prms["workspace_cache_files_dir"],
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_market_groups,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_manufacturing_scheduler
    )

    print("\nBuilding industry report...")
    sys.stdout.flush()

    render_html_industry.dump_industry_into_report(
        # путь, где будет сохранён отчёт
        argv_prms["workspace_cache_files_dir"],
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_industry_stat)

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nDone")


if __name__ == "__main__":
    main()
