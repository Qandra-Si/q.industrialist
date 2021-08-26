<?php
include 'qi_render_html.php';
include_once '.settings.php';
?>

<?php function __dump_cyno_route($route_id, $route_desc, $paths) { ?>
<div class="panel panel-success qind-route">
  <div class="panel-heading"></div>
  <div class="panel-body">
   <form class="form-horizontal">
    <div class="form-group">
     <label class="col-sm-1 control-label">Карта</label>
     <div class="col-sm-11"><span class="qind-map"></span></div>
    </div>
    <div class="form-group">
     <label for="inputDescr" class="col-sm-1 control-label">Примечание</label>
     <div class="col-sm-11">
      <input type="text" class="form-control" id="inputDescr" value="<?=is_null($route_desc)?'(no data)':$route_desc?>">
     </div>
    </div>
    <div class="form-group">
     <div class="col-sm-offset-1 col-sm-11">
      <div class="btn-toolbar" role="toolbar" aria-label="...">
       <div class="btn-group btn-group-sm" role="group" aria-label="...">
        <button type="button" class="btn btn-default qind-edit">Изменить маршрут</button>
        <button type="button" class="btn btn-default disabled qind-commit">Подтвердить изменения</button>
       </div>
       <div class="btn-group btn-group-sm" role="group" aria-label="...">
        <button type="button" class="btn btn-default qind-remove">Удалить</button>
       </div>
      </div>
     </div>
    </div>
   </form>
  </div>
  <ul class="list-group">
    <?php foreach ($paths as $node) { ?>
    <li class="list-group-item qind-node" location_id="<?=$node?>"><?=$node?></li>
    <?php } ?>
  </ul>
</div>
<?php } ?>

<?php function __dump_cyno_network_routes($routes, $paths, $offices) {
    foreach ($routes as $route)
    {
        $route_id = $route['cnr_route_id'];
        $route_desc = $route['cnr_description'];
        $route = array();
        foreach ($paths as $node) {
            if ($node['cnr_route_id'] != $route_id) continue;
            array_push($route, $node['location_id']);
        }
        __dump_cyno_route($route_id, $route_desc, $route);
    }
} ?>

