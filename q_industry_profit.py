""" Q.EVE Industry Profit (desktop/mobile)

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

$ chcp 65001 & @rem on Windows only!
$ python eve_sde_tools.py --cache_dir=~/.q_industrialist
$ python q_industry_profit.py --pilot="Qandra Si" --online --cache_dir=~/.q_industrialist

Requires application scopes:
    * Public scopes
"""
import sys
import typing
import requests

# from memory_profiler import profile

import q_industrialist_settings
import q_router_settings
import console_app
import eve_sde_tools
import profit
import eve_esi_interface as esi
import eve_industry_profit
import render_html_industry_profit
from __init__ import __version__

"""
Некоторые данные для отладки:

select
 sdebp_blueprint_type_id,
 sdebp_product_id,
 sdebp_quantity,
 tid.sdet_type_name,
 t1m.sdebm_material_id,
 t1m.sdebm_quantity,
 t1m_tid.sdet_type_name
from qi.eve_sde_blueprint_products p
 left outer join qi.eve_sde_type_ids as tid on (p.sdebp_product_id=tid.sdet_type_id)
 left outer join qi.eve_sde_blueprint_materials as t1m on (
   p.sdebp_blueprint_type_id=t1m.sdebm_blueprint_type_id and
   p.sdebp_activity=t1m.sdebm_activity and
   t1m.sdebm_material_id in (select sdet_type_id from qi.eve_sde_type_ids where sdet_tech_level=1 and sdet_meta_group_id=1))
 left outer join qi.eve_sde_type_ids as t1m_tid on (t1m.sdebm_material_id=t1m_tid.sdet_type_id)
where
 sdebp_activity = 1 and tid.sdet_published
 --and tid.sdet_type_name = 'Rocket Launcher II'
 and tid.sdet_type_name like '%Tengu%'
order by sdebp_quantity desc, t1m.sdebm_quantity desc, sdebp_blueprint_type_id;

select ebc_blueprint_type_id, ebc_job_activity, ebc_blueprint_runs, ebc_material_efficiency, count(1)
from qi.esi_blueprint_costs
where ebc_blueprint_type_id=2614
group by 1, 2, 3, 4;

-- blueprint product qty  name                                 t1 material                    runs  me
-- 2614      2613    5000 Mjolnir Fury Light Missile                                          10     2
-- 41282     41274   5000 Mjolnir Javelin XL Torpedo           17857 5000x Mjolnir XL Torpedo
-- 48104     47929   5000 Meson Exotic Plasma M                                               5      0
-- 42876     42833    500 Rapid Repair Charge                                                       10
-- 17671     17670    100 Fusion XL                                                                 10
-- 1178        263     10 Cap Booster 25                                                      10     0
-- 41335     41334      4 Gleam XL                             17686 4x Multifrequency XL
-- 57523     57486      3 Life Support Backup Unit                                            30    10
-- 10632     10631      1 Rocket Launcher II                   10629 1x Rocket Launcher I     10     2
-- 12301     12200      1 Mobile Large Warp Disruptor I        447 9x Warp Scrambler I        50    10
-- 12300     12199      1 Mobile Medium Warp Disruptor I       447 6x Warp Scrambler I        60    10
-- 12297     12198      1 Mobile Small Warp Disruptor I        447 3x Warp Scrambler I        100   10
-- 45698     45603      1 Tengu Offensive - Support Processor                                 23     3

select distinct
 tid.sdet_type_name,
 ecb_type_id,
 ecb_material_efficiency,
 ecb_time_efficiency,
 ecb_runs
from
 qi.esi_corporation_blueprints
 left outer join qi.eve_sde_type_ids as tid on (ecb_type_id=tid.sdet_type_id)
where ecb_location_id in (
 select eca_item_id
 from qi.esi_corporation_assets
 where eca_name like '[prod] conveyor%'
);
"""


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
        keep_alive=True,
        debug=argv_prms["verbose_mode"],
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
    sde_market_groups = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "marketGroups")
    sde_bp_materials = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "blueprints")
    sde_icon_ids = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "iconIDs")
    sde_inv_names = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "invNames")

    try:
        # Public information about market prices
        eve_market_prices_data = interface.get_esi_data("markets/prices/")
        print("\nEVE market has {} prices".format(len(eve_market_prices_data) if not (eve_market_prices_data is None) else 0))
        sys.stdout.flush()
    except requests.exceptions.HTTPError as err:
        status_code = err.response.status_code
        if status_code == 404:  # 2020.12.03 поломался доступ к ценам маркета (ССР-шники "внесли правки")
            eve_market_prices_data = []
        else:
            raise
    except:
        print(sys.exc_info())
        raise

    try:
        # Public information about industry cost indices for solar systems
        eve_industry_systems_data = interface.get_esi_data("industry/systems/")
        print("\nEVE industry has {} systems".format(len(eve_industry_systems_data) if not (eve_industry_systems_data is None) else 0))
        sys.stdout.flush()
    except requests.exceptions.HTTPError as err:
        status_code = err.response.status_code
        if status_code == 404:  # по аналогии получению данных выше
            eve_industry_systems_data = []
        else:
            raise
    except:
        print(sys.exc_info())
        raise

    try:
        # Public information about market prices
        eve_forge_orders_data = interface.get_esi_paged_data(f"markets/{profit.QMarketOrders.region_the_forge_id()}/orders/")  # The Forge
        print("\nEVE region The Forge has {} orders".format(len(eve_forge_orders_data) if not (eve_forge_orders_data is None) else 0))
        eve_jita_orders_data = profit.QMarketOrders(profit.QMarketOrders.location_jita4_4_id())
        num_orders: int = eve_jita_orders_data.load_orders(eve_forge_orders_data)
        print("\nEVE station Jita 4-4 has {} orders".format(num_orders))
        sys.stdout.flush()
        del eve_forge_orders_data
    except requests.exceptions.HTTPError as err:
        status_code = err.response.status_code
        if status_code == 404:  # 2020.12.03 поломался доступ к ценам маркета (ССР-шники "внесли правки")
            eve_jita_orders_data = profit.QMarketOrders(profit.QMarketOrders.location_jita4_4_id())
        else:
            raise
    except:
        print(sys.exc_info())
        raise

    # входные данные для расчёта: тип чертежа и сведения о его material efficiency
    # идентификатор industry-чертежа всегда уникально указывает на тип продукта:
    #   select sdebp_blueprint_type_id, count(sdebp_blueprint_type_id)
    #   from qi.eve_sde_blueprint_products p
    #   where sdebp_activity=1
    #   group by 1
    #   order by 2 desc;
    # однако это не относится к другим типам activity !!!
    calc_inputs = [
        # {'bptid': 784, 'qr': 10, 'me': 2, 'te': 4},  # Miner II Blueprint
        # {'bptid': 10632, 'qr': 10, 'me': 2, 'te': 4},  # Rocket Launcher II
        # {'bptid': 10632, 'qr': 10+1, 'me': 2+2, 'te': 4+10},  # Rocket Launcher II (runs +1, me +2, te +10)
        # {'bptid': 10632, 'qr': 1, 'me': 2, 'te': 4},  # Rocket Launcher II
        # {'bptid': 45698, 'qr': 23, 'me': 3, 'te': 2},  # Tengu Offensive - Support Processor
        # {'bptid': 2614, 'qr': 10, 'me': 2, 'te': 4},   # Mjolnir Fury Light Missile
        # {'bptid': 1178, 'qr': 10, 'me': 0, 'te': 0},   # Cap Booster 25
        # {'bptid': 12041, 'qr': 1, 'me': 2, 'te': 4},  # Purifier
        # {'bptid': 12041, 'qr': 1+1, 'me': 2+2, 'te': 4+10},  # Purifier (runs +1, me +2, te +10)
        # {'bptid': 12041, 'qr': 1+9, 'me': 2-2, 'te': 4+2},  # Purifier (runs +9, me -2, te +2)
        # {'bptid': 12035, 'qr': 1+9, 'me': 2-2, 'te': 4+2},  # Hound (runs +9, me -2, te +2)
        # {'bptid': 12031, 'qr': 1+9, 'me': 2-2, 'te': 4+2},  # Manticore (runs +9, me -2, te +2)
        # {'bptid': 11378, 'qr': 1+9, 'me': 2-2, 'te': 4+2},  # Nemesis (runs +9, me -2, te +2)
        # {'bptid': 28666, 'qr': 1+7, 'me': 2+2, 'te': 4+0},  # Vargur (runs +7, me +2, te +0)
        # {'bptid': 28662, 'qr': 1+7, 'me': 2+2, 'te': 4+0},  # Kronos (runs +7, me +2, te +0)
        # {'bptid': 28660, 'qr': 1+7, 'me': 2+2, 'te': 4+0},  # Paladin (runs +7, me +2, te +0)
        # {'bptid': 28711, 'qr': 1+7, 'me': 2+2, 'te': 4+0},  # Golem (runs +7, me +2, te +0)
        # {'bptid': 1072, 'qr': 1, 'me': 10, 'te': 20},  # 1MN Afterburner I Blueprint
        # {'bptid': 1071, 'qr': 10, 'me': 2, 'te': 4},  # 1MN Afterburner II Blueprint
        # {'bptid': 34596, 'qr': 1, 'me': 2, 'te': 4},  # Entosis Link II - наибольшее кол-во материалов
        # {'bptid': 61220, 'qr': 10, 'me': 2, 'te': 4},  # Ubiquitous Moon Mining Crystal Type C II - 3 произв. матер.
        {'bptid': 26341, 'qr': 1+1, 'me': 2+2, 'te': 4+10},  # Large Stasis Drone Augmentor II - 1 производимый матер.
        # {'bptid': 21018, 'qr': 1, 'me': 10, 'te': 20},  # Capital Armor Plates (Methanofullerene с бонусом и ригами)
        # {'bptid': 41356},  # Ametat II (Antimatter Reactor Unit с бонусом и ригами)
        # {'bptid': 45718},  # Legion Core - Augmented Antimatter Reactor
        # {'bptid': 20352},  # 800mm Steel Plates II
    ]

    # with open('{}/industry_cost/dataset.json'.format(argv_prms["workspace_cache_files_dir"]), 'r', encoding='utf8') as f:
    #    s = f.read()
    #    calc_inputs = (json.loads(s))

    # индексы стоимости производства для различных систем (системы и продукция заданы в настройках роутинга)
    industry_cost_indices: typing.List[profit.QIndustryCostIndices] = []
    for r in q_router_settings.g_routes:
        assert 'solar_system' in r
        solar_system: str = r['solar_system']
        solar_system_id: typing.Optional[int] = next((int(_[0]) for _ in sde_inv_names.items()
                                                      if _[1] == solar_system), None)
        assert solar_system_id is not None
        cost_indices = next((_['cost_indices'] for _ in eve_industry_systems_data
                             if _['solar_system_id'] == solar_system_id), None)
        assert cost_indices is not None
        assert 'structure' in r
        factory_bonuses: profit.QIndustryFactoryBonuses = profit.QIndustryFactoryBonuses(
            r['structure'],
            r.get('structure_rigs', []))
        iic: profit.QIndustryCostIndices = profit.QIndustryCostIndices(
            solar_system_id,
            solar_system,
            cost_indices,
            r['station'],
            set(r['output']),
            factory_bonuses)
        industry_cost_indices.append(iic)
    del eve_industry_systems_data

    # настройки оптимизации производства: реакции на 15 ран (сутки) и производство в зависимости от времени (сутки)
    # см. также eve_conveyor_tools.py : setup_blueprint_details
    calc_customization = {
        # длительность всех реакций - около 1 суток
        'reaction_runs': 15,
        # длительность производства компонентов общего потребления (таких как Advanced Components или Fuel Blocks)
        # тоже принимается около 1 суток, остальные материалы рассчитываются в том объёме, в котором необходимо
        # 'industry_time': 5 * 60 * 60 * 24,  # типично для R Industry
        'industry_time': (5 * 60 * 60 * 24) // 8,  # производство по 2400 Fuel Blocks (60 runs)
        'common_components': [  # market-группы компонентов общего потребления
            1870,  # Fuel Blocks
            65,  # Advanced Components
            2768,  # Protective Components
            1908,  # R.A.M.
            1147,  # Subsystem Components
        ],
        # === min_probability ===
        # * 18% jump freighters; 22% battleships; 26% cruisers, BCs, industrial, mining barges;
        #   30% frigate hull, destroyer hull; 34% modules, ammo, drones, rigs
        # * Tech 3 cruiser hulls and subsystems have 22%, 30% or 34% chance depending on artifact used
        # * Tech 3 destroyer hulls have 26%, 35% or 39% chance depending on artifact used
        # рекомендации к минимальным скилам: 3+3+3 (27..30% навыки и импланты)
        # Invention_Chance =
        #  Base_Chance *
        #  (1 + ((Encryption_Skill_Level / 40) +
        #        ((Datacore_1_Skill_Level + Datacore_2_Skill_Level) / 30)
        #       )
        #  ) * Decryptor_Modifier
        'min_probability': 27.5,  # min навыки и импланты пилотов запускающих инвенты (вся научка мин в 3)
        # экономия материалов (material efficiency) промежуточных чертежей
        'unknown_blueprints_me': 10,
    }

    # настройки оптимизации производства: реакции на 15 ран (сутки) и производство в зависимости от времени (сутки)
    # см. также eve_conveyor_tools.py : setup_blueprint_details
    industry_plan_customization: typing.Optional[profit.QIndustryPlanCustomization] = None
    if calc_customization:
        industry_plan_customization = profit.QIndustryPlanCustomization(
            reaction_runs=calc_customization.get('reaction_runs'),
            industry_time=calc_customization.get('industry_time'),
            common_components=calc_customization.get('common_components'),
            min_probability=calc_customization.get('min_probability'),
            unknown_blueprints_me=calc_customization.get('unknown_blueprints_me'))

    for calc_input in calc_inputs:
        # выходные данные после расчёта: дерево материалов и работ, которые надо выполнить
        industry_tree: profit.QIndustryTree = eve_industry_profit.generate_industry_tree(
            # вход и выход для расчёта
            calc_input,
            industry_plan_customization,
            # sde данные, загруженные из .converted_xxx.json файлов
            sde_type_ids,
            sde_bp_materials,
            sde_market_groups,
            eve_market_prices_data,
            industry_cost_indices)

        # выходные данные после расчёта: список материалов и ratio-показатели их расхода для производства qr-ранов
        industry_plan: profit.QIndustryPlan = eve_industry_profit.generate_industry_plan(
            industry_tree.blueprint_runs_per_single_copy,
            industry_tree,
            industry_plan_customization)

        industry_formula: profit.QIndustryFormula = eve_industry_profit.assemble_industry_formula(
            industry_plan)

        render_html_industry_profit.dump_industry_plan(
            industry_plan,
            '{}/industry_cost'.format(argv_prms["workspace_cache_files_dir"]),
            sde_type_ids,
            sde_bp_materials,
            sde_market_groups,
            eve_market_prices_data,
            sde_icon_ids,
            eve_jita_orders_data,
            industry_cost_indices,
            industry_formula)


if __name__ == "__main__":
    main()
