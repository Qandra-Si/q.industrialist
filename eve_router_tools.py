""" Router and Conveyor tools and utils
"""
import typing

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


class ConveyorSettings:
    def __init__(self, corporation: db.QSwaggerCorporation):
        # параметры работы конвейера
        self.corporation: db.QSwaggerCorporation = corporation
        self.fixed_number_of_runs: typing.Optional[int] = None
        self.same_stock_container: bool = False
        self.activities: typing.List[db.QSwaggerActivityCode] = [db.QSwaggerActivityCode.MANUFACTURING]
        self.conveyor_with_reactions: bool = False
        # идентификаторы контейнеров с чертежами, со стоком, с формулами, исключённых из поиска и т.п.
        self.containers_sources: typing.List[ConveyorSettingsPriorityContainer] = []  # station:container:priority
        self.containers_stocks: typing.List[ConveyorSettingsContainer] = []  # station:container
        self.containers_output: typing.List[ConveyorSettingsContainer] = []  # station:container
        self.containers_additional_blueprints: typing.List[ConveyorSettingsContainer] = []  # station:container
        self.containers_react_formulas: typing.List[ConveyorSettingsContainer] = []  # station:container
        self.containers_exclude: typing.List[ConveyorSettingsContainer] = []  # station:container
        # параметры поведения конвейера (связь с торговой деятельностью, влияние её поведения на работу производства)
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


