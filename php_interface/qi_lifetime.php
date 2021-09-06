<?php
include 'qi_render_html.php';
include_once '.settings.php';
?>

<?php function __dump_lifetime_market_hubs($market_hubs) { ?>
<h2>Market Hubs and Structures</h2>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th>Market Hub</th>
  <th style="text-align: right;">Updated At</th>
  <th style="text-align: right;">Orders Known</th>
  <th style="text-align: right;">Updated in 15 min</th>
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


<?php function __dump_lifetime_corporation_assets($corp_assets) { ?>
<h2>Corporation Assets</h2>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th>Corporation</th>
  <th style="text-align: right;">Updated At</th>
  <th style="text-align: right;">Asset Items</th>
  <th style="text-align: right;">Updated in 90 min</th>
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


<?php function __dump_lifetime_corporation_blueprints($corp_blueprints) { ?>
<h2>Corporation Blueprints</h2>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th>Corporation</th>
  <th style="text-align: right;">Updated At</th>
  <th style="text-align: right;">BPO</th>
  <th style="text-align: right;">BPC</th>
  <th style="text-align: right;">Updated in 90 min</th>
 </tr>
</thead>
<tbody>
<?php
    foreach ($corp_blueprints as $corp)
    {
        $corporation_id = $corp['id'];
        $updated_at = $corp['uat'];
        $update_interval = $corp['ui'];
        $bpc_quantity = $corp['bpc'];
        $bpo_quantity = $corp['bpo'];
        $items_changed = $corp['qc'];
        $name = $corp['nm'];
?>
<tr>
 <td><?=$name.'<br><span class="text-muted">'.$corporation_id.'</span> '?></td>
 <td align="right"><?=$updated_at.'<br><span class="text-warning">'.$update_interval.'</span> '?></td>
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


<?php
    __dump_header("Lifetime", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
select
  hubs.ethp_location_id as id,
  hubs.updated_at as uat,
  date_trunc('seconds', CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - hubs.updated_at)::interval as ui,
  hubs.orders_known as ok,
  hubs_stat.orders_changed as oc, -- orders changed in 15min
  ks.name as nm
from (
    select
      ethp_location_id,
      max(ethp_updated_at) as updated_at,
      count(1) as orders_known
    from qi.esi_trade_hub_prices ethp
    group by 1
  ) hubs
  left outer join qi.esi_known_stations ks on (ks.location_id = hubs.ethp_location_id)
  left outer join (
    select
      ethp_location_id as location_id,
      count(1) as orders_changed
    from qi.esi_trade_hub_prices ethp
    where ethp_updated_at >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '15 minutes') -- интервал обновления 10 минут => статистика 15 минут
    group by 1
  ) hubs_stat on (hubs_stat.location_id = hubs.ethp_location_id);
EOD;
    $market_hubs_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $market_hubs = pg_fetch_all($market_hubs_cursor);
    //---
    $query = <<<EOD
select
  ca.corporation_id as id,
  ca.updated_at as uat,
  date_trunc('seconds', CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - ca.updated_at)::interval as ui,
  ca.quantity as q,
  ca_stat.items_changed as qc,
  c.eco_name as nm
from (
    select
      eca_corporation_id as corporation_id,
      max(eca_updated_at) as updated_at,
      sum(eca_quantity) as quantity
    from qi.esi_corporation_assets
    group by 1
  ) ca
  left outer join qi.esi_corporations c on (c.eco_corporation_id = ca.corporation_id)
  left outer join (
    select
      eca_corporation_id as corporation_id,
      count(1) as items_changed
    from qi.esi_corporation_assets
    where eca_updated_at >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '90 minutes')
    group by 1
  ) ca_stat on (ca_stat.corporation_id = ca.corporation_id);
EOD;
    $corp_assets_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $corp_assets = pg_fetch_all($corp_assets_cursor);
    //---
    $query = <<<EOD
--SET intervalstyle = 'postgres_verbose';
select
  cb.corporation_id as id,
  cb.updated_at as uat,
  date_trunc('seconds', CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - cb.updated_at)::interval as ui,
  cb.bpc as bpc,
  cb.bpo as bpo,
  cb_stat.items_changed as qc,
  c.eco_name as nm
from (
    select
      ecb_corporation_id as corporation_id,
      max(ecb_updated_at) as updated_at,
      sum(case when ecb_quantity=-2 then 1 else 0 end) as bpc,
      sum(case when ecb_quantity=-1 then 1 when ecb_quantity>0 then ecb_quantity else 0 end) as bpo
    from qi.esi_corporation_blueprints
    group by 1
  ) cb
  left outer join qi.esi_corporations c on (c.eco_corporation_id = cb.corporation_id)
  left outer join (
    select
      ecb_corporation_id as corporation_id,
      count(1) as items_changed
    from qi.esi_corporation_blueprints
    where ecb_updated_at >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '90 minutes')
    group by 1
  ) cb_stat on (cb_stat.corporation_id = cb.corporation_id);
EOD;
    $corp_blueprints_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $corp_blueprints = pg_fetch_all($corp_blueprints_cursor);
    //---
    pg_close($conn);
?>
<div class="container-fluid">
<?php __dump_lifetime_market_hubs($market_hubs); ?>
<?php __dump_lifetime_corporation_assets($corp_assets); ?>
<?php __dump_lifetime_corporation_blueprints($corp_blueprints); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>
