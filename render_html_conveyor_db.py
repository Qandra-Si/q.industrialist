import math
import json
import typing
import datetime
import itertools

import render_html
from render_html import get_span_glyphicon as glyphicon
from render_html import get_span_glyphicon_ex as glyphicon_ex

import postgresql_interface as db
import eve_router_tools as tools
# from __init__ import __version__


def dump_materials_to_js(glf, dictionary: tools.ConveyorDictionary) -> None:
    type_id_keys = dictionary.materials
    sorted_type_id_keys = sorted(type_id_keys, key=lambda x: int(x))
    glf.write(f"""<script>
const g_sde_max_type_id={sorted_type_id_keys[-1] if len(sorted_type_id_keys) else 0};
const g_sde_type_len={len(sorted_type_id_keys)};
const g_sde_type_ids=[""")
    for (idx, type_id) in enumerate(sorted_type_id_keys):
        # экранируем " (двойные кавычки), т.к. они встречаются реже, чем ' (одинарные кавычки)
        item_type: typing.Optional[db.QSwaggerTypeId] = dictionary.qid.get_type_id(type_id)
        type_name = item_type.name if item_type is not None else str(type_id)
        glf.write('{end}[{id},"{nm}"]'.format(
            id=type_id,
            nm=type_name.replace('"', '\\\"'),
            end=',' if idx else "\n"))
    glf.write("""
];
let iterativeSdeItem = function (arr, x) {
 let start = 0, end = g_sde_type_len - 1;
 while (start <= end) {
  let mid = Math.floor((start + end) / 2);
  let ti = arr[mid][0];
  if (ti == x)
   return arr[mid];
  else if (ti < x)
   start = mid + 1;
  else
   end = mid - 1;
 }
 return null;
}
function getSdeItemName(t) {
 if ((t < 0) || (t > g_sde_max_type_id)) return null;
 let x = iterativeSdeItem(g_sde_type_ids, t, 0, g_sde_type_ids.length - 1);
 if (x === null) return null;
 return x[1];
}
</script>
""")


def declension_of_runs(runs: int) -> str:
    modulo: int = runs % 10
    if modulo in (0, 5, 6, 7, 8, 9):
        return 'прогонов'
    elif modulo == 1:
        return 'прогон'
    elif modulo in (2, 3, 4):
        return 'прогона'


def declension_of_blueprints(blueprints: int) -> str:
    if blueprints == 1:
        return 'чертёж'
    else:
        return 'чертежи'


def declension_of_lost_blueprints(blueprints: int) -> str:
    if blueprints == 1:
        return 'потерянный чертёж'
    else:
        return 'потерянные чертежи'


def declension_of_lost_assets(assets: int) -> str:
    if assets == 1:
        return 'потерянный предмет'
    else:
        return 'потерянные предметы'


def format_num_of_num(possible: typing.Optional[int], total: int, mute_possible: bool = True) -> str:
    if possible is None or possible < 0 or possible >= total:
        return str(total)
    elif mute_possible:
        return f'<mute>{possible} из</mute> {total}'
    else:
        return f'{possible} из{total}'


