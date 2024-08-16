# -*- encoding: utf-8 -*-
import typing
import enum


class QBaseMaterial:
    def __init__(self,
                 type_id: int,
                 name: str,
                 market_group_id: int,
                 market_group_name: str,
                 is_commonly_used: bool,
                 volume: float,
                 price: typing.Optional[float],
                 adjusted_price: float):
        self.__type_id: int = type_id
        self.__name: str = name
        self.__market_group_id: int = market_group_id
        self.__market_group_name: str = market_group_name
        self.__is_commonly_used: bool = is_commonly_used
        self.__volume: float = volume  # TODO: это не упакованный размер! актуальные данные скачиваются в БД
        self.__price: typing.Optional[float] = price
        self.__adjusted_price: float = adjusted_price

    @property
    def type_id(self) -> int:
        return self.__type_id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def market_group_id(self) -> int:
        return self.__market_group_id

    @property
    def market_group_name(self) -> str:
        return self.__market_group_name

    @property
    def is_commonly_used(self) -> bool:
        return self.__is_commonly_used

    @property
    def volume(self) -> float:
        return self.__volume

    @property
    def price(self) -> typing.Optional[float]:
        return self.__price

    @property
    def adjusted_price(self) -> float:
        return self.__adjusted_price


class QMaterial(QBaseMaterial):
    def __init__(self,
                 type_id: int,
                 quantity: int,
                 name: str,
                 group_id: int,
                 group_name: str,
                 is_commonly_used: bool,
                 volume: float,
                 price: typing.Optional[float],
                 adjusted_price: float):
        super().__init__(type_id, name, group_id, group_name, is_commonly_used, volume, price, adjusted_price)
        self.__quantity: int = quantity
        self.__industry: typing.Optional[QIndustryTree] = None

    @property
    def quantity(self) -> int:
        return self.__quantity

    @property
    def industry(self):
        return self.__industry

    def set_industry(self, industry):
        self.__industry = industry


class QIndustryAction(enum.Enum):
    manufacturing = 1
    copying = 5
    invention = 8
    reaction = 9

    def __str__(self) -> str:
        if self == QIndustryAction.manufacturing:
            return 'manufacturing'
        elif self == QIndustryAction.copying:
            return 'copying'
        elif self == QIndustryAction.invention:
            return 'invention'
        elif self == QIndustryAction.reaction:
            return 'reaction'
        else:
            raise Exception('Unknown activity type')

    def to_int(self) -> int:
        return int(self.value)

    @staticmethod
    def from_str(label):
        if label == 'manufacturing':
            return QIndustryAction.manufacturing
        elif label == 'invention':
            return QIndustryAction.invention
        elif label == 'copying':
            return QIndustryAction.copying
        elif label == 'reaction':
            return QIndustryAction.reaction
        else:
            raise Exception('Unknown activity label')


