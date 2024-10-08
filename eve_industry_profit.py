﻿import typing
import math
# import json

import eve_sde_tools
import eve_esi_tools
import eve_efficiency
import profit


# получение цены материала
# составляем дерево материалов, которые будут использоваться в производстве
def generate_materials_tree(
        # входной список материалов, используемых в производстве
        curr_materials: typing.List[typing.Dict[str, int]],
        # выходной список со всеми возможными материалами, задействованными в производстве
        curr_industry: profit.QIndustryTree,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_products: typing.Dict[str, typing.Dict[int, eve_sde_tools.EveSDEProduct]],
        sde_market_groups,
        # esi данные, загруженные с серверов CCP
        eve_market_prices_data,
        # индексы стоимости производства для различных систем (системы и продукция заданы в настройках роутинга)
        industry_cost_indices:  typing.List[profit.QIndustryCostIndices],
        # настройки оптимизации производства
        industry_plan_customization: typing.Optional[profit.QIndustryPlanCustomization]):
    for m1 in curr_materials:
        material_tid: int = int(m1['typeID'])
        material_qty: int = int(m1['quantity'])
        material_name: str = eve_sde_tools.get_item_name_by_type_id(sde_type_ids, material_tid)
        material_market_group_id: typing.Optional[int] = eve_sde_tools.get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, material_tid)
        material_market_group_name: typing.Optional[str] = sde_market_groups[str(material_market_group_id)]['nameID']['en'] if material_market_group_id else None
        material_meta_group_id: typing.Optional[int] = sde_type_ids[str(material_tid)].get('metaGroupID', None)
        material_volume: float = sde_type_ids[str(material_tid)].get('volume', 0.0)
        material_adjusted_price: float = eve_esi_tools.get_material_adjusted_price(material_tid, eve_market_prices_data)
        material_is_commonly_used: bool = eve_sde_tools.is_type_id_nested_into_market_group(
                material_tid,
                industry_plan_customization.common_components,
                sde_type_ids,
                sde_market_groups
        ) if industry_plan_customization and industry_plan_customization.common_components else False
        # пополняем список материалов
        q_material: profit.QMaterial = profit.QMaterial(
            material_tid,
            material_qty,
            material_name,
            material_market_group_id,
            material_market_group_name,
            material_is_commonly_used,
            material_volume,
            material_adjusted_price,
            material_meta_group_id)
        curr_industry.append_material(q_material)
        # или: проверяем, возможно ли получить данный материал с помощью его manufacturing-производства?
        # или: проверяем, возможно ли получить данный материал с помощью его reaction-производства?
        # или: если способов производства данного вида материалов так и не найдено, то данный материал закупается,
        #      переходим к следующему
        cached_product: typing.Optional[eve_sde_tools.EveSDEProduct] = sde_products['manufacturing'].get(material_tid)
        if cached_product:
            material_produce_action: profit.QIndustryAction = profit.QIndustryAction.manufacturing
        else:
            # пытаемся получить чертёж/формулу и параметры производства/реакции
            cached_product: typing.Optional[eve_sde_tools.EveSDEProduct] = sde_products['reaction'].get(material_tid)
            if cached_product:
                material_produce_action: profit.QIndustryAction = profit.QIndustryAction.reaction
            else:
                # пытаемся получить чертёж и параметры копирки (если она предполагается для этого чертежа)
                cached_product: typing.Optional[eve_sde_tools.EveSDEProduct] = sde_products['copying'].get(material_tid)
                if cached_product:
                    material_produce_action = profit.QIndustryAction.copying
                else:
                    continue
        # теперь рассчитываем потребности для этой activity
        activity: str = str(material_produce_action)
        material_bp_tid = cached_product.blueprint_type_id
        max_production_limit: int = cached_product.max_production_limit
        # assert len(cached_product.activity_data.get('products', [])) == 1
        # assert cached_product.activity_data['products'][0]['typeID'] == material_tid
        # готовим данные для следующего уровня вложенности
        products_per_single_run: int = cached_product.products_per_single_run
        single_run_time: int = cached_product.activity_data['time']
        next_materials: typing.Optional[typing.List[typing.Dict[str, int]]] = \
            cached_product.activity_data.get('materials')
        # считаем EIV, который потребуется для вычисления стоимости job cost
        estimated_items_value: float = profit.calc_estimated_items_value(
            material_bp_tid,
            activity,
            sde_bp_materials,
            eve_market_prices_data)
        # получаем информацию о производственных индексах в системе, где крафтится этот продукт
        system_indices, cost_index = profit.get_industry_cost_index(
            material_tid,
            activity,
            industry_cost_indices)
        # в этой точке понятно, что данный материал можно произвести, поэтому список материалов для него будет
        # пополнен более сложным способом
        next_industry: profit.QIndustryTree = profit.QIndustryTree(
            material_bp_tid,
            eve_sde_tools.get_item_name_by_type_id(sde_type_ids, material_bp_tid),
            q_material,
            material_produce_action,
            products_per_single_run,
            max_production_limit,
            single_run_time,
            estimated_items_value,
            system_indices,
            cost_index)
        # настраиваем ME чертежа (нам его знать неоткуда, поэтому ставим максимальное ME)
        if industry_plan_customization and (material_produce_action == profit.QIndustryAction.manufacturing):
            # TODO: не Tech II (2) и не Structure Tech II (53), и не Tech III (14)
            if q_material.meta_group_id is None or q_material.meta_group_id in {2, 53, 14}:
                if industry_plan_customization.unknown_blueprints_me is not None:
                    next_industry.set_me(industry_plan_customization.unknown_blueprints_me)
                if industry_plan_customization.unknown_blueprints_te is not None:
                    next_industry.set_te(industry_plan_customization.unknown_blueprints_te)
        # подключаем к метариалу следующий уровень производства
        q_material.set_industry(next_industry)
        # повторяем те же самые действия по формированию списка задействованных материалов, но теперь уже
        # для нового уровня вложенности
        if next_materials:
            generate_materials_tree(
                next_materials,
                next_industry,
                sde_type_ids,
                sde_bp_materials,
                sde_products,
                sde_market_groups,
                eve_market_prices_data,
                industry_cost_indices,
                industry_plan_customization)