def sec_to_timestr(time: int, trim_to_10min: bool = True) -> str:
    if trim_to_10min:
        time = (time // 600) * 600
    # округляем до 10мин, т.к. всё равно у всех навыки разные, а от обилия циферок рябит в глазах
    res: str = f'{time // 3600:d}:{(time // 60) % 60:02d}'
    return res


def format_time_to_time(min_num: int, max_num: int, mute_min: bool = True) -> str:
    if not min_num:
        return 'нет данных'
    # округляем до 10мин, т.к. всё равно у всех навыки разные, а от обилия циферок рябит в глазах
    res: str = sec_to_timestr(min_num)
    if min_num == max_num:
        return res
    elif mute_min:
        return f'<mute>от {res} до</mute> ' + sec_to_timestr(max_num)
    else:
        return f'от {res} до ' + sec_to_timestr(max_num)


def format_json_data(data_name: str, data_val: typing.Any) -> str:
    val: str = json.dumps(data_val, separators=(',', ':')).replace("'", '"')
    return f"data-{data_name}='{val}'"


def get_industry_icons(activities: typing.List[db.QSwaggerActivityCode], delimiter: str = ' ') -> str:
    activity_distinct: typing.Set[int] = set([3 if _ == 4 else _ for _ in [_.to_int() for _ in activities]])
    activity_icons: str = delimiter.join([render_html.__get_industry_icon_img_ex(_, 'icn_industry') for _ in activity_distinct])
    return activity_icons


def format_product_tier2_info_btn(ia: tools.ConveyorInventAnalysis) -> str:
    info = {'p': ia.product_tier2.product_id,
            'l': ia.product_tier2_limit,
            'a': ia.product_tier2_num_in_assets,
            'j': ia.product_tier2_num_in_jobs,
            's': ia.product_tier2_num_in_sell,
            'b': ia.product_tier2_num_in_blueprints,
            'r': ia.product_tier2_num_in_blueprint_runs}
    product_info_btn: str = \
        '<a data-target="#" role="button" class="qind-info-btn"' \
        f'{format_json_data("product", info)}>{glyphicon("info-sign")}</a>'
    return product_info_btn


def format_product_tier1_info_btn(ma: tools.ConveyorManufacturingAnalysis) -> str:
    info = {'p': ma.product_tier1.product_id,
            'l': ma.product_tier1_limit,
            'a': ma.product_tier1_num_in_assets,
            'j': ma.product_tier1_num_in_jobs,
            's': ma.product_tier1_num_in_sell,
            'b': ma.product_tier1_num_in_blueprints,
            'r': ma.product_tier1_num_in_blueprint_runs}
    product_info_btn: str = \
        '<a data-target="#" role="button" class="qind-info-btn"' \
        f'{format_json_data("product", info)}>{glyphicon("info-sign")}</a>'
    return product_info_btn


class NavMenuDefaults:
    def __init__(self):
        self.run_possible: bool = True
        self.run_impossible: bool = False
        self.overstock_products: bool = False
        self.lost_items: bool = False
        self.phantom_blueprints: bool = False
        self.job_active: bool = False
        self.job_completed: bool = False
        # ---
        self.used_materials: bool = False
        self.not_available: bool = False
        self.industry_product: bool = False

    def get(self, label: str) -> bool:
        if label == 'row-multiple' or \
           label == 'run-possible' or label == 'row-possible' or \
           label == 'run-optional' or label == 'row-optional':
            return self.run_possible
        elif label == 'run-impossible' or label == 'row-impossible':
            return self.run_impossible
        elif label == 'overstock-product' or label == 'row-overstock':
            return self.overstock_products
        elif label == 'lost-blueprints' or label == 'lost-assets' or label == 'lost-jobs':
            return self.lost_items
        elif label == 'phantom-blueprints':
            return self.phantom_blueprints
        elif label == 'job-active':
            return self.job_active
        # ---
        elif label == 'used-materials':
            return self.used_materials
        elif label == 'not-available':
            return self.not_available
        elif label == 'industry-product' or label == 'invent-product':
            return self.industry_product
        else:
            raise Exception("Unsupported label to get nav menu defaults")

    def css(self, label: str, prefix: bool = True) -> str:
        if label == 'row-multiple' or \
           label == 'run-possible' or label == 'row-possible' or \
           label == 'run-optional' or label == 'row-optional':
            opt: bool = self.run_possible
        elif label == 'run-impossible' or label == 'row-impossible':
            opt: bool = self.run_impossible
        elif label == 'overstock-product' or label == 'row-overstock':
            opt: bool = self.overstock_products
        elif label == 'lost-blueprints' or label == 'lost-assets' or label == 'lost-jobs':
            opt: bool = self.lost_items
        elif label == 'phantom-blueprints':
            opt: bool = self.phantom_blueprints
        elif label == 'job-active':
            opt: bool = self.job_active
        elif label == 'job-completed':
            opt: bool = self.job_completed
        # ---
        elif label == 'used-materials':
            opt: bool = self.used_materials
        elif label == 'not-available':
            opt: bool = self.not_available
        elif label == 'industry-product' or label == 'invent-product':
            opt: bool = self.industry_product
        else:
            raise Exception("Unsupported label to get nav menu defaults")
        return '' if opt else (' hidden' if prefix else 'hidden')


g_nav_menu_defaults: NavMenuDefaults = NavMenuDefaults()


def dump_nav_menu(glf) -> None:
    global g_nav_menu_defaults
    menu_settings: typing.List[typing.Optional[typing.Tuple[bool, str, str, bool]]] = [
        (g_nav_menu_defaults.run_possible,       'run-possible',       'Доступные для запуска работы', True),
        (g_nav_menu_defaults.run_impossible,     'run-impossible',     'Недоступные для запуска работы', True),
        (g_nav_menu_defaults.overstock_products, 'overstock-product',  'Избыточные чертежи (перепроизводство)', True),
        (g_nav_menu_defaults.lost_items,         'lost-items',         'Потерянные предметы (не на своём месте)', True),
        (g_nav_menu_defaults.phantom_blueprints, 'phantom-blueprints', 'Фантомные чертежи (рассогласованные)', True),
        (g_nav_menu_defaults.job_active,         'job-active',         'Ведущиеся проекты', True),
        (g_nav_menu_defaults.job_completed,      'job-completed',      'Завершённые проекты', True),
        None,
        (g_nav_menu_defaults.used_materials,     'used-materials',     'Используемые материалы', True),
        (g_nav_menu_defaults.not_available,      'not-available',      'Недоступные материалы', True),
        (g_nav_menu_defaults.industry_product,   'industry-product',   'Продукты производства', True),
        None,
        (True, 'end-level-manuf', "Производство последнего уровня", False),  # btnToggleEndLevelManuf
        (False, 'entry-level-purchasing', "Список для закупки", False),  # btnToggleEntryLevelPurchasing
        (True, 'intermediate-manuf', "Материалы промежуточного производства", False),  # btnToggleIntermediateManuf
        (False, 'enough-materials', "Материалы, которых достаточно", False),  # btnToggleEnoughMaterials
        (False, 'assets-movement', "Список перемещений материалов", False),  # btnToggleAssetsMovement
    ]
    menu_table: typing.List[typing.Optional[typing.Tuple[bool, str, str, bool]]] = [
        (True, 'recommended-runs', "Рекомендуемое кол-во запусков", False),  # btnToggleRecommendedRuns
        (False, 'planned-materials', "Кол-во запланированных материалов", False),  # btnTogglePlannedMaterials
        (False, 'consumed-materials', "Рассчитанное кол-во материалов", False),  # btnToggleConsumedMaterials
        (False, 'exist-in-stock', "Кол-во материалов в стоке", False),  # btnToggleExistInStock
        (False, 'in-progress', "Кол-во материалов, находящихся в производстве", False),  # btnToggleInProgress
    ]
    menu_sort: typing.List[typing.Tuple[bool, str, str, str, str]] = [
        (True,  'name',     'Название',     'sort-by-alphabet',   'sort-by-alphabet-alt'),
        (False, 'duration', 'Длительность', 'sort-by-attributes', 'sort-by-attributes-alt'),
        (False, 'priority', 'Приоритет',    'sort-by-order',      'sort-by-order-alt'),
    ]
    glf.write("""
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
     <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Настройки <span class="caret"></span></a>
      <ul class="dropdown-menu">
""")
    for m in menu_settings:
        if m is None:
            glf.write('<li role="separator" class="divider"></li>\n')
        else:
            disabled: str = '' if m[3] else ' class="disabled"'
            glf.write(f"<li{disabled}><a data-target='#' role='button' class='qind-btn-settings' qind-group='{m[1]}'>{glyphicon('star')} {m[2]}</a></li>\n")
    glf.write("""
       <li role="separator" class="divider"></li>
       <li><a data-target="#" role="button" id="qind-btn-reset">Сбросить настройки</a></li>
      </ul>
    </li>
    <li class="dropdown">
     <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Таблица <span class="caret"></span></a>
      <ul class="dropdown-menu">
""")
    for m in menu_table:
        if m is None:
            glf.write('<li role="separator" class="divider"></li>\n')
        else:
            disabled: str = '' if m[3] else ' class="disabled"'
            glf.write(f"<li{disabled}><a data-target='#' role='button' class='qind-btn-settings' qind-group='{m[1]}'>{glyphicon('star')} {m[2]}</a></li>\n")
    glf.write("""
      </ul>
    </li>
    <li><a data-target="#modalRouter" role="button" data-toggle="modal">Станции</a></li>
    <li><a data-target="#modalConveyor" role="button" data-toggle="modal">Конвейер</a></li>
    <li><a data-target="#modalDemand" role="button" data-toggle="modal">Спрос</a></li>
    <li><a data-target="#modalLifetime" role="button" data-toggle="modal">Время</a></li>
   </ul>
   <form class="navbar-form navbar-right">
    <label>Сортировка:&nbsp;</label>
    <div class="btn-group" role="group" aria-label="Sort">
""")
    for m in menu_sort:
        glf.write(f"<button type='button' class='btn btn-default qind-btn-sort' qind-group='{m[1]}'>"
                  f"{m[2]}{glyphicon_ex(m[3],['asc','hidden'])}{glyphicon_ex(m[4], ['desc','hidden'])}"
                  "</button>")
    glf.write("""
    </div>
   </form>
  </div>
 </div>
</nav>
<script>
""")
    glf.write('var g_menu_options_default=[')
    g_menu_options_default_len = 0
    for (idx, m) in enumerate(menu_settings + menu_table):
        if m is None: continue
        glf.write('{f}[{d},"{nm}"]'.format(
            f=',' if g_menu_options_default_len > 0 else '',
            d='1' if m[0] else '0',
            nm=m[1]
        ))
        g_menu_options_default_len += 1
    glf.write(f'];\nvar g_menu_options_default_len={g_menu_options_default_len};\n')
    # ---
    g_menu_sort_default = next((m[1] for m in menu_sort if m[0]), 'name')
    glf.write(f"var g_menu_sort_default='{g_menu_sort_default}';\n")
    glf.write("var g_menu_sort_order_default=1; // 0-desc, 1-asc\n")
    glf.write("</script>\n")


g_tbl_summary_row_num: int = 0
g_tbl_conveyor_row_num: int = 0
g_tbl_router_row_num: int = 0


def get_tbl_summary_row_num(increment: bool = True) -> int:
    global g_tbl_summary_row_num
    if increment:
        g_tbl_summary_row_num += 1
    return g_tbl_summary_row_num


def get_tbl_conveyor_row_num() -> int:
    global g_tbl_conveyor_row_num
    g_tbl_conveyor_row_num += 1
    return g_tbl_conveyor_row_num


def get_tbl_router_row_num() -> int:
    global g_tbl_router_row_num
    g_tbl_router_row_num += 1
    return g_tbl_router_row_num


def dump_nav_menu_router_dialog(
        glf,
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        global_dictionary: tools.ConveyorDictionary,
        # настройки генерации отчёта
        router_settings: typing.List[tools.RouterSettings],
        conveyor_settings: typing.List[tools.ConveyorSettings],
        # справочник задействованных материалов
        router_materials: typing.Dict[tools.RouterSettings, tools.ConveyorRouterInputMaterials]) -> None:
    # создаём заголовок модального окна, где будем показывать список имеющихся материалов в контейнере "..stock ALL"
    render_html.__dump_any_into_modal_header_wo_button(
        glf,
        "Распределение производства по станциям",
        unique_id="Router",
        modal_size="modal-lg")
    # формируем содержимое модального диалога
    row_num: int = 0
    for (idx, s) in enumerate(router_settings):
        # определяем станцию, корпорацию и стоки конвейера соответствующего роутеру
        router_details: typing.Tuple[db.QSwaggerStation, db.QSwaggerCorporation, typing.Set[int], typing.Set[int]] = tools.get_router_details(
            qid,
            s,
            conveyor_settings
        )
        station: db.QSwaggerStation = router_details[0]
        corporation: db.QSwaggerCorporation = router_details[1]
        containers_stocks: typing.Set[int] = router_details[2]
        containers_output: typing.Set[int] = router_details[3]
        # ---
        if idx > 0:
            glf.write('<hr>')
        glf.write(f"<h3 station_id='{station.station_id}'>{station.station_name} "
                  f"<small>({station.station_type_name}, {s.desc})</small>"
                  "</h3>")
        stock_names: str = ''
        if not corporation or not containers_stocks:
            glf.write("<p style='color:#ffa600'>Внимание! Не найдены сток контейнеры, "
                      "следует проверить настройки конвейера.</p>")
        else:
            z0 = sorted([corporation.assets.get(x).name for x in containers_stocks], key=lambda x: x)
            stock_names = "</mark><li><mark>".join(z0)
        output_names: str = ''
        if not corporation or not containers_output:
            glf.write("<p style='color:#ffa600'>Внимание! Не найдены контейнеры готовой продукции, "
                      "следует проверить настройки конвейера.</p>")
        else:
            z0 = sorted([corporation.assets.get(x).name for x in containers_output], key=lambda x: x)
            output_names = "</mark><li><mark>".join(z0)
        glf.write(f"""
<script>
g_tbl_stock_img_src="{render_html.__get_img_src("{tid}", 32)}";
</script>

<div class="row">
 <div class="col-md-6"><small>Сток контейнеры:<ul><li><mark>{stock_names}</mark></ul></small></div>
 <div class="col-md-6"><small>Контейнеры готовой продукции:<ul><li><mark>{output_names}</mark></ul></small></div>
</div> <!-- row -->

<div class="row">
<div class="col-md-6">
<table class="table table-condensed table-hover tbl-stock">
<thead>
 <tr>
  <th>#</th>
  <th>Сырьё</th>
  <th><small>В стоке</small></th>
  <th><small>Не хватает</small></th>
 </tr>
</thead>
<tbody>""")
        materials: typing.Set[int] = set()
        products: typing.Set[int] = set()
        if s.output:
            # если список output сконфигурирован, то имеет место быть станция из настроек router-а
            materials = set(router_materials[s].valid_materials.keys())
            products = set(s.output)
        else:
            # если список output пустой, то имеет место быть default-ная производственная база,
            # выводим весь сток материалов на этой базе
            for cs in conveyor_settings:
                for type_id in cs.assets.stock.keys():
                    if next((_ for _ in cs.assets.stock[type_id] if _.station_id == station.station_id), None):
                        materials.add(type_id)
            for cs in conveyor_settings:
                for type_id in cs.assets.output.keys():
                    if next((_ for _ in cs.assets.output[type_id] if _.station_id == station.station_id), None):
                        products.add(type_id)
        # сохраняем в глобальный справочник материалов и продуктов используемых конвейером
        global_dictionary.load_type_ids(materials)
        global_dictionary.load_type_ids(products)
        # сортируем по market-группам (внимание! market-group м.б. неизвестной, например для копий чертежей)
        sorted_materials = [(qid.get_type_id(x).market_group_id, x) for x in materials]
        sorted_materials.sort(key=lambda x: x[0] if x[0] else 0)
        # выводим в отчёт
        for __sort_key, material_type_id in sorted_materials:
            row_num += 1
            material: db.QSwaggerTypeId = qid.get_type_id(material_type_id)
            quantity: int = 0
            not_enough: int = 0  # = resource_dict["ne"]
            # считаем кол-во материалов в стоке
            for cs in conveyor_settings:
                aa = cs.assets.get_with_unique_items(
                    material_type_id,
                    [tools.ConveyorPlace.STOCK],
                    station.station_id)
                if not aa: continue
                quantity += sum([_.quantity for _ in aa])
            # --- --- ---
            # <qmaterial tid="16663" icn="24" cl="qind-sign"></qmaterial>
            # эквивалентно:
            #   <qimg24 data-tid="16663"></qimg24> <qnm data-tid="16663"></qnm>&nbsp;<a data-target="#" role="button"
            #   data-tid="16663" class="qind-copy-btn qind-sign" data-toggle="tooltip"><span class="glyphicon
            #   glyphicon-copy" aria-hidden="true"></span></a>
            # эквивалентно:
            #   <img class="icn24" src="http://imageserver.eveonline.com/Type/16663_32.png"> Caesarium Cadmide&nbsp;<a
            #   data-target="#" role="button" data-tid="16663" class="qind-copy-btn qind-sign" data-toggle="tooltip"
            #   data-original-title="" title=""><span class="glyphicon glyphicon-copy" aria-hidden="true"></span></a>
            glf.write(
                '<tr>'
                '<td scope="row">{num}</td>'
                '<td><qmaterial tid="{tid}" cl="qind-sign"></qmaterial></td>'
                '<td>{q}</td>'
                '<td>{ne}</td>'
                '</tr>\n'.
                format(num=row_num,
                       tid=material.type_id,
                       q="" if quantity == 0 else '{:,d}'.format(quantity),
                       ne="" if not_enough == 0 else '{:,d}'.format(not_enough))
            )

        glf.write("""
</tbody>
</table>
</div> <!-- col -->
<div class="col-md-6">
<table class="table table-condensed table-hover tbl-stock">
<thead>
 <tr>
  <th>#</th>
  <th>Продукция</th>
  <th><small>Готово</small></th>
  <th><small>Не хватает</small></th>
  <th><small>Произво-<br>-дится</small></th>
 </tr>
</thead>
<tbody>
""")
        # сортируем по market-группам (внимание! market-group м.б. неизвестной, например для копий чертежей)
        sorted_products = [(qid.get_type_id(x).market_group_id, x) for x in products]
        sorted_products.sort(key=lambda x: x[0] if x[0] else 0)
        # выводим в отчёт
        for __sort_key, product_type_id in sorted_products:
            row_num += 1
            product: db.QSwaggerTypeId = qid.get_type_id(product_type_id)
            if not product: continue
            quantity: int = 0
            in_progress: int = 0
            not_enough: int = 0  # = resource_dict["ne"]
            # считаем кол-во продуктов в стоке/выходе
            for cs in conveyor_settings:
                aa = cs.assets.get_with_unique_items(
                    product_type_id,
                    [tools.ConveyorPlace.STOCK, tools.ConveyorPlace.OUTPUT, tools.ConveyorPlace.SALE_STOCK],
                    station.station_id)
                if aa:
                    quantity += sum([_.quantity for _ in aa])
                # ---
                jj = cs.industry_jobs.get_with_unique_items(
                    None,
                    product_type_id,
                    places=[tools.ConveyorJobPlace.BLUEPRINT, tools.ConveyorJobPlace.OUTPUT],
                    facility_id=station.station_id)
                if jj:
                    single_run_output: int = tools.get_single_run_output_quantity(product_type_id,
                                                                                  jj[0].activity.to_int(),
                                                                                  qid)
                    in_progress += single_run_output * sum([_.runs for _ in jj])
            # проверяем списки метариалов, используемых в исследованиях и производстве
            material_tag: str = ""
            #if product_type_id in materials_for_bps:
            #    pass
            #elif product_type_id in research_materials_for_bps:
            #    material_tag = ' <span class="label label-warning">research material</span></small>'
            #else:
            #    material_tag = ' <span class="label label-danger">non material</span></small>'
            # --- --- ---
            # <qmaterial tid="16663" icn="24" cl="qind-sign"></qmaterial>
            # эквивалентно:
            #   <qimg24 data-tid="16663"></qimg24> <qnm data-tid="16663"></qnm>&nbsp;<a data-target="#" role="button"
            #   data-tid="16663" class="qind-copy-btn qind-sign" data-toggle="tooltip"><span class="glyphicon
            #   glyphicon-copy" aria-hidden="true"></span></a>
            # эквивалентно:
            #   <img class="icn24" src="http://imageserver.eveonline.com/Type/16663_32.png"> Caesarium Cadmide&nbsp;<a
            #   data-target="#" role="button" data-tid="16663" class="qind-copy-btn qind-sign" data-toggle="tooltip"
            #   data-original-title="" title=""><span class="glyphicon glyphicon-copy" aria-hidden="true"></span></a>
            glf.write(
                '<tr>'
                '<td scope="row">{num}</td>'
                '<td><qmaterial tid="{tid}" cl="qind-sign"></qmaterial>{mat_tag}</td>'
                '<td>{q}</td>'
                '<td>{ne}</td>'
                '<td>{ip}</td>'
                '</tr>\n'.
                format(num=row_num,
                       tid=product.type_id,
                       mat_tag=material_tag,
                       q="" if quantity == 0 else '{:,d}'.format(quantity),
                       ne="" if not_enough == 0 else '{:,d}'.format(not_enough),
                       ip="" if in_progress == 0 else '{:,d}'.format(in_progress))
            )
        glf.write("""
</tbody>
</table>
</div> <!-- col -->
</div> <!-- row -->
""")
    # закрываем footer модального диалога
    render_html.__dump_any_into_modal_footer(glf)


def dump_nav_menu_conveyor_dialog(
        glf,
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        # настройки генерации отчёта
        conveyor_settings: typing.List[tools.ConveyorSettings]) -> None:
    # создаём заголовок модального окна, где будем показывать список имеющихся материалов в контейнере "..stock ALL"
    render_html.__dump_any_into_modal_header_wo_button(
        glf,
        "Настройки конвейера",
        unique_id="Conveyor",
        modal_size="modal-lg")
    # формируем содержимое модального диалога
    glf.write("""<p>Ниже перечислены контейнеры, которые "увидел" конвейер и содержимое которых учитывает в расчётах. Названия
контейнеров должны выбираться по специальным шаблонам (см. корпоративные биллютени). В контейнерах из раздела <span style="color:#ffa600">Чертежи</span>
должны находиться BPC или BPO для расчёта производственных процессов, процессов инвента или варки реакций. Содержимое
контейнеров из раздела <span style="color:#ffa600">Оверсток</span> учитывается в расчётах таким образом, что непроданная продукция не будет
снова попадать в расчёт производства (даже если в контейнерах <span style="color:#ffa600">Чертежи</span> имеются чертежи для этой продукции).
Материалы для производства будут браться в расчёт из контейнеров группы <span style="color:#ffa600">Сток</span> (у инвента как правило свой
сток, совпадающий с расположением BPO, а у производства и реакций свой). Для расчёта промежуточных этапов производства
выбираются контейнеры из раздела <span style="color:#ffa600">Дополнительные чертежи</span>, - следите за тем, чтобы в этот раздел не попадали
лишние названия, например персональные коробки или коробки 'Ночного цеха', в противном случае их содержимое попадёт в
расчёт конвейера. Контейнеры из раздела <span style="color:#ffa600">Выход</span> должны выбираться в настройках производства как "Склад
готовой продукции", в противном случае активные и завершённые производственные проекты на странице конвейера будут
просигнализированы предупреждениями.</p>
<hr>""")

    def dump_table(label646: str,
                   corp_name646: str,
                   boxes646: typing.List[tools.ConveyorSettingsContainer],
                   color646: typing.Optional[str] = None) -> None:
        if not boxes646: return
        glf.write(f"""
<table class="table table-condensed table-hover tbl-conveyor">
<thead><tr><th>#</th><th>{label646} <mute>{corp_name646}</mute></th></tr></thead>
<tbody>\n""")
        if color646:
            color646 = f" style='color:{color646}'"
        else:
            color646 = ""
        for box667 in boxes646:
            glf.write(f"<tr container_id='{box667.container_id}'>"
                      f"<td>{get_tbl_conveyor_row_num()}</td>"
                      f"<td{color646}>{box667.container_name}</td>"
                      "</tr>\n")
        glf.write("</tbody></table>\n")

    for (idx, _s) in enumerate(conveyor_settings):
        s: tools.ConveyorSettings = _s
        if idx:
            glf.write('<hr>')
        corporation: db.QSwaggerCorporation = s.corporation
        activities: str = ', '.join([str(_) for _ in s.activities])
        glf.write(f"<h3 corporation_id='{corporation.corporation_id}'>Конвейер {corporation.corporation_name} "
                  f"<small>{activities}</small></h3>")
        stations: typing.List[int] = list(set([x.station_id for x in s.containers_sources] +
                                              [x.station_id for x in s.containers_stocks] +
                                              [x.station_id for x in s.containers_additional_blueprints] +
                                              [x.station_id for x in s.containers_sale_stocks]))
        stations: typing.List[db.QSwaggerStation] = sorted(
            [qid.get_station(x) for x in stations],
            key=lambda x: x.station_name if x else '')
        for station in stations:
            station_id: int = station.station_id if station else None
            station_name: str = station.station_name if station else None
            station_type: str = station.station_type_name if station else None

            glf.write(f"""
<h4 station_id='{station_id}'>{station_name} <small>{station_type}</small></h4>
<div class="row">
 <div class="col-md-4">""")

            if s.conveyor_with_reactions:
                z: typing.List[tools.ConveyorSettingsContainer] = sorted(
                    [x for x in s.containers_react_formulas if x.station_id == station_id],
                    key=lambda x: x.container_name)
                dump_table("Формулы", corporation.corporation_name, z)
                del z

            z: typing.List[tools.ConveyorSettingsPriorityContainer] = sorted(
                [x for x in s.containers_sources if x.station_id == station_id],
                key=lambda x: x.container_name)
            dump_table("Чертежи", corporation.corporation_name, z)
            del z

            glf.write("""
</div> <!-- col -->
<!-- -->
<div class="col-md-4">""")

            z: typing.List[tools.ConveyorSettingsContainer] = [x for x in s.containers_stocks if x.station_id == station_id]
            z.sort(key=lambda x: x.container_name)
            dump_table("Сток", corporation.corporation_name, z)
            del z

            z: typing.List[tools.ConveyorSettingsSaleContainer] = sorted(
                [x for x in s.containers_sale_stocks if x.station_id == station_id],
                key=lambda x: x.container_name)
            if z:
                w0: typing.List[str] = list(set([x.trade_corporation.corporation_name for x in z]))
                w1: typing.List[str] = sorted(w0, key=lambda x: x)
                for corporation_name in w1:
                    dump_table("Оверсток", corporation_name,
                               [_ for _ in z if _.trade_corporation.corporation_name == corporation_name],
                               color646="#ffa600")

            z: typing.List[tools.ConveyorSettingsContainer] = sorted(
                [x for x in s.containers_output if x.station_id == station_id],
                key=lambda x: x.container_name)
            dump_table("Выход", corporation.corporation_name, z)
            del z

            glf.write("""
</div> <!-- col -->
<!-- -->
<div class="col-md-4">""")

            if db.QSwaggerActivityCode.MANUFACTURING in s.activities:
                z: typing.List[tools.ConveyorSettingsContainer] = sorted(
                    [x for x in s.containers_additional_blueprints if x.station_id == station_id],
                    key=lambda x: x.container_name)
                dump_table("Дополнительные чертежи<br>", corporation.corporation_name, z)

            glf.write("""
 </div> <!-- col -->
</div> <!-- row -->
""")
    # закрываем footer модального диалога
    render_html.__dump_any_into_modal_footer(glf)


def dump_nav_menu_demand_dialog(
        glf,
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        demands: typing.Optional[tools.ConveyorDemands],
        # анализ чертежей на предмет перепроизводства
        industry_analysis: tools.ConveyorIndustryAnalysis,
        # настройки генерации отчёта
        conveyor_settings: typing.List[tools.ConveyorSettings]) -> None:
    # создаём заголовок модального окна, где будем показывать список имеющихся материалов в контейнере "..stock ALL"
    render_html.__dump_any_into_modal_header_wo_button(
        glf,
        "Анализ остатков в ордерах",
        unique_id="Demand",
        modal_size="modal-lg")

    # формируем содержимое модального диалога
    glf.write("""
<p style="color:#ffa600">TL;DR Не запускайте копирку!!!
<ul>
 <li style="color:#ffa600">если у вас не включено отображение чертежей, находящихся в работе;
 <li style="color:#ffa600">если копирка чертежей этого типа уже ведётся;
</ul>
</p>

<p>Копирка не будет предлагаться, когда во всех маркетах суммарно выставлено товара больше,
чем настроено в лимите производства (даже если весь товар выставлен всего в одном маркете,
а остальные маркеты пустые, - продукты на продажу надо отвозить туда, куда запланировано).</p>

<p>Если суммарное количество выставленного товара в макетах меньше, чем настроено в лимите
производства, то запуск копирки становится возможен.</p>

<p>Копирка предлагается к запуску только, если отсутствуют T1,T2,T3-чертежи (и работы с
ними), а также если чертежей недостаточно чтобы закрыть требования рынка.</p>

<p>Производственникам, запускающим копирку рекомендуется в настройках окна производства
включить "Показ чертежей находящихся в работе", так вы оперативно сможете увидеть, что
кто-то устел запустить копирку раньше вас. Тем самым учесть лаг в обновлении информации на
странице конвейера. По этой же причине рекомендуется запускать копирку используя все
доступные оригиналы, чтобы исключить невнимательность других игроков.</p>
""")

    for s in conveyor_settings:
        if not demands: break
        corporation: db.QSwaggerCorporation = s.corporation
        if not s.calculate_requirements: continue
        # ищем производственный конвейер корпорации
        if db.QSwaggerActivityCode.MANUFACTURING not in s.activities: continue

        # инициализация списка потребностей (задача копирки), сортировка списка
        requirements: typing.List[tools.ConveyorDemands.Corrected] = [
            _ for _ in demands.ordered_demand
            # if _.rest_percent <= s.requirements_sold_threshold
        ]
        overstock: typing.List[tools.ConveyorDemands.Corrected] = demands.ordered_overstock

        row_num: int = 0
        for index, products in enumerate([requirements, overstock]):
            if index == 0:
                glf.write(
                    f"<h3 corporation_id='{corporation.corporation_id}'"
                    f">Спрос на продукцию <small>{corporation.corporation_name}</small></h3>")
            else:
                glf.write(
                    f"<h3 corporation_id='{corporation.corporation_id}'"
                    f">Оверсток копирки, инвента и производства <small>{corporation.corporation_name}</small></h3>")

            glf.write(f"""
<table class="table table-condensed table-hover tbl-requirements">
<thead>
 <tr>
  <th>#</th>
  <th>{'Спрос' if index==0 else 'Оверсток'}</th>
  <th><small>Потребность</small></th>
  <th><small>Лимит</small></th>
  <th><small>Остаток в<br>маркетах</small></th>
  <th><small>Имеется</small></th>
  <th><small>Готово<br>прогонов</small></th>
  <th><small>BPO</small></th>
 </tr>
</thead>
<tbody>""")

            for product in products:
                row_num += 1

                tr_class: str = ''
                if index == 0:
                    if product.requirement.rest_percent <= s.requirements_sold_threshold:
                        tr_class: str = 'demand'
                    if (product.requirement.trade_remain / product.requirement.limit) <= 0.05:
                        tr_class = tr_class + (' pure' if tr_class else '')
                else:
                    tr_class: str = 'overstock'
                if tr_class:
                    tr_class = f' class="{tr_class}"'

                num_ready: int = 0
                num_prepared: typing.Optional[int] = None
                product_info_btn: str = ''
                product_details_note: str = ''

                if product.analysis_tier2:
                    num_ready: int = product.analysis_tier2.num_ready
                    num_prepared: int = product.analysis_tier2.num_prepared
                    # формирование отчёта со сведениями о производстве
                    product_info_btn = '&nbsp;' + format_product_tier2_info_btn(product.analysis_tier2)
                    # не требуется: product_details_note = f' <mute> - имеется</mute> {num_ready} <mute>шт</mute>'
                    # если произведено излишнее количество продукции, то отмечаем чертежи маркером
                    if (num_ready+num_prepared) > 0 and product.analysis_tier2.product_tier2_overstock:
                        product_details_note += ' <label class="label label-overstock">перепроизводство</label>'
                elif product.analysis_tier1:
                    num_ready: int = product.analysis_tier1.num_ready
                    # формирование отчёта со сведениями о производстве
                    product_info_btn = '&nbsp;' + format_product_tier1_info_btn(product.analysis_tier1)
                    # не требуется: product_details_note = f' <mute> - имеется</mute> {num_ready} <mute>шт</mute>'
                    # если произведено излишнее количество продукции, то отмечаем чертежи маркером
                    if num_ready > 0 and product.analysis_tier1.product_tier1_overstock:
                        product_details_note += ' <label class="label label-overstock">перепроизводство</label>'

                str_ready: str = f'{num_ready:,}'
                if num_ready == product.requirement.trade_remain:
                    str_ready = '<mute>'+str_ready+'</mute>'
                str_prepared: str = ''
                if num_prepared is not None:
                    str_prepared = f'{num_prepared:,}'
                    if num_prepared == 0:
                        str_prepared = '<mute>'+str_prepared+'</mute>'

                num_originals: str = ''

                # TODO: костыль, удалить!
                if product.analysis_tier3:
                    if product.analysis_tier3.product_tier1_num_in_originals:
                        num_originals = str(product.analysis_tier3.product_tier1_num_in_originals)
                    str_prepared += f' + {product.analysis_tier3.product_tier1_num_in_copy_runs}'\
                                    f' + {product.analysis_tier3.product_tier1_num_in_jobs}'\
                                    f' + {product.analysis_tier3.product_tier1_num_in_job_runs}'

                invent_plan: str = ''

                if product.requirement.rest_percent <= s.requirements_sold_threshold and \
                   product.analysis_tier2 and \
                   product.analysis_tier3 and \
                   not num_prepared and \
                   not product.analysis_tier3.product_tier1_num_in_copy_runs and \
                   not product.analysis_tier3.product_tier1_num_in_jobs:
                    copied_bpc: db.QSwaggerBlueprint = product.analysis_tier3.product_tier1
                    copying: typing.Optional[db.QSwaggerBlueprintCopying] = product.analysis_tier3.activity_tier1
                    invention: typing.Optional[db.QSwaggerBlueprintInvention] = product.analysis_tier2.activity_tier1
                    if copied_bpc and copying and invention:
                        invented_bpc: typing.Optional[db.QSwaggerInventionProduct] = next((_ for _ in invention.products
                            if _.product_id==product.analysis_tier2.analysis_tier2.product.blueprint_tier1.type_id), None)
                        if invented_bpc:
                            # считаем длительность инвента одной копии с одним прогоном
                            # 30% бонус сооружения, 15% навыки и импланты (минимально необходимый уровень)
                            single_invent_copy_run: float = ((invention.time * (1-0.3)) * (1-0.15))
                            # считаем кол-во прогонов копий чертежй, которые необходимо выбрать при копирке
                            # (относительно 2х суток)
                            num_copies_runs: int = math.ceil(172800 / single_invent_copy_run)
                            # считаем длительность копирки одной копии с N прогонами
                            # 30% бонус сооружения, 36.3% навыки и импланты (минимально необходимый уровень)
                            n_run_copy_duration: float = (num_copies_runs * copying.time * (1-0.3)) * (1-0.363)
                            # учитываем вероятность успеха инвента T2 чертежей и считаем ориентировочное количество
                            # T2-продукции, которая может быть получена из копий с N прогонами:
                            # 30% навыки и импланты
                            probable_t2_products: float = (num_copies_runs * invented_bpc.quantity * (1-invented_bpc.probability)) * (1-0.3)
                            # поскольку нам необходимо произвести X единиц продукции (в соответствии с ограничениями
                            # на производство), то считаем количество копий чртежей/штук по N прогонов
                            num_copies_by_n_runs: int = math.ceil(product.requirement.limit / probable_t2_products)
                            # ---
                            invent_plan = f'<br><span style="color: #3371b6">{copied_bpc.blueprint_type.name}</span><mute>: ' \
                                          f'Число копий</mute> {num_copies_by_n_runs} ' \
                                          f'<mute>x Прогонов за копию</mute> {num_copies_runs}'

                glf.write(f"""<tr{tr_class}>
<td scope="row">{row_num}</td>
<td><qmaterial tid="{product.requirement.type_id}" cl="qind-sign"></qmaterial>{product_info_btn}{product_details_note}{invent_plan}</td>
<td>{100.0 - product.requirement.rest_percent*100.0:,.1f}%</td>
<td>{product.requirement.limit:,}</td>
<td>{product.requirement.trade_remain:,}</td>
<td>{str_ready}</td>
<td>{str_prepared}</td>
<td>{num_originals}</td>
</tr>
</tr>\n""")

            glf.write(f"""
</tbody>
</table>""")

    # закрываем footer модального диалога
    render_html.__dump_any_into_modal_footer(glf)


def dump_nav_menu_lifetime_dialog(
        glf,
        # данные (справочники)
        qid: db.QSwaggerDictionary) -> None:
    # создаём заголовок модального окна, где будем показывать список имеющихся материалов в контейнере "..stock ALL"
    render_html.__dump_any_into_modal_header_wo_button(
        glf,
        "Актуализация ассетов",
        unique_id="Lifetime",
        modal_size="modal-lg")
    # "текущее" время сервера БД (может отличаться от текущего времени построения отчёта
    server_time = qid.sde_lifetime.get(('current', None))
    # формируем содержимое модального диалога
    glf.write(f"""
<script>
var g_server_time={int(server_time.timestamp())};
</script>
<table class="table table-condensed table-hover tbl-lifetime">
<tbody>
<tr><td>Время сервера</td><td>{server_time}</td></tr>
<tr><td>Время браузера</td><td id="browser-time"></td></tr>
</tbody>
</table>""")
    for corporation in qid.corporations.values():
        corporation_id: int = corporation.corporation_id
        assets: datetime.datetime = qid.sde_lifetime.get(('assets', corporation_id))
        blueprints: datetime.datetime = qid.sde_lifetime.get(('blueprints', corporation_id))
        jobs: datetime.datetime = qid.sde_lifetime.get(('jobs', corporation_id))
        orders: datetime.datetime = qid.sde_lifetime.get(('orders', corporation_id))
        # ---
        assets_left: int = int(assets.timestamp())
        blueprints_left: int = int(blueprints.timestamp())
        jobs_left: int = int(jobs.timestamp())
        orders_left: int = int(orders.timestamp())
        # ---
        glf.write(f"""
<h4>{corporation.corporation_name}</h4>
<table class="table table-condensed table-hover tbl-lifetime">
<thead><tr><th>#</th><th>Время</th></tr></thead>
<tbody>
<tr><td>Ассеты</td><td>{assets} <left data-ts="{assets_left}" data-w="a"></left></td></tr>
<tr><td>Чертежи</td><td>{blueprints} <left data-ts="{blueprints_left}" data-w="b"></left></td></tr>
<tr><td>Производство</td><td>{jobs} <left data-ts="{jobs_left}" data-w="j"></left></td></tr>
<tr><td>Маркет</td><td>{orders} <left data-ts="{orders_left}" data-w="o"></left></td></tr>
</tbody>
</table>
""")
    # закрываем footer модального диалога
    render_html.__dump_any_into_modal_footer(glf)


def dump_industry_product_dialog(glf) -> None:
    # создаём заголовок модального окна, где будем показывать список имеющихся материалов в контейнере "..stock ALL"
    render_html.__dump_any_into_modal_header_wo_button(
        glf,
        "<icon></icon>&nbsp;<span id='product-name'></span>",
        unique_id="IndustryProduct",
        modal_size="modal-sm")
    # формируем содержимое модального диалога
    glf.write("""<p>
Хранится в ассетах: <span id="product-in-assets" class="quantity"></span><br>
Производится: <span id="product-in-jobs" class="quantity"></span><br>
Выставлено на продажу: <span id="product-in-sale" class="quantity"></span><br>
Подготовлено чертежей: <span id="product-in-blueprints" class="quantity"></span><br>
Прогоны чертежей: <span id="product-in-blueprint-runs" class="quantity"></span><hr>
Порог производства: <span id="product-limit" class="quantity"></span>
</p>""")
    # закрываем footer модального диалога
    render_html.__dump_any_into_modal_footer(glf)


def dump_blueprints_overflow_warn(
        glf,
        # настройки генерации отчёта
        conveyor_settings: typing.List[tools.ConveyorSettings]) -> None:
    # перебор всех корпораций у всех возможных конвейеров
    corporations: typing.Set[int] = set()
    for s in conveyor_settings:
        c: db.QSwaggerCorporation = s.corporation
        if c.corporation_id in corporations: continue
        corporations.add(c.corporation_id)
        # подсчёт кол-ва чертежей у корпорации
        qty: int = len(c.blueprints)
        if qty >= 22500:  # 10% 2
            overflow = qty >= 23750  # 5%
            glf.write(
                '<div class="alert alert-{alc}" role="alert">{gly}'
                '<span class="sr-only">{ew}:</span> Количество корпоративных чертежей не должно превышать 25,000 шт.'
                ' В противном случае, чертежи не смогут быть найдены в окне производства. Также может пострадать'
                ' корректность расчётов производственных процессов. В настоящее время в распоряжении <b>{cnm}</b>'
                ' имеется <b>{q:,d}</b> чертежей.'
                '</div>'.
                format(
                    gly=glyphicon("warning-sign"),
                    alc='danger' if overflow else 'warning',
                    ew='Error' if overflow else 'Warning',
                    cnm=c.corporation_name,
                    q=qty,
                ))


def dump_list_of_jobs(
        glf,
        # данные для генератора тэга сортировки
        priority: int,
        # настройки генерации отчёта
        settings: tools.ConveyorSettings,
        # работы
        jobs: typing.List[db.QSwaggerCorporationIndustryJob],
        is_active_jobs: bool) -> None:
    # готовим список контейнеров выхода в проверке
    containers_output_ids: typing.Set[int] = set([_.container_id for _ in settings.containers_output])
    # группируем работы по типу, чтобы получить уникальные сочетания с количествами
    grouped: typing.Dict[typing.Tuple[int, int], typing.List[db.QSwaggerCorporationIndustryJob]] = \
        tools.get_jobs_grouped_by(
            jobs,
            group_by_product=True,
            group_by_activity=True)
    # сортируем уже сгруппированные работы
    grouped_and_sorted: typing.List[typing.Tuple[
        str,
        str,
        typing.Optional[int],
        typing.Optional[int],
        typing.List[db.QSwaggerCorporationIndustryJob]]] = []
    for key in grouped.keys():
        group: typing.List[db.QSwaggerCorporationIndustryJob] = grouped.get(key)
        j0: db.QSwaggerCorporationIndustryJob = group[0]
        if j0.blueprint_type is not None:  # новый тип чертежа, которого ещё нет в БД
            sum_runs: int = sum([j.runs for j in group])
            sum_products: int = sum_runs * tools.get_product_quantity(j0.activity.to_int(),
                                                                      j0.product_type_id,
                                                                      j0.blueprint_type)
            blueprint_type_name: str = j0.blueprint_type.blueprint_type.name
        else:
            sum_runs: typing.Optional[int] = None
            sum_products: typing.Optional[int] = None
            blueprint_type_name: str = str(j0.blueprint_type_id)
        if j0.product_type is not None:
            product_type_name: str = j0.product_type.name
        else:
            product_type_name: str = str(j0.product_type_id)
        grouped_and_sorted.append((
            blueprint_type_name,
            product_type_name,
            sum_runs,
            sum_products,
            group))
    grouped_and_sorted.sort(key=lambda x: x[0])
    # выводим в отчёт
    global g_nav_menu_defaults
    for blueprint_type_name, product_type_name, sum_runs, sum_products, group in grouped_and_sorted:
        j0: db.QSwaggerCorporationIndustryJob = group[0]
        blueprint_type_id: int = j0.blueprint_type_id
        product_type_id: int = j0.product_type_id
        # --- --- ---
        installer: str = ''
        installers_count: int = len(set([_.installer_id for _ in group]))
        if installers_count == 1:
            installer = f'<mute>Оператор</mute> {j0.installer.character_name}'
        else:
            installer_names: str = ', '.join(set([_.installer.character_name for _ in group]))
            if len(installer_names) <= 20:
                installer = f'<mute>Операторы</mute> {installer_names}'
            else:
                installer = f'<mute>Операторы - </mute><a data-target="#" data-copy="{installer_names}"' \
                            f' data-toggle="tooltip" class="qind-copy-btn">{installers_count} перс</a>'
        # --- --- ---
        output: str = ''
        outputs_count: int = len(set([_.output_location_id for _ in group]))
        if outputs_count == 1:
            nm: str = j0.output_location.name if j0.output_location.name else str(j0.output_location_id)
            output = '<mute>Выход</mute>' + nm
        else:
            nms: str = ', '.join(
                set([_.output_location.name if _.output_location.name else str(_.output_location_id) for _ in group]))
            if len(nms) <= 20:
                output = '<mute>Выход</mute>' + nms
            else:
                output = f'<mute>Выход - </mute><a data-target="#" data-copy="{nms}"' \
                         f' data-toggle="tooltip" class="qind-copy-btn">{outputs_count} кор</a>'
        # --- --- ---
        active_label: str = ''
        if is_active_jobs:
            active_label = '<label class="label label-active-job">проект ведётся</label>'
        else:
            active_label = '<label class="label label-completed-job">проект завершён</label>'
        # --- --- ---
        lost_label: str = ''
        lost_output: str = ''
        lost_class: str = ''
        if containers_output_ids:
            lost_outputs: typing.List[db.QSwaggerCorporationIndustryJob] = \
                [_ for _ in group if _.output_location_id not in containers_output_ids]
            if lost_outputs:
                container_prefix: str = '<br><mute>Контейнер - </mute>'
                lost_outputs_count: int = len(set([_.output_location_id for _ in lost_outputs]))
                nms: typing.List[str] = sorted(set([
                    _.output_location.name if _.output_location.name else str(_.output_location_id)
                    for _ in lost_outputs]))
                lost_output: str = \
                    container_prefix + \
                    container_prefix.join(nms) + \
                    f"<!--\njob_ids: {[_.job_id for _ in lost_outputs]}-->"
                if j0.product_type is None:
                    lost_label = f" <label class='label label-lost-assets'>{declension_of_lost_assets(lost_outputs_count)}</label>"
                elif j0.product_type.group and j0.product_type.group.category_id == 9:  # 9 = Blueprints
                    lost_label = f" <label class='label label-lost-jobs'>{declension_of_lost_blueprints(lost_outputs_count)}</label>"
                else:
                    lost_label = f" <label class='label label-lost-assets'>{declension_of_lost_assets(lost_outputs_count)}</label>"
                lost_class = ' lost-jobs'
        # <mute>Стоимость</mute> {'{:,.1f}'.format(job.cost)}
        # </me_tag><tid_tag> ({blueprint_type_id})</tid_tag>
        tr_class: str = 'job-active' if is_active_jobs else 'job-completed'
        tr_class += g_nav_menu_defaults.css(tr_class)
        # --- --- ---
        sort = tools.get_conveyor_table_sort_data(priority, settings.activities, row_num=get_tbl_summary_row_num(False), duration=None)
        # --- --- ---
        activity_icon: str = get_industry_icons(db.get_activities_by_nums([j0.activity.to_int()]))
        # --- --- ---
        glf.write(f"""<tr class="{tr_class}{lost_class}" {format_json_data('sort', sort)}>
<td>{get_tbl_summary_row_num()}</td>
<td><img class="icn32" src="{render_html.__get_img_src(blueprint_type_id, 32)}"></td>
<td>{activity_icon}&nbsp;<qname>{blueprint_type_name}</qname>&nbsp;<a
data-target="#" role="button" data-tid="{blueprint_type_id}" class="qind-copy-btn" data-toggle="tooltip">{glyphicon("copy")}</a>
{active_label}<br>
<mute>Число прогонов - </mute>{sum_runs if sum_runs is not None else 'нет сведений'}
</td>
<td>{len(group)}</td>
<td></td>
<td><img class="icn32" src="{render_html.__get_img_src(product_type_id, 32)}"></td>
<td>{product_type_name}&nbsp;<a
data-target="#" role="button" data-tid="{product_type_id}" class="qind-copy-btn qind-sign" data-toggle="tooltip">{glyphicon("copy")}</a>{lost_label}<br>
<small>{installer} {output}</small>
{lost_output}
</td>
<td>{sum_products if sum_products is not None else 'нет сведений'}</td>
</tr>""")
    # освобождаем память
    del grouped_and_sorted
    del grouped


def dump_list_of_active_jobs(
        glf,
        priority: int,
        settings: tools.ConveyorSettings,
        active_jobs: typing.List[db.QSwaggerCorporationIndustryJob]) -> None:
    dump_list_of_jobs(glf, priority, settings, active_jobs, is_active_jobs=True)


def dump_list_of_completed_jobs(
        glf,
        priority: int,
        settings: tools.ConveyorSettings,
        completed_jobs: typing.List[db.QSwaggerCorporationIndustryJob]) -> None:
    dump_list_of_jobs(glf, priority, settings, completed_jobs, is_active_jobs=False)


def dump_list_of_lost_blueprints(
        glf,
        # данные для генератора тэга сортировки
        priority: int,
        activities: typing.List[db.QSwaggerActivityCode],
        # справочники
        corporation: db.QSwaggerCorporation,
        # список чертежей, которые невозможно запустить в выбранном конвейере
        lost_blueprints: typing.List[db.QSwaggerCorporationBlueprint]) -> None:
    # группируем чертежи по типу, чтобы получить уникальные сочетания с количествами
    grouped: typing.Dict[typing.Tuple[int, int, int, int, int], typing.List[db.QSwaggerCorporationBlueprint]] = \
        tools.get_blueprints_grouped_by(
            lost_blueprints,
            group_by_type_id=True,
            group_by_station=False,
            group_by_me=False,
            group_by_te=False,
            group_by_runs=False)
    # сортируем уже сгруппированные чертежи
    grouped_and_sorted: typing.List[typing.Tuple[str, typing.List[db.QSwaggerCorporationBlueprint]]] = []
    for key in grouped.keys():
        group: typing.List[db.QSwaggerCorporationBlueprint] = grouped.get(key)
        if group[0].blueprint_type and group[0].blueprint_type.blueprint_type:
            grouped_and_sorted.append((group[0].blueprint_type.blueprint_type.name, group))
        else:
            grouped_and_sorted.append((str(group[0].type_id), group))
    grouped_and_sorted.sort(key=lambda x: x[0])
    # локальные переменные
    container_prefix: str = '<br><mute>Контейнер - </mute>'
    # выводим в отчёт
    global g_nav_menu_defaults
    for type_name, group in grouped_and_sorted:
        b0: db.QSwaggerCorporationBlueprint = group[0]
        type_id: int = b0.type_id
        sort = tools.get_conveyor_table_sort_data(priority, activities, row_num=get_tbl_summary_row_num(False), duration=None)
        # ---
        containers: typing.Set[str] = set()
        for b in group:
            c: db.QSwaggerCorporationAssetsItem = corporation.assets.get(b.location_id)
            containers.add(c.name if c and c.name else str(b.location_id))
        containers: typing.List[str] = sorted(containers)
        containers: str = container_prefix.join(containers)
        # ---
        glf.write(f"""<tr
 class="lost-blueprints{g_nav_menu_defaults.css('lost-blueprints')}"
 {format_json_data('sort', sort)}>
<td>{get_tbl_summary_row_num()}</td>
<td><img class="icn32" src="{render_html.__get_img_src(type_id, 32)}"></td>
<td><qname>{type_name}</qname>&nbsp;<a
data-target="#" role="button" data-tid="{type_id}" class="qind-copy-btn" data-toggle="tooltip">{glyphicon("copy")}</a>
<label class="label label-lost-blueprints">{declension_of_lost_blueprints(len(group))}</label>{container_prefix}{containers}<!--
item_ids: {[_.item_id for _ in group]}--></td>
<td>{len(group)}</td>
<td></td><td></td><td></td><td></td>
</tr>""")


def dump_list_of_lost_asset_items(
        glf,
        # данные для генератора тэга сортировки
        priority: int,
        activities: typing.List[db.QSwaggerActivityCode],
        # справочники
        corporation: db.QSwaggerCorporation,
        # список ассетов, которые "потерялись" в конвейере
        lost_asset_items: typing.List[db.QSwaggerCorporationAssetsItem]) -> None:
    # группируем ассеты по типу, чтобы получить уникальные сочетания с количествами
    grouped: typing.Dict[typing.Tuple[int, int], typing.List[db.QSwaggerCorporationAssetsItem]] = \
        tools.get_asset_items_grouped_by(
            lost_asset_items,
            group_by_type_id=True,
            group_by_station=False)
    # сортируем уже сгруппированные чертежи
    grouped_and_sorted: typing.List[typing.Tuple[str, typing.List[db.QSwaggerCorporationAssetsItem]]] = []
    for key in grouped.keys():
        group: typing.List[db.QSwaggerCorporationAssetsItem] = grouped.get(key)
        grouped_and_sorted.append((group[0].item_type.name, group))
    grouped_and_sorted.sort(key=lambda x: x[0])
    # локальные переменные
    container_prefix: str = '<br><mute>Контейнер - </mute>'
    # выводим в отчёт
    global g_nav_menu_defaults
    for _, group in grouped_and_sorted:
        a0: db.QSwaggerCorporationAssetsItem = group[0]
        type_id: int = a0.type_id
        type_name: str = a0.item_type.name
        sort = tools.get_conveyor_table_sort_data(priority, activities, row_num=get_tbl_summary_row_num(False), duration=None)
        # ---
        containers: typing.Set[str] = set()
        for a in group:
            c: db.QSwaggerCorporationAssetsItem = corporation.assets.get(a.location_id)
            containers.add(c.name if c and c.name else str(a.location_id))
        containers: typing.List[str] = sorted(containers)
        containers: str = container_prefix.join(containers)
        # ---
        glf.write(f"""<tr
 class="lost-assets{g_nav_menu_defaults.css('lost-assets')}"
 {format_json_data('sort', sort)}>
<td>{get_tbl_summary_row_num()}</td>
<td><img class="icn32" src="{render_html.__get_img_src(type_id, 32)}"></td>
<td><qname>{type_name}</qname>&nbsp;<a
data-target="#" role="button" data-tid="{type_id}" class="qind-copy-btn qind-sign" data-toggle="tooltip">{glyphicon("copy")}</a>
<label class="label label-lost-assets">{declension_of_lost_assets(len(group))}</label>{container_prefix}{containers}<!--
item_ids: {[_.item_id for _ in group]}--></td>
<td>{len(group)}</td>
<td></td><td></td><td></td><td></td>
</tr>""")


def dump_list_of_phantom_blueprints(
        glf,
        # данные для генератора тэга сортировки
        priority: int,
        activities: typing.List[db.QSwaggerActivityCode],
        # список чертежей, которые фантомно присутствуют в коробке конвейера (глюк ССР)
        phantom_blueprints: typing.List[db.QSwaggerCorporationBlueprint]) -> None:
    # группируем чертежи по типу, чтобы получить уникальные сочетания с количествами
    grouped: typing.Dict[typing.Tuple[int, int, int, int, int], typing.List[db.QSwaggerCorporationBlueprint]] = \
        tools.get_blueprints_grouped_by(
            phantom_blueprints,
            group_by_type_id=True,
            group_by_station=False,
            group_by_me=True,
            group_by_te=True,
            group_by_runs=True)
    # сортируем уже сгруппированные чертежи
    grouped_and_sorted: typing.List[typing.Tuple[str, int, int, int, typing.List[db.QSwaggerCorporationBlueprint]]] = []
    for key in grouped.keys():
        group: typing.List[db.QSwaggerCorporationBlueprint] = grouped.get(key)
        b0: db.QSwaggerCorporationBlueprint = group[0]
        grouped_and_sorted.append((
            b0.blueprint_type.blueprint_type.name,
            b0.material_efficiency,
            b0.time_efficiency,
            b0.runs,
            group))
    grouped_and_sorted.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
    # выводим в отчёт
    global g_nav_menu_defaults
    for _, _, _, _, group in grouped_and_sorted:
        b0: db.QSwaggerCorporationBlueprint = group[0]
        type_id: int = b0.type_id
        type_name: str = b0.blueprint_type.blueprint_type.name
        sort = tools.get_conveyor_table_sort_data(priority, activities, row_num=get_tbl_summary_row_num(False), duration=None)

        glf.write(f"""<tr
 class="phantom-blueprints{g_nav_menu_defaults.css('phantom-blueprints')}"
 {format_json_data('sort', sort)}>
<td>{get_tbl_summary_row_num()}</td>
<td><img class="icn32" src="{render_html.__get_img_src(type_id, 32)}"></td>
<td><qname>{type_name}</qname>&nbsp;<a
data-target="#" role="button" data-tid="{type_id}" class="qind-copy-btn" data-toggle="tooltip">{glyphicon("copy")}</a>
<label class="label label-phantom-blueprint">фантомный чертёж</label><br
>{f'<mute>Копия - </mute>{str(b0.runs)}<mute> {declension_of_runs(b0.runs)}</mute>' if b0.is_copy else 'Оригинал'} <me_tag
>{b0.material_efficiency}% {b0.time_efficiency}%</me_tag><!--
type_id:{type_id}
item_id:{[_.item_id for _ in group]}
location_id:{[_.location_id for _ in group]}--></td>
<td>{len(group)}</td>
<td></td><td></td><td></td><td></td>
</tr>""")


def dump_list_of_possible_blueprints(
        glf,
        # данные для генератора тэга сортировки
        priority: int,
        # настройки генерации отчёта
        settings: tools.ConveyorSettings,
        # список чертежей и их потребности (сгруппированные и отсортированные)
        requirements: typing.List[tools.ConveyorMaterialRequirements.StackOfBlueprints],
        # набор проанализированных производственных активностей на предмет случившегося перепроизводства
        industry_analysis: tools.ConveyorIndustryAnalysis) -> None:
    # группируем стеки по названиям чертежей
    grouped: typing.List[typing.Tuple[str, typing.List[tools.ConveyorMaterialRequirements.StackOfBlueprints]]] = []
    for stack in requirements:
        b0: db.QSwaggerCorporationBlueprint = stack.group[0]
        type_name: str = b0.blueprint_type.blueprint_type.name
        g = next((_ for _ in grouped if _[0] == type_name), None)
        if g:
            g[1].append(stack)
        else:
            grouped.append((type_name, [stack]))

    # выводим группами в отчёт
    global g_nav_menu_defaults
    for type_name, stacks in grouped:
        type_id: int = stacks[0].group[0].type_id
        # ---
        tr_class: str = ''
        for stack in stacks:
            x1: bool = not stack.run_possible
            x2: bool = stack.run_possible and stack.only_decryptors_missing_for_stack
            x3: bool = stack.run_possible and not stack.only_decryptors_missing_for_stack
            if not tr_class:
                if x1:
                    tr_class = 'row-impossible'
                elif x2:
                    tr_class = 'row-optional'
                else:  # x3
                    tr_class = 'row-possible'
                tr_class += g_nav_menu_defaults.css(tr_class)
            elif tr_class.startswith('row-impossible'):
                if x2 or x3:
                    tr_class = ''
                    break
            elif tr_class.startswith('row-optional'):
                if x1 or x3:
                    tr_class = ''
                    break
            elif tr_class.startswith('row-possible'):
                if x1 or x2:
                    tr_class = ''
                    break
        if not tr_class:
            tr_class = 'row-multiple'
            tr_class += g_nav_menu_defaults.css(tr_class)
        if industry_analysis.is_all_variants_overstock(type_id, settings):
            tr_class += ' row-overstock'

        def tr_div_class(which: str,
                         __stack784: typing.Optional[tools.ConveyorMaterialRequirements.StackOfBlueprints] = None,
                         head: typing.Optional[bool] = None) -> str:
            if which == 'tr':
                if tr_class:
                    return f' class="{tr_class}"'
            elif which == 'div':
                if head:
                    if not __stack784.run_possible:  # нельзя запустить (нет материалов)
                        div_class: str = 'run-impossible'
                    elif not __stack784.only_decryptors_missing_for_stack:  # можно запустить (все материалы есть)
                        div_class: str = 'run-possible'
                    else:  # можно запустить (не хватает декрипторов)
                        div_class: str = 'run-optional'
                    div_class += g_nav_menu_defaults.css(div_class)
                    return f'<div class="{div_class}">'
                else:
                    return '</div>'
            return ''

        decryptor: str = ''
        if db.QSwaggerActivityCode.INVENTION in settings.activities:
            m0: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerMaterial]] = stacks[0].required_materials_for_stack
            if len(m0) == 1:  # тут проверяется, что activity одна единственная
                activity: db.QSwaggerActivity = next(iter(m0.keys()))
                if isinstance(activity, db.QSwaggerBlueprintInvention):
                    d: typing.Optional[db.QSwaggerMaterial] = \
                        next((_ for _ in itertools.chain(*m0.values()) if _.material_type.market_group_id == 1873), None)
                    if d:
                        decryptor = f'<mute> - модернизируй с </mute><qdecr>{d.material_type.name}</qdecr>'

        # если активностей в одном конвейере несколько, то настройки скорее всего неправильные
        details: str = ''
        quantities: str = '<br>'
        times: str = '<br>'
        min_duration: int = 0
        max_duration: int = 0
        for stack in stacks:
            # TODO: здесь какая-то путаница с activity(ies)
            na = []
            js = [(_.material_type.type_id, _.quantity) for _ in itertools.chain(*stack.required_materials_for_stack.values())]
            for _ in stack.not_available_materials_for_stack.values(): na.extend(_)
            js = [(tid, q, next((_.quantity for _ in na if _.material_type.type_id == tid), 0)) for (tid, q) in js]
            # ---
            b0: db.QSwaggerCorporationBlueprint = stack.group[0]
            tt: typing.Tuple[int, int] = tools.get_min_max_time(settings.activities, stack)
            if min_duration == 0:
                min_duration, max_duration = tt
            else:
                min_duration, max_duration = min(min_duration, tt[0]), max(max_duration, tt[1])
            me_te_tag: str = ''
            if db.QSwaggerActivityCode.RESEARCH_TIME in settings.activities or \
               db.QSwaggerActivityCode.RESEARCH_MATERIAL in settings.activities:
                me_te_tag = f"<me_tag>{b0.material_efficiency}% <mute>/</mute> {b0.time_efficiency}%</me_tag>"
            elif db.QSwaggerActivityCode.MANUFACTURING in settings.activities:
                me_te_tag = f"<me_tag>{b0.material_efficiency}% <mute>/ {b0.time_efficiency}%</mute></me_tag>"
            elif db.QSwaggerActivityCode.INVENTION in settings.activities:
                pass  # для инвента me_te_tag нет смысла показывать
            details += f"{tr_div_class('div', stack, True)}" \
                       f"{f'<mute>Копия - </mute>{str(b0.runs)}<mute> {declension_of_runs(b0.runs)}</mute>' if b0.is_copy else 'Оригинал'} " \
                       f"{me_te_tag}" \
                       f"<qmaterials {format_json_data('arr', js)}></qmaterials>" \
                       f"{tr_div_class('div', None, False)}"
            quantities += f"{tr_div_class('div', stack, True)}" \
                          f"{format_num_of_num(stack.max_possible_for_single, len(stack.group))}" \
                          f"{tr_div_class('div', None, False)}"
            times += f"{tr_div_class('div', stack, True)}" \
                     f"{format_time_to_time(tt[0], tt[1])}" \
                     f"{tr_div_class('div', None, False)}"

        variants: str = ''
        product_info_btn: str = ''
        product_details_note: str = ''
        if db.QSwaggerActivityCode.INVENTION in settings.activities:
            invent_analysis: typing.Optional[tools.ConveyorInventProductsAnalysis] = \
                industry_analysis.invent_analysis.get(type_id)
            if invent_analysis:
                if len(invent_analysis.products) == 1:
                    ia: tools.ConveyorInventAnalysis = invent_analysis.products[0]
                    if ia.product_tier2 is not None:
                        num_prepared: int = ia.num_ready + ia.num_prepared
                        # формирование отчёта со сведениями об инвенте
                        variants_class: str = "invent-product" + g_nav_menu_defaults.css('invent-product')
                        variants += \
                            f'<div class="{variants_class}">' \
                            f'<qproduct tid="{ia.product_tier2.product_id}" icn="20" cl="qind-sign"></qproduct>' \
                            '</div>'
                        product_info_btn = '&nbsp;' + format_product_tier2_info_btn(ia)
                        product_details_note = f' <mute> - имеется</mute> {num_prepared} <mute>шт</mute>'
                        # если произведено излишнее количество продукции, то отмечаем чертежи маркером
                        if num_prepared > 0 and ia.product_tier2_overstock:
                            product_details_note += ' <label class="label label-overstock">перепроизводство</label>'
                else:
                    for ia in invent_analysis.products:
                        if ia.product_tier2 is None: continue
                        num_prepared: int = ia.num_ready + ia.num_prepared
                        # формирование отчёта со сведениями об инвенте
                        variants += \
                            f'<div class="invent-products">' \
                            f'<qproduct tid="{ia.product_tier2.product_id}" icn="20" cl="qind-sign"></qproduct>' \
                            ' ' + format_product_tier2_info_btn(ia) + \
                            f'<mute> - имеется</mute> {num_prepared} <mute>шт</mute>'
                        # если произведено излишнее количество продукции, то отмечаем чертежи маркером
                        if num_prepared > 0 and ia.product_tier2_overstock:
                            variants += ' <label class="label label-overstock">перепроизводство</label>'
                        variants += '</div>'
        if db.QSwaggerActivityCode.MANUFACTURING in settings.activities:
            manufacturing_analysis: typing.Optional[tools.ConveyorManufacturingProductAnalysis] = \
                industry_analysis.manufacturing_analysis.get(type_id)
            if manufacturing_analysis and manufacturing_analysis.product and manufacturing_analysis.product.product_tier1:
                ma: tools.ConveyorManufacturingAnalysis = manufacturing_analysis.product
                num_ready: int = ma.num_ready
                # формирование отчёта со сведениями о производстве
                variants_class: str = "industry-product" + g_nav_menu_defaults.css('industry-product')
                variants += \
                    f'<div class="{variants_class}">' \
                    f'<qproduct tid="{ma.product_tier1.product_id}" icn="20" cl="qind-sign"></qproduct>' \
                    '</div>'
                product_info_btn = '&nbsp;' + format_product_tier1_info_btn(ma)
                product_details_note = f' <mute> - имеется</mute> {num_ready} <mute>шт</mute>'
                # если произведено излишнее количество продукции, то отмечаем чертежи маркером
                if num_ready > 0 and ma.product_tier1_overstock:
                    product_details_note += ' <label class="label label-overstock">перепроизводство</label>'

        blueprint_copy_btn: str = f'&nbsp;<a data-target="#" role="button" data-tid="{type_id}" class="qind-copy-btn"' \
                                  f' data-toggle="tooltip">{glyphicon("copy")}</a>'

        sort = tools.get_conveyor_table_sort_data(priority, settings.activities, row_num=get_tbl_summary_row_num(False), duration=(min_duration, max_duration))
        activity_icons: str = get_industry_icons(settings.activities)

        glf.write(f"""<tr{tr_div_class('tr')} {format_json_data('sort', sort)}>
<td>{get_tbl_summary_row_num()}</td>
<td><img class="icn32" src="{render_html.__get_img_src(type_id, 32)}"></td>
<td>{activity_icons}&nbsp;<qname>{type_name}</qname>{product_info_btn}{blueprint_copy_btn}{decryptor}
{product_details_note}{details}{variants}</td>
<td>{quantities}</td>
<td>{times}</td>
<td></td><td></td><td></td>
</tr>""")


