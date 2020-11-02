import render_html
import eve_sde_tools


def __dump_corp_wallets_details(
        glf,
        corporation_name,
        corporation_id,
        __corp_wallets,
        __corp_wallet_names,
        __corp_wallets_stat):
    render_html.__dump_any_into_modal_header(
        glf,
        '<span class="text-primary">{nm}</span> Wallets'.format(nm=corporation_name),
        unique_id='{nm}_wallets'.format(nm=corporation_id),
        btn_size="btn-xs",
        btn_nm="details&hellip;")
    glf.write("""
<div class="table-responsive">
  <table class="table table-condensed">
<thead>
 <tr>
  <th>Wallet&nbsp;#</th>
  <th style="text-align: right;">Balance,&nbsp;ISK</th>
 </tr>
</thead>
<tbody>
""")
    for w in __corp_wallets:
        __wallet_division = w["division"]
        __wallet_name = next((wn["name"] for wn in __corp_wallet_names if (wn['division'] == __wallet_division) and ("name" in wn)), None)
        glf.write('<tr class="success">'
                  ' <th scope="row">{nm}</th>'
                  ' <td align="right">{blnc:,.1f}</td>'
                  '</tr>\n'.
                  format(nm="{nm} [{d}]".format(nm=__wallet_name,d=__wallet_division) if not (__wallet_name is None) else "{d} Wallet [{d}]".format(d=__wallet_division),
                         blnc=w["balance"]))
        __wd_keys = __corp_wallets_stat[__wallet_division-1].keys()
        for __wd_key in __wd_keys:
            __amount = __corp_wallets_stat[__wallet_division-1][__wd_key]
            glf.write('<tr>'
                      ' <td>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;{ref}</th>'
                      ' <td align="right"{clr}>{amount:,.1f}</td>'
                      '</tr>\n'.
                      format(ref=__wd_key,
                             amount=__amount,
                             clr=' class="text-danger"' if __amount < 0 else ""))
    glf.write('<tr style="font-weight:bold;">'
              ' <td>Summary</td>'
              ' <td align="right">{sum:,.1f}</td>'
              '</tr>\n'.
              format(sum=sum([w["balance"] for w in __corp_wallets])))
    glf.write("""
</tbody>
 </table>
</div>
""")
    render_html.__dump_any_into_modal_footer(glf)


