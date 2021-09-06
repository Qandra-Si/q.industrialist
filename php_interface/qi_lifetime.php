<?php
include 'qi_render_html.php';
include_once '.settings.php';

function get_numeric($val) {
    return is_numeric($val) ? ($val + 0) : 0;
}
?>

<?php function __dump_lifetime_market_hubs($market_hubs, $interval_minutes) { ?>
<h2>Market Hubs and Structures</h2>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th>Market Hub</th>
  <th style="text-align: right;">Updated At</th>
  <th style="text-align: right;">Orders Known</th>
  <th style="text-align: right;">Updated in <?=$interval_minutes?> min</th>
 </tr>
</thead>
<tbody>
<?php
    foreach ($market_hubs as $hub)
    {
        $location_id = $hub['id'];
        $updated_at = $hub['uat'];
        $update_interval = $hub['ui'];
        $orders_known = $hub['ok'];
        $orders_changed = $hub['oc'];
        $name = $hub['nm'];
?>
<tr>
 <td><?=$name.'<br><span class="text-muted">'.$location_id.'</span> '?></td>
 <td align="right"><?=$updated_at.'<br><span class="text-warning">'.$update_interval.'</span> '?></td>
 <td align="right"><?=number_format($orders_known,0,'.',',')?></td>
 <?php if (is_null($orders_changed)) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($orders_changed,0,'.',',')?></td>
 <?php } ?>
</tr>
<?php
    }
?>
</tbody>
</table>
<?php
} ?>


<?php function __dump_lifetime_corporation_assets($corp_assets, $interval_minutes) { ?>
<h2>Corporation Assets</h2>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th>Corporation</th>
  <th style="text-align: right;">Updated At</th>
  <th style="text-align: right;">Asset Items</th>
  <th style="text-align: right;">Updated in <?=$interval_minutes?> min</th>
 </tr>
</thead>
<tbody>
<?php
    foreach ($corp_assets as $corp)
    {
        $corporation_id = $corp['id'];
        $updated_at = $corp['uat'];
        $update_interval = $corp['ui'];
        $items_quantity = $corp['q'];
        $items_changed = $corp['qc'];
        $name = $corp['nm'];
?>
<tr>
 <td><?=$name.'<br><span class="text-muted">'.$corporation_id.'</span> '?></td>
 <td align="right"><?=$updated_at.'<br><span class="text-warning">'.$update_interval.'</span> '?></td>
 <td align="right"><?=number_format($items_quantity,0,'.',',')?></td>
 <?php if (is_null($items_changed)) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($items_changed,0,'.',',')?></td>
 <?php } ?>
</tr>
<?php
    }
?>
</tbody>
</table>
<?php
} ?>


<?php function __dump_lifetime_corporation_blueprints($corp_blueprints, $interval_minutes) { ?>
<h2>Corporation Blueprints</h2>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th>Corporation</th>
  <th style="text-align: right;">Updated At</th>
  <th style="text-align: right;">Stacks</th>
  <th style="text-align: right;">BPO</th>
  <th style="text-align: right;">BPC</th>
  <th style="text-align: right;">Updated in <?=$interval_minutes?> min</th>
 </tr>
</thead>
<tbody>
<?php
    foreach ($corp_blueprints as $corp)
    {
        $warning = '';

        $corporation_id = $corp['id'];
        $updated_at = $corp['uat'];
        $update_interval = $corp['ui'];
        $bpc_quantity = $corp['bpc'];
        $bpo_quantity = $corp['bpo'];
        $stacks_quantity = $corp['q'];
        $items_changed = $corp['qc'];
        $name = $corp['nm'];

        if ($stacks_quantity >= 22500) // overflow at 25'000
            $warning .= '<span class="label label-danger" data-toggle="tooltip" data-placement="bottom" title="25000 blueprints maximum for normal working">overflow</span>&nbsp;';
?>
<tr>
 <td><?=$name.'<br><span class="text-muted">'.$corporation_id.'</span> '.$warning?></td>
 <td align="right"><?=$updated_at.'<br><span class="text-warning">'.$update_interval.'</span> '?></td>
 <td align="right"><?=number_format($stacks_quantity,0,'.',',')?></td>
 <td align="right"><?=number_format($bpc_quantity,0,'.',',')?></td>
 <td align="right"><?=number_format($bpo_quantity,0,'.',',')?></td>
 <?php if (is_null($items_changed)) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($items_changed,0,'.',',')?></td>
 <?php } ?>
</tr>
<?php
    }
