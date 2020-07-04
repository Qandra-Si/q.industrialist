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


def get_assets_containers_ids(corp_assets_data):
    ass_cont_ids = []
    for a in corp_assets_data:
        if not a["is_singleton"]:
            continue  # пропускаем экземпляры контейнеров, сложенные в стопки (у них нет уник. id и названий тоже не будет)
        loc_flag = str(a["location_flag"])
        if not (loc_flag[:-1] == "CorpSAG") and not (loc_flag == "Unlocked"):
            continue  # пропускаем дронов в дронбеях, патроны в карго, корабли в ангарах и т.п.
        if a["type_id"] in [17363,   # Small Audit Log Secure Container
                            17364,   # Medium Audit Log Secure Container
                            17365,   # Large Audit Log Secure Container
                            17366,   # Station Container
                            17367,   # Station Vault Container
                            17368]:  # Station Warehouse Container
            ass_cont_ids.append(a["item_id"])
    return ass_cont_ids
