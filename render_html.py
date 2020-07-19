import time
import tzlocal

from datetime import datetime
from eve_sde_tools import get_yaml
from eve_sde_tools import get_item_name_by_type_id
from eve_sde_tools import get_blueprint_manufacturing_materials

import q_industrialist_settings

g_local_timezone = tzlocal.get_localzone()


def get_img_src(tp, sz):
    if q_industrialist_settings.g_use_filesystem_resources:
        return './3/Types/{}_{}.png'.format(tp, sz)
    else:
        return 'http://imageserver.eveonline.com/Type/{}_{}.png'.format(tp, sz)


def get_icon_src(icon_id, sde_icon_ids):
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


def dump_header(glf, header_name):
    glf.write(
        '<!doctype html>\n'
        '<html lang="ru">\n'
        ' <head>\n'
        ' <!-- <meta charset="utf-8"> -->\n'
        ' <meta http-equiv="X-UA-Compatible" content="IE=edge">\n'
        ' <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        ' <title>Q.Industrialist - {nm}</title>\n'
        ' <link rel="stylesheet" href="{bs_css}">\n'
        '<style type="text/css">\n'
        '.icn24 {{ width:24px; height:24px; }}\n'
        '.icn32 {{ width:32px; height:32px; }}\n'
        '.icn64 {{ width:64px; height:64px; }}\n'
        '</style>\n'
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
    glf.write("</body></html>")


def dump_wallet(glf, wallet_data):
    glf.write("""<!-- Button trigger for Wallet Modal -->
<button type="button" class="btn btn-primary btn-lg" data-toggle="modal" data-target="#modalWallet">Show Wallet</button>
<!-- Wallet Modal -->
<div class="modal fade" id="modalWallet" tabindex="-1" role="dialog" aria-labelledby="modalWalletLabel">
  <div class="modal-dialog" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        <h4 class="modal-title" id="modalWalletLabel">Wallet</h4>
      </div>
      <div class="modal-body">""")
    glf.write("{} ISK".format(wallet_data))
    glf.write("""</div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
      </div>
    </div>
  </div>
</div>""")


def get_station_name(id):
    dict = get_yaml(2, 'sde/bsd/invUniqueNames.yaml', "    itemID: {}".format(id))
    if "itemName" in dict:
        return dict["itemName"]
    return ""


def build_hangar_tree(blueprint_data, assets_data, names_data):
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
                        name2 = get_station_name(location_id2)
                        if name2:
                            loc2.update({"station_name": name2})
                        locations.append(loc2)
        if "station_id" in loc1:  # контейнер с известным id на станции
            station_name1 = get_station_name(loc1["station_id"])
            if station_name1:
                loc1.update({"station_name": station_name1})
            name1 = None
            for nm in names_data:
                if nm["item_id"] == location_id1:
                    name1 = nm["name"]
            if not (name1 is None):
                loc1.update({"item_name": name1})
        if not ("station_id" in loc1):  # станция с известным id
            name1 = get_station_name(location_id1)
            if name1:
                loc1.update({"station_name": name1})
                loc1.update({"station_id": location_id1})
                loc1.update({"level": 0})
        locations.append(loc1)
    return locations


def dump_blueprints(glf, blueprint_data, assets_data, names_data, type_ids):
    glf.write("""<!-- Button trigger for Blueprints Modal -->
<button type="button" class="btn btn-primary btn-lg" data-toggle="modal" data-target="#modalBlueprints">Show Blueprints</button>
<!-- Blueprints Modal -->
<div class="modal fade" id="modalBlueprints" tabindex="-1" role="dialog" aria-labelledby="modalBlueprintsLabel">
  <div class="modal-dialog" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        <h4 class="modal-title" id="modalBlueprintsLabel">Blueprints</h4>
      </div>
      <div class="modal-body">
<!-- BEGIN: collapsable group (stations) -->
<div class="panel-group" id="accordion" role="tablist" aria-multiselectable="true">""")

    locations = build_hangar_tree(blueprint_data, assets_data, names_data)
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
                src=get_img_src(type_id, 32)
            ))
        glf.write(
            "   </div>\n"
            "  </div>\n"
            " </div>\n"
        )

    glf.write("""</div>
<!-- END: collapsable group (stations) -->
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
        <button type="button" class="btn btn-primary">Choose</button>
      </div>
    </div>
  </div>
</div>""")