# генерация чертежа/чертежей (в результате запуска научки) для точного расчёта научки с учётом datacores и decryptors
def schedule_industry_job__invent(
        # идентификатор "предыдущего" чертежа, из которого делается blueprint_type_id (могут быть варианты)
        prior_blueprint_type_id: typing.Optional[int],
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
        sde_products: typing.Dict[str, typing.Dict[int, eve_sde_tools.EveSDEProduct]],
        sde_market_groups,
        # esi данные, загруженные с серверов CCP
        eve_market_prices_data,
        # индексы стоимости производства для различных систем (системы и продукция заданы в настройках роутинга)
        industry_cost_indices:  typing.List[profit.QIndustryCostIndices],
        # настройки оптимизации производства
        industry_plan_customization: typing.Optional[profit.QIndustryPlanCustomization]):
    # пытаемся получить чертёж и параметры инвента (если он предполагается для этого чертежа)
    cached_product: typing.Optional[eve_sde_tools.EveSDEProduct] = sde_products['invention'].get(blueprint_type_id)
    # если инвент данного чертежа возможен, то добавляем в дерево работ декрипторы и датакоры
    if not cached_product:
        return
    # если возможны варианты инвента данного чертежа, как например для Capital Hull Repairer II Blueprint, то выполняем
    # поиск исходного чертежа по заданному входному параметру (номер должен быть задан корректно, а не огульно)
    if isinstance(cached_product, list):
        assert prior_blueprint_type_id is not None
        cached_product = next((_ for _ in cached_product if _.blueprint_type_id == prior_blueprint_type_id), None)
        assert cached_product is not None
    source_blueprint_type_id: int = cached_product.blueprint_type_id
    # TODO: принимаем за точку отсчёта один чертёж
    blueprint_quantity: int = 1

    # в этой точке понятно, что чертёж можно (и нужно) инвентить, поэтому получаем список материалов для инвента
    # (и предварительной копирки)
    copied_blueprint_name: str = eve_sde_tools.get_item_name_by_type_id(sde_type_ids, source_blueprint_type_id)
    invented_blueprint_name: str = eve_sde_tools.get_item_name_by_type_id(sde_type_ids, blueprint_type_id)
    blueprints_market_group_id: int = 2
    blueprints_market_group_name: str = sde_market_groups[str(blueprints_market_group_id)]['nameID']['en']
    blueprint_meta_group_id: typing.Optional[int] = sde_type_ids[str(blueprint_type_id)].get('metaGroupID', None)

    # коррекция meta группы 1 => 2 для, например, Small Vorton Projector II (который является продукцией Tech II),
    # но чертёж Small Vorton Projector II Blueprint у него (к сожалению) относится к Tech I - это ошибка в sde
    if blueprint_meta_group_id == 1:
        if curr_industry.product.meta_group_id == 2:
            blueprint_meta_group_id = 2

    # пополняем список материалов T2 чертежом
    invented_material: profit.QMaterial = profit.QMaterial(
        blueprint_type_id,
        blueprint_quantity,
        invented_blueprint_name,
        blueprints_market_group_id,
        blueprints_market_group_name,
        False,
        0.0,  # чертёж не перевозится, он копируется и инвентится "на месте"
        0.0,
        blueprint_meta_group_id)
    curr_industry.append_material(invented_material)

    # теперь к T2-чертежу подключаем инвент-работу
    max_production_limit: int = cached_product.max_production_limit
    invent_dict = cached_product.activity_data
    assert len(invent_dict.get('products', [])) >= 1
    invent_product_dict = next((p for p in invent_dict['products'] if p['typeID'] == blueprint_type_id), None)
    assert invent_product_dict is not None
    # получаем параметры инвента: (1) кол-во прогонов Т2 чертежа?
    blueprint_runs_per_single_copy: int = invent_product_dict['quantity']
    invent_run_time: int = invent_dict['time']
    invent_materials__decryptors_only: typing.List[typing.Dict[str, int]] = invent_dict['materials']
    invent_probability: float = invent_product_dict['probability']

    # считаем EIV, который потребуется для вычисления стоимости job cost
    estimated_items_value: float = profit.calc_estimated_items_value(
        blueprint_type_id,
        'invention',
        sde_bp_materials,
        eve_market_prices_data)
    # получаем информацию о производственных индексах в системе, где крафтится этот продукт
    system_indices, cost_index = profit.get_industry_cost_index(
        blueprint_type_id,
        'invention',
        industry_cost_indices)
    # инициализируем базовый объект-справочник со сведениями о производстве
    invent_industry: profit.QIndustryTree = profit.QIndustryTree(
        source_blueprint_type_id,
        copied_blueprint_name,
        invented_material,
        profit.QIndustryAction.invention,
        1,
        max_production_limit,
        invent_run_time,
        estimated_items_value,
        system_indices,
        cost_index)
    invent_industry.set_blueprint_runs_per_single_copy(blueprint_runs_per_single_copy)
    invent_industry.set_probability(invent_probability)
    invented_material.set_industry(invent_industry)

    # в список материалов подкладываем чертёж, который должен скопироваться N раз
    invent_materials: typing.List[typing.Dict[str, int]] = [{'typeID': source_blueprint_type_id, 'quantity': 1}]
    invent_materials.extend(invent_materials__decryptors_only)

    # считаем параметры декриптора
    decryptor_params: typing.Optional[typing.Tuple[int, float]] = profit.get_decryptor_parameters(
        blueprint_me,
        blueprint_te,
        blueprint_runs,
        blueprint_runs_per_single_copy,
        blueprint_meta_group_id)

    if decryptor_params:
        decryptor_type_id: int = decryptor_params[0]
        decryptor_probability: float = decryptor_params[1]

        """
        # сохраняем пропорцию использования текущего материала для текущей работы
        job_probability: float = 1.0
        if job_probability:  # probability
            job_probability: float = 1.0 + decryptor_probability  # сумма м.б. меньше 1.0
        skill_probability: float = 1.0
        if industry_plan_customization and industry_plan_customization.min_probability:
            skill_probability = (100.0 + industry_plan_customization.min_probability) / 100.0
        probability: float = invent_probability * job_probability * skill_probability

        # пытаемся рассчитать сколько прогонов bpc необходимо получить и сколько раз запустить инвент?
        blueprint_copies_output: int = 1
        usage_ratio: float = float(blueprint_quantity) / blueprint_copies_output * (1 / probability)
        # сохраняем сведения о пропорциях использования материалов
        # produced_material.store_usage_ratio(usage_ratio)
        """

        # меняем количество копий
        # TODO: invent_materials[0]['quantity'] = math.ceil(usage_ratio)
        # сохраняем параметры декриптора
        invent_materials.append({'typeID': decryptor_type_id, 'quantity': 1})
        assert decryptor_probability is not None
        invent_industry.set_decryptor_probability(decryptor_probability)

    # составляем дерево материалов, которые будут использоваться для инвента
    generate_materials_tree(
        invent_materials,
        invent_industry,
        sde_type_ids,
        sde_bp_materials,
        sde_products,
        sde_market_groups,
        eve_market_prices_data,
        industry_cost_indices,
        industry_plan_customization)


