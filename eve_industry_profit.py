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
$ python eve_industry_profit.py --pilot="Qandra Si" --online --cache_dir=~/.q_industrialist

Requires application scopes:
    * Public scopes
"""
import sys
import typing
import math
import json
import requests

from memory_profiler import profile

import render_html
import eve_sde_tools
import eve_efficiency
import console_app
import profit
import q_industrialist_settings
import q_router_settings

import eve_esi_interface as esi
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


# получение цены материала
def get_material_price(type_id: int, sde_type_ids, eve_market_prices_data) -> typing.Optional[float]:
    price: typing.Optional[float] = None
    price_dict = next((p for p in eve_market_prices_data if p['type_id'] == int(type_id)), None)
    if price_dict is not None:
        if "average_price" in price_dict:
            price = float(price_dict["average_price"])
        elif "adjusted_price" in price_dict:
            price = float(price_dict["adjusted_price"])
    if not price:
        type_dict = sde_type_ids[str(type_id)]
        if "basePrice" in type_dict:
            price = float(type_dict["basePrice"])
    return price


def get_material_adjusted_price(type_id: int, sde_type_ids, eve_market_prices_data) -> typing.Optional[float]:
    price: typing.Optional[float] = None
    price_dict = next((p for p in eve_market_prices_data if p['type_id'] == int(type_id)), None)
    if price_dict is not None:
        if "adjusted_price" in price_dict:  # используется в расчётах стоимости запуска работы
            price = float(price_dict["adjusted_price"])
        elif "average_price" in price_dict:
            price = float(price_dict["average_price"])
    if not price:
        type_dict = sde_type_ids[str(type_id)]
        if "basePrice" in type_dict:
            price = float(type_dict["basePrice"])
    return price


def get_industry_cost_index(
        product_type_id: int,
        action: str,
        # индексы стоимости производства для различных систем (системы и продукция заданы в настройках роутинга)
        industry_cost_indices:  typing.List[profit.QIndustryCostIndices]) \
        -> typing.Tuple[profit.QIndustryCostIndices, float]:
    # получаем информацию о производственных индексах в системе, где крафтится этот продукт
    system_indices: profit.QIndustryCostIndices = next((
        _ for _ in industry_cost_indices
        if product_type_id in _.product_ids), None)
    if system_indices is None:
        system_indices = next((
            _ for _ in industry_cost_indices
            if not _.product_ids), None)
    assert system_indices is not None
    # получаем производственный индекс в системе
    cost_index: float = next((
        float(_['cost_index']) for _ in system_indices.cost_indices
        if _['activity'] == action), None)
    assert cost_index is not None
    # возвращаем tuple
    return system_indices, cost_index


# составляем дерево материалов, которые будут использоваться в производстве
def generate_materials_tree(
        # входной список материалов, используемых в производстве
        curr_materials,
        # выходной список со всеми возможными материалами, задействованными в производстве
        curr_industry: profit.QIndustryTree,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        # esi данные, загруженные с серверов CCP
        eve_market_prices_data,
        # индексы стоимости производства для различных систем (системы и продукция заданы в настройках роутинга)
        industry_cost_indices:  typing.List[profit.QIndustryCostIndices]):
    for m1 in enumerate(curr_materials, start=1):
        material_tid: int = int(m1[1]['typeID'])
        material_qty: int = int(m1[1]['quantity'])
        material_name: str = eve_sde_tools.get_item_name_by_type_id(sde_type_ids, material_tid)
        material_market_group: int = eve_sde_tools.get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, material_tid)
        material_group_name: str = sde_market_groups[str(material_market_group)]['nameID']['en']
        material_volume: float = sde_type_ids[str(material_tid)].get('volume', 0.0)
        material_price: typing.Optional[float] = get_material_price(material_tid, sde_type_ids, eve_market_prices_data)
        material_adjusted_price: typing.Optional[float] = get_material_adjusted_price(material_tid, sde_type_ids, eve_market_prices_data)
        # пополняем список материалов
        q_material: profit.QMaterial = profit.QMaterial(
            material_tid,
            material_qty,
            material_name,
            material_market_group,
            material_group_name,
            material_volume,
            material_price,
            material_adjusted_price)
        curr_industry.append_material(q_material)
        # или: проверяем, возможно ли получить данный материал с помощью его manufacturing-производства?
        # или: проверяем, возможно ли получить данный материал с помощью его reaction-производства?
        # или: если способов производства данного вида материалов так и не найдено, то данный материал закупается,
        #      переходим к следующему
        for activity in ['manufacturing', 'reaction', '']:
            material_bp_tid, blueprint_dict = \
                eve_sde_tools.get_blueprint_type_id_by_product_id(material_tid, sde_bp_materials, activity)
            if material_bp_tid is not None:
                blueprint_dict = blueprint_dict['activities'][activity]
                assert len(blueprint_dict.get('products', [])) == 1
                assert blueprint_dict['products'][0]['typeID'] == material_tid
                # готовим данные для следующего уровня вложенности
                material_produce_action: profit.QIndustryAction = profit.QIndustryAction.reaction \
                    if activity == 'reaction' else profit.QIndustryAction.manufacturing
                products_per_single_run: int = blueprint_dict['products'][0]['quantity']
                single_run_time: int = blueprint_dict['time']
                next_materials = blueprint_dict['materials']
                # получаем информацию о производственных индексах в системе, где крафтится этот продукт
                system_indices, cost_index = get_industry_cost_index(
                    material_tid,
                    activity,
                    industry_cost_indices)
                # в этой точке понятно, что данный материал можно произвести, поэтому список материалов для него будет
                # пополнен более сложным способом
                next_industry: profit.QIndustryTree = profit.QIndustryTree(
                    material_bp_tid,
                    eve_sde_tools.get_item_name_by_type_id(sde_type_ids, material_bp_tid),
                    material_tid,
                    material_name,
                    material_produce_action,
                    products_per_single_run,
                    single_run_time,
                    system_indices,
                    cost_index)
                q_material.set_industry(next_industry)
                # повторяем те же самые действия по формированию списка задействованных материалов, но теперь уже
                # для нового уровня вложенности
                generate_materials_tree(
                    next_materials,
                    next_industry,
                    sde_type_ids,
                    sde_bp_materials,
                    sde_market_groups,
                    eve_market_prices_data,
                    industry_cost_indices)
                break
    # считаем EIV, который потребуется для вычисления стоимости job cost
    curr_industry.set_estimated_items_value(
        math.ceil(sum([_.adjusted_price * _.quantity for _ in curr_industry.materials]))
    )


# генерация чертежа/чертежей (в результате запуска научки) для точного расчёта научки с учётом datacores и decryptors
def schedule_industry_job__invent(
        # идентификатор чертежа, для которого производится планирование производственной работы
        blueprint_type_id: int,
        blueprint_runs: int,
        blueprint_me: int,
        blueprint_te: int,
        # выходной список со всеми возможными материалами, задействованными в производстве
        curr_industry: profit.QIndustryTree,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        # esi данные, загруженные с серверов CCP
        eve_market_prices_data,
        # индексы стоимости производства для различных систем (системы и продукция заданы в настройках роутинга)
        industry_cost_indices:  typing.List[profit.QIndustryCostIndices]):
    # пытаемся получить чертёж и параметры инвента (если он предполагается для этого чертежа)
    source_blueprint_type_id, invent_dict = eve_sde_tools.get_blueprint_type_id_by_invention_product_id(
        blueprint_type_id,
        sde_bp_materials)
    # если инвент данного чертежа возможен, то добавляем в дерево работ декрипторы и датакоры
    if not source_blueprint_type_id:
        return

    # в этой точке понятно, что чертёж можно (и нужно) инвентить, поэтому получаем список материалов для инвента
    # (и предварительной копирки)
    copied_blueprint_name: str = eve_sde_tools.get_item_name_by_type_id(sde_type_ids, source_blueprint_type_id)
    invented_blueprint_name: str = eve_sde_tools.get_item_name_by_type_id(sde_type_ids, blueprint_type_id)
    blueprints_market_group: int = 2
    blueprints_group_name: str = sde_market_groups[str(blueprints_market_group)]['nameID']['en']

    # пытаемся получить чертёж и параметры копирки (если она предполагается для этого чертежа)
    copying_dict = eve_sde_tools.get_blueprint_copying_activity(
        sde_bp_materials,
        source_blueprint_type_id)
    # если копирка данного чертежа возможен, то добавляем в дерево работ копирку и материалы
    if copying_dict:
        copying_run_time: int = copying_dict.get('time', 0)
        _copying_materials = copying_dict.get('materials', [])

        # пополняем список материалов T1 чертежом
        copying_material: profit.QMaterial = profit.QMaterial(
            source_blueprint_type_id,
            1,
            copied_blueprint_name,
            blueprints_market_group,
            blueprints_group_name,
            0.0,  # чертёж не перевозится, он копируется и инвентится "на месте"
            0.0,  # TODO: х.з. пока, надо ли что-то тут вписать по цене?
            0.0)
        curr_industry.append_material(copying_material)

        # получаем информацию о производственных индексах в системе, где крафтится этот продукт
        system_indices, cost_index = get_industry_cost_index(
            source_blueprint_type_id,
            'copying',
            industry_cost_indices)

        # считаем копирку
        copying_industry: profit.QIndustryTree = profit.QIndustryTree(
            source_blueprint_type_id,
            copied_blueprint_name,
            source_blueprint_type_id,
            copied_blueprint_name,
            profit.QIndustryAction.copying,
            1,
            copying_run_time,
            system_indices,
            cost_index)
        copying_industry.set_blueprint_runs_per_single_copy(1)
        # copying_industry.set_probability(1.0)
        copying_material.set_industry(copying_industry)

        # в список материалов подкладываем чертёж, который должен скопироваться N раз
        # invent_materials = _invent_materials[:]
        copying_materials = []
        copying_materials.append({'typeID': source_blueprint_type_id, 'quantity': 1})
        copying_materials.extend(_copying_materials)

        # считаем работу с материалами для этого типа копирки (копирка с материалами существует только для T2 BPO,
        # есть и такие в Евке)
        generate_materials_tree(
            copying_materials,
            copying_industry,
            sde_type_ids,
            sde_bp_materials,
            sde_market_groups,
            eve_market_prices_data,
            industry_cost_indices)

    # пополняем список материалов T2 чертежом
    invented_material: profit.QMaterial = profit.QMaterial(
        blueprint_type_id,
        1,
        invented_blueprint_name,
        blueprints_market_group,
        blueprints_group_name,
        0.0,  # чертёж не перевозится, он копируется и инвентится "на месте"
        0.0,  # TODO: х.з. пока, надо ли что-то тут вписать по цене?
        0.0)
    curr_industry.append_material(invented_material)

    # теперь к T2-чертежу подключаем инвент-работу
    invent_dict = invent_dict['activities']['invention']
    assert len(invent_dict.get('products', [])) >= 1
    invent_product_dict = next((p for p in invent_dict['products'] if p['typeID'] == blueprint_type_id), None)
    assert invent_product_dict is not None
    # получаем параметры инвента: (1) кол-во прогонов Т2 чертежа?
    blueprint_runs_per_single_copy: int = invent_product_dict['quantity']
    invent_run_time: int = invent_dict['time']
    _invent_materials = invent_dict['materials']
    invent_probability: float = invent_product_dict['probability']

    # получаем информацию о производственных индексах в системе, где крафтится этот продукт
    system_indices, cost_index = get_industry_cost_index(
        blueprint_type_id,
        'invention',
        industry_cost_indices)

    # инициализируем базовый объект-справочник со сведениями о производстве
    invent_industry: profit.QIndustryTree = profit.QIndustryTree(
        source_blueprint_type_id,
        copied_blueprint_name,
        blueprint_type_id,
        invented_blueprint_name,
        profit.QIndustryAction.invent,
        1,
        invent_run_time,
        system_indices,
        cost_index)
    invent_industry.set_blueprint_runs_per_single_copy(blueprint_runs_per_single_copy)
    invent_industry.set_probability(invent_probability)
    invented_material.set_industry(invent_industry)

    # в список материалов подкладываем чертёж, который должен скопироваться N раз
    #invent_materials = _invent_materials[:]
    invent_materials = []
    invent_materials.append({'typeID': source_blueprint_type_id, 'quantity': 1})
    invent_materials.extend(_invent_materials)

    if blueprint_me == 2 and blueprint_te == 4:  # and blueprint_runs == blueprint_runs_per_single_copy:
        pass
    elif blueprint_me == (2+2) and blueprint_te == (4+10) and blueprint_runs == (blueprint_runs_per_single_copy+1):
        # Accelerant Decryptor : probability +20%, runs +1, me +2, te +10
        invent_materials.append({'typeID': 34201, 'quantity': 1})
        invent_industry.set_decryptor_probability(+0.2)
    elif blueprint_me == (2-1) and blueprint_te == (4+4) and blueprint_runs == (blueprint_runs_per_single_copy+4):
        # Attainment Decryptor : probability +80%, runs +4, me -1, te +4
        invent_materials.append({'typeID': 34202, 'quantity': 1})
        invent_industry.set_decryptor_probability(+0.8)
    elif blueprint_me == (2-2) and blueprint_te == (4+2) and blueprint_runs == (blueprint_runs_per_single_copy+9):
        # Augmentation Decryptor : probability -40%, runs +9, me -2, te +2
        invent_materials.append({'typeID': 34203, 'quantity': 1})
        invent_industry.set_decryptor_probability(-0.4)
    elif blueprint_me == (2+1) and blueprint_te == (4-2) and blueprint_runs == (blueprint_runs_per_single_copy+2):
        # Optimized Attainment Decryptor : probability +90%, runs +2, me +1, te -2
        invent_materials.append({'typeID': 34207, 'quantity': 1})
        invent_industry.set_decryptor_probability(+0.9)
    elif blueprint_me == (2+2) and blueprint_te == (4+0) and blueprint_runs == (blueprint_runs_per_single_copy+7):
        # Optimized Augmentation Decryptor : probability -10%, runs +7, me +2, te +0
        invent_materials.append({'typeID': 34208, 'quantity': 1})
        invent_industry.set_decryptor_probability(-0.1)
    elif blueprint_me == (2+1) and blueprint_te == (4-2) and blueprint_runs == (blueprint_runs_per_single_copy+3):
        # Parity Decryptor : probability +50%, runs +3, me +1, te -2
        invent_materials.append({'typeID': 34204, 'quantity': 1})
        invent_industry.set_decryptor_probability(+0.5)
    elif blueprint_me == (2+3) and blueprint_te == (4+6) and blueprint_runs == (blueprint_runs_per_single_copy+0):
        # Process Decryptor : probability +10%, runs +0, me +3, te +6
        invent_materials.append({'typeID': 34205, 'quantity': 1})
        invent_industry.set_decryptor_probability(+0.1)
    elif blueprint_me == (2+1) and blueprint_te == (4+8) and blueprint_runs == (blueprint_runs_per_single_copy+2):
        # Symmetry Decryptor : probability +0, runs +2, me +1, te +8
        invent_materials.append({'typeID': 34206, 'quantity': 1})
        invent_industry.set_decryptor_probability(+0.0)
    else:
        assert 0

    # составляем дерево материалов, которые будут использоваться для инвента
    generate_materials_tree(
        invent_materials,
        invent_industry,
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        eve_market_prices_data,
        industry_cost_indices)


def generate_industry_tree(
        # вход и выход для расчёта
        calc_input,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        # esi данные, загруженные с серверов CCP
        eve_market_prices_data,
        # индексы стоимости производства для различных систем (системы и продукция заданы в настройках роутинга)
        industry_cost_indices:  typing.List[profit.QIndustryCostIndices]) -> profit.QIndustryTree:
    blueprint_type_id = calc_input.get('bptid')
    assert blueprint_type_id is not None

    # далее готовимся обсчитывать только рентабельность manufacturing-производства, для инвентов на входе надо менять
    # формат входных данных (чертёж м.б. один, а продукты у него разные)
    bp0_dict = eve_sde_tools.get_blueprint_any_activity(sde_bp_materials, 'manufacturing', blueprint_type_id)
    assert bp0_dict is not None
    assert len(bp0_dict.get('products', [])) == 1
    product_type_id: int = bp0_dict['products'][0]['typeID']
    single_run_quantity: int = bp0_dict['products'][0]['quantity']

    # из справочной информации о чертеже здесь интересны только материалы, которые будут использоваться в производстве
    base_materials = bp0_dict.get('materials')
    assert base_materials is not None

    # получаем информацию о производственных индексах в системе, где крафтится этот продукт
    system_indices, cost_index = get_industry_cost_index(
        product_type_id,
        'manufacturing',
        industry_cost_indices)

    # инициализируем базовый объект-справочник со сведениями о производстве
    base_industry: profit.QIndustryTree = profit.QIndustryTree(
        blueprint_type_id,
        eve_sde_tools.get_item_name_by_type_id(sde_type_ids, blueprint_type_id),
        product_type_id,
        eve_sde_tools.get_item_name_by_type_id(sde_type_ids, product_type_id),
        profit.QIndustryAction.manufacturing,
        single_run_quantity,
        bp0_dict['time'],
        system_indices,
        cost_index)
    base_industry.set_me(calc_input.get('me', 2))

    # планируем работу (инвент если потребуется)
    schedule_industry_job__invent(
        blueprint_type_id,
        calc_input.get('qr', 10),
        calc_input.get('me', 2),
        calc_input.get('te', 4),
        base_industry,
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        eve_market_prices_data,
        industry_cost_indices)

    # составляем дерево материалов, которые будут использоваться в производстве
    generate_materials_tree(
        base_materials,
        base_industry,
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        eve_market_prices_data,
        industry_cost_indices)

    return base_industry


# TODO: см. также get_optimized_runs_quantity
def get_optimized_runs_quantity(
        # кол-во продуктов, требуемых (с учётом предыдущей эффективности)
        need_quantity: int,
        # сведения о типе производства: кол-во продуктов, которые будут получены за один раз чертежа, признак - формула
        # ли, или реакция продукта? параметры чертежа? и т.п.
        industry: profit.QIndustryTree,
        # настройки генерации отчёта, см. также eve_conveyor_tools.py : setup_blueprint_details
        industry_plan_customization: typing.Optional[profit.QIndustryPlanCustomization] = None) -> typing.Tuple[int, int]:
    # расчёт кол-ва ранов для данного чертежа (учёт настроек оптимизации производства)
    runs_number_per_day = None
    if industry.action == profit.QIndustryAction.reaction:
        # если не None, то настроенное кол-во ранов для реакций
        customized_reaction_runs = industry_plan_customization.reaction_runs if industry_plan_customization else None
        if customized_reaction_runs:
            runs_number_per_day = customized_reaction_runs
    else:
        # если не None, то длительность запуска производственных работ
        customized_industry_time = industry_plan_customization.industry_time if industry_plan_customization else None
        if customized_industry_time:
            if industry.single_run_time >= customized_industry_time:
                runs_number_per_day = 1
            elif industry.single_run_time > 0:
                runs_number_per_day = math.ceil(customized_industry_time / industry.single_run_time)
    # если заданы настройки оптимизации, то считаем кол-во чертежей/ранов с учётом настроек
    if runs_number_per_day:
        # реакции: планируется к запуску N чертежей по, как правило, 15 ранов (сутки)
        # производство: планируется к запуску N ранов для, как правило, оригиналов (длительностью в сутки)
        optimized_blueprints_quantity: int = math.ceil(need_quantity / (industry.products_per_single_run * runs_number_per_day))
        optimized_runs_quantity: int = runs_number_per_day
        return optimized_blueprints_quantity, optimized_runs_quantity
    # если настройки оптимизации не заданы, то считаем кол-во чертежей/ранов с учётом лишь только потребностей
    else:
        blueprints_or_runs: int = math.ceil(need_quantity / industry.products_per_single_run)
        runs_quantity: int = blueprints_or_runs
        return 1, runs_quantity


def calculate_purchased_ratio(
        purchase_quantity: int,
        # соотношение использования материалов в данном текущем цикле производственной активности
        usage_chain: float,
        # указатели на объекты, поля которых будут изменены
        purchased_material: profit.QPlannedMaterial,
        cached_material: profit.QIndustryMaterial):
    # считаем пропорцию использования закупленных материалов
    usage_ratio: float = 1.0 * purchase_quantity
    # для покупных материалов накапливаем сведения о пропорции материала к общему целому производимому базовому
    # продукту (например к десятку t2 пушек)
    cached_material_ratio_before: float = cached_material.purchased_ratio
    cached_material.consume_purchased_ratio(usage_chain * usage_ratio)
    cached_material_ratio_after: float = cached_material.purchased_ratio
    purchased_material.store_summary_ratio(
        cached_material_ratio_before,
        cached_material_ratio_after)
    # сохраняем сведения о пропорциях использования материалов
    purchased_material.store_usage_ratio(usage_ratio)


def calculate_industry_ratio(
        materials_quantity: int,
        industry_output: int,
        # указатели на объекты, поля которых будут изменены
        produced_material: profit.QPlannedMaterial,
        # справочники со сведениями о типе производства
        industry: profit.QIndustryTree,
        # справочник текущего производства с настройками оптимизации процесса
        industry_plan: profit.QIndustryPlan) -> float:
    if industry.action and industry.action in [profit.QIndustryAction.invent]:
        # сохраняем пропорцию использования текущего материала для текущей работы
        invent_probability: float = industry.invent_probability
        decryptor_probability: float = 1.0
        if industry.decryptor_probability is not None:
            decryptor_probability: float = 1.0 + industry.decryptor_probability  # сумма м.б. меньше 1.0
        skill_probability: float = 1.0
        if industry_plan.customization and industry_plan.customization.min_probability:
            skill_probability = (100.0 + industry_plan.customization.min_probability) / 100.0
        probability: float = invent_probability * decryptor_probability * skill_probability
        usage_ratio: float = float(materials_quantity) / industry_output * (1 / probability)
        # сохраняем сведения о пропорциях использования материалов
        produced_material.store_usage_ratio(usage_ratio)
        return usage_ratio
    else:
        # сохраняем пропорцию использования текущего материала для текущей работы
        usage_ratio: float = float(materials_quantity) / industry_output
        # сохраняем сведения о пропорциях использования материалов
        produced_material.store_usage_ratio(usage_ratio)
        return usage_ratio


def copy_reused_industry_plan__internal(
        # исходные данные для формирования отчёта и плана производства
        planned_material: typing.Optional[profit.QPlannedMaterial],
        # соотношение использования материалов в данном текущем цикле производственной активности
        usage_chain: float,
        # справочники, генерируемые во время работы алгоритма
        industry: profit.QIndustryTree,
        # план производства, из которого будут копироваться расход материалов в текущий план
        similar_activity: profit.QPlannedActivity,
        # справочник текущего производства с настройками оптимизации процесса
        industry_plan: profit.QIndustryPlan) -> profit.QPlannedActivity:
    # проверяем, что работа алгоритма на предыдущих этапах была корректна
    assert len(industry.materials) > 0
    assert planned_material is not None
    assert planned_material.obtaining_plan is not None
    assert planned_material.obtaining_plan.reused_duplicate
    assert planned_material.obtaining_plan.activity_plan is not None

    # создаём activity plan, как копию ранее существующей, с теми же параметрами и настройками производства
    reused_activity: profit.QPlannedActivity = planned_material.obtaining_plan.activity_plan
    current_level_activity: profit.QPlannedActivity = profit.QPlannedActivity(
        industry,
        reused_activity.planned_blueprint,
        reused_activity.planned_blueprints)

    # кешируем указатель на репозиторий материалов
    materials_repository: profit.QIndustryMaterialsRepository = industry_plan.materials_repository
    # рекурсивно обходим все материалы, применяем настройки оптимизации производства и применяем сведения об ME
    for m in industry.materials:
        cached_material: typing.Optional[profit.QIndustryMaterial] = materials_repository.get_material(m.type_id)
        if cached_material is None:
            cached_material = materials_repository.register_material(m.type_id, m)
        # сохраняем сводку по использованию материала для формирования последующего отчёта (не меняется)
        cached_material_quantity_before: int = cached_material.purchased + cached_material.manufactured

        # поиск материала, которого было более чем достаточно (перепроизводство)
        similar_quantity: typing.Optional[int] = None
        for similar_material in similar_activity.planned_materials:
            if similar_material.material.type_id == m.type_id:
                similar_quantity = similar_material.quantity_with_efficiency
                break
        assert similar_quantity is not None

        # копируем закуп материала, если его производство невозможно, для этого копируем требуемое кол-во материала
        # с учётом текущего чертежа
        if m.industry is None:
            purchase_quantity: int = similar_quantity

            # составляем план покупки материала в рамках текущего плана производства
            purchased_material: profit.QPlannedMaterial = profit.QPlannedMaterial(
                m,
                planned_material,
                purchase_quantity,
                usage_chain)
            current_level_activity.append_planned_material(purchased_material)
            purchased_material.obtaining_plan.store_purchase(0, purchase_quantity)

            # готовим копирование текущей производственной активности с нулевыми значениями расхода материалов
            purchased_material.obtaining_plan.mark_as_reused_duplicate(None)

            # сохраняем в репозиторий материалов сведения о запланированной покупке
            cached_material.store_purchased(0)
            # cached_material.set_last_known_planned_material(purchased_material)

            # сохраняем сводку по использованию материала для формирования последующего отчёта
            purchased_material.store_summary_quantity(
                cached_material_quantity_before,
                cached_material_quantity_before)

            # считаем пропорцию использования закупленных материалов
            calculate_purchased_ratio(
                purchase_quantity,
                usage_chain,
                purchased_material,
                cached_material)
        else:
            used_rest_materials: int = similar_quantity

            # если выполняется повторный расчёт использования материалов с нулевыми значениями производственной
            # активности, то копируем цепочку материалов "до конца", т.к. например планетарка для fuel blocks
            # должна будет пересчитываться ещё не раз, а пропорции востребованности материалов будут меняться
            reused_material: profit.QPlannedMaterial = copy_reused_industry_plan(
                used_rest_materials,
                planned_material,
                m,
                cached_material,
                usage_chain,
                industry_plan)
            current_level_activity.append_planned_material(reused_material)

            # сохраняем сводку по использованию материала для формирования последующего отчёта
            reused_material.store_summary_quantity(
                cached_material_quantity_before,
                cached_material_quantity_before)

    return current_level_activity


def copy_reused_industry_plan(
        reused_materials_quantity: int,
        # исходные данные для формирования отчёта и плана производства
        planned_material: typing.Optional[profit.QPlannedMaterial],
        current_material: profit.QMaterial,
        cached_material: profit.QIndustryMaterial,
        # соотношение использования материалов в данном текущем цикле производственной активности
        usage_chain: float,
        # справочник текущего производства с настройками оптимизации процесса
        industry_plan: profit.QIndustryPlan) -> profit.QPlannedMaterial:
    assert reused_materials_quantity > 0
    assert planned_material is not None
    assert current_material is not None
    assert current_material.industry is not None
    assert cached_material is not None

    # составляем план использования материала в рамках текущего плана производства
    reused_material: profit.QPlannedMaterial = profit.QPlannedMaterial(
        current_material,
        planned_material,
        reused_materials_quantity,
        usage_chain)

    # готовим копирование текущей производственной активности с нулевыми значениями расхода материалов
    assert cached_material.last_known_planned_material is not None
    # обязательно надо убедиться в том, что копируемый материал ПРОИЗВЕДЁН, на не куплен или не выбран из ассетов
    assert cached_material.last_known_planned_material.obtaining_plan is not None
    reused_material.obtaining_plan.mark_as_reused_duplicate(
        cached_material.last_known_planned_material.obtaining_plan.activity_plan
    )

    # сохраняем недостаточное и невостребованное кол-во материалов для отчёта
    reused_material.obtaining_plan.store_manufacturing_prerequisites(
        0,
        cached_material.manufacture_rest,
        cached_material.last_known_planned_material.obtaining_plan.industry_output)

    # сохраняем пропорцию использования текущего материала для текущей работы
    usage_ratio: float = calculate_industry_ratio(
        reused_materials_quantity,
        cached_material.last_known_planned_material.obtaining_plan.industry_output,
        reused_material,
        current_material.industry,
        industry_plan)

    # если выполняется повторный расчёт использования материалов с нулевыми значениями производственной
    # активности, то копируем цепочку материалов "до конца", т.к. например планетарка для fuel blocks
    # должна будет пересчитываться ещё не раз, а пропорции востребованности материалов будут меняться
    next_level_activity: profit.QPlannedActivity = copy_reused_industry_plan__internal(
        reused_material,
        usage_chain * usage_ratio,
        current_material.industry,
        cached_material.last_known_planned_material.obtaining_plan.activity_plan,
        industry_plan)
    reused_material.obtaining_plan.store_manufacturing_activity_plan(next_level_activity)

    return reused_material


def generate_industry_plan__internal(
        # исходные данные для формирования отчёта и плана производства
        planned_material: typing.Optional[profit.QPlannedMaterial],
        planned_blueprints: int,
        planned_runs: int,
        planned_quantity: int,
        # соотношение использования материалов в данном текущем цикле производственной активности
        usage_chain: float,
        # справочники, генерируемые во время работы алгоритма
        industry: profit.QIndustryTree,
        # справочник текущего производства с настройками оптимизации процесса
        industry_plan: profit.QIndustryPlan) -> profit.QPlannedActivity:
    assert len(industry.materials) > 0
    assert planned_blueprints > 0
    assert planned_runs > 0
    assert planned_quantity > 0

    # формируем чертёж
    current_level_blueprint: profit.QPlannedBlueprint = profit.QPlannedBlueprint(
        profit.QMaterial(industry.blueprint_type_id,
                         1,
                         industry.blueprint_name,
                         2,
                         "Blueprints & Reactions",  # sde_market_groups[str(blueprints_market_group)]['nameID']['en']
                         0.0,  # чертёж не перевозится, он копируется и инвентится "на месте"
                         0,
                         0),
        1.0,
        planned_quantity,
        planned_runs,
        industry.me,
        0)

    current_level_activity: profit.QPlannedActivity = profit.QPlannedActivity(
        industry,
        current_level_blueprint,
        planned_blueprints)

    # кешируем указатель на репозиторий материалов
    materials_repository: profit.QIndustryMaterialsRepository = industry_plan.materials_repository
    # рекурсивно обходим все материалы, применяем настройки оптимизации производства и применяем сведения об ME
    for m in industry.materials:
        cached_material: typing.Optional[profit.QIndustryMaterial] = materials_repository.get_material(m.type_id)
        if cached_material is None:
            cached_material = materials_repository.register_material(m.type_id, m)
        # сохраняем сводку по использованию материала для формирования последующего отчёта
        cached_material_quantity_before: int = cached_material.purchased + cached_material.manufactured

        # считаем необходимое и достаточное кол-во материала с учётом me текущего уровня
        if m.industry and m.industry.action in [profit.QIndustryAction.copying, profit.QIndustryAction.invent]:
            quantity_with_efficiency: int = 1 * eve_efficiency.get_industry_material_efficiency(
                industry.action.name,
                1,  # кол-во run-ов чертежа (инвент или копирка считается отдельно)
                m.quantity,  # кол-во из исходного чертежа (до учёта всех бонусов)
                0)  # me на инвенты и копирку не действуют
        else:  # if industry.action in [profit.QIndustryAction.manufacturing, profit.QIndustryAction.reaction]:
            quantity_with_efficiency: int = planned_blueprints * eve_efficiency.get_industry_material_efficiency(
                industry.action.name,
                planned_runs,  # кол-во run-ов (кол-во продуктов, которые требует предыдущий уровень)
                m.quantity,  # кол-во из исходного чертежа (до учёта всех бонусов)
                industry.me if industry.action == profit.QIndustryAction.manufacturing else 0)  # me предыдущего чертежа

        # планируем закуп материала, если его производство невозможно, для этого считаем требуемое кол-во материала
        # с учётом текущего чертежа
        if m.industry is None:
            purchase_quantity: int = quantity_with_efficiency

            # составляем план покупки материала в рамках текущего плана производства
            purchased_material: profit.QPlannedMaterial = profit.QPlannedMaterial(
                m,
                planned_material,
                purchase_quantity,
                usage_chain)
            current_level_activity.append_planned_material(purchased_material)
            purchased_material.obtaining_plan.store_purchase(0, purchase_quantity)  # TODO: not_enough

            # сохраняем в репозиторий материалов сведения о запланированной покупке
            cached_material.store_purchased(purchase_quantity)
            # cached_material.set_last_known_planned_material(purchased_material)

            # сохраняем сводку по использованию материала для формирования последующего отчёта
            cached_material_quantity_after: int = cached_material.purchased + cached_material.manufactured
            purchased_material.store_summary_quantity(
                cached_material_quantity_before,
                cached_material_quantity_after)

            # считаем пропорцию использования закупленных материалов
            calculate_purchased_ratio(
                purchase_quantity,
                usage_chain,
                purchased_material,
                cached_material)
        else:
            # проверяем, имеются ли в репозитории остатки материалов? и пересчитываем употреблённое кол-во
            # материалов на складе, а также зарезервированное кол-во в уже запущенном производстве
            # сохраняем остатки материала в репозитории, с тем чтобы в следующих шагах расчёта они уже были учтены
            # вычисляем недоступное количество материала, которое надо произвести
            not_enough_materials, used_rest_materials = cached_material.consume_industry_rest(quantity_with_efficiency)

            if used_rest_materials:
                # если выполняется повторный расчёт использования материалов с нулевыми значениями производственной
                # активности, то копируем цепочку материалов "до конца", т.к. например планетарка для fuel blocks
                # должна будет пересчитываться ещё не раз, а пропорции востребованности материалов будут меняться
                reused_material: profit.QPlannedMaterial = copy_reused_industry_plan(
                    used_rest_materials,
                    planned_material,
                    m,
                    cached_material,
                    usage_chain,
                    industry_plan)
                current_level_activity.append_planned_material(reused_material)
                # сохраняем сводку по использованию материала для формирования последующего отчёта
                reused_material.store_summary_quantity(
                    cached_material_quantity_before,
                    cached_material_quantity_before)

            if not_enough_materials:
                # составляем план использования материала в рамках текущего плана производства
                produced_material: profit.QPlannedMaterial = profit.QPlannedMaterial(
                    m,
                    planned_material,
                    quantity_with_efficiency,
                    usage_chain)
                current_level_activity.append_planned_material(produced_material)

                # вычисляем кол-во runs по текущим сведениям о типе производства
                next_industry_level_blueprints, next_industry_level_runs = get_optimized_runs_quantity(
                    not_enough_materials,
                    m.industry,
                    industry_plan_customization=industry_plan.customization)
                # учитываем сведения о кол-ве runs текущего чертежа и считаем кол-во материалов данного типа с
                # учётом ME
                # материалы, которые не производятся, а закупаются, считаются as is
                single_blueprint_optimized_quantity: int = \
                    next_industry_level_runs * m.industry.products_per_single_run
                # получаем то количество материала, которое будет получено в результате запуска производства
                next_industry_level_planned_quantity: int = \
                    next_industry_level_blueprints * single_blueprint_optimized_quantity

                # считаем количество невостребованного материала в случае перепроизводства и сохраняем
                # эту информацию
                next_industry_level_rest_quantity: int = \
                    next_industry_level_planned_quantity - not_enough_materials
                cached_material.store_manufacturing(
                    next_industry_level_planned_quantity,
                    next_industry_level_rest_quantity)
                # сохраняем недостаточное и невостребованное кол-во материалов для отчёта
                produced_material.obtaining_plan.store_manufacturing_prerequisites(
                    not_enough_materials,
                    cached_material.manufacture_rest,
                    next_industry_level_planned_quantity)
                # сохраняем сведения о последнем известном производственном процессе, чтобы относительно него
                # рассчитывать расход остатков (пропорционально)
                cached_material.set_last_known_planned_material(produced_material)

                # сохраняем сводку по использованию материала для формирования последующего отчёта
                cached_material_quantity_after: int = cached_material.purchased + cached_material.manufactured
                produced_material.store_summary_quantity(
                    cached_material_quantity_before,
                    cached_material_quantity_after)

                # сохраняем пропорцию использования текущего материала для текущей работы
                usage_ratio: float = calculate_industry_ratio(
                    produced_material.quantity_with_efficiency,
                    next_industry_level_planned_quantity,
                    produced_material,
                    m.industry,
                    industry_plan)

                # составляем план производства следующего уровня: план производства выше рассчитан для одного
                # чертежа, размножаем это количество на кол-во чертежей (иными словами : один чертёж = одни
                # производственные сутки в соответствии с настройками оптимизации)
                next_level_activity: profit.QPlannedActivity = generate_industry_plan__internal(
                    produced_material,
                    next_industry_level_blueprints,
                    next_industry_level_runs,
                    next_industry_level_planned_quantity,
                    usage_chain * usage_ratio,
                    m.industry,
                    industry_plan)
                produced_material.obtaining_plan.store_manufacturing_activity_plan(next_level_activity)

            if not used_rest_materials and not not_enough_materials:
                assert 0  # TODO: это случай с расчётом остатков в коробках

                # если материал и не производится, и не берётся из остатков производства, то он берётся либо из
                # ассетов (assets), либо находится в процессе производства (in_progress)
                warehoused_material: profit.QPlannedMaterial = profit.QPlannedMaterial(
                    m,
                    planned_material,
                    quantity_with_efficiency,
                    usage_chain)
                current_level_activity.append_planned_material(warehoused_material)

                # сохраняем недостаточное и невостребованное кол-во материалов для отчёта
                warehoused_material.obtaining_plan.store_manufacturing_prerequisites(
                    not_enough_materials,
                    cached_material.manufacture_rest,
                    0)
                # сохраняем сводку по использованию материала для формирования последующего отчёта
                warehoused_material.store_summary_quantity(
                    cached_material_quantity_before,
                    cached_material_quantity_before)

                # НЕ сохраняем пропорцию использования текущего материала для текущей работы
                # TODO: usage_ratio: float = calculate_industry_ratio(
                #    produced_material.quantity_with_efficiency,
                #    cached_material.last_known_planned_material.obtaining_plan.industry_output,
                #    produced_material)

    return current_level_activity


def generate_industry_plan(
        customized_runs: int,
        base_industry: profit.QIndustryTree,
        # настройки генерации отчёта, см. также eve_conveyor_tools.py : setup_blueprint_details
        calc_customization=None) -> profit.QIndustryPlan:
    assert len(base_industry.materials) > 0
    assert customized_runs > 0

    # настройки оптимизации производства: реакции на 15 ран (сутки) и производство в зависимости от времени (сутки)
    # см. также eve_conveyor_tools.py : setup_blueprint_details
    industry_plan_customization: typing.Optional[profit.QIndustryPlanCustomization] = None
    if calc_customization:
        industry_plan_customization = profit.QIndustryPlanCustomization(
            reaction_runs=calc_customization.get('reaction_runs'),
            industry_time=calc_customization.get('industry_time'),
            min_probability=calc_customization.get('min_probability'))

    # формируем отчёт с планом производства
    industry_plan: profit.QIndustryPlan = profit.QIndustryPlan(
        customized_runs,
        industry_plan_customization)

    # рекурсивно обходим все материалы, применяем настройки оптимизации производства и применяем сведения об ME;
    # в настройках производства д.б. заранее задано кол-во запусков - учитываем параметр customized_runs
    base_activity: profit.QPlannedActivity = generate_industry_plan__internal(
        None,
        1,
        customized_runs,
        base_industry.products_per_single_run * customized_runs,
        1.0,
        base_industry,
        industry_plan)
    industry_plan.set_base_planned_activity(base_activity)

    return industry_plan


def render_report(
        glf,
        # данные о продуктах, которые надо отобразить в отчёте
        industry_plan: profit.QIndustryPlan,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_bp_materials,
        sde_market_groups,
        sde_icon_ids):
    base_industry: profit.QIndustryTree = industry_plan.base_industry

    def generate_manuf_materials_list(__it157: profit.QIndustryTree):
        res: str = ''
        for m in __it157.materials:
            res += '<span style="white-space:nowrap">' \
                   '<img class="icn24" src="{src}"> {q:,d} x {nm} ' \
                   '</span>\n'.format(src=render_html.__get_img_src(m.type_id, 32), q=m.quantity, nm=m.name)
        return res

    glf.write('<div class="container-fluid">')
    glf.write('<div class="media">\n'
              ' <div class="media-left"><img class="media-object icn64" src="{src1}" alt="{nm1}"></div>\n'
              ' <div class="media-body">\n'
              '  <h4 class="media-heading">{nm1}</h4>\n'
              '<p>\n'
              'EveUniversity {nm2} wiki: <a href="https://wiki.eveuniversity.org/{nm2}">https://wiki.eveuniversity.org/{nm2}</a><br/>\n'
              'EveMarketer {nm2} tradings: <a href="https://evemarketer.com/types/{pid}">https://evemarketer.com/types/{pid}</a><br/>\n'
              'EveMarketer {nm2} Blueprint tradings: <a href="https://evemarketer.com/types/{bid}">https://evemarketer.com/types/{bid}</a><br/>\n'
              'Adam4EVE {nm2} manufacturing calculator: <a href="https://www.adam4eve.eu/manu_calc.php?typeID={bid}">https://www.adam4eve.eu/manu_calc.php?typeID={bid}</a><br/>\n'
              'Adam4EVE {nm2} price history: <a href="https://www.adam4eve.eu/commodity.php?typeID={pid}">https://www.adam4eve.eu/commodity.php?typeID={pid}</a><br/>\n'
              'Adam4EVE {nm2} Blueprint price history: <a href="https://www.adam4eve.eu/commodity.php?typeID={bid}">https://www.adam4eve.eu/commodity.php?typeID={bid}</a>\n'
              '</p>\n'
              ' </div> <!--media-body-->\n'
              '</div> <!--media-->\n'
              '<hr>\n'
              '<div class="media">\n'
              ' <div class="media-left"><img class="media-object icn64" src="{src2}" alt="Требуемые комплектующие"></div>\n'
              ' <div class="media-body">\n'
              '  <h4 class="media-heading">Организация производства <small>Требуемые комплектующие</small></h4>\n'
              '  {mml}'
              ' </div> <!--media-body-->\n'
              '</div> <!--media-->\n'
              '<hr>\n'
              '<div class="media">\n'
              ' <div class="media-left"><img class="media-object icn64" src="{src0}"></div>\n'
              ' <div class="media-body">\n'
              '<!--<p><var>Efficiency</var> = <var>Required</var> * (100 - <var>material_efficiency</var> - 1 - 4.2) / 100,'
              '<br>where <var>material_efficiency</var> for unknown and unavailable blueprint is ?.</p>-->\n'
              '<p>Число прогонов: {cr}<br>\n'
              'Экономия материалов при производстве: -{me}.0%<br>\n'
              'Экономия материалов при производстве (от других чертежей): -10.0%<br>\n'
              'Установленный модификатор: -4.2%<br>\n'
              'Бонус профиля сооружения: -1.0%<br>\n'
              'Длительность производственных работ: {mtm}<br>\n'
              'Длительность запуска формул и реакций: {ftm}<br>\n'
              'Минимальная вероятность успеха по навыкам и имплантам: {mip}</p>'
              '<hr>\n'.
              format(bid=base_industry.blueprint_type_id,
                     nm1=base_industry.blueprint_name,
                     src1=render_html.__get_img_src(base_industry.blueprint_type_id, 64),
                     pid=base_industry.product_type_id,
                     nm2=base_industry.product_name,
                     src2=render_html.__get_img_src(base_industry.product_type_id, 64),
                     src0=render_html.__get_icon_src(1436, sde_icon_ids),
                     mml=generate_manuf_materials_list(base_industry),
                     cr=industry_plan.customized_runs,
                     me=base_industry.me,
                     mtm='(настройка не задана)' if not industry_plan.customization or
                                                    not industry_plan.customization.industry_time else
                         '{:.1f} часов'.format(float(industry_plan.customization.industry_time) / (5*60*60)),
                     ftm='(настройка не задана)' if not industry_plan.customization or
                                                    not industry_plan.customization.reaction_runs else
                         '{} прогонов'.format(industry_plan.customization.reaction_runs),
                     mip='(настройка не задана)' if not industry_plan.customization or
                                                    not industry_plan.customization.min_probability else
                         '{:.1f}%'.format(industry_plan.customization.min_probability)
              ))

    def generate_components_header(with_current_industry_progress: bool):
        glf.write('<tr>\n'
                  '<th style="width:50px;">#</th>\n'
                  '<th>Материалы</th>\n'
                  + ('<th>Имеется +<br/>Производится</th>\n' if with_current_industry_progress else '')
                  + '<th>Без<br/>ME</th>\n'
                  + '<th>Учёт<br/>ME</th>\n'
                  + '<th>Выход<br/>(произв.)</th>\n'
                  + ('<th>Требуется<br/>(недостаточно)</th>\n' if with_current_industry_progress else '')
                  + '<th>План<br/>(произв.)</th>\n'
                  '<th>Остаток<br/>(произв.)</th>\n'
                  '<th>Соотношение<br/>(как часть целого)</th>\n'
                  '<th>Итог<br/>(закуп.)</th>\n'
                  '<th>Итог<br/>(рентаб.)</th>\n'
                  '</tr>\n')

    def get_pseudographics_prefix(levels, is_first, is_last):
        prfx: str = ''
        for lv in enumerate(levels):
            if lv[1]:
                prfx += '&nbsp; '
            else:
                prfx += '&#x2502; '          # |
        if is_first:
            if not prfx:
                prfx += '&#x2514;'           # └
            else:
                prfx += '&#x2502; &#x2514;'  # | └
        elif is_last:
            prfx += '&#x2514;&#x2500;'       # └─
        else:
            prfx += '&#x251C;&#x2500;'       # ├─
        return prfx

    def generate_industry_plan_item(
            row0_prefix: str,
            row1_num: int,
            row0_levels,
            __it338: profit.QIndustryTree,
            planned_blueprints: int,
            planned_runs: int):
        bp_tid = __it338.blueprint_type_id
        bp_nm = __it338.blueprint_name
        bp_action = __it338.action
        job_cost: typing.Optional[profit.QIndustryJobCost] = __it338.industry_job_cost
        assert job_cost is not None

        fmt: str = \
            '<tr{tr_class}>\n' \
            + '<th scope="row"><span class="text-muted">{num_prfx}</span>{num}</th>\n' \
            + '<td><img class="icn24" src="{src}"> {prfx} {nm}{pstfx}</td>\n' \
            + '<td></td>' \
            + '<td></td>' \
            + '<td></td>' \
            + '<td>{qp}</td>' \
            + '<td></td>' \
            + '<td></td>' \
            + '<td></td>' \
            + '<td></td>' \
            '</tr>'
        glf.write(
            fmt.format(
                tr_class=' class="active"' if not row0_prefix else '',
                num_prfx=row0_prefix, num=row1_num,
                prfx='<tt><span class="text-muted">{}</span></tt>'.format(
                    get_pseudographics_prefix(row0_levels, True, False)),
                nm=bp_nm,
                pstfx="<sup> <strong style='color:maroon;'>{bp}&#215;{run}</strong> "
                      "<span class='text-muted'>{act}</span></sup>".format(
                    bp=planned_blueprints,
                    run=planned_runs,
                    act=str(bp_action).split('.')[-1],
                ),
                src=render_html.__get_img_src(bp_tid, 32),
                qp='<small>'
                   '{}<sup>EIV</sup>*{}<sup>runs</sup>*{:.2f}%<sup>{}</sup>*{}%<sup>rig</sup>'
                   '*{}%<sup>tax</sup> => {}<sup>job</sup>'
                   '</small>'.format(
                        job_cost.estimated_items_value,  # 1.EIV
                        planned_blueprints * planned_runs,  # 1.runs
                        job_cost.industry_cost_index * 100.0,  # 1.const_index
                        job_cost.system_indices.solar_system,  # 1.solar_system
                        job_cost.structure_bonus_rigs * 100.0,  # 1.rig
                        job_cost.scc_surcharge * 100.0,  # 1.tax
                        int(math.ceil(planned_blueprints * planned_runs * job_cost.total_job_cost))  # 2.out
                   )
            )
        )

    def generate_components_list(
            with_current_industry_progress: bool,
            row0_prefix: str,
            row0_levels,
            __ap344: profit.QPlannedActivity):
        # вывод информации о материалах
        for m1 in enumerate(__ap344.planned_materials, start=1):
            row1_num: int = int(m1[0])
            m1_planned_material: profit.QPlannedMaterial = m1[1]
            m1_obtaining_plan: profit.QIndustryObtainingPlan = m1_planned_material.obtaining_plan
            m1_obtaining_activity: profit.QPlannedActivity = m1_obtaining_plan.activity_plan
            m1_material: profit.QMaterial = m1[1].material
            m1_industry: profit.QIndustryTree = m1_material.industry
            m1_tid: int = m1_material.type_id
            m1_tnm: str = m1_material.name
            m1_quantity: int = m1_material.quantity

            m1_copying: bool = m1_industry and m1_industry.action == profit.QIndustryAction.copying
            m1_invention: bool = m1_industry and m1_industry.action == profit.QIndustryAction.invent
            if m1_copying or m1_invention:
                m1_planned_blueprints: int = 1
                m1_planned_runs: int = 1
            else:
                m1_planned_blueprints: int = __ap344.planned_blueprints
                m1_planned_runs: int = __ap344.planned_runs

            def generate_grayed_reused_duplicate(before: bool):
                if not m1_obtaining_plan.reused_duplicate:
                    return ''
                return '<span style="color:lightgray;">' if before else '</span>'

            fmt: str = \
                '<tr{tr_class}>\n' \
                + '<th scope="row"><span class="text-muted">{num_prfx}</span>{num}</th>\n' \
                + '<td><img class="icn24" src="{src}"> {prfx} {nm}{pstfx}</td>\n' \
                + ('<td>{qa:,d}{qip}</td>\n' if with_current_industry_progress else '') \
                + '<td>{qwome:,d}</td>\n' \
                + '<td>{qe}</td>\n' \
                + ('<td>{qne}</td>\n' if with_current_industry_progress else '') \
                + '<td>{qo}</td>\n' \
                + '<td>{qp}</td>\n' \
                + '<td>{qr}</td>\n' \
                + '<td>{qu}</td>\n' \
                + '<td>{qsq}</td>\n' \
                + '<td>{qsr}</td>\n' \
                '</tr>'
            glf.write(
                fmt.format(
                    tr_class=' class="active"' if not row0_prefix else '',
                    num_prfx=row0_prefix, num=row1_num,
                    prfx='<tt><span class="text-muted">{}</span></tt>'.format(
                        get_pseudographics_prefix(row0_levels, False, row1_num == len(__ap344.planned_materials))),
                    nm=m1_tnm,
                    pstfx='{qm}{bpq}'.format(
                        qm="<sup> <strong style='color:darkblue;'>x{}</strong></sup>".format(m1_quantity),
                        bpq='' if m1_industry is None or m1_industry.products_per_single_run == 1 else
                            ' <strong>x{}</strong>'.format(m1_industry.products_per_single_run),
                    ),
                    src=render_html.__get_img_src(m1_tid, 32),
                    qa=-1,
                    qip='',
                    qwome=m1_material.quantity * m1_planned_blueprints * m1_planned_runs,
                    qe='{:,d}'.format(m1_planned_material.quantity_with_efficiency) if m1_industry is not None else
                       '{}{:,d}{}'.format(
                           generate_grayed_reused_duplicate(True),
                           m1_planned_material.quantity_with_efficiency,
                           generate_grayed_reused_duplicate(False)
                       ),
                    qo='' if not m1_material.industry else
                       '{}{}{}'.format(
                           generate_grayed_reused_duplicate(True),
                           m1_obtaining_plan.industry_output,
                           generate_grayed_reused_duplicate(False)
                       ),
                    qp='' if not m1_material.industry else
                       '<small>'
                       '{}<sup>bp</sup>*{}<sup>run</sup>*{}<sup>qty</sup>*{}<sup>%</sup> => '
                       '{:.1f}<sup>%</sup>'
                       '</small>'.format(
                           m1_planned_blueprints,  # 1.bp
                           m1_planned_runs,  # 1.run
                           m1_material.quantity,  # 1.qty
                           '{:.1f}{}'.format(  # 1.prob
                               100.0*m1_industry.invent_probability,
                               '' if m1_industry.decryptor_probability is None else
                               '×{:.1f}'.format(100.0*m1_industry.decryptor_probability)
                           ) if not industry_plan.customization or not industry_plan.customization.min_probability else
                           '({:.1f}{}×{:.1f})'.format(
                               100.0*m1_industry.invent_probability,
                               '' if m1_industry.decryptor_probability is None else
                               '×{:.1f}'.format(100.0*m1_industry.decryptor_probability),
                               industry_plan.customization.min_probability
                           ),
                           m1_planned_blueprints * \
                           m1_planned_runs * \
                           m1_material.quantity * \
                           m1_industry.invent_probability * (  # Purifier : 30x20x27.5 => 0.3*1.2*1.275 => 45.9%
                               1.0 if m1_industry.decryptor_probability is None else
                               (1.0+m1_industry.decryptor_probability)
                           ) * (
                               1.0 if not industry_plan.customization or
                                      not industry_plan.customization.min_probability else
                               (100.0+industry_plan.customization.min_probability)/100.0
                           ) * 100.0  # 2.out
                       ) if m1_invention else
                       '<small>'
                       '{}<sup>bp</sup>*{}<sup>run</sup>*{}<sup>qty</sup> => '
                       '{:.1f}<sup>out</sup>'
                       '</small>'.format(
                           m1_planned_blueprints,  # 1.bp
                           m1_planned_runs,  # 1.run
                           m1_material.quantity,  # 1.qty
                           m1_planned_blueprints * \
                           m1_planned_runs * \
                           m1_material.quantity  # 2.out
                       ) if m1_copying else
                       '<small>'
                       '{}<sup>bp</sup>*{}<sup>run</sup>*{}<sup>qty</sup> => '
                       '{}<sup>me</sup> '
                       '{}=> '
                       '{}<sup>bp</sup>*{}<sup>run</sup>*{}<sup>dose</sup> => '
                       '{}<sup>out</sup>'
                       '{}'
                       '</small>'.format(
                           m1_planned_blueprints,  # 1.bp
                           m1_planned_runs,  # 1.run
                           m1_material.quantity,  # 1.qty
                           m1_planned_material.quantity_with_efficiency,  # 2.me
                           generate_grayed_reused_duplicate(True),  # before 3
                           'TODO' if not m1_obtaining_activity else m1_obtaining_activity.planned_blueprints,  # 3.bp
                           'TODO' if not m1_obtaining_activity else m1_obtaining_activity.planned_runs,  # 3.run
                           m1_industry.products_per_single_run,  # 3.dose
                           m1_obtaining_plan.industry_output,  # 4.out
                           generate_grayed_reused_duplicate(False)  # after 4
                       ),
                    qr='' if not m1_material.industry else
                       '{:,d}{}'.format(
                           m1_obtaining_plan.rest_quantity,
                           '' if not m1_obtaining_plan.reused_duplicate else
                           '<small>=<sup>{}-{}</sup></small>'.format(
                               m1_obtaining_plan.rest_quantity + m1_planned_material.quantity_with_efficiency,
                               m1_planned_material.quantity_with_efficiency
                           )
                       ),
                    qu='<small>'
                       '{:.8f}<sup>chain</sup>*{}<sup>pcs</sup> => '
                       '{:.8f}<sup>ratio</sup>'
                       '</small>'.format(
                            m1_planned_material.usage_chain,
                            m1_planned_material.quantity_with_efficiency,
                            m1_planned_material.usage_chain * m1_planned_material.usage_ratio
                       ) if not m1_material.industry else
                       '<small>'
                       '{:.8f}<sup>chain</sup> * '
                       '({}<sup>me</sup>/{}{}<sup>out</sup>{} => {:.4f}) => '
                       '{:.8f}<sup>ratio</sup>'
                       '</small>'.format(
                           m1_planned_material.usage_chain,  # chain
                           m1_planned_material.quantity_with_efficiency,  # me
                           generate_grayed_reused_duplicate(True),  # before out
                           m1_obtaining_plan.industry_output,  # out
                           generate_grayed_reused_duplicate(False),  # after out
                           m1_planned_material.usage_ratio,  # me/out
                           m1_planned_material.usage_chain * m1_planned_material.usage_ratio  # ratio
                       ),
                    qne='' if not m1_obtaining_plan.not_enough_quantity else
                        '{:,d}'.format(m1_obtaining_plan.not_enough_quantity),
                    qsq='<small>'
                        '{:,d}{}=<sup>{}+{}</sup>{}'
                        '</small>'.format(
                            m1_planned_material.summary_quantity_after,  # sum
                            generate_grayed_reused_duplicate(True),  # before =
                            m1_planned_material.summary_quantity_before,  # 1
                            m1_planned_material.summary_quantity_after-m1_planned_material.summary_quantity_before,  # 2
                            generate_grayed_reused_duplicate(False)  # after =
                        ),
                    qsr='' if m1_material.industry else
                        '<small>'
                        '{:.8f}=<sup>{:.4f}+{:.4f}</sup>'
                        '</small>'.format(
                            m1_planned_material.summary_ratio_after,
                            m1_planned_material.summary_ratio_before,
                            m1_planned_material.summary_ratio_after-m1_planned_material.summary_ratio_before
                        )
                ))
            if m1_obtaining_activity:
                row2_levels = row0_levels[:]
                row2_levels.append(row1_num == len(__ap344.planned_materials))
                row2_prefix: str = "{prfx}{num1}.".format(prfx=row0_prefix, num1=row1_num)
                generate_industry_plan_item(
                    row2_prefix, 0, row2_levels,
                    m1_industry,
                    m1_planned_blueprints, m1_planned_runs)
                generate_components_list(
                    with_current_industry_progress,
                    row2_prefix,
                    row2_levels,
                    m1_obtaining_activity)

    glf.write("""
