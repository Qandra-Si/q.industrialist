<?php
include 'qi_render_html.php';
include_once '.settings.php';
?>

<?php
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
?>

<?php function __dump_querious_market($market) { ?>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th></th>
  <th>Items</th>
  <th style="text-align: right;">Weekly<br><mark>Order</mark></th>
  <th style="text-align: right;">Volume<br>3-FKCZ</th>
  <th style="text-align: right;">3-FKCZ<br>Price</th>
  <th style="text-align: right;">Jita Sell<br><mark>Import Price</mark></th>
  <th style="text-align: right;">Amarr<br>Sell</th>
  <th style="text-align: right;">Universe<br>Price</th>
  <th style="text-align: right;">Jita +10%<br>Price / Markup</th>
  <th style="text-align: right;">+10%<br>Profit</th>
  <th style="text-align: right;">Their<br>Price</th>
 </tr>
</thead>
<tbody>
<?php
    $min_profit = 0.05; // 3%
    $profit = 0.1; // 10%
    $max_profit = 0.20; // 20%
    $taxfee = 0.02 + 0.0113;

    $summary_market_price = 0;
    $summary_market_volume = 0;
    $amarr_buy_order = '';
    $jita_buy_order = '';
    $amarr_buy_price = 0.0;
    $jita_buy_price = 0.0;
    foreach ($market as $product)
    {
        $problems = '';
        $warnings = '';

        $tid = $product['id'];
        $nm = $product['name'];
        $weekly_volume = $product['wv'];
        $order_volume = $product['ov'];
        $market_volume = $product['mv'];
        $packaged_volume = $product['pv'];
        $jita_import_price = $packaged_volume * 866.0;
        $jita_sell = $product['js'];
        $amarr_sell = $product['as'];
        $universe_price = $product['up'];
        $market_price = $product['mp'];
        $markup = $jita_sell * 0.0313;
        $jita_10_price = eve_ceiling($jita_sell * (1.0+$profit+$taxfee)); // Jita +10% Price
        $jita_10_profit = $jita_10_price - $jita_sell - $markup;
        $their_price = $product['tp'];

        if (is_null($market_price)) $problems .= '<span class="label label-danger">no orders</span>&nbsp;';
        if (is_null($market_volume) || ($weekly_volume >= $market_volume)) $problems .= '<span class="label label-info">need delivery</span>&nbsp;';
        if (!is_null($market_volume) && ($order_volume >= $market_volume)) $problems .= '<span class="label label-primary">very few</span>&nbsp;';
        if (!is_null($market_price)) {
            $min_jita_price = $jita_sell * (1.0+$min_profit+$taxfee);
            $min_amarr_price = $amarr_sell * (1.0+$min_profit+$taxfee);
            if (($market_price < $min_jita_price) && ($market_price < $min_amarr_price))
                $warnings .= '<span class="label label-warning" data-toggle="tooltip" data-placement="bottom" title="Min Amarr: '.number_format(eve_ceiling($min_amarr_price),2,'.',',').', min Jita: '.number_format(eve_ceiling($min_jita_price),2,'.',',').'">low price</span>&nbsp;';
            $max_jita_price = $jita_sell * (1.0+$max_profit+$taxfee);
            $max_amarr_price = $amarr_sell * (1.0+$max_profit+$taxfee);
            if (($market_price > $max_jita_price) && ($market_price > $max_amarr_price))
                $warnings .= '<span class="label label-default" data-toggle="tooltip" data-placement="bottom" title="Max Amarr: '.number_format(eve_ceiling($max_amarr_price),2,'.',',').', max Jita: '.number_format(eve_ceiling($max_jita_price),2,'.',',').'">price too high</span>&nbsp;';
        }

        if (!is_null($market_volume)&&!is_null($market_price)) $summary_market_price += $market_volume * $market_price;
        if (!is_null($packaged_volume)) $summary_market_volume += $market_volume * $packaged_volume;

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
 <td><?=$nm.'<br><span class="text-muted">'.$tid.'</span> '.$problems.$warnings?></td>
 <?php if (is_null($weekly_volume)) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($weekly_volume,1,'.',',')?><br><mark><span style="font-size: smaller;"><?=number_format($order_volume,1,'.',',')?></span></mark></td>
 <?php } ?>
 <td align="right"><?=number_format($market_volume,0,'.',',')?></td>
 <?php if (is_null($market_price)) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($market_price,2,'.',',')?></td>
 <?php } ?>
 <td align="right"><?=number_format($jita_sell,2,'.',',')?><br><mark><?=number_format($jita_import_price,2,'.',',')?></mark></td>
 <td align="right"><?=number_format($amarr_sell,2,'.',',')?></td>
 <td align="right"><?=number_format($universe_price,2,'.',',')?></td>
 <?php if (is_null($jita_10_price)) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($jita_10_price,2,'.',',')?><br><mark><?=number_format($markup,2,'.',',')?></mark></td>
 <?php } ?>
 <?php if (is_null($jita_10_profit)) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($jita_10_profit,2,'.',',')?></td>
 <?php } ?>
 <td align="right"><?=!is_null($their_price)?number_format($their_price,2,'.',','):''?></td>
</tr>
<?php
    }
