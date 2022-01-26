# -*- encoding: utf-8 -*-
import typing
import datetime

from .db_interface import QIndustrialistDatabase


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
        self.__icon_id: typing.Optional[int] = row[7]
        self.__packaged_volume: typing.Optional[float] = row[8]

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
    def time(self) -> int:
        return self.__time

    @property
    def products(self) -> typing.List[QSwaggerInventionProduct]:
        return self.__products


class QSwaggerBlueprintCopying(QSwaggerActivity):
    def __init__(self, time: int):
        super().__init__(time)

    def __del__(self):
        pass

    @staticmethod
    def activity_id() -> int:
        return 5


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

    def add_activity_without_product(self, activity_id: int, time: int) -> None:
        if activity_id == 8:
            self.__invention = QSwaggerBlueprintInvention(time)  # продукты добавляются отдельным методом
        elif activity_id == 5:
            self.__copying = QSwaggerBlueprintCopying(time)  # не имеет продукта (продукт того же типа)...
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


class QSwaggerTranslator:
    def __init__(self, db: QIndustrialistDatabase):
        """ constructor

        :param db: instance of QIndustrialistDatabase
        """
        self.db = db

    def __del__(self):
        """ destructor
        """
        del self.db

    # -------------------------------------------------------------------------
    # /market/groups/
    # /market/groups/{market_group_id}/
    # -------------------------------------------------------------------------

    def get_market_groups(self) -> typing.Dict[int, QSwaggerMarketGroup]:
        rows = self.db.select_all_rows(
            "SELECT"
            " sdeg_group_id,"
            " sdeg_parent_id,"
            " sdeg_semantic_id,"
            " sdeg_group_name,"
            " sdeg_icon_id "
            "FROM eve_sde_market_groups;"
        )
        if rows is None:
            return {}
        data = {}
        for row in rows:
            group_id: int = row[0]
            data[group_id] = QSwaggerMarketGroup(row)
        del rows
        return data

    # -------------------------------------------------------------------------
    # /universe/types/
    # /universe/types/{type_id}/
    # -------------------------------------------------------------------------

    def get_published_type_ids(self) -> typing.Dict[int, QSwaggerTypeId]:
        rows = self.db.select_all_rows(
            "SELECT"
            " sdet_type_id,"
            " sdet_type_name,"
            " sdet_volume,"
            " sdet_capacity,"
            " sdet_base_price,"
            " sdet_market_group_id,"
            " sdet_meta_group_id,"
            " sdet_icon_id,"
            " sdet_packaged_volume "
            "FROM eve_sde_type_ids "
            "WHERE sdet_published;"
        )
        if rows is None:
            return {}
        data = {}
        for row in rows:
            type_id: int = row[0]
            data[type_id] = QSwaggerTypeId(row)
        del rows
        return data

    # -------------------------------------------------------------------------
    # blueprints.yaml from https://developers.eveonline.com/resource/resources
    # -------------------------------------------------------------------------

    def get_blueprints(self, type_ids: typing.Dict[int, QSwaggerTypeId]) -> typing.Dict[int, QSwaggerBlueprint]:
        rows = self.db.select_all_rows(  # 15088 записей
            "SELECT"
            " blueprint_type_id,"
            " activity_id,"
            " time,"
            " product_type_id,"
            " quantity,"
            " probability "
            "FROM eve_sde_workable_blueprints;"
        )
        if rows is None:
            return {}
        data = {}
        # добавление чертежей в справочник, проверка входных данных на исключения... у CCP надо быть "готовым ко всему",
        # так как есть, например published manufacturing-чертежи у которых нет производимого продукта:
        # - 27015 Civilian Data Analyzer Blueprint (Civilian Data Analyzer не published)
        # - 2211  Sansha Juggernaut Torpedo Blueprint (Banshee Torpedo не published)
        # - 2179  Sansha Wrath Cruise Missile Blueprint (Haunter Cruise Missile не published)
        # и published чертёж, с которым можно выполнять invent-ы, и у которого нет продукта:
        # - 36949 Coalesced Element Blueprint (в sde есть invention-активность с time=0)
        #
        # и published чертёж, с которым можно выполнять научку и копирку:
        # - 36949 Coalesced Element Blueprint (в sde есть копирка с научкой c time=0)
        # - 41536 Zeugma Integrated Analyzer Blueprint (в sde есть копирка с научкой c time=0)
        for row in rows:
            type_id: int = row[0]
            # у некоторых чертежей есть несколько activity
            blueprint: QSwaggerBlueprint = data.get(type_id)
            if blueprint is None:
                cached_blueprint_type: QSwaggerTypeId = type_ids.get(type_id)
                if cached_blueprint_type is None:
                    raise Exception("Unable to add unknown blueprint #{}".format(type_id))
                blueprint: QSwaggerBlueprint = QSwaggerBlueprint(cached_blueprint_type)
                data[type_id] = blueprint
            # у invention activity может быть несколько products, остальные продукты связаны отношением 1:1
            activity_id: int = row[1]
            product_id = row[3]
            if activity_id == 1:
                if blueprint.manufacturing is not None:
                    raise Exception("Unable to add manufacturing activity twice: blueprint #{}".format(type_id))
                if product_id is None:
                    continue
                cached_product_type: QSwaggerTypeId = type_ids.get(product_id)
                if cached_product_type is None:
                    raise Exception("Unable to add manufacturing activity with unknown product #{}".format(product_id))
                blueprint.add_activity(cached_product_type, row)
            elif activity_id == 8:
                if blueprint.invention is None:
                    blueprint.add_activity_without_product(activity_id, row[2])
                if product_id is None:
                    continue
                cached_product_type: QSwaggerTypeId = type_ids.get(product_id)
                if cached_product_type is None:
                    raise Exception("Unable to add invention activity with unknown product #{}".format(product_id))
                blueprint.invention.add_product(cached_product_type, row)
            elif activity_id == 5:
                if blueprint.copying is not None:
                    raise Exception("Unable to add copying activity twice: blueprint #{}".format(type_id))
                elif product_id is not None:
                    raise Exception("Unable to add copying, product must be unknown: blueprint #{}".format(type_id))
                blueprint.add_activity_without_product(activity_id, row[2])
            elif activity_id == 4:
                if blueprint.research_material is not None:
                    raise Exception("Unable to add research material activity twice: blueprint #{}".format(type_id))
                elif product_id is not None:
                    raise Exception("Unable to add research material, product must be unknown: blueprint #{}".format(type_id))
                blueprint.add_activity_without_product(activity_id, row[2])
            elif activity_id == 3:
                if blueprint.research_time is not None:
                    raise Exception("Unable to add research time activity twice: blueprint #{}".format(type_id))
                elif product_id is not None:
                    raise Exception("Unable to add research time activity, product must be unknown: blueprint #{}".format(type_id))
                blueprint.add_activity_without_product(activity_id, row[2])
            elif activity_id == 9:
                if blueprint.reaction is not None:
                    raise Exception("Unable to add reaction activity twice: blueprint #{}".format(type_id))
                if product_id is None:
                    continue
                cached_product_type: QSwaggerTypeId = type_ids.get(product_id)
                if cached_product_type is None:
                    raise Exception(
                        "Unable to add reaction activity with unknown product #{}".format(product_id))
                blueprint.add_activity(cached_product_type, row)
        del rows
        # ---
        rows = self.db.select_all_rows(
            "SELECT"
            " blueprint_type_id,"
            " activity_id,"
            " material_type_id,"
            " quantity "
            "FROM eve_sde_available_blueprint_materials "
            "ORDER BY 1,2,4 desc;"
        )
        if rows is None:
            return data
        blueprint: QSwaggerBlueprint = None  # noqa
        activity: typing.Union[QSwaggerBlueprintManufacturing, QSwaggerBlueprintInvention,
                               QSwaggerBlueprintCopying, QSwaggerBlueprintResearchMaterial,
                               QSwaggerBlueprintResearchTime, QSwaggerBlueprintReaction] = None  # noqa
        prev_blueprint_type_id: int = -1
        prev_activity_id: int = -1
        for row in rows:
            # используем факт того, что набор данных отсортирован и прореживаем ненужный поиск одних и тех же чертежей
            blueprint_type_id: int = row[0]
            if blueprint_type_id != prev_blueprint_type_id:
                prev_blueprint_type_id = blueprint_type_id
                blueprint = data.get(blueprint_type_id)
                # возможная ситуация, что такого чертежа нет - тогда это ошибка
                if blueprint is None:
                    raise Exception("Unable to add material into blueprint #{} activity #{}".format(blueprint_type_id, activity_id))
                prev_activity_id = -1
            # используем факт того, что набор данных отсортирован и прореживаем ненужный поиск одних и тех же activity
            activity_id: int = row[1]
            if activity_id != prev_activity_id:
                prev_activity_id = activity_id
                activity = blueprint.get_activity(activity_id)
            # возможная ситуация, что чертёж есть, а активность выше не добавлена, т.к. продукт non published:
            # - 2179  Sansha Wrath Cruise Missile Blueprint (Haunter Cruise Missile не published)
            if activity is None:
                continue
            # нужная activity найдена, добавляем материалы
            material_id: int = row[2]
            material_type: QSwaggerTypeId = type_ids.get(material_id)
            if material_type is None:
                raise Exception("Unable to add material #{} into blueprint #{} activity #{}".format(material_id, blueprint_type_id, activity_id))
            activity.materials.add_material(material_type, row[3])
        return data

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/
    # -------------------------------------------------------------------------
    def get_corporation_id(self, corporation_name: str) -> typing.Optional[int]:
        row = self.db.select_one_row(
            "SELECT eco_corporation_id FROM esi_corporations WHERE eco_name=%s;",
            corporation_name
        )
        if row is None:
            return None
        return row[0]

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/assets/
    # -------------------------------------------------------------------------

    def get_corporation_assets(
            self,
            corporation_id: int,
            type_ids: typing.Dict[int, QSwaggerTypeId],
            load_unknown_type_assets: bool = False,
            load_asseted_blueprints: bool = False) -> typing.Dict[int, QSwaggerCorporationAssetsItem]:
        # ассеты могут содержать например 26420 предметов, тогда как чертежей в них будет 23289 шт
        filter_blueprints: str = ''
        if not load_asseted_blueprints:
            filter_blueprints = \
                "INNER JOIN eve_sde_type_ids ON (sdet_type_id=eca_type_id) " \
                "INNER JOIN eve_sde_group_ids ON (sdet_group_id=sdecg_group_id AND sdecg_category_id!=9) "
        rows = self.db.select_all_rows(
            "SELECT"
            " eca_item_id,"
            " eca_type_id,"
            " eca_quantity,"
            " eca_location_id,"
            " eca_location_type,"
            " eca_location_flag,"
            " eca_is_singleton,"
            " eca_name,"
            " eca_updated_at "
            "FROM esi_corporation_assets "
            + filter_blueprints +
            "WHERE eca_corporation_id=%s;",
            corporation_id,
        )
        if rows is None:
            return {}
        data = {}
        for row in rows:
            item_id: int = row[0]
            type_id: int = row[1]
            cached_item_type: QSwaggerTypeId = type_ids.get(type_id)
            if cached_item_type is None and not load_unknown_type_assets:
                continue
            data[item_id] = QSwaggerCorporationAssetsItem(cached_item_type, row)
        del rows
        return data

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/blueprints/
    # -------------------------------------------------------------------------

    def get_corporation_blueprints(
            self,
            corporation_id: int,
            blueprints: typing.Dict[int, QSwaggerBlueprint],
            load_unknown_type_blueprints: bool = False) -> typing.Dict[int, QSwaggerCorporationBlueprint]:
        rows = self.db.select_all_rows(
            "SELECT"
            " ecb_item_id,"
            " ecb_type_id,"
            " ecb_location_id,"
            " ecb_location_flag,"
            " ecb_quantity,"
            " ecb_time_efficiency,"
            " ecb_material_efficiency,"
            " ecb_runs,"
            " ecb_updated_at "
            "FROM esi_corporation_blueprints "
            "WHERE ecb_corporation_id=%s;",
            corporation_id,
        )
        if rows is None:
            return {}
        data = {}
        for row in rows:
            item_id: int = row[0]
            type_id: int = row[1]
            cached_blueprint_type: QSwaggerBlueprint = blueprints.get(type_id)
            if cached_blueprint_type is None and not load_unknown_type_blueprints:
                continue
            data[item_id] = QSwaggerCorporationBlueprint(cached_blueprint_type, row)
        del rows
        return data
