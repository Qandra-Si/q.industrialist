# -*- encoding: utf-8 -*-
import math
import typing
from .industry_tree import QBaseMaterial
from .industry_tree import QMaterial
from .industry_tree import QIndustryTree
from .industry_tree import QIndustryAction
from .industry_tree import QIndustryCostIndices


class QIndustryObtainingPlan:
    def __init__(self):
        self.__reused_duplicate: bool = False
        self.__activity_plan: typing.Optional[QPlannedActivity] = None
        self.__purchase_quantity: typing.Optional[bool] = None
        self.__industry_output: typing.Optional[int] = None
        self.__not_enough_quantity: typing.Optional[int] = None
        self.__rest_quantity: typing.Optional[int] = None

    @property
    def purchase_quantity(self) -> typing.Optional[bool]:
        return self.__purchase_quantity

    @property
    def activity_plan(self):  # -> typing.Optional[QPlannedActivity]
        return self.__activity_plan

    @property
    def industry_output(self) -> typing.Optional[int]:
        return self.__industry_output

    @property
    def not_enough_quantity(self) -> typing.Optional[int]:
        return self.__not_enough_quantity

    @property
    def rest_quantity(self) -> typing.Optional[int]:
        return self.__rest_quantity

    def store_purchase(self, not_enough: int, purchase: int):
        assert self.__activity_plan is None
        assert self.__rest_quantity is None
        self.__purchase_quantity = purchase
        self.__not_enough_quantity = not_enough

    def store_manufacturing_prerequisites(self, not_enough: int, rest_materials: int, industry_output: int):
        assert self.__purchase_quantity is None
        self.__not_enough_quantity = not_enough
        self.__rest_quantity = rest_materials
        self.__industry_output = industry_output

    def store_manufacturing_activity_plan(self, activity_plan):
        assert self.__purchase_quantity is None
        self.__activity_plan = activity_plan

    @property
    def reused_duplicate(self) -> bool:
        return self.__reused_duplicate

    def mark_as_reused_duplicate(self, activity_plan=None):
        self.__reused_duplicate = True
        if activity_plan:
            self.store_manufacturing_activity_plan(activity_plan)


class QPlannedMaterial:
    def __init__(self,
                 material: QMaterial,
                 prior_planned_material,  # typing.Optional[QPlannedMaterial]
                 quantity_with_efficiency: int,
                 usage_chain: float):
        self.__material: QMaterial = material
        self.__prior_planned_material: typing.Optional[QPlannedMaterial] = prior_planned_material
        self.__quantity_with_efficiency: int = quantity_with_efficiency
        self.__obtaining_plan: QIndustryObtainingPlan = QIndustryObtainingPlan()
        self.__usage_chain: float = usage_chain
        self.__usage_ratio: float = 0.0
        self.__summary_ratio_before: float = 0.0
        self.__summary_ratio_after: float = 0.0
        self.__summary_quantity_before: int = 0
        self.__summary_quantity_after: int = 0

    @property
    def material(self) -> QMaterial:
        return self.__material

    @property
    def prior_planned_material(self):  # typing.Optional[QPlannedMaterial]
        return self.__prior_planned_material

    @property
    def quantity_with_efficiency(self) -> int:
        return self.__quantity_with_efficiency

    @property
    def obtaining_plan(self) -> QIndustryObtainingPlan:
        return self.__obtaining_plan

    @property
    def usage_chain(self) -> float:
        return self.__usage_chain

    # def store_usage_chain(self, usage_chain: float):
    #     self.__usage_chain = usage_chain

    @property
    def usage_ratio(self) -> float:
        return self.__usage_ratio

    def store_usage_ratio(self, usage_ratio: float):
        self.__usage_ratio = usage_ratio

    @property
    def summary_ratio_before(self) -> float:
        return self.__summary_ratio_before

    @property
    def summary_ratio_after(self) -> float:
        return self.__summary_ratio_after

    @property
    def summary_quantity_before(self) -> int:
        return self.__summary_quantity_before

    @property
    def summary_quantity_after(self) -> int:
        return self.__summary_quantity_after

    def store_summary_quantity(self, before: int, after: int):
        self.__summary_quantity_before = before
        self.__summary_quantity_after = after

    def store_summary_ratio(self, before: float, after: float):
        self.__summary_ratio_before = before
        self.__summary_ratio_after = after


class QPlannedBlueprint(QPlannedMaterial):
    def __init__(self,
                 blueprint: QMaterial,
                 usage_chain: float,
                 products_per_single_run: int,
                 planned_runs: int,
                 planned_me: int,
                 planned_te: int):
        super().__init__(blueprint, None, 1, usage_chain)
        self.__products_per_single_run: int = products_per_single_run
        self.__runs: int = planned_runs
        self.__me: int = planned_me
        self.__te: int = planned_te

    @property
    def products_per_single_run(self) -> int:
        return self.__products_per_single_run

    @property
    def runs(self) -> int:
        return self.__runs

    @property
    def me(self) -> int:
        return self.__me

    @property
    def te(self) -> int:
        return self.__te