?>
</tbody>
</table>
<?php
} ?>


<?php function __dump_lifetime_corporation_industry_jobs($corp_jobs, $interval_minutes) { ?>
<h2>Corporation Industry Jobs</h2>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th>Corporation</th>
  <th>Facility</th>
  <th style="text-align: right;">Updated At</th>
  <th style="text-align: right;">Active Jobs</th>
  <th style="text-align: right;">Updated in <?=$interval_minutes?> min</th>
 </tr>
</thead>
<tbody>
<?php
    $last_name = '';
    foreach ($corp_jobs as $facility)
    {
        $corporation_id = $facility['id'];
        $facility_id = $facility['fid'];
        $updated_at = $facility['uat'];
        $update_interval = $facility['ui'];
        $jobs_active = $facility['ja'];
        $jobs_changed = $facility['jc'];
        $name = $facility['nm'];
        $fname = $facility['fnm'];
?>
<tr>
 <?php if ($name == $last_name) { ?><td></td><?php } else { $last_name = $name; ?>
 <td><?=$name.'<br><span class="text-muted">'.$corporation_id.'</span> '?></td>
 <?php } ?>
 <td><?=$fname.'<br><span class="text-muted">'.$facility_id.'</span> '?></td>
 <td align="right"><?=$updated_at.'<br><span class="text-warning">'.$update_interval.'</span> '?></td>
 <td align="right"><?=number_format($jobs_active,0,'.',',')?></td>
 <?php if (is_null($jobs_changed)) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($jobs_changed,0,'.',',')?></td>
 <?php } ?>
</tr>
<?php
    }
?>
</tbody>
</table>
<?php
} ?>


<?php function __dump_lifetime_corporation_wallet_journals($corp_wjrnls, $interval_minutes) { ?>
<h2>Corporation Wallet Journals</h2>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th>Corporation</th>
  <th>Wallet Division</th>
  <th style="text-align: right;">Last Event At</th>
  <th style="text-align: right;">Total Quantity</th>
  <th style="text-align: right;">Events in <?=$interval_minutes?> min</th>
 </tr>
</thead>
<tbody>
<?php
    $last_name = '';
    foreach ($corp_wjrnls as $event)
    {
        $corporation_id = $event['id'];
        $division = $event['d'];
        $updated_at = $event['uat'];
        $update_interval = $event['ui'];
        $total_quantity = $event['q'];
        $rows_appear = $event['ra'];
        $name = $event['nm'];
?>
<tr>
 <?php if ($name == $last_name) { ?><td></td><?php } else { $last_name = $name; ?>
 <td><?=$name.'<br><span class="text-muted">'.$corporation_id.'</span> '?></td>
 <?php } ?>
 <td><?=$division?></td>
 <td align="right"><?=$updated_at.'<br><span class="text-warning">'.$update_interval.'</span> '?></td>
 <td align="right"><?=number_format($total_quantity,0,'.',',')?></td>
 <?php if (is_null($rows_appear)) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($rows_appear,0,'.',',')?></td>
 <?php } ?>
</tr>
<?php
    }
?>
</tbody>
</table>
<?php
} ?>


<?php function __dump_lifetime_corporation_wallet_transactions($corp_trnsctns, $interval_minutes) { ?>
<h2>Corporation Wallet Transactions</h2>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th>Corporation</th>
  <th>Wallet Division</th>
  <th style="text-align: right;">Last Transaction At</th>
  <th style="text-align: right;">Total Quantity</th>
  <th style="text-align: right;">Payments in <?=$interval_minutes?> min</th>
 </tr>
</thead>
<tbody>
<?php
    $last_name = '';
    foreach ($corp_trnsctns as $trnsct)
    {
        $corporation_id = $trnsct['id'];
        $division = $trnsct['d'];
        $updated_at = $trnsct['uat'];
        $update_interval = $trnsct['ui'];
        $total_quantity = $trnsct['q'];
        $payments_appear = $trnsct['pa'];
        $name = $trnsct['nm'];
?>
<tr>
 <?php if ($name == $last_name) { ?><td></td><?php } else { $last_name = $name; ?>
 <td><?=$name.'<br><span class="text-muted">'.$corporation_id.'</span> '?></td>
 <?php } ?>
 <td><?=$division?></td>
 <td align="right"><?=$updated_at.'<br><span class="text-warning">'.$update_interval.'</span> '?></td>
 <td align="right"><?=number_format($total_quantity,0,'.',',')?></td>
 <?php if (is_null($payments_appear)) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($payments_appear,0,'.',',')?></td>
 <?php } ?>
</tr>
<?php
    }