def generate_industry_tree(
        # вход и выход для расчёта
        calc_input,
        industry_plan_customization: typing.Optional[profit.QIndustryPlanCustomization],
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_products: typing.Dict[str, typing.Dict[int, eve_sde_tools.EveSDEProduct]],
        sde_market_groups,
        # esi данные, загруженные с серверов CCP
        eve_market_prices_data,
        # индексы стоимости производства для различных систем (системы и продукция заданы в настройках роутинга)
        industry_cost_indices:  typing.List[profit.QIndustryCostIndices]) -> typing.Optional[profit.QIndustryTree]:
    assert 'bptid' in calc_input
    blueprint_type_id = calc_input.get('bptid')
    assert blueprint_type_id is not None

    # далее готовимся обсчитывать только рентабельность manufacturing-производства, для инвентов на входе надо менять
    # формат входных данных (чертёж м.б. один, а продукты у него разные)
    bp0_dict = eve_sde_tools.get_blueprint_any_activity(sde_bp_materials, 'manufacturing', blueprint_type_id)
    assert bp0_dict is not None
    assert len(bp0_dict.get('products', [])) == 1

    product_type_id: int = bp0_dict['products'][0]['typeID']
    single_run_quantity: int = bp0_dict['products'][0]['quantity']
    max_production_limit: int = bp0_dict.get('maxProductionLimit', 0)

    # из справочной информации о чертеже здесь интересны только материалы, которые будут использоваться в производстве
    base_materials: typing.Optional[typing.List[typing.Dict[str, int]]] = bp0_dict.get('materials')
    assert base_materials is not None

    # проверка на странные чертежи типа:
    # Thukker Component Assembly Array Blueprint (33868) - производится то, что требуется в материалах
    if next((1 for _ in base_materials if _['typeID'] == product_type_id), None):
        return None

    # генерируем дескриптор продукта, который будем крафтить
    product_type_name: str = eve_sde_tools.get_item_name_by_type_id(sde_type_ids, product_type_id)
    product_market_group_id: typing.Optional[int] = eve_sde_tools.get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, product_type_id)
    product_market_group_name: typing.Optional[str] = sde_market_groups[str(product_market_group_id)]['nameID']['en'] if product_market_group_id else None
    product_volume: float = sde_type_ids[str(product_type_id)].get('volume', 0.0)
    product_meta_group_id: typing.Optional[int] = sde_type_ids[str(product_type_id)].get('metaGroupID', None)
    product_adjusted_price: float = eve_esi_tools.get_material_adjusted_price(product_type_id, eve_market_prices_data)
    product_is_commonly_used: bool = eve_sde_tools.is_type_id_nested_into_market_group(
        product_type_id,
        industry_plan_customization.common_components,
        sde_type_ids,
        sde_market_groups
    ) if industry_plan_customization and industry_plan_customization.common_components else False

    # если me, te и qr не заданы, то пытаемся получить их автоматизированно
    if 'me' not in calc_input or 'te' not in calc_input or 'qr' not in calc_input:
        if product_meta_group_id in {2, 53}:  # Tech II (2), Structure Tech II (53)
            calc_input.update(eve_efficiency.get_t2_bpc_attributes(
                product_type_id,
                {},
                sde_type_ids,
                sde_market_groups))
        elif product_meta_group_id == 14:  # Tech III (14)
            calc_input.update(eve_efficiency.get_t3_bpc_attributes(
                product_type_id,
                {},
                sde_type_ids,
                sde_market_groups))
    assert 'me' in calc_input
    assert 'te' in calc_input
    assert 'qr' in calc_input
    customized_runs: int = calc_input['qr']

    # составляем продукт/материал, который будет подключен к дереву индустрии
    product: profit.QMaterial = profit.QMaterial(
        product_type_id,
        customized_runs * single_run_quantity,
        product_type_name,
        product_market_group_id,
        product_market_group_name,
        product_is_commonly_used,
        product_volume,
        product_adjusted_price,
        product_meta_group_id)
    # считаем EIV, который потребуется для вычисления стоимости job cost
    estimated_items_value: float = profit.calc_estimated_items_value(
        blueprint_type_id,
        'manufacturing',
        sde_bp_materials,
        eve_market_prices_data)
    # получаем информацию о производственных индексах в системе, где крафтится этот продукт
    system_indices, cost_index = profit.get_industry_cost_index(
        product_type_id,
        'manufacturing',
        industry_cost_indices)
    # инициализируем базовый объект-справочник со сведениями о производстве
    base_industry: profit.QIndustryTree = profit.QIndustryTree(
        blueprint_type_id,
        eve_sde_tools.get_item_name_by_type_id(sde_type_ids, blueprint_type_id),
        product,
        profit.QIndustryAction.manufacturing,
        single_run_quantity,
        max_production_limit,
        bp0_dict['time'],
        estimated_items_value,
        system_indices,
        cost_index)
    base_industry.set_me(calc_input['me'])
    base_industry.set_te(calc_input['te'])
    base_industry.set_blueprint_runs_per_single_copy(customized_runs)
    # TODO: base_industry.set_te(calc_input['te'])

    # планируем работу (инвент если потребуется)
    schedule_industry_job__invent(
        calc_input.get('bpc'),
        blueprint_type_id,
        customized_runs,
        calc_input['me'],
        calc_input['te'],
        base_industry,
        sde_type_ids,
        sde_bp_materials,
        sde_products,
        sde_market_groups,
        eve_market_prices_data,
        industry_cost_indices,
        industry_plan_customization)

    # составляем дерево материалов, которые будут использоваться в производстве
    generate_materials_tree(
        base_materials,
        base_industry,
        sde_type_ids,
        sde_bp_materials,
        sde_products,
        sde_market_groups,
        eve_market_prices_data,
        industry_cost_indices,
        industry_plan_customization)

    return base_industry


