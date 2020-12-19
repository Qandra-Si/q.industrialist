import render_html
import eve_sde_tools
import eve_esi_tools


def get_blueprints_in_location(corp_bp_loc_data, place_id, hangar_num=None):
    # поиск контейнера (офиса) по указанному id
    bp1 = corp_bp_loc_data.get(str(place_id), None)
    if bp1 is None:
        return []
    if not (hangar_num is None):
        # если указан номер ангара, то пытаемся найти чертежи в указанном ангаре
        bp2 = bp1.get("CorpSAG{}".format(hangar_num), None)
        if bp1 is None:
            return []
        return bp2
    else:
        # если номер ангара не указан, то это не офис... поэтому выдаём чертежи в контейнере
        # предполагая, что place_id является номером контейнера (это может быть и не так...)
        return bp1


def is_availabe_blueprints_present(
        type_id,
        corp_bp_loc_data,
        sde_bp_materials,
        blueprint_station_ids,
        corp_assets_tree):
    # определем type_id чертежа по известному type_id материала
    blueprint_type_id, __stub01 = eve_sde_tools.get_blueprint_type_id_by_product_id(type_id, sde_bp_materials)
    # проверяем, возможно этот материал нельзя произвести с помощью чертежей?
    if blueprint_type_id is None:
        return False, False, True
    # поиск чертежей, по их type_id в списках имеющихся у корпы чертежей
    vacant_originals = vacant_copies = None
    loc_ids = corp_bp_loc_data.keys()
    for loc in loc_ids:
        loc_id = int(loc)
        # пропускаем прочие станции, на которых нет текущего stock-а и нет конвейеров (ищем свою станку)
        if not eve_esi_tools.is_location_nested_into_another(loc_id, blueprint_station_ids, corp_assets_tree):
            continue
        # проверяем состояния чертежей
        bp2 = corp_bp_loc_data[str(loc)]
        bp2_keys = bp2.keys()
        for location_flag in bp2_keys:
            bp3 = bp2[location_flag]
            bp3_keys = bp3.keys()
            for __blueprint_type_id in bp3_keys:
                if int(__blueprint_type_id) != int(blueprint_type_id):
                    continue
                bp_keys = bp3[__blueprint_type_id].keys()
                for bpk in bp_keys:
                    bp = bp3[__blueprint_type_id][bpk]
                    if not (bp["st"] is None):  # пропускаем чертежи, по которым ведётся работы
                        continue
                    if bp["cp"]:
                        vacant_copies = True
                    else:
                        vacant_originals = True
                    if not (vacant_copies is None) and vacant_copies and not (vacant_originals is None) and vacant_originals:
                        break
                if not (vacant_copies is None) and vacant_copies and not (vacant_originals is None) and vacant_originals:
                    break
        if not (vacant_copies is None) and vacant_copies and not (vacant_originals is None) and vacant_originals:
            break
    if vacant_copies is None:
        vacant_copies = False
    if vacant_originals is None:
        vacant_originals = False
    return vacant_originals, vacant_copies, False


def __dump_materials_list(
        glf,
        glyphicon_name,  # glyphicon-info-sign
        heading_name,  # Used materials in progress
        materials_list,
        with_copy_to_clipboard,
        with_horizontal_row):
    if len(materials_list) > 0:
        glf.write('<div class="qind-materials-used">')
        if with_horizontal_row:
            glf.write('<hr>\n')
        glf.write("""
<div class="media">
 <div class="media-left">
""")
        glf.write('<span class="glyphicon {}" aria-hidden="false" style="font-size: 64px;"></span>\n'.format(glyphicon_name))
        glf.write("""
 </div>
 <div class="media-body">
""")
        glf.write('<h4 class="media-heading">{}</h4>\n'.format(heading_name))
        if with_copy_to_clipboard:
            glf.write("""
  <a data-target="#" role="button" class="qind-copy-btn" data-toggle="tooltip" data-source="span">
   <button type="button" class="btn btn-default btn-xs"><span class="glyphicon glyphicon-copy" aria-hidden="true"></span> Export to multibuy</button>
  </a><br>
""")
        materials_list.sort(key=lambda bp: bp['nm'])
        for m_usd in materials_list:
            # вывод наименования ресурса
            glf.write(
                '<span style="white-space:nowrap"{qq}>'
                '<img class="icn24" src="{src}"> {q:,d} x {nm} '
                '</span>\n'.format(
                    src=render_html.__get_img_src(m_usd['id'], 32),
                    q=m_usd['q'],
                    nm=m_usd['nm'],
                    qq=' quantity="{}"'.format(m_usd['q']) if with_copy_to_clipboard else ''
                )
            )
        glf.write("""
 </div>
</div>
</div>
""")  # qind-materials-used, media, media-body