def get_asset_items_grouped_by(
        asset_items: typing.List[db.QSwaggerCorporationAssetsItem],
        group_by_type_id: bool = True,
        group_by_station: bool = True) \
        -> typing.Dict[typing.Tuple[int, int], typing.List[db.QSwaggerCorporationAssetsItem]]:
    grouped: typing.Dict[typing.Tuple[int, int], typing.List[db.QSwaggerCorporationAssetsItem]] = {}
    for b in asset_items:
        type_id: int = b.type_id if group_by_type_id else 0
        station_id: int = b.station_id if group_by_station else 0
        key: typing.Tuple[int, int] = type_id, station_id
        g0: typing.List[db.QSwaggerCorporationAssetsItem] = grouped.get(key)
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
    if db.QSwaggerActivityCode.MANUFACTURING.to_int() == activity_id:
        manufacturing: db.QSwaggerBlueprintManufacturing = activity
        return manufacturing.quantity
    elif db.QSwaggerActivityCode.INVENTION.to_int() == activity_id:
        invention: db.QSwaggerBlueprintInvention = activity
        return next((p.quantity for p in invention.products if p.product_id == product_type_id), 1)
    elif db.QSwaggerActivityCode.COPYING.to_int() == activity_id:
        return 1  # copying: db.QSwaggerBlueprintCopying = activity
    elif db.QSwaggerActivityCode.RESEARCH_MATERIAL.to_int() == activity_id:
        return 1  # research_material: db.QSwaggerBlueprintResearchMaterial = activity
    elif db.QSwaggerActivityCode.RESEARCH_TIME.to_int() == activity_id:
        return 1  # research_time: db.QSwaggerBlueprintResearchTime = activity
    elif db.QSwaggerActivityCode.REACTION.to_int() == activity_id:
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
            if a == db.QSwaggerActivityCode.INVENTION:
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
                    market_group: typing.Optional[db.QSwaggerMarketGroup] = qid.there_is_market_group_in_chain(
                        b.blueprint_type.blueprint_type,
                        {204, 943, 1909})
                    if market_group:
                        if market_group.group_id == 204:  # Ships
                            decryptor_type: db.QSwaggerTypeId = qid.get_type_id(34201)  # Accelerant Decryptor
                        elif market_group.group_id == 943:  # Ship Modifications
                            decryptor_type: db.QSwaggerTypeId = qid.get_type_id(34206)  # Symmetry Decryptor
                        elif market_group.group_id == 1909:  # Ancient Relics
                            decryptor_type: db.QSwaggerTypeId = qid.get_type_id(34204)  # Parity Decryptor
                        else:
                            raise Exception("This shouldn't have happened")
                        # расчёт кол-ва декрипторов с учётом эффективности производства
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
             conveyor_settings: ConveyorSettings) \
            -> typing.Dict[int, typing.Dict[int, db.QSwaggerMaterial]]:
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

    class CheckEnoughResult:
        def __init__(self,
                     enough: bool,
                     max_possible: typing.Optional[int],
                     not_available: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerMaterial]]):
            self.non_decryptors_missing: bool = not enough
            self.decryptors_missing: typing.Optional[bool] = None
            self.max_possible: typing.Optional[int] = max_possible
            self.not_available: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerMaterial]] = not_available

        @property
        def enough(self):
            return not self.non_decryptors_missing

        @property
        def only_decryptors_missing(self):
            return not self.non_decryptors_missing and self.decryptors_missing

    def check_enough_materials_at_station(
            self,
            # идентификатор станции на которой в коробках стока находятся материалы
            station_id: int,
            # материалы в списке не должны дублироваться (их необходимо суммировать до проверки)
            required_materials: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerMaterial]]) \
            -> CheckEnoughResult:
        available_materials: typing.Dict[int, db.QSwaggerMaterial] = self.stock_materials.get(station_id)
        if not available_materials:
            if not required_materials:
                return ConveyorCorporationStockMaterials.CheckEnoughResult(True, None, {})
            else:
                return ConveyorCorporationStockMaterials.CheckEnoughResult(False, 0, required_materials)

        result: ConveyorCorporationStockMaterials.CheckEnoughResult = \
            ConveyorCorporationStockMaterials.CheckEnoughResult(True, -1, {})

        def push(a338: db.QSwaggerActivity, m338: db.QSwaggerMaterial, q338: int) -> bool:
            m340: db.QSwaggerMaterial = db.QSwaggerMaterial(m338.material_type, q338)
            mm334: typing.List[db.QSwaggerMaterial] = result.not_available.get(a338)
            if mm334 is None:
                result.not_available[a338] = [m340]
            else:
                mm334.append(m340)
            is_decryptor: bool = m338.material_type.market_group_id == 1873
            if is_decryptor:
                result.decryptors_missing = True
            else:
                result.non_decryptors_missing = True
            return is_decryptor

        for activity, materials in required_materials.items():
            for r in materials:
                # получаем материал в стоке
                a = available_materials.get(r.material_id)
                # определяем, достаточно ли имеющегося кол-ва материалов?
                if not a:
                    if push(activity, r, r.quantity):
                        # отсутствие декрипторов не мешает запуску работы
                        continue
                    else:
                        result.max_possible = 0
                elif a.quantity < r.quantity:
                    if push(activity, r, r.quantity - a.quantity):
                        # отсутствие декрипторов не мешает запуску работы
                        continue
                    else:
                        result.max_possible = 0
                # определяем максимально возможное кол-во производственных запусков для этого списка потребностей
                if result.max_possible in (0, 1):
                    pass
                elif result.max_possible < 0:
                    result.max_possible = a.quantity // r.quantity
                else:
                    result.max_possible = min(result.max_possible, a.quantity // r.quantity)
        return result

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
            self.run_possible: bool = False
            self.only_decryptors_missing_for_stack: bool = True
            self.required_materials_for_stack: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerMaterial]] = {}
            self.not_available_materials_for_stack: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerMaterial]] = {}

        def apply_materials_info(self,
                                 materials_for_single: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerMaterial]],
                                 enough_for_single: ConveyorCorporationStockMaterials.CheckEnoughResult,
                                 materials_for_stack: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerMaterial]],
                                 enough_for_stack: ConveyorCorporationStockMaterials.CheckEnoughResult):
            del self.required_materials_for_single
            del self.required_materials_for_stack
            del self.not_available_materials_for_stack
            # ---
            self.max_possible_for_single = enough_for_single.max_possible
            self.required_materials_for_single = materials_for_single
            # ---
            self.run_possible = enough_for_single.enough
            self.only_decryptors_missing_for_stack = enough_for_stack.only_decryptors_missing
            self.required_materials_for_stack = materials_for_stack
            self.not_available_materials_for_stack = enough_for_stack.not_available

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
            enough_for_single: ConveyorCorporationStockMaterials.CheckEnoughResult = \
                available_materials.check_enough_materials_at_station(b0.station_id, materials_single)
            enough_for_stack: ConveyorCorporationStockMaterials.CheckEnoughResult = \
                available_materials.check_enough_materials_at_station(b0.station_id, materials_stack)
            # сохранение результатов расчёта в стеке чертежей
            stack.apply_materials_info(materials_single, enough_for_single, materials_stack, enough_for_stack)
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


