import typing
import math

import eve_esi_tools
import render_html
import profit


def get_pseudographics_prefix(levels, is_first, is_last):
    prfx: str = ''
    for lv in enumerate(levels):
        if lv[1]:
            prfx += '&nbsp; '
        else:
            prfx += '| '  # &#x2502;
    if is_first:
        if not prfx:
            prfx += '└'  # &#x2514;
        else:
            prfx += '| └'  # &#x2502; &#x2514;
    elif is_last:
        prfx += '└─'  # &#x2514;&#x2500;
    else:
        prfx += '├─'  # &#x251C;&#x2500;
    return prfx


def get_industry_cost_indices_desc(
        # индексы стоимости производства для различных систем (системы и продукция заданы в настройках роутинга)
        industry_cost_indices:  typing.List[profit.QIndustryCostIndices]) -> str:
    desc: str = ''
    if not industry_cost_indices:
        desc = '(настройка не задана)'
    else:
        max0: int = len(industry_cost_indices) - 1
        for lvl0, i in enumerate(industry_cost_indices):
            desc += '<br>\n' + get_pseudographics_prefix([], lvl0 == 0, lvl0 == max0)
            desc += f' {i.factory_name} производит {f'{len(i.product_ids)} видов' if i.product_ids else 'все виды'} продукции'
            bonuses: typing.List[str] = []
            for num in range(2):
                for activity in ['manufacturing', 'copying', 'invent', 'reaction']:
                    if num == 0:
                        me: float = i.factory_bonuses.get_role_bonus(activity, 'me')
                        jc: float = i.factory_bonuses.get_role_bonus(activity, 'job_cost')
                        prfx: str = f'{activity} бонус профиля сооружения: '
                    else:
                        me = i.factory_bonuses.get_rigs_bonus(activity, 'me')
                        jc = i.factory_bonuses.get_rigs_bonus(activity, 'job_cost')
                        prfx: str = f'установленный {activity} модификатор: '
                    if me < -0.001 or jc < -0.001:
                        bonus = prfx
                        if me < -0.001:
                            bonus += f'расход материалов {me*100.0:.1f}%'
                            bonus += ', ' if jc < -0.001 else ''
                        if jc < -0.001:
                            bonus += f'стоимость проекта {jc*100.0:.1f}%'
                        bonuses.append(bonus)
            if bonuses:
                max1: int = len(bonuses) - 1
                for lvl1, bonus in enumerate(bonuses):
                    desc += '<br>\n' + get_pseudographics_prefix([1], lvl1 == 0, lvl1 == max1) + ' ' + bonus
    return desc


def get_common_components_desc(market_group_ids: typing.List[int], sde_market_groups):
    groups: typing.List[str] = []
    for market_group_id in market_group_ids:
        group_name: str = sde_market_groups[str(market_group_id)]['nameID']['en']
        groups.append(group_name)
    desc: str = ''
    max2: int = len(groups) - 1
    for lvl2, group_name in enumerate(groups):
        desc += '<br>\n &nbsp; &nbsp; ' + get_pseudographics_prefix([], lvl2 == 0, lvl2 == max2) + ' ' + group_name
    return desc


