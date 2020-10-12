import render_html


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


def __dump_fit_items(glf, job, job_id):
    __ship = job["ship"]
    __ship_name = job["ship"]["name"] if not (job["ship"] is None) else None
    __fit_comment = job["comment"]
    __eft = job["eft"]
    __total_quantity = job["quantity"]
    __fit_items = job["items"]
    __problems = job["problems"]
    # вывод информации о корабле, а также формирование элементов пользовательского интерфейса
    glf.write(
        '<div class="media">\n'
        ' <div class="media-left"><img class="media-object icn32" src="{src}"></div>\n'
        ' <div class="media-body">\n'
        '  <h4 class="media-heading">{q}x {nm}</h4>\n'
        '  <div class="row">\n'
        '   <div class="col-md-6">\n'
        '    <button type="button" class="btn btn-default btn-xs qind-btn-t2" job="{job}"><span'
        '     class="glyphicon glyphicon-eye-close" aria-hidden="true"></span>&nbsp;<span>T2</span></button>\n'
        '    <button type="button" class="btn btn-default btn-xs qind-btn-eft" data-toggle="modal"'
        '     data-target="#modalEFT{job}"><span class="glyphicon glyphicon-th-list"'
        '     aria-hidden="true"></span>&nbsp;EFT</button>\n'
        '   </div>\n'
        '  </div>\n'
        ' </div>\n'
        '</div>\n'.
        format(
            job=job_id,
            nm=__ship_name,
            src=render_html.__get_img_src(job["ship"]["type_id"], 32),
            q=__total_quantity
        )
    )
    # добавление окна, в котором можно просматривать и копировать EFT
    render_html.__dump_any_into_modal_header_wo_button(
        glf,
        '<strong>{q}x {nm}</strong>{cmnt}'.format(
            q=__total_quantity,
            nm=__ship_name,
            cmnt=', &nbsp<small>{}</small>'.format(__fit_comment) if not (__fit_comment is None) and __fit_comment else ""
        ),
        'EFT{job}'.format(job=job_id),  # modal добавляется автоматически
        None)  # 'modal-sm')
    # формируем содержимое модального диалога
    glf.write(
        '<textarea onclick="this.select();" class="fitting col-md-12" rows="15" style="resize:none"'
        ' readonly="readonly">{eft}</textarea>'.
        format(eft=__eft)
    )
    # закрываем footer модального диалога
    render_html.__dump_any_into_modal_footer(glf)
    # вывод таблицы  item-ов фита
    glf.write(
        '<div class="table-responsive">\n'
        ' <table id="qind-job{num}" class="table table-condensed qind-fit-table">\n'.
        format(num=job_id)
    )
    # сначала показываем список проблем, он всегда будет наверху
    for __problem_dict in __problems:
        __name = __problem_dict["name"]
        __quantity = __problem_dict["quantity"]
        __problem = __problem_dict["problem"]
        __is_blueprint_copy = __problem_dict["is_blueprint_copy"] if "is_blueprint_copy" in __problem_dict else None
        glf.write(
            '<tr class="qind-prblm-job{job} danger">'
            '<td></td>'
            '<td><strong>{q}x</strong> {nm}{copy} <span class="label label-danger">{prblm}</span></td>'
            '<td align="right">{tq:,d}</td>'
            '</tr>\n'.
            format(
                job=job_id,
                q=__quantity,
                nm=__name,
                copy='&nbsp;(Copy)' if not (__is_blueprint_copy is None) and bool(__is_blueprint_copy) else "",
                prblm=__problem,
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
        glf.write(
            '<tr{nont2}>'
            '<td><img class="media-object icn16" src="{img}"></td>'
            '<td><strong>{q}x</strong> {nm}{copy}{renamed}</td>'
            '<td align="right">{tq:,d}</td>'
            '</tr>\n'.
            format(
                nm=__name,
                copy='&nbsp;(Copy)' if not (__is_blueprint_copy is None) and bool(__is_blueprint_copy) else "",
                renamed=' <span class="label label-warning">renamed</span>' if not (__renamed is None) and bool(__renamed) else "",
                img=render_html.__get_img_src(__type_id, 32),
                q=__quantity,
                tq=__total_quantity*__quantity,
                nont2="" if ("metaGroupID" in __details) and (__details["metaGroupID"] == 2) else
                      ' class="qind-nont2-job{} hidden"'.format(job_id)
            )
        )
    glf.write("""
</table>
</div>
""")


def __dump_monthly_jobs(glf, corp_manufacturing_scheduler):
    monthly_jobs = corp_manufacturing_scheduler["monthly_jobs"]

    glf.write("""
<!--start monthly_jobs-->
<div class="panel-group" id="monthly_jobs" role="tablist" aria-multiselectable="true">
""")

    row_num = 0
    for job in monthly_jobs:
        row_num += 1
        __ship = job["ship"]
        __ship_name = job["ship"]["name"] if not (job["ship"] is None) else None
        __fit_comment = job["comment"]
        __eft = job["eft"]
        __total_quantity = job["quantity"]
        __items = job["items"]
        __problems = job["problems"]
        __warnings = len([i for i in __items if "renamed" in i])
        # создаём сворачиваемую панель для работы с содержимым фита
        glf.write(
            '<div class="panel panel-default">\n'
            ' <div class="panel-heading" role="tab" id="monthjob_hd{num}">\n'
            '  <h4 class="panel-title">\n'
            '   <a role="button" data-toggle="collapse"'  # отключение автосворачивания: data-parent="#monthly_jobs"
            '    href="#monthjob_collapse{num}" aria-expanded="true"'
            '    aria-controls="monthjob_collapse{num}"><strong>{nm}</strong>&nbsp;<span'
            '    class="badge">{q}</span>{wrngs}{prblms}</a>\n'
            '  </h4>\n'
            '  {cmnt}\n'
            ' </div>\n'
            ' <div id="monthjob_collapse{num}" class="panel-collapse collapse{vsbl}"'
            '  role="tabpanel" aria-labelledby="monthjob_hd{num}">\n'
            '  <div class="panel-body">\n'.
            format(
                num=row_num,
                nm=__ship_name if not (__ship_name is None) and __ship_name else 'Fit #{}'.format(row_num),
                cmnt='<small>{}</small>'.format(__fit_comment) if not (__fit_comment is None) and __fit_comment else "",
                q=__total_quantity,
                vsbl="",  # свёрнуты все по умолчанию: " in" if row_num == 1 else "",
                wrngs="" if __warnings == 0 else '&nbsp;<span class="label label-warning">warnings</span>',
                prblms="" if len(__problems) == 0 else '&nbsp;<span class="label label-danger">problems</span>'
            )
        )
        # выводим элементы управления фитом и его содержимое
        __dump_fit_items(glf, job, row_num)
        # закрываем сворачиваемую панель
        glf.write(
            '  </div>\n'  # panel-body
            ' </div>\n'  # panel-collapse
            '</div>\n'  # panel
        )

    # только для отладки !!!!!
    # scheduled_blueprints = corp_manufacturing_scheduler["scheduled_blueprints"]
    # glf.write('<table class="table table-condensed" style="padding:1px;font-size:smaller;">')
    # scheduled_blueprints.sort(key=lambda sb: sb["product"]["name"])
    # for bpc in scheduled_blueprints:
    #     glf.write(
    #         '<tr>'
    #         '<td><img class="media-object icn32" src="{img}"></td>'
    #         '<td>{nm} <span class="label label-default">{id}</span></td>'
    #         '<td align="right">{q}</td>'
    #         '</tr>\n'.
    #         format(
    #             img=render_html.__get_img_src(bpc["type_id"], 32),
    #             nm=bpc["product"]["name"],
    #             id=bpc["type_id"],
    #             q=bpc["product"]["scheduled_quantity"]
    #         )
    #     )
    # glf.write('</table>')
    # только для отладки !!!!!

    glf.write("""
</div>
<!--end monthly_jobs-->
""")


def __dump_missing_blueprints(glf, corp_manufacturing_scheduler):
    missing_blueprints = corp_manufacturing_scheduler["missing_blueprints"]
    glf.write('<table class="table table-condensed" style="padding:1px;font-size:smaller;">')
    missing_blueprints.sort(key=lambda mb: mb["name"])
    for bpc in missing_blueprints:
        glf.write(
            '<tr>'
            '<td><img class="media-object icn32" src="{img}"></td>'
            '<td>{nm} <span class="label label-default">{id}</span></td>'
            '<td align="right">{q}</td>'
            '</tr>\n'.
            format(
                img=render_html.__get_img_src(bpc["type_id"], 32),
                nm=bpc["name"],
                id=bpc["type_id"],
                q=bpc["required_quantity"]
            )
        )
    glf.write('</table>')


def __dump_overplus_blueprints(glf, corp_manufacturing_scheduler):
    overplus_blueprints = corp_manufacturing_scheduler["overplus_blueprints"]
    glf.write('<table class="table table-condensed" style="padding:1px;font-size:smaller;">')
    overplus_blueprints.sort(key=lambda mb: mb["name"])
    for bpc in overplus_blueprints:
        glf.write(
            '<tr>'
            '<td><img class="media-object icn32" src="{img}"></td>'
            '<td>{nm} <span class="label label-default">{id}</span></td>'
            '<td align="right">{q}</td>'
            '</tr>\n'.
            format(
                img=render_html.__get_img_src(bpc["type_id"], 32),
                nm=bpc["name"],
                id=bpc["type_id"],
                q=bpc["unnecessary_quantity"]
            )
        )
    glf.write('</table>')


def __dump_workflow_tools(
        glf,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_manufacturing_scheduler):
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
       <li><a id="btnToggleLegend" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowLegend"></span> Show legend</a></li>
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
 <div class="row">
  <!--start group1-->
  <div class="col-md-4">
   <h3>Monthly Scheduled Jobs</h3>
""")

    __dump_monthly_jobs(
        glf,
        corp_manufacturing_scheduler)

    glf.write("""
  </div>
  <!--end group1-->
  <!--start group1-->
  <div class="col-md-4">
   <h3>Missing Blueprints</h3>
""")

    __dump_missing_blueprints(
        glf,
        corp_manufacturing_scheduler)

    glf.write("""
  </div>
  <!--end group1-->
  <!--start group1-->
  <div class="col-md-4">
   <h3>Overplus Blueprints</h3>
""")

    __dump_overplus_blueprints(
        glf,
        corp_manufacturing_scheduler)

    glf.write("""
  </div>
  <!--end group1-->
 </div> <!--row-->

<div id="legend-block">
 <hr>
 <h4>Legend</h4>
 <p>
  <strong>Rorqual</strong>&nbsp;<span class="badge">40</span>&nbsp;<span class="label
  label-warning">warnings</span>&nbsp;<span class="label label-danger">problems</span> - 40x Rorqual ships
  added into the list of monthly jobs, and some problems and warnings detected with items of the Rorqual' fit.
 </p>
 <p>
  <strong>2x</strong> Multispectrum Energized Membrane II <span class="label label-warning">renamed</span> -
  some outdated item found in the fit and converted to a more suitable variant. For example, obsolete
  <em>Energized Adaptive Nano Membrane II</em> could be renamed to <em>Multispectrum Energized Membrane II</em>.
 </p>
 <p>
  <strong>1x</strong> Crimson Cerebral Accelerator <span class="label label-danger">obsolete</span> -
  some unknown or very outdated item found in the fit.</br>
  <strong>3x</strong> Small Gremlin Compact Energy Neutralizer <span class="label label-danger">suppressed</span> -
  some suppressed item found in the fit (the item has already been renamed or is no longer in use, or
  publication discontinued).
 </p>
</div> <!--legend-->
</div> <!--container-fluid-->
""")

    # __dump_sde_type_ids_to_js(glf, sde_type_ids)
    glf.write("""
<script>
  // Workflow Options storage (prepare)
  ls = window.localStorage;

  // Workflow Options storage (init)
  function resetOptionsMenuToDefault() {
    if (!ls.getItem('Show Legend')) {
      ls.setItem('Show Legend', 1);
    }
    if (!ls.getItem('Show T2 Only')) {
      ls.setItem('Show T2 Only', 1);
    }
  }
  // T2 -> All -> T2...
  function setupT2ButtonAndTable(t2_only, job, img, txt) {
    if (t2_only == 1) {
      img.removeClass('glyphicon-eye-open');
      img.addClass('glyphicon-eye-close');
      txt.html('T2');
      $('tr.qind-nont2-job'+job).each(function() { $(this).addClass('hidden'); })    
    } else {
      img.addClass('glyphicon-eye-open');
      img.removeClass('glyphicon-eye-close');
      txt.html('All');
      $('tr.qind-nont2-job'+job).each(function() { $(this).removeClass('hidden'); })    
    }
  }
  function refreshT2ButtonsAndTables() {
    $('button.qind-btn-t2').each(function() {
      var img = $(this).find('span').eq(0);
      var txt = $(this).find('span').eq(1);
      var t2_only = (txt.html() == 'T2') ? 1 : 0;
      var job = $(this).attr('job');
      setupT2ButtonAndTable(t2_only, job, img, txt);
    })
  }
  function resetT2ButtonsAndTables(t2_only) {
    $('button.qind-btn-t2').each(function() {
      var img = $(this).find('span').eq(0);
      var txt = $(this).find('span').eq(1);
      var job = $(this).attr('job');
      setupT2ButtonAndTable(t2_only, job, img, txt);
    })
  }
  // Workflow Options storage (rebuild menu components)
  function rebuildOptionsMenu() {
    show = ls.getItem('Show Legend');
    if (show == 1)
      $('#imgShowLegend').removeClass('hidden');
    else
      $('#imgShowLegend').addClass('hidden');
    t2_only = ls.getItem('Show T2 Only');
    if (t2_only == 1)
      $('#imgShowT2Only').removeClass('hidden');
    else
      $('#imgShowT2Only').addClass('hidden');
  }
  // Worflow Options storage (rebuild body components)
  function rebuildBody() {
    show = ls.getItem('Show Legend');
    if (show == 1)
      $('#legend-block').removeClass('hidden');
    else
      $('#legend-block').addClass('hidden');
    //---
    refreshT2ButtonsAndTables();
  }
  // Workflow Options menu and submenu setup
  $(document).ready(function(){
    $('button.qind-btn-t2').each(function() {
        $(this).on('click', function () {
          var img = $(this).find('span').eq(0);
          var txt = $(this).find('span').eq(1);
          var t2_toggle = (txt.html() == 'T2') ? 0 : 1;
          var job = $(this).attr('job');
          setupT2ButtonAndTable(t2_toggle, job, img, txt);
      })
    })
    $('#btnToggleShowT2Only').on('click', function () {
      t2_toggle = (ls.getItem('Show T2 Only') == 1) ? 0 : 1;
      ls.setItem('Show T2 Only', t2_toggle);
      resetT2ButtonsAndTables(t2_toggle);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleLegend').on('click', function () {
      show = (ls.getItem('Show Legend') == 1) ? 0 : 1;
      ls.setItem('Show Legend', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnResetOptions').on('click', function () {
      ls.clear();
      resetOptionsMenuToDefault();
      rebuildOptionsMenu();
      var t2_only = (ls.getItem('Show T2 Only') == 1) ? 1 : 0;
      resetT2ButtonsAndTables(t2_only);
      rebuildBody();
    });
    // first init
    resetOptionsMenuToDefault();
    rebuildOptionsMenu();
    rebuildBody();
  })
</script>
""")


def dump_workflow_into_report(
        # путь, где будет сохранён отчёт
        ws_dir,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_manufacturing_scheduler):
    glf = open('{dir}/workflow.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(glf, "Workflow")
        __dump_workflow_tools(
            glf,
            sde_type_ids,
            corp_manufacturing_scheduler
        )
        render_html.__dump_footer(glf)
    finally:
        glf.close()
