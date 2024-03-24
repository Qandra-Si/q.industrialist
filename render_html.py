import time
import tzlocal
import re
from datetime import datetime

import q_industrialist_settings

__g_local_timezone = tzlocal.get_localzone()
__g_render_datetime = None
__g_pattern_c2s1 = re.compile(r'(.)([A-Z][a-z]+)')
__g_pattern_c2s2 = re.compile(r'([a-z0-9])([A-Z])')
__g_bootstrap_css_local = 'bootstrap/3.4.1/css/bootstrap.min.css'
__g_jquery_js_local = 'jquery/jquery-1.12.4.min.js'
__g_bootstrap_js_local = 'bootstrap/3.4.1/js/bootstrap.min.js'
__g_bootstrap_css_external = 'https://stackpath.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css" integrity="sha384-HSMxcRTRxnN+Bdg0JdbxYKrThecOKuH5zCYotlSAcp1+c8xmyTe9GYg1l9a69psu" crossorigin="anonymous'
__g_jquery_js_external = 'https://code.jquery.com/jquery-1.12.4.min.js" integrity="sha384-nvAa0+6Qg9clwYCGGPpDQLVpLNn0fRaROjHqs13t4Ggj3Ez50XnGQqc/r8MhnRDZ" crossorigin="anonymous'
__g_bootstrap_js_external = 'https://stackpath.bootstrapcdn.com/bootstrap/3.4.1/js/bootstrap.min.js" integrity="sha384-aJ21OjlMXNL5UyIl/XNwTMqvzeRMZH2w8c5cRVpzpU8Y5bApTppSuUkhZXN0VxHd" crossorigin="anonymous'
# __g_bootstrap_css_external = 'https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css" integrity="sha384-TX8t27EcRE3e/ihU7zmQxVncDAy5uIKz4rEkgIXeMed4M0jlfIDPvg6uqKI2xXr2" crossorigin="anonymous'
# __g_jquery_js_external = 'https://code.jquery.com/jquery-3.5.1.slim.min.js" integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj" crossorigin="anonymous'
# __g_bootstrap_js_external = 'https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-ho+j7jyWK8fNQe+A12Hb8AhRq26LrZ/JpcUGGOn+Y7RsweNrtN/tE3MoK7ZeZDyx" crossorigin="anonymous'


def __camel_to_snake(name, trim_spaces=False):  # https://stackoverflow.com/a/1176023
    name = __g_pattern_c2s1.sub(r'\1_\2', name)
    if trim_spaces:
        name = name.replace(" ", "")
    return __g_pattern_c2s2.sub(r'\1_\2', name).lower()


def __get_render_datetime():
    global __g_render_datetime
    global __g_local_timezone
    if __g_render_datetime is None:
        __g_render_datetime = datetime.fromtimestamp(time.time(), __g_local_timezone).strftime('%a, %d %b %Y %H:%M:%S %z')
    return __g_render_datetime


def __get_img_src(tp, sz):
    if q_industrialist_settings.g_use_filesystem_resources:
        return 'image_export_collection/Types/{}_{}.png'.format(tp, sz)
    else:
        return 'http://imageserver.eveonline.com/Type/{}_{}.png'.format(tp, sz)


def __get_icon_src(icon_id, sde_icon_ids):
    """
    see: https://forums.eveonline.com/t/eve-online-icons/78457/3
    """
    if str(icon_id) in sde_icon_ids:
        nm = sde_icon_ids[str(icon_id)]["iconFile"]
        if q_industrialist_settings.g_use_filesystem_resources:
            return 'image_export_collection/{}'.format(nm)
        else:  # https://everef.net/img/Icons/items/9_64_5.png
            return 'https://everef.net/img/{}'.format(nm)
    else:
        return ""


def __get_file_src(filename: str) -> str:
    if q_industrialist_settings.g_use_filesystem_resources:
        return f'../{filename}'
    else:
        return f'/{filename}'


def get_span_glyphicon(icon: str) -> str:
    return '<span class="glyphicon glyphicon-{}" aria-hidden="true"></span>'.format(icon)