def __dump_corp_accounting_nested_tbl(
        glf,
        loc_id,
        loc_dict,
        __corp_hangar_names,
        sde_type_ids,
        sde_icon_ids,
        filter_flags):
    h3_and_table_printed = False
    tr_divider_skipped = True
    __hangar_colors = ["", "fbfbfe", "f0f5f3", "f8fcf4", "fffdeb", "fff4f5", "f0f1f9", "f8f6f5", "fcfdfd"]
    if "items" in loc_dict:
        __itms_keys = loc_dict["items"].keys()
        for __loc_id in __itms_keys:
            itm_dict = loc_dict["items"][str(__loc_id)]
            # отбрасываем элементы не по фильтру (например нет списка "delivery")
            __filter_found = filter_flags is None
            if not __filter_found:
                for __filter in filter_flags:
                    if __filter in itm_dict["flags"]:
                        __filter_found = True
                        break
            if not __filter_found:
                continue
            # пишем заголовок таблицы (название системы)
            if not h3_and_table_printed:
                h3_and_table_printed = True
                __loc_name = loc_dict["loc_name"]
                if __loc_name is None:
                    __loc_name = loc_id
                glf.write(
                    '<h3>{where}<!--{id}--></h3>\n'.
                    format(where='{} '.format(__loc_name) if not (__loc_name is None) else "",
                           id=loc_id))
                glf.write("""
<div class="table-responsive">
  <table class="table table-condensed">
<thead>
 <tr>
  <th style="width:32px;">#</th>
  <th style="width:32px;"></th>
  <th>Items</th>
  <th style="text-align: right;">Cost, ISK</th>
  <th style="text-align: right;">Volume, m&sup3;</th>
 </tr>
</thead>
<tbody>
""")
            # получаем данные по текущему справочнику
            loc_name = itm_dict["loc_name"]
            foreign = itm_dict["foreign"]
            forbidden = itm_dict["forbidden"] if "forbidden" in itm_dict else False
            type_id = itm_dict["type_id"]
            if loc_name is None:
                loc_name = loc_id
            # добавляем пустую строку для разграничения групп товаров между станциями
            if not tr_divider_skipped:
                glf.write('<tr><td colspan="5"></td></tr>')
            tr_divider_skipped = False
            # добавляем название станции
            __station_type_name = eve_sde_tools.get_item_name_by_type_id(sde_type_ids, type_id) if not (type_id is None) else ""
            glf.write(
                '<tr><td colspan="5">'
                '<div class="media">'
                ' <div class="media-left">{img}</div>'
                ' <div class="media-body"><strong>{where}</strong>{what}{foreign}{forbidden}<!--{id}--></div>'
                '</div>'
                '</td></tr>\n'.
                format(where='{} '.format(loc_name) if not (loc_name is None) else "",
                       id=__loc_id,
                       foreign='&nbsp;<small><span class="label label-warning">foreign</span></small>' if foreign else "",
                       forbidden='&nbsp;<small><span class="label label-danger">forbidden</span></small>' if forbidden else "",
                       img='<img class="media-object icn32" src="{src}">'.format(src=render_html.__get_img_src(type_id, 32)) if not (type_id is None) else "",
                       what='&nbsp;<small>{}</small> '.format(__station_type_name) if __station_type_name else ""))
            row_id = 1
            __summary_cost = None
            __summary_volume = 0
            __blueprints_reactions_dict = None
            if "flags" in itm_dict:
                __f_keys = itm_dict["flags"].keys()
                for hangar_type_flags in range(2):
                    for __flag in __f_keys:  # "CorpDeliveries"
                        # в начало таблицы размещаем офисы на станке с ангарами, так что в конце таблиц размещено всё остальное (без ангаров)
                        if (hangar_type_flags == 0) and (__flag != "OfficeFolder"):
                            continue
                        elif (hangar_type_flags == 1) and (__flag == "OfficeFolder"):
                            continue
                        # отбрасываем элементы не по фильтру (например нет списка "delivery")
                        __filter_found = filter_flags is None
                        if not __filter_found and (0 != filter_flags.count(__flag)):
                            __filter_found = True
                        if not __filter_found:
                            continue
                        # получаем список групп товаров, хранящихся в указанном __flag
                        __flag_dict = itm_dict["flags"][str(__flag)]
                        if str(__flag) == "BlueprintsReactions":
                            __blueprints_reactions_dict = __flag_dict
                            continue
                        # сортируем группы товаров на названию групп
                        __flag_dict_sorted = []
                        __g_h_keys = __flag_dict.keys()
                        for __group_hangar_key in __g_h_keys:
                            __group_dict = __flag_dict[str(__group_hangar_key)]
                            __hangar = 0 if __group_dict["hangar_num"] is None else int(__group_dict["hangar_num"])
                            __flag_dict_sorted.append({"key": __group_hangar_key, "nm": '{}_{}'.format(__hangar, __group_dict["group"]), "hg": __hangar})
                        __flag_dict_sorted.sort(key=lambda s: s["nm"])
                        # подсчёт кол-ва групп товаров, лежащих в ангарах (необходимо для вывода hangar' summary)
                        __hangar_num_qty = [0, 0, 0, 0, 0, 0, 0, 0, 0]
                        for __group_dict_sorted in __flag_dict_sorted:
                            __hangar_num_qty[int(__group_dict_sorted["hg"])] += 1
                        # подготавливаем к выводу номера ангаров (если присутствуют)
                        __prev_hangar_num = None
                        __summary_hangar_groups = None
                        __summary_hangar_cost = None
                        __summary_hangar_volume = None
                        # выводим информацию по содержимому location (группы товаров)
                        for __group_dict_sorted in __flag_dict_sorted:
                            __group_hangar_key = __group_dict_sorted["key"]
                            __group_dict = __flag_dict[str(__group_hangar_key)]
                            __hangar_num = __group_dict["hangar_num"]  # м.б. None, в то время как __group_dict_sorted["hg"] м.б. 0
                            # вывод номера ангара
                            if (__prev_hangar_num is None) and not (__hangar_num is None) or (__prev_hangar_num != __hangar_num):
                                __prev_hangar_num = __hangar_num
                                __summary_hangar_groups = __hangar_num_qty[int(__hangar_num)]
                                __summary_hangar_cost = 0
                                __summary_hangar_volume = 0
                                __hangar_name = next((hn["name"] for hn in __corp_hangar_names if (hn['division'] == __hangar_num) and ("name" in hn)), None)
                                glf.write('<tr style="font-weight:bold;background-color:#{hngr_clr}">'
                                          ' <td colspan="5">{nm}</td>'
                                          '</tr>\n'.
                                          format(nm="{nm} [{num}]".format(nm=__hangar_name,num=__hangar_num) if not (__hangar_name is None) else "{num} Hangar [{num}]".format(num=__hangar_num),
                                                 hngr_clr=__hangar_colors[__hangar_num]))
                            # создание искусственной вложенности (ангары и прочие категории)
                            if not (__hangar_num is None):
                                glf.write('<tr{hngr_clr}>'
                                          ' <td></td>'
                                          ' <th scope="row">{num}</th>'
                                          ' <td>'.
                                          format(hngr_clr=' style="background-color:#{}"'.format(__hangar_colors[__hangar_num]) if not (__hangar_num is None) else "",
                                                 num=row_id))
                            else:
                                glf.write('<tr>'
                                          ' <th scope="row">{num}</th>\n'
                                          ' <td colspan="2">'.
                                          format(num=row_id))
                            # вывод названий товаров, стоимость и объём (строка таблицы)
                            glf.write(' {icn}{nm}{tag}</td>'
                                      ' <td align="right">{cost:,.1f}</td>'
                                      ' <td align="right">{volume:,.1f}</td>'
                                      '</tr>'.
                                      format(nm=__group_dict["group"],
                                             icn='<img class="icn16" src="{}" style="display:inline;">&nbsp;'.
                                                 format(render_html.__get_icon_src(__group_dict["icon"], sde_icon_ids))
                                                 if not (__group_dict["icon"] is None) else "",
                                             cost=__group_dict["cost"],
                                             volume=__group_dict["volume"],
                                             tag='' if not (filter_flags is None) and (len(filter_flags) == 1) else
                                                 ' <small><span class="label label-default">{flag}</span></small>'.
                                                 format(flag=render_html.__camel_to_snake(str(__flag)))
                                            ))
                            # вывод данных по кораблям, находящимся в этой локации
                            __td_ships = ''
                            if "ships" in __group_dict:
                                __ships = __group_dict["ships"]
                                # сортировка по названиям
                                for ship in __ships:
                                    ship.update({"nm": eve_sde_tools.get_item_name_by_type_id(sde_type_ids, ship["type_id"])})
                                __ships.sort(key=lambda s: s["nm"])
                                # подготовка в выводу в подвале раздела Ships
                                for ship in __ships:
                                    __ship_type_id = ship["type_id"]
                                    __td_cost = '{cost:,.1f}'.format(cost=ship["cost"])
                                    __td_volume = '{volume:,.1f}'.format(volume=ship["volume"]+ship["volume_nested"])
                                    __tag_nested = ''
                                    if ship["volume_nested"] > 0:
                                        __td_cost += ' <mark>+ {cost:,.1f}</mark>'.format(cost=ship["cost_nested"])
                                    else:
                                        __tag_nested = ' <span class="label label-primary">hull only</span>'
                                    glf.write(
                                        '<tr style="font-size: x-small;{hngr_clr}">'
                                        ' <td colspan="2"></td>'
                                        ' <td>&nbsp; <img class="icn16" src="{src}" style="display:inline;"> <strong>{q}x</strong> {nm}{tagn}</td>'
                                        ' <td align="right">{cost}</td>'
                                        ' <td align="right">{volume}</td>'
                                        '</tr>\n'.
                                        format(
                                            hngr_clr='' if __hangar_num is None else 'background-color:#{};'.format(__hangar_colors[__hangar_num]),
                                            src=render_html.__get_img_src(__ship_type_id, 32),
                                            nm=ship["nm"],
                                            tagn=__tag_nested,
                                            q=ship["quantity"],
                                            cost=__td_cost,
                                            volume=__td_volume
                                    ))
                            row_id = row_id + 1
                            __summary_cost = __group_dict["cost"] if __summary_cost is None else __summary_cost + __group_dict["cost"]
                            __summary_volume += __group_dict["volume"]
                            # вывод summary-информации по ангару
                            if not (__summary_hangar_cost is None):
                                __summary_hangar_cost += __group_dict["cost"]
                                __summary_hangar_volume += __group_dict["volume"]
                            if not (__summary_hangar_groups is None):
                                __summary_hangar_groups -= 1
                                if __summary_hangar_groups == 0:
                                    glf.write('<tr style="font-weight:bold;background-color:#{hngr_clr}">'
                                              ' <td></td>'
                                              ' <td colspan="2">Summary&nbsp;(<small>Hangar {hangar}</small>)</td>'
                                              ' <td align="right">{cost:,.1f}</td>'
                                              ' <td align="right">{volume:,.1f}</td>'
                                              '</tr>\n'.
                                              format(hangar=__hangar_num,
                                                     hngr_clr=__hangar_colors[__hangar_num],
                                                     cost=__summary_hangar_cost,
                                                     volume=__summary_hangar_volume))
            # вывод summary-информации в конце каждой таблицы
            if not (__summary_cost is None):
                # не копируется в модальном окне:__copy2clpbrd = '&nbsp;<a data-target="#" role="button" data-copy="{cost:.1f}" class="qind-copy-btn"' \
                # не копируется в модальном окне:                '  data-toggle="tooltip"><span class="glyphicon glyphicon-copy"' \
                # не копируется в модальном окне:                '  aria-hidden="true"></span></a>'. \
                # не копируется в модальном окне:                format(cost=__summary_cost)
                glf.write('<tr style="font-weight:bold;">'
                          ' <td colspan="3">Summary{what}</td>'
                          ' <td align="right">{cost:,.1f}</td>'
                          ' <td align="right">{volume:,.1f}</td>'
                          '</tr>'.
                          format(cost=__summary_cost,
                                 volume=__summary_volume,
                                 what='&nbsp;(<small>{}</small>)'.format(__station_type_name) if __station_type_name else ""))
            # вывод пропущенных ранее 'Blueprints & Reactions' (в конце каждой таблицы, под summary)
            if not (__blueprints_reactions_dict is None):
                __flag = "BlueprintsReactions"
                __g_keys = __blueprints_reactions_dict.keys()
                # выводим информацию по содержимому location (группы товаров)
                for __group_id in __g_keys:
                    __group_dict = __blueprints_reactions_dict[str(__group_id)]
                    glf.write('<tr style="color:green;">'
                              ' <td colspan="3">{icn}{nm}{tag}</td>'
                              ' <td align="right">{cost:,.1f}</td>'
                              ' <td align="right">{volume:,.1f}</td>'
                              '</tr>'.
                              format(nm=__group_dict["group"],
                                     icn='<img class="icn16" src="{}" style="display:inline;">&nbsp;'.
                                         format(render_html.__get_icon_src(__group_dict["icon"], sde_icon_ids))
                                         if not (__group_dict["icon"] is None) else "",
                                     cost=__group_dict["cost"],
                                     volume=__group_dict["volume"],
                                     tag='' if not (filter_flags is None) and (len(filter_flags) == 1) else
                                         ' <small><span class="label label-default">{flag}</span></small>'.
                                         format(flag=render_html.__camel_to_snake(str(__flag)))))
    if h3_and_table_printed:
        glf.write("""
</tbody>
 </table>
</div>
""")