def get_optimized_runs_quantity__unoptimized(
        # кол-во продуктов, требуемых (с учётом предыдущей эффективности)
        need_quantity: int,
        # сведения о типе производства: кол-во продуктов, которые будут получены за один раз чертежа, признак - формула
        # ли, или реакция продукта? параметры чертежа? и т.п.
        products_per_single_run: int) -> typing.Tuple[int, int]:
    blueprints_or_runs: int = math.ceil(need_quantity / products_per_single_run)
    runs_quantity: int = blueprints_or_runs
    return 1, runs_quantity


def get_optimized_runs_quantity__reaction(
        # кол-во продуктов, требуемых (с учётом предыдущей эффективности)
        need_quantity: int,
        # сведения о типе производства: кол-во продуктов, которые будут получены за один раз чертежа, признак - формула
        # ли, или реакция продукта? параметры чертежа? и т.п.
        products_per_single_run: int,
        # настройки генерации отчёта, см. также eve_conveyor_tools.py : setup_blueprint_details
        reaction_runs: typing.Optional[int]) -> typing.Tuple[int, int]:
    # если не None, то настроенное кол-во ранов для реакций
    # если заданы настройки оптимизации, то считаем кол-во чертежей/ранов с учётом настроек
    if reaction_runs:
        runs_number_per_day: int = reaction_runs
        # реакции: планируется к запуску N чертежей по, как правило, 15 ранов (сутки)
        # производство: планируется к запуску N ранов для, как правило, оригиналов (длительностью в сутки)
        optimized_blueprints_quantity: int = \
            math.ceil(need_quantity / (products_per_single_run * runs_number_per_day))
        optimized_runs_quantity: int = runs_number_per_day
        return optimized_blueprints_quantity, optimized_runs_quantity
    else:
        return get_optimized_runs_quantity__unoptimized(
            need_quantity,
            products_per_single_run)


