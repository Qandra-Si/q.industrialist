import time
import tzlocal
import re

from datetime import datetime
from eve_sde_tools import get_yaml
from eve_sde_tools import get_item_name_by_type_id
from eve_sde_tools import get_basis_market_group_by_type_id
from eve_esi_tools import get_assets_location_name

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


def __dump_corp_assets_tree_nested(
        glf,
        parent_location_id,
        location_id,
        corp_assets_data,
        corp_assets_tree,
        corp_ass_names_data,
        foreign_structures_data,
        eve_market_prices_data,
        sde_type_ids,
        sde_inv_names,
        sde_inv_items,
        sde_market_groups):
    region_id, region_name, loc_name, foreign = get_assets_location_name(
        location_id,
        sde_inv_names,
        sde_inv_items,
        corp_ass_names_data,
        foreign_structures_data)
    itm_dict = None
    loc_dict = corp_assets_tree[str(location_id)]
    type_id = loc_dict["type_id"] if "type_id" in loc_dict else None
    group_id = get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, type_id)
    items = loc_dict["items"] if "items" in loc_dict else None
    nested_quantity = None
    items_quantity = None
    base_price = None
    volume = None
    if not (items is None):
        nested_quantity = len(items)
    if itm_dict is None:
        itm_dict = corp_assets_data[loc_dict["index"]] if "index" in loc_dict else None
    if not (itm_dict is None):
        items_quantity = itm_dict["quantity"]
        if str(type_id) in sde_type_ids:
            __type_dict = sde_type_ids[str(type_id)]
            if "basePrice" in __type_dict:
                base_price = __type_dict["basePrice"] * items_quantity
            if "volume" in __type_dict:
                volume = __type_dict["volume"] * items_quantity
    if type_id is None:
        __price_dict = None
    else:
        __price_dict = next((p for p in eve_market_prices_data if p['type_id'] == int(type_id)), None)
    glf.write(
        '<div class="media">\n'
        ' <div class="media-left media-top">{img}</div>\n'
        ' <div class="media-body">\n'
        '  <h4 class="media-heading" id="id{id}">{where}{what}{iq}{nq}</h4>\n'
        '  {parent_id}<span class="label label-info">{id}</span>{loc_flag}{foreign}\n'
        '  {grp}{base}{average}{adjusted}{volume}\n'.
        format(
            img='<img class="media-object icn32" src="{src}">'.format(src=__get_img_src(type_id, 32)) if not (type_id is None) else "",
            where='{} '.format(loc_name) if not (loc_name is None) else "",
            what='<small>{}</small> '.format(get_item_name_by_type_id(sde_type_ids, type_id)) if not (type_id is None) else "",
            parent_id='<a href="#id{id}"><span class="label label-primary">parent:{id}</span></a> '.format(id=parent_location_id) if not (parent_location_id is None) else "",
            id=location_id,
            nq=' <span class="badge">{}</span>'.format(items_quantity) if not (items_quantity is None) and (items_quantity > 1) else "",
            iq=' <span class="label label-info">{}</span>'.format(nested_quantity) if not (nested_quantity is None) and (nested_quantity > 1) else "",
            loc_flag=' <span class="label label-default">{}</span>'.format(itm_dict["location_flag"]) if not (itm_dict is None) else "",
            foreign='<br/><span class="label label-warning">foreign</span>' if foreign else "",
            grp='</br><span class="label label-success">{}</span>'.format(sde_market_groups[str(group_id)]["nameID"]["en"]) if not (group_id is None) else "",
            base='</br>base: {:,.1f} ISK'.format(base_price) if not (base_price is None) else "",
            average='</br>average: {:,.1f} ISK'.format(__price_dict["average_price"]*items_quantity) if not (items_quantity is None) and not (__price_dict is None) and ("average_price" in __price_dict) else "",
            adjusted='</br>adjusted: {:,.1f} ISK'.format(__price_dict["adjusted_price"]*items_quantity) if not (items_quantity is None) and not (__price_dict is None) and ("adjusted_price" in __price_dict) else "",
            volume='</br>{:,.1f} m&sup3'.format(volume) if not (volume is None) else ""
        )
    )
    if not (items is None):
        for itm in items:
            __dump_corp_assets_tree_nested(
                glf,
                location_id,
                itm,
                corp_assets_data,
                corp_assets_tree,
                corp_ass_names_data,
                foreign_structures_data,
                eve_market_prices_data,
                sde_type_ids,
                sde_inv_names,
                sde_inv_items,
                sde_market_groups)
    glf.write(
        ' </div>\n'
        '</div>\n'
    )


def __dump_corp_assets_tree(
        glf,
        corp_assets_data,
        corp_assets_tree,
        corp_ass_names_data,
        foreign_structures_data,
        eve_market_prices_data,
        sde_type_ids,
        sde_inv_names,
        sde_inv_items,
        sde_market_groups):
    glf.write("""
<!-- BEGIN: collapsable group (locations) -->
<div class="panel-group" id="accordion" role="tablist" aria-multiselectable="true">
  <ul class="media-list">
    <li class="media">""")

    if "roots" in corp_assets_tree:
        roots = corp_assets_tree["roots"]
        for loc_id in roots:
            __dump_corp_assets_tree_nested(
                glf,
                None,
                loc_id,
                corp_assets_data,
                corp_assets_tree,
                corp_ass_names_data,
                foreign_structures_data,
                eve_market_prices_data,
                sde_type_ids,
                sde_inv_names,
                sde_inv_items,
                sde_market_groups)

    glf.write("""    </li>
  </ul>
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


def dump_assets_tree_into_report(
        ws_dir,
        sde_type_ids,
        sde_inv_names,
        sde_inv_items,
        sde_market_groups,
        corp_assets_data,
        corp_ass_names_data,
        foreign_structures_data,
        eve_market_prices_data,
        corp_assets_tree):
    glf = open('{dir}/assets_tree.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        __dump_header(glf, "Corp Assets")

        #__dump_any_into_modal_header(glf, "Corp Assets")
        __dump_corp_assets_tree(glf, corp_assets_data, corp_assets_tree, corp_ass_names_data, foreign_structures_data, eve_market_prices_data, sde_type_ids, sde_inv_names, sde_inv_items, sde_market_groups)
        #__dump_any_into_modal_footer(glf)

        __dump_footer(glf)
    finally:
        glf.close()
