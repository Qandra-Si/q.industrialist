<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include_once '.settings.php';


?><style>
table.qind-table tbody > tr > td:nth-child(1) > img /* material icon (compact view) */
{ margin-top: -2px; margin-bottom: -1px; }

table.qind-table > tbody > tr > td,
table.qind-table > tbody > tr > th
{ padding: 1px; }

table.qind-table > thead > tr > th,
table.qind-table > tbody > tr > td
{ text-align: right; }

table.qind-table > tbody > tr > td:nth-child(1)
{ width: 24px; }

table.qind-table > thead > tr > th:nth-child(1),
table.qind-table > tbody > tr > td:nth-child(1),
table.qind-table > thead > tr > th:nth-child(2),
table.qind-table > tbody > tr > td:nth-child(2)
{ text-align: left; }

table.qind-table-assets > thead > tr > th:nth-child(3),
table.qind-table-assets > tbody > tr > td:nth-child(3),
table.qind-table-assets > thead > tr > th:nth-child(4),
table.qind-table-assets > tbody > tr > td:nth-child(4)
{ text-align: left; }

table.qind-table-jobs > tbody > tr > td:nth-child(8)
{ width: 24px; }
table.qind-table-jobs > tbody > tr > td:nth-child(8) > img /* material icon (compact view) */
{ margin-top: -2px; margin-bottom: -1px; }

table.qind-table-jobs > thead > tr > th,
table.qind-table-jobs > tbody > tr > td
{ font-size: smaller; }
table.qind-table-jobs > thead > tr > th:nth-child(3),
table.qind-table-jobs > tbody > tr > td:nth-child(3),
table.qind-table-jobs > thead > tr > th:nth-child(4),
table.qind-table-jobs > tbody > tr > td:nth-child(4),
table.qind-table-jobs > thead > tr > th:nth-child(5),
table.qind-table-jobs > tbody > tr > td:nth-child(5),
table.qind-table-jobs > thead > tr > th:nth-child(9),
table.qind-table-jobs > tbody > tr > td:nth-child(9)
{ text-align: left; }

table.qind-table-jobsstat > tbody > tr > td:nth-child(4)
{ width: 24px; }
table.qind-table-jobsstat > tbody > tr > td:nth-child(4) > img /* material icon (compact view) */
{ margin-top: -2px; margin-bottom: -1px; }

table.qind-table-jobsstat > thead > tr > th:nth-child(2),
table.qind-table-jobsstat > tbody > tr > td:nth-child(2),
table.qind-table-jobsstat > thead > tr > th:nth-child(3),
table.qind-table-jobsstat > tbody > tr > td:nth-child(3),
table.qind-table-jobsstat > thead > tr > th:nth-child(5),
table.qind-table-jobsstat > tbody > tr > td:nth-child(5)
{ text-align: left; }
</style><?php


function sys_numbers($var) { return $var <= 2147483647; } 
function user_numbers($var) { return $var > 2147483647; } 

