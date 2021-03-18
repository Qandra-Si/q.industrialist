import render_html
import eve_sde_tools


def __group_blueprints_by_category(blueprints, sde_type_ids, sde_market_groups):
    blueprint_categories = []
    for bp in enumerate(blueprints):
        __product_type_id = bp[1]["product_type_id"]
        __blueprint_name = bp[1]["name"]
        # проверяем список market-груп, которым принадлежит продукт и отбираем
        # базовый как самый информативный
        __market_group_id = eve_sde_tools.get_basis_market_group_by_type_id(
            sde_type_ids,
            sde_market_groups,
            __product_type_id)
        __category_dict = next((bc for bc in blueprint_categories if bc["id"] == __market_group_id), None)
        if __category_dict is None:
            __market_group_name = eve_sde_tools.get_market_group_name_by_id(sde_market_groups, __market_group_id)
            __category_dict = {"id": __market_group_id, "name": __market_group_name, "products": []}
            blueprint_categories.append(__category_dict)
        __category_dict["products"].append({"type_id": __product_type_id, "sort": __blueprint_name, "index": bp[0]})
    # пересортировка всех списков, с тем, чтобы при выводе в отчёт они были по алфавиту
    blueprint_categories.sort(key=lambda bc: bc["name"])
    for bc in blueprint_categories:
        bc["products"].sort(key=lambda bc: bc["sort"])
    return blueprint_categories


def __dump_missing_blueprints(glf, corp_manufacturing_scheduler, sde_type_ids, sde_market_groups):
    missing_blueprints = corp_manufacturing_scheduler["missing_blueprints"]
    blueprint_categories = __group_blueprints_by_category(
        missing_blueprints,
        sde_type_ids,
        sde_market_groups)
    
    glf.write('<table class="table table-condensed" style="padding:1px;font-size:smaller;" id="tblMissngBlprnts"><tbody>\n')
    for __cat_dict in blueprint_categories:
        __products = __cat_dict["products"]
        glf.write('<tr><td class="active text-info" colspan="4"><strong>{nm}</strong></td></tr>\n'.format(nm=__cat_dict["name"]))
        for __product_dict in __products:
            bpc = missing_blueprints[__product_dict["index"]]
            __missing_scheduled = bpc["missing_scheduled_blueprints"]
            __missing_conveyor = bpc["missing_conveyor_blueprints"]
            __availiable = bpc["available_quantity"]
            __scheduled = bpc["scheduled_quantity"]
            __conveyor = bpc["conveyor_quantity"]
            __missing = __missing_scheduled + __missing_conveyor
            glf.write(
                '<tr mcq="{mcq}" msq="{msq}" cq="{cq}" sq="{sq}" aq="{aq}"><!--{id}-->'
                '<td><img class="media-object icn32" src="{img}"></td>'
                '<td><strong>{s}x</strong> {nm}</td>'
                '<td align="right"></td>'
                '<td align="right">{aq}</td>'
                '</tr>\n'.
                format(
                    img=render_html.__get_img_src(bpc["type_id"], 32),
                    nm=bpc["name"],
                    # чертежи могут храниться не только в 6м ангаре: flag='<br/><span class="label label-danger">no blueprints</span>' if "there_are_no_blueprints" in bpc else ""
                    id=bpc["type_id"],
                    mcq=__missing_conveyor,
                    msq=__missing_scheduled,
                    cq=__conveyor,
                    sq=__scheduled,
                    aq=__availiable,
                    s=__scheduled+__conveyor
                )
            )
    glf.write('</tbody></table>\n')