def dump_corp_blueprints(glf, corp_bp_loc_data, corp_ass_loc_data, type_ids, bp_materials):
    # временная мера: хардкодим тут код '.res ALL' контейнера
    tmp_res_src = corp_ass_loc_data["Unlocked"][1032950982419]

    glf.write("""<!-- Button trigger for Corp Blueprints Modal -->
    <button type="button" class="btn btn-primary btn-lg" data-toggle="modal" data-target="#modalCorpBlueprints">Show Corp Blueprints</button>
    <!-- Corp Blueprints Modal -->
    <div class="modal fade" id="modalCorpBlueprints" tabindex="-1" role="dialog" aria-labelledby="modalCorpBlueprintsLabel">
      <div class="modal-dialog" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
            <h4 class="modal-title" id="modalCorpBlueprintsLabel">Corp Blueprints</h4>
          </div>
          <div class="modal-body">
    <!-- BEGIN: collapsable group (locations) -->
    <div class="panel-group" id="accordion" role="tablist" aria-multiselectable="true">""")

    loc_flags = corp_bp_loc_data.keys()
    for loc_flag in loc_flags:
        loc_ids = corp_bp_loc_data[loc_flag].keys()
        for loc in loc_ids:
            loc_id = int(loc)
            # пока нет возможности считать названия контейнеров, - хардкодим тут
            loc_name = loc_id
            if q_industrialist_settings.g_adopt_for_ri4:
                if loc_id == 1033012626278:
                    loc_name = "Sideproject"
                elif loc_id == 1032890037923:
                    loc_name = "Alexa O'Connor pet project"
                elif loc_id == 1033063942756:
                    loc_name = "Alexa O'Connor - Остатки"
                elif loc_id == 1033675076928:
                    loc_name = "[prod] conveyor 2"
                elif loc_id == 1032846295901:
                    loc_name = "[prod] conveyor 1"
            glf.write(
                ' <div class="panel panel-default">\n'
                '  <div class="panel-heading" role="tab" id="headingB{fl}{id}">\n'
                '   <h4 class="panel-title">\n'
                '    <a role="button" data-toggle="collapse" data-parent="#accordion" '
                'href="#collapseB{fl}{id}" aria-expanded="true" aria-controls="collapseB{fl}{id}"'
                '>{fl} - {nm}</a>\n'
                '   </h4>\n'
                '  </div>\n'
                '  <div id="collapseB{fl}{id}" class="panel-collapse collapse" role="tabpanel" '
                'aria-labelledby="headingB{fl}{id}">\n'
                '   <div class="panel-body">\n'.format(
                    fl=loc_flag,
                    id=loc_id,
                    nm=loc_name
                )
            )
            type_keys = corp_bp_loc_data[loc_flag][loc_id].keys()
            materials_summary = {}
            for type_id in type_keys:
                blueprint_name = get_item_name_by_type_id(type_ids, type_id)
                glf.write(
                    '<div class="media">\n'
                    ' <div class="media-left">\n'
                    '  <img class="media-object icn64" src="{src}" alt="{nm}">\n'
                    ' </div>\n'
                    ' <div class="media-body">\n'
                    '  <h4 class="media-heading">{nm}</h4>\n'.format(
                        src=get_img_src(type_id, 64),
                        nm=blueprint_name
                    )
                )
                bp_manuf_mats = get_blueprint_manufacturing_materials(bp_materials, type_id)
                bp_keys = corp_bp_loc_data[loc_flag][loc_id][type_id].keys()
                for bpk in bp_keys:
                    bp = corp_bp_loc_data[loc_flag][loc_id][type_id][bpk]
                    is_blueprint_copy = bp["cp"]
                    quantity_or_runs = bp["qr"]
                    material_efficiency = bp["me"]
                    time_efficiency = bp["te"]
                    blueprint_status = bp["st"]
                    glf.write(
                        '<span class="label label-{cpc}">{cpn}</span>'
                        '&nbsp;<span class="label label-success">{me} {te}</span>'
                        '&nbsp;<span class="badge">{qr}</span>\n'.format(
                            qr=quantity_or_runs,
                            cpc='default' if is_blueprint_copy else 'info',
                            cpn='copy' if is_blueprint_copy else 'original',
                            me=material_efficiency,
                            te=time_efficiency
                        )
                    )
                    if not (blueprint_status is None):  # [ active, cancelled, delivered, paused, ready, reverted ]
                        if (blueprint_status == "active") or (blueprint_status == "delivered") or (blueprint_status == "ready"):
                            glf.write('&nbsp;<span class="label label-info">{}</span></br>\n'.format(blueprint_status))
                        elif (blueprint_status == "cancelled") or (blueprint_status == "paused") or (blueprint_status == "reverted"):
                            glf.write('&nbsp;<span class="label label-warning">{}</span></br>\n'.format(blueprint_status))
                        else:
                            glf.write('&nbsp;<span class="label label-danger">{}</span></br>\n'.format(blueprint_status))
                    elif bp_manuf_mats is None:
                        glf.write('&nbsp;<span class="label label-warning">manufacturing impossible</span></br>\n')
                    else:
                        glf.write('</br><div>\n')  # div(materials)
                        not_enough_materials = []
                        for m in bp_manuf_mats:
                            bpmmq = int(m["quantity"]) * quantity_or_runs
                            bpmmq_me = bpmmq
                            if material_efficiency > 0:
                                _me = int(100 - material_efficiency)
                                bpmmq_me = int((bpmmq * _me) / 100)
                                if 0 != ((bpmmq * _me) % 100):
                                    bpmmq_me = bpmmq_me + 1
                            bpmm_tid = int(m["typeID"])
                            bpmm_tnm = get_item_name_by_type_id(type_ids, bpmm_tid)
                            # проверка наличия имеющихся ресурсов для постройки по этому БП
                            not_available = bpmmq_me
                            if m["typeID"] in tmp_res_src:
                                not_available = 0 if tmp_res_src[m["typeID"]] >= not_available else not_available - tmp_res_src[m["typeID"]]
                            # вывод наименования ресурса
                            glf.write(
                                '<span style="white-space:nowrap">'
                                '<img class="icn24" src="{src}"> {q} x {nm} '
                                '</span>\n'.format(
                                    src=get_img_src(bpmm_tid, 32),
                                    q=bpmmq_me,
                                    nm=bpmm_tnm
                                )
                            )
                            # сохраняем недостающее кол-во материалов для производства по этому чертежу
                            if not_available > 0:
                                not_enough_materials.append({"id": bpmm_tid, "q": not_available, "nm": bpmm_tnm})
                            # сохраняем материалы для производства в список их суммарного кол-ва
                            if m["typeID"] in materials_summary:
                                materials_summary[m["typeID"]] = materials_summary[m["typeID"]] + bpmmq_me
                            else:
                                materials_summary.update({m["typeID"]: bpmmq_me})
                        glf.write('</div>\n')  # div(materials)
                        if len(not_enough_materials) > 0:
                            glf.write('<div>\n')  # div(not_enough_materials)
                            for m in not_enough_materials:
                                glf.write(
                                    '&nbsp;<span class="label label-warning">'
                                    '<img class="icn24" src="{src}"> {q} x {nm} '
                                    '</span>\n'.format(
                                        src=get_img_src(m["id"], 32),
                                        q=m["q"],
                                        nm=m["nm"]
                                    )
                                )
                            glf.write('</div>\n')  # div(not_enough_materials)
                glf.write(
                    ' </div>\n'  # media-body
                    '</div>\n'  # media
                )
            if len(materials_summary) > 0:
                ms_keys = materials_summary.keys()
                glf.write(
                    '<hr><div class="media">\n'
                    ' <div class="media-left">\n'
                    '  <span class="glyphicon glyphicon-alert" aria-hidden="true" style="font-size: 64px;"></span>\n'
                    ' </div>\n'
                    ' <div class="media-body">\n'
                )
                for ms_type_id in ms_keys:
                    glf.write(
                        '<span style="white-space:nowrap">'
                        '<img class="icn24" src="{src}"> {q} x {nm} '
                        '</span>\n'.format(
                            src=get_img_src(ms_type_id, 32),
                            q=materials_summary[ms_type_id],
                            nm=get_item_name_by_type_id(type_ids, ms_type_id)
                        )
                    )
                for ms_type_id in ms_keys:
                    not_available = materials_summary[ms_type_id]
                    if ms_type_id in tmp_res_src:
                        not_available = 0 if tmp_res_src[ms_type_id] >= not_available else not_available - tmp_res_src[ms_type_id]
                    if not_available > 0:
                        glf.write(
                            '&nbsp;<span class="label label-warning">'
                            '<img class="icn24" src="{src}"> {q} x {nm} '
                            '</span>\n'.format(
                                src=get_img_src(ms_type_id, 32),
                                q=not_available,
                                nm=get_item_name_by_type_id(type_ids, ms_type_id)
                            )
                        )
                glf.write(
                    ' </div>\n'
                    '</div>\n'
                )
            glf.write(
                "   </div>\n"
                "  </div>\n"
                " </div>\n"
            )

    glf.write("""</div>
<!-- END: collapsable group (locations) -->
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
        <button type="button" class="btn btn-primary">Choose</button>
      </div>
    </div>
  </div>
</div>""")


