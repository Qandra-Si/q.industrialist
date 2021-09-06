<?php
include 'qi_render_html.php';
include_once '.settings.php';
?>

<?php function __dump_lifetime_market_hubs($market_hubs) { ?>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th>Market Hub</th>
  <th>Updated At</th>
  <th style="text-align: right;">Orders Known</th>
  <th style="text-align: right;">Orders Updated</th>
 </tr>
</thead>
<tbody>
<?php
    foreach ($market_hubs as $hub)
    {
        $location_id = $product['location_id'];
        $updated_at = $product['updated_at'];
        $orders_known = $product['orders_known'];
        $orders_changed = $product['orders_changed'];
        $name = $product['name'];
?>
<tr>
 <td><?=$name.'<br><span class="text-muted">'.$location_id.'</span> '?></td>
 <td align="right"><?=$updated_at?></td>
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


<?php
    __dump_header("Lifetime", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
select
  hubs.location_id,
  hubs.updated_at,
  hubs.orders_known,
  hubs_stat.orders_changed, -- orders changed in 15min
  ks.name
from (
    select
      ethp_location_id as location_id,
      max(ethp_updated_at) as updated_at,
      count(1) as orders_known
    from qi.esi_trade_hub_prices ethp
    group by 1
  ) hubs
  left outer join qi.esi_known_stations ks on (ks.location_id = hubs.location_id)
  left outer join (
    select
      ethp_location_id as location_id,
      count(1) as orders_changed
    from qi.esi_trade_hub_prices ethp
    where ethp_updated_at >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '15 minutes') -- интервал обновления 10 минут => статистика 15 минут
    group by 1
  ) hubs_stat on (hubs_stat.location_id = hubs.location_id);
EOD;
    $market_hubs_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $market_hubs = pg_fetch_all($market_hubs_cursor);
    //---
    pg_close($conn);
?>
<div class="container-fluid">
<?php __dump_lifetime_market_hubs($market_hubs); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>