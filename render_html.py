import json
import time
import tzlocal

from datetime import date
from datetime import datetime
from parse_sde_yaml import get_yaml

import q_industrialist_settings


g_local_timezone = tzlocal.get_localzone()


def dump_header(glf):
    glf.write("""<html><head><style>
body { margin: 0; padding: 0; background-color: #101010; overflow-y: hidden; }
h2 { margin-bottom: 3px }
h3 { margin-bottom: 0px }
body, html { min-height: 100vh; overflow-x: hidden; box-sizing: border-box; line-height: 1.5; color: #fff; font-family: Shentox,Rogan,sans-serif; }
table { border-collapse: collapse; border: none; }
th,td { border: 1px solid gray; text-align: left; vertical-align: top; }
div p, .div p { margin:0px; color:#888; }
p a, .p a, h3 a, .h3 a { color: #2a9fd6; text-decoration: none; }
small { color:gray; }
a.inert { color:#999; }
</style></head><body>
""")
    glf.write("<h2>Q.Industrialist</h2>\n")


def dump_footer(glf):
    # Don't remove line below !
    glf.write('<p><small><small>Generated {dt}</small></br>\n'.format(
        dt=datetime.fromtimestamp(time.time(), g_local_timezone).strftime('%a, %d %b %Y %H:%M:%S %z')))
    glf.write("""</br>
&copy; 2020 Qandra Si &middot; <a class="inert" href="https://github.com/Qandra-Si/q.industrialist">GitHub</a> &middot; Data provided by <a class="inert" href="https://esi.evetech.net/">ESI</a> and <a class="inert" href="https://zkillboard.com/">zKillboard</a> &middot; Tips go to <a class="inert" href="https://zkillboard.com/character/2116129465/">Qandra Si</a></br>
</br>
<small>EVE Online and the EVE logo are the registered trademarks of CCP hf. All rights are reserved worldwide. All other trademarks are the property of their respective owners. EVE Online, the EVE logo, EVE and all associated logos and designs are the intellectual property of CCP hf. All artwork, screenshots, characters, vehicles, storylines, world facts or other recognizable features of the intellectual property relating to these trademarks are likewise the intellectual property of CCP hf.</small>
</small></p>""")
    # Don't remove line above !
    glf.write("""</body>
<script type="text/javascript">
//document.onkeydown = function(evt) {
//    evt = evt || window.event;
//    if (evt.keyCode == 27) showAll();
//};
</script></html>""")


def dump_wallet(glf, wallet_data):
    glf.write("<h3>Wallet</h3><p>{} ISK</p>\n".format(wallet_data))


def get_station_name(id):
    dict = get_yaml(2, 'sde/bsd/invUniqueNames.yaml', "    itemID: {}".format(id))
    if "itemName" in dict:
        return dict["itemName"]
    return ""


def build_hangar_tree(blueprint_data, assets_data):
    locations = []
    for bp in blueprint_data:
        # location_id
        # References a station, a ship or an item_id if this blueprint is located within a container.
        # If the return value is an item_id, then the Character AssetList API must be queried to find
        # the container using the given item_id to determine the correct location of the Blueprint.
        location_id1 = int(bp["location_id"])
        found = False
        for l1 in locations:
            if l1["id"] == location_id1:
                found = True
                break
        if found:
            continue
        loc1 = {"id": location_id1}  # id, station_id, station_name
        for ass in assets_data:
            if ass["item_id"] == location_id1:
                if ass["location_type"] == "station":
                    location_id2 = int(ass["location_id"])
                    loc1.update({"station_id": location_id2, "level": 1})
                    found = False
                    for l3 in locations:
                        if l3["id"] == location_id2:
                            found = True
                            break
                    if not found:
                        loc2 = {"id": location_id2, "station_id": ass["location_id"], "level": 0}
                        name2 = get_station_name(location_id2)
                        if name2:
                            loc2.update({"station_name": name2})
                        locations.append(loc2)
        if ("station_id" in loc1) and not ("station_name" in loc1):  # контейнер с известным id на станции
            name1 = get_station_name(loc1["station_id"])
            if name1:
                loc1.update({"station_name": name1})
        if not ("station_id" in loc1):  # станция с известным id
            name1 = get_station_name(location_id1)
            if name1:
                loc1.update({"station_name": name1})
                loc1.update({"station_id": location_id1})
                loc1.update({"level": 0})
        locations.append(loc1)
    return locations


