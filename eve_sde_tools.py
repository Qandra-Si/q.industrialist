""" Q.Industrialist (desktop/mobile)

run the following command from this directory as the root:

>>> python eve_sde_tools.py --cache_dir=~/.q_industrialist
>>> python q_dictionaries.py --category=all --cache_dir=~/.q_industrialist
"""
import sys
import os
import getopt
import yaml
import json
from yaml import SafeLoader
from pathlib import Path

import pyfa_conversions as conversions


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
            # mkdir
            Path('{dir}/sde_cache'.format(dir=ws_dir)).mkdir(parents=True, exist_ok=True)
            # json
            s = json.dumps(yaml_data, indent=1, sort_keys=False)
            f = open(f_name_json, "wt+", encoding='utf8')
            f.write(s)
            del yaml_data
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
    del dct
    del lst


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


def convert_sde_type_ids(type_ids):
    named_type_ids = {}
    keys = type_ids.keys()
    for type_id in keys:
        type_dict = type_ids[str(type_id)]
        if ("name" in type_dict) and ("en" in type_dict["name"]):
            __name = type_dict["name"]["en"]
            named_dict = type_dict.copy()
            del named_dict["name"]
            named_dict["id"] = int(type_id)
            named_type_ids.update({__name: named_dict})
    return named_type_ids


def find_type_id_by_item_name_ex(named_type_ids, name):
    __item = named_type_ids.get(name)
    if __item is None:
        return None, None
    return __item["id"], __item


def find_type_id_by_item_name(named_type_ids, name):
    type_id, __dummy0 = find_type_id_by_item_name_ex(named_type_ids, name)
    return type_id


def get_type_id_by_item_name_ex(type_ids, name):
    keys = type_ids.keys()
    for type_id in keys:
        type_dict = type_ids[str(type_id)]
        if ("name" in type_dict) and ("en" in type_dict["name"]):
            __name = type_dict["name"]["en"]
            if __name == name:
                return int(type_id), type_dict
    return None, None


def get_type_id_by_item_name(type_ids, name):
    type_id, __dummy0 = get_type_id_by_item_name_ex(type_ids, name)
    return type_id


def get_market_group_name_by_id(sde_type_ids, group_id):
    group_sid = str(group_id)
    if group_sid in sde_type_ids:
        group_dict = sde_type_ids[group_sid]
        if ("nameID" in group_dict) and ("en" in group_dict["nameID"]):
            return group_dict["nameID"]["en"]
        else:
            return group_sid
    return group_sid


def get_market_group_by_type_id(sde_type_ids, type_id):
    if not (str(type_id) in sde_type_ids):
        return None
    type_dict = sde_type_ids[str(type_id)]
    if "marketGroupID" in type_dict:
        return type_dict["marketGroupID"]
    return None


def get_market_group_by_name(sde_market_groups, name):
    for grp in sde_market_groups.items():
        if name == grp[1]["nameID"]["en"]:
            return grp  # id=grp[0], dict=grp[1]
    return None


def get_market_group_id_by_name(sde_market_groups, name):
    grp = get_market_group_by_name(sde_market_groups, name)
    return None if grp is None else grp[0]


def get_market_groups_chain_by_type_id(sde_type_ids, sde_market_groups, type_id):
    group_id = get_market_group_by_type_id(sde_type_ids, type_id)
    if group_id is None:
        return []
    __group_id = group_id
    __groups_chain = [group_id]
    while True:
        __grp1 = sde_market_groups[str(__group_id)]
        if "parentGroupID" in __grp1:
            __group_id = __grp1["parentGroupID"]
            # переворачиваем элементы списка, где корень будет в его начале
            __groups_chain.insert(0, __group_id)
        else:
            return __groups_chain


def get_root_market_group_by_type_id(sde_type_ids, sde_market_groups, type_id):
    groups_chain = get_market_groups_chain_by_type_id(sde_type_ids, sde_market_groups, type_id)
    if (groups_chain is None) or not groups_chain:
        return None
    return groups_chain[0]


def get_basis_market_group_by_group_id(sde_market_groups, group_id: int):
    __group_id = group_id
    while True:
        if __group_id in [# 475,  # Manufacture & Research
                          # 533,  # Materials (parent:475, см. ниже)
                          # 1035, # Components (parent:475)
                          1872,   # Research Equipment (parent:475)
                          955,    # Ship and Module Modifications
                          1112,   # Subsystems (parent:955)
                         ]:
            return __group_id
        __grp1 = sde_market_groups[str(__group_id)]
        if "parentGroupID" in __grp1:
            __parent_group_id = __grp1["parentGroupID"]
            # группа материалов для целей производства должна делиться на подгруппы (производство и заказы
            # в каждой из них решается индивидуально)
            if __parent_group_id in [533,  # Materials
                                     1034, # Reaction Materials
                                     477,  # Structures (чтобы было понятнее содержимое accounting-отчётов)
                                     1035, # Components (parent:475)
                                     ]:
                return __group_id
            __group_id = __parent_group_id
        else:
            return __group_id


