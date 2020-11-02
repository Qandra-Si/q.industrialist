import time
import tzlocal
import re
from datetime import datetime

import q_industrialist_settings

__g_local_timezone = tzlocal.get_localzone()
__g_render_datetime = None
__g_pattern_c2s1 = re.compile(r'(.)([A-Z][a-z]+)')
__g_pattern_c2s2 = re.compile(r'([a-z0-9])([A-Z])')


def __camel_to_snake(name):  # https://stackoverflow.com/a/1176023
  name = __g_pattern_c2s1.sub(r'\1_\2', name)
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


def __dump_header(glf, header_name):
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
    glf.write(
        ' <title>{nm} - Q.Industrialist</title>\n'
        ' <link rel="stylesheet" href="{bs_css}">\n'.
        format(
            nm=header_name,
            bs_css='bootstrap/3.4.1/css/bootstrap.min.css' if q_industrialist_settings.g_use_filesystem_resources else 'https://stackpath.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css" integrity="sha384-HSMxcRTRxnN+Bdg0JdbxYKrThecOKuH5zCYotlSAcp1+c8xmyTe9GYg1l9a69psu" crossorigin="anonymous'
        ))
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
</head>
<body>
""")
    glf.write(
        ' <div class="page-header"><h1>Q.Industrialist <small>{nm}</small></h1></div>\n'
        ' <script src="{jq_js}"></script>\n'
        ' <script src="{bs_js}"></script>\n'.
        format(
            nm=header_name,
            jq_js='jquery/jquery-1.12.4.min.js' if q_industrialist_settings.g_use_filesystem_resources else 'https://code.jquery.com/jquery-1.12.4.min.js" integrity="sha384-nvAa0+6Qg9clwYCGGPpDQLVpLNn0fRaROjHqs13t4Ggj3Ez50XnGQqc/r8MhnRDZ" crossorigin="anonymous',
            bs_js='bootstrap/3.4.1/js/bootstrap.min.js' if q_industrialist_settings.g_use_filesystem_resources else 'https://stackpath.bootstrapcdn.com/bootstrap/3.4.1/js/bootstrap.min.js" integrity="sha384-aJ21OjlMXNL5UyIl/XNwTMqvzeRMZH2w8c5cRVpzpU8Y5bApTppSuUkhZXN0VxHd" crossorigin="anonymous'
    ))


def __dump_footer(glf):
    # Don't remove line below !
    glf.write('<p><small><small>Generated {dt}</small></br>\n'.format(dt=__get_render_datetime()))
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


def __dump_sde_type_ids_to_js(glf, sde_type_ids):
    type_id_keys = sde_type_ids.keys()
    sorted_type_id_keys = sorted(type_id_keys, key=lambda x: int(x))
    glf.write('<script>\nvar g_sde_max_type_id={max};\nvar g_sde_type_ids=['.format(max=sorted_type_id_keys[-1]))
    for type_id in sorted_type_id_keys:
        # экранируем " (двойные кавычки), т.к. они встречаются реже, чем ' (одинарные кавычки)
        glf.write('{end}[{id},"{nm}"]'.format(
            id=type_id,
            nm=sde_type_ids[str(type_id)]["name"]["en"].replace('"', '\\\"'),
            end="\n" if type_id == "0" else ","))
    glf.write("""
];
function getSdeItemName(id) {
 if ((id < 0) || (id > g_sde_max_type_id)) return null;
 for (var i=0; i<=g_sde_max_type_id; ++i)
  if (id == g_sde_type_ids[i][0])
   return g_sde_type_ids[i][1];
 return null;
};
</script>
""")
