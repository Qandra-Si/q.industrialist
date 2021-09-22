<?php
include 'qi_render_html.php';
include_once '.settings.php';


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


function get_clipboard_copy_button($data_copy) {
    return ' <a data-target="#" role="button" data-copy="'.$data_copy.'" class="qind-copy-btn" data-toggle="tooltip" data-original-title="" title=""><span class="glyphicon glyphicon-copy" aria-hidden="true"></a>';
}


function __dump_querious_market($market, $storage) { ?>
<h2>Keepstar Market</h2>
<style>
.label-noordersreal { color: #fff; background-color: #d9534f; }
.label-noorders { color: #fff; background-color: #eebbb9; }
.label-interrupt { color: #8e8e8e; background-color: #e8ce43; }
.label-dontbuy { color: #e8ce43; background-color: #337ab7; }
.label-needdelivery { color: #fff; background-color: #5bc0de; }
.label-placeanorder { color: #fff; background-color: #d973e8; }
.label-lowprice { color: #fff; background-color: #f0ad4e; }
.label-highprice { color: #fff; background-color: #777; }
.label-veryfew { color: #fff; background-color: #337ab7; }
</style>
<table class="table table-condensed" style="padding:1px;font-size:smaller;" id="tblMarket">
<thead>
 <tr>
  <th></th>
  <th>Items</th>
  <th style="text-align: right;">Weekly<br><mark>Order</mark></th>
  <th style="text-align: right;">RI4 Price<br>Quantity</th>
  <th style="text-align: right;">Jita Buy..Sell<br><mark>Import Price</mark></th>
  <th style="text-align: right;">Amarr<br>Sell</th>
  <th style="text-align: right;">Universe<br>Price</th>
  <th style="text-align: right;">Jita +10%<br>Price / Markup</th>
  <th style="text-align: right;">+10%<br>Profit</th>
  <th style="text-align: right;">P-ZMZV Sell<br><mark>Volume</mark></th>
 </tr>
</thead>
<tbody>
<?php
    $min_profit = 0.05; // 3%
    $profit = 0.1; // 10%
    $max_profit = 0.25; // 25%
    $taxfee = 0.03 + 0.0113;

    $summary_market_price = 0;
    $summary_market_volume = 0;
    $summary_jita_sell = 0;
    $summary_jita_buy = 0;
    $amarr_buy_order = '';
    $jita_buy_order = '';
    $amarr_buy_price = 0.0;
    $jita_buy_price = 0.0;
    if ($market)
        foreach ($market as $product)
        {
            $problems = '';
            $warnings = '';
            $interrupt_detected = false;

            $tid = $product['id'];
            $nm = $product['name'];
            $weekly_volume = $product['wv'];
            $order_volume = $product['ov'];
            $day_volume = $product['dv'];
            $market_quantity = $product['mv'];
            $packaged_volume = $product['pv'];
            $jita_import_price = $packaged_volume * 866.0;
            $jita_sell = $product['js'];
            $jita_buy = $product['jb'];
            $amarr_sell = $product['as'];
            $universe_price = $product['up'];
            $market_price = $product['mp'];
            $markup = $jita_sell * 0.0313;
            $jita_10_price = eve_ceiling($jita_sell * (1.0+$profit+$taxfee)); // Jita +10% Price
            $jita_10_profit = $jita_10_price - $jita_sell - $markup;
            $pzmzv_sell = $product['ps'];
            $pzmzv_sell_volume = $product['psv'];

            $storage_quantity = 0;
            if ($storage)
                foreach ($storage as $stock)
                {
                    $sid = $stock['id'];
                    if ($sid != $tid) continue;
                    $storage_quantity = $stock['q'];
                    break;
                }

            if (is_null($market_price)) {
                if (is_null($pzmzv_sell_volume) || !$pzmzv_sell_volume)
                    $problems .= '<span class="label label-noordersreal">no orders</span>&nbsp;';
                else
                    $problems .= '<span class="label label-noorders">no orders</span>&nbsp;';
            }
            if (!is_null($market_quantity)) {
                if ($weekly_volume >= ($market_quantity+$storage_quantity))
                    $problems .= '<span class="label label-needdelivery">need delivery</span>&nbsp;';
                if ($storage_quantity && ($weekly_volume >= $market_quantity))
                    $warnings .= '<span class="label label-placeanorder">place an order</span>&nbsp;';
            }
            if (!is_null($market_quantity) && ($order_volume >= $market_quantity)) $problems .= '<span class="label label-veryfew">very few</span>&nbsp;';
            if (!is_null($market_price)) {
                if ($market_price > 100000 || $packaged_volume < 5) {
                    $min_jita_price = $jita_sell * (1.0+$min_profit+$taxfee);
                    $min_amarr_price = $amarr_sell * (1.0+$min_profit+$taxfee);
                    if (($market_price < $min_jita_price) && ($market_price < $min_amarr_price))
                        $warnings .= '<span class="label label-lowprice" data-toggle="tooltip" data-placement="bottom" title="Min Amarr: '.number_format(eve_ceiling($min_amarr_price),2,'.',',').', min Jita: '.number_format(eve_ceiling($min_jita_price),2,'.',',').'">low price</span>&nbsp;';
                }
                $max_jita_price = $jita_sell * (1.0+$max_profit+$taxfee);
                $max_amarr_price = $amarr_sell * (1.0+$max_profit+$taxfee);
                if (($market_price > $max_jita_price) && ($market_price > $max_amarr_price))
                    $warnings .= '<span class="label label-highprice" data-toggle="tooltip" data-placement="bottom" title="Max Amarr: '.number_format(eve_ceiling($max_amarr_price),2,'.',',').', max Jita: '.number_format(eve_ceiling($max_jita_price),2,'.',',').'">price too high</span>&nbsp;';
                if (!is_null($pzmzv_sell) && ($pzmzv_sell < $market_price) && ($pzmzv_sell_volume > $market_quantity)) {
                    $interrupt_detected = true;
                    $warnings .= '<span class="label label-interrupt">interrupt</span>&nbsp;';
                    // рассчитываем минимальную цену, ниже которой закупку производить не следует - позиция перебита конкурентами
                    $min_buy_price = $pzmzv_sell / (1.0+$taxfee+$min_profit);
                    if (($jita_sell > $min_buy_price) && ($amarr_sell > $min_buy_price))
                        $warnings .= '<span class="label label-dontbuy" data-toggle="tooltip" data-placement="bottom" title="Min buy price: '.number_format(eve_ceiling($min_buy_price),2,'.',',').'">don&apos;t buy</span>&nbsp;';
                    else if ($amarr_sell > $min_buy_price)
                        $warnings .= '<span class="label label-dontbuy" data-toggle="tooltip" data-placement="bottom" title="Min buy price: '.number_format(eve_ceiling($min_buy_price),2,'.',',').'">don&apos;t buy in Amarr</span>&nbsp;';
                    else if ($jita_sell > $min_buy_price)
                        $warnings .= '<span class="label label-dontbuy" data-toggle="tooltip" data-placement="bottom" title="Min buy price: '.number_format(eve_ceiling($min_buy_price),2,'.',',').'">don&apos;t buy in Jita</span>&nbsp;';
                }
            }

            if (!is_null($market_quantity)&&!is_null($market_price)) $summary_market_price += $market_quantity * $market_price;
            if (!is_null($packaged_volume)) $summary_market_volume += $market_quantity * $packaged_volume;
            $summary_jita_sell += $market_quantity * $jita_sell;
            $summary_jita_buy += $market_quantity * $jita_buy;

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
?>
<tr>
 <td><img class="icn32" src="<?=__get_img_src($tid,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
 <td><?=$nm?><?=get_clipboard_copy_button($nm)?><?=(!is_null($day_volume)&&$day_volume)?' <span style="background-color:#00fa9a">&nbsp;+ '.number_format($day_volume,0,'.',',').'&nbsp;</span>':''?><?='<br><span class="text-muted">'.$tid.'</span> '.$problems.$warnings?></td>
 <?php if (is_null($weekly_volume)) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($weekly_volume,1,'.',',')?><br><mark><span style="font-size: smaller;"><?=number_format($order_volume,1,'.',',')?></span></mark></td>
 <?php } ?>
 <?php if (is_null($market_price)) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($market_price,2,'.',',')?><br><mark><?=number_format($market_quantity,0,'.',',')?></mark><?=$storage_quantity?'&nbsp;<small><span style="background-color:#c7c7c7">&nbsp;+ '.number_format($storage_quantity,0,'.',',').'&nbsp;</span></small>':''?></td>
 <?php } ?>
 <td align="right"><small><span class="text-muted"><?=number_format($jita_buy,2,'.',',')?> ..</span></small> <?=number_format($jita_sell,2,'.',',')?><br><mark><?=number_format($jita_import_price,2,'.',',')?></mark></td>
 <td align="right"><?=number_format($amarr_sell,2,'.',',')?></td>
 <td align="right"><?=number_format($universe_price,2,'.',',')?></td>
 <?php if (is_null($jita_10_price)) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($jita_10_price,2,'.',',')?><br><mark><?=number_format($markup,2,'.',',')?></mark></td>
 <?php } ?>
 <?php if (is_null($jita_10_profit)) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($jita_10_profit,2,'.',',')?></td>
 <?php } ?>
 <?php if (is_null($pzmzv_sell)) { ?><td></td><?php } else { ?>
  <?php if ($interrupt_detected) { ?>
  <td align="right" bgcolor="#e8c8c8"><?=number_format($pzmzv_sell,2,'.',',')?><br><mark><?=number_format($pzmzv_sell_volume,0,'.',',')?></mark></td>
  <?php } else { ?>
  <td align="right"><?=number_format($pzmzv_sell,2,'.',',')?><br><mark><?=number_format($pzmzv_sell_volume,0,'.',',')?></mark></td>
  <?php } ?>
 <?php } ?>
</tr>
<?php
    }
?>
<tr style="font-weight:bold;">
 <td colspan="3" align="right">Summary</td>
 <td align="right"><?=number_format($summary_market_price,0,'.',',').'<br>'.number_format($summary_market_volume,0,'.',',')?>m³</td>
 <td align="right"><?=number_format($summary_jita_sell,0,'.',',').'<br>'.number_format($summary_jita_buy,0,'.',',')?></td>
 <td colspan="5"></td>
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


function __dump_querious_storage($storage) { ?>
<h2>Keepstar Storage</h2>
<table class="table table-condensed" style="padding:1px;font-size:smaller;" id="tblStock">
<thead>
 <tr>
  <th></th>
  <th>Items</th>
  <th style="text-align: right;">Volume<br>Hangar 4</th>
  <th style="text-align: right;">RI4<br>Sell</th>
  <th style="text-align: right;">P-ZMZV Sell<br><mark>Volume</mark></th>
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
        foreach ($storage as $product)
        {
            $tid = $product['id'];
            $nm = $product['name'];
            $quantity = $product['q'];
            $ri4_sell = $product['rs'];
            $ri4_sell_volume = $product['rsv'];
            $pzmzv_sell = $product['ps'];
            $pzmzv_sell_volume = $product['psv'];
            $packaged_volume = $product['pv'];
            $jita_import_price = $packaged_volume * 866.0;
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
  tid.sdet_type_name as name,
  case
    when (weeks_passed.volume_sell=0) or (weeks_passed.diff<0.14) then null
    when (weeks_passed.diff < 1.14) then weeks_passed.volume_sell
    else round(weeks_passed.volume_sell/weeks_passed.diff,1)
  end as wv, -- weekly volume
  round(transactions_stat.avg_volume, 1) as ov, -- order volume
  transactions_stat.sum_last_day as dv, -- day volume
  orders_stat.volume_remain as mv, -- RI4 volume
  tid.sdet_volume as pv, -- packaged volume
  jita.sell as js, -- jita sell
  jita.buy as jb, -- jita buy
  amarr.sell as as, -- amarr sell
  case
    when universe.emp_average_price is null or (universe.emp_average_price < 0.001) then universe.emp_adjusted_price
    else universe.emp_average_price
  end as up, -- universe price
  round(orders_stat.ri4_price::numeric, 2) as mp, -- RI4 price
  -- round(jita.sell::numeric*0.0313, 2) as markup,
  -- case
  --   when jita.sell::numeric*1.1313 < 100.0 then round(ceil(jita.sell::numeric*113.13)/100.0, 2)
  --   when jita.sell::numeric*1.1313 < 1000.0 then round(ceil(jita.sell::numeric*11.313)/10.0, 2)
  --   when jita.sell::numeric*1.1313 < 10000.0 then ceil(jita.sell::numeric*1.1313)
  --   when jita.sell::numeric*1.1313 < 100000.0 then round(jita.sell::numeric*1.1313+5, -1)
  --   when jita.sell::numeric*1.1313 < 1000000.0 then round(jita.sell::numeric*1.1313+50, -2)
  --   when jita.sell::numeric*1.1313 < 10000000.0 then round(jita.sell::numeric*1.1313+500, -3)
  --   when jita.sell::numeric*1.1313 < 100000000.0 then round(jita.sell::numeric*1.1313+5000, -4)
  --   when jita.sell::numeric*1.1313 < 1000000000.0 then round(jita.sell::numeric*1.1313+50000, -5)
  --   when jita.sell::numeric*1.1313 < 10000000000.0 then round(jita.sell::numeric*1.1313+500000, -6)
  --   else null
  -- end as j10p, -- jita +10% price
  -- round(jita.sell::numeric*0.1, 2) as "+10% profit",
  sbsq_hub.ethp_sell as ps, -- p-zmzv sell
  sbsq_hub.ethp_sell_volume as psv -- p-zmzv sell volume
from
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
            ecwj_second_party_id in (2116129465,2116746261,2116156168) and -- Qandra Si, Kekuit Void, Qunibbra Do
            ( ecwt_location_id in (1036927076065,1034323745897) and not ecwt_is_buy or
              ecwt_location_id not in (1036927076065,1034323745897) and ecwt_is_buy) and -- станка рынка
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
    -- сведения об sell-ордерах, активных прямо сейчас
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
  not (tid.sdet_market_group_id = 1857) and -- исключая руду
  tid.sdet_type_id not in (17715,2998) -- случайно выставил от корпы
order by 7 desc;
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
  tid.sdet_volume as pv, -- packaged volume
  jita.sell as js, -- jita sell : to_char(jita.sell, 'FM999G999G999G999G999.90')
  jita.buy as jb, -- jita buy : to_char(jita.buy, 'FM999G999G999G999G999.90')
  amarr.sell as as, -- amarr sell : to_char(amarr.sell, 'FM999G999G999G999G999.90')
  universe.price as up, -- universe price : to_char(universe.price, 'FM999G999G999G999G999.90')
  -- case
  --  when (ceil(abs(universe.price - jita.sell)) - ceil(abs(universe.price - amarr.sell))) < 0 then 'jita'
  --  else 'amarr'
  -- end as "proper hub",
  round(tid.sdet_volume::numeric * 866.0, 2) as "jita import price", -- заменить на packaged_volume, считать по ESI
  hangar.eca_created_at::date as since,
  date_trunc('minutes', CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - hangar.eca_updated_at)::interval as last_changed
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
<?php __dump_querious_market($market, $storage); ?>
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

<script>
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
  $(document).ready(function(){
    $('label.qind-btn-market').on('click', function () {
      if (!$(this).hasClass('active')) // включается
        rebuildMarket($(this).attr('group'));
    });
    $('label.qind-btn-stock').on('click', function () {
      if (!$(this).hasClass('active')) // включается
        rebuildStock($(this).attr('group'));
    });
    // Initialization
    rebuildStock('hide');
    // Working with clipboard
    $('a.qind-copy-btn').each(function() {
      $(this).tooltip();
    })
    $('a.qind-copy-btn').bind('click', function () {
      var data_copy = $(this).attr('data-copy');
      if (data_copy === undefined) {
        var data_source = $(this).attr('data-source');
        if (data_source == 'table') {
          var tr = $(this).parent().parent();
          var tbody = tr.parent();
          var rows = tbody.children('tr');
          var start_row = rows.index(tr);
          data_copy = '';
          rows.each( function(idx) {
            if (!(start_row === undefined) && (idx > start_row)) {
              var td0 = $(this).find('td').eq(0); // ищём <td#0 class='active'>
              if (!(td0.attr('class') === undefined))
                start_row = undefined;
              else {
                //ищём <tr>...<td#1><a data-copy='?'>...
                var td1a = $(this).find('td').eq(1).find('a');
                if (!(td1a === undefined)) {
                  var nm = td1a.attr('data-copy');
                  if (!(nm === undefined)) {
                    var td2q = $(this).find('td').eq(2).attr('quantity');
                    if (!(td2q === undefined) && (td2q > 0)) {
                      if (data_copy) data_copy += "\n"; 
                      data_copy += nm + "\t" + td2q;
                    }
                  }
                }
              }
            }
          });
        } else if (data_source == 'span') {
          var div = $(this).parent();
          var spans = div.children('span');
          data_copy = '';
          spans.each( function(idx) {
            var span = $(this);
            if (data_copy) data_copy += "\n";
            var txt = span.text();
            data_copy += txt.substring(txt.indexOf(' x ')+3) + "\t" + span.attr('quantity');
          });
        }
      }
      if (data_copy) {
        if (window.isSecureContext && navigator.clipboard) {
          navigator.clipboard.writeText(data_copy).then(() => {
            $(this).trigger('copied', ['Copied!']);
          }, (e) => {
            $(this).trigger('copied', ['Data not copied!']);
          });
          document.execCommand("copy");
        }
        else {
          var $temp = $("<textarea>");
          $("body").append($temp);
          $temp.val(data_copy).select();
          try {
            success = document.execCommand("copy");
            if (success)
              $(this).trigger('copied', ['Copied!']);
            else
              $(this).trigger('copied', ['Data not copied!']);
          } finally {
            $temp.remove();
          }
        }
      }
      else {
        $(this).trigger('copied', ['Nothing no copy!']);
      }
    });
    $('a.qind-copy-btn').bind('copied', function(event, message) {
      $(this).attr('title', message)
        .tooltip('fixTitle')
        .tooltip('show')
        .attr('title', "Copy to clipboard")
        .tooltip('fixTitle');
    });
    if( /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ) {
      // какой-то код ...
      $('a.qind-copy-btn').each(function() {
        $(this).addClass('hidden');
      })
    }
  });
</script>