def dump_corp_assets(glf, corp_ass_loc_data, corp_ass_names_data, type_ids):
    glf.write("""<!-- Button trigger for Corp Assets Modal -->
<button type="button" class="btn btn-primary btn-lg" data-toggle="modal" data-target="#modalCorpAssets">Show Corp Assets</button>
<!-- Corp Assets Modal -->
<div class="modal fade" id="modalCorpAssets" tabindex="-1" role="dialog" aria-labelledby="modalCorpAssetsLabel">
  <div class="modal-dialog" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        <h4 class="modal-title" id="modalCorpAssetsLabel">Corp Assets</h4>
      </div>
      <div class="modal-body">
<!-- BEGIN: collapsable group (locations) -->
<div class="panel-group" id="accordion" role="tablist" aria-multiselectable="true">""")

    loc_flags = corp_ass_loc_data.keys()
    for loc_flag in loc_flags:
        loc_ids = corp_ass_loc_data[loc_flag].keys()
        for loc in loc_ids:
            loc_id = int(loc)
            loc_name = next((n["name"] for n in corp_ass_names_data if n['item_id'] == loc_id), loc_id)
            type_keys = corp_ass_loc_data[loc_flag][loc_id].keys()
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
                        src=get_img_src(type_id, 32),
                        nm=item_name,
                        q=corp_ass_loc_data[loc_flag][loc_id][type_id]
                    )
                )
            glf.write(
                "   </div>\n"
                "  </div>\n"
                " </div>\n"
            )

    glf.write("""</div>
<!-- END: collapsable group (locations) -->
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
        <button type="button" class="btn btn-primary">Choose</button>
      </div>
    </div>
  </div>
</div>""")


