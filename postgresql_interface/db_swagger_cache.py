# -*- encoding: utf-8 -*-
import typing
import datetime


class QSwaggerMarketGroup:
    def __init__(self, row):
        self.__group_id: int = row[0]
        self.__parent_id: typing.Optional[int] = row[1]
        self.__semantic_id: int = row[2]
        self.__name: str = row[3]
        self.__icon_id: typing.Optional[int] = row[4]

    @property
    def group_id(self) -> int:
        return self.__group_id

    @property
    def parent_id(self) -> typing.Optional[int]:
        return self.__parent_id

    @property
    def semantic_id(self) -> int:
        return self.__semantic_id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def icon_id(self) -> typing.Optional[int]:
        return self.__icon_id


class QSwaggerTypeId:
    def __init__(self, row):
        self.__type_id: int = row[0]
        self.__name: str = row[1]
        self.__volume: typing.Optional[float] = row[2]
        self.__capacity: typing.Optional[float] = row[3]
        self.__base_price: typing.Optional[float] = row[4]
        self.__published: bool = True
        self.__market_group_id: typing.Optional[int] = row[5]
        self.__meta_group_id: typing.Optional[int] = row[6]
        self.__tech_level: typing.Optional[int] = row[7]
        self.__icon_id: typing.Optional[int] = row[8]
        self.__packaged_volume: typing.Optional[float] = row[9]

    @property
    def type_id(self) -> int:
        return self.__type_id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def volume(self) -> typing.Optional[float]:
        return self.__volume

    @property
    def capacity(self) -> typing.Optional[float]:
        return self.__capacity

    @property
    def base_price(self) -> typing.Optional[float]:
        return self.__base_price

    @property
    def published(self) -> bool:
        return self.__published

    @property
    def market_group_id(self) -> typing.Optional[int]:
        return self.__market_group_id

    @property
    def meta_group_id(self) -> typing.Optional[int]:
        return self.__meta_group_id

    @property
    def tech_level(self) -> typing.Optional[int]:
        return self.__tech_level

    @property
    def icon_id(self) -> typing.Optional[int]:
        return self.__icon_id

    @property
    def packaged_volume(self) -> typing.Optional[float]:
        return self.__packaged_volume


class QSwaggerProduct:
    def __init__(self, product_type: QSwaggerTypeId, quantity: int):
        self.__product_type: QSwaggerTypeId = product_type
        self.__quantity: int = quantity

    @property
    def product_type(self) -> QSwaggerTypeId:
        return self.__product_type

    @property
    def quantity(self) -> int:
        return self.__quantity

    @property
    def product_id(self) -> int:
        return self.__product_type.type_id


class QSwaggerInventionProduct:
    def __init__(self, product_type: QSwaggerTypeId, quantity: int, probability: float):
        self.__product_type: QSwaggerTypeId = product_type
        self.__quantity: int = quantity
        self.__probability: float = probability

    @property
    def product_type(self) -> QSwaggerTypeId:
        return self.__product_type

    @property
    def quantity(self) -> int:
        return self.__quantity

    @property
    def probability(self) -> float:
        return self.__probability

    @property
    def product_id(self) -> int:
        return self.__product_type.type_id


class QSwaggerMaterial:
    def __init__(self, material_type: QSwaggerTypeId, quantity: int):
        self.__material_type: QSwaggerTypeId = material_type
        self.__quantity: int = quantity

    @property
    def material_type(self) -> QSwaggerTypeId:
        return self.__material_type

    @property
    def quantity(self) -> int:
        return self.__quantity

    @property
    def material_id(self) -> int:
        return self.__material_type.type_id


class QSwaggerActivityMaterials:
    def __init__(self):
        self.__materials: typing.List[QSwaggerMaterial] = []

    def __del__(self):
        self.__materials.clear()
        del self.__materials

    def add_material(self, material: QSwaggerTypeId, quantity: int) -> None:
        material_id: int = material.type_id
        if [1 for m in self.__materials if m.material_id == material_id]:
            raise Exception("Unable to add blueprint activity material twice")
        self.__materials.append(QSwaggerMaterial(material, quantity))

    @property
    def materials(self) -> typing.List[QSwaggerMaterial]:
        return self.__materials


