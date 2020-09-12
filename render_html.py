import time
import tzlocal
import math
import re

from datetime import datetime
from eve_sde_tools import get_yaml
from eve_sde_tools import get_item_name_by_type_id
from eve_sde_tools import get_type_id_by_item_name
from eve_sde_tools import get_basis_market_group_by_type_id
from eve_sde_tools import get_blueprint_manufacturing_materials
from eve_sde_tools import get_blueprint_reaction_materials
from eve_sde_tools import get_blueprint_type_id_by_product_id
from eve_sde_tools import is_type_id_nested_into_market_group
from eve_esi_tools import get_assets_location_name
from eve_esi_tools import is_location_nested_into_another

import q_industrialist_settings
import q_logist_settings
import q_blueprints_settings

g_local_timezone = tzlocal.get_localzone()


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
        dt=datetime.fromtimestamp(time.time(), g_local_timezone).strftime('%a, %d %b %Y %H:%M:%S %z')))
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


def __is_availabe_blueprints_present(
        type_id,
        corp_bp_loc_data,
        sde_bp_materials,
        exclude_loc_ids,
        blueprint_station_ids,
        corp_assets_tree):
    # определем type_id чертежа по известному type_id материала
    blueprint_type_id, __stub01 = get_blueprint_type_id_by_product_id(type_id, sde_bp_materials)
    # проверяем, возможно этот материал нельзя произвести с помощью чертежей?
    if blueprint_type_id is None:
        return False, False, True
    # поиск чертежей, по их type_id в списках имеющихся у корпы чертежей
    vacant_originals = vacant_copies = None
    loc_ids = corp_bp_loc_data.keys()
    for loc in loc_ids:
        loc_id = int(loc)
        # пропускаем контейнеры, их которых нельзя доставать чертежи для достройки недостающих материалов
        if int(loc_id) in exclude_loc_ids:
            continue
        # пропускаем прочие станции, на которых нет текущего stock-а и нет конвейеров (ищем свою станку)
        if not is_location_nested_into_another(loc_id, blueprint_station_ids, corp_assets_tree):
            continue
        # проверяем состояния чертежей
        __bp2 = corp_bp_loc_data[str(loc)]
        __bp2_keys = __bp2.keys()
        for __blueprint_type_id in __bp2_keys:
            if int(__blueprint_type_id) != int(blueprint_type_id):
                continue
            bp_keys = __bp2[__blueprint_type_id].keys()
            for bpk in bp_keys:
                bp = __bp2[__blueprint_type_id][bpk]
                if not (bp["st"] is None):  # пропускаем чертежи, по которым ведётся работы
                    continue
                if bp["cp"]:
                    vacant_copies = True
                else:
                    vacant_originals = True
                if not (vacant_copies is None) and vacant_copies and not (vacant_originals is None) and vacant_originals:
                    break
            if not (vacant_copies is None) and vacant_copies and not (vacant_originals is None) and vacant_originals:
                break
        if not (vacant_copies is None) and vacant_copies and not (vacant_originals is None) and vacant_originals:
            break
    if vacant_copies is None:
        vacant_copies = False
    if vacant_originals is None:
        vacant_originals = False
    return vacant_originals, vacant_copies, False


def __dump_blueprints_list_with_materials(
        glf,
        conveyor_entity,
        corp_bp_loc_data,
        corp_industry_jobs_data,
        corp_ass_loc_data,
        corp_assets_tree,
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        sde_icon_ids,
        enable_copy_to_clipboard=False):
    # получение списков контейнеров и станок из экземпляра контейнера
    stock_all_loc_ids = [int(ces["id"]) for ces in conveyor_entity["stock"]]
    exclude_loc_ids = [int(cee["id"]) for cee in conveyor_entity["exclude"]]
    blueprint_loc_ids = conveyor_entity["containers"]
    blueprint_station_ids = [conveyor_entity["station_id"]]
    # инициализация списка материалов, которых не хватает в производстве
    stock_not_enough_materials = []
    # формирование списка ресурсов, которые используются в производстве
    stock_resources = {}
    if not (stock_all_loc_ids is None):
        for loc_id in stock_all_loc_ids:
            loc_flags = corp_ass_loc_data.keys()
            for loc_flag in loc_flags:
                __a1 = corp_ass_loc_data[loc_flag]
                if str(loc_id) in __a1:
                    __a2 = __a1[str(loc_id)]
                    for itm in __a2:
                        if str(itm) in stock_resources:
                            stock_resources[itm] = stock_resources[itm] + __a2[itm]
                        else:
                            stock_resources.update({itm: __a2[itm]})

    loc_ids = corp_bp_loc_data.keys()
    for loc in loc_ids:
        loc_id = int(loc)
        __container = next((cec for cec in blueprint_loc_ids if cec['id'] == loc_id), None)
        if __container is None:
            continue
        loc_name = __container["name"]
        fixed_number_of_runs = __container["fixed_number_of_runs"]
        glf.write(
            ' <div class="panel panel-default">\n'
            '  <div class="panel-heading" role="tab" id="headingB{id}">\n'
            '   <h4 class="panel-title">\n'
            '    <a role="button" data-toggle="collapse" data-parent="#accordion" '
            '       href="#collapseB{id}" aria-expanded="true" aria-controls="collapseB{id}">{station} <mark>{nm}</mark></a>\n'
            '   </h4>\n'
            '  </div>\n'
            '  <div id="collapseB{id}" class="panel-collapse collapse" role="tabpanel" '
            'aria-labelledby="headingB{id}">\n'
            '   <div class="panel-body">\n'.format(
                id=loc_id,
                station=conveyor_entity["station"],
                nm=loc_name
            )
        )
        __bp2 = corp_bp_loc_data[str(loc_id)]
        __type_keys = __bp2.keys()
        # сортировка чертежей по их названиям
        type_keys = []
        for type_id in __type_keys:
            type_keys.append({"id": int(type_id), "name": get_item_name_by_type_id(sde_type_ids, int(type_id))})
        type_keys.sort(key=lambda bp: bp["name"])
        # вывод в отчёт инфорации о чертежах
        materials_summary = []
        for type_dict in type_keys:
            type_id = type_dict["id"]
            blueprint_name = type_dict["name"]
            glf.write(
                '<div class="media">\n'
                ' <div class="media-left">\n'
                '  <img class="media-object icn64" src="{src}" alt="{nm}">\n'
                ' </div>\n'
                ' <div class="media-body">\n'
                '  <h4 class="media-heading">{nm}</h4>\n'.format(
                    src=__get_img_src(type_id, 64),
                    nm=blueprint_name
                )
            )
            __blueprint_materials = None
            __is_reaction_formula = is_type_id_nested_into_market_group(type_id, [1849], sde_type_ids, sde_market_groups)
            if __is_reaction_formula:  # Reaction Formulas
                __blueprint_materials = get_blueprint_reaction_materials(sde_bp_materials, type_id)
            else:
                __blueprint_materials = get_blueprint_manufacturing_materials(sde_bp_materials, type_id)
            bp_keys = __bp2[type_id].keys()
            for bpk in bp_keys:
                bp = __bp2[type_id][bpk]
                is_blueprint_copy = bp["cp"]
                quantity_or_runs = bp["qr"]
                material_efficiency = bp["me"]
                time_efficiency = bp["te"]
                blueprint_status = bp["st"]
                glf.write(
                    '<span class="qind-blueprints-{status}">'
                    '<span class="label label-{cpc}">{cpn}</span>{me_te}'
                    '&nbsp;<span class="badge">{qr}{fnr}</span>\n'.format(
                        qr=quantity_or_runs,
                        fnr=' x{}'.format(fixed_number_of_runs) if not (fixed_number_of_runs is None) else "",
                        cpc='default' if is_blueprint_copy else 'info',
                        cpn='copy' if is_blueprint_copy else 'original',
                        me_te='&nbsp;<span class="label label-success">{me} {te}</span>'.format(me=material_efficiency, te=time_efficiency) if not __is_reaction_formula else "",
                        status=blueprint_status if not (blueprint_status is None) else ""
                    )
                )
                if not (blueprint_status is None):  # [ active, cancelled, delivered, paused, ready, reverted ]
                    if (blueprint_status == "active") or (blueprint_status == "delivered"):
                        glf.write('&nbsp;<span class="label label-primary">{}</span>'.format(blueprint_status))
                    elif blueprint_status == "ready":
                        glf.write('&nbsp;<span class="label label-success">{}</span>'.format(blueprint_status))
                    elif (blueprint_status == "cancelled") or (blueprint_status == "paused") or (blueprint_status == "reverted"):
                        glf.write('&nbsp;<span class="label label-warning">{}</span>'.format(blueprint_status))
                    else:
                        glf.write('&nbsp;<span class="label label-danger">{}</span>'.format(blueprint_status))
                    glf.write('</br></span>\n')
                elif __blueprint_materials is None:
                    glf.write('&nbsp;<span class="label label-warning">manufacturing impossible</span>')
                    glf.write('</br></span>\n')
                else:
                    glf.write('</br></span>\n')
                    glf.write('<div class="qind-materials-used">\n')  # div(materials)
                    not_enough_materials = []
                    for m in __blueprint_materials:
                        bp_manuf_need_all = 0
                        bp_manuf_need_min = 0
                        for __bp3 in __bp2[type_id][bpk]["itm"]:
                            if is_blueprint_copy:
                                quantity_or_runs = __bp3["r"]
                            else:
                                quantity_or_runs = __bp3["q"] if __bp3["q"] > 0 else 1
                                if fixed_number_of_runs:
                                    quantity_or_runs = quantity_or_runs * fixed_number_of_runs
                            __used = int(m["quantity"]) * quantity_or_runs  # сведения из чертежа
                            __need = __used  # поправка на эффективнсть материалов
                            if not __is_reaction_formula:
                                # TODO: хардкодим -1% structure role bonus, -4.2% installed rig
                                # см. 1 x run: http://prntscr.com/u0g07w
                                # см. 4 x run: http://prntscr.com/u0g0cd
                                # см. экономия материалов: http://prntscr.com/u0g11u
                                __me = int(100 - material_efficiency - 1 - 4.2)
                                __need = int((__used * __me) / 100)
                                if 0 != ((__used * __me) % 100):
                                    __need = __need + 1
                            # считаем общее количество материалов, необходимых для работ по этом чертежу
                            bp_manuf_need_all = bp_manuf_need_all + __need
                            # вычисляем минимально необходимое материалов, необходимых для работ хотя-бы по одному чертежу
                            bp_manuf_need_min = __need if bp_manuf_need_min == 0 else min(bp_manuf_need_min, __need)
                        bpmm_tid = int(m["typeID"])
                        bpmm_tnm = get_item_name_by_type_id(sde_type_ids, bpmm_tid)
                        # проверка наличия имеющихся ресурсов для постройки по этому БП
                        not_available = bp_manuf_need_all
                        not_available_absolutely = True
                        if bpmm_tid in stock_resources:
                            __stock = stock_resources[bpmm_tid]
                            not_available = 0 if __stock >= not_available else not_available - __stock
                            not_available_absolutely = __stock < bp_manuf_need_min
                        # вывод наименования ресурса
                        glf.write(
                            '<span style="white-space:nowrap">'
                            '<img class="icn24" src="{src}"> {q:,d} x {nm} '
                            '</span>\n'.format(
                                src=__get_img_src(bpmm_tid, 32),
                                q=bp_manuf_need_all,
                                nm=bpmm_tnm
                            )
                        )
                        # сохраняем недостающее кол-во материалов для производства по этому чертежу
                        if not_available > 0:
                            not_enough_materials.append({"id": bpmm_tid, "q": not_available, "nm": bpmm_tnm, "absol": not_available_absolutely})
                        # сохраняем материалы для производства в список их суммарного кол-ва
                        __summary_dict = next((ms for ms in materials_summary if ms['id'] == int(m["typeID"])), None)
                        if __summary_dict is None:
                            __summary_dict = {"id": int(m["typeID"]), "q": bp_manuf_need_all, "nm": bpmm_tnm}
                            materials_summary.append(__summary_dict)
                        else:
                            __summary_dict["q"] += bp_manuf_need_all
                    glf.write('</div>\n')  # div(materials)
                    # отображение списка материалов, которых не хватает
                    if len(not_enough_materials) > 0:
                        glf.write('<div>\n')  # div(not_enough_materials)
                        for m in not_enough_materials:
                            glf.write(
                                '&nbsp;<span class="label label-{absol}">'
                                '<img class="icn24" src="{src}"> {q:,d} x {nm} '
                                '</span>\n'.format(
                                    src=__get_img_src(m["id"], 32),
                                    q=m["q"],
                                    nm=m["nm"],
                                    absol="danger" if m["absol"] else "warning"
                                )
                            )
                        glf.write('</div>\n')  # div(not_enough_materials)
            glf.write(
                ' </div>\n'  # media-body
                '</div>\n'  # media
            )
        # отображение в отчёте summary-информаци по недостающим материалам
        if len(materials_summary) > 0:
            # поиск групп, которым принадлежат материалы, которых не хватает для завершения производства по списку
            # чертеже в этом контейнере (планетарка отдельно, композиты отдельно, запуск работ отдельно)
            material_groups = {}
            for __summary_dict in materials_summary:
                __quantity = __summary_dict["q"]
                __type_id = __summary_dict["id"]
                __item_name = __summary_dict["nm"]
                __market_group = get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, __type_id)
                __material_dict = {"id": __type_id, "q": __quantity, "nm": __item_name}
                if str(__market_group) in material_groups:
                    material_groups[str(__market_group)].append(__material_dict)
                else:
                    material_groups.update({str(__market_group): [__material_dict]})
            # сортировка summary materials списка по названиям элементов
            materials_summary.sort(key=lambda m: m["nm"])
            glf.write(
                '<hr><div class="media">\n'
                ' <div class="media-left">\n'
                '  <span class="glyphicon glyphicon-alert" aria-hidden="false" style="font-size: 64px;"></span>\n'
                ' </div>\n'
                ' <div class="media-body">\n'
                '  <div class="qind-materials-used">'
                '  <h4 class="media-heading">Summary materials</h4>\n'
            )
            for __summary_dict in materials_summary:
                __quantity = __summary_dict["q"]
                __type_id = __summary_dict["id"]
                __item_name = __summary_dict["nm"]
                glf.write(
                    '<span style="white-space:nowrap">'
                    '<img class="icn24" src="{src}"> {q:,d} x {nm} '
                    '</span>\n'.format(
                        src=__get_img_src(__type_id, 32),
                        q=__quantity,
                        nm=__item_name
                    )
                )
            glf.write('<hr></div>\n')  # qind-materials-used

            # вывод списка материалов, которых не хватает для завершения производства по списку чертежей
            not_available_row_num = 1
            ms_groups = material_groups.keys()
            for ms_group_id in ms_groups:
                material_groups[ms_group_id].sort(key=lambda m: m["nm"])
                group_diplayed = False
                for __material_dict in material_groups[ms_group_id]:
                    # получение данных по материалу
                    ms_type_id = __material_dict["id"]
                    not_available = __material_dict["q"]
                    ms_item_name = __material_dict["nm"]
                    if ms_type_id in stock_resources:
                        not_available = 0 if stock_resources[ms_type_id] >= not_available else \
                            not_available - stock_resources[ms_type_id]
                    if not_available > 0:
                        # формирование выходного списка недостающих материалов
                        __stock_ne = next((ne for ne in stock_not_enough_materials if ne['id'] == ms_type_id), None)
                        if __stock_ne is None:
                            stock_not_enough_materials.append({"id": ms_type_id, "q": not_available})
                        else:
                            __stock_ne["q"] += not_available
                        # вывод сведений в отчёт
                        if not_available_row_num == 1:
                            glf.write("""
<h4 class="media-heading">Not available materials</h4>
<div class="table-responsive">
<table class="table table-condensed table-hover">
<thead>
<tr>
<th style="width:40px;">#</th>
<th>Materials</th>
<th>Not available</th>
<th>In progress</th>
</tr>
</thead>
<tbody>
""")
                        # выводим название группы материалов (Ship Equipment, Materials, Components, ...)
                        if not group_diplayed:
                            __grp_name = sde_market_groups[ms_group_id]["nameID"]["en"]
                            __icon_id = sde_market_groups[ms_group_id]["iconID"] if "iconID" in sde_market_groups[ms_group_id] else 0
                            # подготовка элементов управления копирования данных в clipboard
                            __copy2clpbrd = '' if not enable_copy_to_clipboard else \
                                '&nbsp;<a data-target="#" role="button" class="qind-copy-btn"' \
                                '  data-toggle="tooltip"><button type="button" class="btn btn-default btn-xs"><span' \
                                '  class="glyphicon glyphicon-copy" aria-hidden="true"></span> Export to multibuy</button></a>'
                            glf.write(
                                '<tr>\n'
                                # ' <td class="active" colspan="4"><img class="icn24" src="{icn}" style="display:inline;">&nbsp;<strong class="text-primary">{nm}</strong><!--{id}-->{clbrd}</td>\n'
                                ' <td class="active" colspan="4"><strong>{nm}</strong><!--{id}-->{clbrd}</td>\n'
                                '</tr>'.
                                format(nm=__grp_name,
                                       # icn=__get_icon_src(__icon_id, sde_icon_ids),
                                       id=ms_group_id,
                                       clbrd=__copy2clpbrd))
                            group_diplayed = True
                        # получаем список работ, которые выдутся с этим материалом, а результаты сбрабываются в stock-ALL
                        jobs = [j for j in corp_industry_jobs_data if
                                    (j["product_type_id"] == ms_type_id) and
                                    (j['output_location_id'] in stock_all_loc_ids)]
                        in_progress = 0
                        for j in jobs:
                            in_progress = in_progress + j["runs"]
                        # умножаем на кол-во производимых материалов на один run
                        __stub01, __bp_dict = get_blueprint_type_id_by_product_id(ms_type_id, sde_bp_materials)
                        if not (__bp_dict is None):
                            in_progress *= __bp_dict["activities"]["manufacturing"]["products"][0]["quantity"]
                        # получаем список чертежей, которые имеются в распоряжении корпорации для постройки этих материалов
                        vacant_originals, vacant_copies, not_a_product = __is_availabe_blueprints_present(
                            ms_type_id,
                            corp_bp_loc_data,
                            sde_bp_materials,
                            exclude_loc_ids,
                            blueprint_station_ids,
                            corp_assets_tree)
                        # формируем информационные тэги по имеющимся (вакантным) цертежам для запуска производства
                        vacant_originals_tag = ""
                        vacant_copies_tag = ""
                        absent_blueprints_tag = ""
                        if not_available > in_progress:
                            if not not_a_product and vacant_originals:
                                vacant_originals_tag = ' <span class="label label-info">original</span>'
                            if not not_a_product and vacant_copies:
                                vacant_copies_tag = ' <span class="label label-default">copy</span>'
                            if not not_a_product and not vacant_originals and not vacant_copies:
                                absent_blueprints_tag = ' <span class="label label-danger">no blueprints</span>'
                        # подготовка элементов управления копирования данных в clipboard
                        __copy2clpbrd = '' if not enable_copy_to_clipboard else \
                            '&nbsp;<a data-target="#" role="button" data-copy="{nm}" class="qind-copy-btn"' \
                            '  data-toggle="tooltip"><span class="glyphicon glyphicon-copy"'\
                            '  aria-hidden="true"></span></a>'. \
                            format(nm=ms_item_name)
                        # вывод сведений в отчёт
                        glf.write(
                            '<tr>\n'
                            ' <th scope="row">{num}</th>\n'
                            ' <td><img class="icn24" src="{src}"> {nm}{clbrd}</td>\n'
                            ' <td quantity="{q}">{q:,d}{original}{copy}{absent}</td>\n'
                            ' <td>{inp}</td>\n'
                            '</tr>'.
                            format(num=not_available_row_num,
                                   src=__get_img_src(ms_type_id, 32),
                                   q=not_available,
                                   inp='{:,d}'.format(in_progress) if in_progress > 0 else '',
                                   nm=ms_item_name,
                                   clbrd=__copy2clpbrd,
                                   original=vacant_originals_tag,
                                   copy=vacant_copies_tag,
                                   absent=absent_blueprints_tag)
                        )
                        not_available_row_num = not_available_row_num + 1
            if not_available_row_num != 1:
                glf.write("""
</tbody>
</table>
</div>
""")
            glf.write(
                ' </div>\n'
                '</div>\n'
            )
        glf.write(
            "   </div>\n"
            "  </div>\n"
            " </div>\n"
        )

    return stock_not_enough_materials


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

        __dump_any_into_modal_header(glf, "Corp Blueprints")
        __dump_blueprints_list_with_materials(glf, corp_bp_loc_data, corp_industry_jobs_data, corp_ass_names_data, corp_ass_loc_data, corp_assets_tree, sde_type_ids, sde_bp_materials, sde_market_groups, sde_icon_ids, stock_all_loc_ids, exclude_loc_ids, blueprint_loc_ids, blueprint_station_ids)
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


def __get_route_signalling_type(level):
    if level == 0:
        return "success"
    elif level == 1:
        return "warning"
    elif (level == 2) or (level == 3):
        return "danger"


