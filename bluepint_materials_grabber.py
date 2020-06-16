""" Q.Industrialist (desktop/mobile)

To build .html report about used blueprint's materials
run the following command from this directory as the root:

>>> python manipulate_yaml_and_json.py
>>> python bluepint_materials_grabber.py
"""
from manipulate_yaml_and_json import read_converted
from render_html import dump_materials_into_report


def main():
    materials = []
    blueprints = read_converted("blueprints")
    blueprints_wo_manufacturing = []
    blueprints_wo_materials = []
    for bp in blueprints:
        if "manufacturing" in blueprints[bp]["activities"]:
            if "materials" in blueprints[bp]["activities"]["manufacturing"]:
                for m in blueprints[bp]["activities"]["manufacturing"]["materials"]:
                    if "typeID" in m:
                        type_id = int(m["typeID"])
                        if 0 == materials.count(type_id):
                            materials.append(type_id)
            else:
                blueprints_wo_materials.append(bp)
        else:
            blueprints_wo_manufacturing.append(bp)
    dump_materials_into_report(materials, blueprints_wo_manufacturing, blueprints_wo_materials)


if __name__ == "__main__":
    main()
