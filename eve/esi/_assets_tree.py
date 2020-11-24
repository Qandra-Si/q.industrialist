from typing import Dict, List

from eve.domain import Asset
from eve.esi.structure_data import StructureData
from eve.domain import InventoryLocation


def get_assets_tree(
        corp_assets_data: List[Asset],
        foreign_structures_data: Dict[str, StructureData],
        sde_inv_items: Dict[int, InventoryLocation],
        virtual_hierarchy_by_corpsag= False
) -> Dict[str, Dict]:
    """
    https://docs.esi.evetech.net/docs/asset_location_id
    https://forums-archive.eveonline.com/topic/520027/

    Строит дерево в виде:
    { location1: [item1,item2,...], location2: [item3,item4,...] }
    """
    asset_tree: Dict[str, Dict] = {}
    stations = []
    # формируем дерево из набора корпоративных ассетов
    for a in enumerate(corp_assets_data):
        item_id = a[1].item_id
        location_id = a[1].location_id
        location_flag = a[1].location_flag
        type_id = a[1].type_id

        if virtual_hierarchy_by_corpsag and (location_flag[:-1] == "CorpSAG"):
            corpsag_root = '{}_{}'.format(location_id, location_flag)
            virtual_root = str(location_id)
            if (corpsag_root in asset_tree) and ("items" in asset_tree[corpsag_root]):
                asset_tree[corpsag_root]["items"].append(item_id)
            else:
                asset_tree.update({corpsag_root: {"items": [item_id],
                                                "location_id": virtual_root,
                                                "type_id": 41567}})  # Hangar Container
            if (virtual_root in asset_tree) and ("items" in asset_tree[virtual_root]):
                if asset_tree[virtual_root]["items"].count(corpsag_root) == 0:
                    asset_tree[virtual_root]["items"].append(corpsag_root)
            else:
                asset_tree.update({virtual_root: {"items": [corpsag_root]}})
        else:
            locstr_root = str(location_id)
            if (locstr_root in asset_tree) and ("items" in asset_tree[locstr_root]):
                asset_tree[locstr_root]["items"].append(item_id)
            else:
                asset_tree.update({locstr_root: {"items": [item_id]}})
                location_type = a[1].location_type
                if location_type == "solar_system":
                    asset_tree[locstr_root]["type_id"] = 5  # Solar System
                elif location_type == "station":
                    if stations.count(location_id) == 0:
                        stations.append(location_id)
        if not (str(item_id) in asset_tree):
            asset_tree.update({str(item_id): {"type_id": type_id, "index": a[0]}})
        else:
            __a = asset_tree[str(item_id)]
            if not ("type_id" in __a):
                __a["type_id"] = type_id
            if not ("index" in __a):
                __a["index"] = a[0]
    # прописываем location_id парамтеры в каждом элементе по известному item_id
    for a in enumerate(corp_assets_data):
        item_id = str(a[1].item_id)
        location_id = str(a[1].location_id)
        if virtual_hierarchy_by_corpsag:
            location_flag = a[1].location_flag
            virtual_root = '{}_{}'.format(location_id, location_flag) if location_flag[:-1] == "CorpSAG" else location_id
        else:
            virtual_root = location_id
        if item_id in asset_tree:
            __a = asset_tree[item_id]
            if not ("location_id" in __a):
                __a["location_id"] = virtual_root
            if not ("type_id" in __a):
                __a["type_id"] = a[1].type_id
            if not ("index" in __a):
                __a["index"] = a[0]
    # дополняем дерево сведениями о станциях, не принадлежащих корпорации (всё равно,
    # что добавить в список NPC-станции)
    foreign_station_ids = foreign_structures_data.keys()
    for station_id in foreign_station_ids:
        fs = foreign_structures_data[str(station_id)]
        solar_system_id = int(fs.solar_system_id)
        # находим элемент дерева с известным item_id (станцию чужой корпы) и дополняем
        # элемент типом строения и его расположением
        station = asset_tree[str(station_id)]
        station["location_id"] = solar_system_id
        station["type_id"] = fs.type_id
        # находим солнечную систему или добоавляем её в дерево
        if str(solar_system_id) in asset_tree:
            asset_tree[str(solar_system_id)]["items"].append(int(station_id))
        else:
            asset_tree.update({str(solar_system_id): {"items": [int(station_id)], "type_id": 5}})  # 5 = Solar System
    # дополняем дерево сведениям о расположении NPC-станций (данными из eve sde)
    for station_id in stations:
        a = asset_tree[str(station_id)]
        if not ("type_id" in a):
            if stations.count(int(station_id)):
                _fill_ass_tree_with_sde_data(int(station_id), asset_tree, sde_inv_items)
    # формируем корни дерева (станции и системы, с которых начинается общая иерархия)
    ass_keys = asset_tree.keys()
    if len(ass_keys) > 0:
        roots = []
        for k in ass_keys:
            root = _get_assets_tree_root(asset_tree, k)
            if 0 == roots.count(int(root)):
                roots.append(int(root))  # составные root-ы типа 123456_CorpASG2 сюда не попадают, т.к. не корни
        asset_tree["roots"] = roots
    return asset_tree


def _fill_ass_tree_with_sde_data(location_id: int, ass_tree, sde_inv_items: Dict[int, InventoryLocation]):
    if location_id <= 5:
        return
    if not (location_id in sde_inv_items):
        return
    sde_item = sde_inv_items[location_id]
    type_id = sde_item.type_id
    new_location_id = sde_item.parent_location_id
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
