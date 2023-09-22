import math
import typing
import json
import render_html
import eve_sde_tools
import eve_efficiency
import console_app
from render_html import get_span_glyphicon as glyphicon


def get_pseudographics_prefix(levels, is_last):
    prfx: str = ''
    for lv in enumerate(levels):
        if lv[1]:
            prfx += '&nbsp; '
        else:
            prfx += '&#x2502; '  # |
    if is_last:
        prfx += '&#x2514;&#x2500;'  # └─
    else:
        prfx += '&#x251C;&#x2500;'  # ├─
    return prfx


def get_optimized_runs_quantity(
        # кол-во продуктов, требуемых (с учётом предыдущей эффективности)
        need_quantity: int,
        # параметры чертежа
        blueprint_activity_dict,
        # кол-во продуктов, которые будут получены за один раз чертежа
        products_per_single_run: int,
        # признак - формула ли, или реакция продукта?
        is_reaction_formula: bool,
        # настройки генерации отчёта, см. также eve_conveyor_tools.py : setup_blueprint_details
        customized_optimizations,
        # идентификатор материала (используется при проверке содержимого sde_long_term_industry)
        product_tid,
        # если в настройках генерации отчёта задана оптимизация времени производственных работ, то такая оптимизация
        # будет производиться в отношении списка "длительных работ"
        sde_long_term_industry) -> typing.Tuple[int, typing.Optional[int]]:
    # расчёт кол-ва ранов для данного чертежа (учёт настроек оптимизации производства)
    long_term_runs_number = None
    if is_reaction_formula:
        # если не None, то настроенное кол-во ранов для реакций
        customized_reaction_runs = customized_optimizations.get("reaction_runs") if customized_optimizations else None
        if customized_reaction_runs:
            long_term_runs_number = customized_reaction_runs
    else:
        # если не None, то длительность запуска производственных работ
        customized_industry_time = customized_optimizations.get("industry_time") if customized_optimizations else None
        if customized_industry_time:
            # см. также eve_conveyor_tools.py : setup_blueprint_details
            if sde_long_term_industry and product_tid in sde_long_term_industry:
                tm: int = blueprint_activity_dict['time']
                if 0 < tm < customized_industry_time:
                    long_term_runs_number = math.ceil(customized_industry_time / tm)
    # если заданы настройки оптимизации, то считаем кол-во чертежей/ранов с учётом настроек
    if long_term_runs_number:
        # реакции: планируется к запуску N чертежей по, как правило, 15 ранов (сутки)
        # производство: планируется к запуску N ранов для, как правило, оригиналов (длительностью в сутки)
        optimized_blueprints_or_runs_quantity: int = math.ceil(need_quantity / (products_per_single_run * long_term_runs_number))
        return optimized_blueprints_or_runs_quantity * long_term_runs_number, long_term_runs_number
    # если настройки оптимизации не заданы, то считаем кол-во чертежей/ранов с учётом лишь только потребностей
    else:
        optimized_blueprints_or_runs_quantity: int = math.ceil(need_quantity / products_per_single_run)
        return optimized_blueprints_or_runs_quantity, None


def recalc_industry_rest(
        quantity_with_efficiency: int,
        available: int,
        in_progress: int,
        not_enough: int,
        rest: int,
        tid: int, assets_cache, industry_jobs_cache) -> int:
    # расчёт материалов, которые предстоит построить (с учётом уже имеющихся запасов)
    if (available + in_progress + rest) <= quantity_with_efficiency:
        # считаем, сколько материалов останется в неизрасходованном виде,
        # как результат текущего запуска производства
        rest = \
            quantity_with_efficiency - \
            not_enough - \
            assets_cache[tid] - \
            industry_jobs_cache[tid] - \
            rest
        # минусуем остатки на складе и в производстве
        assets_cache[tid] = 0
        industry_jobs_cache[tid] = 0
    else:
        __left = quantity_with_efficiency - not_enough
        # минусуем остатки на складе
        if available >= __left:
            assets_cache[tid] -= __left
            __left = 0
        else:
            __left -= available
            assets_cache[tid] = 0
        # минусуем остатки в производстве
        if __left > 0 and in_progress:
            if in_progress >= __left:
                industry_jobs_cache[tid] -= __left
                __left = 0
            else:
                __left -= industry_jobs_cache[tid]
                industry_jobs_cache[tid] = 0
        # считаем, сколько материалов останется в неизрасходованном виде,
        # как результат текущего запуска производства
        if __left > 0 and rest > 0:
            if rest >= __left:
                rest -= __left
                __left = 0
            else:
                __left -= rest
                rest = 0
    return rest


