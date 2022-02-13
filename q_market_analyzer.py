""" Q.MarketAnalyzer (desktop/mobile)

Prerequisites:
    * Have a Python 3 environment available to you (possibly by using a
      virtual environment: https://virtualenv.pypa.io/en/stable/).
    * Run pip install -r requirements.txt with this directory as your root.

    * Copy q_industrialist_settings.py.template into q_industrialist_settings.py and
      mood for your needs.
    * Copy q_market_analyzer_settings.py.template into q_market_analyzer_settings.py and
      mood for your needs.
    * Create an SSO application at developers.eveonline.com with the scopes
      from g_client_scope list declared in q_industrialist_settings.py and the
      callback URL "https://localhost/callback/".
      Note: never use localhost as a callback in released applications.

To run this example, make sure you have completed the prerequisites and then
run the following command from this directory as the root:

$ chcp 65001 & @rem on Windows only!
$ python eve_sde_tools.py --cache_dir=~/.q_industrialist
$ python q_market_analyzer.py --pilot="Qandra Si" --online --cache_dir=~/.q_industrialist

Requires application scopes:
    * public access
"""
import sys

import eve_esi_interface as esi

import eve_esi_tools
import eve_sde_tools
import console_app
import render_html_market_analyzer
import q_industrialist_settings
import q_market_analyzer_settings

from __init__ import __version__


