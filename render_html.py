import time
import tzlocal
import re

from datetime import datetime
from eve_sde_tools import get_yaml
from eve_sde_tools import get_item_name_by_type_id

import q_industrialist_settings

__g_local_timezone = tzlocal.get_localzone()
__g_pattern_c2s1 = re.compile(r'(.)([A-Z][a-z]+)')
__g_pattern_c2s2 = re.compile(r'([a-z0-9])([A-Z])')


def __camel_to_snake(name):  # https://stackoverflow.com/a/1176023
  name = __g_pattern_c2s1.sub(r'\1_\2', name)
  return __g_pattern_c2s2.sub(r'\1_\2', name).lower()


def __get_img_src(tp, sz):
    if q_industrialist_settings.g_use_filesystem_resources:
        return './3/Types/{}_{}.png'.format(tp, sz)
    else:
        return 'http://imageserver.eveonline.com/Type/{}_{}.png'.format(tp, sz)


def __get_icon_src(icon_id, sde_icon_ids):
    """
    see: https://forums.eveonline.com/t/eve-online-icons/78457/3
    """
    if str(icon_id) in sde_icon_ids:
        nm = sde_icon_ids[str(icon_id)]["iconFile"]
        if q_industrialist_settings.g_use_filesystem_resources:
            return './3/{}'.format(nm)
        else:  # https://everef.net/img/Icons/items/9_64_5.png
            return 'https://everef.net/img/{}'.format(nm)
    else:
        return ""


def __dump_header(glf, header_name):
    glf.write("""
<!doctype html>
<html lang="ru">
 <head>
 <meta charset="utf-8">
 <meta http-equiv="X-UA-Compatible" content="IE=edge">
 <meta name="viewport" content="width=device-width, initial-scale=1">
<style type="text/css">
.icn16 { width:16px; height:16px; }
.icn24 { width:24px; height:24px; }
.icn32 { width:32px; height:32px; }
.icn64 { width:64px; height:64px; }
</style>
""")
    glf.write(
        ' <title>{nm} - Q.Industrialist</title>\n'
        ' <link rel="stylesheet" href="{bs_css}">\n'
        '</head>\n'
        '<body>\n'
        '<div class="page-header">\n'
        ' <h1>Q.Industrialist <small>{nm}</small></h1>\n'
        '</div>\n'
        '<script src="{jq_js}"></script>\n'
        '<script src="{bs_js}"></script>\n'.format(
            nm=header_name,
            bs_css='bootstrap/3.4.1/css/bootstrap.min.css' if q_industrialist_settings.g_use_filesystem_resources else 'https://stackpath.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css" integrity="sha384-HSMxcRTRxnN+Bdg0JdbxYKrThecOKuH5zCYotlSAcp1+c8xmyTe9GYg1l9a69psu" crossorigin="anonymous',
            jq_js='jquery/jquery-1.12.4.min.js' if q_industrialist_settings.g_use_filesystem_resources else 'https://code.jquery.com/jquery-1.12.4.min.js" integrity="sha384-nvAa0+6Qg9clwYCGGPpDQLVpLNn0fRaROjHqs13t4Ggj3Ez50XnGQqc/r8MhnRDZ" crossorigin="anonymous',
            bs_js='bootstrap/3.4.1/js/bootstrap.min.js' if q_industrialist_settings.g_use_filesystem_resources else 'https://stackpath.bootstrapcdn.com/bootstrap/3.4.1/js/bootstrap.min.js" integrity="sha384-aJ21OjlMXNL5UyIl/XNwTMqvzeRMZH2w8c5cRVpzpU8Y5bApTppSuUkhZXN0VxHd" crossorigin="anonymous'
        )
    )

def __dump_footer(glf):
    # Don't remove line below !
    glf.write('<p><small><small>Generated {dt}</small></br>\n'.format(
        dt=datetime.fromtimestamp(time.time(), __g_local_timezone).strftime('%a, %d %b %Y %H:%M:%S %z')))
    glf.write("""</br>
&copy; 2020 Qandra Si &middot; <a class="inert" href="https://github.com/Qandra-Si/q.industrialist">GitHub</a> &middot; Data provided by <a class="inert" href="https://esi.evetech.net/">ESI</a> and <a class="inert" href="https://zkillboard.com/">zKillboard</a> &middot; Tips go to <a class="inert" href="https://zkillboard.com/character/2116129465/">Qandra Si</a></br>
</br>
<small>EVE Online and the EVE logo are the registered trademarks of CCP hf. All rights are reserved worldwide. All other trademarks are the property of their respective owners. EVE Online, the EVE logo, EVE and all associated logos and designs are the intellectual property of CCP hf. All artwork, screenshots, characters, vehicles, storylines, world facts or other recognizable features of the intellectual property relating to these trademarks are likewise the intellectual property of CCP hf.</small>
</small></p>""")
    # Don't remove line above !
    glf.write("</body></html>")


def __dump_any_into_modal_header_wo_button(glf, name, unique_id=None, modal_size=None):
    name_merged = name.replace(' ', '') if unique_id is None else unique_id
    glf.write(
        '<!-- {nm} Modal -->\n'
        '<div class="modal fade" id="modal{nmm}" tabindex="-1" role="dialog" aria-labelledby="modal{nmm}Label">\n'
        ' <div class="modal-dialog{mdl_sz}" role="document">\n'
        '  <div class="modal-content">\n'
        '   <div class="modal-header">\n'
        '    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>\n'
        '    <h4 class="modal-title" id="modal{nmm}Label">{nm}</h4>\n'
        '   </div>\n'
        '   <div class="modal-body">\n'.
        format(nm=name, nmm=name_merged, mdl_sz='' if modal_size is None else ' {}'.format(modal_size)))


