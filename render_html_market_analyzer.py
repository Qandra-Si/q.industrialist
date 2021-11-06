import render_html
import q_market_analyzer_settings


def get_percent_span(total, piece, color="text-muted"):
    return "<span class='{c}'><small>({p:.1f}%)</small></span>".format(
        c=color,
        p=0 if not total else 100.0*piece/total,
    )


def sorted_orders_lambda(d, k, tp):
    res: int = 0
    if tp != 's':
        res = d[k]["orders"]["buy"]
    if tp != 'b':
        res += d[k]["orders"]["sell"]
    return res


def get_popular_market_groups(data_to_sort, order_type, limit, with_caption, sde_icon_ids, sde_market_groups):
    # подготовка списков идентификаторов маркет групп
    sorted_market_ids = list(data_to_sort.keys())
    if not sorted_market_ids:
        return ""
    # сортировка по total/селам/баям
    sorted_market_ids.sort(key=lambda k: sorted_orders_lambda(data_to_sort, k, order_type), reverse=True)
    sorted_market_ids = sorted_market_ids[:limit]
    # формирование строки со списком популярных маркет-груп
    popular_market_groups: str = ""
    for idx, market_group_id in enumerate(sorted_market_ids):
        if idx == limit:
            break
        if sorted_orders_lambda(data_to_sort, market_group_id, order_type) == 0:
            break
        icon = sde_market_groups.get(str(market_group_id), {"iconID": None})["iconID"]
        if with_caption:
            nm = sde_market_groups.get(str(market_group_id), {"nameID": {"en": None}})["nameID"]["en"]
            popular_market_groups += \
                "<img class='icn16' src='{src}' style='display:inline;' alt='{nm}'> {nm} ".format(
                    src=render_html.__get_icon_src(icon, sde_icon_ids),
                    nm=nm,
                )
        else:
            popular_market_groups += \
                "<img class='icn16' src='{src}' style='display:inline;'> ".format(
                    src=render_html.__get_icon_src(icon, sde_icon_ids),
                )
    del sorted_market_ids
    return popular_market_groups


def __dump_market_analyzer(
        glf,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_icon_ids,
        sde_market_groups,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        market_regions):
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
     <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Display Options <span class="caret"></span></a>
      <ul class="dropdown-menu">
       <li><a id="btnResetOptions" data-target="#" role="button">Reset options</a></li>
      </ul>
    </li>
   </ul>
   <form class="navbar-form navbar-right">
    <div class="form-group">
     <input type="text" class="form-control" placeholder="Item" disabled>
    </div>
    <button type="button" class="btn btn-default disabled">Search</button>
   </form>
  </div>
 </div>
</nav>

<div class="container-fluid">
<h3>Markets</h3>
<table class="table table-condensed table-hover table-responsive">
<tr><th width="13%">Region</th><th width="7%">Orders</th><th width="40%">Sell Orders</th><th width="40%">Buy Orders</th></tr>
""")

    # market_regions tuple: (region_id, region_name, region_details)
    market_regions.sort(
        key=lambda mr: mr[2]["orders"]["sell"] + mr[2]["orders"]["buy"],
        reverse=True)
    the_forge_region_dict = next(mr[2] for mr in market_regions if mr[0] == 10000002)
    the_forge_region_total_orders = the_forge_region_dict["orders"]["sell"] + the_forge_region_dict["orders"]["buy"]

    for (region_id, region_name, region_details) in market_regions:
        # сортируем маркет регионов по интенсивности маркет-групп
        # popular_market_groups = get_popular_market_groups(
        #     region_details["market"], 't',
        #     q_market_analyzer_settings.g_popular_region_groups,
        #     q_market_analyzer_settings.g_popular_region_groups_captions,
        #     sde_icon_ids, sde_market_groups)
        popular_market_groups_buy = get_popular_market_groups(
            region_details["market"], 'b',
            q_market_analyzer_settings.g_popular_region_groups,
            q_market_analyzer_settings.g_popular_region_groups_captions,
            sde_icon_ids, sde_market_groups)
        popular_market_groups_sell = get_popular_market_groups(
            region_details["market"], 's',
            q_market_analyzer_settings.g_popular_region_groups,
            q_market_analyzer_settings.g_popular_region_groups_captions,
            sde_icon_ids, sde_market_groups)

        # считаем кол-во ордеров
        sell = region_details["orders"]["sell"]
        buy = region_details["orders"]["buy"]
        total = sell + buy

        glf.write(
            "<tr id='rgn{id}'>"
            "<td>{nm}<br><a class='btn btn-default' href='{rfn}-{fnm}.html' role='button'><span class='glyphicon glyphicon-shopping-cart' aria-hidden='true'></span></a></td>"
            "<td>{t} {tp}</td>"
            "<td>{s} {sp}<br><small><small>{sd}</small></small></td>"
            "<td>{b} {bp}<br><small><small>{bd}</small></small></td>"
            "</tr>\n".
            format(
                id=region_id,
                nm=region_name,
                rfn=q_market_analyzer_settings.g_report_filename,
                fnm=render_html.__camel_to_snake(region_name, True),
                t=total,
                tp="" if region_id == 10000002 else get_percent_span(the_forge_region_total_orders, sell+buy, color="text-primary"),
                # td=popular_market_groups,
                s=sell, sp=get_percent_span(total, sell),
                sd=popular_market_groups_sell,
                b=buy, bp=get_percent_span(total, buy),
                bd=popular_market_groups_buy,
            ))

    glf.write("""