def dump_conveyor_banner(
        glf,
        label: str,
        priority: typing.Optional[int],
        activities: typing.List[db.QSwaggerActivityCode],
        additional_class: typing.Optional[typing.List[str]] = None) -> None:
    if label: label += ' '
    if additional_class:
        additional_class: str = ' ' + ' '.join(additional_class)
    else:
        additional_class: str = ''
    # сведения для java-script с информацией о коробках конвейера (приоритет и activity)
    tag = tools.get_conveyor_table_sort_data(priority, activities, row_num=None, duration=None)
    glf.write(f"""<tr class="row-conveyor{additional_class}" {format_json_data('tag', tag)}>
<td colspan="8">{label}<mute>{', '.join([str(_) for _ in activities])}</mute>
<a data-target="#" role="button" class="qind-btn-hide qind-btn-hide-open">{glyphicon('eye-open')}</a>
</td>
</tr>
""")


def dump_corp_conveyors(
        glf,
        # результат анализа содержимого конвейерных коробок
        corp_conveyors_calcs: tools.ConveyorCalculations,
        # анализ чертежей на предмет перепроизводства
        industry_analysis: tools.ConveyorIndustryAnalysis,
        # настройки генерации отчёта
        conveyor_settings: typing.List[tools.ConveyorSettings]) -> None:
    # проверка, пусты ли настройки конвейера?
    if len(conveyor_settings) == 0: return
    # получаем ссылку на единственную корпорацию
    corporation: db.QSwaggerCorporation = corp_conveyors_calcs.corporation

    glf.write(f"""
<h2>Конвейер {corporation.corporation_name}</h2>
<table class="table table-condensed table-hover tbl-summary">
<thead>
 <tr>
  <th></th><!--1-->
  <th></th><!--2-->
  <th>Названия чертежей</th><!--3-->
  <th>Кол-во</th><!--4-->
  <th>Длит.</th><!--5-->
  <th></th><!--6-->
  <th>Названия предметов</th><!--7-->
  <th>Кол-во</th><!--8-->
 </tr>
</thead>
<tbody>
""")

    for s in conveyor_settings:
        dump_conveyor_banner(glf, '', None, s.activities, additional_class=['hidden'])

    # перебираем сгруппированные преоритизированные группы
    for priority in sorted(corp_conveyors_calcs.prioritized.keys()):
        p0: typing.Dict[tools.ConveyorSettings, tools.ConveyorCalculations.Prioritized] = \
            corp_conveyors_calcs.prioritized.get(priority)
        for settings, _prioritized in p0.items():
            prioritized: tools.ConveyorCalculations.NthPriority = _prioritized.data
            dump_conveyor_banner(glf, f'Приоритет {priority}', priority, settings.activities)
            # если чертежей для продолжения расчётов нет (коробки пустые), то пропускаем приоритет
            if prioritized.possible_blueprints:
                # выводим в отчёт
                dump_list_of_possible_blueprints(
                    glf,
                    priority,
                    settings,
                    prioritized.requirements,
                    industry_analysis)
            # вывести информацию о работах, которые прямо сейчас ведутся с чертежами в коробке конвейера
            if prioritized.active_jobs:
                dump_list_of_active_jobs(
                    glf,
                    priority,
                    settings,
                    prioritized.active_jobs)  # [b for b in blueprints if b.item_id in active_blueprint_ids]
            # вывести информацию о работах, которые прямо недавно закончились
            if prioritized.completed_jobs:
                dump_list_of_completed_jobs(
                    glf,
                    priority,
                    settings,
                    prioritized.completed_jobs)  # [b for b in blueprints if b.item_id in completed_blueprint_ids]
            # возможно появление корпоративных чертежей, которых нет в ассетах (приём довольно длительное время)
            if prioritized.phantom_blueprints:
                dump_list_of_phantom_blueprints(
                    glf,
                    priority,
                    settings.activities,
                    prioritized.phantom_blueprints)
            # если в коробке застряли чертежи которых там не должно быть, то выводим об этом сведения
            if prioritized.lost_blueprints:
                dump_list_of_lost_blueprints(
                    glf,
                    priority,
                    settings.activities,
                    corporation,
                    prioritized.lost_blueprints)
            if prioritized.lost_asset_items:
                dump_list_of_lost_asset_items(
                    glf,
                    priority,
                    settings.activities,
                    corporation,
                    prioritized.lost_asset_items)

    glf.write("""
</tbody>
</table>
""")


