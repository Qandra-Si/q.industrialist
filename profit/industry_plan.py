# -*- encoding: utf-8 -*-
import typing
from .industry_tree import QBaseMaterial
from .industry_tree import QMaterial
from .industry_tree import QIndustryTree


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
    def activity_plan(self):
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


class QPlannedActivity:
    def __init__(self,
                 industry: QIndustryTree,
                 planned_blueprint: QPlannedBlueprint,
                 planned_blueprints: int):
        self.__industry: QIndustryTree = industry
        self.__planned_blueprint: QPlannedBlueprint = planned_blueprint
        self.__planned_blueprints: int = planned_blueprints
        self.__planned_materials: typing.List[QPlannedMaterial] = []

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


class QIndustryMaterial:
    def __init__(self, base: QBaseMaterial):
        self.__base: QBaseMaterial = base
        self.__purchased: int = 0
        self.__manufactured: int = 0
        self.__manufacture_rest: int = 0
        self.__available_in_assets: int = 0
        self.__in_progress: int = 0
        self.__purchased_ratio: float = 0.0
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


class QIndustryPlanCustomization:
    def __init__(self,
                 reaction_runs: typing.Optional[int],
                 industry_time: typing.Optional[int],
                 min_probability: typing.Optional[float]):
        self.__reaction_runs: typing.Optional[int] = reaction_runs
        self.__industry_time: typing.Optional[int] = industry_time
        self.__min_probability: typing.Optional[float] = min_probability

    @property
    def reaction_runs(self) -> typing.Optional[int]:
        return self.__reaction_runs

    @property
    def industry_time(self) -> typing.Optional[int]:
        return self.__industry_time

    @property
    def min_probability(self) -> typing.Optional[float]:
        return self.__min_probability


class QIndustryPlan:
    def __init__(self,
                 customized_runs: int,
                 customization: typing.Optional[QIndustryPlanCustomization] = None):
        self.__customized_runs: int = customized_runs
        self.__base_planned_activity: typing.Optional[QPlannedActivity] = None
        self.__customization: typing.Optional[QIndustryPlanCustomization] = customization
        self.__materials_repository: QIndustryMaterialsRepository = QIndustryMaterialsRepository()

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
