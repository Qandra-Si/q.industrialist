# -*- encoding: utf-8 -*-
import math
import typing
from .industry_tree import QIndustryAction
from .industry_tree import QIndustryFactoryBonuses


def get_decryptor_parameters(
        blueprint_me: int,
        blueprint_te: int,
        blueprint_runs: int,
        blueprint_runs_per_single_copy: int,
        blueprint_meta_group_id: typing.Optional[int]) \
        -> typing.Optional[typing.Tuple[int, float]]:  # type_id, probability
    decryptor_type_id: typing.Optional[int] = None
    decryptor_probability: typing.Optional[float] = None

    if blueprint_meta_group_id == 2:  # Tech II
        if blueprint_me == 2 and blueprint_te == 4:  # and blueprint_runs == blueprint_runs_per_single_copy:
            pass
        elif blueprint_me == (2+2) and blueprint_te == (4+10) and blueprint_runs == (blueprint_runs_per_single_copy+1):
            # Accelerant Decryptor : probability +20%, runs +1, me +2, te +10
            decryptor_type_id = 34201
            decryptor_probability = +0.2
        elif blueprint_me == (2-1) and blueprint_te == (4+4) and blueprint_runs == (blueprint_runs_per_single_copy+4):
            # Attainment Decryptor : probability +80%, runs +4, me -1, te +4
            decryptor_type_id = 34202
            decryptor_probability = +0.8
        elif blueprint_me == (2-2) and blueprint_te == (4+2) and blueprint_runs == (blueprint_runs_per_single_copy+9):
            # Augmentation Decryptor : probability -40%, runs +9, me -2, te +2
            decryptor_type_id = 34203
            decryptor_probability = -0.4
        elif blueprint_me == (2+1) and blueprint_te == (4-2) and blueprint_runs == (blueprint_runs_per_single_copy+2):
            # Optimized Attainment Decryptor : probability +90%, runs +2, me +1, te -2
            decryptor_type_id = 34207
            decryptor_probability = +0.9
        elif blueprint_me == (2+2) and blueprint_te == (4+0) and blueprint_runs == (blueprint_runs_per_single_copy+7):
            # Optimized Augmentation Decryptor : probability -10%, runs +7, me +2, te +0
            decryptor_type_id = 34208
            decryptor_probability = -0.1
        elif blueprint_me == (2+1) and blueprint_te == (4-2) and blueprint_runs == (blueprint_runs_per_single_copy+3):
            # Parity Decryptor : probability +50%, runs +3, me +1, te -2
            decryptor_type_id = 34204
            decryptor_probability = +0.5
        elif blueprint_me == (2+3) and blueprint_te == (4+6) and blueprint_runs == (blueprint_runs_per_single_copy+0):
            # Process Decryptor : probability +10%, runs +0, me +3, te +6
            decryptor_type_id = 34205
            decryptor_probability = +0.1
        elif blueprint_me == (2+1) and blueprint_te == (4+8) and blueprint_runs == (blueprint_runs_per_single_copy+2):
            # Symmetry Decryptor : probability +0, runs +2, me +1, te +8
            decryptor_type_id = 34206
            decryptor_probability = +0.0
        else:
            assert 0
    elif blueprint_meta_group_id == 14:  # Tech III
        if blueprint_me == 2 and blueprint_te == 3:  # and blueprint_runs == blueprint_runs_per_single_copy:
            pass
        elif blueprint_me == (2+2) and blueprint_te == (3+10) and blueprint_runs == (blueprint_runs_per_single_copy+1):
            # Accelerant Decryptor : probability +20%, runs +1, me +2, te +10
            decryptor_type_id = 34201
            decryptor_probability = +0.2
        elif blueprint_me == (2-1) and blueprint_te == (3+4) and blueprint_runs == (blueprint_runs_per_single_copy+4):
            # Attainment Decryptor : probability +80%, runs +4, me -1, te +4
            decryptor_type_id = 34202
            decryptor_probability = +0.8
        elif blueprint_me == (2-2) and blueprint_te == (3+2) and blueprint_runs == (blueprint_runs_per_single_copy+9):
            # Augmentation Decryptor : probability -40%, runs +9, me -2, te +2
            decryptor_type_id = 34203
            decryptor_probability = -0.4
        elif blueprint_me == (2+1) and blueprint_te == (3-2) and blueprint_runs == (blueprint_runs_per_single_copy+2):
            # Optimized Attainment Decryptor : probability +90%, runs +2, me +1, te -2
            decryptor_type_id = 34207
            decryptor_probability = +0.9
        elif blueprint_me == (2+2) and blueprint_te == (3+0) and blueprint_runs == (blueprint_runs_per_single_copy+7):
            # Optimized Augmentation Decryptor : probability -10%, runs +7, me +2, te +0
            decryptor_type_id = 34208
            decryptor_probability = -0.1
        elif blueprint_me == (2+1) and blueprint_te == (3-2) and blueprint_runs == (blueprint_runs_per_single_copy+3):
            # Parity Decryptor : probability +50%, runs +3, me +1, te -2
            decryptor_type_id = 34204
            decryptor_probability = +0.5
        elif blueprint_me == (2+3) and blueprint_te == (3+6) and blueprint_runs == (blueprint_runs_per_single_copy+0):
            # Process Decryptor : probability +10%, runs +0, me +3, te +6
            decryptor_type_id = 34205
            decryptor_probability = +0.1
        elif blueprint_me == (2+1) and blueprint_te == (3+8) and blueprint_runs == (blueprint_runs_per_single_copy+2):
            # Symmetry Decryptor : probability +0, runs +2, me +1, te +8
            decryptor_type_id = 34206
            decryptor_probability = +0.0
        else:
            assert 0

    if decryptor_type_id:
        if decryptor_probability:
            return decryptor_type_id, decryptor_probability
        else:
            return decryptor_type_id, 0.0
    else:
        return None