?>
<tr style="font-weight:bold;">
 <td colspan="3" align="right">Summary</td>
 <td align="right"><?=number_format($summary_market_volume,0,'.',',')?></td>
 <td colspan="5" align="right"><?=number_format($summary_market_price,0,'.',',')?></td>
 <td colspan="3"></td>
</tr>
</tbody>
</table>

<div class="row">
 <div class="col-md-6">
  <h3>Amarr Buy Order</h3>
   <?php if (!is_null($amarr_buy_order)) { ?>
    <pre class="pre-scrollable" style="border: 0; background-color: transparent; font-size: 11px;"><?=$amarr_buy_order?></pre>
    <b>Amarr sell price: <?=number_format($amarr_buy_price,2,'.',',')?></b>
   <?php } ?>
 </div>
 <div class="col-md-6">
  <h3>Jita Buy Order</h3>
   <?php if (!is_null($jita_buy_order)) { ?>
    <pre class="pre-scrollable" style="border: 0; background-color: transparent; font-size: 11px;"><?=$jita_buy_order?></pre>
    <b>Jita sell price: <?=number_format($jita_buy_price,2,'.',',')?></b>
   <?php } ?>
 </div>
</div>

<?php
} ?>


<?php
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
    else round(weeks_passed.volume_sell/weeks_passed.diff,1)
  end as wv, -- weekly volume
  round(transactions_stat.avg_volume, 1) as ov, -- order volume
  orders_stat.volume_remain as mv, -- 3-fkcz volume
  tid.sdet_volume as pv, -- packaged volume
  jita.sell as js, -- jita sell
  amarr.sell as as, -- amarr sell
  case
    when universe.emp_average_price is null or (universe.emp_average_price < 0.001) then universe.emp_adjusted_price
    else universe.emp_average_price
  end as up, -- universe price
  round(orders_stat.price_remain::numeric / orders_stat.volume_remain::numeric, 2) as mp, -- 3-fkcz price
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
  null as tp -- their price
from 
  ( select distinct type_id
    from (
      -- список транзакций по покупке/продаже избранными персонажами от имени 2х корпораций
      select ecwt_type_id as type_id --, 'j'::char as type
      from
        esi_corporation_wallet_journals j
          left outer join esi_corporation_wallet_transactions t on (ecwj_context_id = ecwt_transaction_id) -- (j.ecwj_reference_id = t.ecwt_journal_ref_id)
      where
        not ecwt_is_buy and
        (ecwj_date > '2021-08-15') and
        (ecwj_context_id_type = 'market_transaction_id') and
        ( ( ecwj_corporation_id in (98615601) and -- R Initiative 4
            ecwj_second_party_id in (2116129465,2116746261,2116156168) and -- Qandra Si, Kekuit Void, Qunibbra Do
            ecwj_division = 1) or
          ( ecwj_corporation_id in (98553333) and -- R Strike
            ecwj_second_party_id in (95858524) and -- Xatul' Madan
            ecwj_division = 7)
        )
      union
      -- список того, что корпорация продавала или продаёт
      select ecor_type_id --, 'o'::char
      from esi_corporation_orders
      where
        not ecor_is_buy_order and
        (ecor_corporation_id=98615601) and  -- R Initiative 4
        (ecor_location_id=1036927076065) -- станка рынка
      ) jto
  ) market
    -- сведения о предмете
    left outer join eve_sde_type_ids tid on (market.type_id = tid.sdet_type_id)
    -- цены в жите прямо сейчас
    left outer join (
      select ethp_type_id, ethp_sell as sell
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
        (ecor_location_id=1036927076065)  -- станка рынка
      group by ecor_type_id
    ) weeks_passed on (market.type_id = weeks_passed.ecor_type_id)
    -- усреднённый (типовой) объём sell-ордера по продаже
    left outer join (
      select
        ecwt_type_id,
        avg(ecwt_quantity) as avg_volume
      from esi_corporation_wallet_transactions
      where
        not ecwt_is_buy and
        (ecwt_corporation_id=98615601) and  -- R Initiative 4
        (ecwt_location_id=1036927076065) -- станка рынка
      group by 1
    ) transactions_stat on (market.type_id = transactions_stat.ecwt_type_id)
    -- сведения об sell-ордерах, активных прямо сейчас
    left outer join (
      select
        ecor_type_id,
        sum(ecor_volume_remain) as volume_remain,
        sum(ecor_price*ecor_volume_remain) as price_remain
      from esi_corporation_orders
      where
        not ecor_is_buy_order and
        (ecor_volume_remain > 0) and
        not ecor_history and
        (ecor_corporation_id=98615601) and  -- R Initiative 4
        (ecor_location_id=1036927076065)  -- станка рынка
      group by 1
    ) orders_stat on (market.type_id = orders_stat.ecor_type_id)
where
  not (tid.sdet_market_group_id = 1857) and -- исключая руду
  tid.sdet_type_id not in (17715,2998) -- случайно выставил от корпы
order by 7;
EOD;
    $jobs_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $jobs = pg_fetch_all($jobs_cursor);
    //---
    pg_close($conn);
?>
<div class="container-fluid">
<?php __dump_querious_market($jobs); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>