<?php
include '../qi_tools_and_utils.php';
include_once '../.settings.php';


function json_market_orders(&$conn, $corporation_id, $trade_hub_id, $product_type_id) {
    $query = <<<EOD
select
 th.is_buy,
 th.price,
 th.volume,
 co.remain
from (
 select
  etho_is_buy as is_buy,
  round(etho_price::numeric,2) as price,
  sum(etho_volume_remain) as volume
 from qi.esi_trade_hub_orders
 where etho_location_id=$2 and etho_type_id=$3
 group by 1, 2
 order by 1, 2 desc
) th
 left outer join (
  select
   ecor_is_buy_order as is_buy,
   round(ecor_price::numeric,2) as price,
   sum(ecor_volume_remain) as remain
  from esi_corporation_orders
  where
   ecor_corporation_id=$1 and
   ecor_location_id=$2 and
   ecor_type_id=$3 and
   not ecor_history
  group by 1, 2
 ) co on (co.is_buy=th.is_buy and co.price=th.price);
EOD;
    $params = array($corporation_id, $trade_hub_id, $product_type_id);
    $market_orders_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $market_orders = pg_fetch_all($market_orders_cursor);
    if ($market_orders)
        foreach ($market_orders as &$o)
        {
            $o['is_buy'] = $o['is_buy'] == 't';
            $o['price'] = floatval($o['price']);
            $o['volume'] = intval($o['volume']);
            if (!is_null($o['remain'])) $o['remain'] = intval($o['remain']);
        }
    echo json_encode($market_orders);
}

//$CORPORATION_ID = 98553333;
//$TRADE_HUB_ID = 60003760;
//$PRODUCT_TYPE_ID = 12775; 1190 - и buy и sell; 25812, 33824, 2873, 11239 - много

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
json_market_orders($conn, $CORPORATION_ID, $TRADE_HUB_ID, $PRODUCT_TYPE_ID);

pg_close();
?>