def get_optimized_runs_quantity__manufacturing(
        # кол-во продуктов, требуемых (с учётом предыдущей эффективности)
        need_quantity: int,
        # сведения о типе производства: кол-во продуктов, которые будут получены за один раз чертежа, признак - формула
        # ли, или реакция продукта? параметры чертежа? и т.п.
        single_run_time: int,
        products_per_single_run: int,
        is_commonly_used: bool,
        # настройки генерации отчёта, см. также eve_conveyor_tools.py : setup_blueprint_details
        industry_time: typing.Optional[int]) -> typing.Tuple[int, int]:
    # расчёт кол-ва ранов для данного чертежа (учёт настроек оптимизации производства)
    runs_number_per_day: typing.Optional[int] = None
    if is_commonly_used:
        # если не None, то длительность запуска производственных работ
        if industry_time:
            if single_run_time >= industry_time:
                runs_number_per_day = 1
            elif single_run_time > 0:
                runs_number_per_day = math.ceil(industry_time / single_run_time)
    # если заданы настройки оптимизации, то считаем кол-во чертежей/ранов с учётом настроек
    if runs_number_per_day:
        # реакции: планируется к запуску N чертежей по, как правило, 15 ранов (сутки)
        # производство: планируется к запуску N ранов для, как правило, оригиналов (длительностью в сутки)
        optimized_blueprints_quantity: int = \
            math.ceil(need_quantity / (products_per_single_run * runs_number_per_day))
        optimized_runs_quantity: int = runs_number_per_day
        return optimized_blueprints_quantity, optimized_runs_quantity
    # если настройки оптимизации не заданы, то считаем кол-во чертежей/ранов с учётом лишь только потребностей
    else:
        return get_optimized_runs_quantity__unoptimized(
            need_quantity,
            products_per_single_run)