def __dump_header(glf, header_name, use_dark_mode=False):
    # см. https://github.com/gokulkrishh/awesome-meta-and-manifest
    # см. https://developer.mozilla.org/ru/docs/Web/Manifest
    # рекомендуемый набор favicon-ок, см. https://stackoverflow.com/a/52322368
    # а также тут, см. https://developer.apple.com/design/human-interface-guidelines/ios/icons-and-images/app-icon/#app-icon-sizes
    glf.write("""
<!doctype html>
<html lang="ru">
 <head>
 <meta charset="utf-8">
 <meta http-equiv="X-UA-Compatible" content="IE=edge">
 <meta name="viewport" content="width=device-width,initial-scale=1">
 <meta name="description" content="A tool for planning logistics, building plans for the manufacture of modules, ships, tracking the process of fulfilling contracts.">
 <meta name="keywords" content="eve-online, eve, manufacturing, logistics, q.industrialist">
<style type="text/css">
.icn16 { width:16px; height:16px; }
.icn24 { width:24px; height:24px; }
.icn32 { width:32px; height:32px; }
.icn64 { width:64px; height:64px; }
</style>
""")
    if header_name is None:
        glf.write(' <title>Q.Industrialist</title>\n')
    else:
        glf.write(' <title>{nm} - Q.Industrialist</title>\n'.format(nm=header_name))
    if q_industrialist_settings.g_use_filesystem_resources:
        glf.write(' <link rel="stylesheet" href="{css}">\n'.format(css=__g_bootstrap_css_local))
    else:
        glf.write(' <link rel="stylesheet" href="{css}">\n'.format(css=__g_bootstrap_css_external))
    glf.write("""
 <!-- Android  -->
 <meta name="theme-color" content="#1e2021">
 <meta name="mobile-web-app-capable" content="yes">
 <!-- iOS -->
 <meta name="apple-mobile-web-app-title" content="Q.Industrialist">
 <meta name="apple-mobile-web-app-capable" content="yes">
 <meta name="apple-mobile-web-app-status-bar-style" content="default">
 <!-- Windows  -->
 <meta name="msapplication-navbutton-color" content="#1e2021">
 <meta name="msapplication-TileColor" content="#1e2021">
 <meta name="msapplication-TileImage" content="ms-icon-144x144.png">
 <meta name="msapplication-config" content="browserconfig.xml">
 <!-- Pinned Sites  -->
 <meta name="application-name" content="Q.Industrialist">
 <meta name="msapplication-tooltip" content="Q.Industrialist for EVE Online game">
 <meta name="msapplication-starturl" content="/">
 <!-- Enable night mode for this page  -->
 <meta name="nightmode" content="enable">
 <meta name="color-scheme" content="dark light">
 
 <!-- Main Link Tags -->
 <link rel="icon" type="image/png" sizes="16x16" href="images/favicon/favicon-16x16.png">
 <link rel="icon" type="image/png" sizes="32x32" href="images/favicon/favicon-32x32.png">
 <link rel="icon" type="image/png" sizes="96x96" href="images/favicon/android-icon-96x96.png">
 <!-- Android  -->
 <link rel="icon" type="image/png" sizes="192x192" href="images/favicon/android-icon-192x192.png">
 <link rel="icon" type="image/png" sizes="128x128" href="images/favicon/android-icon-128x128.png">
 <!-- iOS  -->
 <link rel="apple-touch-icon-precomposed" sizes="180x180" href="apple-touch-icon-precomposed.png">
 <link rel="apple-touch-icon" sizes="180x180" href="apple-touch-icon.png">
 <link rel="apple-touch-icon" sizes="120x120" href="images/favicon/apple-icon-120x120.png">
 <link rel="apple-touch-icon" sizes="152x152" href="images/favicon/apple-icon-152x152.png">
 <link rel="apple-touch-icon" sizes="167x167" href="images/favicon/apple-icon-167x167.png">
 <!-- Others -->
 <link rel="shortcut icon" href="favicon.ico" type="image/x-icon">
 <!-- Manifest.json  -->
 <link rel="manifest" href="manifest.webmanifest">
""")
    if use_dark_mode:
        glf.write(' <!-- Q.Industrialist -->\n')
        glf.write(f' <link rel="stylesheet" href="{__get_file_src("render_stylesheet_dark.css")}">')
    glf.write("""
</head>
<body>
""")
    if header_name is None:
        glf.write(' <title>Q.Industrialist</title>\n')
    else:
        glf.write(' <div class="page-header"><h1>Q.Industrialist <small>{nm}</small></h1></div>\n'.format(nm=header_name))
    if q_industrialist_settings.g_use_filesystem_resources:
        glf.write(
            ' <script src="{jq_js}"></script>\n'
            ' <script src="{bs_js}"></script>\n'.
            format(jq_js=__g_jquery_js_local, bs_js=__g_bootstrap_js_local))
    else:
        glf.write(
            ' <script src="{jq_js}"></script>\n'
            ' <script src="{bs_js}"></script>\n'.
            format(jq_js=__g_jquery_js_external, bs_js=__g_bootstrap_js_external))


