<?php
include 'qi_render_html.php';
include_once '.settings.php';

function get_numeric($val) {
    return is_numeric($val) ? ($val + 0) : 0;
}
?>

<?php function __dump_obsolete_stock($stock) { ?>
<style>
.label-obsolete { color: #fff; background-color: #bbb; }
.label-forgotten { color: #fff; background-color: #ddd; }
.label-overstock { color: #333; background-color: #b5d2ea; }
.label-understock { color: #333; background-color: #ff0; }
.label-absent { color: #fff; background-color: #d9534f; }
</style>
<button class="btn btn-default" type="button" data-toggle="collapse" data-target="#collapseAnnotation" aria-expanded="false" aria-controls="collapseAnnotation">Аннотация</button>
<div class="btn-group btn-group-toggle" data-toggle="buttons" id="#btnGroups">
 <label class="btn btn-default active" id="btnGroupAll"><input type="radio" name="options" autocomplete="off" checked>Все</label>
 <label class="btn btn-default" id="btnGroupLost"><input type="radio" name="options" autocomplete="off">Потеряшки</label>
 <label class="btn btn-default" id="btnGroupOverstock"><input type="radio" name="options" autocomplete="off">С избытком</label>
 <label class="btn btn-default" id="btnGroupUnderstock"><input type="radio" name="options" autocomplete="off">Маловато</label>
 <label class="btn btn-default" id="btnGroupObsolete"><input type="radio" name="options" autocomplete="off">Забытые</label>
</div>
<div class="collapse" id="collapseAnnotation">
  <div class="card card-body">
<p>Автоматический расчёт состояния стока. В таблице приведена информация об используемых материалах, сколько их используется, сколько использовалось, какие материалы застряли в стоке, а каких не хватает. Маркеры, которые могут появиться в отчёте:
<ul>
 <li><span class="label label-danger">lost</span> - материал потерялся, надо достать и отправить на продажу;
 <li><span class="label label-warning">not used</span> - материал может быть использован в каком-либо из чертежей, но мы такое не крафтим (аналог потеряшки), например мы не производим 'Augmented' Infiltrator из Infiltrator II;
 <li><span class="label label-forgotten">forgotten</span> - уже месяц, как не используется в работках;
 <li><span class="label label-obsolete">obsolete</span> - уже два месяца не используется;
 <li><span class="label label-default">abandoned</span> - забыт на три месяца;
 <li><span class="label label-understock">understock</span> - материалов в скопилось слишком много;
 <li><span class="label label-overstock">overstock</span> - материалов не хватает;
 <li><span class="label label-absent">absent</span> - материал отсутствует в стоке, хотя использовался в каких-либо работах за последние 2 месяца.
</ul></p>
<p>Также считается количество материала (в штуках) которое мы ежемесячно используем... правда без учёта ME (только сводные данные по чертежам). Параметр <strong>Quantity</strong> - это потраченное кол-во материалов за последние 30 дней. Выборка с помощью бегущего окна, то есть завтра даты обновятся и интервал подвинется. Last 2 Month Quantity - аналогично, но за последние 60 дней. <strong>Times</strong> - количество работ.</p>
<p>Параметр <strong>Since</strong> показывает дату, когда стак с материалами "трогался" последний раз (переупаковывался, пополнялся, или уменьшался). Параметр <strong>Last Using</strong> показывет дату, когда материал использовался в какой-либо из последних работ, <strong>Used in Jobs</strong> - общее количество работ, проведённых с эпомянутым материалом. Параметр <strong>Blueprint Variations</strong> - показывает число возможных работ, в которых может быть задействован материал.</p>
<p>Также возможно формирование отчёта не только по <mark>..stock ALL</mark> коробке. Отчёт может быть сформирован по любому другому списку материалов, находящемуся в ином контейнере, для этого вам необходимо знать его номер и создать закладку в браузере, например <a href="http://<?=$_SERVER['HTTP_HOST'].$_SERVER['PHP_SELF']?>?stock=1036613601158">1036613601158</a>. Для получения уникальной ссылки на ваш контейнер обратитесь к Qandra Si.</p>
  </div>
</div>
<script>
  function rebuildStockMaterials(show_group) {
    $('#tblStock').find('tbody').find('tr').each(function() {
      var tr = $(this);
      var show = false;
      if (show_group == 0) // all
        show = true;
      else if (show_group == 1) // lost, not-used
        show = tr.find('td').eq(1).find('span.label-danger').length ||
               tr.find('td').eq(1).find('span.label-warning').length;
      else if (show_group == 2) // overstock
        show = tr.find('td').eq(1).find('span.label-overstock').length;
      else if (show_group == 3) // understock
        show = tr.find('td').eq(1).find('span.label-understock').length;
      else if (show_group == 4) // abandoned, obsolete, forgotten
        show = tr.find('td').eq(1).find('span.label-obsolete').length ||
               tr.find('td').eq(1).find('span.label-forgotten').length ||
               tr.find('td').eq(1).find('span.label-default').length;
      if (show)
        tr.removeClass('hidden');
      else
        tr.addClass('hidden');
    });
  }
  $(document).ready(function(){
    $('#btnGroupAll').on('click', function () {
      if (!$(this).hasClass('active')) // включается
        rebuildStockMaterials(0);
    });
    $('#btnGroupLost').on('click', function () {
      if (!$(this).hasClass('active')) // включается
        rebuildStockMaterials(1);
    });
    $('#btnGroupOverstock').on('click', function () {
      if (!$(this).hasClass('active')) // включается
        rebuildStockMaterials(2);
    });
    $('#btnGroupUnderstock').on('click', function () {
      if (!$(this).hasClass('active')) // включается
        rebuildStockMaterials(3);
    });
    $('#btnGroupObsolete').on('click', function () {
      if (!$(this).hasClass('active')) // включается
        rebuildStockMaterials(4);
    });
  });
</script>
<table class="table table-condensed" style="padding:1px;font-size:smaller;" id="tblStock">
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
  <th style="text-align: right;">Last 1 Month<br>Quantity / <mark>Times</mark></th>
  <th style="text-align: right;">Last 2 Month<br>Quantity / <mark>Times</mark></th>
  <th style="text-align: right;">Last 3 Month<br>Quantity / <mark>Times</mark></th>
  <th style="text-align: right;">Last 4 Month<br>Quantity / <mark>Times</mark></th>
 </tr>
</thead>
<tbody>
<?php
    $summary_stock_price = 0;
    $summary_jita_sell = 0;
    $summary_jita_buy = 0;
    foreach ($stock as $material)
    {
        $warnings = '';

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
        $last_1_month_quantity = $material['m1q'];
        $last_2_month_quantity = $material['m2q'];
        $last_3_month_quantity = $material['m3q'];
        $last_4_month_quantity = $material['m4q'];

        if (is_null($blueprint_variations) || !$blueprint_variations)
            $warnings .= '<span class="label label-danger">lost</span>&nbsp;';
        else if (is_null($using_in_jobs) || !$using_in_jobs)
            $warnings .= '<span class="label label-warning">not used</span>&nbsp;';
        else {
            if (is_null($last_3_month_using) || !$last_3_month_using)
                $warnings .= '<span class="label label-default">abandoned</span>&nbsp;';
            else if (is_null($last_2_month_using) || !$last_2_month_using)
                $warnings .= '<span class="label label-obsolete">obsolete</span>&nbsp;';
            else if (is_null($last_1_month_using) || !$last_1_month_using)
                $warnings .= '<span class="label label-forgotten">forgotten</span>&nbsp;';

            if (!is_null($last_1_month_quantity) && $last_1_month_quantity && ($last_1_month_quantity > $quantity))
                $warnings .= '<span class="label label-understock">understock</span>&nbsp;';
            else if (!is_null($last_2_month_quantity) && $last_2_month_quantity && ($last_2_month_quantity < $quantity))
                $warnings .= '<span class="label label-overstock">overstock</span>&nbsp;';

            if (is_null($quantity) || !$quantity)
                $warnings .= '<span class="label label-absent">absent</span>&nbsp;';
        }

        $summary_stock_price += $universe_avg_price;
        $summary_jita_sell += $jita_sell;
        $summary_jita_buy += $jita_buy;
?>
<tr>
 <td><img class="icn32" src="<?=__get_img_src($tid,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
 <td><?=$nm.'<br><span class="text-muted">'.$tid.'</span> '.$warnings?></td>
 <td align="right"><?=number_format($quantity,0,'.',',')?></td>
 <?php if (is_null($quantity) || !$quantity) { ?><td></td><td></td><?php } else { ?>
 <td align="right"><?=number_format($universe_avg_price,0,'.',',')?></td>
 <td align="right"><?=number_format($jita_sell,0,'.',',').'<br>'.number_format($jita_buy,0,'.',',')?></td>
 <?php } ?>
 <td align="right"><?=$lie_up_since?></td>
 <?php if (is_null($blueprint_variations) || !$blueprint_variations) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($blueprint_variations,0,'.',',')?></td>
 <?php } ?>
 <?php if (is_null($using_in_jobs) || !$using_in_jobs) { ?><td></td><?php } else { ?>
  <td align="right"><?=number_format($using_in_jobs,0,'.',',')?><?=(!is_null($last_using))?'<br>'.$last_using:''?></td>
 <?php } ?>
 <?php if (is_null($last_1_month_using) || !$last_1_month_using) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($last_1_month_quantity,0,'.',',')?><br><mark><?=number_format($last_1_month_using,0,'.',',')?></mark></td>
 <?php } ?>
 <?php if (is_null($last_2_month_using) || !$last_2_month_using) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($last_2_month_quantity,0,'.',',')?><br><mark><?=number_format($last_2_month_using,0,'.',',')?></mark></td>
 <?php } ?>
 <?php if (is_null($last_3_month_using) || !$last_3_month_using) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($last_3_month_quantity,0,'.',',')?><br><mark><?=number_format($last_3_month_using,0,'.',',')?></mark></td>
 <?php } ?>
 <?php if (is_null($last_4_month_using) || !$last_4_month_using) { ?><td></td><?php } else { ?>
 <td align="right"><?=number_format($last_4_month_quantity,0,'.',',')?><br><mark><?=number_format($last_4_month_using,0,'.',',')?></mark></td>
 <?php } ?>
</tr>
<?php
    }
?>
<tr style="font-weight:bold;">
 <td colspan="3" align="right">Summary</td>
 <td align="right"><?=number_format($summary_stock_price,0,'.',',')?></td>
 <td align="right"><?=number_format($summary_jita_sell,0,'.',',').'<br>'.number_format($summary_jita_buy,0,'.',',')?></td>
 <td colspan="7"></td>
</tr>
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
    $show_absent = 0;
    if (isset($_GET['absent'])) {
        $_get_absent = htmlentities($_GET['absent']);
        if (is_numeric($_get_absent))
            $show_absent = get_numeric($_get_absent) ? 1 : 0;
    }

    __dump_header("Obsolete Stock", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
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
  materials_using.jobs_times as uj, -- used in jobs
  materials_using.last_using as lu, -- last using
  materials_using.using_last_1month as m1, -- last 1 month using
  materials_using.using_last_2month as m2, -- last 2 month using
  materials_using.using_last_3month as m3, -- last 3 month using
  materials_using.using_last_4month as m4, -- last 4 month using
  materials_using.quantity_last_1month as m1q, -- last 1 month quantity
  materials_using.quantity_last_2month as m2q, -- last 2 month quantity
  materials_using.quantity_last_3month as m3q, -- last 3 month quantity
  materials_using.quantity_last_4month as m4q  -- last 4 month quantity
from
  -- список материалов, которые должны попасть в отчёт
  ( -- содержимое коробки ..stock ALL на Сотие
    select
      eca_type_id as type_id,
      sum(eca_quantity) as quantity,
      max(eca_created_at::date) as since
    from qi.esi_corporation_assets
    where eca_location_id = $1
    group by 1
    union
    -- список материалов, которых нет в коробке
    select distinct m.sdebm_material_id, 0, null::date
    from
      qi.eve_sde_blueprint_materials m,
      qi.esi_corporation_industry_jobs j
    where
      ($2 = 1) and
      m.sdebm_blueprint_type_id = j.ecj_blueprint_type_id and
      m.sdebm_activity = j.ecj_activity_id and
      j.ecj_start_date >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '60 days')
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
        sum(jobs.using_last_4month) as using_last_4month,
        sum(jobs.runs_last_1month*sdebm_quantity) as quantity_last_1month,
        sum(jobs.runs_last_2month*sdebm_quantity) as quantity_last_2month,
        sum(jobs.runs_last_3month*sdebm_quantity) as quantity_last_3month,
        sum(jobs.runs_last_4month*sdebm_quantity) as quantity_last_4month
      from
        qi.eve_sde_blueprint_materials
          -- подсчёт кол-ва работ, запущенных с использованием этого типа чертежей
          left outer join (
            select
              ecj_blueprint_type_id,
              ecj_activity_id,
              count(1) as times,
              max(ecj_start_date::date) as last_using,
              sum(case when ecj_start_date::date >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '30 days') then 1 else 0 end) as using_last_1month,
              sum(case when ecj_start_date::date >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '60 days') then 1 else 0 end) as using_last_2month,
              sum(case when ecj_start_date::date >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '90 days') then 1 else 0 end) as using_last_3month,
              sum(case when ecj_start_date::date >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '120 days') then 1 else 0 end) as using_last_4month,
              sum(case when ecj_start_date::date >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '30 days') then ecj_runs else 0 end) as runs_last_1month,
              sum(case when ecj_start_date::date >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '60 days') then ecj_runs else 0 end) as runs_last_2month,
              sum(case when ecj_start_date::date >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '90 days') then ecj_runs else 0 end) as runs_last_3month,
              sum(case when ecj_start_date::date >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '120 days') then ecj_runs else 0 end) as runs_last_4month
            from qi.esi_corporation_industry_jobs jobs
            where jobs.ecj_corporation_id = 98677876
         and ecj_start_date::date >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '120 days')
            group by 1, 2
          ) jobs on (sdebm_blueprint_type_id = jobs.ecj_blueprint_type_id and sdebm_activity = jobs.ecj_activity_id)
      where jobs.ecj_blueprint_type_id is not null
      group by 1
      -- order by 1
    ) materials_using on (stock.type_id = materials_using.material_id)
-- where tid.sdet_market_group_id in (1334,1333,1335,1336,1337) -- планетарка в стоке
order by tid.sdet_market_group_id, tid.sdet_type_name;
EOD;
    $params = array($stock_location_id, $show_absent);
    $stock_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $stock = pg_fetch_all($stock_cursor);
    //---
    pg_close($conn);
?>
<div class="container-fluid">
<?php __dump_obsolete_stock($stock); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>
