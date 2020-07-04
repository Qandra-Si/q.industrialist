""" Q.Logist (desktop/mobile)

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
>>> python q_logist.py
"""
import sys
import json

import q_industrialist_settings
import auth_cache
import shared_flow
import eve_esi_tools
import eve_sde_tools
import eve_esi_interface

from render_html import dump_cynonetwork_into_report


# R Initiative 4 Q.Industrialist
g_ri4_client_id = "022ea197e3f2414f913b789e016990c8"
# Application scopes
g_client_scope = ["esi-assets.read_corporation_assets.v1"]  # Requires role(s): Director


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

    # Requires role(s): Director
    corp_assets_data = eve_esi_interface.get_esi_paged_data(
        access_token,
        "corporations/{}/assets/".format(corporation_id),
        "corp_assets")
    print("\n'{}' corporation has {} assets".format(corporation_name, len(corp_assets_data)))
    sys.stdout.flush()

    corp_asset_names_data = []
    corp_ass_cont_ids = eve_esi_tools.get_assets_containers_ids(corp_assets_data)
    if len(corp_ass_cont_ids) > 0:
        # Requires role(s): Director
        corp_asset_names_data = eve_esi_interface.get_esi_data(
            access_token,
            "corporations/{}/assets/names/".format(corporation_id),
            "corp_asset_names",
            json.dumps(corp_ass_cont_ids, indent=0, sort_keys=False))
    print("\n'{}' corporation has {} asset's names".format(corporation_name, len(corp_asset_names_data)))
    sys.stdout.flush()

    # Построение списка модулей и ресуров, которые имеются в распоряжении корпорации и
    # которые предназначены для использования в чертежах
    corp_ass_loc_data = eve_esi_tools.get_corp_ass_loc_data(corp_assets_data)
    eve_esi_interface.dump_json_into_file("corp_ass_loc_data", corp_ass_loc_data)

    dump_cynonetwork_into_report(
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        # esi данные, загруженные с серверов CCP
        corp_asset_names_data,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_ass_loc_data)


if __name__ == "__main__":
    main()
