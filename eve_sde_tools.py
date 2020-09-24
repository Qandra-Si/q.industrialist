""" Q.Industrialist (desktop/mobile)

run the following command from this directory as the root:

>>> python eve_sde_tools.py --cache_dir=~/.q_industrialist
"""
import sys
import os
import getopt
import yaml
import json
from yaml import SafeLoader


# type=static_data_interface : unpacked SDE-yyyymmdd-TRANQUILITY.zip
def __get_yaml(type, sub_url, item):
    f_name = '{cwd}/{type}/{url}'.format(type=type, cwd=os.getcwd(), url=sub_url)
    item_to_search = "\n{}\n".format(item)
    with open(f_name, 'r', encoding='utf8') as f:
        contents = f.read()
        beg = contents.find(item_to_search)
        if beg == -1:
            return {}
        beg = beg + len(item_to_search)
        # debug:print("{} = {}".format(item, beg))
        end = beg + 1
        length = len(contents)
        while True:
            end = contents.find("\n", end)
            if (end == -1) or (end == (length-1)):
                yaml_contents = contents[beg:length].encode('utf-8')
                break
            if contents[end+1] == ' ':
                end = end + 1
            else:
                yaml_contents = contents[beg:beg+end-beg].encode('utf-8')
                break
        yaml_data = yaml.load(yaml_contents, Loader=SafeLoader)
        return yaml_data


def __get_source_name(subname, name):
    return '{cwd}/{type}/{url}'.format(cwd=os.getcwd(), type="static_data_interface", url="{}/{}.yaml".format(subname, name))


def __get_converted_name(ws_dir, name):
    return '{dir}/sde_cache/.converted_{nm}.json'.format(dir=ws_dir, nm=name)


def read_converted(ws_dir, name):
    f_name_json = __get_converted_name(ws_dir, name)
    with open(f_name_json, 'r', encoding='utf8') as f:
        s = f.read()
        json_data = (json.loads(s))
        return json_data


def __rebuild(ws_dir, subname, name, items_to_stay=None):
    keys_to_stay = []
    dicts_to_stay = []
    if not (items_to_stay is None):
        for i2s in items_to_stay:
            if isinstance(i2s, str):
                keys_to_stay.append(i2s)
            elif isinstance(i2s, dict):
                dicts_to_stay.append(i2s)
    f_name_yaml = __get_source_name(subname, name)
    f_name_json = __get_converted_name(ws_dir, name)
    with open(f_name_yaml, 'r', encoding='utf8') as f:
        try:
            # yaml
            s = f.read()
            yaml_data = yaml.load(s, Loader=SafeLoader)
            # clean yaml
            for yd in yaml_data:
                if isinstance(yaml_data, dict) and (isinstance(yd, str) or isinstance(yd, int)):
                    yd_ref =yaml_data[yd]
                elif isinstance(yaml_data, list):
                    yd_ref = yd
                else:
                    break  # нет смысла продолжать, т.к. все элементы в файлы однотипны
                while True:
                    keys1 = yd_ref.keys()
                    deleted1 = False
                    for key1 in keys1:                  # ["iconID","name"]
                        found1 = False
                        if key1 in keys_to_stay:        # "name"
                            continue
                        for d2s in dicts_to_stay:       # [{"name", ["en"]}]
                            k2s = d2s.get(key1, None)   # ["en"]
                            if k2s is None:
                                continue
                            found1 = True
                            while True:
                                keys2 = yd_ref[key1].keys()  # ["en","de","ru"]
                                deleted2 = False
                                for key2 in keys2:
                                    if not (key2 in k2s):           # "en"
                                        del yd_ref[key1][key2]
                                        deleted2 = True
                                        break
                                if deleted2:
                                    continue
                                break
                        if not found1:
                            del yd_ref[key1]
                            deleted1 = True
                            break
                    if deleted1:
                        continue
                    break
            # json
            s = json.dumps(yaml_data, indent=1, sort_keys=False)
            f = open(f_name_json, "wt+", encoding='utf8')
            f.write(s)
        finally:
            f.close()


