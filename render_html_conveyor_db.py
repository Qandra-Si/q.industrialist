import typing

import render_html
import eve_conveyor_tools
from render_html import get_span_glyphicon as glyphicon

import postgresql_interface as db
from __init__ import __version__


class RouterSettings:
    def __init__(self):
        # параметры работы конвейера
        self.station: str = ''
        self.desc: str = ''
        self.output: typing.List[int] = []


class ConveyorSettingsContainer:
    def __init__(self, corporation: db.QSwaggerCorporation, container: db.QSwaggerCorporationAssetsItem):
        self.corporation: db.QSwaggerCorporation = corporation
        self.container: db.QSwaggerCorporationAssetsItem = container
        self.station_id: typing.Optional[int] = container.station_id

    @property
    def container_id(self) -> int:
        return self.container.item_id

    @property
    def container_name(self) -> str:
        return self.container.name


class ConveyorSettingsPriorityContainer(ConveyorSettingsContainer):
    def __init__(self, priority: int, corporation: db.QSwaggerCorporation, container: db.QSwaggerCorporationAssetsItem):
        super().__init__(corporation, container)
        self.priority: int = priority


class ConveyorSettingsSaleContainer(ConveyorSettingsContainer):
    def __init__(self, trade_corporation: db.QSwaggerCorporation, container: db.QSwaggerCorporationAssetsItem):
        super().__init__(trade_corporation, container)
        self.trade_corporation: db.QSwaggerCorporation = trade_corporation


class ConveyorSettings:
    def __init__(self, corporation: db.QSwaggerCorporation):
        # параметры работы конвейера
        self.corporation: db.QSwaggerCorporation = corporation
        self.fixed_number_of_runs: typing.Optional[int] = None
        self.same_stock_container: bool = False
        self.activities: typing.List[str] = ['manufacturing']
        self.conveyor_with_reactions: bool = False
        # идентификаторы контейнеров с чертежами, со стоком, с формулами, исключённых из поиска и т.п.
        self.containers_sources: typing.List[ConveyorSettingsPriorityContainer] = []  # station:container:priority
        self.containers_stocks: typing.List[ConveyorSettingsContainer] = []  # station:container
        self.containers_additional_blueprints: typing.List[ConveyorSettingsContainer] = []  # station:container
        self.containers_react_formulas: typing.List[int] = []
        self.containers_react_stock: typing.List[int] = []
        self.manufacturing_groups: typing.Optional[typing.List[int]] = []
        # параметры поведения конвейера (связь с торговой деятельностью, влияние её поведения на работу произвдства)
        self.trade_sale_stock: typing.List[ConveyorSettingsSaleContainer] = []  # station:container:trade_corporation


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

