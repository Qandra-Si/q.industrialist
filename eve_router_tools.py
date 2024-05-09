""" Router and Conveyor tools and utils
"""
import typing
from enum import Enum

import eve_efficiency
import postgresql_interface as db


class RouterSettings:
    def __init__(self):
        # параметры работы конвейера
        self.station: str = ''
        self.desc: str = ''
        self.output: typing.List[int] = []


class ConveyorSettings: pass  # forward declaration


class ConveyorSettingsContainer:
    def __init__(self,
                 settings: ConveyorSettings,
                 corporation: db.QSwaggerCorporation,
                 container: db.QSwaggerCorporationAssetsItem):
        self.settings: ConveyorSettings = settings
        self.corporation: db.QSwaggerCorporation = corporation
        self.container: db.QSwaggerCorporationAssetsItem = container
        self.station_id: typing.Optional[int] = container.station_id

    @property
    def container_id(self) -> int:
        return self.container.item_id

    @property
    def container_name(self) -> str:
        return self.container.name


class ConveyorSettingsPriorityContainer(ConveyorSettingsContainer):
    def __init__(self,
                 priority: int,
                 settings: ConveyorSettings,
                 corporation: db.QSwaggerCorporation,
                 container: db.QSwaggerCorporationAssetsItem):
        super().__init__(settings, corporation, container)
        self.priority: int = priority


class ConveyorSettingsSaleContainer(ConveyorSettingsContainer):
    def __init__(self,
                 settings: ConveyorSettings,
                 trade_corporation: db.QSwaggerCorporation,
                 container: db.QSwaggerCorporationAssetsItem):
        super().__init__(settings, trade_corporation, container)
        self.trade_corporation: db.QSwaggerCorporation = trade_corporation


class ConveyorActivity(Enum):
    CONVEYOR_MANUFACTURING = 1
    CONVEYOR_INVENTION = 8
    CONVEYOR_COPYING = 5
    CONVEYOR_RESEARCH_MATERIAL = 4
    CONVEYOR_RESEARCH_TIME = 3
    CONVEYOR_REACTION = 9

    def __str__(self) -> str:
        if self == ConveyorActivity.CONVEYOR_MANUFACTURING:
            return 'manufacturing'
        elif self == ConveyorActivity.CONVEYOR_INVENTION:
            return 'invention'
        elif self == ConveyorActivity.CONVEYOR_COPYING:
            return 'copying'
        elif self == ConveyorActivity.CONVEYOR_RESEARCH_MATERIAL:
            return 'research_material'
        elif self == ConveyorActivity.CONVEYOR_RESEARCH_TIME:
            return 'research_time'
        elif self == ConveyorActivity.CONVEYOR_REACTION:
            return 'reaction'
        else:
            raise Exception('Unknown conveyor activity')

    def to_int(self) -> int:
        return int(self.value)

    @staticmethod
    def from_str(label):
        if label == 'manufacturing':
            return ConveyorActivity.CONVEYOR_MANUFACTURING
        elif label == 'invention':
            return ConveyorActivity.CONVEYOR_INVENTION
        elif label == 'copying':
            return ConveyorActivity.CONVEYOR_COPYING
        elif label == 'research_material':
            return ConveyorActivity.CONVEYOR_RESEARCH_MATERIAL
        elif label == 'research_time':
            return ConveyorActivity.CONVEYOR_RESEARCH_TIME
        elif label == 'reaction':
            return ConveyorActivity.CONVEYOR_REACTION
        else:
            raise Exception('Unknown conveyor activity label')


class ConveyorSettings:
    def __init__(self, corporation: db.QSwaggerCorporation):
        # параметры работы конвейера
        self.corporation: db.QSwaggerCorporation = corporation
        self.fixed_number_of_runs: typing.Optional[int] = None
        self.same_stock_container: bool = False
        self.activities: typing.List[ConveyorActivity] = [ConveyorActivity.CONVEYOR_MANUFACTURING]
        self.conveyor_with_reactions: bool = False
        # идентификаторы контейнеров с чертежами, со стоком, с формулами, исключённых из поиска и т.п.
        self.containers_sources: typing.List[ConveyorSettingsPriorityContainer] = []  # station:container:priority
        self.containers_stocks: typing.List[ConveyorSettingsContainer] = []  # station:container
        self.containers_additional_blueprints: typing.List[ConveyorSettingsContainer] = []  # station:container
        self.containers_react_formulas: typing.List[int] = []
        self.containers_react_stock: typing.List[int] = []
        self.manufacturing_groups: typing.Optional[typing.List[int]] = []
        # параметры поведения конвейера (связь с торговой деятельностью, влияние её поведения на работу произвдства)
        self.trade_sale_stock: typing.List[ConveyorSettingsSaleContainer] = []  # station:container:trade_corporation