<style>
.table-borderless > tbody > tr > td,
.table-borderless > tbody > tr > th,
.table-borderless > tfoot > tr > td,
.table-borderless > tfoot > tr > th,
.table-borderless > thead > tr > td,
.table-borderless > thead > tr > th {
    border: none;
    padding: 0px;
}
</style>
 <table class="table table-borderless table-condensed" style="font-size:small">
<thead>""")

    generate_components_header(False)

    glf.write("""
</thead>
<tbody>""")

    # вывод информации о работе и чертеже
    generate_industry_plan_item(
        '', 0, [],
        industry_plan.base_industry,
        1, industry_plan.customized_runs)
    # вывод информации о чертежах
    generate_components_list(False, '', [], industry_plan.base_planned_activity)

    glf.write("""
</tbody>
</table>
  </div> <!--media-body-->
 </div> <!--media-->
<hr>
 <div class="media">
  <div class="media-left">""")

    glf.write('<img class="media-object icn64" src="{src}" alt="Сводная таблица производства">\n'.
              format(src=render_html.__get_icon_src(1201, sde_icon_ids)))  # Materials

    def generate_summary_raw_header(with_current_industry_progress: bool):
        glf.write('<tr>\n'
                  '<th style="width:40px;">#</th>'
                  '<th>Материалы</th>'
                  + ('<th>Имеется +<br/>Производится</th>\n' if with_current_industry_progress else '')
                  + '<th>Требуется</th>'
                  + ('<th>Прогресс, %</th>\n' if with_current_industry_progress else '')
                  + '<th style="text-align:right;">Цена,&nbsp;ISK/шт.</th>'
                  '<th style="text-align:right;">Цена,&nbsp;ISK</th>'
                  '<th style="text-align:right;">Пропорция,&nbsp;шт.</th>'
                  '<th style="text-align:right;">Пропорция,&nbsp;ISK</th>'
                  '<th style="text-align:right;"><strike>Объём,&nbsp;m&sup3;</strike></th>'
                  '</tr>\n')

    glf.write("""
  </div>
  <div class="media-body">
   <h4 class="media-heading">Сводная таблица производства</h4>""")

    glf.write("""