def __dump_overplus_blueprints(glf, corp_manufacturing_scheduler, sde_type_ids, sde_market_groups):
    overplus_blueprints = corp_manufacturing_scheduler["overplus_blueprints"]
    blueprint_categories = __group_blueprints_by_category(
        overplus_blueprints,
        sde_type_ids,
        sde_market_groups)

    glf.write('<table class="table table-condensed" style="padding:1px;font-size:smaller;"><tbody>\n')
    for __cat_dict in blueprint_categories:
        __products = __cat_dict["products"]
        glf.write('<tr><td class="active text-info" colspan="3"><strong>{nm}</strong></td></tr>\n'.format(nm=__cat_dict["name"]))
        for __product_dict in __products:
            bpc = overplus_blueprints[__product_dict["index"]]
            glf.write(
                '<tr><!--{id}-->'
                '<td><img class="media-object icn32" src="{img}"></td>'
                '<td>{nm}{flag}</td>'
                '<td align="right">{q}</td>'
                '</tr>\n'.
                format(
                    img=render_html.__get_img_src(bpc["type_id"], 32),
                    nm=bpc["name"],
                    id=bpc["type_id"],
                    q=bpc["unnecessary_quantity"],
                    flag='<br/><span class="label label-primary">all of them</span>' if "all_of_them" in bpc else ""
                )
            )
    glf.write('</tbody></table>\n')