class QSwaggerActivity:
    def __init__(self, time: int):
        self.__time: int = time
        self.__materials = QSwaggerActivityMaterials()

    def __del__(self):
        del self.__materials

    @property
    def time(self) -> int:
        return self.__time

    @property
    def materials(self) -> QSwaggerActivityMaterials:
        return self.__materials


class QSwaggerBlueprintManufacturing(QSwaggerActivity):
    def __init__(self, time: int, product_type: QSwaggerTypeId, quantity: int):
        super().__init__(time)
        self.__product: QSwaggerProduct = QSwaggerProduct(product_type, quantity)

    def __del__(self):
        del self.__product

    @staticmethod
    def activity_id() -> int:
        return 1

    @property
    def product(self) -> QSwaggerProduct:
        return self.__product

    @property
    def product_type(self) -> QSwaggerTypeId:
        return self.__product.product_type

    @property
    def product_id(self) -> int:
        return self.__product.product_id

    @property
    def quantity(self) -> int:
        return self.__product.quantity


class QSwaggerBlueprintInvention(QSwaggerActivity):
    def __init__(self, time: int):
        super().__init__(time)
        self.__products: typing.List[QSwaggerInventionProduct] = []

    def __del__(self):
        self.__products.clear()
        del self.__products

    def add_product(self, product_type: QSwaggerTypeId, row) -> None:
        product_id: int = product_type.type_id
        if [1 for p in self.__products if p.product_id == product_id]:
            raise Exception("Unable to add invention product twice")
        product: QSwaggerInventionProduct = QSwaggerInventionProduct(product_type, row[4], row[5])
        self.__products.append(product)

    @staticmethod
    def activity_id() -> int:
        return 8

    @property
    def products(self) -> typing.List[QSwaggerInventionProduct]:
        return self.__products


class QSwaggerBlueprintCopying(QSwaggerActivity):
    def __init__(self, time: int, product_type: QSwaggerTypeId):
        super().__init__(time)
        self.__product: QSwaggerProduct = QSwaggerProduct(product_type, 1)

    def __del__(self):
        del self.__product

    @staticmethod
    def activity_id() -> int:
        return 5

    @property
    def product(self) -> QSwaggerProduct:
        return self.__product

    @property
    def product_type(self) -> QSwaggerTypeId:
        return self.__product.product_type

    @property
    def product_id(self) -> int:
        return self.__product.product_id


class QSwaggerBlueprintResearchMaterial(QSwaggerActivity):
    def __init__(self, time: int):
        super().__init__(time)

    def __del__(self):
        pass

    @staticmethod
    def activity_id() -> int:
        return 4


class QSwaggerBlueprintResearchTime(QSwaggerActivity):
    def __init__(self, time: int):
        super().__init__(time)

    def __del__(self):
        pass

    @staticmethod
    def activity_id() -> int:
        return 3


class QSwaggerBlueprintReaction(QSwaggerActivity):
    def __init__(self, time: int, product_type: QSwaggerTypeId, quantity: int):
        super().__init__(time)
        self.__product: QSwaggerProduct = QSwaggerProduct(product_type, quantity)

    def __del__(self):
        del self.__product

    @staticmethod
    def activity_id() -> int:
        return 9

    @property
    def product(self) -> QSwaggerProduct:
        return self.__product

    @property
    def product_type(self) -> QSwaggerTypeId:
        return self.__product.product_type

    @property
    def product_id(self) -> int:
        return self.__product.product_id

    @property
    def quantity(self) -> int:
        return self.__product.quantity