def get_optimized_runs_quantity(
        # кол-во продуктов, требуемых (с учётом предыдущей эффективности)
        need_quantity: int,
        # сведения о типе производства: кол-во продуктов, которые будут получены за один раз чертежа, признак - формула
        # ли, или реакция продукта? параметры чертежа? и т.п.
        industry: profit.QIndustryTree,
        # настройки генерации отчёта, см. также eve_conveyor_tools.py : setup_blueprint_details
        industry_plan_customization: typing.Optional[profit.QIndustryPlanCustomization] = None) -> typing.Tuple[int, int]:
    # расчёт кол-ва ранов для данного чертежа (учёт настроек оптимизации производства)
    if industry.action == profit.QIndustryAction.reaction:
        return get_optimized_runs_quantity__reaction(
            need_quantity,
            industry.products_per_single_run,
            industry_plan_customization.reaction_runs if industry_plan_customization else None)
    elif industry.action == profit.QIndustryAction.manufacturing:
        return get_optimized_runs_quantity__manufacturing(
            need_quantity,
            industry.single_run_time,
            industry.products_per_single_run,
            industry.product.is_commonly_used,
            industry_plan_customization.industry_time if industry_plan_customization else None)
    # если настройки оптимизации не заданы, то считаем кол-во чертежей/ранов с учётом лишь только потребностей
    else:
        return get_optimized_runs_quantity__unoptimized(
            need_quantity,
            industry.products_per_single_run)


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
    if industry.action and industry.action in [profit.QIndustryAction.invention]:
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
        reused_activity.planned_blueprints,
        reused_activity.industry_job_cost)

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
        prior_planned_material: typing.Optional[profit.QPlannedMaterial],
        current_material: profit.QMaterial,
        cached_material: profit.QIndustryMaterial,
        # соотношение использования материалов в данном текущем цикле производственной активности
        usage_chain: float,
        # справочник текущего производства с настройками оптимизации процесса
        industry_plan: profit.QIndustryPlan) -> profit.QPlannedMaterial:
    assert reused_materials_quantity > 0
    assert current_material is not None
    assert current_material.industry is not None
    assert cached_material is not None

    # составляем план использования материала в рамках текущего плана производства
    # Внимание! это нормально, что prior_planned_material м.б. None, т.к. например в производстве Scourge Rage Rocket
    # требуется 45 Titanium Carbide, излишки которого остаются при получении 1 шт Graviton Pulse Generator, в таком
    # случае prior_planned_material==None
    reused_material: profit.QPlannedMaterial = profit.QPlannedMaterial(
        current_material,
        prior_planned_material,
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

    # считаем стоимость работы с учётом кол-ва запусков предыдущего расчёта (берём свою долю)
    next_level_job_cost: int = math.ceil(
        reused_material.obtaining_plan.activity_plan.planned_blueprints *
        reused_material.obtaining_plan.activity_plan.planned_runs *
        reused_material.obtaining_plan.activity_plan.industry_job_cost.total_job_cost *
        usage_chain * usage_ratio)
    cached_material.increase_job_cost(next_level_job_cost)
    # сохраняем сведения о потраченных исоньках на запуск работок
    industry_plan.job_cost_accumulator.increment_total_paid(next_level_job_cost)

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
                         False,
                         0.0,  # чертёж не перевозится, он копируется и инвентится "на месте"
                         0,
                         industry.product.meta_group_id),  # TODO: технологический уровень продукта, а не от чертежа :(
        1.0,  # usage_chain,
        planned_quantity,
        planned_runs,
        industry.me,
        0)
    # current_level_blueprint.store_usage_ratio(usage_chain)

    current_level_activity: profit.QPlannedActivity = profit.QPlannedActivity(
        industry,
        current_level_blueprint,
        planned_blueprints,
        None)

    # используем EIV, считаем стоимость работы
    current_level_activity.calc_industry_job_cost()

    # кешируем указатель на репозиторий материалов
    materials_repository: profit.QIndustryMaterialsRepository = industry_plan.materials_repository
    # кешируем указатель н репозиторий исонек (job_cost)
    job_cost_accumulator: profit.QIndustryJobCostAccumulator = industry_plan.job_cost_accumulator
    # рекурсивно обходим все материалы, применяем настройки оптимизации производства и применяем сведения об ME
    for m in industry.materials:
        cached_material: typing.Optional[profit.QIndustryMaterial] = materials_repository.get_material(m.type_id)
        if cached_material is None:
            cached_material = materials_repository.register_material(m.type_id, m)
        # сохраняем сводку по использованию материала для формирования последующего отчёта
        cached_material_quantity_before: int = cached_material.purchased + cached_material.manufactured

        # считаем необходимое и достаточное кол-во материала с учётом me текущего уровня
        if m.industry and m.industry.action in [profit.QIndustryAction.invention]:
            assert planned_blueprints == 1
            quantity_with_efficiency: int = planned_blueprints * profit.efficiency_calculator(
                industry.action,
                1,  # кол-во run-ов чертежа (инвент считается отдельно)
                m.quantity,  # кол-во из исходного чертежа (до учёта всех бонусов)
                0,  # me на инвенты и копирку не действуют
                industry.factory_bonuses)
        elif m.industry and m.industry.action in [profit.QIndustryAction.copying]:
            assert m.quantity == 1
            quantity_with_efficiency = m.quantity
            # TODO: quantity_with_efficiency = math.ceil(usage_chain)  # кол-во прогонов копий (зависит от вероятности инвента)
        else:  # if industry.action in [profit.QIndustryAction.manufacturing, profit.QIndustryAction.reaction]:
            quantity_with_efficiency: int = planned_blueprints * profit.efficiency_calculator(
                industry.action,
                planned_runs,  # кол-во run-ов (кол-во продуктов, которые требует предыдущий уровень)
                m.quantity,  # кол-во из исходного чертежа (до учёта всех бонусов)
                industry.me if industry.action == profit.QIndustryAction.manufacturing else 0,  # me предыдущего чертежа
                industry.factory_bonuses)

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
            cached_material_quantity_after: int = cached_material.purchased
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
                cached_material_quantity_after: int = cached_material.manufactured
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

                # считаем стоимость работы с учётом кол-ва запусков
                next_level_job_cost: int = math.ceil(
                    next_industry_level_blueprints *
                    next_industry_level_runs *
                    next_level_activity.industry_job_cost.total_job_cost *
                    usage_chain * usage_ratio)
                cached_material.increase_job_cost(next_level_job_cost)
                # сохраняем сведения о потраченных исоньках на запуск работок
                job_cost_accumulator.increment_total_paid(next_level_job_cost)

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

        # и производство и закуп одного и того же материала тоже не допускаем
        assert (cached_material.purchased > 0) != (cached_material.manufactured > 0)

    return current_level_activity


