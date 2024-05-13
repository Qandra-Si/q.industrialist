import json
import typing
import datetime
import itertools

import render_html
from render_html import get_span_glyphicon as glyphicon

import postgresql_interface as db
import eve_router_tools as tools
# from __init__ import __version__


def dump_additional_stylesheet(glf) -> None:
    glf.write("""
<style>
table.qind-blueprints-tbl > tbody > tr > td { padding: 4px; border-top: none; }

table.qind-table-materials tbody > tr > td:nth-child(2) > img /* material icon (compact view) */
{ margin-top: -2px; margin-bottom: -1px; }

table.qind-table-materials > tbody > tr > td,
table.qind-table-materials > tbody > tr > th
{ padding: 1px; font-size: smaller; }

table.qind-table-materials > tbody > tr > th,
table.qind-table-materials > tbody > tr > td:nth-child(1)
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

div.qind-bib /* blueprints interactivity block */
{ margin-left: auto; margin-right: 0; float: right; padding-top: 1px; white-space: nowrap; }

div.qind-bib a { color: #aaa; } /* material menu: gray color */
div.qind-bib a:hover { color:  #c70039; } /* material menu: dark red color */

tr.qind-em td, /* enough materials */
tr.qind-em th
{ color: #aaa; }

table.tbl-stock tr { font-size: small; }
table.tbl-stock tbody tr td:nth-child(2) img /* material icon (compact view) */
{ margin-top: -2px; margin-bottom: -1px; }
table.tbl-stock tbody tr td { padding: 1px; font-size: smaller; }
table.tbl-stock thead tr { height: 50px; }
table.tbl-stock thead tr th:nth-child(1),
table.tbl-stock tbody tr td:nth-child(1) { width: 24px; font-weight: bold; text-align: right; padding-left: 4px; }
table.tbl-stock tbody tr td:nth-child(2) { white-space: nowrap; }
table.tbl-stock thead tr th:nth-child(3),
table.tbl-stock thead tr th:nth-child(4),
table.tbl-stock thead tr th:nth-child(5),
table.tbl-stock tbody tr td:nth-child(3),
table.tbl-stock tbody tr td:nth-child(4),
table.tbl-stock tbody tr td:nth-child(5) { text-align: right; }

table.tbl-conveyor tr { font-size: small; }
table.tbl-conveyor tbody tr td { padding: 1px; font-size: smaller; }
table.tbl-conveyor thead tr th:nth-child(1),
table.tbl-conveyor tbody tr td:nth-child(1) { width: 24px; font-weight: bold; text-align: right; }
table.tbl-conveyor tbody tr td:nth-child(2) { padding-left: 4px; white-space: nowrap; }

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
mute { color: #777; }

table.tbl-summary { padding: 1px; font-size: smaller; }
table.tbl-summary thead tr th:nth-child(1),
table.tbl-summary tbody tr td:nth-child(1) { width: 24px; font-weight: bold; text-align: right; }
table.tbl-summary thead tr th:nth-child(2),
table.tbl-summary tbody tr td:nth-child(2),
table.tbl-summary thead tr th:nth-child(6),
table.tbl-summary tbody tr td:nth-child(6) { width: 32px; }
table.tbl-summary tbody tr:hover td:nth-child(3),
table.tbl-summary tbody tr.job-active:hover td:nth-child(7),
table.tbl-summary tbody tr.job-completed:hover td:nth-child(7) { border-left: 1px solid #6db09e; }
table.tbl-summary thead tr th { padding: 4px; border-bottom: 1px solid #1d3231; vertical-align: bottom; }
table.tbl-summary tbody tr td { padding: 4px; border-top: none; vertical-align: top; }
table.tbl-summary tfoot tr td { padding: 4px; border-top: 1px solid #1d3231; }
table.tbl-summary tbody tr td { border-left: 1px solid #1d3231; }
table.tbl-summary tbody tr td:nth-child(3),
table.tbl-summary tbody tr td:nth-child(7) { border-left: none; }
table.tbl-summary thead tr th:nth-child(4),
table.tbl-summary tbody tr td:nth-child(4),
table.tbl-summary thead tr th:nth-child(5),
table.tbl-summary tbody tr td:nth-child(5),
table.tbl-summary thead tr th:nth-child(8),
table.tbl-summary tbody tr td:nth-child(8) { text-align: right; }
table.tbl-summary tbody tr td:nth-child(3),
table.tbl-summary tbody tr td:nth-child(7) { white-space: nowrap; }

/* table.tbl-summary tbody tr.job-active { color: #bcbcbc; } */
table.tbl-summary tbody tr.job-active td:nth-child(6) { opacity: 0.5; }
table.tbl-summary tbody tr.job-active :is(td:nth-child(7),td:nth-child(8)) { color: #666; }
table.tbl-summary tbody tr.job-active :is(td:nth-child(7),td:nth-child(8)) mute { color: #444; }
table.tbl-summary tbody tr.job-completed td:nth-child(2) { opacity: 0.5; }
table.tbl-summary tbody tr.job-completed :is(td:nth-child(3),td:nth-child(4)) { color: #666; }
table.tbl-summary tbody tr.job-completed :is(td:nth-child(3),td:nth-child(4)) mute { color: #444; }
table.tbl-summary tbody tr.lost-blueprints { }
table.tbl-summary tbody tr.phantom-blueprints { opacity: 0.15; }
table.tbl-summary tbody tr.row-multiple,
table.tbl-summary tbody tr.row-possible,
table.tbl-summary tbody tr.row-optional,
table.tbl-summary tbody tr.row-impossible,
table.tbl-summary tbody tr td div.run-possible { }
table.tbl-summary tbody tr td div.run-optional {
 background: linear-gradient(-45deg, rgba(0, 0, 0, 0) 49.9%, #541 49.9%, #541 60%, rgba(0, 0, 0, 0) 60%) fixed,
             linear-gradient(-45deg, #541 10%, rgba(0, 0, 0, 0) 10%) fixed;
 background-size: 1em 1em
}
table.tbl-summary tbody tr td div.run-impossible {
 background: linear-gradient(-45deg, rgba(0, 0, 0, 0) 49.9%, #421 49.9%, #421 60%, rgba(0, 0, 0, 0) 60%) fixed,
             linear-gradient(-45deg, #421 10%, rgba(0, 0, 0, 0) 10%) fixed;
 background-size: 1em 1em
}

table.tbl-summary tbody tr.row-conveyor td { font-size: medium; text-align: left; background: #111b1b; border-bottom: 1px solid #111b1b; }
table.tbl-summary tbody tr.row-conveyor:hover td { border-bottom: 1px solid #6db09e; }

table.tbl-summary tbody tr td qmaterials { font-size: 85%; }
table.tbl-summary tbody tr td qmaterials qmat { border: 1px solid transparent; cursor: pointer; }
table.tbl-summary tbody tr td qmaterials qmat:hover { border: 1px dashed #6db09e; }
table.tbl-summary tbody tr td qmaterials qmat.choose { border: 1px solid #57b69f; color: #eee; background-color: #375861; }
table.tbl-summary tbody tr td qmaterials qmat.absent { border: 1px dashed #fd9700; }
table.tbl-summary tbody tr td qmaterials qmat.absent.choose { border: 1px solid #fd9700; color: #eee; background-color: #5c2d19; }

bp_tag { color: #777; }
me_tag { color: #3372b6; font-weight: bold; padding: .1em .1em .1em; border: 1px solid #383739; }
/* tid_tag { color: #777; font-size: 85%; } */

.label-active-job { background-color: #213a42; color: #ccc; }
.label-completed-job { background-color: #0f1111; color: #aaa; }
.label-phantom-blueprint { background-color: #4f351d; color: #d6a879; }
.label-lost-blueprint { background-color: #f96900; color: #111111; }

/* кнопка включения видимости контейнера */
.qind-btn-hide { opacity: 0.75; }
.qind-btn-hide:hover { opacity: 1.0; } /*d94c16 4d91cf*/
.qind-btn-hide-open { color: #23527c; }
.qind-btn-hide-open:hover { color: #337ab7; } /*d94c16 4d91cf*/
.qind-btn-hide-close { color: #66341f; }
.qind-btn-hide-close:hover { color: #d94c16; } /*d94c16 4d91cf*/
/* поведение кнопки копирования около названия декриптора */
qdecr { color: #8dc169; }
.qind-copy-btn:hover + * + qdecr { color: #ec5c5c; }
</style>
""")


