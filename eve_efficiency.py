""" Q.Industrialist (desktop/mobile)
"""
import typing
import eve_sde_tools


g_module_default_settings = {
    "corp_rules:invent": [{"market_group": "Ships", "decryptor": "Parity Decryptor"},
                          {"market_group": "Rigs", "decryptor": "Symmetry Decryptor"}]
}


def get_corp_rules_invent_effects(sde_market_groups, qidb=None):
    if not (qidb is None):
        db_generic_decryptors = qidb.select_all_rows(  # "groupID"=1304 -- Generic Decryptor
            'SELECT t."typeID","typeName",a."attributeID",a."valueFloat" '
            'FROM evesde."invTypes" AS t, evesde."dgmTypeAttributes" AS a '
            'WHERE published AND "groupID"=1304 AND t."typeID"=a."typeID";')
    else:
        db_generic_decryptors = [(34204, 'Parity Decryptor', 1112, 1.5), (34204, 'Parity Decryptor', 1113, 1.0),
                                 (34204, 'Parity Decryptor', 1114, -2.0), (34204, 'Parity Decryptor', 1124, 3.0),
                                 (34201, 'Accelerant Decryptor', 1112, 1.2), (34201, 'Accelerant Decryptor', 1113, 2.0),
                                 (34201, 'Accelerant Decryptor', 1114, 10.0), (34201, 'Accelerant Decryptor', 1124, 1.0),
                                 (34203, 'Augmentation Decryptor', 1112, 0.6),
                                 (34203, 'Augmentation Decryptor', 1113, -2.0),
                                 (34203, 'Augmentation Decryptor', 1114, 2.0), (34203, 'Augmentation Decryptor', 1124, 9.0),
                                 (34202, 'Attainment Decryptor', 1112, 1.8), (34202, 'Attainment Decryptor', 1113, -1.0),
                                 (34202, 'Attainment Decryptor', 1114, 4.0), (34202, 'Attainment Decryptor', 1124, 4.0),
                                 (34205, 'Process Decryptor', 1112, 1.1), (34205, 'Process Decryptor', 1113, 3.0),
                                 (34205, 'Process Decryptor', 1114, 6.0), (34205, 'Process Decryptor', 1124, 0.0),
                                 (34206, 'Symmetry Decryptor', 1112, 1.0), (34206, 'Symmetry Decryptor', 1113, 1.0),
                                 (34206, 'Symmetry Decryptor', 1114, 8.0), (34206, 'Symmetry Decryptor', 1124, 2.0),
                                 (34207, 'Optimized Attainment Decryptor', 1112, 1.9),
                                 (34207, 'Optimized Attainment Decryptor', 1113, 1.0),
                                 (34207, 'Optimized Attainment Decryptor', 1114, -2.0),
                                 (34207, 'Optimized Attainment Decryptor', 1124, 2.0),
                                 (34208, 'Optimized Augmentation Decryptor', 1112, 0.9),
                                 (34208, 'Optimized Augmentation Decryptor', 1113, 2.0),
                                 (34208, 'Optimized Augmentation Decryptor', 1114, 0.0),
                                 (34208, 'Optimized Augmentation Decryptor', 1124, 7.0)]

    invent_effects = {}
    for rule in g_module_default_settings["corp_rules:invent"]:
        market_group_id = eve_sde_tools.get_market_group_id_by_name(sde_market_groups, rule["market_group"])
        me_modifier = next((a[3] for a in db_generic_decryptors if (a[1]==rule["decryptor"]) and (a[2]==1113)), 0)  # inventionMEModifier
        te_modifier = next((a[3] for a in db_generic_decryptors if (a[1]==rule["decryptor"]) and (a[2]==1114)), 0)  # inventionTEModifier
        run_modifier = next((a[3] for a in db_generic_decryptors if (a[1]==rule["decryptor"]) and (a[2]==1124)), 0)  # inventionMaxRunModifier
        invent_effects.update({str(market_group_id): {"me": int(me_modifier), "te": int(te_modifier), "runs": int(run_modifier)}})

    # example: invent_effects= {'4': {'me': 1, 'te': -2, 'runs': 3}, '1111': {'me': 1, 'te': 8, 'runs': 2}}
    return invent_effects


