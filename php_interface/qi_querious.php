<?php
include 'qi_render_html.php';
include_once '.settings.php';


const JITA_IMPORT_PRICE = 866.0; // цена импорта 1куб.м. из Jita в Querious
const MIN_PROFIT = 0.05; // 5%
const DEFAULT_PROFIT = 0.1; // 10%
const MAX_PROFIT = 0.25; // 25%
const TAX_AND_FEE = 0.02 + 0.036; // налог на структуре и брокерская комиссия


function eve_ceiling($isk) {
    if ($isk < 100.0) ;
    else if ($isk < 1000.0) $isk = ceil($isk * 10.0) / 10.0;
    else if ($isk < 10000.0) $isk = ceil($isk);
    else if ($isk < 100000.0) $isk = round($isk+5, -1);
    else if ($isk < 1000000.0) $isk = round($isk+50, -2);
    else if ($isk < 10000000.0) $isk = round($isk+500, -3);
    else if ($isk < 100000000.0) $isk = round($isk+5000, -4);
    else if ($isk < 1000000000.0) $isk = round($isk+50000, -5);
    else if ($isk < 10000000000.0) $isk = round($isk+500000, -6);
    else if ($isk < 100000000000.0) $isk = round($isk+5000000, -7);
    else $isk = null;
    return $isk;
}


