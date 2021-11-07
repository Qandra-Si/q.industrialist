import json
from pathlib import Path


def __get_blueprint_progress_status(corp_industry_jobs_data, blueprint_id):
    for bp in corp_industry_jobs_data:
        if blueprint_id == bp["blueprint_id"]:
            return bp["status"]
    return None


def get_corp_bp_loc_data(corp_blueprints_data, corp_industry_jobs_data):
    """
    Построение иерархических списков БПО и БПЦ, хранящихся в корпоративных ангарах
    """
    corp_bp_loc_data = {}
    for bp in corp_blueprints_data:
        loc_id = int(bp["location_id"])
        blueprint_id = int(bp["item_id"])
        # особенность : чертежи могут отсутствовать в assets по указанному location_id, при этом чертёж будет в
        # blueprints, но его location_id будет указывать на станцию, а не на контейнер, в то же время в industrial
        # jobs этот же самый чертёж будет находиться в списке и иметь blueprint_location_id который указывает на
        # искомый контейнер
        __job_dict = next((j for j in corp_industry_jobs_data if j['blueprint_id'] == int(blueprint_id)), None)
        if not (__job_dict is None):
            loc_id = __job_dict["blueprint_location_id"]
        # { "1033160348166": {} }
        if not (str(loc_id) in corp_bp_loc_data):
            corp_bp_loc_data.update({str(loc_id): {}})
        __bp2 = corp_bp_loc_data[str(loc_id)]
        # { "1033160348166": { "30014": {} } }
        type_id = int(bp["type_id"])
        if not (type_id in __bp2):
            __bp2.update({type_id: {}})
        # { "1033160348166": { "30014": { "o_10_20": {} } } }
        quantity = int(bp["quantity"])
        is_blueprint_copy = quantity < -1
        bp_type = 'c' if is_blueprint_copy else 'o'
        material_efficiency = int(bp["material_efficiency"])
        time_efficiency = int(bp["time_efficiency"])
        bp_status = __get_blueprint_progress_status(corp_industry_jobs_data, blueprint_id)
        bp_key = '{bpt}_{me}_{te}_{st}'.format(
            bpt=bp_type,
            me=material_efficiency,
            te=time_efficiency,
            st="" if bp_status is None else bp_status[:2])
        runs = int(bp["runs"])
        quantity_or_runs = runs if is_blueprint_copy else quantity if quantity > 0 else 1
        # { "1033160348166": { "30014": { "o_10_20": { "cp":false,"me":10,..., [] } } } }
        if not (bp_key in __bp2[type_id]):
            __bp2[type_id].update({bp_key: {
                "cp": is_blueprint_copy,
                "me": material_efficiency,
                "te": time_efficiency,
                "qr": quantity_or_runs,
                "st": bp_status,
                "itm": []
            }})
        else:
            __bp2[type_id][bp_key]["qr"] = __bp2[type_id][bp_key]["qr"] + quantity_or_runs
        # { "1033160348166": { "30014": { "o_10_20": { "cp":false,"me":10,..., [{"id":?,"q":?,"r":?}, {...}] } } } }
        __itm_dict = {
            "id": blueprint_id,
            "q": quantity,
            "r": runs
        }
        if not (__job_dict is None):
            __itm_dict.update({"jc": __job_dict["cost"]})
        __bp2[type_id][bp_key]["itm"].append(__itm_dict)
    return corp_bp_loc_data