def get_t2_bpc_attributes(
        product_type_id: int,
        invent_effects: typing.Dict[int, typing.Any],  # см. get_corp_rules_invent_effects ?
        sde_type_ids,
        sde_market_groups):
    # https://wiki.eveuniversity.org/Invention
    # Tech 2 blueprint copies always have 10 runs, +2% ME and +4% TE, unless modified by a decryptor. [1]
    # T2 BPCs for ships and rigs have 1 run (again unless modified by a decryptor). The only activity you can
    # do with a T2 BPC is to manufacture it, you cannot research or copy it.
    __market_groups_chain: typing.List[int] = eve_sde_tools.get_market_groups_chain_by_type_id(
        sde_type_ids,
        sde_market_groups,
        product_type_id)
    __market_groups = set(__market_groups_chain)
    t2_bpc_me = 2
    t2_bpc_te = 4
    t2_bpc_runs = 10
    if bool(__market_groups & {4, 1111}):  # 4=Ships, 1111=Rigs, 955=Ship and Module Modifications
        t2_bpc_runs = 1
    # учитываем правила, принятые в корпорации по использованию декрипторов
    for ie in invent_effects.items():
        if int(ie[0]) in __market_groups:
            t2_bpc_me += ie[1]["me"]
            t2_bpc_te += ie[1]["te"]
            t2_bpc_runs += ie[1]["runs"]
    return {"me": t2_bpc_me, "te": t2_bpc_te, "qr": t2_bpc_runs}


def get_industry_material_efficiency(
        # тип производства - это чертёж или формула, или реакция?
        manufacturing_activity: str,
        # кол-во run-ов
        runs_quantity: int,
        # кол-во из исходного чертежа (до учёта всех бонусов)
        __bpo_materials_quantity: int,
        # me-параметр чертежа
        material_efficiency: int):
    if __bpo_materials_quantity == 1:
        # не может быть потрачено материалов меньше, чем 1 штука на 1 ран,
        # это значит, что 1шт*11run*(100-1-4.2-4)/100=9.988 => всё равно 11шт
        __need = runs_quantity
    else:
        if manufacturing_activity == 'reaction':
            # TODO: хардкодим -2.2% structure role bonus
            __stage1 = runs_quantity * __bpo_materials_quantity
            # учитываем бонус профиля сооружения
            __stage2 = float(__stage1 * (100.0 - 2.2) / 100.0)
            # округляем вещественное число до старшего целого
            __stage3 = int(float(__stage2 + 0.99))
            # ---
            __need = __stage3
        elif manufacturing_activity == 'manufacturing':
            # TODO: хардкодим -1% structure role bonus, -4.2% installed rig
            # см. 1 x run: http://prntscr.com/u0g07w
            # см. 4 x run: http://prntscr.com/u0g0cd
            # см.11 x run: https://prnt.sc/v3mk1m
            # см. экономия материалов: http://prntscr.com/u0g11u
            # ---
            # считаем бонус чертежа (накладываем ME чертежа на БПЦ)
            __stage1 = float(__bpo_materials_quantity * runs_quantity * (100 - material_efficiency) / 100.0)
            # учитываем бонус профиля сооружения
            __stage2 = float(__stage1 * (100.0 - 1.0) / 100.0)
            # учитываем бонус установленного модификатора
            __stage3 = float(__stage2 * (100.0 - 4.2) / 100.0)
            # округляем вещественное число до старшего целого
            __stage4 = int(float(__stage3 + 0.99))
            # ---
            __need = __stage4
        elif manufacturing_activity == 'invention':
            # TODO: не используется structure role bonus
            __need = runs_quantity * __bpo_materials_quantity
        else:
            # TODO: не поддерживается расчёт... доделать
            __need = runs_quantity * __bpo_materials_quantity
    return __need


def get_t2_bpc_materials_with_efficiency(t2_bpc_attributes, materials):
    # example: materials = [{"quantity": 8, "typeID": 11399}, {"quantity": 9, "typeID": 9838}, ...]
    materials_with_me = materials[:]
    for m in materials_with_me:
        m["quantity"] = get_industry_material_efficiency(
            'manufacturing',
            t2_bpc_attributes["runs"],
            m["quantity"],
            t2_bpc_attributes["me"])
    return materials_with_me