def __dump_corp_cynonetwork(glf, sde_inv_positions, corp_cynonetwork):
    glf.write("""
<style>
.dropdown-submenu {
  position: relative;
}
.dropdown-submenu .dropdown-menu {
  top: 0;
  left: 100%;
  margin-top: -1px;
}
</style>

<nav class="navbar navbar-default">
 <div class="container-fluid">
  <div class="navbar-header">
   <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#bs-navbar-collapse" aria-expanded="false">
    <span class="sr-only">Toggle navigation</span>
    <span class="icon-bar"></span>
    <span class="icon-bar"></span>
    <span class="icon-bar"></span>
   </button>
   <a class="navbar-brand" data-target="#"><span class="glyphicon glyphicon-random" aria-hidden="true"></span></a>
  </div>
   
  <div class="collapse navbar-collapse" id="bs-navbar-collapse">
   <ul class="nav navbar-nav">
    <li class="dropdown">
     <a data-target="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Routes <span class="caret"></span></a>
      <ul class="dropdown-menu">""")
    cynonet_num = 1
    for cn in q_logist_settings.g_cynonetworks:
        cn_route = cn["route"]
        from_id = cn_route[0]
        from_name = corp_cynonetwork[str(from_id)]["solar_system"]
        to_id = cn_route[-1]
        to_name = corp_cynonetwork[str(to_id)]["solar_system"]
        glf.write(
            '\n       '
            '<li><a id="btnCynoNetSel" cynonet="{cnn}" data-target="#" role="button"><span '
                   'class="glyphicon glyphicon-star img-cyno-net" cynonet="{cnn}" aria-hidden="true"></span> '
            '{f} &rarr; {t}</a></li>'.  # предполагается: <li><a>JK-Q77 &rarr; Raravath</a></li>
            format(f=from_name,
                   t=to_name,
                   cnn=cynonet_num
            ))
        cynonet_num = cynonet_num + 1
    glf.write("""
       <li role="separator" class="divider"></li>
       <li><a id="btnCynoNetSel" cynonet="0" data-target="#" role="button"><span 
              class="glyphicon glyphicon-star img-cyno-net" cynonet="0" aria-hidden="true"></span> All routes</a></li>
     </ul>
    </li>
    
    <li class="dropdown">
     <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Jump Options <span class="caret"></span></a>
      <ul class="dropdown-menu">

       <li class="dropdown-submenu">
         <a class="options-submenu" data-target="#" role="button">Ship <mark id="lbJumpShip"></mark><span class="caret"></span></a>
         <ul class="dropdown-menu">
           <li class="dropdown-header">[Jump Freighters]</li>
           <li><a id="btnJumpShip" ship="Anshar" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgJumpShipAnshar"></span> Anshar</a></li>
           <li><a id="btnJumpShip" ship="Ark" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgJumpShipArk"></span> Ark</a></li>
           <li><a id="btnJumpShip" ship="Nomad" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgJumpShipNomad"></span> Nomad</a></li>
           <li><a id="btnJumpShip" ship="Rhea" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgJumpShipRhea"></span> Rhea</a></li>
           <li role="separator" class="divider"></li>
           <li><a id="btnJumpAnyShip" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgJumpAnyShip"></span> Any Ship</a></li>
         </ul>
       </li>

       <li class="dropdown-submenu">
         <a class="options-submenu" data-target="#" role="button">Jump Drive Calibration <mark id="lbJumpCalibration"></mark><span class="caret"></span></a>
         <ul class="dropdown-menu">
           <li><a id="btnJumpCalibration" skill="1" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgJumpCalibration1"></span> 1</a></li>
           <li><a id="btnJumpCalibration" skill="2" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgJumpCalibration2"></span> 2</a></li>
           <li><a id="btnJumpCalibration" skill="3" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgJumpCalibration3"></span> 3</a></li>
           <li><a id="btnJumpCalibration" skill="4" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgJumpCalibration4"></span> 4</a></li>
           <li><a id="btnJumpCalibration" skill="5" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgJumpCalibration5"></span> 5</a></li>
         </ul>
       </li>

       <li class="dropdown-submenu">
         <a class="options-submenu" data-target="#" role="button">Jump Fuel Conservation <mark id="lbJumpConservation"></mark><span class="caret"></span></a>
         <ul class="dropdown-menu">
           <li><a id="btnJumpConservation" skill="1" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgJumpConservation1"></span> 1</a></li>
           <li><a id="btnJumpConservation" skill="2" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgJumpConservation2"></span> 2</a></li>
           <li><a id="btnJumpConservation" skill="3" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgJumpConservation3"></span> 3</a></li>
           <li><a id="btnJumpConservation" skill="4" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgJumpConservation4"></span> 4</a></li>
           <li><a id="btnJumpConservation" skill="5" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgJumpConservation5"></span> 5</a></li>
         </ul>
       </li>

       <li class="dropdown-submenu">
         <a class="options-submenu" data-target="#" role="button">Jump Freighter <mark id="lbJumpFreighter"></mark><span class="caret"></span></a>
         <ul class="dropdown-menu">
           <li><a id="btnJumpFreighter" skill="1" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgJumpFreighter1"></span> 1</a></li>
           <li><a id="btnJumpFreighter" skill="2" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgJumpFreighter2"></span> 2</a></li>
           <li><a id="btnJumpFreighter" skill="3" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgJumpFreighter3"></span> 3</a></li>
           <li><a id="btnJumpFreighter" skill="4" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgJumpFreighter4"></span> 4</a></li>
           <li><a id="btnJumpFreighter" skill="5" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgJumpFreighter5"></span> 5</a></li>
         </ul>
       </li>

       <li role="separator" class="divider"></li>
       <li><a id="btnResetOptions" data-target="#" role="button">Reset options</a></li>
      </ul>
    </li>
    
    <li class="disabled"><a data-target="#" role="button">Problems</a></li>
   </ul>
   <form class="navbar-form navbar-right">
    <div class="form-group">
     <input type="text" class="form-control" placeholder="Solar System" disabled>
    </div>
    <button type="button" class="btn btn-default disabled">Search</button>
   </form>
  </div>
 </div>
</nav>
<div class="container-fluid">""")

    cynonetwork_num = 0
    cynonetwork_distances = []
    for cn in q_logist_settings.g_cynonetworks:
        cynonetwork_num = cynonetwork_num + 1
        cn_route = cn["route"]
        from_id = cn_route[0]
        from_name = corp_cynonetwork[str(from_id)]["solar_system"]
        to_id = cn_route[-1]
        to_name = corp_cynonetwork[str(to_id)]["solar_system"]
        url = ""
        human_readable = ""
        route_signalling_level = 0
        for location_id in cn_route:
            route_place = corp_cynonetwork[str(location_id)]
            system_name = route_place["solar_system"]
            if not url:
                url = system_name
                # from_name = system_name
                human_readable = system_name
            else:
                url = url + ":" + system_name
                # to_name = system_name
                human_readable = human_readable + " &rarr; " + system_name
            route_signalling_level = max(route_signalling_level, route_place["signalling_level"])
        route_signalling_type = __get_route_signalling_type(route_signalling_level)
        # ---
        glf.write(
            '<div class="panel panel-{signal} pn-cyno-net" cynonet="{cnn}">\n'
            ' <div class="panel-heading"><h3 class="panel-title">{signal_sign}{nm}</h3></div>\n'
            '  <div class="panel-body">\n'
            '   <p>Checkout Dotlan link for graphical route building: <a class="lnk-dtln" cynonet="{cnn}" routes="{rs}" href="https://evemaps.dotlan.net/jump/Rhea,544/{url}" class="panel-link">https://evemaps.dotlan.net/jump/Rhea,544/{url}</a></p>\n'
            '   <div class="progress">\n'.
            format(#nm='{} &rarr; {}'.format(from_name, to_name),
                   cnn=cynonetwork_num,
                   rs=len(cn_route),
                   nm=human_readable,
                   url=url,
                   signal=route_signalling_type,
                   signal_sign='<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span> ' if route_signalling_type=="danger" else ""
            ))
        progress_segments = len(cn_route)
        progress_width = int(100/progress_segments)
        progress_times = 1
        for location_id in cn_route:
            route_place = corp_cynonetwork[str(location_id)]
            system_name = route_place["solar_system"]
            if progress_times == progress_segments:
                progress_width = progress_width + 100 - progress_width * progress_segments
            if not ("error" in route_place):
                glf.write(
                    '    <div id="prgrCynoRoute{cnn}_{pt}" class="progress-bar progress-bar-{signal} signal" role="progressbar" style="width:{width}%">{nm}</div>\n'.
                    format(width=progress_width,
                           nm=system_name,
                           signal=__get_route_signalling_type(route_place["signalling_level"]),
                           cnn=cynonetwork_num,
                           pt=progress_times
                    ))
            else:
                glf.write(
                    '    <div class="progress-bar signal" role="progressbar" style="width:{width}%; background-color:#888;">{nm}</div>\n'.
                    format(width=progress_width,
                           nm=system_name
                    ))
            progress_times = progress_times + 1
        glf.write("""   </div>
   <table class="table qind-tbl-cynonet">
    <thead>
     <tr>
      <th>#</th>
      <th>Solar System</th>
      <th><img src="https://imageserver.eveonline.com/Type/648_32.png" width="32px" height="32px" alt="Badger"/></th>
      <th><img src="https://imageserver.eveonline.com/Type/32880_32.png" width="32px" height="32px" alt="Venture"/><img
               src="https://imageserver.eveonline.com/Type/1317_32.png" width="32px" height="32px" alt="Expanded Cargohold I"/><img
               src="https://imageserver.eveonline.com/Type/31117_32.png" width="32px" height="32px" alt="Small Cargohold Optimization I"/></th>
      <th><img src="https://imageserver.eveonline.com/Type/52694_32.png" width="32px" height="32px" alt="Industrial Cynosural Field Generator"/></th>
      <th><img src="https://imageserver.eveonline.com/Type/16273_32.png" width="32px" height="32px" alt="Liquid Ozone"/></th>
      <th class="nitrogen">Nitrogen</th><th class="hydrogen">Hydrogen</th><th class="oxygen">Oxygen</th><th class="helium">Helium</th>
     </tr>
    </thead>
    <tbody>""")
        # --- расчёт дистанции прыжка
        prev_system_id = None
        row_num = 1
        lightyear_distances = []
        for location_id in cn_route:
            route_place = corp_cynonetwork[str(location_id)]
            system_id = route_place["system_id"]
            if row_num > 1:
                pos1 = sde_inv_positions[str(system_id)] if not (system_id is None) and (str(system_id) in sde_inv_positions) else None
                pos2 = sde_inv_positions[str(prev_system_id)] if not (prev_system_id is None) and (str(prev_system_id) in sde_inv_positions) else None
                if not (pos1 is None) and not (pos2 is None):
                    # https://en.wikipedia.org/wiki/Euclidean_distance
                    distance = math.sqrt((pos1["x"]-pos2["x"]) ** 2 + (pos1["y"]-pos2["y"]) ** 2 + (pos1["z"]-pos2["z"]) ** 2)
                    # https://github.com/nikdoof/cynomap
                    # ...Distance calculation is based on CCP's lightyear being 9460000000000000 meters, instead of
                    # the actual value of 9460730472580800 meters...
                    distance = distance / 9460000000000000
                    lightyear_distances.append(distance)  # lightyears
                    # https://wiki.eveuniversity.org/Jump_drives#Jumpdrive_Isotope_Usage_Formula
                    # ... moved to javascript logic ...
                else:
                    lightyear_distances.append(None)
            prev_system_id = system_id
            row_num = row_num + 1
        cynonetwork_distances.append(lightyear_distances)
        # --- построение таблицы по маршруту циносети
        row_num = 1
        for location_id in cn_route:
            route_place = corp_cynonetwork[str(location_id)]
            system_name = route_place["solar_system"]
            lightyears = lightyear_distances[row_num-1] if row_num < len(cn_route) else None
            if not ("error" in route_place) or (route_place["error"] != "no data"):
                badger_num = route_place["badger"]
                venture_num = route_place["venture"]
                liquid_ozone_num = route_place["liquid_ozone"]
                indus_cyno_gen_num = route_place["indus_cyno_gen"]
                exp_cargohold_num = route_place["exp_cargohold"]
                cargohold_rigs_num = route_place["cargohold_rigs"]
                nitrogen_isotope_num = route_place["nitrogen_isotope"]
                hydrogen_isotope_num = route_place["hydrogen_isotope"]
                oxygen_isotope_num = route_place["oxygen_isotope"]
                helium_isotope_num = route_place["helium_isotope"]
                badger_jumps_num = min(badger_num, indus_cyno_gen_num, int(liquid_ozone_num/950))
                venture_jumps_num = min(venture_num, indus_cyno_gen_num, int(liquid_ozone_num/200), exp_cargohold_num, int(cargohold_rigs_num/3))
                glf.write(
                    '<tr id="rowCynoRoute{cnn}_{num}" system="{nm}">\n'
                    ' <th scope="row">{num}</th><td>{nm}</td>\n'
                    ' <td><abbr title="{bjumps} Badger cynos">{b:,d}</abbr></td>\n'
                    ' <td><abbr title="{vjumps} Venture cynos">{v:,d}</abbr> / {ch:,d} / {chr:,d}</td>\n'
                    ' <td>{icg:,d}</td><td>{lo:,d}</td>\n'
                    ' <td class="nitrogen" id="niCynoRoute{cnn}_{num}">{ni:,d}</td>\n'
                    ' <td class="hydrogen" id="hyCynoRoute{cnn}_{num}">{hy:,d}</td>\n'
                    ' <td class="oxygen" id="oxCynoRoute{cnn}_{num}">{ox:,d}</td>\n'
                    ' <td class="helium" id="heCynoRoute{cnn}_{num}">{he:,d}</td>\n'
                    '</tr>'.
                    format(num=row_num,
                           cnn=cynonetwork_num,
                           nm=system_name,
                           bjumps=badger_jumps_num,
                           vjumps=venture_jumps_num,
                           b=badger_num,
                           v=venture_num,
                           lo=liquid_ozone_num,
                           icg=indus_cyno_gen_num,
                           ch=exp_cargohold_num,
                           chr=cargohold_rigs_num,
                           ni=nitrogen_isotope_num,
                           hy=hydrogen_isotope_num,
                           ox=oxygen_isotope_num,
                           he=helium_isotope_num
                    ))
            else:
                glf.write(
                    '<tr>\n'
                    ' <th scope="row">{num}</th><td>{nm}</td>\n'
                    ' <td></td><td></td><td></td><td></td><td></td>\n'
                    '</tr>'.
                    format(num=row_num,
                           nm=system_name))
            if row_num != len(cn_route):
                glf.write(
                    '<tr class="active">\n'
                    ' <th></th><td></td>\n'
                    ' <td colspan="4">{ly}</td><td colspan="4"{ly_val} cynonet="{cnn}" route="{rt}"></td>\n'
                    '</tr>'.
                    format(
                        ly_val=' lightyears="{:0.15f}"'.format(lightyears) if not (lightyears is None) else "",
                        cnn=cynonetwork_num,
                        rt=row_num,
                        ly='Distance: <strong>{:0.3f} ly</strong>'.format(lightyears) if not (lightyears is None) else ""
                    ))
            row_num = row_num + 1
        glf.write("""
    </tbody>
    <tfoot>
     <tr>
      <td colspan="2"></td>
      <td colspan="5">
""")
        # добавляем диалоговое окно, в котором будет видно что именно не хватает на маршруте, и в каком количестве?
        __dump_any_into_modal_header(
            glf,
            'What''s missing on the route <span class="text-primary">{f} &rarr; {t}</span>?'.format(f=from_name,t=to_name),
            'NotEnough{cnn}'.format(cnn=cynonetwork_num),
            "btn-sm",
            "Not enough&hellip;")
        # формируем содержимое модального диалога
        glf.write("""
<div class="table-responsive">
 <table class="table table-condensed table-hover">
<thead>
 <tr>
  <th>#</th>
  <th>Solar System</th>
  <th><img src="https://imageserver.eveonline.com/Type/648_32.png" width="32px" height="32px" alt="Badger"/></th>
  <th><img src="https://imageserver.eveonline.com/Type/32880_32.png" width="32px" height="32px" alt="Venture"/><img
           src="https://imageserver.eveonline.com/Type/1317_32.png" width="32px" height="32px" alt="Expanded Cargohold I"/><img
           src="https://imageserver.eveonline.com/Type/31117_32.png" width="32px" height="32px" alt="Small Cargohold Optimization I"/></th>
  <th><img src="https://imageserver.eveonline.com/Type/52694_32.png" width="32px" height="32px" alt="Industrial Cynosural Field Generator"/></th>
  <th><img src="https://imageserver.eveonline.com/Type/16273_32.png" width="32px" height="32px" alt="Liquid Ozone"/></th>
  <th class="nitrogen">Nitrogen</th><th class="hydrogen">Hydrogen</th><th class="oxygen">Oxygen</th><th class="helium">Helium</th>
 </tr>
</thead>
<tbody>
""")
        # выводим сводную информацию
        row_num = 1
        badger_num_ne_summary = 0
        venture_num_ne_summary = 0
        exp_cargohold_num_ne_summary = 0
        cargohold_rigs_num_ne_summary = 0
        indus_cyno_gen_num_ne_summary = 0
        liquid_ozone_num_ne_summary = 0
        for location_id in cn_route:
            route_place = corp_cynonetwork[str(location_id)]
            system_name = route_place["solar_system"]
            if not ("error" in route_place) or (route_place["error"] != "no data"):
                badger_num = route_place["badger"]
                venture_num = route_place["venture"]
                liquid_ozone_num = route_place["liquid_ozone"]
                indus_cyno_gen_num = route_place["indus_cyno_gen"]
                exp_cargohold_num = route_place["exp_cargohold"]
                cargohold_rigs_num = route_place["cargohold_rigs"]
                #---
                badger_num_ne = 11 - badger_num if badger_num <= 11 else 0
                venture_num_ne = 11 - venture_num if venture_num <= 11 else 0
                exp_cargohold_num_ne = 11 - exp_cargohold_num if exp_cargohold_num <= 11 else 0
                cargohold_rigs_num_ne = 33 - cargohold_rigs_num if cargohold_rigs_num <= 33 else 0
                indus_cyno_gen_num_ne = 11 - indus_cyno_gen_num if indus_cyno_gen_num <= 11 else 0
                liquid_ozone_num_ne = 950*11 - liquid_ozone_num if liquid_ozone_num <= (950*11) else 0
                #---
                badger_num_ne_summary += badger_num_ne
                venture_num_ne_summary += venture_num_ne
                exp_cargohold_num_ne_summary += exp_cargohold_num_ne
                cargohold_rigs_num_ne_summary += cargohold_rigs_num_ne
                indus_cyno_gen_num_ne_summary += indus_cyno_gen_num_ne
                liquid_ozone_num_ne_summary += liquid_ozone_num_ne
                glf.write(
                    '<tr id="rowNotEnough{cnn}_{num}" system="{nm}">\n'
                    ' <th scope="row">{num}</th><td>{nm}</td>\n'
                    ' <td>{bne:,d}</td>\n'
                    ' <td>{vne:,d} / {chne:,d} / {chrne:,d}</td>\n'
                    ' <td>{icgne:,d}</td><td>{lone:,d}</td>\n'
                    ' <td class="nitrogen"></td>\n'
                    ' <td class="hydrogen"></td>\n'
                    ' <td class="oxygen"></td>\n'
                    ' <td class="helium"></td>\n'
                    '</tr>'.
                    format(num=row_num,
                           cnn=cynonetwork_num,
                           nm=system_name,
                           bne=badger_num_ne,
                           vne=venture_num_ne,
                           chne=exp_cargohold_num_ne,
                           chrne=cargohold_rigs_num_ne,
                           icgne=indus_cyno_gen_num_ne,
                           lone=liquid_ozone_num_ne
                    ))
            else:
                glf.write(
                    '<tr>\n'
                    ' <th scope="row">{num}</th><td>{nm}</td>\n'
                    ' <td></td><td></td><td></td><td></td><td></td>\n'
                    '</tr>'.
                    format(num=row_num,
                           nm=system_name))
            row_num = row_num + 1
        # формируем footer модального диалога (формируем summary по недостающим материалам)
        glf.write("""
</tbody>
<tfoot>
""")
        glf.write(
            '<tr id="rowNotEnoughSummary{cnn}" style="font-weight:bold;">\n'
            ' <td colspan="2" align="right">Summary (not enough):</td>\n'
            ' <td>{b:,d}</td>\n'
            ' <td>{v:,d} / {ch:,d} / {chr:,d}</td>\n'
            ' <td>{icg:,d}</td><td>{lo:,d}</td>\n'
            ' <td class="nitrogen"></td>\n'
            ' <td class="hydrogen"></td>\n'
            ' <td class="oxygen"></td>\n'
            ' <td class="helium"></td>\n'
            '</tr>'.
            format(cnn=cynonetwork_num,
                   b=badger_num_ne_summary,
                   v=venture_num_ne_summary,
                   ch=exp_cargohold_num_ne_summary,
                   chr=cargohold_rigs_num_ne_summary,
                   icg=indus_cyno_gen_num_ne_summary,
                   lo=liquid_ozone_num_ne_summary)
        )
        glf.write("""
</tfoot>
 </table>
</div>
""")
        # закрываем footer модального диалога
        __dump_any_into_modal_footer(glf)

        glf.write("""
      </td>
      </tr>
    </tfoot>
   </table>
  </div>
 </div>""")
    glf.write("""<hr/>
<h4>Legend</h4>
  <div class="row">
   <div class="col-xs-3">
    <div class="progress">
     <div class="progress-bar progress-bar-success" role="progressbar" aria-valuenow="95" aria-valuemin="0" aria-valuemax="100" style="width: 95%;"></div>
    </div>
   </div>
   <div class="col-xs-9">10 or more jumps</div>
  </div>

  <div class="row">
   <div class="col-xs-3">
    <div class="progress">
     <div class="progress-bar progress-bar-warning" role="progressbar" aria-valuenow="25" aria-valuemin="0" aria-valuemax="100" style="width: 25%;"></div>
    </div>
   </div>
   <div class="col-xs-9">at least 2 jumps</div>
  </div>

  <div class="row">
   <div class="col-xs-3">
    <div class="progress">
     <div class="progress-bar progress-bar-danger" role="progressbar" aria-valuenow="10" aria-valuemin="0" aria-valuemax="100" style="width: 10%;"></div>
    </div>
   </div>
   <div class="col-xs-9">there is a chance to stop</div>
  </div>

  <div class="row">
   <div class="col-xs-3">
    <div class="progress">
     <div class="progress-bar" role="progressbar" aria-valuenow="50" aria-valuemin="0" aria-valuemax="100" style="width: 50%; background-color:#888;"></div>
    </div>
   </div>
   <div class="col-xs-9">there are temporary problems with ESI (out of sync assets movements)</div>
  </div>
</div>
<script>
  // Cynonetwork contents (data)
  var contentsCynoNetwork = [
""")
    # выгрузка данных для работы с ними с пом. java-script-а (повторный прогон с накопленными данными)
    cynonetwork_num = 1
    for cn in q_logist_settings.g_cynonetworks:
        glf.write('    [{cnn}, [\n'.format(cnn=cynonetwork_num))
        cn_route = cn["route"]
        route_num = 1
        for location_id in cn_route:
            last_route = route_num == len(cn_route)
            route_place = corp_cynonetwork[str(location_id)]
            system_name = route_place["solar_system"]
            lightyears = 0 if last_route else cynonetwork_distances[cynonetwork_num - 1][route_num - 1]
            if not lightyears:
                lightyears = 0
            if not ("error" in route_place) or (route_place["error"] != "no data"):
                nitrogen_isotope_num = route_place["nitrogen_isotope"]
                hydrogen_isotope_num = route_place["hydrogen_isotope"]
                oxygen_isotope_num = route_place["oxygen_isotope"]
                helium_isotope_num = route_place["helium_isotope"]
            else:
                nitrogen_isotope_num = 0
                hydrogen_isotope_num = 0
                oxygen_isotope_num = 0
                helium_isotope_num = 0
            if not ("error" in route_place):
                glf.write("      [{rn},'{nm}','{signal}',{ly},{ni},{hy},{ox},{he}]{comma}\n".
                          format(comma=',' if not last_route else ']',
                                 rn=route_num,
                                 nm=system_name,
                                 signal=__get_route_signalling_type(route_place["signalling_level"]),
                                 ni=nitrogen_isotope_num,
                                 hy=hydrogen_isotope_num,
                                 ox=oxygen_isotope_num,
                                 he=helium_isotope_num,
                                 ly=lightyears))
            route_num = route_num + 1
        glf.write('    ]{comma}\n'.format(comma=',' if cynonetwork_num != len(q_logist_settings.g_cynonetworks) else ''))
        cynonetwork_num = cynonetwork_num + 1
    # крупный листинг с java-программой (без форматирования)
    glf.write("""  ];
  // Jump Options storage (prepare)
  ls = window.localStorage;
  var knownShips = ['Anshar', 'Ark', 'Nomad', 'Rhea'];
  var usedIsotopeTags = ['th', 'td', 'span'];

  // Tools & Utils
  function numLikeEve(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }
  // Jump Options storage (init)
  function resetOptionsMenuToDefault() {
    if (!ls.getItem('CynoNetNum')) {
      ls.setItem('CynoNetNum', 0);
    }
    if (!ls.getItem('Jump Drive Calibration')) {
      ls.setItem('Jump Drive Calibration', 5);
    }
    if (!ls.getItem('Jump Drive Conservation')) {
      ls.setItem('Jump Drive Conservation', 4);
    }
    if (!ls.getItem('Jump Freighter')) {
      ls.setItem('Jump Freighter', 4);
    }
  }
  // Jump Options storage (rebuild menu components)
  function rebuildOptionsMenu() {
    var cynonet = ls.getItem('CynoNetNum');
    $('span.img-cyno-net').each(function() {
      cn = $(this).attr('cynonet');
      if (cn == cynonet)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    });
    var ship = ls.getItem('Ship');
    if (!ship) {
      for (var s of knownShips) {
        $('#imgJumpShip'+s).addClass('hidden');
      }
      $('#imgJumpAnyShip').removeClass('hidden');
      $('#lbJumpShip').addClass('hidden');
    }
    else {
      for (var s of knownShips) {
        if (ship == s)
          $('#imgJumpShip'+s).removeClass('hidden');
        else
          $('#imgJumpShip'+s).addClass('hidden');
      }
      $('#imgJumpAnyShip').addClass('hidden');
      $('#lbJumpShip').html(ship);
      $('#lbJumpShip').removeClass('hidden');
    }
    var skill = ls.getItem('Jump Drive Calibration');
    $('#lbJumpCalibration').html(skill);
    for (var i = 1; i <= 5; i++) {
        if (skill == i)
          $('#imgJumpCalibration'+i.toString()).removeClass('hidden');
        else
          $('#imgJumpCalibration'+i.toString()).addClass('hidden');
    }
    skill = ls.getItem('Jump Drive Conservation');
    $('#lbJumpConservation').html(skill);
    for (var i = 1; i <= 5; i++) {
        if (skill == i)
          $('#imgJumpConservation'+i.toString()).removeClass('hidden');
        else
          $('#imgJumpConservation'+i.toString()).addClass('hidden');
    }
    skill = ls.getItem('Jump Freighter');
    $('#lbJumpFreighter').html(skill);
    for (var i = 1; i <= 5; i++) {
        if (skill == i)
          $('#imgJumpFreighter'+i.toString()).removeClass('hidden');
        else
          $('#imgJumpFreighter'+i.toString()).addClass('hidden');
    }
  }
  // Jump Options storage (rebuild panel links)
  function rebuildPanelLinks() {
    var ship = ls.getItem('Ship');
    if (!ship)
        ship = 'Rhea';
    var calibration_skill = parseInt(ls.getItem('Jump Drive Calibration'));
    var conservation_skill = parseInt(ls.getItem('Jump Drive Conservation'));
    var freighter_skill = parseInt(ls.getItem('Jump Freighter'));
    $('a.lnk-dtln').each(function() {
      cynonet = $(this).attr('cynonet');
      routes = $(this).attr('routes');
      var uri = 'https://evemaps.dotlan.net/jump/'+ship+','+calibration_skill+conservation_skill+freighter_skill+'/';
      for (var i = 1; i <= routes; i++) {
        if (i > 1) uri = uri + ':';
        uri = uri + $('#rowCynoRoute'+cynonet+'_'+i.toString()).attr('system');
      }
      $(this).attr('href', uri);
      $(this).html(uri);
    });
  }
  // Isotope Quantity Calculator
  function calcIsotope(lightyears, fuel_consumption, conservation_skill, freighter_skill) {
    return parseInt(lightyears * fuel_consumption * (1 - 0.1 * conservation_skill) * (1 - 0.1 * freighter_skill), 10);
  }
  // Jump Options storage (rebuild progress bar signals)
  function rebuildProgressBarSignals() {
    var ship = ls.getItem('Ship');
    //TODO:var calibration_skill = parseInt(ls.getItem('Jump Drive Calibration'));
    var conservation_skill = parseInt(ls.getItem('Jump Drive Conservation'));
    var freighter_skill = parseInt(ls.getItem('Jump Freighter'));
    for (var cn of contentsCynoNetwork) {
      cn_num = cn[0];
      for (var rt of cn[1]) {
        ly = rt[3];
        if (!ly) continue;
        signal = rt[2];
        if (signal == 'danger') continue;
        rt_num = rt[0];
        var nitrogen_used = calcIsotope(ly, 10000, conservation_skill, freighter_skill);
        var hydrogen_used = calcIsotope(ly, 8200, conservation_skill, freighter_skill);
        var oxygen_used = calcIsotope(ly, 9400, conservation_skill, freighter_skill);
        var helium_used = calcIsotope(ly, 8800, conservation_skill, freighter_skill);
        var nitrogen_times = parseInt(rt[4] / nitrogen_used, 10);
        var hydrogen_times = parseInt(rt[5] / hydrogen_used, 10);
        var oxygen_times = parseInt(rt[6] / oxygen_used, 10);
        var helium_times = parseInt(rt[7] / helium_used, 10);
        prgr = $('#prgrCynoRoute'+cn_num.toString()+'_'+rt_num.toString());
        if (prgr) {
          var times = 0;
          if (!ship) times = Math.min(nitrogen_times, hydrogen_times, oxygen_times, helium_times);
          else if (ship == 'Anshar') times = oxygen_times; // Gallente : Oxygen isotopes
          else if (ship == 'Ark') times = helium_times; // Amarr : Helium isotopes
          else if (ship == 'Nomad') times = hydrogen_times; // Minmatar : Hydrogen isotopes
          else if (ship == 'Rhea') times = nitrogen_times; // Caldari : Nitrogen isotopes
          if (signal == 'warning') {
            if (times >= 10) times = 2;
          }
          if (times < 2) {
            prgr.addClass('progress-bar-danger');
            prgr.removeClass('progress-bar-success');
            prgr.removeClass('progress-bar-warning');
          }
          else if (times >= 10) {
            prgr.addClass('progress-bar-success');
            prgr.removeClass('progress-bar-danger');
            prgr.removeClass('progress-bar-warning');
          }
          else {
            prgr.addClass('progress-bar-warning');
            prgr.removeClass('progress-bar-danger');
            prgr.removeClass('progress-bar-success');
          }
        }
      }
    }
  }
  // Jump Options storage (rebuild body components)
  function rebuildBody() {
    var ship = ls.getItem('Ship');
    //TODO:var calibration_skill = parseInt(ls.getItem('Jump Drive Calibration'));
    var conservation_skill = parseInt(ls.getItem('Jump Drive Conservation'));
    var freighter_skill = parseInt(ls.getItem('Jump Freighter'));
    $('table.qind-tbl-cynonet').each(function() {
      var table = $(this);
      var tbody = table.find('tbody');
      var not_enough_summary = [0,0,0,0];
      var not_enough_cn_num = null;
      tbody.find('tr.active td').each(function() {
        ly = $(this).attr('lightyears');
        if (ly) {
          ly = parseFloat(ly);
          var nitrogen_used = calcIsotope(ly, 10000, conservation_skill, freighter_skill);
          var hydrogen_used = calcIsotope(ly, 8200, conservation_skill, freighter_skill);
          var oxygen_used = calcIsotope(ly, 9400, conservation_skill, freighter_skill);
          var helium_used = calcIsotope(ly, 8800, conservation_skill, freighter_skill);
          not_enough_cn_num = cn_num = $(this).attr('cynonet');
          rt_num = $(this).attr('route');
          times = null
          contents = null
          for (var rt of contentsCynoNetwork[cn_num-1][1]) {
            if (rt[0] == rt_num) {
              contents = [rt[4],rt[5],rt[6],rt[7]]
              times = [parseInt(rt[4]/nitrogen_used), parseInt(rt[5]/hydrogen_used),
                       parseInt(rt[6]/oxygen_used), parseInt(rt[7]/helium_used)];
              break;
            }
          }
          $(this).html('Isotopes needed: <span class="nitrogen"><strong>' + nitrogen_used + '</strong> Ni</span> ' +
                        '<span class="hydrogen"><strong>' + hydrogen_used + '</strong> Hy</span> ' +
                        '<span class="oxygen"><strong>' + oxygen_used + '</strong> Ox</span> ' +
                        '<span class="helium"><strong>' + helium_used + '</strong> He</span>');
          if (times && contents) {
            if (contents[0]) {
              $('#niCynoRoute'+cn_num+'_'+rt_num).html('<abbr title="'+times[0]+' Rhea jumps">'+numLikeEve(contents[0])+'</abbr>');
              var not_enough = (contents[0] >= (nitrogen_used * 11)) ? 0 : ((nitrogen_used * 11) - contents[0]);
              $('#rowNotEnough'+cn_num+'_'+rt_num).find('td').eq(5).html(numLikeEve(not_enough));
              not_enough_summary[0] += not_enough;
            }
            else {
              $('#rowNotEnough'+cn_num+'_'+rt_num).find('td').eq(5).html(numLikeEve(nitrogen_used * 11));
              not_enough_summary[0] += nitrogen_used * 11;
            }
            if (contents[1]) {
              $('#hyCynoRoute'+cn_num+'_'+rt_num).html('<abbr title="'+times[1]+' Nomad jumps">'+numLikeEve(contents[1])+'</abbr>');
              var not_enough = (contents[1] >= (hydrogen_used * 11)) ? 0 : ((hydrogen_used * 11) - contents[1]);
              $('#rowNotEnough'+cn_num+'_'+rt_num).find('td').eq(6).html(numLikeEve(not_enough));
              not_enough_summary[1] += not_enough;
            }
            else {
              $('#rowNotEnough'+cn_num+'_'+rt_num).find('td').eq(6).html(numLikeEve(hydrogen_used * 11));
              not_enough_summary[1] += hydrogen_used * 11;
            }
            if (contents[2]) {
              $('#oxCynoRoute'+cn_num+'_'+rt_num).html('<abbr title="'+times[2]+' Anshar jumps">'+numLikeEve(contents[2])+'</abbr>');
              var not_enough = (contents[2] >= (oxygen_used * 11)) ? 0 : ((oxygen_used * 11) - contents[2]);
              $('#rowNotEnough'+cn_num+'_'+rt_num).find('td').eq(7).html(numLikeEve(not_enough));
              not_enough_summary[2] += not_enough;
            }
            else {
              $('#rowNotEnough'+cn_num+'_'+rt_num).find('td').eq(7).html(numLikeEve(oxygen_used * 11));
              not_enough_summary[2] += hydrogen_used * 11;
            }
            if (contents[3]) {
              $('#heCynoRoute'+cn_num+'_'+rt_num).html('<abbr title="'+times[3]+' Ark jumps">'+numLikeEve(contents[3])+'</abbr>');
              var not_enough = (contents[3] >= (helium_used * 11)) ? 0 : ((helium_used * 11) - contents[3]);
              $('#rowNotEnough'+cn_num+'_'+rt_num).find('td').eq(8).html(numLikeEve(not_enough));
              not_enough_summary[3] += not_enough;
            }
            else {
              $('#rowNotEnough'+cn_num+'_'+rt_num).find('td').eq(8).html(numLikeEve(helium_used * 11));
              not_enough_summary[3] += helium_used * 11;
            }
          }
        }
      });
      var tr_summary = $('#rowNotEnoughSummary'+not_enough_cn_num.toString());
      for (var i = 0; i < 4; ++i)
        tr_summary.find('td').eq(5+i).html(numLikeEve(not_enough_summary[i]));
    });
    if (!ship) { // show all
      for (var t of usedIsotopeTags) {
        $(t+'.nitrogen').removeClass('hidden');
        $(t+'.hydrogen').removeClass('hidden');
        $(t+'.oxygen').removeClass('hidden');
        $(t+'.helium').removeClass('hidden');
      }
    }
    else if (ship == 'Anshar') { // Gallente : Oxygen isotopes
      for (var t of usedIsotopeTags) {
        $(t+'.nitrogen').addClass('hidden');
        $(t+'.hydrogen').addClass('hidden');
        $(t+'.oxygen').removeClass('hidden');
        $(t+'.helium').addClass('hidden');
      }
    }
    else if (ship == 'Ark') { // Amarr : Helium isotopes
      for (var t of usedIsotopeTags) {
        $(t+'.nitrogen').addClass('hidden');
        $(t+'.hydrogen').addClass('hidden');
        $(t+'.oxygen').addClass('hidden');
        $(t+'.helium').removeClass('hidden');
      }
    }
    else if (ship == 'Nomad') { // Minmatar : Hydrogen isotopes
      for (var t of usedIsotopeTags) {
        $(t+'.nitrogen').addClass('hidden');
        $(t+'.hydrogen').removeClass('hidden');
        $(t+'.oxygen').addClass('hidden');
        $(t+'.helium').addClass('hidden');
      }
    }
    else if (ship == 'Rhea') { // Caldari : Nitrogen isotopes
      for (var t of usedIsotopeTags) {
        $(t+'.nitrogen').removeClass('hidden');
        $(t+'.hydrogen').addClass('hidden');
        $(t+'.oxygen').addClass('hidden');
        $(t+'.helium').addClass('hidden');
      }
    }
    var cynonet = ls.getItem('CynoNetNum');
    $('div.pn-cyno-net').each(function() {
      cn = $(this).attr('cynonet');
      if ((cynonet == 0) || (cynonet == cn.toString()))
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
  }

  // Jump Options menu and submenu setup
  $(document).ready(function(){
    $('.dropdown-submenu a.options-submenu').on("click", function(e){
      $(this).next('ul').toggle();
      e.stopPropagation();
      e.preventDefault();
    });
    $('a#btnCynoNetSel').on('click', function() {
      cynonet = $(this).attr('cynonet');
      ls.setItem('CynoNetNum', cynonet);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('a#btnJumpShip').on('click', function() {
      ship = $(this).attr('ship');
      ls.setItem('Ship', ship);
      rebuildOptionsMenu();
      rebuildPanelLinks();
      rebuildProgressBarSignals();
      rebuildBody();
    });
    $('#btnJumpAnyShip').on('click', function() {
      ls.removeItem('Ship');
      rebuildOptionsMenu();
      rebuildPanelLinks();
      rebuildProgressBarSignals();
      rebuildBody();
    });
    $('a#btnJumpCalibration').on('click', function() {
      skill = $(this).attr('skill');
      ls.setItem('Jump Drive Calibration', skill);
      rebuildOptionsMenu();
      rebuildPanelLinks();
      rebuildProgressBarSignals();
      rebuildBody();
    });
    $('a#btnJumpConservation').on('click', function() {
      skill = $(this).attr('skill');
      ls.setItem('Jump Drive Conservation', skill);
      rebuildOptionsMenu();
      rebuildPanelLinks();
      rebuildProgressBarSignals();
      rebuildBody();
    });
    $('a#btnJumpFreighter').on('click', function() {
      skill = $(this).attr('skill');
      ls.setItem('Jump Freighter', skill);
      rebuildOptionsMenu();
      rebuildPanelLinks();
      rebuildProgressBarSignals();
      rebuildBody();
    });
    $('#btnResetOptions').on('click', function () {
      ls.clear();
      resetOptionsMenuToDefault();
      rebuildOptionsMenu();
      rebuildPanelLinks();
      rebuildProgressBarSignals();
      rebuildBody();
    });
    // first init
    resetOptionsMenuToDefault();
    rebuildOptionsMenu();
    rebuildPanelLinks();
    rebuildProgressBarSignals();
    rebuildBody();
  });
</script>""")


