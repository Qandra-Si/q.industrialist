<?php
include '../qi_tools_and_utils.php';
include_once '../.settings.php';


function json_trade_hub_details(&$conn, $minutes) {
    $query = <<<EOD
select
 h.mh_hub_id as hub,
 h.mh_trader_corp as co,
 h.mh_trader_id as tr,
 ch.ech_name as tnm,
 co.eco_name as cnm,
 co.eco_ticker as cti,
 to_char(hub_prices.updated_at,'yyyy.mm.dd HH24:MI:SS') as uat,
 hub_prices.orders_known as ok,
 hubs_stat.orders_changed as oc
from
 market_hubs h
  left outer join esi_characters as ch on (h.mh_trader_id=ch.ech_character_id)
  left outer join (
   select
    ethp_location_id,
    max(ethp_updated_at) as updated_at,
    (select count(1) from qi.esi_trade_hub_orders where ethp_location_id=etho_location_id) as orders_known
   from qi.esi_trade_hub_prices
   group by 1
  ) as hub_prices on (h.mh_hub_id=hub_prices.ethp_location_id)
  left outer join (
   select
    etho_location_id as location_id,
    count(1) as orders_changed
   from qi.esi_trade_hub_orders
   where etho_updated_at >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - make_interval(mins => $1))
   group by 1
  ) hubs_stat on (h.mh_hub_id=hubs_stat.location_id),
 esi_corporations co
where h.mh_trader_corp=co.eco_corporation_id;
EOD;
    $params = array($minutes);
    $data_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $data = pg_fetch_all($data_cursor);
    if ($data)
        foreach ($data as &$j)
        {
            $j['hub'] = intval($j['hub']);
            $j['co'] = intval($j['co']);
            if (is_null($j['tr'])) unset($j['tr']); else $j['tr'] = intval($j['tr']);
            if (is_null($j['tnm'])) unset($j['tnm']);
            if (is_null($j['cnm'])) unset($j['cnm']);
            if (is_null($j['cti'])) unset($j['cti']);
            if (is_null($j['uat'])) unset($j['uat']);
            if (is_null($j['ok'])) unset($j['ok']); else $j['ok'] = intval($j['ok']);
            if (is_null($j['oc'])) unset($j['oc']); else $j['oc'] = intval($j['oc']);
        }
    echo json_encode($data);
}

if (!isset($_POST['min'])) return; else {
  $_get_min = htmlentities($_POST['min']);
  if (is_numeric($_get_min)) $MINUTEs = get_numeric($_get_min);
  else return;
}

if (!extension_loaded('pgsql')) return;
$conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
        or die('pg_connect err: '.pg_last_error());
pg_exec($conn, "SET search_path TO qi");

ob_end_clean();
header('Content-Type: application/json');
json_trade_hub_details($conn, $MINUTEs);

pg_close();
?>
