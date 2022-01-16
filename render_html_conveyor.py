import render_html
import eve_sde_tools
import eve_esi_tools
import eve_efficiency
from math import ceil

import q_conveyor_settings


g_modal_industry_seq = 1


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


def __dump_material(glf, quantity, type_id, type_name, with_copy_to_clipboard=False):
    # вывод наименования ресурса
    glf.write(
        '<span style="white-space:nowrap"{qq}{nnm}>'
        '<img class="icn24" src="{src}"> <b>{q:,d}</b> {nm} '
        '</span>\n'.format(
            src=render_html.__get_img_src(type_id, 32),
            q=quantity,
            nm=type_name,
            qq=' data-q="{}"'.format(quantity) if with_copy_to_clipboard else '',
            nnm=' data-nm="{}"'.format(type_name) if with_copy_to_clipboard else '',
        )
    )


def __dump_not_enough_material(glf, quantity, type_id, type_name, label_class=None):
    # вывод наименования ресурса (материала) которого не хватает
    glf.write(
        '&nbsp;<span class="label {lcl}">'
        '<img class="icn24" src="{src}"> {q:,d} x <span style="font-weight:normal">{nm}</span> '
        '</span>\n'.format(
            src=render_html.__get_img_src(type_id, 32),
            q=quantity,
            nm=type_name,
            lcl=label_class if label_class else "",
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
        activity,  # тип индустрии: manufacturing, research_material, ...
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
                quantity_of_runs = __bp3["r"]
                quantity_of_blueprints = 1
            else:
                quantity_of_blueprints = __bp3["q"] if __bp3["q"] > 0 else 1
                quantity_of_runs = fixed_number_of_runs if fixed_number_of_runs else 1
                # умножение на количество оригиналов будет выполнено позже...
            # расчёт кол-ва материала с учётом эффективности производства
            __industry_input = eve_efficiency.get_industry_material_efficiency(
                activity,
                quantity_of_runs,
                m["quantity"],  # сведения из чертежа
                material_efficiency)
            # вычисляем минимально необходимое материалов, необходимых для работ хотя-бы по одному чертежу
            bp_manuf_need_min = __industry_input if bp_manuf_need_min == 0 else min(bp_manuf_need_min, __industry_input)
            # выход готовой продукции с одного запуска по N ранов умножаем на кол-во чертежей
            __industry_input *= quantity_of_blueprints
            # считаем общее количество материалов, необходимых для работ по этом чертежу
            bp_manuf_need_all += __industry_input
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
        with_copy_to_clipboard=False):
    # вывод наименований ресурсов (материалов)
    for m_me in materials_list_with_efficiency:
        __dump_material(
            glf,
            m_me["q"], m_me["id"], m_me["nm"],
            with_copy_to_clipboard=with_copy_to_clipboard)


def __dump_materials_list_not_available(
        glf,
        not_enough_materials,
        products_for_bps,
        reaction_products_for_bps,
        ntier=False):
    # вывод наименований ресурсов (материалов) которых не хватает
    for m_na in not_enough_materials:
        m_id: int = m_na["id"]
        # выбираем цвет маркера для label
        if "absol" in m_na:
            if not ntier:
                label_class = "label-impossible" if m_na["absol"] else "label-not-enough"  # крсный и оранжевый label
            else:
                label_class = "label-impossible-ntier"  # блёклый красный
        elif m_id not in products_for_bps and m_id not in reaction_products_for_bps:
            label_class = "label-not-available"  # серый label
        else:
            label_class = "label-impossible-ntier"  # блеклый красный label
        # ---
        __dump_not_enough_material(
            glf,
            m_na["q"], m_id, m_na["nm"],
            label_class=label_class)


def calc_materials_summary(
        materials_list_with_efficiency,  # source
        materials_summary):              # destination
    # выполнение расчётов достаточности метариала и добавление его количества в summary-списки
    for m_src in materials_list_with_efficiency:
        # перебор материалов, количество которых рассчитано на основании сведений о ME
        bpmm_tid: int = m_src["id"]
        # сохраняем материалы для производства в список их суммарного кол-ва
        found: bool = False
        for m_dst in materials_summary:
            if m_dst['id'] != bpmm_tid:
                continue
            if m_dst.get('bps') and m_src.get('bps'):
                if m_dst.get('bps') == 1 and m_src.get('bps') == 1:
                    m_dst['runs'] += m_src['runs']
                    m_dst['q'] += m_src['q']
                    found = True
                    break
                elif m_dst.get('runs', -1) == m_src.get('runs', -2):
                    m_dst['runs'] += m_src['runs']
                    m_dst['q'] += m_src['q']
                    found = True
                    break
            else:
                m_dst['q'] += m_src['q']
                found = True
                break
        if not found:
            materials_summary.append(m_src)


def calc_materials_availability(
        materials_list_with_efficiency,
        ntier_used_and_exist_materials,
        stock_resources,
        refine_stock_resources,
        check_absolutely_not_available=True):
    # выполнение расчётов достаточности метариала и добавление его количества в summary-списки
    used_and_exist_materials = []
    not_enough_materials = []
    for m_me in materials_list_with_efficiency:
        # перебор материалов, количество которых рассчитано на основании сведений о ME
        bpmm_tid: int = m_me["id"]
        bp_manuf_need_all: int = m_me["q"]
        bp_manuf_need_min = m_me["qmin"] if check_absolutely_not_available else None
        bp_manuf_used = next((m["q"] for m in ntier_used_and_exist_materials if m["id"] == bpmm_tid), 0)
        bpmm_tnm: str = m_me["nm"]
        # проверка наличия имеющихся ресурсов для постройки по этому БП
        not_available = bp_manuf_need_all
        in_general_stock = stock_resources.get(bpmm_tid, 0)
        in_refine_stock = refine_stock_resources.get(bpmm_tid, 0)
        in_stock_remained = (in_general_stock + in_refine_stock) - bp_manuf_used
        # получаем признак того, что материалов недостаточно даже для одного рана (сток на др.станке не смотрим)
        not_available_absolutely = True
        if check_absolutely_not_available:
            not_available_absolutely = in_general_stock < bp_manuf_need_min
        # считаем сколько материала нехватает с учётом того количества, что находится в стоке (стоках)
        not_available = 0 if in_stock_remained >= not_available else not_available - in_stock_remained
        available = bp_manuf_need_all if in_stock_remained >= bp_manuf_need_all else in_stock_remained
        # сохраняем использованное из стока кол-во материалов для производства по этому чертежу
        if available > 0:
            used_and_exist_materials.append({"id": bpmm_tid, "q": available, "nm": bpmm_tnm})
        # сохраняем недостающее кол-во материалов для производства по этому чертежу
        not_available_dict = None
        if not_available > 0:
            not_available_dict = {"id": bpmm_tid, "q": not_available, "nm": bpmm_tnm}
        elif in_refine_stock and ((available + bp_manuf_used) > in_general_stock):
            not_available_dict = {"id": bpmm_tid, "q": 0, "nm": bpmm_tnm}
        # ---
        if not_available_dict:
            if check_absolutely_not_available:
                not_available_dict.update({"absol": not_available_absolutely})
            not_enough_materials.append(not_available_dict)
            del not_available_dict

    return used_and_exist_materials, not_enough_materials


# из отсутствующих ресурсов (материалов) генерируются два списка:
#  * ntier_materials_list_for_next_itr - список на обработку следующими итерациями (аналог not_enough_materials)
#  * ntier_materials_list_for_buy - список на закуп (произвести нельзя, как и подать на следующую итерацию)
def get_ntier_materials_list_of_not_available(
        not_enough_materials,
        sde_type_ids,
        sde_bp_materials,
        products_for_bps,
        reaction_products_for_bps):
    # расчёт списка материалов, предыдущего уровня вложенности
    # (по информации о ресурсах, которых не хватает)
    ntier_materials_list_for_next_itr = []
    ntier_materials_list_for_buy = []
    for m in not_enough_materials:
        m_id: int = m["id"]
        # проверяем, можно ли произвести данный ресурс (материал)?
        if m_id in products_for_bps:
            ntier_activity: str = "manufacturing"
            is_reaction_blueprint = False
        elif m_id in reaction_products_for_bps:
            ntier_activity: str = "reaction"
            is_reaction_blueprint = True
        else:
            calc_materials_summary([m], ntier_materials_list_for_buy)
            continue
        # поиск чертежа, который подходит для производства данного типа продукта
        (blueprint_type_id, blueprint_dict) = eve_sde_tools.get_blueprint_type_id_by_product_id(
            m_id,
            sde_bp_materials,
            ntier_activity)
        if not blueprint_type_id:
            calc_materials_summary([m], ntier_materials_list_for_buy)
            continue
        # получение подробной информации о чертеже
        blueprint_activity_dict = blueprint_dict["activities"][ntier_activity]
        quantity_of_single_run = blueprint_activity_dict["products"][0]["quantity"]
        # в случае, если имеем дело с реакциями, то q - это кол-во оригиналов чертежей
        # в случае, если имеем дело не с реакциями, то r - это кол-во ранов чертежа
        if is_reaction_blueprint:
            __blueprints = ceil(m["q"] / (quantity_of_single_run * 50))
            ntier_set_of_blueprints = [{"r": -1, "q": __blueprints}]
            m.update({"bp": {"q": __blueprints,
                             "runs": 50,
                             "id": blueprint_type_id,
                             "nm": eve_sde_tools.get_item_name_by_type_id(sde_type_ids, blueprint_type_id),
                             "p": quantity_of_single_run,
            }})
        else:
            __runs = ceil(m["q"] / quantity_of_single_run)
            ntier_set_of_blueprints = [{"r": __runs}]
            m.update({"bp": {"q": 1,
                             "runs": __runs,
                             "id": blueprint_type_id,
                             "nm": eve_sde_tools.get_item_name_by_type_id(sde_type_ids, blueprint_type_id),
                             "p": quantity_of_single_run,
            }})
        # расчёт материалов по информации о чертеже с учётом ME
        nemlwe = get_materials_list_for_set_of_blueprints(
            sde_type_ids,
            blueprint_activity_dict["materials"],
            ntier_set_of_blueprints,
            ntier_activity,
            # мы не знаем с какой эффективностью будет делаться вложенная работа, наверное 10?
            # по хорошему тут надо слазить в библиотеку чертежей...
            0 if is_reaction_blueprint else 10,
            is_blueprint_copy=not is_reaction_blueprint,
            fixed_number_of_runs=50 if is_reaction_blueprint else None)
        calc_materials_summary(nemlwe, ntier_materials_list_for_next_itr)
        del nemlwe
    return ntier_materials_list_for_next_itr, ntier_materials_list_for_buy


def __dump_materials_list(
        glf,
        glyphicon_name,  # glyphicon-info-sign
        heading_name,  # Used materials in progress
        materials_class,  # qind-materials-used, ...
        materials_list,
        with_copy_to_clipboard,
        with_horizontal_row):
    if len(materials_list) > 0:
        glf.write('<div class="{mcls}">'.format(mcls=materials_class))
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

        # вывод наименований материалов
        glf.write("<small>")
        for m_usd in materials_list:
            __dump_material(glf, m_usd['q'], m_usd['id'], m_usd['nm'], with_copy_to_clipboard)
        glf.write("""</small>
 </div>
</div>
</div>
""")  # qind-materials-used, media, media-body


def __dump_not_available_materials_list_rows(
        glf,
        not_enough_materials,
        # esi данные, загруженные с серверов CCP
        corp_bp_loc_data,
        corp_industry_jobs_data,
        corp_assets_tree,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        # списки контейнеров и станок из экземпляра контейнера
        stock_all_loc_ids,
        exclude_loc_ids,
        blueprint_station_ids,
        refine_stock_all_loc_ids,
        # список ресурсов, которые используются в производстве
        stock_resources,
        refine_stock_resources,
        materials_summary,
        # настройки
        with_copy_to_clipboard):
    # поиск групп, которым принадлежат материалы, которых не хватает для завершения производства по списку
    # чертеже в этом контейнере (планетарка отдельно, композиты отдельно, запуск работ отдельно)
    material_groups_initial = {}
    for __summary_dict in not_enough_materials:
        __quantity = __summary_dict["q"]
        __type_id = __summary_dict["id"]
        __item_name = __summary_dict["nm"]
        __planned = next((ms['q'] for ms in materials_summary if ms['id'] == __type_id), None)
        # компонуем сведения о материале и о способе его получения
        __material_dict = {
            "id": __type_id,
            "q": __quantity,
            "p": __planned,
            "nm": __item_name
        }
        if "bp" in __summary_dict:
            # см. компоновку элемента в get_ntier_materials_list_of_not_available
            __material_dict.update({
                "bpq": __summary_dict["bp"]["q"],
                "bpr": __summary_dict["bp"]["runs"],
                "bpid": __summary_dict["bp"]["id"],
                "bpnm": __summary_dict["bp"]["nm"],
                "bpp": __summary_dict["bp"]["p"],
            })
        # определяем, какой market-группе относится товар?
        __market_group = eve_sde_tools.get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, __type_id)
        # добавляем товар в этой список market-группы
        if str(__market_group) in material_groups_initial:
            material_groups_initial[str(__market_group)].append(__material_dict)
        else:
            material_groups_initial.update({str(__market_group): [__material_dict]})

    # вывод списка материалов, которых не хватает для завершения производства по списку чертежей
    not_available_row_num = 1
    ms_groups = material_groups_initial.keys()
    for ms_group_id in ms_groups:
        material_groups_initial[ms_group_id].sort(key=lambda m: m["nm"])
        group_diplayed = False
        for __material_dict in material_groups_initial[ms_group_id]:
            # получение данных по материалу
            ms_type_id = __material_dict["id"]
            not_available = __material_dict["q"]
            ms_item_name = __material_dict["nm"]
            ms_planned = __material_dict["p"]
            ms_blueprints = __material_dict.get("bpq", None)
            ms_runs = __material_dict.get("bpr", None)
            ms_blueprint_name = __material_dict.get("bpnm", None)
            ms_blueprint_products = __material_dict.get("bpp", None)
            # ms_blueprint_id = __material_dict.get("bpid", None)
            # получаем кол-во материалов этого типа, находящихся в стоке
            ms_in_stock = stock_resources.get(ms_type_id, None)
            # получаем кол-во метариалов этого типа, находящихся в стоке на других станциях
            m_in_refine_stock = refine_stock_resources.get(ms_type_id, None)
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
                    ' <td class="active" colspan="2"><b>{nm}</b><!--{id}-->{clbrd}</td>\n'
                    ' <td class="active"><b>Not available</b></th>'
                    ' <td class="active qind-materials-runs hidden"><b>To launch</b></th>'
                    ' <td class="active qind-materials-planned hidden"><b>Planned</b></th>'
                    ' <td class="active qind-materials-exist hidden"><b>Sotiyo</b></th>'
                    ' <td class="active qind-materials-exist hidden"><b>Tatara</b></th>'
                    ' <td class="active qind-materials-progress hidden"><b>In progress</b></th>'
                    '</tr>'.
                    format(nm=__grp_name,
                           id=ms_group_id,
                           clbrd=__copy2clpbrd))
                group_diplayed = True
            # получаем список работ, которые ведутся с этим материалом, а результаты сбрабываются в stock-ALL
            jobs = [j for j in corp_industry_jobs_data if
                    (j["product_type_id"] == ms_type_id) and
                    (j['output_location_id'] in stock_all_loc_ids)]
            in_progress = 0
            for j in jobs:
                in_progress += j["runs"]
            del jobs
            # получаем список работ, которые ведутся с этим материалом, а результаты сбрасываются в refine stock
            jobs = [j for j in corp_industry_jobs_data if
                    (j["product_type_id"] == ms_type_id) and
                    (j['output_location_id'] in refine_stock_all_loc_ids)]
            for j in jobs:
                in_progress += j["runs"]
            del jobs
            # умножаем на кол-во производимых материалов на один run
            if ms_blueprint_products is not None:
                in_progress *= ms_blueprint_products
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
                '&nbsp;<a data-target="#" role="button" data-copy="{nm}" class="qind-copy-btn"' \
                '  data-toggle="tooltip"><span class="glyphicon glyphicon-copy"' \
                '  aria-hidden="true"></span></a>'. \
                format(nm=ms_item_name if ms_blueprint_name is None else ms_blueprint_name)
            # конструируем строку со сведениями о стоках (стоке конвейера, и стоке на других станциях)
            __in_stock = ''
            if ms_in_stock:
                __in_stock = "{:,d}".format(ms_in_stock)
            __in_refine_stock = ''
            if m_in_refine_stock:
                __in_refine_stock += "{:,d}".format(m_in_refine_stock)
            # конструируем строку со сведениями о способе получения материала (кол-во ранов)
            __runs = ''
            if ms_blueprints and ms_runs:
                __runs = "{} &times; {}".format(ms_blueprints, ms_runs)
            # вывод сведений в отчёт
            glf.write(
                '<tr>\n'
                ' <th scope="row">{num}</th>\n'
                ' <td data-nm="{nm}"><img class="icn24" src="{src}"> {nm}{clbrd}</td>\n'
                ' <td data-q="{q}">{q:,d}{original}{copy}{absent}</td>\n'
                ' <td class="qind-materials-runs hidden">{r}</td>\n'
                ' <td class="qind-materials-planned hidden">{p}</td>\n'
                ' <td class="qind-materials-exist hidden">{ins}</td>\n'
                ' <td class="qind-materials-exist hidden">{inr}</td>\n'
                ' <td class="qind-materials-progress hidden">{inp}</td>\n'
                '</tr>'.
                format(num=not_available_row_num,
                       src=render_html.__get_img_src(ms_type_id, 32),
                       q=not_available,
                       p='{:,d}'.format(ms_planned) if ms_planned else '',
                       inp='{:,d}'.format(in_progress) if in_progress > 0 else '',
                       nm=ms_item_name,
                       r=__runs,
                       ins=__in_stock,
                       inr=__in_refine_stock,
                       clbrd=__copy2clpbrd,
                       original=vacant_originals_tag,
                       copy=vacant_copies_tag,
                       absent=absent_blueprints_tag)
            )
            not_available_row_num = not_available_row_num + 1


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
        refine_stock_all_loc_ids,
        # списком материалов, которых не хватает в производстве
        stock_not_enough_materials,
        # список ресурсов, которые используются в производстве
        stock_resources,
        refine_stock_resources,
        materials_summary,
        # настройки
        with_copy_to_clipboard):
    # отображение в отчёте summary-информации по недостающим материалам
    if not materials_summary:
        return
    # проверка наличия имеющихся ресурсов с учётом запаса в стоке
    (used_and_exist_materials, not_enough_materials__initial) = calc_materials_availability(
        materials_summary,
        [],
        stock_resources,
        refine_stock_resources,
        check_absolutely_not_available=False)
    if not not_enough_materials__initial:
        return
    # расчёт списка материалов, которых не хватает
    ntier: int = 0
    not_enough_materials__market = []
    not_enough_materials__intermediate = []
    not_enough_materials__cycled = not_enough_materials__initial[:]
    while not_enough_materials__cycled:
        # расчёт списка материалов, предыдущего уровня вложенности
        # (по информации о ресурсах, которых не хватает)
        (ntier_materials_list_for_next_itr, ntier_materials_list_for_buy) = get_ntier_materials_list_of_not_available(
            not_enough_materials__cycled,  # этот список изменяется (лучше выдать третьим членом tuple)
            sde_type_ids,
            sde_bp_materials,
            products_for_bps,
            reaction_products_for_bps)
        # сохраняем материалы, которые невозможно произвести, - возможен только их закуп
        if ntier_materials_list_for_buy:
            calc_materials_summary(ntier_materials_list_for_buy, not_enough_materials__market)
        # сохраняем информацию о способе получения материалов (кол-во чертежей и запусков)
        # также сохраняем информацию о недостающих материалах текущего (промежуточного) уровня вложенности
        # примечание: когда ntier==0, данные в not_enough_materials__cycled взяты по ссылке из
        #             not_enough_materials__initial, и потому уже изменены в initial-списке
        if ntier > 0:
            for m in not_enough_materials__cycled:
                if m["id"] in products_for_bps or m["id"] in reaction_products_for_bps:
                    calc_materials_summary([m], not_enough_materials__intermediate)
        # если материалов, которые пригодны для производства не найдено - завершаем итерации
        if not ntier_materials_list_for_next_itr:
            break
        # проверка наличия имеющихся ресурсов для постройки по этому БП
        # сохраняем недостающее кол-во материалов для производства по этому чертежу
        (uaem, not_enough_materials__cycled) = calc_materials_availability(
            ntier_materials_list_for_next_itr,
            used_and_exist_materials,
            stock_resources,
            refine_stock_resources,
            check_absolutely_not_available=False)
        if uaem:
            calc_materials_summary(uaem, used_and_exist_materials)
        del uaem
        # ---
        del ntier_materials_list_for_next_itr
        # переходим к следующему уровню вложенности
        ntier += 1
    del not_enough_materials__cycled

    # добавляем в список изначально отсутствующих материалов те, что надо приобрести
    # ошибка: calc_materials_summary(not_enough_materials__market, not_enough_materials__initial)

    # вывод сведений в отчёт
    glf.write("""
<div class="media qind-not-available-block">
 <div class="media-left">
  <span class="glyphicon glyphicon-remove-sign" aria-hidden="false" style="font-size: 64px;"></span>
 </div>
 <div class="media-body">
  <h4 class="media-heading">Not available materials</h4>

      <h4 class="text-primary">End-level manufacturing</h4>
       <table class="table table-condensed table-hover table-responsive">
       <tbody>
""")

    # поиск в вывод групп, которым принадлежат материалы, которых не хватает для завершения производства по списку
    # чертеже в этом контейнере (планетарка отдельно, композиты отдельно, запуск работ отдельно)
    __dump_not_available_materials_list_rows(
        glf,
        not_enough_materials__initial,
        # esi данные, загруженные с серверов CCP
        corp_bp_loc_data,
        corp_industry_jobs_data,
        corp_assets_tree,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        # списки контейнеров и станок из экземпляра контейнера
        stock_all_loc_ids,
        exclude_loc_ids,
        blueprint_station_ids,
        refine_stock_all_loc_ids,
        # список ресурсов, которые используются в производстве
        stock_resources,
        refine_stock_resources,
        materials_summary,
        # настройки
        with_copy_to_clipboard)

    del not_enough_materials__initial

    glf.write("""
       </tbody>
       </table>
""")

    if not_enough_materials__market:
        glf.write("""
<h4 class="text-primary">Entry-level purchasing</h4>
<table class="table table-condensed table-hover table-responsive">
<tbody>
""")
        __dump_not_available_materials_list_rows(
            glf,
            not_enough_materials__market,
            # esi данные, загруженные с серверов CCP
            corp_bp_loc_data,
            corp_industry_jobs_data,
            corp_assets_tree,
            # sde данные, загруженные из .converted_xxx.json файлов
            sde_type_ids,
            sde_bp_materials,
            sde_market_groups,
            # списки контейнеров и станок из экземпляра контейнера
            stock_all_loc_ids,
            exclude_loc_ids,
            blueprint_station_ids,
            refine_stock_all_loc_ids,
            # список ресурсов, которые используются в производстве
            stock_resources,
            refine_stock_resources,
            materials_summary,
            # настройки
            with_copy_to_clipboard)
        glf.write("""
</tbody>
</table>
""")

    del not_enough_materials__market

    if not_enough_materials__intermediate:
        glf.write("""
<h4 class="text-primary">Intermediate manufacturing</h4>
<table class="table table-condensed table-hover table-responsive">
<tbody>
""")
        # поиск и вывод групп, которым принадлежат материалы, которых не хватает для завершения производства по списку
        # чертеже в этом контейнере (планетарка отдельно, композиты отдельно, запуск работ отдельно)
        __dump_not_available_materials_list_rows(
            glf,
            not_enough_materials__intermediate,
            # esi данные, загруженные с серверов CCP
            corp_bp_loc_data,
            corp_industry_jobs_data,
            corp_assets_tree,
            # sde данные, загруженные из .converted_xxx.json файлов
            sde_type_ids,
            sde_bp_materials,
            sde_market_groups,
            # списки контейнеров и станок из экземпляра контейнера
            stock_all_loc_ids,
            exclude_loc_ids,
            blueprint_station_ids,
            refine_stock_all_loc_ids,
            # список ресурсов, которые используются в производстве
            stock_resources,
            refine_stock_resources,
            materials_summary,
            # настройки
            with_copy_to_clipboard)

    glf.write("""
</tbody>
</table>
    """)

    del not_enough_materials__intermediate

    glf.write("""
     </div> <!--media-body-->
    </div> <!--media-->
    """)


