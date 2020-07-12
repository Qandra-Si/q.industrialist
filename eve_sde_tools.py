""" Q.Industrialist (desktop/mobile)

run the following command from this directory as the root:

>>> python eve_sde_tools.py
"""
import yaml
import json
import sys

from yaml import SafeLoader

import q_industrialist_settings


# type=2 : unpacked SDE-yyyymmdd-TRANQUILITY.zip
def get_yaml(type, sub_url, item):
    f_name = '{tmp}/{type}/{url}'.format(type=type, tmp=q_industrialist_settings.g_tmp_directory, url=sub_url)
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
    return {}


def get_source_name(subname, name):
    return '{tmp}/{type}/{url}'.format(type=2, tmp=q_industrialist_settings.g_tmp_directory, url="sde/{}/{}.yaml".format(subname, name))


def get_converted_name(name):
    return '{dir}/.converted_{nm}.json'.format(dir=q_industrialist_settings.g_tmp_directory, nm=name)


def read_converted(name):
    f_name_json = get_converted_name(name)
    with open(f_name_json, 'r', encoding='utf8') as f:
        s = f.read()
        json_data = (json.loads(s))
        return json_data
    return None


def rebuild(subname, name, items_to_stay=None):
    keys_to_stay = []
    dicts_to_stay = []
    if not (items_to_stay is None):
        for i2s in items_to_stay:
            if isinstance(i2s, str):
                keys_to_stay.append(i2s)
            elif isinstance(i2s, dict):
                dicts_to_stay.append(i2s)
    f_name_yaml = get_source_name(subname, name)
    f_name_json = get_converted_name(name)
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
            f = open(f_name_json, "wt+")
            f.write(s)
        finally:
            f.close()


def rebuild_list2dict_by_key(name, key, val=None):
    # перечитываем построенный файл и преобразуем его из списка в справочник
    # при этом одно из значений элементов списка выбирается ключём в справочнике,
    # в том числ поддерживается возможность упростить
    #  [key1: {key1_2: val1_2}, key2: {key2_1: val2_2}]
    # до
    #  {"key1": val1_2, "key2": val2_2}
    # задав необязательный val-параметр
    lst = read_converted(name)
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
    f_name_json = get_converted_name(name)
    s = json.dumps(dct, indent=1, sort_keys=False)
    f = open(f_name_json, "wt+")
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


def get_materials_for_blueprints(sde_bp_materials):
    """
    Построение списка модулей и ресурсов, которые используются в производстве
    """
    materials_for_bps = []
    for bp in sde_bp_materials:
        if "manufacturing" in sde_bp_materials[bp]["activities"]:
            if "materials" in sde_bp_materials[bp]["activities"]["manufacturing"]:
                for m in sde_bp_materials[bp]["activities"]["manufacturing"]["materials"]:
                    if "typeID" in m:
                        type_id = int(m["typeID"])
                        if 0 == materials_for_bps.count(type_id):
                            materials_for_bps.append(type_id)
    return materials_for_bps


def main():  # rebuild .yaml files
    print("Rebuilding invNames.yaml file...")
    sys.stdout.flush()
    rebuild("bsd", "invNames", ["itemID", "itemName"])
    print("Reindexing .converted_invNames.json file...")
    sys.stdout.flush()
    rebuild_list2dict_by_key("invNames", "itemID", "itemName")

    print("Rebuilding invItems.yaml file...")
    sys.stdout.flush()
    rebuild("bsd", "invItems", ["itemID", "locationID", "typeID"])
    print("Reindexing .converted_invItems.json file...")
    sys.stdout.flush()
    rebuild_list2dict_by_key("invItems", "itemID")

    print("Rebuilding typeIDs.yaml file...")
    sys.stdout.flush()
    rebuild("fsd", "typeIDs", ["groupID", "iconID", "published", {"name": ["en"]}])

    print("Rebuilding blueprints.yaml file...")
    sys.stdout.flush()
    rebuild("fsd", "blueprints", ["activities"])


def test():
    data = get_yaml(2, 'sde/fsd/typeIDs.yaml', "32859:")
    # for d in data:
    #     print("{}".format(d))
    print("{}".format(data["name"]["en"]))  # Small Standard Container Blueprint

    data = get_yaml(2, 'sde/bsd/invUniqueNames.yaml', "    itemID: 60003760")
    # for d in data:
    #     print("{}".format(d))
    print("{}".format(data["itemName"]))  # Jita IV - Moon 4 - Caldari Navy Assembly Plant


if __name__ == "__main__":
    main()
    # test()
