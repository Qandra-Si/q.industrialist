<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include_once '.settings.php';


const SORT_PRFT_ASC = 1;
const SORT_PRFT_DESC = -1;
const SORT_PERC_ASC = 2;
const SORT_PERC_DESC = -2;
const T1_ONLY_DEFAULT = 0;
const T2_ONLY_DEFAULT = 0;
const T3_ONLY_DEFAULT = 0;
const FA_ONLY_DEFAULT = 0;
const RA_ONLY_DEFAULT = 0;
const SHOW_ONLY_RI4_SALES_DEFAULT = 1;
const DO_NOT_SHOW_RAW_MATERIALS_DEFAULT = 1;
const INDUSTRY_POSSIBLE_DEFAULT = null;


$SORT = SORT_PRFT_ASC;
$GRPs = null;

// Abyssal (15) - не производится
// Deadspace (6) - не производится
// Limited Time (19) - иногда производится
// Officer (5) - единичные экземпляры производятся (Zorya's)
// Premium (17) - не производится
// Storyline (3) - иногда производится
// Faction (4)
// Structure Faction (52)
// Structure Tech I (54)
// Structure Tech II (53)
// Tech I (1)
// Tech II (2)
// Tech III (14)
$T1 = T1_ONLY_DEFAULT;
$T2 = T2_ONLY_DEFAULT;
$T3 = T3_ONLY_DEFAULT;
$FA = FA_ONLY_DEFAULT;
$RA = RA_ONLY_DEFAULT;
$INDUSTRY_POSSIBLE = INDUSTRY_POSSIBLE_DEFAULT;


if (!isset($SHOW_ONLY_RI4_SALES))
    $SHOW_ONLY_RI4_SALES = SHOW_ONLY_RI4_SALES_DEFAULT; // признак отображения информации по ордерам, которые выставлены не нами
if (!isset($DO_NOT_SHOW_RAW_MATERIALS))
    $DO_NOT_SHOW_RAW_MATERIALS = DO_NOT_SHOW_RAW_MATERIALS_DEFAULT; // не показывать метариалы, закуп которых выполняется для производственных работ (фильтрация спекуляции и закупа для производства, например минералов)

if (!isset($IMPORT_PRICE_TO_TRADE_HUB))
    $IMPORT_PRICE_TO_TRADE_HUB = null; // null; // например, цена импорта 1куб.м. из Jita в Querious была 866 ISK
if (!isset($MIN_PROFIT))
    $MIN_PROFIT = 0.05; // 5%
if (!isset($DEFAULT_PROFIT))
    $DEFAULT_PROFIT = null; // если не указан, то ниже будет установлен в дефолтное значение с выводом предупреждения)
if (!isset($MAX_PROFIT))
    $MAX_PROFIT = 0.25; // 25%
if (!isset($BROKERS_FEE))
    $BROKERS_FEE = null; // брокерская комиссия - если не указан, то ниже будет установлен в дефолтное значение с выводом предупреждения)
if (!isset($TRADE_HUB_TAX))
    $TRADE_HUB_TAX = null; // sales tax, налог на структуре - если не указан, то ниже будет установлен в дефолтное значение с выводом предупреждения)
if (!isset($CORPORATION_IDs))
    $CORPORATION_IDs = array(98553333); // R Initiative 4: 98615601, R Strike: 98553333, R Industry: 98677876
if (!isset($TRADE_HUB_ID))
    $TRADE_HUB_ID = null; // PZ: 1034323745897, Nisuwa: 60015073, 4-HWWF: 1035466617946, NSI-MW: 1022822609240
if (!isset($TRADER_ID))
    $TRADER_ID = 0; // Xatul' Madan: 95858524, DarkFman: 874053567, Zed Ostus: 2116422143


if (!isset($_GET['grp'])) $GRPs = null; else {
  $_get_grp = htmlentities($_GET['grp']);
  if (is_numeric($_get_grp)) $GRPs = array(get_numeric($_get_grp));
  else if (is_numeric_array($_get_grp)) $GRPs = get_numeric_array($_get_grp);
  else return;
}

if (!isset($_GET['s'])) $SORT = SORT_PRFT_ASC; else {
  $_get_sort = htmlentities($_GET['s']);
  if (is_numeric($_get_sort)) $SORT = get_numeric($_get_sort);
  else $SORT = SORT_PRFT_ASC;
}

if (!isset($_GET['t1'])) $T1 = T1_ONLY_DEFAULT; else {
  $_get_t1 = htmlentities($_GET['t1']);
  if (is_numeric($_get_t1)) $T1 = get_numeric($_get_t1);
  else $T1 = T1_ONLY_DEFAULT;
}

if (!isset($_GET['t2'])) $T2 = T2_ONLY_DEFAULT; else {
  $_get_t2 = htmlentities($_GET['t2']);
  if (is_numeric($_get_t2)) $T2 = get_numeric($_get_t2);
  else $T2 = T2_ONLY_DEFAULT;
}

if (!isset($_GET['t3'])) $T3 = T3_ONLY_DEFAULT; else {
  $_get_t3 = htmlentities($_GET['t3']);
  if (is_numeric($_get_t3)) $T3 = get_numeric($_get_t3);
  else $T3 = T3_ONLY_DEFAULT;
}

if (!isset($_GET['faction'])) $FA = FA_ONLY_DEFAULT; else {
  $_get_faction = htmlentities($_GET['faction']);
  if (is_numeric($_get_faction)) $FA = get_numeric($_get_faction);
  else $FA = FA_ONLY_DEFAULT;
}

