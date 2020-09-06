""" Q.Industrialist (desktop/mobile)

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
>>> python q_industrialist.py
"""
import sys
import json

import eve_esi_interface as esi

import q_industrialist_settings
import eve_esi_tools
import eve_sde_tools
import console_app
from render_html import dump_industrialist_into_report

from __init__ import __version__


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
        "characters/{}/".format(character_id))
    # Public information about a corporation
    corporation_data = interface.get_esi_data(
        "corporations/{}/".format(character_data["corporation_id"]))

    corporation_id = character_data["corporation_id"]
    corporation_name = corporation_data["name"]
    print("\n{} is from '{}' corporation".format(character_name, corporation_name))
    sys.stdout.flush()

    sde_type_ids = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "typeIDs")
    sde_bp_materials = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "blueprints")
    sde_market_groups = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "marketGroups")

    # Requires: access token
    wallet_data = interface.get_esi_data(
        "characters/{}/wallet/".format(character_id))
    print("\n{} has {} ISK".format(character_name, wallet_data))
    sys.stdout.flush()

    # Requires: access token
    blueprint_data = interface.get_esi_data(
        "characters/{}/blueprints/".format(character_id))
    print("\n{} has {} blueprints".format(character_name, len(blueprint_data)))
    sys.stdout.flush()

    # Requires: access token
    assets_data = interface.get_esi_data(
        "characters/{}/assets/".format(character_id))
    print("\n{} has {} assets".format(character_name, len(assets_data)))
    sys.stdout.flush()

    # Построение названий контейнеров, которые переименовал персонаж и храних в своих asset-ах
    asset_names_data = []
    ass_named_ids = eve_esi_tools.get_assets_named_ids(assets_data)
    if len(ass_named_ids) > 0:
        # Requires: access token
        asset_names_data = interface.get_esi_data(
            "characters/{}/assets/names/".format(character_id),
            json.dumps(ass_named_ids, indent=0, sort_keys=False))
    print("\n{} has {} asset's names".format(character_name, len(asset_names_data)))
    sys.stdout.flush()

    # Requires: access token
    fittings_data = interface.get_esi_data(
        "characters/{}/fittings/".format(character_id))
    print("\n{} has {} fittings".format(character_name, len(fittings_data)))
    sys.stdout.flush()

    # Requires: access token
    contracts_data = []  # interface.get_esi_data(
    #   "characters/{}/contracts/".format(character_id))
    # print("\n{} has {} contracts".format(character_name, len(contracts_data)))
    # sys.stdout.flush()

    # Requires role(s): Factory_Manager
    corp_industry_jobs_data = interface.get_esi_paged_data(
        "corporations/{}/industry/jobs/".format(corporation_id))
    print("\n'{}' corporation has {} industry jobs".format(corporation_name, len(corp_industry_jobs_data)))
    sys.stdout.flush()

    # Requires role(s): Director
    corp_assets_data = interface.get_esi_paged_data(
        "corporations/{}/assets/".format(corporation_id))
    print("\n'{}' corporation has {} assets".format(corporation_name, len(corp_assets_data)))
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

    # Requires role(s): Director
    corp_blueprints_data = interface.get_esi_paged_data(
        "corporations/{}/blueprints/".format(corporation_id))
    print("\n'{}' corporation has {} blueprints".format(corporation_name, len(corp_blueprints_data)))
    sys.stdout.flush()

    # Построение иерархических списков БПО и БПЦ, хранящихся в корпоративных ангарах
    corp_bp_loc_data = eve_esi_tools.get_corp_bp_loc_data(corp_blueprints_data, corp_industry_jobs_data)
    eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_bp_loc_data", corp_bp_loc_data)

    # Построение списка модулей и ресурсов, которые используются в производстве
    materials_for_bps = eve_sde_tools.get_materials_for_blueprints(sde_bp_materials)

    # Построение списка модулей и ресуров, которые имеются в распоряжении корпорации и
    # которые предназначены для использования в чертежах
    corp_ass_loc_data = eve_esi_tools.get_corp_ass_loc_data(corp_assets_data, containers_filter=None)
    eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_ass_loc_data", corp_ass_loc_data)

    # Поиск контейнеров, которые участвуют в производстве
    print("\nSearching industrialist containter and station ids...")
    sys.stdout.flush()

    stock_all_loc_ids = [n["item_id"] for n in corp_ass_names_data if n['name'] == "..stock ALL"]
    # for id in stock_all_loc_ids:
    #     print('  {} = {}'.format(id, next((n["name"] for n in corp_ass_names_data if n['item_id'] == id), None)))
    blueprint_loc_ids = [n["item_id"] for n in corp_ass_names_data]
    # for id in blueprint_loc_ids:
    #     print('  {} = {}'.format(id, next((n["name"] for n in corp_ass_names_data if n['item_id'] == id), None)))
    blueprint_station_ids = []
    # TODO: добавить сюда логику, аналогичную q_conveyor.py

    print("\nBuilding report...")
    sys.stdout.flush()

    dump_industrialist_into_report(
        # путь, где будет сохранён отчёт
        argv_prms["workspace_cache_files_dir"],
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        # esi данные, загруженные с серверов CCP
        wallet_data,
        blueprint_data,
        assets_data,
        asset_names_data,
        corp_assets_tree,
        corp_industry_jobs_data,
        corp_ass_names_data,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_ass_loc_data,
        corp_bp_loc_data,
        stock_all_loc_ids,
        exclude_loc_ids,
        blueprint_loc_ids,
        blueprint_station_ids)

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nDone")


if __name__ == "__main__":
    main()
