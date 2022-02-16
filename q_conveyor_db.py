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
    print("\nConveyor v{}-db done".format(__version__))

if __name__ == "__main__":
    main()