def get_router_details(
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        # настройки генерации отчёта
        router_settings: RouterSettings,
        conveyor_settings: typing.List[ConveyorSettings]) \
        -> typing.Tuple[db.QSwaggerStation, db.QSwaggerCorporation, typing.Set[int], typing.Set[int]]:
    # определяем станцию, корпорацию и стоки конвейера соответствующего роутеру
    station: db.QSwaggerStation = qid.get_station_by_name(router_settings.station)
    if not station:
        raise Exception("Invalid router settings with unknown station")
    station_id: int = station.station_id
    containers_stocks: typing.Set[int] = set()
    containers_output: typing.Set[int] = set()
    corporation: typing.Optional[db.QSwaggerCorporation] = None
    for cs in conveyor_settings:
        for c in cs.containers_stocks:
            if c.station_id == station_id:
                containers_stocks.add(c.container_id)
                if corporation and not corporation == c.corporation:
                    raise Exception(
                        f"There are multiple routes for multiple corporations {corporation.corporation_name} and {c.corporation.corporation_name}")
                corporation = c.corporation
        for c in cs.containers_output:
            if c.station_id == station_id:
                containers_output.add(c.container_id)
                if corporation and not corporation == c.corporation:
                    raise Exception(
                        f"There are multiple routes for multiple corporations {corporation.corporation_name} and {c.corporation.corporation_name}")
                corporation = c.corporation
    if not corporation:
        raise Exception("Invalid router settings without corporation' conveyor settings")
    return station, corporation, containers_stocks, containers_output