class QIndustryFactoryBonuses:
    class Bonus:
        def __init__(self, activity: str, me: float, te: float, job_cost: float):
            self.__activity: str = activity
            self.me: float = me / 100.0
            self.te: float = te / 100.0
            self.job_cost: float = job_cost / 100.0

        @property
        def activity(self) -> str:
            return self.__activity

        def get_bonus(self, bonus: str) -> float:
            if bonus == 'me':
                return self.me
            elif bonus == 'te':
                return self.te
            elif bonus == 'job_cost':
                return self.job_cost
            else:
                assert 0

    class RoleBonus(Bonus):
        def __init__(self, activity: str, me: float, te: float, job_cost: float):
            super().__init__(activity, me, te, job_cost)

    class BonusRig(Bonus):
        def __init__(self, activity: str, me: float, te: float, job_cost: float):
            super().__init__(activity, me, te, job_cost)

    def __init__(self, structure: str, structure_rigs: typing.List[typing.Any]):
        self.role_bonuses: typing.List[QIndustryFactoryBonuses.RoleBonus] = []
        self.bonus_rigs: typing.List[QIndustryFactoryBonuses.BonusRig] = []
        if structure == 'Sotiyo':
            # Sotiyo: me -1% (manufacturing),
            #         te -30% (manufacturing and science),
            #         job_cost -5% (manufacturing and science)
            self.role_bonuses.append(QIndustryFactoryBonuses.RoleBonus('manufacturing',        -1.0, -30.0, -5.0))
            self.role_bonuses.append(QIndustryFactoryBonuses.RoleBonus('research_material', 0.0, -30.0, -5.0))
            self.role_bonuses.append(QIndustryFactoryBonuses.RoleBonus('research_time',     0.0, -30.0, -5.0))
            self.role_bonuses.append(QIndustryFactoryBonuses.RoleBonus('copying',           0.0, -30.0, -5.0))
            self.role_bonuses.append(QIndustryFactoryBonuses.RoleBonus('invent',            0.0, -30.0, -5.0))
        elif structure == 'Athanor':
            # Athanor: нет производственных бонусов
            pass
        elif structure == 'Azbel':
            # Azbel: me -1% (manufacturing),
            #        te -20% (manufacturing and science),
            #        job_cost -4% (manufacturing and science)
            self.role_bonuses.append(QIndustryFactoryBonuses.RoleBonus('manufacturing',        -1.0, -20.0, -4.0))
            self.role_bonuses.append(QIndustryFactoryBonuses.RoleBonus('research_material', 0.0, -20.0, -4.0))
            self.role_bonuses.append(QIndustryFactoryBonuses.RoleBonus('research_time',     0.0, -20.0, -4.0))
            self.role_bonuses.append(QIndustryFactoryBonuses.RoleBonus('copying',           0.0, -20.0, -4.0))
            self.role_bonuses.append(QIndustryFactoryBonuses.RoleBonus('invent',            0.0, -20.0, -4.0))
        elif structure == 'Tatara':
            # Tatara: te -25% (reaction)
            self.role_bonuses.append(QIndustryFactoryBonuses.RoleBonus('reaction',          0.0, -25.0, 0.0))
        elif structure == 'Raitaru':
            # Raitaru: me -1% (manufacturing),
            #          te -15% (manufacturing and science),
            #          job_cost -3% (manufacturing and science)
            self.role_bonuses.append(QIndustryFactoryBonuses.RoleBonus('manufacturing',        -1.0, -15.0, -3.0))
            self.role_bonuses.append(QIndustryFactoryBonuses.RoleBonus('research_material', 0.0, -15.0, -3.0))
            self.role_bonuses.append(QIndustryFactoryBonuses.RoleBonus('research_time',     0.0, -15.0, -3.0))
            self.role_bonuses.append(QIndustryFactoryBonuses.RoleBonus('copying',           0.0, -15.0, -3.0))
            self.role_bonuses.append(QIndustryFactoryBonuses.RoleBonus('invent',            0.0, -15.0, -3.0))
        else:
            assert 0
        for sr in structure_rigs:
            self.bonus_rigs.append(QIndustryFactoryBonuses.BonusRig(
                sr['activity'],
                sr.get('me', 0.0),
                sr.get('te', 0.0),
                sr.get('job_cost', 0.0),
            ))

    def get_role_bonus(self, activity: str, bonus: str):
        role_bonus: QIndustryFactoryBonuses.RoleBonus = next((
            _ for _ in self.role_bonuses if _.activity == activity), None)
        if not role_bonus:
            return 0.0
        else:
            return role_bonus.get_bonus(bonus)

    def get_rigs_bonus(self, activity: str, bonus: str):
        bonus_rig: QIndustryFactoryBonuses.BonusRig = next((
            _ for _ in self.bonus_rigs if _.activity == activity), None)
        if not bonus_rig:
            return 0.0
        else:
            return bonus_rig.get_bonus(bonus)


class QIndustryCostIndices:
    def __init__(self,
                 solar_system_id: int,
                 solar_system: str,
                 cost_indices,
                 product_ids: typing.Set[int],
                 factory_bonuses: QIndustryFactoryBonuses):
        self.__solar_system_id: int = solar_system_id
        self.__solar_system: str = solar_system
        self.__cost_indices = cost_indices
        self.__product_ids: typing.Set[int] = product_ids
        self.__factory_bonuses: QIndustryFactoryBonuses = factory_bonuses

    @property
    def solar_system_id(self) -> int:
        return self.__solar_system_id

    @property
    def solar_system(self) -> str:
        return self.__solar_system

    @property
    def cost_indices(self):
        return self.__cost_indices

    @property
    def product_ids(self) -> typing.Set[int]:
        return self.__product_ids

    @property
    def factory_bonuses(self) -> QIndustryFactoryBonuses:
        return self.__factory_bonuses


