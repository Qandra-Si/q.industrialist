""" Q.Industry (desktop/mobile)

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

>>> python eve_sde_tools.py
>>> python q_industry.py --pilot="Qandra Si" --online --cache_dir=~/.q_industrialist

Requires application scopes:
    * esi-industry.read_corporation_jobs.v1 - Requires role(s): Factory_Manager

"""
import sys

import eve_esi_interface as esi
import postgresql_interface as db

import q_industrialist_settings
import eve_sde_tools
import eve_esi_tools
import console_app
import render_html_industry

from datetime import datetime, date, timedelta

from __init__ import __version__


g_module_default_settings = {
    "factory:conveyor_containers": [1032846295901, 1033675076928]
}


def __get_db_connection():
    qidb = db.QIndustrialistDatabase("workflow", debug=True)
    qidb.connect(q_industrialist_settings.g_database)
    return qidb


def __build_industry(
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
        "conveyor_market_groups": {}
    }

    def push_into_conveyor_market_groups(__market_group_id):
        if corp_industry_stat["conveyor_market_groups"].get(str(__market_group_id), None) is None:
            corp_industry_stat["conveyor_market_groups"].update({
                str(__market_group_id): eve_sde_tools.get_market_group_name_by_id(sde_market_groups, __market_group_id)
            })

    # подключаемся к БД
    qidb = __get_db_connection()
    try:
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
        db_workflow_industry_jobs = qidb.select_all_rows(
            "SELECT ptid,sum(cst),sum(prdcts),mnth "
            "FROM (SELECT "
            "  wij_product_tid AS ptid,"
            "  wij_cost AS cst,"
            "  wij_quantity AS prdcts,"
            "  EXTRACT(MONTH FROM wij_end_date) AS mnth"
            " FROM qi.workflow_industry_jobs"
            " WHERE wij_activity_id=1 AND wij_bp_lid=ANY(%s) AND wij_product_tid=ANY(%s)"
            ") AS a "
            "WHERE mnth>=(%s-2) "
            "GROUP BY 1,4 "
            "ORDER BY 1;",
            g_module_default_settings["factory:conveyor_containers"],
            conveyor_product_type_ids,
            db_current_month[0])
        corp_industry_stat["workflow_industry_jobs"] = [{
            "ptid": wij[0],
            "cost": wij[1],
            "products": wij[2],
            "month": int(wij[3])
        } for wij in db_workflow_industry_jobs]
        del db_workflow_industry_jobs
        del conveyor_product_type_ids
    finally:
        # отключение от БД
        del qidb

    return corp_industry_stat