def __dump_blueprint_materials(
        glf,
        row0_prefix,
        row0_levels,
        # сведения о чертеже, его материалах, эффективности и т.п.
        bpmm0_rate: float,  # пропорция от продукта, требуемая (с учётом предыдущей вложенности)
        bpmm0_quantity: int,  # кол-во продуктов, требуемых (с учётом предыдущей эффективности)
        bpmm0_materials,  # материалы, для постройки продукта
        bpmm0_material_efficiency,  # me чертежа продукта (валидно только для manufacturing)
        bpmm0_is_reaction_formula,  # признак - формула ли, или реакция продукта?
        # ...
        # сводная статистика (формируется в процессе работы метода)
        materials_summary,
        blueprints_cache: typing.Dict[int, typing.Any],
        assets_cache: typing.Dict[int, int],
        industry_jobs_cache: typing.Dict[int, int],
        # настройки генерации отчёта
        report_options,
        # параметры/настройки генерации отчёта
        blueprint_containter_ids,
        stock_containter_ids,
        stock_containter_flag_ids,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        sde_long_term_industry,
        # esi данные, загруженные с серверов CCP
        corp_assets_data,
        corp_industry_jobs_data,
        corp_blueprints_data):
    # список контейнеров, в которых будет выполняться поиск ассетов (чертежей)
    allowed_container_ids = blueprint_containter_ids + blueprint_containter_ids
    for m1 in enumerate(bpmm0_materials, start=1):
        row1_num: int = int(m1[0])
        bpmm1_tid = int(m1[1]["typeID"])
        bpmm1_tnm = eve_sde_tools.get_item_name_by_type_id(sde_type_ids, bpmm1_tid)
        bpmm1_quantity = int(m1[1]["quantity"])
        # заранее готовим summary-dict справочник с информацией по плану использования текущего продукта
        __summary_dict = next((ms for ms in materials_summary if ms['id'] == bpmm1_tid), None)
        bpmm1_rest: int = __summary_dict.get('rest', 0) if __summary_dict else 0
        # поиск чертежа для этого типа продукта (которого может и не быть, например если возможен только закуп)
        bpmm1_blueprint_type_id, bpmm1_blueprint_data = \
            eve_sde_tools.get_blueprint_type_id_by_product_id(bpmm1_tid, sde_bp_materials, "manufacturing")
        bpmm1_is_reaction_formula = False
        if bpmm1_blueprint_type_id is None:
            bpmm1_blueprint_type_id, bpmm1_blueprint_data = \
                eve_sde_tools.get_blueprint_type_id_by_product_id(bpmm1_tid, sde_bp_materials, "reaction")
            bpmm1_is_reaction_formula = bpmm1_blueprint_type_id is not None
        if bpmm1_blueprint_type_id is None:
            bpmm1_blueprint_activity_dict = None
            bpmm1_products_per_single_run = None
            bpmm1_blueprint_materials = None
        else:
            # см. также eve_conveyor_tools.py : setup_blueprint_details
            activity: str = 'reaction' if bpmm1_is_reaction_formula else 'manufacturing'
            bpmm1_blueprint_activity_dict = bpmm1_blueprint_data["activities"][activity]
            bpmm1_blueprint_materials = bpmm1_blueprint_activity_dict["materials"]
            bpmm1_blueprint_products = bpmm1_blueprint_activity_dict["products"]
            if len(bpmm1_blueprint_products) == 1:
                bpmm1_products_per_single_run = bpmm1_blueprint_products[0]['quantity']
            else:  # здесь непонятно что делать, т.к. явно надо выбрать правильный продукт? с иным кол-вом на выходе?
                bpmm1_products_per_single_run = bpmm1_blueprint_products[0]['quantity']
        # помечаем использованными материалы и работы, чтобы на следующих элементах использовалось ОСТАВШЕЕСЯ кол-во
        # подсчёт кол-ва имеющихся в наличии материалов
        bpmm1_available = assets_cache.get(bpmm1_tid)
        if bpmm1_available is None:
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
            assets_cache[bpmm1_tid] = bpmm1_available
        # получаем список работ, которые ведутся с материалами
        bpmm1_in_progress = industry_jobs_cache.get(bpmm1_tid)
        if bpmm1_in_progress is None:
            bpmm1_in_progress = 0
            for j in corp_industry_jobs_data:
                __type_id = j["product_type_id"]
                if bpmm1_tid != __type_id:
                    continue
                __blueprint_location_id = j["blueprint_location_id"]
                __output_location_id = j["output_location_id"]
                __found = {__blueprint_location_id, __output_location_id} & set(allowed_container_ids)
                if __found:
                    __runs = int(j["runs"])
                    bpmm1_in_progress += __runs
            industry_jobs_cache[bpmm1_tid] = bpmm1_in_progress
        if bpmm1_tid == 34:
            bpmm1_tid = bpmm1_tid
        # подсчёт кол-ва материалов, учитываемых как "остатки" от предыдущих циклов производства (неиспользованные
        # остатки от ещё незапущенных, но спланированных работ)
        if bpmm1_blueprint_type_id is None:
            # материалы, которые не производятся, а закупаются, считаются as is
            bpmm1_quantity_with_efficiency: int = eve_efficiency.get_industry_material_efficiency(
                'reaction' if bpmm0_is_reaction_formula else 'manufacturing',
                bpmm0_quantity,  # кол-во run-ов (кол-во продуктов, которые требует предыдущий уровень)
                bpmm1_quantity,  # кол-во из исходного чертежа (до учёта всех бонусов)
                0 if bpmm0_is_reaction_formula else bpmm0_material_efficiency)  # me-параметр чертежа предыдущего уровня
            bpmm1_blueprints_or_runs_quantity: int = bpmm0_quantity * bpmm1_quantity
            # bpmm1_optimized_long_term_runs_number: int = 1
        else:
            # расчёт кол-ва материала с учётом эффективности производства (с учётом заданного кол-ва ранов,
            # например с использованием BPO)
            if bpmm0_is_reaction_formula:
                # расчёт кол-ва ранов для данного чертежа (учёт эффективности производства)
                bpmm1_blueprints_or_runs_quantity, bpmm1_long_term_runs_number__dummy = get_optimized_runs_quantity(
                    # кол-во продуктов, требуемых (с учётом предыдущей эффективности)
                    bpmm0_quantity * bpmm1_quantity,
                    # параметры чертежа
                    bpmm1_blueprint_activity_dict,
                    # кол-во продуктов, которые будут получены за один ран чертежа
                    bpmm1_products_per_single_run,
                    # признак - формула ли, или реакция продукта?
                    bpmm1_is_reaction_formula,
                    # настройки генерации отчёта (настройки оптимизации умышленно отключаются для получения min кол-ва
                    # необходимых компонентов)
                    None,
                    # идентификатор материала (используется при проверке содержимого sde_long_term_industry)
                    None,
                    # список "длительных работ производственных работ" (не имеет смысла с пустыми настройками)
                    None)
                bpmm1_quantity_with_efficiency: int = eve_efficiency.get_industry_material_efficiency(
                    'reaction',
                    bpmm1_blueprints_or_runs_quantity,  # кол-во run-ов (кол-во продуктов, которые требует предыдущий уровень)
                    bpmm1_products_per_single_run,  # кол-во из исходного чертежа (до учёта всех бонусов)
                    0)  # me-параметр чертежа предыдущего уровня (у реакций всегда me=0)
            else:
                bpmm1_quantity_with_efficiency: int = eve_efficiency.get_industry_material_efficiency(
                    'manufacturing',
                    bpmm0_quantity,  # кол-во run-ов (кол-во продуктов, которые требует предыдущий уровень)
                    bpmm1_quantity,  # кол-во из исходного чертежа (до учёта всех бонусов)
                    bpmm0_material_efficiency)  # me-параметр чертежа предыдущего уровня
        # расчёт кол-ва материалов, которых не хватает
        bpmm1_not_enough = bpmm1_quantity_with_efficiency - bpmm1_available - bpmm1_in_progress - bpmm1_rest
        if bpmm1_not_enough < 0:
            bpmm1_not_enough = 0
        # если какого-то материала не хватает, то считаем его производство по другой формуле (считываем настройки
        # оптимизации производства) в результате производства будут сформированы излишки, производство которых
        # будет учтено на следующих вложенностях при наличии потребностей
        if bpmm1_not_enough == 0 or bpmm1_blueprint_type_id is None:
            # расчёт материалов, которые предстоит построить (с учётом уже имеющихся запасов)
            # материалы, которые не производятся, а закупаются, считаются as is
            bpmm1_rest: int = recalc_industry_rest(
                bpmm1_quantity_with_efficiency,
                bpmm1_available,
                bpmm1_in_progress,
                bpmm1_not_enough,
                bpmm1_rest,
                bpmm1_tid, assets_cache, industry_jobs_cache
            )
            bpmm1_optimized_blueprints_or_runs_quantity = None
            bpmm1_quantity_with_efficiency_optimized = None
            bpmm1_optimized_quantity_multiplicator: None
            bpmm1_optimized_long_term_runs_number: int = 1
            bpmm1_industry_planned: bool = False
        else:
            # расчёт кол-ва ранов для данного чертежа (учёт настроек оптимизации производства)
            bpmm1_optimized_blueprints_or_runs_quantity, bpmm1_optimized_long_term_runs_number = get_optimized_runs_quantity(
                # кол-во продуктов, требуемых (с учётом предыдущей эффективности)
                bpmm1_not_enough,
                # параметры чертежа
                bpmm1_blueprint_activity_dict,
                # кол-во продуктов, которые будут получены за один ран чертежа
                bpmm1_products_per_single_run,
                # признак - формула ли, или реакция продукта?
                bpmm1_is_reaction_formula,
                # настройки генерации отчёта
                report_options.get("optimization", None),
                # идентификатор материала (используется при проверке содержимого sde_long_term_industry)
                bpmm1_tid,
                # список "длительных работ производственных работ"
                sde_long_term_industry)
            # расчёт кол-ва материала с учётом эффективности производства (с учётом заданного кол-ва ранов,
            # например с использованием BPO), возможная ситуация:
            #  - Для производства 'Neurolink Protection Cell' надо 5x 'Genetic Safeguard Filter' а также (без учёта ME)
            #    20x 'Meta-Operant Neurolink Enhancer' (фильтры производятся по 20 шт/ран и энхансеры тоже производятся
            #    по 20 шт/ран), при этом с учётом ME=10 предыдущего чертежа фактически потребуется 5x фильтров и
            #    18х энхансеров. При отключенной оптимизации (например расчёт капитала) ни фильтров, ни энхансеров
            #    больше чем необходимо (соответственно 5 и 18 шт) не потребуется.
            #  - Для производства XXX надо 1x YYY, а с учётом оптимизации "посуточных" ранов, алгоритм может
            #    порекомендовать произвести не 1x YYY, а 10x YYY. Тогда потребуется большее количество YYY.
            """if bpmm0_is_reaction_formula:
                bpmm1_quantity_with_efficiency_optimized = eve_efficiency.get_industry_material_efficiency(
                    'reaction',
                    bpmm1_optimized_blueprints_or_runs_quantity,  # кол-во run-ов (кол-во продуктов, которые требует предыдущий уровень)
                    bpmm1_optimized_long_term_runs_number,  # кол-во из исходного чертежа (до учёта всех бонусов)
                    0)  # me-параметр чертежа предыдущего уровня
            else:
                if bpmm1_tid == 57482 or bpmm1_tid == 57458:
                    bpmm1_tid = bpmm1_tid
                bpmm1_quantity_with_efficiency_optimized = eve_efficiency.get_industry_material_efficiency(
                    'manufacturing',
                    bpmm1_optimized_blueprints_or_runs_quantity,  # кол-во run-ов (кол-во продуктов, которые требует предыдущий уровень)
                    bpmm1_products_per_single_run, # bpmm1_optimized_long_term_runs_number,  # кол-во из исходного чертежа (до учёта всех бонусов)
                    bpmm0_material_efficiency)  # me-параметр чертежа предыдущего уровня"""
            bpmm1_quantity_with_efficiency_optimized = bpmm1_optimized_blueprints_or_runs_quantity * bpmm1_products_per_single_run
            bpmm1_optimized_quantity_multiplicator: int = bpmm1_products_per_single_run
            if bpmm1_optimized_long_term_runs_number is not None:
                bpmm1_optimized_quantity_multiplicator *= bpmm1_optimized_long_term_runs_number
            # расчёт материалов, которые предстоит построить (с учётом уже имеющихся запасов)
            bpmm1_rest: int = recalc_industry_rest(
                bpmm1_quantity_with_efficiency_optimized,
                bpmm1_available,
                bpmm1_in_progress,
                bpmm1_not_enough,
                bpmm1_rest,
                bpmm1_tid, assets_cache, industry_jobs_cache
            )
            bpmm1_industry_planned: bool = True
        # сохраняем материалы для производства в список их суммарного кол-ва
        if __summary_dict is None:
            __summary_dict = {"id": bpmm1_tid,
                              "bid": bpmm1_blueprint_type_id,
                              "nm": bpmm1_tnm,
                              "q": 0,
                              "a": bpmm1_available,
                              "j": bpmm1_in_progress,
                              "portion": 1 if bpmm1_products_per_single_run is None else bpmm1_products_per_single_run,
                              "rate": 0.0,
                              "rest": 0}
            materials_summary.append(__summary_dict)
        # меняем запланированное кол-во материалов (использованное)
        # bpmm1_summary_rest_quantity: int = __summary_dict["rest"] - bpmm1_rest
        if bpmm1_industry_planned:
            bpmm1_summary_quantity: int = bpmm1_quantity_with_efficiency_optimized
        else:
            bpmm1_summary_quantity: int = bpmm1_not_enough
        __summary_dict["q"] += bpmm1_summary_quantity
        __summary_dict["rest"] = bpmm1_rest
        # считаем, сколько не хватает (в пропорциях) материала текущего уровня вложенности
        if bpmm1_industry_planned:
            bpmm1_rate = bpmm0_rate * (bpmm1_quantity_with_efficiency / bpmm1_optimized_quantity_multiplicator)
        else:
            bpmm1_rate = bpmm0_rate * (bpmm1_quantity_with_efficiency / bpmm0_quantity)  # TODO: тут какая-то фигня
        __summary_dict["rate"] += bpmm1_rate

        # генерация символов для рисования псевдографикой
        nm_prfx: str = get_pseudographics_prefix(row0_levels, row1_num == len(bpmm0_materials))
        # debug: print(row0_prefix + str(row1_num), bpmm1_tnm, bpmm1_not_enough)
        # debug: print(row0_prefix + str(row1_num), bpmm1_tnm, bpmm1_not_enough, "= n{} - a{} - j{}".format(bpmm1_quantity_with_efficiency, bpmm1_available, bpmm1_in_progress))
        # генерация символов для вывода в summary (с раскраской grayed-текстом)
        __txt_summary: str = ''
        if __summary_dict["q"] == bpmm1_summary_quantity:  # первое слагаемое не изменилось
            __txt_summary = '<z0>0+</z0>{}'.format(bpmm1_summary_quantity)
        elif bpmm1_summary_quantity == 0:
            __txt_summary = '{}<z0>+0</z0>'.format(__summary_dict["q"])
        else:
            __txt_summary = '{}+{}'.format(__summary_dict["q"]-bpmm1_summary_quantity, bpmm1_summary_quantity)
        __txt_summary = '{sne1:,d}=<sup>{sne0X}</sup>'.format(sne1=__summary_dict["q"], sne0X=__txt_summary)
        # вывод наименования ресурса
        glf.write(
            '<tr{tr_class}>\n'
            ' <th scope="row"><span class="text-muted">{num_prfx}</span>{num}</th>\n'
            ' <td><img class="icn24" src="{src}"> <tt><span class="text-muted">{nm_prfx}</span></tt> {nm}{qm}{bpr}{bpq}</td>\n'
            ' <td>{qa}{qip}</td>\n'
            ' <td>{qs}</td>\n'
            ' <td>{qe}</td>\n'
            ' <td>{qne:,d}</td>\n'
            ' <td>{qo}</td>\n'
            ' <td>{qr}</td>\n'
            ' <td>{srat1:.8f}%=<sup>{srat0}{ratW:.8f}*({ratX}{ratY})</sup></td>\n'
            ' <td>{sne10X}</td>\n'
            '</tr>'.
            format(
                tr_class=' class="active"' if not row0_prefix else '',
                num_prfx=row0_prefix, num=row1_num,
                nm_prfx=nm_prfx,
                nm=bpmm1_tnm,
                qm=" <span class='qneed_materials'>{q}<sup> надо</sup></span>".format(q=bpmm1_quantity),
                bpq='' if bpmm1_products_per_single_run is None or bpmm1_products_per_single_run == 1 else " <span class='qsingle_run'>{}<sup>шт</sup></span>".format(bpmm1_products_per_single_run),
                bpr='' if bpmm1_optimized_blueprints_or_runs_quantity is None else " <span class='qoptimized_runs'>{}<sup>run</sup></span>".format(bpmm1_optimized_blueprints_or_runs_quantity),
                src=render_html.__get_img_src(bpmm1_tid, 32),
                qs='<z0>0</z0>' if bpmm0_quantity == 0 else '{:,d}'.format(bpmm1_quantity * bpmm0_quantity),  # не д.б. 0? (но это не точно)
                qe='<z0>0</z0>' if bpmm1_quantity_with_efficiency == 0 else '{:,d}'.format(bpmm1_quantity_with_efficiency),  # не д.б. 0? (но это не точно)
                qo='' if bpmm1_quantity_with_efficiency_optimized is None else '{:,d}'.format(bpmm1_quantity_with_efficiency_optimized),
                qa='<z0>0</z0>' if bpmm1_available == 0 else '{:,d}'.format(bpmm1_available),
                qip='' if bpmm1_in_progress == 0 else '<mark>+ {}</mark>'.format(bpmm1_in_progress),
                qne=bpmm1_not_enough,
                qr='' if bpmm1_products_per_single_run is None else '<z0>0</z0>' if __summary_dict["rest"] == 0 else '{:,d}'.format(__summary_dict["rest"]),
                srat1=__summary_dict["rate"],
                srat0='<z0>0.00+</z0>' if __summary_dict["rate"] == bpmm1_rate else '{0:.8f}+'.format(__summary_dict["rate"]-bpmm1_rate),
                ratW=bpmm0_rate,
                ratX=bpmm1_quantity_with_efficiency,
                ratY='/{}'.format(bpmm1_optimized_quantity_multiplicator) if bpmm1_industry_planned else '',
                #
                sne10X=__txt_summary
            )
        )

        # если все материалы собраны, то переходим к следующим компонентам
        if bpmm1_not_enough == 0 or bpmm1_optimized_blueprints_or_runs_quantity is None:
            continue
        # определяем, можно ли строить этот продукт, или возможен только его закуп?
        if bpmm1_blueprint_type_id is None:
            continue
        # debug: print(bpmm1_blueprint_type_id, bpmm1_tnm, bpmm1_blueprint_materials['activities']['manufacturing']['products'])
        # поиск чертежей, имеющихся в наличии у корпорации
        bpmm1_blueprints = blueprints_cache.get(bpmm1_blueprint_type_id)
        if not bpmm1_blueprints:
            bpmm1_blueprints = []
            for b in corp_blueprints_data:
                __type_id = int(b["type_id"])
                if bpmm1_blueprint_type_id != __type_id:
                    continue
                __location_id = int(b["location_id"])
                if not (__location_id in blueprint_containter_ids):
                    continue
                __quantity = int(b["quantity"])
                # A range of numbers with a minimum of -2 and no maximum value where -1 is an original and -2 is a
                # copy. It can be a positive integer if it is a stack of blueprint originals fresh from the market
                # (e.g. no activities performed on them yet).
                __is_blueprint_copy = __quantity == -2
                __bp_dict = {
                    "cp": __is_blueprint_copy,
                    "me": b["material_efficiency"],
                    "te": b["time_efficiency"],
                    "qr": b["runs"] if __is_blueprint_copy else (1 if __quantity == -1 else __quantity)
                }
                bpmm1_blueprints.append(__bp_dict)
            bpmm1_blueprints.sort(key=lambda bp: (100000*int(bp["cp"]) + 10000*bp["me"] + bp["qr"]), reverse=True)
            blueprints_cache[bpmm1_blueprint_type_id] = bpmm1_blueprints

        # спускаемся на уровень ниже и выводим необходимое количество материалов для производства текущего
        # проверяем, что для текущего материала существуют чертежи для производства

        # вывод списка материалов для постройки по чертежу (следующий уровень)
        bpmm2_bp_runs = bpmm1_optimized_blueprints_or_runs_quantity

        # добавление в список материалов чертежей с известным кол-вом run-ов
        __summary_dict = next((ms for ms in materials_summary if ms['id'] == bpmm1_blueprint_type_id), None)
        if __summary_dict is None:
            materials_summary.append({"id": bpmm1_blueprint_type_id,
                                      "q": bpmm2_bp_runs,
                                      "nm": eve_sde_tools.get_item_name_by_type_id(sde_type_ids, bpmm1_blueprint_type_id),
                                      "b": bpmm1_blueprints,
                                      "ajp": bpmm1_in_progress + bpmm1_available})
        else:
            __summary_dict["q"] += bpmm2_bp_runs
        del __summary_dict

        row2_levels = row0_levels[:]
        row2_levels.append(row1_num == len(bpmm0_materials))
        __dump_blueprint_materials(
            glf,
            "{prfx}{num1}.".format(prfx=row0_prefix, num1=row1_num),
            row2_levels,
            # сведения о чертеже, его материалах, эффективности и т.п.
            bpmm1_rate,
            bpmm2_bp_runs,
            bpmm1_blueprint_materials,
            report_options["missing_blueprints"]["material_efficiency"],
            bpmm1_is_reaction_formula,
            # ...
            # сводная статистика (формируется в процессе работы метода)
            materials_summary,
            blueprints_cache,
            assets_cache,
            industry_jobs_cache,
            # настройки генерации отчёта
            report_options,
            # параметры/настройки генерации отчёта
            blueprint_containter_ids,
            stock_containter_ids,
            stock_containter_flag_ids,
            # sde данные, загруженные из .converted_xxx.json файлов
            sde_type_ids,
            sde_bp_materials,
            sde_market_groups,
            sde_long_term_industry,
            # esi данные, загруженные с серверов CCP
            corp_assets_data,
            corp_industry_jobs_data,
            corp_blueprints_data)
        del row2_levels