def generate_industry_plan(
        customized_runs: int,
        base_industry: profit.QIndustryTree,
        # настройки генерации отчёта, см. также eve_conveyor_tools.py : setup_blueprint_details
        industry_plan_customization: typing.Optional[profit.QIndustryPlanCustomization]) -> profit.QIndustryPlan:
    assert len(base_industry.materials) > 0
    assert customized_runs > 0

    # подразумеваем входные данные (один чертёж, использоваться в котором будут ВСЯ выходная продукция, т.ч. ratio=1.0)
    planned_blueprints: int = 1
    startup_usage_chain: float = 1.0
    startup_usage_ratio: float = 1.0

    # формируем отчёт с планом производства
    industry_plan: profit.QIndustryPlan = profit.QIndustryPlan(
        customized_runs,
        industry_plan_customization)

    # рекурсивно обходим все материалы, применяем настройки оптимизации производства и применяем сведения об ME;
    # в настройках производства д.б. заранее задано кол-во запусков - учитываем параметр customized_runs
    base_activity: profit.QPlannedActivity = generate_industry_plan__internal(
        None,
        planned_blueprints,
        customized_runs,
        base_industry.products_per_single_run * customized_runs,
        startup_usage_chain * startup_usage_ratio,
        base_industry,
        industry_plan)
    industry_plan.set_base_planned_activity(base_activity)

    # считаем стоимость работы с учётом кол-ва запусков
    next_level_job_cost: int = math.ceil(
        planned_blueprints *
        customized_runs *
        base_activity.industry_job_cost.total_job_cost *
        startup_usage_chain * startup_usage_ratio)
    # TODO: cached_material.increase_job_cost(next_level_job_cost)
    # сохраняем сведения о потраченных исоньках на запуск работок
    industry_plan.job_cost_accumulator.increment_total_paid(next_level_job_cost)

    return industry_plan


