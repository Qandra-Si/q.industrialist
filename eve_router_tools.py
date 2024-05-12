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
        # список type_id продуктов текущего router-а
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
        group_by_station: bool = True,
        group_by_me: bool = True,
        group_by_te: bool = False,
        group_by_runs: bool = True) \
        -> typing.Dict[typing.Tuple[int, int, int, int, int], typing.List[db.QSwaggerCorporationBlueprint]]:
    grouped: typing.Dict[typing.Tuple[int, int, int, int, int], typing.List[db.QSwaggerCorporationBlueprint]] = {}
    for b in blueprints:
        type_id: int = b.type_id if group_by_type_id else 0
        station_id: int = b.station_id if group_by_station else 0
        me: int = b.material_efficiency if group_by_me else -1
        te: int = b.time_efficiency if group_by_te else -1
        runs: int = b.runs if group_by_runs else -10
        key: typing.Tuple[int, int, int, int, int] = type_id, station_id, me, te, runs
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
        fixed_number_of_runs: typing.Optional[int] = None) \
        -> typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerMaterial]]:
    # список материалов по набору чертежей с учётом ME
    materials_list_with_efficiency: typing.Dict[db.QSwaggerActivity, typing.Dict[int, db.QSwaggerMaterial]] = {}

    def push_into(__a: db.QSwaggerActivity, __m: db.QSwaggerMaterial, __q: int) -> None:
        __in_cache205: typing.Dict[int, db.QSwaggerMaterial] = materials_list_with_efficiency.get(__a)
        if not __in_cache205:
            materials_list_with_efficiency[__a] = {}
            __in_cache205 = materials_list_with_efficiency.get(__a)
        __in_cache209: db.QSwaggerMaterial = __in_cache205.get(__m.material_id)
        if not __in_cache209:
            __in_cache205[__m.material_id] = db.QSwaggerMaterial(__m.material_type, __q)
        else:
            __in_cache209.increment_quantity(__q)

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
                # сохранение информации в справочник материалов
                push_into(activity, m, industry_input)
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
                        # сохранение информации в справочник материалов
                        push_into(activity, db.QSwaggerMaterial(decryptor_type, 0), industry_input)
    # ---
    result: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerMaterial]] = {}
    for activity in materials_list_with_efficiency.keys():
        mm: typing.Dict[int, db.QSwaggerMaterial] = materials_list_with_efficiency.get(activity)
        result[activity] = [m for m in mm.values()]
    return result