def __dump_corp_accounting_details(
        glf,
        __association,
        __keys,
        corporation_name,
        corporation_id,
        __corp_tree,
        __corp_hangar_names,
        sde_type_ids,
        sde_icon_ids):
    render_html.__dump_any_into_modal_header(
        glf,
        '<span class="text-primary">{nm}</span> {key}'.format(nm=corporation_name,
                                                              key=__association),
        '{nm}_{key}'.format(nm=corporation_id,
                            key="all" if __keys is None else render_html.__camel_to_snake(__association)),
        "btn-xs",
        "details&hellip;",
        "modal-lg")
    __roots = __corp_tree.keys()
    for root in __roots:
        __dump_corp_accounting_nested(
            glf,
            root,
            __corp_tree[str(root)],
            __corp_hangar_names,
            sde_type_ids,
            sde_icon_ids,
            __keys)  # ["CorpDeliveries"]
    render_html.__dump_any_into_modal_footer(glf)


def __dump_corp_accounting_nested(
        glf,
        root_id,
        root,
        __corp_hangar_names,
        sde_type_ids,
        sde_icon_ids,
        filter_flags):
    if "region" in root:
        __filter_found = filter_flags is None
        if not __filter_found:
            for __filter in filter_flags:
                if ("flags" in root) and (root["flags"].count(__filter) > 0):
                    __filter_found = True
                    break
        if not __filter_found:
            return
        glf.write('<h2>{rgn}<!--{id}--></h2>\n'.format(rgn=root["region"], id=root_id))
        __sys_keys = root["systems"].keys()
        for loc_id in __sys_keys:
            system = root["systems"][str(loc_id)]
            __dump_corp_accounting_nested_tbl(glf, loc_id, system, __corp_hangar_names, sde_type_ids, sde_icon_ids, filter_flags)
    else:
        glf.write('<h2>???</h2>\n')
        __dump_corp_accounting_nested_tbl(glf, root_id, root, __corp_hangar_names, sde_type_ids, sde_icon_ids, filter_flags)