def dump_corp_assets_tree_nested(
        glf,
        location_id,
        corp_assets_data,
        corp_assets_tree,
        corp_ass_names_data,
        foreign_structures_data,
        sde_type_ids,
        sde_inv_names,
        sde_inv_items):
    # constellation_name = None
    loc_name = None
    itm_dict = None
    foreign = False
    if int(location_id) < 1000000000000:
        if str(location_id) in sde_inv_names:
            loc_name = sde_inv_names[str(location_id)]
            if str(location_id) in sde_inv_items:
                root_item = sde_inv_items[str(location_id)]
                if root_item["typeID"] == 5:  # Solar System
                    # constellation_name = sde_inv_names[str(root_item["locationID"])]
                    constellation_item = sde_inv_items[str(root_item["locationID"])]  # Constellation
                    region_name = sde_inv_names[str(constellation_item["locationID"])]
                    loc_name = '{} {}'.format(region_name, loc_name)
    else:
        loc_name = next((n["name"] for n in corp_ass_names_data if n['item_id'] == location_id), None)
        if loc_name is None:
            loc_name = next((foreign_structures_data[fs]["name"] for fs in foreign_structures_data if int(fs) == location_id), None)
            foreign = False if loc_name is None else True
        # if itm_dict is None:
        #     itm_dict = next((a for a in corp_assets_data if a['item_id'] == location_id), None)
        # if not (itm_dict is None):
        #     loc_name = itm_dict["location_flag"]
    loc_dict = corp_assets_tree[str(location_id)]
    type_id = loc_dict["type_id"] if "type_id" in loc_dict else None
    items = loc_dict["items"] if "items" in loc_dict else None
    quantity = None
    if not (items is None):
        quantity = len(items)
    else:
        if itm_dict is None:
            itm_dict = next((a for a in corp_assets_data if a['item_id'] == location_id), None)
        if not (itm_dict is None):
            quantity = itm_dict["quantity"]
    if itm_dict is None:
        itm_dict = next((a for a in corp_assets_data if a['item_id'] == location_id), None)
    glf.write(
        '<div class="media">\n'
        ' <div class="media-left media-top">{img}</div>\n'
        ' <div class="media-body">\n'
        '  <h4 class="media-heading">{where}{what}{q}</h4>\n'
        '  <span class="label label-info">{id}</span>{loc_flag}{foreign}\n'.
        format(
            img='<img class="media-object icn32" src="{src}">'.format(src=get_img_src(type_id, 32)) if not (type_id is None) else "",
            where='{} '.format(loc_name) if not (loc_name is None) else "",
            what='<small>{}</small> '.format(get_item_name_by_type_id(sde_type_ids, type_id)) if not (type_id is None) else "",
            id=location_id,
            q=' <span class="badge">{}</span>'.format(quantity) if not (quantity is None) else "",
            loc_flag=' <span class="label label-default">{}</span>'.format(itm_dict["location_flag"]) if not (itm_dict is None) else "",
            foreign='<br/><span class="label label-warning">foreign</span>' if foreign else ""
        )
    )
    if not (items is None):
        for itm in items:
            dump_corp_assets_tree_nested(
                glf,
                itm,
                corp_assets_data,
                corp_assets_tree,
                corp_ass_names_data,
                foreign_structures_data,
                sde_type_ids,
                sde_inv_names,
                sde_inv_items)
    glf.write(
        ' </div>\n'
        '</div>\n'
    )