class ConveyorCorporationStockMaterials:
    def __init__(self):
        # материалы сгруппированы по станциям, т.е. чтобы получить информацию об имеющемся кол-ве материалов, надо
        # знать идентификатор станции
        self.stock_materials: typing.Dict[int, typing.Dict[int, db.QSwaggerMaterial]] = {}  # station:type_id:material
        self.conveyor_settings: typing.Optional[ConveyorSettings] = None

    def calc(self,
             # данные корпорации для подсчёта кол-ва материалов
             corporation: db.QSwaggerCorporation,
             # настройки генерации отчёта
             conveyor_settings: ConveyorSettings):
        del self.stock_materials
        self.conveyor_settings = conveyor_settings
        # проверка правильности входных данных
        if not self.conveyor_settings.corporation.corporation_id == corporation.corporation_id:
            raise Exception("Incompatible conveyor settings and corporation data")
        self.stock_materials: typing.Dict[int, typing.Dict[int, db.QSwaggerMaterial]] = {}
        # составляем список контейнеров, в которых будет выполняться поиск материалов
        container_ids: typing.Set[int] = set([c.container_id for c in conveyor_settings.containers_stocks])
        # перебираем ассеты, ищем материалы
        for a in corporation.assets.values():
            if a.location_id not in container_ids: continue
            s: typing.Dict[int, db.QSwaggerMaterial] = self.stock_materials.get(a.station_id)
            if not s:
                self.stock_materials[a.station_id] = {}
                s = self.stock_materials.get(a.station_id)
            m = s.get(a.type_id)
            if m:
                m.increment_quantity(a.quantity)
            else:
                s[a.type_id] = db.QSwaggerMaterial(a.item_type, a.quantity)
        return self.stock_materials

    def check_enough_materials_at_station(
            self,
            # идентификатор станции на которой в коробках стока находятся материалы
            station_id: int,
            # материалы в списке не должны дублироваться (их необходимо суммировать до проверки)
            required_materials: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerMaterial]]) \
            -> typing.Tuple[bool, int]:  # yes|no, max possible
        available_materials: typing.Dict[int, db.QSwaggerMaterial] = self.stock_materials.get(station_id)
        if not available_materials:
            return False, 0
        max_possible: int = -1
        for materials in required_materials.values():
            for r in materials:
                # получаем материал в стоке
                a = available_materials.get(r.material_id)
                # определяем, достаточно ли имеющегося кол-ва материалов?
                if not a:
                    return False, 0
                if a.quantity < r.quantity:
                    return False, 0
                # определяем максимально возможное кол-во производственных запусков для этого списка потребностей
                if max_possible == 1:
                    pass
                elif max_possible < 0:
                    max_possible = a.quantity // r.quantity
                else:
                    max_possible = min(max_possible, a.quantity // r.quantity)
        return True, max_possible

    def check_enough_materials_everywhere(
            self,
            # материалы в списке не должны дублироваться (их необходимо суммировать до проверки)
            required_materials: typing.List[db.QSwaggerMaterial]) -> bool:
        for r in required_materials:
            required_quantity: int = r.quantity
            for station_id in self.stock_materials.keys():
                available_materials: typing.Dict[int, db.QSwaggerMaterial] = self.stock_materials.get(station_id)
                a = available_materials.get(r.material_id)
                if not a: continue
                required_quantity -= a.quantity
                if required_quantity <= 0: break
            if required_quantity > 0:
                return False
        return True


def calc_available_materials(conveyor_settings: typing.List[ConveyorSettings]) \
        -> typing.Dict[ConveyorSettings, ConveyorCorporationStockMaterials]:
    # считаем количество доступных материалов в стоках выбранных конвейеров
    available_materials: typing.Dict[ConveyorSettings, ConveyorCorporationStockMaterials] = {}
    for s in conveyor_settings:
        a: ConveyorCorporationStockMaterials = ConveyorCorporationStockMaterials()
        a.calc(s.corporation, s)
        available_materials[s] = a
    return available_materials


class ConveyorMaterialRequirements:
    class StackOfBlueprints:
        def __init__(self, name: str, station_id: int, runs: int, me: int, group: typing.List[db.QSwaggerCorporationBlueprint]):
            self.name: str = name
            self.station_id: int = station_id
            self.runs: int = runs
            self.me: int = me
            self.group: typing.List[db.QSwaggerCorporationBlueprint] = group
            self.max_possible_for_single: int = 0
            self.required_materials_for_single: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerMaterial]] = {}
            self.enough_for_stack: bool = False
            self.required_materials_for_stack: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerMaterial]] = {}

        def apply_materials_info(self,
                                 max_possible: int,
                                 materials_for_single: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerMaterial]],
                                 enough: bool,
                                 materials_for_stack: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerMaterial]]):
            del self.required_materials_for_single
            del self.required_materials_for_stack
            self.max_possible_for_single = max_possible
            self.required_materials_for_single = materials_for_single
            self.enough_for_stack = enough
            self.required_materials_for_stack = materials_for_stack

    def __init__(self):
        self.conveyor_settings: typing.Optional[ConveyorSettings] = None
        self.blueprints: typing.List[db.QSwaggerCorporationBlueprint] = []
        self.__grouped: typing.Dict[typing.Tuple[int, int, int, int], typing.List[db.QSwaggerCorporationBlueprint]] = {}
        self.__grouped_and_sorted: typing.List[ConveyorMaterialRequirements.StackOfBlueprints] = []

    def calc(
            self,
            # данные (справочники)
            qid: db.QSwaggerDictionary,
            # настройки генерации отчёта
            conveyor_settings: ConveyorSettings,
            # ассеты стока (материалы для расчёта возможностей и потребностей конвейера
            available_materials: ConveyorCorporationStockMaterials,
            # список чертежей, которые необходимо обработать
            ready_blueprints: typing.List[db.QSwaggerCorporationBlueprint]) \
            -> typing.List[StackOfBlueprints]:
        del self.__grouped_and_sorted
        del self.__grouped
        del self.blueprints
        # входной набор чертежей для проверки потребностей в материалах
        self.blueprints: typing.List[db.QSwaggerCorporationBlueprint] = ready_blueprints
        # группируем чертежи по типу, me и runs кодам, чтобы получить уникальные сочетания с количествами
        self.__grouped: typing.Dict[typing.Tuple[int, int, int, int, int], typing.List[db.QSwaggerCorporationBlueprint]] = \
            get_blueprints_grouped_by(  # type_id:station:me:te:runs
                self.blueprints,
                group_by_type_id=True,
                group_by_station=True,
                group_by_me=True,
                group_by_te=False,
                group_by_runs=True)
        # сортируем уже сгруппированные чертежи
        self.__grouped_and_sorted: typing.List[ConveyorMaterialRequirements.StackOfBlueprints] = []
        for key in self.__grouped.keys():
            group: typing.List[db.QSwaggerCorporationBlueprint] = self.__grouped.get(key)
            self.__grouped_and_sorted.append(
                ConveyorMaterialRequirements.StackOfBlueprints(
                    group[0].blueprint_type.blueprint_type.name,
                    group[0].station_id,
                    group[0].runs,
                    group[0].material_efficiency,
                    group))
        self.__grouped_and_sorted.sort(key=lambda x: (x.name, x.runs, -x.me))  # name:runs:me (длительность произв.)
        # рассчитываем потребности в материалах
        # все чертежи собраны в стеки по одному типу название:длительность_производства (name:runs:me)
        for stack in self.__grouped_and_sorted:
            b0: db.QSwaggerCorporationBlueprint = stack.group[0]
            """
            print(f"{b0.blueprint_type.blueprint_type.name} ({b0.type_id})"
                  f" x{len(stack.group)}"
                  f" {b0.material_efficiency}me"
                  f" {b0.runs}runs"
                  f" at {b0.station_id}"
                  # f"\n{[_.item_id for _ in stack.group]}"
                  "\n")
            """
            # вычисляем минимально необходимое кол-во материалов для работ хотя-бы по одному чертежу
            materials_single: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerMaterial]] = get_materials_list(
                qid,
                conveyor_settings,
                [b0],
                conveyor_settings.fixed_number_of_runs)
            # считаем общее количество материалов для работ по стеку чертежей
            materials_stack: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerMaterial]] = get_materials_list(
                qid,
                conveyor_settings,
                stack.group,
                conveyor_settings.fixed_number_of_runs)
            # проверка доступности материалов имеющихся в стоке
            enough_for_single, max_possible = \
                available_materials.check_enough_materials_at_station(b0.station_id, materials_single)
            enough_for_stack, _ = \
                available_materials.check_enough_materials_at_station(b0.station_id, materials_stack)
            # сохранение результатов расчёта в стеке чертежей
            stack.apply_materials_info(
                max_possible if enough_for_single else 0,
                materials_single,
                enough_for_stack,
                materials_stack)
        return self.__grouped_and_sorted