#tblStock tr { font-size: small; }
#tbl-stock tr { font-size: small; }
#tbl-stock tbody tr td:nth-child(2) img /* material icon (compact view) */
{ margin-top: -2px; margin-bottom: -1px; }
#tbl-stock tbody tr td { padding: 1px; font-size: smaller; }
#tbl-stock thead tr { height: 50px; }
#tbl-stock thead tr th:nth-child(1),
#tbl-stock tbody tr td:nth-child(1) { width: 24px; font-weight: bold; text-align: right; padding-left: 4px; }
#tbl-stock tbody tr td:nth-child(2) { white-space: nowrap; }
#tbl-stock thead tr th:nth-child(3),
#tbl-stock thead tr th:nth-child(4),
#tbl-stock thead tr th:nth-child(5),
#tbl-stock tbody tr td:nth-child(3),
#tbl-stock tbody tr td:nth-child(4),
#tbl-stock tbody tr td:nth-child(5) { text-align: right; }

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
</style>
""")


def dump_nav_menu(glf) -> None:
    menu_settings: typing.List[typing.Optional[typing.Tuple[bool, str, str]]] = [
        (True, 'impossible', 'Недоступные для запуска работы'),  # btnToggleImpossible
        (False, 'active', "Запущенные работы"),  # btnToggleActive
        None,
        (False, 'used-materials', "Используемые материалы"),  # btnToggleUsedMaterials
        (True, 'not-available', "Недоступные материалы"),  # btnToggleNotAvailable
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
        qid: db.QSwaggerDictionary,
        router_settings: typing.List[RouterSettings],
        conveyor_settings: typing.List[ConveyorSettings]) -> None:
    # создаём заголовок модального окна, где будем показывать список имеющихся материалов в контейнере "..stock ALL"
    render_html.__dump_any_into_modal_header_wo_button(
        glf,
        "Распределение производства по станциям",
        unique_id="Router",
        modal_size="modal-lg")
    # формируем содержимое модального диалога
    row_num: int = 0
    for (idx, s) in enumerate(router_settings):
        station: db.QSwaggerStation = qid.get_station_by_name(s.station)
        if idx > 0:
            glf.write('<hr>')
        containers_stocks: typing.Set[int] = set()
        corporation: typing.Optional[db.QSwaggerCorporation] = None
        for cs in conveyor_settings:
            for c in cs.containers_stocks:
                if c.station_id == station.station_id:
                    containers_stocks.add(c.container_id)
                    if corporation and not corporation == c.corporation:
                        raise Exception(f"There are multiple routes for multiple corporations {corporation.corporation_name} and {c.corporation.corporation_name}")
                    corporation = c.corporation
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
<div class="row">
 <div class="col-md-6">
<table id="tbl-stock" class="table table-condensed table-hover">
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
            quantity: int = 0  # resource_dict["q"]
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
            copy2clpbrd = '&nbsp;<a data-target="#" role="button" data-tid="{tid}" class="qind-copy-btn qind-sign"' \
                          ' data-toggle="tooltip">{gly}</a>'.format(tid=product_type_id, gly=glyphicon("copy"))
            glf.write(
                '<tr>'
                '<td scope="row">{num}</td>'
                '<td data-nm="{nm}"><img class="icn24" src="{src}"> {nm}{clbrd}{mat_tag}</td>'
                '<td>{q}</td>'
                '<td>{ne}</td>'
                '<td>{ip}</td>'
                '</tr>\n'.
                format(num=row_num,
                       nm=product.name,
                       src=render_html.__get_img_src(product_type_id, 32),
                       clbrd=copy2clpbrd,
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
<table id="tbl-stock" class="table table-condensed table-hover">
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
        for product_type_id in s.output:
            activities: typing.List[db.QSwaggerActivity] = qid.get_activities_by_product(product_type_id)
            if not activities: continue
            for a in activities:
                mats: db.QSwaggerActivityMaterials = a.materials
                for m in mats.materials:
                    materials.add(m.material_id)
        for __sort_key, material_type_id in sorted([(qid.get_type_id(x).market_group_id, x) for x in materials]):
            material: db.QSwaggerTypeId = qid.get_type_id(material_type_id)
            quantity: int = 0  # resource_dict["q"]
            not_enough: int = 0  # = resource_dict["ne"]
            # считаем кол-во материалов в стоке
            if corporation and containers_stocks:
                for a in corporation.assets.values():
                    if a.type_id == material_type_id and a.location_id in containers_stocks:
                        quantity += a.quantity
            copy2clpbrd = '&nbsp;<a data-target="#" role="button" data-tid="{tid}" class="qind-copy-btn qind-sign"' \
                          ' data-toggle="tooltip">{gly}</a>'.format(tid=material_type_id, gly=glyphicon("copy"))
            glf.write(
                '<tr>'
                '<td scope="row">{num}</td>'
                '<td data-nm="{nm}"><img class="icn24" src="{src}"> {nm}{clbrd}</td>'
                '<td>{q}</td>'
                '<td>{ne}</td>'
                '</tr>\n'.
                format(num=row_num,
                       nm=material.name,
                       src=render_html.__get_img_src(material_type_id, 32),
                       clbrd=copy2clpbrd,
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
        qid: db.QSwaggerDictionary,
        conveyor_settings: typing.List[ConveyorSettings]) -> None:
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
        activities: str = ', '.join(s.activities)
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
            z: typing.List[ConveyorSettingsPriorityContainer] = sorted(
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
            z: typing.List[ConveyorSettingsContainer] = sorted(
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
            z: typing.List[ConveyorSettingsSaleContainer] = sorted(
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
            if 'manufacturing' in s.activities:
                z: typing.List[ConveyorSettingsContainer] = sorted(
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


def dump_blueprints_overflow_warn(
        glf,
        # настройки генерации отчёта
        conveyor_settings: typing.List[ConveyorSettings]) -> None:
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


def dump_corp_conveyors(
        glf,
        # настройки генерации отчёта
        router_settings: typing.List[RouterSettings],
        conveyor_settings: typing.List[ConveyorSettings]) -> None:
    pass

def dump_router2_into_report(
        # путь, где будет сохранён отчёт
        ws_dir: str,
        # данные (справочники)
        qid: db.QSwaggerDictionary,
        # настройки генерации отчёта
        router_settings: typing.List[RouterSettings],
        conveyor_settings: typing.List[ConveyorSettings]) -> None:
    glf = open('{dir}/router.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(glf, f'Router', use_dark_mode=True)
        dump_additional_stylesheet(glf)
        dump_nav_menu(glf)
        dump_blueprints_overflow_warn(glf, conveyor_settings)
        # инициализация списка материалов, требуемых (и уже используемых) в производстве
        """global_materials_dictionary = eve_conveyor_tools.ConveyorDictionary()"""
        dump_corp_conveyors(
            glf,
            router_settings,
            conveyor_settings)
        # сохраняем в отчёт справочник названий, кодов и сведений о производстве
        """dump_global_materials_dictionary(glf, global_materials_dictionary)
        # del global_materials_dictionary"""
        # сохраняем содержимое диалоговых окон
        dump_nav_menu_router_dialog(glf, qid, router_settings, conveyor_settings)
        dump_nav_menu_conveyor_dialog(glf, qid, conveyor_settings)
        glf.write(f' <script src="{render_html.__get_file_src("render_html_conveyor.js")}"></script>\n')
        # удаляем более ненужный список материалов
        render_html.__dump_footer(glf)
    finally:
        glf.close()