function __dump_type_ids(&$conn, &$ids) {
    $sys_ids = array_filter($ids, "sys_numbers");
    $query = <<<EOD
select *
from eve_sde_type_ids
where sdet_type_id=any($1) or sdet_market_group_id=any($1) or sdet_group_id=any($1)
order by sdet_type_name;
EOD;
    $params = array('{'.implode(',',$sys_ids).'}');
    $type_ids_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $type_ids = pg_fetch_all($type_ids_cursor);
    if (!$type_ids) return;
?><h2>Сведения о типах предметов</h2>
<table class="table table-condensed table-hover qind-table" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th></th>
  <th>Item</th>
  <th>Volume,<br>m³</th>
  <th>Packaged<br>Volume,&nbsp;m³</th>
  <th>Capacity,<br>m³</th>
  <th>Base price,<br>ISK</th>
  <th>Market<br>Group</th>
  <th>Group</th>
  <th>Meta<br>Group</th>
  <th>Tech Level</th>
  <th>Published</th>
  <th>Created</th>
 </tr>
</thead>
<tbody><?php
    foreach ($type_ids as &$t)
    {
        $type_id = $t['sdet_type_id'];
        $type_name = $t['sdet_type_name'];
?><tr>
 <td><img class="icn24" src="<?=__get_img_src($type_id,32,FS_RESOURCES)?>"></td>
 <td><?=$type_name.get_clipboard_copy_button($type_name)?> <span class="text-muted">(<?=$type_id?>)</span></td>
 <td><?=number_format($t['sdet_volume'],2,'.',',')?></td>
 <td><?=number_format($t['sdet_packaged_volume'],2,'.',',')?></td>
 <td><?=number_format($t['sdet_capacity'],0,'.',',')?></td>
 <td><?=number_format($t['sdet_base_price'],0,'.',',')?></td>
 <td><?=$t['sdet_market_group_id']?></td>
 <td><?=$t['sdet_group_id']?></td>
 <td><?=$t['sdet_meta_group_id']?></td>
 <td><?=$t['sdet_tech_level']?></td>
 <td><?=($t['sdet_published']=='t')?'да':'нет'?></td>
 <td><?=$t['sdet_created_at']?></td>
</tr><?php
    }
?></tbody>
</table><?php
}


function __dump_assets(&$conn, &$ids) {
    $sys_ids = array_filter($ids, "sys_numbers");
    $user_ids = array_filter($ids, "user_numbers");
    $query = <<<EOD
select
 eca_corporation_id,
 eca_type_id,
 tid.sdet_type_name,
 --eca_item_id,
 eca_name,
 eca_location_flag,
 eca_location_id,
 loc.nm as location_name,
 eca_location_type,
 sum(eca_quantity) eca_quantity,
 --eca_is_singleton,
 min(tid.sdet_volume) sdet_volume,
 min(tid.sdet_packaged_volume) sdet_packaged_volume,
 min(date_trunc('seconds', eca_created_at)) eca_created_at,
 max(date_trunc('seconds', eca_updated_at)) eca_updated_at,
 min(jita.ethp_sell) as jita_sell,
 min(jita.ethp_buy) as jita_buy
from esi_corporation_assets
 left outer join eve_sde_type_ids tid on (tid.sdet_type_id=eca_type_id)
 left outer join esi_trade_hub_prices jita on (eca_type_id = jita.ethp_type_id and jita.ethp_location_id = 60003760)
 left outer join (
  select eca_item_id id,eca_name nm
  from esi_corporation_assets
 ) loc on (loc.id=eca_location_id)
where (eca_type_id=any($1) or
       eca_location_id=any($2) or
       tid.sdet_market_group_id=any($1) or
       tid.sdet_group_id=any($1))
group by eca_corporation_id, eca_type_id, tid.sdet_type_name, eca_name, eca_location_flag, eca_location_id, loc.nm, eca_location_type
order by eca_corporation_id, tid.sdet_type_name, eca_location_flag, eca_location_id;
EOD;
    $params = array('{'.implode(',',$sys_ids).'}', '{'.implode(',',$user_ids).'}');
    $assets_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $assets = pg_fetch_all($assets_cursor);
    if (!$assets) return;
?><h2>Сведения о наличии предметов <small>в корпоративных ассетах</small></h2>
<table class="table table-condensed table-hover qind-table qind-table-assets" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th></th>
  <th>Item</th>
  <th>Location, №</th>
  <th>Flag</th>
  <th>Quantity</th>
  <th>Volume, m³<br>(Packaged)</th>
  <th>Jita Buy&#x200B;&hellip;Sell</th>
  <th>Created</th>
  <th>Updated</th>
 </tr>
</thead>
<tbody><?php
    $prev_corporation_id = null;
    foreach ($assets as &$a)
    {
        $corporation_id = $a['eca_corporation_id'];
        $type_id = $a['eca_type_id'];
        $type_name = $a['sdet_type_name'];
        if ($prev_corporation_id != $corporation_id)
        {
            ?><tr><td class="active" colspan="10"><strong>Corporation # <?=$corporation_id?></strong></td><?php
            $prev_corporation_id = $corporation_id;
        }
?><tr>
 <td><img class="icn24" src="<?=__get_img_src($type_id,32,FS_RESOURCES)?>"></td>
 <td><?=(is_null($a['eca_name'])?$type_name:'<mark>'.$a['eca_name'].'</mark>').get_clipboard_copy_button($type_name)?> <span class="text-muted">(<?=$type_id?>)</span></td>
 <td><?=is_null($a['location_name'])?'':'<mark>'.$a['location_name'].'</mark><br>'?><span class="text-muted">(<?=$a['eca_location_id']?>)</span></td>
 <td><?=$a['eca_location_flag']?><?php if ($a['eca_location_type']!='item') { ?><br><span class="label label-warning"><?=$a['eca_location_type']?></span><?php } ?></td>
 <td><?=number_format($a['eca_quantity'],0,'.',',')?></td>
 <td><?=number_format($a['eca_quantity']*$a['sdet_volume'],0,'.',',')?> <span class="text-muted">(<?=number_format($a['eca_quantity']*$a['sdet_packaged_volume'],0,'.',',')?>)</span></td>
 <?php
    if (is_null($a['jita_buy']) && is_null($a['jita_sell']))
    {
        ?><td></td><?php
    }
    else
    {
        ?><td><?=number_format($a['eca_quantity']*$a['jita_buy'],0,'.',',').'&#x200B;&hellip;'.number_format($a['eca_quantity']*$a['jita_sell'],0,'.',',')?></td><?php
    }
 ?>
 <td><?=$a['eca_created_at']?></td>
 <td><?=$a['eca_updated_at']?></td>
</tr><?php
    }
?></tbody>
</table><?php
}