def dump_materials_to_js(glf, dictionary: tools.ConveyorDictionary) -> None:
    type_id_keys = dictionary.materials
    sorted_type_id_keys = sorted(type_id_keys, key=lambda x: int(x))
    glf.write(f"""<script>
var g_sde_max_type_id={sorted_type_id_keys[-1]};
var g_sde_type_len={len(sorted_type_id_keys)};
var g_sde_type_ids=[""")
    for (idx, type_id) in enumerate(sorted_type_id_keys):
        # экранируем " (двойные кавычки), т.к. они встречаются реже, чем ' (одинарные кавычки)
        glf.write('{end}[{id},"{nm}"]'.format(
            id=type_id,
            nm=dictionary.qid.get_type_id(type_id).name.replace('"', '\\\"'),
            end=',' if idx else "\n"))
    glf.write("""
];
function getSdeItemName(t) {
 if ((t < 0) || (t > g_sde_max_type_id)) return null;
 for (var i=0; i<g_sde_type_len; ++i) {
  var ti = g_sde_type_ids[i][0];
  if (t == ti) return g_sde_type_ids[i][1];
  if (ti >= g_sde_max_type_id) break;
 }
 return null;
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


def format_num_of_num(possible: int, total: int, mute_possible: bool = True) -> str:
    if possible >= total:
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
    # округляем до 10мин, т.к. всё равно у всех навыки разные, а от обилия циферок рябит в глазах
    res: str = sec_to_timestr(min_num)
    if min_num == max_num:
        return res
    elif mute_min:
        return f'<mute>от {res} до</mute> ' + sec_to_timestr(max_num)
    else:
        return f'от {res} до ' + sec_to_timestr(max_num)


class NavMenuDefaults:
    def __init__(self):
        self.run_possible: bool = True
        self.run_impossible: bool = False
        self.lost_blueprints: bool = False
        self.phantom_blueprints: bool = False
        self.job_active: bool = False
        self.job_completed: bool = False
        # ---
        self.used_materials: bool = False
        self.not_available: bool = False

    def get(self, label: str) -> bool:
        if label == 'run-possible' or label == 'row-possible' or label == 'row-multiple' or label == 'run-optional' or label == 'row-optional':
            return self.run_possible
        elif label == 'run-impossible' or label == 'row-impossible':
            return self.run_impossible
        elif label == 'lost-blueprints':
            return self.lost_blueprints
        elif label == 'phantom-blueprints':
            return self.phantom_blueprints
        elif label == 'job-active':
            return self.job_active
        # ---
        elif label == 'used-materials':
            return self.used_materials
        elif label == 'not-available':
            return self.not_available
        else:
            raise Exception("Unsupported label to get nav menu defaults")

    def css(self, label: str, prefix: bool = True) -> str:
        opt: bool = False
        if label == 'run-possible' or label == 'row-possible' or label == 'row-multiple' or label == 'run-optional' or label == 'row-optional':
            opt = self.run_possible
        elif label == 'run-impossible' or label == 'row-impossible':
            opt = self.run_impossible
        elif label == 'lost-blueprints':
            opt = self.lost_blueprints
        elif label == 'phantom-blueprints':
            opt = self.phantom_blueprints
        elif label == 'job-active':
            opt = self.job_active
        elif label == 'job-completed':
            opt = self.job_completed
        # ---
        elif label == 'used-materials':
            opt = self.used_materials
        elif label == 'not-available':
            opt = self.not_available
        else:
            raise Exception("Unsupported label to get nav menu defaults")
        return '' if opt else (' hidden' if prefix else 'hidden')


g_nav_menu_defaults: NavMenuDefaults = NavMenuDefaults()


def dump_nav_menu(glf) -> None:
    global g_nav_menu_defaults
    menu_settings: typing.List[typing.Optional[typing.Tuple[bool, str, str]]] = [
        (g_nav_menu_defaults.run_possible,       'run-possible',       'Доступные для запуска работы'),
        (g_nav_menu_defaults.run_impossible,     'run-impossible',     'Недоступные для запуска работы'),  # btnToggleImpossible
        (g_nav_menu_defaults.lost_blueprints,    'lost-blueprints',    'Потерянные чертежи (не на своём месте)'),
        (g_nav_menu_defaults.phantom_blueprints, 'phantom-blueprints', 'Фантомные чертежи (рассогласованные)'),
        (g_nav_menu_defaults.job_active,         'job-active',         'Ведущиеся проекты'),  # btnToggleActive
        (g_nav_menu_defaults.job_completed,      'job-completed',      'Завершённые проекты'),
        None,
        (g_nav_menu_defaults.used_materials,     'used-materials',     'Используемые материалы'),  # btnToggleUsedMaterials
        (g_nav_menu_defaults.not_available,      'not-available',      'Недоступные материалы'),  # btnToggleNotAvailable
        None,
        (True, 'end-level-manuf', "Производство последнего уровня"),  # btnToggleEndLevelManuf
        (False, 'entry-level-purchasing', "Список для закупки"),  # btnToggleEntryLevelPurchasing
        (True, 'intermediate-manuf', "Материалы промежуточного производства"),  # btnToggleIntermediateManuf
        (False, 'enough-materials', "Материалы, которых достаточно"),  # btnToggleEnoughMaterials
        (False, 'assets-movement', "Список перемещений материалов"),  # btnToggleAssetsMovement
    ]
    menu_table: typing.List[typing.Optional[typing.Tuple[bool, str, str]]] = [
        (True, 'recommended-runs', "Рекомендуемое кол-во запусков"),  # btnToggleRecommendedRuns
        (False, 'planned-materials', "Кол-во запланированных материалов"),  # btnTogglePlannedMaterials
        (False, 'consumed-materials', "Рассчитанное кол-во материалов"),  # btnToggleConsumedMaterials
        (False, 'exist-in-stock', "Кол-во материалов в стоке"),  # btnToggleExistInStock
        (False, 'in-progress', "Кол-во материалов, находящихся в производстве"),  # btnToggleInProgress
    ]
    menu_sort: typing.List[typing.Tuple[bool, str, str]] = [
        (False, 'name', "Название"),  # btnSortByName
        (False, 'duration', "Длительность"),  # btnSortByDuration
        (True, 'priority', "Приоритет"),  # btnSortByPriority
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
            glf.write(f"<li><a data-target='#' role='button' class='qind-btn-settings' qind-group='{m[1]}'>{glyphicon('star')} {m[2]}</a></li>\n")
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
            glf.write(f"<li><a data-target='#' role='button' class='qind-btn-settings' qind-group='{m[1]}'>{glyphicon('star')} {m[2]}</a></li>\n")
    glf.write("""
      </ul>
    </li>
    <li><a data-target="#modalRouter" role="button" data-toggle="modal">Станции</a></li>
    <li><a data-target="#modalConveyor" role="button" data-toggle="modal">Конвейер</a></li>
   </ul>
   <form class="navbar-form navbar-right">
    <label>Сортировка:&nbsp;</label>
    <div class="btn-group" role="group" aria-label="Sort">
""")
    for m in menu_sort:
        glf.write(f"<button type='button' class='btn btn-default qind-btn-sort' qind-group='{m[1]}'>{m[2]}</button>")
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
    glf.write("</script>\n")


def dump_nav_menu_router_dialog(
        glf,
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        global_dictionary: tools.ConveyorDictionary,
        # настройки генерации отчёта
        router_settings: typing.List[tools.RouterSettings],
        conveyor_settings: typing.List[tools.ConveyorSettings]) -> None:
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
        station: db.QSwaggerStation = qid.get_station_by_name(s.station)
        containers_stocks: typing.Set[int] = set()
        corporation: typing.Optional[db.QSwaggerCorporation] = None
        for cs in conveyor_settings:
            for c in cs.containers_stocks:
                if c.station_id == station.station_id:
                    containers_stocks.add(c.container_id)
                    if corporation and not corporation == c.corporation:
                        raise Exception(f"There are multiple routes for multiple corporations {corporation.corporation_name} and {c.corporation.corporation_name}")
                    corporation = c.corporation
        # ---
        if idx > 0:
            glf.write('<hr>')
        glf.write(f"<h3 station_id='{station.station_id}'>{station.station_name} "
                  f"<small>({station.station_type_name}, {s.desc})</small>"
                  "</h3>")
        if not corporation or not containers_stocks:
            glf.write("<span style='color:#ffa600'>Внимание! Не найдены stock-контейнеры, следует проверить настройки "
                      "конвейера.</span>")
        else:
            z0 = sorted([corporation.assets.get(x).name for x in containers_stocks], key=lambda x: x)
            glf.write("<small>Сток контейнеры: <ul><li><mark>" + "</mark><li><mark>".join(z0) + "</mark></ul></small>")
        glf.write(f"""
<script>
g_tbl_stock_img_src="{render_html.__get_img_src("{tid}", 32)}";
</script>
<div class="row">
 <div class="col-md-6">
<table class="table table-condensed table-hover tbl-stock">
<thead>
 <tr>
  <th>#</th>
  <th>Продукция</th>
  <th><small>В стоке</small></th>
  <th><small>Не хватает</small></th>
  <th><small>Произво-<br>-дится</small></th>
 </tr>
</thead>
<tbody>
""")
        for product_type_id in s.output:
            row_num += 1
            product: db.QSwaggerTypeId = qid.get_type_id(product_type_id)
            if not product: continue
            quantity: int = 0
            in_progress: int = 0  # = resource_dict["j"]
            not_enough: int = 0  # = resource_dict["ne"]
            # считаем кол-во материалов в стоке
            if corporation and containers_stocks:
                for a in corporation.assets.values():
                    if a.type_id == product_type_id and a.location_id in containers_stocks:
                        quantity += a.quantity
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
        if s.output:
            # если список output сконфигурирован, то имеет место быть станция из настроек router-а
            for product_type_id in s.output:
                activities: typing.List[db.QSwaggerActivity] = qid.get_activities_by_product(product_type_id)
                if not activities: continue
                for a in activities:
                    mats: db.QSwaggerActivityMaterials = a.materials
                    for m in mats.materials:
                        materials.add(m.material_id)
        else:
            # если список output пустой, то имеет место быть default-ная производственная база,
            # выводим весь сток материалов на этой базе
            for a in corporation.assets.values():
                if a.location_id in containers_stocks:
                    materials.add(a.type_id)
        # сохраняем в глобальный справочник материалов и продуктов используемых конвейером
        global_dictionary.load_type_ids(materials)
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
            if corporation and containers_stocks:
                for a in corporation.assets.values():
                    if a.type_id == material_type_id and a.location_id in containers_stocks:
                        quantity += a.quantity
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
контейнеров должны выбираться по специальным шаблонам (см. корпоративные биллютени). В контейнерах из раздела <mark>Чертежи</mark>
должны находиться BPC или BPO для расчёта производственных процессов, процессов инвента или варки реакций. Содержимое
контейнеров из раздела <mark>Оверсток</mark> учитывается в расчётах таким образом, что непроданная продукция не будет
снова попадать в расчёт производства (даже если в контейнерах <mark>Чертежи</mark> имеются чертежи для этой продукции).
Материалы для производства будут браться в расчёт из контейнеров группы <mark>Сток</mark> (у инвента как правило свой
сток, совпадающий с расположением BPO, а у производства и реакций свой). Для расчёта промежуточных этапов производства
выбираются контейнеры из раздела <mark>Дополнительные чертежи</mark>, - следите за тем, чтобы в этот раздел не попадали
лишние названия, например персональные коробки или коробки 'Ночного цеха'.</p><hr>
""")
    row_num: int = 1
    for (idx, s) in enumerate(conveyor_settings):
        if idx:
            glf.write('<hr>')
        corporation: db.QSwaggerCorporation = s.corporation
        activities: str = ', '.join([str(_) for _ in s.activities])
        glf.write(f"<h3 corporation_id='{corporation.corporation_id}'>Конвейер {corporation.corporation_name} "
                  f"<small>{activities}</small></h3>")
        stations: typing.List[int] = list(set([x.station_id for x in s.containers_sources] +
                                              [x.station_id for x in s.containers_stocks] +
                                              [x.station_id for x in s.containers_additional_blueprints] +
                                              [x.station_id for x in s.trade_sale_stock]))
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
 <div class="col-md-4">
