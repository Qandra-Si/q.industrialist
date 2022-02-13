""" Q.Conveyor (desktop/mobile)

Prerequisites:
    * Have a Python 3 environment available to you (possibly by using a
      virtual environment: https://virtualenv.pypa.io/en/stable/).
    * Run pip install -r requirements.txt with this directory as your root.

    * Copy q_industrialist_settings.py.template into q_industrialist_settings.py and
      mood for your needs.
    * Copy q_conveyor_settings.py.template into q_conveyor_settings.py and
      mood for your needs.
    * Create an SSO application at developers.eveonline.com with the scopes
      from g_client_scope list declared in q_industrialist_settings.py and the
      callback URL "https://localhost/callback/".
      Note: never use localhost as a callback in released applications.

To run this example, make sure you have completed the prerequisites and then
run the following command from this directory as the root:

$ chcp 65001 & @rem on Windows only!
$ python eve_sde_tools.py --cache_dir=~/.q_industrialist
$ python q_conveyor.py --pilot="Qandra Si" --online --cache_dir=~/.q_industrialist

Requires application scopes:
    * esi-industry.read_corporation_jobs.v1 - Requires role(s): Factory_Manager
    * esi-assets.read_corporation_assets.v1 - Requires role(s): Director
    * esi-corporations.read_blueprints.v1 - Requires role(s): Director
"""
import typing
import re

import console_app
import q_industrialist_settings
import q_conveyor_settings

import postgresql_interface as db

from __init__ import __version__


class ConveyorSettings:
    def __init__(self):
        # параметры работы конвейера
        self.corporation_id: int = -1
        self.fixed_number_of_runs: typing.Optional[int] = None
        self.same_stock_container: bool = False
        self.activities: typing.List[str] = ['manufacturing']
        self.conveyor_with_reactions: bool = False
        # идентификаторы контейнеров с чертежами, со стоком, с формулами, исключённых из поиска и т.п.
        self.containers_blueprints: typing.List[int] = []
        self.containers_stock: typing.List[int] = []
        self.containers_exclude: typing.List[int] = []
        self.containers_react_formulas: typing.List[int] = []
        self.containers_react_stock: typing.List[int] = []
        self.manufacturing_groups: typing.Optional[typing.List[int]] = []


