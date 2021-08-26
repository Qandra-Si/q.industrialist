import render_html


g_month_names = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"]


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
            prcnt100=" progress-bar-success" if (__progress_factor > 95.999) and (__progress_factor < 104.999) else (" progress-bar-warning" if __progress_factor > 104.999 else ""),
            prcnt=int(__progress_factor) if __progress_factor < 100.001 else 100,
            fprcnt=__progress_factor
        )
    return prgrs


def __dump_industry_product(
        glf,
        product,
        current_month,
        sde_type_ids,
        workflow_industry_jobs,
        workflow_last_industry_jobs):
    # распаковка о продукте данных для вывода в отчёт
    __product_type_id = product["type_id"]
    __product_name = product["name"]
    __product_scheduled_quantity = product["quantity"]
    # получение справочной информации о продукте
    __product_dict = sde_type_ids.get(str(__product_type_id), None)
    __product_volume = __product_dict["volume"] if not (__product_dict is None) and ("volume" in __product_dict) else 0
    __products_fee_tax_sum = 0.0
    __products_quantity_sum = 0
    # вычисление статистики производства, формирование отдельных ячеек таблицы
    __td_manufactured = ["", "", ""]
    __td_manufactured_last30days = ""
    __td_cost = ""
    __td_volume = ""
    for month in range(3):
        __wij_month = (current_month - 1 - (2-month) + 12) % 12 + 1
        # получение информации о производстве этого продукта
        __wij_dict = next((wij for wij in workflow_industry_jobs if
                           (wij["ptid"] == __product_type_id) and (wij["month"] == __wij_month)), None)
        if __wij_dict is None:
            continue
        __wij_products = __wij_dict["products"]
        __products_fee_tax_sum += __wij_dict["cost"]
        __products_quantity_sum += __wij_products
        __td_manufactured[month] = __get_progress_element(__wij_products, __product_scheduled_quantity)
    # подсчёт того, что суммируется
    if __products_quantity_sum > 0:
        __td_cost = \
            '{cost:,.1f}<br><mark><span style="font-size: smaller;">{scost:,.2f}</span></mark>'. \
            format(cost=__products_fee_tax_sum, scost=__products_fee_tax_sum / __products_quantity_sum)
        __td_volume = \
            '{volume:,.1f}<br><mark><span style="font-size: smaller;">{svolume:,.2f}</span></mark>'. \
            format(volume=__product_volume * __products_quantity_sum, svolume=__product_volume)
    # получение информации о производстве этого продукта за последние 30 дней
    __wij_dict = next((wij for wij in workflow_last_industry_jobs if (wij["ptid"] == __product_type_id)), None)
    if not (__wij_dict is None):
        __wij_products = __wij_dict["products"]
        __td_manufactured_last30days = __get_progress_element(__wij_products, __product_scheduled_quantity)
    # формирование строки отчёта
    glf.write(
        '<tr><!--{id}-->'
        '<td><img class="icn32" src="{img}" width="32px" height="32px"></td>'
        '<td>{nm}</td>'
        '<td align="right">{mnf0}</td> <td align="right">{mnf1}</td> <td align="right">{mnf2}</td>'
        '<td align="right">{mnf30}</td>'
        '<td align="right" class="qind-td-feetax">{cost}</td>'
        '<td align="right" class="qind-td-volume">{volume}</td>'
        '</tr>\n'.
        format(
            id=__product_type_id,
            img=render_html.__get_img_src(__product_type_id, 32),
            nm=__product_name,
            scheduled=__product_scheduled_quantity,
            mnf0=__td_manufactured[0],
            mnf1=__td_manufactured[1],
            mnf2=__td_manufactured[2],
            mnf30=__td_manufactured_last30days,
            cost=__td_cost,
            volume=__td_volume
        )
    )


