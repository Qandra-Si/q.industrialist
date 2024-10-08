﻿import typing
import render_html
import eve_sde_tools
import eve_esi_tools
import eve_efficiency
import eve_conveyor_tools
from render_html import get_span_glyphicon as glyphicon
from math import ceil

import q_conveyor_settings


g_modal_industry_seq = 1


def __is_availabe_blueprints_present(
        blueprint_type_id,
        is_reaction,
        corp_bp_loc_data,
        exclude_loc_ids,
        blueprint_station_ids,
        react_station_ids,
        corp_assets_tree):
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
        # пропускаем прочие станции, на которых нет текущего stock-а и нет конвейеров/реакций (ищем свою станку)
        if is_reaction:
            if not eve_esi_tools.is_location_nested_into_another(loc_id, react_station_ids, corp_assets_tree):
                continue
        else:
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


def __dump_material(glf, quantity: int, type_id: int, type_name: str, with_copy_to_clipboard: bool = False):
    # вывод наименования ресурса
    glf.write(
        '<tid{qq}{nnm}><img class="icn24" src="{src}"> <b>{q:,d}</b> {nm} </tid>\n'.
        format(
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
        # - всегда все T3 технологии запускаются с декриптором Parity Decryptor
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
            elif 1909 in groups_chain:  # Ancient Relics
                """ вот так можно проверить чертёж для T3-хулов:
                type_dict = sde_type_ids.get(str(blueprint_type_id)) :
                if type_dict.get("groupID", -1) == 997: ... # Hull
                """
                activity_blueprint_materials.append({'quantity': 1, 'typeID': 34204})  # Parity Decryptor
    # ---
    del activity_dict
    return activity_time, activity_blueprint_materials


# blueprints_details - подробности о чертежах этого типа: [{"q": -1, "r": -1}, {"q": 2, "r": -1}, {"q": -2, "r": 179}]
# метод возвращает список tuple: [{"id": 11399, "q": 11, "qmin": 11", "nm": "Morphite"}] с учётом ME
def get_materials_list_for_set_of_blueprints__obsolete(
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


def calc_materials_summary__obsolete(
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


def calc_materials_availability__obsolete(
        materials_list_with_efficiency,
        ntier_used_and_exist_materials,
        manufacturing_stock_resources,
        reaction_stock_resources,
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
        # устанавливаем, где и как именно производится данный вид продукта, либо где находится его сток?
        # проверка наличия имеющихся ресурсов для постройки по этому БП
        not_available = bp_manuf_need_all
        in_manufacturing_stock = manufacturing_stock_resources.get(bpmm_tid, 0)
        in_reaction_stock = reaction_stock_resources.get(bpmm_tid, 0)
        in_stock_remained = (in_manufacturing_stock + in_reaction_stock) - bp_manuf_used
        # получаем признак того, что материалов недостаточно даже для одного рана (сток на др.станке не смотрим)
        not_available_absolutely = True
        if check_absolutely_not_available:
            not_available_absolutely = in_manufacturing_stock < bp_manuf_need_min
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
        elif in_reaction_stock and ((available + bp_manuf_used) > in_manufacturing_stock):
            not_available_dict = {"id": bpmm_tid, "q": 0, "nm": bpmm_tnm}
        # ---
        if not_available_dict:
            if check_absolutely_not_available:
                not_available_dict.update({"absol": not_available_absolutely})
            not_enough_materials.append(not_available_dict)
            del not_available_dict
    # вывод материалов в стоке имеющихся и помеченным использованными, а также список недостающего кол-ва
    return used_and_exist_materials, not_enough_materials


# из отсутствующих ресурсов (материалов) генерируются три списка:
#  * ntier_materials_list_for_next_itr__sotiyo - список на обработку следующими итерациями (аналог not_enough_materials)
#  * ntier_materials_list_for_next_itr__tatara - список на обработку следующими итерациями (аналог not_enough_materials)
#  * ntier_materials_list_for_buy - список на закуп (произвести нельзя, как и подать на следующую итерацию)
def get_ntier_materials_list_of_not_available__obsolete(
        not_enough_materials,
        sde_type_ids,
        sde_bp_materials,
        products_for_bps,
        reaction_products_for_bps):
    # расчёт списка материалов, предыдущего уровня вложенности
    # (по информации о ресурсах, которых не хватает)
    ntier_materials_list_for_next_itr__sotiyo = []
    ntier_materials_list_for_next_itr__tatara = []
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
            calc_materials_summary__obsolete([m], ntier_materials_list_for_buy)
            continue
        # поиск чертежа, который подходит для производства данного типа продукта
        (blueprint_type_id, blueprint_dict) = eve_sde_tools.get_blueprint_type_id_by_product_id(
            m_id,
            sde_bp_materials,
            sde_type_ids,
            ntier_activity)
        if not blueprint_type_id:
            calc_materials_summary__obsolete([m], ntier_materials_list_for_buy)
            continue
        # получение подробной информации о чертеже
        blueprint_activity_dict = blueprint_dict["activities"][ntier_activity]
        quantity_of_single_run = blueprint_activity_dict["products"][0]["quantity"]
        # в случае, если имеем дело с реакциями, то q - это кол-во оригиналов чертежей
        # в случае, если имеем дело не с реакциями, то r - это кол-во ранов чертежа
        if is_reaction_blueprint:
            __blueprints = ceil(m["q"] / (quantity_of_single_run * 15))  # TODO: надо использовать in_cache.runs_number_per_day
            ntier_set_of_blueprints = [{"r": -1, "q": __blueprints}]
            m.update({"bp": {"q": __blueprints,
                             "runs": 15,  # TODO: надо использовать in_cache.runs_number_per_day
                             "id": blueprint_type_id,
                             "a": ntier_activity,
                             "nm": eve_sde_tools.get_item_name_by_type_id(sde_type_ids, blueprint_type_id),
                             "p": quantity_of_single_run,
            }})
        else:
            __runs = ceil(m["q"] / quantity_of_single_run)
            ntier_set_of_blueprints = [{"r": __runs}]
            m.update({"bp": {"q": 1,
                             "runs": __runs,
                             "id": blueprint_type_id,
                             "a": ntier_activity,
                             "nm": eve_sde_tools.get_item_name_by_type_id(sde_type_ids, blueprint_type_id),
                             "p": quantity_of_single_run,
            }})
        # расчёт материалов по информации о чертеже с учётом ME
        nemlwe = get_materials_list_for_set_of_blueprints__obsolete(
            sde_type_ids,
            blueprint_activity_dict["materials"],
            ntier_set_of_blueprints,
            ntier_activity,
            # мы не знаем с какой эффективностью будет делаться вложенная работа, наверное 10?
            # по хорошему тут надо слазить в библиотеку чертежей...
            0 if is_reaction_blueprint else 10,
            is_blueprint_copy=not is_reaction_blueprint,
            fixed_number_of_runs=15 if is_reaction_blueprint else None)  # TODO: надо использовать in_cache.runs_number_per_day
        if not is_reaction_blueprint:
            calc_materials_summary__obsolete(nemlwe, ntier_materials_list_for_next_itr__sotiyo)
        else:
            calc_materials_summary__obsolete(nemlwe, ntier_materials_list_for_next_itr__tatara)
        del nemlwe
    return ntier_materials_list_for_next_itr__sotiyo, ntier_materials_list_for_next_itr__tatara, ntier_materials_list_for_buy


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
        glf.write("<div class='qind-tid'>")
        for m_usd in materials_list:
            __dump_material(glf, m_usd['q'], m_usd['id'], m_usd['nm'], with_copy_to_clipboard)
        glf.write("""</div>
 </div>
</div>
</div>
""")  # qind-materials-used, media, media-body


def __dump_not_available_materials_list_rows(
        glf,
        not_enough_materials,
        conveyor_materials: eve_conveyor_tools.ConveyorMaterials,
        mutable_row_num: typing.List[int],
        # esi данные, загруженные с серверов CCP
        corp_bp_loc_data,
        corp_assets_tree,
        # списки контейнеров и станок из экземпляра контейнера
        exclude_loc_ids,
        blueprint_station_ids,
        react_station_ids,
        # настройки
        with_copy_to_clipboard__blueprints,
        with_copy_to_clipboard__signs,
        dump_listed_table_cells):
    # поиск групп материалов, которых где не хватает для завершения производства по списку
    # чертежи в этом контейнере (планетарка отдельно, композиты отдельно, запуск работ отдельно)
    material_groups: typing.Dict[int, typing.List[eve_conveyor_tools.ConveyorItem]] = {}
    for type_id in not_enough_materials:
        in_cache: eve_conveyor_tools.ConveyorItem = conveyor_materials.get(type_id)
        # определяем, какой market-группе относится товар?
        group_id: int = in_cache.basis_market_group
        # добавляем товар в этот список market-группы
        group_dict = material_groups.get(group_id)
        if group_dict is None:
            material_groups[group_id] = [in_cache]
        else:
            group_dict.append(in_cache)
    # вывод списка материалов, которых не хватает для завершения производства по списку чертежей
    group_header_first_time: bool = True
    nonhidden_group_header_first_time: bool = True
    ms_groups = material_groups.keys()
    for ms_group_id in ms_groups:
        material_groups[ms_group_id].sort(key=lambda m: m.name)
        group_with_are_enough = True
        # считаем остатки и потребности кол-ва материалов в стоке
        for in_cache in material_groups[ms_group_id]:
            if in_cache.get_not_available_in_all_stocks():
                group_with_are_enough = False
                break
        group_diplayed = False
        for in_cache in material_groups[ms_group_id]:
            # получение данных по материалу
            ms_type_id: int = in_cache.type_id
            ms_item_name: str = in_cache.name
            # получаем информацию по плану работ
            ms_blueprints = in_cache.runs_and_jobs[0].get("q") if in_cache.runs_and_jobs else None
            ms_runs = in_cache.runs_and_jobs[0].get("runs") if in_cache.runs_and_jobs else None
            # получаем информацию о чертеже
            ms_blueprint_type_id = in_cache.blueprint_type_id
            ms_blueprint_name = in_cache.blueprint_name
            ms_blueprint_products = in_cache.products_per_single_run
            is_reaction = in_cache.is_reaction
            ms_where = in_cache.where
            # получаем информацию по кол-ву ранов, которое можно выполнить при имеющемся кол-ве ресурсов
            ms_runs_number_per_day: typing.Optional[int] = in_cache.runs_number_per_day
            ms_possible_jobs: typing.Optional[int] = None
            if ms_runs is not None and ms_runs_number_per_day is not None:
                ms_possible_jobs = conveyor_materials.check_possible_job_runs(in_cache)
                if (ms_runs_number_per_day * ms_possible_jobs) > (ms_runs * ms_blueprints):
                    if ms_runs == ms_runs_number_per_day:
                        ms_possible_jobs = ms_blueprints
                    else:
                        ms_possible_jobs = ceil((ms_runs * ms_blueprints) / ms_runs_number_per_day)
            # считаем остатки и потребности кол-ва материалов в стоке
            ms_planned__manuf: int = in_cache.reserved_in_manuf_stock
            ms_planned__react: int = in_cache.reserved_in_react_stock
            # получаем кол-во материалов этого типа, находящихся в стоке
            ms_in_stock__manuf: int = in_cache.exist_in_manuf_stock
            ms_in_stock__react: int = in_cache.exist_in_react_stock
            # считаем остатки и потребности кол-ва материалов в стоке
            ms_not_available__manuf: int = (ms_planned__manuf - ms_in_stock__manuf) if ms_in_stock__manuf < ms_planned__manuf else 0
            ms_not_available__react: int = (ms_planned__react - ms_in_stock__react) if ms_in_stock__react < ms_planned__react else 0
            # считаем кол-во материалов, которые планируется забрать из стока (м.б. весь сток, либо не больше planned)
            ms_consumed__manuf: int = ms_in_stock__manuf if ms_in_stock__manuf < ms_planned__manuf else ms_planned__manuf
            ms_consumed__react: int = ms_in_stock__react if ms_in_stock__react < ms_planned__react else ms_planned__react
            # считаем кол-во материалов, которое производится в сток
            # TODO: вывести предупреждение о том, что какие-то материалы производятся ИЗ конвейера НЕ В сток
            ms_in_progress = in_cache.in_progress
            # считаем признак того, что материала произведено (или УЖЕ производится) достаточное кол-во
            ms_not_available: bool = (ms_not_available__manuf + ms_not_available__react) > ms_in_progress
            # TODO: вывести таблицу со сводной информацией о необходимости транспортировки накопленного между станциями
            ms_need_stock_transfer__manuf: bool = in_cache.need_transfer_into_manuf_stock()
            ms_need_stock_transfer__react: bool = in_cache.need_transfer_into_react_stock()
            # выводим название группы материалов (Ship Equipment, Materials, Components, ...)
            if not group_diplayed:
                group_dict = in_cache.basis_market_group_dict
                if not group_dict:
                    __grp_name = "Unknown"
                    __icon_id = 0
                else:
                    __grp_name = group_dict["nameID"]["en"]
                    __icon_id = group_dict.get("iconID", 0)
                # подготовка элементов управления копирования данных в clipboard
                __copy2clpbrd = '' if not with_copy_to_clipboard__blueprints else \
                    '&nbsp;<a data-target="#" role="button" class="qind-copy-btn" data-source="table"' \
                    ' data-toggle="tooltip"><button type="button" class="btn btn-default btn-xs">'+glyphicon("copy")+ \
                    ' Export to multibuy</button></a>'
                # подготовка стиля строки, который меняется в зависимости от ей порядка в таблице и содержимого таблицы
                __tr_class = ''
                if group_with_are_enough:
                    __tr_class = 'qind-em hidden'
                __high_group_header: bool = False
                if group_header_first_time or not group_with_are_enough and nonhidden_group_header_first_time:
                    __tr_class += ' ' if __tr_class else ''
                    __tr_class += 'qind-fgh'
                    group_header_first_time = False
                    if not group_with_are_enough:
                        nonhidden_group_header_first_time = False
                    __high_group_header = True
                if __tr_class:
                    __tr_class = ' class="' + __tr_class + '"'
                glf.write(
                    '<tr{trcl}>\n'
                    '<td class="active" colspan="2"><b>{nm}</b><!--{id}-->{clbrd}</td>\n'
                    '<th class="active qind-mr">{prfx}Sotiyo</th>\n'
                    '<th class="active qind-mr">{prfx}Tatara</th>\n'.
                    format(nm=__grp_name,
                           id=ms_group_id,
                           clbrd=__copy2clpbrd,
                           trcl=__tr_class,
                           prfx='Required<br>' if __high_group_header else '',
                           ))
                if 'runs' in dump_listed_table_cells:
                    glf.write(
                        '<th class="active qind-rr hidden">To launch</th>\n'
                        '<th class="active qind-pr hidden">Possible</th>\n'
                    )
                if 'planned' in dump_listed_table_cells:
                    glf.write(
                        '<th class="active qind-mp hidden">{prfx}Sotiyo</th>\n'
                        '<th class="active qind-mp hidden">{prfx}Tatara</th>\n'.
                        format(prfx='Planned<br>' if __high_group_header else '',
                               ))
                if 'consumed' in dump_listed_table_cells:
                    glf.write(
                        '<th class="active qind-mc hidden">{prfx}Sotiyo</th>\n'
                        '<th class="active qind-mc hidden">{prfx}Tatara</th>\n'.
                        format(prfx='Consumed<br>' if __high_group_header else '',
                               ))
                if 'exist' in dump_listed_table_cells:
                    glf.write(
                        '<th class="active qind-me hidden">{prfx}Sotiyo</th>\n'
                        '<th class="active qind-me hidden">{prfx}Tatara</th>\n'.
                        format(prfx='Stock<br>' if __high_group_header else '',
                               ))
                if 'progress' in dump_listed_table_cells:
                    glf.write('<th class="active qind-ip hidden">In progress</th>\n')
                glf.write('</tr>\n')
                group_diplayed = True
            # получаем список чертежей, которые имеются в распоряжении корпорации для постройки этих материалов
            vacant_originals, vacant_copies, not_a_product = __is_availabe_blueprints_present(
                ms_blueprint_type_id,
                is_reaction,
                corp_bp_loc_data,
                exclude_loc_ids,
                blueprint_station_ids,
                react_station_ids,
                corp_assets_tree)
            # формируем информационные тэги по имеющимся (вакантным) чертежам для запуска производства
            __blueprints_availability: str = ''
            if ms_where is not None and ((ms_not_available__manuf + ms_not_available__react) > ms_in_progress):
                if not not_a_product and vacant_originals:
                    __blueprints_availability += ' <span class="label label-{st}">{txt}</span>'.\
                        format(st='success' if is_reaction else 'info',
                               txt='formula' if is_reaction else 'original')
                if not not_a_product and vacant_copies:
                    __blueprints_availability += ' <span class="label label-default">copy</span>'
                if not not_a_product and not vacant_originals and not vacant_copies:
                    __blueprints_availability += ' <span class="label label-danger">no {txt}</span>'.\
                        format(txt='formulas' if is_reaction else 'blueprints')
                if __blueprints_availability:
                    __blueprints_availability = '<div class="qind-ba">' + __blueprints_availability + '</div>'
            # подготовка элемента с признаком необходимости передачи накопленных стоков в другую локацию
            __transfer_sign__manuf = ''
            __transfer_sign__react = ''
            if with_copy_to_clipboard__signs:
                if ms_need_stock_transfer__manuf:
                    __transfer_sign__manuf = \
                        '<a data-target="#" role="button" data-copy="{q}" class="qind-copy-btn qind-sign"' \
                        ' data-toggle="tooltip">{gly}</a> '. \
                        format(q=ms_not_available__manuf, gly=glyphicon("transfer"))
                if ms_need_stock_transfer__react:
                    __transfer_sign__react = \
                        '<a data-target="#" role="button" data-copy="{q}" class="qind-copy-btn qind-sign"' \
                        ' data-toggle="tooltip">{gly}</a> '. \
                        format(q=ms_not_available__react, gly=glyphicon("transfer"))
            # подготовка элементов управления копирования данных в clipboard
            __copy2clpbrd = ''
            if with_copy_to_clipboard__blueprints and ms_blueprint_type_id is not None:
                __copy2clpbrd =\
                    '&nbsp;<a data-target="#" role="button" data-copy="{nm}" class="qind-copy-btn"' \
                    ' data-toggle="tooltip">{gly}</a>'. \
                    format(nm=ms_item_name if ms_blueprint_name is None else ms_blueprint_name, gly=glyphicon("copy"))
            # если предыдущее условие не отработало, то нет чертежа, поэтому следующее настроит копирование материала
            if with_copy_to_clipboard__blueprints and ms_blueprint_type_id is None or \
               with_copy_to_clipboard__signs and (ms_need_stock_transfer__manuf or ms_need_stock_transfer__react):
                __copy2clpbrd +=\
                    '&nbsp;<a data-target="#" role="button" data-copy="{nm}" class="qind-copy-btn qind-sign"' \
                    ' data-toggle="tooltip">{gly}</a>'. \
                    format(nm=ms_item_name, gly=glyphicon("copy"))
            # конструируем строку со сведениями о способе получения материала (кол-во ранов)
            __runs = "{} &times; {:,d}".format(ms_blueprints, ms_runs) if ms_blueprints and ms_runs else ''
            __possible_jobs = "{} &times; {:,d}".format(ms_possible_jobs, ms_runs_number_per_day) if ms_possible_jobs and ms_runs_number_per_day else ''
            # вывод сведений в отчёт
            glf.write(
                '<tr{em}>\n'
                ' <th scope="row">{num}</th>\n'
                ' <td data-nm="{nm}"><img class="icn24" src="{src}"> {nm}{clbrd}{ba}</td>\n'
                ' <td{qm} class="qind-mr">{tsm}{qtm}</td>\n'
                ' <td{qr} class="qind-mr">{tsr}{qtr}</td>\n'.
                format(num=mutable_row_num[0],
                       src=render_html.__get_img_src(ms_type_id, 32),
                       nm=ms_item_name,
                       clbrd=__copy2clpbrd,
                       ba=__blueprints_availability,
                       qm=' data-q="{}"'.format(ms_not_available__manuf) if ms_not_available__manuf else '',
                       qr=' data-q="{}"'.format(ms_not_available__react) if ms_not_available__react else '',
                       tsm=__transfer_sign__manuf,
                       tsr=__transfer_sign__react,
                       qtm="{:,d}".format(ms_not_available__manuf) if ms_not_available__manuf else '',
                       qtr="{:,d}".format(ms_not_available__react) if ms_not_available__react else '',
                       em='' if ms_not_available else ' class="qind-em hidden"'
                       ))
            if 'runs' in dump_listed_table_cells:
                glf.write(
                    ' <td class="qind-rr hidden">{r}</td>\n'
                    ' <td class="qind-pr hidden">{pr}</td>\n'.
                    format(r=__runs, pr=__possible_jobs)
                )
            if 'planned' in dump_listed_table_cells:
                glf.write(
                    ' <td class="qind-mp hidden">{pm}</td>\n'
                    ' <td class="qind-mp hidden">{pr}</td>\n'.
                    format(pm="{:,d}".format(ms_planned__manuf) if ms_planned__manuf else '',
                           pr="{:,d}".format(ms_planned__react) if ms_planned__react else '',
                           ))
            if 'consumed' in dump_listed_table_cells:
                glf.write(
                    ' <td class="qind-mc hidden">{pm}</td>\n'
                    ' <td class="qind-mc hidden">{pr}</td>\n'.
                    format(pm="{:,d}".format(ms_consumed__manuf) if ms_consumed__manuf else '',
                           pr="{:,d}".format(ms_consumed__react) if ms_consumed__react else '',
                           ))
            if 'exist' in dump_listed_table_cells:
                glf.write(
                    ' <td class="qind-me hidden">{tsr}{ins}</td>\n'
                    ' <td class="qind-me hidden">{tsm}{inr}</td>\n'.
                    format(ins="{:,d}".format(ms_in_stock__manuf) if ms_in_stock__manuf else '',
                           inr="{:,d}".format(ms_in_stock__react) if ms_in_stock__react else '',
                           tsm=__transfer_sign__manuf,
                           tsr=__transfer_sign__react,
                           ))
            if 'progress' in dump_listed_table_cells:
                glf.write(' <td class="qind-ip hidden">{inp}</td>\n'.format(inp='{:,d}'.format(ms_in_progress) if ms_in_progress else ''))
            glf.write('</tr>')
            mutable_row_num[0] += 1


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
        sde_long_term_industry,
        # списки контейнеров и станок из экземпляра контейнера
        manufacturing_blueprint_loc_ids,
        manufacturing_stock_loc_ids,
        exclude_loc_ids,
        blueprint_station_ids,
        reaction_stock_loc_ids,
        react_station_ids,
        # список материалов, которых не хватает в производстве
        stock_not_enough_materials,
        # список ресурсов, которые используются в производстве
        manufacturing_stock_resources,
        reaction_stock_resources,
        materials_summary,
        # настройки
        with_copy_to_clipboard,
        with_list_of_assets_movement):
    # отображение в отчёте summary-информации по недостающим материалам
    if not materials_summary:
        return
    # построение справочника материалов, используемых в производстве и производство которых предполагается
    conveyor_materials = eve_conveyor_tools.ConveyorMaterials(
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        sde_long_term_industry,
        # esi данные, загруженные с серверов CCP
        corp_industry_jobs_data,
        # списки контейнеров и станок из экземпляра контейнера
        manufacturing_blueprint_loc_ids,
        manufacturing_stock_loc_ids,
        reaction_stock_loc_ids,
        # список ресурсов, которые используются в производстве
        manufacturing_stock_resources,
        reaction_stock_resources)
    # расчёт списка материалов, требуемых для производства заданного списка продуктов, в формате: ['id':?,'q':?]
    conveyor_materials.calc_not_available_materials_list(materials_summary)

    # добавляем в список изначально отсутствующих материалов те, что надо приобрести, initial-список и т.п.
    type_ids = conveyor_materials.materials.keys()
    not_enough_materials__market = [t for t in type_ids if conveyor_materials.get(t).blueprint_type_id is None]
    not_enough_materials__initial = [t for t in type_ids if t not in not_enough_materials__market and conveyor_materials.get(t).user_data.get('initial')]
    not_enough_materials__intermediate = [t for t in type_ids if t not in not_enough_materials__market and t not in not_enough_materials__initial]
    # построение списка материалов, которые надо перевезти с одной станции на другую
    list_of_assets_movement__materials = [t for t in type_ids if conveyor_materials.get(t).need_transfer_between_stocks()]
    del type_ids

    # номер строки, с которой пойдёт отсчёт (строка будет уникальная в группе таблиц, чтобы голосом быстро находить)
    mutable_not_available_row_num: typing.List[int] = [1]

    # считаем достаточно ли материалов в группах, чтобы сделать возможность прятать их
    group_with_are_enough__initial = True
    for type_id in not_enough_materials__initial:
        in_cache: eve_conveyor_tools.ConveyorItem = conveyor_materials.get(type_id)
        if in_cache.get_not_available_in_all_stocks():
            group_with_are_enough__initial = False
            break
    group_with_are_enough__market = True
    for type_id in not_enough_materials__market:
        in_cache: eve_conveyor_tools.ConveyorItem = conveyor_materials.get(type_id)
        if in_cache.get_not_available_in_all_stocks():
            group_with_are_enough__market = False
            break
    group_with_are_enough__intermediate = True
    for type_id in not_enough_materials__intermediate:
        in_cache: eve_conveyor_tools.ConveyorItem = conveyor_materials.get(type_id)
        if in_cache.get_not_available_in_all_stocks():
            group_with_are_enough__intermediate = False
            break

    # поиск в вывод групп, которым принадлежат материалы, которых не хватает для завершения производства по списку
    # чертеже в этом контейнере (планетарка отдельно, композиты отдельно, запуск работ отдельно)

    if group_with_are_enough__initial and group_with_are_enough__market and group_with_are_enough__intermediate:
        glf.write('<div class="qind-em hidden">')
    glf.write("""
<div class="media qind-not-available-block hidden">
 <div class="media-left">
  <span class="glyphicon glyphicon-remove-sign" aria-hidden="false" style="font-size: 64px;"></span>
 </div>
 <div class="media-body">
  <h4 class="media-heading">Not available materials</h4>
""")

    if not_enough_materials__initial:
        if group_with_are_enough__initial:
            glf.write('<div class="qind-em hidden">')
        glf.write("""
<div class="qind-endlvl-manuf-block">
 <h4 class="text-primary">End-level manufacturing</h4>
 <div class="table-responsive">
  <table class="table table-condensed table-hover qind-end-level-manuf qind-table-materials">
  <tbody>
""")
        __dump_not_available_materials_list_rows(
            glf,
            not_enough_materials__initial,
            conveyor_materials,
            mutable_not_available_row_num,
            # esi данные, загруженные с серверов CCP
            corp_bp_loc_data,
            corp_assets_tree,
            # списки контейнеров и станок из экземпляра контейнера
            exclude_loc_ids,
            blueprint_station_ids,
            react_station_ids,
            # настройки
            with_copy_to_clipboard,
            with_copy_to_clipboard,
            {'runs', 'planned', 'consumed', 'exist', 'progress'})
        glf.write("""
  </tbody>
  </table>
 </div>
</div> <!-- qind-endlvl-manuf-block -->
""")
        if group_with_are_enough__initial:
            glf.write('</div>')
    del not_enough_materials__initial

    if not_enough_materials__market:
        if group_with_are_enough__market:
            glf.write('<div class="qind-em hidden">')
        glf.write("""
<div class="qind-entry-purch-block hidden">
 <h4 class="text-primary">Entry-level purchasing</h4>
 <div class="table-responsive">
  <table class="table table-condensed table-hover qind-entry-level-purch qind-table-materials">
  <tbody>
""")
        __dump_not_available_materials_list_rows(
            glf,
            not_enough_materials__market,
            conveyor_materials,
            mutable_not_available_row_num,
            # esi данные, загруженные с серверов CCP
            corp_bp_loc_data,
            corp_assets_tree,
            # списки контейнеров и станок из экземпляра контейнера
            exclude_loc_ids,
            blueprint_station_ids,
            react_station_ids,
            # настройки
            with_copy_to_clipboard,
            with_copy_to_clipboard,
            {'planned', 'exist'})
        glf.write("""
  </tbody>
  </table>
 </div>
</div> <!-- qind-entry-purch-block -->
""")
        if group_with_are_enough__market:
            glf.write('</div>')
    del not_enough_materials__market

    if not_enough_materials__intermediate:
        if group_with_are_enough__intermediate:
            glf.write('<div class="qind-em hidden">')
        glf.write("""
<div class="qind-interm-manuf-block">
 <h4 class="text-primary">Intermediate manufacturing</h4>
 <div class="table-responsive">
  <table class="table table-condensed table-hover qind-intermediate-manuf qind-table-materials">
  <tbody>
""")
        # поиск и вывод групп, которым принадлежат материалы, которых не хватает для завершения производства по списку
        # чертеже в этом контейнере (планетарка отдельно, композиты отдельно, запуск работ отдельно)
        __dump_not_available_materials_list_rows(
            glf,
            not_enough_materials__intermediate,
            conveyor_materials,
            mutable_not_available_row_num,
            # esi данные, загруженные с серверов CCP
            corp_bp_loc_data,
            corp_assets_tree,
            # списки контейнеров и станок из экземпляра контейнера
            exclude_loc_ids,
            blueprint_station_ids,
            react_station_ids,
            # настройки
            with_copy_to_clipboard,
            with_copy_to_clipboard,
            {'runs', 'planned', 'consumed', 'exist', 'progress'})
        glf.write("""
  </tbody>
  </table>
 </div>
</div> <!-- qind-interm-manuf-block -->
""")
        if group_with_are_enough__intermediate:
            glf.write('</div>')
    del not_enough_materials__intermediate

    glf.write("""
 </div> <!--media-body-->
</div> <!--media-->
""")
    if group_with_are_enough__initial and group_with_are_enough__market and group_with_are_enough__intermediate:
        glf.write('</div>')

    # вывод в отчёт списка тех материалов, которые необходимо перевезти с одной станции на другую

    if with_list_of_assets_movement and list_of_assets_movement__materials:
        glf.write("""
<div class="media qind-assets-move-block hidden">
 <div class="media-left">
  <span class="glyphicon glyphicon-transfer" aria-hidden="false" style="font-size: 64px;"></span>
 </div>
 <div class="media-body">
  <h4 class="media-heading">List of assets movement</h4>

<h4 class="text-primary">Missing materials at the neighboring station</h4>
<div class="table-responsive">
<table class="table table-condensed table-hover qind-missing-materials qind-table-materials">
 <tbody>
""")
        __dump_not_available_materials_list_rows(
            glf,
            list_of_assets_movement__materials,
            conveyor_materials,
            mutable_not_available_row_num,
            # esi данные, загруженные с серверов CCP
            corp_bp_loc_data,
            corp_assets_tree,
            # списки контейнеров и станок из экземпляра контейнера
            exclude_loc_ids,
            blueprint_station_ids,
            react_station_ids,
            # настройки
            False,
            with_copy_to_clipboard,
            {'planned', 'exist', 'progress'})
        glf.write("""
 </tbody>
</table>
</div> <!--table-responsive-->
 </div> <!--media-body-->
</div> <!--media-->
""")
    del list_of_assets_movement__materials

    # удаляем более ненужный список материалов
    del conveyor_materials


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
        sde_long_term_industry,
        products_for_bps,
        reaction_products_for_bps,
        global_materials_summary,
        global_materials_used,
        enable_copy_to_clipboard=False):
    # получение списков контейнеров и станок из экземпляра контейнера
    stock_all_loc_ids = set([int(ces["id"]) for ces in conveyor_entity["stock"]])
    exclude_loc_ids = set([int(cee["id"]) for cee in conveyor_entity["exclude"]])
    blueprint_containers = conveyor_entity["containers"]
    blueprint_loc_ids: typing.Set[int] = set([int(cee["id"]) for cee in blueprint_containers])
    blueprint_station_ids = [conveyor_entity["station_id"]]
    react_stock_all_loc_ids = set([int(ces["id"]) for ces in conveyor_entity["react_stock"]])
    react_station_ids = set([int(ces["loc"]["station_id"]) for ces in conveyor_entity["react_stock"]])
    products_to_exclude: typing.Set[int] = set(conveyor_entity.get('products_to_exclude', []))
    # инициализация списка материалов, которых не хватает в производстве
    stock_not_enough_materials = []
    # формирование списка ресурсов, которые используются в производстве
    stock_resources = get_stock_resources(stock_all_loc_ids, corp_ass_loc_data)
    # формирование списка ресурсов, которые используются в производстве (лежат на других станциях, но тоже учитываются)
    react_stock_resources = get_stock_resources(react_stock_all_loc_ids, corp_ass_loc_data)

    # сортировка контейнеров по названиям
    loc_ids = corp_bp_loc_data.keys()
    sorted_locs_by_names = []
    for loc in loc_ids:
        loc_id = int(loc)
        if loc_id not in blueprint_loc_ids:
            continue
        __container = next((cec for cec in blueprint_containers if cec['id'] == loc_id), None)
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
        stat__runnable_blueprints = 0
        stat__overstocked_blueprints = 0
        stat__runned_blueprints = 0
        stat__all_blueprints = 0
        glf.write(
            ' <div class="panel panel-default">\n'
            '  <div class="panel-heading" role="tab" id="headingB{id}">\n'
            '   <h4 class="panel-title">\n'
            '    <a role="button" data-toggle="collapse" data-parent="#accordion" '
            '       href="#collapseB{id}" aria-expanded="true" aria-controls="collapseB{id}">{station} <mark>{nm}</mark></a>'
            '    <span class="badge"><span id="rnblB{id}">&times;</span></span>\n'
            '   </h4>\n'
            '  </div>\n'
            '  <div id="collapseB{id}" class="panel-collapse collapse" role="tabpanel" '
            'aria-labelledby="headingB{id}">\n'
            '   <div class="panel-body">\n'.format(
                id=loc_id,
                station=conveyor_entity["station"],
                nm=loc_name,
            )
        )
        # сортировка чертежей по их названиям
        type_keys = []
        for tid in __bp2.keys():
            type_id: int = tid
            type_keys.append({"id": type_id, "name": eve_sde_tools.get_item_name_by_type_id(sde_type_ids, type_id)})
        type_keys.sort(key=lambda bp: bp["name"])
        # инициализация скрытой таблицы, которая предназначена для сортировки чертежей по различным критериям
        glf.write("""
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
                manufacturing_activities[0],
                sde_type_ids,
                sde_market_groups,
                sde_bp_materials)
            show_me_te = 'manufacturing' in manufacturing_activities or \
                         'research_material' in manufacturing_activities or \
                         'research_time' in manufacturing_activities
            # ---
            overstock_in_market: bool = False
            overstocked_invent_ids: typing.List[int] = []
            if products_to_exclude:
                if 'manufacturing' in manufacturing_activities:
                    product_ids = eve_sde_tools.get_products_by_blueprint_type_id(type_id, 1, sde_bp_materials)
                    if product_ids:
                        p2e: typing.Set[int] = set([p[0] for p in product_ids])
                        overstock_in_market = len(products_to_exclude.intersection(p2e)) > 0
                        del p2e
                        del product_ids
                elif 'invention' in manufacturing_activities:
                    product_ids = eve_sde_tools.get_products_by_blueprint_type_id(type_id, 8, sde_bp_materials)
                    if product_ids:  # м.б. None
                        p2e: typing.List[int] = [p[0] for p in product_ids]
                        for p2e_id in p2e:  # идентификаторы чертежей -> преобразуем в идентификаторы продуктов
                            p3e = eve_sde_tools.get_products_by_blueprint_type_id(p2e_id, 1, sde_bp_materials)
                            if p3e:  # м.б. None
                                p4e: typing.Set[int] = set([p[0] for p in p3e])
                                if len(products_to_exclude.intersection(p4e)) > 0:
                                    overstocked_invent_ids.append(p2e_id)
                                del p4e
                                del p3e
                        overstock_in_market = len(overstocked_invent_ids) == len(product_ids)
                        del p2e
                        del product_ids
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
                stat__count_blueprints = len(bp["itm"])
                stat__all_blueprints += stat__count_blueprints  # эт д.б. не раны, а кол-во чертежей в статистике
                stat__runned_blueprints += (stat__count_blueprints if blueprint_status is not None else 0)
                stat__overstocked_blueprints += (stat__count_blueprints if blueprint_status is None and overstock_in_market else 0)
                # ---
                market_overstock_html = ''
                if blueprint_status is None and overstock_in_market:
                    market_overstock_html = '&nbsp;<span class="label label-overstock">overstock</span>'
                # ---
                bpk_time_html = ''
                if (blueprint_status is None) and not (max_activity_time is None) and not overstock_in_market:
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
                    '{time}{overstock}\n'.format(
                        qr=quantity_or_runs,
                        fnr=' x{}'.format(fixed_number_of_runs) if not (fixed_number_of_runs is None) else "",
                        cpc='default' if is_blueprint_copy else 'info',
                        cpn='copy' if is_blueprint_copy else 'original',
                        me_te='&nbsp;<span class="label label-success">{me} {te}</span>'.format(me=material_efficiency, te=time_efficiency) if show_me_te else "",
                        status=blueprint_status if not (blueprint_status is None) else "",
                        time=bpk_time_html,
                        overstock=market_overstock_html,
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
                        materials_list_with_efficiency = get_materials_list_for_set_of_blueprints__obsolete(
                            sde_type_ids,
                            activity_blueprint_materials,
                            [{"r": quantity_or_runs}],
                            manufacturing_activities[0],
                            material_efficiency)
                        # сохраняем материалы для производства в список их суммарного кол-ва
                        calc_materials_summary__obsolete(materials_list_with_efficiency, materials_used)
                        # сохраняем материалы для производства в список их суммарного кол-ва
                        calc_materials_summary__obsolete(materials_list_with_efficiency, global_materials_used)
                        del materials_list_with_efficiency
                    # ---
                    glf.write('</br></span>')  # qind-blueprints-?
                elif overstock_in_market:
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
                        stat__runnable_blueprints += stat__count_blueprints
                        if enable_copy_to_clipboard:
                            glf.write(
                                '&nbsp;<a data-target="#" role="button" data-copy="{nm}" class="qind-copy-btn"'
                                ' data-toggle="tooltip">{gly}</a>'.
                                format(nm=blueprint_name, gly=glyphicon("copy"))
                            )
                    glf.write('</br></span>')  # qind-blueprints-?
                else:
                    # подготовка элементов управления копирования данных в clipboard
                    if enable_copy_to_clipboard:
                        glf.write(
                            '&nbsp;<a data-target="#" role="button" data-copy="{nm}" class="qind-copy-btn"'
                            ' data-toggle="tooltip">{gly}</a>'.
                            format(nm=blueprint_name, gly=glyphicon("copy"))
                        )
                    if overstocked_invent_ids:
                        for o in overstocked_invent_ids:
                            glf.write(
                                '&nbsp;<span class="label label-invent-overstocked">{}</span>'.
                                format(eve_sde_tools.get_item_name_by_type_id(sde_type_ids, o))
                            )
                    glf.write('</br></span>')  # qind-blueprints-?

                    # расчёт материалов по информации о чертеже с учётом ME
                    materials_list_with_efficiency = get_materials_list_for_set_of_blueprints__obsolete(
                        sde_type_ids,
                        activity_blueprint_materials,
                        bp["itm"],
                        manufacturing_activities[0],
                        material_efficiency,
                        is_blueprint_copy=is_blueprint_copy,
                        fixed_number_of_runs=fixed_number_of_runs)

                    # сохраняем материалы для производства в список их суммарного кол-ва
                    calc_materials_summary__obsolete(materials_list_with_efficiency, materials_summary)
                    # сохраняем материалы для производства в ГЛОБАЛЬНЫЙ список их суммарного кол-ва
                    calc_materials_summary__obsolete(materials_list_with_efficiency, global_materials_summary)

                    # проверка наличия имеющихся ресурсов для постройки по этому БП
                    # сохраняем недостающее кол-во материалов для производства по этому чертежу
                    (used_and_exist_materials, not_enough_materials) = calc_materials_availability__obsolete(
                        materials_list_with_efficiency,
                        [],
                        stock_resources,
                        {})
                    if not not_enough_materials:
                        stat__runnable_blueprints += stat__count_blueprints

                    # вывод наименования ресурсов (материалов)
                    glf.write('<div class="qind-materials-used qind-tid hiddend">\n')  # div(materials)
                    __dump_materials_list_with_efficiency(glf, materials_list_with_efficiency)
                    glf.write('</div>\n')  # div(materials)

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
                        if q_conveyor_settings.g_generate_with_show_details:
                            glf.write('&nbsp;<button type="button" class="btn btn-default btn-xs qind-materials-used'
                                      ' hidden" data-toggle="modal" data-target="#modal{nmm}">{gly} Show details</button>'.
                                      format(nmm=g_modal_industry_seq, gly=glyphicon("expand")))
                        glf.write('</div>\n')  # div(not_enough_materials 1-level)

                        # создаём заголовок модального окна, где будем показывать вывод одних материалов в другие
                        if q_conveyor_settings.g_generate_with_show_details:
                            render_html.__dump_any_into_modal_header_wo_button(
                                glf,
                                "Sequence of industry steps" if q_conveyor_settings.g_generate_with_additional_details else "Industry and purchasing",
                                g_modal_industry_seq)

                        # формируем содержимое модального диалога
                        # ...

                        ntier: int = 0
                        ntier_not_enough_materials = []
                        while not_enough_materials:
                            if q_conveyor_settings.g_generate_with_show_details and q_conveyor_settings.g_generate_with_additional_details:
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
                            (ntier_materials_list_for_next_itr__industry, ntier_materials_list_for_next_itr__reaction, ntier_materials_list_for_buy) = get_ntier_materials_list_of_not_available__obsolete(
                                not_enough_materials,
                                sde_type_ids,
                                sde_bp_materials,
                                products_for_bps,
                                reaction_products_for_bps)

                            # сохраняем материалы, которые невозможно произвести, - возможен только их закуп
                            if ntier_materials_list_for_buy:
                                calc_materials_summary__obsolete(ntier_materials_list_for_buy, ntier_not_enough_materials)

                            # отладочная детализация (по шагам)
                            if q_conveyor_settings.g_generate_with_show_details and q_conveyor_settings.g_generate_with_additional_details:
                                glf.write('<div><small>')  # div(materials)
                                glf.write('<span class="text-success">')  # зелёный - забираю со склада
                                __dump_materials_list_with_efficiency(glf, used_and_exist_materials)
                                glf.write('</span><span class="text-danger">')  # красный - закупаю
                                __dump_materials_list_with_efficiency(glf, ntier_not_enough_materials)
                                glf.write('</span></small></div>\n')  # div(materials)

                            # если материалов, которые пригодны для производства не найдено - завершаем итерации
                            if not ntier_materials_list_for_next_itr__industry and not ntier_materials_list_for_next_itr__reaction:
                                break

                            # вывод наименования ресурсов (материалов)
                            if q_conveyor_settings.g_generate_with_show_details and q_conveyor_settings.g_generate_with_additional_details:
                                glf.write('<hr><div class="text-material-industry-ntier"><small>\n')  # div(materials)
                                __dump_materials_list_with_efficiency(glf, ntier_materials_list_for_next_itr__industry)
                                __dump_materials_list_with_efficiency(glf, ntier_materials_list_for_next_itr__reaction)
                                glf.write('</small></div>\n')  # div(materials)

                            # проверка наличия имеющихся ресурсов для постройки по этому БП
                            # сохраняем недостающее кол-во материалов для производства по этому чертежу
                            (uaems, not_enough_materials) = calc_materials_availability__obsolete(
                                ntier_materials_list_for_next_itr__industry,
                                used_and_exist_materials,
                                stock_resources,
                                {},
                                check_absolutely_not_available=False)
                            # аналогично для второго списка с реакциями
                            (uaemt, not_enough_materials) = calc_materials_availability__obsolete(
                                ntier_materials_list_for_next_itr__reaction,
                                used_and_exist_materials,
                                stock_resources,
                                {},
                                check_absolutely_not_available=False)
                            if uaems:
                                calc_materials_summary__obsolete(uaems, used_and_exist_materials)
                            if uaemt:
                                calc_materials_summary__obsolete(uaemt, used_and_exist_materials)

                            del uaems
                            del uaemt
                            del ntier_materials_list_for_next_itr__industry
                            del ntier_materials_list_for_next_itr__reaction

                            # переходим к следующему уровню вложенности
                            ntier += 1

                        if q_conveyor_settings.g_generate_with_show_details:
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
            sde_long_term_industry,
            # списки контейнеров и станок из экземпляра контейнера
            blueprint_loc_ids,
            stock_all_loc_ids,
            exclude_loc_ids,
            blueprint_station_ids,
            react_stock_all_loc_ids,
            react_station_ids,
            # список материалов, которых не хватает в производстве
            stock_not_enough_materials,
            # список ресурсов, которые используются в производстве
            stock_resources,
            react_stock_resources,
            materials_summary,
            # настройки
            enable_copy_to_clipboard,
            False)

        glf.write("""
   </div> <!--panel-body-->
  </div> <!--panel-collapse-->
 </div> <!--panel-->
""")
        if stat__all_blueprints == stat__runned_blueprints:
            glf.write(
                "<script> $(document).ready(function(){{ var el=$('#rnblB{id}'); el.html('all of {all} in progress'); "
                "el.parent().css('background-color', '#337ab7'); }});</script>".
                format(id=loc_id, all=stat__all_blueprints))
        elif stat__all_blueprints == (stat__overstocked_blueprints + stat__runned_blueprints):
            glf.write(
                "<script> $(document).ready(function(){{ var el=$('#rnblB{id}'); el.html('all of {all} in overstock'); "
                "el.parent().css('background-color', '#131313'); }});</script>".
                format(id=loc_id, all=stat__all_blueprints))
        else:
            glf.write(
                "<script> $(document).ready(function(){{ var el=$('#rnblB{id}'); el.html('{bps} on {all}'); "
                "el.parent().css('background-color', '{cl}'); }});</script>".
                format(id=loc_id,
                       bps=stat__runnable_blueprints,
                       all=stat__all_blueprints,
                       cl='darkgreen' if stat__runnable_blueprints else 'maroon',
            ))

    return stock_not_enough_materials


def __dump_corp_conveyors_stock_all(
        glf,
        conveyor_data,
        priority: int,
        corp_industry_jobs_data,
        sde_type_ids,
        sde_market_groups,
        materials_for_bps,
        research_materials_for_bps):
    used_stock_places = []
    stock_resources = {}

    for corp_conveyors in conveyor_data:
        # группируются по солнечным системам, поэтому попадаем сюда для каждой системы раз за разом
        for conveyor_entity in corp_conveyors["corp_conveyour_entities_by_priority"].get(priority):
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
.label-overstock { color: # eee; background-color: #131313; }
.label-invent-overstocked { color: # eee; background-color: #131313; }
.label-not-available { color: #fff; background-color: #b7b7b7; }
.text-material-industry-ntier { color: #aaa; }
.text-material-buy-ntier { color: #a67877; }
div.qind-tid { font-size: 85%; }
tid { white-space: nowrap; }
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
        sde_long_term_industry,
        materials_for_bps,
        research_materials_for_bps,
        products_for_bps,
        reaction_products_for_bps,
        # настройки генерации отчёта
        # esi данные, загруженные с серверов CCP
        # данные, полученные в результате анализа и перекомпоновки входных списков
        conveyor_data,
        priority: int):
    glf.write("""
<style>
table.qind-blueprints-tbl > tbody > tr > td { padding: 4px; border-top: none; }

table.qind-table-materials tbody > tr > td:nth-child(2) > img /* material icon (compact view) */
{ margin-top: -2px; margin-bottom: -1px; }

table.qind-table-materials > tbody > tr > td,
table.qind-table-materials > tbody > tr > th
{ padding: 1px; font-size: smaller; }

table.qind-table-materials > tbody > tr > th
{ font-weight: bold; text-align: right; }

table tbody tr.qind-fgh td, /* first group header */
table tbody tr.qind-fgh th
{ vertical-align: bottom; }

table.qind-table-materials tbody tr th:nth-child(1)
{ width: 24px; }

td.qind-mr, /* materials required */
td.qind-mp, /* materials planned */
td.qind-mc, /* materials consumed */
td.qind-rr, /* recommended runs */
td.qind-pr, /* possible runs */
td.qind-me, /* materials exist */
td.qind-ip /* materials in progress */
{ text-align: right; }

td.qind-mr { background-color: #fffbf1; } /* materials required : light yellow */
td.qind-me { background-color: #f2fff1; } /* materials exist : light green */
td.qind-mc { background-color: #f1f7ff; } /* materials consumed : light cyan */
tr:hover td.qind-mr { background-color: #f4f0e7; }
tr:hover td.qind-me { background-color: #e8f4e6; }
tr:hover td.qind-mc { background-color: #e5ecf4; }

a.qind-sign { color: #a52a2a; } /* exclamation sign: brown color */
a.qind-sign:hover { color: #981d21; } /* exclamation sign: brown color (darken) */

div.qind-ba /* blueprints availability */
{ margin-left: auto; margin-right: 0; float: right; padding-top: 1px; white-space: nowrap; }

tr.qind-em td, /* enough materials */
tr.qind-em th
{ color: #aaa; }
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
       <li class="disabled"><a id="btnToggleImpossible" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowImpossible"></span> Show impossible to produce</a></li>
       <li class="disabled"><a id="btnToggleActive" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowActive"></span> Show active blueprints</a></li>
       <li role="separator" class="divider"></li>
       <li><a id="btnToggleUsedMaterials" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowUsedMaterials"></span> Show used materials</a></li>
       <li><a id="btnToggleNotAvailable" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowNotAvailable"></span> Show not available materials</a></li>
       <li><a id="btnToggleEndLevelManuf" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowEndLevelManuf"></span> Show end-level manufacturing</a></li>
       <li><a id="btnToggleEntryLevelPurchasing" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowManufIntermediate"></span> Show entry-level purchasing</a></li>
       <li><a id="btnToggleIntermediateManuf" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowIntermediateManuf"></span> Show intermediate manufacturing</a></li>
       <li><a id="btnToggleAssetsMovement" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowAssetsMovement"></span> Show list of assets movement</a></li>
       <li role="separator" class="divider"></li>
       <li><a id="btnToggleRecommendedRuns" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowRecommendedRuns"></span> Show recommended runs</a></li>
       <li><a id="btnTogglePlannedMaterials" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowPlannedMaterials"></span> Show planned materials</a></li>
       <li><a id="btnToggleConsumedMaterials" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowConsumedMaterials"></span> Show consumed materials</a></li>
       <li><a id="btnToggleExistInStock" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowExistInStock"></span> Show exist in stock</a></li>
       <li><a id="btnToggleInProgress" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowInProgress"></span> Show in progress</a></li>
       <li><a id="btnToggleEnoughMaterials" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowEnoughMaterials"></span> Show materials which are enough</a></li>
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
                '<div class="alert alert-{alc}" role="alert">{gly}'
                '<span class="sr-only">{ew}:</span> The number of corporate blueprints should not exceed 25,000 pieces.'
                ' Otherwise, they cannot be found in the industry control window. Also, the correctness of the'
                ' calculations of industry processes will suffer. <b>{cnm}</b> now has <b>{q:,d}</b> blueprints in'
                ' assets.'
                '</div>'.
                format(
                    gly=glyphicon("exclamation-sign"),
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
<div class="panel-group hidden" id="accordion" role="tablist" aria-multiselectable="true">
""")

        for conveyor_entity in corp_conveyors["corp_conveyour_entities_by_priority"].get(priority):
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
                sde_long_term_industry,
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

        if corp_conveyors["corp_conveyour_entities_by_priority"].get(priority):
            glf.write("<div>")  # <h3>Summary</h3>

            # TODO: нельзя в кучу сваливать все чертежи материалы, нужно их разделить на группы по станциям

            # получение списков контейнеров и станок из экземпляра контейнера
            global_stock_all_loc_ids = []
            global_exclude_loc_ids = []
            global_react_stock_all_loc_ids = []
            global_blueprint_loc_ids: typing.Set[int] = set()
            global_blueprint_station_ids = []
            global_react_station_ids = []
            for conveyor_entity in corp_conveyors["corp_conveyour_entities_by_priority"].get(priority):
                for id in [int(ces["id"]) for ces in conveyor_entity["stock"]]:
                    if not (id in global_stock_all_loc_ids):
                        global_stock_all_loc_ids.append(id)
                for id in [int(cee["id"]) for cee in conveyor_entity["exclude"]]:
                    if not (id in global_exclude_loc_ids):
                        global_exclude_loc_ids.append(id)
                for id in [int(cess["id"]) for cess in conveyor_entity["react_stock"]]:
                    if not (id in global_react_stock_all_loc_ids):
                        global_react_stock_all_loc_ids.append(id)
                for cec in conveyor_entity["containers"]:
                    if not (int(cec['id']) in global_blueprint_loc_ids):
                        global_blueprint_loc_ids.add(int(cec['id']))
                if not (conveyor_entity["station_id"] in global_blueprint_station_ids):
                    global_blueprint_station_ids.append(conveyor_entity["station_id"])
                for id in [int(cess["loc"]["station_id"]) for cess in conveyor_entity["react_stock"]]:
                    if not (id in global_react_station_ids):
                        global_react_station_ids.append(id)
            # переводим списки в множества для ускорения работы программы
            global_stock_all_loc_ids = set(global_stock_all_loc_ids)
            global_exclude_loc_ids = set(global_exclude_loc_ids)
            global_react_stock_all_loc_ids = set(global_react_stock_all_loc_ids)
            # формирование списка ресурсов, которые используются в производстве
            global_stock_resources = get_stock_resources(global_stock_all_loc_ids, corp_conveyors["corp_ass_loc_data"])
            # формирование списка ресурсов, которые используются в производстве (но лежат на других станциях)
            global_react_stock_resources = get_stock_resources(global_react_stock_all_loc_ids, corp_conveyors["corp_ass_loc_data"])

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
                sde_long_term_industry,
                # списки контейнеров и станок из экземпляра контейнера
                global_blueprint_loc_ids,
                global_stock_all_loc_ids,
                global_exclude_loc_ids,
                global_blueprint_station_ids,
                global_react_stock_all_loc_ids,
                global_react_station_ids,
                # список материалов, которых не хватает в производстве
                stock_not_enough_materials,
                # список ресурсов, которые используются в производстве
                global_stock_resources,
                global_react_stock_resources,
                global_materials_summary,
                # настройки
                True,
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
        priority,
        [],
        sde_type_ids,
        sde_market_groups,
        materials_for_bps,
        research_materials_for_bps
    )
    # закрываем footer модального диалога
    render_html.__dump_any_into_modal_footer(glf)

    glf.write("""
<div id="legend-block" class="hidden">
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
    resetOptionToDefault('Show Legend', 0);
    resetOptionToDefault('Show Not Available', 1);
    resetOptionToDefault('Show End Level Manuf', 1);
    resetOptionToDefault('Show Entry Level Purchasing', 0);
    resetOptionToDefault('Show Intermediate Manuf', 1);
    resetOptionToDefault('Show Assets Movement', 0);
    resetOptionToDefault('Show Impossible', 1);
    resetOptionToDefault('Show Active', 1);
    resetOptionToDefault('Show Used Materials', 0);
    resetOptionToDefault('Show Exist In Stock', 0);
    resetOptionToDefault('Show In Progress', 0);
    resetOptionToDefault('Show Enough Materials', 0);
    resetOptionToDefault('Show Planned Materials', 0);
    resetOptionToDefault('Show Consumed Materials', 0);
    resetOptionToDefault('Show Recommended Runs', 1);
  }
  // Conveyor Options storage (rebuild menu components)
  function rebuildOptionsMenu() {
    displayOptionInMenu('Show Legend', $('#imgShowLegend'));
    displayOptionInMenu('Show Not Available', $('#imgShowNotAvailable'));
    displayOptionInMenu('Show End Level Manuf', $('#imgShowEndLevelManuf'));
    displayOptionInMenu('Show Entry Level Purchasing', $('#imgShowManufIntermediate'));
    displayOptionInMenu('Show Intermediate Manuf', $('#imgShowIntermediateManuf'));
    displayOptionInMenu('Show Assets Movement', $('#imgShowAssetsMovement'));
    displayOptionInMenu('Show Impossible', $('#imgShowImpossible'));
    displayOptionInMenu('Show Active', $('#imgShowActive'));
    displayOptionInMenu('Show Used Materials', $('#imgShowUsedMaterials'));
    displayOptionInMenu('Show Exist In Stock', $('#imgShowExistInStock'));
    displayOptionInMenu('Show Planned Materials', $('#imgShowPlannedMaterials'));
    displayOptionInMenu('Show Consumed Materials', $('#imgShowConsumedMaterials'));
    displayOptionInMenu('Show Recommended Runs', $('#imgShowRecommendedRuns'));
    displayOptionInMenu('Show In Progress', $('#imgShowInProgress'));
    displayOptionInMenu('Show Enough Materials', $('#imgShowEnoughMaterials'));
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
        if (non_danger) {
          var non_overstock = true;
          bp_block.find('span.label-overstock').each(function() {
            non_overstock = false;
            //alert(mbody.find('h4.media-heading').html() + " " + $(this).text());
            if (show_impossible == 0)
              bp_block.addClass('hidden');
            else {
              bp_block.removeClass('hidden');
              visible = true;
            }
          })
          if (non_overstock) visible = true;
        }
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
  // Conveyor Options applier (by value)
  function applyOptionVal(show, selector) {
    $(selector).each(function() { if (show==1) $(this).removeClass('hidden'); else $(this).addClass('hidden'); })
  }
  // Conveyor Options applier (by name)
  function applyOption(option, selector) {
    show = ls.getItem(option);
    applyOptionVal(show, selector);
  }
  // Conveyor Options storage (rebuild body components)
  function rebuildBody() {
    show_not_avail = ls.getItem('Show Not Available');
    show_endlvl_manuf = ls.getItem('Show End Level Manuf');
    show_entry_purch = ls.getItem('Show Entry Level Purchasing');
    show_interm_manuf = ls.getItem('Show Intermediate Manuf');
    if ((show_not_avail==1) && ((show_endlvl_manuf==1) || (show_entry_purch==1) || (show_interm_manuf==1))) {
      applyOptionVal(1, 'div.qind-not-available-block');
      applyOptionVal(show_endlvl_manuf,'div.qind-endlvl-manuf-block');
      applyOptionVal(show_entry_purch, 'div.qind-entry-purch-block');
      applyOptionVal(show_interm_manuf, 'div.qind-interm-manuf-block');
      $('#btnToggleEndLevelManuf').parent().removeClass('disabled');
      $('#btnToggleEntryLevelPurchasing').parent().removeClass('disabled');
      $('#btnToggleIntermediateManuf').parent().removeClass('disabled');
    } else {
      applyOptionVal(0, 'div.qind-not-available-block');
      $('#btnToggleEndLevelManuf').parent().addClass('disabled');
      $('#btnToggleEntryLevelPurchasing').parent().addClass('disabled');
      $('#btnToggleIntermediateManuf').parent().addClass('disabled');
    }
    //-
    show_impossible = ls.getItem('Show Impossible');
    show_active = ls.getItem('Show Active');
    if ((show_impossible == 1) && (show_active == 1)) {
      $('div.qind-bp-block').each(function() { $(this).removeClass('hidden'); })
      $('div.media').each(function() { $(this).closest('tr').removeClass('hidden'); })
    } else {
      $('div.media').each(function() { toggleMediaVisibility($(this), show_impossible, show_active); })
    }
    //-
    applyOption('Show Assets Movement', 'div.qind-assets-move-block');
    applyOption('Show Used Materials', '.qind-materials-used');
    applyOption('Show Exist In Stock', '.qind-me');
    applyOption('Show Planned Materials', '.qind-mp');
    applyOption('Show Consumed Materials', '.qind-mc');
    applyOption('Show Recommended Runs', '.qind-rr');
    applyOption('Show Recommended Runs', '.qind-pr');
    applyOption('Show In Progress', '.qind-ip');
    applyOption('Show Enough Materials', '.qind-em');
    applyOption('Show Legend', '#legend-block');
    //-
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
  // Working with clipboard
  function copyToClipboard(elem, data_copy) {
   var $temp = $("<textarea>");
   $("body").append($temp);
   $temp.val(data_copy).select();
   try {
    success = document.execCommand("copy");
    if (success) {
     elem.trigger('copied', ['Copied!']);
    }
   } finally {
    $temp.remove();
   }
  }
  // Working with clipboard (much input variants)
  function doCopyToClipboard(elem) {
   // ожидаем либо data-tid="type_id"; либо data-copy="some value"; либо data-source="table"; либо data-source="span"
   var data_tid = elem.data('tid');
   if (!(data_tid === undefined)) {
    var nm = data_tid; // getSdeItemName(data_tid);
    if (!(nm === null)) copyToClipboard(elem, nm);
    return;
   }
   var data_copy = elem.data('copy');
   if (!(data_copy === undefined)) {
    copyToClipboard(elem, data_copy);
    return;
   }
   data_copy = '';
   var data_source = elem.data('source');
   if (data_source == 'table') {
    var tr = elem.parent().parent();
    var tbody = tr.parent();
    var rows = tbody.children('tr');
    var start_row = rows.index(tr);
    rows.each( function(idx) {
     var tr = $(this);
     if (!(start_row === undefined) && (idx > start_row)) {
      var td = tr.find('td').eq(0);
      if (!(td.attr('class') === undefined))
       start_row = undefined;
      else {
       var q1 = tr.find('td').eq(1).data('q'); q1 = (q1==undefined)?0:parseInt(q1,10);
       var q2 = tr.find('td').eq(2).data('q'); q2 = (q2==undefined)?0:parseInt(q2,10);
       var qq = q1 + q2;
       if (qq == 0) return;
       if (data_copy) data_copy += "\\n";
       data_copy += td.data('nm') + "\\t" + qq;
      }
     }
    });
   } else if (data_source == 'span') {
    var div = elem.parent().find('div.qind-tid');
    if (!(div === undefined)) {
     var tids = div.children('tid');
     if (!(tids === undefined)) {
      tids.each( function(idx) {
       var tid = $(this);
       if (data_copy) data_copy += "\\n";
       data_copy += tid.data('nm') + "\\t" + tid.data('q');
      });
     }
    }
   }
   if (data_copy) copyToClipboard(elem, data_copy);
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
    $('#btnToggleNotAvailable').on('click', function () { toggleMenuOption('Show Not Available'); });
    $('#btnToggleEndLevelManuf').on('click', function () { toggleMenuOption('Show End Level Manuf'); });
    $('#btnToggleEntryLevelPurchasing').on('click', function () { toggleMenuOption('Show Entry Level Purchasing'); });
    $('#btnToggleIntermediateManuf').on('click', function () { toggleMenuOption('Show Intermediate Manuf'); });
    $('#btnToggleAssetsMovement').on('click', function () { toggleMenuOption('Show Assets Movement'); });
    $('#btnToggleImpossible').on('click', function () { toggleMenuOption('Show Impossible'); });
    $('#btnToggleActive').on('click', function () { toggleMenuOption('Show Active'); });
    $('#btnToggleUsedMaterials').on('click', function () { toggleMenuOption('Show Used Materials'); });
    $('#btnToggleExistInStock').on('click', function () { toggleMenuOption('Show Exist In Stock'); });
    $('#btnTogglePlannedMaterials').on('click', function () { toggleMenuOption('Show Planned Materials'); });
    $('#btnToggleConsumedMaterials').on('click', function () { toggleMenuOption('Show Consumed Materials'); });
    $('#btnToggleRecommendedRuns').on('click', function () { toggleMenuOption('Show Recommended Runs'); });
    $('#btnToggleInProgress').on('click', function () { toggleMenuOption('Show In Progress'); });
    $('#btnToggleEnoughMaterials').on('click', function () { toggleMenuOption('Show Enough Materials'); });
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
    });
    $('a.qind-copy-btn').bind('click', function () {
      doCopyToClipboard($(this));
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
        sde_long_term_industry,
        materials_for_bps,
        research_materials_for_bps,
        products_for_bps,
        reaction_products_for_bps,
        # настройки генерации отчёта
        # esi данные, загруженные с серверов CCP
        # данные, полученные в результате анализа и перекомпоновки входных списков
        conveyor_data):
    priorities = []
    for priority in range(10):
        for c in conveyor_data:
            if c['corp_conveyour_entities_by_priority'].get(priority):
                priorities.append(priority)
                break
    priority_names = ['High', '1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th']

    glf_main = open('{dir}/conveyor.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    render_html.__dump_header(glf_main, "Conveyor")
    glf_main.write('<div class="well center-block" style="max-width: 400px;">\n')
    try:
        for priority in priorities:
            fname: str = 'conveyor{prior}.html'.format(prior=priority)
            title: str = '{prior} priority Conveyor'.format(prior=priority_names[priority])
            glf_main.write('<a href="{fnm}" class="btn btn-primary btn-lg btn-block" role="button">{t}</a>\n'.format(fnm=fname,t=title))
            glf = open('{dir}/{fnm}'.format(dir=ws_dir, fnm=fname), "wt+", encoding='utf8')
            try:
                render_html.__dump_header(glf, title)
                __dump_corp_conveyors(
                    glf,
                    sde_type_ids,
                    sde_bp_materials,
                    sde_market_groups,
                    sde_long_term_industry,
                    materials_for_bps,
                    research_materials_for_bps,
                    products_for_bps,
                    reaction_products_for_bps,
                    conveyor_data,
                    priority)
                render_html.__dump_footer(glf)
            finally:
                glf.close()
        glf_main.write('</div>\n')
        render_html.__dump_footer(glf_main)
    finally:
        glf_main.close()
