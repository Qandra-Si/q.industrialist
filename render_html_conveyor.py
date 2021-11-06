import render_html
import eve_sde_tools
import eve_esi_tools
from math import ceil


def __is_availabe_blueprints_present(
        type_id,
        corp_bp_loc_data,
        sde_bp_materials,
        exclude_loc_ids,
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
        # пропускаем контейнеры, их которых нельзя доставать чертежи для достройки недостающих материалов
        if int(loc_id) in exclude_loc_ids:
            continue
        # пропускаем прочие станции, на которых нет текущего stock-а и нет конвейеров (ищем свою станку)
        if not eve_esi_tools.is_location_nested_into_another(loc_id, blueprint_station_ids, corp_assets_tree):
            continue
        # проверяем состояния чертежей
        __bp2 = corp_bp_loc_data[str(loc)]
        __bp2_keys = __bp2.keys()
        for __blueprint_type_id in __bp2_keys:
            if int(__blueprint_type_id) != int(blueprint_type_id):
                continue
            bp_keys = __bp2[__blueprint_type_id].keys()
            for bpk in bp_keys:
                bp = __bp2[__blueprint_type_id][bpk]
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


def __dump_material(glf, quantity, type_id, type_name, with_copy_to_clipboard=False, text_class=None):
    # вывод наименования ресурса
    glf.write(
        '<span style="white-space:nowrap"{qq}{cl}>'
        '<img class="icn24" src="{src}"> <b>{q:,d}</b> {nm} '
        '</span>\n'.format(
            src=render_html.__get_img_src(type_id, 32),
            q=quantity,
            nm=type_name,
            qq=' quantity="{}"'.format(quantity) if with_copy_to_clipboard else '',
            cl=' class="{}"'.format(text_class) if text_class else '',
        )
    )


# get_industry_activity_details tuple: (time, materials)
def get_industry_activity_details(
        blueprint_type_id,
        activity,
        sde_type_ids,
        sde_market_groups,
        sde_bp_materials):
    activity_dict = eve_sde_tools.get_blueprint_any_activity(sde_bp_materials, activity, blueprint_type_id)
    if activity_dict is None:
        return 0, None
    activity_time = activity_dict.get('time', -1)
    activity_blueprint_materials = activity_dict.get('materials')
    # ---
    is_invention_activity = activity == 'invention'
    if is_invention_activity and activity_blueprint_materials:
        # Добавляем декрипторы (замечения и ограничения):
        # - всегда все хулы запускаются с декриптором Accelerant Decryptor
        # - всегда все риги запускаются с декриптором Symmetry Decryptor
        # - всегда все модули запускаются без декрипторов
        # - для запуска модулей скилы должны быть не меньше 2х, для запуска хулов и риг скилы должны быть
        # в 3 и выше. Если ваши скилы меньше - лучше запускайте ресерч или ждите задач по копирке. Будьте
        # внимательны, игнорируя эти замечения вы сильно усложняете работу производственников.
        groups_chain = eve_sde_tools.get_market_groups_chain_by_type_id(sde_type_ids, sde_market_groups, blueprint_type_id)
        if not (groups_chain is None):
            if 204 in groups_chain:  # Ships
                activity_blueprint_materials.append({'quantity': 1, 'typeID': 34201})  # Accelerant Decryptor
            elif 943 in groups_chain:  # Ship Modifications
                activity_blueprint_materials.append({'quantity': 1, 'typeID': 34206})  # Symmetry Decryptor
    # ---
    del activity_dict
    return activity_time, activity_blueprint_materials


# blueprints_details - подробности о чертежах этого типа: [{"q": -1, "r": -1}, {"q": 2, "r": -1}, {"q": -2, "r": 179}]
# метод возвращает список tuple: [{"id": 11399, "q": 11, "qmin": 11", "nm": "Morphite"}] с учётом ME
def get_materials_list_for_set_of_blueprints(
        sde_type_ids,
        blueprint_materials,
        blueprints_details,  # при is_blueprint_copy=True tuple={"r":?}, при False tuple={"r":?,"q":?}
        manufacturing_activity,  # тип индустрии: manufacturing, research_material, ...
        material_efficiency,  # параметр чертежа (набора чертежей)
        is_blueprint_copy=True,  # при is_blueprint_copy=True, в списке blueprints_details анализиуется только "r"
        fixed_number_of_runs=None):  # учитывается только для оригиналов, т.е. для is_blueprint_copy=False
    # список материалов по набору чертежей с учётом ME
    materials_list_with_efficiency = []
    # перебираем все ресурсы (материалы) чертежа
    for m in blueprint_materials:
        bp_manuf_need_all = 0
        bp_manuf_need_min = 0
        for __bp3 in blueprints_details:
            # расчёт кол-ва ранов для этого чертежа
            if is_blueprint_copy:
                quantity_or_runs = __bp3["r"]
            else:
                quantity_or_runs = __bp3["q"] if __bp3["q"] > 0 else 1
                if fixed_number_of_runs:
                    quantity_or_runs = quantity_or_runs * fixed_number_of_runs
            # расчёт кол-ва материала с учётом эффективности производства
            __need = eve_sde_tools.get_industry_material_efficiency(
                manufacturing_activity,
                quantity_or_runs,
                m["quantity"],  # сведения из чертежа
                material_efficiency)
            # считаем общее количество материалов, необходимых для работ по этом чертежу
            bp_manuf_need_all = bp_manuf_need_all + __need
            # вычисляем минимально необходимое материалов, необходимых для работ хотя-бы по одному чертежу
            bp_manuf_need_min = __need if bp_manuf_need_min == 0 else min(bp_manuf_need_min, __need)
        # вывод информации о ресурсе (материале)
        bpmm_tid: int = m["typeID"]
        materials_list_with_efficiency.append({
            "id": bpmm_tid,
            "q": bp_manuf_need_all,
            "qmin": bp_manuf_need_min,
            "nm": eve_sde_tools.get_item_name_by_type_id(sde_type_ids, bpmm_tid)
        })
    return materials_list_with_efficiency


def __dump_materials_list_with_efficiency(
        glf,
        materials_list_with_efficiency,
        with_copy_to_clipboard=False,
        text_class=None):
    # вывод наименований ресурсов (материалов)
    for m_me in materials_list_with_efficiency:
        __dump_material(
            glf,
            m_me["q"], m_me["id"], m_me["nm"],
            with_copy_to_clipboard=with_copy_to_clipboard,
            text_class=text_class)


def calc_materials_availability(
        materials_list_with_efficiency,
        stock_resources,
        check_absolutely_not_available=True):
    not_enough_materials = []
    # выполнение расчётов достаточности метариала и добавление его количества в summary-списки
    for m_me in materials_list_with_efficiency:
        # перебор материалов, количество которых рассчитано на основании сведений о ME
        bpmm_tid: int = m_me["id"]
        bp_manuf_need_all: int = m_me["q"]
        bp_manuf_need_min = m_me["qmin"] if check_absolutely_not_available else None
        bpmm_tnm: str = m_me["nm"]
        # проверка наличия имеющихся ресурсов для постройки по этому БП
        not_available = bp_manuf_need_all
        not_available_absolutely = True
        if bpmm_tid in stock_resources:
            __stock = stock_resources[bpmm_tid]
            not_available = 0 if __stock >= not_available else not_available - __stock
            if check_absolutely_not_available:
                not_available_absolutely = __stock < bp_manuf_need_min
        # сохраняем недостающее кол-во материалов для производства по этому чертежу
        if not_available > 0:
            not_available_dict = {"id": bpmm_tid, "q": not_available, "nm": bpmm_tnm}
            if check_absolutely_not_available:
                not_available_dict.update({"absol": not_available_absolutely})
            not_enough_materials.append(not_available_dict)
            del not_available_dict
    return not_enough_materials


def calc_materials_summary(
        materials_list_with_efficiency,
        materials_summary):
    # выполнение расчётов достаточности метариала и добавление его количества в summary-списки
    for m_me in materials_list_with_efficiency:
        # перебор материалов, количество которых рассчитано на основании сведений о ME
        bpmm_tid: int = m_me["id"]
        bp_manuf_need_all: int = m_me["q"]
        bpmm_tnm: str = m_me["nm"]
        # сохраняем материалы для производства в список их суммарного кол-ва
        __summary_dict = next((ms for ms in materials_summary if ms['id'] == bpmm_tid), None)
        if __summary_dict is None:
            materials_summary.append({"id": bpmm_tid, "q": bp_manuf_need_all, "nm": bpmm_tnm})
        else:
            __summary_dict["q"] += bp_manuf_need_all


def get_ntier_materials_list_of_not_available(
        not_enough_materials,
        sde_type_ids,
        sde_bp_materials,
        products_for_bps,
        reaction_products_for_bps):
    # расчёт списка материалов, предыдущего уровня вложенности
    # (по информации о ресурсах, которых не хватает)
    not_enough_materials_list_with_efficiency = []
    for m in not_enough_materials:
        m_id: int = m["id"]
        # проверяем, можно ли произвести данный ресурс (материал)?
        if m_id in products_for_bps:
            ntier_activity: str = "manufacturing"
        elif m_id in reaction_products_for_bps:
            ntier_activity: str = "reaction"
        else:
            continue
        # поиск чертежа, который подходит для производства данного типа продукта
        (blueprint_type_id, blueprint_dict) = \
            eve_sde_tools.get_blueprint_type_id_by_product_id(m_id, sde_bp_materials, ntier_activity)
        if not blueprint_type_id:
            continue
        # расчёт материалов по информации о чертеже с учётом ME
        blueprint_activity_dict = blueprint_dict["activities"][ntier_activity]
        quantity_for_single_run = blueprint_activity_dict["products"][0]["quantity"]
        ntier_runs = ceil(m["q"] / quantity_for_single_run)
        nemlwe = get_materials_list_for_set_of_blueprints(
            sde_type_ids,
            blueprint_activity_dict["materials"],
            [{"r": ntier_runs}],
            ntier_activity,
            10)  # мы не знаем с какой эффективностью будет делаться вложенная работа, наверное 10?
        calc_materials_summary(nemlwe, not_enough_materials_list_with_efficiency)
        del nemlwe
    return not_enough_materials_list_with_efficiency


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
  </a><br><small>
""")
        materials_list.sort(key=lambda bp: bp['nm'])
        for m_usd in materials_list:
            # вывод наименования ресурса
            __dump_material(glf, m_usd['q'], m_usd['id'], m_usd['nm'], with_copy_to_clipboard)
        glf.write("""</small>
 </div>
</div>
</div>
""")  # qind-materials-used, media, media-body


def __dump_not_available_materials_list(
        glf,
        # esi данные, загруженные с серверов CCP
        corp_bp_loc_data,
        corp_industry_jobs_data,
        corp_assets_tree,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        products_for_bps,
        reaction_products_for_bps,
        # списки контейнеров и станок из экземпляра контейнера
        stock_all_loc_ids,
        exclude_loc_ids,
        blueprint_station_ids,
        # списком материалов, которых не хватает в производстве
        stock_not_enough_materials,
        # список ресурсов, которые используются в производстве
        stock_resources,
        materials_summary,
        # настройки
        with_copy_to_clipboard):
    # отображение в отчёте summary-информации по недостающим материалам
    if not materials_summary:
        return
    # проверка наличия имеющихся ресурсов с учётом запаса в стоке
    not_enough_materials = calc_materials_availability(
        materials_summary,
        stock_resources,
        check_absolutely_not_available=False
    )
    if not not_enough_materials:
        return
    # сохранение информации в ГЛОБАЛЬНОМ списка недостающих материалов
    calc_materials_summary(not_enough_materials, stock_not_enough_materials)
    # расчёт списка материалов, предыдущего уровня вложенности
    # (по информации о ресурсах, которых не хватает)
    if not_enough_materials:
        not_enough_materials_list_with_efficiency = get_ntier_materials_list_of_not_available(
            not_enough_materials,
            sde_type_ids,
            sde_bp_materials,
            products_for_bps,
            reaction_products_for_bps)
        if not_enough_materials_list_with_efficiency:
            calc_materials_summary(not_enough_materials_list_with_efficiency, not_enough_materials)
        del not_enough_materials_list_with_efficiency

    # поиск групп, которым принадлежат материалы, которых не хватает для завершения производства по списку
    # чертеже в этом контейнере (планетарка отдельно, композиты отдельно, запуск работ отдельно)
    material_groups = {}
    for __summary_dict in not_enough_materials:
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
            # получаем кол-во материалов этого типа, находящихся в стоке
            ms_in_stock = stock_resources.get(ms_type_id)
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
         <th>Exist in stock</th>
         <th>In progress</th>
        </tr>
       </thead>
       <tbody>
    """)
            # выводим название группы материалов (Ship Equipment, Materials, Components, ...)
            if not group_diplayed:
                __grp_name = sde_market_groups[ms_group_id]["nameID"]["en"]
                __icon_id = sde_market_groups[ms_group_id]["iconID"] if "iconID" in sde_market_groups[
                    ms_group_id] else 0
                # подготовка элементов управления копирования данных в clipboard
                __copy2clpbrd = '' if not with_copy_to_clipboard else \
                    '&nbsp;<a data-target="#" role="button" class="qind-copy-btn" data-source="table"' \
                    '  data-toggle="tooltip"><button type="button" class="btn btn-default btn-xs"><span' \
                    '  class="glyphicon glyphicon-copy" aria-hidden="true"></span> Export to multibuy</button></a>'
                glf.write(
                    '<tr>\n'
                    ' <td class="active" colspan="5"><strong>{nm}</strong><!--{id}-->{clbrd}</td>\n'
                    '</tr>'.
                    format(nm=__grp_name,
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
            vacant_originals, vacant_copies, not_a_product = __is_availabe_blueprints_present(
                ms_type_id,
                corp_bp_loc_data,
                sde_bp_materials,
                exclude_loc_ids,
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
            __copy2clpbrd = '' if not with_copy_to_clipboard else \
                '&nbsp;<a data-target="#" role="button" data-copy="{nm}" class="qind-copy-btn" data-source="table"' \
                '  data-toggle="tooltip"><span class="glyphicon glyphicon-copy"' \
                '  aria-hidden="true"></span></a>'. \
                format(nm=ms_item_name)
            # вывод сведений в отчёт
            glf.write(
                '<tr>\n'
                ' <th scope="row">{num}</th>\n'
                ' <td><img class="icn24" src="{src}"> {nm}{clbrd}</td>\n'
                ' <td quantity="{q}">{q:,d}{original}{copy}{absent}</td>\n'
                ' <td>{ins}</td>\n'
                ' <td>{inp}</td>\n'
                '</tr>'.
                format(num=not_available_row_num,
                       src=render_html.__get_img_src(ms_type_id, 32),
                       q=not_available,
                       inp='{:,d}'.format(in_progress) if in_progress > 0 else '',
                       nm=ms_item_name,
                       ins='' if not ms_in_stock else ms_in_stock,
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
        products_for_bps,
        reaction_products_for_bps,
        global_materials_summary,
        global_materials_used,
        enable_copy_to_clipboard=False):
    # получение списков контейнеров и станок из экземпляра контейнера
    stock_all_loc_ids = [int(ces["id"]) for ces in conveyor_entity["stock"]]
    exclude_loc_ids = [int(cee["id"]) for cee in conveyor_entity["exclude"]]
    blueprint_loc_ids = conveyor_entity["containers"]
    blueprint_station_ids = [conveyor_entity["station_id"]]
    # инициализация списка материалов, которых не хватает в производстве
    stock_not_enough_materials = []
    # формирование списка ресурсов, которые используются в производстве
    stock_resources = {}
    if not (stock_all_loc_ids is None):
        for loc_id in stock_all_loc_ids:
            loc_flags = corp_ass_loc_data.keys()
            for loc_flag in loc_flags:
                __a1 = corp_ass_loc_data[loc_flag]
                if str(loc_id) in __a1:
                    __a2 = __a1[str(loc_id)]
                    for itm in __a2:
                        if str(itm) in stock_resources:
                            stock_resources[itm] = stock_resources[itm] + __a2[itm]
                        else:
                            stock_resources.update({itm: __a2[itm]})

    # сортировка контейнеров по названиям
    loc_ids = corp_bp_loc_data.keys()
    sorted_locs_by_names = []
    for loc in loc_ids:
        loc_id = int(loc)
        __container = next((cec for cec in blueprint_loc_ids if cec['id'] == loc_id), None)
        if __container is None:
            continue
        loc_name = __container["name"]
        sorted_locs_by_names.append({"id": loc_id, "nm": loc_name, "box": __container})
    sorted_locs_by_names.sort(key=lambda loc: loc["nm"])

    # вывод информации по контейнерам
    for loc in sorted_locs_by_names:
        loc_id = int(loc["id"])
        loc_name = loc["nm"]
        fixed_number_of_runs = loc["box"]["fixed_number_of_runs"]
        manufacturing_activity = loc["box"]["manufacturing_activity"]
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
        __bp2 = corp_bp_loc_data[str(loc_id)]
        __type_keys = __bp2.keys()
        # сортировка чертежей по их названиям
        type_keys = []
        for type_id in __type_keys:
            type_keys.append({"id": int(type_id), "name": eve_sde_tools.get_item_name_by_type_id(sde_type_ids, int(type_id))})
        type_keys.sort(key=lambda bp: bp["name"])
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
            (activity_time, activity_blueprint_materials) = get_industry_activity_details(
                type_id,
                manufacturing_activity,
                sde_type_ids,
                sde_market_groups,
                sde_bp_materials)
            show_me_te = manufacturing_activity in ['manufacturing', 'research_material', 'research_time']
            # ---
            max_activity_time = None  # "огрызков" чертежей с малым кол-вом ранов как правило меньше
            bp_keys = __bp2[type_id].keys()
            for bpk in bp_keys:
                bp = __bp2[type_id][bpk]
                if not (bp["st"] is None):
                    continue  # пропускаем чертежи, по которым ведутся работы
                for itm in bp["itm"]:
                    __runs = itm["r"] if itm["q"] == -2 else (1 if fixed_number_of_runs is None else fixed_number_of_runs)
                    __time = __runs * activity_time
                    if max_activity_time is None:
                        max_activity_time = __time
                    elif max_activity_time < __time:
                        max_activity_time = __time
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
                    time=0 if max_activity_time is None else max_activity_time
                )
            )
            # ---
            # чертежей type_id-типа может быть несколько, они могут быть в разных сосотяниях - запущены, или ждать
            # запуск, следующим циклом перебираем каждый их них, при этом список материалов для работ по чертежу
            # был загружен ранее
            for bpk in bp_keys:
                bp = __bp2[type_id][bpk]
                is_blueprint_copy = bp["cp"]
                quantity_or_runs = bp["qr"]
                material_efficiency = bp["me"]
                time_efficiency = bp["te"]
                blueprint_status = bp["st"]
                # ---
                bpk_time_html = ''
                if (blueprint_status is None) and not (max_activity_time is None):
                    bpk_time_max = None
                    bpk_time_min = None
                    for itm in bp["itm"]:
                        __runs = itm["r"] if itm["q"] == -2 else (1 if fixed_number_of_runs is None else fixed_number_of_runs)
                        __time = __runs * activity_time
                        # TODO: хардкодим тут бонусы риг станций, когда же руки дойдут сделать нормально?!
                        if manufacturing_activity in ['manufacturing']:
                            # считаем бонус чертежа (накладываем TE чертежа на БП)
                            __stage1 = float(__time * (100 - time_efficiency) / 100.0)
                            # учитываем бонус профиля сооружения
                            __stage2 = float(__stage1 * (100.0 - 30.0) / 100.0)
                            # # учитываем бонус установленного модификатора
                            # __stage3 = float(__stage2 * (100.0 - 0) / 100.0)
                            # округляем вещественное число до старшего целого
                            __stage4 = int(float(__stage2 + 0.99))
                            # ---
                            __time = __stage4
                        elif manufacturing_activity in ['reaction']:
                            # учитываем бонус профиля сооружения
                            __stage2 = float(__time * (100.0 - 25.0) / 100.0)
                            # учитываем бонус установленного модификатора
                            __stage3 = float(__stage2 * (100.0 - 22.0) / 100.0)
                            # округляем вещественное число до старшего целого
                            __stage4 = int(float(__stage3 + 0.99))
                            # ---
                            __time = __stage4
                        elif manufacturing_activity in ['invention']:
                            # учитываем бонус профиля сооружения
                            __stage2 = float(__time * (100.0 - 20.0) / 100.0)
                            # # учитываем бонус установленного модификатора
                            # __stage3 = float(__stage2 * (100.0 - 22.0) / 100.0)
                            # округляем вещественное число до старшего целого
                            __stage4 = int(float(__stage2 + 0.99))
                            # ---
                            __time = __stage4
                        __changed: bool = False
                        if bpk_time_max is None:
                            bpk_time_max = __time
                            bpk_time_min = __time
                            __changed = True
                        else:
                            if bpk_time_max < __time:
                                bpk_time_max = __time
                                __changed = True
                            if bpk_time_min > __time:
                                bpk_time_min = __time
                                __changed = True
                        if __changed:
                            if bpk_time_max == bpk_time_min:
                                bpk_time_html =\
                                    '&nbsp;<span class="label label-time">{:d}:{:02d}</span>'.\
                                    format(int(bpk_time_max // 3600), int((bpk_time_max // 60) % 60))
                            else:
                                bpk_time_html =\
                                    '&nbsp;<span class="label label-time">{:d}:{:02d}&hellip;{:d}:{:02d}</span>'.\
                                    format(int(bpk_time_min // 3600), int((bpk_time_min // 60) % 60),
                                           int(bpk_time_max // 3600), int((bpk_time_max // 60) % 60),)
                # ---
                # вывод строки с пареметрами чертежа: [copy] [2:4] (10) [13:06]
                glf.write(
                    '<div class="qind-bp-block"><span class="qind-blueprints-{status}">'
                    '<span class="label label-{cpc}">{cpn}</span>{me_te}'
                    '&nbsp;<span class="badge">{qr}{fnr}</span>'
                    '{time}\n'.format(
                        qr=quantity_or_runs,
                        fnr=' x{}'.format(fixed_number_of_runs) if not (fixed_number_of_runs is None) else "",
                        cpc='default' if is_blueprint_copy else 'info',
                        cpn='copy' if is_blueprint_copy else 'original',
                        me_te='&nbsp;<span class="label label-success">{me} {te}</span>'.format(me=material_efficiency, te=time_efficiency) if show_me_te else "",
                        status=blueprint_status if not (blueprint_status is None) else "",
                        time=bpk_time_html
                    )
                )
                # если чертёж запущен в работу, то ограчиниваемся выводом его состояния добавив в строку с инфорацией
                # о чертеже: [copy] [2:4] (10) [active] 1.330.900.0 ISK
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
                    if not (activity_blueprint_materials is None):
                        materials_list_with_efficiency = get_materials_list_for_set_of_blueprints(
                            sde_type_ids,
                            activity_blueprint_materials,
                            [{"r": quantity_or_runs}],
                            manufacturing_activity,
                            material_efficiency)
                        # сохраняем материалы для производства в список их суммарного кол-ва
                        calc_materials_summary(materials_list_with_efficiency, materials_used)
                        # сохраняем материалы для производства в список их суммарного кол-ва
                        calc_materials_summary(materials_list_with_efficiency, global_materials_used)
                        del materials_list_with_efficiency
                    # ---
                    glf.write('</br></span>')  # qind-blueprints-?
                elif activity_blueprint_materials is None:
                    glf.write('&nbsp;<span class="label label-warning">{} impossible</span>'.format(manufacturing_activity))
                    glf.write('</br></span>')  # qind-blueprints-?
                else:
                    # подготовка элементов управления копирования данных в clipboard
                    if enable_copy_to_clipboard:
                        glf.write(
                            '&nbsp;<a data-target="#" role="button" data-copy="{nm}" class="qind-copy-btn"'
                            ' data-source="table" data-toggle="tooltip"><span class="glyphicon glyphicon-copy"'
                            ' aria-hidden="true"></span></a>'.
                            format(nm=blueprint_name)
                        )
                    glf.write('</br></span>')  # qind-blueprints-?

                    # расчёт материалов по информации о чертеже с учётом ME
                    materials_list_with_efficiency = get_materials_list_for_set_of_blueprints(
                        sde_type_ids,
                        activity_blueprint_materials,
                        bp["itm"],
                        manufacturing_activity,
                        material_efficiency,
                        is_blueprint_copy=is_blueprint_copy,
                        fixed_number_of_runs=fixed_number_of_runs)

                    # проверка наличия имеющихся ресурсов для постройки по этому БП
                    # сохраняем недостающее кол-во материалов для производства по этому чертежу
                    not_enough_materials = calc_materials_availability(materials_list_with_efficiency, stock_resources)

                    # сохраняем материалы для производства в список их суммарного кол-ва
                    calc_materials_summary(materials_list_with_efficiency, materials_summary)
                    # сохраняем материалы для производства в ГЛОБАЛЬНЫЙ список их суммарного кол-ва
                    calc_materials_summary(materials_list_with_efficiency, global_materials_summary)

                    # расчёт списка материалов, предыдущего уровня вложенности
                    # (по информации о ресурсах, которых не хватает)
                    if not_enough_materials:
                        not_enough_materials_list_with_efficiency = get_ntier_materials_list_of_not_available(
                            not_enough_materials,
                            sde_type_ids,
                            sde_bp_materials,
                            products_for_bps,
                            reaction_products_for_bps)
                    else:
                        not_enough_materials_list_with_efficiency = []

                    # вывод наименования ресурсов (материалов)
                    glf.write('<div class="qind-materials-used"><small>\n')  # div(materials)
                    __dump_materials_list_with_efficiency(glf, materials_list_with_efficiency)
                    __dump_materials_list_with_efficiency(glf, not_enough_materials_list_with_efficiency, text_class="text-muted")
                    glf.write('</small></div>\n')  # div(materials)

                    del not_enough_materials_list_with_efficiency
                    del materials_list_with_efficiency

                    # отображение списка материалов, которых не хватает
                    if not_enough_materials:
                        # вывод инфорации о недостающих материалах текущего уровня вложенности
                        glf.write('<div>\n')  # div(not_enough_materials 1-level)
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
                        glf.write('</div>\n')  # div(not_enough_materials 1-level)

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

        # отображение в отчёте summary-информации по недостающим материалам
        __dump_materials_list(glf, 'glyphicon-info-sign', 'Used materials in progress', materials_used, True, True)
        __dump_materials_list(glf, 'glyphicon-question-sign', 'Summary materials', materials_summary, False, True)
        __dump_not_available_materials_list(
            glf,
            # esi данные, загруженные с серверов CCP
            corp_bp_loc_data,
            corp_industry_jobs_data,
            corp_assets_tree,
            # sde данные, загруженные из .converted_xxx.json файлов
            sde_type_ids,
            sde_bp_materials,
            sde_market_groups,
            products_for_bps,
            reaction_products_for_bps,
            # списки контейнеров и станок из экземпляра контейнера
            stock_all_loc_ids,
            exclude_loc_ids,
            blueprint_station_ids,
            # списком материалов, которых не хватает в производстве
            stock_not_enough_materials,
            # список ресурсов, которые используются в производстве
            stock_resources,
            materials_summary,
            # настройки
            enable_copy_to_clipboard)

        glf.write("""
   </div> <!--panel-body-->
  </div> <!--panel-collapse-->
 </div> <!--panel-->
""")

    return stock_not_enough_materials


def __dump_corp_conveyors_stock_all(
        glf,
        conveyor_data,
        corp_industry_jobs_data,
        sde_type_ids,
        sde_market_groups,
        materials_for_bps,
        research_materials_for_bps):
    used_stock_places = []
    stock_resources = {}

    for corp_conveyors in conveyor_data:
        # группируются по солнечным системам, поэтому попадаем сюда для каждой системы раз за разом
        for conveyor_entity in corp_conveyors["corp_conveyour_entities"]:
            # группируются по контейнерам с чертежами
            if len(conveyor_entity["stock"]) == 0:
                continue
            stock = conveyor_entity["stock"][0]
            stock_id = stock["id"]  # 1035633039842
            stock_name = stock["name"]  # ..stock ALL
            stock_tree_dict = corp_conveyors["corp_assets_tree"][str(stock_id)]  # {'type_id': 17368,...
            stock_item_dict = corp_conveyors["corp_assets_data"][int(stock_tree_dict["index"])]  # {'is_singleton': True,
            # stock_item_type_id = int(stock_tree_dict["type_id"])  # 17368
            stock_location_flag = stock_item_dict["location_flag"]  # CorpSAG6
            # office_id = stock_item_dict["location_id"]  # 1035631968791
            # office_tree_dict = corp_conveyors["corp_assets_tree"][str(office_id)]  # {'items': [1030288472777, ...
            # office_item_dict = corp_conveyors["corp_assets_data"][int(office_tree_dict["index"])]  # {'location_flag': 'OfficeFolder'
            station_id = conveyor_entity["station_id"]  # 1035620655696
            station_name = conveyor_entity["station"]  # Poinen - Ri4 Love Prod
            # print(stock_id, stock_location_flag, station_id, station_name, "\n\n")

            # формирование списка ресурсов, которые используются в производстве
            if "items" in stock_tree_dict:
                for item_id in stock_tree_dict["items"]:
                    tree_dict = corp_conveyors["corp_assets_tree"][str(item_id)]  # {'type_id': 25592...
                    item_dict = corp_conveyors["corp_assets_data"][int(tree_dict["index"])]  # {'quantity': 24...
                    # print(stock_id, item_id, tree_dict, item_dict, "\n\n")
                    type_id: int = int(tree_dict["type_id"])
                    quantity: int = int(item_dict["quantity"])
                    # определяем группу, которой принадлежат материалы
                    item_market_group = eve_sde_tools.get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, type_id)
                    if str(item_market_group) in stock_resources:
                        stock_group = stock_resources[str(item_market_group)]
                    else:
                        group_name = sde_market_groups[str(item_market_group)]["nameID"]["en"] if str(item_market_group) in sde_market_groups else None  # устарел sde?
                        if not (group_name is None):
                            stock_group = {"name": group_name, "items": []}
                            stock_resources.update({str(item_market_group): stock_group})
                        else:
                            stock_group = {"name": "Unknown", "items": []}
                            stock_resources.update({"0": stock_group})
                    # пополняем список материалов в группе
                    resource_dict = next((r for r in stock_group["items"] if r['id'] == type_id), None)
                    if resource_dict is None:
                        # получаем данные из корпассетов по этому элементу
                        item_type_desc = sde_type_ids.get(str(type_id), {})
                        item_name = item_type_desc.get("name", {}).get("en", "Unknown Type {}".format(type_id))
                        # получаем статистику по текущим работам, считаем сколько производится этих материалов?
                        jobs = [j for j in corp_conveyors["corp_industry_jobs_data"] if
                                (j["product_type_id"] == type_id) and
                                (j['output_location_id']==stock_id)]
                        in_progress: int = 0
                        for j in jobs:
                            in_progress = in_progress + j["runs"]
                        # сохраняем ресурс в справочник
                        resource_dict = {
                            "stock": stock_id,
                            "id": type_id,
                            "name": item_name,
                            "q": quantity,
                            "j": in_progress,
                            "ne": 0
                        }
                        stock_group["items"].append(resource_dict)
                    else:
                        resource_dict["q"] += quantity

            # пополняем список ресурсом записями с недостающим (отсутствующим количеством)
            for ne in corp_conveyors["stock_not_enough_materials"]:
                type_id = ne["id"]
                not_enough_quantity = ne["q"]
                # определяем группу, которой принадлежат материалы
                market_group = eve_sde_tools.get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, type_id)
                if str(market_group) in stock_resources:
                    stock_group = stock_resources[str(market_group)]
                else:
                    stock_group = {"name": sde_market_groups[str(market_group)]["nameID"]["en"], "items": []}
                    stock_resources.update({str(market_group): stock_group})
                # пополняем список материалов в группе
                resource_dict = next((r for r in stock_group["items"] if r['id'] == type_id), None)
                if resource_dict is None:
                    # получаем данные из корпассетов по этому элементу
                    item_type_desc = sde_type_ids.get(str(type_id), {})
                    item_name = item_type_desc.get("name", {}).get("en", "Unknown Type {}".format(type_id))
                    # получаем статистику по текущим работам, считаем сколько производится этих материалов?
                    jobs = [j for j in corp_conveyors["corp_industry_jobs_data"] if
                            (j["product_type_id"] == type_id) and
                            (j['output_location_id']==stock_id)]
                    in_progress: int = 0
                    for j in jobs:
                        in_progress = in_progress + j["runs"]
                        # сохраняем ресурс в справочник
                    resource_dict = {
                        "stock": stock_id,
                        "id": type_id,
                        "name": item_name,
                        "q": 0,
                        "j": in_progress,
                        "ne": not_enough_quantity,
                    }
                    stock_group["items"].append(resource_dict)
                else:
                    resource_dict["ne"] += not_enough_quantity

            used_stock_places.append({
                "stock_id": stock_id,
                "stock_name": stock_name,
                "hangar_name": stock_location_flag,
                "station_id": station_id,
                "station_name": station_name,
                "stock_resources": stock_resources,
            })

            #del office_item_dict
            #del office_tree_dict
            del stock_item_dict
            del stock_tree_dict
            del stock

    # сортируем станции, ангары и контейнеры по названиям
    used_stock_places = sorted(used_stock_places, key=lambda x: "{}_{}_{}".format(x["station_name"], x["hangar_name"], x["stock_name"]))
    # сортируем материалы по названию
    stock_keys = stock_resources.keys()
    for stock_key in stock_keys:
        stock_resources[str(stock_key)]["items"].sort(key=lambda r: r["name"])

    # формируем dropdown список, где можон будет выбрать локации и ангары
    glf.write("""
<div id="ddStocks" class="dropdown">
  <button class="btn btn-default dropdown-toggle" type="button" id="ddStocksMenu" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">
    <span class="qind-lb-dd">Choose Place&hellip;</span>
    <span class="caret"></span>
  </button>
  <ul class="dropdown-menu" aria-labelledby="ddMenuStock">
""")
    prev_station_id = None
    for stock in enumerate(used_stock_places):
        if stock[0] > 0:
            glf.write('<li role="separator" class="divider"></li>\n')
        if not prev_station_id or (prev_station_id != int(stock[1]["station_id"])):
            prev_station_id = int(stock[1]["station_id"])
            glf.write('<li class="dropdown-header">{st}</li>\n'.format(st=stock[1]["station_name"]))
        glf.write('<li><a href="#" loc="{id}">{hg} <mark>{nm}</mark></a></li>\n'.
                  format(
                      id=stock[1]["stock_id"],
                      hg=stock[1]["hangar_name"],
                      nm=stock[1]["stock_name"]))
    glf.write("""
  </ul>
</div>

<style>
#tblStock tr { font-size: small; }
.badge-light { color: #212529; background-color: #f8f9fa; }
.label-time { color: #131313; background-color: #7adee3; }
</style>

<div class="table-responsive">
 <table id="tblStock" class="table table-condensed table-hover">
<thead>
 <tr>
  <th class="hidden"></th>
  <th>#</th>
  <th>Item</th>
  <th>In stock</th>
  <th>Not available</th>
  <th>In progress</th>
 </tr>
</thead>
<tbody>""")

    stock_not_enough_materials = []

    row_num = 1
    stock_keys = stock_resources.keys()
    for stock_key in stock_keys:
        __group_dict = stock_resources[str(stock_key)]
        glf.write(
            '<tr>\n'
            ' <td class="active" colspan="5"><strong>{nm}</strong></td>\n'
            '</tr>'.
            format(nm=__group_dict["name"]))
        for resource_dict in __group_dict["items"]:
            stock_id = resource_dict["stock"]
            type_id = resource_dict["id"]
            quantity = resource_dict["q"]
            in_progress = resource_dict["j"]
            not_enough = resource_dict["ne"]
            # проверяем списки метариалов, используемых в исследованиях и производстве
            material_tag = ""
            if type_id in materials_for_bps:
                pass
            elif type_id in research_materials_for_bps:
                material_tag = ' <span class="label label-warning">research material</span></small>'
            else:
                material_tag = ' <span class="label label-danger">non material</span></small>'
            # формируем строку таблицы - найден нужный чертёж в ассетах
            glf.write(
                '<tr>'
                '<td class="hidden">{stock}</td>'
                '<th scope="row">{num}</th>'
                '<td>{nm}{mat_tag}</td>'
                '<td align="right">{q}</td>'
                '<td align="right">{ne}</td>'
                '<td align="right">{ip}</td>'
                '</tr>\n'.
                format(stock=stock_id,
                       num=row_num,
                       nm=resource_dict["name"],
                       mat_tag=material_tag,
                       q="" if quantity == 0 else '{:,d}'.format(quantity),
                       ne="" if not_enough == 0 else '{:,d}'.format(not_enough),
                       ip="" if in_progress == 0 else '{:,d}'.format(in_progress))
            )
            row_num = row_num + 1

    glf.write("""
</tbody>     
 </table>     
</div>     
""")


def __dump_corp_conveyors(
        glf,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        materials_for_bps,
        research_materials_for_bps,
        products_for_bps,
        reaction_products_for_bps,
        # настройки генерации отчёта
        # esi данные, загруженные с серверов CCP
        # данные, полученные в результате анализа и перекомпоновки входных списков
        conveyor_data):
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
       <li><a id="btnToggleSummary" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowSummary"></span> Show summary</a></li>
       <li><a id="btnToggleLegend" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowLegend"></span> Show legend</a></li>
       <li role="separator" class="divider"></li>
       <li><a id="btnResetOptions" data-target="#" role="button">Reset options</a></li>
      </ul>
    </li>
    <li><a data-target="#modalMaterials" role="button" data-toggle="modal">Materials</a></li>
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
""")

    # инициализация списка материалов, требуемых (и уже используемых) в производстве
    global_materials_summary = []
    global_materials_used = []

    for corp_conveyors in conveyor_data:
        glf.write("""
<!-- BEGIN: collapsable group (locations) -->
<div class="panel-group" id="accordion" role="tablist" aria-multiselectable="true">
""")

        for conveyor_entity in corp_conveyors["corp_conveyour_entities"]:
            stock_not_enough_materials = __dump_blueprints_list_with_materials(
                glf,
                conveyor_entity,
                corp_conveyors["corp_bp_loc_data"],
                corp_conveyors["corp_industry_jobs_data"],
                corp_conveyors["corp_ass_loc_data"],
                corp_conveyors["corp_assets_tree"],
                sde_type_ids,
                sde_bp_materials,
                sde_market_groups,
                products_for_bps,
                reaction_products_for_bps,
                global_materials_summary,
                global_materials_used,
                enable_copy_to_clipboard=True)
            corp_conveyors["stock_not_enough_materials"] = stock_not_enough_materials

        glf.write("""
 </div>
 <!-- END: collapsable group (locations) -->
""")

        if corp_conveyors["corp_conveyour_entities"]:
            glf.write("""
<div class="qind-summary-block">
 <h3>Summary</h3>
""")

            # Внимание! нельзя в кучу сваливать все чертежи материалы, нужно их разделить на группы по станциям
            __dump_materials_list(glf, 'glyphicon-info-sign', 'Used materials in progress', global_materials_used, True, True)
            __dump_materials_list(glf, 'glyphicon-question-sign', 'Summary materials', global_materials_summary, False, True)

            # получение списков контейнеров и станок из экземпляра контейнера
            global_stock_all_loc_ids = []
            global_exclude_loc_ids = []
            # global_blueprint_loc_ids = []
            global_blueprint_station_ids = []
            for conveyor_entity in corp_conveyors["corp_conveyour_entities"]:
                for id in [int(ces["id"]) for ces in conveyor_entity["stock"]]:
                    if not (id in global_stock_all_loc_ids):
                        global_stock_all_loc_ids.append(id)
                for id in [int(cee["id"]) for cee in conveyor_entity["exclude"]]:
                    if not (id in global_exclude_loc_ids):
                        global_exclude_loc_ids.append(id)
                # for id in conveyor_entity["containers"]:
                #     if not (id in global_blueprint_loc_ids):
                #         global_blueprint_loc_ids.append(id)
                if not (conveyor_entity["station_id"] in global_blueprint_station_ids):
                    global_blueprint_station_ids.append(conveyor_entity["station_id"])
            # формирование списка ресурсов, которые используются в производстве
            global_stock_resources = {}
            if not (global_stock_all_loc_ids is None):
                for loc_id in global_stock_all_loc_ids:
                    loc_flags = corp_conveyors["corp_ass_loc_data"].keys()
                    for loc_flag in loc_flags:
                        __a1 = corp_conveyors["corp_ass_loc_data"][loc_flag]
                        if str(loc_id) in __a1:
                            __a2 = __a1[str(loc_id)]
                            for itm in __a2:
                                if str(itm) in global_stock_resources:
                                    global_stock_resources[itm] = global_stock_resources[itm] + __a2[itm]
                                else:
                                    global_stock_resources.update({itm: __a2[itm]})
            __dump_not_available_materials_list(
                glf,
                # esi данные, загруженные с серверов CCP
                corp_conveyors["corp_bp_loc_data"],
                corp_conveyors["corp_industry_jobs_data"],
                corp_conveyors["corp_assets_tree"],
                # sde данные, загруженные из .converted_xxx.json файлов
                sde_type_ids,
                sde_bp_materials,
                sde_market_groups,
                products_for_bps,
                reaction_products_for_bps,
                # списки контейнеров и станок из экземпляра контейнера
                global_stock_all_loc_ids,
                global_exclude_loc_ids,
                global_blueprint_station_ids,
                # списком материалов, которых не хватает в производстве
                stock_not_enough_materials,
                # список ресурсов, которые используются в производстве
                global_stock_resources,
                global_materials_summary,
                # настройки
                True)
            glf.write("""
</div>
""")

    # создаём заголовок модального окна, где будем показывать список имеющихся материалов в контейнере "..stock ALL"
    render_html.__dump_any_into_modal_header_wo_button(
        glf,
        "Stock Materials",
        unique_id="Materials",
        modal_size="modal-lg")
    # формируем содержимое модального диалога
    __dump_corp_conveyors_stock_all(
        glf,
        conveyor_data,
        [],
        sde_type_ids,
        sde_market_groups,
        materials_for_bps,
        research_materials_for_bps
    )
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
    if (!ls.getItem('Show Summary')) {
      ls.setItem('Show Summary', 0);
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
    show = ls.getItem('Show Summary');
    if (show == 1)
      $('#imgShowSummary').removeClass('hidden');
    else
      $('#imgShowSummary').addClass('hidden');
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
    show = ls.getItem('Show Summary');
    $('div.qind-summary-block').each(function() {
      if (show == 1)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
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
  function rebuildStockMaterials() {
    // filtering stocks
    var stock_id = ls.getItem('Stock Id');
    $('#tblStock').find('tbody').find('tr').each(function() {
      var tr = $(this);
      var show = true;
      if (!(stock_id === null)) {
        show = stock_id == tr.find('td').eq(0).text();
      }
      if (show)
        tr.removeClass('hidden');
      else
        tr.addClass('hidden');
    });
  }
  // Stocks Dropdown menu setup
  function rebuildStocksDropdown() {
    var stock_id = ls.getItem('Stock Id');
    if (!(stock_id === null)) {
      var btn = $('#ddStocks');
      btn.find('li a').each(function() {
        if ($(this).attr('loc') == stock_id) {
          btn.find('span.qind-lb-dd').html($(this).html());
          btn.val($(this).html());
        }
      });
    }
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
    $('#btnToggleSummary').on('click', function () { toggleMenuOption('Show Summary'); });
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
    $('#ddStocks').on('click', 'li a', function () {
      var li_a = $(this);
      var stock_id = li_a.attr('loc');
      ls.setItem('Stock Id', stock_id);
      rebuildStocksDropdown();
      rebuildStockMaterials();
    });
    // first init
    resetOptionsMenuToDefault();
    rebuildOptionsMenu();
    rebuildBody();
    rebuildStocksDropdown();
    rebuildStockMaterials();
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
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        materials_for_bps,
        research_materials_for_bps,
        products_for_bps,
        reaction_products_for_bps,
        # настройки генерации отчёта
        # esi данные, загруженные с серверов CCP
        # данные, полученные в результате анализа и перекомпоновки входных списков
        conveyor_data):
    glf = open('{dir}/conveyor.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(glf, "Conveyor")
        __dump_corp_conveyors(
            glf,
            sde_type_ids,
            sde_bp_materials,
            sde_market_groups,
            materials_for_bps,
            research_materials_for_bps,
            products_for_bps,
            reaction_products_for_bps,
            conveyor_data)
        render_html.__dump_footer(glf)
    finally:
        glf.close()
