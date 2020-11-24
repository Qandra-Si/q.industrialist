""" Q.Assets (desktop/mobile)

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

>>> python eve_sde_tools.py --cache_dir=~/.q_industrialist
>>> python q_assets.py --pilot1="Qandra Si" --pilot2="Your Name" --online --cache_dir=~/.q_industrialist

Requires application scopes:
    * esi-assets.read_corporation_assets.v1 - Requires role(s): Director
    * esi-universe.read_structures.v1 - Requires: access token
"""
import sys
import json
from typing import Dict

import requests

import eve_esi_interface as esi

import eve_esi_tools
import eve_sde_tools
import console_app
import render_html_assets
import q_industrialist_settings

from memory_profiler import profile

from __init__ import __version__


# type_id - тип требуемых данных
#  * None : корневой, т.е. данные по текущей локации маршрута циносети
#  * <number> : значение type_id, поиск которого осуществляется (солнечная система, или топляк)
#               при type_id > 0 поиск осуществляется вверх по дереву
#               при type_id < 0 поиск осуществляется вниз по дереву
from eve.esi import StructureData
from eve.domain import Asset, MarketPrice
from eve.gateways import GetCorpAssetsGateway, GetInventoryLocationGateway, GetMarketPricesGateway, GetTypeInfoGateway, \
    GetMarketGroupsGateway, GetCorpAssetsNamesGateway, GetForeignStructuresGateway
from eve.esi import get_assets_tree

#@profile
def main():
    # работа с параметрами командной строки, получение настроек запуска программы, как то: работа в offline-режиме,
    # имя пилота ранее зарегистрированного и для которого имеется аутентификационный токен, регистрация нового и т.д.
    argv_prms = console_app.get_argv_prms()

    cache_dir = argv_prms["workspace_cache_files_dir"]

    # настройка Eve Online ESI Swagger interface
    auth = esi.EveESIAuth(
        '{}/auth_cache'.format(cache_dir),
        debug=True)
    client = esi.EveESIClient(
        auth,
        debug=False,
        logger=True,
        user_agent='Q.Industrialist v{ver}'.format(ver=__version__))
    interface = esi.EveOnlineInterface(
        client,
        q_industrialist_settings.g_client_scope,
        cache_dir='{}/esi_cache'.format(cache_dir),
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

    type_info_gateway = GetTypeInfoGateway(cache_dir=cache_dir)
    sde_type_ids = type_info_gateway.type_info()

    inventory_location_gateway = GetInventoryLocationGateway(cache_dir = cache_dir)
    sde_inv_items = inventory_location_gateway.get_inventory_locations()

    market_groups_gateway = GetMarketGroupsGateway(cache_dir=cache_dir)
    sde_market_groups = market_groups_gateway.market_groups()

    # Requires role(s): Director
    corp_assets_gateway = GetCorpAssetsGateway(eve_interface=interface, corporation_id=corporation_id)
    corp_assets_data = corp_assets_gateway.assets()

    print("\n'{}' corporation has {} assets".format(corporation_name, len(corp_assets_data)))
    sys.stdout.flush()

    # Получение названий контейнеров, станций, и т.п. - всё что переименовывается ingame
    corp_assets_names_gateway = GetCorpAssetsNamesGateway(
        eve_interface=interface,
        corporation_id=corporation_id
    )
    corp_ass_names_data = corp_assets_names_gateway.asets_name(corp_assets_data)
    print("\n'{}' corporation has {} custom asset's names".format(corporation_name, len(corp_ass_names_data)))
    sys.stdout.flush()

    # Поиск тех станций, которые не принадлежат корпорации (на них имеется офис, но самой станции в ассетах нет)
    foreign_structures_gateway = GetForeignStructuresGateway(interface)
    foreign_structures_data = foreign_structures_gateway.structures(
        corp_assets_data= corp_assets_data,
        corporation_name= corporation_name
    )

    # Public information about market prices
    market_prices_gateway = GetMarketPricesGateway(eve_interface = interface)
    eve_market_prices_data = market_prices_gateway.market_prices()
    print("\nEVE market has {} prices".format(len(eve_market_prices_data)))
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
    corp_assets_tree = get_assets_tree(
        corp_assets_data,
        foreign_structures_data,
        sde_inv_items,
        virtual_hierarchy_by_corpsag=True
    )
    eve_esi_tools.dump_debug_into_file(cache_dir, "corp_assets_tree", corp_assets_tree)

    # Построение дерева asset-ов:
    print("\nBuilding assets tree report...")
    sys.stdout.flush()
    sde_inv_names = eve_sde_tools.read_converted(cache_dir, "invNames")
    render_html_assets.dump_assets_tree_into_report(
        # путь, где будет сохранён отчёт
        cache_dir,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_inv_names,
        sde_inv_items,
        sde_market_groups,
        # esi данные, загруженные с серверов CCP
        corp_assets_data,
        corp_ass_names_data,
        foreign_structures_data,
        eve_market_prices_data,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_assets_tree)

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nDone")

def _get_cyno_solar_system_details(location_id, corp_assets_tree, subtype=None):
    if not (str(location_id) in corp_assets_tree):
        return None
    loc_dict = corp_assets_tree[str(location_id)]
    if subtype is None:
        if "location_id" in loc_dict: # иногда ESI присылает содержимое контейнеров, которые исчезают из ангаров, кораблей и звёздных систем
            solar_system_id = _get_cyno_solar_system_details(
                loc_dict["location_id"],
                corp_assets_tree,
                -5  # Solar System (поиск вниз по дереву)
            )
        else:
            solar_system_id = None
        badger_ids = _get_cyno_solar_system_details(location_id, corp_assets_tree, 648)  # Badger
        venture_ids = _get_cyno_solar_system_details(location_id, corp_assets_tree, 32880)  # Venture
        liquid_ozone_ids = _get_cyno_solar_system_details(location_id, corp_assets_tree, 16273)  # Liquid Ozone
        indus_cyno_gen_ids = _get_cyno_solar_system_details(location_id, corp_assets_tree, 52694)  # Industrial Cynosural Field Generator
        exp_cargohold_ids = _get_cyno_solar_system_details(location_id, corp_assets_tree, 1317)  # Expanded Cargohold I
        cargohold_rigs_ids = _get_cyno_solar_system_details(location_id, corp_assets_tree, 31117)  # Small Cargohold Optimization I
        nitrogen_isotope_ids = _get_cyno_solar_system_details(location_id, corp_assets_tree, 17888)  # Nitrogen Isotopes
        hydrogen_isotope_ids = _get_cyno_solar_system_details(location_id, corp_assets_tree, 17889)  # Hydrogen Isotopes
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
                return _get_cyno_solar_system_details(loc_dict["location_id"], corp_assets_tree, subtype)
            else:
                return None
        else:  # subtype > 0
            result = []
            items = loc_dict["items"] if "items" in loc_dict else None
            if not (items is None):
                for i in items:
                    item_ids = _get_cyno_solar_system_details(i, corp_assets_tree, subtype)
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



if __name__ == "__main__":
    main()