<div class="table-responsive">
 <table class="table table-condensed" style="font-size:small">
<thead>""")

    generate_summary_raw_header(True)

    glf.write("""
</thead>
<tbody>""")

    material_groups: typing.Dict[int, typing.List[profit.QIndustryMaterial]] = {}
    for type_id in industry_plan.materials_repository.materials.keys():
        m: profit.QIndustryMaterial = industry_plan.materials_repository.get_material(type_id)
        mg: typing.List[profit.QIndustryMaterial] = material_groups.get(m.base.group_id)
        if mg is None:
            mg = []
            material_groups[m.base.group_id] = mg
        mg.append(m)

    row3_num: int = 0
    for group_id in material_groups.keys():
        mg: typing.List[profit.QIndustryMaterial] = material_groups.get(group_id)
        is_blueprints_group: bool = group_id == 2
        if group_id == 1857:
            mg.sort(key=lambda __m685: __m685.purchased+__m685.manufactured, reverse=True)
        else:
            mg.sort(key=lambda __m685: __m685.purchased+__m685.manufactured)
        # рисуем заголовок группы
        glf.write('<tr><td class="active" colspan="10"><strong>{nm}</strong><!--{id}-->{clbrd}</td></tr>\n'.format(
            nm=mg[0].base.group_name,
            id=group_id,
            clbrd=''))
        # выводим товары группы
        for m in mg:
            row3_num += 1
            # получение данных по материалу
            m3_tid: int = m.base.type_id
            m3_tnm: str = m.base.name
            m3_q = m.purchased + m.manufactured  # quantity (required)
            m3_r = m.purchased_ratio  # ratio (пропорция от требуемого кол-ва с учётом вложенных уровней)
            m3_a = m.available_in_assets  # available in assets
            m3_j = m.in_progress  # in progress (runs of jobs)
            m3_v = m.base.volume  # volume
            m3_p = m.base.price   # price
            # расчёт прогресса выполнения (постройки, сбора) материалов (m1_j пропускаем, т.к. они не готовы ещё)
            if m.available_in_assets >= m3_q:
                m3_progress = 100.0
            elif m3_q == 0:
                m3_progress = 100.0
            else:
                m3_progress = float(100.0 * float(m3_a) / m3_q)
            # вывод наименования ресурса
            glf.write(
                '<tr>\n'
                ' <th scope="row">{num}</th>\n'
                ' <td data-copy="{nm}"><img class="icn24" src="{src}"> {nm}{me_te}</td>\n'
                ' <td>{qa}{qip}</td>\n'
                ' <td quantity="{qneed}">{qrn:,d}</td>\n'
                ' <td><div class="progress" style="margin-bottom:0px"><div class="progress-bar{prcnt100}"'
                ' role="progressbar" aria-valuenow="{prcnt}" aria-valuemin="0" aria-valuemax="100"'
                ' style="width: {prcnt}%;">{fprcnt:.1f}%</div></div></td>\n'
                ' <td align="right">{price}</td>'
                ' <td align="right">{costn}</td>'
                ' <td align="right">{qratio}</td>'
                ' <td align="right">{pratio}</td>'
                ' <td align="right"><strike>{volume}</strike></td>'
                '</tr>'.format(
                    num=row3_num,
                    nm=m3_tnm,
                    me_te='',
                    src=render_html.__get_img_src(m3_tid, 32),
                    qrn=m3_q,
                    qneed=m3_q-m3_a-m3_j if m3_q > (m3_a+m3_j) else 0,
                    qa='{:,d}'.format(m3_a) if m3_a >= 0 else
                       '&infin; <small>runs</small>',
                    qip='' if m3_j == 0 else
                        '<mark>+ {}</mark>'.format(m3_j),
                    prcnt=int(m3_progress),
                    fprcnt=m3_progress,
                    prcnt100=" progress-bar-success" if m3_progress == 100 else '',
                    price='{:,.1f}'.format(m3_p) if m3_p is not None else '',
                    costn='{:,.1f}'.format(m3_p * m3_q) if m3_p is not None else '',
                    qratio='' if not m.purchased else
                           '{:,.8f}'.format(m3_r),
                    pratio='' if not m.purchased or m3_p is None else
                           '{:,.1f}'.format(m3_p*m3_r+0.004999),
                    volume='{:,.1f}'.format(m3_v * m3_q) if not is_blueprints_group else ''
                ))

    glf.write("""
