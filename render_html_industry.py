import render_html


g_month_names = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"]


def __dump_industry_workflow_product(
        glf,
        product,
        current_month,
        sde_type_ids,
        workflow_industry_jobs):
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
    __td_cost = ""
    __td_volume = ""
    for month in range(3):
        __wij_month = (current_month - 2) + month
        # получение информации о производстве этого продукта
        __wij_dict = next((wij for wij in workflow_industry_jobs if
                           (wij["ptid"] == __product_type_id) and (wij["month"] == __wij_month)), None)
        if __wij_dict is None:
            continue
        __wij_products = __wij_dict["products"]
        __products_fee_tax_sum += __wij_dict["cost"]
        __products_quantity_sum += __wij_products
        if __wij_products >= __product_scheduled_quantity:
            __wij_progress_factor = 100
        else:
            __wij_progress_factor = float(100 * __wij_products / __product_scheduled_quantity)
        __td_manufactured[month] = \
            '<strong><span class="text-warning">{q:,d}</span></strong> / {sc}<br>' \
            '<div class="progress" style="margin-bottom:0px"><div class="progress-bar{prcnt100}" role="progressbar"' \
            ' aria-valuenow="{prcnt}" aria-valuemin="0" aria-valuemax="100" style="width: {prcnt}%;">{fprcnt:.1f}%</div></div>'. \
            format(
                q=__wij_products,
                sc=__product_scheduled_quantity,
                prcnt100=" progress-bar-success" if __wij_progress_factor >= 99.999 else "",
                prcnt=int(__wij_progress_factor),
                fprcnt=__wij_progress_factor
            )
    # подсчёт того, что суммируется
    if __products_quantity_sum > 0:
        __td_cost = \
            '{cost:,.1f}<br><mark><span style="font-size: smaller;">{scost:,.2f}</span></mark>'. \
            format(cost=__products_fee_tax_sum, scost=__products_fee_tax_sum / __products_quantity_sum)
        __td_volume = \
            '{volume:,.1f}<br><mark><span style="font-size: smaller;">{svolume:,.2f}</span></mark>'. \
            format(volume=__product_volume * __products_quantity_sum, svolume=__product_volume)
    # формирование строки отчёта
    glf.write(
        '<tr><!--{id}-->'
        '<td><img class="icn32" src="{img}" width="32px" height="32px"></td>'
        '<td>{nm}</td>'
        '<td align="right">{mnf0}</td> <td align="right">{mnf1}</td> <td align="right">{mnf2}</td>'
        '<td align="right">{cost}</td>'
        '<td align="right">{volume}</td>'
        '</tr>\n'.
        format(
            id=__product_type_id,
            img=render_html.__get_img_src(__product_type_id, 32),
            nm=__product_name,
            scheduled=__product_scheduled_quantity,
            mnf0=__td_manufactured[0],
            mnf1=__td_manufactured[1],
            mnf2=__td_manufactured[2],
            cost=__td_cost,
            volume=__td_volume
        )
    )


def __dump_industry_workflow(
        glf,
        sde_type_ids,
        corp_industry_stat):
    conveyor_scheduled_products = corp_industry_stat["conveyor_scheduled_products"]
    workflow_industry_jobs = corp_industry_stat["workflow_industry_jobs"]
    current_month = corp_industry_stat["current_month"]
    conveyor_market_groups = corp_industry_stat["conveyor_market_groups"]

    glf.write("""
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th style="width:32px;" rowspan="2"></th>
  <th rowspan="2">Products</th>
  <th style="text-align: center;" colspan="3">Manufactured / Scheduled<br>Progress of Monthly Jobs</th>
  <th style="text-align: right;" rowspan="2">Fee &amp; Tax, ISK</th>
  <th style="text-align: right;" rowspan="2">Volume, m&sup3;</th>
 </tr>
 <tr>
""")
    glf.write(
        '<th style="text-align: center;">{}</th>'
        '<th style="text-align: center;">{}</th>'
        '<th style="text-align: center;">{}</th>'.
        format(g_month_names[(current_month+9)%12+1], g_month_names[(current_month+10)%12+1], g_month_names[current_month]))
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
            if product["market"] == __market_group_id:
                __dump_industry_workflow_product(glf, product, current_month, sde_type_ids, workflow_industry_jobs)

    glf.write("""
</tbody>
</table>
""")


