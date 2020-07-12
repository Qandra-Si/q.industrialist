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

import q_industrialist_settings
import auth_cache
import shared_flow
import eve_esi_tools
import eve_sde_tools
import eve_esi_interface

from render_html import dump_into_report


# R Initiative 4 Q.Industrialist
g_ri4_client_id = "022ea197e3f2414f913b789e016990c8"
# Application scopes
g_client_scope = ["esi-characters.read_blueprints.v1",  # Requires: access token
                  "esi-wallet.read_character_wallet.v1",  # Requires: access token
                  "esi-assets.read_assets.v1",  # Requires: access token
                  # "esi-contracts.read_character_contracts.v1",  # Requires: access token
                  "esi-fittings.read_fittings.v1",  # Requires: access token
                  "esi-assets.read_corporation_assets.v1",  # Requires role(s): Director
                  "esi-corporations.read_blueprints.v1",  # Requires role(s): Director
                  "esi-industry.read_corporation_jobs.v1",  # Requires role(s): Factory_Manager
                  "esi-universe.read_structures.v1"  # Requires: access token
                 ]


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

    # Requires: access token
    wallet_data = eve_esi_interface.get_esi_data(
        access_token,
        "characters/{}/wallet/".format(character_id),
        "wallet")
    print("\n{} has {} ISK".format(character_name, wallet_data))
    sys.stdout.flush()

    # Requires: access token
    blueprint_data = eve_esi_interface.get_esi_data(
        access_token,
        "characters/{}/blueprints/".format(character_id),
        "blueprints")
    print("\n{} has {} blueprints".format(character_name, len(blueprint_data)))
    sys.stdout.flush()

    # Requires: access token
    assets_data = eve_esi_interface.get_esi_data(
        access_token,
        "characters/{}/assets/".format(character_id),
        "assets")
    print("\n{} has {} assets".format(character_name, len(assets_data)))
    sys.stdout.flush()

    # Построение названий контейнеров, которые переименовал персонаж и храних в своих asset-ах
    asset_names_data = []
    ass_named_ids = eve_esi_tools.get_assets_named_ids(assets_data)
    if len(ass_named_ids) > 0:
        # Requires: access token
        asset_names_data = eve_esi_interface.get_esi_data(
            access_token,
            "characters/{}/assets/names/".format(character_id),
            "assets_names",
            json.dumps(ass_named_ids, indent=0, sort_keys=False))
    print("\n{} has {} asset's names".format(character_name, len(asset_names_data)))
    sys.stdout.flush()

    # Requires: access token
    fittings_data = eve_esi_interface.get_esi_data(
        access_token,
        "characters/{}/fittings/".format(character_id),
        "fittings")
    print("\n{} has {} fittings".format(character_name, len(fittings_data)))
    sys.stdout.flush()

    # Requires: access token
    # contracts_data = eve_esi_interface.get_esi_data(
    #   access_token,
    #   "characters/{}/contracts/".format(character_id),
    #   "contracts")
    # print("\n{} has {} contracts".format(character_name, len(contracts_data)))
    # sys.stdout.flush()

    # Requires role(s): Factory_Manager
    corp_industry_jobs_data = eve_esi_interface.get_esi_paged_data(
        access_token,
        "corporations/{}/industry/jobs/".format(corporation_id),
        "corp_industry_jobs")
    print("\n'{}' corporation has {} industry jobs".format(corporation_name, len(corp_industry_jobs_data)))
    sys.stdout.flush()

    # Requires role(s): Director
    corp_assets_data = eve_esi_interface.get_esi_paged_data(
        access_token,
        "corporations/{}/assets/".format(corporation_id),
        "corp_assets")
    print("\n'{}' corporation has {} assets".format(corporation_name, len(corp_assets_data)))
    sys.stdout.flush()

    corp_ass_names_data = []
    corp_ass_named_ids = eve_esi_tools.get_assets_named_ids(corp_assets_data)
    if len(corp_ass_named_ids) > 0:
        # Requires role(s): Director
        corp_ass_names_data = eve_esi_interface.get_esi_data(
            access_token,
            "corporations/{}/assets/names/".format(corporation_id),
            "corp_ass_names",
            json.dumps(corp_ass_named_ids, indent=0, sort_keys=False))
    print("\n'{}' corporation has {} custom asset's names".format(corporation_name, len(corp_ass_names_data)))
    sys.stdout.flush()

    # Requires role(s): Director
    corp_blueprints_data = eve_esi_interface.get_esi_paged_data(
        access_token,
        "corporations/{}/blueprints/".format(corporation_id),
        "corp_blueprints")
    print("\n'{}' corporation has {} blueprints".format(corporation_name, len(corp_blueprints_data)))
    sys.stdout.flush()

    # Построение иерархических списков БПО и БПЦ, хранящихся в корпоративных ангарах
    corp_bp_loc_data = eve_esi_tools.get_corp_bp_loc_data(corp_blueprints_data, corp_industry_jobs_data)
    eve_esi_interface.dump_json_into_file("corp_bp_loc_data", corp_bp_loc_data)

    # Построение списка модулей и ресурсов, которые используются в производстве
    materials_for_bps = eve_sde_tools.get_materials_for_blueprints(sde_bp_materials)

    # Построение списка модулей и ресуров, которые имеются в распоряжении корпорации и
    # которые предназначены для использования в чертежах
    corp_ass_loc_data = eve_esi_tools.get_corp_ass_loc_data(
        corp_assets_data,
        [1032950982419] if q_industrialist_settings.g_adopt_for_ri4 else None)
    eve_esi_interface.dump_json_into_file("corp_ass_loc_data", corp_ass_loc_data)

    print("\nBuilding report...")
    sys.stdout.flush()

    dump_into_report(
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        # esi данные, загруженные с серверов CCP
        wallet_data,
        blueprint_data,
        assets_data,
        asset_names_data,
        corp_ass_names_data,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_ass_loc_data,
        corp_bp_loc_data)


if __name__ == "__main__":
    main()