def __dump_industry(
        glf,
        sde_type_ids,
        corp_industry_stat):
    conveyor_scheduled_products = corp_industry_stat["conveyor_scheduled_products"]
    workflow_industry_jobs = corp_industry_stat["workflow_industry_jobs"]
    workflow_last_industry_jobs = corp_industry_stat["workflow_last_industry_jobs"]
    current_month = corp_industry_stat["current_month"]
    conveyor_market_groups = corp_industry_stat["conveyor_market_groups"]

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
       <li><a id="btnToggleShowFeeTax" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowFeeTax"></span> Show Fee &amp; Tax</a></li>
       <li><a id="btnToggleShowVolume" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowVolume"></span> Show Volume</a></li>
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
<h3>Scheduled Industry Jobs</h3>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th style="width:32px;" rowspan="2"></th>
  <th rowspan="2">Products</th>
  <th style="text-align: center;" colspan="4">Manufactured / Scheduled<br>Progress of Monthly Jobs</th>
  <th style="text-align: right;" rowspan="2" class="qind-td-feetax">Fee &amp; Tax, ISK</th>
  <th style="text-align: right;" rowspan="2" class="qind-td-volume">Volume, m&sup3;</th>
 </tr>
 <tr>
""")
    glf.write(
        '<th style="text-align: center;">{}</th>'
        '<th style="text-align: center;">{}</th>'
        '<th style="text-align: center;">{}</th>'
        '<th style="text-align: center;">Last 30 days</th>'.
        format(g_month_names[(current_month+9)%12+1],
               g_month_names[(current_month+10)%12+1],
               g_month_names[current_month]))
    glf.write("""
 </tr>
</thead>
<tbody>
""")

    conveyor_scheduled_products.sort(key=lambda p: p["name"])
    conveyor_market_groups = list(conveyor_market_groups.items())
    conveyor_market_groups.sort(key=lambda m: m[1])
    for market in conveyor_market_groups:
        glf.write('<tr><td class="active text-info" colspan="8"><strong>{nm}</strong></td></tr>\n'.format(nm=market[1]))
        __market_group_id = int(market[0])
        for product in conveyor_scheduled_products:
            if product["market"] != __market_group_id:
                continue
            __dump_industry_product(
                glf,
                product,
                current_month,
                sde_type_ids,
                workflow_industry_jobs,
                workflow_last_industry_jobs)

    glf.write("""
</tbody>
</table>
</div> <!--container-fluid-->
""")

    # __dump_sde_type_ids_to_js(glf, sde_type_ids)
    glf.write("""
<script>
  // Industry Options storage (prepare)
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

  // Industry Options storage (init)
  function resetOptionsMenuToDefault() {
    setupOptionDefaultValue('Show FeeTax', 0);
    setupOptionDefaultValue('Show Volume', 0);
    setupOptionDefaultValue('Show Legend', 1);
  }
  // Industry Options storage (rebuild menu components)
  function rebuildOptionsMenu() {
    makeVisibleByOption('Show FeeTax', '#imgShowFeeTax');
    makeVisibleByOption('Show Volume', '#imgShowVolume');
    makeVisibleByOption('Show Legend', '#imgShowLegend');
  }
  // Industry Options storage (rebuild body components)
  function rebuildBody() {
    makeVisibleByOption('Show FeeTax', '.qind-td-feetax');
    makeVisibleByOption('Show Volume', '.qind-td-volume');
    makeVisibleByOption('Show Legend', '#legend-block');
    rebuildMissingBlueprints();
  }
  // Industry Options menu and submenu setup
  $(document).ready(function(){
    $('#btnToggleShowFeeTax').on('click', function () {
      toggleOptionValue('Show FeeTax');
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleShowVolume').on('click', function () {
      toggleOptionValue('Show Volume');
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
      rebuildBody();
    });
    // first init
    resetOptionsMenuToDefault();
    rebuildOptionsMenu();
    rebuildBody();
  })
</script>
""")


def dump_industry_into_report(
        # путь, где будет сохранён отчёт
        ws_dir,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_industry_stat
):
    glf = open('{dir}/industry.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(glf, "Industry")
        __dump_industry(
            glf,
            sde_type_ids,
            corp_industry_stat)
        render_html.__dump_footer(glf)
    finally:
        glf.close()
