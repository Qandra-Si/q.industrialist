""" Q.Regroup (desktop/mobile)

Prerequisites:
    * Have a Python 3 environment available to you (possibly by using a
      virtual environment: https://virtualenv.pypa.io/en/stable/).
    * Run pip install -r requirements.txt with this directory as your root.

    * Copy q_industrialist_settings.py.template into q_industrialist_settings.py and
      mood for your needs.
    * Create an SSO application at developers.eveonline.com with the scopes
      from g_client_scope list declared in q_industrialist_settings.py and the
      callback URL "https://localhost/callback/".
      Note: never use localhost as a callback in released applications.

To run this example, make sure you have completed the prerequisites and then
run the following command from this directory as the root:

>>> python eve_sde_tools.py
>>> python q_regroup.py --pilot="Qandra Si" --online --cache_dir=~/.q_industrialist

Requires application scopes:
    * esi-assets.read_corporation_assets.v1 - Requires role(s): Director
"""
import sys
import requests

import eve_esi_interface as esi
import postgresql_interface as db

import q_industrialist_settings
import eve_esi_tools
import eve_sde_tools
import console_app
import render_html_regroup

from __init__ import __version__


def __get_containers(
        # настройки из БД
        db_regroup_stock,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_inv_names,
        # esi данные, загруженные с серверов CCP
        corp_assets_data,
        foreign_structures_data,
        corp_ass_names_data):
    # построение списка уникальных наименований станций
    stations = list(dict.fromkeys([r["station"] for r in db_regroup_stock]))
    # построение списка станций для которых необходимо получить списки контейнеров
    search_settings = []
    tmp_sc: str = "search_containers"
    tmp_sh: str = "stock_hangars"
    for station_name in stations:
        stock_containers = [r["container"] for r in db_regroup_stock if r["station"] == station_name]
        stock_hangars = list(dict.fromkeys([c for c in stock_containers if c[:-1] == "CorpSAG"]))
        stock_containers = list(dict.fromkeys([c for c in stock_containers if c[:-1] != "CorpSAG"]))
        search_settings.append({
            "station_name": station_name,
            "user_data": {tmp_sc: stock_containers, tmp_sh: stock_hangars},
        })
    regroup_containers = eve_esi_tools.get_containers_on_stations(
        search_settings,
        sde_type_ids,
        sde_inv_names,
        corp_assets_data,
        foreign_structures_data,
        corp_ass_names_data,
        throw_when_not_found=False
    )
    for station_dict in regroup_containers:
        station_dict["containers"] = [c for c in station_dict["containers"] if c["name"] in station_dict[tmp_sc]]
        del station_dict[tmp_sc]
        del station_dict["hangars_filter"]
    return regroup_containers


