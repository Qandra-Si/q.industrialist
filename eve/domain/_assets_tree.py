from dataclasses import dataclass
from typing import Dict, List

from eve.domain import Asset, TypeIds
from eve.esi.structure_data import StructureData
from eve.domain import InventoryLocation


@dataclass
class AssetTreeItem:
    item_id: int
    type_id: int = None
    index: int = None
    location_id: str = None
    items: List[str] = None


def get_assets_tree(
        corp_assets_data: List[Asset],
        foreign_structures_data: Dict[str, StructureData],
        sde_inv_items: Dict[int, InventoryLocation],
        virtual_hierarchy_by_corpsag=False
) -> Dict[str, AssetTreeItem]:
    """
    https://docs.esi.evetech.net/docs/asset_location_id
    https://forums-archive.eveonline.com/topic/520027/

    Строит дерево в виде:
    { location1: [item1,item2,...], location2: [item3,item4,...] }
    """
    asset_tree: Dict[str, AssetTreeItem] = {}
    stations = []
    # формируем дерево из набора корпоративных ассетов
    for index, asset in enumerate(corp_assets_data):
        item_id = asset.item_id
        location_id = asset.location_id
        location_flag = asset.location_flag
        type_id = asset.type_id
        if not (str(item_id) in asset_tree):
            tree_item = AssetTreeItem(
                item_id=item_id,
                type_id=type_id,
                index=index,
                items=[],
                location_id=location_id
            )
            asset_tree[str(item_id)] = tree_item
        else:
            _update_tree_item(asset_tree, index, item_id, type_id, location_id)

        tree_item = asset_tree[str(item_id)]

        if virtual_hierarchy_by_corpsag and (location_flag[:-1] == "CorpSAG"):
            _update_copr_angar(asset_tree, item_id, location_flag, location_id, tree_item)

        _add_station_if_need(asset, location_id, stations)

        if asset.location_type == "solar_system":
            if (str(asset.location_id) not in asset_tree):
                solar_system = AssetTreeItem(
                    item_id=asset.location_id,
                    type_id=TypeIds.SOLAR_SYSTEM.value,
                    items=[]
                )
                asset_tree[str(asset.location_id)] = solar_system

    # дополняем дерево сведениями о станциях, не принадлежащих корпорации (всё равно,
    # что добавить в список NPC-станции)
    foreign_station_ids = foreign_structures_data.keys()
    for station_id in foreign_station_ids:
        fs = foreign_structures_data[str(station_id)]
        solar_system_id = int(fs.solar_system_id)
        # находим элемент дерева с известным item_id (станцию чужой корпы) и дополняем
        # элемент типом строения и его расположением
        if str(station_id) not in asset_tree:
            station = AssetTreeItem(
                item_id=station_id,
                type_id=fs.type_id,
                items=[],
                location_id=str(solar_system_id),
            )
            asset_tree[str(station_id)] = station

        # находим солнечную систему или добоавляем её в дерево
        if str(solar_system_id) in asset_tree:
            pass
            # asset_tree[str(solar_system_id)].items.append(int(station_id))
        else:
            # TODO: fix it
            asset_tree.update(
                {str(solar_system_id): AssetTreeItem(item_id=solar_system_id, items=[], type_id=5)})  # 5 = Solar System

    # asset_tree[locstr_root].items.append(item_id)

    # дополняем дерево сведениям о расположении NPC-станций (данными из eve sde)
    for station_id in stations:
        station = asset_tree.get(str(station_id), None)
        if not station:
            _fill_ass_tree_with_sde_data(int(station_id), asset_tree, sde_inv_items)

    _apend_items(asset_tree, corp_assets_data)

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


def _apend_items(asset_tree, corp_assets_data):
    # unknown place to collect items with unknown location
    unknown_place = AssetTreeItem(
        item_id=1,
        items=[]
    )
    for asset in asset_tree.values():
        if (asset.location_id != None):
            location = asset_tree.get(str(asset.location_id), None)
            if not location:
                unknown_place.items.append(asset)
                asset.location_id = unknown_place.item_id
            else:
                location.items.append(asset.item_id)
    asset_tree["1"] = unknown_place


def _add_station_if_need(asset, location_id, stations):
    location_type = asset.location_type
    if location_type == "station" and stations.count(location_id) == 0:
        stations.append(location_id)


def _create_or_update_location(asset, asset_tree, item_id, location_id, stations):
    locstr_root = str(location_id)
    location_type = asset.location_type
    if locstr_root not in asset_tree:
        type_id = TypeIds.SOLAR_SYSTEM.value if location_type == "solar_system" else None
        tree_item = AssetTreeItem(item_id=location_id, type_id=type_id, items=[])
        asset_tree[locstr_root] = tree_item


def _update_copr_angar(asset_tree, item_id, location_flag, location_id, asset: AssetTreeItem):
    corpsag_root: str = '{}_{}'.format(location_id, location_flag)
    if corpsag_root not in asset_tree:
        item = AssetTreeItem(
            item_id=corpsag_root,
            items=[],
            location_id=str(location_id),
            type_id=TypeIds.HANGAR_CONTAINER.value,
        )
        asset_tree[corpsag_root] = item

    # move to corp angar virtual root
    asset.location_id = corpsag_root


def _update_tree_item(asset_tree, index, item_id, type_id, location_id):
    tree_item = asset_tree[str(item_id)]
    if not tree_item.type_id:
        tree_item.type_id = type_id
    if not tree_item.index:
        tree_item.index = index
    if not tree_item.location_id:
        tree_item.location_id = location_id


def _fill_ass_tree_with_sde_data(
        location_id: int,
        ass_tree: Dict[str, AssetTreeItem],
        sde_inv_items: Dict[int, InventoryLocation]
):
    if location_id <= 5:
        return
    if not (location_id in sde_inv_items):
        return
    sde_item = sde_inv_items[location_id]
    type_id = sde_item.type_id
    new_location_id = sde_item.parent_location_id

    if not (str(location_id) in ass_tree):
        ass_tree.update({str(location_id): AssetTreeItem(item_id=location_id, type_id=type_id, items=[])})
    else:
        ass_tree[str(location_id)].type_id = type_id

    if type_id > 5:  # останавливаем глубину на Constellation (и не добавляем её в ass_tree)
        ass_tree[str(location_id)].location_id = new_location_id
        ass_tree.update({str(new_location_id): AssetTreeItem(item_id=new_location_id, items=[])})
    if type_id == 5:  # останавливаемся а глубине Solar System
        return
    _fill_ass_tree_with_sde_data(new_location_id, ass_tree, sde_inv_items)


def _get_assets_tree_root(asset_tree: Dict[str, AssetTreeItem], location_id: str):
    item = asset_tree.get(location_id, None)
    while (item is not None) and item.location_id:
        location_id = item.location_id
        item = asset_tree.get(str(location_id), None)
    return location_id