def __dump_report(
        glf,
        jdata,
        # настройки генерации отчёта
        report_options,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        sde_icon_ids,
        sde_long_term_industry,
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
              'EveUniversity {nm} wiki: <a class="url" href="https://wiki.eveuniversity.org/{nm}">https://wiki.eveuniversity.org/{nm}</a><br/>\n'
              'EveMarketer {nm} tradings: <a class="url" href="https://evemarketer.com/types/{pid}">https://evemarketer.com/types/{pid}</a><br/>\n'
              'EveMarketer {nm} Blueprint tradings: <a class="url" href="https://evemarketer.com/types/{bid}">https://evemarketer.com/types/{bid}</a><br/>\n'
              'Adam4EVE {nm} manufacturing calculator: <a class="url" href="https://www.adam4eve.eu/manu_calc.php?typeID={bid}">https://www.adam4eve.eu/manu_calc.php?typeID={bid}</a><br/>\n'
              'Adam4EVE {nm} price history: <a class="url" href="https://www.adam4eve.eu/commodity.php?typeID={pid}">https://www.adam4eve.eu/commodity.php?typeID={pid}</a><br/>\n'
              'Adam4EVE {nm} Blueprint price history: <a class="url" href="https://www.adam4eve.eu/commodity.php?typeID={bid}">https://www.adam4eve.eu/commodity.php?typeID={bid}</a>\n'.
              format(nm=product_name,
                     src=render_html.__get_img_src(__type_id, 64),
                     pid=__type_id,
                     bid=__capital_blueprint_type_id))

    # создаём запись несуществующего пока чертежа
    __capital_blueprint_dict = report_options['base_blueprint']
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
    glf.write('  <img class="media-object icn64" src="{src}" alt="Список материалов для постройки">\n'.
              format(src=render_html.__get_icon_src(1436, sde_icon_ids)))  # Manufacture & Research
    glf.write("""
  </div>
  <div class="media-body">
   <h4 class="media-heading">Список материалов для постройки</h4>
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
    glf.write('<img class="media-object icn64" src="{src}" alt="Компоненты {nm}">\n'.
              format(src=render_html.__get_icon_src(2863, sde_icon_ids), nm=product_name))  # Standard Capital Ship Components
    glf.write("""
  </div>
  <div class="media-body">
""")
    glf.write('<h4 class="media-heading">Компоненты {nm}</h4>\n'
              '<ul>'
              '<li><var>ReactionEfficiency</var> = <var>Required</var> * (100 - 2.2) / 100'
              '<li><var>IndustryEfficiency</var> = <var>Required</var> * (100 - <var>material_efficiency</var> '
              '- 1 - 4.2) / 100,<br>где <var>material_efficiency={mb_me}</var> для неизвестных и недоступных чертежей'.
              format(nm=product_name,  # Standard Capital Ship Components
                     mb_me=report_options["missing_blueprints"]["material_efficiency"]
    ))
    customized_optimizations = report_options.get("optimization", None)
    if customized_optimizations:
        # если не None, то настроенное кол-во ранов для реакций
        customized_reaction_runs = customized_optimizations.get("reaction_runs") if customized_optimizations else None
        if customized_reaction_runs:
            glf.write('<li>Настройки оптимизации варки реакций: '
                      'по {} прогонов'.format(customized_reaction_runs))
        # если не None, то длительность запуска производственных работ
        customized_industry_time = customized_optimizations.get("industry_time") if customized_optimizations else None
        if customized_industry_time:
            glf.write('<li>Настройки оптимизации длительности производства: '
                      'прогоны длительностью {:.1f} часов'.format(customized_industry_time/(5*60*60)))
    glf.write('</ul>\n')

    glf.write("""
<div class="panel-group" id="capital-accordion" role="tablist" aria-multiselectable="true">
 <div class="panel panel-default">
  <div class="panel-heading" role="tab" id="headingComponents">
   <h4 class="panel-title">
    <a role="button" data-toggle="collapse" data-parent="#capital-accordion" href="#collapseComponents" aria-expanded="true" aria-controls="collapseComponents">Полный список задействованных компонентов</a>
   </h4>
  </div>
  <div id="collapseComponents" class="panel-collapse collapse in" role="tabpanel" aria-labelledby="headingComponents">
   <div class="panel-body">
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
#tblFLCI thead tr th { padding: 1px; border-bottom: 1px solid #1d3231; }
#tblFLCI tbody tr td { padding-left: 1px; padding-right: 1px; border-top: none; vertical-align: middle; }
#tblFLCI tbody tr td:nth-child(2) { white-space: nowrap; }
#tblFLCI thead tr th:nth-child(3),
#tblFLCI thead tr th:nth-child(4),
#tblFLCI thead tr th:nth-child(5),
#tblFLCI thead tr th:nth-child(6),
#tblFLCI thead tr th:nth-child(7),
#tblFLCI thead tr th:nth-child(8),
#tblFLCI tbody tr td:nth-child(3),
#tblFLCI tbody tr td:nth-child(4),
#tblFLCI tbody tr td:nth-child(5),
#tblFLCI tbody tr td:nth-child(6),
#tblFLCI tbody tr td:nth-child(7),
#tblFLCI tbody tr td:nth-child(8) { text-align: right; }
#tblFLCI thead tr th:nth-child(9),
#tblFLCI thead tr th:nth-child(10),
#tblFLCI tbody tr td:nth-child(9),
#tblFLCI tbody tr td:nth-child(10) { padding-left: 3px; text-align: left; }
#tblFLCI tbody tr td:nth-child(3),
#tblFLCI tbody tr td:nth-child(4),
#tblFLCI tbody tr td:nth-child(5),
#tblFLCI tbody tr td:nth-child(6),
#tblFLCI tbody tr td:nth-child(7),
#tblFLCI tbody tr td:nth-child(8),
#tblFLCI tbody tr td:nth-child(9),
#tblFLCI tbody tr td:nth-child(10) { border-left: 1px solid #1d3231; }
span.qneed_materials {
 color: #727272;
 font-size: 75%;
 font-weight: 700;
}
span.qsingle_run {
 color: #8bbe68;
 font-size: 75%;
 font-weight: 700;
}
span.qoptimized_runs {
 color: #ff4546;
 font-size: 75%;
}
z0 {
 color: #727272;
}
</style>
<ul>
 <li>A - доступное кол-во материалов, в наличии в стоке (<mark>+ производится в настоящее время</mark>)
 <li>S - стандартное кол-во материалов без учёта ME (ME=0)
 <li>ME - кол-во материалов с учётом ME чертежей
 <li>N - требуемое количество материалов (не хватает)
 <li>O - кол-во материалов, рассчитанное с учётом правил оптимизации (раны длительностью в сутки и т.п.)
 <li>R - кол-во материалов, которое останется невостребованным после завершения работы
</ul>
 <table class="table table-borderless table-condensed" style="font-size:small" id=tblFLCI>
<thead>
 <tr>
  <th style="width:50px;">#</th>
  <th>Материалы</th>
  <th>A<!--В наличии<br/>+ запущено--></th>
  <th>S<!--Без ME--></th>
  <th>ME<!--Учёт ME--></th>
  <th>N<!--Требуется (не хватает)--></th>
  <th>O<!--Оптимизация--></th>
  <th>R<!--Остаток<br>(произв.)--></th>
  <th>Пропорция<sup> (часть от общего кол-ва)</sup></th>
  <th>Итог</th>
 </tr>
</thead>
<tbody>
""")

    materials_summary = []

    # debug = __capital_blueprint_materials["activities"]["manufacturing"]["materials"][:]
    # debug.append({"typeID": 11186, "quantity": 15})
    # debug.append({"typeID": 41332, "quantity": 10})
    blueprints_cache: typing.Dict[int, typing.Any] = {}
    assets_cache: typing.Dict[int, int] = {}
    industry_jobs_cache: typing.Dict[int, int] = {}
    __dump_blueprint_materials(
        glf,
        '',
        [],
        # сведения о чертеже, его материалах, эффективности и т.п.
        1.0,
        __capital_quantity_or_runs,
        __capital_blueprint_materials["activities"]["manufacturing"]["materials"],
        __capital_material_efficiency,
        __is_reaction_formula,
        # ...
        # сводная статистика (формируется в процессе работы метода)
        materials_summary,
        blueprints_cache,
        assets_cache,
        industry_jobs_cache,
        # настройки генерации отчёта
        report_options,
        # параметры/настройки генерации отчёта
        blueprint_containter_ids,
        stock_containter_ids,
        stock_containter_flag_ids,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        sde_long_term_industry,
        # esi данные, загруженные с серверов CCP
        corp_assets_data,
        corp_industry_jobs_data,
        corp_blueprints_data)

    glf.write("""
</tbody>
</table>
   </div> <!-- panel-body -->
  </div> <!-- "panel-collapse -->
 </div> <!-- panel -->
</div> <!-- panel-group -->
  </div> <!--media-body-->
 </div> <!--media-->
<hr>
 <div class="media">
  <div class="media-left">
""")
    glf.write('  <img class="media-object icn64" src="{src}" alt="Список сырья для производства">\n'.
              format(src=render_html.__get_icon_src(1201, sde_icon_ids)))  # Materials
    glf.write("""
  </div>
  <div class="media-body">
   <h4 class="media-heading">Список сырья для производства</h4>
""")
    str_stock_cont_names = ""
    for st in report_options["stock"]:
        if str_stock_cont_names:
            str_stock_cont_names = str_stock_cont_names + ', '
        str_stock_cont_names += '<mark>' + st.get('name', st.get('flag')) + '</mark>'
    if not str_stock_cont_names:
        str_stock_cont_names = '<mark></mark>'
    glf.write('<p>The number of Minerals and Components is considered based on the presence of aseets in container(s) {}.</p>\n'.
              format(str_stock_cont_names))  # Materials
    str_bp_cont_names = ""
    for bp in report_options["blueprints"]:
        if str_bp_cont_names:
            str_bp_cont_names = str_bp_cont_names + ', '
        str_bp_cont_names += '<mark>' + bp.get('name', bp.get('flag')) + '</mark>'
    if not str_bp_cont_names:
        str_bp_cont_names = '<mark></mark>'
    glf.write('<p>The number of Blueprints is considered based on the presence of blueprints in container(s) {}.</p>\n'.
              format(str_bp_cont_names))  # Blueprints
    glf.write("""
<div class="table-responsive">
<style>
.progress-tblSRM {
 height: 8px;
 margin-bottom: 0px;
 background-color: #232e31;
 border-radius: 0px;
}
#tblSRM thead tr th { padding: 0px; padding-left: 4px; padding-right: 4px; border-bottom: 1px solid #1d3231; }
#tblSRM tbody tr td { padding: 0px; padding-left: 4px; padding-right: 4px; border-top: none; }
#tblSRM tbody tr td:nth-child(3),
#tblSRM tbody tr td:nth-child(4),
#tblSRM tbody tr td:nth-child(5),
#tblSRM tbody tr td:nth-child(6),
#tblSRM tbody tr td:nth-child(7),
#tblSRM tbody tr td:nth-child(8) { text-align: right; vertical-align: middle; }
#tblSRM tbody tr td:nth-child(3),
#tblSRM tbody tr td:nth-child(4),
#tblSRM tbody tr td:nth-child(5),
#tblSRM tbody tr td:nth-child(6),
#tblSRM tbody tr td:nth-child(7),
#tblSRM tbody tr td:nth-child(8) { border-left: 1px solid #1d3231; }
#tblSRM tbody tr td:nth-child(5) { font-size: smaller; }
</style>
 <table class="table table-borderless table-condensed" style="font-size:small" id="tblSRM">
<thead>
 <tr>
  <th style="width:24px;">#</th>
  <th>Материалы</th>
  <th>В наличии<br/>+запущено</th>
  <th>Требуется<br>(эффективность / пропорция)</th>
  <th>Прогресс</th>
  <th style="text-align:right;">Цена за<br/>шт., ISK</th>
  <th style="text-align:right;">Суммарно,&nbsp;ISK</th>
  <th style="text-align:right;">Объём,&nbsp;m&sup3;</th>
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
        __ratio = __summary_dict.get("rate", -1.0)
        __assets = __summary_dict["a"] if "a" in __summary_dict else 0
        __blueprints = __summary_dict["b"] if "b" in __summary_dict else []
        __in_progress = __summary_dict["j"] if "j" in __summary_dict else 0
        __products_available_and_in_progress = __summary_dict.get("ajp", 0)
        __type_id = __summary_dict["id"]
        __blueprint_type_id = __summary_dict.get("bid", None)
        __item_name = __summary_dict["nm"]
        # ---
        __quantity -= __products_available_and_in_progress
        if __quantity < 0:
            __quantity = 0
        # ---
        __market_group = eve_sde_tools.get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, __type_id)
        __material_dict = {
            "id": __type_id,
            "bid": __blueprint_type_id,
            "q": __quantity,
            "nm": __item_name,
            "a": __assets,
            "b": __blueprints,
            "j": __in_progress,
            "rate": __ratio}
        if str(__market_group) in material_groups:
            material_groups[str(__market_group)].append(__material_dict)
        else:
            material_groups.update({str(__market_group): [__material_dict]})

    # добавление чертежа на корабль в список требуемых материалов
    # Vanquisher Blueprint не имеет marketGroupID, что является ошибкой ССР, и поэтому приходится изгаляться...
    __capital_blueprint = {
        "id": __capital_blueprint_type_id,
        "bid": None,
        "q": __capital_quantity_or_runs,
        "nm": eve_sde_tools.get_item_name_by_type_id(sde_type_ids, __capital_blueprint_type_id),
        "a": 0,
        "b": [__capital_blueprint_dict] if not (__capital_blueprint_dict["id"] is None) else [],
        "j": 0,  # не показываем, что строим титан
        "rate": 1.0}
    materials_summary.append(__capital_blueprint)
    if material_groups.get("2"):
        material_groups["2"].append(__capital_blueprint)  # Blueprints & Reactions
    else:
        material_groups.update({"2": [__capital_blueprint]})

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
                '&nbsp;<a data-target="#" role="button" class="qind-copy-btn" data-toggle="tooltip">' \
                '<button type="button" class="btn btn-default btn-xs" style="margin: 2px;">{gly}' \
                ' Export to multibuy</button></a>'.format(gly=glyphicon("copy"))
            glf.write('<tr>\n'
                      ' <td class="active" colspan="8"><strong>{nm}</strong><!--{id}-->{clbrd}</td>\n'
                      '</tr>'.
                      format(
                        nm=__group_name,
                        id=__group_id,
                        clbrd=__copy2clpbrd
                      ))
        # вывод материалов в группе
        __summary_cost: float = 0
        __summary_volume: float = 0
        __summary_cost_ratio = None
        __summary_volume_ratio = None
        for __material_dict in __mg1:
            # получение данных по материалу
            bpmm3_tid = __material_dict["id"]
            bpmm3_bptid = __material_dict.get("bid")
            bpmm3_tnm = __material_dict["nm"]
            bpmm3_q = __material_dict["q"]  # quantity (required, not available yet)
            bpmm3_r = __material_dict.get("rate", -2.0)  # ratio (пропорция от требуемого кол-ва с учётом вложенных уровней)
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
            elif bpmm3_q == 0:
                bpmm3_progress = 100
            else:
                bpmm3_progress = float(100 * bpmm3_available / bpmm3_q)
            # подготовка кнопки копирования названия в буфер обмена
            __copy2clpbrd = '' if not enable_copy_to_clipboard else \
                '&nbsp;<a data-target="#" role="button" data-copy="{nm}" class="qind-copy-btn"' \
                ' data-toggle="tooltip">{gly}</a>'. \
                format(nm=bpmm3_tnm, gly=glyphicon("copy"))
            # подготовка progress-бара
            __prgrs_bar = '<span>{fprcnt:.1f}%</span><br>' \
                          '<div class="progress progress-tblSRM"><div class="progress-bar activity1" ' \
                          'role="progressbar" aria-valuenow="{prcnt}" aria-valuemin="0" aria-valuemax="100" ' \
                          'style="width: {fprcnt:.1f}%;"></div></div>'. \
                          format(prcnt=int(bpmm3_progress), fprcnt=bpmm3_progress)
            # вывод наименования ресурса
            glf.write(
                '<tr>\n'
                ' <th scope="row">{num}</th>\n'
                ' <td data-copy="{nm}"><img class="icn24" src="{src}"> {nm}{clbrd}{me_te}</td>\n'
                ' <td>{qa}{qip}</td>\n'
                ' <td quantity="{qneed}">{qrn:,d}{qrr}</td>\n'
                ' <td>{prgrs}</td>\n'
                ' <td>{price}</td>'
                ' <td>{costn}{costr}</td>'
                ' <td>{volume}</td>'
                '</tr>'.
                format(
                    num=row3_num,
                    nm=bpmm3_tnm,
                    clbrd=__copy2clpbrd,
                    me_te=me_te_tags,
                    src=render_html.__get_img_src(bpmm3_tid, 32),
                    qrn=bpmm3_q,
                    qrr='' if bpmm3_bptid is not None else ' <span class="text-muted">({:.2f})</span>'.format(bpmm3_r),
                    qneed=bpmm3_q-bpmm3_available-bpmm3_j if bpmm3_q > (bpmm3_available+bpmm3_j) else 0,
                    qa='{:,d}'.format(bpmm3_available) if bpmm3_available >= 0 else "&infin; <small>runs</small>",
                    qip="" if bpmm3_j == 0 else '<mark>+ {}</mark>'.format(bpmm3_j),
                    prgrs=__prgrs_bar,
                    price='{:,.1f}'.format(bpmm3_price) if bpmm3_price is not None else '',
                    costn='{:,.1f}'.format(bpmm3_price * bpmm3_q) if bpmm3_price is not None else '',
                    costr='' if bpmm3_bptid is not None or bpmm3_price is None else ' <span class="text-muted">({:.2f})</span>'.format(bpmm3_price*bpmm3_r+0.004999),
                    volume='{:,.1f}'.format(__type_dict["volume"] * bpmm3_q) if not __is_blueprints_group else ""
                ))
            # подсчёт summary кол-ва по всем материалам группы
            if not (bpmm3_price is None):
                __summary_cost += bpmm3_price * bpmm3_q
                if bpmm3_bptid is None:
                    val: float = bpmm3_price * bpmm3_r
                    if __summary_cost_ratio is None:
                        __summary_cost_ratio = val
                    else:
                        __summary_cost_ratio += val
            __summary_volume += __type_dict["volume"] * bpmm3_q
            if bpmm3_bptid is None:
                val: float = __type_dict["volume"] * bpmm3_r
                if __summary_volume_ratio is None:
                    __summary_volume_ratio = val
                else:
                    __summary_volume_ratio += val
            # подсчёт кол-ва ресурсов, которые выдаются из этого метода в сериализованном виде
            if jdata is not None and bpmm3_bptid is not None:
                jdata['materials'].append({
                    'id': bpmm3_tid,
                    'q': bpmm3_q,
                    'r': bpmm3_r,
                })
        # вывод summary-строки для текущей группы материалов
        if not (__group_id == "None") and not (__group_id == "2"):
            glf.write('<tr style="font-weight:bold">'
                      ' <th></th>'
                      ' <td colspan="4">Summary&nbsp;(<small>{nm}</small>)</td>'
                      ' <td colspan="2" align="right">{costn:,.1f}&nbsp;ISK{costr}</td>'
                      ' <td align="right">{volumen:,.1f}&nbsp;m&sup3;{volumer}</td>'
                      '</tr>\n'.
                      format(nm=__group_name,
                             costn=__summary_cost,
                             costr='' if __summary_cost_ratio is None else ' <span class="text-muted">({:,.2f})</span>'.format(__summary_cost_ratio),
                             volumen=__summary_volume,
                             volumer='' if __summary_volume_ratio is None else ' <span class="text-muted">({:,.1f})</span>'.format(__summary_volume_ratio)))

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