def get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, type_id):
    group_id = get_market_group_by_type_id(sde_type_ids, type_id)
    if group_id is None:
        return None
    return get_basis_market_group_by_group_id(sde_market_groups, int(group_id))


def is_type_id_nested_into_market_group(type_id, market_groups, sde_type_ids, sde_market_groups):
    groups_chain = get_market_groups_chain_by_type_id(sde_type_ids, sde_market_groups, type_id)
    if groups_chain is None:
        return None
    return bool(set(groups_chain) & set(market_groups))


def get_blueprint_any_activity(blueprints, activity: str, type_id: int):
    #  manufacturing - производство
    #  invention - запуск инвентов
    #  copying - копирка
    #  research_material - запуск ME
    #  research_time - запуск TE
    #  reaction - реакции
    if activity in ['manufacturing', 'invention', 'copying', 'research_material', 'research_time', 'reaction']:
        if not (str(type_id) in blueprints):
            return None
        else:
            bp = blueprints[str(type_id)]
            bp1 = bp.get('activities')
            if bp1 is None:
                return None
            bp2 = bp1.get(activity)
            if bp2 is None:
                return None
            bp3 = bp2.get('materials')
            if bp3 is None:
                return None
            return bp2
    else:
        return None


def get_blueprint_any_materials(blueprints, activity: str, type_id: int):
    a = get_blueprint_any_activity(blueprints, activity, type_id)
    if a is None:
        return None
    return a['materials']


def get_blueprint_manufacturing_activity(blueprints, type_id: int):
    return get_blueprint_any_activity(blueprints, 'manufacturing', type_id)


def get_blueprint_manufacturing_materials(blueprints, type_id: int):
    return get_blueprint_any_materials(blueprints, 'manufacturing', type_id)


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


def get_products_for_blueprints(sde_bp_materials, activity="manufacturing"):
    """
    Построение списка продуктов, которые появляются в результате производства
    """
    products_for_bps = []
    for bp in sde_bp_materials:
        __bpm2 = sde_bp_materials[bp]["activities"].get(activity)
        if not __bpm2:
            continue
        __bpm3 = __bpm2.get("products")
        if not __bpm3:
            continue
        for m in __bpm3:
            type_id: int = m.get("typeID")
            if 0 == products_for_bps.count(type_id):
                products_for_bps.append(type_id)
    return products_for_bps


def get_blueprint_type_id_by_product_id(product_id, sde_bp_materials, activity="manufacturing"):
    """
    Поиск идентификатора чертежа по известному идентификатору manufacturing-продукта
    """
    for bp in sde_bp_materials:
        __bpm1 = sde_bp_materials[bp]["activities"]
        if activity in __bpm1:
            __bpm2 = __bpm1[activity]
            if "products" in __bpm2:
                __bpm3 = __bpm2["products"]
                for m in __bpm3:
                    type_id = int(m["typeID"])
                    if product_id == type_id:
                        return int(bp), sde_bp_materials[bp]
    return None, None


def get_blueprint_type_id_by_manufacturing_product_id(product_id, sde_bp_materials):
    a, b = get_blueprint_type_id_by_product_id(product_id, sde_bp_materials, activity="manufacturing")
    return a, b


def get_blueprint_type_id_by_invention_product_id(product_id, sde_bp_materials):
    a, b = get_blueprint_type_id_by_product_id(product_id, sde_bp_materials, activity="invention")
    return a, b


def get_product_by_blueprint_type_id(blueprint_type_id, activity_id, sde_bp_materials):
    """
    Поиск идентификатора manufacturing/reaction-продукта по известному идентификатору чертежа
    """
    __bpm0 = sde_bp_materials.get(str(blueprint_type_id), None)
    if __bpm0 is None:
        return None, None, None
    __bpm1 = __bpm0.get("activities", None)
    if __bpm1 is None:
        return None, None, None
    __bpm2 = None
    if activity_id == 1:
        if "manufacturing" in __bpm1:
            __bpm2 = __bpm1["manufacturing"]
    elif activity_id == 8:
        if "invention" in __bpm1:
            __bpm2 = __bpm1["invention"]
    elif activity_id in (9, 11):
        if "reaction" in __bpm1:
            __bpm2 = __bpm1["reaction"]
    if __bpm2 is None:
        return None, None, None
    __bpm3 = __bpm2.get("products")
    for m in __bpm3:
        product_id = int(m["typeID"])
        quantity = int(m["quantity"])
        return product_id, quantity, __bpm2["materials"]
    return None, None, None


