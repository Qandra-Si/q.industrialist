# -*- encoding: utf-8 -*-
import typing


class QBaseMaterial:
    def __init__(self,
                 type_id: int,
                 name: str,
                 group_id: int,
                 group_name: str,
                 volume: float,
                 price: typing.Optional[float]):
        self.__type_id: int = type_id
        self.__name: str = name
        self.__group_id: int = group_id
        self.__group_name: str = group_name
        self.__volume: float = volume  # TODO: это не упакованный размер! актуальные данные скачиваются в БД
        self.__price: typing.Optional[float] = price

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


class QMaterial(QBaseMaterial):
    def __init__(self,
                 type_id: int,
                 quantity: int,
                 name: str,
                 group_id: int,
                 group_name: str,
                 volume: float,
                 price: typing.Optional[float]):
        super().__init__(type_id, name, group_id, group_name, volume, price)
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


class QIndustryTree:
    def __init__(self,
                 blueprint_type_id: int,
                 blueprint_name: str,
                 product_type_id: int,
                 product_name: str,
                 formula: bool,
                 products_per_single_run: int,
                 single_run_time: int):
        self.__blueprint_type_id: int = blueprint_type_id
        self.__blueprint_name: str = blueprint_name
        self.__product_type_id: int = product_type_id
        self.__product_name: str = product_name
        self.__products_per_single_run: int = products_per_single_run
        self.__single_run_time: int = single_run_time
        self.__is_formula: bool = formula
        self.__materials: typing.List[QMaterial] = []
        self.__me: int = 0 if formula else 10  # TODO: переместить этот параметр в QPlannedActivity

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
    def is_formula(self) -> bool:
        return self.__is_formula

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