class ConveyorCorporationOutputProducts:
    def __init__(self, index: int):
        self.index: int = index
        self.output_products: typing.Dict[int, db.QSwaggerMaterial] = {}  # type_id:material
        self.lost_products: typing.Dict[int, typing.List[db.QSwaggerCorporationAssetsItem]] = {}  # type_id:list(assets)
        self.corporation: typing.Optional[db.QSwaggerCorporation] = None
        self.station: typing.Optional[db.QSwaggerStation] = None
        self.router_settings: typing.Optional[RouterSettings] = None
        self.conveyor_settings: typing.List[ConveyorSettings] = []
        self.activities: typing.Set[db.QSwaggerActivityCode] = set()

    def calc(self,
             # данные (справочники)
             qid: db.QSwaggerDictionary,
             # данные корпорации для подсчёта кол-ва материалов
             corporation: db.QSwaggerCorporation,
             # настройки генерации отчёта
             conveyor_settings: typing.List[ConveyorSettings],
             router_settings: RouterSettings,
             # список активностей, которые выполняются для получения продуктов роутера
             activities: typing.Set[db.QSwaggerActivityCode]) \
            -> typing.Dict[int, db.QSwaggerMaterial]:
        del self.activities
        del self.conveyor_settings
        del self.lost_products
        del self.output_products
        # ---
        self.output_products: typing.Dict[int, db.QSwaggerMaterial] = {}
        self.lost_products: typing.Dict[int, typing.List[db.QSwaggerCorporationAssetsItem]] = {}
        self.corporation: db.QSwaggerCorporation = corporation
        self.station: db.QSwaggerStation = None
        self.router_settings: RouterSettings = router_settings
        self.conveyor_settings: typing.List[ConveyorSettings] = conveyor_settings[:]
        self.activities: typing.Set[db.QSwaggerActivityCode] = activities
        # ---
        # проверка правильности входных данных
        if next((_ for _ in self.conveyor_settings if not _.corporation.corporation_id == self.corporation.corporation_id), None) is not None:
            raise Exception("Incompatible conveyor settings and corporation data")
        # определяем станцию, корпорацию и стоки конвейера соответствующего роутеру
        router_details: typing.Tuple[db.QSwaggerStation, db.QSwaggerCorporation, typing.Set[int], typing.Set[int]] = get_router_details(
            qid,
            router_settings,
            conveyor_settings
        )
        self.station: db.QSwaggerStation = router_details[0]
        if corporation.corporation_id != router_details[1].corporation_id:
            raise Exception("Something wrong: incompatible corporations for conveyor/router settings")
        # containers_stocks: typing.Set[int] = router_details[2]
        containers_output: typing.Set[int] = router_details[3]
        containers_exclude: typing.Set[int] = set([_.container_id for x in conveyor_settings for _ in x.containers_exclude])
        # перебираем ассеты, ищем материалы
        if containers_output:
            station_id: int = self.station.station_id
            for a in corporation.assets.values():
                if not a.station_id == station_id: continue
                if a.location_id in containers_exclude: continue
                # проверям "заблудился" ли продукт, или лежит на своём месте?
                type_id: int = a.type_id
                # если output не сконфигурирован, то на станции производится вся возможная продукция (кроме тех, что
                # сконфигурированы на других станциях)
                correct_container: bool = a.location_id in containers_output
                correct_product: bool = True
                if router_settings.output:
                    if type_id not in router_settings.output:
                        correct_product = False
                elif not correct_container:
                    continue
                # ---
                if not correct_container and not correct_product:
                    continue
                elif correct_container and correct_product:
                    p = self.output_products.get(a.type_id)
                    if p:
                        p.increment_quantity(a.quantity)
                    else:
                        self.output_products[a.type_id] = db.QSwaggerMaterial(a.item_type, a.quantity)
                else:
                    p = self.lost_products.get(a.type_id)
                    if p:
                        p.append(a)
                    else:
                        self.lost_products[a.type_id] = [a]
        return self.output_products


def calc_ready_products(
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        # настройки генерации отчёта
        router_settings: typing.List[RouterSettings],
        conveyor_settings: typing.List[ConveyorSettings]) \
        -> typing.Dict[RouterSettings, ConveyorCorporationOutputProducts]:
    if not conveyor_settings or not router_settings:
        return {}
    # проверям, что конвейер - поддерживается только одна производственная корпорация
    corporation: db.QSwaggerCorporation = conveyor_settings[0].corporation
    if next((_ for _ in conveyor_settings if not _.corporation.corporation_id == corporation.corporation_id), None) is not None:
        raise Exception("Unsupported multi-corporation conveyor")
    # считаем количество готовых продуктов на выбранных станциях
    ready_products: typing.Dict[RouterSettings, ConveyorCorporationOutputProducts] = {}
    for index, rs in enumerate(router_settings):
        # надо определиться, является ли конвейер manufacturing или reaction
        activities: typing.Set[db.QSwaggerActivityCode] = set()
        if rs.output:
            # если список производства задан, то это "внешняя станция" со своими настройками производства
            for b in qid.sde_blueprints.values():
                if b.manufacturing and b.manufacturing.product_id in rs.output:
                    activities.add(db.QSwaggerActivityCode.MANUFACTURING)
                if b.reaction and b.reaction.product_id in rs.output:
                    activities.add(db.QSwaggerActivityCode.REACTION)
        else:
            # если список производства не задан, то это основная станция на которой производится всё, кроме
            # перечисленного (хотя при наличии чертежей, можно запускать что угодно вообще, и реакции?)
            activities.add(db.QSwaggerActivityCode.MANUFACTURING)
        local_conveyor_settings: typing.List[ConveyorSettings] = []
        for cs in conveyor_settings:
            # также можно проверять: if not _.corporation.corporation_id == corporation.corporation_id: continue
            if db.QSwaggerActivityCode.REACTION in cs.activities:
                if db.QSwaggerActivityCode.REACTION in activities:
                    # local_conveyor_settings.append(cs)
                    # continue
                    # Внимание! это неподдерживаемый способ настройки конвейера
                    pass
            if db.QSwaggerActivityCode.MANUFACTURING in cs.activities:
                if db.QSwaggerActivityCode.MANUFACTURING in activities:
                    local_conveyor_settings.append(cs)
                    continue
                if cs.conveyor_with_reactions and db.QSwaggerActivityCode.REACTION in activities:
                    local_conveyor_settings.append(cs)
                    continue
        if not local_conveyor_settings:
            raise Exception("There is router settings not complementary with conveyor settings")
        if not local_conveyor_settings: continue
        a: ConveyorCorporationOutputProducts = ConveyorCorporationOutputProducts(index)
        a.calc(qid, corporation, local_conveyor_settings, rs, activities)
        ready_products[rs] = a
    return ready_products