def dump_list_of_products(
        glf,
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        corporation: db.QSwaggerCorporation,
        # текущие сведения роутинга на станции
        current_router_settings: tools.RouterSettings,
        # ищем производственный конвейер корпорации
        manufacturing_conveyor: tools.ConveyorSettings,
        # справочник задействованных материалов
        router_materials: typing.Dict[tools.RouterSettings, tools.ConveyorRouterInputMaterials],
        # список произведённых продуктов
        products_ready: typing.Optional[typing.List[db.QSwaggerMaterial]] = None,
        # список потерянных продуктов
        products_lost: typing.Optional[typing.List[db.QSwaggerCorporationAssetsItem]] = None) -> None:
    # локальные переменные
    container_prefix: str = '<br><mute>Контейнер - </mute>'
    # список продуктов, сконвентированный для хранения разных сущностей
    products: typing.List[typing.Tuple[
        int,  # код: 0 - ready, 1 - lost
        int,  # type_id
        int,  # количество
        db.QSwaggerTypeId,  # тип продукта
        typing.Optional[typing.List[str]]  # только для lost: названия контейнеров, где обнаружены "потеряшки"
    ]] = []

    if products_ready is not None:
        products = [(0, _.material_id, _.quantity, _.material_type, None) for _ in products_ready]

    if products_lost is not None:
        # группируем ассеты по типу, чтобы получить уникальные сочетания с количествами
        grouped: typing.Dict[typing.Tuple[int, int], typing.List[db.QSwaggerCorporationAssetsItem]] = \
            tools.get_asset_items_grouped_by(
                products_lost,
                group_by_type_id=True,
                group_by_station=False)
        # сортируем уже сгруппированные чертежи
        grouped_and_sorted: typing.List[typing.Tuple[str, typing.List[db.QSwaggerCorporationAssetsItem]]] = []
        for key in grouped.keys():
            group: typing.List[db.QSwaggerCorporationAssetsItem] = grouped.get(key)
            grouped_and_sorted.append((group[0].item_type.name, group))
        grouped_and_sorted.sort(key=lambda x: x[0])
        # готовим сгруппированный набор данных
        for _, group in grouped_and_sorted:
            a0: db.QSwaggerCorporationAssetsItem = group[0]
            type_id: int = a0.type_id
            quantity: int = sum([_.quantity for _ in group])
            containers: typing.Set[str] = set()
            for a in group:
                c: db.QSwaggerCorporationAssetsItem = corporation.assets.get(a.location_id)
                containers.add(c.name if c and c.name else str(a.location_id))
            containers: typing.List[str] = sorted(containers)
            # ---
            products.append((1, type_id, quantity, a0.item_type, containers))

    for code, type_id, quantity, product_type, containers in products:
        next_factory: str = ''
        product_info_btn: str = ''
        row_class: str = 'interim-factory'
        # если список output сконфигурирован, то имеет место быть станция из настроек router-а
        for router_settings, materials in router_materials.items():
            if type_id in materials.valid_materials:
                next_factory = router_settings.station
                break
        # если список output пустой, то имеет место быть default-ная производственная база,
        # перемещаем на неё весь сток "неприкаянных" материалов с этой фабрики
        if not next_factory:
            if current_router_settings.output:
                next_factory = next((rs.station for rs in router_materials.keys() if not rs.output), '')
            else:
                row_class: str = 'last-factory'
                # анализируем состояние производства продукта (добываем информацию где он уже имеется? продаётся?)
                ma: tools.ConveyorManufacturingProductAnalysis = tools.ConveyorManufacturingProductAnalysis()
                ma.analyse_product(
                    qid,
                    product_type,
                    manufacturing_conveyor)
                pma: tools.ConveyorManufacturingAnalysis = ma.product
                # генерируем кнопку для получения информации о наличии предметов (а также их производстве)
                product_info_btn = ' ' + format_product_tier1_info_btn(pma)
                # формируем список направлений для транспортировки товара
                num_in_assets: int = pma.product_tier1_num_in_assets  # stock, output, sale_stock

                def format_trade_hub(num: int, solar_system: str, is_hub: bool) -> str:
                    # форматируем строку с информацией о транспортировке товаров
                    if num == 0:
                        res: str = '0 '
                    else:
                        res: str = f'<num>{num:,d}</num> '
                    if is_hub:
                        res += f'<hub>{solar_system}</hub>'
                    else:
                        res += f'{solar_system}'
                    return res

                # пытаемся распределить продукты по торговым хабам
                trade_hubs: typing.List[str] = []
                rest_in_assets: int = num_in_assets
                if pma.product_tier1_limits:
                    for l in pma.product_tier1_limits:
                        hub_id: int = l.trade_hub_id
                        # считаем сколько товара выставлено на продажу в этом хабе
                        hub_remain: int = sum([_.volume_remain for _ in pma.product_tier1_in_sell if _.location_id == hub_id])
                        # если на продажу в хабе выставлено больше заданного лимита - пропускаем перевозку
                        if hub_remain > l.approximate:
                            # форматируем строку с информацией о транспортировке товаров
                            trade_hubs.append(format_trade_hub(0, l.trade_hub.solar_system_name, True))
                            continue
                        # учитываем кол-во нераспределённого товара и кол-во которое надо доставить в хаб
                        num_to_hub: int = min(rest_in_assets, l.approximate - hub_remain)
                        # форматируем строку с информацией о транспортировке товаров
                        trade_hubs.append(format_trade_hub(num_to_hub, l.trade_hub.solar_system_name, True))
                        # уменьшаем кол-во нераспределённого товара
                        rest_in_assets -= num_to_hub
                        if rest_in_assets == 0: break
                # если полностью распределить товары не удалось, то выводим оставшееся нераспределённого количество
                if rest_in_assets:
                    # форматируем строку с информацией о транспортировке товаров
                    trade_hubs.append(format_trade_hub(rest_in_assets, 'др', False))
                next_factory = ', '.join(trade_hubs)

                # разделяем вывод на два типа: с выводом информацией о контейнерах и без
        if code == 0:
            glf.write(f"""<tr class="{row_class} hidden">
<td>{get_tbl_router_row_num()}</td>
<td><img class="icn16" src="{render_html.__get_img_src(type_id, 32)}"></td>
<td>{product_type.name}{product_info_btn}&nbsp;<a
data-target="#" role="button" data-tid="{type_id}" class="qind-copy-btn qind-sign" data-toggle="tooltip">{glyphicon("copy")}</a></td>
<td>{next_factory}</td>
<td>{quantity:,d}</td>
<td>{int(quantity * product_type.packaged_volume + 0.9):,d}</td>
</tr>""")
        elif code == 1:
            warn_sign: str = glyphicon_ex('warning-sign', ['lost-sign'])
            container_names: str = container_prefix.join(containers)
            glf.write(f"""<tr class="{row_class} hidden lost-assets">
<td>{get_tbl_router_row_num()}</td>
<td><img class="icn16" src="{render_html.__get_img_src(type_id, 32)}"></td>
<td>{warn_sign} {product_type.name}{product_info_btn}&nbsp;<a
data-target="#" role="button" data-tid="{type_id}" class="qind-copy-btn qind-sign" data-toggle="tooltip">{glyphicon("copy")}</a>
<label class='label label-lost-assets'>{declension_of_lost_assets(quantity)}</label>{container_prefix}{container_names}</td>
<td>{next_factory}</td>
<td>{quantity:,d}</td>
<td>{warn_sign} {int(quantity * product_type.packaged_volume + 0.9):,d}</td>
</tr>""")