def get_corp_ass_loc_data(corp_assets_data, containers_filter=None):
    """
    Построение списка модулей и ресуров, которые имеются в распоряжении корпорации и
    которые предназначены для использования в чертежах
    """
    corp_ass_loc_data = {}
    for a in corp_assets_data:
        type_id = int(a["type_id"])
        # if materials_for_bps.count(type_id) > 0:
        loc_flag = str(a["location_flag"])
        if not (loc_flag[:-1] == "CorpSAG") and not (loc_flag == "Unlocked") and not (loc_flag == "AutoFit"):
            continue  # пропускаем дронов в дронбеях, патроны в карго, корабли в ангарах и т.п.
        loc_id = int(a["location_id"])
        if not (containers_filter is None):
            if not (loc_id in containers_filter):
                continue  # пропускаем все контейнеры, кроме тех, откуда ведётся производство
        quantity = int(a["quantity"])
        # { "CorpSAG6": {} }
        if not (str(loc_flag) in corp_ass_loc_data):
            corp_ass_loc_data.update({str(loc_flag): {}})
        __a1 = corp_ass_loc_data[str(loc_flag)]
        # { "CorpSAG6": {"1033692665735": {} } }
        if not (str(loc_id) in __a1):
            __a1.update({str(loc_id): {}})
        __a2 = __a1[str(loc_id)]
        # { "CorpSAG6": {"1033692665735": { "2488": <quantity> } } }
        if not (type_id in __a2):
            __a2.update({type_id: quantity})
        else:
            __a2[type_id] = quantity + __a2[type_id]
    return corp_ass_loc_data


def get_assets_named_ids(corp_assets_data):
    ass_cont_ids = []
    for a in corp_assets_data:
        if not a["is_singleton"]:
            continue  # пропускаем экземпляры контейнеров, сложенные в стопки (у них нет уник. id и названий тоже не будет)
        loc_flag = str(a["location_flag"])
        if not (loc_flag[:-1] == "CorpSAG") and not (loc_flag == "Unlocked") and not (loc_flag == "AutoFit"):
            continue  # пропускаем дронов в дронбеях, патроны в карго, корабли в ангарах и т.п.
        if a["type_id"] in [17363,   # Small Audit Log Secure Container
                            17364,   # Medium Audit Log Secure Container
                            17365,   # Large Audit Log Secure Container
                            17366,   # Station Container
                            17367,   # Station Vault Container
                            17368,   # Station Warehouse Container
                            2233,    # Customs Office
                            24445,   # Giant Freight Container
                            33003,   # Enormous Freight Container
                            33005,   # Huge Freight Container
                            33007,   # Large Freight Container
                            33009,   # Medium Freight Container
                            33011,   # Small Freight Container
                            35825,   # Raitaru
                            35826,   # Azbel
                            35827,   # Sotiyo
                            35828,   # Medium Laboratory
                            35829,   # Large Laboratory
                            35830,   # X-Large Laboratory
                            35832,   # Astrahus
                            35833,   # Fortizar
                            35834,   # Keepstar
                            35835,   # Athanor
                            35836    # Tatara
                           ]:
            if ass_cont_ids.count(a["item_id"]) == 0:
                ass_cont_ids.append(a["item_id"])
    return ass_cont_ids


def get_foreign_structures_ids(corp_assets_data):
    foreign_structs_ids = []
    for a in corp_assets_data:
        # проверяем либо location_flag=OfficeFolder, либо type_id=27 (Office)
        if a["type_id"] == 27:
            # если будет найден Офис корпорации, то надо найти станцию
            # в том случае, если её нет в ассетах, то станция принадлежит другой
            # корпорации (пропускаем NPC-станции, с int32-кодами, и формируем
            # список из станций с int64-кодами)
            station_id = int(a["location_id"])
            if station_id < 1000000000000:
                continue
            found = False
            for _a in corp_assets_data:
                if _a["item_id"] == station_id:
                    found = True
                    break
            if not found:
                if 0 == foreign_structs_ids.count(station_id):
                    foreign_structs_ids.append(station_id)
        elif (a["location_flag"] == "CorpDeliveries") and (a["location_type"] == "item"):
            # если будут найдены корпоративные delivery, то следует иметь в виду, что
            # всякое corp-delivery всегда находится в разделе "входящие" на станциях, так
            # что всякая локация corp-deliveries - это станции
            location_id = int(a["location_id"])
            if location_id < 1000000000000:
                continue
            if 0 == foreign_structs_ids.count(location_id):
                foreign_structs_ids.append(location_id)
    return foreign_structs_ids