""")
            z: typing.List[tools.ConveyorSettingsPriorityContainer] = sorted(
                [x for x in s.containers_sources if x.station_id == station_id],
                key=lambda x: x.container_name)
            if z:
                glf.write("""
<table class="table table-condensed table-hover tbl-conveyor">
<thead><tr><th>#</th><th>Чертежи</th></tr></thead>
<tbody>""")
                for container in z:
                    glf.write(f"<tr container_id='{container.container_id}'>"
                              f"<td>{row_num}</td>"
                              f"<td>{container.container_name}</td>"
                              "</tr>")
                    row_num += 1
                glf.write("""
</tbody>
</table>""")
            glf.write("""
</div> <!-- col -->
<!-- -->
<div class="col-md-4">""")
            z: typing.List[tools.ConveyorSettingsContainer] = sorted(
                [x for x in s.containers_stocks if x.station_id == station_id],
                key=lambda x: x.container_name)
            if z:
                glf.write(f"""
<table class="table table-condensed table-hover tbl-conveyor">
<thead><tr><th>#</th><th>Сток <span style="color:#777">{corporation.corporation_name}</span></th></tr><thead>
<tbody>""")
                for container in z:
                    glf.write(f"<tr container_id='{container.container_id}'>"
                              f"<td>{row_num}</td>"
                              f"<td>{container.container_name}</td>"
                              "</tr>")
                    row_num += 1
                glf.write("</tbody></table>")
            z: typing.List[tools.ConveyorSettingsSaleContainer] = sorted(
                [x for x in s.trade_sale_stock if x.station_id == station_id],
                key=lambda x: x.container_name)
            if z:
                w0: typing.List[str] = list(set([x.trade_corporation.corporation_name for x in z]))
                w1: typing.List[str] = sorted(w0, key=lambda x: x)
                for corporation_name in w1:
                    glf.write(f"""