def main():
    # работа с параметрами командной строки, получение настроек запуска программы, как то: работа в offline-режиме,
    # имя пилота ранее зарегистрированного и для которого имеется аутентификационный токен, регистрация нового и т.д.
    argv_prms = console_app.get_argv_prms()

    sde_type_ids = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "typeIDs")
    sde_inv_names = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "invNames")
    # sde_inv_items = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "invItems")
    sde_market_groups = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "marketGroups")
    sde_icon_ids = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "iconIDs")
    sde_bp_materials = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "blueprints")

    # удаление из списка чертежей тех, которые не published (надо соединить typeIDs и blueprints, отбросив часть)
    for t in [t for t in sde_type_ids if t in sde_bp_materials.keys() and sde_type_ids[t].get('published')==False]:
        del sde_bp_materials[t]
    # построение списка продуктов, которые появляются в результате производства
    products_for_bps = set(eve_sde_tools.get_products_for_blueprints(sde_bp_materials))
    materials_for_bps = eve_sde_tools.get_materials_for_blueprints(sde_bp_materials)
    research_materials_for_bps = eve_sde_tools.get_research_materials_for_blueprints(sde_bp_materials)
    materials_for_bps.extend(research_materials_for_bps)
    materials_for_bps = set(materials_for_bps)
    del research_materials_for_bps

    pilot_name = argv_prms["character_names"][0]

    # настройка Eve Online ESI Swagger interface
    auth = esi.EveESIAuth(
        '{}/auth_cache'.format(argv_prms["workspace_cache_files_dir"]),
        debug=True)
    client = esi.EveESIClient(
        auth,
        keep_alive=True,
        debug=argv_prms["verbose_mode"],
        logger=True,
        user_agent='Q.Industrialist v{ver}'.format(ver=__version__))
    interface = esi.EveOnlineInterface(
        client,
        q_industrialist_settings.g_client_scope,
        cache_dir='{}/esi_cache'.format(argv_prms["workspace_cache_files_dir"]),
        offline_mode=argv_prms["offline_mode"])

    authz = interface.authenticate(pilot_name)
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

    # corporation_id = character_data["corporation_id"]
    corporation_name = corporation_data["name"]
    print("\n{} is from '{}' corporation".format(character_name, corporation_name))
    sys.stdout.flush()

    market_regions = [(int(id), sde_inv_names[id], {}) for id in sde_inv_names if sde_inv_names[id] in q_market_analyzer_settings.g_regions]

    for (region_id, region_name, region_details) in market_regions:
        # Requires: public access
        markets_region_orders = interface.get_esi_paged_data(
            "markets/{}/orders/".format(region_id))
        sys.stdout.flush()

        region_details.update({
            "orders": {
                "buy": 0,
                "sell": 0,
            },
        })

        region_systems = {}
        region_trade_hubs = {}
        region_market = {}
        for o in markets_region_orders:
            type_id: int = o["type_id"]

            # проверяем к какой группе товаров относится данный type_id, если это чертежи, книжки, шкурки - пропускаем
            market_chain = eve_sde_tools.get_market_groups_chain_by_type_id(sde_type_ids, sde_market_groups, type_id)
            if market_chain:
                if market_chain[0] in [
                    2,  # пропускаем Blueprints
                    1659,  # пропускаем Special Edition Assets
                    1396,  # пропускаем Apparel
                    1954,  # пропускаем Ship SKINs
                    150,  # пропускаем Skills
                ]:
                    continue
                semantic_market_group_id = market_chain[0] if len(market_chain) == 1 else market_chain[1]
            else:
                semantic_market_group_id = 0  # нам что 0, что None - без разницы, группы для него нет

            # проверяем, и пропускаем те товары, которые нельзся произвести
            if q_market_analyzer_settings.g_skip_non_manufacturing_products:
                if type_id not in products_for_bps and type_id not in materials_for_bps:
                    continue

            system_id: str = o["system_id"]
            location_id: str = o["location_id"]

            system_dict = region_systems.get(system_id)
            if not system_dict:
                region_systems.update({system_id: {
                    "name": sde_inv_names.get(str(system_id)),
                    "orders": {"buy": 0, "sell": 0},
                    "market": {},
                }})
                system_dict = region_systems.get(system_id)

            trade_hub_dict = region_trade_hubs.get(location_id)
            if not trade_hub_dict:
                region_trade_hubs.update({location_id: {
                    "name": sde_inv_names.get(str(location_id)),
                    "system": system_id,
                    "orders": {"buy": 0, "sell": 0},
                    "market": {},
                }})
                trade_hub_dict = region_trade_hubs.get(location_id)

            region_market_dict = region_market.get(semantic_market_group_id)
            if not region_market_dict:
                region_market.update({semantic_market_group_id: {
                    "orders": {"buy": 0, "sell": 0},
                }})
                region_market_dict = region_market.get(semantic_market_group_id)

            system_market_dict = system_dict["market"].get(semantic_market_group_id)
            if not system_market_dict:
                system_dict["market"].update({semantic_market_group_id: {
                    "orders": {"buy": 0, "sell": 0},
                }})
                system_market_dict = system_dict["market"].get(semantic_market_group_id)

            trade_hub_market_dict = trade_hub_dict["market"].get(semantic_market_group_id)
            if not trade_hub_market_dict:
                trade_hub_dict["market"].update({semantic_market_group_id: {
                    "orders": {"buy": 0, "sell": 0},
                }})
                trade_hub_market_dict = trade_hub_dict["market"].get(semantic_market_group_id)

            """ debug
            if system_id == 30045352:
                print(
                    "{:>6} {:<50} {:>4} {:>11} {:>11} {:>11} {:>6} {}".
                    format(
                        type_id,
                        sde_type_ids.get(str(type_id), {"name":{"en":"?"}})["name"]["en"],
                        "buy" if o["is_buy_order"] else "sell",
                        o["range"],
                        o["price"],
                        o["volume_remain"],
                        semantic_market_group_id if semantic_market_group_id else "?",
                        sde_market_groups.get(str(semantic_market_group_id), {"nameID": {"en": "?"}})["nameID"]["en"]
                    ),
                    # o
                )
            """

            tag_order: str = "buy" if o["is_buy_order"] else "sell"
            region_details["orders"][tag_order] += 1
            system_dict["orders"][tag_order] += 1
            trade_hub_dict["orders"][tag_order] += 1
            region_market_dict["orders"][tag_order] += 1
            system_market_dict["orders"][tag_order] += 1
            trade_hub_market_dict["orders"][tag_order] += 1

        region_details.update({
            "systems": region_systems,
            "trade_hubs": region_trade_hubs,
            "market": region_market,
        })

        del region_market
        del region_trade_hubs
        del region_systems
        del markets_region_orders

    eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "market_regions", market_regions)

    render_html_market_analyzer.dump_market_analyzer_into_report(
        # путь, где будет сохранён отчёт
        argv_prms["workspace_cache_files_dir"],
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_icon_ids,
        sde_market_groups,
        sde_inv_names,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        market_regions
    )

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nDone")


if __name__ == "__main__":
    main()
