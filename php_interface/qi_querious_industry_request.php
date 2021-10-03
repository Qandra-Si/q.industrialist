<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include_once '.settings.php';
?>

<?php function __dump_industry_cost(&$industry_cost) { ?>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th></th>
  <th width="100%">Items</th>
  <th style="text-align: right;">Weekly<br>Volume</th>
  <th style="text-align: right;">Jita Materials<br>Cost</th>
  <th style="text-align: right;">Jita Sell<br>Jita Buy</th>
  <th style="text-align: right;">Amarr Materials<br>Cost</th>
  <th style="text-align: right;">Amarr Sell<br>Amarr Buy</th>
 </tr>
</thead>
<tbody>
<?php
    $prev_market_group = null;
    if ($industry_cost)
        foreach ($industry_cost as &$product)
        {
            $tid = $product['id'];
            $blueprint_tid = $product['bp_id'];
            $market_group = $product['grp'];
            $nm = $product['name'];
            $weekly_volume = $product['wv'];
            $jita_sell = $product['js'];
            $jita_buy = $product['jb'];
            $amarr_sell = $product['as'];
            $amarr_buy = $product['ab'];
            $jita_materials_cost = $product['jsmp'];
            $amarr_materials_cost = $product['asmp'];

            if ($prev_market_group != $market_group)
            {
                $prev_market_group = $market_group;
                ?><tr><td class="active" colspan="7"><strong><?=$market_group?></strong></td></tr><?php
            }
?>
<tr>
 <td><img class="icn32" src="<?=__get_img_src($tid,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
 <td><?=$nm?><?=get_clipboard_copy_button($nm)?><br><span class="text-muted"><?=$tid?> / <?=$blueprint_tid?></span></td>
<?php
    if (is_null($weekly_volume))
    {
        ?><td></td><?php
    }
    else
    {
        ?><td align="right"><?=number_format($weekly_volume,1,'.',',')?></td><?php
    }

    if (is_null($jita_materials_cost))
    {
        ?><td></td><?php
    }
    else
    {
        ?><td align="right"><?=number_format($jita_materials_cost,2,'.',',')?></td><?php
    }

    if (is_null($jita_sell))
    {
        ?><td></td><?php
    }
    else
    {
        ?><td align="right"><?=number_format($jita_sell,2,'.',',')?><br><?=number_format($jita_buy,2,'.',',')?></td><?php
    }

    if (is_null($amarr_materials_cost))
    {
        ?><td></td><?php
    }
    else
    {
        ?><td align="right"><?=number_format($amarr_materials_cost,2,'.',',')?></td><?php
    }

    if (is_null($amarr_sell))
    {
        ?><td></td><?php
    }
    else
    {
        ?><td align="right"><?=number_format($amarr_sell,2,'.',',')?><br><?=number_format($amarr_buy,2,'.',',')?></td><?php
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



    __dump_header("Querious Industry Request", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
select
  product.sdebp_product_id as id,
  cost.sdebm_blueprint_type_id as bp_id,
  market_group.name as grp,
  tid.sdet_type_name as name,
  round((cost.jsmp/product.sdebp_quantity)::numeric, 2) as jsmp,
  round((cost.asmp/product.sdebp_quantity)::numeric, 2) as asmp,
  jita.ethp_sell as js,
  jita.ethp_buy as jb,
  amarr.ethp_sell as as,
  amarr.ethp_buy as ab,
  case
    when (weeks_passed.volume_sell=0) or (weeks_passed.diff<0.14) then null
    when (weeks_passed.diff < 1.14) then weeks_passed.volume_sell
    else round(weeks_passed.volume_sell/weeks_passed.diff,1)
  end as wv -- weekly volume
from
  -- продукты производства
  qi.eve_sde_blueprint_products as product
    -- цены на продукт производства в жите прямо сейчас
    left outer join (
      select ethp_type_id, ethp_sell, ethp_buy
      from esi_trade_hub_prices
      where ethp_location_id = 60003760
    ) jita on (product.sdebp_product_id = jita.ethp_type_id)
    -- цены на продукт производства в жите прямо сейчас
    left outer join (
      select ethp_type_id, ethp_sell, ethp_buy
      from esi_trade_hub_prices
      where ethp_location_id = 60008494
    ) amarr on (product.sdebp_product_id = amarr.ethp_type_id),
  -- сведения о предмете
  qi.eve_sde_type_ids as tid,
  -- сведения о market-группе предмета
  qi.eve_sde_market_groups_semantic as market_group,
  -- расчёт стоимости материалов в постройке продукта
  ( select
      m.sdebm_blueprint_type_id,
      -- m.sdebm_material_id,
      -- m.sdebm_quantity,
      sum(m.sdebm_quantity * jita.ethp_sell) as jsmp, -- jita' sell materials price
      sum(m.sdebm_quantity * amarr.ethp_sell) as asmp -- amarr' sell materials price
    from
      qi.eve_sde_blueprint_materials m
        -- цены на материалы в жите прямо сейчас
        left outer join (
          select ethp_type_id, ethp_sell
          from esi_trade_hub_prices
          where ethp_location_id = 60003760
        ) jita on (m.sdebm_material_id = jita.ethp_type_id)
        -- цены на материалы в жите прямо сейчас
        left outer join (
          select ethp_type_id, ethp_sell
          from esi_trade_hub_prices
          where ethp_location_id = 60008494
        ) amarr on (m.sdebm_material_id = amarr.ethp_type_id)
    where
      --m.sdebm_blueprint_type_id=42883 and
      m.sdebm_activity = 1
    group by m.sdebm_blueprint_type_id
  ) as cost,
  -- предметы, выставленные на продажу
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
  ) querious
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
    ) weeks_passed on (querious.type_id = weeks_passed.ecor_type_id)
where
  querious.type_id = product.sdebp_product_id and
  product.sdebp_blueprint_type_id = cost.sdebm_blueprint_type_id and
  product.sdebp_activity = 1 and
  tid.sdet_type_id = product.sdebp_product_id and
  market_group.id = tid.sdet_market_group_id and
  market_group.semantic_id not in (
    19, -- Trade Goods
    499, -- Advanced Moon Materials
    500, -- Processed Moon Materials
    501, -- Raw Moon Materials
    1031, -- Raw Materials
    1035, -- Components
    1332, -- Planetary Materials
    1857, -- Minerals
    1858, -- Booster Materials
    1860, -- Polymer Materials
    1861, -- Salvage Materials
    1872, -- Research Equipment
    2767 -- Molecular-Forged Materials
  )
order by market_group.name, tid.sdet_type_name;
EOD;
    $industry_cost_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $industry_cost = pg_fetch_all($industry_cost_cursor);
    //---
    pg_close($conn);
?>

<div class="container-fluid">
<?php __dump_industry_cost($industry_cost); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>
