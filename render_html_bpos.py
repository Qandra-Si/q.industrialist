import render_html


def __dump_market_groups_tree_nested(
        group_id,
        sde_market_groups,
        sde_icon_ids,
        market_groups_tree,
        market_data,
        market_data_printer):
    if not (str(group_id) in market_data) and not ("items" in market_groups_tree[str(group_id)]):
        return ""
    sde_group = sde_market_groups[str(group_id)]
    icon_id = sde_group["iconID"] if "iconID" in sde_group else 0
    tbl_glf = market_data_printer(group_id, market_data)
    sub_glf = ''
    if "items" in market_groups_tree[str(group_id)]:
        for group_id in market_groups_tree[str(group_id)]["items"]:
            sub_glf = sub_glf + __dump_market_groups_tree_nested(
                group_id,
                sde_market_groups,
                sde_icon_ids,
                market_groups_tree,
                market_data,
                market_data_printer
            )
    if not tbl_glf and not sub_glf:
        return ""
    glf = '' \
          '<div class="media">\n' \
          ' <div class="media-left media-top">{img}</div>\n' \
          ' <div class="media-body">\n' \
          '  <h4 class="media-heading">{nm}</h4>\n' \
          '{tbl}{sub}' \
          ' </div>\n' \
          '</div>\n'.format(
            img='<img class="media-object icn32" src="{src}">'.format(src=render_html.__get_icon_src(icon_id, sde_icon_ids)),
            nm=sde_group["nameID"]["en"],
            tbl=tbl_glf,
            sub=sub_glf
          )
    return glf


def __dump_market_groups_tree(glf, sde_market_groups, sde_icon_ids, market_groups_tree, market_data, market_data_printer):
    glf.write("""<ul class="media-list">
 <li class="media">""")

    if "roots" in market_groups_tree:
        roots = market_groups_tree["roots"]
        for group_id in roots:
            glf.write(
                __dump_market_groups_tree_nested(
                    group_id,
                    sde_market_groups,
                    sde_icon_ids,
                    market_groups_tree,
                    market_data,
                    market_data_printer)
            )

    glf.write(""" </li>
</ul>""")


def dump_bpos_into_report(
        ws_dir,
        sde_type_ids,
        sde_market_groups,
        sde_icon_ids,
        sde_bp_materials,
        corp_assets_data,
        corp_blueprints_data,
        market_groups_tree):
    market_data = {}
    for a in corp_assets_data:
        if not (str(a["type_id"]) in sde_bp_materials):
            continue
        if ("is_blueprint_copy" in a) and a["is_blueprint_copy"]:
            continue
        item_id = a["item_id"]
        blueprint = next((b for b in corp_blueprints_data if b["item_id"] == item_id), None)
        if blueprint is None:
            continue
        type_id = sde_type_ids[str(a["type_id"])]
        data_item = {
            "type_id": int(a["type_id"]),
            "name": type_id["name"]["en"],
            "me": blueprint["material_efficiency"],
            "te": blueprint["time_efficiency"],
            "quantity": 1
        }
        if "basePrice" in type_id:
            data_item["price"] = type_id["basePrice"]
        group_id = type_id["marketGroupID"]
        if not (str(group_id) in market_data):
            market_data[str(group_id)] = [data_item]
        else:
            prev_items = market_data[str(group_id)]
            found = False
            for prev in prev_items:
                if (prev["type_id"] == data_item["type_id"]) and (prev["me"] == data_item["me"])  and (prev["te"] == data_item["te"]):
                    prev["quantity"] = prev["quantity"] + 1
                    found = True
                    break
            if not found:
                market_data[str(group_id)].append(data_item)

    def blueprints_printer(group_id, market_data):
        if not (str(group_id) in market_data):
            return ""
        res = """<table class="table" style="width: unset; max-width: unset; margin-bottom: 0px;">
<thead>
 <tr>
 <th style="width:30px;">#</th>
 <th style="width:300px;">Blueprint</th>
 <th style="width:125px;">Base Price</th>
 <th style="width:85px;">Material Efficiency</th>
 <th style="width:85px;">Time Efficiency</th>
 <th style="width:75px;">Quantity</th>
 </tr>
</thead>
<tbody>
"""  # width: 700px
        items = market_data[str(group_id)]
        num = 1
        for item in items:
            res = res + '<tr>' \
                        '<th scope="row">{num}</th>' \
                        '<td>{nm}</td>' \
                        '<td>{prc}</td>' \
                        '<td>{me}</td>' \
                        '<td>{te}</td>' \
                        '<td>{q}</td>' \
                        '</tr>\n'.format(
                            num=num,
                            nm=item["name"],
                            prc='{:,.1f}'.format(item["price"]) if "price" in item else "",
                            me=item["me"],
                            te=item["te"],
                            q=item["quantity"]
                        )
            num = num + 1
        res = res + """</tbody>
</table>"""
        return res

    glf = open('{dir}/bpos.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(glf, "BPOs")
        glf.write("<div class='container-fluid'>\n")
        __dump_market_groups_tree(glf, sde_market_groups, sde_icon_ids, market_groups_tree, market_data, blueprints_printer)
        glf.write("</div>\n")
        render_html.__dump_footer(glf)
    finally:
        glf.close()
