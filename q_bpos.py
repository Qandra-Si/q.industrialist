""" Q.BPOs (desktop/mobile)

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
$ python q_bpos.py --pilot="Qandra Si" --online --cache_dir=~/.q_industrialist

Required application scopes:
    * esi-assets.read_corporation_assets.v1 - Requires role(s): Director
    * esi-corporations.read_blueprints.v1 - Requires role(s): Director
"""
import sys
import time
import tzlocal
from datetime import datetime

import eve_esi_interface as esi

import eve_esi_tools
import eve_sde_tools
import console_app
import render_html_bpos
import q_industrialist_settings

from __init__ import __version__


# Current timezone offset                 ]
g_local_timezone = tzlocal.get_localzone()


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
        q_industrialist_settings.g_client_id,
        keep_alive=True,
        debug=argv_prms["verbose_mode"],
        logger=True,
        user_agent='Q.Industrialist v{ver}'.format(ver=__version__),
        restrict_tls13=q_industrialist_settings.g_client_restrict_tls13)
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
    sde_bp_materials = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "blueprints")
    sde_market_groups = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "marketGroups")
    sde_icon_ids = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "iconIDs")

    # удаление из списка чертежей тех, которые не published (надо соединить typeIDs и blueprints, отбросив часть)
    for t in [t for t in sde_type_ids if t in sde_bp_materials.keys() and sde_type_ids[t].get('published')==False]:
        del sde_bp_materials[t]

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

    # Построение дерева market-групп с элементами, в виде:
    # { group1: {items:[sub1,sub2,...]},
    #   group2: {items:[sub3],parent_id} }
    market_groups_tree = eve_sde_tools.get_market_groups_tree(sde_market_groups)
    eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "market_groups_tree", market_groups_tree)

    print("\nBuilding report...")
    sys.stdout.flush()

    found_blueprints = []
    glf = open('{dir}/corp_bpo.csv'.format(dir=argv_prms["workspace_cache_files_dir"]), "wt+", encoding='utf8')
    try:
        glf.write('Blueprint\tBase Price\tMaterial Efficiency\tTime Efficiency\n')
        for a in corp_assets_data:
            if not (str(a["type_id"]) in sde_bp_materials):
                continue
            if ("is_blueprint_copy" in a) and a["is_blueprint_copy"]:
                continue
            item_id = a["item_id"]
            blueprint = None
            for b in corp_blueprints_data:
                if b["item_id"] == item_id:
                    blueprint = b
                    break
            if blueprint is None:
                continue
            type_id = sde_type_ids[str(a["type_id"])]
            glf.write('{nm}\t{prc}\t{me}\t{te}\n'.format(
                nm=type_id["name"]["en"],
                prc=type_id["basePrice"] if "basePrice" in type_id else "",
                me=blueprint["material_efficiency"],
                te=blueprint["time_efficiency"]
            ))
            found_blueprints.append(int(a["type_id"]))
        glf.write('\nGenerated {}'.format(datetime.fromtimestamp(time.time(), g_local_timezone).strftime('%a, %d %b %Y %H:%M:%S %z')))
    finally:
        glf.close()

    glf = open('{dir}/corp_absent_bpo.csv'.format(dir=argv_prms["workspace_cache_files_dir"]), "wt+", encoding='utf8')
    try:
        glf.write('Blueprint\tBase Price\tPresent\tManufacturing Impossible\tAbsent Materials\n')
        bpo_keys = sde_bp_materials.keys()
        for tid in bpo_keys:
            type_id = int(tid)
            sde_type_id = sde_type_ids[str(type_id)]
            found = next((True for b in found_blueprints if b == type_id), False)
            glf.write('{nm}\t{prc}\t{fnd}\t{impsbl}\t{absnt}\n'.format(
                nm=sde_type_id["name"]["en"],
                prc=sde_type_id["basePrice"] if "basePrice" in sde_type_id else "",
                fnd="yes" if found else "no",
                impsbl="yes" if not ("activities" in sde_bp_materials[tid]) or not ("manufacturing" in sde_bp_materials[tid]["activities"]) else "no",
                absnt="yes" if not ("activities" in sde_bp_materials[tid]) or not ("manufacturing" in sde_bp_materials[tid]["activities"]) or not ("materials" in sde_bp_materials[tid]["activities"]["manufacturing"]) else "no"
            ))
        glf.write('\nGenerated {}'.format(datetime.fromtimestamp(time.time(), g_local_timezone).strftime('%a, %d %b %Y %H:%M:%S %z')))
    finally:
        glf.close()

    print("\nBuilding BPOs report...")
    sys.stdout.flush()
    render_html_bpos.dump_bpos_into_report(
        # путь, где будет сохранён отчёт
        argv_prms["workspace_cache_files_dir"],
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_market_groups,
        sde_icon_ids,
        sde_bp_materials,
        # esi данные, загруженные с серверов CCP
        corp_assets_data,
        corp_blueprints_data,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        market_groups_tree
    )

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nDone")


if __name__ == "__main__":
    main()
