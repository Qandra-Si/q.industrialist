import render_html


def __get_progress_element(current_num, max_num):
    if max_num == 0:
        __progress_factor: float = 100.0
    else:
        __progress_factor: float = float(100 * current_num / max_num)
    prgrs = \
        '<strong><span class="text-warning">{q:,d}</span></strong> / {sc:,d}<br>' \
        '<div class="progress" style="margin-bottom:0px"><div class="progress-bar{prcnt100}" role="progressbar"' \
        ' aria-valuenow="{prcnt}" aria-valuemin="0" aria-valuemax="100" style="width: {prcnt}%;">{fprcnt:.1f}%</div></div>'. \
        format(
            q=current_num,
            sc=max_num,
            prcnt100=" progress-bar-success" if (__progress_factor > 95.999) and (__progress_factor < 104.999) else (
                " progress-bar-warning" if __progress_factor > 104.999 else ""),
            prcnt=int(__progress_factor) if __progress_factor < 100.001 else 100,
            fprcnt=__progress_factor
        )
    return prgrs


def __dump_regroup_items_table(
        glf,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        regroup_market_groups,
        scheduled_items_in_regroup):
    mrkt_keys = list(dict.fromkeys([v["market"] for v in scheduled_items_in_regroup.values()]))
    mrkt_nms = [{"nm": regroup_market_groups.get(int(g)), "id": g} for g in mrkt_keys]
    mrkt_nms.sort(key=lambda g: g["nm"])

    glf.write('<table class="table">'
              ' <tr>'
              '  <th colspan="2">Components</th><th align="right">Scheduled / Regroup</th>'
              ' </tr>')

    for mrkt in mrkt_nms:
        glf.write('<tr><td class="active" colspan="3"><strong>{nm}</strong></tr>'.format(nm=mrkt["nm"]))
        mrkt_id = mrkt["id"]
        itms = [(i, scheduled_items_in_regroup[int(i)]) for i in scheduled_items_in_regroup]
        itms = [i for i in itms if i[1]["market"] == mrkt_id]
        itms.sort(key=lambda g: g[1]["name"])
        for item_dict in itms:
            type_id = item_dict[0]
            quantity = item_dict[1]["quantity"]
            available = item_dict[1]["available"]
            glf.write('<tr>'
                      ' <td><img class="media-object icn32" src="{img}"></td>'
                      ' <td>{nm}</td>'
                      ' <td align="right">{p}</td>'
                      '</tr>'.
                      format(nm=item_dict[1]["name"],
                             img=render_html.__get_img_src(type_id, 32),
                             p=__get_progress_element(available, quantity)))

    glf.write(' </table>')


