""" Q.Industrialist (desktop/mobile)

To build .html report about used blueprint's materials
run the following command from this directory as the root:

>>> python manipulate_yaml_and_json.py
>>> python bluepint_materials_grabber.py
"""
from manipulate_yaml_and_json import read_converted
from render_html import dump_materials_into_report


def main():
    sde_type_ids = read_converted("typeIDs")
    sde_blueprints = read_converted("blueprints")
    materials = []
    blueprints_wo_manufacturing = []
    blueprints_wo_materials = []
    for bp in sde_blueprints:
        if "manufacturing" in sde_blueprints[bp]["activities"]:
            if "materials" in sde_blueprints[bp]["activities"]["manufacturing"]:
                for m in sde_blueprints[bp]["activities"]["manufacturing"]["materials"]:
                    if "typeID" in m:
                        type_id = int(m["typeID"])
                        if 0 == materials.count(type_id):
                            materials.append(type_id)
            else:
                blueprints_wo_materials.append(bp)
        else:
            blueprints_wo_manufacturing.append(bp)
    dump_materials_into_report(sde_type_ids, materials, blueprints_wo_manufacturing, blueprints_wo_materials)


if __name__ == "__main__":
    main()