def get_manufacturing_product_by_blueprint_type_id(blueprint_type_id, sde_bp_materials):
    """
    Поиск идентификатора manufacturing-продукта по известному идентификатору чертежа
    """
    if str(blueprint_type_id) in sde_bp_materials:
        __bpm1 = sde_bp_materials[str(blueprint_type_id)]["activities"]
        if "manufacturing" in __bpm1:
            __bpm2 = __bpm1["manufacturing"]
            if "products" in __bpm2:
                __bpm3 = __bpm2["products"]
                for m in __bpm3:
                    product_id = int(m["typeID"])
                    quantity = int(m["quantity"])
                    return product_id, quantity, __bpm2["materials"]
    return None, None, None


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


# только для работы с текстовыми фитами, где возможно хранятся устаревшие названия модулей
def __try_to_get_type_id_by_item_name(name, sde_named_type_ids):
    __type_id = __item = None
    __item_name = name
    for i in range(10):
        # шаг №0 : поиск item-а в справочнике, актуальном на дату обновления EVE static data resources
        # шаг №1 : поиск item-а в pyfa_conversions-справочнике переименованных модулей
        # шаг №2..9 : повторный поиск item-а в pyfa_conversions, возможны множественные переименования
        __type_id, __item = find_type_id_by_item_name_ex(sde_named_type_ids, name)
        if not (__type_id is None):
            if bool(__item["published"]):
                break
        # пытаемся найти item в pyfa_conversions, возможно он устарел и переименован?
        __converted_name = conversions.all.get(name)
        if __converted_name is None:
            return None, None, None
        # если найден item с другим названием, то пытаемся снова определить его type_id
        __item_name = name = __converted_name
    return __type_id, __item, __item_name