def get_min_max_time(
        activities: typing.List[db.QSwaggerActivityCode],
        stack: ConveyorMaterialRequirements.StackOfBlueprints) -> typing.Tuple[int, int]:
    min_time, max_time = None, None

    def apply(min_t: int, max_t: int, t: int) -> typing.Tuple[int, int]:
        if min_t is None:
            min_t = t
            max_t = t
        else:
            min_t = min(min_t, t)
            max_t = max(max_t, t)
        return min_t, max_t

    for b in stack.group:
        if db.QSwaggerActivityCode.MANUFACTURING in activities and b.blueprint_type.manufacturing:
            activity: db.QSwaggerBlueprintManufacturing = b.blueprint_type.manufacturing
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
        if db.QSwaggerActivityCode.INVENTION in activities and b.blueprint_type.invention:
            activity: db.QSwaggerBlueprintInvention = b.blueprint_type.invention
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
        if db.QSwaggerActivityCode.REACTION in activities and b.blueprint_type.reaction:
            activity: db.QSwaggerBlueprintReaction = b.blueprint_type.reaction
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
        if b.is_original:
            for a in [db.QSwaggerActivityCode.COPYING,
                      db.QSwaggerActivityCode.RESEARCH_TIME,
                      db.QSwaggerActivityCode.RESEARCH_MATERIAL]:
                if a not in activities: continue
                activity: db.QSwaggerActivity = b.blueprint_type.get_activity(a.to_int())
                if not activity: continue
                # навыки и импланты (базовые навыки начинающего производственника, который "ничего не умеет делать")
                __stage1: float = float(activity.time * (100.0 - 27.2) / 100.0)
                # учитываем бонус профиля сооружения
                __stage2: float = float(__stage1 * (100.0 - 30.0) / 100.0)
                # округляем вещественное число до старшего целого
                __stage3: int = int(float(__stage2 + 0.99))
                # умножаем на кол-во прогонов
                __stageX: int = __stage3  # нельзя умножать на runs, оно равно -1
                # считаем min/max
                min_time, max_time = apply(min_time, max_time, __stageX)
    return min_time, max_time


