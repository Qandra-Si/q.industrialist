<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include_once '.settings.php';

const SORT_PRFT_ASC = 1;
const SORT_PRFT_DESC = -1;
const SORT_PERC_ASC = 2;
const SORT_PERC_DESC = -2;
const SHOW_ONLY_RI4_SALES_DEFAULT = 1;
const DO_NOT_SHOW_RAW_MATERIALS_DEFAULT = 1;
const SHOW_JITA_PRICE_INCLUDE_OURS_DEFAULT = 1;
const RHEA_CARGO_M3 = 410417.9;

$SORT = SORT_PRFT_ASC;
$SHOW_ONLY_RI4_SALES = SHOW_ONLY_RI4_SALES_DEFAULT;
$DO_NOT_SHOW_RAW_MATERIALS = DO_NOT_SHOW_RAW_MATERIALS_DEFAULT;
$SHOW_JITA_PRICE_INCLUDE_OURS = SHOW_JITA_PRICE_INCLUDE_OURS_DEFAULT;
$GRPs = null;


if (!isset($_GET['s'])) $SORT = SORT_PRFT_ASC; else {
  $_get_sort = htmlentities($_GET['s']);
  if (is_numeric($_get_sort)) $SORT = get_numeric($_get_sort);
  else $SORT = SORT_PRFT_ASC;
}
if (isset($_GET['only_ri4_sales'])) {
    $_get_only_ri4_sales = htmlentities($_GET['only_ri4_sales']);
    if (is_numeric($_get_only_ri4_sales)) $SHOW_ONLY_RI4_SALES = get_numeric($_get_only_ri4_sales) ? 1 : 0;
    else $SHOW_ONLY_RI4_SALES = SHOW_ONLY_RI4_SALES_DEFAULT;
}
if (isset($_GET['raw_materials'])) {
    $_get_raw_materials = htmlentities($_GET['raw_materials']);
    if (is_numeric($_get_raw_materials)) $DO_NOT_SHOW_RAW_MATERIALS = get_numeric($_get_raw_materials) ? 0 : 1; // инверсия
    else $DO_NOT_SHOW_RAW_MATERIALS = DO_NOT_SHOW_RAW_MATERIALS_DEFAULT;
}
if (isset($_GET['jpio'])) {
    $_get_jpio = htmlentities($_GET['jpio']);
    if (is_numeric($_get_jpio)) $SHOW_JITA_PRICE_INCLUDE_OURS = get_numeric($_get_jpio) ? 1 : 0;
    else $SHOW_JITA_PRICE_INCLUDE_OURS = SHOW_JITA_PRICE_INCLUDE_OURS_DEFAULT;
}
if (!isset($_GET['grp'])) $GRPs = null; else {
  $_get_grp = htmlentities($_GET['grp']);
  if (is_numeric($_get_grp)) $GRPs = array(get_numeric($_get_grp));
  else if (is_numeric_array($_get_grp)) $GRPs = get_numeric_array($_get_grp);
  else return;
}