# описание формата см. на этой странице https://www.eveonline.com/ru/article/import-export-fittings
def get_items_list_from_eft(
        eft,
        sde_named_type_ids,
        exclude_specified_meta_groups=None,
        include_only_meta_groups=None):
    __converted = {
        "ship": None,
        "comment": None,
        "eft": eft,
        "items": [],
        "problems": []
    }
    items = __converted["items"]
    problems = __converted["problems"]

    def push_into_problems(name, quantity, is_blueprint_copy, problem):
        __problem_dict = next((p for p in problems if (p["name"] == name) and (p["problem"] == problem)), None)
        if __problem_dict is None:
            __problem_dict = {"name": name, "quantity": int(quantity), "problem": problem}
            if not (is_blueprint_copy is None):
                __problem_dict.update({"is_blueprint_copy": bool(is_blueprint_copy)})
            problems.append(__problem_dict)
        else:
            __problem_dict["quantity"] += int(quantity)

    def push_item_into_problems(item, problem):
        push_into_problems(
            item["name"],
            item["quantity"],
            item["is_blueprint_copy"] if "is_blueprint_copy" in item else None,
            problem
        )

    # начинаем обработку входных данных
    item_names = eft.split("\n")
    for __line in enumerate(item_names):
        __original_name = __line[1].strip()
        # пропускаем пустые строки, и даже не считаем позиции для определения к чему относится
        # модуль, к разъёму малой или большой мощности? т.к. нам надо получить лишь список
        # модулей, из которых состоит фит,... лежат ли они в карго, тоже не имеет значения
        if not __original_name:
            continue
        # пропускаем строки вида [Empty Low slot], [Empty High slot], [Empty Rig slot],...
        if (__original_name[:7] == '[Empty ') and (__original_name[-6:] == ' slot]'):
            continue
        # распаковываем название корабля из первой строки с квадратными скобками,
        # например: [Stratios, Vinnegar Douche's Stratios]
        __quantity = 1
        __ship_flag = False
        __is_blueprint_copy = None
        if __line[0] == 0:
            if (__original_name[:1] == '[') and (__original_name[-1:] == ']'):
                # выполняем поиск названия корабля в строке
                __end = __line[1].find(",")
                if __end < 0:
                    continue
                __converted["comment"] = __original_name[__end+1:-1].strip()
                __original_name = __original_name[1:__end]
                if not __original_name:
                    continue
                __ship_flag = True
        else:
            # попытка найти в конце строке сочетание x?, например: Nanite Repair Paste x50
            __quantity_pos = __original_name.rfind(" x")
            if __quantity_pos > 1:
                __num = __original_name[__quantity_pos + 2:]
                if __num.isnumeric():
                    __quantity = __num
                    __original_name = __original_name[:__quantity_pos]
            # попытка найти в строке сочетание (Copy), например: Vespa I Blueprint (Copy) x2
            __copy_pos = __original_name.rfind(" (Copy)")
            if __copy_pos >= 1:
                __original_name = __original_name.replace(" (Copy)", "")
                __is_blueprint_copy = True
        # попытка получить сведения об item-е по его наименованию
        __item_dicts = None
        __type_id, __item, __name = __try_to_get_type_id_by_item_name(__original_name, sde_named_type_ids)
        # Внимание! если известен __type_id, то с __name и __original_name могут не совпадать!!!
        if not (__type_id is None):
            __item_dicts = [{"name": __name,
                             "type_id": __type_id,
                             "quantity": int(__quantity),
                             "details": __item}]
            if not (__is_blueprint_copy is None) and __is_blueprint_copy:
                __item_dicts[0].update({"is_blueprint_copy": True})
            if __original_name != __name:
                __item_dicts[0].update({"renamed": True})
        else:
            # возможно встретилась ситуация: Sisters Core Probe Launcher,Sisters Core Scanner Probe
            pair = __original_name.split(",")
            if len(pair) == 2:
                __type_id0, __item0, pair[0] = __try_to_get_type_id_by_item_name(pair[0], sde_named_type_ids)
                __type_id1, __item1, pair[1] = __try_to_get_type_id_by_item_name(pair[1], sde_named_type_ids)
                if not (__type_id0 is None) and not (__type_id1 is None):
                    __quantity = 1
                    if ("capacity" in __item0) and ("volume" in __item1):
                        __quantity = int(__item0["capacity"]/__item1["volume"])
                    __item_dicts = [  # флаг __is_blueprint_copy здесь не может быть выставлен
                        {"name": pair[0], "type_id": __type_id0, "quantity": 1, "details": __item0},
                        {"name": pair[1], "type_id": __type_id1, "quantity": __quantity, "details": __item1}
                    ]
        # в случае, если элемент не найден, то сохраняем об этом информацию в список проблем
        if __item_dicts is None:
            push_into_problems(__original_name, __quantity, __is_blueprint_copy, "obsolete")
        elif __ship_flag:
            # хул корабля всегда существует в одном экземпляре (не путать с тем, что валяется в карго)
            __converted["ship"] = __item_dicts[0]
        else:
            for __item_dict in __item_dicts:
                if not bool(__item_dict["details"]["published"]):
                    push_item_into_problems(__item_dict, "suppressed")
                    continue
                # Внимание! Хул корабля сохранён не в items, а в ship, т.о. если корабль перевозит
                # в карго такие-же хулы, то их там будет ровно столько, сколько и должно быть
                __exists = next((i for i in items if i["name"] == __item_dict["name"]), None)
                if __exists is None:
                    if "metaGroupID" in __item_dict["details"]:
                        __mg_num = __item_dict["details"]["metaGroupID"]
                        # если указано не включать модуль неподходящей мета-группы в
                        # список item-ов, то пропускаем его
                        if not (exclude_specified_meta_groups is None) and (__mg_num in exclude_specified_meta_groups):
                            continue
                        # если указано, что включать модули только указанной мета-группы в
                        # список item-ов, то добавляем только его
                        if not (include_only_meta_groups is None) and not (__mg_num is include_only_meta_groups):
                            continue
                    elif not (exclude_specified_meta_groups is None) or not (include_only_meta_groups is None):
                        push_item_into_problems(__item_dict, "unknown meta group")
                        continue
                    items.append(__item_dict)
                else:
                    __exists["quantity"] += int(__item_dict["quantity"])
    return __converted


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
    del icon_keys
    del icons


def __clean_positions(ws_dir, name):
    positions = read_converted(ws_dir, name)
    positions = [i for i in positions if (i["x"] != 0.0) and (i["y"] != 0.0) and (i["z"] != 0.0)]
    # json
    f_name_json = __get_converted_name(ws_dir, name)
    s = json.dumps(positions, indent=1, sort_keys=False)
    f = open(f_name_json, "wt+", encoding='utf8')
    f.write(s)
    del positions


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

    print("Rebuilding metaGroups.yaml file...")
    sys.stdout.flush()
    __rebuild(workspace_cache_files_dir, "fsd", "metaGroups", ["iconID", {"nameID": ["en"]}])

    print("Rebuilding typeIDs.yaml file...")
    sys.stdout.flush()
    __rebuild(workspace_cache_files_dir, "fsd", "typeIDs", ["basePrice", "capacity", "iconID", "marketGroupID", "metaGroupID", {"name": ["en"]}, "published", "volume"])

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