def __dump_corp_accounting(
        glf,
        sde_type_ids,
        sde_icon_ids,
        corps_accounting):
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
       <a class="navbar-brand" data-target="#"><span class="glyphicon glyphicon-list-alt" aria-hidden="true"></span></a>
      </div>

      <div class="collapse navbar-collapse" id="bs-navbar-collapse">
       <ul class="nav navbar-nav">
        <li class="dropdown">
         <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Display Options <span class="caret"></span></a>
          <ul class="dropdown-menu">
           <li><a id="btnToggleBlueprints" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowBlueprints"></span> Show blueprints and reactions</a></li>
           <li><a id="btnToggleLegend" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowLegend"></span> Show legend</a></li>
           <li role="separator" class="divider"></li>
           <li><a id="btnResetOptions" data-target="#" role="button">Reset options</a></li>
          </ul>
        </li>

        <li class="disabled"><a data-target="#" role="button">Problems</a></li>
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
    """)
    glf.write("""
<div class="table-responsive">
  <table class="table table-condensed table-hover">
<thead>
 <tr>
  <th style="width:40px;">#</th>
  <th>Locations</th>
  <th style="text-align: right;">Cost, ISK</th>
  <th style="text-align: right;">Volume, m&sup3;</th>
  <th style="text-align: center;">Details</th>
 </tr>
