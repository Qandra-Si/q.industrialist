import render_html
import q_blueprints_settings


def __dump_corp_blueprints_sales(
        glf,
        corps_blueprints):
    __corp_keys = corps_blueprints.keys()
    # составляем список locations, где могут лежать чертежи, с тем чтобы сделать возможность группировать их по locations
    used_location_names = []
    for corporation_id in __corp_keys:
        if not (int(corporation_id) in q_blueprints_settings.g_sale_of_blueprint["corporation_id"]):
            continue
        __corp = corps_blueprints[str(corporation_id)]
        # название станций и звёздных систем
        __loc_keys = __corp["locations"].keys()
        for __loc_key in __loc_keys:
            __loc_dict = __corp["locations"][str(__loc_key)]
            if "station" in __loc_dict:
                __location_name = __loc_dict["station"]
            elif "solar" in __loc_dict:
                __location_name = __loc_dict["solar"]
            else:
                __location_name = __loc_key
            __used_name = next((n for n in used_location_names if n['name'] == __location_name), None)
            # определяем ангары, где лежат чертёжи
            for __blueprint_dict in __corp["blueprints"]:
                if __blueprint_dict["loc"] != int(__loc_key):
                    continue
                if "st" in __blueprint_dict:  # пропускаем чертежы, над которым выполяются какие-либо работы
                    continue
                if "cntrct_sta" in __blueprint_dict:  # пропускаем places из контрактов (там не ангары, а ingame комментарии)
                    continue
                __type_id = __blueprint_dict["type_id"]
                if not (__used_name is None):  # в окно sales чертежи одного типа многократно не добавляются
                    if __used_name["types"].count(__type_id) > 0:
                        continue
                __blueprint_id = __blueprint_dict["item_id"]
                __place = __blueprint_dict["flag"]
                if __place[:-1] == "CorpSAG":
                    __place = 'Hangar {}'.format(__place[-1:])  # Corp Security Access Group
                # добавляем в список обнаруженных мест, локацию с ангарами (исключая локации только с контрактами)
                if __used_name is None:
                    __used_name = {"name": __location_name, "places": [__place], "ids": [], "types": []}
                    used_location_names.append(__used_name)
                elif __used_name["places"].count(__place) == 0:
                    __used_name["places"].append(__place)
                __used_name["ids"].append(__blueprint_id)
                __used_name["types"].append(__type_id)
            if not (__used_name is None):
                __used_name["places"].sort()
    used_location_names = sorted(used_location_names, key=lambda x: x['name'])

    # формируем dropdown список, где можон будет выбрать локации и ангары
    glf.write("""
<div id="ddSales" class="dropdown">
  <button class="btn btn-default dropdown-toggle" type="button" id="ddSalesMenu" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">
    <span class="qind-lb-dd">Choose Place&hellip;</span>
    <span class="caret"></span>
  </button>
  <ul class="dropdown-menu" aria-labelledby="dropdownMenu1">
""")
    first_time = True
    for __used_name in used_location_names:
        if not first_time:
            glf.write('<li role="separator" class="divider"></li>\n')
        first_time = False
        glf.write('<li class="dropdown-header">{nm}</li>\n'.format(nm=__used_name["name"]))
        for __place in __used_name["places"]:
            glf.write('<li><a href="#" loc="{nm}">{pl}</a></li>\n'.format(nm=__used_name["name"], pl=__place))
    glf.write("""
  </ul>
</div>

<style>
#tblSales tr {
  font-size: small;
}
</style>

<div class="table-responsive">
 <table id="tblSales" class="table table-condensed table-hover">
<thead>
 <tr>
  <th>#</th>
  <th>Blueprint</th>
  <th class="hidden"></th>
  <th class="hidden"></th>
  <th>Price</th>
  <th>Contract</th>
 </tr>
</thead>
<tbody>
""")

    row_num = 1
    for corporation_id in __corp_keys:
        if not (int(corporation_id) in q_blueprints_settings.g_sale_of_blueprint["corporation_id"]):
            continue
        __corp = corps_blueprints[str(corporation_id)]
        __loc_keys = __corp["locations"].keys()
        for __loc_key in __loc_keys:
            __loc_dict = __corp["locations"][str(__loc_key)]
            if "station" in __loc_dict:
                __location_name = __loc_dict["station"]
            elif "solar" in __loc_dict:
                __location_name = __loc_dict["solar"]
            else:
                __location_name = __loc_key
            __used_name = next((n for n in used_location_names if n['name'] == __location_name), None)
            if __used_name is None:
                continue
            # определяем ангары, где лежат чертёжи
            __corp_blueprints = __corp["blueprints"]
            for __blueprint_dict in __corp_blueprints:
                if not __blueprint_dict["item_id"] in __used_name["ids"]:
                    continue
                __place = __blueprint_dict["flag"]
                if __place[:-1] == "CorpSAG":
                    __place = 'Hangar {}'.format(__place[-1:])  # Corp Security Access Group
                __me = __blueprint_dict["me"]
                __te = __blueprint_dict["te"]
                __copy = __blueprint_dict["copy"]
                __type_id = __blueprint_dict["type_id"]
                __price = ""
                # выясняем сколько стоит чертёж?
                if "base_price" in __blueprint_dict:
                    __price = '{cost:,.1f} <sup class="qind-price-tag"><span class="label label-default">B</span></sup>'.format(cost=__blueprint_dict["base_price"])
                elif "average_price" in __blueprint_dict:
                    __price = '{cost:,.1f} <sup class="qind-price-tag"><span class="label label-primary">A</span></sup>'.format(cost=__blueprint_dict["average_price"])
                elif "adjusted_price" in __blueprint_dict:
                    __price = '{cost:,.1f} <sup class="qind-price-tag"><span class="label label-info">J</span></sup>'.format(cost=__blueprint_dict["adjusted_price"])
                # выясняем список текущих контрактов по чертежу
                __contracts = [b for b in __corp_blueprints if (b['type_id'] == __type_id) and ("cntrct_sta" in b)]

                __contracts_summary = ""
                for __cntrct_dict in __contracts:
                    # [ unknown, item_exchange, auction, courier, loan ]
                    __blueprint_status = __cntrct_dict["cntrct_typ"]
                    __status = '&nbsp;<span class="label label-default">{}</span>'.format(__blueprint_status)
                    # [ outstanding, in_progress, finished_issuer, finished_contractor, finished, cancelled, rejected, failed, deleted, reversed ]
                    __blueprint_contract_activity = __cntrct_dict["cntrct_sta"]
                    if __blueprint_contract_activity in ["outstanding", "finished_issuer", "finished_contractor", "reversed"]:
                        __activity = '&nbsp;<span class="label label-warning">{}</span>'.format(__blueprint_contract_activity)
                    elif __blueprint_contract_activity in ["in_progress"]:
                        __activity = '&nbsp;<span class="label label-success">{}</span>'.format(__blueprint_contract_activity)
                    else:
                        __activity = '&nbsp;<span class="label label-danger">{}</span>'.format(__blueprint_contract_activity)
                    # issuer
                    __issuer = '&nbsp;<a href="https://evewho.com/character/{id}" target="_blank">{nm}</a>'. \
                               format(id=__cntrct_dict["cntrct_issuer"],nm=__cntrct_dict["cntrct_issuer_name"])
                    # summary по контракту
                    if __contracts_summary:
                        __contracts_summary += '</br>\n'
                    __contracts_summary += \
                        '{prc:,.1f}{st}{act}{iss}'. \
                        format(prc=__cntrct_dict["price"],
                               st=__status,
                               act=__activity,
                               iss=__issuer)
                # формируем строку таблицы - найден нужный чертёж в ассетах
                glf.write(
                    '<tr>'
                    '<th scope="row">{num}</th>'
                    '<td>{nm} <span class="label label-{lbclr}">{me} {te}{cp}</span></td>'
                    '<td class="hidden">{loc}</td>'
                    '<td class="hidden">{pl}</td>'
                    '<td align="right">{prc}</td>'
                    '<td>{cntrct}</td>'
                    '</tr>\n'.
                    format(num=row_num,
                           nm=__blueprint_dict["name"],
                           me=__me,
                           te=__te,
                           cp='&nbsp;<span class="label label-copy">copy</span>' if __copy else '',
                           lbclr="success" if (__me == 10) and (__te == 20) else "warning",
                           loc=__location_name,
                           pl=__place,
                           prc=__price,
                           cntrct=__contracts_summary)
                )
                row_num = row_num + 1

    glf.write("""
</tbody>     
 </table>
</div>     
""")