def __dump_footer(glf, show_generated_datetime=True):
    if show_generated_datetime:
        glf.write('<p style="font-size:85%;"><small>Generated {dt}</small></p>\n'.format(dt=__get_render_datetime()))
    # Don't remove line below !
    glf.write("""
<p style="font-size:85%;">
&copy; 2020 Qandra Si &middot; <a class="inert" href="https://github.com/Qandra-Si/q.industrialist">GitHub</a> &middot; Data provided by <a class="inert" href="https://esi.evetech.net/">ESI</a> and <a class="inert" href="https://zkillboard.com/">zKillboard</a> &middot; Tips go to <a class="inert" href="https://zkillboard.com/character/2116129465/">Qandra Si</a>
</p>
<p style="line-height:1;font-size:75%;">
EVE Online and the EVE logo are the registered trademarks of CCP hf. All rights are reserved worldwide. All other trademarks are the property of their respective owners. EVE Online, the EVE logo, EVE and all associated logos and designs are the intellectual property of CCP hf. All artwork, screenshots, characters, vehicles, storylines, world facts or other recognizable features of the intellectual property relating to these trademarks are likewise the intellectual property of CCP hf.
</p>
""")
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


def __dump_sde_type_ids_to_js(glf, sde_type_ids):
    type_id_keys = sde_type_ids.keys()
    sorted_type_id_keys = sorted(type_id_keys, key=lambda x: int(x))
    glf.write('<script>\n'
              'var g_sde_max_type_id={max};\n'
              'var g_sde_type_len={len};\n'
              'var g_sde_type_ids=['.format(max=sorted_type_id_keys[-1], len=len(sorted_type_id_keys)))
    for (idx, type_id) in enumerate(sorted_type_id_keys):
        # экранируем " (двойные кавычки), т.к. они встречаются реже, чем ' (одинарные кавычки)
        glf.write('{end}[{id},"{nm}"]'.format(
            id=type_id,
            nm=sde_type_ids[str(type_id)]["name"]["en"].replace('"', '\\\"'),
            end=',' if idx else "\n"))
    glf.write("""
];
function getSdeItemName(t) {
 if ((t < 0) || (t > g_sde_max_type_id)) return null;
 for (var i=0; i<g_sde_type_len; ++i) {
  var ti = g_sde_type_ids[i][0];
  if (t == ti) return g_sde_type_ids[i][1];
  if (ti >= g_sde_max_type_id) break;
 }
 return null;
}
</script>
""")