<table class="table table-condensed table-hover tbl-conveyor">
<thead><tr><th>#</th><th>Оверсток <span style="color:#777">{corporation_name}</span></th></tr></thead>
<tbody>""")
                    for container in z:
                        if container.trade_corporation.corporation_name == corporation_name:
                            glf.write(f"<tr container_id='{container.container_id}'>"
                                      f"<td>{row_num}</td>"
                                      f"<td style='color:#ffa600'>{container.container_name}</td>"
                                      "</tr>")
                            row_num += 1
                glf.write("</tbody></table>")
            glf.write("""
</div> <!-- col -->
<!-- -->
<div class="col-md-4">""")
            if tools.ConveyorActivity.CONVEYOR_MANUFACTURING in s.activities:
                z: typing.List[tools.ConveyorSettingsContainer] = sorted(
                    [x for x in s.containers_additional_blueprints if x.station_id == station_id],
                    key=lambda x: x.container_name)
                if z:
                    glf.write("""
<table class="table table-condensed table-hover tbl-conveyor">
<thead><tr><th>#</th><th>Дополнительные чертежи</th></tr></thead>
<tbody>""")
                    for container in z:
                        glf.write(f"<tr container_id='{container.container_id}'>"
                                  f"<td>{row_num}</td>"
                                  f"<td>{container.container_name}</td>"
                                  "</tr>")
                        row_num += 1
                    glf.write("</tbody></table>")
            glf.write("""
 </div> <!-- col -->
