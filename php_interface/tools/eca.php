<?php
include '../qi_tools_and_utils.php';
include_once '../.settings.php';


function json_corporation_assets(&$conn, &$corporation_ids, &$product_type_ids) {
    $query = <<<EOD
select
 eca_corporation_id as corp,
 eca_type_id as tid,
 eca_name as nm,
 eca_location_id as lid,
 eca_location_flag as lfl,
 loc.nm as lnm, -- location name
 sum(eca_quantity) as qty,
 min(date_trunc('seconds', eca_created_at)) as cat,
 max(date_trunc('seconds', eca_updated_at)) as uat
from esi_corporation_assets
 left outer join eve_sde_type_ids tid on (tid.sdet_type_id=eca_type_id)
 left outer join (
  select eca_item_id id,eca_name nm, eca_location_flag fl
  from esi_corporation_assets
 ) loc on (loc.id=eca_location_id)
where
 eca_type_id=any($2) and
 eca_corporation_id=any($1)
group by eca_corporation_id, eca_type_id, eca_name, eca_location_id, eca_location_flag, loc.nm
order by eca_corporation_id, eca_location_flag, eca_location_id;
EOD;
    $params = array('{'.implode(',',$corporation_ids).'}', '{'.implode(',',$product_type_ids).'}');
    $data_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $data = pg_fetch_all($data_cursor);
    if ($data)
        foreach ($data as &$o)
        {
            //if ($o['is_buy'] == 't') $o['buy'] = floatval($o['price']); else $o['sell'] = floatval($o['price']);
            //unset($o['is_buy']);
            $o['tid'] = intval($o['tid']);
            $o['lid'] = intval($o['lid']);
            $o['qty'] = intval($o['qty']);
            if (is_null($o['corp'])) unset($o['corp']); else $o['corp'] = intval($o['corp']);
        }
    echo json_encode($data);
}

if (!isset($_POST['corp'])) return; else {
  $_get_corp = htmlentities($_POST['corp']);
  if (is_numeric($_get_corp)) $CORPORATION_IDs = array(get_numeric($_get_corp));
  else if (is_numeric_array($_get_corp)) $CORPORATION_IDs = get_numeric_array($_get_corp);
  else return;
}
if (!isset($_POST['tid'])) return; else {
  $_get_tid = htmlentities($_POST['tid']);
  if (is_numeric($_get_tid)) $PRODUCT_TYPE_IDs = array(get_numeric($_get_tid));
  else if (is_numeric_array($_get_tid)) $PRODUCT_TYPE_IDs = get_numeric_array($_get_tid);
  else return;
}

if (!extension_loaded('pgsql')) return;
$conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
        or die('pg_connect err: '.pg_last_error());
pg_exec($conn, "SET search_path TO qi");

ob_end_clean();
header('Content-Type: application/json');
json_corporation_assets($conn, $CORPORATION_IDs, $PRODUCT_TYPE_IDs);

pg_close();
?>
