import q_industrialist_settings


def get_blueprint_progress_status(corp_industry_jobs_data, blueprint_id):
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
        loc_flag = str(bp["location_flag"])
        loc_id = int(bp["location_id"])
        if q_industrialist_settings.g_adopt_for_ri4:
            if not (loc_id in [1033012626278, 1032890037923, 1033063942756, 1033675076928, 1032846295901]):
                continue  # пропускаем все контейнеры, кроме тех, откуда ведётся производство
        # { "CorpSAG6": {} }
        if not (loc_flag in corp_bp_loc_data):
            corp_bp_loc_data.update({loc_flag: {}})
        # { "CorpSAG6": { "1033160348166": {} } }
        if not (loc_id in corp_bp_loc_data[loc_flag]):
            corp_bp_loc_data[loc_flag].update({loc_id: {}})
        # { "CorpSAG6": { "1033160348166": { "30014": {} } } }
        type_id = int(bp["type_id"])
        if not (type_id in corp_bp_loc_data[loc_flag][loc_id]):
            corp_bp_loc_data[loc_flag][loc_id].update({type_id: {}})
        # { "CorpSAG6": { "1033160348166": { "30014": { "o_10_20": {} } } } }
        quantity = int(bp["quantity"])
        blueprint_id = int(bp["item_id"])
        is_blueprint_copy = quantity < -1
        bp_type = 'c' if is_blueprint_copy else 'o'
        material_efficiency = int(bp["material_efficiency"])
        time_efficiency = int(bp["time_efficiency"])
        bp_status = get_blueprint_progress_status(corp_industry_jobs_data, blueprint_id)
        bp_key = '{bpt}_{me}_{te}_{st}'.format(
            bpt=bp_type,
            me=material_efficiency,
            te=time_efficiency,
            st="" if bp_status is None else bp_status[:2])
        runs = int(bp["runs"])
        quantity_or_runs = runs if is_blueprint_copy else quantity if quantity > 0 else 1
        # { "CorpSAG6": { "1033160348166": { "30014": { "o_10_20": { "cp":false,"me":10,..., [] } } } } }
        if not (bp_key in corp_bp_loc_data[loc_flag][loc_id][type_id]):
            corp_bp_loc_data[loc_flag][loc_id][type_id].update({bp_key: {
                "cp": is_blueprint_copy,
                "me": material_efficiency,
                "te": time_efficiency,
                "qr": quantity_or_runs,
                "st": bp_status,
                "itm": []
            }})
        elif is_blueprint_copy:
            corp_bp_loc_data[loc_flag][loc_id][type_id][bp_key]["qr"] = \
            corp_bp_loc_data[loc_flag][loc_id][type_id][bp_key]["qr"] + quantity_or_runs
        # { "CorpSAG6": { "1033160348166": { "30014": { "o_10_20": { "cp":false,"me":10,..., [{"id":?,"q":?,"r":?}, {...}] } } } } }
        corp_bp_loc_data[loc_flag][loc_id][type_id][bp_key]["itm"].append({
            "id": int(bp["item_id"]),
            "q": quantity,
            "r": runs
        })
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
        if not (loc_flag[:-1] == "CorpSAG") and not (loc_flag == "Unlocked"):
            continue  # пропускаем дронов в дронбеях, патроны в карго, корабли в ангарах и т.п.
        loc_id = int(a["location_id"])
        if not (containers_filter is None) and (containers_filter.count(loc_id) == 0):
            continue  # пропускаем все контейнеры, кроме тех, откуда ведётся производство
        quantity = int(a["quantity"])
        # { "DroneBay": {} }
        if not (loc_flag in corp_ass_loc_data):
            corp_ass_loc_data.update({loc_flag: {}})
        # { "DroneBay": { "1033692665735": {} } }
        if not (loc_id in corp_ass_loc_data[loc_flag]):
            corp_ass_loc_data[loc_flag].update({loc_id: {}})
        # { "DroneBay": { "1033692665735": { "2488": { "q":? } } } }
        if not (type_id in corp_ass_loc_data[loc_flag][loc_id]):
            corp_ass_loc_data[loc_flag][loc_id].update({type_id: quantity})
        else:
            corp_ass_loc_data[loc_flag][loc_id][type_id] = quantity + corp_ass_loc_data[loc_flag][loc_id][type_id]
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
    if type_id == 5:  # останавливаемся а глубине Solar System
        return
    fill_ass_tree_with_sde_data(new_location_id, ass_tree, sde_inv_items)


def get_assets_tree(corp_assets_data, foreign_structures_data, sde_inv_items):
    """
    https://docs.esi.evetech.net/docs/asset_location_id
    https://forums-archive.eveonline.com/topic/520027/

    Строит дерево в виде:
    { location1: [item1,item2,...], location2: [item3,item4,...] }
    """
    ass_tree = {}
    stations = []
    # формируем дерево из набора корпоративных ассетов
    for a in corp_assets_data:
        item_id = int(a["item_id"])
        location_id = int(a["location_id"])
        type_id = int(a["type_id"])
        if (str(location_id) in ass_tree) and ("items" in ass_tree[str(location_id)]):
            ass_tree[str(location_id)]["items"].append(item_id)
        else:
            ass_tree.update({str(location_id): {"items": [item_id]}})
            location_type = a["location_type"]
            if location_type == "solar_system":
                ass_tree[str(location_id)]["type_id"] = 5  # Solar System
            elif location_type == "station":
                if stations.count(location_id) == 0:
                    stations.append(location_id)
        if not (str(item_id) in ass_tree):
            ass_tree.update({str(item_id): {"type_id": type_id}})
        elif not ("type_id" in ass_tree[str(item_id)]):
            ass_tree[str(item_id)]["type_id"] = type_id
    for a in corp_assets_data:
        item_id = int(a["item_id"])
        location_id = int(a["location_id"])
        if str(item_id) in ass_tree:
            itm = ass_tree[str(item_id)]
            if not ("location_id" in itm):
                itm["location_id"] = location_id
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
                roots.append(int(root))
        ass_tree["roots"] = roots
    return ass_tree