</table>
</div> <!--container-fluid-->
""")


def __dump_region_market_analyzer(
        glf,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_icon_ids,
        sde_market_groups,
        sde_inv_names,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        region_tuple):
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
     <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Display Options <span class="caret"></span></a>
      <ul class="dropdown-menu">
       <li><a id="btnResetOptions" data-target="#" role="button">Reset options</a></li>
      </ul>
    </li>
   </ul>
   <form class="navbar-form navbar-right">
    <div class="form-group">
     <input type="text" class="form-control" placeholder="Item" disabled>
    </div>
    <button type="button" class="btn btn-default disabled">Search</button>
   </form>
  </div>
 </div>
</nav>

<div class="container-fluid">
<div class="row">
""")

    sorting_types = ['t', 's', 'b']
    sorted_system_captions = ['Total', 'Sell', 'Buy']

    # market_regions tuple: (region_id, region_name, region_details)
    (region_id, region_name, region_details) = region_tuple
    region_systems = region_details["systems"]

    for region_col in range(3):
        glf.write("""
<div class="col-md-4">
<table class="table table-condensed table-hover table-responsive">
""")
        # сортируем системы по частоте торговых операций
        sorted_systems_ids = list(region_systems.keys())
        sorted_systems_ids.sort(key=lambda k: sorted_orders_lambda(region_systems, k, sorting_types[region_col]), reverse=True)

        # вывод систем в отсортированном порядке
        glf.write("<h4>{} Orders</h4><tr><th>System</th><th>Quantity</th></tr>".format(sorted_system_captions[region_col]))
        for system_id in sorted_systems_ids:
            system_dict = region_systems[system_id]
            quantity = sorted_orders_lambda(region_systems, system_id, sorting_types[region_col])
            if quantity < q_market_analyzer_settings.g_do_not_display_orders_less_often_than:
                continue
            total = system_dict["orders"]["sell"] + system_dict["orders"]["buy"]
            # сортируем маркеты систем по интенсивности маркет-групп
            popular_market_groups = "" if not region_col else get_popular_market_groups(
                system_dict["market"],
                sorting_types[region_col],
                q_market_analyzer_settings.g_popular_system_groups,
                q_market_analyzer_settings.g_popular_system_groups_captions,
                sde_icon_ids,
                sde_market_groups)
            glf.write(
                "<tr id='sys{id}'>"
                "<td>{nm}</td>"
                "<td>{q} {qp} {qd}</td>"
                "</tr>\n".
                format(
                    id=system_id,
                    nm=system_dict["name"],
                    q=quantity,
                    qp="" if not region_col else get_percent_span(total, quantity),
                    qd=popular_market_groups,
                ))
        del sorted_systems_ids

        glf.write("""
</table>
</div> <!-- col-md-4 -->
""")

    glf.write("""
</div> <!-- row -->
""")
    glf.write("<h4>{} Trade Hubs</h4>".format(region_name))
    glf.write("""
<table class="table table-condensed table-hover table-responsive">
<tr><th>Trade Hub</th><th>Orders</th><th>Sell Orders</th><th>Buy Orders</th></tr>
""")

    region_trade_hubs = region_details["trade_hubs"]

    # сортируем торговые хабы по частоте торговых операций
    sorted_trade_hubs_ids = list(region_trade_hubs.keys())
    sorted_trade_hubs_ids.sort(key=lambda k: sorted_orders_lambda(region_trade_hubs, k, 't'), reverse=True)

    for trade_hub_id in sorted_trade_hubs_ids:
        trade_hub_dict = region_trade_hubs[trade_hub_id]

        sell = trade_hub_dict["orders"]["sell"]
        buy = trade_hub_dict["orders"]["buy"]
        total = sell + buy
        if total < q_market_analyzer_settings.g_do_not_display_orders_less_often_than:
            continue

        # сортируем маркеты торговых хабов по интенсивности маркет-групп
        popular_market_groups_sell = get_popular_market_groups(
            trade_hub_dict["market"], 's',
            q_market_analyzer_settings.g_popular_trade_hub_groups,
            q_market_analyzer_settings.g_popular_trade_hub_groups_captions,
            sde_icon_ids, sde_market_groups)
        popular_market_groups_buy = get_popular_market_groups(
            trade_hub_dict["market"], 'b',
            q_market_analyzer_settings.g_popular_trade_hub_groups,
            q_market_analyzer_settings.g_popular_trade_hub_groups_captions,
            sde_icon_ids, sde_market_groups)

        trade_hub_name = sde_inv_names.get(str(trade_hub_id))
        if not trade_hub_name:
            trade_hub_name = "{} - {}".format(sde_inv_names.get(str(trade_hub_dict["system"])), trade_hub_id)

        glf.write(
            "<tr id='hub{id}'>"
            "<td>{nm}</td>"
            "<td>{t}</td>"
            "<td>{s} {sp} <small><small>{sd}</small></small></td>"
            "<td>{b} {bp} <small><small>{bd}</small></small></td>"
            "</tr>\n".
            format(
                id=trade_hub_id,
                nm=trade_hub_name,
                t=total,
                # tp=get_percent_span(the_forge_region_total_orders, sell + buy, color="text-primary"),
                # td=popular_market_groups,
                s=sell, sp=get_percent_span(total, sell),
                sd=popular_market_groups_sell,
                b=buy, bp=get_percent_span(total, buy),
                bd=popular_market_groups_buy,
            ))
    del sorted_trade_hubs_ids

    glf.write("""
</table>""")

    del region_trade_hubs
    del region_systems

    glf.write("""
</div> <!--container-fluid-->
""")


def dump_market_analyzer_into_report(
        # путь, где будет сохранён отчёт
        ws_dir,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_icon_ids,
        sde_market_groups,
        sde_inv_names,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        market_regions):
    glf = open('{dir}/{rfn}.html'.format(dir=ws_dir, rfn=q_market_analyzer_settings.g_report_filename), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(glf, "Markets")
        __dump_market_analyzer(
            glf,
            sde_icon_ids,
            sde_market_groups,
            market_regions
        )
        render_html.__dump_footer(glf)
    finally:
        glf.close()

    # market_regions tuple: (region_id, region_name, region_details)
    for region_tuple in market_regions:
        glf = open('{dir}/{rfn}-{fnm}.html'.format(
            dir=ws_dir,
            rfn=q_market_analyzer_settings.g_report_filename,
            fnm=render_html.__camel_to_snake(region_tuple[1], True)), "wt+", encoding='utf8')
        try:
            render_html.__dump_header(glf, "{} Markets".format(region_tuple[1]))
            __dump_region_market_analyzer(
                glf,
                sde_icon_ids,
                sde_market_groups,
                sde_inv_names,
                region_tuple
            )
            render_html.__dump_footer(glf)
        finally:
            glf.close()