def assemble_industry_jobs(
        planned_activity: profit.QPlannedActivity,
        industry_formula: profit.QIndustryFormula,
        usage_chain: float) -> None:
    job_cost: typing.Optional[profit.QPlannedJobCost] = planned_activity.industry_job_cost
    assert job_cost is not None

    if planned_activity.industry.action == profit.QIndustryAction.invention:
        estimated_blueprint_type_id: int = planned_activity.industry.product.type_id
    else:
        estimated_blueprint_type_id: int = planned_activity.industry.blueprint_type_id
    industry_formula.append_job_cost(
        usage_chain,
        job_cost.system_indices.solar_system_id,
        estimated_blueprint_type_id,
        planned_activity.planned_blueprints,
        planned_activity.planned_runs,
        planned_activity.industry.action.to_int(),
        job_cost.role_bonus_job_cost,
        job_cost.rigs_bonus_job_cost,
        job_cost.scc_surcharge,
        job_cost.facility_tax)

    for m1_planned_material in planned_activity.planned_materials:
        m1_obtaining_plan: profit.QIndustryObtainingPlan = m1_planned_material.obtaining_plan
        m1_planned_activity: profit.QPlannedActivity = m1_obtaining_plan.activity_plan
        if m1_planned_activity:
            assemble_industry_jobs(
                m1_planned_activity,
                industry_formula,
                m1_planned_material.usage_chain * m1_planned_material.usage_ratio)


def assemble_industry_formula(industry_plan: profit.QIndustryPlan) -> profit.QIndustryFormula:
    # пытаемся получить использованный декриптор
    used_decryptor_type_id: typing.Optional[int] = None
    invent_tree: typing.Optional[profit.QIndustryTree] = next((
        _.obtaining_plan.activity_plan.industry for _ in industry_plan.base_planned_activity.planned_materials
        if _.obtaining_plan.activity_plan and
        _.obtaining_plan.activity_plan.industry.action == profit.QIndustryAction.invention), None)
    if invent_tree and invent_tree.decryptor_probability is not None:
        used_decryptor_type_id = invent_tree.materials[-1].type_id
    # получаем информацию об исходном чертеже (актуально для чертежей, в которые инвентятся разные варианты)
    prior_blueprint_type_id: typing.Optional[int] = next((
        _.industry.blueprint_type_id for _ in industry_plan.base_industry.materials
        if _.industry and _.industry.action == profit.QIndustryAction.invention), None)
    # составляем производственную формулу
    industry_formula: profit.QIndustryFormula = profit.QIndustryFormula(
        prior_blueprint_type_id,
        industry_plan.base_industry.blueprint_type_id,
        industry_plan.base_industry.product_type_id,
        used_decryptor_type_id,
        industry_plan.customized_runs,
        industry_plan.base_industry.products_per_single_run,
        industry_plan.base_industry.me,
        industry_plan.base_industry.te)
    # выполняем рекурсивный поиск всех работ чтобы посчитать их стоимость
    assemble_industry_jobs(industry_plan.base_planned_activity, industry_formula, 1.0)
    # считаем сколько покупных материалов и в какой пропорции необходимо для постройки продукта
    for type_id in industry_plan.materials_repository.materials.keys():
        m: profit.QIndustryMaterial = industry_plan.materials_repository.get_material(type_id)
        # алгоритм не должен запускаться с загруженными сведениями по имеющимся ассетам и ведущимся работам,
        # иначе формула будет неправильной
        assert m.in_progress == 0 and m.available_in_assets == 0
        # и производство и закуп одного и того же материала тоже не пропускаем
        assert (m.purchased > 0) != (m.manufactured > 0)
        # получение данных по материалу
        if m.purchased:
            m3_tid: int = m.base.type_id
            # m3_tnm: str = m.base.name
            m3_r: float = m.purchased_ratio  # количество (доля от требуемого кол-ва с учётом вложенных уровней)
            industry_formula.append_purchase(m3_tid, m3_r)
    return industry_formula