def render_report(
        glf,
        # данные о продуктах, которые надо отобразить в отчёте
        industry_plan: profit.QIndustryPlan,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        eve_market_prices_data,
        sde_icon_ids,
        # ордера, выставленные в Jita 4-4
        eve_jita_orders_data: profit.QMarketOrders,
        # индексы стоимости производства для различных систем (системы и продукция заданы в настройках роутинга)
        industry_cost_indices:  typing.List[profit.QIndustryCostIndices]):
    base_industry: profit.QIndustryTree = industry_plan.base_industry

    def generate_manuf_materials_list(__it157: profit.QIndustryTree):
        res: str = ''
        for m in __it157.materials:
            res += '<span style="white-space:nowrap">' \
                   '<img class="icn24" src="{src}"> {q:,d} x {nm} ' \
                   '</span>\n'.format(src=render_html.__get_img_src(m.type_id, 32), q=m.quantity, nm=m.name)
        return res

    industry_cost_indices_desc: str = get_industry_cost_indices_desc(industry_cost_indices)

    glf.write(f"""
<div class="container-fluid">
<div class="media">
 <div class="media-left"><img class="media-object icn64" src="{render_html.__get_img_src(base_industry.blueprint_type_id, 64)}" alt="{base_industry.blueprint_name}"></div>
 <div class="media-body">
  <h4 class="media-heading">{base_industry.blueprint_name}</h4>
<p>
EveUniversity {base_industry.product_name} wiki: <a href="https://wiki.eveuniversity.org/{base_industry.product_name}">https://wiki.eveuniversity.org/{base_industry.product_name}</a><br/>
EveMarketer {base_industry.product_name} tradings: <a href="https://evemarketer.com/types/{base_industry.product_type_id}">https://evemarketer.com/types/{base_industry.product_type_id}</a><br/>
EveMarketer {base_industry.product_name} Blueprint tradings: <a href="https://evemarketer.com/types/{base_industry.blueprint_type_id}">https://evemarketer.com/types/{base_industry.blueprint_type_id}</a><br/>
Adam4EVE {base_industry.product_name} manufacturing calculator: <a href="https://www.adam4eve.eu/manu_calc.php?typeID={base_industry.blueprint_type_id}">https://www.adam4eve.eu/manu_calc.php?typeID={base_industry.blueprint_type_id}</a><br/>
Adam4EVE {base_industry.product_name} price history: <a href="https://www.adam4eve.eu/commodity.php?typeID={base_industry.product_type_id}">https://www.adam4eve.eu/commodity.php?typeID={base_industry.product_type_id}</a><br/>
Adam4EVE {base_industry.product_name} Blueprint price history: <a href="https://www.adam4eve.eu/commodity.php?typeID={base_industry.blueprint_type_id}">https://www.adam4eve.eu/commodity.php?typeID={base_industry.blueprint_type_id}</a>
</p>
 </div> <!--media-body-->
</div> <!--media-->
<hr>
<div class="media">
 <div class="media-left"><img class="media-object icn64" src="{render_html.__get_img_src(base_industry.product_type_id, 64)}" alt="Требуемые комплектующие"></div>
 <div class="media-body">
  <h4 class="media-heading">Организация производства <small>Требуемые комплектующие</small></h4>
  {generate_manuf_materials_list(base_industry)}
 </div> <!--media-body-->
</div> <!--media-->
<hr>
<div class="media">
 <div class="media-left"><img class="media-object icn64" src="{render_html.__get_icon_src(1436, sde_icon_ids)}"></div>
 <div class="media-body">
<!--<p><var>Efficiency</var> = <var>Required</var> * (100 - <var>material_efficiency</var> - 1 - 4.2) / 100,
<br>where <var>material_efficiency</var> for unknown and unavailable blueprint is ?.</p>-->
<p>
Параметры чертежа:<br>
 ├─ Число прогонов: {industry_plan.customized_runs}<br>
 └─ Экономия материалов при производстве: -{base_industry.me}.0%<br>
Экономия материалов промежуточных чертежей: {'(настройка не задана)' if not industry_plan.customization or industry_plan.customization.unknown_blueprints_me is None else
                                             f'-{industry_plan.customization.unknown_blueprints_me}.0%'}<br>
<br>
Бонусы сооружений: {industry_cost_indices_desc}<br>
<br>
Длительность производственных работ общих компонентов: {'(настройка не задана)' if not industry_plan.customization or not industry_plan.customization.industry_time else
                                                        '{:.1f} часов'.format(float(industry_plan.customization.industry_time) / (5*60*60))}<br>
 └─ Группы компонентов общего назначения: {'(настройка не задана)' if not industry_plan.customization or not industry_plan.customization.common_components else
    f'{get_common_components_desc(industry_plan.customization.common_components, sde_market_groups)}'}<br>
Длительность запуска формул и реакций: {'(настройка не задана)' if not industry_plan.customization or not industry_plan.customization.reaction_runs else
                                        '{} прогонов'.format(industry_plan.customization.reaction_runs)}<br>
Минимальная вероятность успеха по навыкам и имплантам: {'(настройка не задана)' if not industry_plan.customization or not industry_plan.customization.min_probability else
                                                        '{:.1f}%'.format(industry_plan.customization.min_probability)}
</p>
<hr>""")

    def generate_components_header(with_current_industry_progress: bool):
        glf.write('<tr>\n'
                  '<th style="width:50px;">#</th>\n'
                  '<th>Материалы</th>\n'
                  + ('<th>Имеется +<br/>Производится</th>\n' if with_current_industry_progress else '')
                  + '<th>Без<br/>ME</th>\n'
                  + '<th>Учёт<br/>ME</th>\n'
                  + '<th>Выход<br/>(произв.)</th>\n'
                  + ('<th>Требуется<br/>(недостаточно)</th>\n' if with_current_industry_progress else '')
                  + '<th>План<br/>(произв.)</th>\n'
                  '<th>Остаток<br/>(произв.)</th>\n'
                  '<th>Соотношение<br/>(как часть целого)</th>\n'
                  '<th>Итог<br/>(закуп.)</th>\n'
                  '<th>Итог<br/>(рентаб.)</th>\n'
                  '</tr>\n')

    class TotalAllJobCost:
        def __init__(self):
            self.job_cost: float = 0.0

        def increase(self, val: float) -> float:
            self.job_cost += val
            return self.job_cost

    linear_cost_verification: profit.QIndustryJobCostAccumulator = profit.QIndustryJobCostAccumulator()

    def generate_grayed_reused_duplicate(plan: profit.QIndustryObtainingPlan, before: bool) -> str:
        if not plan or not plan.reused_duplicate:
            return ''
        return '<span style="color:lightgray;">' if before else '</span>'

    def generate_industry_plan_item(
            row0_prefix: str,
            row1_num: int,
            row0_levels,
            __pa339: profit.QPlannedActivity,
            __op340: typing.Optional[profit.QIndustryObtainingPlan],
            usage_chain: float):
        bp_tid = __pa339.industry.blueprint_type_id
        bp_action = __pa339.industry.action
        # bp_nm = __pa339.industry.blueprint_name
        # planned_material: profit.QPlannedMaterial = __pa339.planned_blueprint
        planned_blueprints: int = __pa339.planned_blueprints
        planned_runs: int = __pa339.planned_runs

        job_cost: typing.Optional[profit.QPlannedJobCost] = __pa339.industry_job_cost
        assert job_cost is not None
        current_level_job_cost: int = math.ceil(planned_blueprints * planned_runs * job_cost.total_job_cost)
        usage_chain_job_cost: float = usage_chain * current_level_job_cost

        fmt: str = \
            '<tr{tr_class}>\n' \
            + '<th scope="row"><span class="text-muted">{num_prfx}</span>{num}</th>\n' \
            + '<td><img class="icn24" src="{src}"> {prfx} {nm}{pstfx}</td>\n' \
            + '<td></td>' \
            + '<td></td>' \
            + '<td></td>' \
            + '<td>{qp}</td>' \
            + '<td></td>' \
            + '<td>{qu}</td>' \
            + '<td></td>' \
            + '<td>{qsr}</td>' \
            '</tr>'
        glf.write(
            fmt.format(
                tr_class=' class="active"' if not row0_prefix else '',
                num_prfx=row0_prefix, num=row1_num,
                prfx='<tt><span class="text-muted">{}</span></tt>'.format(
                    get_pseudographics_prefix(row0_levels, True, False)),
                nm="<span class='text-muted'>{act}</span>".format(
                    act=str(bp_action),
                ),
                pstfx="<sup> <strong style='color:maroon;'>{bp}&#215;{run}</strong></sup>".format(
                    bp=planned_blueprints,
                    run=planned_runs,
                ),
                src=render_html.__get_img_src(bp_tid, 32),
                qp='<small>{}'
                   '{}<sup>eiv</sup>*{}<sup>runs</sup>*{:.2f}%<sup>{}</sup>{}'
                   '*{}%<sup>tax</sup> => {}<sup>job</sup>'
                   '{}</small>'.format(
                        generate_grayed_reused_duplicate(__op340, True),  # before ALL
                        job_cost.estimated_items_value,  # 1.eiv
                        planned_blueprints * planned_runs,  # 1.runs
                        job_cost.industry_cost_index * 100.0,  # 1.const_index
                        job_cost.system_indices.solar_system,  # 1.solar_system
                        '' if not job_cost.structure_bonus_rigs else
                        f'*{job_cost.structure_bonus_rigs * 100.0:.2f}%<sup>rig</sup>',  # 1.rig
                        job_cost.scc_surcharge * 100.0,  # 1.tax
                        current_level_job_cost,  # 2.out
                        generate_grayed_reused_duplicate(__op340, False),  # after ALL
                   ),
                qu='<small style="color:maroon;">'
                   '{:.8f}<sup>chain</sup>*{}<sup>job</sup> => '
                   '{:.2f}<sup>ratio</sup>'
                   '</small>'.format(
                       usage_chain,
                       current_level_job_cost,
                       usage_chain_job_cost,
                   ),
                qsr='<small style="color:maroon;">'
                    '{:.2f}=<sup>{:d}+{:d}</sup>'
                    '</small>'.format(
                        linear_cost_verification.total_paid + usage_chain_job_cost,  # 1.sum
                        math.ceil(linear_cost_verification.total_paid),  # 2.total
                        math.ceil(usage_chain_job_cost)  # 1.job
                    )
            )
        )

        linear_cost_verification.increment_total_paid(usage_chain_job_cost)

    def generate_components_list(
            with_current_industry_progress: bool,
            row0_prefix: str,
            row0_levels,
            __ap344: profit.QPlannedActivity):
        # вывод информации о материалах
        for m1 in enumerate(__ap344.planned_materials, start=1):
            row1_num: int = int(m1[0])
            m1_planned_material: profit.QPlannedMaterial = m1[1]
            m1_obtaining_plan: profit.QIndustryObtainingPlan = m1_planned_material.obtaining_plan
            m1_obtaining_activity: profit.QPlannedActivity = m1_obtaining_plan.activity_plan
            m1_material: profit.QMaterial = m1[1].material
            m1_industry: profit.QIndustryTree = m1_material.industry
            m1_tid: int = m1_material.type_id
            m1_tnm: str = m1_material.name
            m1_quantity: int = m1_material.quantity

            m1_copying: bool = m1_industry and m1_industry.action == profit.QIndustryAction.copying
            m1_invention: bool = m1_industry and m1_industry.action == profit.QIndustryAction.invention
            if m1_copying or m1_invention:
                m1_planned_blueprints: int = m1_obtaining_activity.planned_blueprints
                m1_planned_runs: int = m1_obtaining_activity.planned_runs
            else:
                m1_planned_blueprints: int = __ap344.planned_blueprints
                m1_planned_runs: int = __ap344.planned_runs

            fmt: str = \
                '<tr{tr_class}>\n' \
                + '<th scope="row"><span class="text-muted">{num_prfx}</span>{num}</th>\n' \
                + '<td><img class="icn24" src="{src}"> {prfx} {nm}{pstfx}</td>\n' \
                + ('<td>{qa:,d}{qip}</td>\n' if with_current_industry_progress else '') \
                + '<td>{qwome:,d}</td>\n' \
                + '<td>{qe}</td>\n' \
                + ('<td>{qne}</td>\n' if with_current_industry_progress else '') \
                + '<td>{qo}</td>\n' \
                + '<td>{qp}</td>\n' \
                + '<td>{qr}</td>\n' \
                + '<td>{qu}</td>\n' \
                + '<td>{qsq}</td>\n' \
                + '<td>{qsr}</td>\n' \
                '</tr>'
            glf.write(
                fmt.format(
                    tr_class=' class="active"' if not row0_prefix else '',
                    num_prfx=row0_prefix, num=row1_num,
                    prfx='<tt><span class="text-muted">{}</span></tt>'.format(
                        get_pseudographics_prefix(row0_levels, False, row1_num == len(__ap344.planned_materials))),
                    nm=m1_tnm,
                    pstfx='{qm}{bpq}'.format(
                        qm="<sup> <strong style='color:darkblue;'>x{}</strong></sup>".format(m1_quantity),
                        bpq='' if m1_industry is None or m1_industry.products_per_single_run == 1 else
                            ' <strong>x{}</strong>'.format(m1_industry.products_per_single_run),
                    ),
                    src=render_html.__get_img_src(m1_tid, 32),
                    qa=-1,
                    qip='',
                    qwome=m1_material.quantity * m1_planned_blueprints * m1_planned_runs,
                    qe='{:,d}'.format(m1_planned_material.quantity_with_efficiency) if m1_industry is not None else
                       '{}{:,d}{}'.format(
                           generate_grayed_reused_duplicate(m1_obtaining_plan, True),
                           m1_planned_material.quantity_with_efficiency,
                           generate_grayed_reused_duplicate(m1_obtaining_plan, False)
                       ),
                    qo='' if not m1_material.industry else
                       '{}{}{}'.format(
                           generate_grayed_reused_duplicate(m1_obtaining_plan, True),
                           m1_obtaining_plan.industry_output,
                           generate_grayed_reused_duplicate(m1_obtaining_plan, False)
                       ),
                    qp='' if not m1_material.industry else
                       '<small>'
                       '{}<sup>bp</sup>*{}<sup>run</sup>*{}<sup>qty</sup>*{}<sup>%</sup> => '
                       '{:.1f}<sup>%</sup>'
                       '</small>'.format(
                           m1_planned_blueprints,  # 1.bp
                           m1_planned_runs,  # 1.run
                           m1_material.quantity,  # 1.qty
                           '{:.1f}{}'.format(  # 1.prob
                               100.0*m1_industry.invent_probability,
                               '' if m1_industry.decryptor_probability is None else
                               '×{:.1f}'.format(100.0*m1_industry.decryptor_probability)
                           ) if not industry_plan.customization or not industry_plan.customization.min_probability else
                           '({:.1f}{}×{:.1f})'.format(
                               100.0*m1_industry.invent_probability,
                               '' if m1_industry.decryptor_probability is None else
                               '×{:.1f}'.format(100.0*m1_industry.decryptor_probability),
                               industry_plan.customization.min_probability
                           ),
                           m1_planned_blueprints * \
                           m1_planned_runs * \
                           m1_material.quantity * \
                           m1_industry.invent_probability * (  # Purifier : 30x20x27.5 => 0.3*1.2*1.275 => 45.9%
                               1.0 if m1_industry.decryptor_probability is None else
                               (1.0+m1_industry.decryptor_probability)
                           ) * (
                               1.0 if not industry_plan.customization or
                                      not industry_plan.customization.min_probability else
                               (100.0+industry_plan.customization.min_probability)/100.0
                           ) * 100.0  # 2.out
                       ) if m1_invention else
                       '<small>'
                       '{}<sup>bp</sup>*{}<sup>run</sup>*{}<sup>qty</sup> => '
                       '{:.1f}<sup>out</sup>'
                       '</small>'.format(
                           m1_planned_blueprints,  # 1.bp
                           m1_planned_runs,  # 1.run
                           m1_material.quantity,  # 1.qty
                           m1_planned_blueprints * \
                           m1_planned_runs * \
                           m1_material.quantity  # 2.out
                       ) if m1_copying else
                       '<small>'
                       '{}<sup>bp</sup>*{}<sup>run</sup>*{}<sup>qty</sup> => '
                       '{}<sup>me</sup> '
                       '{}=> '
                       '{}<sup>bp</sup>*{}<sup>run</sup>*{}<sup>dose</sup> => '
                       '{}<sup>out</sup>'
                       '{}'
                       '</small>'.format(
                           m1_planned_blueprints,  # 1.bp
                           m1_planned_runs,  # 1.run
                           m1_material.quantity,  # 1.qty
                           m1_planned_material.quantity_with_efficiency,  # 2.me
                           generate_grayed_reused_duplicate(m1_obtaining_plan, True),  # before 3
                           'TODO' if not m1_obtaining_activity else m1_obtaining_activity.planned_blueprints,  # 3.bp
                           'TODO' if not m1_obtaining_activity else m1_obtaining_activity.planned_runs,  # 3.run
                           m1_industry.products_per_single_run,  # 3.dose
                           m1_obtaining_plan.industry_output,  # 4.out
                           generate_grayed_reused_duplicate(m1_obtaining_plan, False)  # after 4
                       ),
                    qr='' if not m1_material.industry else
                       '{:,d}{}'.format(
                           m1_obtaining_plan.rest_quantity,
                           '' if not m1_obtaining_plan.reused_duplicate else
                           '<small>=<sup>{}-{}</sup></small>'.format(
                               m1_obtaining_plan.rest_quantity + m1_planned_material.quantity_with_efficiency,
                               m1_planned_material.quantity_with_efficiency
                           )
                       ),
                    qu='<small>'
                       '{:.8f}<sup>chain</sup>*{}<sup>pcs</sup> => '
                       '{:.8f}<sup>ratio</sup>'
                       '</small>'.format(
                            m1_planned_material.usage_chain,
                            m1_planned_material.quantity_with_efficiency,
                            m1_planned_material.usage_chain * m1_planned_material.usage_ratio
                       ) if not m1_material.industry else
                       # '<small>'
                       # '{:.8f}<sup>chain</sup> => {}<sup>runs'
                       # '</small>'.format(
                       #     m1_planned_material.usage_chain,
                       #     m1_planned_material.quantity_with_efficiency
                       # ) if m1_material.industry.action == profit.QIndustryAction.copying else
                       '<small>'
                       '{:.8f}<sup>chain</sup> * '
                       '({}<sup>me</sup>/{}{}<sup>out</sup>{} => {:.4f}) => '
                       '{:.8f}<sup>ratio</sup>'
                       '</small>'.format(
                           m1_planned_material.usage_chain,  # chain
                           m1_planned_material.quantity_with_efficiency,  # me
                           generate_grayed_reused_duplicate(m1_obtaining_plan, True),  # before out
                           m1_obtaining_plan.industry_output,  # out
                           generate_grayed_reused_duplicate(m1_obtaining_plan, False),  # after out
                           m1_planned_material.usage_ratio,  # me/out
                           m1_planned_material.usage_chain * m1_planned_material.usage_ratio  # ratio
                       ),
                    qne='' if not m1_obtaining_plan.not_enough_quantity else
                        '{:,d}'.format(m1_obtaining_plan.not_enough_quantity),
                    qsq='<small>'
                        '{:,d}{}=<sup>{}+{}</sup>{}'
                        '</small>'.format(
                            m1_planned_material.summary_quantity_after,  # sum
                            generate_grayed_reused_duplicate(m1_obtaining_plan, True),  # before =
                            m1_planned_material.summary_quantity_before,  # 1
                            m1_planned_material.summary_quantity_after-m1_planned_material.summary_quantity_before,  # 2
                            generate_grayed_reused_duplicate(m1_obtaining_plan, False)  # after =
                        ),
                    qsr='' if m1_material.industry else
                        '<small>'
                        '{:.8f}=<sup>{:.4f}+{:.4f}</sup>'
                        '</small>'.format(
                            m1_planned_material.summary_ratio_after,
                            m1_planned_material.summary_ratio_before,
                            m1_planned_material.summary_ratio_after-m1_planned_material.summary_ratio_before
                        )
                ))
            if m1_obtaining_activity:
                row2_levels = row0_levels[:]
                row2_levels.append(row1_num == len(__ap344.planned_materials))
                row2_prefix: str = "{prfx}{num1}.".format(prfx=row0_prefix, num1=row1_num)
                generate_industry_plan_item(
                    row2_prefix, 0, row2_levels,
                    m1_obtaining_activity,
                    m1_obtaining_plan,
                    # 1.0 if m1_copying or m1_invention else
                    m1_planned_material.usage_chain * m1_planned_material.usage_ratio
                )
                generate_components_list(
                    with_current_industry_progress,
                    row2_prefix,
                    row2_levels,
                    m1_obtaining_activity)

    glf.write("""
<style>
.table-borderless > tbody > tr > td,
.table-borderless > tbody > tr > th,
.table-borderless > tfoot > tr > td,
.table-borderless > tfoot > tr > th,
.table-borderless > thead > tr > td,
.table-borderless > thead > tr > th {
    border: none;
    padding: 0px;
}
</style>
 <table class="table table-borderless table-condensed" style="font-size:small">
<thead>""")

    generate_components_header(False)

    glf.write("""
</thead>
<tbody>""")

    # вывод информации о работе и чертеже
    generate_industry_plan_item(
        '', 0, [],
        industry_plan.base_planned_activity,
        None,
        1.0)
    # вывод информации о чертежах
    generate_components_list(False, '', [], industry_plan.base_planned_activity)

    glf.write(f"""
</tbody>
</table>
  </div> <!--media-body-->
 </div> <!--media-->
<hr>
 <div class="media">
  <div class="media-left">
   <img class="media-object icn64" src="{render_html.__get_icon_src(1201, sde_icon_ids)}" alt="Сводная таблица производства">
  </div>
  <div class="media-body">
   <h4 class="media-heading">Сводная таблица производства</h4>""")

    def generate_summary_raw_header(with_current_industry_progress: bool):
        glf.write('<tr>\n'
                  '<th style="width:40px;">#</th>'
                  '<th>Материалы</th>'
                  + ('<th>Имеется +<br/>Производится</th>\n' if with_current_industry_progress else '')
                  + '<th>Требуется</th>'
                  + ('<th>Прогресс, %</th>\n' if with_current_industry_progress else '')
                  + '<th style="text-align:right;">Цена,&nbsp;ISK/шт.</th>'
                  '<th style="text-align:right;">Цена,&nbsp;ISK</th>'
                  '<th style="text-align:right;">Пропорция,<br>шт.</th>'
                  '<th style="text-align:right;">Пропорция,<br>ISK</th>'
                  '<th style="text-align:right;color:maroon;">Доля 1шт<br>продукта,&nbsp;ISK</th>'
                  '<th style="text-align:right;"><strike>Объём,&nbsp;m&sup3;</strike></th>'
                  '</tr>\n')

    def generate_group_header(group_name: str) -> None:
        clbrd: str = ''
        glf.write(f'<tr><td class="active" colspan="11"><strong>{group_name}</strong><!--{id}-->{clbrd}</td></tr>\n')

    glf.write("""
<div class="table-responsive">
 <table class="table table-condensed" style="font-size:small">
<thead>""")

    generate_summary_raw_header(True)

    glf.write("""
</thead>
<tbody>""")

    def get_grayed_material_not_purchased(is_purchased: int, is_first: bool) -> str:
        if is_purchased:
            return ''
        else:
            return '<span style="color:#aaa;">' if is_first else '</span>'

    material_groups: typing.Dict[int, typing.List[profit.QIndustryMaterial]] = {}
    for type_id in industry_plan.materials_repository.materials.keys():
        m: profit.QIndustryMaterial = industry_plan.materials_repository.get_material(type_id)
        mg: typing.List[profit.QIndustryMaterial] = material_groups.get(m.base.market_group_id)
        if mg is None:
            mg = []
            material_groups[m.base.market_group_id] = mg
        mg.append(m)

    row3_num: int = 0
    total_purchase: float = 0.0
    total_purchase_volume: float = 0.0

    for group_id in material_groups.keys():
        mg: typing.List[profit.QIndustryMaterial] = material_groups.get(group_id)
        if group_id == 1857:
            mg.sort(key=lambda __m685: __m685.purchased+__m685.manufactured, reverse=True)
        else:
            mg.sort(key=lambda __m685: __m685.purchased+__m685.manufactured)
        # рисуем заголовок группы
        generate_group_header(mg[0].base.market_group_name)
        # выводим товары группы
        for m in mg:
            row3_num += 1
            # получение данных по материалу
            m3_tid: int = m.base.type_id
            m3_tnm: str = m.base.name
            m3_q = m.purchased + m.manufactured  # quantity (required)
            m3_r = m.purchased_ratio  # ratio (пропорция от требуемого кол-ва с учётом вложенных уровней)
            m3_a = m.available_in_assets  # available in assets
            m3_j = m.in_progress  # in progress (runs of jobs)
            m3_v = m.base.volume  # volume
            # получение стоимости закупа материала (или стоимость копирки/инвента чертежей)
            m3_p: typing.Optional[float] = None
            is_blueprints_group: bool = m.base.market_group_id == 2
            if not is_blueprints_group:
                if eve_jita_orders_data:
                    max_buy: typing.Optional[profit.QMarketOrder] = eve_jita_orders_data.get_max_buy_order(m3_tid)
                    if max_buy:
                        m3_p = profit.eve_ceiling_change_by_point(max_buy.price, +1)
                    else:
                        min_sell: typing.Optional[profit.QMarketOrder] = eve_jita_orders_data.get_min_sell_order(m3_tid)
                        if min_sell:
                            m3_p = min_sell.price
                            # TODO: внимание, с этой цены налог не выплачивается!
                if not m3_p:
                    m3_p = eve_esi_tools.get_material_price(m3_tid, sde_type_ids, eve_market_prices_data)
                if not m3_p:
                    m3_p = -1000000000.00  # fake price
            else:
                m3_p = m.job_cost  # blueprints * runs * job_cost
            # расчёт прогресса выполнения (постройки, сбора) материалов (m1_j пропускаем, т.к. они не готовы ещё)
            if m.available_in_assets >= m3_q:
                m3_progress = 100.0
            elif m3_q == 0:
                m3_progress = 100.0
            else:
                m3_progress = float(100.0 * float(m3_a) / m3_q)
            # получение стоимости за одну штуку
            if m.purchased:
                total_purchase += (m3_p * m3_r)
                total_purchase_volume += (m3_v * m3_r)
            # вывод наименования ресурса
            glf.write(
                '<tr>\n'
                ' <th scope="row">{num}</th>\n'
                ' <td data-copy="{nm}"><img class="icn24" src="{src}"> {nm}{me_te}</td>\n'
                ' <td>{qa}{qip}</td>\n'
                ' <td quantity="{qneed}">{qrn:,d}</td>\n'
                ' <td><div class="progress" style="margin-bottom:0px"><div class="progress-bar{prcnt100}"'
                ' role="progressbar" aria-valuenow="{prcnt}" aria-valuemin="0" aria-valuemax="100"'
                ' style="width: {prcnt}%;">{fprcnt:.1f}%</div></div></td>\n'
                ' <td align="right">{price}</td>'
                ' <td align="right">{costn}</td>'
                ' <td align="right">{qratio}</td>'
                ' <td align="right">{pratio}</td>'
                ' <td align="right" style="color:maroon;">{instance_isk}</td>'
                ' <td align="right">{volume}</td>'
                '</tr>'.format(
                    num=row3_num,
                    nm=m3_tnm,
                    me_te='',
                    src=render_html.__get_img_src(m3_tid, 32),
                    qrn=m3_q,
                    qneed=m3_q-m3_a-m3_j if m3_q > (m3_a+m3_j) else 0,
                    qa='{:,d}'.format(m3_a) if m3_a >= 0 else
                       '&infin; <small>runs</small>',
                    qip='' if m3_j == 0 else
                        '<mark>+ {}</mark>'.format(m3_j),
                    prcnt=int(m3_progress),
                    fprcnt=m3_progress,
                    prcnt100=" progress-bar-success" if m3_progress == 100 else '',
                    price='' if is_blueprints_group else
                          '{}{:,.2f}{}'.format(
                              get_grayed_material_not_purchased(m.purchased, True),
                              m3_p,
                              get_grayed_material_not_purchased(m.purchased, False),
                          ) if m3_p is not None else
                          '',
                    costn='{:,d}'.format(m3_p) if is_blueprints_group else
                          '{}{:,.2f}{}'.format(
                              get_grayed_material_not_purchased(m.purchased, True),
                              m3_p * m3_q,
                              get_grayed_material_not_purchased(m.purchased, False),
                          ) if m3_p is not None else
                          '',
                    qratio='' if is_blueprints_group else
                           '' if not m.purchased else
                           '{:,.5f}'.format(m3_r),
                    pratio='' if is_blueprints_group else
                           '' if not m.purchased or m3_p is None else
                           '{:,.1f}'.format(m3_p*m3_r+0.004999),
                    instance_isk='{}{:,.2f}{}'.format(
                                     get_grayed_material_not_purchased(False, True),
                                     m3_p / industry_plan.customized_runs,
                                     get_grayed_material_not_purchased(False, True),
                                 ) if is_blueprints_group else
                                 '' if not m.purchased else
                                 '{:,.2f}'.format((m3_p*m3_r+0.004999) / industry_plan.customized_runs),
                    volume='<strike>{:,.2f}</strike>'.format(m3_v * m3_r) if not is_blueprints_group else ''
                ))

    glf.write(f"""
</tbody>
</table>
</div> <!--table-responsive-->
  </div> <!--media-body-->
 </div> <!--media-->
<hr>
 <div class="media">
  <div class="media-left">
   <img class="media-object icn64" src="{render_html.__get_icon_src(2512, sde_icon_ids)}" alt="Общая стоимость проекта">
  </div>
  <div class="media-body">
   <h4 class="media-heading">Общая стоимость проекта</h4>
<div class="table-responsive">
<table class="table table-condensed" style="font-size:small">
<thead>
 <tr>
  <th class="active">{base_industry.product_name}</th>
  <th class="active" style="text-align:right;">Производство {industry_plan.customized_runs}шт продукта</th>
  <th class="active" style="text-align:right;">Доля 1шт продукта</th>
 </tr>
</thead>
<tbody>""")

    def generate_summary_lines(
            caption: str,
            total_summary: str,
            one_instance_summary: str):
        glf.write(f"""<tr>
 <td class="active">{caption}</td>
 <td style="text-align:right">{total_summary}</td>
 <td style="text-align:right;">{one_instance_summary}</td>
</tr>""")

    total_gross_cost: float = 0.0

    generate_summary_lines(
        'Стоимость закупки материалов, ISK',
        f'{total_purchase * 1.02:,.2f}',
        f'{(total_purchase * 1.02) / industry_plan.customized_runs:,.2f}')
    generate_summary_lines(
        '├─ Стоимость материалов, ISK',
        f'{total_purchase:,.2f}',
        f'{total_purchase / industry_plan.customized_runs:,.2f}')
    generate_summary_lines(
        '└─ Брокерская комиссия, ISK',
        f'{total_purchase * 0.02:,.2f}',
        f'{(total_purchase * 0.02) / industry_plan.customized_runs:,.2f}')

    total_gross_cost += total_purchase * 1.02

    # Rhea с 3x ORE Expanded Cargohold имеет 386'404.0 куб.м
    # до Jita дистанция 64'484 свет.лет со всеми скилами в 5 понадобится сжечь 79'353 Nitrogen Isotopes (buy 545.40 ISK)
    nitrogen_isotopes_type_id: int = 17888  # Nitrogen Isotopes
    nitrogen_isotopes_isk: typing.Optional[float] = None  # price
    if eve_jita_orders_data:
        max_buy: typing.Optional[profit.QMarketOrder] = eve_jita_orders_data.get_max_buy_order(nitrogen_isotopes_type_id)
        if max_buy:
            nitrogen_isotopes_isk = profit.eve_ceiling_change_by_point(max_buy.price, +1) * 1.02
        else:
            min_sell: typing.Optional[profit.QMarketOrder] = eve_jita_orders_data.get_min_sell_order(nitrogen_isotopes_type_id)
            if min_sell:
                nitrogen_isotopes_isk = min_sell.price  # с этой цены налог и комиссии не удерживаются
    if not nitrogen_isotopes_isk:
        # ого! в Жите топляк закончился?
        nitrogen_isotopes_isk = eve_esi_tools.get_material_price(nitrogen_isotopes_type_id, sde_type_ids, eve_market_prices_data)
    if not nitrogen_isotopes_isk:
        nitrogen_isotopes_isk = 545.40  # hardcoded price (august 2024)

    transfer_cost: float = total_purchase_volume * ((79353 * nitrogen_isotopes_isk) / 386404)
    generate_summary_lines(
        'Стоимость доставки закупаемых материалов, ISK',
        f'{transfer_cost:,.2f}',
        f'{transfer_cost / industry_plan.customized_runs:,.2f}')
    generate_summary_lines(
        '└─ Объём закупаемых материалов, m&sup3;',
        f'{total_purchase_volume:,.1f} m&sup3;',
        f'{total_purchase_volume / industry_plan.customized_runs:,.1f} m&sup3;')

    total_gross_cost += transfer_cost

    generate_summary_lines(
        'Стоимость запуска работ, ISK',
        f'{industry_plan.job_cost_accumulator.total_paid:,.2f}<br>'
        f'<span style="color:lightgray;">проверка: {linear_cost_verification.total_paid:,.2f}</span>',
        f'{industry_plan.job_cost_accumulator.total_paid / industry_plan.customized_runs:,.2f}')

    total_gross_cost += industry_plan.job_cost_accumulator.total_paid * 0.0

    total_ready_volume: float = industry_plan.base_industry.product.volume * industry_plan.customized_runs
    # TODO: total_ready_volume: float = 50000 * industry_plan.customized_runs
    total_ready_volume: float = 2500 * industry_plan.customized_runs
    transfer_cost: float = total_ready_volume * ((79353 * nitrogen_isotopes_isk) / 386404) * 1.02
    generate_summary_lines(
        'Стоимость отправки готовой продукции, ISK',
        f'{transfer_cost:,.2f}',
        f'{transfer_cost / industry_plan.customized_runs:,.2f}')
    generate_summary_lines(
        '└─ Объём готовой продукции, m&sup3;',
        f'{total_ready_volume:,.1f} m&sup3;',
        f'{total_ready_volume / industry_plan.customized_runs:,.1f} m&sup3;')

    total_gross_cost += transfer_cost

    generate_summary_lines(
        'Общая стоимость проекта, ISK',
        f'<b>{total_gross_cost:,.2f}</b>',
        f'<b>{total_gross_cost / industry_plan.customized_runs:,.2f}</b>')

    product_type_id: int = industry_plan.base_industry.product.type_id
    product_sell_order_isk: typing.Optional[float] = None
    if eve_jita_orders_data:
        min_sell: typing.Optional[profit.QMarketOrder] = eve_jita_orders_data.get_min_sell_order(product_type_id)
        if min_sell:
            product_sell_order_isk = profit.eve_ceiling_change_by_point(min_sell.price, -1)
    if not product_sell_order_isk:
        product_sell_order_isk = eve_esi_tools.get_material_price(product_type_id, sde_type_ids, eve_market_prices_data)
    if not product_sell_order_isk:
        product_sell_order_isk = 1000000000.00  # fake price

    product_sell_order_isk *= industry_plan.customized_runs
    sales_broker_fee: float = product_sell_order_isk * 0.02
    sales_tax: float = product_sell_order_isk * 0.016
    sales_profit: float = product_sell_order_isk - sales_broker_fee - sales_tax

    generate_summary_lines(
        'Доход с продаж, ISK',
        f'{sales_profit:,.2f}',
        f'{sales_profit / industry_plan.customized_runs:,.2f}')
    generate_summary_lines(
        '├─ Рыночная цена, ISK',
        f'{product_sell_order_isk:,.2f}',
        f'{product_sell_order_isk / industry_plan.customized_runs:,.2f}')
    generate_summary_lines(
        '├─ Брокерская комиссия, ISK',
        f'{sales_broker_fee:,.2f}',
        f'{sales_broker_fee / industry_plan.customized_runs:,.2f}')
    generate_summary_lines(
        '└─ Налог с продаж, ISK',
        f'{sales_tax:,.2f}',
        f'{sales_tax / industry_plan.customized_runs:,.2f}')

    generate_summary_lines(
        'Итоговый профит проекта, ISK',
        f'<b>{sales_profit-total_gross_cost:,.2f}</b>',
        f'<b>{(sales_profit-total_gross_cost) / industry_plan.customized_runs:,.2f}</b>')

    glf.write("""
</tbody>
</table>
</div> <!--table-responsive-->
  </div> <!--media-body-->
 </div> <!--media-->
</div> <!--container-fluid-->""")


def dump_industry_plan(
        # данные о продуктах, которые надо отобразить в отчёте
        industry_plan: profit.QIndustryPlan,
        # путь, где будет сохранён отчёт
        ws_dir,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        eve_market_prices_data,
        sde_icon_ids,
        # ордера, выставленные в Jita 4-4
        eve_jita_orders_data: profit.QMarketOrders,
        # индексы стоимости производства для различных систем (системы и продукция заданы в настройках роутинга)
        industry_cost_indices:  typing.List[profit.QIndustryCostIndices]):
    assert industry_plan.base_industry

    product_name: str = industry_plan.base_industry.product_name
    file_name_c2s: str = render_html.__camel_to_snake(product_name, True)
    ghf = open('{dir}/{fnm}.html'.format(dir=ws_dir, fnm=file_name_c2s), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(ghf, product_name)
        render_report(
            ghf,
            industry_plan,
            sde_type_ids,
            sde_bp_materials,
            sde_market_groups,
            eve_market_prices_data,
            sde_icon_ids,
            eve_jita_orders_data,
            industry_cost_indices)
        render_html.__dump_footer(ghf)
    finally:
        ghf.close()