def calc_industry_cost(
        # результаты расчёта: какие ресурсы (и сколько) надо потратить, чтобы получить желаемый продукт
        jdata,
        # путь, где будет сохранён отчёт
        ws_dir,
        # настройки генерации отчёта
        report_options,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        sde_icon_ids,
        sde_long_term_industry,
        # esi данные, загруженные с серверов CCP
        corp_assets_data,
        corp_industry_jobs_data,
        corp_blueprints_data,
        eve_market_prices_data):
    product_name = report_options["product"]
    file_name: str = report_options.get('assignment', product_name)
    file_name_c2s: str = render_html.__camel_to_snake(file_name, True)
    ghf = open('{dir}/{fnm}.html'.format(dir=ws_dir, fnm=file_name_c2s), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(ghf, product_name, use_dark_mode=True)
        __dump_report(
            ghf,
            jdata,
            report_options,
            sde_type_ids,
            sde_bp_materials,
            sde_market_groups,
            sde_icon_ids,
            sde_long_term_industry,
            corp_assets_data,
            corp_industry_jobs_data,
            corp_blueprints_data,
            eve_market_prices_data)
        render_html.__dump_footer(ghf)
        # сохранение результатов расчёта во внешний .json файл
        if jdata:
            gjf = open('{dir}/{fnm}.json'.format(dir=ws_dir, fnm=file_name_c2s), "wt+", encoding='utf8')
            try:
                sjdata = json.dumps(jdata, indent=1, sort_keys=False)
                gjf.write(sjdata)
            finally:
                gjf.close()
    finally:
        ghf.close()


def main():
    # работа с параметрами командной строки, получение настроек запуска программы, как то: работа в offline-режиме,
    # имя пилота ранее зарегистрированного и для которого имеется аутентификационный токен, регистрация нового и т.д.
    argv_prms = console_app.get_argv_prms()

    sde_type_ids = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "typeIDs")
    sde_market_groups = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "marketGroups")
    sde_bp_materials = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "blueprints")
    sde_icon_ids = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "iconIDs")
    sde_long_term_industry = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "longTermIndustry")

    # результаты расчёта:
    #  * id: int  - идентификатор материала
    #  * q: int   - количество экземпляров (шт.) материала необходимое для запуска работ
    #  * r: float - пропорция материала (шт.) которое будет потрачено для изготовления, без учёта его остатков
    jdata = {
        "materials": [],
    }

    calc_industry_cost(
        # результаты расчёта: какие ресурсы (и сколько) надо потратить, чтобы получить желаемый продукт
        jdata,
        # путь, где будет сохранён отчёт
        '{}/industry_cost'.format(argv_prms["workspace_cache_files_dir"]),
        # настройки генерации отчёта
        {
            "base_blueprint": {"cp": True, "qr": 10, "me": 2, "te": 4, "st": None, "id": None},
            "product": "Rocket Launcher II",
            # "base_blueprint": {"cp": False, "qr": 1, "me": 10, "te": 16, "st": None, "id": None},
            # "product": "Neurolink Protection Cell",
            "container_templates": [],
            "blueprints": [],
            "stock": [],
            "missing_blueprints": {"material_efficiency": 10},
            # "optimization": {"reaction_runs": 15, "industry_time": 5*60*60*24},  # см. также eve_conveyor_tools.py : setup_blueprint_details
            # "optimization": {"industry_time": 5*60*4},  # 4 минуты
        },
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        sde_bp_materials,
        sde_market_groups,
        sde_icon_ids,
        sde_long_term_industry,
        # esi данные, загруженные с серверов CCP
        [],
        [],
        [],
        []
    )


if __name__ == "__main__":
    main()