def __build_regroup(
        # настройки
        db_regroup_stock,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_inv_names,
        sde_market_groups,
        sde_named_type_ids,
        # esi данные, загруженные с серверов CCP
        corp_assets_data,
        foreign_structures_data,
        corp_ass_names_data):
    regroup_containers = __get_containers(
        # настройки из БД
        db_regroup_stock,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_inv_names,
        # esi данные, загруженные с серверов CCP
        corp_assets_data,
        foreign_structures_data,
        corp_ass_names_data
    )

    # Example of regroup_containers:
    # [ { 'station_id': 1029371791363,
    #     'station_name': 'BX-VEX - Two Titans. Every Hangar.',
    #     'station_foreign': True,
    #     'containers': [{'id': 1035621139039, 'type_id': 17368, 'name': '..stock ALL'}]
    # },
    # {   'station_id': 1029853015264,
    #     'station_name': 'W6V-VM - Delta After Dark - RIP Remdick',
    #     'station_foreign': True,
    #     'containers': [{'id': 1035776350534, 'type_id': 17366, 'name': '!▒▒▒▒▒▒▒▒▒!CTA Stock'}]
    # },
    # {   'station_id': ?,
    #     'station_name': 'YZ-LQL VI - Moon 19 - Guardian Angels Logistic Support',
    #     'containers': [],
    #     'stock_hangars': ['CorpSAG3']
    # } ]

    corp_regroup_stat = {
        "regroup_market_groups": {},
        "regroup_containers": regroup_containers,
        "regroup_stocks": {},
    }

    def push_into_regroup_market_groups(__market_group_id):
        if corp_regroup_stat["regroup_market_groups"].get(int(__market_group_id), None) is None:
            corp_regroup_stat["regroup_market_groups"].update({
                int(__market_group_id): eve_sde_tools.get_market_group_name_by_id(sde_market_groups, __market_group_id)
            })

    def get_new_product_dict(container_id, hangar_dict, type_id: int, item_name: str, quantity: int):
        if isinstance(container_id, str):  # ангар
            __available121 = 0
        elif isinstance(container_id, int):  # контейнер
            __available121 = sum([a["quantity"] for a in corp_assets_data
                                  if (a["type_id"] == type_id) and (a["location_id"] == container_id)])
        else:
            __available121 = 0
        __market123 = eve_sde_tools.get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, type_id)
        if not (hangar_dict is None):
            hangar_loc_id: int = int(hangar_dict["location_id"])  # это может быть, например, номер офиса на станции
            hangar_num: str = hangar_dict["location_flag"]  # название в формате CorpSAG?
            __available121 += sum([a["quantity"] for a in corp_assets_data
                                   if (a["type_id"] == type_id) and (a["location_id"] == hangar_loc_id)
                                   and (a["location_flag"] == hangar_num)])
        push_into_regroup_market_groups(__market123)
        return {
            "name": item_name,
            "quantity": quantity,
            "available": __available121,
            "market": __market123,
        }

    def push_into_regroup_stock(station_id: int, container_id, hangar_dict, type_id: int, item_name: str,
                                quantity: int):
        __station135 = corp_regroup_stat["regroup_stocks"].get(int(station_id), None)
        if __station135 is None:
            corp_regroup_stat["regroup_stocks"][int(station_id)] = {
                container_id: {
                    "stock": {
                        int(type_id): get_new_product_dict(container_id, hangar_dict, type_id, item_name, quantity)
                    },
                    "fits": []
                }
            }
        else:
            __container141 = __station135.get(container_id, None)
            if __container141 is None:
                __station135[container_id] = {
                    "stock": {
                        int(type_id): get_new_product_dict(container_id, hangar_dict, type_id, item_name, quantity)
                    },
                    "fits": []
                }
            else:
                __product145 = __container141["stock"].get(int(type_id), None)
                if __product145 is None:
                    __container141["stock"][int(type_id)] = get_new_product_dict(container_id, hangar_dict, type_id, item_name, quantity)
                else:
                    __product145["quantity"] += quantity

    def push_fit_into_regroup_stock(station_id: int, container_id: int, converted_fit):
        __station152 = corp_regroup_stat["regroup_stocks"].get(int(station_id), None)
        if __station152 is None:
            return
        __container155 = __station152.get(container_id, None)
        if __container155 is None:
            return
        __container155["fits"].append(converted_fit)

    # конвертация ETF в список item-ов
    for regroup in db_regroup_stock:
        __total_quantity = regroup["q"]
        __eft = regroup["eft"]
        __station_name = regroup["station"]
        __container_name = regroup["container"]
        # ---
        station_dict = next((r for r in regroup_containers if r["station_name"] == __station_name), None)
        if (station_dict is None) or (station_dict.get("station_id") is None):
            continue
        station_id = station_dict.get("station_id")
        # ---
        if __container_name[:-1] == "CorpSAG":
            office_id = next((a["item_id"] for a in corp_assets_data if a["location_flag"] == "OfficeFolder" and a["location_id"] == station_id), None)
            if office_id is None:
                continue
            container_id = "{}_{}".format(station_id, __container_name)  # в контейнерах не искать, только в ангаре
            # ---
            hangar_dict = {"location_id": int(office_id), "location_flag": __container_name}
        else:
            container_id = next((c["id"] for c in station_dict["containers"] if c["name"] == __container_name), None)
            if container_id is None:
                continue
            # ---
            hangar_dict = None  # попытаемся найти номер ангара, в котором лежит контейнер (будет там искать ships)
            container_dict = next((a for a in corp_assets_data if a["item_id"] == container_id), None)
            if not (container_dict is None):
                container_loc_flag: str = container_dict["location_flag"]
                if container_loc_flag[:-1] == "CorpSAG":  # контейнер находится в ангаре
                    hangar_dict = {"location_id": int(container_dict["location_id"]), "location_flag": container_loc_flag}
        # ---
        __converted = eve_sde_tools.get_items_list_from_eft(__eft, sde_named_type_ids)
        __converted.update({"quantity": __total_quantity})
        if not (__converted["ship"] is None):
            push_into_regroup_stock(
                station_id,
                container_id,
                hangar_dict,  # это может быть номер офиса и название ангара, в котором лежит контейнер
                __converted["ship"]["type_id"],
                __converted["ship"]["name"],
                __total_quantity)
            # пересчитываем общее кол-во, необходимое для регрупа и кол-во доступных компонентов
            __converted["ship"]["available"] = corp_regroup_stat["regroup_stocks"][int(station_id)][container_id]["stock"][int(__converted["ship"]["type_id"])]["available"]
        __converted["items"].sort(key=lambda i: i["name"])
        for __item_dict in __converted["items"]:
            push_into_regroup_stock(
                station_id,
                container_id,
                hangar_dict,
                __item_dict["type_id"],
                __item_dict["name"],
                __total_quantity * __item_dict["quantity"])
            # пересчитываем общее кол-во, необходимое для регрупа и кол-во доступных компонентов
            __item_dict["available"] = corp_regroup_stat["regroup_stocks"][int(station_id)][container_id]["stock"][int(__item_dict["type_id"])]["available"]
        for __problem_dict in __converted["problems"]:
            # у проблемных item-ов неизвестен type_id
            __problem_dict["available"] = 0
        # сохраняем регруп-фит для этого контейнера этой станции
        push_fit_into_regroup_stock(station_id, container_id, __converted)

    return corp_regroup_stat