def __dump_corp_blueprints_tbl(
        glf,
        corps_blueprints):
    __corp_keys = corps_blueprints.keys()
    # составляем список locations, где могут лежать чертежи, с тем чтобы сделать возможность группировать их по locations
    used_location_names = []
    for corporation_id in __corp_keys:
        __corp = corps_blueprints[str(corporation_id)]
        __loc_keys = __corp["locations"].keys()
        for __loc_key in __loc_keys:
            __loc_dict = __corp["locations"][str(__loc_key)]
            if "station" in __loc_dict:
                __location_name = __loc_dict["station"]
            elif "solar" in __loc_dict:
                __location_name = __loc_dict["solar"]
            else:
                __location_name = __loc_key
            if used_location_names.count(__location_name) == 0:
                used_location_names.append(__location_name)
    used_location_names.sort()

    glf.write("""
<style>
.dropdown-submenu {
  position: relative;
}
.dropdown-submenu .dropdown-menu {
  top: 0;
  left: 100%;
  margin-top: -1px;
}
.btn.btn-default:disabled{
  color: #aaa;
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
   <a class="navbar-brand" data-target="#"><span class="glyphicon glyphicon-duplicate" aria-hidden="true"></span></a>
  </div>

  <div class="collapse navbar-collapse" id="bs-navbar-collapse">
   <ul class="nav navbar-nav">
    <li class="dropdown">
     <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Display Options <span class="caret"></span></a>
      <ul class="dropdown-menu">
       <li class="dropdown-submenu">
         <a class="options-submenu" data-target="#" role="button">Industry jobs <mark id="lbSelJob"></mark><span class="caret"></span></a>
         <ul class="dropdown-menu">
           <li class="dropdown-header">[Industry activities]</li>
           <li><a id="btnSelJob" job="1" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star qind-img-seljob" aria-hidden="true" job="1"></span> Manufacturing only</a></li>
           <li><a id="btnSelJob" job="3" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star qind-img-seljob" aria-hidden="true" job="3"></span> Research TE &amp; ME only</a></li>
           <li><a id="btnSelJob" job="5" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star qind-img-seljob" aria-hidden="true" job="5"></span> Copying only</a></li>
           <li><a id="btnSelJob" job="7" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star qind-img-seljob" aria-hidden="true" job="7"></span> Reverse Engineering only</a></li>
           <li><a id="btnSelJob" job="8" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star qind-img-seljob" aria-hidden="true" job="8"></span> Invention only</a></li>
           <li><a id="btnSelJob" job="9" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star qind-img-seljob" aria-hidden="true" job="9"></span> Reactions only</a></li>
           <li role="separator" class="divider"></li>
           <li><a id="btnSelJob" job="12" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star qind-img-seljob" aria-hidden="true" job="12"></span> Show all</a></li>
           <li><a id="btnSelJob" job="13" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star qind-img-seljob" aria-hidden="true" job="13"></span> Hide all</a></li>
           <li role="separator" class="divider"></li>
           <li><a id="btnToggleUnusedBlueprints" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowUnusedBlueprints"></span> Show unused blueprints</a></li>
         </ul>
       </li>

       <li><a id="btnTogglePriceVals" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowPriceVals"></span> Show Price column</a></li>
       <li><a id="btnTogglePriceTags" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowPriceTags"></span> Show Price tags</a></li>
       <li><a id="btnTogglePlace" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowPlace"></span> Show Place column</a></li>
       <li><a id="btnToggleBox" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowBox"></span> Show Box column</a></li>
       <li><a id="btnToggleOut" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowOut"></span> Show Output Box column</a></li>
       <li class="dropdown-submenu">
         <a class="options-submenu" data-target="#" role="button">Show by Types <mark id="lbSelBPx"></mark><span class="caret"></span></a>
         <ul class="dropdown-menu">
           <li class="dropdown-header">[Blueprint Types]</li>
           <li><a id="btnSelBPx" copy="0" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star qind-img-selbpx" aria-hidden="true" copy="0"></span> Originals only</a></li>
           <li><a id="btnSelBPx" copy="1" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star qind-img-selbpx" aria-hidden="true" copy="1"></span> Copies only</a></li>
           <li role="separator" class="divider"></li>
           <li><a id="btnSelBPx" copy="2" class="option" data-target="#" role="button"><span class="glyphicon glyphicon-star qind-img-selbpx" aria-hidden="true" copy="2"></span> Show all</a></li>
         </ul>
       </li>

       <li role="separator" class="divider"></li>
       <li><a id="btnToggleShowContracts" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowContracts"></span> Show Contracts</a></li>
       <li><a id="btnToggleShowFinishedContracts" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowFinishedContracts"></span> Show Finished Contracts</a></li>
       <li role="separator" class="divider"></li>
       <li><a id="btnToggleExpand" data-target="#" role="button">Expand all tables</a></li>
       <li><a id="btnToggleCollapse" data-target="#" role="button">Collapse all tables</a></li>
       <li><a id="btnToggleLegend" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowLegend"></span> Show Legend</a></li>
       <li role="separator" class="divider"></li>
       <li><a id="btnResetOptions" data-target="#" role="button">Reset options</a></li>
      </ul>
    </li>
    
    <li class="dropdown">
     <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Locations <span class="caret"></span></a>
      <ul class="dropdown-menu">
""")
    for loc_name in used_location_names:
        glf.write(
            '<li><a id="btnSelLoc" loc="{nm}" data-target="#" role="button"><span class="glyphicon glyphicon-star qind-img-selloc" aria-hidden="true" loc="{nm}"></span> {nm}</a></li>\n'.
            format(nm=loc_name)
        )
    glf.write("""
       <li role="separator" class="divider"></li>
       <li><a id="btnToggleShowAllLocations" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowAllLocations"></span> Show all locations</a></li>
      </ul>
    </li>
""")

    glf.write("""

    <li><a data-target="#modalSales" role="button" data-toggle="modal">Sales</a></li>
   </ul>

   <form id="frmFilter" class="navbar-form navbar-right">
    <div class="input-group">
     <input id="edFilter" type="text" class="form-control" placeholder="What?">
      <span class="input-group-btn">
       <button id="btnFilter" class="btn btn-default" type="button" disabled>Filter</button>
      </span>
    </div>
   </form>
  </div>
 </div>
</nav>

<style>
.hvr-icon-fade {
  display--: inline-block;
  vertical-align: middle;
  -webkit-transform: perspective(1px) translateZ(0);
  transform: perspective(1px) translateZ(0);
  box-shadow: 0 0 1px rgba(0, 0, 0, 0);
}
.hvr-icon-fade .hvr-icon {
  -webkit-transform: translateZ(0);
  transform: translateZ(0);
  -webkit-transition-duration: 0.5s;
  transition-duration: 0.5s;
  -webkit-transition-property: color;
  transition-property: color;
}
.hvr-icon {
  color: #D6E0EE;
  top: 2px;
  left: 3px;
  font-size: smaller;
}
.hvr-icon-fade:hover .hvr-icon, .hvr-icon-fade:focus .hvr-icon, .hvr-icon-fade:active .hvr-icon {
  color: #0F9E5E;
}
.hvr-icon-sel {
  color: #999999;
}
tr.qind-bp-row {
  font-size: small;
}
.label-copy {
    background-color: #a49e9329;
}
</style>

<div class="container-fluid">
 <div class="panel-group" id="accordion" role="tablist" aria-multiselectable="true">
""")
    first_time = True
    for corporation_id in __corp_keys:
        __corp = corps_blueprints[str(corporation_id)]
        glf.write('  <div class="panel panel-primary">\n'
                  '   <div class="panel-heading" role="tab">\n'
                  '    <h3 class="panel-title">\n'
                  '     <a role="button" data-toggle="collapse" data-parent="#accordion" href="#pn{id}" aria-expanded="true" aria-controls="pn{id}">{nm}</a>\n'
                  '    </h3>\n'
                  '   </div>\n'
                  '   <div id="pn{id}" class="panel-collapse collapse{vsbl}" role="tabpanel" aria-labelledby="heading{id}">\n'.
                  format(nm=__corp["corporation"],
                         id=corporation_id,
                         vsbl=" in" if first_time else "")
        )
        first_time = False
        glf.write("""
    <div class="panel-body">
     <div class="table-responsive">
      <table class="table table-condensed table-hover">
<thead>
 <tr>
  <th>#</th>
  <th class="hvr-icon-fade" id="thSortSel" col="0">Blueprint<span class="glyphicon glyphicon-sort hvr-icon" aria-hidden="true"></span></th>
  <th class="hvr-icon-fade" id="thSortSel" col="1">ME<span class="glyphicon glyphicon-sort hvr-icon" aria-hidden="true"></span></th>
  <th class="hvr-icon-fade" id="thSortSel" col="2">TE<span class="glyphicon glyphicon-sort hvr-icon" aria-hidden="true"></span></th>
  <th class="hvr-icon-fade" id="thSortSel" col="3">Qty<span class="glyphicon glyphicon-sort hvr-icon" aria-hidden="true"></span></th>
  <th class="qind-td-prc hvr-icon-fade" id="thSortSel" col="4">Price, ISK<span class="glyphicon glyphicon-sort hvr-icon" aria-hidden="true"></span></th>
  <th class="hvr-icon-fade" id="thSortSel" col="5">Location<span class="glyphicon glyphicon-sort hvr-icon" aria-hidden="true"></span></th>
  <th class="qind-td-plc hvr-icon-fade" id="thSortSel" col="6">Place<span class="glyphicon glyphicon-sort hvr-icon" aria-hidden="true"></span></th>
  <th class="qind-td-box hvr-icon-fade" id="thSortSel" col="7">Box<span class="glyphicon glyphicon-sort hvr-icon" aria-hidden="true"></span></th>
  <th class="qind-td-out hvr-icon-fade" id="thSortSel" col="8">Output<span class="glyphicon glyphicon-sort hvr-icon" aria-hidden="true"></span></th>
 </tr>
</thead>
<tbody>
""")
        row_num = 1
        __summary_cost = 0
        for __blueprint_dict in __corp["blueprints"]:
            # выясняем сколько стоит один чертёж?
            __price = ""
            __fprice = ""
            if "base_price" in __blueprint_dict:
                __price = '{cost:,.1f} <sup class="qind-price-tag"><span class="label label-default">B</span></sup>'.format(cost=__blueprint_dict["base_price"])
                __fprice = '{:.1f}'.format(__blueprint_dict["base_price"])
            elif "average_price" in __blueprint_dict:
                __price = '{cost:,.1f} <sup class="qind-price-tag"><span class="label label-primary">A</span></sup>'.format(cost=__blueprint_dict["average_price"])
                __fprice = '{:.1f}'.format(__blueprint_dict["average_price"])
            elif "adjusted_price" in __blueprint_dict:
                __price = '{cost:,.1f} <sup class="qind-price-tag"><span class="label label-info">J</span></sup>'.format(cost=__blueprint_dict["adjusted_price"])
                __fprice = '{:.1f}'.format(__blueprint_dict["adjusted_price"])
            elif "price" in __blueprint_dict:
                __price = '{cost:,.1f} <sup class="qind-price-tag"><span class="label label-danger">C</span></sup>'.format(cost=__blueprint_dict["price"])
                __fprice = '{:.1f}'.format(__blueprint_dict["price"])
            # проверяем работки по текущему чертежу?
            __status = ""
            __activity = ""
            __blueprint_activity = None
            __blueprint_contract_activity = None
            __output_location_id = None
            if "st" in __blueprint_dict:
                # [ active, cancelled, delivered, paused, ready, reverted ]
                __blueprint_status = __blueprint_dict["st"]
                if (__blueprint_status == "active") or (__blueprint_status == "delivered"):
                    __status = '&nbsp;<span class="label label-default">{}</span>'.format(__blueprint_status)
                elif __blueprint_status == "ready":
                    __status = '&nbsp;<span class="label label-success">{}</span>'.format(__blueprint_status)
                elif (__blueprint_status == "cancelled") or (__blueprint_status == "paused") or (__blueprint_status == "reverted"):
                    __status = '&nbsp;<span class="label label-warning">{}</span>'.format(__blueprint_status)
                else:
                    __status = '&nbsp;<span class="label label-danger">{}</span>'.format(__blueprint_status)
                # [1..6] : https://support.eveonline.com/hc/en-us/articles/203210272-Activities-and-Job-Types
                # [0,1,3,4,5,7,8,11, +9?] : https://github.com/esi/esi-issues/issues/894
                __blueprint_activity = __blueprint_dict["act"]
                if __blueprint_activity == 1:
                    __activity = '&nbsp;<span class="label label-primary">manufacturing</span>'  # Manufacturing
                elif __blueprint_activity == 3:
                    __activity = '&nbsp;<span class="label label-info">te</span>'  # Science
                elif __blueprint_activity == 4:
                    __activity = '&nbsp;<span class="label label-info">me</span>'  # Science
                elif __blueprint_activity == 5:
                    __activity = '&nbsp;<span class="label label-info">copying</span>'  # Science
                elif __blueprint_activity == 7:
                    __activity = '&nbsp;<span class="label label-info">reverse</span>'  # Science
                elif __blueprint_activity == 8:
                    __activity = '&nbsp;<span class="label label-info">invention</span>'  # Science
                elif (__blueprint_activity == 9) or (__blueprint_activity == 11):
                    __activity = '&nbsp;<span class="label label-success">reaction</span>'  # Reaction
                else:
                    __activity = '&nbsp;<span class="label label-danger">{}</span>'.format(__blueprint_activity)
            # проверяем сведения по контракту, если чертёж прямо сейчас продаётся
            elif "cntrct_sta" in __blueprint_dict:
                # [ unknown, item_exchange, auction, courier, loan ]
                __blueprint_status = __blueprint_dict["cntrct_typ"]
                __status = '&nbsp;<span class="label label-default">{}</span>'.format(__blueprint_status)
                # [ outstanding, in_progress, finished_issuer, finished_contractor, finished, cancelled, rejected, failed, deleted, reversed ]
                __blueprint_contract_activity = __blueprint_dict["cntrct_sta"]
                __activity = '&nbsp;<span class="label label-danger">{}</span>'.format(__blueprint_contract_activity)
            # определяем местоположение чертежа
            __location_id = __blueprint_dict["loc"]
            __location_name = __location_id
            __location_box = ""
            if str(__location_id) in __corp["locations"]:
                # определяем название станции или солнечной системы, где лежит чертёж
                __loc_dict = __corp["locations"][str(__location_id)]
                if "station" in __loc_dict:
                    __location_name = __loc_dict["station"]
                elif "solar" in __loc_dict:
                    __location_name = __loc_dict["solar"]
                # определяем название контейнера, где лежит чертёж (названия ingame задают игроки)
                if not (__loc_dict["name"] is None):
                    __location_box = __loc_dict["name"]
            # определяем ангар и коробку, где лежит чертёж
            __place = __blueprint_dict["flag"]
            if __place[:-1] == "CorpSAG":
                __place = 'Hangar {}'.format(__place[-1:])  # Corp Security Access Group
            # определяем выход готовой продукции
            __output_location_id = __blueprint_dict.get("out", None)
            __output_location_box = __blueprint_dict.get("out", "")
            if not (__output_location_id is None):
                if str(__output_location_id) in __corp["locations"]:
                    # определяем название контейнера выхода готовой продукции (названия ingame задают игроки)
                    __loc_dict = __corp["locations"][str(__output_location_id)]
                    if not (__loc_dict["name"] is None):
                        __output_location_box = __loc_dict["name"]
            # определяем, является ли чертёж БПО или БПЦ
            __is_blueprint_copy = bool(__blueprint_dict["copy"])
            # вывод в таблицу информацию о чертеже
            glf.write('<tr class="qind-bp-row"{job}{cntrct}{copy}>'
                      ' <th scope="row">{num}</th>\n'
                      ' <td>{nm}{cp}{st}{act}</td>'
                      ' <td align="right">{me}</td>'
                      ' <td align="right">{te}</td>'
                      ' <td align="right">{q}</td>'
                      ' <td class="qind-td-prc" align="right" x-data="{iprice}">{price}</td>'
                      ' <td>{loc}</td>'
                      ' <td class="qind-td-plc">{plc}</td>'
                      ' <td class="qind-td-box">{box}</td>'
                      ' <td class="qind-td-out">{out}</td>'
                      '</tr>\n'.
                      format(num=row_num,
                             nm=__blueprint_dict["name"],
                             cp='&nbsp;<span class="label label-copy">copy</span>' if __is_blueprint_copy else '',
                             copy=' copy="1"' if __is_blueprint_copy else ' copy="0"',
                             st=__status,
                             act=__activity,
                             job="" if __blueprint_activity is None else ' job="{}"'.format(__blueprint_activity),
                             cntrct="" if __blueprint_contract_activity is None else ' cntrct="{}"'.format(__blueprint_contract_activity),
                             me=__blueprint_dict["me"] if "me" in __blueprint_dict else "",
                             te=__blueprint_dict["te"] if "te" in __blueprint_dict else "",
                             q=__blueprint_dict["q"],
                             price=__price,
                             iprice=__fprice,
                             loc=__location_name,
                             plc=__place,
                             box=__location_box,
                             out=__output_location_box))
            # подсчёт общей статистики
            # __summary_cost = __summary_cost + __stat_dict["cost"]
            row_num = row_num + 1

        glf.write("""
</tbody>
<tfoot>
<tr class="qind-summary-assets" style="font-weight:bold;">
 <th></th>
 <td align="right" colspan="3">Summary (assets)</td>
 <td align="right"></td>
 <td class="qind-td-prc" align="right"></td>
 <td></td>
 <td class="qind-td-plc"></td>
 <td class="qind-td-box"></td>
 <td class="qind-td-out"></td>
</tr>
<tr class="qind-summary-contracts" style="font-weight:bold;">
 <th></th>
 <td align="right" colspan="3">Summary (contracts)</td>
 <td align="right"></td>
 <td class="qind-td-prc" align="right"></td>
 <td></td>
 <td class="qind-td-plc"></td>
 <td class="qind-td-box"></td>
 <td class="qind-td-out"></td>
</tr>
</tfoot>
      </table>
     </div> <!--table-responsive-->
    </div> <!--panel-body-->
   </div> <!--panel-collapse-->
  </div> <!--panel-->
""")

    glf.write("""
 </div> <!--accordion-->
""")

    # создаём заголовок модального окна, где будем показывать список чертежей для продажи
    render_html.__dump_any_into_modal_header_wo_button(
        glf,
        'Sales of blueprints',
        'Sales',
        'modal-lg')
    # формируем содержимое модального диалога
    __dump_corp_blueprints_sales(glf, corps_blueprints)
    # закрываем footer модального диалога
    render_html.__dump_any_into_modal_footer(glf)

    glf.write("""
<div id="legend-block">
 <hr>
 <h4>Legend</h4>
 <p>
  <strong>ME</strong> - Material Efficiency, <strong>TE</strong> - Time Efficiency, <strong>Qty</strong> - blueprints
  quantity if it is a stack of blueprint originals fresh from the market (e.g. no activities performed
  on them yet), <strong>Price</strong> - price for one blueprint, <strong>Location</strong>, <strong>Place</strong> and
  <strong>Box</strong> - detailed location of blueprint.
 </p>
 <p>
  <span class="label label-primary">A</span>, <span class="label label-info">J</span>, <span class="label label-default">B</span>,
  <span class="label label-danger">C</span> - <strong>price tags</strong>,
  to indicate type of market' price. There are <span class="label label-primary">A</span> average price (<i>current market price</i>),
  and <span class="label label-info">J</span> adjusted price (<i>average over the last 28 days</i>), <span class="label label-default">B</span>
  base price (<i>standart CCP item price</i>) and <span class="label label-danger">C</span> - contract price.
 </p>
 <p>
  <span class="label label-default">active</span>, <span class="label label-default">delivered</span>,
  <span class="label label-success">ready</span>, <span class="label label-warning">cancelled</span>,
  <span class="label label-warning">paused</span>, <span class="label label-warning">reverted</span> - all possible
  <strong>statuses</strong> of blueprints that are in industry mode.
 </p>
  <span class="label label-danger">outstanding</span>,
  <span class="label label-danger">in_progress</span>,
  <span class="label label-danger">finished_issuer</span>,
  <span class="label label-danger">finished_contractor</span>,
  <span class="label label-danger">finished</span>,
  <span class="label label-danger">cancelled</span>,
  <span class="label label-danger">rejected</span>,
  <span class="label label-danger">failed</span>,
  <span class="label label-danger">deleted</span>,
  <span class="label label-danger">reversed</span> - all possible <strong>statuses</strong> of current contracts.
 <p>
  <span class="label label-primary">manufacturing</span> - manufacturing industry activity.</br>
  <span class="label label-info">te</span>, 
  <span class="label label-info">me</span>, 
  <span class="label label-info">copying</span>, 
  <span class="label label-info">reverse</span>, 
  <span class="label label-info">invention</span> - science industry activities.</br> 
  <span class="label label-success">reaction</span> - reaction industry activity.
 </p>
</div>

<script>
  // Blueprints Options dictionaries
  var g_job_activities = [
    '', 'Manufacturing', '', 'Research TE &amp; ME', '', 'Copying', '',
    'Reverse Engineering', 'Invention', 'Reactions', '', '',
    'Show', 'Hide'
  ];
  var g_blueprint_types = ['Original', 'Copy', 'All'];
  var g_tbl_col_types = [0,1,1,1,2,0,0,0,0]; // 0:str, 1:num, 2:x-data
  var g_tbl_filter = null;

  // Blueprints Options storage (prepare)
  ls = window.localStorage;

  // Tools & Utils
  function numLikeEve(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }
  // Blueprints table sorter
  function sortTable(table, order, what, typ) {
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

  // Disable function
  jQuery.fn.extend({
    disable: function(state) {
      return this.each(function() {
        this.disabled = state;
      });
    }
  });

  // Blueprints Options storage (init)
  function resetOptionsMenuToDefault() {
    if (!ls.getItem('Show Legend')) {
      ls.setItem('Show Legend', 1);
    }
    if (!ls.getItem('Show Price Vals')) {
      ls.setItem('Show Price Vals', 1);
    }
    if (!ls.getItem('Show Price Tags')) {
      ls.setItem('Show Price Tags', 1);
    }
    if (!ls.getItem('Show Place')) {
      ls.setItem('Show Place', 0);
    }
    if (!ls.getItem('Show Box')) {
      ls.setItem('Show Box', 0);
    }
    if (!ls.getItem('Show Unused Blueprints')) {
      ls.setItem('Show Unused Blueprints', 1);
    }
    if (!ls.getItem('Show Industry Jobs')) {
      ls.setItem('Show Industry Jobs', 12);
    }
    if (!ls.getItem('Show by Types')) {
      ls.setItem('Show by Types', 2);
    }
    if (!ls.getItem('Show Contracts')) {
      ls.setItem('Show Contracts', 1);
    }
    if (!ls.getItem('Show Finished Contracts')) {
      ls.setItem('Show Finished Contracts', 1);
    }
  }
  // Blueprints Options storage (rebuild menu components)
  function rebuildOptionsMenu() {
    show = ls.getItem('Show Legend');
    if (show == 1)
      $('#imgShowLegend').removeClass('hidden');
    else
      $('#imgShowLegend').addClass('hidden');
    show = ls.getItem('Show Contracts');
    if (show == 1)
      $('#imgShowContracts').removeClass('hidden');
    else
      $('#imgShowContracts').addClass('hidden');
    show = ls.getItem('Show Finished Contracts');
    if (show == 1)
      $('#imgShowFinishedContracts').removeClass('hidden');
    else
      $('#imgShowFinishedContracts').addClass('hidden');
    show = ls.getItem('Show Price Vals');
    if (show == 1)
      $('#imgShowPriceVals').removeClass('hidden');
    else
      $('#imgShowPriceVals').addClass('hidden');
    show = ls.getItem('Show Price Tags');
    if (show == 1)
      $('#imgShowPriceTags').removeClass('hidden');
    else
      $('#imgShowPriceTags').addClass('hidden');
    show = ls.getItem('Show Place');
    if (show == 1)
      $('#imgShowPlace').removeClass('hidden');
    else
      $('#imgShowPlace').addClass('hidden');
    show = ls.getItem('Show Box');
    if (show == 1)
      $('#imgShowBox').removeClass('hidden');
    else
      $('#imgShowBox').addClass('hidden');
    show = ls.getItem('Show Out');
    if (show == 1)
      $('#imgShowOut').removeClass('hidden');
    else
      $('#imgShowOut').addClass('hidden');
    show = ls.getItem('Show Unused Blueprints');
    if (show == 1)
      $('#imgShowUnusedBlueprints').removeClass('hidden');
    else
      $('#imgShowUnusedBlueprints').addClass('hidden');
    job = ls.getItem('Show Industry Jobs');
    $('span.qind-img-seljob').each(function() {
      _job = $(this).attr('job');
      if (job == _job)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
    $('#lbSelJob').html(g_job_activities[job]);
    cp = ls.getItem('Show by Types');
    $('span.qind-img-selbpx').each(function() {
      _cp = $(this).attr('copy');
      if (cp == _cp)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
    $('#lbSelBPx').html(g_blueprint_types[cp]);
    loc = ls.getItem('Show Only Location');
    if (!loc) {
      $('span.qind-img-selloc').each(function() { $(this).addClass('hidden'); })
      $('#imgShowAllLocations').removeClass('hidden');
    } else {
      $('#imgShowAllLocations').addClass('hidden');
      $('span.qind-img-selloc').each(function() {
        _loc = $(this).attr('loc');
        if (loc == _loc)
          $(this).removeClass('hidden');
        else
          $(this).addClass('hidden');
      })
    }
  }
  // Blueprints filter method (to rebuild body components)
  function isBlueprintVisible(el, loc, unused, job, cntrct, cntrct_fin, cp) {
    _res = 1;
    _loc = el.find('td').eq(5).text();
    _job = el.attr('job');
    _cntrct = el.attr('cntrct');
    _cp = el.attr('copy');
    _res = (loc && (_loc != loc)) ? 0 : 1;
    if (!(_cntrct === undefined)) {
      if (_res && (cntrct == 0))
        _res = 0;
      if (_res && (cntrct_fin == 0) && (_cntrct == "finished"))
        _res = 0;
    } else {
      if (_res && (!(_cp === undefined))) {
        if ((cp != 2) && (cp != _cp))
          _res = 0;
      }
      if (_res && (unused == 0)) {
        if (_job === undefined)
          _res = 0;
      }
      if (_res && (!(_job === undefined))) {
        if (job == 13)
          _res = 0;
        else if (job == 12)
          _res = 1;
        else if ((job == _job) || (job == 3) && (_job == 4) || (job == 9) && (_job == 11))
          _res = 1;
        else
          _res = 0;
      }
    }
    if (_res && (!(g_tbl_filter === null))) {
      var txt = el.find('td').eq(0).text().toLowerCase();
      _res = txt.includes(g_tbl_filter);
      if (!_res) {
        txt = el.find('td').eq(5).text().toLowerCase();
        _res = txt.includes(g_tbl_filter);
        if (!_res) {
          txt = el.find('td').eq(6).text().toLowerCase();
          _res = txt.includes(g_tbl_filter);
          if (!_res) {
            txt = el.find('td').eq(7).text().toLowerCase();
            _res = txt.includes(g_tbl_filter);
            if (!_res) {
              txt = el.find('td').eq(8).text().toLowerCase();
              _res = txt.includes(g_tbl_filter);
            }
          }
        }
      }
    }
    return _res;
  }
  // Blueprints Options storage (rebuild body components)
  function rebuildBody() {
    show = ls.getItem('Show Legend');
    if (show == 1)
      $('#legend-block').removeClass('hidden');
    else
      $('#legend-block').addClass('hidden');
    show = ls.getItem('Show Price Vals');
    $('.qind-td-prc').each(function() {
      if (show == 1)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
    show = ls.getItem('Show Price Tags');
    $('sup.qind-price-tag').each(function() {
      if (show == 1)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
    show = ls.getItem('Show Place');
    $('.qind-td-plc').each(function() {
      if (show == 1)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
    show = ls.getItem('Show Box');
    $('.qind-td-box').each(function() {
      if (show == 1)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
    show = ls.getItem('Show Out');
    $('.qind-td-out').each(function() {
      if (show == 1)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
    loc = ls.getItem('Show Only Location');
    unused = ls.getItem('Show Unused Blueprints');
    job = ls.getItem('Show Industry Jobs');
    cntrct = ls.getItem('Show Contracts');
    cntrct_fin = ls.getItem('Show Finished Contracts');
    cp = ls.getItem('Show by Types');
    $('table').each(function() {
      _summary_a_qty = 0;
      _summary_a_price = 0.0;
      _summary_c_qty = 0;
      _summary_c_price = 0.0;
      // filtering
      $(this).find('tr.qind-bp-row').each(function() {
        show = isBlueprintVisible($(this), loc, unused, job, cntrct, cntrct_fin, cp);
        if (show == 1) {
          $(this).removeClass('hidden');
          _cntrct = $(this).attr('cntrct');
          if (_cntrct === undefined) {
            _summary_a_qty += parseInt($(this).find('td').eq(3).text(),10);
            _summary_a_price += parseFloat($(this).find('td').eq(4).attr('x-data'));
          } else {
            _summary_c_qty += parseInt($(this).find('td').eq(3).text(),10);
            _summary_c_price += parseFloat($(this).find('td').eq(4).attr('x-data'));
          }
        } else
          $(this).addClass('hidden');
      })
      // sorting
      col = $(this).attr('sort_col');
      if (!(col === undefined)) {
        order = $(this).attr('sort_order');
        sortTable($(this),order,col,g_tbl_col_types[col]);
      }
      // summary (assets)
      tr_summary = $(this).find('tr.qind-summary-assets');
      tr_summary.find('td').eq(1).html(_summary_a_qty);
      tr_summary.find('td').eq(2).html(numLikeEve(_summary_a_price.toFixed(1)));
      // summary (contracts)
      tr_summary = $(this).find('tr.qind-summary-contracts');
      tr_summary.find('td').eq(1).html(_summary_c_qty);
      tr_summary.find('td').eq(2).html(numLikeEve(_summary_c_price.toFixed(1)));
    })
    // filtering sales
    var sales_loc_name = ls.getItem('Sales Location');
    var sales_place = ls.getItem('Sales Place');
    $('#tblSales').find('tbody').find('tr').each(function() {
      var tr = $(this);
      var show = true;
      if (!(sales_loc_name === null)) {
        show = sales_loc_name == tr.find('td').eq(1).text();
        if (show)
          show = sales_place == tr.find('td').eq(2).text();
      }
      if (show)
        tr.removeClass('hidden');
      else
        tr.addClass('hidden');
    });
  }
  // Blueprints Dropdown menu setup
  function rebuildSalesDropdown() {
    var sales_loc_name = ls.getItem('Sales Location');
    var sales_place = ls.getItem('Sales Place');
    if (!(sales_loc_name === null)) {
      var btn = $('#ddSalesMenu');
      btn.find('span.qind-lb-dd').html(sales_loc_name + ' <mark>' + sales_place + '</mark>');
      btn.val(sales_place);
    }
  }
  // Blueprints Options menu and submenu setup
  $(document).ready(function(){
    $('.dropdown-submenu a.options-submenu').on("click", function(e){
      $(this).next('ul').toggle();
      e.stopPropagation();
      e.preventDefault();
    });
    $('a#btnSelJob').on('click', function() {
      job = $(this).attr('job');
      ls.setItem('Show Industry Jobs', job);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('a#btnSelBPx').on('click', function() {
      cp = $(this).attr('copy');
      ls.setItem('Show by Types', cp);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleLegend').on('click', function () {
      show = (ls.getItem('Show Legend') == 1) ? 0 : 1;
      ls.setItem('Show Legend', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleShowContracts').on('click', function () {
      show = (ls.getItem('Show Contracts') == 1) ? 0 : 1;
      ls.setItem('Show Contracts', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleShowFinishedContracts').on('click', function () {
      show = (ls.getItem('Show Finished Contracts') == 1) ? 0 : 1;
      ls.setItem('Show Finished Contracts', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleExpand').on('click', function () {
      $('div.panel-collapse').each(function(){ $(this).addClass('in'); });
    });
    $('#btnToggleCollapse').on('click', function () {
      $('div.panel-collapse').each(function(){ $(this).removeClass('in'); });
    });
    $('#btnTogglePriceVals').on('click', function () {
      show = (ls.getItem('Show Price Vals') == 1) ? 0 : 1;
      ls.setItem('Show Price Vals', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnTogglePriceTags').on('click', function () {
      show = (ls.getItem('Show Price Tags') == 1) ? 0 : 1;
      ls.setItem('Show Price Tags', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnTogglePlace').on('click', function () {
      show = (ls.getItem('Show Place') == 1) ? 0 : 1;
      ls.setItem('Show Place', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleBox').on('click', function () {
      show = (ls.getItem('Show Box') == 1) ? 0 : 1;
      ls.setItem('Show Box', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleOut').on('click', function () {
      show = (ls.getItem('Show Out') == 1) ? 0 : 1;
      ls.setItem('Show Out', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleUnusedBlueprints').on('click', function () {
      show = (ls.getItem('Show Unused Blueprints') == 1) ? 0 : 1;
      ls.setItem('Show Unused Blueprints', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleShowAllLocations').on('click', function () {
      ls.removeItem('Show Only Location');
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('a#btnSelLoc').on('click', function() {
      loc = $(this).attr('loc');
      ls.setItem('Show Only Location', loc);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('th#thSortSel').on('click', function() {
      var col = $(this).attr('col');
      var table = $(this).closest('table');
      var thead = table.find('thead');
      var sort = table.attr('sort_col');
      var order = table.attr('sort_order');
      thead.find('th').each(function() {
        _col = $(this).attr('col');
        var icn = $(this).find('span');
        if (col == _col) {
          if (sort === undefined)
            order = 1;
          else if (sort == col)
            order = -order;
          else
            order = 1;
          icn.removeClass('glyphicon-sort');
          if (order == 1) {
            icn.removeClass('glyphicon-sort-by-attributes-alt');
            icn.addClass('glyphicon-sort-by-attributes');
          } else {
            icn.removeClass('glyphicon-sort-by-attributes');
            icn.addClass('glyphicon-sort-by-attributes-alt');
          }
          icn.addClass('hvr-icon-sel');
          table.attr('sort_col', col);
          table.attr('sort_order', order);
        } else if (!(sort === undefined)) {
          icn.removeClass('glyphicon-sort-by-attributes');
          icn.removeClass('glyphicon-sort-by-attributes-alt');
          icn.addClass('glyphicon-sort');
          icn.removeClass('hvr-icon-sel');
        }
      })
      sortTable(table,order,col,g_tbl_col_types[col]);
    });
    $('#edFilter').on('keypress', function (e) {
      if (e.which == 13)
        $('#btnFilter').click();
    })
    $('#edFilter').on('change', function () {
      var what = $('#edFilter').val();
      $('#btnFilter').disable(what.length == 0);
      $('#btnFilter').click();
    });
    $('#btnFilter').on('click', function () {
      var what = $('#edFilter').val();
      if (what.length == 0)
        g_tbl_filter = null;
      else
        g_tbl_filter = what.toLowerCase();
      rebuildBody();
    });
    $("#frmFilter").submit(function(e) {
      e.preventDefault();
    });
    $('#ddSales').on('click', 'li a', function () {
      var li_a = $(this);
      var loc_name = li_a.attr('loc');
      var place = li_a.text();
      ls.setItem('Sales Location', loc_name);
      ls.setItem('Sales Place', place);
      rebuildSalesDropdown();
      rebuildBody();
    });
    $('#btnResetOptions').on('click', function () {
      ls.clear();
      resetOptionsMenuToDefault();
      rebuildOptionsMenu();
      rebuildBody();
    });
    // first init
    resetOptionsMenuToDefault();
    rebuildOptionsMenu();
    rebuildSalesDropdown();
    rebuildBody();
  });
</script>
""")


def dump_blueprints_into_report(
        ws_dir,
        corps_blueprints):
    glf = open('{dir}/blueprints.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(glf, "Blueprints")
        __dump_corp_blueprints_tbl(
            glf,
            corps_blueprints)
        render_html.__dump_footer(glf)
    finally:
        glf.close()