def efficiency_calculator(
        # тип производства - это чертёж или формула, или реакция?
        activity: QIndustryAction,
        # кол-во run-ов
        runs_quantity: int,
        # кол-во из исходного чертежа (до учёта всех бонусов, ME0)
        material_quantity: int,
        # me-параметр чертежа
        blueprint_material_efficiency: int,
        # сведения о бонусах структуры и её ригах, там где будет выполняться производство по этому чертежу
        factory_bonuses: QIndustryFactoryBonuses) -> int:
    if material_quantity == 1:
        # не может быть потрачено материалов меньше, чем 1 штука на 1 ран,
        # это значит, что 1шт*11run*(100-1-4.2-4)/100=9.988 => всё равно 11шт
        need_quantity: int = runs_quantity
    else:
        role_bonus: float = factory_bonuses.get_role_bonus(str(activity), 'me') * 100.0
        rigs_bonus: float = factory_bonuses.get_rigs_bonus(str(activity), 'me') * 100.0
        if activity == QIndustryAction.reaction:
            # -2.2% structure role bonus
            stage1: int = runs_quantity * material_quantity
            # учитываем бонус профиля сооружения
            stage2: float = float(stage1 * (100.0 + role_bonus) / 100.0)
            # учитываем бонус установленного модификатора
            stage3: float = float(stage2 * (100.0 + rigs_bonus) / 100.0)
            # округляем вещественное число до старшего целого
            stage4: int = int(float(stage3 + 0.99))
            # ---
            need_quantity: int = stage4
        # elif activity == QIndustryAction.manufacturing:
        else:  # общий тип расчёта как и для manufacturing
            # -1% structure role bonus, -4.2% installed rig
            # см. 1 x run: http://prntscr.com/u0g07w
            # см. 4 x run: http://prntscr.com/u0g0cd
            # см.11 x run: https://prnt.sc/v3mk1m
            # см. экономия материалов: http://prntscr.com/u0g11u
            # ---
            # считаем бонус чертежа (накладываем ME чертежа на БПЦ)
            stage1: float = float(material_quantity * runs_quantity * (100 - blueprint_material_efficiency) / 100.0)
            # учитываем бонус профиля сооружения
            stage2: float = float(stage1 * (100.0 + role_bonus) / 100.0)
            # учитываем бонус установленного модификатора
            stage3: float = float(stage2 * (100.0 + rigs_bonus) / 100.0)
            # округляем вещественное число до старшего целого
            stage4: int = int(float(stage3 + 0.99))
            # ---
            need_quantity: int = stage4
    return need_quantity
