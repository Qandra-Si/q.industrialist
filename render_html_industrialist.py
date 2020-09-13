import render_html
import eve_sde_tools


def __dump_wallet(glf, wallet_data):
    glf.write("{} ISK".format(wallet_data))


def __get_station_name(id):
    dict = eve_sde_tools.get_yaml(2, 'sde/bsd/invUniqueNames.yaml', "    itemID: {}".format(id))
    if "itemName" in dict:
        return dict["itemName"]
    return ""


def __build_hangar_tree(blueprint_data, assets_data, names_data):
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
                    loc1.update({"station_id": location_id2, "type_id": ass["type_id"], "level": 1})
                    found = False
                    for l3 in locations:
                        if l3["id"] == location_id2:
                            found = True
                            break
                    if not found:
                        loc2 = {"id": location_id2, "station_id": ass["location_id"], "level": 0}
                        name2 = __get_station_name(location_id2)
                        if name2:
                            loc2.update({"station_name": name2})
                        locations.append(loc2)
        if "station_id" in loc1:  # контейнер с известным id на станции
            station_name1 = __get_station_name(loc1["station_id"])
            if station_name1:
                loc1.update({"station_name": station_name1})
            name1 = None
            for nm in names_data:
                if nm["item_id"] == location_id1:
                    name1 = nm["name"]
            if not (name1 is None):
                loc1.update({"item_name": name1})
        if not ("station_id" in loc1):  # станция с известным id
            name1 = __get_station_name(location_id1)
            if name1:
                loc1.update({"station_name": name1})
                loc1.update({"station_id": location_id1})
                loc1.update({"level": 0})
        locations.append(loc1)
    return locations


def __dump_blueprints(glf, blueprint_data, assets_data, names_data, type_ids):
    glf.write("""
<!-- BEGIN: collapsable group (stations) -->
<div class="panel-group" id="accordion" role="tablist" aria-multiselectable="true">
""")

    locations = __build_hangar_tree(blueprint_data, assets_data, names_data)
    # debug: glf.write("<!-- {} -->\n".format(locations))
    for loc in locations:
        # level : loc["level"] : REQUIRED
        # type_id : loc["type_id"] : OPTIONAL
        # location_id : loc["id"] : REQUIRED
        location_id = int(loc["id"])
        glf.write(
            " <div class=\"panel panel-default\">\n"
            "  <div class=\"panel-heading\" role=\"tab\" id=\"heading{id}\">\n"
            "   <h4 class=\"panel-title\">\n".format(id=location_id)
        )
        if "item_name" in loc:
            location_name = loc["item_name"]
            if "station_name" in loc:
                location_name = "{} - {}".format(loc["station_name"], location_name)
        elif "station_name" in loc:
            location_name = loc["station_name"]
        elif "station_id" in loc:
            location_name = loc["station_id"]
        else:
            location_name = location_id
        glf.write("    <a role=\"button\" data-toggle=\"collapse\" data-parent=\"#accordion\" "
                  "href=\"#collapse{id}\" aria-expanded=\"true\" aria-controls=\"collapse{id}\""
                  ">{nm}</a>\n".format(id=location_id, nm=location_name))
        # if "type_id" in loc:  # у станции нет type_id, он есть только у item-ов (контейнеров)
        #     glf.write('<img src=\'./3/Types/{tp}_32.png\'/>'.format(tp=loc["type_id"]))
        glf.write(
            "   </h4>\n"
            "  </div>\n"
            "  <div id=\"collapse{id}\" class=\"panel-collapse collapse\" role=\"tabpanel\""
            "  aria-labelledby=\"heading{id}\">\n"
            "   <div class=\"panel-body\">\n".format(id=location_id)
        )
        # blueprints list
        for bp in blueprint_data:
            if bp["location_id"] != location_id:
                continue
            type_id = bp["type_id"]
            blueprint_name = eve_sde_tools.get_item_name_by_type_id(type_ids, type_id)
            glf.write('<p><img class="icn32" src="{src}"/>{nm}</p>\n'.format(
                nm=blueprint_name,
                src=render_html.__get_img_src(type_id, 32)
            ))
        glf.write(
            "   </div>\n"
            "  </div>\n"
            " </div>\n"
        )

    glf.write("""
</div>
<!-- END: collapsable group (stations) -->
""")