</tbody>
</table>
</div> <!--table-responsive-->
  </div> <!--media-body-->
 </div> <!--media-->
</div> <!--container-fluid-->""")


def dump_industry_plan(
        # данные о продуктах, которые надо отобразить в отчёте
        industry_plan: profit.QIndustryPlan,
        # путь, где будет сохранён отчёт
        ws_dir,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_bp_materials,
        sde_market_groups,
        sde_icon_ids):
    assert industry_plan.base_industry

    product_name: str = industry_plan.base_industry.product_name
    file_name_c2s: str = render_html.__camel_to_snake(product_name, True)
    ghf = open('{dir}/{fnm}.html'.format(dir=ws_dir, fnm=file_name_c2s), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(ghf, product_name)
        render_report(
            ghf,
            industry_plan,
            sde_bp_materials,
            sde_market_groups,
            sde_icon_ids)
        render_html.__dump_footer(ghf)
    finally:
        ghf.close()


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
        {'bptid': 1072, 'qr': 1, 'me': 10, 'te': 20},  # 1MN Afterburner I Blueprint
    ]

    # with open('{}/industry_cost/dataset.json'.format(argv_prms["workspace_cache_files_dir"]), 'r', encoding='utf8') as f:
    #    s = f.read()
    #    calc_inputs = (json.loads(s))

    # индексы стоимости производства для различных систем (системы и продукция заданы в настройках роутинга)
    industry_cost_indices: typing.List[profit.QIndustryCostIndices] = []
    for r in q_router_settings.g_routes:
        solar_system: str = r['solar_system']
        solar_system_id: typing.Optional[int] = next((int(_[0]) for _ in sde_inv_names.items()
                                                      if _[1] == solar_system), None)
        assert solar_system_id is not None
        cost_indices = next((_['cost_indices'] for _ in eve_industry_systems_data
                             if _['solar_system_id'] == solar_system_id), None)
        assert cost_indices is not None
        iic: profit.QIndustryCostIndices = profit.QIndustryCostIndices(
            solar_system_id,
            solar_system,
            cost_indices,
            set(r['output']))
        industry_cost_indices.append(iic)
    del eve_industry_systems_data

    # настройки оптимизации производства: реакции на 15 ран (сутки) и производство в зависимости от времени (сутки)
    # см. также eve_conveyor_tools.py : setup_blueprint_details
    calc_customization = {
        'reaction_runs': 15,
        # 'industry_time': 5 * 60 * 60 * 24,
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
    }

    for calc_input in calc_inputs:
        # выходные данные после расчёта: дерево материалов и работ, которые надо выполнить
        industry_tree: profit.QIndustryTree = generate_industry_tree(
            # вход и выход для расчёта
            calc_input,
            # sde данные, загруженные из .converted_xxx.json файлов
            sde_type_ids,
            sde_bp_materials,
            sde_market_groups,
            eve_market_prices_data,
            industry_cost_indices)

        # выходные данные после расчёта: список материалов и ratio-показатели их расхода для производства qr-ранов
        industry_plan: profit.QIndustryPlan = generate_industry_plan(
            calc_input.get('qr', 1),
            industry_tree,
            calc_customization)

        dump_industry_plan(
            industry_plan,
            '{}/industry_cost'.format(argv_prms["workspace_cache_files_dir"]),
            sde_bp_materials,
            sde_market_groups,
            sde_icon_ids)


if __name__ == "__main__":
    main()