def __dump_blueprints_list_with_materials(
        glf,
        conveyor_entity,
        corp_bp_loc_data,
        corp_industry_jobs_data,
        corp_ass_loc_data,
        corp_assets_tree,
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        sde_icon_ids,
        enable_copy_to_clipboard=False):
    # получение списков контейнеров и станок из экземпляра контейнера
    blueprint_loc_ids = conveyor_entity["blueprints"]
    blueprint_station_ids = [conveyor_entity["station_id"]]
    # инициализация списка материалов, которых не хватает в производстве
    stock_not_enough_materials = []

    loc_ids = corp_bp_loc_data.keys()
    for loc in loc_ids:
        loc_id = int(loc)
        __container = next((cec for cec in blueprint_loc_ids if cec['id'] == loc_id), None)
        if __container is None:
            continue
        loc_name = __container["name"]
        blueprints_hangar_num = __container.get('hangar_num', None)
        if loc_name is None:
            # обычно это означает, что нет названия контейера, тогда проверяем, что это м.б. пара станция/ангар
            if not (blueprints_hangar_num is None):
                loc_name = 'Hangar {}'.format(blueprints_hangar_num)
        fixed_number_of_runs = __container.get("fixed_number_of_runs", None)
        # пытаемся понять где находится сток, если нет элемента stock, то это м.б. same_stock_container
        if 'stock' in conveyor_entity:
            stock_all_loc_ids = [int(ces['id']) for ces in conveyor_entity['stock']]
        elif __container.get('same_stock_container', False):
            stock_all_loc_ids = [loc_id]
        else:
            stock_all_loc_ids = []
        # формирование списка ресурсов, которые используются в производстве
        stock_resources = {}
        for salid in stock_all_loc_ids:
            salid_flags = corp_ass_loc_data.keys()
            for loc_flag in salid_flags:
                __a1s = corp_ass_loc_data[loc_flag]
                if str(salid) in __a1s:
                    __a2s = __a1s[str(salid)]
                    for itm in __a2s:
                        if str(itm) in stock_resources:
                            stock_resources[itm] = stock_resources[itm] + __a2s[itm]
                        else:
                            stock_resources.update({itm: __a2s[itm]})
        # формирование списка чертежей с учётом либо выбранного ангара, либо всех ангаров
        if not (blueprints_hangar_num is None):
            __bp2 = get_blueprints_in_location(corp_bp_loc_data, loc_id, hangar_num=blueprints_hangar_num)
        else:
            __bp2 = get_blueprints_in_location(corp_bp_loc_data, loc_id)
        if not __bp2:
            continue
        __type_keys = __bp2.keys()
        # сортировка чертежей по их названиям
        type_keys = []
        for type_id in __type_keys:
            type_keys.append({"id": int(type_id), "name": eve_sde_tools.get_item_name_by_type_id(sde_type_ids, int(type_id))})
        type_keys.sort(key=lambda bp: bp["name"])
        glf.write(
            ' <div class="panel panel-default">\n'
            '  <div class="panel-heading" role="tab" id="headingB{id}">\n'
            '   <h4 class="panel-title">\n'
            '    <a role="button" data-toggle="collapse" data-parent="#accordion" '
            '       href="#collapseB{id}" aria-expanded="true" aria-controls="collapseB{id}">{station} <mark>{nm}</mark></a>\n'
            '   </h4>\n'
            '  </div>\n'
            '  <div id="collapseB{id}" class="panel-collapse collapse" role="tabpanel" '
            'aria-labelledby="headingB{id}">\n'
            '   <div class="panel-body">\n'.format(
                id=loc_id,
                station=conveyor_entity["station"],
                nm=loc_name
            )
        )
        # инициализация скрытой таблицы, которая предназначена для сортировки чертежей по различным критериям
        glf.write("""
<div class="table-responsive">
 <table class="table table-condensed qind-blueprints-tbl">
  <tbody>
""")
        # вывод в отчёт инфорации о чертежах
        materials_summary = []
        materials_used = []
        for type_dict in type_keys:
            type_id = type_dict["id"]
            blueprint_name = type_dict["name"]
            # ---
            __activity_time = 0
            __blueprint_materials = None
            __is_reaction_formula = eve_sde_tools.is_type_id_nested_into_market_group(type_id, [1849], sde_type_ids, sde_market_groups)
            if __is_reaction_formula:  # Reaction Formulas
                __reaction = eve_sde_tools.get_blueprint_reaction_activity(sde_bp_materials, type_id)
                __blueprint_materials = __reaction["materials"]
                __activity_time = __reaction["time"]
            else:
                __manufacturing = eve_sde_tools.get_blueprint_manufacturing_activity(sde_bp_materials, type_id)
                __blueprint_materials = __manufacturing["materials"]
                __activity_time = __manufacturing["time"]
            __min_activity_time = None
            # ---
            bp_keys = __bp2[type_id].keys()
            for bpk in bp_keys:
                bp = __bp2[type_id][bpk]
                for itm in bp["itm"]:
                    __runs = itm["r"] if itm["q"] == -2 else (1 if fixed_number_of_runs is None else fixed_number_of_runs)
                    __time = __runs * __activity_time
                    if __min_activity_time is None:
                        __min_activity_time = __time
                    elif __min_activity_time > __time:
                        __min_activity_time = __time
            # ---
            glf.write(
                '<tr><td class="hidden">{nm}</td><td class="hidden">{time}</td><td>\n'
                '<div class="media">\n'
                ' <div class="media-left">\n'
                '  <img class="media-object icn64" src="{src}" alt="{nm}">\n'
                ' </div>\n'
                ' <div class="media-body">\n'
                '  <h4 class="media-heading">{nm}</h4>\n'.format(
                    src=render_html.__get_img_src(type_id, 64),
                    nm=blueprint_name,
                    time=__min_activity_time
                )
            )
            for bpk in bp_keys:
                bp = __bp2[type_id][bpk]
                is_blueprint_copy = bp["cp"]
                quantity_or_runs = bp["qr"]
                material_efficiency = bp["me"]
                time_efficiency = bp["te"]
                blueprint_status = bp["st"]
                glf.write(
                    '<div class="qind-bp-block"><span class="qind-blueprints-{status}">'
                    '<span class="label label-{cpc}">{cpn}</span>{me_te}'
                    '&nbsp;<span class="badge">{qr}{fnr}</span>\n'.format(
                        qr=quantity_or_runs,
                        fnr=' x{}'.format(fixed_number_of_runs) if not (fixed_number_of_runs is None) else "",
                        cpc='default' if is_blueprint_copy else 'info',
                        cpn='copy' if is_blueprint_copy else 'original',
                        me_te='&nbsp;<span class="label label-success">{me} {te}</span>'.format(me=material_efficiency, te=time_efficiency) if not __is_reaction_formula else "",
                        status=blueprint_status if not (blueprint_status is None) else ""
                    )
                )
                if not (blueprint_status is None):  # [ active, cancelled, delivered, paused, ready, reverted ]
                    if (blueprint_status == "active") or (blueprint_status == "delivered"):
                        glf.write('&nbsp;<span class="label label-primary">{}</span>'.format(blueprint_status))
                    elif blueprint_status == "ready":
                        glf.write('&nbsp;<span class="label label-success">{}</span>'.format(blueprint_status))
                    elif (blueprint_status == "cancelled") or (blueprint_status == "paused") or (blueprint_status == "reverted"):
                        glf.write('&nbsp;<span class="label label-warning">{}</span>'.format(blueprint_status))
                    else:
                        glf.write('&nbsp;<span class="label label-danger">{}</span>'.format(blueprint_status))
                    # ---
                    __jobs_cost = sum([i["jc"] for i in bp["itm"] if "jc" in i])
                    glf.write('&nbsp;<span class="label badge-light">{:,.1f} ISK</span>'.format(__jobs_cost))
                    # ---
                    if not (__blueprint_materials is None):
                        for m in __blueprint_materials:
                            # расчёт кол-ва материала с учётом эффективности производства
                            __need = eve_sde_tools.get_industry_material_efficiency(
                                __is_reaction_formula,
                                quantity_or_runs,
                                m["quantity"],  # сведения из чертежа
                                material_efficiency)
                            # сохраняем материалы для производства в список их суммарного кол-ва
                            bpmm_tid = int(m["typeID"])
                            bpmm_tnm = eve_sde_tools.get_item_name_by_type_id(sde_type_ids, bpmm_tid)
                            __used_dict = next((ms for ms in materials_used if ms['id'] == bpmm_tid), None)
                            if __used_dict is None:
                                __used_dict = {"id": bpmm_tid, "q": __need, "nm": bpmm_tnm}
                                materials_used.append(__used_dict)
                            else:
                                __used_dict["q"] += __need
                    # ---
                    glf.write('</br></span>')  # qind-blueprints-?
                elif __blueprint_materials is None:
                    glf.write('&nbsp;<span class="label label-warning">manufacturing impossible</span>')
                    glf.write('</br></span>')  # qind-blueprints-?
                else:
                    glf.write('</br></span>')  # qind-blueprints-?
                    glf.write('<div class="qind-materials-used">\n')  # div(materials)
                    not_enough_materials = []
                    for m in __blueprint_materials:
                        bp_manuf_need_all = 0
                        bp_manuf_need_min = 0
                        for __bp3 in bp["itm"]:
                            if is_blueprint_copy:
                                quantity_or_runs = __bp3["r"]
                            else:
                                quantity_or_runs = __bp3["q"] if __bp3["q"] > 0 else 1
                                if fixed_number_of_runs:
                                    quantity_or_runs = quantity_or_runs * fixed_number_of_runs
                            # расчёт кол-ва материала с учётом эффективности производства
                            __need = eve_sde_tools.get_industry_material_efficiency(
                                __is_reaction_formula,
                                quantity_or_runs,
                                m["quantity"],  # сведения из чертежа
                                material_efficiency)
                            # считаем общее количество материалов, необходимых для работ по этом чертежу
                            bp_manuf_need_all = bp_manuf_need_all + __need
                            # вычисляем минимально необходимое материалов, необходимых для работ хотя-бы по одному чертежу
                            bp_manuf_need_min = __need if bp_manuf_need_min == 0 else min(bp_manuf_need_min, __need)
                        bpmm_tid = int(m["typeID"])
                        bpmm_tnm = eve_sde_tools.get_item_name_by_type_id(sde_type_ids, bpmm_tid)
                        # проверка наличия имеющихся ресурсов для постройки по этому БП
                        not_available = bp_manuf_need_all
                        not_available_absolutely = True
                        if bpmm_tid in stock_resources:
                            __stock = stock_resources[bpmm_tid]
                            not_available = 0 if __stock >= not_available else not_available - __stock
                            not_available_absolutely = __stock < bp_manuf_need_min
                        # вывод наименования ресурса
                        glf.write(
                            '<span style="white-space:nowrap">'
                            '<img class="icn24" src="{src}"> {q:,d} x {nm} '
                            '</span>\n'.format(
                                src=render_html.__get_img_src(bpmm_tid, 32),
                                q=bp_manuf_need_all,
                                nm=bpmm_tnm
                            )
                        )
                        # сохраняем недостающее кол-во материалов для производства по этому чертежу
                        if not_available > 0:
                            not_enough_materials.append({"id": bpmm_tid, "q": not_available, "nm": bpmm_tnm, "absol": not_available_absolutely})
                        # сохраняем материалы для производства в список их суммарного кол-ва
                        __summary_dict = next((ms for ms in materials_summary if ms['id'] == int(m["typeID"])), None)
                        if __summary_dict is None:
                            __summary_dict = {"id": int(m["typeID"]), "q": bp_manuf_need_all, "nm": bpmm_tnm}
                            materials_summary.append(__summary_dict)
                        else:
                            __summary_dict["q"] += bp_manuf_need_all
                    glf.write('</div>\n')  # div(materials)
                    # отображение списка материалов, которых не хватает
                    if len(not_enough_materials) > 0:
                        glf.write('<div>\n')  # div(not_enough_materials)
                        for m in not_enough_materials:
                            glf.write(
                                '&nbsp;<span class="label label-{absol}">'
                                '<img class="icn24" src="{src}"> {q:,d} x {nm} '
                                '</span>\n'.format(
                                    src=render_html.__get_img_src(m["id"], 32),
                                    q=m["q"],
                                    nm=m["nm"],
                                    absol="danger" if m["absol"] else "warning"
                                )
                            )
                        glf.write('</div>\n')  # div(not_enough_materials)
                glf.write('</div>\n')  # qind-bp-block
            glf.write(
                ' </div>\n'  # media-body
                '</div>\n'  # media
                '</td></tr>\n'
            )
        glf.write("""
  </tbody>
 </table>
</div> <!--table-responsive-->
""")

        __dump_materials_list(glf, 'glyphicon-info-sign', 'Used materials in progress', materials_used, True, True)
        __dump_materials_list(glf, 'glyphicon-question-sign', 'Summary materials', materials_summary, False, True)

        # отображение в отчёте summary-информации по недостающим материалам
        if len(materials_summary) > 0:
            # поиск групп, которым принадлежат материалы, которых не хватает для завершения производства по списку
            # чертеже в этом контейнере (планетарка отдельно, композиты отдельно, запуск работ отдельно)
            material_groups = {}
            for __summary_dict in materials_summary:
                __quantity = __summary_dict["q"]
                __type_id = __summary_dict["id"]
                __item_name = __summary_dict["nm"]
                __market_group = eve_sde_tools.get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, __type_id)
                __material_dict = {"id": __type_id, "q": __quantity, "nm": __item_name}
                if str(__market_group) in material_groups:
                    material_groups[str(__market_group)].append(__material_dict)
                else:
                    material_groups.update({str(__market_group): [__material_dict]})
            # вывод списка материалов, которых не хватает для завершения производства по списку чертежей
            not_available_row_num = 1
            ms_groups = material_groups.keys()
            for ms_group_id in ms_groups:
                material_groups[ms_group_id].sort(key=lambda m: m["nm"])
                group_diplayed = False
                for __material_dict in material_groups[ms_group_id]:
                    # получение данных по материалу
                    ms_type_id = __material_dict["id"]
                    not_available = __material_dict["q"]
                    ms_item_name = __material_dict["nm"]
                    if ms_type_id in stock_resources:
                        not_available = 0 if stock_resources[ms_type_id] >= not_available else \
                            not_available - stock_resources[ms_type_id]
                    if not_available > 0:
                        # формирование выходного списка недостающих материалов
                        __stock_ne = next((ne for ne in stock_not_enough_materials if ne['id'] == ms_type_id), None)
                        if __stock_ne is None:
                            stock_not_enough_materials.append({"id": ms_type_id, "q": not_available})
                        else:
                            __stock_ne["q"] += not_available
                        # вывод сведений в отчёт
                        if not_available_row_num == 1:
                            glf.write("""
<div class="media">
 <div class="media-left">
  <span class="glyphicon glyphicon-remove-sign" aria-hidden="false" style="font-size: 64px;"></span>
 </div>
 <div class="media-body">
  <h4 class="media-heading">Not available materials</h4>
  <div class="table-responsive">
   <table class="table table-condensed table-hover">
   <thead>
    <tr>
     <th style="width:40px;">#</th>
     <th>Materials</th>
     <th>Not available</th>
     <th>In progress</th>
    </tr>
   </thead>
   <tbody>
""")
                        # выводим название группы материалов (Ship Equipment, Materials, Components, ...)
                        if not group_diplayed:
                            __grp_name = sde_market_groups[ms_group_id]["nameID"]["en"]
                            __icon_id = sde_market_groups[ms_group_id]["iconID"] if "iconID" in sde_market_groups[ms_group_id] else 0
                            # подготовка элементов управления копирования данных в clipboard
                            __copy2clpbrd = '' if not enable_copy_to_clipboard else \
                                '&nbsp;<a data-target="#" role="button" class="qind-copy-btn" data-source="table"' \
                                '  data-toggle="tooltip"><button type="button" class="btn btn-default btn-xs"><span' \
                                '  class="glyphicon glyphicon-copy" aria-hidden="true"></span> Export to multibuy</button></a>'
                            glf.write(
                                '<tr>\n'
                                # ' <td class="active" colspan="4"><img class="icn24" src="{icn}" style="display:inline;">&nbsp;<strong class="text-primary">{nm}</strong><!--{id}-->{clbrd}</td>\n'
                                ' <td class="active" colspan="4"><strong>{nm}</strong><!--{id}-->{clbrd}</td>\n'
                                '</tr>'.
                                format(nm=__grp_name,
                                       # icn=__get_icon_src(__icon_id, sde_icon_ids),
                                       id=ms_group_id,
                                       clbrd=__copy2clpbrd))
                            group_diplayed = True
                        # получаем список работ, которые выдутся с этим материалом, а результаты сбрабываются в stock-ALL
                        jobs = [j for j in corp_industry_jobs_data if
                                    (j["product_type_id"] == ms_type_id) and
                                    (j['output_location_id'] in stock_all_loc_ids)]
                        in_progress = 0
                        for j in jobs:
                            in_progress = in_progress + j["runs"]
                        # умножаем на кол-во производимых материалов на один run
                        __stub01, __bp_dict = eve_sde_tools.get_blueprint_type_id_by_product_id(ms_type_id, sde_bp_materials)
                        if not (__bp_dict is None):
                            in_progress *= __bp_dict["activities"]["manufacturing"]["products"][0]["quantity"]
                        # получаем список чертежей, которые имеются в распоряжении корпорации для постройки этих материалов
                        vacant_originals, vacant_copies, not_a_product = is_availabe_blueprints_present(
                            ms_type_id,
                            corp_bp_loc_data,
                            sde_bp_materials,
                            blueprint_station_ids,
                            corp_assets_tree)
                        # формируем информационные тэги по имеющимся (вакантным) цертежам для запуска производства
                        vacant_originals_tag = ""
                        vacant_copies_tag = ""
                        absent_blueprints_tag = ""
                        if not_available > in_progress:
                            if not not_a_product and vacant_originals:
                                vacant_originals_tag = ' <span class="label label-info">original</span>'
                            if not not_a_product and vacant_copies:
                                vacant_copies_tag = ' <span class="label label-default">copy</span>'
                            if not not_a_product and not vacant_originals and not vacant_copies:
                                absent_blueprints_tag = ' <span class="label label-danger">no blueprints</span>'
                        # подготовка элементов управления копирования данных в clipboard
                        __copy2clpbrd = '' if not enable_copy_to_clipboard else \
                            '&nbsp;<a data-target="#" role="button" data-copy="{nm}" class="qind-copy-btn" data-source="table"' \
                            '  data-toggle="tooltip"><span class="glyphicon glyphicon-copy"'\
                            '  aria-hidden="true"></span></a>'. \
                            format(nm=ms_item_name)
                        # вывод сведений в отчёт
                        glf.write(
                            '<tr>\n'
                            ' <th scope="row">{num}</th>\n'
                            ' <td><img class="icn24" src="{src}"> {nm}{clbrd}</td>\n'
                            ' <td quantity="{q}">{q:,d}{original}{copy}{absent}</td>\n'
                            ' <td>{inp}</td>\n'
                            '</tr>'.
                            format(num=not_available_row_num,
                                   src=render_html.__get_img_src(ms_type_id, 32),
                                   q=not_available,
                                   inp='{:,d}'.format(in_progress) if in_progress > 0 else '',
                                   nm=ms_item_name,
                                   clbrd=__copy2clpbrd,
                                   original=vacant_originals_tag,
                                   copy=vacant_copies_tag,
                                   absent=absent_blueprints_tag)
                        )
                        not_available_row_num = not_available_row_num + 1
            if not_available_row_num != 1:
                glf.write("""
   </tbody>
   </table>
  </div> <!--table-responsive-->
 </div> <!--media-body-->
</div> <!--media-->
""")

        glf.write("""
   </div> <!--panel-body-->
  </div> <!--panel-collapse-->
 </div> <!--panel-->
""")

    return stock_not_enough_materials


