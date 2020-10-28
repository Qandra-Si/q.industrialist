import render_html


g_month_names = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"]


def __dump__industry(
        glf,
        sde_type_ids,
        corp_industry_stat):
    conveyor_scheduled_products = corp_industry_stat["conveyor_scheduled_products"]
    conveyor_scheduled_products.sort(key=lambda p: p["name"])

    workflow_industry_jobs = corp_industry_stat["workflow_industry_jobs"]
    current_month = corp_industry_stat["current_month"]

    glf.write("""
<div class="container-fluid">
<h3>Scheduled Industry Jobs</h3>
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

    for product in conveyor_scheduled_products:
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
            __wij_dict = next((wij for wij in workflow_industry_jobs if (wij["ptid"] == __product_type_id) and (wij["month"] == __wij_month)), None)
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
                format(cost=__products_fee_tax_sum, scost=__products_fee_tax_sum/__products_quantity_sum)
            __td_volume = \
                '{volume:,.1f}<br><mark><span style="font-size: smaller;">{svolume:,.2f}</span></mark>'. \
                format(volume=__product_volume*__products_quantity_sum, svolume=__product_volume)
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

    glf.write("""
</tbody>
</table>
</div> <!--container-fluid-->
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
        __dump__industry(
            glf,
            sde_type_ids,
            corp_industry_stat)
        render_html.__dump_footer(glf)
    finally:
        glf.close()