def dump_corp_assets_tree(
        glf,
        corp_assets_data,
        corp_assets_tree,
        corp_ass_names_data,
        foreign_structures_data,
        sde_type_ids,
        sde_inv_names,
        sde_inv_items):
    glf.write("""<!-- Button trigger for Corp Assets Tree Modal -->
<button type="button" class="btn btn-primary btn-lg" data-toggle="modal" data-target="#modalCorpAssetsTree">Show Corp Assets Tree</button>
<!-- Corp Assets Tree Modal -->
<div class="modal fade" id="modalCorpAssetsTree" tabindex="-1" role="dialog" aria-labelledby="modalCorpAssetsTreeLabel">
  <div class="modal-dialog" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        <h4 class="modal-title" id="modalCorpAssetsTreeLabel">Corp Assets Tree</h4>
      </div>
      <div class="modal-body">
<!-- BEGIN: collapsable group (locations) -->
<div class="panel-group" id="accordion" role="tablist" aria-multiselectable="true">
  <ul class="media-list">
    <li class="media">""")

    if "roots" in corp_assets_tree:
        roots = corp_assets_tree["roots"]
        for loc_id in roots:
            dump_corp_assets_tree_nested(
                glf,
                loc_id,
                corp_assets_data,
                corp_assets_tree,
                corp_ass_names_data,
                foreign_structures_data,
                sde_type_ids,
                sde_inv_names,
                sde_inv_items)

    glf.write("""    </li>
  </ul>
</div>
<!-- END: collapsable group (locations) -->
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
        <button type="button" class="btn btn-primary">Choose</button>
      </div>
    </div>
  </div>
</div>""")