?>
</tbody>
</table>
<?php
} ?>


<?php function __dump_lifetime_corporation_orders($corp_orders, $interval_minutes) { ?>
<h2>Corporation Orders</h2>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th>Corporation</th>
  <th>Trade Hub</th>
  <th style="text-align: right;">Updated At</th>
  <th style="text-align: right;">Active (total)</th>
  <th style="text-align: right;">Active (sell)</th>
  <th style="text-align: right;">Active (buy)</th>
  <th style="text-align: right;">Updated in <?=$interval_minutes?> min</th>
  <th style="text-align: right;">Updated (sell)</th>
  <th style="text-align: right;">Updated (buy)</th>
 </tr>
</thead>
<tbody>
<?php
    $last_name = '';
    foreach ($corp_orders as $order)
    {
        $corporation_id = $order['id'];
        $location_id = $order['lid'];
        $updated_at = $order['uat'];
        $update_interval = $order['ui'];
        $total_quantity = $order['t'];
        $sell_quantity = $order['s'];
        $buy_quantity = $order['b'];
        $total_updated = $order['tu'];
        $sell_updated = $order['su'];
        $buy_updated = $order['bu'];
        $name = $order['nm'];
        $trade_hub = $order['hub'];
?>
<tr>
 <?php if ($name == $last_name) { ?><td></td><?php } else { $last_name = $name; ?>
 <td><?=$name.'<br><span class="text-muted">'.$corporation_id.'</span> '?></td>
 <?php } ?>
 <td><?=$trade_hub.'<br><span class="text-muted">'.$location_id.'</span> '?></td>
 <td align="right"><?=$updated_at.'<br><span class="text-warning">'.$update_interval.'</span> '?></td>
 <td align="right"><?=number_format($total_quantity,0,'.',',')?></td>
 <td align="right"><?=$sell_quantity?number_format($sell_quantity,0,'.',','):''?></td>
 <td align="right"><?=$buy_quantity?number_format($buy_quantity,0,'.',','):''?></td>
 <?php if (is_null($total_updated)) { ?><td></td><td></td><td></td><?php } else { ?>
 <td align="right"><?=number_format($total_updated,0,'.',',')?></td>
 <td align="right"><?=$sell_updated?number_format($sell_updated,0,'.',','):''?></td>
 <td align="right"><?=$buy_updated?number_format($buy_updated,0,'.',','):''?></td>
 <?php } ?>
</tr>
<?php
    }
?>
</tbody>
</table>
<?php
} ?>