def __rebuild_list2dict_by_key(ws_dir, name, key, val=None):
    # перечитываем построенный файл и преобразуем его из списка в справочник
    # при этом одно из значений элементов списка выбирается ключём в справочнике,
    # в том числ поддерживается возможность упростить
    #  [key1: {key1_2: val1_2}, key2: {key2_1: val2_2}]
    # до
    #  {"key1": val1_2, "key2": val2_2}
    # задав необязательный val-параметр
    lst = read_converted(ws_dir, name)
    if not isinstance(lst, list):
        return
    dct = {}
    for itm in lst:
        if val is None:
            key_value = itm[key]
            del itm[key]
            dct.update({str(key_value): itm})
        else:
            dct.update({str(itm[key]): itm[val]})
    # json
    f_name_json = __get_converted_name(ws_dir, name)
    s = json.dumps(dct, indent=1, sort_keys=False)
    f = open(f_name_json, "wt+", encoding='utf8')
    f.write(s)


def get_item_name_by_type_id(type_ids, type_id):
    if not (str(type_id) in type_ids):
        name = type_id
    else:
        type_dict = type_ids[str(type_id)]
        if ("name" in type_dict) and ("en" in type_dict["name"]):
            name = type_dict["name"]["en"]
        else:
            name = type_id
    return name


def get_type_id_by_item_name(type_ids, name):
    keys = type_ids.keys()
    for type_id in keys:
        type_dict = type_ids[str(type_id)]
        if ("name" in type_dict) and ("en" in type_dict["name"]):
            __name = type_dict["name"]["en"]
            if __name == name:
                return int(type_id)
    return None


def get_market_group_by_type_id(type_ids, type_id):
    if not (str(type_id) in type_ids):
        return None
    type_dict = type_ids[str(type_id)]
    if "marketGroupID" in type_dict:
        return type_dict["marketGroupID"]
    return None


def get_root_market_group_by_type_id(type_ids, market_groups, type_id):
    group_id = get_market_group_by_type_id(type_ids, type_id)
    if group_id is None:
        return None
    __group_id = group_id
    while True:
        __grp1 = market_groups[str(__group_id)]
        if "parentGroupID" in __grp1:
            __group_id = __grp1["parentGroupID"]
        else:
            return __group_id


def get_basis_market_group_by_type_id(type_ids, market_groups, type_id):
    group_id = get_market_group_by_type_id(type_ids, type_id)
    if group_id is None:
        return None
    __group_id = group_id
    while True:
        if __group_id in [# 475,  # Manufacture & Research
                          # 533,  # Materials (parent:475, см. ниже)
                          1035,  # Components (parent:475)
                          1872,  # Research Equipment (parent:475)
                          955,  # Ship and Module Modifications
                          1112,  # Subsystems (parent:955)
                         ]:
            return __group_id
        __grp1 = market_groups[str(__group_id)]
        if "parentGroupID" in __grp1:
            __parent_group_id = __grp1["parentGroupID"]
            # группа материалов для целей производства должна делиться на подгруппы (производство и заказы
            # в каждой из них решается индивидуально)
            if __parent_group_id in [533,  # Materials
                                     1034,  # Reaction Materials
                                     477,  # Structures (чтобы было понятнее содержимое accounting-отчётов)
                                     ]:
                return __group_id
            __group_id = __parent_group_id
        else:
            return __group_id
    return group_id


def is_type_id_nested_into_market_group(type_id, market_groups, sde_type_ids, sde_market_groups):
    group_id = get_market_group_by_type_id(sde_type_ids, type_id)
    if group_id is None:
        return None
    __group_id = group_id
    while True:
        if int(__group_id) in market_groups:
            return True
        __grp1 = sde_market_groups[str(__group_id)]
        if "parentGroupID" in __grp1:
            __group_id = __grp1["parentGroupID"]
        else:
            return False


def get_blueprint_manufacturing_materials(blueprints, type_id):
    if not (str(type_id) in blueprints):
        return None
    else:
        bp = blueprints[str(type_id)]
        if not ("activities" in bp):
            return None
        elif not ("manufacturing" in bp["activities"]):
            return None
        elif not ("materials" in bp["activities"]["manufacturing"]):
            return None
        else:
            materials = bp["activities"]["manufacturing"]["materials"]
            return materials


def get_blueprint_reaction_materials(blueprints, type_id):
    if not (str(type_id) in blueprints):
        return None
    else:
        bp = blueprints[str(type_id)]
        if not ("activities" in bp):
            return None
        elif not ("reaction" in bp["activities"]):
            return None
        elif not ("materials" in bp["activities"]["reaction"]):
            return None
        else:
            materials = bp["activities"]["reaction"]["materials"]
            return materials