class QSwaggerBlueprint:
    def __init__(self, blueprint_type: QSwaggerTypeId):
        self.__blueprint_type: QSwaggerTypeId = blueprint_type
        self.__manufacturing: typing.Optional[QSwaggerBlueprintManufacturing] = None
        self.__invention: typing.Optional[QSwaggerBlueprintInvention] = None
        self.__copying: typing.Optional[QSwaggerBlueprintCopying] = None
        self.__research_material: typing.Optional[QSwaggerBlueprintResearchMaterial] = None
        self.__research_time: typing.Optional[QSwaggerBlueprintResearchTime] = None
        self.__reaction: typing.Optional[QSwaggerBlueprintReaction] = None

    def __del__(self):
        if self.__manufacturing is not None:
            del self.__manufacturing
        if self.__invention is not None:
            del self.__invention
        if self.__copying is not None:
            del self.__copying
        if self.__research_material is not None:
            del self.__research_material
        if self.__research_time is not None:
            del self.__research_time
        if self.__reaction is not None:
            del self.__reaction

    def add_activity(self, product_type: typing.Optional[QSwaggerTypeId], row) -> None:
        activity_id: int = row[1]
        time: int = row[2]
        if activity_id == 1:
            quantity: int = row[4]
            self.__manufacturing = QSwaggerBlueprintManufacturing(time, product_type, quantity)
        elif activity_id == 9:
            quantity: int = row[4]
            self.__reaction = QSwaggerBlueprintReaction(time, product_type, quantity)
        elif activity_id == 5:
            # продукт не всегда того же типа: копирка чертежа 33082 производит чертёж 33081
            self.__copying = QSwaggerBlueprintCopying(time, product_type)

    def add_activity_without_product(self, activity_id: int, time: int) -> None:
        if activity_id == 8:
            self.__invention = QSwaggerBlueprintInvention(time)  # продукты добавляются отдельным методом
        elif activity_id == 4:
            self.__research_material = QSwaggerBlueprintResearchMaterial(time)  # ...также не имеет продукта
        elif activity_id == 3:
            self.__research_time = QSwaggerBlueprintResearchTime(time)  # ...также не имеет продукта

    @property
    def type_id(self) -> int:
        return self.__blueprint_type.type_id

    @property
    def blueprint_type(self) -> QSwaggerTypeId:
        return self.__blueprint_type

    @property
    def manufacturing(self) -> QSwaggerBlueprintManufacturing:
        return self.__manufacturing

    @property
    def invention(self) -> QSwaggerBlueprintInvention:
        return self.__invention

    @property
    def copying(self) -> QSwaggerBlueprintCopying:
        return self.__copying

    @property
    def research_material(self) -> QSwaggerBlueprintResearchMaterial:
        return self.__research_material

    @property
    def research_time(self) -> QSwaggerBlueprintResearchTime:
        return self.__research_time

    @property
    def reaction(self) -> QSwaggerBlueprintReaction:
        return self.__reaction

    def get_activity(self, activity_id: int) -> typing.Union[QSwaggerBlueprintManufacturing, QSwaggerBlueprintInvention,
                                                             QSwaggerBlueprintCopying, QSwaggerBlueprintResearchMaterial,
                                                             QSwaggerBlueprintResearchTime, QSwaggerBlueprintReaction]:
        if activity_id == 1:
            return self.__manufacturing
        elif activity_id == 8:
            return self.__invention
        elif activity_id == 5:
            return self.__copying
        elif activity_id == 4:
            return self.__research_material
        elif activity_id == 3:
            return self.__research_time
        elif activity_id == 9:
            return self.__reaction
        else:
            raise Exception("Impossible to get an activity #{}".format(activity_id))


class QSwaggerCharacter:
    def __init__(self, character_id: int, character_name: str):
        self.__character_id: int = character_id
        self.__character_name: str = character_name

    @property
    def character_id(self) -> int:
        return self.__character_id

    @property
    def character_name(self) -> str:
        return self.__character_name


class QSwaggerStation:
    def __init__(
            self,
            station_id: int,
            station_name: str,
            solar_system_id: int,
            solar_system_name: str,
            station_type: QSwaggerTypeId,
            station_type_name: str):
        self.__station_id: int = station_id
        self.__station_name: str = station_name
        self.__solar_system_id: int = solar_system_id
        self.__solar_system_name: str = solar_system_name
        self.__station_type: QSwaggerTypeId = station_type
        self.__station_type_name: str = station_type_name

    @property
    def station_id(self) -> int:
        return self.__station_id

    @property
    def station_name(self) -> str:
        return self.__station_name

    @property
    def solar_system_id(self) -> int:
        return self.__solar_system_id

    @property
    def solar_system_name(self) -> str:
        return self.__solar_system_name

    @property
    def station_type(self) -> QSwaggerTypeId:
        return self.__station_type

    @property
    def station_type_name(self) -> str:
        return self.__station_type_name