def __get_converted_fit_status(fit, available_attr: str):
    if not available_attr:
        return "default"
    ship_dict = fit["ship"]
    ship_name = ship_dict["name"] if not (ship_dict is None) else None
    ship_type_id = ship_dict["type_id"] if not (ship_dict is None) and ("type_id" in ship_dict) else None
    total_quantity: int = int(fit["quantity"])
    # ---
    if ship_type_id and ship_name:
        available: int = int(ship_dict[available_attr])
        if available < total_quantity:
            return "warning" if available > 0 else "danger"
    # ---
    something_not_available: bool = False
    for item_dict in fit["items"]:
        available: int = int(item_dict[available_attr])
        if available == 0:
            return "danger"
        elif something_not_available:
            continue
        quantity: int = int(item_dict["quantity"])
        if available < (total_quantity * quantity):
            something_not_available = True
    return "warning" if something_not_available else "success"


def __get_possible_fit_assembles(fit, available_attr: str):
    if not available_attr:
        return None
    possible_assembles = None  # min, max
    ship_dict = fit["ship"]
    # ---
    ship_name = ship_dict["name"] if not (ship_dict is None) else None
    ship_type_id = ship_dict["type_id"] if not (ship_dict is None) and ("type_id" in ship_dict) else None
    # total_quantity: int = int(fit["quantity"])
    # ---
    if ship_type_id and ship_name:
        available: int = int(ship_dict[available_attr])
        if available == 0:
            return 0
        possible_assembles = available
    # ---
    for item_dict in fit["items"]:
        available: int = int(item_dict[available_attr])
        if available == 0:
            return 0
        quantity: int = int(item_dict["quantity"])
        possible = divmod(available, quantity)
        if possible_assembles is None:
            possible_assembles = possible[0]
        elif possible[0] < possible_assembles:
            possible_assembles = possible[0]
    return possible_assembles