def __dump_regroup_stations(
        glf,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_market_groups,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_regroup_stats):
    glf.write("""
<style>
.qind-fit-table {
  font-size: smaller;
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
   <a class="navbar-brand" data-target="#"><span class="glyphicon glyphicon-tasks" aria-hidden="true"></span></a>
  </div>

  <div class="collapse navbar-collapse" id="bs-navbar-collapse">
   <ul class="nav navbar-nav">
    <li class="dropdown">
     <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Display Options <span class="caret"></span></a>
      <ul class="dropdown-menu">
       <li><a id="btnToggleShowT2Only" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowT2Only"></span> Show T2 only</a></li>
       <li role="separator" class="divider"></li>
       <li><a id="btnResetOptions" data-target="#" role="button">Reset options</a></li>
      </ul>
    </li>
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
 <h3>Regroup Stations</h3>
""")

    fit_multiplexer = 0
    for corp_regroup_stat in corp_regroup_stats:
        corporation_name = corp_regroup_stat["corporation_name"]
        glf.write('<h4>{}</h4>'.format(corporation_name))

        for station_dict in corp_regroup_stat["regroup_containers"]:
            station_id = station_dict["station_id"]
            if not (station_id is None):
                regroup_station_dict = corp_regroup_stat["regroup_stocks"].get(int(station_id))
            else:
                regroup_station_dict = None
            station_name = station_dict["station_name"]
            foreign = station_dict.get("station_foreign", False)
            containers = station_dict["containers"]
            stock_hangars = station_dict["stock_hangars"]

            glf.write('<div class="panel panel-default" id="id{id}">\n'  # panel (station)
                      ' <div class="panel-heading">\n'
                      '  <h3 class="panel-title">{nm}{foreign}</h3>\n'
                      ' </div>\n'
                      ' <div class="panel-body">\n'.  # panel-body (station)
                      format(id=station_id,
                             nm=station_name,
                             foreign=' <span class="label label-warning">foreign</span>' if foreign else ""))

            for container_dict in containers:
                container_id = container_dict["id"]
                regroup_container_dict = regroup_station_dict.get(int(container_id)) if not (regroup_station_dict is None) else None
                if not regroup_container_dict:
                    continue
                container_name = container_dict["name"]

                glf.write('<div class="panel panel-default" id="id{id}">\n'  # panel (container)
                          ' <div class="panel-heading">\n'
                          '  <h3 class="panel-title">{nm}</h3>\n'
                          ' </div>\n'
                          ' <div class="panel-body">\n'  # panel-body (container)
                          '  <div class="row">\n'  # row
                          '   <div class="col-md-5">\n'.  # start group1 (fits)
                          format(id=container_id, nm=container_name))

                if regroup_container_dict:
                    render_html.__dump_converted_fits(
                        glf,
                        regroup_container_dict["fits"],
                        'regroup_fits{id}'.format(id=container_id),
                        'rgrpfit{id}'.format(id=container_id),
                        collapse_pn_types=None,
                        row_num_multiplexer=fit_multiplexer,
                        fit_keyword="regroup",
                        available_attr="available"
                    )

                glf.write('   </div>\n'  # end group1 (fits)
                          '   <div class="col-md-7">\n')  # start group1 (stock)

                if regroup_container_dict:
                    __dump_regroup_items_table(
                        glf,
                        corp_regroup_stat["regroup_market_groups"],
                        regroup_container_dict["stock"]
                    )

                glf.write('   </div>\n'  # end group1 (stock)
                          '  </div>\n'  # row
                          ' </div>\n'  # panel-body (container)
                          '</div>\n')  # panel (container)

                fit_multiplexer += 1000

            for hangar_dict in stock_hangars:
                hangar_id = "{}_{}".format(station_id, hangar_dict)
                regroup_hangar_dict = regroup_station_dict.get(hangar_id) if not (regroup_station_dict is None) else None
                if not regroup_hangar_dict:
                    continue
                hangar_name = "Corp Security Access Group {}".format(hangar_dict[-1:])

                glf.write('<div class="panel panel-default" id="id{id}">\n'  # panel (container)
                          ' <div class="panel-heading">\n'
                          '  <h3 class="panel-title">{nm}</h3>\n'
                          ' </div>\n'
                          ' <div class="panel-body">\n'  # panel-body (container)
                          '  <div class="row">\n'  # row
                          '   <div class="col-md-5">\n'.  # start group1 (fits)
                          format(id=hangar_id, nm=hangar_name))

                if regroup_hangar_dict:
                    render_html.__dump_converted_fits(
                        glf,
                        regroup_hangar_dict["fits"],
                        'regroup_fits{id}'.format(id=hangar_id),
                        'rgrpfit{id}'.format(id=hangar_id),
                        collapse_pn_types=None,
                        row_num_multiplexer=fit_multiplexer,
                        fit_keyword="regroup",
                        available_attr="available"
                    )

                glf.write('   </div>\n'  # end group1 (fits)
                          '   <div class="col-md-7">\n')  # start group1 (stock)

                if regroup_hangar_dict:
                    __dump_regroup_items_table(
                        glf,
                        corp_regroup_stat["regroup_market_groups"],
                        regroup_hangar_dict["stock"]
                    )

                glf.write('   </div>\n'  # end group1 (stock)
                          '  </div>\n'  # row
                          ' </div>\n'  # panel-body (container)
                          '</div>\n')  # panel (container)

                fit_multiplexer += 1000

            glf.write(' </div>\n'  # panel-body (station)
                      '</div>\n')  # panel (station)

    glf.write("""
</div> <!--container-fluid-->
""")

    # __dump_sde_type_ids_to_js(glf, sde_type_ids)
    glf.write("""
<script>
  // Workflow Options storage (prepare)
  ls = window.localStorage;
  function setupOptionDefaultValue(ls_name, val) {
    if (!ls.getItem(ls_name))
      ls.setItem(ls_name, val);
  }
  function makeVisibleByOption(ls_name, element_id) {
    show = ls.getItem(ls_name);
    $(element_id).each(function() {
      if (show == 1)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
  }
  function toggleOptionValue(ls_name) {
    toggle = (ls.getItem(ls_name) == 1) ? 0 : 1;
    ls.setItem(ls_name, toggle);
    return toggle;
  }
  // Workflow Options storage (init)
  function resetOptionsMenuToDefault() {
    setupOptionDefaultValue('Show T2 Only', 0);
  }
""")
    render_html.__dump_converted_fits_script(glf, "regroup")
    glf.write("""
  // Workflow Options storage (rebuild menu components)
  function rebuildOptionsMenu() {
    makeVisibleByOption('Show T2 Only', '#imgShowT2Only');
  }
  // Workflow Options storage (rebuild body components)
  function rebuildBody() {
    refreshT2ButtonsAndTables();
  }
  // Workflow Options menu and submenu setup
  $(document).ready(function(){
    $('#btnToggleShowT2Only').on('click', function () {
      t2_toggle = toggleOptionValue('Show T2 Only');
      resetT2ButtonsAndTables(t2_toggle);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnResetOptions').on('click', function () {
      ls.clear();
      resetOptionsMenuToDefault();
      rebuildOptionsMenu();
      resetT2ButtonsAndTables((ls.getItem('Show T2 Only')==1)?1:0);
      rebuildBody();
    });
    // first init
    resetOptionsMenuToDefault();
    rebuildOptionsMenu();
    rebuildBody();
  })
</script>
""")


def dump_regroup_into_report(
        # путь, где будет сохранён отчёт
        ws_dir,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_market_groups,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_regroup_stats):
    glf = open('{dir}/regroup.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(glf, "Regroup")
        __dump_regroup_stations(
            glf,
            sde_type_ids,
            sde_market_groups,
            corp_regroup_stats
        )
        render_html.__dump_footer(glf)
    finally:
        glf.close()