function __dump_querious_market(&$market, &$storage, &$purchase) { ?>
<h2>Keepstar Market</h2>
<style>
.label-noordersreal { color: #fff; background-color: #d9534f; }
.label-noorders { color: #fff; background-color: #eebbb9; }
.label-interrupt { color: #8e8e8e; background-color: #e8ce43; }
.label-dontbuy { color: #e8ce43; background-color: #b74c33; }
.label-needdelivery { color: #fff; background-color: #5bc0de; }
.label-placeanorder { color: #fff; background-color: #d973e8; }
.label-lowprice { color: #fff; background-color: #f0ad4e; }
.label-highprice { color: #fff; background-color: #777; }
.label-veryfew { color: #fff; background-color: #337ab7; }
.text-muted-much { color: #bbb; }
</style>
<table class="table table-condensed" style="padding:1px;font-size:smaller;" id="tblMarket">
<thead>
 <tr>
  <th></th>
  <th>Items</th>
  <th style="text-align: right;">Weekly<br><mark>Order</mark></th>
  <th style="text-align: right;">RI4 Price&nbsp;/&nbsp;P-ZMZV Sell<br>Quantity</th>
  <th style="text-align: right;">Jita Buy..Sell<br><mark>Import Price</mark></th>
  <th style="text-align: right;">Amarr<br>Sell</th>
  <th style="text-align: right;">Universe<br>Price</th>
  <th style="text-align: center;">Details</th>
 </tr>
</thead>
<tbody>
<?php
    $summary_market_price = 0;
    $summary_market_volume = 0;
    $summary_jita_sell = 0;
    $summary_jita_buy = 0;
    $amarr_buy_order = '';
    $jita_buy_order = '';
    $amarr_buy_price = 0.0;
    $jita_buy_price = 0.0;
    $prev_market_group = null;
    if ($market)
        foreach ($market as &$product)
        {
            $problems = '';
            $warnings = '';
            $interrupt_detected = false;

            $tid = $product['id'];
            $market_group = $product['grp'];
            $nm = $product['name'];
            $weekly_volume = $product['wv'];
            $order_volume = $product['ov'];
            $day_volume = $product['dv'];
            $ri4_market_quantity = $product['mv'];
            $packaged_volume = $product['pv'];
            $jita_import_price = $packaged_volume * JITA_IMPORT_PRICE;
            $jita_sell = $product['js'];
            $jita_buy = $product['jb'];
            $amarr_sell = $product['as'];
            $jita_price_lower = $jita_sell < $amarr_sell;
            $amarr_price_lower = $amarr_sell < $jita_sell;
            $universe_price = $product['up'];
            $ri4_price = $product['mp'];
            //$markup = $jita_sell * TAX_AND_FEE;
            //$jita_10_price = eve_ceiling($jita_sell * (1.0+DEFAULT_PROFIT+TAX_AND_FEE)); // Jita +10% Price
            //$jita_10_profit = $jita_10_price - $jita_sell - $markup;
            $pzmzv_sell = $product['ps'];
            $pzmzv_sell_volume = $product['psv'];

            $storage_quantity = 0;
            if ($storage)
                foreach ($storage as &$stock)
                {
                    $sid = $stock['id'];
                    if ($sid != $tid) continue;
                    $storage_quantity = $stock['q'];
                    break;
                }

            if (is_null($ri4_price)) {
                if (is_null($pzmzv_sell_volume) || !$pzmzv_sell_volume)
                    $problems .= '<span class="label label-noordersreal">no orders</span>&nbsp;';
                else
                    $problems .= '<span class="label label-noorders">no orders</span>&nbsp;';
            }
            if (!is_null($ri4_market_quantity)) {
                if ($weekly_volume >= ($ri4_market_quantity+$storage_quantity))
                    $problems .= '<span class="label label-needdelivery">need delivery</span>&nbsp;';
                if ($storage_quantity && ($weekly_volume >= $ri4_market_quantity))
                    $warnings .= '<span class="label label-placeanorder">place an order</span>&nbsp;';
            }
            if (!is_null($ri4_market_quantity) && ($order_volume >= $ri4_market_quantity)) $problems .= '<span class="label label-veryfew">very few</span>&nbsp;';
            if (!is_null($ri4_price)) {
                if ($ri4_price > 100000 || $packaged_volume < 5) {
                    $min_jita_price = $jita_sell * (1.0+MIN_PROFIT+TAX_AND_FEE);
                    $min_amarr_price = $amarr_sell * (1.0+MIN_PROFIT+TAX_AND_FEE);
                    if (($ri4_price < $min_jita_price) && ($ri4_price < $min_amarr_price))
                        $warnings .= '<span class="label label-lowprice" data-toggle="tooltip" data-placement="bottom" title="Min Amarr: '.number_format(eve_ceiling($min_amarr_price),2,'.',',').', min Jita: '.number_format(eve_ceiling($min_jita_price),2,'.',',').'">low price</span>&nbsp;';
                }
                $max_jita_price = $jita_sell * (1.0+MAX_PROFIT+TAX_AND_FEE);
                $max_amarr_price = $amarr_sell * (1.0+MAX_PROFIT+TAX_AND_FEE);
                if (($ri4_price > $max_jita_price) && ($ri4_price > $max_amarr_price))
                    $warnings .= '<span class="label label-highprice" data-toggle="tooltip" data-placement="bottom" title="Max Amarr: '.number_format(eve_ceiling($max_amarr_price),2,'.',',').', max Jita: '.number_format(eve_ceiling($max_jita_price),2,'.',',').'">price too high</span>&nbsp;';
                if (!is_null($pzmzv_sell) && ($pzmzv_sell < $ri4_price) && ($pzmzv_sell_volume > $ri4_market_quantity)) {
                    $interrupt_detected = true;
                    $warnings .= '<span class="label label-interrupt">interrupt</span>&nbsp;';
                }
            }
            if ($pzmzv_sell_volume > $ri4_market_quantity) {
                // рассчитываем минимальную цену, ниже которой закупку производить не следует - позиция перебита конкурентами
                $min_buy_price = $pzmzv_sell / (1.0+TAX_AND_FEE+MIN_PROFIT);
                if (($jita_sell > $min_buy_price) && ($amarr_sell > $min_buy_price))
                    $warnings .= '<span class="label label-dontbuy" data-toggle="tooltip" data-placement="bottom" title="Min buy price: '.number_format(eve_ceiling($min_buy_price),2,'.',',').'">don&apos;t buy</span>&nbsp;';
                else if ($amarr_sell > $min_buy_price)
                    $warnings .= '<span class="label label-dontbuy" data-toggle="tooltip" data-placement="bottom" title="Min buy price: '.number_format(eve_ceiling($min_buy_price),2,'.',',').'">don&apos;t buy in Amarr</span>&nbsp;';
                else if ($jita_sell > $min_buy_price)
                    $warnings .= '<span class="label label-dontbuy" data-toggle="tooltip" data-placement="bottom" title="Min buy price: '.number_format(eve_ceiling($min_buy_price),2,'.',',').'">don&apos;t buy in Jita</span>&nbsp;';
            }

            if (!is_null($ri4_market_quantity)&&!is_null($ri4_price)) $summary_market_price += $ri4_market_quantity * $ri4_price;
            if (!is_null($packaged_volume)) $summary_market_volume += $ri4_market_quantity * $packaged_volume;
            $summary_jita_sell += $ri4_market_quantity * $jita_sell;
            $summary_jita_buy += $ri4_market_quantity * $jita_buy;

            if (!empty($problems)) {
                if ($amarr_sell <= $jita_sell) {
                    $amarr_buy_order .= $nm.' '.ceil($weekly_volume)."\n";
                    $amarr_buy_price += $amarr_sell * ceil($weekly_volume);
                }
                else {
                    $jita_buy_order .= $nm.' '.ceil($weekly_volume)."\n";
                    $jita_buy_price += $jita_sell * ceil($weekly_volume);
                }
            }

            // определяем, выполнялась ли закупка этого продукта в последнее время?
            $we_bought_it = false; // array_search($tid, array_column($purchase, 'id')) !== false;
            if ($purchase)
                foreach ($purchase as &$buy)
                {
                    $buy_id = $buy['id'];
                    if ($buy_id < $tid) continue;
                    if ($buy_id > $tid) break;
                    $we_bought_it = true;
                    break;
                }

            if ($prev_market_group != $market_group)
            {
                $prev_market_group = $market_group;
                ?><tr><td class="active" colspan="8"><strong><?=$market_group?></strong></td></tr><?php
            }
?>
<tr>
 <td><img class="icn32" src="<?=__get_img_src($tid,32,FS_RESOURCES)?>" width="32px" height="32px"></td>

 <td><?=$nm?><?=get_clipboard_copy_button($nm)?><?=(!is_null($day_volume)&&$day_volume)?' <span style="background-color:#00fa9a">&nbsp;+ '.number_format($day_volume,0,'.',',').'&nbsp;</span>':''?><?='<br><span class="text-muted">'.$tid.'</span> '.$problems.$warnings?></td>

 <?php if (is_null($weekly_volume)) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($weekly_volume,1,'.',',')?><br><mark><span style="font-size: smaller;"><?=number_format($order_volume,1,'.',',')?></span></mark></td>
 <?php } ?>

<?php
    // поле с информацией о наличии товара на рынке
    if (is_null($pzmzv_sell) && is_null($ri4_price))
    {
        ?><td></td><?php
    }
    else
    {
        if ($interrupt_detected) { ?><td align="right" bgcolor="#e8c8c8"><?php } else { ?><td align="right"><?php }

        if (!is_null($ri4_price))
        {
            ?><?=number_format($ri4_price,2,'.',',')?>&nbsp;<mark><?=number_format($ri4_market_quantity,0,'.',',')?></mark><?php
        }
        if ($storage_quantity)
        {
            ?>&nbsp;<small><span style="background-color:#c7c7c7">&nbsp;+ <?=number_format($storage_quantity,0,'.',',')?>&nbsp;</span></small><?php
        }
        if (!is_null($pzmzv_sell))
        {
            if (!is_null($ri4_price) && ($ri4_price == $pzmzv_sell) && ($ri4_market_quantity == $pzmzv_sell_volume))
            {
            }
            else
            {
                if ($ri4_price == $pzmzv_sell) { ?><span class="text-muted-much"><?php }
                ?><br><?=number_format($pzmzv_sell,2,'.',',')?>&nbsp;<mark><?=number_format($pzmzv_sell_volume,0,'.',',')?></mark><?php
                if ($ri4_price == $pzmzv_sell) { ?></span><?php }
            }
        }

        ?></td><?php
    }

  if (is_null($amarr_sell)) { ?><td></td><?php }
  else
  {
    ?><td align="right"><small><span class="text-muted-much"><?=number_format($jita_buy,2,'.',',')?> ..</span></small> <?=$amarr_price_lower?'<span class="text-muted-much">':''?><?=number_format($jita_sell,2,'.',',')?><?=$amarr_price_lower?'</span>':''?><br><mark><small><?=number_format($jita_import_price,2,'.',',')?></small></mark></td><?php
  }

  if (is_null($amarr_sell)) { ?><td></td><?php }
  else
  {
      ?><td align="right"><?=$jita_price_lower?'<span class="text-muted-much">':''?><?=number_format($amarr_sell,2,'.',',')?><?=$jita_price_lower?'</class>':''?></td><?php
  }
?>

 <td align="right"><?=number_format($universe_price,2,'.',',')?></td>

<?php
    // поле с кнопкой details
    if (!$we_bought_it)
    {
        ?><td align="center"><button type="button" class="btn btn-default btn-xs qind-btn-details" type_id="<?=$tid?>">details…</button></td><?php
    }
    else
    {
        ?><td align="center"><button type="button" class="btn btn-primary btn-xs qind-btn-details" type_id="<?=$tid?>">details…</button></td><?php
    }
?>
</tr>
<?php
    }
?>
<tr style="font-weight:bold;">
 <td colspan="3" align="right">Summary</td>
 <td align="right"><?=number_format($summary_market_price,0,'.',',').'<br>'.number_format($summary_market_volume,0,'.',',')?>m³</td>
 <td align="right"><?=number_format($summary_jita_sell,0,'.',',').'<br>'.number_format($summary_jita_buy,0,'.',',')?></td>
 <td colspan="4"></td>
</tr>
</tbody>
</table>

<div class="row">
 <div class="col-md-6">
  <button class="btn btn-default" type="button" data-toggle="collapse" data-target="#collapseAmarrBuyOrder" aria-expanded="false" aria-controls="collapseAmarrBuyOrder">Amarr Buy Order</button>
  <div class="collapse" id="collapseAmarrBuyOrder">
   <div class="card card-body">
    <?php if (!is_null($amarr_buy_order)) { ?>
     <pre class="pre-scrollable" style="border: 0; background-color: transparent; font-size: 11px;"><?=$amarr_buy_order?></pre>
     <b>Amarr sell price: <?=number_format($amarr_buy_price,2,'.',',')?></b>
    <?php } ?>
   </div>
  </div>
 </div>
 <div class="col-md-6">
  <button class="btn btn-default" type="button" data-toggle="collapse" data-target="#collapseJitaBuyOrder" aria-expanded="false" aria-controls="collapseJitaBuyOrder">Jita Buy Order</button>
  <div class="collapse" id="collapseJitaBuyOrder">
   <div class="card card-body">
    <?php if (!is_null($jita_buy_order)) { ?>
     <pre class="pre-scrollable" style="border: 0; background-color: transparent; font-size: 11px;"><?=$jita_buy_order?></pre>
     <b>Jita sell price: <?=number_format($jita_buy_price,2,'.',',')?></b>
    <?php } ?>
   </div>
  </div>
 </div>
</div>

<?php
}


function __dump_querious_storage(&$storage) { ?>
<h2>Keepstar Storage</h2>
<table class="table table-condensed" style="padding:1px;font-size:smaller;" id="tblStock">
<thead>
 <tr>
  <th></th>
  <th>Items</th>
  <th style="text-align: right;">Quantity<br>in Storage</th>
  <th style="text-align: right;">RI4<br>Sell</th>
  <th style="text-align: right;">P-ZMZV Sell<br><mark>Quantity</mark></th>
  <th style="text-align: right;">Jita Buy..Sell<br><mark>Import Price</mark></th>
  <th style="text-align: right;">Amarr<br>Sell</th>
  <th style="text-align: right;">Universe<br>Price</th>
 </tr>
</thead>
<tbody>
<?php
    $summary_jita_sell = 0;
    $summary_jita_buy = 0;
    if ($storage)
        foreach ($storage as &$product)
        {
            $tid = $product['id'];
            $nm = $product['name'];
            $quantity = $product['q'];
            $ri4_sell = $product['rs'];
            $ri4_sell_volume = $product['rsv'];
            $pzmzv_sell = $product['ps'];
            $pzmzv_sell_volume = $product['psv'];
            $packaged_volume = $product['pv'];
            $jita_import_price = $packaged_volume * JITA_IMPORT_PRICE;
            $jita_sell = $product['js'];
            $jita_buy = $product['jb'];
            $amarr_sell = $product['as'];
            $universe_price = $product['up'];

            $summary_jita_sell += $jita_sell * $ri4_sell_volume;
            $summary_jita_buy += $jita_buy * $ri4_sell_volume;
?>
<tr>
 <td><img class="icn32" src="<?=__get_img_src($tid,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
 <td><?=$nm.'<br><span class="text-muted">'.$tid.'</span> '?></td>
 <td align="right"><?=number_format($quantity,0,'.',',')?></td>
 <?php if (is_null($ri4_sell)) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($ri4_sell,2,'.',',')?><br><mark><?=number_format($ri4_sell_volume,0,'.',',')?></mark></td>
 <?php } ?>
 <?php if (is_null($pzmzv_sell)) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($pzmzv_sell,2,'.',',')?><br><mark><?=number_format($pzmzv_sell_volume,0,'.',',')?></mark></td>
 <?php } ?>
 <td align="right"><?=number_format($jita_buy,2,'.',',')?> .. <?=number_format($jita_sell,2,'.',',')?><br><mark><?=number_format($jita_import_price,2,'.',',')?></mark></td>
 <td align="right"><?=number_format($amarr_sell,2,'.',',')?></td>
 <td align="right"><?=number_format($universe_price,2,'.',',')?></td>
</tr>
<?php
        }
?>
<tr style="font-weight:bold;">
 <td colspan="5" align="right">Summary</td>
 <td align="right"><?=number_format($summary_jita_sell,0,'.',',').'<br>'.number_format($summary_jita_buy,0,'.',',')?></td>
 <td colspan="3"></td>
</tr>
</tbody>
</table>
<?php
}



    __dump_header("Querious Market", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
select
  market.type_id as id,
  market_group.name as grp,
  tid.sdet_type_name as name,
  case
    when (weeks_passed.volume_sell=0) or (weeks_passed.diff<0.14) then null
    when (weeks_passed.diff < 1.14) then weeks_passed.volume_sell
    else round(weeks_passed.volume_sell/weeks_passed.diff,1)
  end as wv, -- weekly volume
  round(transactions_stat.avg_volume, 1) as ov, -- order volume
  transactions_stat.sum_last_day as dv, -- day volume
  orders_stat.volume_remain as mv, -- RI4 volume
  coalesce(tid.sdet_packaged_volume, 0) as pv, -- packaged volume
  jita.sell as js, -- jita sell
  jita.buy as jb, -- jita buy
  amarr.sell as as, -- amarr sell
  case
    when universe.emp_average_price is null or (universe.emp_average_price < 0.001) then universe.emp_adjusted_price
    else universe.emp_average_price
  end as up, -- universe price
  round(orders_stat.ri4_price::numeric, 2) as mp, -- RI4 price
  sbsq_hub.ethp_sell as ps, -- p-zmzv sell
  sbsq_hub.ethp_sell_volume as psv -- p-zmzv sell volume
from
  qi.eve_sde_market_groups_semantic as market_group,
  ( select distinct type_id
    from (
      -- список транзакций по покупке/продаже избранными персонажами от имени 2х корпораций
      select ecwt_type_id as type_id --, 'j'::char as type
      from
        esi_corporation_wallet_journals j
          left outer join esi_corporation_wallet_transactions t on (ecwj_context_id = ecwt_transaction_id) -- (j.ecwj_reference_id = t.ecwt_journal_ref_id)
      where
        (ecwj_date > '2021-08-15') and
        (ecwj_context_id_type = 'market_transaction_id') and
        ( ( ecwj_corporation_id in (98615601) and -- R Initiative 4
            ecwj_second_party_id in (2116129465,2116746261,2116156168,2119173458) and -- Qandra Si, Kekuit Void, Qunibbra Do, Zenorti Void
            ( ecwt_location_id in (1036927076065,1034323745897) and not ecwt_is_buy or -- станка рынка
              ecwt_location_id not in (1036927076065,1034323745897) and ecwt_is_buy
            ) and
            ecwj_division = 1) or
          ( ecwj_corporation_id in (98553333) and -- R Strike
            ecwj_second_party_id in (95858524) and -- Xatul' Madan
            ecwt_is_buy and
            ecwj_division = 7)
        )
      union
      -- список того, что корпорация продавала или продаёт
      select ecor_type_id --, 'o'::char
      from esi_corporation_orders
      where
        not ecor_is_buy_order and
        (ecor_corporation_id=98615601) and  -- R Initiative 4
        (ecor_location_id in (1036927076065,1034323745897)) -- станка рынка
      ) jto
  ) market
    -- сведения о предмете
    left outer join eve_sde_type_ids tid on (market.type_id = tid.sdet_type_id)
    -- цены в жите прямо сейчас
    left outer join (
      select ethp_type_id, ethp_sell as sell, ethp_buy as buy
      from esi_trade_hub_prices
      where ethp_location_id = 60003760
    ) jita on (market.type_id = jita.ethp_type_id)
    -- цены в амарре прямо сейчас
    left outer join (
      select ethp_type_id, ethp_sell as sell
      from esi_trade_hub_prices
      where ethp_location_id = 60008494
    ) amarr on (market.type_id = amarr.ethp_type_id)
    -- усреднённые цены по евке прямо сейчас
    left outer join esi_markets_prices universe on (market.type_id = universe.emp_type_id)
    -- сведения о длительности sell-ордеров и о кол-ве проданного на станке рынка
    left outer join (
      select
        ecor_type_id,
        (current_date - min(ecor_issued::date))/7.0 as diff,
        sum(ecor_volume_total - ecor_volume_remain) as volume_sell
      from esi_corporation_orders
      where
        not ecor_is_buy_order and
        (ecor_corporation_id=98615601) and  -- R Initiative 4
        (ecor_location_id in (1036927076065,1034323745897))  -- станка рынка
      group by ecor_type_id
    ) weeks_passed on (market.type_id = weeks_passed.ecor_type_id)
    -- усреднённый (типовой) объём sell-ордера по продаже
    -- количество проданных товаров за последние сутки
    left outer join (
      select
        ecwt_type_id,
        avg(ecwt_quantity) as avg_volume,
        sum(case when (ecwt_date >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '24 hours')) then ecwt_quantity else 0 end) as sum_last_day
      from esi_corporation_wallet_transactions
      where
        not ecwt_is_buy and
        (ecwt_corporation_id=98615601) and  -- R Initiative 4
        (ecwt_location_id in (1036927076065,1034323745897)) -- станка рынка
      group by 1
    ) transactions_stat on (market.type_id = transactions_stat.ecwt_type_id)
    -- сведения о sell-ордерах, активных прямо сейчас
    left outer join (
      select
        ecor_type_id,
        sum(ecor_volume_remain) as volume_remain,
        min(ecor_price) as ri4_price
      from esi_corporation_orders
      where
        not ecor_is_buy_order and
        (ecor_volume_remain > 0) and
        not ecor_history and
        (ecor_corporation_id=98615601) and  -- R Initiative 4
        (ecor_location_id in (1036927076065,1034323745897))  -- станка рынка
      group by 1
    ) orders_stat on (market.type_id = orders_stat.ecor_type_id)
    -- ордера (в т.ч. и не наши) на данный товар на на нашей структуре
    left outer join (
      select
        ethp_type_id,
        -- to_char(ethp_sell, 'FM999G999G999G999.90') || ' (x' || to_char(ethp_sell_volume, 'FM999999999999999999') || ')' a$
        ethp_sell, ethp_sell_volume
        --, ethp_buy, ethp_buy_volume
      from qi.esi_trade_hub_prices
      where ethp_location_id = 1034323745897
    ) sbsq_hub on (market.type_id = sbsq_hub.ethp_type_id)
where
  market_group.id = tid.sdet_market_group_id and
  market_group.semantic_id not in (
    19, -- Trade Goods
    150, -- Skills
    499, -- Advanced Moon Materials
    500, -- Processed Moon Materials
    501, -- Raw Moon Materials
    1031, -- Raw Materials
    1035,65,781,1021,1147,1865,1870,1883,1908,2768, -- Components
    1332, -- Planetary Materials
    1857, -- Minerals
    1858, -- Booster Materials
    1860, -- Polymer Materials
    1861, -- Salvage Materials
    1872, -- Research Equipment
    2767 -- Molecular-Forged Materials
  )
-- order by tid.sdet_packaged_volume desc
order by market_group.name, tid.sdet_type_name;
EOD;
    $market_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $market = pg_fetch_all($market_cursor);
    //---
    // --SET intervalstyle = 'postgres_verbose';
    // select eca_item_id as office_id -- 1037133900408
    // from qi.esi_corporation_assets
    // where eca_location_id = 1034323745897 and eca_corporation_id = 98615601 and eca_location_flag = 'OfficeFolder';
    //---
    $query = <<<EOD
select
  -- hangar.eca_item_id,
  hangar.eca_type_id as id,
  tid.sdet_type_name as name,
  hangar.eca_quantity as q,
  ri4_orders.avg_price as rs, -- ri4 sell
  ri4_orders.volume as rsv, -- ri4 sell volume : to_char(ri4_orders.avg_price, 'FM999G999G999G999.90') || ' (x' || to_char(ri4_orders.volume, 'FM999999999999999999') || ')'
  sbsq_hub.ethp_sell as ps, -- p-zmzv sell
  sbsq_hub.ethp_sell_volume as psv, -- p-zmzv sell volume
  coalesce(tid.sdet_packaged_volume, 0) as pv, -- packaged volume
  jita.sell as js, -- jita sell : to_char(jita.sell, 'FM999G999G999G999G999.90')
  jita.buy as jb, -- jita buy : to_char(jita.buy, 'FM999G999G999G999G999.90')
  amarr.sell as as, -- amarr sell : to_char(amarr.sell, 'FM999G999G999G999G999.90')
  universe.price as up -- universe price : to_char(universe.price, 'FM999G999G999G999G999.90')
from
  -- предметы на продажу в ангаре
  qi.esi_corporation_assets hangar
    -- сведения о предмете
    left outer join qi.eve_sde_type_ids tid on (hangar.eca_type_id = tid.sdet_type_id)
    -- цены в жите прямо сейчас
    left outer join (
      select ethp_type_id, ethp_sell as sell, ethp_buy as buy
      from qi.esi_trade_hub_prices
      where ethp_location_id = 60003760
    ) jita on (hangar.eca_type_id = jita.ethp_type_id)
    -- цены в амарре прямо сейчас
    left outer join (
      select ethp_type_id, ethp_sell as sell
      from qi.esi_trade_hub_prices
      where ethp_location_id = 60008494
    ) amarr on (hangar.eca_type_id = amarr.ethp_type_id)
    -- усреднённые цены по евке прямо сейчас
    left outer join (
      select
        emp_type_id,
        case
          when emp_average_price is null or (emp_average_price < 0.001) then emp_adjusted_price
          else emp_average_price
        end as price
      from qi.esi_markets_prices
    ) universe on (hangar.eca_type_id = universe.emp_type_id)
    -- ордера (в т.ч. и не наши) на данный товар на на нашей структуре
    left outer join (
      select
        ethp_type_id,
        -- to_char(ethp_sell, 'FM999G999G999G999.90') || ' (x' || to_char(ethp_sell_volume, 'FM999999999999999999') || ')' as sell,
        ethp_sell, ethp_sell_volume
        --, ethp_buy, ethp_buy_volume
      from qi.esi_trade_hub_prices
      where ethp_location_id = 1034323745897
    ) sbsq_hub on (hangar.eca_type_id = sbsq_hub.ethp_type_id)
    -- сведения об sell-ордерах, активных прямо сейчас
    left outer join (
      select
        o.ecor_type_id,
        o.volume_remain as volume,
        round(o.price_remain::numeric / o.volume_remain::numeric, 2) as avg_price
      from (
        select
          ecor_type_id,
          sum(ecor_volume_remain) as volume_remain,
          sum(ecor_price*ecor_volume_remain) as price_remain
        from qi.esi_corporation_orders
        where
          not ecor_is_buy_order and
          (ecor_volume_remain > 0) and
          not ecor_history and
          (ecor_corporation_id=98615601) and  -- R Initiative 4
          (ecor_location_id in (1036927076065,1034323745897))  -- станка рынка
        group by 1
      ) o
    ) ri4_orders on (hangar.eca_type_id = ri4_orders.ecor_type_id)
where
  ( hangar.eca_location_id = 1037133900408 and hangar.eca_location_flag = 'CorpSAG4' or
    hangar.eca_location_id = 1037061477103
  ) and
  hangar.eca_location_type = 'item' and
  not exists (select box.eca_item_id from qi.esi_corporation_assets as box where box.eca_location_id = hangar.eca_item_id)
-- order by universe.price desc
order by tid.sdet_market_group_id, tid.sdet_type_name;
EOD;
    $storage_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $storage = pg_fetch_all($storage_cursor);
    //---
    $query = <<<EOD
select
  buy.ecwt_type_id as id,
  buy.dt as dt,
  round((buy.sup/buy.sq)::numeric, 2) as up,
  buy.sq as sq
from (
  select
    t.ecwt_type_id,
    j.ecwj_date::date as dt,
    sum(t.ecwt_unit_price*t.ecwt_quantity) as sup,
    sum(t.ecwt_quantity) as sq
  from
    esi_corporation_wallet_journals j
      left outer join esi_corporation_wallet_transactions t on (ecwj_context_id = ecwt_transaction_id) -- (j.ecwj_reference_id = t.ecwt_journal_ref_id)
  where
    (ecwj_date > (now() - '14 days'::interval)::date) and
    (ecwj_context_id_type = 'market_transaction_id') and
    ecwt_is_buy and
    ( ( ecwj_corporation_id in (98615601) and -- R Initiative 4
        ecwj_second_party_id in (2116129465,2116746261,2116156168,2119173458) and -- Qandra Si, Kekuit Void, Qunibbra Do, Zenorti Void
        ecwt_location_id not in (1036927076065,1034323745897) and -- станка рынка
        ecwj_division = 1) or
      ( ecwj_corporation_id in (98553333) and -- R Strike
        ecwj_second_party_id in (95858524) and -- Xatul' Madan
        ecwj_division = 7)
    )
  group by 1, 2
) buy
order by 1, 2 desc;
EOD;
    $purchase_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $purchase = pg_fetch_all($purchase_cursor);
    //---
    pg_close($conn);
?>

<div class="container-fluid">
<div class="btn-group btn-group-toggle" data-toggle="buttons">
 <label class="btn btn-default qind-btn-market active" group="all"><input type="radio" name="options" autocomplete="off" checked>Все</label>
 <label class="btn btn-default qind-btn-market" group="sold"><input type="radio" name="options" autocomplete="off">Всё продано</label>
 <label class="btn btn-default qind-btn-market" group="very-few"><input type="radio" name="options" autocomplete="off">Товар заканчивается</label>
 <label class="btn btn-default qind-btn-market" group="need-delivery"><input type="radio" name="options" autocomplete="off">Требуется доставка</label>
 <label class="btn btn-default qind-btn-market" group="place-an-order"><input type="radio" name="options" autocomplete="off">Выставить на продажу</label>
 <label class="btn btn-default qind-btn-market" group="low-price"><input type="radio" name="options" autocomplete="off">Цена занижена</label>
 <label class="btn btn-default qind-btn-market" group="high-price"><input type="radio" name="options" autocomplete="off">Цена завышена</label>
 <label class="btn btn-default qind-btn-market" group="interrupt"><input type="radio" name="options" autocomplete="off">Конкуренты</label>
</div>
<?php __dump_querious_market($market, $storage, $purchase); ?>
<!-- --- --- --- -->
<hr>
<!-- --- --- --- -->
<div class="btn-group btn-group-toggle" data-toggle="buttons">
 <label class="btn btn-default qind-btn-stock" group="all"><input type="radio" name="options" autocomplete="off" checked>Показать</label>
 <label class="btn btn-default qind-btn-stock active" group="hide"><input type="radio" name="options" autocomplete="off">Скрыть</label>
</div>
<?php __dump_querious_storage($storage); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>

<div class="modal fade" id="modalDetails" tabindex="-1" role="dialog" aria-labelledby="modalDetailsLabel">
 <div class="modal-dialog" role="document">
  <div class="modal-content">
   <div class="modal-header">
    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
    <h4 class="modal-title" id="modalDetailsLabel"></h4>
   </div>
   <div class="modal-body">
<!-- -->
<div class="table-responsive">
 <table class="table table-condensed" style="padding:1px;font-size:small;" id="tblPurchase">
  <thead>
   <tr>
    <th>Даты закупки (посл. 2 нед)</th>
    <th style="text-align:right;">Кол-во</th>
    <th style="text-align:right; width:120px;">Усредн. цена,&nbsp;ISK</th>
   </tr>
  </thead>
  <tbody>
  </tbody>
 </table>
</div>
<hr>
<div class="row">
  <div class="col-md-8">Объём в упакованном виде</div>
  <div class="col-md-4" align="right"><mark id="dtlsPackedVolume"></mark> m³</div>
</div>
<div class="row">
  <div class="col-md-8">Стоимость доставки из Jita</div>
  <div class="col-md-4" align="right"><mark id="dtlsImportPrice"></mark> ISK</div>
</div>
<div class="row">
  <div class="col-md-8">Текущая Jita Sell цена</div>
  <div class="col-md-4" align="right"><mark id="dtlsJitaSell"></mark> ISK</div>
</div>
<div class="row">
  <div class="col-md-8">Текущая Jita Buy цена</div>
  <div class="col-md-4" align="right"><mark id="dtlsJitaBuy"></mark> ISK</div>
</div>
<div class="row">
  <div class="col-md-8">Текущая Amarr Sell цена</div>
  <div class="col-md-4" align="right"><mark id="dtlsAmarrSell"></mark> ISK</div>
</div>
<div class="row">
  <div class="col-md-8">Средняя цена товара на Tranquility</div>
  <div class="col-md-4" align="right"><mark id="dtlsUniversePrice"></mark> ISK</div>
</div>
<div class="row">
  <div class="col-md-8">Усредн. цена последнего закупа</div>
  <div class="col-md-4" align="right"><mark id="dtlsLastBuyPrice"></mark> ISK</div>
</div>
<hr>
<div class="btn-group btn-group-toggle" data-toggle="buttons" packed_volume="" id="dtlsCalc">
 <label class="btn btn-default qind-btn-calc" price="" profit="<?=DEFAULT_PROFIT?>" caption="Jita Sell +<?=DEFAULT_PROFIT*100?>%" id="dtlsCalcJS10"><input type="radio" name="options" autocomplete="off" checked>Jita +<?=DEFAULT_PROFIT*100?>%</label>
 <label class="btn btn-default qind-btn-calc" price="" profit="0.05" caption="Jita Sell +5%" id="dtlsCalcJS5"><input type="radio" name="options" autocomplete="off">Jita +5%</label>
 <label class="btn btn-default qind-btn-calc" price="" profit="0.15" caption="Jita Sell +15%" id="dtlsCalcJS15"><input type="radio" name="options" autocomplete="off">Jita +15%</label>
 <label class="btn btn-default qind-btn-calc" price="" profit="<?=DEFAULT_PROFIT?>" caption="Amarr Sell +<?=DEFAULT_PROFIT*100?>%" id="dtlsCalcAS10"><input type="radio" name="options" autocomplete="off">Amarr +<?=DEFAULT_PROFIT*100?>%</label>
 <label class="btn btn-default qind-btn-calc active" price="" profit="<?=DEFAULT_PROFIT?>" caption="от цены закупа +<?=DEFAULT_PROFIT*100?>%" id="dtlsCalcUP10"><input type="radio" name="options" autocomplete="off">Закуп +<?=DEFAULT_PROFIT*100?>%</label>
</div>
<div class="row">
  <div class="col-md-8">Цена закупа</mark></div>
  <div class="col-md-4" align="right"><mark id="dtlsSellVar_purchase"></mark> ISK</div>
</div>
<div class="row">
  <div class="col-md-1"></div>
  <div class="col-md-7">продажа <mark id="dtlsSellVar_name"></mark></div>
  <div class="col-md-4" align="right"><mark id="dtlsSellVar_price"></mark> ISK</div>
</div>
<div class="row">
  <div class="col-md-1"></div>
  <div class="col-md-7"><input type="checkbox" value="" checked="true" id="dtlsSellVar_import_check"> плюс стоимость импорта</div>
  <div class="col-md-4" align="right"><mark id="dtlsSellVar_import"></mark> ISK</div>
</div>
<div class="row">
  <div class="col-md-1"></div>
  <div class="col-md-7">плюс 2% налог и 3.6% комиссия</div>
  <div class="col-md-4" align="right"><mark id="dtlsSellVar_tax"></mark> ISK</div>
</div>
<div class="row">
  <div class="col-md-1"></div>
  <div class="col-md-7">выставить на продажу</div>
  <div class="col-md-4" align="right"><mark id="dtlsSellVar_order"></mark> ISK <a data-target="#" role="button" data-copy="" class="qind-copy-btn" data-toggle="tooltip" data-original-title="" title="" id="dtlsSellVar_order_copy"><span class="glyphicon glyphicon-copy" aria-hidden="true"></a></div>
</div>
<div class="row">
  <div class="col-md-1"></div>
  <div class="col-md-7">профит на единицу товара</div>
  <div class="col-md-4" align="right"><mark id="dtlsSellVar_profit"></mark> ISK</div>
</div>
<!-- -->
   </div>
   <div class="modal-footer">
    <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
   </div>
  </div>
 </div>
</div>

<script>
var g_jita_import_price = <?=JITA_IMPORT_PRICE?>;
var g_market_types = [<?php
    if ($market)
        foreach ($market as &$product)
        {
            $tid = $product['id'];
            $nm = $product['name'];
            //$weekly_volume = $product['wv'];
            //$order_volume = $product['ov'];
            //$day_volume = $product['dv'];
            //$ri4_market_quantity = $product['mv'];
            $packaged_volume = $product['pv'];
            $jita_import_price = $packaged_volume * JITA_IMPORT_PRICE;
            $jita_sell = $product['js'];
            $jita_buy = $product['jb'];
            $amarr_sell = $product['as'];
            //$jita_price_lower = $jita_sell < $amarr_sell;
            //$amarr_price_lower = $amarr_sell < $jita_sell;
            $universe_price = $product['up'];
            //$ri4_price = $product['mp'];
            //$jita_purchase_and_import_price = $jita_sell + $jita_import_price; // то, за сколько будем продавать: закуп + импорт
            //$markup = $jita_purchase_and_import_price * TAX_AND_FEE; // комиссия считается от суммы закупа и транспортировки
            //$jita_10_price = eve_ceiling($jita_purchase_and_import_price * (1.0+DEFAULT_PROFIT+TAX_AND_FEE)); // Jita +10% Price
            //$jita_10_profit = $jita_10_price - $jita_purchase_and_import_price - $markup;
            //$pzmzv_sell = $product['ps'];
            //$pzmzv_sell_volume = $product['psv'];

            print('['.$tid.',"'.$nm.'",'.$packaged_volume.','.(is_null($jita_sell)?'0':$jita_sell).','.(is_null($jita_buy)?'0':$jita_buy).','.(is_null($amarr_sell)?'0':$amarr_sell).','.(is_null($universe_price)?'0':$universe_price)."],\n");
        }
?>];
var g_purchase_types = [<?php
    if ($purchase)
        foreach ($purchase as &$buy)
        {
            print('['.$buy['id'].',"'.$buy['dt'].'",'.$buy['up'].','.$buy['sq'].'],');
        }
?>];

  function numLikeEve(x) {
    if (x < 1.0) return x;
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }
  (function() {
    /**
     * Корректировка округления десятичных дробей.
     *
     * @param {String}  type  Тип корректировки.
     * @param {Number}  value Число.
     * @param {Integer} exp   Показатель степени (десятичный логарифм основания корректировки).
     * @returns {Number} Скорректированное значение.
     */
    function decimalAdjust(type, value, exp) {
      // Если степень не определена, либо равна нулю...
      if (typeof exp === 'undefined' || +exp === 0) {
        return Math[type](value);
      }
      value = +value;
      exp = +exp;
      // Если значение не является числом, либо степень не является целым числом...
      if (isNaN(value) || !(typeof exp === 'number' && exp % 1 === 0)) {
        return NaN;
      }
      // Сдвиг разрядов
      value = value.toString().split('e');
      value = Math[type](+(value[0] + 'e' + (value[1] ? (+value[1] - exp) : -exp)));
      // Обратный сдвиг
      value = value.toString().split('e');
      return +(value[0] + 'e' + (value[1] ? (+value[1] + exp) : exp));
    }
    // Десятичное округление к ближайшему
    if (!Math.round10) {
      Math.round10 = function(value, exp) {
        return decimalAdjust('round', value, exp);
      };
    }
    // Десятичное округление вниз
    if (!Math.floor10) {
      Math.floor10 = function(value, exp) {
        return decimalAdjust('floor', value, exp);
      };
    }
    // Десятичное округление вверх
    if (!Math.ceil10) {
      Math.ceil10 = function(value, exp) {
        return decimalAdjust('ceil', value, exp);
      };
    }
  })();
  function eveCeiling(isk) {
    if (isk < 100.0) ;
    else if (isk < 1000.0) isk = Math.ceil10(isk * 10.0) / 10.0;
    else if (isk < 10000.0) isk = Math.ceil10(isk);
    else if (isk < 100000.0) isk = Math.round10(isk+5, 1);
    else if (isk < 1000000.0) isk = Math.round10(isk+50, 2);
    else if (isk < 10000000.0) isk = Math.round10(isk+500, 3);
    else if (isk < 100000000.0) isk = Math.round10(isk+5000, 4);
    else if (isk < 1000000000.0) isk = Math.round10(isk+50000, 5);
    else if (isk < 10000000000.0) isk = Math.round10(isk+500000, 6);
    else if (isk < 100000000000.0) isk = Math.round10(isk+5000000, 7);
    else isk = null;
    return isk;
  }

  function rebuildMarket(show_group) {
    $('#tblMarket').find('tbody').find('tr').each(function() {
      var tr = $(this);
      var show = false;
      if (show_group == 'all')
        show = true;
      else if (show_group == 'sold')
        show = tr.find('td').eq(1).find('span.label-noordersreal').length ||
               tr.find('td').eq(1).find('span.label-noorders').length;
      else if (show_group == 'low-price')
        show = tr.find('td').eq(1).find('span.label-lowprice').length;
      else if (show_group == 'high-price')
        show = tr.find('td').eq(1).find('span.label-highprice').length;
      else if (show_group == 'very-few')
        show = tr.find('td').eq(1).find('span.label-veryfew').length;
      else if (show_group == 'need-delivery')
        show = tr.find('td').eq(1).find('span.label-needdelivery').length;
      else if (show_group == 'place-an-order')
        show = tr.find('td').eq(1).find('span.label-placeanorder').length;
      else if (show_group == 'interrupt')
        show = tr.find('td').eq(1).find('span.label-interrupt').length;
      if (show)
        tr.removeClass('hidden');
      else if (tr.find('td').eq(0).hasClass('active'))
        tr.removeClass('hidden');
      else
        tr.addClass('hidden');
    });
  }
  function rebuildStock(show_group) {
    $('#tblStock').find('tbody').find('tr').each(function() {
      var tr = $(this);
      var show = false;
      if (show_group == 'all')
        show = true;
      else if (show_group == 'hide')
        show = false;
      if (show)
        tr.removeClass('hidden');
      else
        tr.addClass('hidden');
    });
  }
  function recalcDetails(btn) {
    var take_import = 1 * $('#dtlsSellVar_import_check').is(':checked');
    var import_price = take_import * g_jita_import_price * $('#dtlsCalc').attr('packed_volume');
    var price_purchase = 1.0 * btn.attr('price');
    var price_profit = price_purchase * (1.0+1.0*btn.attr('profit'));
    var price_profit_import = price_profit + import_price;
    var price_profit_import_markup = price_profit_import * <?=TAX_AND_FEE?>;
    var price_profit_import_tax = price_profit_import + price_profit_import_markup;
    var price_order = eveCeiling(price_profit_import_tax);
    var profit_order = price_order - price_profit_import_markup - price_purchase - import_price;
    $('#dtlsSellVar_name').html(btn.attr('caption'));
    $('#dtlsSellVar_purchase').html(numLikeEve(price_purchase.toFixed(2)));
    $('#dtlsSellVar_price').html(numLikeEve(price_profit.toFixed(2)));
    $('#dtlsSellVar_import').html(numLikeEve(price_profit_import.toFixed(2)));
    $('#dtlsSellVar_tax').html(numLikeEve(price_profit_import_tax.toFixed(2)));
    $('#dtlsSellVar_order').html(numLikeEve(price_order.toFixed(2)));
    $('#dtlsSellVar_profit').html(numLikeEve(profit_order.toFixed(2)));
    $('#dtlsSellVar_order_copy').attr('data-copy', numLikeEve(price_order.toFixed(2)));
    if (take_import)
      $('#dtlsSellVar_import').parent().removeClass('hidden');
    else
      $('#dtlsSellVar_import').parent().addClass('hidden');
  }
  $(document).ready(function(){
    $('label.qind-btn-market').on('click', function () {
      if (!$(this).hasClass('active')) // включается
        rebuildMarket($(this).attr('group'));
    });
    $('label.qind-btn-stock').on('click', function () {
      if (!$(this).hasClass('active')) // включается
        rebuildStock($(this).attr('group'));
    });
    $('button.qind-btn-details').on('click', function () {
      var tid = $(this).attr('type_id');
      var cnt = g_market_types.length, i = 0;
      var market_type = null;
      for (;i<cnt;++i) {
        if (tid != g_market_types[i][0]) continue;
        market_type = g_market_types[i];
        break;
      }
      if (market_type === null) return;
      var modal = $("#modalDetails");
      $('#modalDetailsLabel').html('<span class="text-primary">Подробности о товаре</span> '+market_type[1]);
      $('#dtlsPackedVolume').html(numLikeEve(market_type[2]));
      $('#dtlsImportPrice').html(numLikeEve(Math.ceil10(market_type[2]*g_jita_import_price, -2).toFixed(2)));
      if (market_type[3]) {
        $('#dtlsJitaSell')
         .html(numLikeEve(market_type[3].toFixed(2)))
         .parent().removeClass('hidden');
      } else {
        $('#dtlsJitaSell')
         .html(numLikeEve(market_type[3].toFixed(2)))
         .parent().addClass('hidden');
      }
      if (market_type[4]) {
        $('#dtlsJitaBuy')
         .html(numLikeEve(market_type[4].toFixed(2)))
         .parent().removeClass('hidden');
      } else {
        $('#dtlsJitaBuy')
         .html(numLikeEve(market_type[4].toFixed(2)))
         .parent().addClass('hidden');
      }
      if (market_type[5]) {
        $('#dtlsAmarrSell')
         .html(numLikeEve(market_type[5].toFixed(2)))
         .parent().removeClass('hidden');
      } else {
        $('#dtlsAmarrSell')
         .html(numLikeEve(market_type[5].toFixed(2)))
         .parent().addClass('hidden');
      }
      $('#dtlsUniversePrice').html(numLikeEve(market_type[6].toFixed(2)));
      var span_last_ri4_buy = $('#dtlsLastBuyPrice');
      $('#dtlsCalcUP10').attr('price', '');
      //- формирование таблицы
      $('#tblPurchase tbody tr').remove();
      var tbdy = $('#tblPurchase').find('tbody');
      var cnt = g_purchase_types.length, i = 0;
      for (;i<cnt;++i) {
        if (g_purchase_types[i][0] < tid) continue;
        if (g_purchase_types[i][0] > tid) break;
        var avg_buy_price = numLikeEve(g_purchase_types[i][2].toFixed(2));
        tbdy.append($('<tr>')
         .append($('<td>')
          .text(g_purchase_types[i][1])
         )
         .append($('<td>')
          .attr('align','right')
          .text(g_purchase_types[i][3])
         )
         .append($('<td>')
          .attr('align','right')
          .text(avg_buy_price)
         )
        )
        if (span_last_ri4_buy) {
          span_last_ri4_buy.html(avg_buy_price);
          $('#dtlsCalcUP10').attr('price', g_purchase_types[i][2]);
          span_last_ri4_buy = null;
        }
      }
      //- автоматические расчёты +10% jita sell,...
      $('#dtlsCalc').attr('packed_volume', market_type[2]);
      $('#dtlsCalcJS10')
       .attr('price', market_type[3]);
      $('#dtlsCalcJS5')
       .attr('price', market_type[3])
       .removeClass('active');
      $('#dtlsCalcJS15')
       .attr('price', market_type[3])
       .removeClass('active');
      $('#dtlsCalcAS10')
       .attr('price', market_type[5])
       .removeClass('active');
      if (1 * $('#dtlsCalcUP10').attr('price')) {
        $('#dtlsCalcJS10')
         .removeClass('active');
        $('#dtlsCalcUP10')
         .removeClass('hidden')
         .addClass('active');
        recalcDetails($('#dtlsCalcUP10'));
      } else {
        $('#dtlsCalcJS10')
         .addClass('active');
        $('#dtlsCalcUP10')
         .addClass('hidden')
         .removeClass('active');
        recalcDetails($('#dtlsCalcJS10'));
      }
      modal.modal('show');
    });
    $('label.qind-btn-calc').on('click', function () {
      var btn = $(this);
      if (!btn.hasClass('active')) { // включается
        recalcDetails(btn);
      }
    });
    $('#dtlsSellVar_import_check').on('click', function () {
      $('label.qind-btn-calc.active').each(function() {
        recalcDetails($(this));
      });
    });
    // Initialization
    rebuildStock('hide');
  });
</script>
<?php __dump_copy_to_clipboard_javascript() ?>
