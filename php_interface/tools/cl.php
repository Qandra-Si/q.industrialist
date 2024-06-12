<?php
include '../qi_tools_and_utils.php';
include_once '../.settings.php';


function apply_conveyor_limits(&$conn, &$product_type_id, &$hub_ids, &$corporation_ids, &$limit_ids) {
    $insert_query = <<<EOD
insert into conveyor_limits
values($1,$2,$3,$4)
on conflict on constraint pk_cl do update set
 cl_approximate=$4;
EOD;
    $delete_query = <<<EOD
delete from conveyor_limits
where
 cl_type_id=$1 and
 cl_trade_hub=$2 and
 cl_trader_corp=$3;
EOD;
    $index = 0;
    foreach ($limit_ids as &$lim)
    {
        if ($lim != 0)
        {
            $params = array($product_type_id, $hub_ids[$index], $corporation_ids[$index], $lim);
            $data_cursor = pg_query_params($conn, $insert_query, $params)
                    or die('pg_query err: '.pg_last_error());
            $data = pg_fetch_all($data_cursor);
        }
        else
        {
            $params = array($product_type_id, $hub_ids[$index], $corporation_ids[$index]);
            $data_cursor = pg_query_params($conn, $delete_query, $params)
                    or die('pg_query err: '.pg_last_error());
            $data = pg_fetch_all($data_cursor);
        }
        $index++;
    }
}

function json_conveyor_limits(&$conn, &$product_type_ids) {
    $query = <<<EOD
select
 cl_type_id tid,
 cl_trade_hub hub,
 cl_trader_corp corp,
 cl_approximate lim
from conveyor_limits
where cl_type_id=any($1);
EOD;
    $params = array('{'.implode(',',$product_type_ids).'}');
    $data_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $data = pg_fetch_all($data_cursor);
    if ($data)
        foreach ($data as &$l)
        {
            $l['tid'] = intval($l['tid']);
            $l['hub'] = intval($l['hub']);
            $l['corp'] = intval($l['corp']);
            $l['lim'] = intval($l['lim']);
        }
    echo json_encode($data);
}

if (!isset($_POST['tid'])) return; else {
  $_get_tid = htmlentities($_POST['tid']);
  if (!is_numeric($_get_tid)) return;
  $PRODUCT_TYPE_ID = get_numeric($_get_tid);
}
$PRODUCT_TYPE_IDs=array($PRODUCT_TYPE_ID);
if (!isset($_POST['hub'])) return; else {
  $_get_hub = htmlentities($_POST['hub']);
  if (is_numeric($_get_hub)) $HUB_IDs = array(get_numeric($_get_hub));
  else if (is_numeric_array($_get_hub)) $HUB_IDs = get_numeric_array($_get_hub);
  else return;
}
if (!isset($_POST['corp'])) return; else {
  $_get_corp = htmlentities($_POST['corp']);
  if (is_numeric($_get_corp)) $CORPORATION_IDs = array(get_numeric($_get_corp));
  else if (is_numeric_array($_get_corp)) $CORPORATION_IDs = get_numeric_array($_get_corp);
  else return;
}
if (!isset($_POST['limit'])) return; else {
  $_get_limit = htmlentities($_POST['limit']);
  if (is_numeric($_get_limit)) $LIMIT_IDs = array(get_numeric($_get_limit));
  else if (is_numeric_array($_get_limit)) $LIMIT_IDs = get_numeric_array($_get_limit);
  else return;
}

if (!extension_loaded('pgsql')) return;
$conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
        or die('pg_connect err: '.pg_last_error());
pg_exec($conn, "SET search_path TO qi");

ob_end_clean();
header('Content-Type: application/json');
apply_conveyor_limits($conn, $PRODUCT_TYPE_ID, $HUB_IDs, $CORPORATION_IDs, $LIMIT_IDs);
json_conveyor_limits($conn, $PRODUCT_TYPE_IDs);

pg_close();
?>