def dump_blueprints(glf, blueprint_data, assets_data):
    glf.write("<h3>Blueprints</h3>\n")

    locations = build_hangar_tree(blueprint_data, assets_data)
    # debug:glf.write("<!-- {} -->\n".format(locations))
    for loc in locations:
        # level
        offset_str = ""
        offset_num = loc["level"]
        while offset_num:
            offset_str = offset_str + "&nbsp;&nbsp;&nbsp;&nbsp;"
            offset_num = offset_num - 1
        # location_id
        location_id = int(loc["id"])
        if "station_name" in loc:
            glf.write("<p id='{id}'>{off}{nm}</p>\n".format(off=offset_str, id=location_id, nm=loc["station_name"]))
        elif "station_id" in loc:
            glf.write("<p id='{id}'>{off}{nm}</p>\n".format(off=offset_str, id=location_id, nm=loc["station_id"]))
        else:
            glf.write("<p id='{id}'>{off}{id}</p>\n".format(off=offset_str, id=location_id))
        # blueprints list
        for bp in blueprint_data:
            if loc["id"] != location_id:
                continue
            type_id = bp["type_id"]
            type_dict = get_yaml(2, 'sde/fsd/typeIDs.yaml', "{}:".format(type_id))
            if ("name" in type_dict) and ("en" in type_dict["name"]):
                glf.write("<p>{off}&nbsp;&nbsp;&nbsp;&nbsp;{nm}</p>\n".format(off=offset_str, nm=type_dict["name"]["en"]))
            else:
                glf.write("<p>{off}&nbsp;&nbsp;&nbsp;&nbsp;{id}</p>\n".format(off=offset_str, id=type_id))


def dump_into_report(wallet_data, blueprint_data, assets_data):
    glf = open('{tmp}/report.html'.format(tmp=q_industrialist_settings.g_tmp_directory), "wt+")
    try:
        dump_header(glf)
        dump_wallet(glf, wallet_data)
        dump_blueprints(glf, blueprint_data, assets_data)
        dump_footer(glf)
    finally:
        glf.close()


def main():
    blueprints_data = (json.loads("""[
 {
  "item_id": 1032415077622,
  "location_flag": "Hangar",
  "location_id": 1033013802131,
  "material_efficiency": 5,
  "quantity": -2,
  "runs": 188,
  "time_efficiency": 2,
  "type_id": 1220
 },
 {
  "item_id": 1033373083634,
  "location_flag": "Hangar",
  "location_id": 60003760,
  "material_efficiency": 0,
  "quantity": 1,
  "runs": -1,
  "time_efficiency": 0,
  "type_id": 32859
 },
 {
  "item_id": 1033373084812,
  "location_flag": "Hangar",
  "location_id": 60003760,
  "material_efficiency": 0,
  "quantity": 1,
  "runs": -1,
  "time_efficiency": 0,
  "type_id": 32860
 },
  {
  "item_id": 1033506273254,
  "location_flag": "Hangar",
  "location_id": 60003760,
  "material_efficiency": 0,
  "quantity": -2,
  "runs": 2,
  "time_efficiency": 0,
  "type_id": 836
 }
]"""))
    assets_data = (json.loads("""[
{
  "is_singleton": true,
  "item_id": 1033013802131,
  "location_flag": "Hangar",
  "location_id": 60003760,
  "location_type": "station",
  "quantity": 1,
  "type_id": 17366
 }
]"""))
    dump_into_report(14966087542.58, blueprints_data, assets_data)


if __name__ == "__main__":
    main()