def get_assets_tree_root(ass_tree, location_id):
    if not (str(location_id) in ass_tree):
        return location_id
    itm = ass_tree[str(location_id)]
    if not ("location_id" in itm):
        return location_id
    return get_assets_tree_root(ass_tree, itm["location_id"])


def fill_ass_tree_with_sde_data(location_id, ass_tree, sde_inv_items):
    if location_id <= 5:
        return
    if not (str(location_id) in sde_inv_items):
        return
    sde_item = sde_inv_items[str(location_id)]
    type_id = sde_item["typeID"]
    new_location_id = sde_item["locationID"]
    if not (str(location_id) in ass_tree):
        ass_tree.update({str(location_id): {"type_id": type_id}})
    else:
        ass_tree[str(location_id)]["type_id"] = type_id
    if type_id > 5:  # останавливаем глубину на Constellation (и не добавляем её в ass_tree)
        ass_tree[str(location_id)]["location_id"] = new_location_id
        if not (str(new_location_id) in ass_tree):
            ass_tree.update({str(new_location_id): {"items": [location_id]}})
        else:
            ass_tree[str(new_location_id)]["items"].append(location_id)
    if type_id == 5:  # останавливаемся а глубине Solar System
        return
    fill_ass_tree_with_sde_data(new_location_id, ass_tree, sde_inv_items)


def get_assets_tree(corp_assets_data, foreign_structures_data, sde_inv_items, virtual_hierarchy_by_corpsag = False):
    """
    https://docs.esi.evetech.net/docs/asset_location_id
    https://forums-archive.eveonline.com/topic/520027/

    Строит дерево в виде:
    { location1: [item1,item2,...], location2: [item3,item4,...] }
    """
    ass_tree = {}
    stations = []
    # формируем дерево из набора корпоративных ассетов
    for a in enumerate(corp_assets_data):
        item_id = int(a[1]["item_id"])
        location_id = int(a[1]["location_id"])
        location_flag = a[1]["location_flag"]
        type_id = int(a[1]["type_id"])
        if virtual_hierarchy_by_corpsag and (location_flag[:-1] == "CorpSAG"):
            corpsag_root = '{}_{}'.format(location_id, location_flag)
            virt_root = str(location_id)
            if (corpsag_root in ass_tree) and ("items" in ass_tree[corpsag_root]):
                ass_tree[corpsag_root]["items"].append(item_id)
            else:
                ass_tree.update({corpsag_root: {"items": [item_id],
                                                "location_id": virt_root,
                                                "type_id": 41567}})  # Hangar Container
            if (virt_root in ass_tree) and ("items" in ass_tree[virt_root]):
                if ass_tree[virt_root]["items"].count(corpsag_root) == 0:
                    ass_tree[virt_root]["items"].append(corpsag_root)
            else:
                ass_tree.update({virt_root: {"items": [corpsag_root]}})
        else:
            locstr_root = str(location_id)
            if (locstr_root in ass_tree) and ("items" in ass_tree[locstr_root]):
                ass_tree[locstr_root]["items"].append(item_id)
            else:
                ass_tree.update({locstr_root: {"items": [item_id]}})
                location_type = a[1]["location_type"]
                if location_type == "solar_system":
                    ass_tree[locstr_root]["type_id"] = 5  # Solar System
                elif location_type == "station":
                    if stations.count(location_id) == 0:
                        stations.append(location_id)
        if not (str(item_id) in ass_tree):
            ass_tree.update({str(item_id): {"type_id": type_id, "index": a[0]}})
        else:
            __a = ass_tree[str(item_id)]
            if not ("type_id" in __a):
                __a["type_id"] = type_id
            if not ("index" in __a):
                __a["index"] = a[0]
    # прописываем location_id парамтеры в каждом элементе по известному item_id
    for a in enumerate(corp_assets_data):
        item_id = str(a[1]["item_id"])
        location_id = str(a[1]["location_id"])
        if virtual_hierarchy_by_corpsag:
            location_flag = a[1]["location_flag"]
            virt_root = '{}_{}'.format(location_id, location_flag) if location_flag[:-1] == "CorpSAG" else location_id
        else:
            virt_root = location_id
        if item_id in ass_tree:
            __a = ass_tree[item_id]
            if not ("location_id" in __a):
                __a["location_id"] = virt_root
            if not ("type_id" in __a):
                __a["type_id"] = a[1]["type_id"]
            if not ("index" in __a):
                __a["index"] = a[0]
    # дополняем дерево сведениями о станциях, не принадлежащих корпорации (всё равно,
    # что добавить в список NPC-станции)
    foreign_station_ids = foreign_structures_data.keys()
    for station_id in foreign_station_ids:
        fs = foreign_structures_data[str(station_id)]
        solar_system_id = int(fs["solar_system_id"])
        # находим элемент дерева с известным item_id (станцию чужой корпы) и дополняем
        # элемент типом строения и его расположением
        station = ass_tree[str(station_id)]
        station["location_id"] = solar_system_id
        station["type_id"] = fs["type_id"]
        # находим солнечную систему или добоавляем её в дерево
        if str(solar_system_id) in ass_tree:
            ass_tree[str(solar_system_id)]["items"].append(int(station_id))
        else:
            ass_tree.update({str(solar_system_id): {"items": [int(station_id)], "type_id": 5}})  # 5 = Solar System
    # дополняем дерево сведениям о расположении NPC-станций (данными из eve sde)
    for station_id in stations:
        a = ass_tree[str(station_id)]
        if not ("type_id" in a):
            if stations.count(int(station_id)):
                fill_ass_tree_with_sde_data(int(station_id), ass_tree, sde_inv_items)
    # формируем корни дерева (станции и системы, с которых начинается общая иерархия)
    ass_keys = ass_tree.keys()
    if len(ass_keys) > 0:
        roots = []
        for k in ass_keys:
            root = get_assets_tree_root(ass_tree, k)
            if 0 == roots.count(int(root)):
                roots.append(int(root))  # составные root-ы типа 123456_CorpASG2 сюда не попадают, т.к. не корни
        ass_tree["roots"] = roots
    return ass_tree


