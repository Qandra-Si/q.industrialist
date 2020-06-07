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


def dump_blueprints(glf, data):
    glf.write("<h3>Blueprints</h3>\n")

    locations = []
    for bp in data:
        location_id = int(bp["location_id"])
        if 0 == locations.count(location_id):
            locations.append(location_id)

    for location_id in locations:
        # location_id
        # References a station, a ship or an item_id if this blueprint is located within a container.
        # If the return value is an item_id, then the Character AssetList API must be queried to find
        # the container using the given item_id to determine the correct location of the Blueprint.
        location_dict = get_yaml(2, 'sde/bsd/invUniqueNames.yaml', "    itemID: {}".format(location_id))
        if "itemName" in location_dict:
            glf.write("<p>{}</p>\n".format(location_dict["itemName"]))
        else:
            glf.write("<p>{}</p>\n".format(location_id))
        # blueprints list
        for bp in data:
            if location_id != int(bp["location_id"]):
                continue
            type_id = bp["type_id"]
            type_dict = get_yaml(2, 'sde/fsd/typeIDs.yaml', "{}:".format(type_id))
            if ("name" in type_dict) and ("en" in type_dict["name"]):
                glf.write("<p>&nbsp;&nbsp;&nbsp;&nbsp;{}</p>\n".format(type_dict["name"]["en"]))
            else:
                glf.write("<p>&nbsp;&nbsp;&nbsp;&nbsp;{}</p>\n".format(type_id))


def main():
    data = (json.loads("""[
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
    glf = open('{tmp}/report.html'.format(tmp=q_industrialist_settings.g_tmp_directory), "wt+")
    try:
        dump_header(glf)
        dump_blueprints(glf, data)
        dump_footer(glf)
    finally:
       glf.close()


if __name__ == "__main__":
    main()