def get_blueprints_grouped_by(
        blueprints: typing.List[db.QSwaggerCorporationBlueprint],
        group_by_type_id: bool = True,
        group_by_me: bool = True,
        group_by_te: bool = False,
        group_by_runs: bool = True) \
        -> typing.Dict[typing.Tuple[int, int, int, int], typing.List[db.QSwaggerCorporationBlueprint]]:
    grouped: typing.Dict[typing.Tuple[int, int, int, int], typing.List[db.QSwaggerCorporationBlueprint]] = {}
    for b in blueprints:
        type_id: int = b.type_id if group_by_type_id else 0
        me: int = b.material_efficiency if group_by_me else -1
        te: int = b.time_efficiency if group_by_te else -1
        runs: int = b.runs if group_by_runs else -10
        key: typing.Tuple[int, int, int, int] = type_id, me, te, runs
        g0: typing.List[db.QSwaggerCorporationBlueprint] = grouped.get(key)
        if not g0:
            grouped[key] = []
            g0 = grouped.get(key)
        g0.append(b)
    return grouped


def get_jobs_grouped_by(
        jobs: typing.List[db.QSwaggerCorporationIndustryJob],
        group_by_product: bool = True,
        group_by_activity: bool = False) \
        -> typing.Dict[typing.Tuple[int, int], typing.List[db.QSwaggerCorporationIndustryJob]]:
    grouped: typing.Dict[typing.Tuple[int, int], typing.List[db.QSwaggerCorporationIndustryJob]] = {}
    for j in jobs:
        product_type_id: int = j.product_type_id if group_by_product else 0
        activity: int = j.activity_id if group_by_activity else 0
        key: typing.Tuple[int, int] = product_type_id, activity
        g0: typing.List[db.QSwaggerCorporationIndustryJob] = grouped.get(key)
        if not g0:
            grouped[key] = []
            g0 = grouped.get(key)
        g0.append(j)
    return grouped


def get_product_quantity(
        activity_id: int,
        product_type_id: int,
        blueprint: db.QSwaggerBlueprint) -> int:
    activity = blueprint.get_activity(activity_id=activity_id)
    if ConveyorActivity.CONVEYOR_MANUFACTURING.to_int() == activity_id:
        manufacturing: db.QSwaggerBlueprintManufacturing = activity
        return manufacturing.quantity
    elif ConveyorActivity.CONVEYOR_INVENTION.to_int() == activity_id:
        invention: db.QSwaggerBlueprintInvention = activity
        return next((p.quantity for p in invention.products if p.product_id == product_type_id), 1)
    elif ConveyorActivity.CONVEYOR_COPYING.to_int() == activity_id:
        return 1  # copying: db.QSwaggerBlueprintCopying = activity
    elif ConveyorActivity.CONVEYOR_RESEARCH_MATERIAL.to_int() == activity_id:
        return 1  # research_material: db.QSwaggerBlueprintResearchMaterial = activity
    elif ConveyorActivity.CONVEYOR_RESEARCH_TIME.to_int() == activity_id:
        return 1  # research_time: db.QSwaggerBlueprintResearchTime = activity
    elif ConveyorActivity.CONVEYOR_REACTION.to_int() == activity_id:
        reaction: db.QSwaggerBlueprintReaction = activity
        return reaction.quantity