def __get_db_connection():
    qidb = db.QIndustrialistDatabase("regroup", debug=False)
    qidb.connect(q_industrialist_settings.g_database)
    return qidb


def main():
    qidb = __get_db_connection()
    try:
        db_regroup_stock = qidb.select_all_rows(
            "SELECT rs_quantity,rs_eft,rs_station,rs_container "
            "FROM regroup_stock "
            "WHERE rs_active;")

        db_regroup_stock = [{"eft": wmj[1], "q": wmj[0], "station": wmj[2], "container": wmj[3]} for wmj in db_regroup_stock]
    except:
        print(sys.exc_info())
        sys.exit(1)  # errno.h : EPERM=1 /* Operation not permitted */
    del qidb

    # работа с параметрами командной строки, получение настроек запуска программы, как то: работа в offline-режиме,
    # имя пилота ранее зарегистрированного и для которого имеется аутентификационный токен, регистрация нового и т.д.
    argv_prms = console_app.get_argv_prms()

    sde_type_ids = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "typeIDs")
    sde_inv_names = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "invNames")
    sde_market_groups = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "marketGroups")
    sde_named_type_ids = eve_sde_tools.convert_sde_type_ids(sde_type_ids)

    corp_regroup_stats = []
    for pilot_name in argv_prms["character_names"]:
        # настройка Eve Online ESI Swagger interface
        auth = esi.EveESIAuth(
            '{}/auth_cache'.format(argv_prms["workspace_cache_files_dir"]),
            debug=True)
        client = esi.EveESIClient(
            auth,
            debug=False,
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

        # для того, чтобы получить названия коробок и в каком ангаре они расположены, надо загрузить
        # данные по ассетам, т.к. только в этих данных можно учитывая иерархию пересчитать коробки
        # в нужном ангаре

        # Requires role(s): Director
        corp_assets_data = interface.get_esi_paged_data(
            "corporations/{}/assets/".format(corporation_id))
        print("\n'{}' corporation has {} assets".format(corporation_name, len(corp_assets_data)))
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
        print(
            "\n'{}' corporation has offices in {} foreign stations".format(corporation_name, len(foreign_structures_data)))
        if len(foreign_structures_forbidden_ids) > 0:
            print("\n'{}' corporation has offices in {} forbidden stations : {}".format(corporation_name, len(
                foreign_structures_forbidden_ids), foreign_structures_forbidden_ids))
        sys.stdout.flush()

        # строим данные для генерации отчёта
        corp_regroup_stat = __build_regroup(
            # настройки из БД
            db_regroup_stock,
            # sde данные, загруженные из .converted_xxx.json файлов
            sde_type_ids,
            sde_inv_names,
            sde_market_groups,
            sde_named_type_ids,
            # esi данные, загруженные с серверов CCP
            corp_assets_data,
            foreign_structures_data,
            corp_ass_names_data)

        # обновление данных в БД (названия контейнеров, и первичное автозаполнение)
        for stock_containers in corp_regroup_stat["regroup_containers"]:
            cntnrs = stock_containers["containers"]
            print('\nFound station {} with containers...'.format(stock_containers["station_name"]))
            print('  {} = {}'.format(stock_containers["station_id"], stock_containers["station_name"]))
            print('  regroup containers = {}'.format([(c['id'], c['name']) for c in cntnrs]))
        sys.stdout.flush()

        eve_esi_tools.dump_debug_into_file(argv_prms["workspace_cache_files_dir"], "corp_regroup_stat.{}".format(corporation_name), corp_regroup_stat)

        corp_regroup_stat.update({"corporation_name": corporation_name})
        corp_regroup_stats.append(corp_regroup_stat)

    # освобождаем память от ненужных более списков
    del sde_inv_names
    del sde_named_type_ids

    print("\nBuilding regroup report...")
    sys.stdout.flush()

    render_html_regroup.dump_regroup_into_report(
        # путь, где будет сохранён отчёт
        argv_prms["workspace_cache_files_dir"],
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_market_groups,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_regroup_stats
    )

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nDone")


if __name__ == "__main__":
    main()
