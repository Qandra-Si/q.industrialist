""" Conveyor tools and utils
"""
import typing
from math import ceil
from math import floor

import eve_sde_tools
import eve_efficiency

from __init__ import __version__


# ConveyorItem - это и материал (material) используемый в производстве, и продукт (product) используемый в производстве
class ConveyorItem:
    def __init__(self,
                 type_id: int,
                 # sde данные, загруженные из .converted_xxx.json файлов
                 sde_type_ids,
                 sde_bp_materials,
                 sde_market_groups,
                 # esi данные, загруженные с серверов CCP
                 corp_industry_jobs_data,
                 # списки контейнеров и станок из экземпляра контейнера
                 manufacturing_blueprint_loc_ids,
                 manufacturing_stock_loc_ids,
                 reaction_stock_loc_ids,
                 # список ресурсов, которые используются в производстве
                 manufacturing_stock_resources,
                 reaction_stock_resources):
        # код продукта
        self.type_id: int = type_id
        # название продукта
        self.name: str = eve_sde_tools.get_item_name_by_type_id(sde_type_ids, type_id)
        # market-группа, которой принадлежит продукт
        self.market_group: int = eve_sde_tools.get_market_group_by_type_id(sde_type_ids, type_id)
        self.market_group_dict = sde_market_groups.get(str(self.market_group))
        # базовая (основная) market-группа, которой принадлежит товар
        self.basis_market_group: int = eve_sde_tools.get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, type_id)
        self.basis_market_group_dict = sde_market_groups.get(str(self.basis_market_group))
        # кол-во данного продукта, который имеется на manufacturing-станции
        self.exist_in_manuf_stock: int = manufacturing_stock_resources.get(type_id, 0)
        # кол-во данного продукта, который имеется на reaction-станции
        self.exist_in_react_stock: int = reaction_stock_resources.get(type_id, 0)
        # кол-во данного продукта, который зарезервирован на manufacturing-станции (в результате расчёта производства)
        self.reserved_in_manuf_stock: int = 0
        # кол-во данного продукта, который зарезервирован на reaction-станции (в результате расчёта производства)
        self.reserved_in_react_stock: int = 0
        # поиск чертежа, который подходит для производства данного типа продукта
        self.blueprint_type_id = None
        self.blueprint_name = None
        self.blueprint_activity = None
        self.blueprint_activity_dict = None
        # признак, получается ли данный продукт в результате реакции
        self.is_reaction = None
        # 'символ' станции, на которой происходит производство данного продукта
        #  'M' - индустриальная станция (Sotiyo)
        #  'R' - станция проведения реакций (Tatara)
        #  None - если продукт не производится (например Tritanium) или данных по нему нет (не обновлён SDE)
        self.where = None
        # сведения о запуске чертежа/ей
        self.products_per_single_run = None
        self.runs_number_per_day = None
        # настраиваем запуски чертежей: списка запусков (план по имеющимся в наличие чертежам)
        self.runs_and_jobs = []
        # настраиваем справочник для сохранения "пользовательских" данных в объекте (очищается методом clear)
        self.user_data = {}
        # сводные сведения о работах
        self.in_progress: int = 0
        # ---
        # получаем информацию о чертежах и способе производства материала
        # настройка запусков чертежей
        self.setup_blueprint_details(sde_type_ids, sde_bp_materials)
        # получаем список работ, которые ведутся с этим материалом, а результаты сбрасываются в сток
        self.setup_industry_jobs(
            corp_industry_jobs_data,
            manufacturing_blueprint_loc_ids,
            manufacturing_stock_loc_ids, reaction_stock_loc_ids)

    def __del__(self):
        self.clear()
        del self.blueprint_activity_dict
        del self.runs_and_jobs
        del self.user_data

    # сброс сведений о зерезервированности продукта (меняются в результате расчёта)
    def clear(self):
        self.reserved_in_manuf_stock: int = 0
        self.reserved_in_react_stock: int = 0
        self.runs_and_jobs = []
        self.user_data = {}

    # считаем остатки и потребности кол-ва материалов в manufacturing-стоке
    def get_not_available_in_manuf_stock(self):
        res: int = (self.reserved_in_manuf_stock - self.exist_in_manuf_stock) if self.exist_in_manuf_stock < self.reserved_in_manuf_stock else 0
        return res

    # считаем остатки и потребности кол-ва материалов в reaction-стоке
    def get_not_available_in_react_stock(self):
        res: int = (self.reserved_in_react_stock - self.exist_in_react_stock) if self.exist_in_react_stock < self.reserved_in_react_stock else 0
        return res

    # считаем остатки и потребности кол-ва материалов и в manufacturing-стоке и в reaction-стоке
    def get_not_available_in_all_stocks(self):
        return self.get_not_available_in_manuf_stock() + self.get_not_available_in_react_stock()

    # выполняем проверку на необходимость/возможность транспортировки части стока с другой станции в manufacturing-сток
    def need_transfer_into_manuf_stock(self):
        if self.exist_in_react_stock:
            if self.get_not_available_in_react_stock():
                return False
            elif self.get_not_available_in_manuf_stock():
                return True
        return False

    # выполняем проверку на необходимость/возможность транспортировки части стока с другой станции в reaction-сток
    def need_transfer_into_react_stock(self):
        if self.exist_in_manuf_stock:
            if self.get_not_available_in_manuf_stock():
                return False
            elif self.get_not_available_in_react_stock():
                return True
        return False

    # выполняем проверку на необходимость/возможность транспортировки части стока с одной станции на другую
    def need_transfer_between_stocks(self):
        return self.need_transfer_into_manuf_stock() or self.need_transfer_into_react_stock()

    # получаем информацию о чертежах и способе производства материала
    # TODO: внимание! возможно, что один и тот же продукт может производиться разными способами - касается инвентов!
    def setup_blueprint_details(self, sde_type_ids, sde_bp_materials):
        # если продукт производится по формулам, то это однозначно реакция (производить на татаре)
        (self.blueprint_type_id, activity_dict) = eve_sde_tools.get_blueprint_type_id_by_product_id(
            self.type_id,
            sde_bp_materials,
            'reaction')
        if self.blueprint_type_id is not None:
            self.is_reaction = True
            self.where = 'R'
            self.blueprint_activity = 'reaction'
        else:
            # если имеем дело с manufacturing-производством, то проверяем какой market-группе принадлежит продукт, если
            # это топливные блоки, то помечаем, что они будут крафтиться на reaction-станции
            (self.blueprint_type_id, activity_dict) = eve_sde_tools.get_blueprint_type_id_by_product_id(
                self.type_id,
                sde_bp_materials,
                'manufacturing')
            if self.blueprint_type_id is None:
                # если продукт не производится в результате производства, то оставляем поля None
                # если данные по производимому продукту отсутствуют (не обновлён SDE), то оставляем поля None
                return
            self.is_reaction = False
            self.where = 'M'
            self.blueprint_activity = 'manufacturing'
        # получаем прочую справочную информацию о чертеже и методе производства материала
        self.blueprint_name = eve_sde_tools.get_item_name_by_type_id(sde_type_ids, self.blueprint_type_id)
        self.blueprint_activity_dict = activity_dict['activities'][self.blueprint_activity]
        if len(self.blueprint_activity_dict['products']) != 1:
            raise Exception('Unable to get product quantity information')
        self.products_per_single_run = self.blueprint_activity_dict['products'][0]['quantity']
        if self.is_reaction:
            self.runs_number_per_day = 15
        else:
            tm: int = self.blueprint_activity_dict['time']
            if tm >= (5*60*60*24):
                self.runs_number_per_day = 1
            elif tm > 0:
                self.runs_number_per_day = ceil(5*60*60*24 / tm)
        # определяем какой группе принадлежит производимый продукт и корректируем использование чертежей
        # TODO: оформить это как настройку
        # if self.market_group == 1870:  # Fuel Blocks -> Tatara
        #     self.where = 'R'

    # получаем список работ, которые ведутся с этим материалом, а результаты сбрасываются в сток
    def setup_industry_jobs(
            self,
            corp_industry_jobs_data,
            manufacturing_blueprint_loc_ids,
            manufacturing_stock_loc_ids,
            reaction_stock_loc_ids):
        if self.blueprint_type_id is None:
            self.in_progress = 0
        else:
            # проверяем список работ, которые ведутся с этим материалом, а результаты сбрасываются в manuf/react stock
            # также проверяем список работ, чертежи которых были взяты из контейнеров конвейера
            for j in corp_industry_jobs_data:
                product_type_id: int = j["product_type_id"]
                if product_type_id != self.type_id:
                    continue
                output_location_id: int = j['output_location_id']
                if output_location_id in manufacturing_stock_loc_ids:
                    self.in_progress += j["runs"]
                elif output_location_id in reaction_stock_loc_ids:
                    self.in_progress += j["runs"]
                # TODO: потерявшиеся работы надо как-то отдельным образом подсвечивать
                # возможна ситуация, когда какая-либо работа запущена из коробки с чертежами, но её выход направлен не
                # в сток, а например в ту же коробку, что можно обнаружить с помощью blueprint_location_id и учесть
            # умножаем на кол-во производимых материалов на один run
            if self.products_per_single_run is not None:
                self.in_progress *= self.products_per_single_run

    # отслеживание (подготовка) запусков работ
    def schedule_job_launches(self, blueprints: int, runs: int):
        # реакции планируются к запуску определённым кол-вом запусков, поэтому не сверяемся с кол-вом run-ов
        if self.is_reaction:
            if not self.runs_and_jobs:
                self.runs_and_jobs = [{'q': blueprints, 'runs': runs}]
            else:
                self.runs_and_jobs[0]['q'] += blueprints
        # по всем остальным типам работ пока нет никаких конкретных планов, поэтому увеличиваем раны одного чертежа
        # TODO: найти чертежи и построить план запусков bpc (пока не кончатся), а потом уже планировать использовать bpo
        else:
            if not self.runs_and_jobs:
                self.runs_and_jobs = [{'q': 1, 'runs': runs}]
            else:
                self.runs_and_jobs[0]['runs'] += runs

    # blueprints_details: подробности о чертежах этого типа [{"q": -1, "r": -1}, {"q": 2, "r": -1}, {"q": -2, "r": 179}]
    # метод возвращает список tuple: [{"id": 11399, "q": 11, "qmin": 11"}] с учётом ME
    def get_materials_list_for_set_of_blueprints(
            self,  # используются сведения о чертеже, тип индустрии (manufacturing, research_material),...
            blueprints_details,  # при is_blueprint_copy=True tuple={"r":?}, при False tuple={"r":?,"q":?}
            material_efficiency,  # параметр чертежа (набора чертежей)
            is_blueprint_copy=True,  # при is_blueprint_copy=True, в списке blueprints_details анализиуется только "r"
            fixed_number_of_runs=None):  # учитывается только для оригиналов, т.е. для is_blueprint_copy=False
        # список материалов по набору чертежей с учётом ME
        materials_list_with_efficiency = []
        # перебираем все ресурсы (материалы) чертежа
        for m in self.blueprint_activity_dict["materials"]:
            bp_manuf_need_all = 0
            bp_manuf_need_min = 0
            for __bp3 in blueprints_details:
                # расчёт кол-ва ранов для этого чертежа
                if is_blueprint_copy:
                    quantity_of_runs = __bp3["r"]
                    quantity_of_blueprints = 1
                else:
                    quantity_of_blueprints = __bp3["q"] if __bp3["q"] > 0 else 1
                    quantity_of_runs = fixed_number_of_runs if fixed_number_of_runs else 1
                    # умножение на количество оригиналов будет выполнено позже...
                # расчёт кол-ва материала с учётом эффективности производства
                __industry_input = eve_efficiency.get_industry_material_efficiency(
                    self.blueprint_activity,
                    quantity_of_runs,
                    m["quantity"],  # сведения из чертежа
                    material_efficiency)
                # вычисляем минимально необходимое материалов, необходимых для работ хотя-бы по одному чертежу
                bp_manuf_need_min = __industry_input if bp_manuf_need_min == 0 else min(bp_manuf_need_min, __industry_input)
                # выход готовой продукции с одного запуска по N ранов умножаем на кол-во чертежей
                __industry_input *= quantity_of_blueprints
                # считаем общее количество материалов, необходимых для работ по этом чертежу
                bp_manuf_need_all += __industry_input
            # вывод информации о ресурсе (материале)
            bpmm_tid: int = m["typeID"]
            materials_list_with_efficiency.append({
                "id": bpmm_tid,
                "q": bp_manuf_need_all,
                "qmin": bp_manuf_need_min,
            })
        return materials_list_with_efficiency