def get_stock_resources(stock_loc_ids, corp_ass_loc_data):
    stock_resources = {}
    if not (stock_loc_ids is None):
        for loc_id in stock_loc_ids:
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
    return stock_resources


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
    stock_all_loc_ids = set([int(ces["id"]) for ces in conveyor_entity["stock"]])
    exclude_loc_ids = set([int(cee["id"]) for cee in conveyor_entity["exclude"]])
    blueprint_loc_ids = conveyor_entity["containers"]
    blueprint_station_ids = [conveyor_entity["station_id"]]
    refine_stock_all_loc_ids = set([int(ces["id"]) for ces in conveyor_entity["refine_stock"]])
    # инициализация списка материалов, которых не хватает в производстве
    stock_not_enough_materials = []
    # формирование списка ресурсов, которые используются в производстве
    stock_resources = get_stock_resources(stock_all_loc_ids, corp_ass_loc_data)
    # формирование списка ресурсов, которые используются в производстве (лежат на других станциях, но тоже учитываются)
    refine_stock_resources = get_stock_resources(refine_stock_all_loc_ids, corp_ass_loc_data)

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
        manufacturing_activities = loc["box"]["manufacturing_activities"]
        __bp2 = corp_bp_loc_data[str(loc_id)]
        runnable_blueprints = 0
        glf.write(
            ' <div class="panel panel-default">\n'
            '  <div class="panel-heading" role="tab" id="headingB{id}">\n'
            '   <h4 class="panel-title">\n'
            '    <a role="button" data-toggle="collapse" data-parent="#accordion" '
            '       href="#collapseB{id}" aria-expanded="true" aria-controls="collapseB{id}">{station} <mark>{nm}</mark></a>'
            '    <span class="badge"><span id="rnblB{id}">0</span> of {bps}</span>\n'
            '   </h4>\n'
            '  </div>\n'
            '  <div id="collapseB{id}" class="panel-collapse collapse" role="tabpanel" '
            'aria-labelledby="headingB{id}">\n'
            '   <div class="panel-body">\n'.format(
                id=loc_id,
                station=conveyor_entity["station"],
                nm=loc_name,
                bps=len(__bp2)
            )
        )
        __type_keys = __bp2.keys()
        # сортировка чертежей по их названиям
        type_keys = []
        for type_id in __type_keys:
            type_keys.append({"id": int(type_id), "name": eve_sde_tools.get_item_name_by_type_id(sde_type_ids, int(type_id))})
        type_keys.sort(key=lambda bp: bp["name"])
        # инициализация скрытой таблицы, которая предназначена для сортировки чертежей по различным критериям
        glf.write("""
 <table class="table table-condensed table-responsive qind-blueprints-tbl">
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
                manufacturing_activities[0],
                sde_type_ids,
                sde_market_groups,
                sde_bp_materials)
            show_me_te = 'manufacturing' in manufacturing_activities or \
                         'research_material' in manufacturing_activities or \
                         'research_time' in manufacturing_activities
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
                        if 'manufacturing' in manufacturing_activities:
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
                        elif 'reaction' in manufacturing_activities:
                            # учитываем бонус профиля сооружения
                            __stage2 = float(__time * (100.0 - 25.0) / 100.0)
                            # учитываем бонус установленного модификатора
                            __stage3 = float(__stage2 * (100.0 - 22.0) / 100.0)
                            # округляем вещественное число до старшего целого
                            __stage4 = int(float(__stage3 + 0.99))
                            # ---
                            __time = __stage4
                        elif 'invention' in manufacturing_activities:
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
                            manufacturing_activities[0],
                            material_efficiency)
                        # сохраняем материалы для производства в список их суммарного кол-ва
                        calc_materials_summary(materials_list_with_efficiency, materials_used)
                        # сохраняем материалы для производства в список их суммарного кол-ва
                        calc_materials_summary(materials_list_with_efficiency, global_materials_used)
                        del materials_list_with_efficiency
                    # ---
                    glf.write('</br></span>')  # qind-blueprints-?
                elif activity_blueprint_materials is None:
                    something_else: bool = False
                    for ma in manufacturing_activities:
                        if ma not in ['copying', 'research_material', 'research_time']:
                            something_else = True
                            break
                    if something_else:
                        glf.write('&nbsp;<span class="label label-warning">{} impossible</span>'.format(",".join(manufacturing_activities)))
                    else:
                        runnable_blueprints += 1
                        if enable_copy_to_clipboard:
                            glf.write(
                                '&nbsp;<a data-target="#" role="button" data-copy="{nm}" class="qind-copy-btn"'
                                ' data-toggle="tooltip"><span class="glyphicon glyphicon-copy"'
                                ' aria-hidden="true"></span></a>'.
                                format(nm=blueprint_name)
                            )
                    glf.write('</br></span>')  # qind-blueprints-?
                else:
                    # подготовка элементов управления копирования данных в clipboard
                    if enable_copy_to_clipboard:
                        glf.write(
                            '&nbsp;<a data-target="#" role="button" data-copy="{nm}" class="qind-copy-btn"'
                            ' data-toggle="tooltip"><span class="glyphicon glyphicon-copy"'
                            ' aria-hidden="true"></span></a>'.
                            format(nm=blueprint_name)
                        )
                    glf.write('</br></span>')  # qind-blueprints-?

                    # расчёт материалов по информации о чертеже с учётом ME
                    materials_list_with_efficiency = get_materials_list_for_set_of_blueprints(
                        sde_type_ids,
                        activity_blueprint_materials,
                        bp["itm"],
                        manufacturing_activities[0],
                        material_efficiency,
                        is_blueprint_copy=is_blueprint_copy,
                        fixed_number_of_runs=fixed_number_of_runs)

                    # сохраняем материалы для производства в список их суммарного кол-ва
                    calc_materials_summary(materials_list_with_efficiency, materials_summary)
                    # сохраняем материалы для производства в ГЛОБАЛЬНЫЙ список их суммарного кол-ва
                    calc_materials_summary(materials_list_with_efficiency, global_materials_summary)

                    # проверка наличия имеющихся ресурсов для постройки по этому БП
                    # сохраняем недостающее кол-во материалов для производства по этому чертежу
                    (used_and_exist_materials, not_enough_materials) = calc_materials_availability(
                        materials_list_with_efficiency,
                        [],
                        stock_resources,
                        {})
                    if not not_enough_materials:
                        runnable_blueprints += 1

                    # вывод наименования ресурсов (материалов)
                    glf.write('<div class="qind-materials-used hidden"><small>\n')  # div(materials)
                    __dump_materials_list_with_efficiency(glf, materials_list_with_efficiency)
                    glf.write('</small></div>\n')  # div(materials)

                    # отображение списка материалов, которых не хватает
                    if not_enough_materials:
                        global g_modal_industry_seq
                        g_modal_industry_seq += 1

                        # вывод информации о недостающих материалах текущего уровня вложенности
                        glf.write('<div>\n')  # div(not_enough_materials 1-level)
                        __dump_materials_list_not_available(
                            glf,
                            not_enough_materials,
                            products_for_bps,
                            reaction_products_for_bps,
                            ntier=False)
                        glf.write('&nbsp;<button type="button" class="btn btn-default btn-xs qind-materials-used hidden"'
                                  ' data-toggle="modal" data-target="#modal{nmm}"><span class="glyphicon'
                                  ' glyphicon-expand" aria-hidden="true"></span> Show details</button>'.
                                  format(nmm=g_modal_industry_seq))
                        glf.write('</div>\n')  # div(not_enough_materials 1-level)

                        # создаём заголовок модального окна, где будем показывать вывод одних материалов в другие
                        render_html.__dump_any_into_modal_header_wo_button(
                            glf,
                            "Sequence of industry steps" if q_conveyor_settings.g_generate_with_show_details else "Industry and purchasing",
                            g_modal_industry_seq)

                        # формируем содержимое модального диалога
                        # ...

                        ntier: int = 0
                        ntier_not_enough_materials = []
                        while not_enough_materials:
                            if q_conveyor_settings.g_generate_with_show_details:
                                # вывод информации о недостающих материалах текущего уровня вложенности
                                glf.write('<div>\n')  # div(not_enough_materials 1,N-level)
                                __dump_materials_list_not_available(
                                    glf,
                                    not_enough_materials,
                                    products_for_bps,
                                    reaction_products_for_bps,
                                    ntier > 0)
                                glf.write('</div>\n')  # div(not_enough_materials 1,N-level)

                            # расчёт списка материалов, предыдущего уровня вложенности
                            # (по информации о ресурсах, которых не хватает)
                            (ntier_materials_list_for_next_itr, ntier_materials_list_for_buy) = get_ntier_materials_list_of_not_available(
                                not_enough_materials,
                                sde_type_ids,
                                sde_bp_materials,
                                products_for_bps,
                                reaction_products_for_bps)

                            # сохраняем материалы, которые невозможно произвести, - возможен только их закуп
                            if ntier_materials_list_for_buy:
                                calc_materials_summary(ntier_materials_list_for_buy, ntier_not_enough_materials)

                            # отладочная детализация (по шагам)
                            if q_conveyor_settings.g_generate_with_show_details:
                                glf.write('<div><small>')  # div(materials)
                                glf.write('<span class="text-success">')  # зелёный - забираю со склада
                                __dump_materials_list_with_efficiency(glf, used_and_exist_materials)
                                glf.write('</span><span class="text-danger">')  # красный - закупаю
                                __dump_materials_list_with_efficiency(glf, ntier_not_enough_materials)
                                glf.write('</span></small></div>\n')  # div(materials)

                            # если материалов, которые пригодны для производства не найдено - завершаем итерации
                            if not ntier_materials_list_for_next_itr:
                                break

                            # вывод наименования ресурсов (материалов)
                            if q_conveyor_settings.g_generate_with_show_details:
                                glf.write('<hr><div class="text-material-industry-ntier"><small>\n')  # div(materials)
                                __dump_materials_list_with_efficiency(glf, ntier_materials_list_for_next_itr)
                                glf.write('</small></div>\n')  # div(materials)

                            # проверка наличия имеющихся ресурсов для постройки по этому БП
                            # сохраняем недостающее кол-во материалов для производства по этому чертежу
                            (uaem, not_enough_materials) = calc_materials_availability(
                                ntier_materials_list_for_next_itr,
                                used_and_exist_materials,
                                stock_resources,
                                {},
                                check_absolutely_not_available=False)
                            if uaem:
                                calc_materials_summary(uaem, used_and_exist_materials)

                            del ntier_materials_list_for_next_itr

                            # переходим к следующему уровню вложенности
                            ntier += 1

                        # вывод наименования ресурсов (материалов) которые надо закупить или использовать
                        glf.write('<div><small>')  # div(materials) : чёрный - забираю со склада
                        __dump_materials_list_with_efficiency(glf, used_and_exist_materials)
                        glf.write('<span class="text-material-buy-ntier">')  # красный - закупаю
                        __dump_materials_list_with_efficiency(glf, ntier_not_enough_materials)
                        glf.write('</span></small></div>\n')  # div(materials)

                        # закрываем footer модального диалога
                        render_html.__dump_any_into_modal_footer(glf)

                        del ntier_not_enough_materials

                    del used_and_exist_materials
                    del not_enough_materials
                    del materials_list_with_efficiency

                glf.write('</div>\n')  # qind-bp-block
            glf.write(
                ' </div>\n'  # media-body
                '</div>\n'  # media
                '</td></tr>\n'
            )
        glf.write("""
  </tbody>
 </table>
""")

        # отображение в отчёте summary-информации по недостающим материалам
        __dump_materials_list(glf, 'glyphicon-info-sign', 'Used materials in progress', 'qind-materials-used hidden', materials_used, True, True)
        __dump_materials_list(glf, 'glyphicon-question-sign', 'Summary materials', 'qind-summary-block hidden', materials_summary, False, True)
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
            refine_stock_all_loc_ids,
            # списком материалов, которых не хватает в производстве
            stock_not_enough_materials,
            # список ресурсов, которые используются в производстве
            stock_resources,
            refine_stock_resources,
            materials_summary,
            # настройки
            enable_copy_to_clipboard)

        glf.write("""
   </div> <!--panel-body-->
  </div> <!--panel-collapse-->
 </div> <!--panel-->
""")
        glf.write(
            "<script> $(document).ready(function(){{ $('#rnblB{id}').html('{bps}'); }});</script>".
            format(id=loc_id, bps=runnable_blueprints)
        )

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
.label-not-enough { color: #fff; background-color: #f0ad4e; }
.label-impossible { color: #fff; background-color: #d9534f; }
.label-impossible-ntier { color: #fff; background-color: #e89694; }
.label-not-available { color: #fff; background-color: #b7b7b7; }
.text-material-industry-ntier { color: #aaa; }
.text-material-buy-ntier { color: #a67877; }
</style>

 <table id="tblStock" class="table table-condensed table-hover table-responsive">
<thead>
 <tr>
  <th class="hidden"></th>
  <th>#</th>
  <th>Item</th>
  <th>In stock</th>
  <th>Not available</th>
  <th>In progress (runs)</th>
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
.table > tbody > tr > td { padding: 1px; font-size: smaller; }
.table > tbody > tr > th { padding: 1px; font-size: smaller; }
.qind-blueprints-tbl > tbody > tr > td { padding: 4px; border-top: none; }
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
       <li role="separator" class="divider"></li>
       <li><a id="btnToggleUsedMaterials" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowUsedMaterials"></span> Show used materials</a></li>
       <li><a id="btnToggleSummary" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowSummary"></span> Show summary materials</a></li>
       <li><a id="btnToggleNotAvailable" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowNotAvailable"></span> Show not available materials</a></li>
       <li role="separator" class="divider"></li>
       <li><a id="btnToggleRecommendedRuns" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowRecommendedRuns"></span> Show recommended runs</a></li>
       <li><a id="btnTogglePlannedMaterials" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowPlannedMaterials"></span> Show planned materials</a></li>
       <li><a id="btnToggleExistInStock" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowExistInStock"></span> Show exist in stock</a></li>
       <li><a id="btnToggleInProgress" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowInProgress"></span> Show in progress</a></li>
       <li role="separator" class="divider"></li>
       <li><a id="btnToggleLegend" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowLegend"></span> Show legend</a></li>
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

    for corp_conveyors in conveyor_data:
        corp_blueprints_data_len = corp_conveyors["corp_bp_quantity"]
        if corp_blueprints_data_len >= 22500:  # 10%
            overflow = corp_blueprints_data_len >= 23750  # 5%
            glf.write(
                '<div class="alert alert-{alc}" role="alert">'
                '<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>'
                '<span class="sr-only">{ew}:</span> The number of corporate blueprints should not exceed 25,000 pieces.'
                ' Otherwise, they cannot be found in the industry control window. Also, the correctness of the'
                ' calculations of industry processes will suffer. <b>{cnm}</b> now has <b>{q:,d}</b> blueprints in'
                ' assets.'
                '</div>'.
                format(
                    alc='danger' if overflow else 'warning',
                    ew='Error' if overflow else 'Warning',
                    cnm=corp_conveyors["corporation_name"],
                    q=corp_blueprints_data_len,
                ))

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
            glf.write("<div>")  # <h3>Summary</h3>

            # Внимание! нельзя в кучу сваливать все чертежи материалы, нужно их разделить на группы по станциям
            __dump_materials_list(glf, 'glyphicon-info-sign', 'Used materials in progress', 'qind-materials-used hidden', global_materials_used, True, True)
            __dump_materials_list(glf, 'glyphicon-question-sign', 'Summary materials', 'qind-summary-block hidden', global_materials_summary, False, True)

            # получение списков контейнеров и станок из экземпляра контейнера
            global_stock_all_loc_ids = []
            global_exclude_loc_ids = []
            global_refine_stock_all_loc_ids = []
            # global_blueprint_loc_ids = []
            global_blueprint_station_ids = []
            for conveyor_entity in corp_conveyors["corp_conveyour_entities"]:
                for id in [int(ces["id"]) for ces in conveyor_entity["stock"]]:
                    if not (id in global_stock_all_loc_ids):
                        global_stock_all_loc_ids.append(id)
                for id in [int(cee["id"]) for cee in conveyor_entity["exclude"]]:
                    if not (id in global_exclude_loc_ids):
                        global_exclude_loc_ids.append(id)
                for id in [int(cess["id"]) for cess in conveyor_entity["refine_stock"]]:
                    if not (id in global_refine_stock_all_loc_ids):
                        global_refine_stock_all_loc_ids.append(id)
                # for id in conveyor_entity["containers"]:
                #     if not (id in global_blueprint_loc_ids):
                #         global_blueprint_loc_ids.append(id)
                if not (conveyor_entity["station_id"] in global_blueprint_station_ids):
                    global_blueprint_station_ids.append(conveyor_entity["station_id"])
            # переводим списки в множества для ускорения работы программы
            global_stock_all_loc_ids = set(global_stock_all_loc_ids)
            global_exclude_loc_ids = set(global_exclude_loc_ids)
            global_refine_stock_all_loc_ids = set(global_refine_stock_all_loc_ids)
            # формирование списка ресурсов, которые используются в производстве
            global_stock_resources = get_stock_resources(global_stock_all_loc_ids, corp_conveyors["corp_ass_loc_data"])
            # формирование списка ресурсов, которые используются в производстве (но лежат на других станциях)
            global_refine_stock_resources = get_stock_resources(global_refine_stock_all_loc_ids, corp_conveyors["corp_ass_loc_data"])

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
                global_refine_stock_all_loc_ids,
                # списком материалов, которых не хватает в производстве
                stock_not_enough_materials,
                # список ресурсов, которые используются в производстве
                global_stock_resources,
                global_refine_stock_resources,
                global_materials_summary,
                # настройки
                True)
            glf.write("</div>")  # <h3>Summary</h3>

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

  function resetOptionToDefault(opt, def) {
    if (!ls.getItem(opt)) ls.setItem(opt, def);
  }
  function displayOptionInMenu(opt, img) {
    show = ls.getItem(opt);
    if (show == 1)
      img.removeClass('hidden');
    else
      img.addClass('hidden');
  }

  // Conveyor Options storage (init)
  function resetOptionsMenuToDefault() {
    resetOptionToDefault('Show Legend', 1);
    resetOptionToDefault('Show Summary', 0);
    resetOptionToDefault('Show Not Available', 0);
    resetOptionToDefault('Show Impossible', 1);
    resetOptionToDefault('Show Active', 1);
    resetOptionToDefault('Show Used Materials', 1);
    resetOptionToDefault('Show Exist In Stock', 0);
    resetOptionToDefault('Show In Progress', 0);
    resetOptionToDefault('Show Planned Materials', 0);
    resetOptionToDefault('Show Recommended Runs', 1);
  }
  // Conveyor Options storage (rebuild menu components)
  function rebuildOptionsMenu() {
    displayOptionInMenu('Show Legend', $('#imgShowLegend'));
    displayOptionInMenu('Show Summary', $('#imgShowSummary'));
    displayOptionInMenu('Show Not Available', $('#imgShowNotAvailable'));
    displayOptionInMenu('Show Impossible', $('#imgShowImpossible'));
    displayOptionInMenu('Show Active', $('#imgShowActive'));
    displayOptionInMenu('Show Used Materials', $('#imgShowUsedMaterials'));
    displayOptionInMenu('Show Exist In Stock', $('#imgShowExistInStock'));
    displayOptionInMenu('Show Planned Materials', $('#imgShowPlannedMaterials'));
    displayOptionInMenu('Show Recommended Runs', $('#imgShowRecommendedRuns'));
    displayOptionInMenu('Show In Progress', $('#imgShowInProgress'));
    show = ls.getItem('Show ');
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
        bp_block.find('span.label-impossible').each(function() {
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
    show = ls.getItem('Show Not Available');
    $('div.qind-not-available-block').each(function() {
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
    show = ls.getItem('Show Used Materials');
    $('.qind-materials-used').each(function() {
      if (show == 1)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
    show = ls.getItem('Show Exist In Stock');
    $('.qind-materials-exist').each(function() {
      if (show == 1)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
    show = ls.getItem('Show Planned Materials');
    $('.qind-materials-planned').each(function() {
      if (show == 1)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
    show = ls.getItem('Show Recommended Runs');
    $('.qind-materials-runs').each(function() {
      if (show == 1)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
    show = ls.getItem('Show In Progress');
    $('.qind-materials-progress').each(function() {
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
    $('#btnToggleNotAvailable').on('click', function () { toggleMenuOption('Show Not Available'); });
    $('#btnToggleImpossible').on('click', function () { toggleMenuOption('Show Impossible'); });
    $('#btnToggleActive').on('click', function () { toggleMenuOption('Show Active'); });
    $('#btnToggleUsedMaterials').on('click', function () { toggleMenuOption('Show Used Materials'); });
    $('#btnToggleExistInStock').on('click', function () { toggleMenuOption('Show Exist In Stock'); });
    $('#btnTogglePlannedMaterials').on('click', function () { toggleMenuOption('Show Planned Materials'); });
    $('#btnToggleRecommendedRuns').on('click', function () { toggleMenuOption('Show Recommended Runs'); });
    $('#btnToggleInProgress').on('click', function () { toggleMenuOption('Show In Progress'); });
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
                data_copy += td.attr('data-nm') + "\\t" + $(this).find('td').eq(1).attr('data-q');
              }
            }
          });
        } else if (data_source == 'span') {
          data_copy = '';
          var small = $(this).parent().find('small');
          if (!(small === undefined)) {
            var spans = small.children('span');
            if (!(small === undefined)) {
              spans.each( function(idx) {
                var span = $(this);
                if (data_copy) data_copy += "\\n";
                data_copy += span.attr('data-nm') + "\\t" + span.attr('data-q');
              });
            }
          }
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
