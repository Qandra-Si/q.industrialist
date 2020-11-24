from typing import Dict, Optional

import render_html
import eve_sde_tools
import eve_esi_tools
from eve.esi import MarketPrice
from eve.sde import SDEItem
from eve.domain import Asset

def __dump_corp_assets_tree_nested(
        glf,
        parent_location_id,
        location_id,
        corp_assets_data,
        corp_assets_tree,
        corp_ass_names_data,
        foreign_structures_data,
        eve_market_prices_data: Dict[int, MarketPrice],
        sde_type_ids,
        sde_inv_names,
        sde_inv_items: Dict[int, SDEItem],
        sde_market_groups):
    region_id, region_name, loc_name, foreign = eve_esi_tools.get_assets_location_name(
        location_id,
        sde_inv_names,
        sde_inv_items,
        corp_ass_names_data,
        foreign_structures_data)
    itm_dict: Optional[Asset] = None
    loc_dict = corp_assets_tree[str(location_id)]
    type_id = loc_dict["type_id"] if "type_id" in loc_dict else None
    group_id = eve_sde_tools.get_basis_market_group_by_type_id(sde_type_ids, sde_market_groups, type_id)
    items = loc_dict["items"] if "items" in loc_dict else None
    nested_quantity = None
    items_quantity = None
    base_price = None
    volume = None
    if not (items is None):
        nested_quantity = len(items)
    if itm_dict is None:
        itm_dict = corp_assets_data[loc_dict["index"]] if "index" in loc_dict else None
    if not (itm_dict is None):
        items_quantity = itm_dict.quantity
        if str(type_id) in sde_type_ids:
            __type_dict = sde_type_ids[str(type_id)]
            if "basePrice" in __type_dict:
                base_price = __type_dict["basePrice"] * items_quantity
            if "volume" in __type_dict:
                volume = __type_dict["volume"] * items_quantity
    if type_id is None:
        market_price = None
    else:
        market_price = eve_market_prices_data.get(type_id, None)
    glf.write(
        '<div class="media">\n'
        ' <div class="media-left media-top">{img}</div>\n'
        ' <div class="media-body">\n'
        '  <h4 class="media-heading" id="id{id}">{where}{what}{iq}{nq}</h4>\n'
        '  {parent_id}<span class="label label-info">{id}</span>{loc_flag}{foreign}\n'
        '  {grp}{base}{average}{adjusted}{volume}\n'.
        format(
            img='<img class="media-object icn32" src="{src}">'.format(src=render_html.__get_img_src(type_id, 32)) if not (type_id is None) else "",
            where='{} '.format(loc_name) if not (loc_name is None) else "",
            what='<small>{}</small> '.format(eve_sde_tools.get_item_name_by_type_id(sde_type_ids, type_id)) if not (type_id is None) else "",
            parent_id='<a href="#id{id}"><span class="label label-primary">parent:{id}</span></a> '.format(id=parent_location_id) if not (parent_location_id is None) else "",
            id=location_id,
            nq=' <span class="badge">{}</span>'.format(items_quantity) if not (items_quantity is None) and (items_quantity > 1) else "",
            iq=' <span class="label label-info">{}</span>'.format(nested_quantity) if not (nested_quantity is None) and (nested_quantity > 1) else "",
            loc_flag=' <span class="label label-default">{}</span>'.format(itm_dict.location_flag) if not (itm_dict is None) else "",
            foreign='<br/><span class="label label-warning">foreign</span>' if foreign else "",
            grp='</br><span class="label label-success">{}</span>'.format(sde_market_groups[str(group_id)]["nameID"]["en"]) if not (group_id is None) else "",
            base='</br>base: {:,.1f} ISK'.format(base_price) if not (base_price is None) else "",
            average='</br>average: {:,.1f} ISK'.format(market_price.average_price*items_quantity) if not (items_quantity is None) and not (market_price is None) and (market_price.average_price >0) else "",
            adjusted='</br>adjusted: {:,.1f} ISK'.format(market_price.adjusted_price*items_quantity) if not (items_quantity is None) and not (market_price is None) and (market_price.average_price >0) else "",
            volume='</br>{:,.1f} m&sup3'.format(volume) if not (volume is None) else ""
        )
    )
    if not (items is None):
        for itm in items:
            __dump_corp_assets_tree_nested(
                glf,
                location_id,
                itm,
                corp_assets_data,
                corp_assets_tree,
                corp_ass_names_data,
                foreign_structures_data,
                eve_market_prices_data,
                sde_type_ids,
                sde_inv_names,
                sde_inv_items,
                sde_market_groups)
    glf.write(
        ' </div>\n'
        '</div>\n'
    )


def __dump_corp_assets_tree(
        glf,
        corp_assets_data,
        corp_assets_tree,
        corp_ass_names_data,
        foreign_structures_data,
        eve_market_prices_data,
        sde_type_ids,
        sde_inv_names,
        sde_inv_items: Dict[int, SDEItem],
        sde_market_groups):
    glf.write("""
<!-- BEGIN: collapsable group (locations) -->
<div class="panel-group" id="accordion" role="tablist" aria-multiselectable="true">
  <ul class="media-list">
    <li class="media">""")

    if "roots" in corp_assets_tree:
        roots = corp_assets_tree["roots"]
        for loc_id in roots:
            __dump_corp_assets_tree_nested(
                glf,
                None,
                loc_id,
                corp_assets_data,
                corp_assets_tree,
                corp_ass_names_data,
                foreign_structures_data,
                eve_market_prices_data,
                sde_type_ids,
                sde_inv_names,
                sde_inv_items,
                sde_market_groups)

    glf.write("""    </li>
  </ul>
</div>
<!-- END: collapsable group (locations) -->
""")


def dump_assets_tree_into_report(
        ws_dir,
        sde_type_ids,
        sde_inv_names,
        sde_inv_items: Dict[int, SDEItem],
        sde_market_groups,
        corp_assets_data,
        corp_ass_names_data,
        foreign_structures_data,
        eve_market_prices_data: Dict[int, MarketPrice],
        corp_assets_tree):
    glf = open('{dir}/assets_tree.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(glf, "Corp Assets")

        #__dump_any_into_modal_header(glf, "Corp Assets")
        __dump_corp_assets_tree(glf, corp_assets_data, corp_assets_tree, corp_ass_names_data, foreign_structures_data, eve_market_prices_data, sde_type_ids, sde_inv_names, sde_inv_items, sde_market_groups)
        #__dump_any_into_modal_footer(glf)

        render_html.__dump_footer(glf)
    finally:
        glf.close()