class QIndustryTree:
    def __init__(self,
                 blueprint_type_id: int,
                 blueprint_name: str,
                 product: QMaterial,
                 activity: QIndustryAction,
                 products_per_single_run: int,
                 max_production_limit: int,
                 single_run_time: int,
                 estimated_items_value: float,
                 system_indices: QIndustryCostIndices,
                 industry_cost_index: float):
        self.__blueprint_type_id: int = blueprint_type_id
        self.__blueprint_name: str = blueprint_name
        self.__product: QMaterial = product
        self.__products_per_single_run: int = products_per_single_run
        self.__max_production_limit: int = max_production_limit
        self.__single_run_time: int = single_run_time
        self.__activity: QIndustryAction = activity
        self.__materials: typing.List[QMaterial] = []
        # базовые, исходные сведения (даны в самом начале расчёта), во всех остальных случаях (подбор имеющихся в
        # ассетах чертежей), данные параметры должны быть упомянуты в QPlannedActivity
        self.__me: int = 10 if activity.value == QIndustryAction.manufacturing else 0
        self.__blueprint_runs_per_single_copy: typing.Optional[int] = None
        self.__invent_probability: typing.Optional[float] = None
        self.__decryptor_probability: typing.Optional[float] = None
        # входные данные для расчёта (стоимость материалов)
        self.__estimated_items_value: float = estimated_items_value  # ISK
        # сведения о производственных индексах в системе
        self.__system_indices: QIndustryCostIndices = system_indices
        self.__industry_cost_index: float = industry_cost_index

    @property
    def blueprint_type_id(self) -> int:
        return self.__blueprint_type_id

    @property
    def blueprint_name(self) -> str:
        return self.__blueprint_name

    @property
    def product_type_id(self) -> int:
        return self.__product.type_id

    @property
    def product_name(self) -> str:
        return self.__product.name

    @property
    def product(self) -> QMaterial:
        return self.__product

    @property
    def action(self) -> QIndustryAction:
        return self.__activity

    @property
    def products_per_single_run(self) -> int:
        return self.__products_per_single_run

    @property
    def max_production_limit(self) -> int:
        return self.__max_production_limit

    @property
    def single_run_time(self) -> int:
        return self.__single_run_time

    @property
    def materials(self) -> typing.List[QMaterial]:
        return self.__materials

    def append_material(self, material: QMaterial):
        self.__materials.append(material)

    @property
    def me(self) -> int:
        return self.__me

    def set_me(self, me: int):
        self.__me = me

    @property
    def blueprint_runs_per_single_copy(self) -> typing.Optional[int]:
        return self.__blueprint_runs_per_single_copy

    def set_blueprint_runs_per_single_copy(self, blueprint_runs_per_single_copy: int):
        self.__blueprint_runs_per_single_copy = blueprint_runs_per_single_copy

    @property
    def invent_probability(self) -> typing.Optional[float]:
        return self.__invent_probability

    def set_probability(self, invent_probability: float):
        self.__invent_probability = invent_probability

    @property
    def decryptor_probability(self) -> typing.Optional[float]:
        return self.__decryptor_probability

    def set_decryptor_probability(self, decryptor_probability: float):
        self.__decryptor_probability = decryptor_probability

    @property
    def estimated_items_value(self) -> float:
        return self.__estimated_items_value

    @property
    def system_indices(self) -> QIndustryCostIndices:
        return self.__system_indices

    @property
    def industry_cost_index(self) -> float:
        return self.__industry_cost_index

    @property
    def factory_bonuses(self) -> QIndustryFactoryBonuses:
        # сведения о бонусах структуры и её ригах, там где будет выполняться производство по этому чертежу
        return self.__system_indices.factory_bonuses
