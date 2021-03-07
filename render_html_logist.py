import math

import render_html
import q_logist_settings


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
""")
        glf.write(
            '<th><img src="{src648}" width="32px" height="32px" alt="Badger"/></th>\n'
            '<th><img src="{src32880}" width="32px" height="32px" alt="Venture"/><img\n'
            ' src="{src1317}" width="32px" height="32px" alt="Expanded Cargohold I"/><img\n'
            ' src="{src31117}" width="32px" height="32px" alt="Small Cargohold Optimization I"/></th>\n'
            '<th><img src="{src52694}" width="32px" height="32px" alt="Industrial Cynosural Field Generator"/></th>\n'
            '<th><img src="{src16273}" width="32px" height="32px" alt="Liquid Ozone"/></th>\n'.
            format(
                src648=render_html.__get_img_src(648,32),
                src32880=render_html.__get_img_src(32880,32),
                src1317=render_html.__get_img_src(1317,32),
                src31117=render_html.__get_img_src(31117,32),
                src52694="https://imageserver.eveonline.com/Type/52694_32.png",  # there are no in IEC: render_html.__get_img_src(52694,32),
                src16273=render_html.__get_img_src(16273,32)
            )
        )
        glf.write("""<th class="nitrogen">Nitrogen</th><th class="hydrogen">Hydrogen</th><th class="oxygen">Oxygen</th><th class="helium">Helium</th>
     </tr>
    </thead>
    <tbody>
""")
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
                    '<tr id="rowCynoRoute{cnn}_{num}" system="{nm}">\n'
                    ' <th scope="row">{num}</th><td>{nm}</td>\n'
                    ' <td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td>\n'
                    '</tr>'.
                    format(num=row_num,
                           cnn=cynonetwork_num,
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
        render_html.__dump_any_into_modal_header(
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
                    ' <td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td>\n'
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
        render_html.__dump_any_into_modal_footer(glf)

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
            else:
                glf.write("      [{rn},'{nm}','{signal}',{ly},0,0,0,0]{comma}\n".
                          format(comma=',' if not last_route else ']',
                                 rn=route_num,
                                 nm=system_name,
                                 signal=__get_route_signalling_type(3),
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
    if (!ls.getItem('Ship')) {
      ls.setItem('Ship', 'Rhea');
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
        render_html.__dump_header(glf, "Cyno Network")
        __dump_corp_cynonetwork(glf, sde_inv_positions, corp_cynonetwork)
        render_html.__dump_footer(glf)
    finally:
        glf.close()
