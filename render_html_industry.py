import render_html
import eve_sde_tools


def __dump__industry(
        glf,
        sde_type_ids,
        db_workflow_industry_jobs):
    glf.write("""
<div class="container-fluid">
<h3>Industry Jobs</h3>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th style="width:32px;"></th>
  <th>Items</th>
  <th>Progress of Monthly Jobs</th>
  <th style="text-align: right;">Fee &amp; Tax, ISK</th>
  <th style="text-align: right;">Volume, m&sup3;</th>
 </tr>
</thead>
<tbody>

""")

    for wij in db_workflow_industry_jobs:
        # распаковка данных для вывода в отчёт
        __product_type_id = wij["ptid"]
        __product_dict = sde_type_ids.get(str(__product_type_id), None)
        __product_name = __product_dict["name"]["en"] if not (__product_dict is None) and ("name" in __product_dict) and ("en" in __product_dict["name"]) else __product_type_id
        __product_volume = __product_dict["volume"] if not (__product_dict is None) and ("volume" in __product_dict) else 0
        __blueprints_runs = wij["runs"]
        # расчёт прогресса
        __progress = ""
        if not (__product_dict is None):
            if ("metaGroupID" in __product_dict) and ("marketGroupID" in __product_dict):
                if (__product_dict["metaGroupID"] == 2) and (__product_dict["marketGroupID"] == 838):
                    __should_be = 1000
                    if __blueprints_runs >= __should_be:
                        __progress_factor = 100
                    else:
                        __progress_factor = float(100 * __blueprints_runs / __should_be)
                    __progress =\
                        '<div class="progress" style="margin-bottom:0px"><div class="progress-bar{prcnt100}" role="progressbar"'\
                        ' aria-valuenow="{prcnt}" aria-valuemin="0" aria-valuemax="100" style="width: {prcnt}%;">{fprcnt:.1f}%</div></div>'\
                        .format(
                            prcnt100=" progress-bar-success" if __progress_factor >= 99.999 else "",
                            prcnt=int(__progress_factor),
                            fprcnt=__progress_factor,
                        )
        # формирование строки отчёта
        glf.write(
            '<tr><!--{id}-->'
            '<td><img class="icn32" src="{img}" width="32px" height="32px"></td>'
            '<td><strong>{q}x</strong> {nm}</td>'
            '<td>{progress}</td>'
            '<td align="right">{cost:,.1f}</td>'
            '<td align="right">{volume:,.1f}</td>'
            '</tr>\n'.
            format(
                id=__product_type_id,
                img=render_html.__get_img_src(__product_type_id, 32),
                nm=__product_name,
                q=__blueprints_runs,
                cost=wij["cost"],
                volume=__blueprints_runs*__product_volume,
                progress=__progress
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
        db_workflow_industry_jobs
):
    glf = open('{dir}/industry.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(glf, "Industry")
        __dump__industry(
            glf,
            sde_type_ids,
            db_workflow_industry_jobs)
        render_html.__dump_footer(glf)
    finally:
        glf.close()
