""" Q.BPOs (desktop/mobile)

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
>>> python q_bpos.py
"""
import sys
import time
import tzlocal

import q_industrialist_settings
import auth_cache
import shared_flow
import eve_sde_tools
import eve_esi_interface
import render_html

from datetime import datetime


# R Initiative 4 Q.Industrialist
g_ri4_client_id = "022ea197e3f2414f913b789e016990c8"
# Application scopes
g_client_scope = ["esi-assets.read_corporation_assets.v1",  # Requires role(s): Director
                  "esi-corporations.read_blueprints.v1"  # Requires role(s): Director
                 ]
# Current timezone offset                 ]
g_local_timezone = tzlocal.get_localzone()


def main():
    global g_client_scope
    cache = auth_cache.read_cache()
    if not q_industrialist_settings.g_offline_mode:
        if not ('access_token' in cache) or not ('refresh_token' in cache) or not ('expired' in cache):
            cache = shared_flow.auth(g_client_scope)
        elif not ('scope' in cache) or not auth_cache.verify_auth_scope(cache, g_client_scope):
            cache = shared_flow.auth(g_client_scope, cache["client_id"])
        elif auth_cache.is_timestamp_expired(int(cache["expired"])):
            cache = shared_flow.re_auth(g_client_scope, cache)
    else:
        if not ('access_token' in cache):
            print("There is no way to continue working offline.")
            return

    access_token = cache["access_token"]
    character_id = cache["character_id"]
    character_name = cache["character_name"]

    # Public information about a character
    character_data = eve_esi_interface.get_esi_data(
        access_token,
        "characters/{}/".format(character_id),
        "character")
    # Public information about a corporation
    corporation_data = eve_esi_interface.get_esi_data(
        access_token,
        "corporations/{}/".format(character_data["corporation_id"]),
        "corporation")
    print("\n{} is from '{}' corporation".format(character_name, corporation_data["name"]))
    sys.stdout.flush()

    corporation_id = character_data["corporation_id"]
    corporation_name = corporation_data["name"]

    sde_type_ids = eve_sde_tools.read_converted("typeIDs")
    sde_bp_materials = eve_sde_tools.read_converted("blueprints")
    sde_market_groups = eve_sde_tools.read_converted("marketGroups")
    sde_icon_ids = eve_sde_tools.read_converted("iconIDs")

    # Requires role(s): Director
    corp_assets_data = eve_esi_interface.get_esi_paged_data(
        access_token,
        "corporations/{}/assets/".format(corporation_id),
        "corp_assets")
    print("\n'{}' corporation has {} assets".format(corporation_name, len(corp_assets_data)))
    sys.stdout.flush()

    # Requires role(s): Director
    corp_blueprints_data = eve_esi_interface.get_esi_paged_data(
        access_token,
        "corporations/{}/blueprints/".format(corporation_id),
        "corp_blueprints")
    print("\n'{}' corporation has {} blueprints".format(corporation_name, len(corp_blueprints_data)))
    sys.stdout.flush()

    # Построение дерева merket-групп с элементами, в виде:
    # { group1: {items:[sub1,sub2,...]},
    #   group2: {items:[sub3],parent_id} }
    market_groups_tree = eve_sde_tools.get_market_groups_tree(sde_market_groups)
    eve_esi_interface.dump_json_into_file("market_groups_tree", market_groups_tree)

    print("\nBuilding report...")
    sys.stdout.flush()

    found_blueprints = []
    glf = open('{tmp}/corp_bpo.csv'.format(tmp=q_industrialist_settings.g_tmp_directory), "wt+", encoding='utf8')
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

    glf = open('{tmp}/corp_absent_bpo.csv'.format(tmp=q_industrialist_settings.g_tmp_directory), "wt+", encoding='utf8')
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

    render_html.dump_bpos_into_report(
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


if __name__ == "__main__":
    main()