def dump_list_of_ready_products(
        glf,
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        corporation: db.QSwaggerCorporation,
        # список произведённых продуктов
        products_ready: typing.List[db.QSwaggerMaterial],
        # текущие сведения роутинга на станции
        current_router_settings: tools.RouterSettings,
        # ищем производственный конвейер корпорации
        manufacturing_conveyor: tools.ConveyorSettings,
        # справочник задействованных материалов
        router_materials: typing.Dict[tools.RouterSettings, tools.ConveyorRouterInputMaterials]) -> None:
    # следующий метод вызывается независимо для products_ready, но можно его вызов не разделять
    dump_list_of_products(
        glf,
        qid,
        corporation,
        current_router_settings,
        manufacturing_conveyor,
        router_materials,
        products_ready=products_ready)


def dump_list_of_lost_products(
        glf,
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        corporation: db.QSwaggerCorporation,
        # список потерянных продуктов
        products_lost: typing.List[db.QSwaggerCorporationAssetsItem],
        # текущие сведения роутинга на станции
        current_router_settings: tools.RouterSettings,
        # ищем производственный конвейер корпорации
        manufacturing_conveyor: tools.ConveyorSettings,
        # справочник задействованных материалов
        router_materials: typing.Dict[tools.RouterSettings, tools.ConveyorRouterInputMaterials]) -> None:
    # следующий метод вызывается независимо для products_lost, но можно его вызов не разделять
    dump_list_of_products(
        glf,
        qid,
        corporation,
        current_router_settings,
        manufacturing_conveyor,
        router_materials,
        products_lost=products_lost)


