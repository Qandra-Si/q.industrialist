from typing import Dict

from eve.sde import SDEItem


def get_assets_tree(
        corp_assets_data,
        foreign_structures_data,
        sde_inv_items: Dict[int, SDEItem],
        virtual_hierarchy_by_corpsag=False
):
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
                _fill_ass_tree_with_sde_data(int(station_id), ass_tree, sde_inv_items)
    # формируем корни дерева (станции и системы, с которых начинается общая иерархия)
    ass_keys = ass_tree.keys()
    if len(ass_keys) > 0:
        roots = []
        for k in ass_keys:
            root = _get_assets_tree_root(ass_tree, k)
            if 0 == roots.count(int(root)):
                roots.append(int(root))  # составные root-ы типа 123456_CorpASG2 сюда не попадают, т.к. не корни
        ass_tree["roots"] = roots
    return ass_tree


def _fill_ass_tree_with_sde_data(location_id: int, ass_tree, sde_inv_items: Dict[int, SDEItem]):
    if location_id <= 5:
        return
    if not (location_id in sde_inv_items):
        return
    sde_item = sde_inv_items[location_id]
    type_id = sde_item.typeID
    new_location_id = sde_item.locationID
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
    _fill_ass_tree_with_sde_data(new_location_id, ass_tree, sde_inv_items)


def _get_assets_tree_root(ass_tree, location_id):
    if not (str(location_id) in ass_tree):
        return location_id
    itm = ass_tree[str(location_id)]
    if not ("location_id" in itm):
        return location_id
    return _get_assets_tree_root(ass_tree, itm["location_id"])