def dump_cynonetwork_into_report(ws_dir, sde_inv_positions, corp_cynonetwork):
    glf = open('{dir}/cynonetwork.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        __dump_header(glf, "Cyno Network")
        __dump_corp_cynonetwork(glf, sde_inv_positions, corp_cynonetwork)
        __dump_footer(glf)
    finally:
        glf.close()


def __dump_market_groups_tree_nested(
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
            sub_glf = sub_glf + __dump_market_groups_tree_nested(
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
            img='<img class="media-object icn32" src="{src}">'.format(src=__get_icon_src(icon_id, sde_icon_ids)),
            nm=sde_group["nameID"]["en"],
            tbl=tbl_glf,
            sub=sub_glf
          )
    return glf


def __dump_market_groups_tree(glf, sde_market_groups, sde_icon_ids, market_groups_tree, market_data, market_data_printer):
    glf.write("""<ul class="media-list">
 <li class="media">""")

    if "roots" in market_groups_tree:
        roots = market_groups_tree["roots"]
        for group_id in roots:
            glf.write(
                __dump_market_groups_tree_nested(
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
        ws_dir,
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
        res = """<table class="table" style="width: unset; max-width: unset; margin-bottom: 0px;">
<thead>
 <tr>
 <th style="width:30px;">#</th>
 <th style="width:300px;">Blueprint</th>
 <th style="width:125px;">Base Price</th>
 <th style="width:85px;">Material Efficiency</th>
 <th style="width:85px;">Time Efficiency</th>
 <th style="width:75px;">Quantity</th>
 </tr>
</thead>
<tbody>
"""  # width: 700px
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
                            prc='{:,.1f}'.format(item["price"]) if "price" in item else "",
                            me=item["me"],
                            te=item["te"],
                            q=item["quantity"]
                        )
            num = num + 1
        res = res + """</tbody>
</table>"""
        return res

    glf = open('{dir}/bpos.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        __dump_header(glf, "BPOs")
        glf.write("<div class='container-fluid'>\n")
        __dump_market_groups_tree(glf, sde_market_groups, sde_icon_ids, market_groups_tree, market_data, blueprints_printer)
        glf.write("</div>\n")
        __dump_footer(glf)
    finally:
        glf.close()


def __dump_conveyor_stock_all(
        glf,
        corp_industry_jobs_data,
        corp_ass_loc_data,
        materials_for_bps,
        research_materials_for_bps,
        sde_type_ids,
        sde_market_groups,
        stock_all_loc_ids,
        stock_not_enough_materials):
    if stock_all_loc_ids is None:
        return
    # формирование списка ресурсов, которые используются в производстве
    stock_resources = {}
    loc_flags = corp_ass_loc_data.keys()
    for loc_flag in loc_flags:
        __a1 = corp_ass_loc_data[loc_flag]
        for loc_id in __a1:
            if not (int(loc_id) in stock_all_loc_ids):
                continue
            __a2 = __a1[str(loc_id)]
            __a2_keys = __a2.keys()
            for __a3 in __a2_keys:
                __type_id = int(__a3)
                __quantity = __a2[__type_id]
                # определяем группу, которой принадлежат материалы
                __market_group = get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, __type_id)
                if str(__market_group) in stock_resources:
                    __stock_group = stock_resources[str(__market_group)]
                else:
                    __group_name = sde_market_groups[str(__market_group)]["nameID"]["en"] if str(__market_group) in sde_market_groups else None  # устарел sde?
                    if not (__group_name is None):
                        __stock_group = {"name": __group_name, "items": []}
                        stock_resources.update({str(__market_group): __stock_group})
                    else:
                        __stock_group = {"name": "Unknown", "items": []}
                        stock_resources.update({"0": __stock_group})
                # пополняем список материалов в группе
                __resource_dict = next((r for r in __stock_group["items"] if r['id'] == __type_id), None)
                if __resource_dict is None:
                    __name = sde_type_ids[str(__type_id)]["name"]["en"] if str(__type_id) in sde_type_ids else str(__type_id)
                    __resource_dict = {"id": __type_id,
                                       "name": __name,
                                       "q": __quantity}
                    __stock_group["items"].append(__resource_dict)
                else:
                    __resource_dict["q"] += __quantity
    # пополняем список ресурсом записями с недостающим (отсутствующим количеством)
    for ne in stock_not_enough_materials:
        __type_id = ne["id"]
        # определяем группу, которой принадлежат материалы
        __market_group = get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, __type_id)
        if str(__market_group) in stock_resources:
            __stock_group = stock_resources[str(__market_group)]
        else:
            __stock_group = {"name": sde_market_groups[str(__market_group)]["nameID"]["en"], "items": []}
            stock_resources.update({str(__market_group): __stock_group})
        __resource_dict = next((r for r in __stock_group["items"] if r['id'] == __type_id), None)
        # пополняем список материалов в группе
        if __resource_dict is None:
            __name = sde_type_ids[str(__type_id)]["name"]["en"] if str(__type_id) in sde_type_ids else str(__type_id)
            __resource_dict = {"id": __type_id,
                               "name": __name,
                               "q": 0}
            __stock_group["items"].append(__resource_dict)

    # сортируем материалы по названию
    stock_keys = stock_resources.keys()
    for stock_key in stock_keys:
        stock_resources[str(stock_key)]["items"].sort(key=lambda r: r["name"])

    glf.write("""
<style>
#tblStockAll tr {
  font-size: small;
}
</style>

<div class="table-responsive">
 <table id="tblStockAll" class="table table-condensed table-hover">
<thead>
 <tr>
  <th>#</th>
  <th>Item</th>
  <th>In stock</th>
  <th>Not available</th>
  <th>In progress</th>
 </tr>
</thead>
<tbody>""")

    row_num = 1
    stock_keys = stock_resources.keys()
    for stock_key in stock_keys:
        __group_dict = stock_resources[str(stock_key)]
        glf.write(
            '<tr>\n'
            ' <td class="active" colspan="5"><strong>{nm}</strong></td>\n'
            '</tr>'.
            format(nm=__group_dict["name"]))
        for __resource_dict in __group_dict["items"]:
            __type_id = __resource_dict["id"]
            __quantity = __resource_dict["q"]
            # получаем статистику по текущим работам, считаем сколько производится этих материалов?
            jobs = [j for j in corp_industry_jobs_data if
                    (j["product_type_id"] == __type_id) and
                    (j['output_location_id'] in stock_all_loc_ids)]
            in_progress = 0
            for j in jobs:
                in_progress = in_progress + j["runs"]
            # получаем статистику по недостающим материалам
            not_enough = next((ne for ne in stock_not_enough_materials if ne['id'] == __type_id), None)
            # проверяем списки метариалов, используемых в исследованиях и производстве
            material_tag = ""
            if __type_id in materials_for_bps:
                pass
            elif __type_id in research_materials_for_bps:
                material_tag = ' <span class="label label-warning">research material</span></small>'
            else:
                material_tag = ' <span class="label label-danger">non material</span></small>'
            # формируем строку таблицы - найден нужный чертёж в ассетах
            glf.write(
                '<tr>'
                '<th scope="row">{num}</th>'
                '<td>{nm}{mat_tag}</td>'
                '<td align="right">{q}</td>'
                '<td align="right">{ne}</td>'
                '<td align="right">{ip}</td>'
                '</tr>\n'.
                format(num=row_num,
                       nm=__resource_dict["name"],
                       mat_tag=material_tag,
                       q="" if __quantity == 0 else '{:,d}'.format(__quantity),
                       ne="" if not_enough is None else '{:,d}'.format(not_enough["q"]),
                       ip="" if in_progress == 0 else '{:,d}'.format(in_progress))
            )
            row_num = row_num + 1

    glf.write("""
</tbody>     
 </table>     
</div>     
""")


def __dump_corp_conveyor(
        glf,
        conveyour_entities,
        corp_bp_loc_data,
        corp_industry_jobs_data,
        corp_ass_names_data,
        corp_ass_loc_data,
        corp_assets_tree,
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        sde_icon_ids,
        materials_for_bps,
        research_materials_for_bps):
    glf.write("""
<nav class="navbar navbar-default">
 <div class="container-fluid">
  <div class="navbar-header">
   <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#bs-navbar-collapse" aria-expanded="false">
    <span class="sr-only">Toggle navigation</span>
    <span class="icon-bar"></span>
    <span class="icon-bar"></span>
    <span class="icon-bar"></span>
   </button>
   <a class="navbar-brand" data-target="#"><span class="glyphicon glyphicon-tasks" aria-hidden="true"></span></a>
  </div>

  <div class="collapse navbar-collapse" id="bs-navbar-collapse">
   <ul class="nav navbar-nav">
    <li class="dropdown">
     <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Display Options <span class="caret"></span></a>
      <ul class="dropdown-menu">
       <li><a id="btnToggleActive" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowActive"></span> Show active blueprints</a></li>
       <li><a id="btnToggleMaterials" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowMaterials"></span> Show used materials</a></li>
       <li><a id="btnToggleLegend" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowLegend"></span> Show legend</a></li>
       <li role="separator" class="divider"></li>
       <li><a id="btnResetOptions" data-target="#" role="button">Reset options</a></li>
      </ul>
    </li>
    <li><a data-target="#modalStockAll" role="button" data-toggle="modal">Stock All</a></li>
   </ul>
   <form class="navbar-form navbar-right">
    <div class="form-group">
     <input type="text" class="form-control" placeholder="Item" disabled>
    </div>
    <button type="button" class="btn btn-default disabled">Search</button>
   </form>
  </div>
 </div>
</nav>
<div class="container-fluid">
 <!-- BEGIN: collapsable group (locations) -->
 <div class="panel-group" id="accordion" role="tablist" aria-multiselectable="true">
""")

    stock_not_enough_materials = None
    for __conveyor_entity in conveyour_entities:
        __stock_not_enough_materials = __dump_blueprints_list_with_materials(
            glf,
            __conveyor_entity,
            corp_bp_loc_data,
            corp_industry_jobs_data,
            corp_ass_loc_data,
            corp_assets_tree,
            sde_type_ids,
            sde_bp_materials,
            sde_market_groups,
            sde_icon_ids,
            enable_copy_to_clipboard=True)
        if stock_not_enough_materials is None:
            stock_not_enough_materials = __stock_not_enough_materials

    glf.write("""
 </div>
 <!-- END: collapsable group (locations) -->
""")

    # получение списков контейнеров и станок из экземпляра контейнера
    conveyor_entity = conveyour_entities[0]
    stock_all_loc_ids = [int(ces["id"]) for ces in conveyor_entity["stock"]]
    # создаём заголовок модального окна, где будем показывать список имеющихся материалов в контейнере "..stock ALL"
    __dump_any_into_modal_header_wo_button(
        glf,
        conveyor_entity["stock"][0]["name"],
        'StockAll')
    # формируем содержимое модального диалога
    __dump_conveyor_stock_all(
        glf,
        corp_industry_jobs_data,
        corp_ass_loc_data,
        materials_for_bps,
        research_materials_for_bps,
        sde_type_ids,
        sde_market_groups,
        stock_all_loc_ids,
        stock_not_enough_materials)
    # закрываем footer модального диалога
    __dump_any_into_modal_footer(glf)

    glf.write("""
<div id="legend-block">
 <hr>
 <h4>Legend</h4>
 <p>
  <span class="label label-default">copy</span>&nbsp;<span class="label label-success">2 4</span>&nbsp;<span
   class="badge">150</span> - blueprints <strong>copies</strong> with <strong>2</strong> material efficiency and
   <strong>4</strong> time efficiency with total of <strong>150</strong> runs.
 </p>
 <p>
  <span class="label label-info">original</span>&nbsp;<span class="label label-success">10 20</span>&nbsp;<span
   class="badge">2</span>&nbsp;<span class="label label-primary">active</span> - <strong>two</strong>
   <strong>original</strong> blueprints with <strong>10</strong> material efficiency and <strong>20</strong> time efficiency,
   production is currently <strong>active</strong>.
 </p>
""")
    glf.write('<p>'
              '<span style="white-space:nowrap"><img class="icn24" src="{src}"> 30 x Ice Harvester I </span>'
              '&nbsp;<span class="label label-warning"><img class="icn24" src="{src}"> 6 x Ice Harvester I </span>&nbsp;-'
              '&nbsp;<strong>30</strong> items used in the production, the items are missing <strong>6</strong>.'
              '</p>'
              '<p>'
              '<span style="white-space:nowrap"><img class="icn24" src="{src}"> 30 x Ice Harvester I </span>'
              '&nbsp;<span class="label label-danger"><img class="icn24" src="{src}"> 29 x Ice Harvester I </span>&nbsp;-'
              '&nbsp;missing number of items, such that it is not enough to run at least one blueprint copy.'
              '<p>'.
              format(src=__get_img_src(16278, 32)))
    glf.write("""
 <p>
  <span class="label label-info">original</span>, <span class="label label-default">copy</span>,
  <span class="label label-danger">no blueprints</span> - possible labels that reflect the presence of vacant blueprints
  in the hangars of the station (<i>Not available materials</i> section).
 </p>
</div>
</div>
<script>
  // Conveyor Options storage (prepare)
  ls = window.localStorage;

  // Conveyor Options storage (init)
  function resetOptionsMenuToDefault() {
    if (!ls.getItem('Show Legend')) {
      ls.setItem('Show Legend', 1);
    }
    if (!ls.getItem('Show Active')) {
      ls.setItem('Show Active', 1);
    }
    if (!ls.getItem('Show Materials')) {
      ls.setItem('Show Materials', 1);
    }
  }
  // Conveyor Options storage (rebuild menu components)
  function rebuildOptionsMenu() {
    show = ls.getItem('Show Legend');
    if (show == 1)
      $('#imgShowLegend').removeClass('hidden');
    else
      $('#imgShowLegend').addClass('hidden');
    show = ls.getItem('Show Active');
    if (show == 1)
      $('#imgShowActive').removeClass('hidden');
    else
      $('#imgShowActive').addClass('hidden');
    show = ls.getItem('Show Materials');
    if (show == 1)
      $('#imgShowMaterials').removeClass('hidden');
    else
      $('#imgShowMaterials').addClass('hidden');
  }
  // Conveyor Options storage (rebuild body components)
  function rebuildBody() {
    show = ls.getItem('Show Legend');
    if (show == 1)
      $('#legend-block').removeClass('hidden');
    else
      $('#legend-block').addClass('hidden');
    show = ls.getItem('Show Active');
    $('span.qind-blueprints-active').each(function() {
      if (show == 1)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
    show = ls.getItem('Show Materials');
    $('div.qind-materials-used').each(function() {
      if (show == 1)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
  }
  // Conveyor Options menu and submenu setup
  $(document).ready(function(){
    $('#btnToggleLegend').on('click', function () {
      show = (ls.getItem('Show Legend') == 1) ? 0 : 1;
      ls.setItem('Show Legend', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleActive').on('click', function () {
      show = (ls.getItem('Show Active') == 1) ? 0 : 1;
      ls.setItem('Show Active', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleMaterials').on('click', function () {
      show = (ls.getItem('Show Materials') == 1) ? 0 : 1;
      ls.setItem('Show Materials', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnResetOptions').on('click', function () {
      ls.clear();
      resetOptionsMenuToDefault();
      rebuildOptionsMenu();
      rebuildBody();
    });
    // first init
    resetOptionsMenuToDefault();
    rebuildOptionsMenu();
    rebuildBody();
    // Working with clipboard
    $('a.qind-copy-btn').each(function() {
      $(this).tooltip();
    })
    $('a.qind-copy-btn').bind('click', function () {
      var data_copy = $(this).attr('data-copy');
      if (data_copy === undefined) {
        var tr = $(this).parent().parent();
        var tbody = tr.parent();
        var rows = tbody.children('tr');
        var start_row = rows.index(tr);
        data_copy = '';
        rows.each( function(idx) {
          if (!(start_row === undefined) && (idx > start_row)) {
            var td = $(this).find('td').eq(0);
            if (!(td.attr('class') === undefined))
              start_row = undefined;
            else {
              if (data_copy) data_copy += "\\n"; 
              data_copy += td.find('a').attr('data-copy') + "\\t" + $(this).find('td').eq(1).attr('quantity');
            }
          }
        });
      }
      var $temp = $("<textarea>");
      $("body").append($temp);
      $temp.val(data_copy).select();
      try {
        success = document.execCommand("copy");
        if (success) {
          $(this).trigger('copied', ['Copied!']);
        }
      } finally {
        $temp.remove();
      }
    });
    $('a.qind-copy-btn').bind('copied', function(event, message) {
      $(this).attr('title', message)
        .tooltip('fixTitle')
        .tooltip('show')
        .attr('title', "Copy to clipboard")
        .tooltip('fixTitle');
    });
    if( /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ) {
      // какой-то код ...
      $('a.qind-copy-btn').each(function() {
        $(this).addClass('hidden');
      })
    }
  });
</script>
""")


__g_pattern_c2s1 = re.compile(r'(.)([A-Z][a-z]+)')
__g_pattern_c2s2 = re.compile(r'([a-z0-9])([A-Z])')


def __camel_to_snake(name):  # https://stackoverflow.com/a/1176023
  name = __g_pattern_c2s1.sub(r'\1_\2', name)
  return __g_pattern_c2s2.sub(r'\1_\2', name).lower()


def dump_conveyor_into_report(
        # путь, где будет сохранён отчёт
        ws_dir,
        # настройки генерации отчёта
        conveyour_entities,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        sde_icon_ids,
        # esi данные, загруженные с серверов CCP
        corp_industry_jobs_data,
        corp_ass_names_data,
        corp_ass_loc_data,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_bp_loc_data,
        corp_assets_tree,
        materials_for_bps,
        research_materials_for_bps):
    glf = open('{dir}/conveyor.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        __dump_header(glf, "Conveyor")
        __dump_corp_conveyor(
            glf,
            conveyour_entities,
            corp_bp_loc_data,
            corp_industry_jobs_data,
            corp_ass_names_data,
            corp_ass_loc_data,
            corp_assets_tree,
            sde_type_ids,
            sde_bp_materials,
            sde_market_groups,
            sde_icon_ids,
            materials_for_bps,
            research_materials_for_bps)
        __dump_footer(glf)
    finally:
        glf.close()


def __dump_corp_accounting_nested_tbl(
        glf,
        loc_id,
        loc_dict,
        sde_type_ids,
        sde_icon_ids,
        filter_flags):
    h3_and_table_printed = False
    tr_divider_skipped = True
    __hangar_colors = ["", "fbfbfe", "f0f5f3", "f8fcf4", "fffdeb", "fff4f5", "f0f1f9", "f8f6f5", "fcfdfd"]
    if "items" in loc_dict:
        __itms_keys = loc_dict["items"].keys()
        for __loc_id in __itms_keys:
            itm_dict = loc_dict["items"][str(__loc_id)]
            # отбрасываем элементы не по фильтру (например нет списка "delivery")
            __filter_found = filter_flags is None
            if not __filter_found:
                for __filter in filter_flags:
                    if __filter in itm_dict["flags"]:
                        __filter_found = True
                        break
            if not __filter_found:
                continue
            # пишем заголовок таблицы (название системы)
            if not h3_and_table_printed:
                h3_and_table_printed = True
                __loc_name = loc_dict["loc_name"]
                if __loc_name is None:
                    __loc_name = loc_id
                glf.write(
                    '<h3>{where}</strong><!--{id}--></h3>\n'.
                    format(where='{} '.format(__loc_name) if not (__loc_name is None) else "",
                           id=loc_id))
                glf.write("""
<div class="table-responsive">
  <table class="table table-condensed">
<thead>
 <tr>
  <th style="width:32px;">#</th>
  <th style="width:32px;"></th>
  <th>Items</th>
  <th style="text-align: right;">Cost, ISK</th>
  <th style="text-align: right;">Volume, m&sup3;</th>
 </tr>
</thead>
<tbody>
""")
            # получаем данные по текущему справочнику
            loc_name = itm_dict["loc_name"]
            foreign = itm_dict["foreign"]
            forbidden = itm_dict["forbidden"] if "forbidden" in itm_dict else False
            type_id = itm_dict["type_id"]
            if loc_name is None:
                loc_name = loc_id
            # добавляем пустую строку для разграничения групп товаров между станциями
            if not tr_divider_skipped:
                glf.write('<tr><td colspan="5"></td></tr>')
            tr_divider_skipped = False
            # добавляем название станции
            __station_type_name = get_item_name_by_type_id(sde_type_ids, type_id) if not (type_id is None) else ""
            glf.write(
                '<tr><td colspan="5">'
                '<div class="media">'
                ' <div class="media-left">{img}</div>'
                ' <div class="media-body"><strong>{where}</strong>{what}{foreign}{forbidden}<!--{id}--></div>'
                '</div>'
                '</td></tr>\n'.
                format(where='{} '.format(loc_name) if not (loc_name is None) else "",
                       id=__loc_id,
                       foreign='&nbsp;<small><span class="label label-warning">foreign</span></small>' if foreign else "",
                       forbidden='&nbsp;<small><span class="label label-danger">forbidden</span></small>' if forbidden else "",
                       img='<img class="media-object icn32" src="{src}">'.format(src=__get_img_src(type_id, 32)) if not (type_id is None) else "",
                       what='&nbsp;<small>{}</small> '.format(__station_type_name) if __station_type_name else ""))
            row_id = 1
            __summary_cost = None
            __summary_volume = 0
            __blueprints_reactions_dict = None
            if "flags" in itm_dict:
                __f_keys = itm_dict["flags"].keys()
                for hangar_type_flags in range(2):
                    for __flag in __f_keys:  # "CorpDeliveries"
                        # в начало таблицы размещаем офисы на станке с ангарами, так что в конце таблиц размещено всё остальное (без ангаров)
                        if (hangar_type_flags == 0) and (__flag != "OfficeFolder"):
                            continue
                        elif (hangar_type_flags == 1) and (__flag == "OfficeFolder"):
                            continue
                        # отбрасываем элементы не по фильтру (например нет списка "delivery")
                        __filter_found = filter_flags is None
                        if not __filter_found and (0 != filter_flags.count(__flag)):
                            __filter_found = True
                        if not __filter_found:
                            continue
                        # получаем список групп товаров, хранящихся в указанном __flag
                        __flag_dict = itm_dict["flags"][str(__flag)]
                        if str(__flag) == "BlueprintsReactions":
                            __blueprints_reactions_dict = __flag_dict
                            continue
                        # сортируем группы товаров на названию групп
                        __flag_dict_sorted = []
                        __g_h_keys = __flag_dict.keys()
                        for __group_hangar_key in __g_h_keys:
                            __group_dict = __flag_dict[str(__group_hangar_key)]
                            __hangar = 0 if __group_dict["hangar_num"] is None else int(__group_dict["hangar_num"])
                            __flag_dict_sorted.append({"key": __group_hangar_key, "nm": '{}_{}'.format(__hangar, __group_dict["group"]), "hg": __hangar})
                        __flag_dict_sorted.sort(key=lambda s: s["nm"])
                        # подсчёт кол-ва групп товаров, лежащих в ангарах (необходимо для вывода hangar' summary)
                        __hangar_num_qty = [0, 0, 0, 0, 0, 0, 0, 0, 0]
                        for __group_dict_sorted in __flag_dict_sorted:
                            __hangar_num_qty[int(__group_dict_sorted["hg"])] += 1
                        # подготавливаем к выводу номера ангаров (если присутствуют)
                        __prev_hangar_num = None
                        __summary_hangar_groups = None
                        __summary_hangar_cost = None
                        __summary_hangar_volume = None
                        # выводим информацию по содержимому location (группы товаров)
                        for __group_dict_sorted in __flag_dict_sorted:
                            __group_hangar_key = __group_dict_sorted["key"]
                            __group_dict = __flag_dict[str(__group_hangar_key)]
                            __hangar_num = __group_dict["hangar_num"]  # м.б. None, в то время как __group_dict_sorted["hg"] м.б. 0
                            # вывод номера ангара
                            if (__prev_hangar_num is None) and not (__hangar_num is None) or (__prev_hangar_num != __hangar_num):
                                __prev_hangar_num = __hangar_num
                                __summary_hangar_groups = __hangar_num_qty[int(__hangar_num)]
                                __summary_hangar_cost = 0
                                __summary_hangar_volume = 0
                                glf.write('<tr style="font-weight:bold;background-color:#{hngr_clr}">'
                                          ' <td colspan="5">Hangar {hangar}</td>'
                                          '</tr>\n'.
                                          format(hangar=__hangar_num,
                                                 hngr_clr=__hangar_colors[__hangar_num]))
                            # создание искусственной вложенности (ангары и прочие категории)
                            if not (__hangar_num is None):
                                glf.write('<tr{hngr_clr}>'
                                          ' <td></td>'
                                          ' <th scope="row">{num}</th>'
                                          ' <td>'.
                                          format(hngr_clr=' style="background-color:#{}"'.format(__hangar_colors[__hangar_num]) if not (__hangar_num is None) else "",
                                                 num=row_id))
                            else:
                                glf.write('<tr>'
                                          ' <th scope="row">{num}</th>\n'
                                          ' <td colspan="2">'.
                                          format(num=row_id))
                            # вывод названий товаров, стоимость и объём (строка таблицы)
                            glf.write(' {icn}{nm}{tag}</td>'
                                      ' <td align="right">{cost:,.1f}</td>'
                                      ' <td align="right">{volume:,.1f}</td>'
                                      '</tr>'.
                                      format(nm=__group_dict["group"],
                                             icn='<img class="icn16" src="{}" style="display:inline;">&nbsp;'.
                                                 format(__get_icon_src(__group_dict["icon"], sde_icon_ids))
                                                 if not (__group_dict["icon"] is None) else "",
                                             cost=__group_dict["cost"],
                                             volume=__group_dict["volume"],
                                             tag='' if not (filter_flags is None) and (len(filter_flags) == 1) else
                                                 ' <small><span class="label label-default">{flag}</span></small>'.
                                                 format(flag=__camel_to_snake(str(__flag))
                                            )))
                            row_id = row_id + 1
                            __summary_cost = __group_dict["cost"] if __summary_cost is None else __summary_cost + __group_dict["cost"]
                            __summary_volume += __group_dict["volume"]
                            # вывод summary-информации по ангару
                            if not (__summary_hangar_cost is None):
                                __summary_hangar_cost += __group_dict["cost"]
                                __summary_hangar_volume += __group_dict["volume"]
                            if not (__summary_hangar_groups is None):
                                __summary_hangar_groups -= 1
                                if __summary_hangar_groups == 0:
                                    glf.write('<tr style="font-weight:bold;background-color:#{hngr_clr}">'
                                              ' <td></td>'
                                              ' <td colspan="2">Summary&nbsp;(<small>Hangar {hangar}</small>)</td>'
                                              ' <td align="right">{cost:,.1f}</td>'
                                              ' <td align="right">{volume:,.1f}</td>'
                                              '</tr>\n'.
                                              format(hangar=__hangar_num,
                                                     hngr_clr=__hangar_colors[__hangar_num],
                                                     cost=__summary_hangar_cost,
                                                     volume=__summary_hangar_volume))
            # вывод summary-информации в конце каждой таблицы
            if not (__summary_cost is None):
                # не копируется в модальном окне:__copy2clpbrd = '&nbsp;<a data-target="#" role="button" data-copy="{cost:.1f}" class="qind-copy-btn"' \
                # не копируется в модальном окне:                '  data-toggle="tooltip"><span class="glyphicon glyphicon-copy"' \
                # не копируется в модальном окне:                '  aria-hidden="true"></span></a>'. \
                # не копируется в модальном окне:                format(cost=__summary_cost)
                glf.write('<tr style="font-weight:bold;">'
                          ' <td colspan="3">Summary{what}</td>'
                          ' <td align="right">{cost:,.1f}</td>'
                          ' <td align="right">{volume:,.1f}</td>'
                          '</tr>'.
                          format(cost=__summary_cost,
                                 volume=__summary_volume,
                                 what='&nbsp;(<small>{}</small>)'.format(__station_type_name) if __station_type_name else ""))
            # вывод пропущенных ранее 'Blueprints & Reactions' (в конце каждой таблицы, под summary)
            if not (__blueprints_reactions_dict is None):
                __flag = "BlueprintsReactions"
                __g_keys = __blueprints_reactions_dict.keys()
                # выводим информацию по содержимому location (группы товаров)
                for __group_id in __g_keys:
                    __group_dict = __blueprints_reactions_dict[str(__group_id)]
                    glf.write('<tr style="color:green;">'
                              ' <td colspan="3">{icn}{nm}{tag}</td>'
                              ' <td align="right">{cost:,.1f}</td>'
                              ' <td align="right">{volume:,.1f}</td>'
                              '</tr>'.
                              format(nm=__group_dict["group"],
                                     icn='<img class="icn16" src="{}" style="display:inline;">&nbsp;'.
                                         format(__get_icon_src(__group_dict["icon"], sde_icon_ids))
                                         if not (__group_dict["icon"] is None) else "",
                                     cost=__group_dict["cost"],
                                     volume=__group_dict["volume"],
                                     tag='' if not (filter_flags is None) and (len(filter_flags) == 1) else
                                         ' <small><span class="label label-default">{flag}</span></small>'.
                                         format(flag=__camel_to_snake(str(__flag)))))
    if h3_and_table_printed:
        glf.write("""
</tbody>
 </table>
</div>
""")


def __dump_corp_accounting_details(
        glf,
        __key,
        corporation_name,
        corporation_id,
        __corp_tree,
        sde_type_ids,
        sde_icon_ids):
    __dump_any_into_modal_header(
        glf,
        '<span class="text-primary">{nm}</span> {key}'.format(nm=corporation_name,
                                                              key="" if __key is None else __key),
        '{nm}_{key}'.format(nm=corporation_id,
                            key="all" if __key is None else __key),
        "btn-xs",
        "details&hellip;",
        "modal-lg")
    __roots = __corp_tree.keys()
    __filter = None if __key is None else [__key]
    for root in __roots:
        __dump_corp_accounting_nested(
            glf,
            root,
            __corp_tree[str(root)],
            sde_type_ids,
            sde_icon_ids,
            __filter)  # ["CorpDeliveries"]
    __dump_any_into_modal_footer(glf)


def __dump_corp_accounting_nested(
        glf,
        root_id,
        root,
        sde_type_ids,
        sde_icon_ids,
        filter_flags):
    if "region" in root:
        __filter_found = filter_flags is None
        if not __filter_found:
            for __filter in filter_flags:
                if ("flags" in root) and (root["flags"].count(__filter) > 0):
                    __filter_found = True
                    break
        if not __filter_found:
            return
        glf.write('<h2>{rgn}<!--{id}--></h2>\n'.format(rgn=root["region"], id=root_id))
        __sys_keys = root["systems"].keys()
        for loc_id in __sys_keys:
            system = root["systems"][str(loc_id)]
            __dump_corp_accounting_nested_tbl(glf, loc_id, system, sde_type_ids, sde_icon_ids, filter_flags)
    else:
        glf.write('<h2>???</h2>\n')
        __dump_corp_accounting_nested_tbl(glf, root_id, root, sde_type_ids, sde_icon_ids, filter_flags)


def __dump_corp_accounting(
        glf,
        sde_type_ids,
        sde_icon_ids,
        corps_accounting):
    glf.write("""
    <nav class="navbar navbar-default">
     <div class="container-fluid">
      <div class="navbar-header">
       <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#bs-navbar-collapse" aria-expanded="false">
        <span class="sr-only">Toggle navigation</span>
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
       </button>
       <a class="navbar-brand" data-target="#"><span class="glyphicon glyphicon-list-alt" aria-hidden="true"></span></a>
      </div>

      <div class="collapse navbar-collapse" id="bs-navbar-collapse">
       <ul class="nav navbar-nav">
        <li class="dropdown">
         <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Display Options <span class="caret"></span></a>
          <ul class="dropdown-menu">
           <li><a id="btnToggleBlueprints" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowBlueprints"></span> Show blueprints and reactions</a></li>
           <li><a id="btnToggleLegend" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowLegend"></span> Show legend</a></li>
           <li role="separator" class="divider"></li>
           <li><a id="btnResetOptions" data-target="#" role="button">Reset options</a></li>
          </ul>
        </li>

        <li class="disabled"><a data-target="#" role="button">Problems</a></li>
       </ul>
       <form class="navbar-form navbar-right">
        <div class="form-group">
         <input type="text" class="form-control" placeholder="Item" disabled>
        </div>
        <button type="button" class="btn btn-default disabled">Search</button>
       </form>
      </div>
     </div>
    </nav>
    <div class="container-fluid">
    """)
    glf.write("""
<div class="table-responsive">
  <table class="table table-condensed table-hover">
<thead>
 <tr>
  <th style="width:40px;">#</th>
  <th>Locations</th>
  <th style="text-align: right;">Cost, ISK</th>
  <th style="text-align: right;">Volume, m&sup3;</th>
  <th style="text-align: center;">Details</th>
 </tr>
</thead>
<tbody>
""")

    __corp_keys = corps_accounting.keys()
    for corporation_id in __corp_keys:
        __corp = corps_accounting[str(corporation_id)]
        glf.write('<tr class="active">'
                  ' <td colspan="5"><span class="text-primary"><strong>{nm}</strong></span></td>'
                  '</tr>\n'.
                  format(nm=__corp["corporation"]))
        row_num = 1
        __summary_cost = 0
        __summary_volume = 0
        __stat_keys = __corp["stat"].keys()
        for __key in __stat_keys:
            __stat_dict = __corp["stat"][str(__key)]
            if ("omit_in_summary" in __stat_dict) and __stat_dict["omit_in_summary"]:
                continue
            glf.write('<tr>'
                      ' <th scope="row">{num}</th>\n'
                      ' <td>{nm}</td>'
                      ' <td align="right">{cost:,.1f}</td>'
                      ' <td align="right">{volume:,.1f}</td>'
                      ' <td align="center">'.
                      format(num=row_num,
                             nm=__key,  # "CorpDeliveries"
                             cost=__stat_dict["cost"],
                             volume=__stat_dict["volume"]))
            # подсчёт общей статистики
            __summary_cost = __summary_cost + __stat_dict["cost"]
            __summary_volume = __summary_volume + __stat_dict["volume"]
            # добавление details на страницу
            __dump_corp_accounting_details(
                glf,
                __key,
                __corp["corporation"],
                corporation_id,
                __corp["tree"],
                sde_type_ids,
                sde_icon_ids)
            glf.write('</td>'
                      '</tr>\n')
            row_num = row_num + 1
        __copy2clpbrd = '&nbsp;<a data-target="#" role="button" data-copy="{cost:.1f}" class="qind-copy-btn"' \
                        '  data-toggle="tooltip"><span class="glyphicon glyphicon-copy"' \
                        '  aria-hidden="true"></span></a>'. \
                        format(cost=__summary_cost)
        glf.write('<tr>'
                  ' <th></th>\n'
                  ' <td><strong>Summary</strong></td>\n'
                  ' <td align="right"><strong>{cost:,.1f}{clbrd}</strong></td>'
                  ' <td align="right"><strong>{volume:,.1f}</strong></td>'
                  ' <td align="center">'.
                  format(cost=__summary_cost,
                         volume=__summary_volume,
                         clbrd=__copy2clpbrd))
        # добавление details в summary
        __dump_corp_accounting_details(
            glf,
            None,
            __corp["corporation"],
            corporation_id,
            __corp["tree"],
            sde_type_ids,
            sde_icon_ids)
        glf.write('</td>'
                  '</tr>\n')
        # добавление в подвал (под summary) информацию об omitted-категориях (такая у нас Blueprints & Reactions)
        # повторно запускаем цикл
        for __key in __stat_keys:
            __stat_dict = __corp["stat"][str(__key)]
            if not ("omit_in_summary" in __stat_dict) or not __stat_dict["omit_in_summary"]:
                continue
            glf.write('<tr class="qind-blueprints-stat">'
                      ' <th></th>\n'
                      ' <td style="color:green;">{nm}</td>'
                      ' <td style="color:green;" align="right">{cost:,.1f}</td>'
                      ' <td style="color:green;" align="right">{volume:,.1f}</td>'
                      ' <td align="center">'.
                      format(nm=__key,  # "BlueprintsReactions"
                             cost=__stat_dict["cost"],
                             volume=__stat_dict["volume"]))
            # добавление details на страницу
            __dump_corp_accounting_details(
                glf,
                __key,
                __corp["corporation"],
                corporation_id,
                __corp["tree"],
                sde_type_ids,
                sde_icon_ids)
            glf.write('</td>'
                      '</tr>\n')

    glf.write("""
</tbody>
 </table>
</div>
""")
    glf.write("""
<div id="legend-block">
 <hr>
 <h4>Legend</h4>
 <p>
  <small><span class="label label-warning">foreign</span></small> - the station or structure is owned by another corporation.
 </p>
 <p>
  <small><span class="label label-danger">forbidden</span></small> - now there is no access to the station or structure.
 </p>
 <p>
  <small><span class="label label-default">corp_deliveries</span>, <span class="label label-default">office_folder</span>,&hellip;</small> - locations of items.
 </p>
""")
    glf.write("""
</div>
<script>
  // Accounting Options storage (prepare)
  ls = window.localStorage;

  // Accounting Options storage (init)
  function resetOptionsMenuToDefault() {
    if (!ls.getItem('Show Legend')) {
      ls.setItem('Show Legend', 1);
    }
    if (!ls.getItem('Show Blueprints')) {
      ls.setItem('Show Blueprints', 1);
    }
  }
  // Accounting Options storage (rebuild menu components)
  function rebuildOptionsMenu() {
    show = ls.getItem('Show Legend');
    if (show == 1)
      $('#imgShowLegend').removeClass('hidden');
    else
      $('#imgShowLegend').addClass('hidden');
    show = ls.getItem('Show Blueprints');
    if (show == 1)
      $('#imgShowBlueprints').removeClass('hidden');
    else
      $('#imgShowBlueprints').addClass('hidden');
  }
  // Accounting Options storage (rebuild body components)
  function rebuildBody() {
    show = ls.getItem('Show Legend');
    if (show == 1)
      $('#legend-block').removeClass('hidden');
    else
      $('#legend-block').addClass('hidden');
    show = ls.getItem('Show Blueprints');
    $('tr.qind-blueprints-stat').each(function() {
      if (show == 1)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
  }
  // Accounting Options menu and submenu setup
  $(document).ready(function(){
    $('#btnToggleLegend').on('click', function () {
      show = (ls.getItem('Show Legend') == 1) ? 0 : 1;
      ls.setItem('Show Legend', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleBlueprints').on('click', function () {
      show = (ls.getItem('Show Blueprints') == 1) ? 0 : 1;
      ls.setItem('Show Blueprints', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnResetOptions').on('click', function () {
      ls.clear();
      resetOptionsMenuToDefault();
      rebuildOptionsMenu();
      rebuildBody();
    });
    // first init
    resetOptionsMenuToDefault();
    rebuildOptionsMenu();
    rebuildBody();
    // Working with clipboard
    $('a.qind-copy-btn').each(function() {
      $(this).tooltip();
    })
    $('a.qind-copy-btn').bind('click', function () {
      var $temp = $("<input>");
      $("body").append($temp);
      $temp.val($(this).attr('data-copy')).select();
      try {
        success = document.execCommand("copy");
        if (success) {
          $(this).trigger('copied', ['Copied!']);
        }
      } finally {
        $temp.remove();
      }
    });
    $('a.qind-copy-btn').bind('copied', function(event, message) {
      $(this).attr('title', message)
        .tooltip('fixTitle')
        .tooltip('show')
        .attr('title', "Copy to clipboard")
        .tooltip('fixTitle');
    });
    if( /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ) {
      // какой-то код ...
      $('a.qind-copy-btn').each(function() {
        $(this).addClass('hidden');
      })
    }
  });
</script>
""")


def dump_accounting_into_report(
        ws_dir,
        sde_type_ids,
        sde_icon_ids,
        corps_accounting):
    glf = open('{dir}/accounting.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        __dump_header(glf, "Accounting")
        __dump_corp_accounting(glf, sde_type_ids, sde_icon_ids, corps_accounting)
        __dump_footer(glf)
    finally:
        glf.close()


def __dump_corp_blueprints_sales(
        glf,
        corps_blueprints):
    __corp_keys = corps_blueprints.keys()
    # составляем список locations, где могут лежать чертежи, с тем чтобы сделать возможность группировать их по locations
    used_location_names = []
    for corporation_id in __corp_keys:
        if not (int(corporation_id) in q_blueprints_settings.g_sale_of_blueprint["corporation_id"]):
            continue
        __corp = corps_blueprints[str(corporation_id)]
        # название станций и звёздных систем
        __loc_keys = __corp["locations"].keys()
        for __loc_key in __loc_keys:
            __loc_dict = __corp["locations"][str(__loc_key)]
            if "station" in __loc_dict:
                __location_name = __loc_dict["station"]
            elif "solar" in __loc_dict:
                __location_name = __loc_dict["solar"]
            else:
                __location_name = __loc_key
            __used_name = next((n for n in used_location_names if n['name'] == __location_name), None)
            # определяем ангары, где лежат чертёжи
            for __blueprint_dict in __corp["blueprints"]:
                if __blueprint_dict["loc"] != int(__loc_key):
                    continue
                if "st" in __blueprint_dict:  # пропускаем чертежы, над которым выполяются какие-либо работы
                    continue
                if "cntrct_sta" in __blueprint_dict:  # пропускаем places из контрактов (там не ангары, а ingame комментарии)
                    continue
                __type_id = __blueprint_dict["type_id"]
                if not (__used_name is None):  # в окно sales чертежи одного типа многократно не добавляются
                    if __used_name["types"].count(__type_id) > 0:
                        continue
                __blueprint_id = __blueprint_dict["item_id"]
                __place = __blueprint_dict["flag"]
                if __place[:-1] == "CorpSAG":
                    __place = 'Hangar {}'.format(__place[-1:])  # Corp Security Access Group
                # добавляем в список обнаруженных мест, локацию с ангарами (исключая локации только с контрактами)
                if __used_name is None:
                    __used_name = {"name": __location_name, "places": [__place], "ids": [], "types": []}
                    used_location_names.append(__used_name)
                elif __used_name["places"].count(__place) == 0:
                    __used_name["places"].append(__place)
                __used_name["ids"].append(__blueprint_id)
                __used_name["types"].append(__type_id)
            if not (__used_name is None):
                __used_name["places"].sort()
    used_location_names = sorted(used_location_names, key=lambda x: x['name'])

    # формируем dropdown список, где можон будет выбрать локации и ангары
    glf.write("""
<div id="ddSales" class="dropdown">
  <button class="btn btn-default dropdown-toggle" type="button" id="ddSalesMenu" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">
    <span class="qind-lb-dd">Choose Place&hellip;</span>
    <span class="caret"></span>
  </button>
  <ul class="dropdown-menu" aria-labelledby="dropdownMenu1">
""")
    first_time = True
    for __used_name in used_location_names:
        if not first_time:
            glf.write('<li role="separator" class="divider"></li>\n')
        first_time = False
        glf.write('<li class="dropdown-header">{nm}</li>\n'.format(nm=__used_name["name"]))
        for __place in __used_name["places"]:
            glf.write('<li><a href="#" loc="{nm}">{pl}</a></li>\n'.format(nm=__used_name["name"], pl=__place))
    glf.write("""
  </ul>
</div>

<style>
#tblSales tr {
  font-size: small;
}
</style>

<div class="table-responsive">
 <table id="tblSales" class="table table-condensed table-hover">
<thead>
 <tr>
  <th>#</th>
  <th>Blueprint</th>
  <th class="hidden"></th>
  <th class="hidden"></th>
  <th>Price</th>
  <th>Contract</th>
 </tr>
</thead>
<tbody>
""")

    row_num = 1
    for corporation_id in __corp_keys:
        if not (int(corporation_id) in q_blueprints_settings.g_sale_of_blueprint["corporation_id"]):
            continue
        __corp = corps_blueprints[str(corporation_id)]
        __loc_keys = __corp["locations"].keys()
        for __loc_key in __loc_keys:
            __loc_dict = __corp["locations"][str(__loc_key)]
            if "station" in __loc_dict:
                __location_name = __loc_dict["station"]
            elif "solar" in __loc_dict:
                __location_name = __loc_dict["solar"]
            else:
                __location_name = __loc_key
            __used_name = next((n for n in used_location_names if n['name'] == __location_name), None)
            if __used_name is None:
                continue
            # определяем ангары, где лежат чертёжи
            __corp_blueprints = __corp["blueprints"]
            for __blueprint_dict in __corp_blueprints:
                if not __blueprint_dict["item_id"] in __used_name["ids"]:
                    continue
                __place = __blueprint_dict["flag"]
                if __place[:-1] == "CorpSAG":
                    __place = 'Hangar {}'.format(__place[-1:])  # Corp Security Access Group
                __me = __blueprint_dict["me"]
                __te = __blueprint_dict["te"]
                __type_id = __blueprint_dict["type_id"]
                __price = ""
                # выясняем сколько стоит чертёж?
                if "base_price" in __blueprint_dict:
                    __price = '{cost:,.1f} <sup class="qind-price-tag"><span class="label label-default">B</span></sup>'.format(cost=__blueprint_dict["base_price"])
                elif "average_price" in __blueprint_dict:
                    __price = '{cost:,.1f} <sup class="qind-price-tag"><span class="label label-primary">A</span></sup>'.format(cost=__blueprint_dict["average_price"])
                elif "adjusted_price" in __blueprint_dict:
                    __price = '{cost:,.1f} <sup class="qind-price-tag"><span class="label label-info">J</span></sup>'.format(cost=__blueprint_dict["adjusted_price"])
                # выясняем список текущих контрактов по чертежу
                __contracts = [b for b in __corp_blueprints if (b['type_id'] == __type_id) and ("cntrct_sta" in b)]

                __contracts_summary = ""
                for __cntrct_dict in __contracts:
                    # [ unknown, item_exchange, auction, courier, loan ]
                    __blueprint_status = __cntrct_dict["cntrct_typ"]
                    __status = '&nbsp;<span class="label label-default">{}</span>'.format(__blueprint_status)
                    # [ outstanding, in_progress, finished_issuer, finished_contractor, finished, cancelled, rejected, failed, deleted, reversed ]
                    __blueprint_contract_activity = __cntrct_dict["cntrct_sta"]
                    __activity = '&nbsp;<span class="label label-danger">{}</span>'.format(__blueprint_contract_activity)
                    # summary по контракту
                    if __contracts_summary:
                        __contracts_summary += '</br>\n'
                    __contracts_summary += \
                        '{prc:,.1f}{st}{act}'. \
                        format(prc=__cntrct_dict["price"],
                               st=__status,
                               act=__activity)
                # формируем строку таблицы - найден нужный чертёж в ассетах
                glf.write(
                    '<tr>'
                    '<th scope="row">{num}</th>'
                    '<td>{nm} <span class="label label-{lbclr}">{me} {te}</span></td>'
                    '<td class="hidden">{loc}</td>'
                    '<td class="hidden">{pl}</td>'
                    '<td align="right">{prc}</td>'
                    '<td>{cntrct}</td>'
                    '</tr>\n'.
                    format(num=row_num,
                           nm=__blueprint_dict["name"],
                           me=__me,
                           te=__te,
                           lbclr="success" if (__me == 10) and (__te == 20) else "warning",
                           loc=__location_name,
                           pl=__place,
                           prc=__price,
                           cntrct=__contracts_summary)
                )
                row_num = row_num + 1

    glf.write("""
</tbody>     
 </table>
</div>     
""")


def __dump_corp_blueprints_tbl(
        glf,
        corps_blueprints):
    __corp_keys = corps_blueprints.keys()
    # составляем список locations, где могут лежать чертежи, с тем чтобы сделать возможность группировать их по locations
    used_location_names = []
    for corporation_id in __corp_keys:
        __corp = corps_blueprints[str(corporation_id)]
        __loc_keys = __corp["locations"].keys()
        for __loc_key in __loc_keys:
            __loc_dict = __corp["locations"][str(__loc_key)]
            if "station" in __loc_dict:
                __location_name = __loc_dict["station"]
            elif "solar" in __loc_dict:
                __location_name = __loc_dict["solar"]
            else:
                __location_name = __loc_key
            if used_location_names.count(__location_name) == 0:
                used_location_names.append(__location_name)
    used_location_names.sort()

    glf.write("""
<style>
.dropdown-submenu {
  position: relative;
}
.dropdown-submenu .dropdown-menu {
  top: 0;
  left: 100%;
  margin-top: -1px;
}
.btn.btn-default:disabled{
  color: #aaa;
}
</style>

<nav class="navbar navbar-default">
 <div class="container-fluid">
  <div class="navbar-header">
   <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#bs-navbar-collapse" aria-expanded="false">
    <span class="sr-only">Toggle navigation</span>
    <span class="icon-bar"></span>
    <span class="icon-bar"></span>
    <span class="icon-bar"></span>
   </button>
   <a class="navbar-brand" data-target="#"><span class="glyphicon glyphicon-duplicate" aria-hidden="true"></span></a>
  </div>

  <div class="collapse navbar-collapse" id="bs-navbar-collapse">
   <ul class="nav navbar-nav">
    <li class="dropdown">
     <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Display Options <span class="caret"></span></a>
      <ul class="dropdown-menu">
       <li class="dropdown-submenu">
         <a class="options-submenu" data-target="#" role="button">Industry jobs <mark id="lbSelJob"></mark><span class="caret"></span></a>
         <ul class="dropdown-menu">
           <li class="dropdown-header">[Industry activities]</li>
           <li><a id="btnSelJob" job="1" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star qind-img-seljob" aria-hidden="true" job="1"></span> Manufacturing only</a></li>
           <li><a id="btnSelJob" job="3" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star qind-img-seljob" aria-hidden="true" job="3"></span> Research TE &amp; ME only</a></li>
           <li><a id="btnSelJob" job="5" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star qind-img-seljob" aria-hidden="true" job="5"></span> Copying only</a></li>
           <li><a id="btnSelJob" job="7" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star qind-img-seljob" aria-hidden="true" job="7"></span> Reverse Engineering only</a></li>
           <li><a id="btnSelJob" job="8" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star qind-img-seljob" aria-hidden="true" job="8"></span> Invention only</a></li>
           <li><a id="btnSelJob" job="9" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star qind-img-seljob" aria-hidden="true" job="9"></span> Reactions only</a></li>
           <li role="separator" class="divider"></li>
           <li><a id="btnSelJob" job="12" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star qind-img-seljob" aria-hidden="true" job="12"></span> Show all</a></li>
           <li><a id="btnSelJob" job="13" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star qind-img-seljob" aria-hidden="true" job="13"></span> Hide all</a></li>
           <li role="separator" class="divider"></li>
           <li><a id="btnToggleUnusedBlueprints" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowUnusedBlueprints"></span> Show unused blueprints</a></li>
         </ul>
       </li>

       <li><a id="btnTogglePriceVals" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowPriceVals"></span> Show Price column</a></li>
       <li><a id="btnTogglePriceTags" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowPriceTags"></span> Show Price tags</a></li>
       <li><a id="btnTogglePlace" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowPlace"></span> Show Place column</a></li>
       <li><a id="btnToggleBox" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowBox"></span> Show Box column</a></li>
       <li role="separator" class="divider"></li>
       <li><a id="btnToggleShowContracts" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowContracts"></span> Show Contracts</a></li>
       <li><a id="btnToggleShowFinishedContracts" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowFinishedContracts"></span> Show Finished Contracts</a></li>
       <li role="separator" class="divider"></li>
       <li><a id="btnToggleExpand" data-target="#" role="button">Expand all tables</a></li>
       <li><a id="btnToggleCollapse" data-target="#" role="button">Collapse all tables</a></li>
       <li><a id="btnToggleLegend" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowLegend"></span> Show Legend</a></li>
       <li role="separator" class="divider"></li>
       <li><a id="btnResetOptions" data-target="#" role="button">Reset options</a></li>
      </ul>
    </li>
    
    <li class="dropdown">
     <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Locations <span class="caret"></span></a>
      <ul class="dropdown-menu">
""")
    for loc_name in used_location_names:
        glf.write(
            '<li><a id="btnSelLoc" loc="{nm}" data-target="#" role="button"><span class="glyphicon glyphicon-star qind-img-selloc" aria-hidden="true" loc="{nm}"></span> {nm}</a></li>\n'.
            format(nm=loc_name)
        )
    glf.write("""
       <li role="separator" class="divider"></li>
       <li><a id="btnToggleShowAllLocations" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowAllLocations"></span> Show all locations</a></li>
      </ul>
    </li>
""")

    glf.write("""

    <li><a data-target="#modalSales" role="button" data-toggle="modal">Sales</a></li>
   </ul>

   <form id="frmFilter" class="navbar-form navbar-right">
    <div class="input-group">
     <input id="edFilter" type="text" class="form-control" placeholder="What?">
      <span class="input-group-btn">
       <button id="btnFilter" class="btn btn-default" type="button" disabled>Filter</button>
      </span>
    </div>
   </form>
  </div>
 </div>
</nav>

<style>
.hvr-icon-fade {
  display--: inline-block;
  vertical-align: middle;
  -webkit-transform: perspective(1px) translateZ(0);
  transform: perspective(1px) translateZ(0);
  box-shadow: 0 0 1px rgba(0, 0, 0, 0);
}
.hvr-icon-fade .hvr-icon {
  -webkit-transform: translateZ(0);
  transform: translateZ(0);
  -webkit-transition-duration: 0.5s;
  transition-duration: 0.5s;
  -webkit-transition-property: color;
  transition-property: color;
}
.hvr-icon {
  color: #D6E0EE;
  top: 2px;
  left: 3px;
  font-size: smaller;
}
.hvr-icon-fade:hover .hvr-icon, .hvr-icon-fade:focus .hvr-icon, .hvr-icon-fade:active .hvr-icon {
  color: #0F9E5E;
}
.hvr-icon-sel {
  color: #999999;
}
tr.qind-bp-row {
  font-size: small;
}
</style>

<div class="container-fluid">
 <div class="panel-group" id="accordion" role="tablist" aria-multiselectable="true">
""")
    first_time = True
    for corporation_id in __corp_keys:
        __corp = corps_blueprints[str(corporation_id)]
        glf.write('  <div class="panel panel-primary">\n'
                  '   <div class="panel-heading" role="tab">\n'
                  '    <h3 class="panel-title">\n'
                  '     <a role="button" data-toggle="collapse" data-parent="#accordion" href="#pn{id}" aria-expanded="true" aria-controls="pn{id}">{nm}</a>\n'
                  '    </h3>\n'
                  '   </div>\n'
                  '   <div id="pn{id}" class="panel-collapse collapse{vsbl}" role="tabpanel" aria-labelledby="heading{id}">\n'.
                  format(nm=__corp["corporation"],
                         id=corporation_id,
                         vsbl=" in" if first_time else "")
        )
        first_time = False
        glf.write("""
    <div class="panel-body">
     <div class="table-responsive">
      <table class="table table-condensed table-hover">
<thead>
 <tr>
  <th>#</th>
  <th class="hvr-icon-fade" id="thSortSel" col="0">Blueprint<span class="glyphicon glyphicon-sort hvr-icon" aria-hidden="true"></span></th>
  <th class="hvr-icon-fade" id="thSortSel" col="1">ME<span class="glyphicon glyphicon-sort hvr-icon" aria-hidden="true"></span></th>
  <th class="hvr-icon-fade" id="thSortSel" col="2">TE<span class="glyphicon glyphicon-sort hvr-icon" aria-hidden="true"></span></th>
  <th class="hvr-icon-fade" id="thSortSel" col="3">Qty<span class="glyphicon glyphicon-sort hvr-icon" aria-hidden="true"></span></th>
  <th class="qind-td-prc hvr-icon-fade" id="thSortSel" col="4">Price, ISK<span class="glyphicon glyphicon-sort hvr-icon" aria-hidden="true"></span></th>
  <th class="hvr-icon-fade" id="thSortSel" col="5">Location<span class="glyphicon glyphicon-sort hvr-icon" aria-hidden="true"></span></th>
  <th class="qind-td-plc hvr-icon-fade" id="thSortSel" col="6">Place<span class="glyphicon glyphicon-sort hvr-icon" aria-hidden="true"></span></th>
  <th class="qind-td-box hvr-icon-fade" id="thSortSel" col="7">Box<span class="glyphicon glyphicon-sort hvr-icon" aria-hidden="true"></span></th>
 </tr>
</thead>
<tbody>
""")
        row_num = 1
        __summary_cost = 0
        for __blueprint_dict in __corp["blueprints"]:
            # выясняем сколько стоит один чертёж?
            __price = ""
            __fprice = ""
            if "base_price" in __blueprint_dict:
                __price = '{cost:,.1f} <sup class="qind-price-tag"><span class="label label-default">B</span></sup>'.format(cost=__blueprint_dict["base_price"])
                __fprice = '{:.1f}'.format(__blueprint_dict["base_price"])
            elif "average_price" in __blueprint_dict:
                __price = '{cost:,.1f} <sup class="qind-price-tag"><span class="label label-primary">A</span></sup>'.format(cost=__blueprint_dict["average_price"])
                __fprice = '{:.1f}'.format(__blueprint_dict["average_price"])
            elif "adjusted_price" in __blueprint_dict:
                __price = '{cost:,.1f} <sup class="qind-price-tag"><span class="label label-info">J</span></sup>'.format(cost=__blueprint_dict["adjusted_price"])
                __fprice = '{:.1f}'.format(__blueprint_dict["adjusted_price"])
            elif "price" in __blueprint_dict:
                __price = '{cost:,.1f} <sup class="qind-price-tag"><span class="label label-danger">C</span></sup>'.format(cost=__blueprint_dict["price"])
                __fprice = '{:.1f}'.format(__blueprint_dict["price"])
            # проверяем работки по текущему чертежу?
            __status = ""
            __activity = ""
            __blueprint_activity = None
            __blueprint_contract_activity = None
            if "st" in __blueprint_dict:
                # [ active, cancelled, delivered, paused, ready, reverted ]
                __blueprint_status = __blueprint_dict["st"]
                if (__blueprint_status == "active") or (__blueprint_status == "delivered"):
                    __status = '&nbsp;<span class="label label-default">{}</span>'.format(__blueprint_status)
                elif __blueprint_status == "ready":
                    __status = '&nbsp;<span class="label label-success">{}</span>'.format(__blueprint_status)
                elif (__blueprint_status == "cancelled") or (__blueprint_status == "paused") or (__blueprint_status == "reverted"):
                    __status = '&nbsp;<span class="label label-warning">{}</span>'.format(__blueprint_status)
                else:
                    __status = '&nbsp;<span class="label label-danger">{}</span>'.format(__blueprint_status)
                # [1..6] : https://support.eveonline.com/hc/en-us/articles/203210272-Activities-and-Job-Types
                # [0,1,3,4,5,7,8,11, +9?] : https://github.com/esi/esi-issues/issues/894
                __blueprint_activity = __blueprint_dict["act"]
                if __blueprint_activity == 1:
                    __activity = '&nbsp;<span class="label label-primary">manufacturing</span>'  # Manufacturing
                elif __blueprint_activity == 3:
                    __activity = '&nbsp;<span class="label label-info">te</span>'  # Science
                elif __blueprint_activity == 4:
                    __activity = '&nbsp;<span class="label label-info">me</span>'  # Science
                elif __blueprint_activity == 5:
                    __activity = '&nbsp;<span class="label label-info">copying</span>'  # Science
                elif __blueprint_activity == 7:
                    __activity = '&nbsp;<span class="label label-info">reverse</span>'  # Science
                elif __blueprint_activity == 8:
                    __activity = '&nbsp;<span class="label label-info">invention</span>'  # Science
                elif (__blueprint_activity == 9) or (__blueprint_activity == 11):
                    __activity = '&nbsp;<span class="label label-success">reaction</span>'  # Reaction
                else:
                    __activity = '&nbsp;<span class="label label-danger">{}</span>'.format(__blueprint_activity)
            # проверяем сведения по контракту, если чертёж прямо сейчас продаётся
            elif "cntrct_sta" in __blueprint_dict:
                # [ unknown, item_exchange, auction, courier, loan ]
                __blueprint_status = __blueprint_dict["cntrct_typ"]
                __status = '&nbsp;<span class="label label-default">{}</span>'.format(__blueprint_status)
                # [ outstanding, in_progress, finished_issuer, finished_contractor, finished, cancelled, rejected, failed, deleted, reversed ]
                __blueprint_contract_activity = __blueprint_dict["cntrct_sta"]
                __activity = '&nbsp;<span class="label label-danger">{}</span>'.format(__blueprint_contract_activity)
            # определяем местоположение чертежа
            __location_id = __blueprint_dict["loc"]
            __location_name = __location_id
            __location_box = ""
            if str(__location_id) in __corp["locations"]:
                # определяем название станции или солнечной системы, где лежит чертёж
                __loc_dict = __corp["locations"][str(__location_id)]
                if "station" in __loc_dict:
                    __location_name = __loc_dict["station"]
                elif "solar" in __loc_dict:
                    __location_name = __loc_dict["solar"]
                # определяем название контейнера, где лежит чертёж (названия ingame задают игроки)
                if not (__loc_dict["name"] is None):
                    __location_box = __loc_dict["name"]
            # определяем ангар и коробку, где лежит чертёж
            __place = __blueprint_dict["flag"]
            if __place[:-1] == "CorpSAG":
                __place = 'Hangar {}'.format(__place[-1:])  # Corp Security Access Group
            # вывод в таблицу информацию о чертеже
            glf.write('<tr class="qind-bp-row"{job}{cntrct}>'
                      ' <th scope="row">{num}</th>\n'
                      ' <td>{nm}{st}{act}</td>'
                      ' <td align="right">{me}</td>'
                      ' <td align="right">{te}</td>'
                      ' <td align="right">{q}</td>'
                      ' <td class="qind-td-prc" align="right" x-data="{iprice}">{price}</td>'
                      ' <td>{loc}</td>'
                      ' <td class="qind-td-plc">{plc}</td>'
                      ' <td class="qind-td-box">{box}</td>'
                      '</tr>\n'.
                      format(num=row_num,
                             nm=__blueprint_dict["name"],
                             st=__status,
                             act=__activity,
                             job="" if __blueprint_activity is None else ' job="{}"'.format(__blueprint_activity),
                             cntrct="" if __blueprint_contract_activity is None else ' cntrct="{}"'.format(__blueprint_contract_activity),
                             me=__blueprint_dict["me"] if "me" in __blueprint_dict else "",
                             te=__blueprint_dict["te"] if "te" in __blueprint_dict else "",
                             q=__blueprint_dict["q"],
                             price=__price,
                             iprice=__fprice,
                             loc=__location_name,
                             plc=__place,
                             box=__location_box))
            # подсчёт общей статистики
            # __summary_cost = __summary_cost + __stat_dict["cost"]
            row_num = row_num + 1

        glf.write("""
</tbody>
<tfoot>
<tr class="qind-summary-assets" style="font-weight:bold;">
 <th></th>
 <td align="right" colspan="3">Summary (assets)</td>
 <td align="right"></td>
 <td class="qind-td-prc" align="right"></td>
 <td></td>
 <td class="qind-td-plc"></td>
 <td class="qind-td-box"></td>
</tr>
<tr class="qind-summary-contracts" style="font-weight:bold;">
 <th></th>
 <td align="right" colspan="3">Summary (contracts)</td>
 <td align="right"></td>
 <td class="qind-td-prc" align="right"></td>
 <td></td>
 <td class="qind-td-plc"></td>
 <td class="qind-td-box"></td>
</tr>
</tfoot>
      </table>
     </div> <!--table-responsive-->
    </div> <!--panel-body-->
   </div> <!--panel-collapse-->
  </div> <!--panel-->
""")

    glf.write("""
 </div> <!--accordion-->
""")

    # создаём заголовок модального окна, где будем показывать список чертежей для продажи
    __dump_any_into_modal_header_wo_button(
        glf,
        'Sales of blueprints',
        'Sales',
        'modal-lg')
    # формируем содержимое модального диалога
    __dump_corp_blueprints_sales(glf, corps_blueprints)
    # закрываем footer модального диалога
    __dump_any_into_modal_footer(glf)

    glf.write("""
<div id="legend-block">
 <hr>
 <h4>Legend</h4>
 <p>
  <strong>ME</strong> - Material Efficiency, <strong>TE</strong> - Time Efficiency, <strong>Qty</strong> - blueprints
  quantity if it is a stack of blueprint originals fresh from the market (e.g. no activities performed
  on them yet), <strong>Price</strong> - price for one blueprint, <strong>Location</strong>, <strong>Place</strong> and
  <strong>Box</strong> - detailed location of blueprint.
 </p>
 <p>
  <span class="label label-primary">A</span>, <span class="label label-info">J</span>, <span class="label label-default">B</span>,
  <span class="label label-danger">C</span> - <strong>price tags</strong>,
  to indicate type of market' price. There are <span class="label label-primary">A</span> average price (<i>current market price</i>),
  and <span class="label label-info">J</span> adjusted price (<i>average over the last 28 days</i>), <span class="label label-default">B</span>
  base price (<i>standart CCP item price</i>) and <span class="label label-danger">C</span> - contract price.
 </p>
 <p>
  <span class="label label-default">active</span>, <span class="label label-default">delivered</span>,
  <span class="label label-success">ready</span>, <span class="label label-warning">cancelled</span>,
  <span class="label label-warning">paused</span>, <span class="label label-warning">reverted</span> - all possible
  <strong>statuses</strong> of blueprints that are in industry mode.
 </p>
  <span class="label label-danger">outstanding</span>,
  <span class="label label-danger">in_progress</span>,
  <span class="label label-danger">finished_issuer</span>,
  <span class="label label-danger">finished_contractor</span>,
  <span class="label label-danger">finished</span>,
  <span class="label label-danger">cancelled</span>,
  <span class="label label-danger">rejected</span>,
  <span class="label label-danger">failed</span>,
  <span class="label label-danger">deleted</span>,
  <span class="label label-danger">reversed</span> - all possible <strong>statuses</strong> of current contracts.
 <p>
  <span class="label label-primary">manufacturing</span> - manufacturing industry activity.</br>
  <span class="label label-info">te</span>, 
  <span class="label label-info">me</span>, 
  <span class="label label-info">copying</span>, 
  <span class="label label-info">reverse</span>, 
  <span class="label label-info">invention</span> - science industry activities.</br> 
  <span class="label label-success">reaction</span> - reaction industry activity.
 </p>
</div>

<script>
  // Blueprints Options dictionaries
  var g_job_activities = [
    '', 'Manufacturing', '', 'Research TE &amp; ME', '', 'Copying', '',
    'Reverse Engineering', 'Invention', 'Reactions', '', '',
    'Show', 'Hide'
  ];
  var g_tbl_col_types = [0,1,1,1,2,0,0,0]; // 0:str, 1:num, 2:x-data
  var g_tbl_filter = null;

  // Blueprints Options storage (prepare)
  ls = window.localStorage;

  // Tools & Utils
  function numLikeEve(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }
  // Blueprints table sorter
  function sortTable(table, order, what, typ) {
    var asc = order > 0;
    var col = 'td:eq('+what.toString()+')';
    var tbody = table.find('tbody');
    tbody.find('tr').sort(function(a, b) {
      var keyA, keyB;
      if (typ == 2) {
        keyA = parseFloat($(col, a).attr('x-data'));
        keyB = parseFloat($(col, b).attr('x-data'));
        if (isNaN(keyA)) keyA = 0;
        if (isNaN(keyB)) keyB = 0;
        return asc ? (keyA - keyB) : (keyB - keyA);
      }
      else {
        keyA = $(col, a).text();
        keyB = $(col, b).text();
        if (typ == 1) {
          keyA = parseInt(keyA, 10);
          keyB = parseInt(keyB, 10);
          if (isNaN(keyA)) keyA = 0;
          if (isNaN(keyB)) keyB = 0;
          return asc ? (keyA - keyB) : (keyB - keyA);
        } 
      }
      _res = (keyA < keyB) ? -1 : ((keyA > keyB) ? 1 : 0);
      if (asc) _res = -_res;
      return _res;
    }).appendTo(tbody);
  }

  // Disable function
  jQuery.fn.extend({
    disable: function(state) {
      return this.each(function() {
        this.disabled = state;
      });
    }
  });

  // Blueprints Options storage (init)
  function resetOptionsMenuToDefault() {
    if (!ls.getItem('Show Legend')) {
      ls.setItem('Show Legend', 1);
    }
    if (!ls.getItem('Show Price Vals')) {
      ls.setItem('Show Price Vals', 1);
    }
    if (!ls.getItem('Show Price Tags')) {
      ls.setItem('Show Price Tags', 1);
    }
    if (!ls.getItem('Show Place')) {
      ls.setItem('Show Place', 0);
    }
    if (!ls.getItem('Show Box')) {
      ls.setItem('Show Box', 0);
    }
    if (!ls.getItem('Show Unused Blueprints')) {
      ls.setItem('Show Unused Blueprints', 1);
    }
    if (!ls.getItem('Show Industry Jobs')) {
      ls.setItem('Show Industry Jobs', 12);
    }
    if (!ls.getItem('Show Contracts')) {
      ls.setItem('Show Contracts', 1);
    }
    if (!ls.getItem('Show Finished Contracts')) {
      ls.setItem('Show Finished Contracts', 1);
    }
  }
  // Blueprints Options storage (rebuild menu components)
  function rebuildOptionsMenu() {
    show = ls.getItem('Show Legend');
    if (show == 1)
      $('#imgShowLegend').removeClass('hidden');
    else
      $('#imgShowLegend').addClass('hidden');
    show = ls.getItem('Show Contracts');
    if (show == 1)
      $('#imgShowContracts').removeClass('hidden');
    else
      $('#imgShowContracts').addClass('hidden');
    show = ls.getItem('Show Finished Contracts');
    if (show == 1)
      $('#imgShowFinishedContracts').removeClass('hidden');
    else
      $('#imgShowFinishedContracts').addClass('hidden');
    show = ls.getItem('Show Price Vals');
    if (show == 1)
      $('#imgShowPriceVals').removeClass('hidden');
    else
      $('#imgShowPriceVals').addClass('hidden');
    show = ls.getItem('Show Price Tags');
    if (show == 1)
      $('#imgShowPriceTags').removeClass('hidden');
    else
      $('#imgShowPriceTags').addClass('hidden');
    show = ls.getItem('Show Place');
    if (show == 1)
      $('#imgShowPlace').removeClass('hidden');
    else
      $('#imgShowPlace').addClass('hidden');
    show = ls.getItem('Show Box');
    if (show == 1)
      $('#imgShowBox').removeClass('hidden');
    else
      $('#imgShowBox').addClass('hidden');
    show = ls.getItem('Show Unused Blueprints');
    if (show == 1)
      $('#imgShowUnusedBlueprints').removeClass('hidden');
    else
      $('#imgShowUnusedBlueprints').addClass('hidden');
    job = ls.getItem('Show Industry Jobs');
    $('span.qind-img-seljob').each(function() {
      _job = $(this).attr('job');
      if (job == _job)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
    $('#lbSelJob').html(g_job_activities[job]);
    loc = ls.getItem('Show Only Location');
    if (!loc) {
      $('span.qind-img-selloc').each(function() { $(this).addClass('hidden'); })
      $('#imgShowAllLocations').removeClass('hidden');
    } else {
      $('#imgShowAllLocations').addClass('hidden');
      $('span.qind-img-selloc').each(function() {
        _loc = $(this).attr('loc');
        if (loc == _loc)
          $(this).removeClass('hidden');
        else
          $(this).addClass('hidden');
      })
    }
  }
  // Blueprints filter method (to rebuild body components)
  function isBlueprintVisible(el, loc, unused, job, cntrct, cntrct_fin) {
    _res = 1;
    _loc = el.find('td').eq(5).text();
    _job = el.attr('job');
    _cntrct = el.attr('cntrct');
    _res = (loc && (_loc != loc)) ? 0 : 1;
    if (!(_cntrct === undefined)) {
      if (_res && (cntrct == 0))
        _res = 0;
      if (_res && (cntrct_fin == 0) && (_cntrct == "finished"))
        _res = 0;
    } else {
      if (_res && (unused == 0)) {
        if (_job === undefined)
          _res = 0;
      }
      if (_res && (!(_job === undefined))) {
        if (job == 13)
          _res = 0;
        else if (job == 12)
          _res = 1;
        else if ((job == _job) || (job == 3) && (_job == 4) || (job == 9) && (_job == 11))
          _res = 1;
        else
          _res = 0;
      }
    }
    if (_res && (!(g_tbl_filter === null))) {
      var txt = el.find('td').eq(0).text().toLowerCase();
      _res = txt.includes(g_tbl_filter);
      if (!_res) {
        txt = el.find('td').eq(5).text().toLowerCase();
        _res = txt.includes(g_tbl_filter);
        if (!_res) {
          txt = el.find('td').eq(6).text().toLowerCase();
          _res = txt.includes(g_tbl_filter);
          if (!_res) {
            txt = el.find('td').eq(7).text().toLowerCase();
            _res = txt.includes(g_tbl_filter);
          }
        }
      }
    }
    return _res;
  }
  // Blueprints Options storage (rebuild body components)
  function rebuildBody() {
    show = ls.getItem('Show Legend');
    if (show == 1)
      $('#legend-block').removeClass('hidden');
    else
      $('#legend-block').addClass('hidden');
    show = ls.getItem('Show Price Vals');
    $('.qind-td-prc').each(function() {
      if (show == 1)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
    show = ls.getItem('Show Price Tags');
    $('sup.qind-price-tag').each(function() {
      if (show == 1)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
    show = ls.getItem('Show Place');
    $('.qind-td-plc').each(function() {
      if (show == 1)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
    show = ls.getItem('Show Box');
    $('.qind-td-box').each(function() {
      if (show == 1)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
    loc = ls.getItem('Show Only Location');
    unused = ls.getItem('Show Unused Blueprints');
    job = ls.getItem('Show Industry Jobs');
    cntrct = ls.getItem('Show Contracts');
    cntrct_fin = ls.getItem('Show Finished Contracts');
    $('table').each(function() {
      _summary_a_qty = 0;
      _summary_a_price = 0.0;
      _summary_c_qty = 0;
      _summary_c_price = 0.0;
      // filtering
      $(this).find('tr.qind-bp-row').each(function() {
        show = isBlueprintVisible($(this), loc, unused, job, cntrct, cntrct_fin);
        if (show == 1) {
          $(this).removeClass('hidden');
          _cntrct = $(this).attr('cntrct');
          if (_cntrct === undefined) {
            _summary_a_qty += parseInt($(this).find('td').eq(3).text(),10);
            _summary_a_price += parseFloat($(this).find('td').eq(4).attr('x-data'));
          } else {
            _summary_c_qty += parseInt($(this).find('td').eq(3).text(),10);
            _summary_c_price += parseFloat($(this).find('td').eq(4).attr('x-data'));
          }
        } else
          $(this).addClass('hidden');
      })
      // sorting
      col = $(this).attr('sort_col');
      if (!(col === undefined)) {
        order = $(this).attr('sort_order');
        sortTable($(this),order,col,g_tbl_col_types[col]);
      }
      // summary (assets)
      tr_summary = $(this).find('tr.qind-summary-assets');
      tr_summary.find('td').eq(1).html(_summary_a_qty);
      tr_summary.find('td').eq(2).html(numLikeEve(_summary_a_price.toFixed(1)));
      // summary (contracts)
      tr_summary = $(this).find('tr.qind-summary-contracts');
      tr_summary.find('td').eq(1).html(_summary_c_qty);
      tr_summary.find('td').eq(2).html(numLikeEve(_summary_c_price.toFixed(1)));
    })
    // filtering sales
    var sales_loc_name = ls.getItem('Sales Location');
    var sales_place = ls.getItem('Sales Place');
    $('#tblSales').find('tbody').find('tr').each(function() {
      var tr = $(this);
      var show = true;
      if (!(sales_loc_name === null)) {
        show = sales_loc_name == tr.find('td').eq(1).text();
        if (show)
          show = sales_place == tr.find('td').eq(2).text();
      }
      if (show)
        tr.removeClass('hidden');
      else
        tr.addClass('hidden');
    });
  }
  // Blueprints Dropdown menu setup
  function rebuildSalesDropdown() {
    var sales_loc_name = ls.getItem('Sales Location');
    var sales_place = ls.getItem('Sales Place');
    if (!(sales_loc_name === null)) {
      var btn = $('#ddSalesMenu');
      btn.find('span.qind-lb-dd').html(sales_loc_name + ' <mark>' + sales_place + '</mark>');
      btn.val(sales_place);
    }
  }
  // Blueprints Options menu and submenu setup
  $(document).ready(function(){
    $('.dropdown-submenu a.options-submenu').on("click", function(e){
      $(this).next('ul').toggle();
      e.stopPropagation();
      e.preventDefault();
    });
    $('a#btnSelJob').on('click', function() {
      job = $(this).attr('job');
      ls.setItem('Show Industry Jobs', job);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleLegend').on('click', function () {
      show = (ls.getItem('Show Legend') == 1) ? 0 : 1;
      ls.setItem('Show Legend', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleShowContracts').on('click', function () {
      show = (ls.getItem('Show Contracts') == 1) ? 0 : 1;
      ls.setItem('Show Contracts', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleShowFinishedContracts').on('click', function () {
      show = (ls.getItem('Show Finished Contracts') == 1) ? 0 : 1;
      ls.setItem('Show Finished Contracts', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleExpand').on('click', function () {
      $('div.panel-collapse').each(function(){ $(this).addClass('in'); });
    });
    $('#btnToggleCollapse').on('click', function () {
      $('div.panel-collapse').each(function(){ $(this).removeClass('in'); });
    });
    $('#btnTogglePriceVals').on('click', function () {
      show = (ls.getItem('Show Price Vals') == 1) ? 0 : 1;
      ls.setItem('Show Price Vals', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnTogglePriceTags').on('click', function () {
      show = (ls.getItem('Show Price Tags') == 1) ? 0 : 1;
      ls.setItem('Show Price Tags', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnTogglePlace').on('click', function () {
      show = (ls.getItem('Show Place') == 1) ? 0 : 1;
      ls.setItem('Show Place', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleBox').on('click', function () {
      show = (ls.getItem('Show Box') == 1) ? 0 : 1;
      ls.setItem('Show Box', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleUnusedBlueprints').on('click', function () {
      show = (ls.getItem('Show Unused Blueprints') == 1) ? 0 : 1;
      ls.setItem('Show Unused Blueprints', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleShowAllLocations').on('click', function () {
      ls.removeItem('Show Only Location');
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('a#btnSelLoc').on('click', function() {
      loc = $(this).attr('loc');
      ls.setItem('Show Only Location', loc);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('th#thSortSel').on('click', function() {
      var col = $(this).attr('col');
      var table = $(this).closest('table');
      var thead = table.find('thead');
      var sort = table.attr('sort_col');
      var order = table.attr('sort_order');
      thead.find('th').each(function() {
        _col = $(this).attr('col');
        var icn = $(this).find('span');
        if (col == _col) {
          if (sort === undefined)
            order = 1;
          else if (sort == col)
            order = -order;
          else
            order = 1;
          icn.removeClass('glyphicon-sort');
          if (order == 1) {
            icn.removeClass('glyphicon-sort-by-attributes-alt');
            icn.addClass('glyphicon-sort-by-attributes');
          } else {
            icn.removeClass('glyphicon-sort-by-attributes');
            icn.addClass('glyphicon-sort-by-attributes-alt');
          }
          icn.addClass('hvr-icon-sel');
          table.attr('sort_col', col);
          table.attr('sort_order', order);
        } else if (!(sort === undefined)) {
          icn.removeClass('glyphicon-sort-by-attributes');
          icn.removeClass('glyphicon-sort-by-attributes-alt');
          icn.addClass('glyphicon-sort');
          icn.removeClass('hvr-icon-sel');
        }
      })
      sortTable(table,order,col,g_tbl_col_types[col]);
    });
    $('#edFilter').on('keypress', function (e) {
      if (e.which == 13)
        $('#btnFilter').click();
    })
    $('#edFilter').on('change', function () {
      var what = $('#edFilter').val();
      $('#btnFilter').disable(what.length == 0);
      $('#btnFilter').click();
    });
    $('#btnFilter').on('click', function () {
      var what = $('#edFilter').val();
      if (what.length == 0)
        g_tbl_filter = null;
      else
        g_tbl_filter = what.toLowerCase();
      rebuildBody();
    });
    $("#frmFilter").submit(function(e) {
      e.preventDefault();
    });
    $('#ddSales').on('click', 'li a', function () {
      var li_a = $(this);
      var loc_name = li_a.attr('loc');
      var place = li_a.text();
      ls.setItem('Sales Location', loc_name);
      ls.setItem('Sales Place', place);
      rebuildSalesDropdown();
      rebuildBody();
    });
    $('#btnResetOptions').on('click', function () {
      ls.clear();
      resetOptionsMenuToDefault();
      rebuildOptionsMenu();
      rebuildBody();
    });
    // first init
    resetOptionsMenuToDefault();
    rebuildOptionsMenu();
    rebuildSalesDropdown();
    rebuildBody();
  });
</script>
""")


def dump_blueprints_into_report(
        ws_dir,
        corps_blueprints):
    glf = open('{dir}/blueprints.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        __dump_header(glf, "Blueprints")
        __dump_corp_blueprints_tbl(glf, corps_blueprints)
        __dump_footer(glf)
    finally:
        glf.close()


def __dump_corp_titan(
        glf,
        # настройки генерации отчёта
        report_options,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        sde_icon_ids,
        # esi данные, загруженные с серверов CCP
        corp_assets_data,
        corp_industry_jobs_data,
        corp_ass_names_data,
        corp_blueprints_data,
        eve_market_prices_data,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_ass_loc_data,
        corp_bp_loc_data,
        corp_assets_tree,
        materials_for_bps,
        research_materials_for_bps):
    product_name = report_options["product"]
    blueprint_containter_ids = [c["id"] for c in report_options["blueprints"]]
    enable_copy_to_clipboard = True

    __type_id = get_type_id_by_item_name(sde_type_ids, product_name)
    if __type_id is None:
        return
    __blueprint_id, __blueprint_materials = get_blueprint_type_id_by_product_id(__type_id, sde_bp_materials)
    __is_reaction_formula = is_type_id_nested_into_market_group(__type_id, [1849], sde_type_ids, sde_market_groups)

    glf.write("""
<div class="container-fluid">
<div class="media">
 <div class="media-left">
""")

    glf.write('  <img class="media-object icn64" src="{src}" alt="{nm}">\n'
              ' </div>\n'
              ' <div class="media-body">\n'
              '  <h4 class="media-heading">{nm}</h4>\n'
              '<p>\n'
              'EveMarketer {nm} tradings: <a href="https://evemarketer.com/types/{pid}">https://evemarketer.com/types/{pid}</a></br>'
              'EveMarketer {nm} Blueprint tradings: <a href="https://evemarketer.com/types/{bid}">https://evemarketer.com/types/{bid}</a></br>'
              'Adam4EVE {nm} manufacturing calculator: <a href="https://www.adam4eve.eu/manu_calc.php?typeID={bid}">https://www.adam4eve.eu/manu_calc.php?typeID={bid}</a></br>'
              'Adam4EVE {nm} price history: <a href="https://www.adam4eve.eu/commodity.php?typeID={pid}">https://www.adam4eve.eu/commodity.php?typeID={pid}</a></br>'
              'Adam4EVE {nm} Blueprint price history: <a href="https://www.adam4eve.eu/commodity.php?typeID={bid}">https://www.adam4eve.eu/commodity.php?typeID={bid}</a>'.
              format(nm=product_name,
                     src=__get_img_src(__type_id, 64),
                     pid=__type_id,
                     bid=__blueprint_id))

    # создаём запись несуществующего пока чертежа
    __titan_blueprint_dict = {
        "cp": True,  # блюпринт на титан - копия
        "qr": 1,
        "me": 0,
        "te": 0,
        "st": None,
        "id": None
    }
    for b in corp_blueprints_data:
        __type_id = int(b["type_id"])
        if __blueprint_id != __type_id:
            continue
        # __location_id = int(b["location_id"])
        # if not (__location_id in blueprint_containter_ids):
        #     continue
        if (__titan_blueprint_dict["me"] < b["material_efficiency"]) or (__titan_blueprint_dict["id"] is None):
            __quantity = int(b["quantity"])
            # A range of numbers with a minimum of -2 and no maximum value where -1 is an original and -2 is a copy.
            # It can be a positive integer if it is a stack of blueprint originals fresh from the market (e.g. no
            # activities performed on them yet).
            __is_blueprint_copy = __quantity == -2
            __titan_blueprint_dict = {
                "cp": __is_blueprint_copy,
                "me": b["material_efficiency"],
                "te": b["time_efficiency"],
                "qr": b["runs"] if __is_blueprint_copy else (1 if __quantity == -1 else __quantity),
                "id": b["item_id"]
            }
            print('Found {} Blueprint: '.format(product_name), __titan_blueprint_dict)

    # __titan_is_blueprint_copy = __titan_blueprint_dict["cp"]
    __titan_material_efficiency = __titan_blueprint_dict["me"]
    # __titan_time_efficiency = __titan_blueprint_dict["te"]
    # __titan_blueprint_status = __titan_blueprint_dict["st"]
    __titan_quantity_or_runs = __titan_blueprint_dict["qr"]

    glf.write("""
</p>
  </div> <!--media-body-->
 </div> <!--media-->
<hr>
 <div class="media">
  <div class="media-left">
""")
    glf.write('  <img class="media-object icn64" src="{src}" alt="Summary raw materials">\n'.
              format(src=__get_icon_src(1436, sde_icon_ids)))  # Manufacture & Research
    glf.write("""
  </div>
  <div class="media-body">
   <h4 class="media-heading">Manufacturing materials</h4>
""")
    for m in __blueprint_materials["activities"]["manufacturing"]["materials"]:
        bpmm_used = int(m["quantity"])
        bpmm_tid = int(m["typeID"])
        bpmm_tnm = get_item_name_by_type_id(sde_type_ids, bpmm_tid)
        # вывод наименования ресурса
        glf.write(
            '<span style="white-space:nowrap">'
            '<img class="icn24" src="{src}"> {q:,d} x {nm} '
            '</span>\n'.format(
                src=__get_img_src(bpmm_tid, 32),
                q=bpmm_used,
                nm=bpmm_tnm
            )
        )

    glf.write("""
  </div> <!--media-body-->
 </div> <!--media-->
<hr>
 <div class="media">
  <div class="media-left">
""")
    glf.write('  <img class="media-object icn64" src="{src}" alt="Capital Ship Components">\n'.
              format(src=__get_icon_src(2863, sde_icon_ids)))  # Standard Capital Ship Components
    glf.write("""
  </div>
  <div class="media-body">
   <h4 class="media-heading">Capital Ship Components</h4>
<p><var>Efficiency</var> = <var>Required</var> * (100 - <var>material_efficiency</var> - 1 - 4.2) / 100,<br/>
where <var>material_efficiency</var> for unknown and unavailable blueprint is 0.</p>
<div class="table-responsive">
 <table class="table table-condensed">
<thead>
 <tr>
  <th style="width:40px;">#</th>
  <th>Materials</th>
  <th>Required</th>
  <th>Efficiency</th>
 </tr>
</thead>
<tbody>
""")

    materials_summary = []

    row1_num = 0
    for m1 in __blueprint_materials["activities"]["manufacturing"]["materials"]:
        row1_num = row1_num + 1
        bpmm1_tid = int(m1["typeID"])
        bpmm1_tnm = get_item_name_by_type_id(sde_type_ids, bpmm1_tid)
        bpmm1_used = int(m1["quantity"])
        bpmm1_need = bpmm1_used  # поправка на эффективнсть материалов
        bpmm1_blueprint_id, bpmm1_blueprint_materials = get_blueprint_type_id_by_product_id(bpmm1_tid, sde_bp_materials)
        # поиск чертежей, имеющихся в наличии у корпорации
        bpmm1_blueprints = []
        if not (bpmm1_blueprint_id is None):
            for b in corp_blueprints_data:
                __type_id = int(b["type_id"])
                if bpmm1_blueprint_id != __type_id:
                    continue
                __location_id = int(b["location_id"])
                if not (__location_id in blueprint_containter_ids):
                    continue
                __quantity = int(b["quantity"])
                # A range of numbers with a minimum of -2 and no maximum value where -1 is an original and -2 is a copy.
                # It can be a positive integer if it is a stack of blueprint originals fresh from the market (e.g. no
                # activities performed on them yet).
                __is_blueprint_copy = __quantity == -2
                __bp_dict = {
                    "cp": __is_blueprint_copy,
                    "me": b["material_efficiency"],
                    "te": b["time_efficiency"],
                    "qr": b["runs"] if __is_blueprint_copy else (1 if __quantity == -1 else __quantity)
                }
                bpmm1_blueprints.append(__bp_dict)
        # расчёт материалов с учётом эффективность производства
        if not __is_reaction_formula:
            # TODO: хардкодим -1% structure role bonus, -4.2% installed rig
            # см. 1 x run: http://prntscr.com/u0g07w
            # см. 4 x run: http://prntscr.com/u0g0cd
            # см. экономия материалов: http://prntscr.com/u0g11u
            __me = int(100 - __titan_material_efficiency - 1 - 4.2)
            bpmm1_need = int((bpmm1_used * __me) / 100)
            if 0 != ((bpmm1_used * __me) % 100):
                bpmm1_need = bpmm1_need + 1
        # вывод наименования ресурса
        glf.write(
            '<tr class="active">\n'
            ' <th scope="row">{num}</th>\n'
            ' <td><img class="icn24" src="{src}"> {nm}</td>\n'
            ' <td>{qr:,d}</td>\n'
            ' <td>{qe:,d}</td>\n'
            '</tr>'.
            format(
                num=row1_num,
                nm=bpmm1_tnm,
                src=__get_img_src(bpmm1_tid, 32),
                qr=bpmm1_used,
                qe=bpmm1_need
            )
        )
        # добавляем в summary сами материалы (продукты первого уровня)
        materials_summary.append({"id": bpmm1_tid,
                                  "q": bpmm1_need,
                                  "nm": bpmm1_tnm})
        # спускаемся на уровень ниже и выводим необходимое количество материалов для производства текущего
        # проверяем, что для текущего материала существуют чертежи для производства
        if not (bpmm1_blueprint_id is None):
            row2_num = 0
            # добавление в список материалов чертежей с известным кол-вом run-ов
            materials_summary.append({"id": bpmm1_blueprint_id,
                                      "q": bpmm1_need,
                                      "nm": get_item_name_by_type_id(sde_type_ids, bpmm1_blueprint_id),
                                      "b": bpmm1_blueprints})
            # вывод списка материалов для постройки по чертежу
            for m2 in bpmm1_blueprint_materials["activities"]["manufacturing"]["materials"]:
                row2_num = row2_num + 1
                bpmm2_tid = int(m2["typeID"])
                bpmm2_tnm = get_item_name_by_type_id(sde_type_ids, bpmm2_tid)
                bpmm2_used = int(m2["quantity"])  # сведения из чертежа
                bpmm2_need = bpmm2_used  # поправка на эффективнсть материалов
                bpmm2_is_reaction_formula = is_type_id_nested_into_market_group(bpmm1_tid, [1849], sde_type_ids, sde_market_groups)
                if not bpmm2_is_reaction_formula:
                    # TODO: хардкодим тут me, которая пока что одинакова на всех БПО и БПЦ в коллекции
                    material_efficiency = 10
                    # TODO: хардкодим -1% structure role bonus, -4.2% installed rig
                    # см. 1 x run: http://prntscr.com/u0g07w
                    # см. 4 x run: http://prntscr.com/u0g0cd
                    # см. экономия материалов: http://prntscr.com/u0g11u
                    __me = int(100 - material_efficiency - 1 - 4.2)
                    bpmm2_need = int((bpmm2_used * __me) / 100)
                    if 0 != ((bpmm2_used * __me) % 100):
                        bpmm2_need = bpmm2_need + 1
                # вывод наименования ресурса
                glf.write(
                    '<tr>\n'
                    ' <th scope="row">{num1}.{num2}</th>\n'
                    ' <td><img class="icn24" src="{src}"> {nm}</td>\n'
                    ' <td>{qr:,d}</td>\n'
                    ' <td>{qc:,d}</td>\n'
                    '</tr>'.
                    format(
                        num1=row1_num, num2=row2_num,
                        nm=bpmm2_tnm,
                        src=__get_img_src(bpmm2_tid, 32),
                        qr=bpmm1_used * bpmm2_used,
                        qc=bpmm1_need * bpmm2_need
                    )
                )
                # сохраняем материалы для производства в список их суммарного кол-ва
                __summary_dict = next((ms for ms in materials_summary if ms['id'] == bpmm2_tid), None)
                if __summary_dict is None:
                    __summary_dict = {"id": bpmm2_tid, "q": bpmm1_need * bpmm2_need, "nm": bpmm2_tnm}
                    materials_summary.append(__summary_dict)
                else:
                    __summary_dict["q"] += bpmm1_need * bpmm2_need

    glf.write("""
</tbody>
</table>
</div> <!--table-responsive-->
  </div> <!--media-body-->
 </div> <!--media-->
<hr>
 <div class="media">
  <div class="media-left">
""")
    glf.write('  <img class="media-object icn64" src="{src}" alt="Summary raw materials">\n'.
              format(src=__get_icon_src(1201, sde_icon_ids)))  # Materials
    glf.write("""
  </div>
  <div class="media-body">
   <h4 class="media-heading">Summary raw materials</h4>
<p>The number of Minerals and Components is counted for <mark>all assets</mark> owned by the corporation.</p>
""")
    glf.write('<p>The number of Blueprints is considered based on the presence of blueprints in container <mark>{}</mark>.</p>\n'.
              format(report_options["blueprints"][0]["name"]))  # Materials
    glf.write("""
<div class="table-responsive">
 <table class="table table-condensed" style="font-size:small">
<thead>
 <tr>
  <th style="width:40px;">#</th>
  <th>Materials</th>
  <th>Summary</th>
  <th>Available +<br/>In progress</th>
  <th>Not available</th>
  <th style="text-align:right;">Cost, ISK</th>
  <th style="text-align:right;">Volume, m&sup3;</th>
 </tr>
</thead>
<tbody>
""")

    material_groups = {}
    # not_enough_materials = []
    # stock_resources = []

    # подсчёт кол-ва имеющихся в наличии материалов
    for a in corp_assets_data:
        __type_id = int(a["type_id"])
        __summary_dict = next((ms for ms in materials_summary if ms['id'] == __type_id), None)
        if __summary_dict is None:
            continue
        __quantity = int(a["quantity"])
        if "a" in __summary_dict:
            __summary_dict["a"] += __quantity
        else:
            __summary_dict.update({"a": __quantity})
    # получаем список работ, которые выдутся с материалами
    for j in corp_industry_jobs_data:
        __type_id = j["product_type_id"]
        __summary_dict = next((ms for ms in materials_summary if ms['id'] == __type_id), None)
        if __summary_dict is None:
            continue
        __runs = int(j["runs"])
        if "j" in __summary_dict:
            __summary_dict["j"] += __runs
        else:
            __summary_dict.update({"j": __runs})

    # поиск групп, которым принадлежат материалы, которых не хватает для завершения производства по списку
    # чертежей в этом контейнере (планетарка отдельно, композиты отдельно, запуск работ отдельно)
    for __summary_dict in materials_summary:
        __quantity = __summary_dict["q"]
        __assets = __summary_dict["a"] if "a" in __summary_dict else 0
        __blueprints = __summary_dict["b"] if "b" in __summary_dict else []
        __in_progress = __summary_dict["j"] if "j" in __summary_dict else 0
        __type_id = __summary_dict["id"]
        __item_name = __summary_dict["nm"]
        #---
        __market_group = get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, __type_id)
        __material_dict = {
            "id": __type_id,
            "q": __quantity,
            "nm": __item_name,
            "a": __assets,
            "b": __blueprints,
            "j": __in_progress}
        if str(__market_group) in material_groups:
            material_groups[str(__market_group)].append(__material_dict)
        else:
            material_groups.update({str(__market_group): [__material_dict]})

    # добавление чертежа на корабль в список требуемых материалов
    # Vanquisher Blueprint не имеет marketGroupID, что является ошибкой ССР, и поэтому приходится изгаляться...
    __titan_blueprint = {
        "id": __blueprint_id,
        "q": __titan_quantity_or_runs,
        "nm": get_item_name_by_type_id(sde_type_ids, __blueprint_id),
        "a": 0,
        "b": [__titan_blueprint_dict] if not (__titan_blueprint_dict["id"] is None) else [],
        "j": 0}  # не показываем, что строим титан
    materials_summary.append(__titan_blueprint)
    material_groups["2"].append(__titan_blueprint)  # Blueprints & Reactions

    # вывод окончательного summary-списка материалов для постройки по чертежу
    ms_groups = material_groups.keys()
    row3_num = 0
    for __group_id in ms_groups:
        __is_blueprints_group = __group_id == "2"  # Blueprints & Reactions
        __mg1 = material_groups[__group_id]
        if (__group_id == "None") or (int(__group_id) == 1857):  # Minerals
            __mg1.sort(key=lambda m: m["q"], reverse=True)
        else:
            __mg1.sort(key=lambda m: m["q"])
        # выводим название группы материалов (Ship Equipment, Materials, Components, ...)
        if not (__group_id == "None"):
            __group_name = sde_market_groups[__group_id]["nameID"]["en"]
            # подготовка элементов управления копирования данных в clipboard
            __copy2clpbrd = '' if not enable_copy_to_clipboard else \
                '&nbsp;<a data-target="#" role="button" class="qind-copy-btn"' \
                '  data-toggle="tooltip"><button type="button" class="btn btn-default btn-xs"><span' \
                '  class="glyphicon glyphicon-copy" aria-hidden="true"></span> Export to multibuy</button></a>'
            glf.write('<tr>\n'
                      ' <td class="active" colspan="7"><strong>{nm}</strong><!--{id}-->{clbrd}</td>\n'
                      '</tr>'.
                      format(
                        nm=__group_name,
                        id=__group_id,
                        clbrd=__copy2clpbrd
                      ))
        # вывод материалов в группе
        __summary_cost = 0
        __summary_volume = 0
        for __material_dict in __mg1:
            # получение данных по материалу
            bpmm3_tid = __material_dict["id"]
            bpmm3_tnm = __material_dict["nm"]
            bpmm3_q = __material_dict["q"]  # quantity
            bpmm3_a = __material_dict["a"]  # available in assets
            bpmm3_b = __material_dict["b"]  # blueprints list
            bpmm3_j = __material_dict["j"]  # in progress (runs of jobs)
            row3_num = row3_num + 1
            # получение справочной информации о материале
            __type_dict = sde_type_ids[str(bpmm3_tid)]
            # получение цены материала
            bpmm3_price = None
            if not __is_blueprints_group:
                __price_dict = next((p for p in eve_market_prices_data if p['type_id'] == int(__type_id)), None)
                if not (__price_dict is None):
                    if "average_price" in __price_dict:
                        bpmm3_price = __price_dict["average_price"]
                    elif "adjusted_price" in __price_dict:
                        bpmm3_price = __price_dict["adjusted_price"]
                    elif "basePrice" in __type_dict:
                        bpmm3_price = __type_dict["basePrice"]
                elif "basePrice" in __type_dict:
                    bpmm3_price = __type_dict["basePrice"]
            # получение информации о кол-ве материала (сперва по блюпринтам, потом по ассетам)
            me_te_tags_list = []
            me_te_tags = ""
            if not __is_blueprints_group:
                bpmm3_available = bpmm3_a
            else:
                bpmm3_available = 0
                for b in bpmm3_b:
                    if not bool(b["cp"]):
                        # найден оригинал, это значит что можно произвести ∞ кол-во материалов
                        bpmm3_available = -1
                    if bpmm3_available >= 0:
                        bpmm3_available += int(b["qr"])
                    # составляем тэги с информацией о me/te чертежей
                    __me_te = '{me} {te}'.format(me=b["me"], te=b["te"])
                    if not (__me_te in me_te_tags_list):
                        me_te_tags += '&nbsp;<span class="label label-success">{}</span>'.format(__me_te)
                        me_te_tags_list.append(__me_te)
            # расчёт недостающего количества материала
            if bpmm3_available < 0:
                bpmm3_not_available = 0
            else:
                bpmm3_not_available = bpmm3_q - bpmm3_available if bpmm3_q >= bpmm3_available else 0
            # вывод наименования ресурса
            glf.write(
                '<tr>\n'
                ' <th scope="row">{num}</th>\n'
                ' <td data-copy="{nm}"><img class="icn24" src="{src}"> {nm}{me_te}</td>\n'
                ' <td>{qs:,d}</td>\n'
                ' <td>{qa}{qip}</td>\n'
                ' <td quantity="{qna}">{qna:,d}</td>\n'
                ' <td align="right">{cost}</td>'
                ' <td align="right">{volume}</td>'
                '</tr>'.
                format(
                    num=row3_num,
                    nm=bpmm3_tnm,
                    me_te=me_te_tags,
                    src=__get_img_src(bpmm3_tid, 32),
                    qs=bpmm3_q,
                    qa='{:,d}'.format(bpmm3_available) if bpmm3_available >= 0 else "&infin; <small>runs</small>",
                    qip="" if bpmm3_j == 0 else '<mark>+ {}</mark>'.format(bpmm3_j),
                    qna=bpmm3_not_available,
                    cost='{:,.1f}'.format(bpmm3_price * bpmm3_q) if not (bpmm3_price is None) else "",
                    volume='{:,.1f}'.format(__type_dict["volume"] * bpmm3_q) if not __is_blueprints_group else ""
                ))
            # подсчёт summary кол-ва по всем материалам группы
            if not (bpmm3_price is None):
                __summary_cost += bpmm3_price * bpmm3_q
                __summary_volume += __type_dict["volume"] * bpmm3_q
        # вывод summary-строки для текущей группы материалов
        if not (__group_id == "None") and not (__group_id == "2"):
            glf.write('<tr style="font-weight:bold">'
                      ' <th></th>'
                      ' <td colspan="4">Summary&nbsp;(<small>{nm}</small>)</td>'
                      ' <td align="right">{cost:,.1f}</td>'
                      ' <td align="right">{volume:,.1f}</td>'
                      '</tr>\n'.
                      format(nm=__group_name,
                             cost=__summary_cost,
                             volume=__summary_volume))

    glf.write("""
</tbody>
</table>
</div> <!--table-responsive-->
  </div> <!--media-body-->
 </div> <!--media-->
</div> <!--container-fluid-->

<script>
  // Titan' Options menu and submenu setup
  $(document).ready(function(){
    // Working with clipboard
    $('a.qind-copy-btn').each(function() {
      $(this).tooltip();
    })
    $('a.qind-copy-btn').bind('click', function () {
      var data_copy = $(this).attr('data-copy');
      if (data_copy === undefined) {
        var tr = $(this).parent().parent();
        var tbody = tr.parent();
        var rows = tbody.children('tr');
        var start_row = rows.index(tr);
        data_copy = '';
        rows.each( function(idx) {
          if (!(start_row === undefined) && (idx > start_row)) {
            var td = $(this).find('td').eq(0);
            if (!(td.attr('class') === undefined))
              start_row = undefined;
            else {
              var nm = td.attr('data-copy');
              if (!(nm === undefined)) {
                if (data_copy) data_copy += "\\n"; 
                data_copy += nm + "\\t" + $(this).find('td').eq(3).attr('quantity');
              }
            }
          }
        });
      }
      var $temp = $("<textarea>");
      $("body").append($temp);
      $temp.val(data_copy).select();
      try {
        success = document.execCommand("copy");
        if (success) {
          $(this).trigger('copied', ['Copied!']);
        }
      } finally {
        $temp.remove();
      }
    });
    $('a.qind-copy-btn').bind('copied', function(event, message) {
      $(this).attr('title', message)
        .tooltip('fixTitle')
        .tooltip('show')
        .attr('title', "Copy to clipboard")
        .tooltip('fixTitle');
    });
    if( /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ) {
      // какой-то код ...
      $('a.qind-copy-btn').each(function() {
        $(this).addClass('hidden');
      })
    }
  });
</script>
""")


def dump_titan_into_report(
        # путь, где будет сохранён отчёт
        ws_dir,
        # настройки генерации отчёта
        report_options,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        sde_icon_ids,
        # esi данные, загруженные с серверов CCP
        corp_assets_data,
        corp_industry_jobs_data,
        corp_ass_names_data,
        corp_blueprints_data,
        eve_market_prices_data,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_ass_loc_data,
        corp_bp_loc_data,
        corp_assets_tree,
        materials_for_bps,
        research_materials_for_bps):
    product_name = report_options["product"]
    glf = open('{dir}/{fnm}.html'.format(dir=ws_dir, fnm=__camel_to_snake(product_name)), "wt+", encoding='utf8')
    try:
        __dump_header(glf, product_name)
        __dump_corp_titan(
            glf,
            report_options,
            sde_type_ids,
            sde_bp_materials,
            sde_market_groups,
            sde_icon_ids,
            corp_assets_data,
            corp_industry_jobs_data,
            corp_ass_names_data,
            corp_blueprints_data,
            eve_market_prices_data,
            corp_ass_loc_data,
            corp_bp_loc_data,
            corp_assets_tree,
            materials_for_bps,
            research_materials_for_bps)
        __dump_footer(glf)
    finally:
        glf.close()