def dump_corp_router(
        glf,
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        # настройки генерации отчёта
        conveyor_settings: typing.List[tools.ConveyorSettings],
        # список готовых продуктов в стоках конвейера
        ready_products: typing.Dict[tools.RouterSettings, tools.ConveyorCorporationOutputProducts],
        # справочник задействованных материалов
        ready_materials: typing.Dict[tools.RouterSettings, tools.ConveyorRouterInputMaterials]) -> None:
    # проверка, пусты ли настройки конвейера?
    if not ready_products: return

    # получаем ссылку на единственную корпорацию (странная операция...)
    corporation: db.QSwaggerCorporation = next(iter(ready_products.values())).corporation
    if not corporation:
        corporation: db.QSwaggerCorporation = next(iter(ready_materials.values())).corporation

    # проверка, принадлежат ли настройки конвейера лишь одной корпорации?
    # если нет, то... надо добавить здесь какой-то сворачиваемый список?
    corporations: typing.Set[int] = set([s.corporation.corporation_id for s in conveyor_settings])
    if not len(corporations) == 1:
        raise Exception("Unsupported mode: multiple corporations in a single conveyor")
    # получаем ссылку на единственную корпорацию
    if not corporation.corporation_id == conveyor_settings[0].corporation.corporation_id:
        raise Exception("Unsupported mode: multiple corporations in conveyor and router settings")
    # ищем производственный конвейер корпорации
    manufacturing_conveyor: tools.ConveyorSettings = next(
        (s for s in conveyor_settings if db.QSwaggerActivityCode.MANUFACTURING in s.activities), None)

    glf.write(f"""
<hr>
<h3>Маршрутизатор {corporation.corporation_name}</h3>
<table class="table table-condensed table-hover tbl-router">
<thead>
 <tr>
  <th></th><!--1-->
  <th></th><!--2-->
  <th>Продукция</th><!--3-->
  <th>След.фабрика</th><!--4-->
  <th>Кол-во</th><!--5-->
  <th>Объём</th><!--6-->
 </tr>
</thead>
<tbody>
""")
    # формируем содержимое отчёта
    router_products: typing.List[tools.ConveyorCorporationOutputProducts] = list(ready_products.values())
    router_products.sort(key=lambda x: int(x.index))
    for products in router_products:
        # определяем станцию, корпорацию и выход конвейера соответствующего роутеру
        router_settings: tools.RouterSettings = products.router_settings
        materials: tools.ConveyorRouterInputMaterials = ready_materials.get(router_settings)
        station: db.QSwaggerStation = products.station
        station_id: int = station.station_id
        sum_volume: int = int(sum([_.quantity * _.material_type.packaged_volume for _ in products.output_products.values()]) + 0.9)
        tag = {"r": station_id}
        warn_sign: str = ''

        # TODO: неуместно здесь корректировать списки, они должны изначально компоноваться правильно!
        #  (придётся объединить калькуляцию материалов и продуктов)
        products_ready: typing.List[db.QSwaggerMaterial] = list(products.output_products.values())

        # возможна ситуация, когда алгоритм среагирует на некорректное расположение asset-ов, которые и не материалы, и
        # не продукты, поэтому чтобы списки не дублировались - прореживаю уже невалидными элементами
        # также возможная ситуация, когда скажем Axosomatic Neurolink Enhancer является в конвейере и продуктом и
        # материалом, когда он точно лежит на своём месте
        products_lost: typing.List[db.QSwaggerCorporationAssetsItem] = \
            [_ for x in products.lost_products.values() for _ in x
             if _.type_id not in products.valid_products.keys()]
        products_lost_ids: typing.Set[int] = set([_.item_id for _ in products_lost])
        materials_lost: typing.List[db.QSwaggerCorporationAssetsItem] = \
            [_ for x in materials.lost_materials.values() for _ in x
             if _.type_id not in products.valid_products.keys() and _.item_id not in products_lost_ids]
        products_lost.extend(materials_lost)
        del materials_lost

        if products_ready:
            products_ready.sort(key=lambda p: (p.material_type.group_id, p.material_type.name))

        if products_lost:
            products_lost.sort(key=lambda p: (p.item_type.group_id, p.item_type.name))
            warn_sign: str = glyphicon_ex('warning-sign', ['lost-sign']) + ' '

        glf.write(f"""<tr class="row-station" {format_json_data('tag', tag)}>
<td colspan="5">{station.station_name}
<mute>({station.station_type_name}, {router_settings.desc})</mute>
<a data-target="#" role="button" class="qind-btn-hide qind-btn-hide-open">{glyphicon('eye-open')}</a></td>
<td>{warn_sign}{sum_volume:,d} m<sup>3</sup></td>
</tr>
""")

        if products_ready:
            products_ready.sort(key=lambda p: (p.material_type.group_id, p.material_type.name))
            dump_list_of_ready_products(
                glf,
                qid,
                products.corporation,
                products_ready,
                router_settings,
                manufacturing_conveyor,
                ready_materials)

        if products_lost:
            products_lost.sort(key=lambda p: (p.item_type.group_id, p.item_type.name))
            dump_list_of_lost_products(
                glf,
                qid,
                products.corporation,
                products_lost,
                router_settings,
                manufacturing_conveyor,
                ready_materials)

        del products_ready
        del products_lost

    glf.write("""
</tbody>
</table>
""")