def get_materials_for_blueprints(sde_bp_materials):
    """
    Построение списка модулей и ресурсов, которые используются в производстве
    """
    materials_for_bps = []
    for bp in sde_bp_materials:
        __bpm1 = sde_bp_materials[bp]["activities"]
        if "manufacturing" in __bpm1:
            __bpm2 = __bpm1["manufacturing"]
            if "materials" in __bpm2:
                __bpm3 = __bpm2["materials"]
                for m in __bpm3:
                    if "typeID" in m:
                        type_id = int(m["typeID"])
                        if 0 == materials_for_bps.count(type_id):
                            materials_for_bps.append(type_id)
    return materials_for_bps


def get_research_materials_for_blueprints(sde_bp_materials):
    """
    Построение списка модулей и ресурсов, которые используются в производстве
    """
    research_materials_for_bps = []
    for bp in sde_bp_materials:
        __bpm1 = sde_bp_materials[bp]["activities"]
        if "research_material" in __bpm1:
            __bpm2 = __bpm1["research_material"]
            if "materials" in __bpm2:
                __bpm3 = __bpm2["materials"]
                for m in __bpm3:
                    if "typeID" in m:
                        type_id = int(m["typeID"])
                        if 0 == research_materials_for_bps.count(type_id):
                            research_materials_for_bps.append(type_id)
    return research_materials_for_bps


def get_blueprint_type_id_by_product_id(product_id, sde_bp_materials):
    """
    Поиск идентификатора чертежа по известному идентификатору manufacturing-продукта
    """
    for bp in sde_bp_materials:
        __bpm1 = sde_bp_materials[bp]["activities"]
        if "manufacturing" in __bpm1:
            __bpm2 = __bpm1["manufacturing"]
            if "products" in __bpm2:
                __bpm3 = __bpm2["products"]
                for m in __bpm3:
                    if "typeID" in m:
                        type_id = int(m["typeID"])
                        if product_id == type_id:
                            return int(bp), sde_bp_materials[bp]
    return None, None


def get_market_groups_tree_root(groups_tree, group_id):
    if not (str(group_id) in groups_tree):
        return group_id
    itm = groups_tree[str(group_id)]
    if not ("parent_id" in itm):
        return group_id
    return get_market_groups_tree_root(groups_tree, itm["parent_id"])


def get_market_groups_tree(sde_market_groups):
    """
    Строит дерево в виде:
    { group1: [sub1,sub2,...], group2: [sub3,sub4,...] }
    """
    groups_tree = {}
    sde_market_groups_keys = sde_market_groups.keys()
    for group_id in sde_market_groups_keys:
        mg = sde_market_groups[str(group_id)]
        if "parentGroupID" in mg:
            parent_id = mg["parentGroupID"]
            if (str(parent_id) in groups_tree) and ("items" in groups_tree[str(parent_id)]):
                groups_tree[str(parent_id)]["items"].append(int(group_id))
            else:
                groups_tree.update({str(parent_id): {"items": []}})
            groups_tree.update({str(group_id): {"parent_id": int(parent_id)}})
        else:
            groups_tree.update({str(group_id): {}})
    groups_tree_keys = groups_tree.keys()
    if len(groups_tree_keys) > 0:
        roots = []
        for k in groups_tree_keys:
            root = get_market_groups_tree_root(groups_tree, k)
            if 0 == roots.count(int(root)):
                roots.append(int(root))
        groups_tree["roots"] = roots
    return groups_tree


def __rebuild_icons(ws_dir, name):
    icons = read_converted(ws_dir, name)
    icon_keys = icons.keys()
    for ik in icon_keys:
        icon_file = icons[str(ik)]["iconFile"]
        if icon_file[:22].lower() == "res:/ui/texture/icons/":
            icon_file = '{}/{}'.format("Icons/items", icon_file[22:])
            icons[str(ik)]["iconFile"] = icon_file
    # json
    f_name_json = __get_converted_name(ws_dir, name)
    s = json.dumps(icons, indent=1, sort_keys=False)
    f = open(f_name_json, "wt+", encoding='utf8')
    f.write(s)