<?php
    __dump_header("Cyno Network", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
select sden_id as id, sden_name as name
from eve_sde_names
where sden_id >= 30000000 and sden_id <= 32000000
order by 1;
EOD;
    $solar_systems_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $solar_systems = pg_fetch_all($solar_systems_cursor);
    //---
    $query = <<<EOD
select
  cnr_route_id,
  cnr_description
from cyno_network_routes;
EOD;
    $routes_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $routes = pg_fetch_all($routes_cursor);
    //---
    $query = <<<EOD
select
  cnr_route_id,
  idx,
  cnr_path[idx] as location_id
from
  cyno_network_routes,
  lateral generate_subscripts(cnr_path, 1) as idx
order by 1, 2;
EOD;
    $paths_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $paths = pg_fetch_all($paths_cursor);
    //---
    $query = <<<EOD
select
 s.location_id,
 s.name,
 s.system_id as solar_system_id,
 s.type_id as station_type_id,
 sol.sden_name as solar_system_name,
 strct.sden_name as station_type_name,
 coalesce(s.forbidden,false) as forbidden
from (
 select
  a.eca_location_id as location_id,
  s.ets_name as name,
  s.ets_system_id as system_id,
  s.ets_type_id as type_id,
  false as forbidden
 from
  esi_corporation_assets a
    left outer join esi_tranquility_stations s on (a.eca_location_id = s.ets_station_id)
 where
  a.eca_type_id = 27 and -- Office
  a.eca_corporation_id = 98615601 and -- RI4
  a.eca_location_id < 1000000000
 union
 select
  a.eca_location_id,
  s.eus_name,
  s.eus_system_id,
  s.eus_type_id,
  s.eus_forbidden
 from
  esi_corporation_assets a
    left outer join esi_universe_structures s on (a.eca_location_id = s.eus_structure_id)
 where
  a.eca_type_id = 27 and -- Office
  a.eca_corporation_id = 98615601 and -- RI4
  a.eca_location_id >= 1000000000
 ) s
 left outer join eve_sde_names sol on (sol.sden_category = 3 and sol.sden_id = s.system_id) -- cat:3 invNames
 left outer join eve_sde_names strct on (strct.sden_category = 1 and strct.sden_id = s.type_id); -- cat:1 typeIDs
EOD;
    $offices_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $offices = pg_fetch_all($offices_cursor);
    //---
    pg_close($conn);
?>
<div class="container-fluid">
<?php __dump_cyno_network_routes($routes, $paths, $offices); ?>
</div> <!--container-fluid-->

<div class="modal fade" tabindex="-1" role="dialog" aria-labelledby="modal-remove-label" id="modal-remove">
 <div class="modal-dialog modal-sm" role="document">
  <div class="modal-content">
   <div class="modal-header">
    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
    <h4 class="modal-title" id="modal-remove-label"></h4>
   </div>
   <div class="modal-body">
    <form  id="frm-remove">
     <div class="form-group">
      <label for="ed-magic-word" class="control-label">Волшебное слово</label>
      <input type="text" class="form-control" id="ed-magic-word">
     </div>
    </form>
   </div>
   <div class="modal-footer">
    <button type="submit" class="btn btn-primary" onclick="$('#frm-remove').submit();" id="btn-remove">Удалить</button>
    <button type="button" class="btn btn-default" data-dismiss="modal">Передумал</button>
   </div>
  </div>
 </div>
</div>

<script>
  var g_solar_systems = [ <?php foreach ($solar_systems as $ss) echo '['.$ss['id'].',\''.$ss['name'].'\'],'; ?> [0,'']];
  var g_offices = [ <?php foreach ($offices as $o) echo sprintf(
    "[%d,'%s',%d,'%s',%d],\n",
    $o['location_id'], // 0
    is_null($o['name']) ? null : str_replace('\'', '\\\'', $o['name']), // 1
    is_null($o['solar_system_id']) ? null : $o['solar_system_id'], // 2
    is_null($o['station_type_name']) ? null : str_replace('\'', '\\\'', $o['station_type_name']), // 3
    (is_null($o['forbidden'])||($o['forbidden']=='f'))?0:1); // 4 ?>
    [0,null,null,null,0]
  ];
  function getSolarSystemName(id) {
    if (id === null) return null;
    for (var i = 0, cnt = g_solar_systems.length; i < cnt; ++i) {
      if (g_solar_systems[i][0] == id) return g_solar_systems[i][1];
      if (g_solar_systems[i][0] > id) break;
    }
    return null;
  }
  function getOffice(id) {
    for (var i = 0, cnt = g_offices.length; i < cnt; ++i) if (g_offices[i][0] == id) return g_offices[i];
    return null;
  }
  function checkMagicWord(ed, btn) {
    var ok = ed.val().toLowerCase() == 'пожалуйста';
    btn.prop('disabled', !ok);
    return ok;
  }
  function rebuildBody() {
    $('div.qind-route').each(function() {
      var solars_dots = '', solars_dash = '';
      var warning = false;
      var div = $(this);
      var pnhead = div.find('div.panel-heading');
      var pnbody = div.find('div.panel-body');
      div.find('li.qind-node').each(function() {
        var location_id = $(this).attr('location_id');
        var office = getOffice(location_id);
        var solar = null, name = null, type_name = null, forbidden = null;
        if (office === null)
          warning = true;
        else {
          solar = getSolarSystemName(office[2]);
          name = office[1];
          type_name = office[3];
          forbidden = office[4];
          if ((name === null) || forbidden || (solar === null))
            warning = true;
        }
        //---
        var txt = '<div class="row">';
        if (!(solar === null)) {
          txt += '<div class="col-md-2"><b>'+solar+'</b></div>';
          if (!(name === null)) {
            txt += '<div class="col-md-10">'+name;
            if (!(type_name === null))
              txt += ' <mark><small>'+type_name+'</small></mark>';
            if (forbidden)
              txt += ' <span class="label label-danger">forbidden</span>';
            txt += '</div>';
          }
        }
        else {
          txt += '<div class="col-md-2"><small>(unknown solar system)</small></div>';
          txt += '<div class="col-md-10">&nbsp;</div>';
        }
        txt += '</div>';
        $(this).html(txt);
        //---
        solars_dots += ':'
        if (!(solar === null)) solars_dots += solar;
        //---
        if (solars_dash.length) solars_dash += ' - ';
        if (solar === null) solars_dash += '(no data)'; else solars_dash += solar;
      })
      var map_url = 'https://evemaps.dotlan.net/jump/Rhea,555/' + solars_dots.substring(1);
      pnhead.html('Jump route: ' + solars_dash);
      pnbody.find('span.qind-map').html('<a href="'+map_url+'">'+map_url+'</a>');
      if (warning) {
        div.removeClass('panel-success');
        div.addClass('panel-danger');
      } else {
        div.addClass('panel-success');
        div.removeClass('panel-danger');
      }
    })
    $('.qind-remove').on('click', function () {
      var modal = $("#modal-remove");
      $('#btn-remove').prop('disabled', true);
      modal.modal('show');
    });
    $('#ed-magic-word').on('keyup change', function (e) {
      checkMagicWord($('#ed-magic-word'), $('#btn-remove'));
    })
    $('#ed-magic-word').on('keypress', function (e) {
      if (e.which == 13) {
        if (checkMagicWord($('#ed-magic-word'), $('#btn-remove')))
         $('#btn-remove').click();
        else {
         e.preventDefault();
         return false;
        }
      }
    })
  }
  $(document).ready(function(){
    rebuildBody();
  });
</script>
<?php __dump_footer(); ?>