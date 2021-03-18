import render_html
import eve_sde_tools
import eve_efficiency


def __dump_corp_capital(
        glf,
        # настройки генерации отчёта
        report_options,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        sde_icon_ids,
        # esi данные, загруженные с серверов CCP
        corp_assets_data,
        corp_industry_jobs_data,
        corp_blueprints_data,
        eve_market_prices_data):
    product_name = report_options["product"]
    blueprint_containter_ids = [c["id"] for c in report_options["blueprints"]]
    stock_containter_ids = [c['id'] for c in report_options["stock"]]
    stock_containter_flag_ids = [{'id': c['id'], 'flag': c['flag']} for c in report_options['stock'] if 'flag' in c]
    enable_copy_to_clipboard = True

    __type_id = eve_sde_tools.get_type_id_by_item_name(sde_type_ids, product_name)
    if __type_id is None:
        return
    __capital_blueprint_type_id, __capital_blueprint_materials = eve_sde_tools.get_blueprint_type_id_by_product_id(__type_id, sde_bp_materials)
    __is_reaction_formula = eve_sde_tools.is_type_id_nested_into_market_group(__type_id, [1849], sde_type_ids, sde_market_groups)

    glf.write("""
<div class="container-fluid">
<div class="media">
 <div class="media-left">
""")

    glf.write('  <img class="media-object icn64" src="{src}" alt="{nm}">\n'
              ' </div>\n'
              ' <div class="media-body">\n'
              '  <h4 class="media-heading">{nm}</h4>\n'
              '<p>\n'
              'EveUniversity {nm} wiki: <a href="https://wiki.eveuniversity.org/{nm}">https://wiki.eveuniversity.org/{nm}</a><br/>\n'
              'EveMarketer {nm} tradings: <a href="https://evemarketer.com/types/{pid}">https://evemarketer.com/types/{pid}</a><br/>\n'
              'EveMarketer {nm} Blueprint tradings: <a href="https://evemarketer.com/types/{bid}">https://evemarketer.com/types/{bid}</a><br/>\n'
              'Adam4EVE {nm} manufacturing calculator: <a href="https://www.adam4eve.eu/manu_calc.php?typeID={bid}">https://www.adam4eve.eu/manu_calc.php?typeID={bid}</a><br/>\n'
              'Adam4EVE {nm} price history: <a href="https://www.adam4eve.eu/commodity.php?typeID={pid}">https://www.adam4eve.eu/commodity.php?typeID={pid}</a><br/>\n'
              'Adam4EVE {nm} Blueprint price history: <a href="https://www.adam4eve.eu/commodity.php?typeID={bid}">https://www.adam4eve.eu/commodity.php?typeID={bid}</a>\n'.
              format(nm=product_name,
                     src=render_html.__get_img_src(__type_id, 64),
                     pid=__type_id,
                     bid=__capital_blueprint_type_id))

    # создаём запись несуществующего пока чертежа
    __capital_blueprint_dict = {
        "cp": True,  # блюпринт на титан - копия
        "qr": 1,
        "me": 0,
        "te": 0,
        "st": None,
        "id": None
    }
    for b in corp_blueprints_data:
        __type_id = int(b["type_id"])
        if __capital_blueprint_type_id != __type_id:
            continue
        # __location_id = int(b["location_id"])
        # if not (__location_id in blueprint_containter_ids):
        #     continue
        if (__capital_blueprint_dict["me"] < b["material_efficiency"]) or (__capital_blueprint_dict["id"] is None):
            __quantity = int(b["quantity"])
            # A range of numbers with a minimum of -2 and no maximum value where -1 is an original and -2 is a copy.
            # It can be a positive integer if it is a stack of blueprint originals fresh from the market (e.g. no
            # activities performed on them yet).
            __is_blueprint_copy = __quantity == -2
            __capital_blueprint_dict = {
                "cp": __is_blueprint_copy,
                "me": b["material_efficiency"],
                "te": b["time_efficiency"],
                "qr": b["runs"] if __is_blueprint_copy else (1 if __quantity == -1 else __quantity),
                "id": b["item_id"]
            }
            print('Found {} Blueprint: '.format(product_name), __capital_blueprint_dict)

    # __capital_is_blueprint_copy = __capital_blueprint_dict["cp"]
    __capital_material_efficiency = __capital_blueprint_dict["me"]
    # __capital_time_efficiency = __capital_blueprint_dict["te"]
    # __capital_blueprint_status = __capital_blueprint_dict["st"]
    __capital_quantity_or_runs = __capital_blueprint_dict["qr"]

    glf.write("""
</p>
  </div> <!--media-body-->
 </div> <!--media-->
<hr>
 <div class="media">
  <div class="media-left">
""")
    glf.write('  <img class="media-object icn64" src="{src}" alt="Summary raw materials">\n'.
              format(src=render_html.__get_icon_src(1436, sde_icon_ids)))  # Manufacture & Research
    glf.write("""
  </div>
  <div class="media-body">
   <h4 class="media-heading">Manufacturing materials</h4>
""")
    for m in __capital_blueprint_materials["activities"]["manufacturing"]["materials"]:
        bpmm_used = int(m["quantity"])
        bpmm_tid = int(m["typeID"])
        bpmm_tnm = eve_sde_tools.get_item_name_by_type_id(sde_type_ids, bpmm_tid)
        # вывод наименования ресурса
        glf.write(
            '<span style="white-space:nowrap">'
            '<img class="icn24" src="{src}"> {q:,d} x {nm} '
            '</span>\n'.format(
                src=render_html.__get_img_src(bpmm_tid, 32),
                q=bpmm_used,
                nm=bpmm_tnm
            )
        )

    glf.write("""
  </div> <!--media-body-->
 </div> <!--media-->
<hr>
 <div class="media">
  <div class="media-left">
""")
    glf.write('<img class="media-object icn64" src="{src}" alt="{nm} Components">\n'.
              format(src=render_html.__get_icon_src(2863, sde_icon_ids), nm=product_name))  # Standard Capital Ship Components
    glf.write("""
  </div>
  <div class="media-body">
""")
    glf.write('<h4 class="media-heading">{nm} Components</h4>\n'.
              format(nm=product_name))  # Standard Capital Ship Components
   
    glf.write("""
<p><var>Efficiency</var> = <var>Required</var> * (100 - <var>material_efficiency</var> - 1 - 4.2) / 100,<br/>
where <var>material_efficiency</var> for unknown and unavailable blueprint is 0.</p>
<div class="table-responsive">
 <table class="table table-condensed" style="font-size:small">
<thead>
 <tr>
  <th style="width:40px;">#</th>
  <th>Materials</th>
  <th>Available +<br/>In progress</th>
  <th>Standard</th>
  <th>Efficiency</th>
  <th>Required<br/>(Not enough)</th>
 </tr>
</thead>
<tbody>
""")

    materials_summary = []

    row1_num = 0
    # debug = __capital_blueprint_materials["activities"]["manufacturing"]["materials"][:]
    # debug.append({"typeID": 11186, "quantity": 15})
    # debug.append({"typeID": 41332, "quantity": 10})
    for m1 in __capital_blueprint_materials["activities"]["manufacturing"]["materials"]:
        row1_num = row1_num + 1
        bpmm1_tid = int(m1["typeID"])
        bpmm1_tnm = eve_sde_tools.get_item_name_by_type_id(sde_type_ids, bpmm1_tid)
        bpmm1_standard = int(m1["quantity"])
        bpmm1_efficiency = bpmm1_standard  # поправка на эффективность материалов
        bpmm1_blueprint_type_id, bpmm1_blueprint_materials = eve_sde_tools.get_blueprint_type_id_by_product_id(bpmm1_tid, sde_bp_materials)
        # поиск чертежей, имеющихся в наличии у корпорации
        bpmm1_blueprints = []
        if not (bpmm1_blueprint_type_id is None):
            for b in corp_blueprints_data:
                __type_id = int(b["type_id"])
                if bpmm1_blueprint_type_id != __type_id:
                    continue
                __location_id = int(b["location_id"])
                if not (__location_id in blueprint_containter_ids):
                    continue
                __quantity = int(b["quantity"])
                # A range of numbers with a minimum of -2 and no maximum value where -1 is an original and -2 is a copy.
                # It can be a positive integer if it is a stack of blueprint originals fresh from the market (e.g. no
                # activities performed on them yet).
                __is_blueprint_copy = __quantity == -2
                __bp_dict = {
                    "cp": __is_blueprint_copy,
                    "me": b["material_efficiency"],
                    "te": b["time_efficiency"],
                    "qr": b["runs"] if __is_blueprint_copy else (1 if __quantity == -1 else __quantity)
                }
                bpmm1_blueprints.append(__bp_dict)
        # подсчёт кол-ва имеющихся в наличии материалов
        bpmm1_available = 0
        for a in corp_assets_data:
            __location_id = int(a["location_id"])
            if not (__location_id in stock_containter_ids):
                continue
            __stock_flag_dict = next((c for c in stock_containter_flag_ids if c['id'] == __location_id), None)
            if not (__stock_flag_dict is None):
                if not (__stock_flag_dict['flag'] == a['location_flag']):
                    continue
            __type_id = int(a["type_id"])
            if bpmm1_tid != __type_id:
                continue
            __quantity = int(a["quantity"])
            bpmm1_available += __quantity
        # получаем список работ, которые ведутся с материалами
        bpmm1_in_progress = 0
        for j in corp_industry_jobs_data:
            __type_id = j["product_type_id"]
            if bpmm1_tid != __type_id:
                continue
            __runs = int(j["runs"])
            bpmm1_in_progress += __runs
        # расчёт кол-ва материала с учётом эффективности производства
        bpmm1_efficiency = eve_efficiency.get_industry_material_efficiency(
            'reaction' if __is_reaction_formula else 'manufacturing',
            1,
            bpmm1_standard,  # сведения из чертежа
            __capital_material_efficiency)
        # расчёт материалов, которые предстоит построить (с учётом уже имеющихся запасов)
        bpmm1_not_enough = bpmm1_efficiency - bpmm1_available - bpmm1_in_progress
        if bpmm1_not_enough < 0:
            bpmm1_not_enough = 0
        # вывод наименования ресурса
        glf.write(
            '<tr class="active">\n'
            ' <th scope="row">{num}</th>\n'
            ' <td><img class="icn24" src="{src}"> {nm}</td>\n'
            ' <td>{qa:,d}{qip}</td>\n'
            ' <td>{qs:,d}</td>\n'
            ' <td>{qe:,d}</td>\n'
            ' <td>{qne:,d}</td>\n'
            '</tr>'.
            format(
                num=row1_num,
                nm=bpmm1_tnm,
                src=render_html.__get_img_src(bpmm1_tid, 32),
                qs=bpmm1_standard,
                qe=bpmm1_efficiency,
                qa=bpmm1_available,
                qip="" if bpmm1_in_progress == 0 else '<mark>+ {}</mark>'.format(bpmm1_in_progress),
                qne=bpmm1_not_enough
            )
        )
        # добавляем в summary сами материалы (продукты первого уровня)
        materials_summary.append({"id": bpmm1_tid,
                                  "nm": bpmm1_tnm,
                                  "q": bpmm1_efficiency,
                                  "a": bpmm1_available,
                                  "j": bpmm1_in_progress})
        # спускаемся на уровень ниже и выводим необходимое количество материалов для производства текущего
        # проверяем, что для текущего материала существуют чертежи для производства
        if not (bpmm1_blueprint_type_id is None):
            row2_num = 0
            # добавление в список материалов чертежей с известным кол-вом run-ов
            materials_summary.append({"id": bpmm1_blueprint_type_id,
                                      "q": bpmm1_efficiency,
                                      "nm": eve_sde_tools.get_item_name_by_type_id(sde_type_ids, bpmm1_blueprint_type_id),
                                      "b": bpmm1_blueprints,
                                      "ajp": bpmm1_in_progress + bpmm1_available})
            # вывод списка материалов для постройки по чертежу
            for m2 in bpmm1_blueprint_materials["activities"]["manufacturing"]["materials"]:
                row2_num = row2_num + 1
                bpmm2_tid = int(m2["typeID"])
                bpmm2_tnm = eve_sde_tools.get_item_name_by_type_id(sde_type_ids, bpmm2_tid)
                bpmm2_quantity = int(m2["quantity"])  # сведения из чертежа
                bpmm2_efficiency = bpmm2_quantity * bpmm1_efficiency  # поправка на эффективность материалов
                bpmm2_not_enough = bpmm2_quantity * bpmm1_not_enough
                bpmm2_is_reaction_formula = eve_sde_tools.is_type_id_nested_into_market_group(bpmm1_tid, [1849], sde_type_ids, sde_market_groups)
                # берём из настроек me=??, которая подразумевается одинаковой на всех БПО и БПЦ в коллекции
                material_efficiency = report_options["missing_blueprints"]["material_efficiency"]
                bpmm2_efficiency = eve_sde_tools.get_industry_material_efficiency(
                    'reaction' if bpmm2_is_reaction_formula else 'manufacturing',
                    1,
                    bpmm2_efficiency,
                    material_efficiency)
                bpmm2_not_enough = eve_sde_tools.get_industry_material_efficiency(
                    'reaction' if bpmm2_is_reaction_formula else 'manufacturing',
                    1,
                    bpmm2_not_enough,
                    material_efficiency)
                # вывод наименования ресурса
                glf.write(
                    '<tr>\n'
                    ' <th scope="row">{num1}.{num2}</th>\n'
                    ' <td><img class="icn24" src="{src}"> {nm}</td>\n'
                    ' <td></td>\n'
                    ' <td>{qs:,d}</td>\n'
                    ' <td>{qe:,d}</td>\n'
                    ' <td>{qne:,d}</td>\n'
                    '</tr>'.
                    format(
                        num1=row1_num, num2=row2_num,
                        nm=bpmm2_tnm,
                        src=render_html.__get_img_src(bpmm2_tid, 32),
                        qs=bpmm1_standard * bpmm2_quantity,
                        qe=bpmm2_efficiency,
                        qne=bpmm2_not_enough
                    )
                )
                # сохраняем материалы для производства в список их суммарного кол-ва
                __summary_dict = next((ms for ms in materials_summary if ms['id'] == bpmm2_tid), None)
                if __summary_dict is None:
                    __summary_dict = {"id": bpmm2_tid, "q": bpmm2_not_enough, "nm": bpmm2_tnm}
                    materials_summary.append(__summary_dict)
                else:
                    __summary_dict["q"] += bpmm2_not_enough

    glf.write("""
</tbody>
</table>
</div> <!--table-responsive-->
  </div> <!--media-body-->
 </div> <!--media-->
<hr>
 <div class="media">
  <div class="media-left">
""")
    glf.write('  <img class="media-object icn64" src="{src}" alt="Summary raw materials">\n'.
              format(src=render_html.__get_icon_src(1201, sde_icon_ids)))  # Materials
    glf.write("""
  </div>
  <div class="media-body">
   <h4 class="media-heading">Summary raw materials</h4>
<p>The number of Minerals and Components is counted for <mark>all assets</mark> owned by the corporation.</p>
""")
    str_bp_cont_names = ""
    for bp in report_options["blueprints"]:
        if str_bp_cont_names:
            str_bp_cont_names = str_bp_cont_names + ', '
        str_bp_cont_names += '<mark>' + bp['name'] + '</mark>'
    if not str_bp_cont_names:
        str_bp_cont_names = '<mark></mark>'
    glf.write('<p>The number of Blueprints is considered based on the presence of blueprints in container(s) {}.</p>\n'.
              format(str_bp_cont_names))  # Materials
    glf.write("""
<div class="table-responsive">
 <table class="table table-condensed" style="font-size:small">
<thead>
 <tr>
  <th style="width:40px;">#</th>
  <th>Materials</th>
  <th>Exists +<br/>In progress</th>
  <th>Need<br/>(Efficiency)</th>
  <th>Progress, %</th>
  <th style="text-align:right;">Price per<br/>Unit, ISK</th>
  <th style="text-align:right;">Sum,&nbsp;ISK</th>
  <th style="text-align:right;">Volume,&nbsp;m&sup3;</th>
 </tr>
</thead>
<tbody>
""")

    material_groups = {}
    # not_enough_materials = []
    # stock_resources = []

    # подсчёт кол-ва имеющихся в наличии материалов
    # составляем список тех материалов, у которых нет поля 'a', что говорит о том, что ассеты по
    # этим материалам не проверялись (в список они попали в результате анализа БП второго уровня)
    materials_summary_without_a = [int(ms["id"]) for ms in materials_summary if not ("a" in ms)]
    for a in corp_assets_data:
        __location_id = int(a["location_id"])
        if not (__location_id in stock_containter_ids):
            continue
        __stock_flag_dict = next((c for c in stock_containter_flag_ids if c['id'] == __location_id), None)
        if not (__stock_flag_dict is None):
            if not (__stock_flag_dict['flag'] == a['location_flag']):
                continue
        __type_id = int(a["type_id"])
        if int(__type_id) in materials_summary_without_a:
            __summary_dict = next((ms for ms in materials_summary if ms['id'] == __type_id), None)
            if __summary_dict is None:
                continue
            __quantity = int(a["quantity"])
            if "a" in __summary_dict:
                __summary_dict["a"] += __quantity
            else:
                __summary_dict.update({"a": __quantity})
    # получаем список работ, которые ведутся с материалами
    materials_summary_without_j = [int(ms["id"]) for ms in materials_summary if not ("j" in ms)]
    for j in corp_industry_jobs_data:
        __type_id = j["product_type_id"]
        if __type_id in materials_summary_without_j:
            __summary_dict = next((ms for ms in materials_summary if ms['id'] == __type_id), None)
            if __summary_dict is None:
                continue
            __runs = int(j["runs"])
            if "j" in __summary_dict:
                __summary_dict["j"] += __runs
            else:
                __summary_dict.update({"j": __runs})

    # поиск групп, которым принадлежат материалы, которых не хватает для завершения производства по списку
    # чертежей в этом контейнере (планетарка отдельно, композиты отдельно, запуск работ отдельно)
    for __summary_dict in materials_summary:
        __quantity = __summary_dict["q"]
        __assets = __summary_dict["a"] if "a" in __summary_dict else 0
        __blueprints = __summary_dict["b"] if "b" in __summary_dict else []
        __in_progress = __summary_dict["j"] if "j" in __summary_dict else 0
        __products_available_and_in_progress = __summary_dict.get("ajp", 0)
        __type_id = __summary_dict["id"]
        __item_name = __summary_dict["nm"]
        # ---
        __quantity -= __products_available_and_in_progress
        if __quantity < 0:
            __quantity = 0
        # ---
        __market_group = eve_sde_tools.get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, __type_id)
        __material_dict = {
            "id": __type_id,
            "q": __quantity,
            "nm": __item_name,
            "a": __assets,
            "b": __blueprints,
            "j": __in_progress}
        if str(__market_group) in material_groups:
            material_groups[str(__market_group)].append(__material_dict)
        else:
            material_groups.update({str(__market_group): [__material_dict]})

    # добавление чертежа на корабль в список требуемых материалов
    # Vanquisher Blueprint не имеет marketGroupID, что является ошибкой ССР, и поэтому приходится изгаляться...
    __capital_blueprint = {
        "id": __capital_blueprint_type_id,
        "q": __capital_quantity_or_runs,
        "nm": eve_sde_tools.get_item_name_by_type_id(sde_type_ids, __capital_blueprint_type_id),
        "a": 0,
        "b": [__capital_blueprint_dict] if not (__capital_blueprint_dict["id"] is None) else [],
        "j": 0}  # не показываем, что строим титан
    materials_summary.append(__capital_blueprint)
    material_groups["2"].append(__capital_blueprint)  # Blueprints & Reactions

    # вывод окончательного summary-списка материалов для постройки по чертежу
    ms_groups = material_groups.keys()
    row3_num = 0
    for __group_id in ms_groups:
        __is_blueprints_group = __group_id == "2"  # Blueprints & Reactions
        __mg1 = material_groups[__group_id]
        if (__group_id == "None") or (int(__group_id) == 1857):  # Minerals
            __mg1.sort(key=lambda m: m["q"], reverse=True)
        else:
            __mg1.sort(key=lambda m: m["q"])
        # выводим название группы материалов (Ship Equipment, Materials, Components, ...)
        if __group_id == "None":
            __group_name = ""
        else:
            __group_name = sde_market_groups[__group_id]["nameID"]["en"]
            # подготовка элементов управления копирования данных в clipboard
            __copy2clpbrd = '' if not enable_copy_to_clipboard else \
                '&nbsp;<a data-target="#" role="button" class="qind-copy-btn"' \
                '  data-toggle="tooltip"><button type="button" class="btn btn-default btn-xs"><span' \
                '  class="glyphicon glyphicon-copy" aria-hidden="true"></span> Export to multibuy</button></a>'
            glf.write('<tr>\n'
                      ' <td class="active" colspan="8"><strong>{nm}</strong><!--{id}-->{clbrd}</td>\n'
                      '</tr>'.
                      format(
                        nm=__group_name,
                        id=__group_id,
                        clbrd=__copy2clpbrd
                      ))
        # вывод материалов в группе
        __summary_cost = 0
        __summary_volume = 0
        for __material_dict in __mg1:
            # получение данных по материалу
            bpmm3_tid = __material_dict["id"]
            bpmm3_tnm = __material_dict["nm"]
            bpmm3_q = __material_dict["q"]  # quantity (required, not available yet)
            bpmm3_a = __material_dict["a"]  # available in assets
            bpmm3_b = __material_dict["b"]  # blueprints list
            bpmm3_j = __material_dict["j"]  # in progress (runs of jobs)
            row3_num = row3_num + 1
            # получение справочной информации о материале
            __type_dict = sde_type_ids[str(bpmm3_tid)]
            # получение цены материала
            bpmm3_price = None
            if not __is_blueprints_group:
                __price_dict = next((p for p in eve_market_prices_data if p['type_id'] == int(bpmm3_tid)), None)
                if not (__price_dict is None):
                    if "average_price" in __price_dict:
                        bpmm3_price = __price_dict["average_price"]
                    elif "adjusted_price" in __price_dict:
                        bpmm3_price = __price_dict["adjusted_price"]
                    elif "basePrice" in __type_dict:
                        bpmm3_price = __type_dict["basePrice"]
                elif "basePrice" in __type_dict:
                    bpmm3_price = __type_dict["basePrice"]
            # получение информации о кол-ве материала (сперва по блюпринтам, потом по ассетам)
            me_te_tags_list = []
            me_te_tags = ""
            if not __is_blueprints_group:
                bpmm3_available = bpmm3_a
            else:
                bpmm3_available = 0
                for b in bpmm3_b:
                    if not bool(b["cp"]):
                        # найден оригинал, это значит что можно произвести ∞ кол-во материалов
                        bpmm3_available = -1
                    if bpmm3_available >= 0:
                        bpmm3_available += int(b["qr"])
                    # составляем тэги с информацией о me/te чертежей
                    __me_te = '{me} {te}'.format(me=b["me"], te=b["te"])
                    if not (__me_te in me_te_tags_list):
                        me_te_tags += '&nbsp;<span class="label label-success">{}</span>'.format(__me_te)
                        me_te_tags_list.append(__me_te)
            # расчёт прогресса выполнения (постройки, сбора) материалов (bpmm3_j пропускаем, т.к. они не готовы ещё)
            if bpmm3_available >= bpmm3_q:
                bpmm3_progress = 100
            else:
                bpmm3_progress = float(100 * bpmm3_available / bpmm3_q)
            # вывод наименования ресурса
            glf.write(
                '<tr>\n'
                ' <th scope="row">{num}</th>\n'
                ' <td data-copy="{nm}"><img class="icn24" src="{src}"> {nm}{me_te}</td>\n'
                ' <td>{qa}{qip}</td>\n'
                ' <td quantity="{qneed}">{qr:,d}</td>\n'
                ' <td><div class="progress" style="margin-bottom:0px"><div class="progress-bar{prcnt100}" role="progressbar"'
                ' aria-valuenow="{prcnt}" aria-valuemin="0" aria-valuemax="100" style="width: {prcnt}%;">{fprcnt:.1f}%</div></div></td>\n'
                ' <td align="right">{price}</td>'
                ' <td align="right">{cost}</td>'
                ' <td align="right">{volume}</td>'
                '</tr>'.
                format(
                    num=row3_num,
                    nm=bpmm3_tnm,
                    me_te=me_te_tags,
                    src=render_html.__get_img_src(bpmm3_tid, 32),
                    qr=bpmm3_q,
                    qneed=bpmm3_q-bpmm3_available-bpmm3_j if bpmm3_q > (bpmm3_available+bpmm3_j) else 0,
                    qa='{:,d}'.format(bpmm3_available) if bpmm3_available >= 0 else "&infin; <small>runs</small>",
                    qip="" if bpmm3_j == 0 else '<mark>+ {}</mark>'.format(bpmm3_j),
                    prcnt=int(bpmm3_progress),
                    fprcnt=bpmm3_progress,
                    prcnt100=" progress-bar-success" if bpmm3_progress == 100 else "",
                    price='{:,.1f}'.format(bpmm3_price) if not (bpmm3_price is None) else "",
                    cost='{:,.1f}'.format(bpmm3_price * bpmm3_q) if not (bpmm3_price is None) else "",
                    volume='{:,.1f}'.format(__type_dict["volume"] * bpmm3_q) if not __is_blueprints_group else ""
                ))
            # подсчёт summary кол-ва по всем материалам группы
            if not (bpmm3_price is None):
                __summary_cost = __summary_cost + (bpmm3_price * bpmm3_q)
                __summary_volume = __summary_volume + (__type_dict["volume"] * bpmm3_q)
        # вывод summary-строки для текущей группы материалов
        if not (__group_id == "None") and not (__group_id == "2"):
            glf.write('<tr style="font-weight:bold">'
                      ' <th></th>'
                      ' <td colspan="4">Summary&nbsp;(<small>{nm}</small>)</td>'
                      ' <td colspan="2" align="right">{cost:,.1f}&nbsp;ISK</td>'
                      ' <td align="right">{volume:,.1f}&nbsp;m&sup3;</td>'
                      '</tr>\n'.
                      format(nm=__group_name,
                             cost=__summary_cost,
                             volume=__summary_volume))

    glf.write("""
</tbody>
</table>
</div> <!--table-responsive-->
  </div> <!--media-body-->
 </div> <!--media-->
</div> <!--container-fluid-->

<script>
  // Capital Ship' Options menu and submenu setup
  $(document).ready(function(){
    // Working with clipboard
    $('a.qind-copy-btn').each(function() {
      $(this).tooltip();
    })
    $('a.qind-copy-btn').bind('click', function () {
      var data_copy = $(this).attr('data-copy');
      if (data_copy === undefined) {
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
              var nm = td.attr('data-copy');
              if (!(nm === undefined)) {
                if (data_copy) data_copy += "\\n"; 
                data_copy += nm + "\\t" + $(this).find('td').eq(2).attr('quantity');
              }
            }
          }
        });
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


def dump_capital_into_report(
        # путь, где будет сохранён отчёт
        ws_dir,
        # настройки генерации отчёта
        report_options,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        sde_icon_ids,
        # esi данные, загруженные с серверов CCP
        corp_assets_data,
        corp_industry_jobs_data,
        corp_blueprints_data,
        eve_market_prices_data):
    product_name = report_options["product"]
    glf = open('{dir}/{fnm}.html'.format(dir=ws_dir, fnm=render_html.__camel_to_snake(product_name, True)), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(glf, product_name)
        __dump_corp_capital(
            glf,
            report_options,
            sde_type_ids,
            sde_bp_materials,
            sde_market_groups,
            sde_icon_ids,
            corp_assets_data,
            corp_industry_jobs_data,
            corp_blueprints_data,
            eve_market_prices_data)
        render_html.__dump_footer(glf)
    finally:
        glf.close()
