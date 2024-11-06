""" Q.Universe Structures (desktop/mobile)

Prerequisites:
    * Have a Python 3 environment available to you (possibly by using a
      virtual environment: https://virtualenv.pypa.io/en/stable/).
    * Run pip install -r requirements.txt --user with this directory.
      or
      Run pip install -r requirements.txt with this directory as your root.

    * Copy q_industrialist_settings.py.template into q_industrialist_settings.py and
      mood for your needs.
    * Copy q_blueprints_settings.py.template into q_blueprints_settings.py and
      mood for your needs.
    * Create an SSO application at developers.eveonline.com with the scopes
      from g_client_scope list declared in q_industrialist_settings.py and the
      callback URL "https://localhost/callback/".
      Note: never use localhost as a callback in released applications.

To run this example, make sure you have completed the prerequisites and then
run the following command from this directory:

$ chcp 65001 & @rem on Windows only!
$ python eve_sde_tools.py --cache_dir=~/.q_industrialist
$ python q_dictionaries.py --category=all --cache_dir=~/.q_industrialist
$ python q_universe_preloader.py --category=all --pilot="Qandra Si" --pilot="Your Name" --online --cache_dir=~/.q_industrialist

Attention, the first launch takes about 4 hours of work!
Usually single launch for one corporation takes 1.5-2 minutes, but in case of a long
downtime, it will take up to 3-4 minutes for each very active corporation.
Loading market prices for The Forge region will require about 1GB of memory.

To refresh blueprints you need to feel market_hubs and market_routes tables and then
run the following command from this directory:

$ chcp 65001 & @rem on Windows only!
$ python q_dictionaries.py --category=conveyor_formulas --cache_dir=~/.q_industrialist
$ python q_universe_preloader.py --category=trade_hubs --category=industry_systems --category=market_prices --category=conveyor_formulas --pilot="Your Name" --online --cache_dir=~/.q_industrialist

Required application scopes:
    * esi-universe.read_structures.v1 - Requires: access token
    * esi-corporations.read_structures.v1 - Requires role(s): Station_Manager
    * esi-assets.read_corporation_assets.v1 - Requires role(s): Director
    * esi-corporations.read_blueprints.v1 - Requires role(s): Director
    * esi-industry.read_corporation_jobs.v1 - Requires role(s): Factory_Manager
    * esi-wallet.read_corporation_wallets.v1 - Requires one of: Accountant, Junior_Accountant
"""
import sys
import typing

import q_industrialist_settings
import eve_db_tools
import console_app
import postgresql_interface as db
# from memory_profiler import memory_usage