</div> <!-- row -->
""")
    # закрываем footer модального диалога
    render_html.__dump_any_into_modal_footer(glf)


g_tbl_summary_row_num: int = 0


def get_tbl_summary_row_num() -> int:
    global g_tbl_summary_row_num
    g_tbl_summary_row_num += 1
    return g_tbl_summary_row_num


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
        jobs: typing.List[db.QSwaggerCorporationIndustryJob],
        is_active_jobs: bool) -> None:
    # группируем работы по типу, чтобы получить уникальные сочетания с количествами
    grouped: typing.Dict[typing.Tuple[int, int], typing.List[db.QSwaggerCorporationIndustryJob]] = \
        tools.get_jobs_grouped_by(
            jobs,
            group_by_product=True,
            group_by_activity=True)
    # сортируем уже сгруппированные работы
    grouped_and_sorted: typing.List[typing.Tuple[str, int, int, typing.List[db.QSwaggerCorporationIndustryJob]]] = []
    for key in grouped.keys():
        group: typing.List[db.QSwaggerCorporationIndustryJob] = grouped.get(key)
        j0: db.QSwaggerCorporationIndustryJob = group[0]
        sum_runs: int = sum([j.runs for j in group])
        sum_products: int = sum_runs * tools.get_product_quantity(j0.activity_id, j0.product_type_id, j0.blueprint_type)
        grouped_and_sorted.append((
            j0.product_type.name,
            sum_runs,
            sum_products,
            group))
    grouped_and_sorted.sort(key=lambda x: x[0])
    # выводим в отчёт
    global g_nav_menu_defaults
    for _, sum_runs, sum_products, group in grouped_and_sorted:
        j0: db.QSwaggerCorporationIndustryJob = group[0]
        blueprint_type_id: int = j0.blueprint_type_id
        blueprint_type_name: str = j0.blueprint_type.blueprint_type.name
        product_type_id: int = j0.product_type_id
        product_type_name: str = j0.product_type.name
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
        output: str = ''
        outputs_count: int = len(set([_.output_location_id for _ in group]))
        if outputs_count == 1:
            output = f'<mute>Выход</mute> {j0.output_location.name if j0.output_location.name else j0.output_location_id}'
        else:
            output_names: str = ', '.join(
                set([_.output_location.name if _.output_location.name else str(_.output_location_id) for _ in group]))
            if len(output_names) <= 20:
                output = f'<mute>Выход</mute> {output_names}'
            else:
                output = f'<mute>Выход - </mute><a data-target="#" data-copy="{output_names}"' \
                         f' data-toggle="tooltip" class="qind-copy-btn">{outputs_count} кор</a>'
        active_label: str = ''
        if is_active_jobs:
            active_label = '<label class="label label-active-job">проект ведётся</label>'
        else:
            active_label = '<label class="label label-completed-job">проект завершён</label>'
        # <mute>Стоимость</mute> {'{:,.1f}'.format(job.cost)}
        # </me_tag><tid_tag> ({blueprint_type_id})</tid_tag>
        tr_class: str = 'job-active' if is_active_jobs else 'job-completed'
        tr_class += g_nav_menu_defaults.css(tr_class)
        glf.write(f"""<tr class="{tr_class}">
<td>{get_tbl_summary_row_num()}</td>
<td><img class="icn32" src="{render_html.__get_img_src(blueprint_type_id, 32)}"></td>
<td>{blueprint_type_name}&nbsp;<a
data-target="#" role="button" data-copy="{blueprint_type_name}" class="qind-copy-btn" data-toggle="tooltip">{glyphicon("copy")}</a>
{active_label}<br>
<mute>Число прогонов - </mute>{sum_runs}
</td>
<td>{len(group)}</td>
<td></td>
<td><img class="icn32" src="{render_html.__get_img_src(product_type_id, 32)}"></td>
<td>{product_type_name}&nbsp;<a
data-target="#" role="button" data-copy="{product_type_name}" class="qind-copy-btn qind-sign" data-toggle="tooltip">{glyphicon("copy")}</a><br>
<small>{installer} {output}</small>
</td>
<td>{sum_products}</td>
</tr>""")
    # освобождаем память
    del grouped_and_sorted
    del grouped


def dump_list_of_active_jobs(glf, active_jobs: typing.List[db.QSwaggerCorporationIndustryJob]) -> None:
    dump_list_of_jobs(glf, active_jobs, is_active_jobs=True)


def dump_list_of_completed_jobs(glf, completed_jobs: typing.List[db.QSwaggerCorporationIndustryJob]) -> None:
    dump_list_of_jobs(glf, completed_jobs, is_active_jobs=False)


def dump_list_of_lost_blueprints(
        glf,
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
        grouped_and_sorted.append((group[0].blueprint_type.blueprint_type.name, group))
    grouped_and_sorted.sort(key=lambda x: x[0])
    # локальные переменные
    container_prefix: str = '<br><mute>Контейнер - </mute>'
    # выводим в отчёт
    global g_nav_menu_defaults
    for _, group in grouped_and_sorted:
        b0: db.QSwaggerCorporationBlueprint = group[0]
        type_id: int = b0.type_id
        type_name: str = b0.blueprint_type.blueprint_type.name
        containers: typing.Set[str] = set()
        for b in group:
            c: db.QSwaggerCorporationAssetsItem = corporation.assets.get(b.location_id)
            containers.add(c.name if c and c.name else str(b.location_id))
        containers: typing.List[str] = sorted(containers)
        containers: str = container_prefix.join(containers)
        glf.write(f"""<tr class="lost-blueprints{g_nav_menu_defaults.css('lost-blueprints')}">