def __dump_converted_fits_items(
        glf,
        fit,
        num_id: int,
        fit_keyword: str,
        available_attr: str):
    __ship = fit["ship"]
    __ship_name = __ship["name"] if not (__ship is None) else None
    __ship_type_id = __ship["type_id"] if not (__ship is None) and ("type_id" in __ship) else None
    __fit_comment = fit["comment"]
    __eft = fit["eft"]
    __total_quantity = fit["quantity"]
    __fit_items = fit["items"]
    __problems = fit["problems"]
    # вывод информации о корабле, а также формирование элементов пользовательского интерфейса
    if (__ship_name is None) or (__ship_type_id is None):
        glf.write(
            '<div class="media">\n'
            ' <div class="media-left"></div>\n'
            ' <div class="media-body">\n'
            '  <div class="row">\n'
            '   <div class="col-md-6">\n'
            '    <button type="button" class="btn btn-default btn-xs qind-btn-t2" {fitk}="{num}">{gly1}&nbsp;<span>T2</span></button>\n'
            '    <button type="button" class="btn btn-default btn-xs qind-btn-eft" data-toggle="modal"'
            '     data-target="#modalEFT{num}">{gly2}&nbsp;EFT</button>\n'
            '   </div>\n'
            '  </div>\n'
            ' </div>\n'
            '</div>\n'.
            format(fitk=fit_keyword, num=num_id, gly1=get_span_glyphicon("eye-close"), gly2=get_span_glyphicon("th-list"))
        )
    else:
        __available_txt = ""
        if available_attr:
            __available_txt = \
                '<strong><span class="text-{cls}">{q:,d}</span></strong>&nbsp;/&nbsp;'.\
                format(
                    q=__ship[available_attr],
                    cls="success" if (__ship[available_attr] >= __total_quantity) else "warning"
                )
        glf.write(
            '<div class="media">\n'
            ' <div class="media-left"><img class="media-object icn32" src="{src}"></div>\n'
            ' <div class="media-body">\n'
            '  <h4 class="media-heading">{aq}{q}x {nm}</h4>\n'
            '  <div class="row">\n'
            '   <div class="col-md-6">\n'
            '    <button type="button" class="btn btn-default btn-xs qind-btn-t2" {fitk}="{num}">{gly1}&nbsp;<span>T2</span></button>\n'
            '    <button type="button" class="btn btn-default btn-xs qind-btn-eft" data-toggle="modal"'
            '     data-target="#modalEFT{num}">{gly2}&nbsp;EFT</button>\n'
            '   </div>\n'
            '  </div>\n'
            ' </div>\n'
            '</div>\n'.
            format(
                fitk=fit_keyword,
                num=num_id,
                nm=__ship_name,
                src=__get_img_src(__ship_type_id if not (__ship_type_id is None) else 0, 32),
                aq=__available_txt,
                q=__total_quantity,
                gly1=get_span_glyphicon("eye-close"),
                gly2=get_span_glyphicon("th-list"),
            )
        )
    # добавление окна, в котором можно просматривать и копировать EFT
    __dump_any_into_modal_header_wo_button(
        glf,
        '<strong>{q}x {nm}</strong>{cmnt}'.format(
            q=__total_quantity,
            nm=__ship_name,
            cmnt=', &nbsp<small>{}</small>'.format(__fit_comment) if not (__fit_comment is None) and __fit_comment else ""
        ),
        'EFT{num}'.format(num=num_id),  # modal добавляется автоматически
        None)  # 'modal-sm')
    # формируем содержимое модального диалога
    glf.write(
        '<textarea onclick="this.select();" class="fitting col-md-12" rows="15" style="resize:none"'
        ' readonly="readonly">{eft}</textarea>'.
        format(eft=__eft)
    )
    # закрываем footer модального диалога
    __dump_any_into_modal_footer(glf)
    # вывод таблицы  item-ов фита
    glf.write(
        '<div class="table-responsive">\n'
        ' <table id="qind-{fitk}{num}" class="table table-condensed qind-fit-table">\n'.
        format(fitk=fit_keyword, num=num_id)
    )
    # сначала показываем список проблем, он всегда будет наверху
    for __problem_dict in __problems:
        __name = __problem_dict["name"]
        __quantity = __problem_dict["quantity"]
        __problem = __problem_dict["problem"]
        __is_blueprint_copy = __problem_dict["is_blueprint_copy"] if "is_blueprint_copy" in __problem_dict else None
        __available_txt = ""
        if available_attr:
            __available_txt = \
                '<strong><span class="text-{cls}">{q:,d}</span></strong>&nbsp;/&nbsp;'.\
                format(
                    q=__problem_dict[available_attr],
                    cls="success" if (__problem_dict[available_attr] >= (__total_quantity*__quantity)) else "warning"
                )
        glf.write(
            '<tr class="qind-prblm-{fitk}{num} danger">'
            '<td></td>'
            '<td><strong>{q}x</strong> {nm}{copy} <span class="label label-danger">{prblm}</span></td>'
            '<td align="right">{aq}{tq:,d}</td>'
            '</tr>\n'.
            format(
                num=num_id,
                fitk=fit_keyword,
                q=__quantity,
                nm=__name,
                copy='&nbsp;(Copy)' if not (__is_blueprint_copy is None) and bool(__is_blueprint_copy) else "",
                prblm=__problem,
                aq=__available_txt,
                tq=__total_quantity * __quantity
            )
        )
    # следом за проблемами показываем список модулей фита
    for __item_dict in __fit_items:
        __name = __item_dict["name"]
        __type_id = __item_dict["type_id"]
        __quantity = __item_dict["quantity"]
        __details = __item_dict["details"]
        __is_blueprint_copy = __item_dict["is_blueprint_copy"] if "is_blueprint_copy" in __item_dict else None
        __renamed = __item_dict["renamed"] if "renamed" in __item_dict else None
        __available_txt = ""
        if available_attr:
            __available_txt = \
                '<strong><span class="text-{cls}">{q:,d}</span></strong>&nbsp;/&nbsp;'.\
                format(
                    q=__item_dict[available_attr],
                    cls="success" if (__item_dict[available_attr] >= (__total_quantity*__quantity)) else "warning"
                )
        glf.write(
            '<tr{nont2}>'
            '<td><img class="media-object icn16" src="{img}"></td>'
            '<td><strong>{q}x</strong> {nm}{copy}{renamed}</td>'
            '<td align="right">{aq}{tq:,d}</td>'
            '</tr>\n'.
            format(
                nm=__name,
                copy='&nbsp;(Copy)' if not (__is_blueprint_copy is None) and bool(__is_blueprint_copy) else "",
                renamed=' <span class="label label-warning">renamed</span>' if not (__renamed is None) and bool(__renamed) else "",
                img=__get_img_src(__type_id, 32),
                q=__quantity,
                aq=__available_txt,
                tq=__total_quantity*__quantity,
                nont2="" if ("metaGroupID" in __details) and (__details["metaGroupID"] == 2) else
                      ' class="qind-nont2-{fitk}{num} hidden"'.format(fitk=fit_keyword, num=num_id)
            )
        )
    glf.write("""
</table>
</div>
""")