def __dump_market_product(
        glf,
        product,
        jita_materials_market):
    # распаковка о продукте данных для вывода в отчёт
    __product_type_id = product["type_id"]
    __product_name = product["name"]
    __product_market_dict = jita_materials_market.get(str(__product_type_id), None)
    __product_manuf_price = product["manuf_price"]
    # формирование ячеек с опциональными значениями
    __td_nao = ""
    __td_njso = ""
    __td_manuf_lo = ""
    __td_manuf_avg = ""
    __td_manuf_hi = ""
    __td_average = ""
    __td_volume = ""
    __td_profit = ""
    __td_sell = ""
    __td_buy = ""
    if not product["active_orders"]:
        __td_nao = '&nbsp;<span class="label label-danger">no active orders</span>'
    elif (__product_market_dict is None) or not ("sell" in __product_market_dict["orders"]):
        __td_njso = '&nbsp;<span class="label label-warning">no jita sell orders</span>'
    if not (__product_market_dict is None):
        if "month" in __product_market_dict:
            __month_volume = __product_market_dict["month"]["sum_volume"]
            __month_isk = __product_market_dict["month"]["avg_isk"]
            if (__month_volume > 0) and (__month_isk >= 0.01):
                # делим на 30, т.к. данные выбираются из market/{}/history за последние 31 день (последний отсутствует)
                __td_average = '{mon_isk:,.0f}'\
                               '<br><mark><span style="font-size: smaller;">&asymp;{day_isk:,.0f}</span></mark>'.\
                               format(mon_isk=__month_isk, day_isk=__month_isk/__month_volume)
                __td_volume = '{mon_pcs:,.0f}'.format(mon_pcs=__month_volume)
                if __month_volume >= 30:
                    __td_volume += '<br><mark><span style="font-size: smaller;">&asymp;{dpcs:,.0f}</span></mark>'.\
                                   format(dpcs=__month_volume/30)
        __market_orders = __product_market_dict["orders"]
        __td_sell = '{isk:,.2f}'.format(isk=__market_orders["sell"]) if "sell" in __market_orders else ''
        __td_buy = '{isk:,.2f}'.format(isk=__market_orders["buy"]) if "buy" in __market_orders else ''
    if __product_manuf_price["lo_known"]:
        __td_manuf_lo = '{isk:,.0f}'.format(isk=__product_manuf_price["lo"])
    if __product_manuf_price["hi_known"]:
        __td_manuf_hi = '{isk:,.0f}'.format(isk=__product_manuf_price["hi"])
    if __product_manuf_price["avg_known"]:
        __td_manuf_avg = '{isk:,.0f}'.format(isk=__product_manuf_price["avg"])
        # берём среднюю (текущую в моменте) цену на материалы и пытаемся продать по sell-ам (Глорден долго
        # держит позицию), если не получается, то продаём по баям
    if not (product["profit"] is None):
        __td_profit = '{isk:,.0f}'.format(isk=product["profit"])
        if product["profit"] < 0:
            __td_profit = '<span class="text-danger">' + __td_profit + '</span>'

    # формирование строки отчёта
    glf.write(
        '<tr pid="{id}">'
        '<td><img class="icn32" src="{img}" width="32px" height="32px"></td>'
        '<td>{nm}{nao}{njso}</td>'
        '<td align="right">{average}</td>'
        '<td align="right">{volume}</td>'
        '<td align="right">{mhi}</td>'
        '<td align="right">{mavg}</td>'
        '<td align="right">{mlo}</td>'
        '<td align="right">{profit}</td>'
        '<td align="right">{sell}</td>'
        '<td align="right">{buy}</td>'
        '</tr>\n'.
        format(
            id=__product_type_id,
            img=render_html.__get_img_src(__product_type_id, 32),
            nm=__product_name,
            nao=__td_nao,
            njso=__td_njso,
            mlo=__td_manuf_lo,
            mavg=__td_manuf_avg,
            mhi=__td_manuf_hi,
            average=__td_average,
            volume=__td_volume,
            profit=__td_profit,
            sell=__td_sell,
            buy=__td_buy
        )
    )