def __build_possible_t2_products(
        esi_interface,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups):
    # автоматический расчёт плана производства на следующий месяц (или для корректировки текущего)
    possible_t2_products = {
        "products": [],
        "market_groups": {},
        "materials": {}
    }
    __now = datetime.now()

    def push_into_market_groups(__market_group_id):
        if possible_t2_products["market_groups"].get(str(__market_group_id), None) is None:
            possible_t2_products["market_groups"].update({
                str(__market_group_id): eve_sde_tools.get_market_group_name_by_id(sde_market_groups, __market_group_id)
            })

    def push_into_materials(__product_type_id):
        if possible_t2_products["materials"].get(str(__product_type_id), None) is None:
            __product183 = {}

            # Public information about market prices
            __markets_theforge_orders_data186 = esi_interface.get_esi_paged_data(
                "markets/{}/orders/?type_id={}&order_type=all".format(10000002, __product_type_id),
                fully_trust_cache=True
                )

            # Public information about market prices
            __markets_theforge_history_data190 = esi_interface.get_esi_data(
                "markets/{}/history/?type_id={}".format(10000002, __product_type_id),
                fully_trust_cache=True)

            # 60003760: "Jita IV - Moon 4 - Caldari Navy Assembly Plant"
            __jita_sell194 = [o["price"] for o in __markets_theforge_orders_data186 if (o["location_id"] == 60003760) and not o["is_buy_order"]]
            __jita_buy195 = [o["price"] for o in __markets_theforge_orders_data186 if (o["location_id"] == 60003760) and o["is_buy_order"]]
            if __jita_sell194:
                __product183.update({"jita_sell": min(__jita_sell194)})
            if __jita_buy195:
                __product183.update({"jita_buy": max(__jita_buy195)})

            __theforge_market201 = [{"average": h["average"], "volume": h["volume"]}
                               for h in __markets_theforge_history_data190 if (__now-datetime.fromisoformat(h["date"])).days <= 31]
            __month_theforge_volume203 = sum([h["volume"] for h in __theforge_market201])  # сумма (кол-во сделок по дням)
            __month_theforge_average_isk204 = sum([h["average"]*h["volume"] for h in __theforge_market201])  # средний объём isk за последний месяц
            __product183.update({"month": {
                "sum_volume": __month_theforge_volume203,
                "avg_isk": __month_theforge_average_isk204
            }})

            possible_t2_products["materials"].update({
                str(__product_type_id): __product183
            })
            sys.stdout.flush()

    # Public information about market prices
    markets_theforge_types_data = esi_interface.get_esi_paged_data(
        "markets/{}/types/".format(10000002))
    print("\n'{}' region has {} product's market positions".format('The Forge', len(markets_theforge_types_data)))
    sys.stdout.flush()

    for p in sde_type_ids.items():
        __p_dict = p[1]
        if ("published" in __p_dict) and not __p_dict["published"]:
            continue
        if ("metaGroupID" in __p_dict) and (__p_dict["metaGroupID"] == 2):
            __product_type_id = int(p[0])
            __product_name = __p_dict["name"]["en"] if "name" in __p_dict else str(__product_type_id)
            if (__product_name == "unused blueprint type") or (__product_name[-9:] == "Blueprint"):
                continue  # на самом деле следует проверить groupID продукта и categoryID группы, пропустив чертежи
            __blueprint_type_id, __materials = eve_sde_tools.get_blueprint_type_id_by_product_id(__product_type_id, sde_bp_materials)
            if __blueprint_type_id is None:
                continue
            __market_group_id = eve_sde_tools.get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, __product_type_id)
            if not (__market_group_id is None):
                push_into_market_groups(__market_group_id)
            possible_t2_products["products"].append({
                "type_id": __product_type_id,
                "name": __product_name,
                "active_orders": __product_type_id in markets_theforge_types_data,
                "materials": __materials["activities"]["manufacturing"]["materials"],
                "market": __market_group_id
            })
            for m in __materials["activities"]["manufacturing"]["materials"]:
                push_into_materials(m["typeID"])

    for product in possible_t2_products["products"]:
        if product["active_orders"]:
            push_into_materials(product["type_id"])

    return possible_t2_products


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
    sde_market_groups = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "marketGroups")
    sde_named_type_ids = eve_sde_tools.convert_sde_type_ids(sde_type_ids)

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

    possible_t2_products = __build_possible_t2_products(
        interface,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups
    )
    eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "possible_t2_products", possible_t2_products)

    # строим данные для генерации отчёта
    corp_industry_stat = __build_industry(
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        sde_named_type_ids,
        # esi данные, загруженные с серверов CCP
        corp_industry_jobs_data)
    eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_industry_stat", corp_industry_stat)

    # вывод отчёта на экран
    print("\n'{}' corporation has {} new jobs since last update".format(corporation_name, corp_industry_stat["new_jobs_found"]))
    print("'{}' market has {} / {} active orders for T2-products".format('The Forge', len([p for p in possible_t2_products["products"] if p["active_orders"]]), len(possible_t2_products["products"])))
    sys.stdout.flush()

    print("\nBuilding report...")
    sys.stdout.flush()

    render_html_industry.dump_industry_into_report(
        # путь, где будет сохранён отчёт
        argv_prms["workspace_cache_files_dir"],
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_industry_stat,
        possible_t2_products)

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nDone")


if __name__ == "__main__":
    main()
