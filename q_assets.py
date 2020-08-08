""" Q.Assets (desktop/mobile)

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
>>> python q_assets.py
"""
import sys
import json

import requests

import q_industrialist_settings
import auth_cache
import shared_flow
import eve_esi_tools
import eve_sde_tools
import eve_esi_interface

from render_html import dump_assets_tree_into_report


# Application scopes
g_client_scope = ["esi-assets.read_corporation_assets.v1",  # Requires role(s): Director
                  "esi-universe.read_structures.v1"  # Requires: access token
                 ]


# type_id - тип требуемых данных
#  * None : корневой, т.е. данные по текущей локации маршрута циносети
#  * <number> : значение type_id, поиск которого осуществляется (солнечная система, или топляк)
#               при type_id > 0 поиск осуществляется вверх по дереву
#               при type_id < 0 поиск осуществляется вниз по дереву
def get_cyno_solar_system_details(location_id, corp_assets_tree, subtype=None):
    if not (str(location_id) in corp_assets_tree):
        return None
    loc_dict = corp_assets_tree[str(location_id)]
    if subtype is None:
        if "location_id" in loc_dict: # иногда ESI присылает содержимое контейнеров, которые исчезают из ангаров, кораблей и звёздных систем
            solar_system_id = get_cyno_solar_system_details(
                loc_dict["location_id"],
                corp_assets_tree,
                -5  # Solar System (поиск вниз по дереву)
            )
        else:
            solar_system_id = None
        badger_ids = get_cyno_solar_system_details(location_id, corp_assets_tree, 648)  # Badger
        venture_ids = get_cyno_solar_system_details(location_id, corp_assets_tree, 32880)  # Venture
        liquid_ozone_ids = get_cyno_solar_system_details(location_id, corp_assets_tree, 16273)  # Liquid Ozone
        indus_cyno_gen_ids = get_cyno_solar_system_details(location_id, corp_assets_tree, 52694)  # Industrial Cynosural Field Generator
        exp_cargohold_ids = get_cyno_solar_system_details(location_id, corp_assets_tree, 1317)  # Expanded Cargohold I
        cargohold_rigs_ids = get_cyno_solar_system_details(location_id, corp_assets_tree, 31117)  # Small Cargohold Optimization I
        nitrogen_isotope_ids = get_cyno_solar_system_details(location_id, corp_assets_tree, 17888)  # Nitrogen Isotopes
        hydrogen_isotope_ids = get_cyno_solar_system_details(location_id, corp_assets_tree, 17889)  # Hydrogen Isotopes
        return {"solar_system": solar_system_id,
                "badger": badger_ids,
                "venture": venture_ids,
                "liquid_ozone": liquid_ozone_ids,
                "indus_cyno_gen": indus_cyno_gen_ids,
                "exp_cargohold": exp_cargohold_ids,
                "cargohold_rigs": cargohold_rigs_ids,
                "nitrogen_isotope": nitrogen_isotope_ids,
                "hydrogen_isotope": hydrogen_isotope_ids}
    else:
        type_id = loc_dict["type_id"] if "type_id" in loc_dict else None
        if not (type_id is None) and (type_id == abs(subtype)):  # нашли
            return location_id  # выдаём как item_id
        if subtype < 0:
            if "location_id" in loc_dict:
                return get_cyno_solar_system_details(loc_dict["location_id"], corp_assets_tree, subtype)
            else:
                return None
        else:  # subtype > 0
            result = []
            items = loc_dict["items"] if "items" in loc_dict else None
            if not (items is None):
                for i in items:
                    item_ids = get_cyno_solar_system_details(i, corp_assets_tree, subtype)
                    if not (item_ids is None):
                        if isinstance(item_ids, list):
                            result.extend(item_ids)
                        else:
                            result.append(item_ids)
            if len(result) > 0:
                return result
            else:
                return None
    return None


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
    sde_inv_names = eve_sde_tools.read_converted("invNames")
    sde_inv_items = eve_sde_tools.read_converted("invItems")

    # Requires role(s): Director
    corp_assets_data = eve_esi_interface.get_esi_paged_data(
        access_token,
        "corporations/{}/assets/".format(corporation_id),
        "corp_assets")
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
            "corp_ass_names",
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
                    "universe/structures/{}/".format(structure_id),
                    'universe_structures_{}'.format(structure_id))
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
    #     "universe/structures/",
    #     "universe_structures")
    # print("\nFound {} public structures in universe".format(len(universe_structures_data)))
    # sys.stdout.flush()

    # Построение дерева ассетов, с узлави в роли станций и систем, и листьями в роли хранящихся
    # элементов, в виде:
    # { location1: {items:[item1,item2,...],type_id,location_id},
    #   location2: {items:[item3],type_id} }
    corp_assets_tree = eve_esi_tools.get_assets_tree(corp_assets_data, foreign_structures_data, sde_inv_items)
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
    main()