# вывод сворачиваемых панелей со списком фитов, полученных как результат работы
# метода eve_sde_tools.get_items_list_from_eft, в каждый из dict-ов должно быть добавлено
# поле quantity, как кол-во fit-ов (счётчик, отображаемый в виде badge), а список
# item-ов рекомендуется отсортировать по полю name (в случае необходимости конечно);
# параметр collapse_pn_types является либо None, либо массивом из двух элементов, где
# первый элемент - ключ элемента списка, а второй - словарь возможных значений такого
# элемента, которые задают стили сворачиваемых панелей, например:
# ("conveyor", {"False": "qind-job-schdld", "True": "qind-job-cnveyr"});
# мультиплексор row_num_multiplexer позволяет уникально проиндексировать фиты по их номерам;
# параметр fit_keyword позволяет задать названия html-классов для идентификации
# сгенерированных таблиц с фитами;
# название available_attr задаёт имя параметра, которое использутся для полученыя
# сведений о кол-ве доступных элементов для фита (available опционально)
def __dump_converted_fits(
        glf,
        converted_fits,
        converted_fits_name: str,
        collapse_pn_name: str,
        collapse_pn_types=None,
        row_num_multiplexer: int = 0,
        fit_keyword: str = "fit",
        available_attr: str = None):
    glf.write('<!--start {nm}-->'
              '<div class="panel-group" id="{nm}" role="tablist" aria-multiselectable="true">'.
              format(nm=converted_fits_name))

    row_num = row_num_multiplexer
    for fit in converted_fits:
        row_num += 1
        __ship = fit["ship"]
        __ship_name = fit["ship"]["name"] if not (fit["ship"] is None) else None
        __fit_comment = fit["comment"]
        __eft = fit["eft"]
        __total_quantity = fit["quantity"]
        __items = fit["items"]
        __problems = fit["problems"]
        if collapse_pn_types:
            __pn_flag_name: str = collapse_pn_types[0]
            __pn_flag_val: str = str(fit.get(__pn_flag_name))
            __pn_flag_type: str = collapse_pn_types[1].get(__pn_flag_val)
        else:
            __pn_flag_type = None
        __warnings = len([i for i in __items if "renamed" in i])
        __fit_status = __get_converted_fit_status(fit, available_attr)
        __fit_possible_assembles = __get_possible_fit_assembles(fit, available_attr)
        # создаём сворачиваемую панель для работы с содержимым фита
        glf.write(
            '<div class="panel panel-{status} {pnclass}">\n'
            ' <div class="panel-heading" role="tab" id="{prfxcllps}_hd{num}">\n'
            '  <h4 class="panel-title">\n'
            '   <a role="button" data-toggle="collapse"'  # отключение автосворачивания: data-parent="#monthly_jobs"
            '    href="#{prfxcllps}_collapse{num}" aria-expanded="true"'
            '    aria-controls="{prfxcllps}_collapse{num}"><strong>{nm}</strong>&nbsp;<span'
            '    class="badge">{fpass}{q}</span>{wrngs}{prblms}</a>\n'
            '  </h4>\n'
            '  {cmnt}\n'
            ' </div>\n'
            ' <div id="{prfxcllps}_collapse{num}" class="panel-collapse collapse{vsbl}"'
            '  role="tabpanel" aria-labelledby="{prfxcllps}_hd{num}">\n'
            '  <div class="panel-body">\n'.
            format(
                status=__fit_status,
                num=row_num,
                prfxcllps=collapse_pn_name,
                nm=__ship_name if not (__ship_name is None) and __ship_name else 'Fit #{}'.format(row_num),
                cmnt='<small>{}</small>'.format(__fit_comment) if not (__fit_comment is None) and __fit_comment else "",
                q=__total_quantity,
                vsbl="",  # свёрнуты все по умолчанию: " in" if row_num == 1 else "",
                wrngs="" if __warnings == 0 else '&nbsp;<span class="label label-warning">warnings</span>',
                prblms="" if len(__problems) == 0 else '&nbsp;<span class="label label-danger">problems</span>',
                pnclass=__pn_flag_type if __pn_flag_type else '',
                fpass="" if __fit_possible_assembles is None else '{} of '.format(__fit_possible_assembles),
            )
        )
        # выводим элементы управления фитом и его содержимое
        __dump_converted_fits_items(glf, fit, row_num, fit_keyword, available_attr)
        # закрываем сворачиваемую панель
        glf.write(
            '  </div>\n'  # panel-body
            ' </div>\n'  # panel-collapse
            '</div>\n'  # panel
        )

    glf.write('</div>'
              '<!--end {nm}-->'.
              format(nm=converted_fits_name))