function eve_ceiling($isk)
{
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

class market_hub_margin
{
    public float $price; // стоимость ордера с наценками, комиссиями, перевозками и т.п.
    public float $price_wo_profit; // стоимость без наценки (но с налогами и комиссией)
    public float $price_wo_fee_tax; // стоимость без налогов и комиссий (но с перевозкой)
    public float $price_wo_logistic; // стоимость без перевозки

    // вычислить относительно цены в маркете (комиссии, доставка и налоги вычитаются)
    public function calculate_down(&$hub, float $price, float $packaged_volume, float $isotopes_price)
    {
        $brokers_fee = $hub['fee'];
        $trade_hub_tax = $hub['tax'];
        $default_profit = $hub['pr']; // маржа на рынке
        //$manufacturing_possible = $hub['m'];
        //$invent_possible = $hub['i'];
        //$lightyears = $hub['ly'];
        $isotopes = $hub['it'];

        $this->price = $price;
        $this->price_wo_profit = $price/(1+$default_profit);
        $this->price_wo_fee_tax =  $this->price_wo_profit / (1+$brokers_fee+$trade_hub_tax);
        $this->price_wo_logistic = $this->price_wo_fee_tax - ($packaged_volume * $isotopes_price * $isotopes) / RHEA_CARGO_M3;
    }

    // вычислить относительно, например, цены производства (комиссии, доставка и налоги прибавляются)
    public function calculate_up(&$hub, float $price, float $packaged_volume, float $isotopes_price)
    {
        $brokers_fee = $hub['fee'];
        $trade_hub_tax = $hub['tax'];
        $default_profit = $hub['pr']; // маржа на рынке
        //$manufacturing_possible = $hub['m'];
        //$invent_possible = $hub['i'];
        //$lightyears = $hub['ly'];
        $isotopes = $hub['it'];

        $this->price_wo_logistic = $price;
        $this->price_wo_fee_tax = $this->price_wo_logistic + ($packaged_volume * $isotopes_price * $isotopes) / RHEA_CARGO_M3;
        $this->price_wo_profit = $this->price_wo_fee_tax * (1+$brokers_fee+$trade_hub_tax);
        $this->price = $this->price_wo_profit * (1+$default_profit);
    }
}

function get_actual_url($s, $grp, $ri4, $nsraw, $jpio)
{
    $url = strtok($_SERVER['REQUEST_URI'], '?').'?s='.$s;
    if (!is_null($grp) && !empty($grp)) $url = $url.'&grp='.implode(',',$grp);
    if ($ri4!=SHOW_ONLY_RI4_SALES_DEFAULT) $url = $url.'&only_ri4_sales='.($ri4?1:0);
    if ($nsraw!=DO_NOT_SHOW_RAW_MATERIALS_DEFAULT) $url = $url.'&raw_materials='.($nsraw?0:1); // инверсия
    if ($jpio!=SHOW_JITA_PRICE_INCLUDE_OURS_DEFAULT) $url = $url.'&jpio='.($jpio?1:0);
    return $url;
}

function __dump_market_hubs_links(&$market_groups, $SORT, $GRPs, $RI4, $NSRAW, $JPIO) {
    ?>Фильтры: <?php

    $no_filters =
        is_null($GRPs) &&
        ($RI4==SHOW_ONLY_RI4_SALES_DEFAULT) &&
        ($NSRAW==DO_NOT_SHOW_RAW_MATERIALS_DEFAULT) &&
        ($JPIO==SHOW_JITA_PRICE_INCLUDE_OURS_DEFAULT);
    if ($no_filters) { ?><b><?php }
    ?><a href="<?=get_actual_url($SORT, null, SHOW_ONLY_RI4_SALES_DEFAULT, DO_NOT_SHOW_RAW_MATERIALS_DEFAULT, SHOW_JITA_PRICE_INCLUDE_OURS_DEFAULT)?>">сбросить</a><?php
    if ($no_filters) { ?></b><?php }

    ?><br>Настройки: <?php

    if ($RI4==1) { ?><b><?php }
    ?><a href="<?=get_actual_url($SORT, $GRPs, $RI4?0:1, $NSRAW, $JPIO)?>"><?=($RI4)?'Только наши ордера':'Все ордера маркетов'?></a><?php
    if ($RI4==1) { ?></b><?php }

    if ($NSRAW==1) { ?><b><?php }
    ?>, <a href="<?=get_actual_url($SORT, $GRPs, $RI4, $NSRAW?0:1, $JPIO)?>"><?=($NSRAW)?'Без raw-материалов':'С raw-материалами'?></a><?php
    if ($NSRAW==1) { ?></b><?php }

    if ($JPIO==1) { ?><b><?php }
    ?>, <a href="<?=get_actual_url($SORT, $GRPs, $RI4, $NSRAW, $JPIO?0:1)?>">Jita-прайс <?=($JPIO)?'с учётом':'без'?> наших ордеров</a><?php
    if ($JPIO==1) { ?></b><?php }

    if ($market_groups)
    {
        $first = true;
        foreach ($market_groups as ["id" => $market_group_id, "grp" => $market_group_name]) // отсортированы сервером по названиям (market_group_name)
        {
            $market_group_id = intval($market_group_id);
            $grps = is_null($GRPs) ? array() : $GRPs;
            $key = array_search($market_group_id, $grps);
            $not_found = $key === false;
            if ($not_found) array_push($grps, $market_group_id); else unset($grps[$key]);
            if ($first) { $first = false; ?><br>Категории: <?php } else { ?>, <?php }
            if (!$not_found) { ?><b><?php }
            ?><a href="<?=get_actual_url($SORT, $grps, $RI4, $NSRAW, $JPIO)?>"><?=$market_group_name?></a><?php
            if (!$not_found) { ?></b><?php }
        }
    }
}

function __dump_market_hubs_table(&$market_hubs, $isotopes_price) { ?>
<table class="table table-condensed" style="padding:1px;font-size:smaller;" id="tblHubs">
<thead>
 <tr>
  <th>hub</th>
  <th>trader_corp</th>
  <th>brokers_fee</th>
  <th>trade_hub_tax</th>
  <th>profit</th>
  <th>manuf</th>
  <th>invent</th>
  <th>archive</th>
  <th>forbidden</th>
  <th>system_name</th>
  <th>station_type</th>
  <th>station_name</th>
  <th>lightyears</th>
  <th>isotopes</th>
  <th>route_to</th>
  <th>route_from</th>
 </tr>
</thead>
<tbody>
<?php
    foreach ($market_hubs as ["hub" => $hub
                              ,"co" => $trader_corp
                              ,"fee" => $brokers_fee
                              ,"tax" => $trade_hub_tax
                              ,"pr" => $default_profit
                              ,"m" => $manufacturing_possible
                              ,"i" => $invent_possible
                              ,"a" => $archive
                              ,"f" => $forbidden
                              ,"ss" => $solar_system_name
                              ,"snm" => $station_type_name
                              ,"nm" => $station_name
                              ,"ly" => $lightyears
                              ,"it" => $isotopes
                              ,"rs" => $route_to
                              ,"rd" => $route_from
                             ])
    {
?><tr>
 <td><?=$hub?></th>
 <td><?=$trader_corp?></th>
 <td><?=$brokers_fee?></th>
 <td><?=$trade_hub_tax?></th>
 <td><?=$default_profit?></th>
 <td><?=$manufacturing_possible?></th>
 <td><?=$invent_possible?></th>
 <td><?=$archive?></th>
 <td><?=$forbidden?></th>
 <td><?=$solar_system_name?></th>
 <td><?=$station_type_name?></th>
 <td><?=$station_name?></th>
 <td><?=$lightyears?></th>
 <td><?php if (!is_null($isotopes)) { ?><?=$isotopes.' ('.number_format(($isotopes_price*$isotopes)/RHEA_CARGO_M3,2,'.',',').' isk/m³)'?><?php } ?></th>
 <td><?php if (!is_null($route_to)) { ?><a href="<?=$route_to?>">to</a><?php } ?></th>
 <td><?php if (!is_null($route_from)) { ?><a href="<?=$route_from?>">from</a><?php } ?></th>
</tr><?php
    }
?>
</tbody>
</table>
<?php }

function __dump_market_table_header(&$hub_ids, &$market_hubs) {?>
<table class="table table-condensed" style="padding:1px;font-size:smaller;" id="tblMarkets">
<thead>
 <tr>
  <th style="width:32px;"></th>
  <th>Названия предметов</th>
<?php
    // список market_hubs отсортирован по дистанции прыжка (самые дальние маркеты в начале, Jita например)
    foreach ($market_hubs as ["hub" => $hub
                              //,"co" => $trader_corp
                              //,"fee" => $brokers_fee
                              //,"tax" => $trade_hub_tax
                              //,"pr" => $default_profit
                              //,"m" => $manufacturing_possible
                              //,"i" => $invent_possible
                              ,"a" => $archive
                              ,"f" => $forbidden
                              ,"ss" => $solar_system_name
                              //,"snm" => $station_type_name
                              //,"nm" => $station_name
                              //,"ly" => $lightyears
                              //,"it" => $isotopes
                              //,"rs" => $route_to
                              //,"rd" => $route_from
                             ])
    {
        // массив market_hubs В конце содержит архивные и закрытые маркеты, их в таблицу не выводим
        // пользуемся списоком hub_ids для определения что именно выводить, а что нет?: if ($a == 't' || $f == 't') break;
        $hub = get_numeric($hub);
        if (!in_array($hub, $hub_ids)) continue; ?>
  <th><?=$solar_system_name?></th>
        <?php
    }
?>
  <th style="text-align:right;">Jita Sell..Buy</th>
  <th style="text-align:center;">Подробности</th>
 </tr>
</thead>
<tbody>
<?php }

function __dump_market_table_footer(&$hub_ids, $summary_market_price, $summary_market_volume, $summary_jita_sell, $summary_jita_buy) {?>
</tbody>
<tfoot>
<tr class="qind-summary">
 <td colspan="<?=count($hub_ids)?>">Итог</td>
 <td><?=number_format($summary_market_price,0,'.',',').'<br>'.number_format($summary_market_volume,0,'.',',')?>m³</td>
 <td><?=number_format($summary_jita_sell,0,'.',',').'<br>'.number_format($summary_jita_buy,0,'.',',')?></td>
 <td colspan="1"></td>
</tr>
</tfoot>
</table>
<?php }

function __dump_market_group_name(&$hub_ids, &$market_group_name) { ?>
<tr><td class="active" colspan="<?=2+count($hub_ids)+3?>"><strong><?=$market_group_name?></strong></td></tr>
<?php }

function __dump_market_group_summary(&$hub_ids, &$market_group_name, $price, $volume, $jita_sell, $jita_buy) { ?>
<tr class="qind-summary">
 <td colspan="<?=2+count($hub_ids)?>">Итог по <?=$market_group_name?></td>
 <td><?=number_format($price,0,'.',',').'<br>'.number_format($volume,0,'.',',')?>m³</td>
 <td><?=number_format($jita_sell,0,'.',',').'<br>'.number_format($jita_buy,0,'.',',')?></td>
 <td colspan="1"></td>
</tr>
<?php }

function __dump_market_sale_orders(
    &$hub_ids,
    &$market_hubs,
    &$jita_market,
    &$sale_orders,
    $market_group_id,
    &$jita_market_index,
    &$sale_orders_index,
    $isotopes_price,
    &$market_jita_hub)
{
    foreach ($jita_market_index as $jm_key)
    {
        $jm = &$jita_market[$jm_key];
        $type_id = get_numeric($jm['id']);
        $type_name = $jm['nm'];
        $packaged_volume = $jm['pv']; // м.б. null
        $_market_group_id = $jm['grp'];
        $jita_sell = $jm['js'];
        $jita_buy = $jm['jb'];

        $hub_positions = null;
        foreach ($sale_orders_index as $so_key)
        {
            $so = &$sale_orders[$so_key];
            $_type_id = get_numeric($so['id']);
            if ($_type_id != $type_id) continue;
            $hub = get_numeric($so['hub']);
            $hub_idx = 0; foreach ($hub_ids as $h) if ($h == $hub) break; else $hub_idx++;
            if (is_null($hub_positions))
            {
                $hub_positions = array();
                foreach (range(0, count($hub_ids)-1) as $i) $hub_positions[$i] = null;
            }
            $hub_positions[$hub_idx] = $so_key;
        }
        ?>
<tr>
<td><img class="icn32" src="<?=__get_img_src($type_id,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
<td><?=$type_name?><?=get_clipboard_copy_button($type_name)/*.var_export($hub_positions)*/?></td>
        <?php
        if (!is_null($hub_positions))
            foreach ($hub_positions as $hub_key => &$so_key)
            {
                $h = $market_hubs[$hub_key];
                $brokers_fee = $h['fee'];
                $trade_hub_tax = $h['tax'];
                $default_profit = $h['pr'];
                $manufacturing_possible = $h['m'];
                $invent_possible = $h['i'];
                //$lightyears = $h['ly'];
                $isotopes = $h['it'];

                $jita_margin = null;
                $relative_jita_margin = null;
                if (($h['hub'] != 60003760) && !is_null($market_jita_hub) && !is_null($jita_sell))
                {
                    $jita_margin = new market_hub_margin();
                    $jita_margin->calculate_down($market_jita_hub, $jita_sell, $packaged_volume, $isotopes_price);
                    $relative_jita_margin = new market_hub_margin();
                    $relative_jita_margin->calculate_up($h, $jita_margin->price_wo_logistic, $packaged_volume, $isotopes_price);
                }

                if (is_null($so_key))
                {
?><td>
their_price/volume =<br>
our_price/volume =<br>
<?=is_null($packaged_volume)?'':'<br>packaged = '.number_format($packaged_volume*$our_volume,2,'.',',').'m³'?><br>
their =<br>
our =<br>
<?=is_null($jita_margin)?'':'jita = '.number_format($jita_margin->price,2,'.',',').'&nbsp;= '.
   number_format(eve_ceiling($jita_margin->price_wo_profit),2,'.',',').'&nbsp;= '.
   number_format(eve_ceiling($jita_margin->price_wo_fee_tax),2,'.',',').'&nbsp;= '.
   number_format(eve_ceiling($jita_margin->price_wo_logistic),2,'.',',')?><br>
<?=is_null($relative_jita_margin)?'':'rel jita = '.number_format($relative_jita_margin->price_wo_logistic,2,'.',',').'&nbsp;= '.
   number_format(eve_ceiling($relative_jita_margin->price_wo_fee_tax),2,'.',',').'&nbsp;= '.
   number_format(eve_ceiling($relative_jita_margin->price_wo_profit),2,'.',',').'&nbsp;= '.
   number_format(eve_ceiling($relative_jita_margin->price),2,'.',',')?><br>
</td><?php
                }
                else
                {
                    $o = $sale_orders[$so_key];
                    $our_volume = $o['ov'];
                    $price_total = $o['pt'];
                    $our_price = $o['op'];
                    $price_max = $o['pm'];
                    $orders_total = $o['ot'];
                    $their_volume = $o['tv'];
                    $their_price = $o['tp'];
?><td>
their_price/volume = <?=is_null($their_price)?'':number_format($their_price,2,'.',',').' ('.$their_volume.')'?><br>
our_price/volume = <?=number_format($our_price,2,'.',',').' ('.$our_volume.')'?>
<?=is_null($packaged_volume)?'':'<br>packaged = '.number_format($packaged_volume*$our_volume,2,'.',',').'m³'?><br>
<?php
  $hub_margin = new market_hub_margin();
  $hub_margin->calculate_down($h, $our_price, $packaged_volume, $isotopes_price);
  $their_margin = null;
  if (!is_null($their_price))
  {
    $their_margin = new market_hub_margin();
    $their_margin->calculate_down($h, $their_price, $packaged_volume, $isotopes_price);
  }
?>

their = <?=is_null($their_margin)?'':number_format($their_margin->price,2,'.',',').'&nbsp;= '.
   number_format(eve_ceiling($their_margin->price_wo_profit),2,'.',',').'&nbsp;= '.
   number_format(eve_ceiling($their_margin->price_wo_fee_tax),2,'.',',').'&nbsp;= '.
   number_format(eve_ceiling($their_margin->price_wo_logistic),2,'.',',')?><br>
our = <?=number_format($hub_margin->price,2,'.',',').'&nbsp;= '.
   number_format(eve_ceiling($hub_margin->price_wo_profit),2,'.',',').'&nbsp;= '.
   number_format(eve_ceiling($hub_margin->price_wo_fee_tax),2,'.',',').'&nbsp;= '.
   number_format(eve_ceiling($hub_margin->price_wo_logistic),2,'.',',')?><br>
<?=is_null($jita_margin)?'':'jita = '.number_format($jita_margin->price,2,'.',',').'&nbsp;= '.
   number_format(eve_ceiling($jita_margin->price_wo_profit),2,'.',',').'&nbsp;= '.
   number_format(eve_ceiling($jita_margin->price_wo_fee_tax),2,'.',',').'&nbsp;= '.
   number_format(eve_ceiling($jita_margin->price_wo_logistic),2,'.',',')?><br>
<?=is_null($relative_jita_margin)?'':'rel jita = '.number_format($relative_jita_margin->price_wo_logistic,2,'.',',').'&nbsp;= '.
   number_format(eve_ceiling($relative_jita_margin->price_wo_fee_tax),2,'.',',').'&nbsp;= '.
   number_format(eve_ceiling($relative_jita_margin->price_wo_profit),2,'.',',').'&nbsp;= '.
   number_format(eve_ceiling($relative_jita_margin->price),2,'.',',')?><br>


? = <?='tot:'.$price_total.' max:'.$price_max.' num:'.$orders_total.' '.($default_profit*100).'%'?></td><?php
                }
            }
        if (!is_null($hub_positions)) { unset($hub_positions); $hub_positions = null; }
        ?>
<td>
 <?=is_null($jita_sell)?'':number_format($jita_sell,2,'.',',')?><br>
 <?=is_null($jita_buy)?'':number_format($jita_buy,2,'.',',')?><br>
 <?=is_null($packaged_volume)?'':number_format($packaged_volume,($packaged_volume>0.009)?2:3,'.',',').'m³'?>
</td>
<td></td>
</tr>
<?php
    }
}


__dump_header("Market Hubs", FS_RESOURCES);
?>
<div class="container-fluid">
<?php
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");

    //--- --- --- --- ---
    $query = <<<EOD
select
 h.mh_hub_id as hub,
 h.mh_trader_corp as co,
 h.mh_brokers_fee as fee,
 h.mh_trade_hub_tax as tax,
 h.mh_default_profit as pr,
 h.mh_manufacturing_possible as m,
 h.mh_invent_possible as i,
 h.mh_archive as a,
 --c.ech_name as tr,
 s.forbidden as f,
 s.solar_system_name as ss,
 s.station_type_name as snm,
 s.name as nm,
 r.mr_lightyears_src_dst+r.mr_lightyears_dst_src as ly,
 r.mr_isotopes_src_dst+r.mr_isotopes_dst_src as it,
 r.mr_route_src_dst as rs,
 r.mr_route_dst_src as rd
from
 market_hubs h
  --left outer join esi_characters as c on (h.mh_trader_id=c.ech_character_id)
  left outer join market_routes as r on (h.mh_hub_id=r.mr_dst_hub),
 esi_known_stations s
where h.mh_hub_id=s.location_id
order by h.mh_archive, s.forbidden, r.mr_lightyears_dst_src desc;
EOD;
    $params = array();
    $market_hubs_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $market_hubs = pg_fetch_all($market_hubs_cursor);
    $hub_ids = array();
    $trader_corp_ids = array();
    foreach ($market_hubs as ["hub" => $hub, "co" => $co, "a" => $a, "f" => $f])
    {
      if ($a == 't' || $f == 't') continue; // archive or forbidden
      $hub_ids[] = get_numeric($hub);
      $trader_corp_ids[] = get_numeric($co);
    }
    $hub_ids = array_unique($hub_ids, SORT_NUMERIC);
    $trader_corp_ids = array_unique($trader_corp_ids, SORT_NUMERIC);
    //--- --- --- --- ---

    //echo '<pre>'.$query.' -- '.var_export($params, true).'</pre>';
    //echo "<b>market_hubs[0] = </b>"; var_dump($market_hubs[0]); echo "<br>";
    //echo "<b>count(market_hubs) = </b>"; var_dump(count($market_hubs)); echo "<br>";
    //echo "<b>hub_ids = </b>"; var_dump($hub_ids); echo "<br>";
    //echo "<b>trader_corp_ids = </b>"; var_dump($trader_corp_ids); echo "<hr>";

    //--- --- --- --- ---
    $query = <<<EOD
select distinct semantic_id as id, name as grp
from eve_sde_market_groups_semantic as market_group
where
 ($1=0 or market_group.semantic_id not in (
   2, -- Blueprints & Reactions
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
  ))
order by name;
EOD;
    $params = array($DO_NOT_SHOW_RAW_MATERIALS);
    $market_groups_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $market_groups = pg_fetch_all($market_groups_cursor);
    $grp_ids = array();
    foreach ($market_groups as ["id" => $id, "grp" => $name]) $grp_ids[] = get_numeric($id);
    //--- --- --- --- ---

    //echo '<pre>'.$query.' -- '.var_export($params, true).'</pre>';
    //echo "<b>market_groups[0] = </b>"; var_dump($market_groups[0]); echo "<br>";
    //echo "<b>count(market_groups) = </b>"; var_dump(count($market_groups)); echo "<br>";
    //echo "<b>grp_ids = </b>"; var_dump($grp_ids); echo "<hr>";

    //--- --- --- --- ---
    if ($SHOW_JITA_PRICE_INCLUDE_OURS)
    {
        $query = <<<EOD
select
 tid.sdet_type_id as id, -- type_id
 tid.sdet_type_name as nm, -- type_name
 tid.sdet_packaged_volume as pv, -- packaged_volume my be null
 market_group.semantic_id as grp, -- market_group_id
 jita_market.ethp_sell as js, -- jita sell
 jita_market.ethp_buy as jb -- jita buy
from
 eve_sde_type_ids as tid,
 eve_sde_market_groups_semantic as market_group,
 esi_trade_hub_prices as jita_market
where
 jita_market.ethp_location_id=60003760 and -- Jita
 jita_market.ethp_type_id=tid.sdet_type_id and
 jita_market.ethp_sell is not null and
 jita_market.ethp_sell_volume > 0 and
 market_group.id=tid.sdet_market_group_id and
 market_group.semantic_id=any($1) and
 ($2=0 or
  jita_market.ethp_type_id in (
   select ecor_type_id
   from esi_corporation_orders
   where ecor_corporation_id=any($3) and not ecor_is_buy_order and not ecor_history
 ))
order by market_group.name,tid.sdet_type_name;
EOD;
    }
    else
    {
        $query = <<<EOD
select
 tid.sdet_type_id as id, -- type_id
 tid.sdet_type_name as nm, -- type_name
 tid.sdet_packaged_volume as pv, -- packaged_volume my be null
 market_group.semantic_id as grp, -- market_group_id
 jita_market.jita_sell_price as js -- jita sell
from
 eve_sde_type_ids as tid,
 eve_sde_market_groups_semantic as market_group,
 (select
   etho_type_id as type_id,
   min(etho_price) as jita_sell_price,
   sum(etho_volume_remain) as jita_total_volume
  from esi_trade_hub_orders -- pk:location_id+oder_id
  where
   not etho_is_buy and
   etho_location_id=60003760 and
   etho_order_id not in (
    select ecor_order_id
    from esi_corporation_orders -- pk:corporation_id+order_id
    where ecor_corporation_id=98553333 and ecor_location_id=60003760 -- R Strike in Jita
   ) and
   ($2=0 or
    etho_type_id in (
     select ecor_type_id
     from esi_corporation_orders
     where ecor_corporation_id=any($3) and not ecor_is_buy_order and not ecor_history
   ))
  group by etho_type_id) as jita_market
where
 jita_market.type_id=tid.sdet_type_id and
 market_group.id=tid.sdet_market_group_id and
 market_group.semantic_id=any($1)
order by market_group.name,tid.sdet_type_name;
EOD;
    }
    $params = array('{'.implode(',',$grp_ids).'}',$SHOW_ONLY_RI4_SALES,'{'.implode(',',$trader_corp_ids).'}');
    $jita_market_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $jita_market = pg_fetch_all($jita_market_cursor);
    //--- --- --- --- ---

    //echo '<pre>'.$query.' -- '.var_export($params, true).'</pre>';
    //echo "<b>jita_market[0] = </b>"; var_dump($jita_market[0]); echo "<br>";
    //echo "<b>count(jita_market) = </b>".count($jita_market)."<hr>";

    //--- --- --- --- ---
    $query = <<<EOD
select
 --sell_orders.corp_id,
 sell_orders.type_id as id, -- type_id
 sell_orders.hub_id as hub, -- hub id
 sell_orders.volume_remain as ov, -- our_volume
 round(sell_orders.price_total::numeric, 2) as pt, -- price_total
 sell_orders.price_min as op, -- our_price
 sell_orders.price_max as pm, -- price_max
 sell_orders.orders_total as ot, -- orders_total
 hub_market.total_volume as tv, -- their_volume
 hub_market.min_price as tp -- their_price
from
 -- сводная статистика по текущим ордерам в наших маркетах
 (select
  ecor_corporation_id as corp_id,
  ecor_location_id as hub_id,
  ecor_type_id as type_id,
  sum(ecor_volume_remain) as volume_remain,
  avg(ecor_price*ecor_volume_remain) as price_total,
  min(ecor_price) as price_min,
  max(ecor_price) as price_max,
  count(1) as orders_total
 from esi_corporation_orders
 where
  not ecor_is_buy_order and
  not ecor_history and
  ecor_corporation_id=any($1)
 group by ecor_corporation_id, ecor_location_id, ecor_type_id) sell_orders
  -- локальные цены в этих торговых хабах (исключая наши позиции)
  left outer join (
   select
    etho_location_id as hub_id,
    etho_type_id as type_id,
    min(etho_price) as min_price,
    sum(etho_volume_remain) as total_volume
   from esi_trade_hub_orders -- pk:location_id+oder_id
   where
    not etho_is_buy and
    etho_location_id=any($2) and
    etho_order_id not in (
     select ecor_order_id
     from market_hubs, esi_corporation_orders -- pk:corporation_id+order_id
     where ecor_corporation_id=mh_trader_corp and ecor_location_id=mh_hub_id
    )
   group by etho_location_id, etho_type_id
  ) as hub_market on (sell_orders.hub_id=hub_market.hub_id and sell_orders.type_id=hub_market.type_id)
  left outer join (
    select ethp_type_id, ethp_sell as sell, ethp_buy as buy
    from esi_trade_hub_prices
    where ethp_location_id=60003760
  ) jita_market on (sell_orders.type_id=jita_market.ethp_type_id)
order by sell_orders.type_id;
EOD;
    $params = array('{'.implode(',',$trader_corp_ids).'}','{'.implode(',',$hub_ids).'}');
    $sale_orders_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $sale_orders = pg_fetch_all($sale_orders_cursor);
    //--- --- --- --- ---

    //echo '<pre>'.$query.' -- '.var_export($params, true).'</pre>';
    //echo "<b>sale_orders[0] = </b>"; var_dump($sale_orders[0]); echo "<br>";
    //echo "<b>count(sale_orders) = </b>".count($sale_orders)."<hr>";

    //--- --- --- --- ---
    $query = <<<EOD
select
 ethp_type_id as id,
 ethp_sell as js, -- jita sell
 ethp_buy as jb, -- jita buy
 round(ri_isotopes.price::numeric,2) as rib -- r initiative buy price
from
 esi_trade_hub_prices
  left outer join (
   select ri_isotopes.type_id, sum(total_price)/sum(total_volume) as price
   from
    (select
     ecor_type_id as type_id,
     ecor_volume_total-ecor_volume_remain as total_volume,
     ecor_price*(ecor_volume_total-ecor_volume_remain) * case
      when o.ecor_duration=0 then 1
      else 1+h.mh_brokers_fee
     end as total_price -- на длительных ордерах платим брокерскую комиссию
    from
     esi_corporation_orders o,
     market_hubs h
    where
     h.mh_hub_id=any($1) and
     o.ecor_corporation_id=mh_trader_corp and
     o.ecor_type_id in (17888,17887,16274,17889) and
     o.ecor_is_buy_order and
     ecor_volume_total<>ecor_volume_remain
    order by ecor_issued desc
    limit 20) ri_isotopes
   group by type_id
  ) as ri_isotopes on (ri_isotopes.type_id=ethp_type_id)
where
 ethp_location_id=60003760 and -- Jita
 -- Rhea:Nitrogen Isotopes, Anshar:Oxygen Isotopes, Ark:Helium Isotopes, Nomad:Hydrogen Isotopes
 ethp_type_id in (17888,17887,16274,17889);
EOD;
    $params = array('{'.implode(',',$hub_ids).'}');
    $isotopes_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $isotopes = pg_fetch_all($isotopes_cursor);
    $isotopes_price = null;
    foreach ($isotopes as ["id" => $id, "rib" => $rib, "js" => $js, "jb" => $jb])
      if (get_numeric($id) == 17888) // Rhea:Nitrogen Isotopes
      {
        if (!is_null($rib))
          $isotopes_price = get_numeric($rib);
        else if (!is_null($jb))
          $isotopes_price = get_numeric(($jb)*1.02);
        else
          $isotopes_price = get_numeric($js);
      }
    //--- --- --- --- ---

    //echo '<pre>'.$query.' -- '.var_export($params, true).'</pre>';
    echo "<b>isotopes = </b>"; var_dump($isotopes); echo "<br>";
    echo "<b>isotopes_price = </b>"; var_dump($isotopes_price); echo "<hr>";

    //--- --- --- --- ---
    $market_jita_hub = null;
    foreach ($market_hubs as $mh_key => ["hub" => $hub])
    {
      if (intval($hub) != 60003760) continue;
      $market_jita_hub = &$market_hubs[$mh_key];
      break;
    }
    //--- --- --- --- ---
    $grp_to_sale_orders_index = array();
    $grp_to_jita_market_index = array();
    foreach ($grp_ids as $market_group_id) // отсортированы сервером по названиям (market_group_name)
    {
      $gso = array();
      $gjm = array();
      foreach ($jita_market as $jm_key => ["id" => $type_id, "grp" => $_market_group_id]) // отсортированы по названиям (market_group_name, type_name)
      {
        if ($market_group_id != $_market_group_id) continue;
        $gjm[] = $jm_key;
        $type_id = get_numeric($type_id);
        foreach ($sale_orders as $so_key => ["id" => $_type_id, "hub" => $hub]) // отсортированы по type_id
        {
          $_type_id = get_numeric($_type_id);
          if ($_type_id < $type_id) continue;
          if ($_type_id > $type_id) break;
          $gso[] = $so_key;
        }
      }
      $grp_to_jita_market_index[$market_group_id] = $gjm;
      $grp_to_sale_orders_index[$market_group_id] = $gso;
      unset($gso);
    }
    //--- --- --- --- ---

    //echo "<b>grp_to_jita_market_index = </b>"; var_dump($grp_to_jita_market_index); echo "<hr>";
    //echo "<b>grp_to_sale_orders_index = </b>"; var_dump($grp_to_sale_orders_index); echo "<hr>";


__dump_market_hubs_links($market_groups, $SORT, $GRPs, $SHOW_ONLY_RI4_SALES, $DO_NOT_SHOW_RAW_MATERIALS, $SHOW_JITA_PRICE_INCLUDE_OURS);
__dump_market_hubs_table($market_hubs, $isotopes_price);
__dump_market_table_header($hub_ids, $market_hubs);
foreach ($market_groups as ["id" => $id, "grp" => $name])
{
  if (0 == count($grp_to_jita_market_index[$id])) continue;
  __dump_market_group_name($hub_ids, $name);
  __dump_market_sale_orders(
    $hub_ids,
    $market_hubs,
    $jita_market,
    $sale_orders,
    $id,
    $grp_to_jita_market_index[$id],
    $grp_to_sale_orders_index[$id],
    $isotopes_price,
    $market_jita_hub);
  __dump_market_group_summary($hub_ids, $name, 0, 0, 0, 0);
}
__dump_market_table_footer($hub_ids, 0, 0, 0, 0);

?></div> <!--container-fluid-->
<?php __dump_footer(); ?>

<?php __dump_copy_to_clipboard_javascript() ?>