</thead>
<tbody>
""")

    __corp_keys = corps_accounting.keys()
    for corporation_id in __corp_keys:
        __corp = corps_accounting[str(corporation_id)]
        __wallets_balance = sum([w["balance"] for w in __corp["wallet"]])
        # создание первой строчки - название корпорации
        # создание второй строчки - кошельки корпорации
        glf.write('<tr class="active">'
                  ' <td colspan="5"><span class="text-primary"><strong>{nm}</strong></span></td>'
                  '</tr>\n'
                  '<tr>'
                  ' <th scope="row">1</th>'
                  ' <td>Wallets</td>'
                  ' <td align="right">{wallet:,.1f}</td>'
                  ' <td></td>'
                  ' <td align="center">'.
                  format(nm=__corp["corporation"],
                         wallet=__wallets_balance))
        # добавление details на страницу (подробности по кошелькам)
        __dump_corp_wallets_details(
            glf,
            __corp["corporation"],
            corporation_id,
            __corp["wallet"],
            __corp["divisions"]["wallet"] if "wallet" in __corp["divisions"] else [],
            __corp["wallet_stat"])
        glf.write('</td>'
                  '</tr>\n')

        # вывод третьей, четвёртой, ... строчек - ассеты корпорации
        row_num = 2
        __summary_cost = __wallets_balance
        __summary_volume = 0
        __stat_keys = __corp["stat"].keys()

        # [
        #  { "Structures": [{"AutoFit": ...}, {"ServiceSlot0": ...}, ...] },
        #  { "OfficeFolder": [{"OfficeFolder": ...}]] },
        #  { "FighterTube": [{"FighterTube0": ...}, {"FighterTube1": ...}, ...]] },
        # ]
        __sorted_keys = []

        def add_into_sorted_keys(__association, __key, __stat_dict):
            __association_dict = next((k442 for k442 in __sorted_keys if __association in k442), None)
            if __association_dict is None:
                __sorted_keys.append({__association: [{__key: __stat_dict}]})
            else:
                __association_dict[__association].append({__key: __stat_dict})

        for __key in __stat_keys:
            __stat_dict = __corp["stat"][str(__key)]
            if ("omit_in_summary" in __stat_dict) and __stat_dict["omit_in_summary"]:
                continue
            # удаляем из нумерованных ключей последнюю цифру
            __unnumbered_key = __key[:-1]
            # https://github.com/esi/eve-glue/blob/master/eve_glue/location_flag.py
            if (__key == "AutoFit") or (__unnumbered_key == "ServiceSlot") or \
               (__key == "StructureFuel") or (__unnumbered_key == "RigSlot"):
                # собираем структурные keys (AutoFit, ServiceSlot? => Structures)
                add_into_sorted_keys("Structures", __key, __stat_dict)
            else:
                # FighterTube0, FighterTube1, ..., SubSystemSlot0, SubSystemSlot1, ...
                if (__unnumbered_key == "FighterTube") or \
                   (__unnumbered_key == "CorpSAG") or \
                   (__unnumbered_key == "HiSlot") or \
                   (__unnumbered_key == "MedSlot") or \
                   (__unnumbered_key == "LoSlot") or \
                   (__unnumbered_key == "SubSystemSlot"):
                    add_into_sorted_keys(__unnumbered_key, __key, __stat_dict)
                else:
                    add_into_sorted_keys(__key, __key, __stat_dict)

        __sorted_keys = sorted(__sorted_keys, key=lambda x: str(list(x.keys())[0]))
        for ka in __sorted_keys:
            __association = list(ka.keys())[0]      # "Structures"
            __association_dict = ka[__association]  # [{"AutoFit": ...}, {"ServiceSlot0": ...}, ...]
            __association_dict = sorted(__association_dict, key=lambda x: str(list(x.keys())[0]))
            # подсчёт общей статистики
            __association_cost = 0
            __association_volume = 0
            __association_keys = []
            for ad in __association_dict:
                __key = list(ad.keys())[0]  # "AutoFit"
                __stat_dict = ad[__key]     # ...
                __association_keys.append(__key)
                # подсчёт общей статистики
                __association_cost += __stat_dict["cost"]
                __association_volume += __stat_dict["volume"]
                __summary_cost += __stat_dict["cost"]
                __summary_volume += __stat_dict["volume"]
            glf.write('<tr>'
                      ' <th scope="row">{num}</th>\n'
                      ' <td>{nm}</td>'
                      ' <td align="right">{cost:,.1f}</td>'
                      ' <td align="right">{volume:,.1f}</td>'
                      ' <td align="center">'.
                      format(num=row_num,
                             nm=__association,  # "CorpDeliveries"
                             cost=__association_cost,
                             volume=__association_volume))
            # добавление details на страницу
            __dump_corp_accounting_details(
                glf,
                __association,
                __association_keys,
                __corp["corporation"],
                corporation_id,
                __corp["tree"],
                __corp["divisions"]["hangar"] if "hangar" in __corp["divisions"] else [],
                sde_type_ids,
                sde_icon_ids)
            glf.write('</td>'
                      '</tr>\n')
            row_num = row_num + 1

        # добавление строки Summary
        __copy2clpbrd = '&nbsp;<a data-target="#" role="button" data-copy="{cost:.1f}" class="qind-copy-btn"' \
                        '  data-toggle="tooltip"><span class="glyphicon glyphicon-copy"' \
                        '  aria-hidden="true"></span></a>'. \
                        format(cost=__summary_cost)
        glf.write('<tr>'
                  ' <th></th>\n'
                  ' <td><strong>Summary</strong></td>\n'
                  ' <td align="right"><strong>{cost:,.1f}{clbrd}</strong></td>'
                  ' <td align="right"><strong>{volume:,.1f}</strong></td>'
                  ' <td align="center">'.
                  format(cost=__summary_cost,
                         volume=__summary_volume,
                         clbrd=__copy2clpbrd))
        # добавление details в summary
        __dump_corp_accounting_details(
            glf,
            "Summary",
            None,
            __corp["corporation"],
            corporation_id,
            __corp["tree"],
            __corp["divisions"]["hangar"] if "hangar" in __corp["divisions"] else [],
            sde_type_ids,
            sde_icon_ids)
        glf.write('</td>'
                  '</tr>\n')

        # добавление в подвал (под summary) информацию об omitted-категориях (такая у нас Blueprints & Reactions)
        # повторно запускаем цикл
        for __key in __stat_keys:
            __stat_dict = __corp["stat"][str(__key)]
            if not ("omit_in_summary" in __stat_dict) or not __stat_dict["omit_in_summary"]:
                continue
            glf.write('<tr class="qind-blueprints-stat">'
                      ' <th></th>\n'
                      ' <td style="color:green;">{nm}</td>'
                      ' <td style="color:green;" align="right">{cost:,.1f}</td>'
                      ' <td style="color:green;" align="right">{volume:,.1f}</td>'
                      ' <td align="center">'.
                      format(nm=__key,  # "BlueprintsReactions"
                             cost=__stat_dict["cost"],
                             volume=__stat_dict["volume"]))
            # добавление details на страницу
            __dump_corp_accounting_details(
                glf,
                __key,  # "BlueprintsReactions"
                [__key],
                __corp["corporation"],
                corporation_id,
                __corp["tree"],
                __corp["divisions"]["hangar"] if "hangar" in __corp["divisions"] else [],
                sde_type_ids,
                sde_icon_ids)
            glf.write('</td>'
                      '</tr>\n')

    glf.write("""