def calc_corp_conveyor(
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        # настройки генерации отчёта
        router_settings: typing.List[RouterSettings],
        conveyor_settings: ConveyorSettings,
        # ассеты стока (материалы для расчёта возможностей и потребностей конвейера
        available_materials: ConveyorCorporationStockMaterials,
        # список чертежей, которые нобходимо обработать
        ready_blueprints: typing.List[db.QSwaggerCorporationBlueprint]) \
        -> typing.List[ConveyorMaterialRequirements.StackOfBlueprints]:
    # готовимся к расчёту потребностей для заданного кол-ва чертежей
    requirements: ConveyorMaterialRequirements = ConveyorMaterialRequirements()
    # группируем чертежи по типу, me и runs кодам, чтобы получить уникальные сочетания с количествами
    # рассчитываем потребности в материалах
    # все чертежи собраны в стеки по одному типу название:длительность_производства (name:runs:me)
    grouped_and_sorted: typing.List[ConveyorMaterialRequirements.StackOfBlueprints] = requirements.calc(
        qid,
        conveyor_settings,
        available_materials,
        ready_blueprints
    )
    return grouped_and_sorted


def get_min_max_time(stack: ConveyorMaterialRequirements.StackOfBlueprints) -> typing.Tuple[int, int]:
    min_time, max_time = None, None

    def apply(min_t: int, max_t: int, t: int) -> typing.Tuple[int, int]:
        if min_t is None:
            min_t = t
            max_t = t
        else:
            min_t = min(min_t, t)
            max_t = max(max_t, t)
        return min_t, max_t

    for activity in stack.required_materials_for_stack.keys():
        if isinstance(activity, db.QSwaggerBlueprintManufacturing):
            for b in stack.group:
                # считаем бонус чертежа (накладываем TE чертежа на БП)
                __stage1: float = float(activity.time * (100 - b.time_efficiency) / 100.0)
                # навыки и импланты (базовые навыки начинающего производственника, который "ничего не умеет делать")
                __stage2: float = float(__stage1 * (100.0 - 31.5) / 100.0)
                # # учитываем бонус установленного модификатора
                __stage3: float = float(__stage2 * (100.0 - 42.0) / 100.0)
                # учитываем бонус профиля сооружения
                __stage4: float = float(__stage3 * (100.0 - 30.0) / 100.0)
                # округляем вещественное число до старшего целого
                __stage5: int = int(float(__stage4 + 0.99))
                # умножаем на кол-во прогонов
                __stageX: int = __stage5 * b.runs
                # считаем min/max
                min_time, max_time = apply(min_time, max_time, __stageX)
        elif isinstance(activity, db.QSwaggerBlueprintInvention):
            for b in stack.group:
                # навыки и импланты (базовые навыки начинающего производственника, который "ничего не умеет делать")
                __stage1: float = float(activity.time * (100.0 - 9.0) / 100.0)
                # учитываем бонус профиля сооружения
                __stage2: float = float(__stage1 * (100.0 - 30.0) / 100.0)
                # округляем вещественное число до старшего целого
                __stage3: int = int(float(__stage2 + 0.99))
                # умножаем на кол-во прогонов
                __stageX: int = __stage3 * b.runs
                # считаем min/max
                min_time, max_time = apply(min_time, max_time, __stageX)
        elif isinstance(activity, db.QSwaggerBlueprintReaction):
            for b in stack.group:
                # навыки и импланты (базовые навыки начинающего производственника, который "ничего не умеет делать")
                __stage1: float = float(activity.time * (100.0 - 16.0) / 100.0)
                # учитываем бонус установленного модификатора
                __stage2: float = float(__stage1 * (100.0 - 22.0) / 100.0)
                # учитываем бонус профиля сооружения
                __stage3: float = float(__stage2 * (100.0 - 25.0) / 100.0)
                # округляем вещественное число до старшего целого
                __stage4: int = int(float(__stage3 + 0.99))
                # умножаем на кол-во прогонов
                __stageX: int = __stage4 * b.runs
                # считаем min/max
                min_time, max_time = apply(min_time, max_time, __stageX)
        else:  # подразумевается копирка (или research)
            for b in stack.group:
                # навыки и импланты (базовые навыки начинающего производственника, который "ничего не умеет делать")
                __stage1: float = float(activity.time * (100.0 - 27.2) / 100.0)
                # учитываем бонус профиля сооружения
                __stage2: float = float(__stage1 * (100.0 - 30.0) / 100.0)
                # округляем вещественное число до старшего целого
                __stage3: int = int(float(__stage2 + 0.99))
                # умножаем на кол-во прогонов
                __stageX: int = __stage3 * b.runs
                # считаем min/max
                min_time, max_time = apply(min_time, max_time, __stageX)
    return min_time, max_time


# ConveyorDictionary - долговременный справочник материалов конвейера, хранится долго и накапливает информацию из
# экземпляров QSwaggerTypeId
class ConveyorDictionary:
    def __init__(self, qid: db.QSwaggerDictionary):
        # сохраняем ссылку на ПОЛНЫЙ справочник загруженный из БД
        self.qid: db.QSwaggerDictionary = qid
        # подготовка списка-справочника, который будет хранить идентификаторы  все продуктов, используемых конвейером
        self.materials: typing.Set[int] = set()

    def __del__(self):
        # уничтожаем свой список-справочник, остальные (не наши) не трогаем
        del self.materials

    def load_router_settings(self, router_settings: typing.List[RouterSettings]) -> None:
        for r in router_settings:
            self.materials = self.materials | set(r.output)

    def load_type_ids(self, type_ids: typing.Set[int]):
        self.materials = self.materials | set(type_ids)