class QPlannedJobCost:
    def __init__(self,
                 action: QIndustryAction,
                 estimated_items_value: float,
                 system_indices: QIndustryCostIndices,
                 industry_cost_index: float):
        # входные данные для расчёта (стоимость материалов, производственный индекс в системе)
        self.estimated_items_value: float = estimated_items_value  # ISK
        # сведения о производственных индексах в системе
        self.system_indices: QIndustryCostIndices = system_indices
        self.industry_cost_index: float = industry_cost_index  # процент
        # расчёт стоимости работы
        if action in [QIndustryAction.manufacturing, QIndustryAction.reaction]:
            self.__job_cost_base: float = self.estimated_items_value  # ISK
        else:  # copying, invention
            self.__job_cost_base: float = self.estimated_items_value * 0.02  # ISK
        # внимание! недостаточная точность расчёта общей стоимости проекта в этом месте возможна потому, что
        # индекс стоимости проектов в системе ingame показывается как 5.97%, от ESI он же приходит как 0.0597,
        # хотя на самом деле является 878020 / 14719117 = 0.05965167611616919683429379629226
        # а если быть точнее, то      878019 / 14719117 = 0.05965160817731117973992597517908
        #                             878021 / 14719117 = 0.05965174405502721392866161740545
        # число должно иметь точность как минимум 8 знаков после запятой, а не 4 (как приходит по ESI)
        # --- итоги расчёта:
        # |                       |     моя версия |     ingame | на самом деле |
        # | estimated_items_value |     14'719'117 | 14'719'117 |               | <== правильно
        # |   industry_cost_index |          5.97% |      5.97% |      5.965167 | <== низкая точность, страдает расчёт
        # |           system_cost |   878'731.2849 |            |               |
        # |                       |        878'732 |    878'020 |     878'019.9 | <== разница в  712 ISK
        # |  structure_bonus_rigs |          -5.0% |      -5.0% |               |
        # |  structure_role_bonus | -43'936.564245 |            |               |
        # |                       |        -43'937 |    -43'901 |               | <== разница в  36 ISK
        # |  total_job_gross_cost | 834'794.720655 |            |               |
        # |                       |        834'795 |    834'119 |               | <== разница в  676 ISK
        # |         scc_surcharge |         -4.00% |      4.00% |               |
        # |     tax_scc_surcharge |     588'764.68 |            |               |
        # |                       |        588'765 |    588'765 |               | <== правильно
        # |           total_taxes |        588'765 |    588'765 |               | <== правильно
        # |        total_job_cost |      1'423'560 |  1'422'884 |               | <== разница в  676 ISK
        self.system_cost: int = int(math.ceil(self.__job_cost_base * self.industry_cost_index))  # ISK
        self.role_bonus_job_cost: float = system_indices.factory_bonuses.get_role_bonus(str(action), 'job_cost')
        self.structure_role_bonus: int = int(math.ceil(self.system_cost * self.role_bonus_job_cost))  # ISK
        self.rigs_bonus_job_cost: float = system_indices.factory_bonuses.get_rigs_bonus(str(action), 'job_cost')
        self.structure_rigs_bonus: int = int(math.ceil(self.system_cost * self.rigs_bonus_job_cost))  # ISK
        self.total_job_gross_cost: int = self.system_cost + self.structure_role_bonus + self.structure_rigs_bonus  # ISK
        self.scc_surcharge: float = 0.04  # TODO: процент должен быть перенесён в настройки routing-а (system_indices)?
        self.tax_scc_surcharge: int = int(math.ceil(self.__job_cost_base * self.scc_surcharge))  # ISK
        self.facility_tax: float = 0.00  # TODO: процент должен быть перенесён в настройки routing-а (system_indices)?
        self.tax_facility: int = int(math.ceil(self.__job_cost_base * self.facility_tax))  # ISK
        self.total_taxes: int = self.tax_scc_surcharge + self.tax_facility  # ISK
        self.total_job_cost: int = self.total_job_gross_cost + self.total_taxes  # ISK