def __dump_corp_assets(glf, corp_ass_loc_data, corp_ass_names_data, type_ids):
    glf.write("""
<!-- BEGIN: collapsable group (locations) -->
<div class="panel-group" id="accordion" role="tablist" aria-multiselectable="true">
""")

    loc_flags = corp_ass_loc_data.keys()
    for loc_flag in loc_flags:
        __a1 = corp_ass_loc_data[loc_flag]
        loc_ids = __a1.keys()
        for loc in loc_ids:
            loc_id = int(loc)
            loc_name = next((n["name"] for n in corp_ass_names_data if n['item_id'] == loc_id), loc_id)
            __a2 = __a1[str(loc_id)]
            type_keys = __a2.keys()
            glf.write(
                ' <div class="panel panel-default">\n'
                '  <div class="panel-heading" role="tab" id="headingA{fl}{id}">\n'
                '   <h4 class="panel-title">\n'
                '    <a role="button" data-toggle="collapse" data-parent="#accordion" '
                'href="#collapseA{fl}{id}" aria-expanded="true" aria-controls="collapseA{fl}{id}"'
                '>{fl} - {nm}</a> <span class="badge">{q}</span>\n'
                '   </h4>\n'
                '  </div>\n'
                '  <div id="collapseA{fl}{id}" class="panel-collapse collapse" role="tabpanel" '
                'aria-labelledby="headingA{fl}{id}">\n'
                '   <div class="panel-body">\n'.format(
                    fl=loc_flag,
                    id=loc_id,
                    nm=loc_name,
                    q=len(type_keys)
                )
            )
            for type_id in type_keys:
                item_name = eve_sde_tools.get_item_name_by_type_id(type_ids, type_id)
                glf.write(
                    '<div class="media">\n'
                    ' <div class="media-left">\n'
                    '  <img class="media-object icn32" src="{src}" alt="{nm}">\n'
                    ' </div>\n'
                    ' <div class="media-body">\n'
                    '  <h4 class="media-heading">{nm} <span class="badge">{q}</span></h4>\n'
                    ' </div>\n'
                    '</div>\n'.format(
                        src=render_html.__get_img_src(type_id, 32),
                        nm=item_name,
                        q=__a2[type_id]
                    )
                )
            glf.write(
                "   </div>\n"
                "  </div>\n"
                " </div>\n"
            )

    glf.write("""
</div>
<!-- END: collapsable group (locations) -->
""")


def dump_industrialist_into_report(
        ws_dir,
        sde_type_ids,
        wallet_data,
        blueprint_data,
        assets_data,
        asset_names_data,
        corp_ass_names_data,
        corp_ass_loc_data):
    glf = open('{dir}/industrialist.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(glf, "Workflow")

        render_html.__dump_any_into_modal_header(glf, "Wallet")
        __dump_wallet(glf, wallet_data)
        render_html.__dump_any_into_modal_footer(glf)

        render_html.__dump_any_into_modal_header(glf, "Blueprints")
        __dump_blueprints(glf, blueprint_data, assets_data, asset_names_data, sde_type_ids)
        render_html.__dump_any_into_modal_footer(glf)

        render_html.__dump_any_into_modal_header(glf, "Corp Assets")
        __dump_corp_assets(glf, corp_ass_loc_data, corp_ass_names_data, sde_type_ids)
        render_html.__dump_any_into_modal_footer(glf)

        render_html.__dump_footer(glf)
    finally:
        glf.close()