<?php
    $interval_minutes = 60;
    if (isset($_GET['interval'])) {
        $_get_interval = htmlentities($_GET['interval']);
        if (is_numeric($_get_interval))
            switch (get_numeric($_get_interval))
            {
            case 15: $interval_minutes = 15; break;
            case 60: $interval_minutes = 60; break;
            case 360: $interval_minutes = 360; break;
            case 720: $interval_minutes = 720; break;
            case 1440: $interval_minutes = 1440; break;
            }
    }

    __dump_header("Lifetime", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query =
"select".
"  hubs.ethp_location_id as id,".
"  hubs.updated_at as uat,".
"  date_trunc('seconds', CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - hubs.updated_at)::interval as ui,".
"  hubs.orders_known as ok,".
"  hubs_stat.orders_changed as oc,".
"  ks.name as nm ".
"from (".
"    select".
"      ethp_location_id,".
"      max(ethp_updated_at) as updated_at,".
"      count(1) as orders_known".
"    from qi.esi_trade_hub_prices ethp".
"    group by 1".
"  ) hubs".
"  left outer join qi.esi_known_stations ks on (ks.location_id = hubs.ethp_location_id)".
"  left outer join (".
"    select".
"      ethp_location_id as location_id,".
"      count(1) as orders_changed".
"    from qi.esi_trade_hub_prices ethp".
"    where ethp_updated_at >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '".$interval_minutes." minutes')".
"    group by 1".
"  ) hubs_stat on (hubs_stat.location_id = hubs.ethp_location_id)".
"order by ks.name;";
    $market_hubs_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $market_hubs = pg_fetch_all($market_hubs_cursor);
    //---
    $query =
"select".
"  ca.corporation_id as id,".
"  ca.updated_at as uat,".
"  date_trunc('seconds', CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - ca.updated_at)::interval as ui,".
"  ca.quantity as q,".
"  ca_stat.items_changed as qc,".
"  c.eco_name as nm ".
"from (".
"    select".
"      eca_corporation_id as corporation_id,".
"      max(eca_updated_at) as updated_at,".
"      sum(eca_quantity) as quantity".
"    from qi.esi_corporation_assets".
"    group by 1".
"  ) ca".
"  left outer join qi.esi_corporations c on (c.eco_corporation_id = ca.corporation_id)".
"  left outer join (".
"    select".
"      eca_corporation_id as corporation_id,".
"      count(1) as items_changed".
"    from qi.esi_corporation_assets".
"    where eca_updated_at >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '".$interval_minutes." minutes')".
"    group by 1".
"  ) ca_stat on (ca_stat.corporation_id = ca.corporation_id)".
"order by c.eco_name;";
    $corp_assets_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $corp_assets = pg_fetch_all($corp_assets_cursor);
    //---
    $query =
"select".
"  cb.corporation_id as id,".
"  cb.updated_at as uat,".
"  date_trunc('seconds', CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - cb.updated_at)::interval as ui,".
"  cb.bpc as bpc,".
"  cb.bpo as bpo,".
"  cb.quantity as q,".
"  cb_stat.items_changed as qc,".
"  c.eco_name as nm ".
"from (".
"    select".
"      ecb_corporation_id as corporation_id,".
"      max(ecb_updated_at) as updated_at,".
"      sum(case when ecb_quantity=-2 then 1 else 0 end) as bpc,".
"      sum(case when ecb_quantity=-1 then 1 when ecb_quantity>0 then ecb_quantity else 0 end) as bpo,".
"      count(1) as quantity".
"    from qi.esi_corporation_blueprints".
"    group by 1".
"  ) cb".
"  left outer join qi.esi_corporations c on (c.eco_corporation_id = cb.corporation_id)".
"  left outer join (".
"    select".
"      ecb_corporation_id as corporation_id,".
"      count(1) as items_changed".
"    from qi.esi_corporation_blueprints".
"    where ecb_updated_at >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '".$interval_minutes." minutes')".
"    group by 1".
"  ) cb_stat on (cb_stat.corporation_id = cb.corporation_id)".
"order by c.eco_name;";
    $corp_blueprints_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $corp_blueprints = pg_fetch_all($corp_blueprints_cursor);
    //---
    $query =
"select".
"  cj.corporation_id as id,".
"  cj.facility_id as fid,".
"  cj.updated_at as uat,".
"  date_trunc('seconds', CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - cj.updated_at)::interval as ui,".
"  cj.jobs_active as ja,".
"  cj_stat.jobs_changed as jc,".
"  c.eco_name as nm,".
"  ks.name as fnm ".
"from (".
"    select".
"      ecj_corporation_id as corporation_id,".
"      ecj_facility_id as facility_id,".
"      max(ecj_updated_at) as updated_at,".
"      count(1) as jobs_active".
"    from qi.esi_corporation_industry_jobs".
"    where ecj_status = 'active'".
"    group by 1, 2".
"  ) cj".
"  left outer join qi.esi_corporations c on (c.eco_corporation_id = cj.corporation_id)".
"  left outer join qi.esi_known_stations ks on (ks.location_id = cj.facility_id)".
"  left outer join (".
"    select".
"      ecj_corporation_id as corporation_id,".
"      ecj_facility_id as facility_id,".
"      count(1) as jobs_changed".
"    from qi.esi_corporation_industry_jobs".
"    where ecj_updated_at >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '".$interval_minutes." minutes')".
"    group by 1, 2".
"  ) cj_stat on (cj_stat.corporation_id = cj.corporation_id and cj_stat.facility_id = cj.facility_id)".
"order by c.eco_name, ks.name;";
    $corp_jobs_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $corp_jobs = pg_fetch_all($corp_jobs_cursor);
    //---
    $query =
"select".
"  wj.corporation_id as id,".
"  wj.division as d,".
"  wj.updated_at as uat,".
"  date_trunc('seconds', CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - wj.updated_at)::interval as ui,".
"  wj.quantity as q,".
"  wj_stat.rows_appear as ra,".
"  c.eco_name as nm ".
"from (".
"    select".
"      ecwj_corporation_id as corporation_id,".
"      ecwj_division as division,".
"      max(ecwj_created_at) as updated_at,".
"      count(1) as quantity".
"    from qi.esi_corporation_wallet_journals".
"    group by 1, 2".
"  ) wj".
"  left outer join qi.esi_corporations c on (c.eco_corporation_id = wj.corporation_id)".
"  left outer join (".
"    select".
"      ecwj_corporation_id as corporation_id,".
"      ecwj_division as division,".
"      count(1) as rows_appear".
"    from qi.esi_corporation_wallet_journals".
"    where ecwj_created_at >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '".$interval_minutes." minutes')".
"    group by 1, 2".
"  ) wj_stat on (wj_stat.corporation_id = wj.corporation_id and wj_stat.division = wj.division)".
"order by c.eco_name, wj.division;";
    $corp_wjrnls_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $corp_wjrnls = pg_fetch_all($corp_wjrnls_cursor);
    //---
    $query =
"select".
"  wt.corporation_id as id,".
"  wt.division as d,".
"  wt.updated_at as uat,".
"  date_trunc('seconds', CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - wt.updated_at)::interval as ui,".
"  wt.quantity as q,".
"  wt_stat.payments_appear as pa,".
"  c.eco_name as nm ".
"from (".
"    select".
"      ecwt_corporation_id as corporation_id,".
"      ecwt_division as division,".
"      max(ecwt_created_at) as updated_at,".
"      count(1) as quantity".
"    from qi.esi_corporation_wallet_transactions".
"    group by 1, 2".
"  ) wt".
"  left outer join qi.esi_corporations c on (c.eco_corporation_id = wt.corporation_id)".
"  left outer join (".
"    select".
"      ecwt_corporation_id as corporation_id,".
"      ecwt_division as division,".
"      count(1) as payments_appear".
"    from qi.esi_corporation_wallet_transactions".
"    where ecwt_created_at >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '".$interval_minutes." minutes')".
"    group by 1, 2".
"  ) wt_stat on (wt_stat.corporation_id = wt.corporation_id and wt_stat.division = wt.division)".
"order by c.eco_name, wt.division;";
    $corp_trnsctns_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $corp_trnsctns = pg_fetch_all($corp_trnsctns_cursor);
    //---
    $query =
"select".
"  o.corporation_id as id,".
"  o.location_id as lid,".
"  o.updated_at as uat,".
"  date_trunc('seconds', CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - o.updated_at)::interval as ui,".
"  o.total as t,".
"  o.buy as b,".
"  o.total-o.buy as s,".
"  o_stat.total as tu,".
"  o_stat.buy as bu,".
"  o_stat.total-o_stat.buy as su,".
"  c.eco_name as nm,".
"  ks.name as hub ".
"from (".
"    select".
"      ecor_corporation_id as corporation_id,".
"      ecor_location_id as location_id,".
"      max(ecor_updated_at) as updated_at,".
"      count(1) as total,".
"      sum(ecor_is_buy_order::int) as buy".
"    from qi.esi_corporation_orders".
"    where not ecor_history".
"    group by 1, 2".
"  ) o".
"  left outer join qi.esi_corporations c on (c.eco_corporation_id = o.corporation_id)".
"  left outer join qi.esi_known_stations ks on (ks.location_id = o.location_id)".
"  left outer join (".
"    select".
"      ecor_corporation_id as corporation_id,".
"      ecor_location_id as location_id,".
"      count(1) as total,".
"      sum(ecor_is_buy_order::int) as buy".
"    from qi.esi_corporation_orders".
"    where ecor_updated_at >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '".$interval_minutes." minutes')".
"    group by 1, 2".
"  ) o_stat on (o_stat.corporation_id = o.corporation_id and o_stat.location_id = o.location_id)".
"order by c.eco_name, ks.name;";
    $corp_orders_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $corp_orders = pg_fetch_all($corp_orders_cursor);
    //---
    pg_close($conn);
?>
<div class="container-fluid">
<?php __dump_lifetime_market_hubs($market_hubs, $interval_minutes); ?>
<?php __dump_lifetime_corporation_assets($corp_assets, $interval_minutes); ?>
<?php __dump_lifetime_corporation_blueprints($corp_blueprints, $interval_minutes); ?>
<?php __dump_lifetime_corporation_industry_jobs($corp_jobs, $interval_minutes); ?>
<?php __dump_lifetime_corporation_wallet_journals($corp_wjrnls, $interval_minutes); ?>
<?php __dump_lifetime_corporation_wallet_transactions($corp_trnsctns, $interval_minutes); ?>
<?php __dump_lifetime_corporation_orders($corp_orders, $interval_minutes); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>