def dump_debug_into_file(ws_dir, nm, data):
    f_name = '{dir}/debug/{nm}.json'.format(dir=ws_dir, nm=nm)
    s = json.dumps(data, indent=1, sort_keys=False)
    Path('{dir}/debug'.format(dir=ws_dir)).mkdir(parents=True, exist_ok=True)
    with open(f_name, 'wt+', encoding='utf8') as f:
        try:
            f.write(s)
        finally:
            f.close()
    return


def __represents_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def get_assets_location_name(
        location_id,
        sde_inv_names,
        sde_inv_items,
        corp_ass_names_data,
        foreign_structures_data):
    region_id = None
    region_name = None
    loc_name = None
    foreign = False
    loc_is_not_virtual = __represents_int(location_id)
    if loc_is_not_virtual and (int(location_id) < 1000000000000):
        if str(location_id) in sde_inv_names:
            loc_name = sde_inv_names[str(location_id)]
            if str(location_id) in sde_inv_items:
                root_item = sde_inv_items[str(location_id)]
                if root_item["typeID"] == 5:  # Solar System
                    # constellation_name = sde_inv_names[str(root_item["locationID"])]
                    constellation_item = sde_inv_items[str(root_item["locationID"])]  # Constellation
                    region_id = constellation_item["locationID"]
                    region_name = sde_inv_names[str(region_id)]
    else:
        if not loc_is_not_virtual and (location_id[:-1])[-7:] == "CorpSAG":
            loc_name = 'Corp Security Access Group {}'.format(location_id[-1:])
        else:
            loc_name = next((n["name"] for n in corp_ass_names_data if n['item_id'] == location_id), None)
            if loc_name is None:
                loc_name = next((foreign_structures_data[fs]["name"] for fs in foreign_structures_data if int(fs) == location_id), None)
                foreign = False if loc_name is None else True
    return region_id, region_name, loc_name, foreign