</tbody>
 </table>
</div>
""")
    glf.write("""
<div id="legend-block">
 <hr>
 <h4>Legend</h4>
 <p>
  <small><span class="label label-warning">foreign</span></small> - the station or structure is owned by another corporation.
 </p>
 <p>
  <small><span class="label label-danger">forbidden</span></small> - now there is no access to the station or structure.
 </p>
 <p>
  <small><span class="label label-default">corp_deliveries</span>, <span class="label label-default">office_folder</span>,&hellip;</small> - locations of items.
 </p>
""")
    glf.write("""
</div>
<script>
  // Accounting Options storage (prepare)
  ls = window.localStorage;

  // Accounting Options storage (init)
  function resetOptionsMenuToDefault() {
    if (!ls.getItem('Show Legend')) {
      ls.setItem('Show Legend', 1);
    }
    if (!ls.getItem('Show Blueprints')) {
      ls.setItem('Show Blueprints', 1);
    }
  }
  // Accounting Options storage (rebuild menu components)
  function rebuildOptionsMenu() {
    show = ls.getItem('Show Legend');
    if (show == 1)
      $('#imgShowLegend').removeClass('hidden');
    else
      $('#imgShowLegend').addClass('hidden');
    show = ls.getItem('Show Blueprints');
    if (show == 1)
      $('#imgShowBlueprints').removeClass('hidden');
    else
      $('#imgShowBlueprints').addClass('hidden');
  }
  // Accounting Options storage (rebuild body components)
  function rebuildBody() {
    show = ls.getItem('Show Legend');
    if (show == 1)
      $('#legend-block').removeClass('hidden');
    else
      $('#legend-block').addClass('hidden');
    show = ls.getItem('Show Blueprints');
    $('tr.qind-blueprints-stat').each(function() {
      if (show == 1)
        $(this).removeClass('hidden');
      else
        $(this).addClass('hidden');
    })
  }
  // Accounting Options menu and submenu setup
  $(document).ready(function(){
    $('#btnToggleLegend').on('click', function () {
      show = (ls.getItem('Show Legend') == 1) ? 0 : 1;
      ls.setItem('Show Legend', show);
      rebuildOptionsMenu();
      rebuildBody();
    });
    $('#btnToggleBlueprints').on('click', function () {
      show = (ls.getItem('Show Blueprints') == 1) ? 0 : 1;
      ls.setItem('Show Blueprints', show);
      rebuildOptionsMenu();
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
    rebuildBody();
    // Working with clipboard
    $('a.qind-copy-btn').each(function() {
      $(this).tooltip();
    })
    $('a.qind-copy-btn').bind('click', function () {
      var $temp = $("<input>");
      $("body").append($temp);
      $temp.val($(this).attr('data-copy')).select();
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


def dump_accounting_into_report(
        ws_dir,
        sde_type_ids,
        sde_icon_ids,
        corps_accounting):
    glf = open('{dir}/accounting.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(glf, "Accounting")
        __dump_corp_accounting(glf, sde_type_ids, sde_icon_ids, corps_accounting)
        render_html.__dump_footer(glf)
    finally:
        glf.close()
