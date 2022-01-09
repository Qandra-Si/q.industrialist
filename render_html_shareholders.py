import render_html


def __dump_corp_shareholders(
        glf,
        # настройки генерации отчёта
        shareholders_data):
    glf.write("""
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
</style>

<div class="container-fluid">
<div class="table-responsive">
 <table class="table table-condensed table-striped" style="font-size:small">
<thead>
 <tr>
  <th class="hvr-icon-fade" id="thSortSel" col="0" style="width:40px;">#<span class="glyphicon glyphicon-sort hvr-icon" aria-hidden="true"></span></th>
  <th class="hvr-icon-fade" id="thSortSel" col="1">Shareholder<span class="glyphicon glyphicon-sort hvr-icon" aria-hidden="true"></span></th>
  <th class="hvr-icon-fade" id="thSortSel" col="2">Corporation<span class="glyphicon glyphicon-sort hvr-icon" aria-hidden="true"></span></th>
  <th class="hvr-icon-fade" id="thSortSel" col="3">Count<span class="glyphicon glyphicon-sort hvr-icon" aria-hidden="true"></span></th>
 </tr>
</thead>
<tbody>
""")
    shareholders = shareholders_data['shareholders']
    characters = shareholders_data['characters']
    corporations = shareholders_data['corporations']
    num = 1
    for shareholder in shareholders:
        if shareholder['shareholder_type'] == 'corporation':
            corp_id = shareholder['shareholder_id']
            corp_dict = corporations.get(str(corp_id))
            corp_name = corp_dict['name']
            glf.write('<tr>\n'
                      ' <td scope="row">{num}</td>\n'
                      ' <td><span class="label label-info">corporation</span></td>'
                      ' <td><b>{nm}</b></td>\n'
                      ' <td align="right" x-data="{q}">{q:,d}</td>\n'
                      '</tr>'.
                      format(
                          num=num,
                          nm=corp_name,
                          q=shareholder['share_count']
                      ))
        elif shareholder['shareholder_type'] == 'character':
            pilot_id = shareholder['shareholder_id']
            pilot_dict = characters.get(str(pilot_id))  # пилот м.б. быть в списке с dict=None
            pilot_name = pilot_dict["name"] if pilot_dict else "Deleted #"+str(pilot_id)
            if pilot_dict:
                corp_id = pilot_dict['corporation_id']
                corp_dict = corporations.get(str(corp_id))
                corp_name = corp_dict['name']
            else:
                corp_name = ''
            glf.write('<tr>\n'
                      ' <td scope="row">{num}</td>\n'
                      ' <td><mark>{nm}</mark></td>\n'
                      ' <td>{cnm}</td>\n'
                      ' <td align="right" x-data="{q}">{q:,d}</td>\n'
                      '</tr>'.
                      format(
                          num=num,
                          nm=pilot_name,
                          cnm=corp_name,
                          q=shareholder['share_count']
                      ))
        num += 1
    glf.write("""
</tbody>
</table>
</div> <!--table-responsive-->
</div> <!--container-fluid-->

<script>
  // Shareholders Options dictionaries
  var g_tbl_col_types = [1,0,0,2]; // 0:str, 1:num, 2:x-data
  var g_tbl_filter = null;

  // Tools & Utils
  function numLikeEve(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }
  // Shareholders table sorter
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

  // Blueprints Options menu and submenu setup
  $(document).ready(function(){
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
    // first init
  });
</script>
""")


def dump_shareholders_into_report(
        ws_dir,
        shareholders_data):
    corporation_name = shareholders_data["corporation"]["name"]
    glf = open('{dir}/shareholders_{fnm}.html'.format(dir=ws_dir, fnm=render_html.__camel_to_snake(corporation_name, True)), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(glf, 'Shareholders of {}'.format(corporation_name))
        __dump_corp_shareholders(glf, shareholders_data)
        render_html.__dump_footer(glf)
    finally:
        glf.close()