def dump_into_report(
        sde_type_ids,
        sde_bp_materials,
        wallet_data,
        blueprint_data,
        assets_data,
        asset_names_data,
        corp_ass_names_data,
        corp_ass_loc_data,
        corp_bp_loc_data):
    glf = open('{tmp}/report.html'.format(tmp=q_industrialist_settings.g_tmp_directory), "wt+", encoding='utf8')
    try:
        dump_header(glf, "Workflow")
        dump_wallet(glf, wallet_data)
        dump_blueprints(glf, blueprint_data, assets_data, asset_names_data, sde_type_ids)
        dump_corp_blueprints(glf, corp_bp_loc_data, corp_ass_loc_data, sde_type_ids, sde_bp_materials)
        dump_corp_assets(glf, corp_ass_loc_data, corp_ass_names_data, sde_type_ids)
        dump_footer(glf)
    finally:
        glf.close()


def dump_materials(glf, materials, type_ids):
    glf.write("""<!-- Button trigger for all Possible Materials Modal -->
<button type="button" class="btn btn-primary btn-lg" data-toggle="modal" data-target="#modalAllPossibleMaterials">Show all Possible Materials</button>
<!-- All Possible Modal -->
<div class="modal fade" id="modalAllPossibleMaterials" tabindex="-1" role="dialog" aria-labelledby="modalAllPossibleMaterialsLabel">
  <div class="modal-dialog" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        <h4 class="modal-title" id="modalAllPossibleMaterialsLabel">All Possible Materials</h4>
      </div>
      <div class="modal-body">""")
    for type_id in materials:
        sid = str(type_id)
        if not (sid in type_ids):
            material_name = sid
        else:
            material_name = type_ids[sid]["name"]["en"]
        glf.write('<p><img src="{src}"/>{nm} ({tp})</p>\n'.format(src=get_img_src(type_id, 32), nm=material_name, tp=type_id))
    glf.write("""</div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
      </div>
    </div>
  </div>
</div>""")


def dump_bp_wo_manufacturing(glf, blueprints, type_ids):
    glf.write("""<!-- Button trigger for Impossible to Produce Blueprints Modal -->
<button type="button" class="btn btn-primary btn-lg" data-toggle="modal" data-target="#modalImpossible2ProduceBlueprints">Show Impossible to Produce Blueprints</button>
<!-- Impossible to Produce Blueprints Modal -->
<div class="modal fade" id="modalImpossible2ProduceBlueprints" tabindex="-1" role="dialog" aria-labelledby="modalImpossible2ProduceBlueprintsLabel">
  <div class="modal-dialog" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        <h4 class="modal-title" id="modalImpossible2ProduceBlueprintsLabel">Impossible to Produce Blueprints</h4>
      </div>
      <div class="modal-body">""")
    for type_id in blueprints:
        sid = str(type_id)
        if not (sid in type_ids):
            material_name = sid
        else:
            material_name = type_ids[sid]["name"]["en"]
        glf.write('<p><img src="{src}">{nm} ({tp})</p>\n'.format(src=get_img_src(type_id, 32), nm=material_name, tp=type_id))
    glf.write("""</div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
      </div>
    </div>
  </div>
</div>""")