def __dump_market_analytics_products(
        glf,
        sde_type_ids,
        products,
        market_groups,
        jita_materials_market,
        grouping=True):
    glf.write("""
<div class="table-responsive">
<table class="table table-condensed table-hover" style="padding:1px;font-size:smaller;" id="tblPrdcs">
<thead>
 <tr>
  <th style="width:32px;" rowspan="2"></th>
  <th rowspan="2">Products</th>
  <th style="text-align: center;" colspan="2">The Forge region</th>
  <th style="text-align: center;" colspan="3">Manufacturing, ISK</th>
  <th style="text-align: center;" rowspan="2">Profit</th>
  <th style="text-align: center;" colspan="2">Jita trade hub</th>
 </tr>
 <tr>
  <th style="text-align: right;">Average, ISK</th>
  <th style="text-align: right;">Volume, pcs.</th>

  <th style="text-align: right;">Sell (highest)</th>
  <th style="text-align: right;">Average</th>
  <th style="text-align: right;">Buy (lowest)</th>

  <th style="text-align: right;">Sell, ISK</th>
  <th style="text-align: right;">Buy, ISK</th>
 </tr>
</thead>
<tbody>
""")

    if grouping:
        products_groups = [p["market_group_id"] for p in products]
        market_groups = list(market_groups.items())
        market_groups = [g for g in market_groups if int(g[0]) in products_groups]
        market_groups.sort(key=lambda g: g[1])
        for product in products:
            if product["market_group_id"] is None:
                __dump_market_product(glf, product, jita_materials_market)
        for market in market_groups:
            glf.write('<tr><td class="active text-info" colspan="10"><strong>{nm}</strong></td></tr>\n'.format(nm=market[1]))
            __market_group_id = int(market[0])
            for product in products:
                if product["market_group_id"] == __market_group_id:
                    __dump_market_product(glf, product, jita_materials_market)
    else:
        for product in products:
            __dump_market_product(glf, product, jita_materials_market)

    glf.write("""
</tbody>
</table>
</div> <!--table-responsive-->
""")

    render_html.__dump_sde_type_ids_to_js(glf, sde_type_ids)  # добавляет <script></script>

    glf.write("""
<div class="modal fade" tabindex="-1" role="dialog" id="modalIndustry">
 <div class="modal-dialog" role="document">
  <div class="modal-content">
   <div class="modal-header">
    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
    <h5 class="modal-title"></h5>
   </div>
   <div class="modal-body"></div>
   <div class="modal-footer">
    <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
   </div>
  </div>
 </div>
</div>

<script>
var g_prdcts_tbl = [
""")

    for p in products:
        __materials = p["t2_bpc_materials"]
        __materials_ls = ''
        for m in enumerate(__materials):
            if m[0] != 0:
                __materials_ls += ','
            __materials_ls += '[{},{}]'.format(m[1]["quantity"], m[1]["typeID"])

        glf.write(
            '[{id},{bpid},null,{me},{te},{runs},[{mat}]],'.
            format(id=p['type_id'],
                   bpid=p['blueprint_type_id'],
                   me=p['t2_bpc_attrs']['me'],
                   te=p['t2_bpc_attrs']['te'],
                   runs=p['t2_bpc_attrs']['runs'],
                   mat=__materials_ls)
        )

    glf.write("""[-1]];
$(document).ready(function(){
  $('#tblPrdcs > tbody > tr').click(function() {
    var tr = $(this);
    var pid = tr.attr('pid');
    var pnm = getSdeItemName(pid);
    var prdcts = null;
    var modal = $('#modalIndustry');
    var pnm_w_lbls = tr.find('td').eq(1).html();
    for (var i=0; i<g_prdcts_tbl.length; i++) {
      if (g_prdcts_tbl[i][0]==pid) {
        prdcts = g_prdcts_tbl[i];
        break;
      }
    }
    modal.find('.modal-title').html(tr.find('td').eq(0).html() + ' ' + pnm_w_lbls);
    if (!(prdcts === null)) {
      var mtrls = '';
      for (var i=0; i<prdcts[6].length; i++)
        mtrls += '<img class="icn16" src="image_export_collection/Types/'+prdcts[6][i][1]+'_32.png" width="16px" height="16px">'+
                 '<strong>'+prdcts[6][i][0]+'x</strong> '+getSdeItemName(prdcts[6][i][1])+'<br>';
      var txt =
        '<dl class="dl-horizontal">' +
        '<dt>Продукт №'+pid+'</dt><dd>'+pnm+'</dd>' +
        '<dt>Чертёж №'+prdcts[1]+'</dt><dd>'+pnm+' Blueprint</dd>' +
        '<dt>ME</dt><dd>'+prdcts[3]+'%</dd>' +
        '<dt>TE</dt><dd>'+prdcts[4]+'%</dd>' +
        '<dt>Копия</dt><dd>'+prdcts[5]+' прогон(ов)</dd>' +
        '<dt>Материалы</dt><dd>'+mtrls+'</dd>' +
        '</dt>';
      modal.find('.modal-body').html(txt);
    }
    modal.modal('show');
  });
});
</script>
""")