def __dump_conveyor_stock_all(
        glf,
        corp_industry_jobs_data,
        corp_ass_loc_data,
        materials_for_bps,
        research_materials_for_bps,
        sde_type_ids,
        sde_market_groups,
        stock_all_loc_ids,
        stock_not_enough_materials):
    if stock_all_loc_ids is None:
        return
    # формирование списка ресурсов, которые используются в производстве
    stock_resources = {}
    loc_flags = corp_ass_loc_data.keys()
    for loc_flag in loc_flags:
        __a1 = corp_ass_loc_data[loc_flag]
        for loc_id in __a1:
            if not (int(loc_id) in stock_all_loc_ids):
                continue
            __a2 = __a1[str(loc_id)]
            __a2_keys = __a2.keys()
            for __a3 in __a2_keys:
                __type_id = int(__a3)
                __quantity = __a2[__type_id]
                # определяем группу, которой принадлежат материалы
                __market_group = eve_sde_tools.get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, __type_id)
                if str(__market_group) in stock_resources:
                    __stock_group = stock_resources[str(__market_group)]
                else:
                    __group_name = sde_market_groups[str(__market_group)]["nameID"]["en"] if str(__market_group) in sde_market_groups else None  # устарел sde?
                    if not (__group_name is None):
                        __stock_group = {"name": __group_name, "items": []}
                        stock_resources.update({str(__market_group): __stock_group})
                    else:
                        __stock_group = {"name": "Unknown", "items": []}
                        stock_resources.update({"0": __stock_group})
                # пополняем список материалов в группе
                __resource_dict = next((r for r in __stock_group["items"] if r['id'] == __type_id), None)
                if __resource_dict is None:
                    __name = sde_type_ids[str(__type_id)]["name"]["en"] if str(__type_id) in sde_type_ids else str(__type_id)
                    __resource_dict = {"id": __type_id,
                                       "name": __name,
                                       "q": __quantity}
                    __stock_group["items"].append(__resource_dict)
                else:
                    __resource_dict["q"] += __quantity
    # пополняем список ресурсом записями с недостающим (отсутствующим количеством)
    for ne in stock_not_enough_materials:
        __type_id = ne["id"]
        # определяем группу, которой принадлежат материалы
        __market_group = eve_sde_tools.get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, __type_id)
        if str(__market_group) in stock_resources:
            __stock_group = stock_resources[str(__market_group)]
        else:
            __stock_group = {"name": sde_market_groups[str(__market_group)]["nameID"]["en"], "items": []}
            stock_resources.update({str(__market_group): __stock_group})
        __resource_dict = next((r for r in __stock_group["items"] if r['id'] == __type_id), None)
        # пополняем список материалов в группе
        if __resource_dict is None:
            __name = sde_type_ids[str(__type_id)]["name"]["en"] if str(__type_id) in sde_type_ids else str(__type_id)
            __resource_dict = {"id": __type_id,
                               "name": __name,
                               "q": 0}
            __stock_group["items"].append(__resource_dict)

    # сортируем материалы по названию
    stock_keys = stock_resources.keys()
    for stock_key in stock_keys:
        stock_resources[str(stock_key)]["items"].sort(key=lambda r: r["name"])

    glf.write("""
<style>
#tblStockAll tr {
  font-size: small;
}
.badge-light {
  color: #212529;
  background-color: #f8f9fa;
}
</style>

<div class="table-responsive">
 <table id="tblStockAll" class="table table-condensed table-hover">
<thead>
 <tr>
  <th>#</th>
  <th>Item</th>
  <th>In stock</th>
  <th>Not available</th>
  <th>In progress</th>
 </tr>
</thead>
<tbody>""")

    row_num = 1
    stock_keys = stock_resources.keys()
    for stock_key in stock_keys:
        __group_dict = stock_resources[str(stock_key)]
        glf.write(
            '<tr>\n'
            ' <td class="active" colspan="5"><strong>{nm}</strong></td>\n'
            '</tr>'.
            format(nm=__group_dict["name"]))
        for __resource_dict in __group_dict["items"]:
            __type_id = __resource_dict["id"]
            __quantity = __resource_dict["q"]
            # получаем статистику по текущим работам, считаем сколько производится этих материалов?
            jobs = [j for j in corp_industry_jobs_data if
                    (j["product_type_id"] == __type_id) and
                    (j['output_location_id'] in stock_all_loc_ids)]
            in_progress = 0
            for j in jobs:
                in_progress = in_progress + j["runs"]
            # получаем статистику по недостающим материалам
            not_enough = next((ne for ne in stock_not_enough_materials if ne['id'] == __type_id), None)
            # проверяем списки метариалов, используемых в исследованиях и производстве
            material_tag = ""
            if __type_id in materials_for_bps:
                pass
            elif __type_id in research_materials_for_bps:
                material_tag = ' <span class="label label-warning">research material</span></small>'
            else:
                material_tag = ' <span class="label label-danger">non material</span></small>'
            # формируем строку таблицы - найден нужный чертёж в ассетах
            glf.write(
                '<tr>'
                '<th scope="row">{num}</th>'
                '<td>{nm}{mat_tag}</td>'
                '<td align="right">{q}</td>'
                '<td align="right">{ne}</td>'
                '<td align="right">{ip}</td>'
                '</tr>\n'.
                format(num=row_num,
                       nm=__resource_dict["name"],
                       mat_tag=material_tag,
                       q="" if __quantity == 0 else '{:,d}'.format(__quantity),
                       ne="" if not_enough is None else '{:,d}'.format(not_enough["q"]),
                       ip="" if in_progress == 0 else '{:,d}'.format(in_progress))
            )
            row_num = row_num + 1

    glf.write("""
</tbody>     
 </table>     
</div>     
""")


