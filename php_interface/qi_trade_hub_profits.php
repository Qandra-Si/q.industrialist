<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include_once '.settings.php';


function __dump_trade_hub_orders(&$trade_hub_orders, $trade_hub_system) { ?>
<table class="table table-condensed" style="padding:1px;font-size:smaller;" id="tblMarket">
<thead>
 <tr>
  <th></th>
  <th width="100%">Items</th>
  <th style="text-align: center;">Profit,&nbsp;ISK/m³<br><small>Jita&nbsp;Buy&nbsp;-7.5%</small></th>
  <th style="text-align: right;">Packaged,&nbsp;m³</th>
  <th style="text-align: right;" class="text-info"><?=$trade_hub_system?> Sell<br><br>Volume</th>
  <th style="text-align: right;">Jita Sell<br>Jita Buy<br>Volume</th>
  <th style="text-align: right;">Querious Sell<br><span class="text-success">Sell&nbsp;-4.13%</span><br>Volume</th>
 </tr>
</thead>
<tbody>
<?php
    if ($trade_hub_orders)
        foreach ($trade_hub_orders as &$product)
        {
            $tid = $product['id'];
            $nm = $product['name'];
            $packaged_volume = $product['pv'];
            $irmalin_sell = $product['is'];
            $jita_sell = $product['js'];
            $jita_buy = $product['jb'];
            $irmalin_volume = $product['iv'];
            $jita_volume = $product['jv'];
            $profit = $product['p'];
            $querious_sell = $product['qs'];
            $querious_volume = $product['qv'];
?>
<tr>
 <td><img class="icn32" src="<?=__get_img_src($tid,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
 <td><?=$nm?><?=get_clipboard_copy_button($nm)?><br><span class="text-muted"><?=$tid?></span></td>
<?php
  if ($profit <= 0.0)
  {
      ?><td align="right" class="text-warning"><?=number_format($profit,2,'.',',')?></td><?php
  }
  else
  {
      ?><td align="right"><?=number_format($profit,2,'.',',')?></td><?php
  }
?>
 <td align="right"><?=$packaged_volume?></td>
 <td align="right" class="text-info"><?=number_format($irmalin_sell,2,'.',',')?><br><br><?=number_format($irmalin_volume,0,'.',',')?></td>
 <td align="right"><?=number_format($jita_sell,2,'.',',')?><br><?=number_format($jita_buy,2,'.',',')?><br><?=number_format($jita_volume,0,'.',',')?></td>
<?php
    if (is_null($querious_sell))
    {
        ?><td></td><?php
    }
    else
    {
        $querious_non_profitable = $querious_sell * (1-0.03-0.0113);
        ?><td align="right"><?=number_format($querious_sell,2,'.',',')?><br><?php
        if ($irmalin_sell < $querious_non_profitable)
        {
            ?><span class="text-success"><strong><?=number_format($querious_non_profitable,2,'.',',')?></strong></span><?php
        }
        else
        {
            ?><span class="text-danger"><?=number_format($querious_non_profitable,2,'.',',')?></span><?php
        }
        ?><br><?=number_format($querious_volume,0,'.',',')?></td><?php
    }
?>
</tr>
<?php
        }
?>
</tbody>
</table>
<?php
}

    // если что-то пойдёт не так, то данные будут показаны по Irmalin
    const DEFAULT_TRADE_HUB_ID = 60013945;
    const DEFAULT_TRADE_HUB_SYSTEM = 'Irmalin';


    $trade_hub_id = DEFAULT_TRADE_HUB_ID; // Irmalin по умолчанию
    $trade_hub_system = DEFAULT_TRADE_HUB_SYSTEM;
    if (isset($_GET['trade_hub_id'])) {
        $_get_trade_hub_id = htmlentities($_GET['trade_hub_id']);
        if (is_numeric($_get_trade_hub_id))
            $trade_hub_id = get_numeric($_get_trade_hub_id);
    }

    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
select
 name,
 solar_system_name as ssn,
 prc.up as up
