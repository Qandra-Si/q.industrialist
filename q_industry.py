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
import console_app
import render_html_industry

from __init__ import __version__


def __get_db_connection():
    qidb = db.QIndustrialistDatabase("workflow", debug=True)
    qidb.connect(q_industrialist_settings.g_database)
    return qidb


def main():
    qidb = __get_db_connection()
    db_conveyor_jobs = qidb.select_all_rows(
        "SELECT wmj_quantity,wmj_eft "
        "FROM workflow_monthly_jobs "
        "WHERE wmj_active AND wmj_conveyor;")

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

    # Requires role(s): Factory_Manager
    corp_industry_jobs_data = interface.get_esi_paged_data(
        "corporations/{}/industry/jobs/".format(corporation_id))
    print("\n'{}' corporation has {} industry jobs".format(corporation_name, len(corp_industry_jobs_data)))
    sys.stdout.flush()

    # сохраняем данные по производству в БД
    wij = db.QWorkflowIndustryJobs(qidb)
    new_jobs_found = wij.actualize(corp_industry_jobs_data, sde_bp_materials)
    print("\n'{}' corporation has {} new jobs since last update".format(corporation_name, new_jobs_found))
    sys.stdout.flush()
    del wij

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
                conveyor_scheduled_products.append({
                    "name": __converted["ship"]["name"],
                    "type_id": __product_type_id,
                    "quantity": __total_quantity
                })
            else:
                __job_dict = next((j for j in conveyor_scheduled_products if j["type_id"] == __product_type_id), None)
                __job_dict["quantity"] += __total_quantity
        for __item_dict in __converted["items"]:
            __product_type_id = __item_dict["type_id"]
            if conveyor_product_type_ids.count(__product_type_id) == 0:
                conveyor_product_type_ids.append(__product_type_id)
                conveyor_scheduled_products.append({
                    "name": __item_dict["name"],
                    "type_id": __product_type_id,
                    "quantity": __total_quantity * __item_dict["quantity"]
                })
            else:
                __job_dict = next((j for j in conveyor_scheduled_products if j["type_id"] == __product_type_id), None)
                __job_dict["quantity"] += __total_quantity * __item_dict["quantity"]

    # выбираем накопленные данные по производству из БД
    workflow_industry_jobs = qidb.select_all_rows(
        "SELECT"
        " wij_product_tid AS ptid,"
        " sum(wij_cost) AS cost,"
        " sum(wij_quantity) AS products,"
        " wij_bp_tid AS bptid,"
        " wij_bp_lid AS bplid,"
        " wij_out_lid AS olid,"
        " wij_facility_id AS fid "
        "FROM workflow_industry_jobs "
        "WHERE wij_activity_id=1 AND wij_product_tid=ANY(%s) "
        "GROUP BY 1,4,5,6,7 "
        "ORDER BY 1;",
        conveyor_product_type_ids
        )
    db_workflow_industry_jobs = [{"ptid": wij[0], "cost": wij[1], "products": wij[2], "bptid": wij[3], "bplid": wij[4], "olid": wij[5], "fid": wij[6]} for wij in workflow_industry_jobs]
    del workflow_industry_jobs

    print("\nBuilding report...")
    sys.stdout.flush()

    render_html_industry.dump_industry_into_report(
        # путь, где будет сохранён отчёт
        argv_prms["workspace_cache_files_dir"],
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        db_workflow_industry_jobs,
        conveyor_scheduled_products
    )

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    del qidb
    print("\nDone")


if __name__ == "__main__":
    main()