def __dump_workflow_tools(
        glf,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_market_groups,
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
       <li><a id="btnToggleShowBPCConver" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowBPCConver"></span> Show Conveyor</a></li>
       <li><a id="btnToggleShowBPCSchdld" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowBPCSchdld"></span> Show Scheduled</a></li>
       <li><a id="btnToggleLegend" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowLegend"></span> Show Legend</a></li>
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
""")

    # кол-во блюпринтов в имуществе корпорации не должно быть больше 25'000
    __loaded_blueprints_quantity = corp_manufacturing_scheduler["loaded_blueprints"]
    __loaded_factor = (__loaded_blueprints_quantity / 25000.0) * 100.0
    glf.write(
        '<div class="progress" style="margin-bottom:0px">'
        ' <div class="progress-bar progress-bar-{prcnt100}" role="progressbar" aria-valuenow="{prcnt}" aria-valuemin="0" aria-valuemax="100" style="width: {prcnt}%;">Capacity: {fprcnt:.1f}%</div>'
        '</div>'.
        format(prcnt100="danger" if __loaded_blueprints_quantity >= 24000 else ("warning" if __loaded_blueprints_quantity >= 23000 else "info"),
               prcnt=int(__loaded_factor),
               fprcnt=__loaded_factor,))

    glf.write("""
 <div class="row">
  <!--start group1-->
  <div class="col-md-4">
   <h3>Monthly Scheduled Jobs</h3>
""")

    render_html.__dump_converted_fits(
        glf,
        corp_manufacturing_scheduler["monthly_jobs"],
        "monthly_jobs",  # наименование группы сворачиваемых панелей
        "monthjob",  # профикс названий сворачиваемых панелей
        collapse_pn_types=("conveyor", {"False": "qind-job-schdld", "True": "qind-job-cnveyr"}),
        row_num_multiplexer=0,
        fit_keyword="job",
        available_attr=None
    )

    glf.write("""
  </div>
  <!--end group1-->
  <!--start group1-->
  <div class="col-md-4">
   <h3>Missing Blueprints</h3>
""")

    __dump_missing_blueprints(
        glf,
        corp_manufacturing_scheduler,
        sde_type_ids,
        sde_market_groups)

    glf.write("""
  </div>
  <!--end group1-->
  <!--start group1-->
  <div class="col-md-4">
   <h3>Overplus Blueprints</h3>
""")

    __dump_overplus_blueprints(
        glf,
        corp_manufacturing_scheduler,
        sde_type_ids,
        sde_market_groups)

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
    setupOptionDefaultValue('Show T2 Only', 1);
    setupOptionDefaultValue('Show Conveyor', 0);
    setupOptionDefaultValue('Show Scheduled', 1);
    setupOptionDefaultValue('Show Legend', 1);
  }
""")
    render_html.__dump_converted_fits_script(glf, "job")
    glf.write("""
  // Missing Blueprints Row Color
  function toggleRowColor(tr,clr) { // 1-danger;2-muted;3-warning
    if (clr==1) {
      tr.addClass('danger');
      tr.removeClass('text-muted');
      tr.removeClass('warning');
    } else if (clr==2) {
      tr.removeClass('danger');
      tr.addClass('text-muted');
      tr.removeClass('warning');
    } else {
      tr.removeClass('danger');
      tr.removeClass('text-muted');
      tr.addClass('warning');
    }
  }
  // Missing Blueprints Visibility
  function rebuildMissingBlueprints() {
    var cnveyr = ls.getItem('Show Conveyor');
    var schdld = ls.getItem('Show Scheduled');
    var tbody = $('#tblMissngBlprnts').find('tbody');
    var rows = tbody.children('tr');
    rows.each( function(idx) {
      var tr = $(this);
      var td1s = tr.find('td').eq(1);
      var td2 = tr.find('td').eq(2);
      var td3 = tr.find('td').eq(3);
      if (!(td2 === undefined)) {
        var mcq = tr.attr('mcq'); // missing conveyor quantity
        if (!(mcq === undefined)) {
          var msq = tr.attr('msq'); // missing scheduled quantity
          var cq = tr.attr('cq'); // conveyor quantity
          var sq = tr.attr('sq'); // conveyor quantity
          var aq = tr.attr('aq'); // available quantity
          var mq = -1; // missing quantity
          if (cnveyr==1 && schdld==1) {
            td2.html(mcq+'/<strong>'+msq+'</strong>');
            //var all = Number(cq) + Number(sq);
            //td1s.find('strong').html(all+'x');
            tr.removeClass('hidden');
            mq = Number(mcq) + Number(msq);
          }
          else if (cnveyr==1) {
            if (cq==0)
              tr.addClass('hidden');
            else {
              td2.html(mcq);
              //td1s.find('strong').html(cq+'x');
              tr.removeClass('hidden');
              mq = mcq;
            }
          }
          else if (schdld==1) {
            if (sq==0)
              tr.addClass('hidden');
            else {
              td2.html('<strong>'+msq+'</strong>');
              //td1s.find('strong').html(sq+'x');
              tr.removeClass('hidden');
              mq = msq;
            }
          }
          else
            tr.addClass('hidden');
          if (mq!=-1) {
            if (aq==0)
              toggleRowColor(tr,1);
            else if (mq==0)
              toggleRowColor(tr,2);
            else
              toggleRowColor(tr,3);
          }
        }
      }
    });
  } 
  // Workflow Options storage (rebuild menu components)
  function rebuildOptionsMenu() {
    makeVisibleByOption('Show T2 Only', '#imgShowT2Only');
    makeVisibleByOption('Show Conveyor', '#imgShowBPCConver');
    makeVisibleByOption('Show Scheduled', '#imgShowBPCSchdld');
    makeVisibleByOption('Show Legend', '#imgShowLegend');
  }
  // Workflow Options storage (rebuild body components)
  function rebuildBody() {
    makeVisibleByOption('Show Legend', '#legend-block');
    refreshT2ButtonsAndTables();
    makeVisibleByOption('Show Conveyor', 'div.qind-job-cnveyr');
    makeVisibleByOption('Show Scheduled', 'div.qind-job-schdld');
    rebuildMissingBlueprints();
  }
  // Workflow Options menu and submenu setup
  $(document).ready(function(){
    $('#btnToggleShowT2Only').on('click', function () {
      t2_toggle = toggleOptionValue('Show T2 Only');
      resetT2ButtonsAndTables(t2_toggle);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleShowBPCConver').on('click', function () {
      toggleOptionValue('Show Conveyor');
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleShowBPCSchdld').on('click', function () {
      toggleOptionValue('Show Scheduled');
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleLegend').on('click', function () {
      toggleOptionValue('Show Legend');
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


def dump_workflow_into_report(
        # путь, где будет сохранён отчёт
        ws_dir,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_market_groups,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_manufacturing_scheduler):
    glf = open('{dir}/workflow.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(glf, "Workflow")
        __dump_workflow_tools(
            glf,
            sde_type_ids,
            sde_market_groups,
            corp_manufacturing_scheduler
        )
        render_html.__dump_footer(glf)
    finally:
        glf.close()