function __dump_industry_lines(&$conn, &$ids) {
    $sys_ids = array_filter($ids, "sys_numbers");
    $user_ids = array_filter($ids, "user_numbers");
    $query = <<<EOD
select
 ecj_corporation_id,
 ecj_facility_id,
 fac.name facility_name,
 ecj_installer_id,
 inst.ech_name installer_name,
 ecj_blueprint_type_id,
 coalesce(bpt.sdet_type_name, ecj_blueprint_type_id::varchar(255)) blueprint_type_name,
 coalesce(loc.eca_name, ecj_blueprint_location_id::varchar(255)) blueprint_loc_name,
 case
  when cout.eca_type_id=27 then (select name from esi_known_stations where cout.eca_location_id=location_id)
  else coalesce(cout.eca_name, ecj_output_location_id::varchar(255))
 end output_loc_name,
 cout.eca_location_flag,
 -- ecj_blueprint_id,
 ecj_activity_id,
 ecj_runs,
 ecj_successful_runs,
 ecj_licensed_runs,
 ecj_cost,
 ecj_product_type_id,
 coalesce(prod.sdet_type_name, ecj_product_type_id::varchar(255)) product_type_name,
 date_trunc('seconds', ecj_start_date) start_date,
 date_trunc('seconds', ecj_end_date) end_date,
 date_trunc('seconds', ecj_completed_date) completed_date
 --,date_trunc('seconds', ecj_updated_at) updated_at
from esi_corporation_industry_jobs
 left outer join esi_characters inst on (inst.ech_character_id=ecj_installer_id)
 left outer join esi_known_stations fac on (fac.location_id=ecj_facility_id)
 left outer join esi_corporation_assets loc on (loc.eca_item_id=ecj_blueprint_location_id)
 left outer join eve_sde_type_ids bpt on (bpt.sdet_type_id=ecj_blueprint_type_id) 
 left outer join esi_corporation_assets cout on (cout.eca_item_id=ecj_output_location_id)
 left outer join eve_sde_type_ids prod on (prod.sdet_type_id=ecj_product_type_id) 
where
 ecj_end_date > (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '7 days') and
 (ecj_product_type_id=any($1) or
  ecj_blueprint_type_id=any($1) or
  ecj_blueprint_location_id=any($2) or
  ecj_output_location_id=any($2) or
  ecj_facility_id=any($2) or
  bpt.sdet_market_group_id=any($1) or
  bpt.sdet_group_id=any($1) or
  prod.sdet_market_group_id=any($1) or
  prod.sdet_group_id=any($1) or
  ecj_installer_id=any($3))
order by ecj_corporation_id, ecj_facility_id, ecj_end_date desc;
EOD;
    $params = array('{'.implode(',',$sys_ids).'}', '{'.implode(',',$user_ids).'}', '{'.implode(',',$ids).'}');
    $jobs_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $jobs = pg_fetch_all($jobs_cursor);
    if (!$jobs) return;
?><h2>Хронология производства предмета <small>за последнюю неделю</small></h2>
<table class="table table-condensed table-hover qind-table qind-table-jobs" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th></th>
  <th>Blueprint</th>
  <th>Installer</th>
  <th>Input » Output</th>
  <th>Activity</th>
  <th>Runs</th>
  <th>Cost, ISK</th>
  <th></th>
  <th>Product</th>
  <th>Start</th>
  <th>End</th>
  <th>Completed</th>
 </tr>
</thead>
<tbody><?php
    $prev_corporation_id = null;
    $prev_facility_name = null;
    foreach ($jobs as &$j)
    {
        $corporation_id = $j['ecj_corporation_id'];
        $facility_name = $j['facility_name'];
        $blueprint_type_id = $j['ecj_blueprint_type_id'];
        $blueprint_type_name = $j['blueprint_type_name'];
        $product_type_id = $j['ecj_product_type_id'];
        $product_type_name = $j['product_type_name'];
        $activity_id = $j['ecj_activity_id'];
        if ($prev_corporation_id != $corporation_id || $prev_facility_name != $facility_name)
        {
            ?><tr><td class="active" colspan="12"><strong>Corporation # <?=$corporation_id?> » <?=$facility_name?> <span class="text-muted">(<?=$j['ecj_facility_id']?>)</span></strong></td><?php
            $prev_corporation_id = $corporation_id;
            $prev_facility_name = $facility_name;
        }
?><tr>
 <td><img class="icn24" src="<?=__get_img_src($blueprint_type_id,32,FS_RESOURCES)?>"></td>
 <td><?=$blueprint_type_name.get_clipboard_copy_button($blueprint_type_name)?> <span class="text-muted">(<?=$blueprint_type_id?>)</span></td>
 <td><?=$j['installer_name']?> <span class="text-muted">(<?=$j['ecj_installer_id']?>)</span></td>
 <td><?=$j['blueprint_loc_name']?> » <?=$j['output_loc_name']?> <span class="text-muted">(<?=$j['eca_location_flag']?>)</span></td>
 <td><?php
    switch ($activity_id)
    {
    case 1: echo 'произв.'; break;
    case 8: echo 'инвент'; break;
    case 5: echo 'копир.'; break;
    case 4: echo 'me'; break;
    case 3: echo 'te'; break;
    case 9: echo 'реакции'; break;
    }
 ?></td>
 <td><?=(($j['ecj_licensed_runs']==$j['ecj_runs'])?$j['ecj_runs']:($j['ecj_runs'].' из '.$j['ecj_licensed_runs'])).(!is_null($j['ecj_successful_runs'])?' <span class="text-muted">('.$j['ecj_successful_runs'].')</span>':'')?></td>
 <td><?=number_format($j['ecj_cost'],0,'.',',')?></td>
 <td><img class="icn24" src="<?=__get_img_src($product_type_id,32,FS_RESOURCES)?>"></td>
 <td><?=$product_type_name.get_clipboard_copy_button($product_type_name)?> <span class="text-muted">(<?=$product_type_id?>)</span></td>
 <td><?=$j['start_date']?></td>
 <td><?=$j['end_date']?></td>
 <td><?=$j['completed_date']?></td>
</tr><?php
    }
?></tbody>
</table><?php
}