# ConveyorMaterials - набор материалов и продуктов, задействованных в производстве конвейера (всё то, что расположено
# в коробках, или рассчитано как нужды производства)
class ConveyorMaterials:
    def __init__(self,
                 # sde данные, загруженные из .converted_xxx.json файлов
                 sde_type_ids,
                 sde_bp_materials,
                 sde_market_groups,
                 # esi данные, загруженные с серверов CCP
                 corp_industry_jobs_data,
                 # списки контейнеров и станок из экземпляра контейнера
                 manufacturing_blueprint_loc_ids,
                 manufacturing_stock_loc_ids,
                 reaction_stock_loc_ids,
                 # список ресурсов, которые используются в производстве
                 manufacturing_stock_resources,
                 reaction_stock_resources):
        self.__sde_type_ids = sde_type_ids
        self.__sde_bp_materials = sde_bp_materials
        self.__sde_market_groups = sde_market_groups
        self.__corp_industry_jobs_data = corp_industry_jobs_data
        self.__manufacturing_stock_loc_ids = manufacturing_stock_loc_ids
        self.__manufacturing_blueprint_loc_ids = manufacturing_blueprint_loc_ids
        self.__reaction_stock_loc_ids = reaction_stock_loc_ids
        self.__manufacturing_stock_resources = manufacturing_stock_resources
        self.__reaction_stock_resources = reaction_stock_resources
        # подготовка списка-справочника, который будет хранить все продукты, используемые конвейером
        self.materials: typing.Dict[int, ConveyorItem] = {}

    def __del__(self):
        # уничтожаем свой список-спрвочник, остальные (не наши) не трогаем
        del self.materials

    def get(self, type_id: int) -> ConveyorItem:
        in_cache = self.materials.get(type_id)
        if in_cache is None:
            in_cache = ConveyorItem(
                type_id,
                # sde данные, загруженные из .converted_xxx.json файлов
                self.__sde_type_ids,
                self.__sde_bp_materials,
                self.__sde_market_groups,
                # esi данные, загруженные с серверов CCP
                self.__corp_industry_jobs_data,
                # списки контейнеров и станок из экземпляра контейнера
                self.__manufacturing_blueprint_loc_ids,
                self.__manufacturing_stock_loc_ids,
                self.__reaction_stock_loc_ids,
                # список ресурсов, которые используются в производстве
                self.__manufacturing_stock_resources,
                self.__reaction_stock_resources)
            self.materials[type_id] = in_cache
        return in_cache

    def load(self):
        # инициализируем (загружаем) справочники о материалах в стоке и о продуктах производства
        # списки сюда могут попадать как экземплярами list(), так и экземплярами set(), так и dict(id: val,...)
        for tids in [self.__manufacturing_stock_resources,
                     self.__reaction_stock_resources]:
            for tid in tids:
                type_id: int = tid
                if self.get(type_id) is None:
                    self.materials[type_id] = ConveyorItem(
                        type_id,
                        self.__sde_type_ids,
                        self.__sde_bp_materials,
                        self.__sde_market_groups,
                        self.__manufacturing_stock_resources,
                        self.__reaction_stock_resources)

    # выполнение расчётов достаточности материалов:
    # - materials_to_produce_with_efficiency - список [{'id':?,'q':?},...] материалов, которые требуется потратить
    # - materials_will_consumed_from_factory - признак 'M' или 'R', откуда планируется тратить материалы (в том случае,
    #   если материалы не производятся, а покупаются)
    # на выходе будут сформированы два списка:
    # - used_and_exist_materials - список [{'id':?,'q':?},...] материалов, которые отмечены зарезервированными (использ)
    # - not_enough_materials - список [{'id':?,'q':?},...] материалов, которых не хватает для производства по вх.списку
    def calc_materials_availability(
            self,
            materials_to_produce_with_efficiency,
            materials_will_consumed_from_factory: str):
        # подготовка промежуточных списков со сведениями об изменении достаточности и используемости материалов
        used_and_exist_materials = []
        not_enough_materials = []
        for m_me in materials_to_produce_with_efficiency:
            # перебор материалов, количество которых рассчитано на основании сведений о ME
            type_id: int = m_me["id"]
            need_quantity: int = m_me["q"]
            # получение сведений о материале, находящемся в справочнике конвейера
            in_cache = self.get(type_id)
            # считаем сколько материала не хватает с учётом того количества, что находится в стоке (стоках)
            if materials_will_consumed_from_factory == 'M':
                # проверяем manufacturing-сток
                in_stock_remained: int = in_cache.exist_in_manuf_stock - in_cache.reserved_in_manuf_stock
                not_available: int = 0 if in_stock_remained >= need_quantity else need_quantity - in_stock_remained
                consumed: int = need_quantity if in_stock_remained >= need_quantity else in_stock_remained
                # корректируем справочник материалов, увеличивая зарезервированное кол-во предметов этого типа
                in_cache.reserved_in_manuf_stock += need_quantity
            elif materials_will_consumed_from_factory == 'R':
                # проверяем reaction-сток
                in_stock_remained: int = in_cache.exist_in_react_stock - in_cache.reserved_in_react_stock
                not_available: int = 0 if in_stock_remained >= need_quantity else need_quantity - in_stock_remained
                consumed: int = need_quantity if in_stock_remained >= need_quantity else in_stock_remained
                # корректируем справочник материалов, увеличивая зарезервированное кол-во предметов этого типа
                in_cache.reserved_in_react_stock += need_quantity
            else:
                raise Exception('Unable to check the stock at industry station')
            # сохраняем использованное из стока кол-во материалов для производства по этому чертежу
            if consumed > 0:
                used_and_exist_materials.append({"id": type_id, "q": consumed, "w": materials_will_consumed_from_factory})
            # сохраняем недостающее кол-во материалов для производства по этому чертежу
            if not_available > 0:
                # устанавливаем, где и как именно производится данный вид продукта (не там же, где находится его сток!)
                # если это покупной материал и сведений о его производстве нет, то его закупка уже рассчитана вследствие
                # операций выполненных выше
                if in_cache.where is None:
                    not_enough_materials.append({"id": type_id, "q": not_available, "w": materials_will_consumed_from_factory})
                    continue
                #
                #remained_in_all_stocks: int = in_cache.exist_in_manuf_stock - in_cache.reserved_in_manuf_stock + \
                #                              in_cache.exist_in_react_stock - in_cache.reserved_in_react_stock
                #not_available_over_all_stocks: int = 0 if remained_in_all_stocks >= need_quantity else need_quantity - remained_in_all_stocks
                # сохраняем недостающее кол-во материалов для производства по этому чертежу
                not_enough_materials.append({"id": type_id, "q": not_available, "w": in_cache.where})
        # вывод материалов в стоке имеющихся и помеченным использованными, а также список недостающего кол-ва
        return used_and_exist_materials, not_enough_materials

    def check_possible_job_runs(self, item: ConveyorItem) -> typing.Optional[int]:
        # проверяем, можно ли произвести данный ресурс (материал)?
        if item.blueprint_type_id is None:
            return None
        # расчёт материалов по информации о чертеже с учётом ME
        # TODO: добавить авторасчёт необходимых чертежей в список конвейера
        ntier_set_of_blueprints = [{'r': item.runs_number_per_day}]
        nemlwe = item.get_materials_list_for_set_of_blueprints(
            ntier_set_of_blueprints,
            # мы не знаем с какой эффективностью будет делаться вложенная работа, наверное 10?
            # по-хорошему тут надо слазить в библиотеку чертежей...
            0 if item.is_reaction else 10,
            is_blueprint_copy=True,
            fixed_number_of_runs=None)
        # пытаемся расчитать кол-во чертежей, которое запустить с указанным кол-вом ранов
        possible_job_runs: int = 0
        # перебираем все ресурсы (материалы) чертежа
        for (idx, m) in enumerate(nemlwe):
            in_cache: ConveyorItem = self.get(m['id'])
            quantity: int = m['q']
            if item.where == 'M':
                exist_in_stock = in_cache.exist_in_manuf_stock
            elif item.where == 'R':
                exist_in_stock = in_cache.exist_in_react_stock
            else:
                exist_in_stock = 0
            # считаем минимально возможное кол-во запусков
            if idx == 0:
                possible_job_runs = floor(exist_in_stock / quantity)
            else:
                possible_job_runs = min(possible_job_runs, floor(exist_in_stock / quantity))
            # если уже выяснили, что материалов не хватает - ответ 0
            if possible_job_runs == 0:
                return 0
        return possible_job_runs

    # объединение двух списков типа ['id':?,'q':?] таким образом, чтобы в результирующий не содержал повторения по id
    # возможна работа со списками ['id':?,'q':?,'w':?] с проверкой флага 'w' в src и dst (с пом. check_where_flag)
    @staticmethod
    def calc_materials_summary(
            source_list,
            destination_list,
            check_where_flag=True):
        # выполнение расчётов достаточности материала и добавление его количества в summary-списки
        for src in source_list:
            # перебор материалов, количество которых рассчитано на основании сведений о ME
            type_id: int = src['id']
            where = src['w'] if check_where_flag else None
            # сохраняем материалы для производства в список их суммарного кол-ва
            found: bool = False
            for dst in destination_list:
                if dst['id'] != type_id:
                    continue
                if check_where_flag and dst['w'] != where:
                    continue
                dst['q'] += src['q']
                found = True
                break
            if not found:
                destination_list.append({'id': type_id, 'q': src['q']})
                if check_where_flag:
                    destination_list[len(destination_list)-1].update({'w': where})

    # расчёт материалов, необходимых на следующем уровне производства по справочным данным, имеющимся в каталоге
    # конвейера:
    # - not_enough_materials - список [{'id':?,'q':?},...] материалов, которых не хватает для производства по вх.списку
    #   см. результат работы метода calc_materials_availability
    # - next_tier_materials - список материалов для производства на следующем уровне
    # - next_tier_for_buy - список на закуп на следующем уровне (произвести нельзя)
    def get_ntier_materials_list_of_not_available(
            self,
            not_enough_materials):
        # расчёт списка материалов, предыдущего уровня вложенности (по информации о ресурсах, которых не хватает)
        next_tier_materials = []
        next_tier_for_buy = []
        for m in not_enough_materials:
            type_id: int = m['id']
            # получение сведений о материале, находящемся в справочнике конвейера
            in_cache = self.get(type_id)
            # проверяем, можно ли произвести данный ресурс (материал)?
            if in_cache.blueprint_type_id is None:
                self.calc_materials_summary([m], next_tier_for_buy, check_where_flag=False)
                continue
            # в случае, если имеем дело с реакциями, то q - это кол-во оригиналов чертежей
            # в случае, если имеем дело не с реакциями, то r - это кол-во ранов чертежа
            if in_cache.is_reaction:
                blueprints: int = ceil(m['q'] / (in_cache.products_per_single_run * in_cache.runs_number_per_day))
                ntier_set_of_blueprints = [{'r': -1, 'q': blueprints}]
                in_cache.schedule_job_launches(blueprints, in_cache.runs_number_per_day)
            else:
                runs: int = ceil(m['q'] / in_cache.products_per_single_run)
                ntier_set_of_blueprints = [{'r': runs}]
                in_cache.schedule_job_launches(1, runs)
            # расчёт материалов по информации о чертеже с учётом ME
            # TODO: добавить авторасчёт необходимых чертежей в список конвейера
            nemlwe = in_cache.get_materials_list_for_set_of_blueprints(
                ntier_set_of_blueprints,
                # мы не знаем с какой эффективностью будет делаться вложенная работа, наверное 10?
                # по-хорошему тут надо слазить в библиотеку чертежей...
                0 if in_cache.is_reaction else 10,
                is_blueprint_copy=not in_cache.is_reaction,
                fixed_number_of_runs=in_cache.runs_number_per_day if in_cache.is_reaction else None)
            # получение сведений о материалах, находящемся (или пока ещё нет) в справочнике конвейера
            for m2 in nemlwe:
                type_id2: int = m2['id']
                in_cache2 = self.get(type_id2)
                # - в том случае, если известно где будет производиться материал, добавляем его в список с w-маркером
                # - в том случае, если место производства неизвестно, то скорее всего будет запланирован его закуп с
                #   доставкой на станцию, где будет запускаться производство текущего чертежа (определяется в вызывающем
                #   методе)
                self.calc_materials_summary(
                    [{'id': type_id2, 'q': m2['q'], 'w': in_cache2.where}],  # in_cache2.where м.б. None
                    next_tier_materials,
                    check_where_flag=True)
            del nemlwe
        return next_tier_materials, next_tier_for_buy

    calc_run_times: int = 0
    calc_run_debug: bool = False

    def show_debug_list(self, prefix: str, materials):
        print("{}: {}".format(
            prefix,
            ["{} {}".format(m['q'], self.get(m['id']).name) for m in materials if m['q'] > 0]))

    def calc_not_available_materials_list(
            self,
            # список ресурсов, которые требуется произвести, в формате: ['id':?,'q':?]
            materials_summary):
        # расчёт информации по недостающим материалам
        if not materials_summary:
            return
        # набор lambda-функций, которые применяются ниже
        make_m = lambda m: {'id': m['id'], 'q': m['q']}
        # подготовка списков материалов к работе
        # noinspection PyUnusedLocal
        used_and_exist_materials = []
        # noinspection PyUnusedLocal
        not_enough_materials__initial = []
        not_enough_materials__market = []
        not_enough_materials__intermediate = []
        not_enough_materials__cycled = {'M': [], 'R': []}
        not_enough_materials__again = {'M': []}
        # проверка наличия имеющихся ресурсов с учётом запаса в стоке
        # (эта версия расчётов конвейера в качестве "старта расчёта" имеет только manufacturing-план)
        if True:
            # запускаем расчёт недостающего кол-ва материалов для производственных работ в manufacturing-станции
            (used_and_exist_materials, not_enough_materials__initial) = self.calc_materials_availability(
                materials_summary,
                'M')
            # если всех материалов в стоке достаточно, то выходим; иначе продолжаем вычислять производственные цепочки
            if not not_enough_materials__initial:
                return
            # отмечаем "стартовые" материалы в справочнике initial-флагом
            for m in not_enough_materials__initial:
                self.get(m['id']).user_data.update({'initial': True})
            # расчёт списка материалов, которых не хватает
            # - заполняем cycled-список для manufacturing-производства
            # - не трогаем initial-список для reaction-производства (все изменения в not_available и consumed
            #   уже произошли) и возможная ситуация, что продукты реакций отсутствуют в стоке, в этом случае они уже
            #   попали в initial-список с w='R' и повлияли на значения полей в ConveyorItem
            self.calc_materials_summary(
                [make_m(m) for m in not_enough_materials__initial if m['w'] == 'M'],
                not_enough_materials__cycled['M'],
                check_where_flag=False)
        # вывод отладочной информации (временная мера для отслеживания справочников)
        if self.calc_run_debug:
            self.calc_run_times += 1
            self.show_debug_list("\n\n#{}-0'tier NOT ENOUGH".format(self.calc_run_times), not_enough_materials__initial)
        # На первой итерации собираем все производственные работы и рассчитываем их потребность и возможность выполнить
        # производство с учётом имеющихся в стоке материалов. В том случае, если попадаются реакции, то откладываем их в
        # список работ Татары.
        # На второй итерации все работы на Татаре рассчитываются аналогично тому, как это делалось на предыдущем шаге,
        # но расчёт продолжается до тех пор, пока не будут спланированы вообще все работы, потому как даже зависимое
        # производство Fuel-блоков выполняется на Татаре.
        # ---
        # готовим итератор типов расчётов: 'A' - again, 'M' - manuf, 'R' - reaction
        where = 'A'
        while True:
            if where == 'A':
                where = 'M'
            elif where == 'M':
                where = 'R'
            elif where == 'R':
                break
            ntier: int = 0
            while not_enough_materials__cycled[where]:
                # Расчёт списка материалов, предыдущего уровня вложенности (по информации о ресурсах, которых не
                # хватает).
                # ---
                # Следующий метод расщепляет список not_enough_materials__cycled на:
                # - buy : для тех материалов, которые в cycled-списке не производятся, а лишь покупаются
                # - next_tier : прочие материалы, следовательно, можно произвести и новый список будет содержать
                #   из чего именно
                (next_tier, buy) = self.get_ntier_materials_list_of_not_available(
                    not_enough_materials__cycled[where])
                # сохраняем материалы, которые невозможно произвести - возможен только их закуп
                if buy:
                    if self.calc_run_debug:
                        # вывод отладочной информации (временная мера для отслеживания справочников)
                        self.show_debug_list("#{}-{}{}'tier FOR BUY".format(self.calc_run_times, ntier, where), buy)
                    self.calc_materials_summary(
                        buy,
                        not_enough_materials__market,
                        check_where_flag=False)
                # Сохраняем информацию о способе получения материалов (кол-во чертежей и запусков)
                # если материалов, которые пригодны для производства не найдено - завершаем итерации
                if not next_tier:
                    break
                # вывод отладочной информации (временная мера для отслеживания справочников)
                if self.calc_run_debug:
                    self.show_debug_list("#{}-{}{}'tier PLANNED at SOTIYO".format(self.calc_run_times, ntier+1, where), [m for m in next_tier if (m['w'] is None and where == 'M') or m['w'] == 'M'])
                    self.show_debug_list("#{}-{}{}'tier PLANNED at TATARA".format(self.calc_run_times, ntier+1, where), [m for m in next_tier if (m['w'] is None and where == 'R') or m['w'] == 'R'])
                # первые прогоны цикла лишь накапливают сведения о материалах, производство которых запланировано на
                # станции проведения реакций (Tatara)
                if where == 'M':
                    self.calc_materials_summary(
                        [make_m(m) for m in next_tier if m['w'] == 'R'],
                        not_enough_materials__cycled['R'],
                        check_where_flag=False)
                # далее подготавливаем список тех материалов, которые будут крафтиться на текущем типе станции
                next_tier__plan = [make_m(m) for m in next_tier if m['w'] is None or m['w'] == where]
                # в случае обработки reaction-списка  может быть повторно сформирован manufacturing-заказ (Fuel Blocks)
                if where == 'R':
                    manuf_again = [make_m(m) for m in next_tier if m['w'] == 'M']
                    if manuf_again:
                        self.calc_materials_summary(manuf_again, not_enough_materials__again['M'], check_where_flag=False)
                        # вывод отладочной информации (временная мера для отслеживания справочников)
                        if self.calc_run_debug:
                            self.show_debug_list("#{}-{}{}'tier AGAIN at SOTIYO".format(self.calc_run_times, ntier + 1, where), manuf_again)
                    del manuf_again
                # уничтожаем список, чтобы случайно к нему не обратиться
                del next_tier
                # uaem - used and exist materials
                # подготовка списка недостающих материалов к следующей итерации этого цикла
                (uaem, not_enough_materials__cycled[where]) = self.calc_materials_availability(
                    next_tier__plan,
                    where)
                # уничтожаем список, чтобы случайно к нему не обратиться
                del next_tier__plan
                if uaem:
                    self.calc_materials_summary(uaem, used_and_exist_materials)
                # уничтожаем ненужный список
                del uaem
                # сохраняем информацию о недостающих материалах текущего (промежуточного) уровня вложенности
                for m in not_enough_materials__cycled[where]:
                    if self.get(m['id']).blueprint_type_id is not None:
                        self.calc_materials_summary(
                            [m],
                            not_enough_materials__intermediate,
                            check_where_flag=False)
                # вывод отладочной информации (временная мера для отслеживания справочников)
                if self.calc_run_debug:
                    self.show_debug_list("#{}-{}{}'tier NOT ENOUGH SOTIYO".format(self.calc_run_times, ntier+1, where), [m for m in not_enough_materials__cycled[where] if (m['w'] is None and where == 'M') or m['w'] == 'M'])
                    self.show_debug_list("#{}-{}{}'tier NOT ENOUGH TATARA".format(self.calc_run_times, ntier+1, where), [m for m in not_enough_materials__cycled[where] if (m['w'] is None and where == 'R') or m['w'] == 'R'])
                # ---
                # переходим к следующему уровню вложенности, строим план производства для следующего
                # списка not_enough_materials__cycled
                ntier += 1
            # уничтожаем список, чтобы случайно к нему не обратиться
            del not_enough_materials__cycled[where]
            # --
            # На первом запуска цикла для reaction-производства (по собранным требованиям в cycled-списке) надо
            # зарегистрировать эти требования с помощью calc_materials_availability (этот метод для w='R' ранее
            # не выполнялся.
            if where == 'M':
                # - uaem : used and exist materials
                # - cnem : current not enough materials
                # - not_enough_materials__cycled['R'] : составлен в ходе планирования manufacturing-работ, расчёт
                #   достаточного кол-ва этих материалов надо провести на производственной станке (Сотия, а не Татара)
                # подготовка списка недостающих материалов к текущей итерации этого цикла
                (uaem, cnem) = self.calc_materials_availability(
                    not_enough_materials__cycled['R'],
                    'M')
                # сохраняем в промежуточный список материалы, которые уже есть в стоке
                if uaem:
                    self.calc_materials_summary(uaem, used_and_exist_materials)
                # если всех материалов в стоке достаточно, то выходим; иначе продолжаем вычислять
                # производственные цепочки
                if cnem:
                    # заново компонуем cycled-список для reaction-производства
                    not_enough_materials__cycled['R'] = []
                    cnem = [make_m(m) for m in cnem]
                    self.calc_materials_summary(
                        cnem,
                        not_enough_materials__cycled['R'],
                        check_where_flag=False)
                    # в этот список также войдёт содержимое initial-списка для reaction-производства, но без
                    # вызова метода calc_materials_availability, который для initial-списка ранее уже вызывался
                    if not_enough_materials__initial:
                        # возможная ситуация, когда цикл проходит цепочкой: 'M', 'R', 'A' -> 'M', 'R' и в этой точке
                        # можно оказаться повторно (исключаем подобное)
                        self.calc_materials_summary(
                            [make_m(m) for m in not_enough_materials__initial if m['w'] == 'R'],
                            not_enough_materials__cycled['R'],
                            check_where_flag=False)
                    # сохраняем информацию о недостающих материалах текущего (промежуточного) уровня вложенности
                    cnem = [m for m in cnem if self.get(m['id']).blueprint_type_id is not None]
                    if cnem:
                        self.calc_materials_summary(
                            cnem,
                            not_enough_materials__intermediate,
                            check_where_flag=False)
                # уничтожаем списки, чтобы случайно к ним не обратиться (в т.ч. более ненужный список
                # стартовых потребностей)
                del uaem
                del cnem
                not_enough_materials__initial.clear()
            # --
            # На втором запуске цикла reaction-производства могут быть снова получены материалы manufacture-производства
            # (например Fuel Blocks) надо зарегистрировать эти требования с помощью calc_materials_availability и
            # повторить итерацию с where='A'
            elif where == 'R':
                if not not_enough_materials__again['M']:
                    continue
                # - uaem : used and exist materials
                # - cnem : current not enough materials
                # - not_enough_materials__again['M'] : составлен в ходе планирования reaction-работ, расчёт
                #   достаточного кол-ва этих материалов надо провести на станке реакций (Татара, а не Сотия)
                # подготовка списка недостающих материалов к текущей итерации этого цикла
                (uaem, cnem) = self.calc_materials_availability(
                    not_enough_materials__again['M'],
                    'R')
                # сохраняем в промежуточный список материалы, которые уже есть в стоке
                if uaem:
                    self.calc_materials_summary(uaem, used_and_exist_materials)
                # если всех материалов в стоке достаточно, то выходим; иначе продолжаем вычислять
                # производственные цепочки
                if cnem:
                    # заново компонуем cycled-список для manufacture-производства (и ранее уничтоженный reaction)
                    not_enough_materials__cycled = {'M': [], 'R': []}
                    cnem = [make_m(m) for m in cnem]
                    self.calc_materials_summary(
                        cnem,
                        not_enough_materials__cycled['M'],
                        check_where_flag=False)
                    # сохраняем информацию о недостающих материалах текущего (промежуточного) уровня вложенности
                    cnem = [m for m in cnem if self.get(m['id']).blueprint_type_id is not None]
                    if cnem:
                        self.calc_materials_summary(
                            cnem,
                            not_enough_materials__intermediate,
                            check_where_flag=False)
                    # итератор цикла устанавливаем в начальную позицию where=again
                    where = 'A'
                # уничтожаем списки, чтобы случайно к ним не обратиться (в т.ч. более ненужный список
                # стартовых потребностей)
                del uaem
                del cnem
                not_enough_materials__again['M'].clear()