<td>{get_tbl_summary_row_num()}</td>
<td><img class="icn32" src="{render_html.__get_img_src(type_id, 32)}"></td>
<td>{type_name}&nbsp;<a
data-target="#" role="button" data-copy="{type_name}" class="qind-copy-btn" data-toggle="tooltip">{glyphicon("copy")}</a>
<label class="label label-lost-blueprint">{declension_of_lost_blueprints(len(group))}</label>{container_prefix}{containers}<!--
item_ids: {[_.item_id for _ in group]}--></td>
<td>{len(group)}</td>
<td></td><td></td><td></td><td></td>
</tr>""")


def dump_list_of_phantom_blueprints(
        glf,
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
        glf.write(f"""<tr class="phantom-blueprints{g_nav_menu_defaults.css('phantom-blueprints')}">
<td>{get_tbl_summary_row_num()}</td>
<td><img class="icn32" src="{render_html.__get_img_src(type_id, 32)}"></td>
<td>{type_name}&nbsp;<a
data-target="#" role="button" data-copy="{type_name}" class="qind-copy-btn" data-toggle="tooltip">{glyphicon("copy")}</a>
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
        # список чертежей и их потребности (сгруппированные и отсортированные)
        requirements: typing.List[tools.ConveyorMaterialRequirements.StackOfBlueprints]) -> None:
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
            if not tr_class:
                if not stack.enough_for_stack:
                    tr_class = 'row-impossible'
                elif stack.only_decryptors_missing_for_stack:
                    tr_class = 'row-optional'
                else:
                    tr_class = 'row-possible'
                tr_class += g_nav_menu_defaults.css(tr_class)
            elif tr_class.startswith('row-impossible'):
                if stack.enough_for_stack and stack.only_decryptors_missing_for_stack or stack.enough_for_stack:
                    tr_class = ''
                    break
            elif tr_class.startswith('row-optional'):
                if not stack.enough_for_stack or stack.enough_for_stack and not stack.only_decryptors_missing_for_stack:
                    tr_class = ''
                    break
            elif tr_class.startswith('row-possible'):
                if not stack.enough_for_stack or stack.enough_for_stack and stack.only_decryptors_missing_for_stack:
                    tr_class = ''
                    break
        if not tr_class:
            tr_class = 'row-multiple'
            tr_class += g_nav_menu_defaults.css(tr_class)

        def tr_div_class(which: str,
                         __stack784: typing.Optional[tools.ConveyorMaterialRequirements.StackOfBlueprints] = None,
                         head: typing.Optional[bool] = None) -> str:
            if which == 'tr':
                if tr_class:
                    return f' class="{tr_class}"'
            elif which == 'div':
                if head:
                    div_class: str = ('run-impossible' if not __stack784.enough_for_stack else  # нельзя запустить (нет материалов)
                                      ('run-possible' if not __stack784.only_decryptors_missing_for_stack else  # можно запустить (все материалы есть)
                                       'run-optional'))  # можно запустить (не хватает декрипторов)
                    div_class += g_nav_menu_defaults.css(div_class)
                    return f'<div class="{div_class}">'
                else:
                    return '</div>'
            return ''

        decryptor: str = ''
        m0: typing.Dict[db.QSwaggerActivity, typing.List[db.QSwaggerMaterial]] = stacks[0].required_materials_for_stack
        if len(m0) == 1:
            activity: db.QSwaggerActivity = next(iter(m0.keys()))
            if isinstance(activity, db.QSwaggerBlueprintInvention):
                d: typing.Optional[db.QSwaggerMaterial] = \
                    next((_ for _ in itertools.chain(*m0.values()) if _.material_type.market_group_id == 1873), None)
                if d:
                    decryptor = f'<mute> - модернизируй с </mute><qdecr>{d.material_type.name}</qdecr>'

        glf.write(f"""<tr{tr_div_class('tr')}>
<td>{get_tbl_summary_row_num()}</td>
<td><img class="icn32" src="{render_html.__get_img_src(type_id, 32)}"></td>
<td>{type_name}&nbsp;<a
data-target="#" role="button" data-copy="{type_name}" class="qind-copy-btn" data-toggle="tooltip">{glyphicon("copy")}</a>{decryptor}""")
        quantities: str = '<br>'
        times: str = '<br>'
        for stack in stacks:
            # TODO: здесь какая-то путаница с activity(ies)
            na = []
            js = [(_.material_type.type_id, _.quantity) for _ in itertools.chain(*stack.required_materials_for_stack.values())]
            for _ in stack.not_available_materials_for_stack.values(): na.extend(_)
            js = [(tid, q, next((_.quantity for _ in na if _.material_type.type_id == tid), 0)) for (tid, q) in js]
            # ---
            b0: db.QSwaggerCorporationBlueprint = stack.group[0]
            tt: typing.Tuple[int, int] = tools.get_min_max_time(stack)
            glf.write(f"{tr_div_class('div', stack, True)}"
                      f"{f'<mute>Копия - </mute>{str(b0.runs)}<mute> {declension_of_runs(b0.runs)}</mute>' if b0.is_copy else 'Оригинал'} "
                      f"<me_tag>{b0.material_efficiency}%</me_tag>"
                      f"<qmaterials data-arr='{json.dumps(js,separators=(',', ':'))}'></qmaterials>"
                      f"{tr_div_class('div', None, False)}")
            quantities += f"{tr_div_class('div', stack, True)}" \
                          f"{format_num_of_num(stack.max_possible_for_single, len(stack.group))}" \
                          f"{tr_div_class('div', None, False)}"
            times += f"{tr_div_class('div', stack, True)}" \
                     f"{format_time_to_time(tt[0], tt[1])}" \
                     f"{tr_div_class('div', None, False)}"
        glf.write(f"""</td>
<td>{quantities}</td>
<td>{times}</td>
<td></td><td></td><td></td>
</tr>""")