function __dump_industry_statistic(&$conn, &$ids) {
    $sys_ids = array_filter($ids, "sys_numbers");
    $user_ids = array_filter($ids, "user_numbers");
    $query = <<<EOD
select
 ecj_corporation_id,
 ecj_facility_id,
 fac.name facility_name,
 ecj_blueprint_type_id,
 coalesce(bpt.sdet_type_name, ecj_blueprint_type_id::varchar(255)) blueprint_type_name,
 ecj_activity_id,
 ecj_product_type_id,
 prod.sdet_type_name product_type_name,
 in_progress_runs,
 runs,
 successful_runs,
 cost,
 start_date,
 end_date
from (
 select
  ecj_corporation_id,
  ecj_facility_id,
  ecj_blueprint_type_id,
  ecj_activity_id,
  ecj_product_type_id,
  sum(case
   when ecj_end_date > CURRENT_TIMESTAMP AT TIME ZONE 'GMT' then ecj_runs
   else 0
  end) in_progress_runs,
  sum(ecj_runs) runs,
  sum(ecj_successful_runs) successful_runs,
  sum(ecj_cost) as cost,
  min(date_trunc('seconds', ecj_start_date)) start_date,
  max(date_trunc('seconds', ecj_end_date)) end_date
 from esi_corporation_industry_jobs
  left outer join eve_sde_type_ids bpt on (bpt.sdet_type_id=ecj_blueprint_type_id) 
  left outer join eve_sde_type_ids prod on (prod.sdet_type_id=ecj_product_type_id) 
 where
  ecj_end_date > (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '30 days') and
  (ecj_product_type_id=any($1) or
   ecj_blueprint_type_id=any($1) or
   ecj_blueprint_location_id=any($2) or
   ecj_output_location_id=any($2) or
   ecj_facility_id=any($2) or
   bpt.sdet_market_group_id=any($1) or
   bpt.sdet_group_id=any($1) or
   prod.sdet_market_group_id=any($1) or
   prod.sdet_group_id=any($1) or
   ecj_installer_id=any($3))
 group by
  ecj_corporation_id,
  ecj_facility_id,
  ecj_blueprint_type_id,
  ecj_activity_id,
  ecj_product_type_id
) x
 left outer join esi_known_stations fac on (fac.location_id=ecj_facility_id)
 left outer join eve_sde_type_ids bpt on (bpt.sdet_type_id=ecj_blueprint_type_id) 
 left outer join eve_sde_type_ids prod on (prod.sdet_type_id=ecj_product_type_id) 
order by ecj_corporation_id, fac.name, bpt.sdet_type_name, prod.sdet_type_name;
EOD;
    $params = array('{'.implode(',',$sys_ids).'}', '{'.implode(',',$user_ids).'}', '{'.implode(',',$ids).'}');
    $jobs_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $jobs = pg_fetch_all($jobs_cursor);
    if (!$jobs) return;
?><h2>Статистика производства предмета <small>за последний месяц</small></h2>
<table class="table table-condensed table-hover qind-table qind-table-jobsstat" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th></th>
  <th>Blueprint</th>
  <th>Activity</th>
  <th></th>
  <th>Product</th>
  <th>Runs</th>
  <th>In progress</th>
  <th>Cost, ISK</th>
  <th>First Start</th>
  <th>Last End</th>
 </tr>
</thead>
<tbody><?php
    $prev_corporation_id = null;
    $prev_facility_name = null;
    foreach ($jobs as &$j)
    {
        $corporation_id = $j['ecj_corporation_id'];
        $facility_name = $j['facility_name'];
        $blueprint_type_id = $j['ecj_blueprint_type_id'];
        $blueprint_type_name = $j['blueprint_type_name'];
        $product_type_id = $j['ecj_product_type_id'];
        $product_type_name = $j['product_type_name'];
        $activity_id = $j['ecj_activity_id'];
        if ($prev_corporation_id != $corporation_id || $prev_facility_name != $facility_name)
        {
            ?><tr><td class="active" colspan="10"><strong>Corporation # <?=$corporation_id?> » <?=$facility_name?> <span class="text-muted">(<?=$j['ecj_facility_id']?>)</span></strong></td><?php
            $prev_corporation_id = $corporation_id;
            $prev_facility_name = $facility_name;
        }
?><tr>
 <td><img class="icn24" src="<?=__get_img_src($blueprint_type_id,32,FS_RESOURCES)?>"></td>
 <td><?=$blueprint_type_name.get_clipboard_copy_button($blueprint_type_name)?> <span class="text-muted">(<?=$blueprint_type_id?>)</span></td>
 <td><?php
    switch ($activity_id)
    {
    case 1: echo 'произв.'; break;
    case 8: echo 'инвент'; break;
    case 5: echo 'копир.'; break;
    case 4: echo 'me'; break;
    case 3: echo 'te'; break;
    case 9: echo 'реакции'; break;
    }
 ?></td>
 <td><img class="icn24" src="<?=__get_img_src($product_type_id,32,FS_RESOURCES)?>"></td>
 <td><?=$product_type_name.get_clipboard_copy_button($product_type_name)?> <span class="text-muted">(<?=$product_type_id?>)</span></td>
 <td><?=$j['runs'].(!is_null($j['successful_runs'])?' <span class="text-muted">('.$j['successful_runs'].')</span>':'')?></td>
 <td><?=$j['in_progress_runs']?$j['in_progress_runs']:''?></td>
 <td><?=number_format($j['cost'],0,'.',',')?></td>
 <td><?=$j['start_date']?></td>
 <td><?=$j['end_date']?></td>
</tr><?php
    }
?></tbody>
</table><?php
}