def dump_bp_wo_materials(glf, blueprints, type_ids):
    glf.write("""<!-- Button trigger for Blueprints without Materials Modal -->
<button type="button" class="btn btn-primary btn-lg" data-toggle="modal" data-target="#modalBlueprintsWithoutMaterials">Show Blueprints without Materials</button>
<!-- Blueprints without Materials Modal -->
<div class="modal fade" id="modalBlueprintsWithoutMaterials" tabindex="-1" role="dialog" aria-labelledby="modalBlueprintsWithoutMaterialsLabel">
  <div class="modal-dialog" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        <h4 class="modal-title" id="modalBlueprintsWithoutMaterialsLabel">Blueprints without Materials</h4>
      </div>
      <div class="modal-body">""")
    for type_id in blueprints:
        sid = str(type_id)
        if not (sid in type_ids):
            material_name = sid
        else:
            material_name = type_ids[sid]["name"]["en"]
        glf.write('<p><img src="{src}"/>{nm} ({tp})</p>\n'.format(src=get_img_src(type_id, 32), nm=material_name, tp=type_id))
    glf.write("""</div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
      </div>
    </div>
  </div>
</div>""")


def dump_materials_into_report(sde_type_ids, materials, wo_manufacturing, wo_materials):
    glf = open('{tmp}/materials.html'.format(tmp=q_industrialist_settings.g_tmp_directory), "wt+", encoding='utf8')
    try:
        dump_header(glf, "Materials")
        dump_materials(glf, materials, sde_type_ids)
        dump_bp_wo_manufacturing(glf, wo_manufacturing, sde_type_ids)
        dump_bp_wo_materials(glf, wo_materials, sde_type_ids)
        dump_footer(glf)
    finally:
        glf.close()


def dump_assets_tree_into_report(
        sde_type_ids,
        sde_inv_names,
        sde_inv_items,
        corp_assets_data,
        corp_ass_names_data,
        foreign_structures_data,
        corp_ass_loc_data,
        corp_assets_tree):
    glf = open('{tmp}/assets_tree.html'.format(tmp=q_industrialist_settings.g_tmp_directory), "wt+", encoding='utf8')
    try:
        dump_header(glf, "Corp Assets")
        # dump_corp_assets(glf, corp_ass_loc_data, corp_ass_names_data, sde_type_ids)
        dump_corp_assets_tree(glf, corp_assets_data, corp_assets_tree, corp_ass_names_data, foreign_structures_data, sde_type_ids, sde_inv_names, sde_inv_items)
        dump_footer(glf)
    finally:
        glf.close()


def dump_cynonetwork_into_report():
    glf = open('{tmp}/cynonetwork.html'.format(tmp=q_industrialist_settings.g_tmp_directory), "wt+", encoding='utf8')
    try:
        dump_header(glf, "Cyno Network")
        dump_footer(glf)
    finally:
        glf.close()


def dump_market_groups_tree_nested(
        group_id,
        sde_market_groups,
        sde_icon_ids,
        market_groups_tree,
        market_data,
        market_data_printer):
    if not (str(group_id) in market_data) and not ("items" in market_groups_tree[str(group_id)]):
        return ""
    sde_group = sde_market_groups[str(group_id)]
    icon_id = sde_group["iconID"] if "iconID" in sde_group else 0
    tbl_glf = market_data_printer(group_id, market_data)
    sub_glf = ''
    if "items" in market_groups_tree[str(group_id)]:
        for group_id in market_groups_tree[str(group_id)]["items"]:
            sub_glf = sub_glf + dump_market_groups_tree_nested(
                group_id,
                sde_market_groups,
                sde_icon_ids,
                market_groups_tree,
                market_data,
                market_data_printer
            )
    if not tbl_glf and not sub_glf:
        return ""
    glf = '' \
          '<div class="media">\n' \
          ' <div class="media-left media-top">{img}</div>\n' \
          ' <div class="media-body">\n' \
          '  <h4 class="media-heading">{nm}</h4>\n' \
          '{tbl}{sub}' \
          ' </div>\n' \
          '</div>\n'.format(
            img='<img class="media-object icn32" src="{src}">'.format(src=get_icon_src(icon_id, sde_icon_ids)),
            nm=sde_group["nameID"]["en"],
            tbl=tbl_glf,
            sub=sub_glf
          )
    return glf