if (!isset($_GET['rare'])) $RA = RA_ONLY_DEFAULT; else {
  $_get_rare = htmlentities($_GET['rare']);
  if (is_numeric($_get_rare)) $RA = get_numeric($_get_rare);
  else $RA = RA_ONLY_DEFAULT;
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

if (isset($_GET['industry_possible'])) {
    $_get_industry_possible = htmlentities($_GET['industry_possible']);
    if (is_numeric($_get_industry_possible)) $INDUSTRY_POSSIBLE = get_numeric($_get_industry_possible) ? 1 : 0;
    else $INDUSTRY_POSSIBLE = INDUSTRY_POSSIBLE_DEFAULT;
}

if (isset($_GET['import'])) {
    $_get_import_price = htmlentities($_GET['import']);
    if (is_numeric($_get_import_price))
        $IMPORT_PRICE_TO_TRADE_HUB = get_numeric($_get_import_price);
}

if (isset($_GET['profit'])) {
    $_get_default_profit = htmlentities($_GET['profit']);
    if (is_numeric($_get_default_profit)) {
        $DEFAULT_PROFIT = get_numeric($_get_default_profit) / 100.0;
        if ($MIN_PROFIT > $DEFAULT_PROFIT)
            $MIN_PROFIT = $DEFAULT_PROFIT;
        if ($MAX_PROFIT < $DEFAULT_PROFIT)
            $MAX_PROFIT = $DEFAULT_PROFIT;
    }
}

if (isset($_GET['fee'])) {
    $_get_fee = htmlentities($_GET['fee']);
    if (is_numeric($_get_fee))
        $BROKERS_FEE = get_numeric($_get_fee);
}

if (isset($_GET['tax'])) {
    $_get_tax = htmlentities($_GET['tax']);
    if (is_numeric($_get_tax))
        $TRADE_HUB_TAX = get_numeric($_get_tax);
}

if (isset($_GET['corp'])) {
    $_get_corp = htmlentities($_GET['corp']);
    if (is_numeric($_get_corp))
        $CORPORATION_IDs = array(get_numeric($_get_corp));
    else if (is_numeric_array($_get_corp))
        $CORPORATION_IDs = get_numeric_array($_get_corp);
}

if (isset($_GET['hub'])) {
    $_get_trade_hub_id = htmlentities($_GET['hub']);
    if (is_numeric($_get_trade_hub_id))
        $TRADE_HUB_ID = get_numeric($_get_trade_hub_id);
}

if (isset($_GET['trader'])) {
    $_get_trader_id = htmlentities($_GET['trader']);
    if (is_numeric($_get_trader_id))
        $TRADER_ID = get_numeric($_get_trader_id);
}


function get_actual_url($s, $grp, $t1, $t2, $t3, $fa, $ra, $ri4, $nsraw, $ip)
{
    $url = strtok($_SERVER[REQUEST_URI], '?').'?s='.$s;
    if ($t1!=T1_ONLY_DEFAULT) $url = $url.'&t1='.($t1?1:0);
    if ($t2!=T2_ONLY_DEFAULT) $url = $url.'&t2='.($t2?1:0);
    if ($t3!=T3_ONLY_DEFAULT) $url = $url.'&t3='.($t3?1:0);
    if ($fa!=FA_ONLY_DEFAULT) $url = $url.'&faction='.($fa?1:0);
    if ($ra!=RA_ONLY_DEFAULT) $url = $url.'&rare='.($ra?1:0);
    if (!is_null($grp) && !empty($grp)) $url = $url.'&grp='.implode(',',$grp);
    if ($ri4!=SHOW_ONLY_RI4_SALES_DEFAULT) $url = $url.'&only_ri4_sales='.($ri4?1:0);
    if ($nsraw!=DO_NOT_SHOW_RAW_MATERIALS_DEFAULT) $url = $url.'&raw_materials='.($nsraw?0:1); // инверсия
    if (!is_null($ip)) $url = $url.'&industry_possible='.($ip?1:0);
    return $url;
}


function __dump_trade_hub_links(&$market, $SORT, $GRPs, $T1, $T2, $T3, $FA, $RA, $RI4, $NSRAW, $IP) {
    ?>Filters: <?php

    $no_filters =
        is_null($GRPs) &&
        ($T1==T1_ONLY_DEFAULT) &&
        ($T2==T2_ONLY_DEFAULT) &&
        ($T3==T3_ONLY_DEFAULT) &&
        ($FA==FA_ONLY_DEFAULT) &&
        ($RA==RA_ONLY_DEFAULT) &&
        ($RI4==SHOW_ONLY_RI4_SALES_DEFAULT) &&
        ($NSRAW==DO_NOT_SHOW_RAW_MATERIALS_DEFAULT) &&
        (!is_null($IP));
    if ($no_filters) { ?><b><?php }
    ?><a href="<?=get_actual_url($SORT, null, T1_ONLY_DEFAULT, T2_ONLY_DEFAULT, T3_ONLY_DEFAULT, FA_ONLY_DEFAULT, RA_ONLY_DEFAULT, SHOW_ONLY_RI4_SALES_DEFAULT, DO_NOT_SHOW_RAW_MATERIALS_DEFAULT, INDUSTRY_POSSIBLE_DEFAULT)?>">DEFAULT</a><?php
    if ($no_filters) { ?></b><?php }

    if ($T1==1) { ?><b><?php }
    ?>, <a href="<?=get_actual_url($SORT, $GRPs, $T1?0:1, 0, 0, 0, 0, $RI4, $NSRAW, $IP)?>">T1 only</a><?php
    if ($T1==1) { ?></b><?php }

    if ($T2==1) { ?><b><?php }
    ?>, <a href="<?=get_actual_url($SORT, $GRPs, 0, $T2?0:1, 0, 0, 0, $RI4, $NSRAW, $IP)?>">T2 only</a><?php
    if ($T2==1) { ?></b><?php }

    if ($T3==1) { ?><b><?php }
    ?>, <a href="<?=get_actual_url($SORT, $GRPs, 0, 0, $T3?0:1, 0, 0, $RI4, $NSRAW, $IP)?>">T3 only</a><?php
    if ($T3==1) { ?></b><?php }

    if ($FA==1) { ?><b><?php }
    ?>, <a href="<?=get_actual_url($SORT, $GRPs, 0, 0, 0, $FA?0:1, 0, $RI4, $NSRAW, $IP)?>">Faction only</a><?php
    if ($FA==1) { ?></b><?php }

    if ($RA==1) { ?><b><?php }
    ?>, <a href="<?=get_actual_url($SORT, $GRPs, 0, 0, 0, 0, $RA?0:1, $RI4, $NSRAW, $IP)?>">Rare speciments</a><?php
    if ($RA==1) { ?></b><?php }

    ?><br>Settings: <?php

    if ($RI4==1) { ?><b><?php }
    ?><a href="<?=get_actual_url($SORT, $GRPs, $T1, $T2, $T3, $FA, $RA, $RI4?0:1, $NSRAW, $IP)?>">Only RI4 sales</a><?php
    if ($RI4==1) { ?></b><?php }

    if ($NSRAW==1) { ?><b><?php }
    ?>, <a href="<?=get_actual_url($SORT, $GRPs, $T1, $T2, $T3, $FA, $RA, $RI4, $NSRAW?0:1, $IP)?>">Without RAW materials</a><?php
    if ($NSRAW==1) { ?></b><?php }

    if (!is_null($IP)) {
    ?>, <b><a href="<?=get_actual_url($SORT, $GRPs, $T1, $T2, $T3, $FA, $RA, $RI4, $NSRAW, $IP?0:null)?>">Industry <?=($IP==0)?'im':''?>possible</a></b><?php
    } else {
    ?>, <a href="<?=get_actual_url($SORT, $GRPs, $T1, $T2, $T3, $FA, $RA, $RI4, $NSRAW, 1)?>">Industry undefined</a><?php
    }

    $first = true;
    $prev_market_group = null;
    if ($market)
        foreach ($market as $pkey => &$product)
        {
            $market_group = $product['grp'];
            if ($prev_market_group != $market_group)
            {
                $prev_market_group = $market_group;
                $market_group_id = intval($product['grp_id']);
                $grp = is_null($GRPs) ? array() : $GRPs;
                $key = array_search($market_group_id, $grp);
                $not_found = $key === false;
                if ($not_found) array_push($grp, $market_group_id); else unset($grp[$key]);
                if ($first) { $first = false; ?><br>Categories: <?php } else { ?>, <?php }
                if (!$not_found) { ?><b><?php }
                ?><a href="<?=get_actual_url($SORT, $grp, $T1, $T2, $T3, $FA, $RA, $RI4, $NSRAW, $IP)?>"><?=$market_group?></a><?php
                if (!$not_found) { ?></b><?php }
            }
        }
}


// настройки видимости элементов таблицы (по умолчанию)
const MARKET_TABLE_columns = 9;
const MARKET_TABLE_DEFAULT_order_volume_visible = 0; // видимость колонки таблицы "кол-во сделок (неделя/ордер)"
const MARKET_TABLE_DEFAULT_industry_volume_visible = 0; // видимость колонки таблицы "объём производства"



    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
select
 name,
 solar_system_name as ssn,
 prc.up as prc,
 ord.up as ord,
 tra.up as tra
from
 qi.esi_known_stations
  left outer join (
   select ethp_location_id, max(ethp_updated_at) as up
   from qi.esi_trade_hub_prices
   group by 1
  ) prc on (prc.ethp_location_id = location_id)
  left outer join (
   select ecor_location_id, max(ecor_updated_at) as up
   from qi.esi_corporation_orders
   group by 1
  ) ord on (ord.ecor_location_id = location_id)
  left outer join (
   -- список транзакций по покупке/продаже имени корпораций или от имени избранных персонажей
   select t.ecwt_location_id, max(j.ecwj_date) as up
   from
    qi.esi_corporation_wallet_journals j
     left outer join qi.esi_corporation_wallet_transactions t on (ecwj_context_id = ecwt_transaction_id) -- (j.ecwj_reference_id = t.ecwt_journal_ref_id)
   where
    (ecwj_date > '2023-05-01') and
    (ecwj_context_id_type = 'market_transaction_id') and
    ( ( ecwj_corporation_id=any($1) and
        ecwt_location_id=$2 and not ecwt_is_buy ) or -- станка рынка
      ( ecwj_second_party_id=$3 and -- торговый персонаж,...
        ecwt_location_id<>$2 and ecwt_is_buy ) -- ..., который закупается не по месту продажи
    ) and
    ecwt_type_id is not null -- данные journal могут пока отсутствовать, а в transaction уже быть
   group by 1
  ) tra on (tra.ecwt_location_id = location_id)
where location_id = $2;
EOD;
    $params = array('{'.implode(',',$CORPORATION_IDs).'}', $TRADE_HUB_ID, $TRADER_ID);
    $trade_hub_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $trade_hub_status = pg_fetch_all($trade_hub_cursor);
    if ($trade_hub_status)
    {
        $trade_hub_system = $trade_hub_status[0]['ssn'];
    }
    else
    {
        $trade_hub_system = 'Unknown';
        unset($trade_hub_status);
        $trade_hub_status = null;
    }

    __dump_header($trade_hub_system." Market", FS_RESOURCES);

    if (is_null($IMPORT_PRICE_TO_TRADE_HUB)) { ?>
<div class="alert alert-warning" role="alert">
<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>
<span class="sr-only">Внимание:</span> Не указан параметр <mark>import_price</mark> (стоимость доставки товаров) который используется в автоматическом расчёте цены при размещении ордера. Воспользуйтесь руководством или обратитесь к разработчику для добавления шаблона торгового терминала для маркета в этой системе.
</div> <?php
    }

    if (is_null($DEFAULT_PROFIT)) {
        // устанавливаем профит в значение по умолчанию
        $DEFAULT_PROFIT = 0.15; ?>
<div class="alert alert-warning" role="alert">
<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>
<span class="sr-only">Внимание:</span> Не указан параметр <mark>profit</mark> (профит от продажи товаров) который используется в автоматическом расчёте цены при размещении ордера. Воспользуйтесь руководством или обратитесь к разработчику для добавления шаблона торгового терминала для маркета в этой системе. Значение параметра автоматически принято равным <mark><?=$DEFAULT_PROFIT*100?>%</mark>, что может не соответствовать ориентировочной доходности в системе <?=$trade_hub_system?>.
</div> <?php
    }

    if (is_null($BROKERS_FEE)) {
        // устанавливаем брокерскую комиссию в значение по умолчанию
        $BROKERS_FEE = 0.02; ?>
<div class="alert alert-warning" role="alert">
<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>
<span class="sr-only">Внимание:</span> Не указан параметр <mark>brokers_fee</mark> (брокерская комиссия) который используется в автоматическом расчёте цены при размещении ордера. Воспользуйтесь руководством или обратитесь к разработчику для добавления шаблона торгового терминала для маркета в этой системе. Значение параметра автоматически принято равным <mark><?=$BROKERS_FEE*100?>%</mark>, что может не соответствовать комисии вашего торговца на рынке в системе <?=$trade_hub_system?>.
</div> <?php
    }

    if (is_null($TRADE_HUB_TAX)) {
        // устанавливаем налог в значение по умолчанию
        $TRADE_HUB_TAX = 0.036; ?>
<div class="alert alert-warning" role="alert">
<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>
<span class="sr-only">Внимание:</span> Не указан параметр <mark>sales_tax</mark> (налог от продаж, налог на структуре) который используется в автоматическом расчёте цены при размещении ордера. Воспользуйтесь руководством или обратитесь к разработчику для добавления шаблона торгового терминала для маркета в этой системе. Значение параметра автоматически принято равным <mark><?=$TRADE_HUB_TAX*100?>%</mark>, что может не соответствовать налогу для вашего торговца на рынке в системе <?=$trade_hub_system?>.
</div> <?php
    }



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


function __dump_market_group_summary(&$market_group, $price, $volume, $jita_sell, $jita_buy) { ?>
<tr class="qind-summary">
 <td colspan="<?=(MARKET_TABLE_DEFAULT_order_volume_visible?3:2)+(MARKET_TABLE_DEFAULT_industry_volume_visible?1:0)?>"><?=$market_group?> Summary</td>
 <td><?=number_format($price,0,'.',',').'<br>'.number_format($volume,0,'.',',')?>m³</td>
 <td><?=number_format($jita_sell,0,'.',',').'<br>'.number_format($jita_buy,0,'.',',')?></td>
 <td colspan="<?=MARKET_TABLE_columns-6-(MARKET_TABLE_DEFAULT_order_volume_visible?0:1)-(MARKET_TABLE_DEFAULT_industry_volume_visible?0:1)?>"></td>
</tr>
<?php }


function __dump_querious_market(&$market, &$storage, &$purchase, $trade_hub_system) {
    global $IMPORT_PRICE_TO_TRADE_HUB, $MIN_PROFIT, $MAX_PROFIT;
    global $TRADE_HUB_TAX, $BROKERS_FEE;
    global $GRPs, $T1, $T2, $T3, $FA, $RA, $INDUSTRY_POSSIBLE;
    $TAX_AND_FEE = $TRADE_HUB_TAX + $BROKERS_FEE;
?>
<h2><?=$trade_hub_system?> Market</h2>
<style>
/*метки*/
.label-qind-noordersreal { color: #fff; background-color: #d9534f; }
.label-qind-noorders { color: #fff; background-color: #eebbb9; }
.label-qind-interrupt { color: #8e8e8e; background-color: #e8ce43; }
.label-qind-dontbuy { color: #e8ce43; background-color: #b74c33; }
.label-qind-needdelivery { color: #fff; background-color: #5bc0de; }
.label-qind-placeanorder { color: #fff; background-color: #d973e8; }
.label-qind-lowprice { color: #fff; background-color: #f0ad4e; }
.label-qind-highprice { color: #fff; background-color: #777; }
.label-qind-veryfew { color: #fff; background-color: #337ab7; }
.label-qind-prepblueprints,
.label-qind-invblueprints { color: #d9d9d9; background-color: #20528a; }
.label-qind-industryjobs { color: #000; background-color: #ff9900; }
.label-qind-inassets { color: #fff; background-color: #0a7f6f; } /*c8c8c8:751c1c*/
/*стили отображения ячеек таблицы*/
#tblMarket thead tr th:nth-child(3),
#tblMarket tbody tr td:nth-child(3) { text-align: right; display: <?=MARKET_TABLE_DEFAULT_order_volume_visible?'table-cell':'none'?>; }
#tblMarket thead tr th:nth-child(4),
#tblMarket tbody tr td:nth-child(4) { text-align: right; display: <?=MARKET_TABLE_DEFAULT_industry_volume_visible?'table-cell':'none'?>; }
#tblMarket thead tr th:nth-child(5),
#tblMarket tbody tr td:nth-child(5) { text-align: right; }
#tblMarket thead tr th:nth-child(6),
#tblMarket tbody tr td:nth-child(6) { text-align: right; }
#tblMarket tfoot tr,
.qind-summary { font-weight: bold; }
#tblMarket tfoot tr td,
.qind-summary { text-align: right; }
tr.qind-summary td:nth-child(3) { display: table-cell !important; }
/*цвета,тексты*/
mute, mute-sm { padding: 0.2em; color: #bbb; }
mute-sm { font-size: 85%; }
</style>
<table class="table table-condensed" style="padding:1px;font-size:smaller;" id="tblMarket">
<thead>
 <tr>
  <th style="width:32px;"></th>
  <th>Названия предметов (+продано за сутки)</th>
  <th>Неделя<br><mark>Ордер</mark> шт</th>
  <th>Объёмы<br>производства</th>
  <th>Цена RI4<sup>sell</sup><br><mark>Кол-во</mark> шт</th>
  <th>Цена <?=$trade_hub_system?><sup>sell</sup><br><mark>Кол-во</mark> шт</th>
  <th style="text-align:right;">Jita Buy..Sell<br><?php if (!is_null($IMPORT_PRICE_TO_TRADE_HUB)) { ?><mark>Import Price</mark><?php } ?></th>
  <th style="text-align:right;">Amarr<br>Sell</th>
  <th style="text-align:right;">Universe<br>Price</th>
  <th style="text-align:center;">Details</th>
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
    $curr_market_group = null;
    $summary_market_group_price = 0;
    $summary_market_group_volume = 0;
    $summary_market_group_jita_sell = 0;
    $summary_market_group_jita_buy = 0;
    $market_group_summary_market_price = 0;
    $market_group_summary_market_volume = 0;
    $market_group_summary_jita_sell = 0;
    $market_group_summary_jita_buy = 0;
    if ($market)
        foreach ($market as &$product)
        {
            $problems = '';
            $warnings = '';
            $industry = '';
            $interrupt_detected = false;

            $tid = $product['id'];
            $ri4_sell_lvl = $product['ri4s'];
            $nm = $product['name'];
            $weekly_volume = $product['wv'];
            $order_volume = $product['ov'];
            $day_volume = $product['dv'];
            $ri4_market_quantity = $product['mv'];
            $packaged_volume = $product['pv'];
            $trade_hub_import_price = is_null($IMPORT_PRICE_TO_TRADE_HUB) ? null : ($packaged_volume * $IMPORT_PRICE_TO_TRADE_HUB);
            $jita_sell = $product['js'];
            $jita_buy = $product['jb'];
            $amarr_sell = $product['as'];
            $jita_price_lower = $jita_sell < $amarr_sell;
            $amarr_price_lower = $amarr_sell < $jita_sell;
            $universe_price = $product['up'];
            $ri4_price = $product['mp'];
            //$markup = $jita_sell * $TAX_AND_FEE;
            //$jita_10_price = eve_ceiling($jita_sell * (1.0+$DEFAULT_PROFIT+$TAX_AND_FEE)); // Jita +10% Price
            //$jita_10_profit = $jita_10_price - $jita_sell - $markup;
            $trade_hub_sell = $product['ps'];
            $trade_hub_sell_volume = $product['psv'];
            $industrial_jobs = $product['jq'];
            $present_in_assets = $product['aq'];
            $blueprints_prepared = $product['bpr'];
            $blueprints_invent = $product['bpi'];

            $market_group = $product['grp'];
            if ($prev_market_group != $market_group)
            {
                if (!is_null($prev_market_group) && $market_group_summary_market_price)
                {
                    __dump_market_group_summary(
                        $prev_market_group,
                        $market_group_summary_market_price,
                        $market_group_summary_market_volume,
                        $market_group_summary_jita_sell,
                        $market_group_summary_jita_buy
                    );
                }
                $prev_market_group = $market_group;
                $curr_market_group = $market_group;
                $market_group_summary_market_price = 0;
                $market_group_summary_market_volume = 0;
                $market_group_summary_jita_sell = 0;
                $market_group_summary_jita_buy = 0;
                ?><tr><td class="active" colspan="<?=MARKET_TABLE_columns?>"><strong><?=$market_group?></strong></td></tr><?php
            }

            if ($T1 == 1 || $T2 == 1 || $T3 == 1 || $FA == 1 || $RA == 1)
            {
                $meta = $product['meta'];
                if (is_null($meta)) continue;
                // см. https://everef.net/meta-groups
                $meta_num = intval($meta);
                if ($T1 == 1) { if ($meta_num != 1 && $meta_num != 54) continue; }
                else if ($T2 == 1) { if ($meta_num != 2 && $meta_num != 53) continue; }
                else if ($T3 == 1) { if ($meta_num != 14) continue; }
                else if ($FA == 1) { if ($meta_num != 4 && $meta_num != 52) continue; }
                else if ($RA == 1) { if ($meta_num != 15 && $meta_num != 6 && $meta_num != 19 && $meta_num != 5 && $meta_num != 17 && $meta_num != 3) continue; } // 15,6,19,5,17,3
            }
            if (!is_null($INDUSTRY_POSSIBLE))
            {
                $blueprint_type_id = $product['bp_tid'];
                if ($INDUSTRY_POSSIBLE == 1) // possible
                {
                    if (is_null($blueprint_type_id)) continue;
                }
                else if ($INDUSTRY_POSSIBLE == 0) // impossible
                {
                    if (!is_null($blueprint_type_id)) continue;
                }
            }
            if (!is_null($GRPs))
            {
                $market_group_id = intval($product['grp_id']);
                if (array_search($market_group_id, $GRPs) === false) continue;
            }

            if (!is_null($blueprints_invent))
                $industry .= '<span class="label label-qind-invblueprints">invent</span>&nbsp;';
            if (!is_null($blueprints_prepared))
                $industry .= '<span class="label label-qind-prepblueprints">blueprints</span>&nbsp;';
            if (!is_null($industrial_jobs))
                $industry .= '<span class="label label-qind-industryjobs">jobs</span>&nbsp;';
            if (!is_null($present_in_assets))
                $industry .= '<span class="label label-qind-inassets">in assets</span>&nbsp;';

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
                if (is_null($trade_hub_sell_volume) || !$trade_hub_sell_volume)
                    $problems .= '<span class="label label-qind-noordersreal">no orders</span>&nbsp;';
                else
                    $problems .= '<span class="label label-qind-noorders">no orders</span>&nbsp;';
            }
            if (!is_null($ri4_market_quantity)) {
                if ($weekly_volume >= ($ri4_market_quantity+$storage_quantity))
                    $problems .= '<span class="label label-qind-needdelivery">need delivery</span>&nbsp;';
                if ($storage_quantity && ($weekly_volume >= $ri4_market_quantity))
                    $warnings .= '<span class="label label-qind-placeanorder">place an order</span>&nbsp;';
            }
            if (!is_null($ri4_market_quantity) && ($order_volume >= $ri4_market_quantity)) $problems .= '<span class="label label-qind-veryfew">very few</span>&nbsp;';
            if (!is_null($ri4_price)) {
                if ($ri4_price > 100000 || $packaged_volume < 5) {
                    $min_jita_price = $jita_sell * (1.0+$MIN_PROFIT+$TAX_AND_FEE);
                    $min_amarr_price = $amarr_sell * (1.0+$MIN_PROFIT+$TAX_AND_FEE);
                    if (($ri4_price < $min_jita_price) && ($ri4_price < $min_amarr_price))
                        $warnings .= '<span class="label label-qind-lowprice" data-toggle="tooltip" data-placement="bottom" title="Min Amarr: '.number_format(eve_ceiling($min_amarr_price),2,'.',',').', min Jita: '.number_format(eve_ceiling($min_jita_price),2,'.',',').'">low price</span>&nbsp;';
                }
                $max_jita_price = $jita_sell * (1.0+$MAX_PROFIT+$TAX_AND_FEE);
                $max_amarr_price = $amarr_sell * (1.0+$MAX_PROFIT+$TAX_AND_FEE);
                if (($ri4_price > $max_jita_price) && ($ri4_price > $max_amarr_price))
                    $warnings .= '<span class="label label-qind-highprice" data-toggle="tooltip" data-placement="bottom" title="Max Amarr: '.number_format(eve_ceiling($max_amarr_price),2,'.',',').', max Jita: '.number_format(eve_ceiling($max_jita_price),2,'.',',').'">price too high</span>&nbsp;';
                if (!is_null($trade_hub_sell) && ($trade_hub_sell < $ri4_price) && ($trade_hub_sell_volume > $ri4_market_quantity)) {
                    $interrupt_detected = true;
                    $warnings .= '<span class="label label-qind-interrupt">interrupt</span>&nbsp;';
                }
            }
            if ($trade_hub_sell_volume > $ri4_market_quantity) {
                // рассчитываем минимальную цену, ниже которой закупку производить не следует - позиция перебита конкурентами
                $min_buy_price = $trade_hub_sell / (1.0+$TAX_AND_FEE+$MIN_PROFIT);
                if (($jita_sell > $min_buy_price) && ($amarr_sell > $min_buy_price))
                    $warnings .= '<span class="label label-qind-dontbuy" data-toggle="tooltip" data-placement="bottom" title="Min buy price: '.number_format(eve_ceiling($min_buy_price),2,'.',',').'">don&apos;t buy</span>&nbsp;';
                else if ($amarr_sell > $min_buy_price)
                    $warnings .= '<span class="label label-qind-dontbuy" data-toggle="tooltip" data-placement="bottom" title="Min buy price: '.number_format(eve_ceiling($min_buy_price),2,'.',',').'">don&apos;t buy in Amarr</span>&nbsp;';
                else if ($jita_sell > $min_buy_price)
                    $warnings .= '<span class="label label-qind-dontbuy" data-toggle="tooltip" data-placement="bottom" title="Min buy price: '.number_format(eve_ceiling($min_buy_price),2,'.',',').'">don&apos;t buy in Jita</span>&nbsp;';
            }

            if (!is_null($ri4_market_quantity)&&!is_null($ri4_price))
            {
                $summary_market_price += $ri4_market_quantity * $ri4_price;
                $market_group_summary_market_price += $ri4_market_quantity * $ri4_price;
            }
            if (!is_null($packaged_volume))
            {
                $summary_market_volume += $ri4_market_quantity * $packaged_volume;
                $market_group_summary_market_volume += $ri4_market_quantity * $packaged_volume;
            }
            $summary_jita_sell += $ri4_market_quantity * $jita_sell;
            $summary_jita_buy += $ri4_market_quantity * $jita_buy;

            $market_group_summary_jita_sell += $ri4_market_quantity * $jita_sell;
            $market_group_summary_jita_buy += $ri4_market_quantity * $jita_buy;

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
?>
<tr<?php if ($ri4_sell_lvl==2) { ?> style="background: #e8e8e8;"<?php } ?>>
 <td><img class="icn32" src="<?=__get_img_src($tid,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
 <td><?=$nm?><?=get_clipboard_copy_button($nm)?><?=(!is_null($day_volume)&&$day_volume)?' <span style="background-color:#00fa9a">&nbsp;+ '.number_format($day_volume,0,'.',',').'&nbsp;</span>':''?><?='<br><span class="text-muted">'.$tid.'</span> '.$problems.$warnings.$industry?></td>

 <?php if (is_null($weekly_volume)) { ?><td></td><?php } else { ?>
 <td><?=number_format($weekly_volume,1,'.',',')?><br><mark><span style="font-size: smaller;"><?=number_format($order_volume,1,'.',',')?></span></mark></td>
 <?php } ?>

 <?php if (is_null($industrial_jobs) && is_null($present_in_assets) && is_null($blueprints_prepared)) { ?><td></td><?php } else { ?>
 <td><?=is_null($blueprints_invent)?'':'&asymp;'.$blueprints_invent.'<sup> inv</sup><br>'?>
     <?=is_null($blueprints_prepared)?'':$blueprints_prepared.'<sup> bp</sup><br>'?>
     <?=is_null($industrial_jobs)?'':$industrial_jobs.'<sup> job</sup><br>'?>
     <?=is_null($present_in_assets)?'':$present_in_assets.'<sup> stock</sup>'?></td>
 <?php } ?>

<?php
  // поле с информацией о наличии товара на рынке (текущие цены, текущее кол-во)
  if (is_null($ri4_price))
  {
    ?><td></td><?php
  }
  else
  {
    if ($interrupt_detected) { ?><td bgcolor="#e8c8c8"><?php } else { ?><td><?php }
    ?><?=number_format($ri4_price,2,'.',',')?><br><mark><?=number_format($ri4_market_quantity,0,'.',',')?></mark><?php
    if ($storage_quantity)
    {
      ?>&nbsp;<small><span style="background-color:#c7c7c7">&nbsp;+ <?=number_format($storage_quantity,0,'.',',')?>&nbsp;</span></small><?php
    }
    ?></td><?php
  }
  
  if (is_null($trade_hub_sell))
  {
    ?><td></td><?php
  }
  else
  {
    if ($interrupt_detected) { ?><td bgcolor="#e8c8c8"><?php } else { ?><td><?php }
    if ($ri4_price == $trade_hub_sell) { ?><mute><?php }
    ?><?=number_format($trade_hub_sell,2,'.',',')?><br><mark><?=number_format($trade_hub_sell_volume,0,'.',',')?></mark><?php
    if ($ri4_price == $trade_hub_sell) { ?></mute><?php }
    ?></td><?php
  }

  if (is_null($amarr_sell)) { ?><td></td><?php }
  else
  {
    ?><td align="right"><mute-sm><?=number_format($jita_buy,2,'.',',')?> ..</mute-sm> <?=$amarr_price_lower?'<mute>':''?><?=number_format($jita_sell,2,'.',',')?><?=$amarr_price_lower?'</mute>':''?><?php if (!is_null($trade_hub_import_price)) { ?><br><mark><small><?=number_format($trade_hub_import_price,2,'.',',')?></small></mark><?php } ?></td><?php
  }

  if (is_null($amarr_sell)) { ?><td></td><?php }
  else
  {
      ?><td align="right"><?=$jita_price_lower?'<mute>':''?><?=number_format($amarr_sell,2,'.',',')?><?=$jita_price_lower?'</mute>':''?></td><?php
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
    if (!is_null($curr_market_group) && $market_group_summary_market_price)
    {
        __dump_market_group_summary(
            $curr_market_group,
            $market_group_summary_market_price,
            $market_group_summary_market_volume,
            $market_group_summary_jita_sell,
            $market_group_summary_jita_buy
        );
    }
?>
</tbody>
<tfoot>
<tr class="qind-summary">
 <td colspan="<?=MARKET_TABLE_DEFAULT_order_volume_visible?3:2?>">Summary</td>
 <td><?=number_format($summary_market_price,0,'.',',').'<br>'.number_format($summary_market_volume,0,'.',',')?>m³</td>
 <td><?=number_format($summary_jita_sell,0,'.',',').'<br>'.number_format($summary_jita_buy,0,'.',',')?></td>
 <td colspan="<?=MARKET_TABLE_columns-5-(MARKET_TABLE_DEFAULT_order_volume_visible?0:1)?>"></td>
</tr>
</tfoot>
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


function __dump_querious_storage(&$storage, $trade_hub_system) { ?>
<h2><?=$trade_hub_system?> Storage</h2>
<table class="table table-condensed" style="padding:1px;font-size:smaller;" id="tblStock">
<thead>
 <tr>
  <th></th>
  <th>Items</th>
  <th style="text-align: right;">Quantity<br>in Storage</th>
  <th style="text-align: right;">RI4<br>Sell</th>
  <th style="text-align: right;"><?=$trade_hub_system?> Sell<br><mark>Quantity</mark></th>
  <th style="text-align: right;">Jita Buy..Sell<br><mark>Import Price</mark></th>
  <th style="text-align: right;">Amarr<br>Sell</th>
  <th style="text-align: right;">Universe<br>Price</th>
 </tr>
</thead>
<tbody>
<?php
    global $IMPORT_PRICE_TO_TRADE_HUB;

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
            $trade_hub_sell = $product['ps'];
            $trade_hub_sell_volume = $product['psv'];
            $packaged_volume = $product['pv'];
            $trade_hub_import_price = is_null($IMPORT_PRICE_TO_TRADE_HUB) ? null : ($packaged_volume * $IMPORT_PRICE_TO_TRADE_HUB);
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
 <?php if (is_null($trade_hub_sell)) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($trade_hub_sell,2,'.',',')?><br><mark><?=number_format($trade_hub_sell_volume,0,'.',',')?></mark></td>
 <?php } ?>
 <td align="right"><?=number_format($jita_buy,2,'.',',')?> .. <?=number_format($jita_sell,2,'.',',')?><?php if (!is_null($trade_hub_import_price)) { ?><br><mark><?=number_format($trade_hub_import_price,2,'.',',')?></mark><?php } ?></td>
 <td align="right"><?=number_format($amarr_sell,2,'.',',')?></td>
 <td align="right"><?=number_format($universe_price,2,'.',',')?></td>
</tr>
<?php
        }
?>
</tbody>
<tfoot>
<tr style="font-weight:bold;">
 <td colspan="5" align="right">Summary</td>
 <td align="right"><?=number_format($summary_jita_sell,0,'.',',').'<br>'.number_format($summary_jita_buy,0,'.',',')?></td>
 <td colspan="3"></td>
</tr>
</tfoot>
</table>
<?php
}



    //---
    $query = <<<EOD
select
  market.type_id as id,
  market.lvl as ri4s, -- RI4 sell level
  market_group.semantic_id as grp_id,
  market_group.name as grp,
  tid.sdet_type_name as name,
  tid.sdet_meta_group_id as meta,
  industry.sdebp_blueprint_type_id as bp_tid,
  bptid.sdet_type_name as bp_name,
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
  trade_hub.ethp_sell as ps, -- Nisuwa sell
  trade_hub.ethp_sell_volume as psv, -- Nisuwa sell volume
  jobs.qty as jq,
  coass.qty as aq,
  bprdy.qty as bpr,
  bpinv.qty as bpi
from
  qi.eve_sde_market_groups_semantic as market_group,
  ( select m.type_id, min(m.lvl) as lvl
    from (
      -- список транзакций по покупке/продаже имени корпораций или от имени избранных персонажей
      select ecwt_type_id as type_id, 0 as lvl
      from
        esi_corporation_wallet_journals j
          left outer join esi_corporation_wallet_transactions t on (ecwj_context_id = ecwt_transaction_id) -- (j.ecwj_reference_id = t.ecwt_journal_ref_id)
      where
        (ecwj_date > '2023-05-01') and
        (ecwj_context_id_type = 'market_transaction_id') and
        ( ( ecwj_corporation_id=any($1) and
            ecwt_location_id=$2 and not ecwt_is_buy ) or -- станка рынка
          ( ecwj_second_party_id=$3 and -- торговый персонаж,...
            ecwt_location_id<>$2 and ecwt_is_buy ) -- ..., который закупается не по месту продажи
        ) and
        ecwt_type_id is not null -- данные journal могут пока отсутствовать, а в transaction уже быть
      union
      -- список того, что корпорация продавала или продаёт
      select ecor_type_id, 1
      from esi_corporation_orders
      where
        not ecor_is_buy_order and
        (ecor_corporation_id=any($1)) and
        (ecor_location_id=$2)  -- станка рынка
      union
      -- список того, что выставлено в маркете (не нами)
      select ethp_type_id, 2
      from qi.esi_trade_hub_prices
      where $4=0 and ethp_location_id=$2  -- станка рынка
    ) m
    group by 1
  ) market
    -- сведения о предмете
    left outer join eve_sde_type_ids tid on (market.type_id = tid.sdet_type_id)
    -- сведения о возможности производства предмета
    left outer join eve_sde_blueprint_products as industry on (sdebp_product_id = market.type_id and sdebp_activity=1)
    left outer join eve_sde_type_ids bptid on (industry.sdebp_blueprint_type_id = tid.sdet_type_id)
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
        (ecor_corporation_id=any($1)) and
        (ecor_location_id=$2)  -- станка рынка
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
        (ecwt_corporation_id=any($1)) and
        (ecwt_location_id=$2)  -- станка рынка
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
        (ecor_corporation_id=any($1)) and
        (ecor_location_id=$2)  -- станка рынка
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
      where ethp_location_id=$2  -- станка рынка
    ) trade_hub on (market.type_id = trade_hub.ethp_type_id)
    -- производственные работы для этого товара
    left outer join (
      select ecj_product_type_id,sum(ecj_runs*sdebp_quantity) qty
      from esi_corporation_industry_jobs,eve_sde_blueprint_products
      where
        ecj_corporation_id=any($1) and ecj_status='active' and ecj_activity_id=1 and
        ecj_product_type_id=sdebp_product_id and sdebp_activity=1 and sdebp_blueprint_type_id=ecj_blueprint_type_id and
        ecj_blueprint_location_id in (select container_id from eve_ri4_manufacturing_containers where corporation_id=any($1))
      group by ecj_product_type_id
    ) jobs on (market.type_id = jobs.ecj_product_type_id)
    -- наличие товара в ассетах корпорации
    left outer join (
      select eca_type_id,sum(eca_quantity) qty
      from esi_corporation_assets
      where
        eca_corporation_id=any($1) and
        eca_location_id not in (select container_id from eve_ri4_personal_containers where corporation_id=any($1))
      group by eca_type_id
    ) coass on (market.type_id = coass.eca_type_id)
    -- чертежи в ассетах корпорации
    left outer join (
      select sdebp_product_id,sum(ecb_runs*sdebp_quantity) qty
      from esi_corporation_blueprints,eve_sde_blueprint_products
      where
        ecb_corporation_id=any($1) and ecb_quantity=-2 and sdebp_activity=1 and sdebp_blueprint_type_id=ecb_type_id and
        ecb_location_id not in (select container_id from eve_ri4_manufacturing_containers where corporation_id=any($1))
      group by sdebp_product_id
    ) bprdy on (market.type_id = bprdy.sdebp_product_id)
    -- чертежи, которые сейчас инвентятся
    left outer join (
      select
       --i.bp1id,
       --i.bp2id,
       i.pr3id,
       --(select sdet_type_name from eve_sde_type_ids where sdet_type_id=bp1id) bp1nm,
       --(select sdet_type_name from eve_sde_type_ids where sdet_type_id=bp2id) bp2nm,
       --(select sdet_type_name from eve_sde_type_ids where sdet_type_id=pr3id) pr3nm,
       i.qty
      from (
        select
         ecj_blueprint_type_id as bp1id,
         bp2.sdebp_product_id as bp2id,
         pr3.sdebp_product_id as pr3id,
         sum(round(ecj_runs*bp2.sdebp_quantity*ecj_probability)*pr3.sdebp_quantity) as qty -- без учёта декрипторов, огульное округление
        from esi_corporation_industry_jobs bp1
          left outer join eve_sde_blueprint_products as bp2 on (ecj_blueprint_type_id=bp2.sdebp_blueprint_type_id and bp2.sdebp_activity=8)
          left outer join eve_sde_blueprint_products as pr3 on (bp2.sdebp_product_id=pr3.sdebp_blueprint_type_id and pr3.sdebp_activity=1)
        where
          ecj_corporation_id=any($1) and ecj_status='active' and ecj_activity_id=8 and
          ecj_blueprint_location_id in (select container_id from eve_ri4_invent_containers where corporation_id=any($1))
        group by 1,2,3
      ) i
    ) bpinv on (market.type_id = bpinv.pr3id)
where
  market_group.id = tid.sdet_market_group_id and
  ($5=0 or market_group.semantic_id not in (
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
-- order by tid.sdet_packaged_volume desc
order by market_group.name, tid.sdet_type_name;
EOD;
    $params = array('{'.implode(',',$CORPORATION_IDs).'}', $TRADE_HUB_ID, $TRADER_ID, $SHOW_ONLY_RI4_SALES, $DO_NOT_SHOW_RAW_MATERIALS);
    $market_cursor = pg_query_params($conn, $query, $params)
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
  trade_hub.ethp_sell as ps, -- nisuwa sell
  trade_hub.ethp_sell_volume as psv, -- nisuwa sell volume
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
      where ethp_location_id=$2  -- станка рынка
    ) trade_hub on (hangar.eca_type_id = trade_hub.ethp_type_id)
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
          (ecor_corporation_id=any($1)) and
          (ecor_location_id=$2)  -- станка рынка
        group by 1
      ) o
    ) ri4_orders on (hangar.eca_type_id = ri4_orders.ecor_type_id)
where
  hangar.eca_location_id = 99999999 and hangar.eca_location_flag = 'CorpSAG4' and
  hangar.eca_location_type = 'item' and
  not exists (select box.eca_item_id from qi.esi_corporation_assets as box where box.eca_location_id = hangar.eca_item_id)
-- order by universe.price desc
order by tid.sdet_market_group_id, tid.sdet_type_name;
EOD;
    $params = array('{'.implode(',',$CORPORATION_IDs).'}', $TRADE_HUB_ID);
    $storage_cursor = pg_query_params($conn, $query, $params)
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
    ecwj_second_party_id=$1 -- торговый персонаж, который что-то где-то покупал за последние 2 недели
  group by 1, 2
) buy
order by 1, 2 desc;
EOD;
    $params = array($TRADE_HUB_ID);
    $purchase_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $purchase = pg_fetch_all($purchase_cursor);
    //---
    pg_close($conn);
?>


<nav class="navbar navbar-default">
 <div class="container-fluid">
  <div class="navbar-header">
   <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#bs-navbar-collapse" aria-expanded="false">
    <span class="sr-only">Toggle navigation</span>
    <span class="icon-bar"></span>
    <span class="icon-bar"></span>
    <span class="icon-bar"></span>
   </button>
   <a class="navbar-brand" data-target="#"><span class="glyphicon glyphicon-tasks" aria-hidden="true"></span></a>
  </div>

  <div class="collapse navbar-collapse" id="bs-navbar-collapse">
   <ul class="nav navbar-nav">
    <li class="dropdown">
     <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Настройки таблицы <span class="caret"></span></a>
      <ul class="dropdown-menu">
       <li><a data-target="#" role="button" id="btn-qind-showlabels"><span class="glyphicon glyphicon-star" aria-hidden="true"></span> Показывать цветные маркеры</a></li>
       <li><a data-target="#" role="button" id="btn-qind-hidednotbuylabels"><span class="glyphicon glyphicon-star" aria-hidden="true"></span> Не показывать don't buy маркеры</a></li>
       <li role="separator" class="divider"></li>
       <li><a data-target="#" role="button" id="btn-qind-showordervolumes"><span class="glyphicon glyphicon-star" aria-hidden="true"></span> Показывать объём сделок (неделя/ордер)</a></li>
       <li><a data-target="#" role="button" id="btn-qind-showindustryvolumes"><span class="glyphicon glyphicon-star" aria-hidden="true"></span> Показывать объём производства</a></li>
       <li role="separator" class="divider"></li>
       <li><a data-target="#" role="button" id="qind-btn-reset">Сбросить настройки</a></li>
      </ul>
    </li>
    <li class="dropdown">
     <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Фильтрация <span class="caret"></span></a>
      <ul class="dropdown-menu">
       <li><a data-target="#" role="button" class="qind-btn-filter" qind-group="all"><span class="glyphicon glyphicon-star" aria-hidden="true"></span> Все ордера</a></li>
       <li><a data-target="#" role="button" class="qind-btn-filter" qind-group="active"><span class="glyphicon glyphicon-star" aria-hidden="true"></span> Активные ордера</a></li>
       <li><a data-target="#" role="button" class="qind-btn-filter" qind-group="sold"><span class="glyphicon glyphicon-star" aria-hidden="true"></span> Всё продано</a></li>
       <li><a data-target="#" role="button" class="qind-btn-filter" qind-group="out-of-market"><span class="glyphicon glyphicon-star" aria-hidden="true"></span> Отсутствует на рынке</a></li>
       <li><a data-target="#" role="button" class="qind-btn-filter" qind-group="very-few"><span class="glyphicon glyphicon-star" aria-hidden="true"></span> Товар заканчивается</a></li>
       <li><a data-target="#" role="button" class="qind-btn-filter" qind-group="need-delivery"><span class="glyphicon glyphicon-star" aria-hidden="true"></span> Требуется доставка</a></li>
       <li role="separator" class="divider"></li>
       <li><a data-target="#" role="button" class="qind-btn-filter" qind-group="high-price"><span class="glyphicon glyphicon-star" aria-hidden="true"></span> Цена завышена</a></li>
       <li><a data-target="#" role="button" class="qind-btn-filter" qind-group="low-price"><span class="glyphicon glyphicon-star" aria-hidden="true"></span> Цена занижена</a></li>
       <li><a data-target="#" role="button" class="qind-btn-filter" qind-group="interrupt"><span class="glyphicon glyphicon-star" aria-hidden="true"></span> Обновить ордера (конкуренты)</a></li>
       <li role="separator" class="divider"></li>
       <li><a data-target="#" role="button" class="qind-btn-filter" qind-group="place-an-order"><span class="glyphicon glyphicon-star" aria-hidden="true"></span> Выставить на продажу (довоз)</a></li>
       <li role="separator" class="divider"></li>
       <li><a data-target="#" role="button" class="qind-btn-filter" qind-group="inv-blueprints"><span class="glyphicon glyphicon-star" aria-hidden="true"></span> Чертежи инвентятся</a></li>
       <li><a data-target="#" role="button" class="qind-btn-filter" qind-group="prep-blueprints"><span class="glyphicon glyphicon-star" aria-hidden="true"></span> Чертежи готовы (инвент)</a></li>
       <li><a data-target="#" role="button" class="qind-btn-filter" qind-group="industry-jobs"><span class="glyphicon glyphicon-star" aria-hidden="true"></span> Товар производится</a></li>
       <li><a data-target="#" role="button" class="qind-btn-filter" qind-group="in-assets"><span class="glyphicon glyphicon-star" aria-hidden="true"></span> Товар находится в ассетах</a></li>
     </ul>
    </li>
   </ul>
   <form class="navbar-form navbar-right">
    <label>Sort:&nbsp;</label>
    <div class="btn-group" role="group" aria-label="Sort">
     <button id="btnSortByName" type="button" class="btn btn-default active">Name</button>
    </div>
   </form>
  </div>
 </div>
</nav>


<div class="container-fluid">
<?php
    if ($trade_hub_status)
    {
      ?><p>Станция рынка: <span class="text-primary"><?=$trade_hub_status[0]['name']?></span><?=get_clipboard_copy_button($trade_hub_status[0]['name'])?><br>Время последней актуализации цен: <span class="text-primary"><?=is_null($trade_hub_status[0]['prc'])?'нет данных':$trade_hub_status[0]['prc'].' ET'?></span><br>Время последней актуализации ордеров: <span class="text-primary"><?=is_null($trade_hub_status[0]['ord'])?'нет данных':$trade_hub_status[0]['ord'].' ET'?></span><br>Время последней сделки: <span class="text-primary"><?=is_null($trade_hub_status[0]['tra'])?'нет данных':$trade_hub_status[0]['tra'].' ET'?></span></p><?php
    }
    __dump_trade_hub_links($market, $SORT, $GRPs, $T1, $T2, $T3, $FA, $RA, $SHOW_ONLY_RI4_SALES, $DO_NOT_SHOW_RAW_MATERIALS, $INDUSTRY_POSSIBLE);
    __dump_querious_market($market, $storage, $purchase, $trade_hub_system);
?>
<!-- --- --- --- -->
<hr>
<!-- --- --- --- -->
<div class="btn-group btn-group-toggle" data-toggle="buttons">
 <label class="btn btn-default qind-btn-stock" group="all"><input type="radio" name="options" autocomplete="off" checked>Показать</label>
 <label class="btn btn-default qind-btn-stock active" group="hide"><input type="radio" name="options" autocomplete="off">Скрыть</label>
</div>
<?php __dump_querious_storage($storage, $trade_hub_system); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>

<div class="modal fade" id="modalDetails" tabindex="-1" role="dialog" aria-labelledby="modalDetailsLabel">
 <div class="modal-dialog modal-lg" role="document">
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
<!-- -->
<hr>
<!-- -->
<div class="row">
  <div class="col-md-8">Объём в упакованном виде</div>
  <div class="col-md-4" align="right"><mark id="dtlsPackedVolume"></mark> m³</div>
</div>
<div class="row">
  <div class="col-md-8">Стоимость доставки</div>
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
<!-- -->
<hr>
<!-- -->
<div class="btn-group btn-group-toggle" data-toggle="buttons" packed_volume="" id="dtlsCalc">
 <label class="btn btn-default qind-btn-calc" price="" profit="<?=$DEFAULT_PROFIT?>" caption="Jita Sell +<?=$DEFAULT_PROFIT*100?>%" id="dtlsCalcJS10"><input type="radio" name="options" autocomplete="off" checked>Jita +<?=$DEFAULT_PROFIT*100?>%</label>
 <label class="btn btn-default qind-btn-calc" price="" profit="0.05" caption="Jita Sell +5%" id="dtlsCalcJS5"><input type="radio" name="options" autocomplete="off">Jita +5%</label>
 <label class="btn btn-default qind-btn-calc" price="" profit="<?=$DEFAULT_PROFIT+0.05?>" caption="Jita Sell +<?=($DEFAULT_PROFIT+0.05)*100?>%" id="dtlsCalcJS15"><input type="radio" name="options" autocomplete="off">Jita +<?=($DEFAULT_PROFIT+0.05)*100?>%</label>
 <label class="btn btn-default qind-btn-calc" price="" profit="<?=$DEFAULT_PROFIT?>" caption="Amarr Sell +<?=$DEFAULT_PROFIT*100?>%" id="dtlsCalcAS10"><input type="radio" name="options" autocomplete="off">Amarr +<?=$DEFAULT_PROFIT*100?>%</label>
 <label class="btn btn-default qind-btn-calc active" price="" profit="<?=$DEFAULT_PROFIT?>" caption="от цены закупа +<?=$DEFAULT_PROFIT*100?>%" id="dtlsCalcUP10"><input type="radio" name="options" autocomplete="off">Закуп +<?=$DEFAULT_PROFIT*100?>%</label>
</div>
<div class="row">
  <div class="col-md-8">Цена закупа</div>
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
  <div class="col-md-7">плюс <?=$BROKERS_FEE*100.0?>% комиссия и <?=$TRADE_HUB_TAX*100.0?>% налог</div>
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
<hr>
<!-- -->
<div class="row">
 <div class="col-md-5">
  Текущие ордера в маркете
<style type="text/css">
.tblMarketOrders-wrapper { max-height: 300px; overflow: auto; }
.tblMarketOrders-wrapper table { padding:1px; font-size: x-small; width: 100%; }
.tblMarketOrders-wrapper thead th { position: sticky; top: 0; z-index: 1; background-color: #fff; text-align:center; }
.tblMarketOrders-wrapper tbody tr td:nth-child(1) { text-align: right; font-weight: bold; }
.tblMarketOrders-wrapper tbody tr td:nth-child(2) { text-align: right; }
.tblMarketOrders-wrapper tbody tr td:nth-child(3) { text-align: center; }
.tblMarketOrders-wrapper tbody tr td:nth-child(4) { text-align: left; }
.tblMarketOrders-wrapper tbody tr td:nth-child(5) { text-align: left; font-weight: bold; }
</style>
<div class="tblMarketOrders-wrapper">
 <table id="tblMarketOrders">
  <thead>
   <tr>
    <th style="width:30%;" colspan="2">Покупка</th>
    <th style="width:40%;">Цена,&nbsp;ISK</th>
    <th style="width:30%;" colspan="2">Продажа</th>
   </tr>
  </thead>
  <tbody>
  </tbody>
 </table>
 <form id="frmMarketOrders">
  <input type="hidden" name="corp" readonly value="<?=implode(',',$CORPORATION_IDs)?>">
  <input type="hidden" name="hub" readonly value="<?=$TRADE_HUB_ID?>">
  <input type="hidden" name="tid" readonly>
 </form>
</div>
<!-- -->
 </div>
 <div class="col-md-7">
  Хронология изменений ордеров
<!-- -->
<style type="text/css">
.tblMarketHistory-wrapper { max-height: 300px; overflow: auto; }
.tblMarketHistory-wrapper table { padding:1px; font-size: x-small; width: 100%; }
.tblMarketHistory-wrapper thead th { position: sticky; top: 0; z-index: 1; background-color: #fff; text-align:center; }
.tblMarketHistory-wrapper tbody tr td:nth-child(1) { text-align: left; }
.tblMarketHistory-wrapper tbody tr td:nth-child(2) { text-align: right; }
.tblMarketHistory-wrapper tbody tr td:nth-child(3) { text-align: center; }
.tblMarketHistory-wrapper tbody tr td:nth-child(4) { text-align: left; }
.tblMarketHistory-wrapper tbody tr td:nth-child(5) { text-align: right; }
.tblMarketHistory-wrapper tbody tr td:nth-child(6) { text-align: right; }
</style>
<div class="tblMarketHistory-wrapper">
 <table id="tblMarketHistory">
  <thead>
   <tr>
    <th style="width:21%;" colspan="2">Покупка</th>
    <th style="width:28%;">Цена,&nbsp;ISK</th>
    <th style="width:21%;" colspan="2">Продажа</th>
    <th style="width:30%;">Длительность ордера</th>
   </tr>
  </thead>
  <tbody>
  </tbody>
 </table>
 <form id="frmMarketHistory">
  <input type="hidden" name="corp" readonly value="<?=implode(',',$CORPORATION_IDs)?>">
  <input type="hidden" name="hub" readonly value="<?=$TRADE_HUB_ID?>">
  <input type="hidden" name="tid" readonly>
 </form>
</div>
 </div>
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
var g_import_price_to_trade_hub = <?=is_null($IMPORT_PRICE_TO_TRADE_HUB)?0:$IMPORT_PRICE_TO_TRADE_HUB?>;
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
            //$import_price_to_trade_hub = is_null($IMPORT_PRICE_TO_TRADE_HUB) ? null : ($packaged_volume * $IMPORT_PRICE_TO_TRADE_HUB);
            $jita_sell = $product['js'];
            $jita_buy = $product['jb'];
            $amarr_sell = $product['as'];
            //$jita_price_lower = $jita_sell < $amarr_sell;
            //$amarr_price_lower = $amarr_sell < $jita_sell;
            $universe_price = $product['up'];
            //$ri4_price = $product['mp'];
            //$jita_purchase_and_import_price = $jita_sell + $import_price_to_trade_hub; // то, за сколько будем продавать: закуп + импорт
            //$markup = $jita_purchase_and_import_price * $TAX_AND_FEE; // комиссия считается от суммы закупа и транспортировки
            //$jita_10_price = eve_ceiling($jita_purchase_and_import_price * (1.0+$DEFAULT_PROFIT+$TAX_AND_FEE)); // Jita +10% Price
            //$jita_10_profit = $jita_10_price - $jita_purchase_and_import_price - $markup;
            //$trade_hub_sell = $product['ps'];
            //$trade_hub_sell_volume = $product['psv'];

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
      else if (show_group == 'active')
        show = (0 == tr.find('td').eq(1).find('span.label-qind-noordersreal').length) &&
               (0 == tr.find('td').eq(1).find('span.label-qind-noorders').length);
      else if (show_group == 'sold')
        show = tr.find('td').eq(1).find('span.label-qind-noordersreal').length ||
               tr.find('td').eq(1).find('span.label-qind-noorders').length;
      else if (show_group == 'out-of-market')
        show = tr.find('td').eq(1).find('span.label-qind-noordersreal').length;
      else if (show_group == 'low-price')
        show = tr.find('td').eq(1).find('span.label-qind-lowprice').length;
      else if (show_group == 'high-price')
        show = tr.find('td').eq(1).find('span.label-qind-highprice').length;
      else if (show_group == 'very-few')
        show = tr.find('td').eq(1).find('span.label-qind-veryfew').length;
      else if (show_group == 'need-delivery')
        show = tr.find('td').eq(1).find('span.label-qind-needdelivery').length;
      else if (show_group == 'place-an-order')
        show = tr.find('td').eq(1).find('span.label-qind-placeanorder').length;
      else if (show_group == 'interrupt')
        show = tr.find('td').eq(1).find('span.label-qind-interrupt').length;
      else if (show_group == 'prep-blueprints')
        show = tr.find('td').eq(1).find('span.label-qind-prepblueprints').length;
      else if (show_group == 'inv-blueprints')
        show = tr.find('td').eq(1).find('span.label-qind-invblueprints').length;
      else if (show_group == 'industry-jobs')
        show = tr.find('td').eq(1).find('span.label-qind-industryjobs').length;
      else if (show_group == 'in-assets')
        show = tr.find('td').eq(1).find('span.label-qind-inassets').length;
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
    var import_price = take_import * g_import_price_to_trade_hub * $('#dtlsCalc').attr('packed_volume');
    var price_purchase = 1.0 * btn.attr('price');
    var price_profit = price_purchase * (1.0+1.0*btn.attr('profit'));
    var price_profit_import = price_profit + import_price;
    var price_profit_import_markup = price_profit_import * <?=$TRADE_HUB_TAX+$BROKERS_FEE?>;
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
  function rebuildLabelsVisibility() {
   var turn_off=isMenuActivated($('#btn-qind-showlabels'));
   var hide_dontbuy=isMenuActivated($('#btn-qind-hidednotbuylabels'));
   $('*[class*=label-qind-]').each(function(){
    if(turn_off) {
     if (hide_dontbuy && $(this).hasClass('label-qind-dontbuy'))
      $(this).addClass('hidden');
     else
      $(this).removeClass('hidden');
    }
    else
     $(this).addClass('hidden');
   });
  }
//-----------
// работа с пунктами меню
//-----------
function isMenuActivated(btn){
 return btn.hasClass('qind-btn-active');
}
function toggleMenuMarker(btn, active){
 if(active){
  btn.addClass('qind-btn-active');
  btn.find('span').removeClass('hidden');
 }else{
  btn.removeClass('qind-btn-active');
  btn.find('span').addClass('hidden');
 }
}
function rebuildFilterMenu(active_grp) {
 $('a.qind-btn-filter').each(function() {
  if(active_grp==$(this).attr('qind-group')){
   $(this).addClass('qind-btn-active');
   toggleMenuMarker($(this),true);
  }else{
   $(this).removeClass('qind-btn-active');
   toggleMenuMarker($(this),false);
  }
 })
}
//-----------
// обработчики нажатий на кнопки
//-----------
$('a.qind-btn-filter').on('click', function () {
 if(!isMenuActivated($(this))){// включается
  var grp=$(this).attr('qind-group');
  rebuildMarket(grp);
  rebuildFilterMenu(grp);
 }
});
//-----------
$('#btn-qind-showlabels').on('click', function () {
 var turn_off=!isMenuActivated($(this));
 toggleMenuMarker($(this),turn_off);
 rebuildLabelsVisibility();
});
//-----------
$('#btn-qind-hidednotbuylabels').on('click', function () {
 var hide_dontbuy=!isMenuActivated($(this));
 toggleMenuMarker($(this),hide_dontbuy);
 rebuildLabelsVisibility();
});
//-----------
$('#btn-qind-showordervolumes').on('click', function () {
 var turn_on=!isMenuActivated($(this));
 toggleMenuMarker($(this),turn_on);
 $('#tblMarket thead tr th:nth-child(3)').each(function() {
  turn_on ? $(this).css('display','table-cell') : $(this).css('display','none');
 });
 $('#tblMarket tbody tr td:nth-child(3)').each(function() {
  turn_on ? $(this).css('display','table-cell') : $(this).css('display','none');
 });
 // двигаем слово summary на место колонки, которую удалили
 var col4_on=!isMenuActivated($('#btn-qind-showindustryvolumes'));
 $('tr.qind-summary td:nth-child(1)').each(function() {
  $(this).attr('colspan',(turn_on?3:2)+(col4_on?1:0));
 });
});
//-----------
$('#btn-qind-showindustryvolumes').on('click', function () {
 var turn_on=!isMenuActivated($(this));
 toggleMenuMarker($(this),turn_on);
 $('#tblMarket thead tr th:nth-child(4)').each(function() {
  turn_on ? $(this).css('display','table-cell') : $(this).css('display','none');
 });
 $('#tblMarket tbody tr td:nth-child(4)').each(function() {
  turn_on ? $(this).css('display','table-cell') : $(this).css('display','none');
 });
 // двигаем слово summary на место колонки, которую удалили
 var col3_on=!isMenuActivated($('#btn-qind-showordervolumes'));
 $('tr.qind-summary td:nth-child(1)').each(function() {
  $(this).attr('colspan',(turn_on?3:2)+(col3_on?1:0));
 });
});
//-----------
// настройки по умолчанию (те, что автоматически действуют после загрузки страницы)
//-----------
$(document).ready(function(){
 rebuildFilterMenu('all');
 toggleMenuMarker($('#btn-qind-showlabels'), true);
 toggleMenuMarker($('#btn-qind-hidednotbuylabels'), true);
 toggleMenuMarker($('#btn-qind-showordervolumes'), <?=MARKET_TABLE_DEFAULT_order_volume_visible?1:0?>);
 toggleMenuMarker($('#btn-qind-showindustryvolumes'), <?=MARKET_TABLE_DEFAULT_industry_volume_visible?1:0?>);
 rebuildLabelsVisibility();
 




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
      //- отправка запроса на формирование таблицы текущий маркет-ордеров
      $("#tblMarketOrders tbody").html('');
      var frm = $("#frmMarketOrders");
      frm.find("input[name='tid']").val(tid);
      frm.submit();
      //- отправка запроса на формирование таблицы текущий маркет-ордеров
      $("#tblMarketHistory tbody").html('');
      /*var*/ frm = $("#frmMarketHistory");
      frm.find("input[name='tid']").val(tid);
      frm.submit();
      //- инициализация автокалькулятора
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
      if (g_import_price_to_trade_hub) {
        $('#dtlsImportPrice').html(numLikeEve(Math.ceil10(market_type[2]*g_import_price_to_trade_hub, -2).toFixed(2)));
      } else {
        $('#dtlsImportPrice').html('');
      }
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

$("#frmMarketOrders").on("submit", function(e){
 e.preventDefault();
 $.ajax({
  url: '/tools/etho_ecor.php',
  method: 'post',
  dataType: 'json',
  data: $(this).serialize(),
  success: function(data){
   var tbody = '';
   $(data).each(function(i,row) {
    var tr = "";
    var corp_remain = (row.corp === undefined)?'':row.corp;
    var buy = row.sell === undefined;
    var bg = (buy?'#ff8080':'#80ff80') + ((row.corp === undefined)?'80':'');
    if (buy)
     tr = "<tr style='background:"+bg+"'><td>"+corp_remain+"</td><td>"+row.volume+"</td><td>"+row.buy+"</td><td></td><td></td></tr>";
    else
     tr = "<tr style='background:"+bg+"'><td></td><td></td><td>"+row.sell+"</td><td>"+row.volume+"</td><td>"+corp_remain+"</td></tr>";
    tbody += tr;
   });
   var tbl = $("#tblMarketOrders tbody");
   tbl.html(tbody);
   <?php /* как дождаться прорисовки tbody?!
   $("#tblMarketOrders").parent().scrollTop(0);
   //-- scroll
   var rows = $("#tblMarketOrders thead tr");
   if (!(rows === undefined) && (rows.length == 1)) { // на всякий случай
     var tbl_head_px = rows[0].offsetHeight;
     rows = $("#tblMarketOrders tbody tr");
     if (!(rows === undefined) && (rows.length > 0)) { // вдруг содержимое таблицы пусто?
       var px = rows[1].offsetHeight; // высота строки
       var tbody_px = 300 - tbl_head_px;
       if ((px > 0) && ((tbody_px / rows.length) < px)) { // если вся таблица не влезла в tblMarketOrders-wrapper=300px, то скроллируем её к середине
         var split = row_buy_idx * px;
         alert(tbody_px + ' ' + px + ' ' + ' ' + rows.length + ' ' + split);
         if ((tbody_px/2) < split) {
   $("#tblMarketOrders").parent().scrollTop(split);
         }
       }
     }
   }
   */ ?>
  },
  error: function (jqXHR, exception) {
   if (jqXHR.status === 0) alert('Not connect. Verify Network.');
   else if (jqXHR.status == 404) alert('Requested page not found (404).');
   else if (jqXHR.status == 500) alert('Internal Server Error (500).');
   else if (exception === 'parsererror') alert('Requested JSON parse failed.'); // некорректный ввод post-params => return в .php, нет данных
   else if (exception === 'timeout') alert('Time out error.'); // сервер завис?
   else if (exception === 'abort') alert('Ajax request aborted.');
   else alert('Uncaught Error. ' + jqXHR.responseText);
  }
 });
});

$("#frmMarketHistory").on("submit", function(e){
 e.preventDefault();
 $.ajax({
  url: '/tools/ethh.php',
  method: 'post',
  dataType: 'json',
  data: $(this).serialize(),
  success: function(data){
   var tbody = '';
   $(data).each(function(i,row) {
    tr = '';
    if (!(row.date == undefined)) {
      tr = "<tr style='background-color:#f5f5f5;'><td colspan='7' style='padding-left:10px;'><b>"+row.date+"</b></td></tr>";
    }
    var buy = row.sell === undefined;
    var bg = (buy?'#ff8080':'#80ff80') + ((row.corp === undefined)?'80':'');
    var volume = '';
    if (row.closed) {
      if (row.volume == row.total)
        volume = row.volume;
      else
        volume = row.volume+'&hellip;<span style="color:gray;">'+row.total+'</span>';
    } else if (row.volume > 0)
      volume = row.volume;
    var closed = row.closed?'<span class="glyphicon glyphicon-remove" aria-hidden="true"></span>':'';
    if (buy)
     tr += "<tr style='background:"+bg+"'><td>"+closed+"</td><td>"+volume+"</td><td>"+row.buy+"</td><td></td><td></td><td>"+row.duration+"</td></tr>";
    else
     tr += "<tr style='background:"+bg+"'><td></td><td></td><td>"+row.sell+"</td><td>"+volume+"</td><td>"+closed+"</td><td>"+row.duration+"</td></tr>";
    tbody += tr;
   });
   var tbl = $("#tblMarketHistory tbody");
   tbl.html(tbody);
  },
  error: function (jqXHR, exception) {
   if (jqXHR.status === 0) alert('Not connect. Verify Network.');
   else if (jqXHR.status == 404) alert('Requested page not found (404).');
   else if (jqXHR.status == 500) alert('Internal Server Error (500).');
   else if (exception === 'parsererror') alert('Requested JSON parse failed.'); // некорректный ввод post-params => return в .php, нет данных
   else if (exception === 'timeout') alert('Time out error.'); // сервер завис?
   else if (exception === 'abort') alert('Ajax request aborted.');
   else alert('Uncaught Error. ' + jqXHR.responseText);
  }
 });
});
</script>
<?php __dump_copy_to_clipboard_javascript() ?>