class QPlannedActivity:
    def __init__(self,
                 industry: QIndustryTree,
                 planned_blueprint: QPlannedBlueprint,
                 planned_blueprints: int,
                 industry_job_cost: typing.Optional[QPlannedJobCost]):
        self.__industry: QIndustryTree = industry
        self.__planned_blueprint: QPlannedBlueprint = planned_blueprint
        self.__planned_blueprints: int = planned_blueprints
        self.__planned_materials: typing.List[QPlannedMaterial] = []
        # стоимость одного прогона (не зависит от me чертежа и не зависит от декрипторов инвента)
        self.__industry_job_cost: typing.Optional[QPlannedJobCost] = industry_job_cost

    @property
    def industry(self) -> QIndustryTree:
        return self.__industry

    @property
    def planned_blueprint(self) -> QPlannedBlueprint:
        return self.__planned_blueprint

    @property
    def planned_blueprints(self) -> int:
        return self.__planned_blueprints

    @property
    def planned_runs(self) -> int:
        return self.__planned_blueprint.runs

    @property
    def planned_me(self) -> int:
        return self.__planned_blueprint.me

    @property
    def planned_te(self) -> int:
        return self.__planned_blueprint.te

    @property
    def planned_quantity(self) -> int:
        return self.__planned_blueprint.products_per_single_run

    @property
    def planned_materials(self) -> typing.List[QPlannedMaterial]:
        return self.__planned_materials

    def append_planned_material(self, planned_material: QPlannedMaterial):
        self.__planned_materials.append(planned_material)

    def calc_industry_job_cost(self) -> QPlannedJobCost:
        self.__industry_job_cost = QPlannedJobCost(
            self.industry.action,
            self.industry.estimated_items_value,
            self.industry.system_indices,
            self.industry.industry_cost_index)
        return self.__industry_job_cost

    @property
    def industry_job_cost(self) -> typing.Optional[QPlannedJobCost]:
        return self.__industry_job_cost


class QIndustryMaterial:
    def __init__(self, base: QBaseMaterial):
        self.__base: QBaseMaterial = base
        # это количество материалов, которые надо закупить с учётом настроек производства (некоторые материалы
        # производятся партиями на интервалах 1 суток), количество суммируется на всяком очередном закупе
        self.__purchased: int = 0
        # это __количество__ материала, накопленное с учётом пропорций "на сколько задействован материал в общем плане"
        self.__purchased_ratio: float = 0.0
        self.__manufactured: int = 0
        self.__manufacture_rest: int = 0
        self.__available_in_assets: int = 0
        self.__in_progress: int = 0
        self.__job_cost: int = 0
        self.__last_known_planned_material: typing.Optional[QPlannedMaterial] = None

    @property
    def base(self) -> QBaseMaterial:
        return self.__base

    @property
    def purchased(self) -> int:
        return self.__purchased

    def store_purchased(self, quantity: int):
        self.__purchased += quantity

    @property
    def manufactured(self) -> int:
        return self.__manufactured

    @property
    def manufacture_rest(self) -> int:
        return self.__manufacture_rest

    def store_manufacturing(self, manufactured: int, new_rest: int):
        self.__manufactured += manufactured
        self.__manufacture_rest = new_rest

    def consume_manufacture_rest(self, consumed_quantity: int):
        self.__manufacture_rest -= consumed_quantity
        assert self.__manufacture_rest >= 0

    @property
    def available_in_assets(self) -> int:
        return self.__available_in_assets

    def consume_assets(self, consumed_quantity: int):
        self.__available_in_assets -= consumed_quantity
        assert self.__available_in_assets >= 0

    @property
    def in_progress(self) -> int:
        return self.__in_progress

    def consume_in_progress(self, consumed_quantity: int):
        self.__in_progress -= consumed_quantity
        assert self.__in_progress >= 0

    def consume_industry_rest(self, quantity_with_efficiency: int) -> typing.Tuple[int, int]:
        # расчёт кол-ва материалов, которых не хватает
        cached: int = self.available_in_assets + self.in_progress + self.manufacture_rest
        not_enough: int = quantity_with_efficiency - cached
        used_rest: int = 0
        if not_enough < 0:
            not_enough = 0
        # расчёт материалов, которые предстоит построить (с учётом уже имеющихся запасов)
        if cached <= quantity_with_efficiency:
            # считаем, сколько материалов останется в неизрасходованном виде,
            # как результат текущего запуска производства
            used_rest = self.manufacture_rest
            # минусуем остатки на складе и в производстве
            self.consume_assets(self.available_in_assets)
            self.consume_in_progress(self.in_progress)
            self.consume_manufacture_rest(self.manufacture_rest)
        else:
            __left = quantity_with_efficiency - not_enough
            # минусуем остатки на складе
            if self.available_in_assets >= __left:
                self.consume_assets(__left)
                __left = 0
            else:
                __left -= self.available_in_assets
                self.consume_assets(self.available_in_assets)
            # минусуем остатки в производстве
            if __left > 0 and self.in_progress:
                if self.in_progress >= __left:
                    self.consume_in_progress(__left)
                    __left = 0
                else:
                    __left -= self.in_progress
                    self.consume_in_progress(self.in_progress)
            # считаем, сколько материалов останется в неизрасходованном виде,
            # как результат текущего запуска производства
            if __left > 0 and self.manufacture_rest > 0:
                if self.manufacture_rest >= __left:
                    used_rest = __left
                    self.consume_manufacture_rest(__left)
                    __left = 0
                else:
                    used_rest = self.manufacture_rest
                    __left -= self.manufacture_rest
                    self.consume_manufacture_rest(self.manufacture_rest)
        return not_enough, used_rest

    @property
    def purchased_ratio(self) -> float:
        return self.__purchased_ratio

    def consume_purchased_ratio(self, purchased_ratio: float):
        assert purchased_ratio > 0
        self.__purchased_ratio += purchased_ratio

    @property
    def job_cost(self) -> int:
        return self.__job_cost

    def increase_job_cost(self, job_cost: int) -> None:
        self.__job_cost += job_cost

    @property
    def last_known_planned_material(self) -> typing.Optional[QPlannedMaterial]:
        return self.__last_known_planned_material

    def set_last_known_planned_material(self, last_known_planned_material: QPlannedMaterial):
        self.__last_known_planned_material = last_known_planned_material