# ConveyorDictionary - долговременный справочник материалов конвейера, хранится долго и накапливает информацию из
# экземпляров QSwaggerTypeId
class ConveyorDictionary:
    def __init__(self, qid: db.QSwaggerDictionary):
        # сохраняем ссылку на ПОЛНЫЙ справочник загруженный из БД
        self.qid: db.QSwaggerDictionary = qid
        # подготовка списка-справочника, который будет хранить идентификаторы всех продуктов, используемых конвейером
        self.materials: typing.Set[int] = set()
        # подготовка списка-справочника, который будет хранить используемые материалы в различных activity (скопом)
        self.involved_materials: typing.Dict[db.QSwaggerActivityCode, typing.Set[int]] = {}
        self._fill_involved_materials()

    def __del__(self):
        # уничтожаем свой список-справочник, остальные (не наши) не трогаем
        del self.materials

    def _fill_involved_materials(self):
        self.involved_materials: typing.Dict[db.QSwaggerActivityCode, typing.Set[int]] = {
            db.QSwaggerActivityCode.MANUFACTURING: set(),
            db.QSwaggerActivityCode.INVENTION: set(),
            db.QSwaggerActivityCode.COPYING: set(),
            db.QSwaggerActivityCode.RESEARCH_MATERIAL: set(),
            db.QSwaggerActivityCode.RESEARCH_TIME: set(),
            db.QSwaggerActivityCode.REACTION: set()
        }
        for by_products in self.qid.sde_activities.values():
            for activity in by_products:
                ids: typing.Set[int] = set([_.material_id for _ in activity.materials.materials])
                if isinstance(activity, db.QSwaggerBlueprintManufacturing):
                    a: db.QSwaggerActivityCode = db.QSwaggerActivityCode.MANUFACTURING
                elif isinstance(activity, db.QSwaggerBlueprintInvention):
                    a: db.QSwaggerActivityCode = db.QSwaggerActivityCode.INVENTION
                elif isinstance(activity, db.QSwaggerBlueprintCopying):
                    a: db.QSwaggerActivityCode = db.QSwaggerActivityCode.COPYING
                elif isinstance(activity, db.QSwaggerBlueprintResearchMaterial):
                    a: db.QSwaggerActivityCode = db.QSwaggerActivityCode.RESEARCH_MATERIAL
                elif isinstance(activity, db.QSwaggerBlueprintResearchTime):
                    a: db.QSwaggerActivityCode = db.QSwaggerActivityCode.RESEARCH_TIME
                elif isinstance(activity, db.QSwaggerBlueprintReaction):
                    a: db.QSwaggerActivityCode = db.QSwaggerActivityCode.REACTION
                else:
                    raise Exception("Unknown type of activity")
                involved: typing.Set[int] = self.involved_materials.get(a)
                involved.update(ids)

    def load_router_settings(self, router_settings: typing.List[RouterSettings]) -> None:
        for r in router_settings:
            self.materials = self.materials | set(r.output)

    def load_type_ids(self, type_ids: typing.Set[int]):
        self.materials = self.materials | set(type_ids)

    def load_available_materials(self, available_materials: typing.Dict[ConveyorSettings, ConveyorCorporationStockMaterials]):
        for stocks in available_materials.values():
            for materials in stocks.stock_materials.values():
                self.load_type_ids(materials.keys())

    def load_ready_products(self, ready_products: typing.Dict[RouterSettings, ConveyorCorporationOutputProducts]):
        for products in ready_products.values():
            self.load_type_ids(products.output_products.keys())
            self.load_type_ids(products.lost_products.keys())

    def load_requirements(self, requirements: typing.List[ConveyorMaterialRequirements.StackOfBlueprints]):
        for stack in requirements:
            for materials in stack.required_materials_for_single.values():
                self.load_type_ids(set([_.material_id for _ in materials]))


def get_conveyor_table_sort_data(
        priority: int,
        activities: typing.List[db.QSwaggerActivityCode],
        row_num: typing.Optional[int],
        duration: typing.Optional[typing.Tuple[int, int]]):
    sort = {'p': priority, 'a': [_.to_int() for _ in activities]}
    if row_num is not None:
        sort.update({'n': row_num + 1})  # не м.б. 0, т.к. 0 зарезервирован для banner-а
    if duration is not None:
        if duration[0] == duration[1]:  # 0-min, 1-max
            sort.update({'d': duration[0]})
        else:
            sort.update({'d1': duration[0], 'd2': duration[1]})
    elif row_num is not None:
        sort.update({'lp': 1})   # нижняя часть (несортируемая)
    return sort