def __dump_converted_fits_script(glf, fit_keyword="fit"):
    glf.write(
        "  // T2 -> All -> T2...\n"
        "  function setupT2ButtonAndTable(t2_only, {fitk}, img, txt) {{\n"
        "    if (t2_only == 1) {{\n"
        "      img.removeClass('glyphicon-eye-open');\n"
        "      img.addClass('glyphicon-eye-close');\n"
        "      txt.html('T2');\n"
        "      $('tr.qind-nont2-{fitk}'+{fitk}).each(function() {{ $(this).addClass('hidden'); }})\n"
        "    }} else {{\n"
        "      img.addClass('glyphicon-eye-open');\n"
        "      img.removeClass('glyphicon-eye-close');\n"
        "      txt.html('All');\n"
        "      $('tr.qind-nont2-{fitk}'+{fitk}).each(function() {{ $(this).removeClass('hidden'); }})\n"
        "    }}\n"
        "  }}\n"
        "  function refreshT2ButtonsAndTables() {{\n"
        "    $('button.qind-btn-t2').each(function() {{\n"
        "      var img = $(this).find('span').eq(0);\n"
        "      var txt = $(this).find('span').eq(1);\n"
        "      var t2_only = (txt.html() == 'T2') ? 1 : 0;\n"
        "      var {fitk} = $(this).attr('{fitk}');\n"
        "      setupT2ButtonAndTable(t2_only, {fitk}, img, txt);\n"
        "    }})\n"
        "  }}\n"
        "  function resetT2ButtonsAndTables(t2_only) {{\n"
        "    $('button.qind-btn-t2').each(function() {{\n"
        "      var img = $(this).find('span').eq(0);\n"
        "      var txt = $(this).find('span').eq(1);\n"
        "      var {fitk} = $(this).attr('{fitk}');\n"
        "      setupT2ButtonAndTable(t2_only, {fitk}, img, txt);\n"
        "    }})\n"
        "  }}\n"
        "  $(document).ready(function(){{\n"
        "    $('button.qind-btn-t2').each(function() {{\n"
        "        $(this).on('click', function () {{\n"
        "          var img = $(this).find('span').eq(0);\n"
        "          var txt = $(this).find('span').eq(1);\n"
        "          var t2_toggle = (txt.html() == 'T2') ? 0 : 1;\n"
        "          var {fitk} = $(this).attr('{fitk}');\n"
        "          setupT2ButtonAndTable(t2_toggle, {fitk}, img, txt);\n"
        "        }})\n"
        "    }})\n"
        "  }})".
        format(fitk=fit_keyword)
    )