def main():
    # работа с параметрами командной строки, получение настроек запуска программы
    argv_prms = console_app.get_argv_prms(['corporation='])

    if not argv_prms["corporation"]:
        console_app.print_version_screen()
        console_app.print_help_screen(0)
        return

    qidb: db.QIndustrialistDatabase = db.QIndustrialistDatabase("conveyor", debug=argv_prms.get("verbose_mode", False))
    qidb.connect(q_industrialist_settings.g_database)
    qit: db.QSwaggerTranslator = db.QSwaggerTranslator(qidb)
    qid: db.QSwaggerDictionary = db.QSwaggerDictionary(qit)
    # загрузка справочников
    qid.load_market_groups()
    qid.load_published_type_ids()
    qid.load_blueprints()
    # загрузка информации, связанной с корпорациями
    for corporation_name in argv_prms['corporation']:
        # публичные сведения (пилоты, структуры, станции, корпорации)
        corporation: db.QSwaggerCorporation = qid.load_corporation(corporation_name)
        # загрузка корпоративных ассетов
        qid.load_corporation_assets(corporation, load_unknown_type_assets=True, load_asseted_blueprints=False)
        qid.load_corporation_blueprints(corporation, load_unknown_type_blueprints=True)
        qid.load_corporation_industry_jobs(corporation, load_unknown_type_blueprints=True)
        """
        for job in corporation.industry_jobs.values():
            if not job.installer.character_name or not job.blueprint_type or not job.product_type or \
               not job.facility or not job.blueprint_location or not job.output_location:
                print("{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
                    job.job_id,
                    job.installer.character_name if job.installer else '?',
                    job.blueprint_type.blueprint_type.name if job.blueprint_type else '?',
                    job.product_type.name if job.product_type else '?',
                    job.blueprint_location.name if job.blueprint_location else '?',
                    job.output_location.name if job.output_location else '?',
                    job.facility.station_name if job.facility else '?'))
        """
    qid.disconnect_from_translator()
    del qit
    del qidb

    # следуем по загруженным данным и собираем входные данные (настройки) запуска алгоритма конвейера
    settings_of_conveyors: typing.List[ConveyorSettings] = []
    for entity in q_conveyor_settings.g_entities:
        # пропускаем отключенные группы настроек (остались для архива?)
        if not entity.get('enabled', False) or not entity.get('conveyors'):
            continue
        # собираем список корпораций к которым относятся настройки
        corporation_name: str = entity.get('corporation')
        if corporation_name:
            corporation: db.QSwaggerCorporation = qid.get_corporation_by_name(corporation_name)
            if not corporation:
                continue
            corporation_ids: typing.List[int] = [corporation.corporation_id]
        else:
            corporation_ids: typing.List[int] = [corporation_id for corporation_id in qid.corporations.keys()]
        # собираем списки контейнеров, к которым относятся настройки
        for conveyor in entity['conveyors']:
            # пропускаем некорректные настройки (не зависят от корпорации, просто правильность синтаксиса настроек)
            if not conveyor.get('blueprints'):
                continue
            if conveyor.get('reactions') and not conveyor['reactions'].get('formulas'):
                continue
            # собираем список корпоративных контейнеров по указанным названиям
            for corporation_id in corporation_ids:
                corporation = qid.get_corporation(corporation_id)
                # инициализируем настройки запуска конвейера
                settings: ConveyorSettings = ConveyorSettings()
                settings.corporation_id = corporation_id
                # читаем настройки производственной активности
                settings.fixed_number_of_runs = conveyor.get('fixed_number_of_runs', None)
                settings.same_stock_container = conveyor.get('same_stock_container', True)
                settings.activities = conveyor.get('activities', ['manufacturing'])
                settings.conveyor_with_reactions = conveyor.get('reactions', False)
                # получаем информацию по реакциям (если включены)
                if settings.conveyor_with_reactions:
                    settings.manufacturing_groups = conveyor['reactions'].get('manufacturing_groups', [])
                for container_id in corporation.container_ids:
                    container: db.QSwaggerCorporationAssetsItem = corporation.assets.get(container_id)
                    if not container:
                        continue
                    container_name: str = container.name
                    if not container_name:
                        continue
                    # превращаем названия (шаблоны названий) в номера контейнеров
                    if next((1 for tmplt in conveyor['blueprints'] if re.search(tmplt, container_name)), None):
                        settings.containers_blueprints.append(container_id)
                        if settings.same_stock_container:
                            settings.containers_stock.append(container_id)
                    if not settings.same_stock_container:
                        if next((1 for tmplt in conveyor['stock'] if re.search(tmplt, container_name)), None):
                            settings.containers_blueprints.append(container_id)
                    # получаем информацию по реакциям (если включены)
                    if settings.conveyor_with_reactions:
                        if next((1 for tmplt in conveyor['reactions']['formulas'] if re.search(tmplt, container_name)), None):
                            settings.containers_react_formulas.append(container_id)
                        if 'stock' in conveyor['reactions']:
                            if next((1 for tmplt in conveyor['reactions']['stock'] if re.search(tmplt, container_name)), None):
                                settings.containers_react_stock.append(container_id)
                # если в этой корпорации не найдены основные параметры (контейнеры по названиям, то пропускаем корпу)
                if not settings.containers_blueprints:
                    continue
                # сохраняем полученные настройки, обрабатывать будем потом
                settings_of_conveyors.append(settings)
    # вывод на экран того, что получилось
    for (idx, s) in enumerate(settings_of_conveyors):
        corporation: db.QSwaggerCorporation = qid.get_corporation(s.corporation_id)
        if idx > 0:
            print()
        print('corporation: ', corporation.corporation_name)
        print('activities:  ', s.activities)
        print('blueprints:  ', [corporation.assets.get(x).name for x in s.containers_blueprints])
        print('stock:       ', [corporation.assets.get(x).name for x in s.containers_stock])
        print('exclude:     ', [corporation.assets.get(x).name for x in s.containers_exclude])
        if s.fixed_number_of_runs is not None:
            print('fixed runs:  ', s.fixed_number_of_runs)
        if s.conveyor_with_reactions:
            print('formulas:    ', [corporation.assets.get(x).name for x in s.containers_react_formulas])
            print('react stock: ', [corporation.assets.get(x).name for x in s.containers_react_stock])
    # ---
    del qid

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nConveyor v{} done".format(__version__))


