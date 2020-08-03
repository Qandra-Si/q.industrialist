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
import q_logist_settings
import auth_cache
import shared_flow
import eve_esi_tools
import eve_sde_tools
import eve_esi_interface

from render_html import dump_assets_tree_into_report
from render_html import dump_cynonetwork_into_report


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
    if len(foreign_structures_ids) > 0:
        # Requires: access token
        for structure_id in foreign_structures_ids:
            universe_structure_data = eve_esi_interface.get_esi_data(
                access_token,
                "universe/structures/{}/".format(structure_id),
                'universe_structures_{}'.format(structure_id))
            foreign_structures_data.update({str(structure_id): universe_structure_data})
    print("\n'{}' corporation has offices in {} foreign stations".format(corporation_name, len(foreign_structures_data)))
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
    eve_esi_interface.dump_json_into_file("corp_assets_tree", corp_assets_tree)

    # Построение списка модулей и ресуров, которые имеются в распоряжении корпорации и
    # которые предназначены для использования в чертежах
    corp_ass_loc_data = eve_esi_tools.get_corp_ass_loc_data(corp_assets_data)
    eve_esi_interface.dump_json_into_file("corp_ass_loc_data", corp_ass_loc_data)

    # Только для поиска ассетов:
    #print("\nBuilding assets tree report...")
    #sys.stdout.flush()
    #dump_assets_tree_into_report(
    #    # sde данные, загруженные из .converted_xxx.json файлов
    #    sde_type_ids,
    #    sde_inv_names,
    #    sde_inv_items,
    #    # esi данные, загруженные с серверов CCP
    #    corp_assets_data,
    #    corp_ass_names_data,
    #    foreign_structures_data,
    #    # данные, полученные в результате анализа и перекомпоновки входных списков
    #    corp_ass_loc_data,
    #    corp_assets_tree)

    # Фильтрация (вручную) ассетов, которые расположены на станках циносети
    corp_cynonetwork = {}
    for cn in q_logist_settings.g_cynonetworks:
        cn_route = cn["route"]
        for location_id in cn_route:
            # если системы в цино сети повторяются, не гоняем искалочку зазря (повторно)
            if not (str(location_id) in corp_cynonetwork):
                data = get_cyno_solar_system_details(location_id, corp_assets_tree)
                # ---
                # signalling_level = 0 - normal, 1 - warning, 2 - danger, 3 - ошибка получения данных
                # оптимальный набор: 10 баджеров, 10 цин, 10'000 (по 950 на прожиг) озона
                #              плюс: 10 вентур, 10 цин, 10'000 (по 200 на прожиг) озона, 30 риг, 10 каргохолда
                # минимальный набор: 1 баджер, 1 вентурка, 2 цины, 1150 озона, 3 риги, 1 каргохолд
                if data is None:
                    # print('{} {}'.format(location_id, data))
                    loc_name = "NO-DATA!"
                    loc_id = location_id
                    if int(loc_id) < 1000000000000:
                        if str(loc_id) in sde_inv_names:
                            loc_name = sde_inv_names[str(loc_id)]
                            print(loc_name)
                            if str(loc_id) in sde_inv_items:
                                root_item = sde_inv_items[str(loc_id)]
                                # print("root_item", root_item)
                                if root_item["typeID"] != 5:  # not Solar System (may be Station?)
                                    loc_id = root_item["locationID"]
                                    root_item = sde_inv_items[str(loc_id)]
                                    # print(" >>> ", loc_id, root_item)
                                    if root_item["typeID"] == 5:  # Solar System
                                        loc_name = sde_inv_names[str(loc_id)]  # Solar System (name)
                                        # print(" >>> >>> ", loc_name)
                    data = {"error": "no data",
                            "solar_system": loc_name,
                            "signalling_level": 3}
                else:
                    system_id = data["solar_system"]
                    badger_ids = data["badger"]
                    venture_ids = data["venture"]
                    liquid_ozone_ids = data["liquid_ozone"]
                    indus_cyno_gen_ids = data["indus_cyno_gen"]
                    exp_cargohold_ids = data["exp_cargohold"]
                    cargohold_rigs_ids = data["cargohold_rigs"]
                    nitrogen_isotope_ids = data["nitrogen_isotope"]
                    hydrogen_isotope_ids = data["hydrogen_isotope"]
                    if system_id is None:
                        system_name = "NO-DATA!"
                    else:
                        system_name = sde_inv_names[str(system_id)]
                    badger_num = 0
                    venture_num = 0
                    liquid_ozone_num = 0
                    indus_cyno_gen_num = 0
                    exp_cargohold_num = 0
                    cargohold_rigs_num = 0
                    nitrogen_isotope_num = 0
                    hydrogen_isotope_num = 0
                    # ---
                    for a in corp_assets_data:
                        item_id = int(a["item_id"])
                        quantity = int(a["quantity"])
                        if not (badger_ids is None) and badger_ids.count(item_id) > 0:
                            badger_num = badger_num + quantity
                        elif not (venture_ids is None) and venture_ids.count(item_id) > 0:
                            venture_num = venture_num + quantity
                        elif not (liquid_ozone_ids is None) and liquid_ozone_ids.count(item_id) > 0:
                            liquid_ozone_num = liquid_ozone_num + quantity
                        elif not (indus_cyno_gen_ids is None) and indus_cyno_gen_ids.count(item_id) > 0:
                            indus_cyno_gen_num = indus_cyno_gen_num + quantity
                        elif not (exp_cargohold_ids is None) and exp_cargohold_ids.count(item_id) > 0:
                            exp_cargohold_num = exp_cargohold_num + quantity
                        elif not (cargohold_rigs_ids is None) and cargohold_rigs_ids.count(item_id) > 0:
                            cargohold_rigs_num = cargohold_rigs_num + quantity
                        elif not (nitrogen_isotope_ids is None) and nitrogen_isotope_ids.count(item_id) > 0:
                            nitrogen_isotope_num = nitrogen_isotope_num + quantity
                        elif not (hydrogen_isotope_ids is None) and hydrogen_isotope_ids.count(item_id) > 0:
                            hydrogen_isotope_num = hydrogen_isotope_num + quantity
                    # ---
                    if system_id is None:
                        signalling_level = 3
                    elif (badger_num >= 10) and\
                       (venture_num >= 10) and\
                       (liquid_ozone_num >= 20000) and\
                       (indus_cyno_gen_num >= 20) and\
                       (exp_cargohold_num >= 10) and\
                       (cargohold_rigs_num >= 30) and\
                       (nitrogen_isotope_num >= 0) and\
                       (hydrogen_isotope_num >= 0):
                        signalling_level = 0
                    elif (badger_num >= 1) and \
                         (venture_num >= 1) and \
                         (liquid_ozone_num >= 1150) and \
                         (indus_cyno_gen_num >= 2) and \
                         (exp_cargohold_num >= 1) and \
                         (cargohold_rigs_num >= 3) and \
                         (nitrogen_isotope_num >= 0):
                        signalling_level = 1
                    else:
                        signalling_level = 2
                    # ---
                    data = {
                        "solar_system": system_name,
                        "badger": badger_num,
                        "venture": venture_num,
                        "liquid_ozone": liquid_ozone_num,
                        "indus_cyno_gen": indus_cyno_gen_num,
                        "exp_cargohold": exp_cargohold_num,
                        "cargohold_rigs": cargohold_rigs_num,
                        "nitrogen_isotope": nitrogen_isotope_num,
                        "hydrogen_isotope": hydrogen_isotope_num,
                        "signalling_level": signalling_level
                    }
                    if system_id is None:
                        data.update({"error": "no solar system"})
                corp_cynonetwork.update({str(location_id): data})

    print("\nBuilding cyno network report...")
    sys.stdout.flush()
    dump_cynonetwork_into_report(
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_cynonetwork
    )


if __name__ == "__main__":
    main()
