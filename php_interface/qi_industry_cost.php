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
            $jita_sell = $product['js'];
            $jita_buy = $product['jb'];
            $amarr_sell = $product['as'];
            $amarr_buy = $product['ab'];
            $jita_materials_cost = $product['jsmp'];
            $amarr_materials_cost = $product['asmp'];

            if ($prev_market_group != $market_group)
            {
                $prev_market_group = $market_group;
                ?><tr><td class="active" colspan="6"><strong><?=$market_group?></strong></td></tr><?php
            }
?>
<tr>
 <td><img class="icn32" src="<?=__get_img_src($tid,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
 <td><?=$nm?><?=get_clipboard_copy_button($nm)?><br><span class="text-muted"><?=$tid?> / <?=$blueprint_tid?></span></td>
<?php
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



    __dump_header("Industry Cost", FS_RESOURCES);
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
  amarr.ethp_buy as ab
from
  -- продукты производства
  qi.eve_sde_blueprint_products as product
    -- сведения о чертеже (должен быть published)
    left outer join qi.eve_sde_type_ids product_bp on (product.sdebp_blueprint_type_id = product_bp.sdet_type_id)
    -- цены на продукт производства в жите прямо сейчас
    left outer join (
      select ethp_type_id, ethp_sell, ethp_buy
      from qi.esi_trade_hub_prices
      where ethp_location_id = 60003760
    ) jita on (product.sdebp_product_id = jita.ethp_type_id)
    -- цены на продукт производства в жите прямо сейчас
    left outer join (
      select ethp_type_id, ethp_sell, ethp_buy
      from qi.esi_trade_hub_prices
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
          from qi.esi_trade_hub_prices
          where ethp_location_id = 60003760
        ) jita on (m.sdebm_material_id = jita.ethp_type_id)
        -- цены на материалы в жите прямо сейчас
        left outer join (
          select ethp_type_id, ethp_sell
          from qi.esi_trade_hub_prices
          where ethp_location_id = 60008494
        ) amarr on (m.sdebm_material_id = amarr.ethp_type_id)
    where
      --m.sdebm_blueprint_type_id=42883 and
      m.sdebm_activity = 1
    group by m.sdebm_blueprint_type_id
  ) as cost
where
  product.sdebp_blueprint_type_id = cost.sdebm_blueprint_type_id and
  product.sdebp_activity = 1 and
  product_bp.sdet_published and 
  tid.sdet_type_id = product.sdebp_product_id and
  tid.sdet_published and
  market_group.id = tid.sdet_market_group_id
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