class QIndustryMaterialsRepository:
    def __init__(self):
        self.__materials: typing.Dict[int, QIndustryMaterial] = {}

    @property
    def materials(self) -> typing.Dict[int, QIndustryMaterial]:
        return self.__materials

    def get_material(self, type_id: int) -> typing.Optional[QIndustryMaterial]:
        return self.__materials.get(type_id)

    def register_material(self, type_id: int, base: QBaseMaterial) -> QIndustryMaterial:
        assert self.__materials.get(type_id) is None
        m: QIndustryMaterial = QIndustryMaterial(base)
        self.__materials[type_id] = m
        return m


class QIndustryJobCostAccumulator:
    def __init__(self):
        self.__total_paid: float = 0.0

    @property
    def total_paid(self) -> float:
        return self.__total_paid

    def increment_total_paid(self, job_cost: float):
        self.__total_paid += job_cost


class QIndustryPlanCustomization:
    def __init__(self,
                 reaction_runs: typing.Optional[int],
                 industry_time: typing.Optional[int],
                 common_components: typing.Optional[typing.List[int]],
                 min_probability: typing.Optional[float],
                 unknown_blueprints_me: typing.Optional[int]):
        if unknown_blueprints_me is not None:
            assert 0 <= unknown_blueprints_me <= 10
        self.__reaction_runs: typing.Optional[int] = reaction_runs
        self.__industry_time: typing.Optional[int] = industry_time
        self.__common_components: typing.Optional[typing.List[int]] = common_components
        self.__min_probability: typing.Optional[float] = min_probability
        self.__unknown_blueprints_me: typing.Optional[int] = unknown_blueprints_me

    @property
    def reaction_runs(self) -> typing.Optional[int]:
        return self.__reaction_runs

    @property
    def industry_time(self) -> typing.Optional[int]:
        return self.__industry_time

    @property
    def common_components(self) -> typing.Optional[typing.List[int]]:
        return self.__common_components

    @property
    def min_probability(self) -> typing.Optional[float]:
        return self.__min_probability

    @property
    def unknown_blueprints_me(self) -> typing.Optional[int]:
        return self.__unknown_blueprints_me


class QIndustryPlan:
    def __init__(self,
                 customized_runs: int,
                 customization: typing.Optional[QIndustryPlanCustomization] = None):
        self.__customized_runs: int = customized_runs
        self.__base_planned_activity: typing.Optional[QPlannedActivity] = None
        self.__customization: typing.Optional[QIndustryPlanCustomization] = customization
        self.__materials_repository: QIndustryMaterialsRepository = QIndustryMaterialsRepository()
        self.__job_cost_accumulator: QIndustryJobCostAccumulator = QIndustryJobCostAccumulator()

    @property
    def base_industry(self) -> QIndustryTree:
        return self.__base_planned_activity.industry

    @property
    def base_planned_activity(self) -> QPlannedActivity:
        return self.__base_planned_activity

    def set_base_planned_activity(self, base_planned_activity: QPlannedActivity):
        self.__base_planned_activity = base_planned_activity

    @property
    def customized_runs(self) -> int:
        return self.__customized_runs

    @property
    def customization(self) -> typing.Optional[QIndustryPlanCustomization]:
        return self.__customization

    @property
    def materials_repository(self) -> QIndustryMaterialsRepository:
        return self.__materials_repository

    @property
    def job_cost_accumulator(self) -> QIndustryJobCostAccumulator:
        return self.__job_cost_accumulator