def __dump_market_analytics(
        glf,
        sde_type_ids,
        possible_t2_products):
    products = possible_t2_products["products"]
    market_groups = possible_t2_products["market_groups"]
    jita_market = possible_t2_products["market"]

    __dummy_history = {"month": {"avg_isk": 0}}
    __dummy_orders = {"orders": {}}

    products_no_active_orders = [p for p in products if not p["active_orders"]]
    inactive_ptids = [p["type_id"] for p in products_no_active_orders]

    products_no_sell_jita_orders = [p for p in products if not (p["type_id"] in inactive_ptids) and not ("sell" in jita_market.get(str(p["type_id"]), __dummy_orders)["orders"])]
    inactive_ptids.extend([p["type_id"] for p in products_no_sell_jita_orders])

    products_active_orders = [p for p in products if not (p["type_id"] in inactive_ptids)]

    if products_no_active_orders:
        glf.write("<h4>No Active orders in 'The Forge' region</h4>")
        products_no_active_orders.sort(key=lambda p: p["name"])
        __dump_market_analytics_products(glf, sde_type_ids, products_no_active_orders, market_groups, jita_market)

    if products_no_sell_jita_orders:
        glf.write("<h4>No Sell orders in Jita</h4>")
        products_no_sell_jita_orders.sort(key=lambda p: p["name"])
        __dump_market_analytics_products(glf, sde_type_ids, products_no_sell_jita_orders, market_groups, jita_market)

    glf.write('<h4>Market in Jita</h4>'
              '<var>The Forge average</var> = <span style="font-size: large;">∑<sub><sub>last month</sub></sub></span> <var>average &lowast; volume</var>, ISK<br>'
              '<var>Jita sell</var> &amp; <var>Jita buy</var> = <var>last known prices</var>, ISK <small><small>({dt})</small></small><br>'.
              format(dt=render_html.__get_render_datetime()))

    products_active_orders.sort(key=lambda p: p["profit"] if "profit" in p else -2147483648, reverse=True)
    __dump_market_analytics_products(glf, sde_type_ids, products_active_orders, market_groups, jita_market, grouping=False)


def dump_industry_into_report(
        # путь, где будет сохранён отчёт
        ws_dir,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_industry_stat,
        possible_t2_products):
    glf = open('{dir}/industry.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(glf, "Industry")
        glf.write('<div class="container-fluid">')
        glf.write("<h3>Scheduled Industry Jobs</h3>")
        __dump_industry_workflow(
            glf,
            sde_type_ids,
            corp_industry_stat)
        glf.write("<h3>Jita' market analytics</h3>")
        __dump_market_analytics(
            glf,
            sde_type_ids,
            possible_t2_products
        )
        glf.write('</div> <!--container-fluid-->')
        render_html.__dump_footer(glf)
    finally:
        glf.close()
