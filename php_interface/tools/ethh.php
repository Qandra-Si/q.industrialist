<?php
include '../qi_tools_and_utils.php';
include_once '../.settings.php';


function json_history_orders(&$conn, $corporation_ids, $trade_hub_id, $product_type_id) {
    $query = <<<EOD
select
 ethh_updated_at::date as date,
 ethh_is_buy as is_buy,
 round(ethh_price::numeric,2) as price,
 ethh_volume_total-ethh_volume_remain as volume,
 ethh_volume_total as total,
 case ethh_done is null when true then date_trunc('minutes', (CURRENT_TIMESTAMP AT TIME ZONE 'GMT')-ethh_issued)
 else date_trunc('minutes', ethh_done-ethh_issued) end as duration,
 case ethh_done is null when true then 0 else 1 end as closed,
 o.ecor_corporation_id as corp
from esi_trade_hub_history
 left outer join (select ecor_corporation_id,ecor_order_id from esi_corporation_orders) o on (
  o.ecor_corporation_id=any($1) and
  o.ecor_order_id=ethh_order_id
 )
where ethh_location_id = $2 and ethh_type_id = $3
order by ethh_updated_at desc, ethh_price desc
limit 50;
EOD;
    $params = array('{'.implode(',',$corporation_ids).'}',$trade_hub_id, $product_type_id);
    $history_orders_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $history_orders = pg_fetch_all($history_orders_cursor);
    if ($history_orders)
    {
        $prev_date = '';
        foreach ($history_orders as &$o)
        {
            if ($prev_date != $o['date']) $prev_date = $o['date']; else unset($o['date']);
            if ($o['is_buy'] == 't') $o['buy'] = floatval($o['price']); else $o['sell'] = floatval($o['price']);
            unset($o['is_buy']);
            unset($o['price']);
            $o['volume'] = intval($o['volume']);
            $o['total'] = intval($o['total']);
            $o['duration'] = strval(rtrim($o['duration'],':00'));
            $o['closed'] = $o['closed'] == 1;
            if (is_null($o['corp'])) unset($o['corp']); else $o['corp'] = intval($o['corp']);
        }
    }
    echo json_encode($history_orders);
}

//$TRADE_HUB_ID = 60003760;
//$PRODUCT_TYPE_ID = 2876 - много транзакций

if (!isset($_POST['corp'])) return; else {
  $_get_corp = htmlentities($_POST['corp']);
  if (is_numeric($_get_corp)) $CORPORATION_IDs = array(get_numeric($_get_corp));
  else if (is_numeric_array($_get_corp)) $CORPORATION_IDs = get_numeric_array($_get_corp);
  else return;
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
json_history_orders($conn, $CORPORATION_IDs, $TRADE_HUB_ID, $PRODUCT_TYPE_ID);

pg_close();
?>