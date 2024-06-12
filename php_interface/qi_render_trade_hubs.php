<?php
function __dump_market_hubs_data(&$conn, &$market_hubs) {
  $query = <<<EOD
select
 h.mh_hub_id as hub,
 h.mh_trader_corp as co,
 h.mh_brokers_fee as fee,
 h.mh_trade_hub_tax as tax,
 h.mh_default_profit as pr,
 h.mh_manufacturing_possible as m,
 h.mh_invent_possible as i,
 h.mh_archive as a,
 --c.ech_name as tr,
 s.forbidden as f,
 s.solar_system_name as ss,
 s.station_type_name as snm,
 s.name as nm,
 r.mr_lightyears_src_dst+r.mr_lightyears_dst_src as ly,
 r.mr_isotopes_src_dst+r.mr_isotopes_dst_src as it,
 r.mr_route_src_dst as rs,
 r.mr_route_dst_src as rd
from
 market_hubs h
  --left outer join esi_characters as c on (h.mh_trader_id=c.ech_character_id)
  left outer join market_routes as r on (h.mh_hub_id=r.mr_dst_hub),
 esi_known_stations s
where h.mh_hub_id=s.location_id
order by h.mh_archive, s.forbidden, r.mr_lightyears_dst_src desc;
EOD;
  $params = array();
  $market_hubs_cursor = pg_query_params($conn, $query, $params)
          or die('pg_query err: '.pg_last_error());
  $market_hubs = pg_fetch_all($market_hubs_cursor);

  echo 'g_market_hubs=[';
  foreach ($market_hubs as ["hub" => $hub
           ,"co" => $trader_corp
           ,"fee" => $brokers_fee
           ,"tax" => $trade_hub_tax
           ,"pr" => $default_profit
           ,"m" => $manufacturing_possible
           ,"i" => $invent_possible
           ,"a" => $archive
           ,"f" => $forbidden
           ,"ss" => $solar_system_name
           ,"snm" => $station_type_name
           ,"nm" => $station_name
           ,"ly" => $lightyears
           ,"it" => $isotopes
           ,"rs" => $route_to
           ,"rd" => $route_from
          ])
  {
    echo '['.
            $hub.','. //0
            $trader_corp.','. //1
            $brokers_fee.','. //2
            $trade_hub_tax.','. //3
            $default_profit.','. //4
            (($manufacturing_possible=='t')?1:0).','. //5
            (($invent_possible=='t')?1:0).','. //6
            (($archive=='t')?1:0).','. //7
            (($forbidden=='t')?1:0).','. //8
            '"'.$solar_system_name.'",'. //9
            '"'.$station_type_name.'",'. //10
            '"'.str_replace('"','\"',$station_name).'",'. //11
            (is_null($lightyears)?'null':'"'.$lightyears.'"').','. // 12
            (is_null($isotopes)?'null':'"'.$isotopes.'"').','. //13
            (is_null($route_to)?'null':'"'.$route_to.'"').','. //14
            (is_null($route_from)?'null':'"'.$route_from.'"'). //15
         "],\n";
  }
  echo "null];\n";
}

function get_active_market_hub_ids(&$market_hubs, &$active_market_hub_ids, &$active_trader_corp_ids)
{
  foreach ($market_hubs as ["hub" => $hub, "co" => $co, "a" => $a, "f" => $f])
  {
    if ($a == 't' || $f == 't') continue; // archive or forbidden
    $active_market_hub_ids[] = intval($hub);
    $active_trader_corp_ids[] = intval($co);
  }
  $active_market_hub_ids = array_unique($active_market_hub_ids, SORT_NUMERIC);
  $active_trader_corp_ids = array_unique($active_trader_corp_ids, SORT_NUMERIC);
}

function __dump_market_hubs_dialog(&$market_hubs) { ?>
<style>
table.table-market-hubs thead tr th:nth-child(2),
table.table-market-hubs thead tr th:nth-child(3),
table.table-market-hubs thead tr th:nth-child(4),
table.table-market-hubs thead tr th:nth-child(5),
table.table-market-hubs thead tr th:nth-child(6),
table.table-market-hubs thead tr th:nth-child(7),
table.table-market-hubs tbody tr td:nth-child(2),
table.table-market-hubs tbody tr td:nth-child(3),
table.table-market-hubs tbody tr td:nth-child(4),
table.table-market-hubs tbody tr td:nth-child(5),
table.table-market-hubs tbody tr td:nth-child(6),
table.table-market-hubs tbody tr td:nth-child(7) { text-align: right; }
</style>
<div class="modal fade" id="modalMarketHubs" tabindex="-1" role="dialog" aria-labelledby="modalMarketHubs">
 <div class="modal-dialog modal-lg" role="document">
  <div class="modal-content">
   <div class="modal-header">
    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
    <h4 class="modal-title" id="modalMarketHubsLabel"></h4>
   </div>
   <div class="modal-body">
   <!-- -->
<form id="frmMarketHubDetails">
 <input type="hidden" name="min" readonly value="">
</form>
<h3>Активные хабы</h3>
<table id="tblHubs" class="table table-condensed table-market-hubs table-hover" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th>Хаб</th>
  <th>Актуальность</th>
  <th>Пошлина<br>КпБТ,%</th>
  <th>Комиссия<br>брокера,%</th>
  <th>Налог с<br>продаж,%</th>
  <th>Маржа,%</th>
  <th>Дистанция,сл<br>Изотопы,шт</th>
  <th>Маршрут</th>
 </tr>
</thead>
<tbody>
</tbody>
</table>
<p>В списках выше перечислены торговые хабы, в которых наши корпорации выставляли сделки и ведут торговую деятельность. Имена пилотов, которые упомянуты, появляются в списках либо в результате массовой торговой деятельности, либо фиксируются в базе данных при добавлении нового хаба. Актуальность отображает дату/время последних операций на рынке (вообще всех операций, а не только корпоративных); отображает количество известных на данный сомент ордеров и количество зафиксированных изменений в ордерах за последние X минут.</p>
<p>Пошлина КпБП - процент от ордера, который выплачивается комиссии по безопасной торговле (прямой вывод ССР). Комиссия брокера устанавливается владельцем структуры. Налог с продаж зависит от скилов пилота. Маржа - задаёт профит по сделкам, принятый для торговли на этой структуре (используется в автоматических расчётах в качестве рекомендованного уровня "жадности", однако не отражает рыночную ситуацию в целом, т.ч. остаётся на усмотрение торговца).</p>
<p>Дистанция показывает кол-во световых лет туда-и-обратно, которые рассчитываются прыжками <mark>Rhea</mark> со скилами в 5. Изотопами считаются <mark>Nitrogen Isotopes</mark> на пути туда-и-обратно на <mark>Rhea</mark> со скилами в 5. См. также ссылки на маршруты в торговый хаб и обратно в домашку.</p>
<h3>Архивные хабы</h3>
<table id="tblArchiveHubs" class="table table-condensed table-market-hubs" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th>Хаб</th>
  <th>Актуальность</th>
  <th>Пошлина<br>КпБТ,%</th>
  <th>Комиссия<br>брокера,%</th>
  <th>Налог с<br>продаж,%</th>
  <th>Маржа,%</th>
  <th>Дистанция,сл<br>Изотопы,шт</th>
  <th>Маршрут</th>
 </tr>
</thead>
<tbody>
</tbody>
</table>
   <!-- -->
   </div>
   <div class="modal-footer">
    <button type="button" class="btn btn-default" data-dismiss="modal">Закрыть</button>
   </div>
  </div>
 </div>
</div>
<?php }

?>
