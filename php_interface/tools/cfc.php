<?php
include '../qi_tools_and_utils.php';
include_once '../.settings.php';


function json_conveyor_formula_calculus(&$conn, $corporation_ids, $trade_hub_id, $product_type_id) {
    $query = <<<EOD
select
 cfc_formula formula,
 f.cf_blueprint_type_id blueprint_type_id,
 fb.sdet_type_name blueprint,
 f.cf_activity activity,
 --f.cf_product_type_id product_type_id,
 f.cf_decryptor_type_id decryptor_type_id,
 fd.sdet_type_name decryptor,
 f.cf_ancient_relics ancient_relics,
 f.cf_prior_blueprint_type_id prior_blueprint_type_id,
 fpb.sdet_type_name prior_blueprint,
 f.cf_customized_runs customized_runs,
 cfc_products_per_single_run products_per_single_run,
 cfc_products_num products_num,
 cfc_best_choice best_choice,
 --cfc_industry_hub industry_hub,
 --cfc_trade_hub trade_hub,
 --cfc_trader_corp trader_corp,
 cfc_buying_brokers_fee buying_brokers_fee,
 cfc_sales_brokers_fee sales_brokers_fee,
 cfc_sales_tax sales_tax,
 cfc_fuel_price_isk fuel_price_isk,
 cfc_materials_cost materials_cost,
 cfc_materials_cost_with_fee materials_cost_with_fee,
 cfc_purchase_volume purchase_volume,
 cfc_materials_transfer_cost materials_transfer_cost,
 cfc_jobs_cost jobs_cost,
 cfc_ready_volume ready_volume,
 cfc_ready_transfer_cost ready_transfer_cost,
 cfc_products_recommended_price products_recommended_price,
 cfc_products_sell_fee_and_tax products_sell_fee_and_tax,
 cfc_total_gross_cost total_gross_cost,
 cfc_single_product_cost single_product_cost,
 cfc_product_mininum_price product_mininum_price,
 cfc_created_at created_at,
 date_trunc('minutes', CURRENT_TIMESTAMP AT TIME ZONE 'GMT'-cfc_created_at) created_at,
 date_trunc('minutes', CURRENT_TIMESTAMP AT TIME ZONE 'GMT'-cfc_updated_at) updated_at
from
 conveyor_formula_calculus c,
 conveyor_formulas f
  left outer join eve_sde_type_ids fd on (f.cf_decryptor_type_id is not null and fd.sdet_type_id=f.cf_decryptor_type_id)
  left outer join eve_sde_type_ids fb on (f.cf_blueprint_type_id is not null and fb.sdet_type_id=f.cf_blueprint_type_id)
  left outer join eve_sde_type_ids fpb on (f.cf_prior_blueprint_type_id is not null and fpb.sdet_type_id=f.cf_prior_blueprint_type_id)
where
 cfc_trader_corp=any($1) and
 cfc_trade_hub=$2 and
 cfc_formula in (
  select cf_formula
  from qi.conveyor_formulas
  where cf_product_type_id=$3
 ) and
 cfc_formula=cf_formula
order by cfc_single_product_cost;
EOD;
    $params = array('{'.implode(',',$corporation_ids).'}', $trade_hub_id, $product_type_id);
    $conveyor_formula_calculus_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $conveyor_formula_calculus = pg_fetch_all($conveyor_formula_calculus_cursor);
    if ($conveyor_formula_calculus)
    {
        $idx = 0;
        foreach ($conveyor_formula_calculus as &$o)
        {
            if (0 == $idx++)
            {
                $o['formula'] = intval($o['formula']);
                $o['blueprint_type_id'] = intval($o['blueprint_type_id']);
                if (is_null($o['blueprint'])) unset($o['blueprint']);
                $o['activity'] = intval($o['activity']);
                if (is_null($o['prior_blueprint_type_id'])) unset($o['prior_blueprint_type_id']); else $o['prior_blueprint_type_id'] = intval($o['prior_blueprint_type_id']);
                if (is_null($o['prior_blueprint'])) unset($o['prior_blueprint']);
                $o['products_per_single_run'] = intval($o['products_per_single_run']);
                $o['buying_brokers_fee'] = floatval($o['buying_brokers_fee']);
                $o['sales_brokers_fee'] = floatval($o['sales_brokers_fee']);
                $o['sales_tax'] = floatval($o['sales_tax']);
                $o['fuel_price_isk'] = floatval($o['fuel_price_isk']);
            }
            else
            {
                unset($o['formula']);
                unset($o['blueprint_type_id']);
                unset($o['activity']);
                unset($o['prior_blueprint_type_id']);
                unset($o['products_per_single_run']);
                unset($o['buying_brokers_fee']);
                unset($o['sales_brokers_fee']);
                unset($o['sales_tax']);
                unset($o['fuel_price_isk']);
            }
			if (is_null($o['decryptor_type_id'])) unset($o['decryptor_type_id']); else $o['decryptor_type_id'] = intval($o['decryptor_type_id']);
			if (is_null($o['decryptor'])) unset($o['decryptor']);
			if ($o['ancient_relics']=='unused') unset($o['ancient_relics']); else $o['ancient_relics'] = intval($o['ancient_relics']);
			$o['customized_runs'] = intval($o['customized_runs']);
			$o['products_num'] = intval($o['products_num']);
			$o['best_choice'] = $o['best_choice'] == 't';
			$o['materials_cost'] = floatval($o['materials_cost']);
			$o['materials_cost_with_fee'] = floatval($o['materials_cost_with_fee']);
			$o['purchase_volume'] = floatval($o['purchase_volume']);
			$o['materials_transfer_cost'] = floatval($o['materials_transfer_cost']);
			$o['jobs_cost'] = floatval($o['jobs_cost']);
			$o['ready_volume'] = floatval($o['ready_volume']);
			$o['ready_transfer_cost'] = floatval($o['ready_transfer_cost']);
			if (is_null($o['products_recommended_price'])) unset($o['products_recommended_price']); else $o['products_recommended_price'] = floatval($o['products_recommended_price']);
			if (is_null($o['products_sell_fee_and_tax'])) unset($o['products_sell_fee_and_tax']); else $o['products_sell_fee_and_tax'] = floatval($o['products_sell_fee_and_tax']);
			$o['total_gross_cost'] = floatval($o['total_gross_cost']);
			$o['single_product_cost'] = floatval($o['single_product_cost']);
			if (is_null($o['product_mininum_price'])) unset($o['product_mininum_price']); else $o['product_mininum_price'] = floatval($o['product_mininum_price']);
			$o['created_at'] = strval(rtrim($o['created_at'],':00'));
			$o['updated_at'] = strval(rtrim($o['updated_at'],':00'));
        }
    }
    echo json_encode($conveyor_formula_calculus);
}

//$CORPORATION_ID = 98553333;
//$TRADE_HUB_ID = 60003760;
//$PRODUCT_TYPE_ID = 60302;

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

//$PRODUCT_TYPE_ID = 20185; // Charon

if (!extension_loaded('pgsql')) return;
$conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
        or die('pg_connect err: '.pg_last_error());
pg_exec($conn, "SET search_path TO qi");

ob_end_clean();
header('Content-Type: application/json');
json_conveyor_formula_calculus($conn, $CORPORATION_IDs, $TRADE_HUB_ID, $PRODUCT_TYPE_ID);

pg_close();
?>