def dump_router2_into_report(
        # путь, где будет сохранён отчёт
        ws_dir: str,
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        # настройки генерации отчёта
        router_settings: typing.List[tools.RouterSettings],
        conveyor_settings: typing.List[tools.ConveyorSettings]) -> None:
    glf = open('{dir}/router.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(
            glf,
            f'Router',
            use_dark_mode=True,
            additional_stylesheets=["render_html_conveyor.css"])
        # компоновка отчёта
        dump_nav_menu(glf)
        dump_blueprints_overflow_warn(glf, conveyor_settings)
        # инициализация справочника материалов, в которых будут хранится все используемые предметы
        global_dictionary: tools.ConveyorDictionary = tools.ConveyorDictionary(qid)
        global_dictionary.load_router_settings(router_settings)
        # инициализация списка материалов, требуемых (и уже используемых) в производстве
        available_materials: typing.Dict[tools.ConveyorSettings, tools.ConveyorCorporationStockMaterials] = \
            tools.calc_available_materials(conveyor_settings)
        global_dictionary.load_available_materials(available_materials)
        # инициализация списка продуктов, уже произведённых на станциях (и требующих перевозки)
        ready_products: typing.Dict[tools.RouterSettings, tools.ConveyorCorporationOutputProducts] = \
            tools.calc_router_products(qid, router_settings, conveyor_settings)
        global_dictionary.load_ready_products(ready_products)
        # инициализация списка материалов, требуемых всоответствии с настройками роутера
        ready_materials: typing.Dict[tools.RouterSettings, tools.ConveyorRouterInputMaterials] = \
            tools.calc_router_materials(qid, router_settings, conveyor_settings)
        # анализ чертежей на предмет перепроизводства
        # сбор данных для вывода сведений о высшем уровне конвейера
        industry_analysis: tools.ConveyorIndustryAnalysis = tools.ConveyorIndustryAnalysis()
        corp_conveyors_calcs: tools.ConveyorCalculations = tools.ConveyorCalculations()
        corp_conveyors_calcs.calc_corp_conveyors(
            qid,
            global_dictionary,
            industry_analysis,
            router_settings,
            conveyor_settings,
            available_materials)
        # инициализация списка потребностей (задача копирки), сортировка списка
        demands: typing.Optional[tools.ConveyorDemands] = None
        manufacturing_conveyor: tools.ConveyorSettings = \
            next((_ for _ in conveyor_settings if _.calculate_requirements), None)
        invent_conveyor: tools.ConveyorSettings = \
            next((_ for _ in conveyor_settings if db.QSwaggerActivityCode.INVENTION in _.activities), None)
        if manufacturing_conveyor:
            demands = tools.ConveyorDemands(
                qid,
                global_dictionary,
                conveyor_settings,
                industry_analysis,
                manufacturing_conveyor,
                invent_conveyor)
            global_dictionary.load_demands(demands)
        # компоновка высшего уровня конвейера
        dump_corp_conveyors(
            glf,
            corp_conveyors_calcs,
            industry_analysis,
            conveyor_settings)
        # компоновка маршрутизатора по факту наличия ассетов для перемещения
        dump_corp_router(
            glf,
            qid,
            conveyor_settings,
            ready_products,
            ready_materials)
        # сохраняем содержимое диалоговых окон [Станции]
        dump_nav_menu_router_dialog(
            glf,
            qid,
            global_dictionary,
            router_settings,
            conveyor_settings,
            ready_materials)
        # сохраняем содержимое диалоговых окон [Конвейер]
        dump_nav_menu_conveyor_dialog(glf, qid, conveyor_settings)
        # сохраняем содержимое диалоговых окон [Время]
        dump_nav_menu_lifetime_dialog(glf, qid)
        # сохраняем содержимое диалоговых окон [Спрос]
        dump_nav_menu_demand_dialog(glf, qid, demands, industry_analysis, conveyor_settings)
        # сохраняем содержимое диалоговых окон [<<информация о продукте>>]
        dump_industry_product_dialog(glf)
        # сохраняем справочник названий, используемых на странице конвейера
        dump_materials_to_js(glf, global_dictionary)
        glf.write(f' <script src="{render_html.__get_file_src("render_html_conveyor.js")}"></script>\n')
        render_html.__dump_footer(glf)
        # удаляем более ненужные списки
        del available_materials
        del global_dictionary
    finally:
        glf.close()
