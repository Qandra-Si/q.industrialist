<?php
include '../qi_tools_and_utils.php';
include_once '../.settings.php';


function json_corporation_orders(&$conn, $corporation_id, $trade_hub_id, $product_type_id) {
    $query = <<<EOD
select
 o.ecor_order_id as id,
 o.ecor_is_buy_order as is_buy,
 o.ecor_range as range,
 round(o.ecor_price::numeric,2) as price,
 o.ecor_volume_remain remain,
 o.ecor_volume_total-o.ecor_volume_remain as done,
 c.ech_name as trader,
 o.ecor_history as history,
 date_trunc('seconds', o.ecor_issued) as issued
from esi_corporation_orders o
 left outer join esi_characters c on (c.ech_character_id=o.ecor_issued_by)
where
 (not o.ecor_history or (o.ecor_issued >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - make_interval(days => 14)))) and
 o.ecor_corporation_id=$1 and
 o.ecor_location_id=$2 and
 o.ecor_type_id=$3;
EOD;
    $params = array($corporation_id, $trade_hub_id, $product_type_id);
    $corp_orders_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $corp_orders = pg_fetch_all($corp_orders_cursor);
    if ($corp_orders)
        foreach ($corp_orders as &$o)
        {
            $o['history'] = $o['history'] == 't';
            $o['is_buy'] = $o['is_buy'] == 't';
            $o['price'] = floatval($o['price']);
            $o['done'] = intval($o['done']);
            $o['remain'] = intval($o['remain']);
            $o['id'] = intval($o['id']);
        }
    echo json_encode($corp_orders);
}

//$CORPORATION_ID = 98553333;
//$TRADE_HUB_ID = 60003760;
//$PRODUCT_TYPE_ID = 12775; 1190 - и buy и sell; 25812, 33824, 2873, 11239 - много; 44992 - PLEX

if (!isset($_POST['corp'])) return; else {
  $_get_corp = htmlentities($_POST['corp']);
  if (!is_numeric($_get_corp)) return;
  $CORPORATION_ID = get_numeric($_get_corp);
}
if (!isset($_POST['hub'])) return; else {
  $_get_hub = htmlentities($_POST['hub']);
  if (!is_numeric($_get_hub)) return;
  $TRADE_HUB_ID = get_numeric($_get_hub);
}
if (!isset($_POST['tid'])) return; else {
  $_get_tid = htmlentities($_POST['tid']);
  if (!is_numeric($_get_tid)) return;
  $PRODUCT_TYPE_ID = get_numeric($_get_tid);
}

if (!extension_loaded('pgsql')) return;
$conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
        or die('pg_connect err: '.pg_last_error());
pg_exec($conn, "SET search_path TO qi");

ob_end_clean();
header('Content-Type: application/json');
json_corporation_orders($conn, $CORPORATION_ID, $TRADE_HUB_ID, $PRODUCT_TYPE_ID);

pg_close();
?>