def dump_corp_conveyors(
        glf,
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        global_dictionary: tools.ConveyorDictionary,
        # настройки генерации отчёта
        router_settings: typing.List[tools.RouterSettings],
        conveyor_settings: typing.List[tools.ConveyorSettings],
        # список доступных материалов в стоках конвейеров
        available_materials: typing.Dict[tools.ConveyorSettings, tools.ConveyorCorporationStockMaterials]) -> None:
    # проверка, пусты ли настройки конвейера?
    if len(conveyor_settings) == 0: return

    # инициализируем интервал отсеивания фантомных чертежей из списка corporation blueprints
    phantom_timedelta = datetime.timedelta(hours=3)

    # проверка, принадлежат ли настройки конвейера лишь одной корпорации?
    # если нет, то... надо добавить здесь какой-то сворачиваемый список?
    corporations: typing.Set[int] = set([s.corporation.corporation_id for s in conveyor_settings])
    if not len(corporations) == 1:
        raise Exception("Unsupported mode: multiple corporations in a single conveyor")
    # получаем ссылку на единственную корпорацию
    corporation: db.QSwaggerCorporation = conveyor_settings[0].corporation
    # группируем контейнеры по приоритетам
    prioritized: typing.Dict[int, typing.Dict[tools.ConveyorSettings, typing.List[tools.ConveyorSettingsPriorityContainer]]] = {}
    for s in conveyor_settings:
        for container in s.containers_sources:
            p0 = prioritized.get(container.priority)
            if not p0:
                prioritized[container.priority] = {}
                p0 = prioritized.get(container.priority)
            p1 = p0.get(s)
            if p1:
                p1.append(container)
            else:
                p0[s] = [container]

    glf.write(f"""
<h2>Конвейер {corporation.corporation_name}</h2>
<hr>
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

    # перебираем сгруппированные преоритизированные группы
    for priority in sorted(prioritized.keys()):
        p0 = prioritized.get(priority)
        for settings in p0.keys():
            # сведения для java-script с информацией о коробках конвейера (приоритет и activity)
            tag = {"p": priority, "a": [_.to_int() for _ in settings.activities]}
            # получаем список контейнеров с чертежами для производства
            containers: typing.List[tools.ConveyorSettingsPriorityContainer] = p0.get(settings)
            container_ids: typing.Set[int] = set([_.container_id for _ in containers])
            glf.write(f"""<tr class="row-conveyor" data-tag='{json.dumps(tag,separators=(',', ':')).replace("'",'"')}'>
<td colspan="8">Приоритет {priority}
<mute>{', '.join([str(_) for _ in settings.activities])}</mute>
<a data-target="#" role="button" class="qind-btn-hide qind-btn-hide-open">{glyphicon('eye-open')}</a>
</td>
</tr>
""")
            """
            glf.write(f"containers: {[f'{_.container_id}:<mark>{_.container_name}</mark>' for _ in containers]}<br>")
            """
            # получаем список чертежей, находящихся в этих контейнерах
            blueprints: typing.List[db.QSwaggerCorporationBlueprint] = \
                [b for b in corporation.blueprints.values() if b.location_id in container_ids]
            # проверяем текущие работы (запущенные из этих контейнеров),
            # если чертёж находится в активных работах, то им пользоваться нельзя
            active_jobs: typing.List[db.QSwaggerCorporationIndustryJob] = \
                [j for j in corporation.industry_jobs_active.values() if j.blueprint_location_id in container_ids]
            # также, если чертёж находится в завершённых работах, то им тоже пользоваться нельзя
            completed_jobs: typing.List[db.QSwaggerCorporationIndustryJob] = \
                [j for j in corporation.industry_jobs_completed.values() if j.blueprint_location_id in container_ids]
            # составляем новый (уменьшенный) список тех чертежей, запуск которых возможен
            active_blueprint_ids: typing.Set[int] = \
                set([j.blueprint_id for j in active_jobs])
            """
            completed_blueprint_ids: typing.Set[int] = \
                set([j.blueprint_id for j in completed_jobs if j.blueprint_id not in active_blueprint_ids])
            # фильтруем список завершённых работ, удаляя из него использующиеся прямо сейчас чертежи
            # (один и тот же чертёж мог быть запущен, выполнен, и снова запущен и выполняться прямо сейчас повторно)
            completed_jobs: typing.List[db.QSwaggerCorporationIndustryJob] = \
                [j for j in completed_jobs if j.blueprint_id not in active_blueprint_ids]
            """
            # отсеиваем те чертежи, которые не подходят к текущей activity конвейера
            possible_blueprints: typing.List[db.QSwaggerCorporationBlueprint] = []
            lost_blueprints: typing.List[db.QSwaggerCorporationBlueprint] = []
            for b in blueprints:
                possible: bool = False
                lost: bool = False
                for _a in settings.activities:
                    a: tools.ConveyorActivity = _a
                    if b.is_copy and a in (tools.ConveyorActivity.CONVEYOR_RESEARCH_TIME,
                                           tools.ConveyorActivity.CONVEYOR_RESEARCH_MATERIAL):
                        lost, possible = True, False
                        break
                    activity = b.blueprint_type.get_activity(activity_id=a.to_int())
                    if activity:
                        if b.item_id not in active_blueprint_ids:
                            possible = True
                    else:
                        lost = True
                if possible:
                    possible_blueprints.append(b)
                elif lost:
                    lost_blueprints.append(b)
            # 2024-05-07 выяснилась проблема: CCP отдают отчёт со сведениями о чертежах в котором чертёж есть,
            # и отдают его 2 дня подряд... а в коробке (в игре) чертежа на самом деле нет, в отчёте с ассетами
            # чертежа тоже нет, ...вот такие фантомные чертежи мешаются в процессе расчётов (фильтрую чертежи более
            # актуальными ассетами)
            phantom_blueprints: typing.List[db.QSwaggerCorporationBlueprint] = []
            if possible_blueprints:
                # внимание! для поиска фантомных чертежей ассеты должны загружаться вместе с чертежами, т.е.
                # при загрузке ассетов надо использовать флаг load_asseted_blueprints=True
                phantom_blueprint_ids: typing.Set[int] = set()
                for p in possible_blueprints:
                    a: db.QSwaggerCorporationAssetsItem = corporation.assets.get(p.item_id)
                    if a is not None: continue
                    # если в ассетах чертежа нет, то это плохой признак
                    # надо решать дилемму: чертежа уже нет, или всё ещё нет?
                    b: db.QSwaggerCorporationBlueprint = corporation.blueprints.get(p.item_id)
                    if (b.updated_at + phantom_timedelta) < qid.eve_now:
                        phantom_blueprint_ids.add(b.item_id)
                        phantom_blueprints.append(b)
                # корректируем составляем список возможных к постройке чертежей
                if phantom_blueprint_ids:
                    possible_blueprints: typing.List[db.QSwaggerCorporationBlueprint] = \
                        [b for b in possible_blueprints if b.item_id not in phantom_blueprint_ids]
                del phantom_blueprint_ids
            # составляем список "залётных" чертежей, которые упали не в ту коробку
            if lost_blueprints:
                lost_blueprints: typing.List[db.QSwaggerCorporationBlueprint] = \
                    [b for b in lost_blueprints if b.item_id not in active_blueprint_ids]
            """
            glf.write(f"<h4>blueprints</h4>{[_.item_id for _ in blueprints]}<br>"
                      f"<h4>active_blueprint_ids</h4>{active_blueprint_ids}<br>"
                      f"<h4>completed_blueprint_ids</h4>{completed_blueprint_ids}<br>"
                      f"<h4>used_blueprint_ids</h4>{used_blueprint_ids}<br>"
                      f"<h4>phantom_blueprints</h4>{[_.item_id for _ in phantom_blueprints]}<br>"
                      f"<h4>possible_blueprints</h4>{[_.item_id for _ in possible_blueprints]}<br>"
                      f"<h4>lost_blueprints</h4>{[_.item_id for _ in lost_blueprints]}<br>")
            """
            # если чертежей для продолжения расчётов нет (коробки пустые), то пропускаем приоритет
            if possible_blueprints:
                # получаем количество материалов в стоке выбранного конвейера
                stock_materials: tools.ConveyorCorporationStockMaterials = available_materials.get(settings)
                # считаем потребности конвейера
                requirements: typing.List[tools.ConveyorMaterialRequirements.StackOfBlueprints] = tools.calc_corp_conveyor(
                    # данные (справочники)
                    qid,
                    # настройки генерации отчёта
                    router_settings,
                    settings,
                    # ассеты стока (материалы для расчёта возможностей и потребностей конвейера
                    stock_materials,
                    # список чертежей, которые необходимо обработать
                    possible_blueprints)
                # выводим в отчёт
                dump_list_of_possible_blueprints(glf, requirements)
            # вывести информацию о работах, которые прямо сейчас ведутся с чертежами в коробке конвейера
            if active_jobs:
                dump_list_of_active_jobs(
                    glf,
                    active_jobs)  # [b for b in blueprints if b.item_id in active_blueprint_ids]
            # вывести информацию о работах, которые прямо недавно закончились
            if completed_jobs:
                dump_list_of_completed_jobs(
                    glf,
                    completed_jobs)  # [b for b in blueprints if b.item_id in completed_blueprint_ids]
            # если в коробке застряли чертежи которых там не должно быть, то выводим об этом сведения
            if lost_blueprints:
                dump_list_of_lost_blueprints(
                    glf,
                    corporation,
                    lost_blueprints)
            # возможно появление корпоративных чертежей, которых нет в ассетах (приём довольно длительное время)
            if phantom_blueprints:
                dump_list_of_phantom_blueprints(
                    glf,
                    phantom_blueprints)
        # удаление списков найденных чертежей, предметов и работ
        del phantom_blueprints
        del possible_blueprints
        del lost_blueprints
        del active_blueprint_ids
        del completed_jobs
        del active_jobs
        del blueprints

    glf.write(f"""
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
        render_html.__dump_header(glf, f'Router', use_dark_mode=True)
        # компоновка отчёта
        dump_additional_stylesheet(glf)
        dump_nav_menu(glf)
        dump_blueprints_overflow_warn(glf, conveyor_settings)
        # инициализация справочника материалов, в которых будут хранится все используемые предметы
        global_dictionary: tools.ConveyorDictionary = tools.ConveyorDictionary(qid)
        global_dictionary.load_router_settings(router_settings)
        # инициализация списка материалов, требуемых (и уже используемых) в производстве
        available_materials: typing.Dict[tools.ConveyorSettings, tools.ConveyorCorporationStockMaterials] = \
            tools.calc_available_materials(conveyor_settings)
        # компоновка высшего уровня конвейера
        dump_corp_conveyors(
            glf,
            qid,
            global_dictionary,
            router_settings,
            conveyor_settings,
            available_materials)
        # сохраняем содержимое диалоговых окон
        dump_nav_menu_router_dialog(glf, qid, global_dictionary, router_settings, conveyor_settings)
        dump_nav_menu_conveyor_dialog(glf, qid, conveyor_settings)
        dump_materials_to_js(glf, global_dictionary)
        glf.write(f' <script src="{render_html.__get_file_src("render_html_conveyor.js")}"></script>\n')
        render_html.__dump_footer(glf)
        # удаляем более ненужные списки
        del available_materials
        del global_dictionary
    finally:
        glf.close()