from
 qi.esi_known_stations
  left outer join (
   select ethp_location_id, max(ethp_updated_at) as up
   from qi.esi_trade_hub_prices
   group by 1
  ) prc on (prc.ethp_location_id = location_id)
where location_id = $1;
EOD;
    $params = array($trade_hub_id);
    $trade_hub_status_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $trade_hub_status = pg_fetch_all($trade_hub_status_cursor);
    if ($trade_hub_status)
    {
        $trade_hub_system = $trade_hub_status[0]['ssn'];
    }
    else
    {
        $trade_hub_id = DEFAULT_TRADE_HUB_ID;
        unset($trade_hub_status);
        $trade_hub_status = null;
    }
    //---

    __dump_header($trade_hub_system, FS_RESOURCES);

    //---
    $query = <<<EOD
select 
 jita.ethp_type_id as id,
 tid.sdet_type_name as name,
 tid.sdet_packaged_volume as pv,
 irmalin.ethp_sell as is, -- irmalin sell
 round(jita.ethp_buy::numeric,2) as jb, -- jita buy
 round(jita.ethp_sell::numeric,2) as js, -- jita sell
 irmalin.ethp_sell_volume as iv, -- irmalin volume
 jita.ethp_buy_volume as jv, -- jita volume
 round((((jita.ethp_buy*0.925) - irmalin.ethp_sell) / tid.sdet_packaged_volume)::numeric,2) as p, -- profit/куб.м (-7.5%)
 querious.ethp_sell as qs,
 querious.ethp_sell_volume as qv
from
 (select * from qi.esi_trade_hub_prices where ethp_location_id = 60003760) as jita
  left outer join qi.eve_sde_type_ids tid on (jita.ethp_type_id = tid.sdet_type_id),
 (select * from qi.esi_trade_hub_prices where ethp_location_id = $1) as irmalin
  left outer join (
    select ethp_type_id, ethp_sell, ethp_sell_volume
    from qi.esi_trade_hub_prices
    where ethp_location_id = 1034323745897 -- станка рынка
  ) querious on (querious.ethp_type_id = irmalin.ethp_type_id)
where
 jita.ethp_type_id = irmalin.ethp_type_id and
 irmalin.ethp_sell < jita.ethp_buy and
 irmalin.ethp_sell_volume > 0 and
 jita.ethp_buy_volume > 0
order by 9 desc;
EOD;
    $params = array($trade_hub_id);
    $trade_hub_orders_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $trade_hub_orders = pg_fetch_all($trade_hub_orders_cursor);
    //---
    pg_close($conn);
?>
<div class="container-fluid">
<h2>Profitable Orders</h2>
<p>Ниже перечислены товары, продающиеся в <strong><?=$trade_hub_system?></strong> по цене ниже Jita Buy. Параметр <strong>Profit</strong> рассчитывается:<br>
<em>Profit = (Jita Buy - 7.5%) / Packaged Volume,</em><br>
таким образом, этот параметр измеряется в ISK/m³ для того, чтобы наиболее эффективно заполнить карго jump-фуры.</p>
<?php
  if ($trade_hub_status)
  {
      ?><p>Станция рынка: <span class="text-primary"><?=$trade_hub_status[0]['name']?></span><?=get_clipboard_copy_button($trade_hub_status[0]['name'])?><br>Время последней актуализации данных: <span class="text-primary"><?=is_null($trade_hub_status[0]['up'])?'нет данных':$trade_hub_status[0]['up'].' ET'?></span></p><?php
  }
?>
<?php __dump_trade_hub_orders($trade_hub_orders, $trade_hub_system); ?>
<button class="btn btn-default" type="button" id="btn-copyAllItemsIntoClipboard">Copy all items into Clipboard</button>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>
<?php __dump_copy_to_clipboard_javascript() ?>

<script>
$('#btn-copyAllItemsIntoClipboard').on('click', function () {
 var data_copy = '';
 $('#tblMarket tbody tr td:nth-child(2) a').each(function() {
  var nm = $(this).attr('data-copy');
  if (nm === null) return;
  if (data_copy) data_copy += nm + "\n"; else data_copy = nm;
 });
 doCopyToClpbrd($(this), data_copy);
});
</script>
