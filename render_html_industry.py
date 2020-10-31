import render_html


g_month_names = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"]


def __dump_industry_product(
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


def __dump_industry(
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
                __dump_industry_product(glf, product, current_month, sde_type_ids, workflow_industry_jobs)

    glf.write("""
</tbody>
</table>
""")


def __dump_market_product(
        glf,
        product):
    # распаковка о продукте данных для вывода в отчёт
    __product_type_id = product["type_id"]
    __product_name = product["name"]
    # формирование ячеек с опциональными значениями
    __td_nao = ""
    __td_njso = ""
    __td_average = ""
    __td_volume = ""
    if not product["active_orders"]:
        __td_nao = '&nbsp;<span class="label label-danger">no active orders</span>'
    elif not ("jita_sell" in product):
        __td_njso = '&nbsp;<span class="label label-warning">no jita sell orders</span>'
    if "month" in product:
        __month_volume = product["month"]["sum_volume"]
        __month_isk = product["month"]["avg_isk"]
        if (__month_volume > 0) and (__month_isk >= 0.01):
            # делим на 30, т.к. данные выбираются из market/{}/history за последние 31 день (последний отсутствует)
            __td_average = '{mon_isk:,.0f}'\
                           '<br><mark><span style="font-size: smaller;">&asymp;{day_isk:,.0f}</span></mark>'.\
                           format(mon_isk=__month_isk, day_isk=__month_isk/__month_volume)
            __td_volume = '{mon_pcs:,.0f}'.format(mon_pcs=__month_volume)
            if __month_volume >= 30:
                __td_volume += '<br><mark><span style="font-size: smaller;">&asymp;{dpcs:,.0f}</span></mark>'.\
                               format(dpcs=__month_volume/30)

    # формирование строки отчёта
    glf.write(
        '<tr><!--{id}-->'
        '<td><img class="icn32" src="{img}" width="32px" height="32px"></td>'
        '<td>{nm}{nao}{njso}</td>'
        '<td align="right">{average}</td>'
        '<td align="right">{volume}</td>'
        '<td align="right">{sell}</td>'
        '<td align="right">{buy}</td>'
        '</tr>\n'.
        format(
            id=__product_type_id,
            img=render_html.__get_img_src(__product_type_id, 32),
            nm=__product_name,
            nao=__td_nao,
            njso=__td_njso,
            average=__td_average,
            volume=__td_volume,
            sell='{isk:,.2f}'.format(isk=product["jita_sell"]) if "jita_sell" in product else '',
            buy='{isk:,.2f}'.format(isk=product["jita_buy"]) if "jita_buy" in product else ''
        )
    )


def __dump_market_analytics_products(
        glf,
        products,
        market_groups,
        grouping=True):
    glf.write("""
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th style="width:32px;" rowspan="2"></th>
  <th rowspan="2">Products</th>
  <th style="text-align: center;" colspan="2">The Forge region</th>
  <th style="text-align: center;" colspan="2">Jita trade hub</th>
 </tr>
 <tr>
  <th style="text-align: right;">Average, ISK</th>
  <th style="text-align: right;">Volume, pcs.</th>
  <th style="text-align: right;">Sell, ISK</th>
  <th style="text-align: right;">Buy, ISK</th>
 </tr>
</thead>
<tbody>
""")

    if grouping:
        products_groups = [p["market"] for p in products]
        market_groups = list(market_groups.items())
        market_groups = [g for g in market_groups if int(g[0]) in products_groups]
        market_groups.sort(key=lambda g: g[1])
        for product in products:
            if product["market"] is None:
                __dump_market_product(glf, product)
        for market in market_groups:
            glf.write('<tr><td class="active text-info" colspan="6"><strong>{nm}</strong></td></tr>\n'.format(nm=market[1]))
            __market_group_id = int(market[0])
            for product in products:
                if product["market"] == __market_group_id:
                    __dump_market_product(glf, product)
    else:
        for product in products:
            __dump_market_product(glf, product)

    glf.write("""
</tbody>
</table>
""")


def __dump_market_analytics(
        glf,
        possible_t2_products):
    products = possible_t2_products["products"]
    market_groups = possible_t2_products["market_groups"]

    products_no_active_orders = [p for p in products if not p["active_orders"]]
    products_no_sell_jita_orders = [p for p in products if p["active_orders"] and not ("jita_sell" in p)]
    products_active_orders = [p for p in products if p["active_orders"] and ("jita_sell" in p)]

    if products_no_active_orders:
        glf.write("<h4>No Active orders in 'The Forge' region</h4>")
        products_no_active_orders.sort(key=lambda p: p["name"])
        __dump_market_analytics_products(glf, products_no_active_orders, market_groups)

    if products_no_sell_jita_orders:
        glf.write("<h4>No Sell orders in Jita</h4>")
        products_no_sell_jita_orders.sort(key=lambda p: p["name"])
        __dump_market_analytics_products(glf, products_no_sell_jita_orders, market_groups)

    glf.write('<h4>Market in Jita</h4>'
              '<var>The Forge average</var> = <span style="font-size: large;">∑<sub><sub>last month</sub></sub></span> <var>average &lowast; volume</var>, ISK<br>'
              '<var>Jita sell</var> &amp; <var>Jita buy</var> = <var>last known prices</var>, ISK <small><small>({dt})</small></small><br>'.
              format(dt=render_html.__get_render_datetime()))
    products_active_orders.sort(key=lambda p: p["month"]["avg_isk"], reverse=True)
    __dump_market_analytics_products(glf, products_active_orders, market_groups, grouping=False)


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
        __dump_industry(
            glf,
            sde_type_ids,
            corp_industry_stat)
        glf.write("<h3>Jita' market analytics</h3>")
        __dump_market_analytics(
            glf,
            possible_t2_products
        )
        glf.write('</div> <!--container-fluid-->')
        render_html.__dump_footer(glf)
    finally:
        glf.close()
