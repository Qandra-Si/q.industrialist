import render_html
import eve_sde_tools


def __dump__industry(
        glf,
        sde_type_ids,
        db_workflow_industry_jobs,
        conveyor_scheduled_products):
    glf.write("""
<div class="container-fluid">
<h3>Scheduled Industry Jobs</h3>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th style="width:32px;"></th>
  <th>Products</th>
  <th style="text-align: center;">Manufactured / Scheduled<br>Progress of Monthly Jobs</th>
  <th style="text-align: right;">Fee &amp; Tax, ISK</th>
  <th style="text-align: right;">Volume, m&sup3;</th>
 </tr>
</thead>
<tbody>

""")

    conveyor_scheduled_products.sort(key=lambda p: p["name"])
    for product in conveyor_scheduled_products:
        # распаковка о продукте данных для вывода в отчёт
        __product_type_id = product["type_id"]
        __product_name = product["name"]
        __product_scheduled_quantity = product["quantity"]
        # получение справочной информации о продукте
        __product_dict = sde_type_ids.get(str(__product_type_id), None)
        __product_volume = __product_dict["volume"] if not (__product_dict is None) and ("volume" in __product_dict) else 0
        # получение информации о производстве этого продукта
        __wij_dict = next((wij for wij in db_workflow_industry_jobs if wij["ptid"] == __product_type_id), None)
        # вычисление статистики производства, формирование отдельных ячеек таблицы
        __td_manufactured = ""
        __td_progress = ""
        __td_cost = ""
        __td_volume = ""
        if not (__wij_dict is None):
            __wij_runs = __wij_dict["runs"]
            __wij_cost = __wij_dict["cost"]
            __td_manufactured =\
                '<span class="text-warning">{q:,d}</span>'.\
                format(q=__wij_runs)
            __td_cost = \
                '{cost:,.1f}<br><mark><span style="font-size: smaller;">{scost:,.2f}</span></mark>'.\
                format(cost=__wij_cost, scost=__wij_cost/__wij_runs)
            __td_volume = \
                '{volume:,.1f}<br><mark><span style="font-size: smaller;">{svolume:,.2f}</span></mark>'.\
                format(volume=__product_volume, svolume=__product_volume/__wij_runs)
            if __wij_runs >= __product_scheduled_quantity:
                __progress_factor = 100
            else:
                __progress_factor = float(100 * __wij_runs / __product_scheduled_quantity)
            __td_progress = \
                '<div class="progress" style="margin-bottom:0px"><div class="progress-bar{prcnt100}" role="progressbar"' \
                ' aria-valuenow="{prcnt}" aria-valuemin="0" aria-valuemax="100" style="width: {prcnt}%;">{fprcnt:.1f}%</div></div>'.\
                format(
                    prcnt100=" progress-bar-success" if __progress_factor >= 99.999 else "",
                    prcnt=int(__progress_factor),
                    fprcnt=__progress_factor,
                )
        # формирование строки отчёта
        glf.write(
            '<tr><!--{id}-->'
            '<td><img class="icn32" src="{img}" width="32px" height="32px"></td>'
            '<td>{nm}</td>'
            '<td align="right">{manufactured} / {scheduled:,d}<br>{progress}</td>'
            '<td align="right">{cost}</td>'
            '<td align="right">{volume}</td>'
            '</tr>\n'.
            format(
                id=__product_type_id,
                img=render_html.__get_img_src(__product_type_id, 32),
                nm=__product_name,
                scheduled=__product_scheduled_quantity,
                manufactured=__td_manufactured,
                progress=__td_progress,
                cost=__td_cost,
                volume=__td_volume,
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
        db_workflow_industry_jobs,
        conveyor_scheduled_products
):
    glf = open('{dir}/industry.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(glf, "Industry")
        __dump__industry(
            glf,
            sde_type_ids,
            db_workflow_industry_jobs,
            conveyor_scheduled_products)
        render_html.__dump_footer(glf)
    finally:
        glf.close()