"""
    sde_type_ids = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "typeIDs")
    sde_inv_names = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "invNames")
    sde_inv_items = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "invItems")
    sde_market_groups = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "marketGroups")
    sde_bp_materials = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "blueprints")

    # удаление из списка чертежей тех, которые не published (надо соединить typeIDs и blueprints, отбросив часть)
    for t in [t for t in sde_type_ids if t in sde_bp_materials.keys() and sde_type_ids[t].get('published')==False]:
        del sde_bp_materials[t]
    # индексация списка модулей и ресурсов, которые ИСПОЛЬЗУЮТСЯ в производстве
    materials_for_bps = set(eve_sde_tools.get_materials_for_blueprints(sde_bp_materials))
    research_materials_for_bps = set(eve_sde_tools.get_research_materials_for_blueprints(sde_bp_materials))
    # индексация списка продуктов, которые ПОЯВЛЯЮТСЯ в результате производства
    products_for_bps = set(eve_sde_tools.get_products_for_blueprints(sde_bp_materials, activity="manufacturing"))
    reaction_products_for_bps = set(eve_sde_tools.get_products_for_blueprints(sde_bp_materials, activity="reaction"))

    conveyor_data = []
    for pilot_name in argv_prms["character_names"]:
        # настройка Eve Online ESI Swagger interface
        auth = esi.EveESIAuth(
            '{}/auth_cache'.format(argv_prms["workspace_cache_files_dir"]),
            debug=True)
        client = esi.EveESIClient(
            auth,
            keep_alive=True,
            debug=argv_prms["verbose_mode"],
            logger=True,
            user_agent='Q.Industrialist v{ver}'.format(ver=__version__))
        interface = esi.EveOnlineInterface(
            client,
            q_industrialist_settings.g_client_scope,
            cache_dir='{}/esi_cache'.format(argv_prms["workspace_cache_files_dir"]),
            offline_mode=argv_prms["offline_mode"])

        authz = interface.authenticate(pilot_name)
        character_id = authz["character_id"]
        character_name = authz["character_name"]

        # Public information about a character
        character_data = interface.get_esi_data(
            "characters/{}/".format(character_id),
            fully_trust_cache=True)
        # Public information about a corporation
        corporation_data = interface.get_esi_data(
            "corporations/{}/".format(character_data["corporation_id"]),
            fully_trust_cache=True)

        corporation_id = character_data["corporation_id"]
        corporation_name = corporation_data["name"]
        print("\n{} is from '{}' corporation".format(character_name, corporation_name))
        sys.stdout.flush()

        # Requires role(s): Director
        corp_assets_data = interface.get_esi_paged_data(
            "corporations/{}/assets/".format(corporation_id))
        print("\n'{}' corporation has {} assets".format(corporation_name, len(corp_assets_data)))
        sys.stdout.flush()

        # Requires role(s): Director
        corp_blueprints_data = interface.get_esi_paged_data(
            "corporations/{}/blueprints/".format(corporation_id))
        corp_blueprints_data_len = len(corp_blueprints_data)
        print("\n'{}' corporation has {} blueprints".format(corporation_name, corp_blueprints_data_len))
        sys.stdout.flush()

        # Requires role(s): Factory_Manager
        corp_industry_jobs_data = interface.get_esi_paged_data(
            "corporations/{}/industry/jobs/".format(corporation_id))
        print("\n'{}' corporation has {} industry jobs".format(corporation_name, len(corp_industry_jobs_data)))
        sys.stdout.flush()

        # Получение названий контейнеров, станций, и т.п. - всё что переименовывается ingame
        corp_ass_named_ids = eve_esi_tools.get_assets_named_ids(corp_assets_data)
        # Requires role(s): Director
        corp_ass_names_data = interface.get_esi_piece_data(
            "corporations/{}/assets/names/".format(corporation_id),
            corp_ass_named_ids)
        print("\n'{}' corporation has {} custom asset's names".format(corporation_name, len(corp_ass_names_data)))
        sys.stdout.flush()
        del corp_ass_named_ids

        # Построение иерархических списков БПО и БПЦ, хранящихся в корпоративных ангарах
        corp_bp_loc_data = eve_esi_tools.get_corp_bp_loc_data(corp_blueprints_data, corp_industry_jobs_data)
        eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_bp_loc_data", corp_bp_loc_data)

        del corp_blueprints_data

        # Построение списка модулей и ресуров, которые имеются в распоряжении корпорации и
        # которые предназначены для использования в чертежах
        corp_ass_loc_data = eve_esi_tools.get_corp_ass_loc_data(corp_assets_data, containers_filter=None)
        eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_ass_loc_data", corp_ass_loc_data)

        # Поиск тех станций, которые не принадлежат корпорации (на них имеется офис, но самой станции в ассетах нет)
        foreign_structures_data = {}
        foreign_structures_ids = eve_esi_tools.get_foreign_structures_ids(corp_assets_data)
        foreign_structures_forbidden_ids = []
        if len(foreign_structures_ids) > 0:
            # Requires: access token
            for structure_id in foreign_structures_ids:
                try:
                    universe_structure_data = interface.get_esi_data(
                        "universe/structures/{}/".format(structure_id),
                        fully_trust_cache=True)
                    foreign_structures_data.update({str(structure_id): universe_structure_data})
                except requests.exceptions.HTTPError as err:
                    status_code = err.response.status_code
                    if status_code == 403:  # это нормально, что часть структур со временем могут оказаться Forbidden
                        foreign_structures_forbidden_ids.append(structure_id)
                    else:
                        raise
                except:
                    print(sys.exc_info())
                    raise
        print("\n'{}' corporation has offices in {} foreign stations".format(corporation_name, len(foreign_structures_data)))
        if len(foreign_structures_forbidden_ids) > 0:
            print("\n'{}' corporation has offices in {} forbidden stations : {}".format(corporation_name, len(foreign_structures_forbidden_ids), foreign_structures_forbidden_ids))
        sys.stdout.flush()

        # Построение дерева ассетов, с узлави в роли станций и систем, и листьями в роли хранящихся
        # элементов, в виде:
        # { location1: {items:[item1,item2,...],type_id,location_id},
        #   location2: {items:[item3],type_id} }
        corp_assets_tree = eve_esi_tools.get_assets_tree(corp_assets_data, foreign_structures_data, sde_inv_items, virtual_hierarchy_by_corpsag=False)
        eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_assets_tree", corp_assets_tree)

        # Поиск контейнеров, которые участвуют в производстве
        corp_conveyour_entities = []
        for (__manuf_dict_num, __manuf_dict) in enumerate(q_conveyor_settings.g_manufacturing):
            # находим контейнеры по заданным названиям
            blueprint_loc_ids = []
            for tmplt in __manuf_dict["conveyor_container_names"]:
                blueprint_loc_ids.extend([n["item_id"] for n in corp_ass_names_data if re.search(tmplt, n['name'])])
            # кешируем признак того, что контейнеры являются стоком материалов
            same_stock_container = __manuf_dict.get("same_stock_container", False)
            fixed_number_of_runs = __manuf_dict.get("fixed_number_of_runs", None)
            manufacturing_activities = __manuf_dict.get("manufacturing_activities", ["manufacturing"])
            # находим станцию, где расположены найденные контейнеры
            for id in blueprint_loc_ids:
                __loc_dict = eve_esi_tools.get_universe_location_by_item(
                    id,
                    sde_inv_names,
                    sde_inv_items,
                    corp_assets_tree,
                    corp_ass_names_data,
                    foreign_structures_data
                )
                if not ("station_id" in __loc_dict):
                    continue
                __station_id = __loc_dict["station_id"]
                __conveyor_entity = next((id for id in corp_conveyour_entities if (id["station_id"] == __station_id) and (id["num"] == __manuf_dict_num)), None)
                if __conveyor_entity is None:
                    __conveyor_entity = __loc_dict
                    __conveyor_entity.update({
                        "containers": [],
                        "stock": [],
                        "react_stock": [],
                        "exclude": [],
                        "num": __manuf_dict_num,
                    })
                    corp_conveyour_entities.append(__conveyor_entity)
                    # на этой же станции находим контейнер со стоком материалов
                    if same_stock_container:
                        __conveyor_entity["stock"].append({"id": id, "name": next((n["name"] for n in corp_ass_names_data if n['item_id'] == id), None)})
                    else:
                        for tmplt in __manuf_dict["stock_container_names"]:
                            __stock_ids = [n["item_id"] for n in corp_ass_names_data if re.search(tmplt, n['name'])]
                            for __stock_id in __stock_ids:
                                __stock_loc_dict = eve_esi_tools.get_universe_location_by_item(
                                    __stock_id,
                                    sde_inv_names,
                                    sde_inv_items,
                                    corp_assets_tree,
                                    corp_ass_names_data,
                                    foreign_structures_data
                                )
                                if ("station_id" in __stock_loc_dict) and (__station_id == __stock_loc_dict["station_id"]):
                                    __conveyor_entity["stock"].append({"id": __stock_id, "name": next((n["name"] for n in corp_ass_names_data if n['item_id'] == __stock_id), None)})
                    # на этой же станции находим контейнеры, из которых нельзя доставать чертежи для производства материалов
                    for tmplt in __manuf_dict["exclude_container_names"]:
                        __exclude_ids = [n["item_id"] for n in corp_ass_names_data if re.search(tmplt, n['name'])]
                        for __exclude_id in __exclude_ids:
                            __stock_loc_dict = eve_esi_tools.get_universe_location_by_item(
                                __exclude_id,
                                sde_inv_names,
                                sde_inv_items,
                                corp_assets_tree,
                                corp_ass_names_data,
                                foreign_structures_data
                            )
                            if ("station_id" in __stock_loc_dict) and (__station_id == __stock_loc_dict["station_id"]):
                                __conveyor_entity["exclude"].append({"id": __exclude_id, "name": next((n["name"] for n in corp_ass_names_data if n['item_id'] == __exclude_id), None)})
                    # на любой другой станции находим контейнер, в котором находится сток для нужд конвейера, но пока
                    # ещё на нужную станцию (например с Татары на Сотию)
                    for tmplt in __manuf_dict.get("reaction_stock_containers", []):
                        rs_ids = [(n["item_id"], n['name']) for n in corp_ass_names_data if re.search(tmplt, n['name'])]
                        for (rs_id, rs_name) in rs_ids:
                            rs_loc_dict = eve_esi_tools.get_universe_location_by_item(
                                rs_id,
                                sde_inv_names,
                                sde_inv_items,
                                corp_assets_tree,
                                corp_ass_names_data,
                                foreign_structures_data
                            )
                            if "station_id" in rs_loc_dict:
                                __conveyor_entity["react_stock"].append({"id": rs_id, "name": rs_name, "loc": rs_loc_dict})
                        del rs_ids
                # добавляем к текущей станции контейнер с чертежами
                # добаляем в свойства контейнера фиксированное кол-во запусков чертежей из настроек
                __conveyor_entity["containers"].append({
                    "id": id,
                    "name": next((n["name"] for n in corp_ass_names_data if n['item_id'] == id), None),
                    "fixed_number_of_runs": fixed_number_of_runs,
                    "manufacturing_activities": manufacturing_activities,
                })

        conveyor_data.append({
            "corporation_id": corporation_id,
            "corporation_name": corporation_name,
            "corp_conveyour_entities": corp_conveyour_entities,
            # esi данные, загруженные с серверов CCP
            "corp_industry_jobs_data": corp_industry_jobs_data,
            "corp_assets_data": corp_assets_data,
            "corp_bp_quantity": corp_blueprints_data_len,
            # данные, полученные в результате анализа и перекомпоновки входных списков
            "corp_ass_loc_data": corp_ass_loc_data,
            "corp_bp_loc_data": corp_bp_loc_data,
            "corp_assets_tree": corp_assets_tree,
        })
        del corp_conveyour_entities
        del corp_industry_jobs_data
        del corp_ass_names_data
        del corp_ass_loc_data
        del corp_bp_loc_data
        del corp_assets_tree

    # перечисляем станции и контейнеры, которые были найдены
    print('\nFound conveyor containters and station ids...')
    for cd in conveyor_data:
        print(' corporation = {}'.format(cd["corporation_name"]))
        for ce in cd["corp_conveyour_entities"]:
            print('   {} = {}'.format(ce["station_id"], ce["station"]))
            print('     containers with blueprints:')
            for cec in ce["containers"]:
                print('       {} = {}'.format(cec["id"], cec["name"]))
            print('     stock containers:')
            for ces in ce["stock"]:
                print('       {} = {}'.format(ces["id"], ces["name"]))
            if ce["react_stock"]:
                print('     reaction stock containers:')
                for cess in ce["react_stock"]:
                    print('       {} = {}'.format(cess["loc"]["station_id"], cess["loc"]["station"]))
                    print('         {} = {}'.format(cess["id"], cess["name"]))
            if ce["containers"]:
                print('     exclude containers:')
                for cee in ce["exclude"]:
                    print('       {} = {}'.format(cee["id"], cee["name"]))
    sys.stdout.flush()

    print("\nBuilding report...")
    sys.stdout.flush()

    del sde_inv_names
    del sde_inv_items

    render_html_conveyor.dump_conveyor_into_report(
        # путь, где будет сохранён отчёт
        argv_prms["workspace_cache_files_dir"],
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        materials_for_bps,
        research_materials_for_bps,
        products_for_bps,
        reaction_products_for_bps,
        # настройки генерации отчёта
        # esi данные, загруженные с серверов CCP
        # данные, полученные в результате анализа и перекомпоновки входных списков
        conveyor_data
    )
"""

if __name__ == "__main__":
    main()