function __dump_orders_statistic(&$conn, &$ids) {
    $sys_ids = array_filter($ids, "sys_numbers");
    $user_ids = array_filter($ids, "user_numbers");
    $query = <<<EOD
select
 ecor_is_buy_order,
 ecor_corporation_id,
 ecor_location_id,
 hub.name as trade_hub_name,
 ecor_type_id,
 coalesce(itm.sdet_type_name, ecor_type_id::varchar(255)) type_name,
 price_close,
 price_remain,
 escrow,
 volume_close,
 volume_remain,
 orders_remain
from (
 select
  ecor_is_buy_order,
  ecor_corporation_id,
  ecor_type_id,
  ecor_location_id,
  ceil(avg((ecor_volume_total-ecor_volume_remain)*ecor_price)) price_close,
  ceil(avg((case when ecor_history then 0 else ecor_volume_remain end)*ecor_price)) price_remain,
  sum((case when ecor_history then 0 else ecor_escrow end)*ecor_price) escrow,
  sum(ecor_volume_total-ecor_volume_remain) volume_close,
  sum(case when ecor_history then 0 else ecor_volume_remain end) volume_remain,
  sum(case when ecor_history then 0 else 1 end) orders_remain
 from esi_corporation_orders
  left outer join eve_sde_type_ids itm on (itm.sdet_type_id=ecor_type_id) 
 where
  ((not ecor_history and (ecor_updated_at > (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '100 days'))) or
   (ecor_updated_at > (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '30 days'))) and
  (ecor_type_id=any($1) or
   ecor_location_id=any($2) or
   itm.sdet_market_group_id=any($1) or
   itm.sdet_group_id=any($1) or
   ecor_issued_by=any($2))
 group by
  ecor_is_buy_order,
  ecor_corporation_id,
  ecor_location_id,
  ecor_type_id
) x
 left outer join esi_known_stations hub on (hub.location_id=ecor_location_id)
 left outer join eve_sde_type_ids itm on (itm.sdet_type_id=ecor_type_id) 
order by ecor_is_buy_order, ecor_corporation_id, ecor_location_id, itm.sdet_type_name;
EOD;
    $params = array('{'.implode(',',$sys_ids).'}','{'.implode(',',$ids).'}');
    $orders_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $orders = pg_fetch_all($orders_cursor);
    if (!$orders) return;

    $prev_is_buy_order = null;
    $body_printed = false;
    foreach ($orders as &$o)
    {
        $is_buy_order = $o['ecor_is_buy_order'];
        $corporation_id = $o['ecor_corporation_id'];
        $trade_hub_name = $o['trade_hub_name'];
        $type_id = $o['ecor_type_id'];
        $type_name = $o['type_name'];
        if ($prev_is_buy_order != $is_buy_order)
        {
            $prev_is_buy_order = $is_buy_order;
            $prev_corporation_id = null;
            $prev_trade_hub_name = null;
            if (!$body_printed) { ?><h2>Статистика торговли предметом</h2><?php }
            if ($body_printed) { ?></tbody></table><?php }
            $body_printed = true;
?><h3><?=($is_buy_order=='t')?'Закупка':'Продажи'?> <small>за последний месяц</small></h3>
<table class="table table-condensed table-hover qind-table qind-table-tradestat" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th></th>
  <th>Item</th>
  <th>Цена, ISK<br>(исполнено)</th>
  <th>Объём<br>(исполнено)</th>
  <th>Кол-во<br>ордеров</th>
  <th>Цена, ISK<br>(остатки<?=($is_buy_order=='t')?'+escrow':''?>)</th>
  <th>Объём<br>(остатки)</th>
 </tr>
</thead>
<tbody><?php
        }
        if ($prev_corporation_id != $corporation_id || $prev_trade_hub_name != $trade_hub_name)
        {
            ?><tr><td class="active" colspan="7"><strong>Corporation # <?=$corporation_id?> » <?=$trade_hub_name?> <span class="text-muted">(<?=$o['ecor_location_id']?>)</span></strong></td><?php
            $prev_corporation_id = $corporation_id;
            $prev_trade_hub_name = $trade_hub_name;
        }
?><tr>
 <td><img class="icn24" src="<?=__get_img_src($type_id,32,FS_RESOURCES)?>"></td>
 <td><?=$type_name.get_clipboard_copy_button($type_name)?> <span class="text-muted">(<?=$type_id?>)</span></td>
 <td><?=number_format($o['price_close'],0,'.',',')?></td>
 <td><?=number_format($o['volume_close'],0,'.',',')?></td>
  <?php
    if ($o['orders_remain']==0)
    {
        ?><td></td><td></td><td></td><?php
    }
    else
    {
 ?><td><?=$o['orders_remain']?number_format($o['orders_remain'],0,'.',','):''?></td>
 <td><?=number_format($o['price_remain']+$o['escrow'],0,'.',',')?></td>
 <td><?=number_format($o['volume_remain'],0,'.',',')?></td><?php
    }
 ?>
</tr><?php
    }
    if ($body_printed) { ?></tbody></table><?php }
}



if (!isset($_GET['id'])) return; else {
  $_get_id = htmlentities($_GET['id']);
  if (is_numeric($_get_id)) $IDs = array(get_numeric($_get_id));
  else if (is_numeric_array($_get_id)) $IDs = get_numeric_array($_get_id);
  else return;
}


__dump_header("Googler", FS_RESOURCES);
if (!extension_loaded('pgsql')) return;
$conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
        or die('pg_connect err: '.pg_last_error());
pg_exec($conn, "SET search_path TO qi");
?>
<div class="container-fluid">
<?php __dump_type_ids($conn, $IDs); ?>
<?php __dump_assets($conn, $IDs); ?>
<?php __dump_industry_lines($conn, $IDs); ?>
<?php __dump_industry_statistic($conn, $IDs); ?>
<?php __dump_orders_statistic($conn, $IDs); ?>
</div> <!--container-fluid-->
<?php
__dump_footer();
pg_close($conn);
?>

<?php __dump_copy_to_clipboard_javascript() ?>
