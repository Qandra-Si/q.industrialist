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
import getopt
import os
import json
import requests

import q_industrialist_settings
import eve_esi_tools
import eve_sde_tools

import eve_esi_interface as esi
from render_html import dump_assets_tree_into_report


def main(argv):
    character_name = None  # for example : Qandra Si
    signup_new_character = False
    exit_or_wrong_getopt = None
    try:
        opts, args = getopt.getopt(argv, "hp:s", ["help", "pilot=", "signup"])
    except getopt.GetoptError:
        exit_or_wrong_getopt = 2
    if exit_or_wrong_getopt is None:
        for opt, arg in opts:
            if opt in ('-h', "--help"):
                exit_or_wrong_getopt = 0
                break
            elif opt in ("-p", "--pilot"):
                character_name = arg
            elif opt in ("-s", "--signup"):
                signup_new_character = True
        if (character_name is None) == (signup_new_character == False):  # д.б. либо указано имя, либо флаг регистрации
            exit_or_wrong_getopt = 0
    if not (exit_or_wrong_getopt is None):
        print('Usage: ' + os.path.basename(__file__) + ' --pilot=<name>')
        print('    or ' + os.path.basename(__file__) + ' --signup')
        print('Example: ' + os.path.basename(__file__) + ' --pilot="Qandra Si"')
        sys.exit(exit_or_wrong_getopt)

    auth = esi.EveESIAuth('{}/.auth_cache'.format(q_industrialist_settings.g_tmp_directory, debug=True))
    client = esi.EveESIClient(auth, debug=False, logger=True, user_agent=q_industrialist_settings.g_user_agent)
    config = esi.EveOnlineConfig(
        q_industrialist_settings.g_client_scope,
        cache_dir='{}/.q_industrialist'.format(q_industrialist_settings.g_tmp_directory),
        offline_mode=q_industrialist_settings.g_offline_mode)
    interface = esi.EveOnlineInterface(config, client)

    authz = interface.authenticate(character_name)
    #access_token = authz["access_token"]
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
    return

    sde_type_ids = eve_sde_tools.read_converted("typeIDs")
    sde_inv_names = eve_sde_tools.read_converted("invNames")
    sde_inv_items = eve_sde_tools.read_converted("invItems")

    # Requires role(s): Director
    corp_assets_data = eve_esi_interface.get_esi_paged_data(
        access_token,
        "corporations/{}/assets/".format(corporation_id))
    print("\n'{}' corporation has {} assets".format(corporation_name, len(corp_assets_data)))
    sys.stdout.flush()

    # Получение названий контейнеров, станций, и т.п. - всё что переименовывается ingame
    corp_ass_names_data = []
    corp_ass_named_ids = eve_esi_tools.get_assets_named_ids(corp_assets_data)
    if len(corp_ass_named_ids) > 0:
        # Requires role(s): Director
        corp_ass_names_data = eve_esi_interface.get_esi_data(
            access_token,
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
                universe_structure_data = eve_esi_interface.get_esi_data(
                    access_token,
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
    eve_esi_interface.dump_debug_into_file("corp_assets_tree", corp_assets_tree)

    # Построение списка модулей и ресуров, которые имеются в распоряжении корпорации и
    # которые предназначены для использования в чертежах
    corp_ass_loc_data = eve_esi_tools.get_corp_ass_loc_data(corp_assets_data)
    eve_esi_interface.dump_debug_into_file("corp_ass_loc_data", corp_ass_loc_data)

    # Построение дерева asset-ов:
    print("\nBuilding assets tree report...")
    sys.stdout.flush()
    dump_assets_tree_into_report(
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_inv_names,
        sde_inv_items,
        # esi данные, загруженные с серверов CCP
        corp_assets_data,
        corp_ass_names_data,
        foreign_structures_data,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_ass_loc_data,
        corp_assets_tree)

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nDone")


if __name__ == "__main__":
    main(sys.argv[1:])