def __dump_any_into_modal_header(glf, name, unique_id=None, btn_size="btn-lg", btn_nm=None, modal_size=None):
    name_merged = name.replace(' ', '') if unique_id is None else unique_id
    glf.write(
        '<!-- Button trigger for {nm} Modal -->\n'
        '<button type="button" class="btn btn-primary {btn_sz}" data-toggle="modal" data-target="#modal{nmm}">{btn_nm}</button>\n'.
        format(nm=name,
               nmm=name_merged,
               btn_sz=btn_size,
               btn_nm='Show {nm}'.format(nm=name) if btn_nm is None else btn_nm))
    __dump_any_into_modal_header_wo_button(glf, name, unique_id, modal_size=modal_size)


def __dump_any_into_modal_footer(glf):
    glf.write("""
   </div>
   <div class="modal-footer">
    <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
    <!-- <button type="button" class="btn btn-primary">Choose</button> -->
   </div>
  </div>
 </div>
</div>
""")


def __dump_wallet(glf, wallet_data):
    glf.write("{} ISK".format(wallet_data))


def __get_station_name(id):
    dict = get_yaml(2, 'sde/bsd/invUniqueNames.yaml', "    itemID: {}".format(id))
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
            blueprint_name = get_item_name_by_type_id(type_ids, type_id)
            glf.write('<p><img class="icn32" src="{src}"/>{nm}</p>\n'.format(
                nm=blueprint_name,
                src=__get_img_src(type_id, 32)
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
                item_name = get_item_name_by_type_id(type_ids, type_id)
                glf.write(
                    '<div class="media">\n'
                    ' <div class="media-left">\n'
                    '  <img class="media-object icn32" src="{src}" alt="{nm}">\n'
                    ' </div>\n'
                    ' <div class="media-body">\n'
                    '  <h4 class="media-heading">{nm} <span class="badge">{q}</span></h4>\n'
                    ' </div>\n'
                    '</div>\n'.format(
                        src=__get_img_src(type_id, 32),
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
        sde_bp_materials,
        sde_market_groups,
        sde_icon_ids,
        wallet_data,
        blueprint_data,
        assets_data,
        asset_names_data,
        corp_assets_tree,
        corp_industry_jobs_data,
        corp_ass_names_data,
        corp_ass_loc_data,
        corp_bp_loc_data,
        stock_all_loc_ids,
        exclude_loc_ids,
        blueprint_loc_ids,
        blueprint_station_ids):
    glf = open('{dir}/report.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        __dump_header(glf, "Workflow")

        __dump_any_into_modal_header(glf, "Wallet")
        __dump_wallet(glf, wallet_data)
        __dump_any_into_modal_footer(glf)

        __dump_any_into_modal_header(glf, "Blueprints")
        __dump_blueprints(glf, blueprint_data, assets_data, asset_names_data, sde_type_ids)
        __dump_any_into_modal_footer(glf)

        __dump_any_into_modal_header(glf, "Corp Assets")
        __dump_corp_assets(glf, corp_ass_loc_data, corp_ass_names_data, sde_type_ids)
        __dump_any_into_modal_footer(glf)

        __dump_footer(glf)
    finally:
        glf.close()


def __dump_materials(glf, materials, type_ids):
    for type_id in materials:
        sid = str(type_id)
        if not (sid in type_ids):
            material_name = sid
        else:
            material_name = type_ids[sid]["name"]["en"]
        glf.write('<p><img src="{src}"/>{nm} ({tp})</p>\n'.format(src=__get_img_src(type_id, 32), nm=material_name, tp=type_id))


def __dump_bp_wo_manufacturing(glf, blueprints, type_ids):
    for type_id in blueprints:
        sid = str(type_id)
        if not (sid in type_ids):
            material_name = sid
        else:
            material_name = type_ids[sid]["name"]["en"]
        glf.write('<p><img src="{src}">{nm} ({tp})</p>\n'.format(src=__get_img_src(type_id, 32), nm=material_name, tp=type_id))


def __dump_bp_wo_materials(glf, blueprints, type_ids):
    for type_id in blueprints:
        sid = str(type_id)
        if not (sid in type_ids):
            material_name = sid
        else:
            material_name = type_ids[sid]["name"]["en"]
        glf.write('<p><img src="{src}"/>{nm} ({tp})</p>\n'.format(src=__get_img_src(type_id, 32), nm=material_name, tp=type_id))


def dump_materials_into_report(ws_dir, sde_type_ids, materials, wo_manufacturing, wo_materials):
    glf = open('{dir}/materials.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        __dump_header(glf, "Materials")

        __dump_any_into_modal_header(glf, "All Possible Materials")
        __dump_materials(glf, materials, sde_type_ids)
        __dump_any_into_modal_footer(glf)

        __dump_any_into_modal_header(glf, "Impossible to Produce Blueprints")
        __dump_bp_wo_manufacturing(glf, wo_manufacturing, sde_type_ids)
        __dump_any_into_modal_footer(glf)

        __dump_any_into_modal_header(glf, "Blueprints without Materials")
        __dump_bp_wo_materials(glf, wo_materials, sde_type_ids)
        __dump_any_into_modal_footer(glf)

        __dump_footer(glf)
    finally:
        glf.close()
