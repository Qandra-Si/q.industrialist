# -*- encoding: utf-8 -*-
import typing
import enum


class QBaseMaterial:
    def __init__(self,
                 type_id: int,
                 name: str,
                 group_id: int,
                 group_name: str,
                 volume: float,
                 price: typing.Optional[float],
                 adjusted_price: typing.Optional[float]):
        self.__type_id: int = type_id
        self.__name: str = name
        self.__group_id: int = group_id
        self.__group_name: str = group_name
        self.__volume: float = volume  # TODO: это не упакованный размер! актуальные данные скачиваются в БД
        self.__price: typing.Optional[float] = price
        self.__adjusted_price: typing.Optional[float] = adjusted_price

    @property
    def type_id(self) -> int:
        return self.__type_id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def group_id(self) -> int:
        return self.__group_id

    @property
    def group_name(self) -> str:
        return self.__group_name

    @property
    def volume(self) -> float:
        return self.__volume

    @property
    def price(self) -> typing.Optional[float]:
        return self.__price

    @property
    def adjusted_price(self) -> typing.Optional[float]:
        return self.__adjusted_price


class QMaterial(QBaseMaterial):
    def __init__(self,
                 type_id: int,
                 quantity: int,
                 name: str,
                 group_id: int,
                 group_name: str,
                 volume: float,
                 price: typing.Optional[float],
                 adjusted_price: typing.Optional[float]):
        super().__init__(type_id, name, group_id, group_name, volume, price, adjusted_price)
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
    invent = 8
    reaction = 9


class QIndustryTree:
    def __init__(self,
                 blueprint_type_id: int,
                 blueprint_name: str,
                 product_type_id: int,
                 product_name: str,
                 action: QIndustryAction,
                 products_per_single_run: int,
                 single_run_time: int):
        self.__blueprint_type_id: int = blueprint_type_id
        self.__blueprint_name: str = blueprint_name
        self.__product_type_id: int = product_type_id
        self.__product_name: str = product_name
        self.__products_per_single_run: int = products_per_single_run
        self.__single_run_time: int = single_run_time
        self.__action: QIndustryAction = action
        self.__materials: typing.List[QMaterial] = []
        # базовые, исходные сведения (даны в самом начале расчёта), во всех остальных случаях (подбор имеющихся в
        # ассетах чертежей), данные параметры должны быть упомянуты в QPlannedActivity
        self.__me: int = 10 if action.value == QIndustryAction.manufacturing else 0
        self.__blueprint_runs_per_single_copy: typing.Optional[int] = None
        self.__invent_probability: typing.Optional[float] = None
        self.__decryptor_probability: typing.Optional[float] = None
        # стоимость материалов для me=0 (используется для расчёта industry job cost)
        self.__estimated_items_value: typing.Optional[float] = None

    @property
    def blueprint_type_id(self) -> int:
        return self.__blueprint_type_id

    @property
    def blueprint_name(self) -> str:
        return self.__blueprint_name

    @property
    def product_type_id(self) -> int:
        return self.__product_type_id

    @property
    def product_name(self) -> str:
        return self.__product_name

    @property
    def action(self) -> QIndustryAction:
        return self.__action

    @property
    def products_per_single_run(self) -> int:
        return self.__products_per_single_run

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
    def estimated_items_value(self) -> typing.Optional[float]:
        return self.__estimated_items_value

    def set_estimated_items_value(self, estimated_items_value: float):
        self.__estimated_items_value = estimated_items_value