def __dump_corp_conveyor(
        glf,
        conveyour_entities,
        corp_bp_loc_data,
        corp_industry_jobs_data,
        corp_ass_names_data,
        corp_ass_loc_data,
        corp_assets_tree,
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        sde_icon_ids,
        materials_for_bps,
        research_materials_for_bps):
    glf.write("""
<style>
.qind-blueprints-tbl>tbody>tr>td {
  padding: 4px;
  border-top: none;
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
       <li><a id="btnToggleImpossible" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowImpossible"></span> Show impossible to produce</a></li>
       <li><a id="btnToggleActive" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowActive"></span> Show active blueprints</a></li>
       <li><a id="btnToggleMaterials" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowMaterials"></span> Show used materials</a></li>
       <li><a id="btnToggleLegend" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowLegend"></span> Show legend</a></li>
       <li role="separator" class="divider"></li>
       <li><a id="btnResetOptions" data-target="#" role="button">Reset options</a></li>
      </ul>
    </li>
    <li><a data-target="#modalStockAll" role="button" data-toggle="modal">Stock All</a></li>
   </ul>
   <form class="navbar-form navbar-right">
    <label>Sorting:&nbsp;</label>
    <div class="btn-group" role="group" aria-label="Sorting">
     <button id="btnSortByName" type="button" class="btn btn-default active">Name</button>
     <button id="btnSortByTime" type="button" class="btn btn-default">Duration</button>
    </div>
   </form>
  </div>
 </div>
</nav>
<div class="container-fluid">
 <!-- BEGIN: collapsable group (locations) -->
 <div class="panel-group" id="accordion" role="tablist" aria-multiselectable="true">
""")

    stock_not_enough_materials = None
    for __conveyor_entity in conveyour_entities:
        __stock_not_enough_materials = __dump_blueprints_list_with_materials(
            glf,
            __conveyor_entity,
            corp_bp_loc_data,
            corp_industry_jobs_data,
            corp_ass_loc_data,
            corp_assets_tree,
            sde_type_ids,
            sde_bp_materials,
            sde_market_groups,
            sde_icon_ids,
            enable_copy_to_clipboard=True)
        if stock_not_enough_materials is None:
            stock_not_enough_materials = __stock_not_enough_materials

    glf.write("""
 </div>
 <!-- END: collapsable group (locations) -->
""")

    if conveyour_entities:
        # получение списков контейнеров и станок из экземпляра контейнера
        conveyor_entity = conveyour_entities[0]
        if 'stock' in conveyor_entity:
            stock_all_loc_ids = [int(ces["id"]) for ces in conveyor_entity["stock"]]
            # создаём заголовок модального окна, где будем показывать список имеющихся
            # материалов в контейнере "..stock ALL"
            render_html.__dump_any_into_modal_header_wo_button(
                glf,
                conveyor_entity["stock"][0]["name"],
                'StockAll')
            # формируем содержимое модального диалога
            __dump_conveyor_stock_all(
                glf,
                corp_industry_jobs_data,
                corp_ass_loc_data,
                materials_for_bps,
                research_materials_for_bps,
                sde_type_ids,
                sde_market_groups,
                stock_all_loc_ids,
                stock_not_enough_materials)
            # закрываем footer модального диалога
            render_html.__dump_any_into_modal_footer(glf)

    glf.write("""
<div id="legend-block">
 <hr>
 <h4>Legend</h4>
 <p>
  <span class="label label-default">copy</span>&nbsp;<span class="label label-success">2 4</span>&nbsp;<span
   class="badge">150</span> - blueprints <strong>copies</strong> with <strong>2</strong> material efficiency and
   <strong>4</strong> time efficiency with total of <strong>150</strong> runs.
 </p>
 <p>
  <span class="label label-info">original</span>&nbsp;<span class="label label-success">10 20</span>&nbsp;<span
   class="badge">2</span>&nbsp;<span class="label label-primary">active</span> - <strong>two</strong>
   <strong>original</strong> blueprints with <strong>10</strong> material efficiency and <strong>20</strong> time efficiency,
   production is currently <strong>active</strong>.
 </p>
""")
    glf.write('<p>'
              '<span style="white-space:nowrap"><img class="icn24" src="{src}"> 30 x Ice Harvester I </span>'
              '&nbsp;<span class="label label-warning"><img class="icn24" src="{src}"> 6 x Ice Harvester I </span>&nbsp;-'
              '&nbsp;<strong>30</strong> items used in the production, the items are missing <strong>6</strong>.'
              '</p>'
              '<p>'
              '<span style="white-space:nowrap"><img class="icn24" src="{src}"> 30 x Ice Harvester I </span>'
              '&nbsp;<span class="label label-danger"><img class="icn24" src="{src}"> 29 x Ice Harvester I </span>&nbsp;-'
              '&nbsp;missing number of items, such that it is not enough to run at least one blueprint copy.'
              '<p>'.
              format(src=render_html.__get_img_src(16278, 32)))
    glf.write("""
 <p>
  <span class="label label-info">original</span>, <span class="label label-default">copy</span>,
  <span class="label label-danger">no blueprints</span> - possible labels that reflect the presence of vacant blueprints
  in the hangars of the station (<i>Not available materials</i> section).
 </p>
</div>
</div>
<script>
  // Conveyor Options dictionaries
  var g_tbl_col_orders = [-1,+1]; // -1:desc, +1:asc
  var g_tbl_col_types = [0,1]; // 0:str, 1:num, 2:x-data
  // Conveyor Options storage (prepare)
  ls = window.localStorage;

  // Conveyor Options storage (init)
  function resetOptionsMenuToDefault() {
    if (!ls.getItem('Show Legend')) {
      ls.setItem('Show Legend', 1);
    }
    if (!ls.getItem('Show Impossible')) {
      ls.setItem('Show Impossible', 1);
    }
    if (!ls.getItem('Show Active')) {
      ls.setItem('Show Active', 1);
    }
    if (!ls.getItem('Show Materials')) {
      ls.setItem('Show Materials', 1);
    }
  }
  // Conveyor Options storage (rebuild menu components)
  function rebuildOptionsMenu() {
    show = ls.getItem('Show Legend');
    if (show == 1)
      $('#imgShowLegend').removeClass('hidden');
    else
      $('#imgShowLegend').addClass('hidden');
    show = ls.getItem('Show Impossible');
    if (show == 1)
      $('#imgShowImpossible').removeClass('hidden');
    else
      $('#imgShowImpossible').addClass('hidden');
    show = ls.getItem('Show Active');
    if (show == 1)
      $('#imgShowActive').removeClass('hidden');
    else
      $('#imgShowActive').addClass('hidden');
    show = ls.getItem('Show Materials');
    if (show == 1)
      $('#imgShowMaterials').removeClass('hidden');
    else
      $('#imgShowMaterials').addClass('hidden');
    sort_by = ls.getItem('Sort By');
    if ((sort_by === null) || (sort_by == 0)) {
      $('#btnSortByName').addClass('active');
      $('#btnSortByTime').removeClass('active');
    } else if (sort_by == 1) {
      $('#btnSortByName').removeClass('active');
      $('#btnSortByTime').addClass('active');
    }
  }
  // Conveyor media body visibility toggler
  function toggleMediaVisibility(media, show_impossible, show_active) {
    var mbody = media.find('div.media-body');
    var visible = false;
    mbody.find('div.qind-bp-block').each(function() {
      var bp_block = $(this);
      var non_active = true;
      bp_block.find('span.qind-blueprints-active').each(function() {
        non_active = false;
        //alert(mbody.find('h4.media-heading').html() + " " + $(this).text());
        if (show_active == 0)
          bp_block.addClass('hidden');
        else {
          bp_block.removeClass('hidden');
          visible = true;
        }
      })
      if (non_active) {
        var non_danger = true;
        bp_block.find('span.label-danger').each(function() {
          non_danger = false;
          //alert(mbody.find('h4.media-heading').html() + " " + $(this).text());
          if (show_impossible == 0)
            bp_block.addClass('hidden');
          else {
            bp_block.removeClass('hidden');
            visible = true;
          }
        })
        if (non_danger) visible = true;
      }
    })
    if (visible)
      media.closest('tr').removeClass('hidden');
    else
      media.closest('tr').addClass('hidden');
  }
  // Conveyor table sorter
  function sortConveyor(table, order, what, typ) {
    var asc = order > 0;
    var col = 'td:eq('+what.toString()+')';
    var tbody = table.find('tbody');
    tbody.find('tr').sort(function(a, b) {
      var keyA, keyB;
      if (typ == 2) {
        keyA = parseFloat($(col, a).attr('x-data'));
        keyB = parseFloat($(col, b).attr('x-data'));
        if (isNaN(keyA)) keyA = 0;
        if (isNaN(keyB)) keyB = 0;
        return asc ? (keyA - keyB) : (keyB - keyA);
      }
      else {
        keyA = $(col, a).text();
        keyB = $(col, b).text();
        if (typ == 1) {
          keyA = parseInt(keyA, 10);
          keyB = parseInt(keyB, 10);
          if (isNaN(keyA)) keyA = 0;
          if (isNaN(keyB)) keyB = 0;
          return asc ? (keyA - keyB) : (keyB - keyA);
        } 
      }
      _res = (keyA < keyB) ? -1 : ((keyA > keyB) ? 1 : 0);
      if (asc) _res = -_res;
      return _res;
    }).appendTo(tbody);
  }
  // Conveyor Options storage (rebuild body components)
  function rebuildBody() {
    show = ls.getItem('Show Legend');
    if (show == 1)
      $('#legend-block').removeClass('hidden');
    else
      $('#legend-block').addClass('hidden');
    show_impossible = ls.getItem('Show Impossible');
    show_active = ls.getItem('Show Active');
    if ((show_impossible == 1) && (show_active == 1)) {
      $('div.qind-bp-block').each(function() { $(this).removeClass('hidden'); })
      $('div.media').each(function() { $(this).closest('tr').removeClass('hidden'); })
    } else {
      $('div.media').each(function() { toggleMediaVisibility($(this), show_impossible, show_active); })
    }
    show = ls.getItem('Show Materials');
    $('div.qind-materials-used').each(function() {
      if (show == 1)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
    sort_by = ls.getItem('Sort By');
    sort_by = (sort_by === null) ? 0 : sort_by;
    $('table.qind-blueprints-tbl').each(function() {
      sortConveyor($(this),g_tbl_col_orders[sort_by],sort_by,g_tbl_col_types[sort_by]);
    })
  }
  // Conveyor Options menu and submenu setup
  function toggleMenuOption(name) {
    show = (ls.getItem(name) == 1) ? 0 : 1;
    ls.setItem(name, show);
    rebuildOptionsMenu();
    rebuildBody();
  }
  $(document).ready(function(){
    $('#btnToggleLegend').on('click', function () { toggleMenuOption('Show Legend'); });
    $('#btnToggleImpossible').on('click', function () { toggleMenuOption('Show Impossible'); });
    $('#btnToggleActive').on('click', function () { toggleMenuOption('Show Active'); });
    $('#btnToggleMaterials').on('click', function () { toggleMenuOption('Show Materials'); });
    $('#btnResetOptions').on('click', function () {
      ls.clear();
      resetOptionsMenuToDefault();
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnSortByName').on('click', function () {
      ls.setItem('Sort By', 0);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnSortByTime').on('click', function () {
      ls.setItem('Sort By', 1);
      rebuildOptionsMenu();
      rebuildBody();
    });
    // first init
    resetOptionsMenuToDefault();
    rebuildOptionsMenu();
    rebuildBody();
    // Working with clipboard
    $('a.qind-copy-btn').each(function() {
      $(this).tooltip();
    })
    $('a.qind-copy-btn').bind('click', function () {
      var data_copy = $(this).attr('data-copy');
      if (data_copy === undefined) {
        var data_source = $(this).attr('data-source');
        if (data_source == 'table') {
          var tr = $(this).parent().parent();
          var tbody = tr.parent();
          var rows = tbody.children('tr');
          var start_row = rows.index(tr);
          data_copy = '';
          rows.each( function(idx) {
            if (!(start_row === undefined) && (idx > start_row)) {
              var td = $(this).find('td').eq(0);
              if (!(td.attr('class') === undefined))
                start_row = undefined;
              else {
                if (data_copy) data_copy += "\\n"; 
                data_copy += td.find('a').attr('data-copy') + "\\t" + $(this).find('td').eq(1).attr('quantity');
              }
            }
          });
        } else if (data_source == 'span') {
          var div = $(this).parent();
          var spans = div.children('span');
          data_copy = '';
          spans.each( function(idx) {
            var span = $(this);
            if (data_copy) data_copy += "\\n";
            var txt = span.text();
            data_copy += txt.substring(txt.indexOf(' x ')+3) + "\\t" + span.attr('quantity');
          });
        }
      }
      var $temp = $("<textarea>");
      $("body").append($temp);
      $temp.val(data_copy).select();
      try {
        success = document.execCommand("copy");
        if (success) {
          $(this).trigger('copied', ['Copied!']);
        }
      } finally {
        $temp.remove();
      }
    });
    $('a.qind-copy-btn').bind('copied', function(event, message) {
      $(this).attr('title', message)
        .tooltip('fixTitle')
        .tooltip('show')
        .attr('title', "Copy to clipboard")
        .tooltip('fixTitle');
    });
    if( /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ) {
      // какой-то код ...
      $('a.qind-copy-btn').each(function() {
        $(this).addClass('hidden');
      })
    }
  });
</script>
""")


def dump_conveyor_into_report(
        # путь, где будет сохранён отчёт
        ws_dir,
        # настройки генерации отчёта
        conveyour_entities,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        sde_icon_ids,
        # esi данные, загруженные с серверов CCP
        corp_industry_jobs_data,
        corp_ass_names_data,
        corp_ass_loc_data,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_bp_loc_data,
        corp_assets_tree,
        materials_for_bps,
        research_materials_for_bps):
    glf = open('{dir}/conveyor.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(glf, "Conveyor")
        __dump_corp_conveyor(
            glf,
            conveyour_entities,
            corp_bp_loc_data,
            corp_industry_jobs_data,
            corp_ass_names_data,
            corp_ass_loc_data,
            corp_assets_tree,
            sde_type_ids,
            sde_bp_materials,
            sde_market_groups,
            sde_icon_ids,
            materials_for_bps,
            research_materials_for_bps)
        render_html.__dump_footer(glf)
    finally:
        glf.close()