class QSwaggerCorporationAssetsItem:
    def __init__(self, item_type: QSwaggerTypeId, row):
        self.__item_id: int = row[0]
        self.__type_id: int = row[1]
        self.__item_type: QSwaggerTypeId = item_type  # None, если данные о типе предмета недоступны (пока)
        self.__quantity: int = row[2]
        self.__location_id: int = row[3]
        self.__location_type: str = row[4]
        self.__location_flag: str = row[5]
        self.__is_singleton: bool = row[6]
        self.__name: typing.Optional[str] = row[7]
        self.__updated_at: datetime.datetime = row[8]
        self.__station_id: typing.Optional[int] = None

    @property
    def item_id(self) -> int:
        return self.__item_id

    @property
    def type_id(self) -> int:  # безопасный метод получения type_id (известен, даже когда неизвестен item_type)
        return self.__type_id

    @property
    def item_type(self) -> QSwaggerTypeId:
        return self.__item_type

    @property
    def quantity(self) -> int:
        return self.__quantity

    @property
    def location_id(self) -> int:
        return self.__location_id

    @property
    def location_type(self) -> str:
        return self.__location_type

    @property
    def location_flag(self) -> str:
        return self.__location_flag

    @property
    def is_singleton(self) -> bool:
        return self.__is_singleton

    @property
    def name(self) -> typing.Optional[str]:
        return self.__name

    @property
    def updated_at(self) -> datetime.datetime:
        return self.__updated_at

    @property
    def station_id(self) -> typing.Optional[int]:
        return self.__station_id

    def set_station_id(self, station_id: int) -> None:
        self.__station_id = station_id


class QSwaggerCorporationBlueprint:
    def __init__(self, blueprint_type: QSwaggerBlueprint, row):
        self.__item_id: int = row[0]
        self.__type_id: int = row[1]
        self.__blueprint_type: QSwaggerBlueprint = blueprint_type  # None, если данные о типе предмета недоступны (пока)
        self.__location_id: int = row[2]
        self.__location_flag: str = row[3]
        self.__quantity: int = row[4]
        self.__time_efficiency: int = row[5]
        self.__material_efficiency: int = row[6]
        self.__runs: int = row[7]
        self.__updated_at: datetime.datetime = row[8]
        self.__station_id: typing.Optional[int] = None

    @property
    def item_id(self) -> int:
        return self.__item_id

    @property
    def type_id(self) -> int:  # безопасный метод получения type_id (известен, даже когда неизвестен blueprint_type)
        return self.__type_id

    @property
    def blueprint_type(self) -> QSwaggerBlueprint:
        return self.__blueprint_type

    @property
    def location_id(self) -> int:
        return self.__location_id

    @property
    def location_flag(self) -> str:
        return self.__location_flag

    @property
    def quantity(self) -> int:
        return self.__quantity

    @property
    def time_efficiency(self) -> int:
        return self.__time_efficiency

    @property
    def material_efficiency(self) -> int:
        return self.__material_efficiency

    @property
    def runs(self) -> int:
        return self.__runs

    @property
    def updated_at(self) -> datetime.datetime:
        return self.__updated_at

    @property
    def station_id(self) -> typing.Optional[int]:
        return self.__station_id

    def set_station_id(self, station_id: int) -> None:
        self.__station_id = station_id