# blueprints_details: подробности о чертежах этого типа [{"q": -1, "r": -1}, {"q": 2, "r": -1}, {"q": -2, "r": 179}]
# метод возвращает список tuple: [{"id": 11399, "q": 11, "qmin": 11"}] с учётом ME
# при is_blueprint_copy=True tuple={"r":?}, при False tuple={"r":?,"q":?}
# fixed_number_of_runs учитывается только для оригиналов, т.е. для is_blueprint_copy=False
def get_materials_list(
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        # настройки генерации отчёта
        conveyor_settings: ConveyorSettings,
        # список чертежей для которых необходимо рассчитать потребность в материалах
        blueprints: typing.List[db.QSwaggerCorporationBlueprint],
        fixed_number_of_runs: typing.Optional[int] = None) -> typing.List[db.QSwaggerMaterial]:
    # список материалов по набору чертежей с учётом ME
    materials_list_with_efficiency: typing.Dict[int, db.QSwaggerMaterial] = {}
    # перебираем все активности и все чертежи
    for a in conveyor_settings.activities:
        for b in blueprints:
            activity = b.blueprint_type.get_activity(activity_id=a.to_int())
            if not activity: continue
            # получаем справочную информацию по этому типу чертежа для выбранной активности
            materials: db.QSwaggerActivityMaterials = activity.materials
            if not materials: continue
            # расчёт кол-ва ранов для этого чертежа
            if b.is_copy:
                quantity_of_runs = b.runs
                quantity_of_blueprints = 1
            else:
                quantity_of_blueprints = b.quantity if b.quantity > 0 else 1
                quantity_of_runs = fixed_number_of_runs if fixed_number_of_runs else 1
                # умножение на количество оригиналов будет выполнено позже...
            # перебираем все материалы и считаем кол-во с учётом me
            for m in materials.materials:
                # расчёт кол-ва материала с учётом эффективности производства
                industry_input = eve_efficiency.get_industry_material_efficiency(
                    str(a),
                    quantity_of_runs,
                    m.quantity,  # сведения из чертежа
                    b.material_efficiency)  # сведения из корпоративного чертежа
                # выход готовой продукции с одного запуска по N ранов умножаем на кол-во чертежей
                industry_input *= quantity_of_blueprints
                # ---
                in_cache: db.QSwaggerMaterial = materials_list_with_efficiency.get(m.material_id)
                if not in_cache:
                    materials_list_with_efficiency[m.material_id] = db.QSwaggerMaterial(m.material_type, industry_input)
                else:
                    in_cache.increment_quantity(industry_input)
            # ---
            if a == ConveyorActivity.CONVEYOR_INVENTION:
                # Добавляем декрипторы (замечения и ограничения):
                # - всегда все хулы запускаются с декриптором Accelerant Decryptor
                # - всегда все риги запускаются с декриптором Symmetry Decryptor
                # - всегда все T3 технологии запускаются с декриптором Parity Decryptor
                # - всегда все модули запускаются без декрипторов
                # - для запуска модулей скилы должны быть не меньше 2х, для запуска хулов и риг скилы должны быть
                # в 3 и выше. Если ваши скилы меньше - лучше запускайте ресерч или ждите задач по копирке. Будьте
                # внимательны, игнорируя эти замечения вы сильно усложняете работу производственников.
                invention: db.QSwaggerBlueprintInvention = activity
                # считаем, что какие бы варианты чертежей не инвентились, все они будут одного типа
                product_blueprint_id: int = invention.products[0].product_id
                product_blueprint_type: db.QSwaggerBlueprint = qid.get_blueprint(product_blueprint_id)
                if product_blueprint_type and product_blueprint_type.manufacturing:
                    market_group_id: int = product_blueprint_type.manufacturing.product_type.market_group_id
                    decryptor_type: typing.Optional[db.QSwaggerTypeId] = None
                    while market_group_id is not None:
                        if market_group_id == 204:  # Ships
                            decryptor_type = qid.get_type_id(34201)  # Accelerant Decryptor
                        elif market_group_id == 943:  # Ship Modifications
                            decryptor_type = qid.get_type_id(34206)  # Symmetry Decryptor
                        elif market_group_id == 1909:  # Ancient Relics
                            decryptor_type = qid.get_type_id(34204)  # Parity Decryptor
                        if decryptor_type: break
                        market_group: db.QSwaggerMarketGroup = qid.get_market_group(market_group_id)
                        if not market_group: break
                        market_group_id = market_group.parent_id
                    # расчёт кол-ва декрипторов с учётом эффективности производства
                    if decryptor_type:
                        industry_input = eve_efficiency.get_industry_material_efficiency(
                            str(a),
                            quantity_of_runs,
                            1,  # всегда один декриптор
                            b.material_efficiency)  # сведения из корпоративного чертежа
                        # выход готовой продукции с одного запуска по N ранов умножаем на кол-во чертежей
                        industry_input *= quantity_of_blueprints
                        # ---
                        in_cache: db.QSwaggerMaterial = materials_list_with_efficiency.get(decryptor_type.type_id)
                        if not in_cache:
                            materials_list_with_efficiency[decryptor_type.type_id] = db.QSwaggerMaterial(decryptor_type, industry_input)
                        else:
                            in_cache.increment_quantity(industry_input)
    return [m for m in materials_list_with_efficiency.values()]