# ConveyorReference - долговременный справочник материала конвейера, хранится долго и накапливает информацию из
# экземпляров ConveyorMaterials и ConveyorItem
# - subtype=0 : сохранение данных материала
# - subtype=1 : сохранение данных чертежа для постройки материала
class ConveyorReference:
    def __init__(self, item: ConveyorItem, subtype: int):
        if subtype == 0:
            # код продукта
            self.type_id: int = item.type_id
            # название продукта
            self.name: str = item.name
        else:
            # код продукта
            self.type_id: int = item.blueprint_type_id
            # название продукта
            self.name: str = item.blueprint_name
            self.name: str = item.blueprint_name


# ConveyorMaterials - долговременный справочник материалов конвейера, хранится долго и накапливает информацию из
# экземпляров ConveyorMaterials и ConveyorItem
class ConveyorDictionary:
    def __init__(self):
        # подготовка списка-справочника, который будет хранить все продукты, используемые конвейером
        self.materials: typing.Dict[int, ConveyorReference] = {}

    def __del__(self):
        # уничтожаем свой список-справочник, остальные (не наши) не трогаем
        del self.materials

    def get(self, type_id: int) -> ConveyorReference:
        return self.materials.get(type_id)

    def load(self, conveyor_materials: ConveyorMaterials):
        # инициализируем (загружаем) справочники о материалах
        type_ids = conveyor_materials.materials.keys()
        for type_id in type_ids:
            in_ref: ConveyorReference = self.materials.get(type_id)
            if in_ref is not None:
                continue
            in_cache: ConveyorItem = conveyor_materials.get(type_id)
            self.materials[type_id] = ConveyorReference(in_cache, 0)
            if in_cache.blueprint_type_id is not None:
                self.materials[in_cache.blueprint_type_id] = ConveyorReference(in_cache, 1)