def dump_market_groups_tree(glf, sde_market_groups, sde_icon_ids, market_groups_tree, market_data, market_data_printer):
    glf.write("""<ul class="media-list">
 <li class="media">""")

    if "roots" in market_groups_tree:
        roots = market_groups_tree["roots"]
        for group_id in roots:
            glf.write(
                dump_market_groups_tree_nested(
                    group_id,
                    sde_market_groups,
                    sde_icon_ids,
                    market_groups_tree,
                    market_data,
                    market_data_printer)
            )

    glf.write(""" </li>
</ul>""")


def dump_bpos_into_report(
        sde_type_ids,
        sde_market_groups,
        sde_icon_ids,
        sde_bp_materials,
        corp_assets_data,
        corp_blueprints_data,
        market_groups_tree):
    market_data = {}
    for a in corp_assets_data:
        if not (str(a["type_id"]) in sde_bp_materials):
            continue
        if ("is_blueprint_copy" in a) and a["is_blueprint_copy"]:
            continue
        item_id = a["item_id"]
        blueprint = next((b for b in corp_blueprints_data if b["item_id"] == item_id), None)
        if blueprint is None:
            continue
        type_id = sde_type_ids[str(a["type_id"])]
        data_item = {
            "type_id": int(a["type_id"]),
            "name": type_id["name"]["en"],
            "me": blueprint["material_efficiency"],
            "te": blueprint["time_efficiency"],
            "quantity": 1
        }
        if "basePrice" in type_id:
            data_item["price"] = type_id["basePrice"]
        group_id = type_id["marketGroupID"]
        if not (str(group_id) in market_data):
            market_data[str(group_id)] = [data_item]
        else:
            prev_items = market_data[str(group_id)]
            found = False
            for prev in prev_items:
                if (prev["type_id"] == data_item["type_id"]) and (prev["me"] == data_item["me"])  and (prev["te"] == data_item["te"]):
                    prev["quantity"] = prev["quantity"] + 1
                    found = True
                    break
            if not found:
                market_data[str(group_id)].append(data_item)

    def blueprints_printer(group_id, market_data):
        if not (str(group_id) in market_data):
            return ""
        res = '<table class="table">\n' \
              '<thead>' \
              '<tr>' \
              '<th>#</th>' \
              '<th>Blueprint</th>' \
              '<th>Base Price</th>' \
              '<th>Material Efficiency</th>' \
              '<th>Time Efficiency</th>' \
              '<th>Quantity</th>' \
              '</tr>' \
              '</thead>\n' \
              '<tbody>\n'
        items = market_data[str(group_id)]
        num = 1
        for item in items:
            res = res + '<tr>' \
                        '<th scope="row">{num}</th>' \
                        '<td>{nm}</td>' \
                        '<td>{prc}</td>' \
                        '<td>{me}</td>' \
                        '<td>{te}</td>' \
                        '<td>{q}</td>' \
                        '</tr>\n'.format(
                            num=num,
                            nm=item["name"],
                            prc=item["price"] if "price" in item else "",
                            me=item["me"],
                            te=item["te"],
                            q=item["quantity"]
                        )
            num = num + 1
        res = res + '</tbody>\n' \
                    '</table>\n'
        return res

    glf = open('{tmp}/bpos.html'.format(tmp=q_industrialist_settings.g_tmp_directory), "wt+", encoding='utf8')
    try:
        dump_header(glf, "BPOs")
        dump_market_groups_tree(glf, sde_market_groups, sde_icon_ids, market_groups_tree, market_data, blueprints_printer)
        dump_footer(glf)
    finally:
        glf.close()


if __name__ == "__main__":
    main()