def get_universe_location_by_item(
        __location_id,
        sde_inv_names,
        sde_inv_items,
        corp_assets_tree,
        corp_ass_names_data,
        foreign_structures_data):
    # получение название контейнера (названия ingame задают игроки)
    __loc_name = next((n["name"] for n in corp_ass_names_data if n['item_id'] == __location_id), None)
    __loc_dict = {"name": __loc_name}
    # получение информации о регионе, солнечной системе и т.п. (поиск исходного root-а)
    __root_location_id = __prev_location_id = int(__location_id)
    __assets_roots = corp_assets_tree["roots"]
    while True:
        if __root_location_id in __assets_roots:
            break
        if str(__root_location_id) in corp_assets_tree:
            a = corp_assets_tree[str(__root_location_id)]
            if "location_id" in a:
                __prev_location_id = int(__root_location_id)
                __root_location_id = int(a["location_id"])
            else:
                break
        else:
            # корня нет (нет ассетов в Jita, но контракт там есть)
            # переходим к поиску по sde-items, см. https://docs.esi.evetech.net/docs/asset_location_id
            if __root_location_id > 64000000:
                break
            if str(__root_location_id) in sde_inv_items:
                i = sde_inv_items[str(__root_location_id)]
                if "locationID" in i:
                    if i["locationID"] < 30000000:
                        break
                    __prev_location_id = int(__root_location_id)
                    __root_location_id = int(i["locationID"])
    # определяем регион и солнечную систему, где расположен чертёж
    region_id, region_name, loc_name, __dummy0 = get_assets_location_name(
        int(__root_location_id),
        sde_inv_names,
        sde_inv_items,
        corp_ass_names_data,
        foreign_structures_data)
    if not (region_id is None):
        __loc_dict.update({"region_id": region_id, "region": region_name, "solar": loc_name, "solar_id": int(__root_location_id)})
        if __prev_location_id != __root_location_id:
            __dummy1, __dummy2, loc_name, foreign = get_assets_location_name(
                int(__prev_location_id),
                sde_inv_names,
                sde_inv_items,
                corp_ass_names_data,
                foreign_structures_data)
            __loc_dict.update({"station": loc_name, "station_id": int(__prev_location_id), "foreign": foreign})
    return __loc_dict


def is_location_nested_into_another(
        item_location,
        root_locations,
        corp_assets_tree):
    loc_id = int(item_location)
    while True:
        if loc_id in root_locations:
            return True
        if str(loc_id) in corp_assets_tree:
            __loc_dict = corp_assets_tree[str(loc_id)]
            if "location_id" in __loc_dict:
                loc_id = int(__loc_dict["location_id"])
            else:
                return False
        else:
            return False