class QSwaggerCorporationIndustryJob:
    def __init__(self,
                 blueprint: typing.Optional[QSwaggerCorporationBlueprint],
                 blueprint_type: typing.Optional[QSwaggerBlueprint],
                 product_type: typing.Optional[QSwaggerTypeId],
                 installer: typing.Optional[QSwaggerCharacter],
                 blueprint_location: typing.Optional[QSwaggerCorporationAssetsItem],
                 output_location: typing.Optional[QSwaggerCorporationAssetsItem],
                 facility: typing.Optional[QSwaggerStation],
                 row):
        self.__job_id: int = row[0]
        self.__installer_id: int = row[1]
        self.__installer: typing.Optional[QSwaggerCharacter] = installer
        self.__facility_id: int = row[2]
        self.__facility: typing.Optional[QSwaggerStation] = facility
        # self.__location_id: int = row[?] # бесполезно, аналогично facility_id
        self.__activity_id: int = row[3]
        self.__blueprint_id: int = row[4]
        self.__blueprint: typing.Optional[QSwaggerCorporationBlueprint] = blueprint
        self.__blueprint_type_id: int = row[5]
        self.__blueprint_type: typing.Optional[QSwaggerBlueprint] = blueprint_type
        self.__blueprint_location_id: int = row[6]  # коробка, где находится чертёж
        self.__blueprint_location: typing.Optional[QSwaggerCorporationAssetsItem] = blueprint_location
        self.__output_location_id: int = row[7]  # коробка, куда будет помещён продукт
        self.__output_location: typing.Optional[QSwaggerCorporationAssetsItem] = output_location
        self.__runs: int = row[8]
        self.__cost: float = row[9]
        self.__licensed_runs: int = row[10]
        self.__probability: float = row[11]
        self.__product_type_id: int = row[12]
        self.__product_type: typing.Optional[QSwaggerTypeId] = product_type
        self.__end_date: datetime.datetime = row[13]

    @property
    def job_id(self) -> int:
        return self.__job_id

    @property
    def installer_id(self) -> int:
        return self.__installer_id

    @property
    def installer(self) -> typing.Optional[QSwaggerCharacter]:
        return self.__installer

    @property
    def facility_id(self) -> int:
        return self.__facility_id

    @property
    def facility(self) -> typing.Optional[QSwaggerStation]:
        return self.__facility

    @property
    def activity_id(self) -> int:
        return self.__activity_id

    @property
    def blueprint_id(self) -> int:
        return self.__blueprint_id

    @property
    def blueprint(self) -> typing.Optional[QSwaggerCorporationBlueprint]:
        return self.__blueprint

    @property
    def blueprint_type_id(self) -> int:
        return self.__blueprint_type_id

    @property
    def blueprint_type(self) -> typing.Optional[QSwaggerBlueprint]:
        return self.__blueprint_type

    @property
    def blueprint_location_id(self) -> int:
        return self.__blueprint_location_id

    @property
    def blueprint_location(self) -> typing.Optional[QSwaggerCorporationAssetsItem]:
        return self.__blueprint_location

    @property
    def output_location_id(self) -> int:
        return self.__output_location_id

    @property
    def output_location(self) -> typing.Optional[QSwaggerCorporationAssetsItem]:
        return self.__output_location

    @property
    def runs(self) -> int:
        return self.__runs

    @property
    def cost(self) -> float:
        return self.__cost

    @property
    def licensed_runs(self) -> int:
        return self.__licensed_runs

    @property
    def probability(self) -> float:
        return self.__probability

    @property
    def product_type_id(self) -> int:
        return self.__product_type_id

    @property
    def product_type(self) -> typing.Optional[QSwaggerTypeId]:
        return self.__product_type

    @property
    def end_date(self) -> datetime.datetime:
        return self.__end_date


class QSwaggerCorporation:
    def __init__(self, corporation_id: int, corporation_name: str):
        # идентификаторы
        self.__corporation_id = corporation_id
        self.__corporation_name = corporation_name
        # наборы данных (взаимосвязаны друг с другом, ВАЖЕН ПОРЯДОК уничтожения!)
        self.assets: typing.Dict[int, QSwaggerCorporationAssetsItem] = {}
        self.blueprints: typing.Dict[int, QSwaggerCorporationBlueprint] = {}
        self.industry_jobs: typing.Dict[int, QSwaggerCorporationIndustryJob] = {}
        # идентификаторы корпоративных контейнеров
        self.container_ids: typing.List[int] = []

    def __del__(self):
        # идентификаторы корпоративных контейнеров
        del self.container_ids
        # наборы данных (взаимосвязаны друг с другом, ВАЖЕН ПОРЯДОК уничтожения!)
        del self.industry_jobs
        del self.blueprints
        del self.assets

    @property
    def corporation_id(self) -> int:
        return self.__corporation_id

    @property
    def corporation_name(self) -> str:
        return self.__corporation_name