def main():
    possible_categories = [
        # запуск скрипта со вводом всех возможных данных в БД (крайне не рекомендуется
        # запускать в этом режиме без необходимости, т.к. ряд категорий актуализируется
        # ОЧЕНЬ ДОЛГО, часами и потому может пострадать оперативность ввода прочих данных)
        'all',
        # актуализация PUBLIC сведений о вселенной, таких как:
        # * public structures, появляющихся время от времени во вселенной - БЫСТРО
        # * public prices на trade hubs, например Jita-4-4 - МЕДЛЕННО
        # * public trade goods (ids), т.е. предметов добавленных во вселенную - раз в день ОЧЕНЬ МЕДЛЕННО
        # * markets region history, т.е. рыночных цен по регионам - раз в день ОЧЕНЬ МЕДЛЕННО
        'public',
        # актуализация рыночных цен на товары во вселенной, в частности:
        # * цен в market-хабах по заданным настройках - скорость зависит от региона, но в частности Jita ДОЛГО
        # * цен на структурах по заданным настройкам - доступ зависит от корпорации, если альянс оч.крупный то НЕ БЫСТРО
        'trade_hubs',
        # актуализация ассетов корпорации, а также её прочего имущества (структур в спейсе), ордеров и работ:
        'assets',
        'blueprints',
        'industry',
        'finances',
        'orders',
        # актуализация исторических рыночных цен по вселенной, т.н. markets region history - ОЧЕНЬ МЕДЛЕННО
        'trade_history',
        # сведения о trade goods (ids), т.е. предметах добавленных во вселенную - раз в день ОЧЕНЬ МЕДЛЕННО
        'goods',
        # актуализация производственных индексов по всем солнечным системам вселенной - БЫСТРО (обновляется редко)
        'industry_systems',
        # актуализация adjusted и average цен на материалы в вселенной - НЕ БЫСТРО (в EVE Online обновляется по четвергам)
        'market_prices',
        # пересчёт кеша таблиц для conveyor-формул (выборка данных по стоимости производства различных предметов)
        'conveyor_formulas',
        # ----- ----- ----- ----- -----
        # предустановка для набора категорий, например категория 'corporation' обуславливает загрузку 'assets',
        # 'blueprints', и т.п. то есть всех тех данных, которые относятся именно к корпорации (не цен по вселенной)
        'corporation',
        # предустановка для категорий и действий, которые выполняются медленно, и выполнение которых желательно либо
        # откладывать, либо запускать "в фоне"
        'rare',
        # предустановка для категорий и действий, которые выполняются крайне медленно, и выполнение которых желательно
        # запускать раз в сутки (либо однократно при обновлении набора данных в sde.zip от CCPшников)
        'once',
    ]

    # работа с параметрами командной строки, получение настроек запуска программы, как то: работа в offline-режиме,
    # имя пилота ранее зарегистрированного и для которого имеется аутентификационный токен, регистрация нового и т.д.
    argv_prms = console_app.get_argv_prms(['category='])

    # проверка названий категорий, они должны относится к ограниченному списку
    wrong_categories = [c for c in argv_prms["category"] if c not in possible_categories]
    if wrong_categories:
        print("Unsupported category: {}".format(wrong_categories))
        return
    del wrong_categories
    del possible_categories
    # подготовка набора категорий, заданных пользователем к использованию
    categories = set(argv_prms['category'])

    # подключаемся к БД для сохранения данных, которые будут получены из ESI Swagger Interface
    dbtools = eve_db_tools.QDatabaseTools(
        "universe_structures",
        q_industrialist_settings.g_client_scope,
        q_industrialist_settings.g_database,
        debug=argv_prms['verbose_mode']
    )

    first_time: bool = True
    conveyor_formulas_jobs_refresh: bool = False
    conveyor_formulas_purchase_refresh: bool = False
    conveyor_formulas_delivery_refresh: bool = False
    pilot_max_num: int = len(argv_prms["character_names"])

    # пытаемся в список g_market_hubs добавить станции из БД, в которых ведётся торговля (trade_hub в настройках
    # является non archive)
    active_market_hubs: typing.List[typing.Dict[str, typing.Union[int, str, typing.List[typing.Union[str, db.QSwaggerInterface.MarketHub]]]]] = \
        q_industrialist_settings.g_market_hubs
    active_market_structures: typing.List[typing.Union[typing.Dict[str, typing.Union[int, str]]]] = \
        q_industrialist_settings.g_market_structures
    # ---
    for hub in dbtools.active_market_hubs:
        # настройки загруженные из базы данных имеют выше приоритет, чем заданные в q_industrialist_settings (постепенно
        # пытаюсь отказаться от устаревающей практики ввода настроек в _settings файлах), в связи с чем, если в БД уже
        # есть станция, которая либо активная, либо архивная, то она либо добавляется в список для загрузки цен, либо
        # удаляется оттуда
        if hub.is_nonuser_station:
            region_dict: typing.Dict[str, typing.Union[int, str, typing.List[str]]] = \
                next((_ for _ in active_market_hubs if _['region'] == hub.region), None)
            if not region_dict:
                if hub.active:
                    active_market_hubs.append({
                        'region': hub.region,
                        'region_id': hub.region_id,
                        'trade_hubs': [hub.trade_hub]})
            else:
                region_dict.update({'region_id': hub.region_id})
                region_stations: typing.List[typing.Union[str, db.QSwaggerInterface.MarketHub]] = region_dict['trade_hubs']
                if hub.trade_hub not in region_stations:
                    if hub.active:
                        region_stations.append(hub)
                else:
                    if hub.archive:
                        region_stations.remove(hub.trade_hub)
                    elif hub.active:
                        region_stations.remove(hub.trade_hub)
                        region_stations.append(hub)
        # аналогичные действия выполняем для структур, где настройки заданные в БД также имеют приоритет выше, чем в
        # файле _settings
        if hub.is_user_structure:
            structure_dict: typing.Dict[str, typing.Union[int, str]] = \
                next((_ for _ in active_market_structures if _['structure_id'] == hub.trade_hub_id), None)
            if not structure_dict:
                if hub.active:
                    active_market_structures.append({
                        'structure_id': hub.trade_hub_id,
                        'corporation_name': hub.trader_corporation})
            else:
                if hub.active:
                    structure_dict['corporation_name'] = hub.trader_corporation
                elif hub.archive:
                    active_market_structures.remove(structure_dict)

    for pilot_num, pilot_name in enumerate(argv_prms["character_names"], start=1):
        # настройка Eve Online ESI Swagger interface
        authz = dbtools.auth_pilot_by_name(
            pilot_name,
            argv_prms["offline_mode"],
            argv_prms["workspace_cache_files_dir"],
            q_industrialist_settings.g_client_id,  # токен приложения Q.Industrialist
            q_industrialist_settings.g_client_restrict_tls13
        )
        character_id = authz["character_id"]
        character_name = authz["character_name"]

        # Public information about a character
        character_data = dbtools.actualize_character(character_id, True)
        # Public information about a corporation
        corporation_id = character_data["corporation_id"]
        corporation_data = dbtools.actualize_corporation(corporation_id, True)

        corporation_name = corporation_data["name"]
        print("\n{} is from '{}' corporation".format(character_name, corporation_name))
        sys.stdout.flush()

        last_time: bool = pilot_num == pilot_max_num
        if first_time:
            first_time = False

            # один раз для первого пилота (его аутентификационного токена) читаем данные
            # с серверов CCP по публичным структурам - обычно быстро
            if categories & {'all', 'public', 'rare'}:
                # Requires: access token
                universe_structures_stat = dbtools.actualize_universe_structures()
                if universe_structures_stat is None:
                    print("Universe public structures has no updates\n")
                else:
                    print("{} new of {} public structures found in the universe\n".
                          format(universe_structures_stat[1], universe_structures_stat[0]))
                sys.stdout.flush()

            # в зависимости от заданных натроек загружаем цены в регионах, фильтруем по
            # market-хабам и пишем в БД
            if categories & {'all', 'public', 'rare', 'industry_systems'}:
                # Requires: public access
                industry_systems_updated = dbtools.actualize_industry_systems()
                print("Industry indicies has {} updates\n".format('no' if industry_systems_updated is None else industry_systems_updated))
                sys.stdout.flush()
                # готовим признаки пересчёта conveyor-формул
                if industry_systems_updated:
                    # industry system cost index используется в расчёте стоимости работ, возможно индекс поменялся в
                    # наших производственных системах?
                    conveyor_formulas_jobs_refresh = True

            # загружаем цены во вселенной: производственные adjusted и торговые averaged
            if categories & {'all', 'public', 'rare', 'market_prices'}:
                # Requires: public access
                markets_prices_updated: typing.Optional[typing.Tuple[int, int]] = dbtools.actualize_markets_prices()
                if markets_prices_updated is None:
                    print("Markets prices has no updates\n")
                else:
                    average_price_num: int = markets_prices_updated[0]
                    adjusted_price_num: int = markets_prices_updated[1]
                    print(f"Markets prices has {average_price_num} average updates, {adjusted_price_num} adjusted updates\n")
                    # готовим признаки пересчёта conveyor-формул
                    if average_price_num:
                        # average price используется в расчёте materials purchase (используется тогда и только тогда,
                        # когда цена в jita по buy неизвестна, а также неизвестна и jite sell цена), так что непонятно
                        # сколько стоит материал? ...может он вообще по контрактам продаётся?!
                        conveyor_formulas_purchase_refresh = True
                    if adjusted_price_num:
                        # adjusted price используется в estimated_items_value при расчёте job_cost
                        conveyor_formulas_jobs_refresh = True
                sys.stdout.flush()

            # в зависимости от заданных настроек загружаем цены в регионах, фильтруем по
            # market-хабам и пишем в БД
            if categories & {'all', 'public', 'rare', 'trade_hubs'}:
                # Requires: public access
                for region in active_market_hubs:
                    found_market_goods, updated_market_orders = dbtools.actualize_trade_hubs_market_orders(
                        region['region'],
                        # в настройках заданных пользователем это строковый параметр - название станции (м.б. загружен
                        # из БД вместе с настройками активных торговых хабов, тогда это будет объект с названием и
                        # кодом станции)
                        region['trade_hubs'],
                        # в настройках заданных пользователем это необязательный параметр (м.б. загружен из БД вместе
                        # с настройками активных торговых хабов)
                        region.get('region_id'))
                    print("'{}' market has {} goods and {} order updates\n".format(
                        region['region'],
                        'not new' if found_market_goods is None else found_market_goods,
                        'no' if updated_market_orders is None else updated_market_orders))
                    sys.stdout.flush()
                    # готовим признаки пересчёта conveyor-формул
                    if updated_market_orders:
                        if region['region'] == "The Forge":
                            # цены региона The Forge (там где расположена Jita 4-4 используются в расчёте materials
                            # purchase
                            conveyor_formulas_purchase_refresh = True

                # Requires: public access
                for structure in active_market_structures:
                    if structure.get("corporation_name", None) is None:
                        found_market_goods, updated_market_orders = dbtools.actualize_markets_structures_prices(structure.get("structure_id"))
                        print("'{}' market has {} goods and {} order updates\n".format(
                            structure.get("structure_id"),
                            'not new' if found_market_goods is None else found_market_goods,
                            'no' if updated_market_orders is None else updated_market_orders))
                        sys.stdout.flush()

        # в зависимости от заданных настроек загружаем цены на альянсовых структурах
        # и пишем в БД (внимание! в настройках запуска могут будет заданы РАЗНЫЕ корпорации,
        # так что одна корпорация может не иметь доступа к структуре, а другая иметь, таким
        # одразом фильтрация осуществляется по названиям корпораций)
        if categories & {'all', 'corporation', 'trade_hubs'}:
            # Requires: public access
            for structure in active_market_structures:
                if structure.get("corporation_name") == corporation_name:
                    found_market_goods, updated_market_orders = dbtools.actualize_markets_structures_prices(structure.get("structure_id"))
                    print("'{}' market has {} goods and {} order updates\n".format(
                        structure.get("structure_id"),
                        'not new' if found_market_goods is None else found_market_goods,
                        'no' if updated_market_orders is None else updated_market_orders))
                    sys.stdout.flush()

        # приступаем к загрузке корпоративных данных

        if categories & {'all', 'corporation', 'assets'}:
            # Requires role(s): Station_Manager
            corp_structures_data, corp_structures_new = dbtools.actualize_corporation_structures(corporation_id)
            if not corp_structures_data:
                print("'{}' corporation has no any structures\n".format(corporation_name))
            else:
                print("'{}' corporation has {} of {} new structures\n".
                      format(corporation_name, corp_structures_new, len(corp_structures_data)))
            sys.stdout.flush()

            # Requires role(s): Director
            known_asset_items = dbtools.actualize_corporation_assets(corporation_id)
            print("'{}' corporation has {} asset items\n".
                  format(corporation_name, 'no updates in' if known_asset_items is None else known_asset_items))
            sys.stdout.flush()

        if categories & {'all', 'corporation', 'blueprints'}:
            # Requires role(s): Director
            known_blueprints = dbtools.actualize_corporation_blueprints(corporation_id)
            print("'{}' corporation has {} blueprints\n".
                  format(corporation_name, 'no updates in' if known_blueprints is None else known_blueprints))
            sys.stdout.flush()

        if categories & {'all', 'corporation', 'industry'}:
            # Requires role(s): Factory_Manager
            corp_industry_stat = dbtools.actualize_corporation_industry_jobs(corporation_id)
            if corp_industry_stat is None:
                print("'{}' corporation has no update in industry jobs\n".format(corporation_name))
            else:
                print("'{}' corporation has {} active of {} total industry jobs\n".
                      format(corporation_name, corp_industry_stat[1], corp_industry_stat[0]))
            sys.stdout.flush()

        if categories & {'all', 'corporation', 'finances'}:
            # Requires role(s): Accountant, Junior_Accountant
            corp_made_new_payments = dbtools.actualize_corporation_wallet_journals(corporation_id)
            print("'{}' corporation made {} new payments\n".
                  format(corporation_name, corp_made_new_payments))
            sys.stdout.flush()

            # Requires role(s): Accountant, Junior_Accountant
            corp_made_new_transactions = dbtools.actualize_corporation_wallet_transactions(corporation_id)
            print("'{}' corporation made {} new transactions\n".
                  format(corporation_name, corp_made_new_transactions))
            sys.stdout.flush()

        if categories & {'all', 'corporation', 'orders'}:
            # Requires role(s): Accountant, Trader
            corp_orders_stat = dbtools.actualize_corporation_orders(corporation_id)
            if corp_orders_stat is None:
                print("'{}' corporation has no update in orders\n".format(corporation_name))
            else:
                print("'{}' corporation has {} active and {} finished orders\n".
                      format(corporation_name, corp_orders_stat[0], corp_orders_stat[1]))
            sys.stdout.flush()

        if categories & {'all', 'corporation', 'blueprints', 'industry'}:
            # Пытаемся отследить и сохраняем связи между чертежами и работами
            dbtools.link_blueprints_and_jobs(corporation_id)
            print(f"'{corporation_name}' corporation link blueprints and jobs completed\n")
            sys.stdout.flush()

        # приступаем к загрузке тех данных, что грузятся крайне медленно (публичные и их много)

        if last_time:
            # проверка необходимости актуализации добавленных CCP-шниками новых типов предметов,
            # их обнаружение и добавление в БД (список CCP-шниками обновлется раз в день и приводит к
            # ОЧЕНЬ ДЛИТЕЛЬНОМУ обновлению всех type_ids, поскольку даже проверить etags у нескольких
            # тысяч предметов - долго)
            if categories & {'all', 'public', 'once', 'goods'}:
                # Public information about type_id
                num_actualized: int = dbtools.actualize_type_ids(full_database_upgrade=True)
                if num_actualized == 0:
                    print("No new items found in the Universe")
                else:
                    print("{} Universe' items actualized in database".format(num_actualized))
                sys.stdout.flush()
                # готовим признаки пересчёта conveyor-формул
                if num_actualized:
                    # мы здесь не знаем что именно поменялось в предметах? (скорее всего не поменялось, а добавились
                    # новые предметы); однако иногда через эту точку мы проходим на инструкции из шапки этого файла,
                    # т.е. после запуска q_dictionaries.py --category=all когда программа заново загружает все сведения
                    # о предметах, в том числе и параметр packaged_volume, который используется в расчёте
                    # conveyor-формул в части касающейся транспортных расходов (топляк помноженный на кубометры, где
                    # упакованный размер предмета влияет на стоимость транспортировки от конвейера до торгового хаба)
                    conveyor_formulas_delivery_refresh = True

            # загрузка исторических цен по регионам (ОЧЕНЬ МЕДЛЕННО из-за большого кол-ва данных), как
            # правило загрузка рыночных данных одного крупного региона, например The Forge, занимает
            # несколько часов
            # ---
            # НЕЛЬЗЯ СЮДА ДОБАВЛЯТЬ РЕГИОНЫ БЕЗ СОГЛАСОВАНИЯ С ССР, ИНАЧЕ БУДЕТ БАН: You have been banned
            # from using ESI. Please contact Technical Support. (support@eveonline.com)
            # ---
            # if categories & {'all', 'public', 'once', 'trade_history'}:
            #    # Requires: public access
            #    if dbtools.is_market_regions_history_refreshed():
            #        for region in q_industrialist_settings.g_market_regions:
            #            market_region_history_updates = dbtools.actualize_market_region_history(region)
            #            print("Region '{}' has {} market history updates\n".
            #                  format(region, 'no' if market_region_history_updates is None
            #                  else market_region_history_updates))
            #            sys.stdout.flush()

            # если признаки пересчёта conveyor-формул установлены, то надо отреагировать и пересчитать кеши таблиц
            if categories & {'all', 'once', 'conveyor_formulas'} or \
               conveyor_formulas_jobs_refresh or \
               conveyor_formulas_purchase_refresh or \
               conveyor_formulas_delivery_refresh:
                print("Conveyor formulas must be recalculated because {} have been updated".format(
                    ','.join(filter(str,
                                    ['jobs cost' if conveyor_formulas_jobs_refresh else '',
                                     'purchase' if conveyor_formulas_purchase_refresh else '',
                                     'delivery' if conveyor_formulas_delivery_refresh else '']))
                ))
                dbtools.actualize_conveyor_formulas_calculus()

    sys.stdout.flush()

    del dbtools

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nDone")


if __name__ == "__main__":
    # mem = memory_usage(main, max_usage=True)
    # print("Memory used: {}Mb".format(mem))
    main()  # 121.4Mb