def __clean_positions(ws_dir, name):
    positions = read_converted(ws_dir, name)
    positions = [i for i in positions if (i["x"] != 0.0) and (i["y"] != 0.0) and (i["z"] != 0.0)]
    # json
    f_name_json = __get_converted_name(ws_dir, name)
    s = json.dumps(positions, indent=1, sort_keys=False)
    f = open(f_name_json, "wt+", encoding='utf8')
    f.write(s)


def main():  # rebuild .yaml files
    exit_or_wrong_getopt = None
    workspace_cache_files_dir = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help", "cache_dir="])
    except getopt.GetoptError:
        exit_or_wrong_getopt = 2
    if exit_or_wrong_getopt is None:
        for opt, arg in opts:  # noqa
            if opt in ('-h', "--help"):
                exit_or_wrong_getopt = 0
                break
            elif opt in ("--cache_dir"):
                workspace_cache_files_dir = arg[:-1] if arg[-1:] == '/' else arg
        if workspace_cache_files_dir is None:
            exit_or_wrong_getopt = 0
    if not (exit_or_wrong_getopt is None):
        print('Usage: {app} --cache_dir=/tmp\n'.
            format(app=sys.argv[0]))
        sys.exit(exit_or_wrong_getopt)

    print("Rebuilding typeIDs.yaml file...")
    sys.stdout.flush()
    __rebuild(workspace_cache_files_dir, "fsd", "typeIDs", ["basePrice", "iconID", "published", "marketGroupID", {"name": ["en"]}, "volume"])
    
    print("Rebuilding invPositions.yaml file...")
    sys.stdout.flush()
    __rebuild(workspace_cache_files_dir, "bsd", "invPositions", ["itemID", "x", "y", "z"])
    __clean_positions(workspace_cache_files_dir, "invPositions")
    print("Reindexing .converted_invPositions.json file...")
    sys.stdout.flush()
    __rebuild_list2dict_by_key(workspace_cache_files_dir, "invPositions", "itemID")

    print("Rebuilding marketGroups.yaml file...")
    sys.stdout.flush()
    __rebuild(workspace_cache_files_dir, "fsd", "marketGroups", ["iconID", {"nameID": ["en"]}, "parentGroupID"])
    
    print("Rebuilding iconIDs.yaml file...")
    sys.stdout.flush()
    __rebuild(workspace_cache_files_dir, "fsd", "iconIDs", ["iconFile"])
    print("Reindexing .converted_iconIDs.json file...")
    __rebuild_icons(workspace_cache_files_dir, "iconIDs")
    
    print("Rebuilding invNames.yaml file...")
    sys.stdout.flush()
    __rebuild(workspace_cache_files_dir, "bsd", "invNames", ["itemID", "itemName"])
    print("Reindexing .converted_invNames.json file...")
    sys.stdout.flush()
    __rebuild_list2dict_by_key(workspace_cache_files_dir, "invNames", "itemID", "itemName")
    
    print("Rebuilding invItems.yaml file...")
    sys.stdout.flush()
    __rebuild(workspace_cache_files_dir, "bsd", "invItems", ["itemID", "locationID", "typeID"])
    print("Reindexing .converted_invItems.json file...")
    sys.stdout.flush()
    __rebuild_list2dict_by_key(workspace_cache_files_dir, "invItems", "itemID")

    print("Rebuilding typeIDs.yaml file...")
    sys.stdout.flush()
    __rebuild(workspace_cache_files_dir, "fsd", "typeIDs", ["basePrice", "iconID", "published", "marketGroupID", {"name": ["en"]}, "volume"])

    print("Rebuilding blueprints.yaml file...")
    sys.stdout.flush()
    __rebuild(workspace_cache_files_dir, "fsd", "blueprints", ["activities"])


def test():
    data = __get_yaml("static_data_interface", 'fsd/typeIDs.yaml', "32859:")
    # for d in data:
    #     print("{}".format(d))
    print("{}".format(data["name"]["en"]))  # Small Standard Container Blueprint

    data = __get_yaml("static_data_interface", 'bsd/invUniqueNames.yaml', "    itemID: 60003760")
    # for d in data:
    #     print("{}".format(d))
    print("{}".format(data["itemName"]))  # Jita IV - Moon 4 - Caldari Navy Assembly Plant


if __name__ == "__main__":
    main()
    # test()
