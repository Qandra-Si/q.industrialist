<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include_once '.settings.php';

const SHOW_ONLY_RI4_SALES_DEFAULT = 1;
const DO_NOT_SHOW_RAW_MATERIALS_DEFAULT = 1;
const SHOW_JITA_PRICE_INCLUDE_OURS_DEFAULT = 1;

$SHOW_ONLY_RI4_SALES = SHOW_ONLY_RI4_SALES_DEFAULT;
$DO_NOT_SHOW_RAW_MATERIALS = DO_NOT_SHOW_RAW_MATERIALS_DEFAULT;
$SHOW_JITA_PRICE_INCLUDE_OURS = SHOW_JITA_PRICE_INCLUDE_OURS_DEFAULT;

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


__dump_header("Market Hubs", FS_RESOURCES);
?>
<div class="container-fluid">
<?php
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");

    //---
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
order by h.mh_archive, s.forbidden;
EOD;
    $params = array();
    $market_hubs_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $market_hubs = pg_fetch_all($market_hubs_cursor);
    echo "market_hubs[0] = "; var_dump($market_hubs[0]); echo "<hr>";
    echo "count(market_hubs) = "; var_dump(count($market_hubs)); echo "<hr>";

    //---
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
    echo "hub_ids = "; var_dump($hub_ids); echo "<hr>";
    echo "trader_corp_ids = "; var_dump($trader_corp_ids); echo "<hr>";

    //---
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
    $groups_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $groups = pg_fetch_all($groups_cursor);
    echo "groups = "; var_dump($groups); echo "<hr>";
    //---
    $grp_ids = array();
    foreach ($groups as ["id" => $id, "grp" => $name]) $grp_ids[] = get_numeric($id);
    echo "grp_ids = "; var_dump($grp_ids); echo "<hr>";

    //---
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
    echo "jita_market[0] = "; var_dump($jita_market[0]); echo "<hr>";
    echo "count(jita_market) = ".count($jita_market)."<hr>";

    //---
    $query = <<<EOD
select
 --sell_orders.corp_id,
 sell_orders.hub_id as hub, -- hub id
 sell_orders.type_id as id, -- type_id
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
    echo "sale_orders[0] = "; var_dump($sale_orders[0]); echo "<hr>";
    echo "count(sale_orders) = ".count($sale_orders)."<hr>";

    //---
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
    echo "isotopes = "; var_dump($isotopes); echo "<hr>";
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
    echo "isotopes_price = "; var_dump($isotopes_price); echo "<hr>";
?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>

<?php __dump_copy_to_clipboard_javascript() ?>