def __find_containers_in_hangars_nested(
        item_id,
        hangars_filter,
        sde_type_ids,
        corp_assets_data):
    item_dict = next((a for a in corp_assets_data if a["item_id"] == int(item_id)), None)
    # пытаемся в дереве asset-ов найти идентификатор, если его нет, то это терминальный узел, например
    # чертёж, и он нам не интересен, т.к. требуется выдать идентификаторы контейнеров
    if item_dict is None:
        return []
    __nested_items = [a for a in corp_assets_data if a["location_id"] == int(item_id)]
    # нас интересуют только те контейнеры и ангары, в которых что-то есть, т.к. из них мы будем
    # впоследствии доставать информацию о находящихся чертежах, т.ч. пустые коробки пропускаем
    if not __nested_items:
        return []
    # ---
    containers = []
    for __item_dict in __nested_items:
        # пропускаем экземпляры контейнеров, сложенные в стопки (у них нет уник. id и названий
        # тоже не будет)
        if not __item_dict["is_singleton"]:
            continue
        # ожидаем найти офис со списком ангаров, а пока...
        # ...если список ангаров ещё не найден, то продолжаем поиски; как только нужные ангары будет
        # найдены, то зануляем параметр blueprints_hangar, что будет в дальнейшем означать, что поиск
        # ангаров уже остановлен и идёт поиск контейнеров в ангарах
        __item_id = __item_dict["item_id"]
        __location_flag = __item_dict["location_flag"]
        if __location_flag[:-1] == "CorpSAG":
            str_hangar_num = __location_flag[-1:]
            if not (int(str_hangar_num) in hangars_filter):
                continue
            # debug: print(str_hangar_num, "  ", __item_id)
            # если текущий item является контейнером, то выдаём его номер и внутрь не заглядываем
            __type_id = __item_dict["type_id"]
            __is_container = __type_id in [
                # 379: Cargo Containers
                #   1651: Secure Containers
                3465,   # Large Secure Container
                3466,   # Medium Secure Container
                3467,   # Small Secure Container
                11488,  # Huge Secure Container
                11489,  # Giant Secure Container
                #   1652: Audit Log Containers
                17363,  # Small Audit Log Secure Container
                17364,  # Medium Audit Log Secure Container
                17365,  # Large Audit Log Secure Container
                #   1653: Freight Containers
                24445,  # Giant Freight Container
                33003,  # Enormous Freight Container
                33005,  # Huge Freight Container
                33007,  # Large Freight Container
                33009,  # Medium Freight Container
                33011,  # Small Freight Container
                #   1657: Standard Containers
                3293,   # Medium Standard Container
                3296,   # Large Standard Container
                3297,   # Small Standard Container
                #   1658: Station Containers
                17366,  # Station Container
                17367,  # Station Vault Container
                17368,  # Station Warehouse Container
            ]
            if __is_container:
                if next((c for c in containers if c["id"] == int(__item_id)), None) is None:
                    # container_name = next((an["name"] for an in corp_ass_names_data if an["item_id"] == __item_id), None)
                    # debug: print("       ", item_id, __type_id, container_name)
                    containers.append({"id": __item_id, "type_id": __type_id})  # "name": container_name
                continue
        else:
            # debug: print(" ", __item_id, __location_flag)
            containers.extend(__find_containers_in_hangars_nested(
                __item_id,
                hangars_filter,
                sde_type_ids,
                corp_assets_data))
    return containers


def find_containers_in_hangars(
        station_id,
        hangars_filter,
        sde_type_ids,
        corp_assets_data,
        # настройки
        throw_when_not_found=True):
    # пытаемся получить станцию, как item (это возможно, если она есть в корп-ассетах, т.е. является
    # имуществом корпорации, иначе она принадлежит альянсу, или корпорация просто имеет там офис)
    __station_dict = next((a for a in corp_assets_data if a["item_id"] == int(station_id)), None)
    # на своих станциях тоже офис бывает
    __office_dict = next((a for a in corp_assets_data if (a["location_id"] == int(station_id)) and (a["location_flag"] == "OfficeFolder")), None)

    if (__station_dict is None) and (__office_dict is None):
        if throw_when_not_found:
            raise Exception('Not found station or office {} in assets!!!'.format(station_id))
        else:
            print("ERROR: not found station or office {} in assets!!!".format(station_id))
            return []

    # поиск контейнеров на станции station_id в ангарах hangars_filter
    __containers = []
    if not (__station_dict is None):
        __containers = __find_containers_in_hangars_nested(
            station_id,
            hangars_filter,
            sde_type_ids,
            corp_assets_data)
    if not (__office_dict is None):
        __containers2 = __find_containers_in_hangars_nested(
            __office_dict["item_id"],
            hangars_filter,
            sde_type_ids,
            corp_assets_data)
        for __cont in __containers2:
            if next((c for c in __containers if c['id'] == __cont['id']), None) is None:
                __containers.append(__cont)
    return __containers


