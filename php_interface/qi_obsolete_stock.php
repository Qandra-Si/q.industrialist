<?php
include 'qi_render_html.php';
include_once '.settings.php';

function get_numeric($val) {
    return is_numeric($val) ? ($val + 0) : 0;
}
?>

<?php function __dump_obsolete_stock($stock) { ?>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th></th>
  <th>Material</th>
  <th style="text-align: right;">Quantity</th>
  <th style="text-align: right;">Universe<br>Price</th>
  <th style="text-align: right;">Jita Sell<br>Jita Buy</th>
  <th style="text-align: right;">Since</th>
  <th style="text-align: right;">Blueprint<br>Variations</th>
  <th style="text-align: right;">Used in Jobs<br>Last Using</th>
  <th style="text-align: right;">Last 1<br>Month Used</th>
  <th style="text-align: right;">Last 2<br>Month Used</th>
  <th style="text-align: right;">Last 3<br>Month Used</th>
  <th style="text-align: right;">Last 4<br>Month Used</th>
 </tr>
</thead>
<tbody>
<?php
    foreach ($stock as $material)
    {
        $tid = $material['id'];
        $nm = $material['name'];
        $quantity = $material['q'];
        $universe_avg_price = $material['uap'];
        $jita_sell = $material['js'];
        $jita_buy = $material['jb'];
        $lie_up_since = $material['s'];
        $blueprint_variations = $material['bv'];
        $using_in_jobs = $material['uj'];
        $last_using = $material['lu'];
        $last_1_month_using = $material['m1'];
        $last_2_month_using = $material['m2'];
        $last_3_month_using = $material['m3'];
        $last_4_month_using = $material['m4'];
?>
<tr>
 <td><img class="icn32" src="<?=__get_img_src($tid,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
 <td><?=$nm.'<br><span class="text-muted">'.$tid.'</span> '.$problems.$warnings?></td>
 <td align="right"><?=number_format($quantity,0,'.',',')?></td>
 <td align="right"><?=number_format($universe_avg_price,0,'.',',')?></td>
 <td align="right"><?=number_format($jita_sell,0,'.',',').'<br>'.number_format($jita_buy,0,'.',',')?></td>
 <td align="right"><?=$lie_up_since?></td>
 <?php if (is_null($blueprint_variations) || !$blueprint_variations) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($blueprint_variations,0,'.',',')?></td>
 <?php } ?>
 <?php if (is_null($using_in_jobs) || !$using_in_jobs) { ?><td></td><?php } else { ?>
  <td align="right"><?=number_format($using_in_jobs,0,'.',',')?><?=(!is_null($last_using))?'<br>'.$last_using:''?></td>
 <?php } ?>
 <?php if (is_null($last_1_month_using) || !$last_1_month_using) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($last_1_month_using,0,'.',',')?></td>
 <?php } ?>
 <?php if (is_null($last_2_month_using) || !$last_2_month_using) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($last_2_month_using,0,'.',',')?></td>
 <?php } ?>
 <?php if (is_null($last_3_month_using) || !$last_3_month_using) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($last_3_month_using,0,'.',',')?></td>
 <?php } ?>
 <?php if (is_null($last_4_month_using) || !$last_4_month_using) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($last_4_month_using,0,'.',',')?></td>
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
    $stock_location_id = 1036612408249;
    if (isset($_GET['stock'])) {
        $_get_id = htmlentities($_GET['stock']);
        if (is_numeric($_get_id))
            $stock_location_id = get_numeric($_get_id);
    }

    __dump_header("Obsolete Stock", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query =
    $query = <<<EOD
select
  stock.type_id as id,
  tid.sdet_type_name as name,
  stock.quantity as q, -- quantity
  ceil(universe.price * stock.quantity) as uap, -- universe avg price
  ceil(jita.sell * stock.quantity) as js, -- jita sell
  ceil(jita.buy * stock.quantity) as jb, -- jita buy
  stock.since as s, -- lie up since
  materials_using.variations as bv, -- blueprint variations
  materials_using.jobs_times as uj, -- using in jobs
  materials_using.last_using as lu, -- last using
  materials_using.using_last_1month as m1, -- last 1 month using
  materials_using.using_last_2month as m2, -- last 2 month using
  materials_using.using_last_3month as m3, -- last 3 month using
  materials_using.using_last_4month as m4 -- last 4 month using
from
  -- содержимое коробки ..stock ALL на Сотие
  ( select
      eca_type_id as type_id,
      sum(eca_quantity) as quantity,
      max(eca_created_at::date) as since
    from qi.esi_corporation_assets
    where eca_location_id = 1036612408249
    group by 1
    -- order by 1
  ) stock
    -- сведения о предмете
    left outer join qi.eve_sde_type_ids tid on (stock.type_id = tid.sdet_type_id)
    -- усреднённые цены по евке прямо сейчас
    left outer join (
      select
        emp_type_id,
        case
          when emp_average_price is null or (emp_average_price < 0.001) then emp_adjusted_price
          else emp_average_price
        end as price
      from qi.esi_markets_prices
    ) universe on (stock.type_id = universe.emp_type_id)
    -- цены в жите прямо сейчас
    left outer join (
      select ethp_type_id, ethp_sell as sell, ethp_buy as buy
      from qi.esi_trade_hub_prices
      where ethp_location_id = 60003760
    ) jita on (stock.type_id = jita.ethp_type_id)
    -- производственные работы с обнаруженным материалом
    left outer join (
      select
        -- sdebm_blueprint_type_id,
        sdebm_material_id as material_id,
        count(1) as variations,
        sum(jobs.times) as jobs_times,
        max(jobs.last_using) as last_using,
        sum(jobs.using_last_1month) as using_last_1month,
        sum(jobs.using_last_2month) as using_last_2month,
        sum(jobs.using_last_3month) as using_last_3month,
        sum(jobs.using_last_4month) as using_last_4month
      from
        qi.eve_sde_blueprint_materials
          -- подсчёт кол-ва работ, запущенных с использованием этого типа чертежей
          left outer join (
            select
              ecj_blueprint_type_id,
              ecj_activity_id,
              count(1) as times,
              max(ecj_end_date::date) as last_using,
              sum(case when ecj_end_date::date >= '2021-08-10' then 1 else 0 end) as using_last_1month,
              sum(case when ecj_end_date::date >= '2021-07-10' then 1 else 0 end) as using_last_2month,
              sum(case when ecj_end_date::date >= '2021-06-10' then 1 else 0 end) as using_last_3month,
              sum(case when ecj_end_date::date >= '2021-05-10' then 1 else 0 end) as using_last_4month
            from qi.esi_corporation_industry_jobs jobs
            where jobs.ecj_corporation_id = 98677876
            group by 1, 2
          ) jobs on (sdebm_blueprint_type_id = jobs.ecj_blueprint_type_id and sdebm_activity = jobs.ecj_activity_id)
      group by 1
      -- order by 1
    ) materials_using on (stock.type_id = materials_using.material_id)
-- where tid.sdet_market_group_id in (1334,1333,1335,1336,1337) -- планетарка в стоке
order by tid.sdet_market_group_id;
EOD;
    $stock_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $stock = pg_fetch_all($stock_cursor);
    //---
    pg_close($conn);
?>
<div class="container-fluid">
<?php __dump_obsolete_stock($stock); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>