def get_containers_on_stations(
        # условия для поиска данных станций и контейнеров в ассетах, в формате:
        # [{"station_id": int, "station_name": str, "hangars_filter": list, "user_data": {}}}]
        # например:
        # [{"station_id": 1029853015264, "hangars_filter": [6], "user_data": {"station_num": 1}}]
        # или же:
        # [{"station_name": "Keberz - fort"}, {"station_name": "BX-VEX - Two Titans. Every Hangar."}]
        search_settings,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_inv_names,
        # esi данные, загруженные с серверов CCP
        corp_assets_data,
        foreign_structures_data,
        corp_ass_names_data,
        # настройки
        throw_when_not_found=True):
    found_containers = []
    for station_dict in search_settings:
        # input setings
        hangars_filter = station_dict.get("hangars_filter", [1,2,3,4,5,6,7])
        # output factory containers
        station_containers = {
            "station_id": station_dict.get("station_id", None),
            "station_name": station_dict.get("station_name", None),
            "station_foreign": None,
            "hangars_filter": hangars_filter,
            "containers": []
        }
        if "user_data" in station_dict:
            station_containers.update(station_dict.get("user_data"))
        if (hangars_filter is None) or (station_containers['station_id'] is None) and (station_containers['station_name'] is None):
            continue

        # пытаемся определить недостающее звено, либо station_id, либо station_name (если неизвестны)
        if not (station_containers["station_id"] is None):
            station_id = station_containers["station_id"]
            station_name = None
            station_containers["station_foreign"] = next((a for a in corp_assets_data if a["item_id"] == int(station_id)), None) is None

            # поиск контейнеров на станции station_id в ангарах hangars_filter
            station_containers["containers"] = find_containers_in_hangars(
                station_id,
                hangars_filter,
                sde_type_ids,
                corp_assets_data,
                throw_when_not_found=throw_when_not_found)

            if not station_containers["station_foreign"]:
                station_name = next((an['name'] for an in corp_ass_names_data if an["item_id"] == station_id), None)

            if station_containers["station_foreign"]:
                # поиск одной единственной станции, которая не принадлежат корпорации (на них имеется офис,
                # но самой станции в ассетах нет)
                if str(station_id) in foreign_structures_data:
                    station_name = foreign_structures_data[str(station_id)]["name"]

            # вывод на экран найденных station_id и station_name
            if station_name is None:
                if throw_when_not_found:
                    raise Exception('Not found station name for factory {}!!!'.format(station_id))
                else:
                    print("ERROR: not found station name for factory {}!!!".format(station_id))

        elif not (station_containers["station_name"] is None):
            station_name = station_containers["station_name"]
            station_id = next((an for an in corp_ass_names_data if an["name"] == station_name), None)
            if station_id is None:
                station_id = next((int(n) for n in sde_inv_names if sde_inv_names[str(n)] == station_name), None)
                if not (station_id is None):
                    station_containers["station_npc"] = True
                else:
                    station_containers["station_foreign"] = station_id is None

            if station_containers["station_foreign"]:
                # поиск тех станций, которые не принадлежат корпорации (на них имеется офис, но самой станции в ассетах нет)
                __foreign_keys = foreign_structures_data.keys()
                for __foreign_id in __foreign_keys:
                    __foreign_dict = foreign_structures_data[str(__foreign_id)]
                    if __foreign_dict["name"] == station_name:
                        station_id = int(__foreign_id)
                        break

            # вывод на экран найденных station_id и station_name
            if station_id is None:
                if throw_when_not_found:
                    raise Exception('Not found station identity for factory {}!!!'.format(station_name))
                else:
                    print("ERROR: not found station identity for factory {}!!!".format(station_name))

            else:
                # поиск контейнеров на станции station_id в ангарах hangars_filter
                station_containers["containers"] = find_containers_in_hangars(
                    station_id,
                    hangars_filter,
                    sde_type_ids,
                    corp_assets_data,
                    throw_when_not_found=throw_when_not_found)

        elif throw_when_not_found:
            raise Exception('Not found station identity and name!!!')

        else:
            print("ERROR: not found station identity and name!!!")
            station_id = None
            station_name = None

        station_containers["station_id"] = station_id
        station_containers["station_name"] = station_name

        # получение названий контейнеров и сохранение из в списке контейнеров
        for __cont_dict in station_containers["containers"]:
            __item_id = __cont_dict["id"]
            __item_name = next((an for an in corp_ass_names_data if an["item_id"] == __item_id), None)
            if not (__item_name is None):
                __cont_dict["name"] = __item_name["name"]

        found_containers.append(station_containers)

    return found_containers
