<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include_once '.settings.php';


?><style>
table.qind-materials tbody > tr > td:nth-child(1) > img /* material icon (compact view) */
{ margin-top: -2px; margin-bottom: -1px; }

table.qind-materials > tbody > tr > td,
table.qind-materials > tbody > tr > th
{ padding: 1px; }

table.qind-materials > tbody > tr > th
{ font-weight: bold; text-align: right; }

table.qind-materials > tbody > tr > td:nth-child(1)
{ width: 24px; }

table.qind-materials > thead > tr > th:nth-child(3),
table.qind-materials > tbody > tr > td:nth-child(3),
table.qind-materials > thead > tr > th:nth-child(4),
table.qind-materials > tbody > tr > td:nth-child(4),
table.qind-materials > thead > tr > th:nth-child(5),
table.qind-materials > tbody > tr > td:nth-child(5),
table.qind-materials > thead > tr > th:nth-child(6),
table.qind-materials > tbody > tr > td:nth-child(6),
table.qind-materials > thead > tr > th:nth-child(7),
table.qind-materials > tbody > tr > td:nth-child(7),
table.qind-materials > thead > tr > th:nth-child(9),
table.qind-materials > tbody > tr > td:nth-child(9),
table.qind-materials > thead > tr > th:nth-child(8),
table.qind-materials > tbody > tr > td:nth-child(8)
{ text-align: right; }

table.qind-materials > tbody > tr > td:nth-child(4)
{ background-color: #f1f7ff; }
table.qind-materials > tbody > tr > td:nth-child(6)
{ background-color: #fffbf1; }
table.qind-materials > tbody > tr > td:nth-child(8),
table.qind-materials > tbody > tr > td:nth-child(9)
{ background-color: #f4ffdd; }
</style><?php


function __dump_materials_tree(&$materials, &$sale) { ?>
<?php
    if ($sale)
        foreach ($sale as &$s)
            $s['bp2_in'] = explode(',',$s['bp2_in']);
    $body_printed = false;
    $prev_out_off = null;
    $prev_ip = null;
    $prev_im = null;
    if ($materials)
        foreach ($materials as &$m)
        {
            $material_id = $m['mid'];
            $material_name = $m['mnm'];
            $material_qty = $m['q'];
            $material_calc = $m['calc'];
            //$material_options = $m['opts']; // кол-во чертежей, в которых упоминается материал
            $material_out_off = $m['out_off'];
            $material_tech_level = $m['tech'];
            $in_progress = $m['in_progress'];
            $industry_possible = $m['ip']; // industry possible
            $material_for_invented_blueprints = $m['im']; // material for invented blueprints
            $overstock = ($material_qty + $in_progress) - $material_calc;
            if (is_null($prev_out_off) ||
                ($material_out_off == 'f') && ($prev_ip != $industry_possible || $prev_im != $material_for_invented_blueprints))
            {
                if ($body_printed)
                {
                    ?></tbody></table><?php
                }
                $prev_out_off = $material_out_off;
                $prev_ip = $industry_possible;
                $prev_im = $material_for_invented_blueprints;
                if ($material_out_off == 't')
                {
                    ?><h3>Убрать из стока</h3><?php
                }
                else
                {
                    ?><h3>Расчёт потребностей стока</h3><?php
                    if ($material_for_invented_blueprints == 't')
                    {
                        ?><h4>Материалы, используемые в чертежах, которые можно инвентить</h4><?php
                    }
                    else
                    {
                        ?><h4>Материалы, которые не используются в invent-чертежах</h4><?php
                    }
                    if ($industry_possible == 't')
                    {
                        ?><h5>Материалы, производство которых возможно</h5><?php
                    }
                    else
                    {
                        ?><h5>Материалы, которые не производятся</h5><?php
                    }
                }
                $body_printed = true;
                ?>
<table class="table table-condensed table-hover qind-materials" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th></th>
  <th>Material</th>
  <th>Tech Level</th>
  <th>In stock<br>Sotiyo</th>
  <th>Calculated<br>by BP Copies</th>
  <th>Overstock<br>Sotiyo</th>
  <th>Required<br>Sotiyo</th>
  <th>Sale<br>Now</th>
  <th>Sold<br>30 days</th>
 </tr>
</thead>
<tbody>
                <?php
            }

            $sale_now = 0;
            $sold_30_days = 0;
            if ($sale)
                foreach ($sale as &$s)
                    if (in_array($material_id,$s['bp2_in']))
                    {
                        //$bp2_out = $s['bp2_out'];
                        $sale_now += $s['sale'];
                        $sold_30_days += $s['sold'];
                    }
            ?>
<tr>
 <td><img class="icn24" src="<?=__get_img_src($material_id,32,FS_RESOURCES)?>"></td>
 <td><?php
    /*if ($material_qty > 1) { ?><strong><?=$material_qty?>x</strong> <?php }*/
    ?><?=$material_name.get_clipboard_copy_button($material_name)?>&nbsp;&nbsp;<span class="text-muted">(<?=$material_id?>)</span><?php
    if ($material_out_off=='t')
    {
        ?>&nbsp;<span class="label label-warning">out off</span><?php
    }
?></td>
 <td><?=$material_tech_level?></td>
 <td><?=$material_qty?><?=($in_progress>0)?'<mark>+'.$in_progress.'</mark>':''?></td>
 <td><?=$material_calc?></td>
 <td><?=($overstock>0)?$overstock.get_clipboard_copy_button($overstock):''?></td>
 <td><?=($overstock<0)?-$overstock:''?></td>
 <td><?=$sale_now?$sale_now:''?></td>
 <td><?=$sold_30_days?$sold_30_days:''?></td>
</tr>
            <?php
        }
    if ($body_printed)
    {
        ?>
</tbody>
</table>
        <?php
    }
}



    __dump_header("Industry' Stock", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
select
 stock.t mid,
 t.sdet_type_name mnm,
 stock.q,
 needs.calc,
 opts.c as opts,
 (opts.c is null) as out_off,
 t.sdet_tech_level as tech,
 coalesce(jobs.r,0) in_progress,
 (prod.p is not null) as ip,
 (invent.m is not null) as im
from (
 select eca_type_id t, sum(eca_quantity) q
 from qi.esi_corporation_assets
 where eca_location_id in (
  select eca_item_id 
  from qi.esi_corporation_assets
  where eca_corporation_id=98677876 and (eca_name='..stock ALL' or eca_name='..stock OBSOLETE')
 )
 group by 1
) stock
 -- сведения о компоненте
 left outer join qi.eve_sde_type_ids t on (t.sdet_type_id=stock.t)
 -- список материалов, которые используются в производстве после инвента
 -- (ищем чертежи, которые инвентятся, и строим список материалов для них)
 left outer join (
  select distinct
   --sdebp_blueprint_type_id bp1,
   --sdebp_product_id bp2,
   sdebm_material_id m
  from
   qi.eve_sde_blueprint_products,
   qi.eve_sde_type_ids,
   qi.eve_sde_blueprint_materials
  where
   sdebp_activity=8 and
   sdebp_blueprint_type_id=sdet_type_id and sdet_published and
   sdebm_blueprint_type_id=sdebp_product_id and sdebm_activity=1
 ) invent on (stock.t=invent.m)
 -- кол-во чертежей, в которых данный компонент является продуктом (производится ли?)
 left outer join (
  select sdebp_product_id p, count(1) c
  from qi.eve_sde_blueprint_products, qi.eve_sde_type_ids
  where sdebp_blueprint_type_id=sdet_type_id and sdet_published
  group by 1
 ) prod on (stock.t=prod.p)
 -- кол-во чертежей, в которых компонент используется как материал (место ли ему в стоке?)
 left outer join (
  select sdebm_material_id m, count(1) c
  from qi.eve_sde_blueprint_materials, qi.eve_sde_type_ids
  where sdebm_blueprint_type_id=sdet_type_id and sdet_published and sdebm_activity=1
  group by 1
 ) opts on (stock.t=opts.m)
 -- производственные работы, в результате которых появляются компоненты
 left outer join (
  select ecj_product_type_id t,sum(ecj_runs) r
  from qi.esi_corporation_industry_jobs
  where ecj_corporation_id=98677876 and ecj_end_date>CURRENT_TIMESTAMP AT TIME ZONE 'GMT'
  group by 1
 ) jobs on (jobs.t=stock.t)
 -- подсчёт подтребностей данного компонента с учётом имеющихся копий
 left outer join (
  select
   y.t,
   y.calc
  from (
   select
    x.m_id t,
    sum(x.m_calc) calc
   from (
    select
     --bpc.t bp_tid,
     --(select sdet_type_name from qi.eve_sde_type_ids bp where sdet_type_id=bpc.t) bp_name,
     --bpc.q bp_q,
     --bpc.r bp_r,
     --bpc.me bp_me,
     mat.sdebm_material_id m_id,
     --(select sdet_type_name from qi.eve_sde_type_ids bp where sdet_type_id=mat.sdebm_material_id) m_name,
     --mat.sdebm_quantity m_qty,
     case
      when mat.sdebm_quantity=1 then bpc.r*bpc.q
      else bpc.q*trunc(((mat.sdebm_quantity*bpc.r*(100-bpc.me)/100.0)*0.99)*0.958+0.99)
     end m_calc
    from (
     select x.t, x.q, x.r, x.me
     from (
      -- список корпоративных чертежей в конвейере (их раны)
      select ecb_type_id t, count(1) q, ecb_runs r, ecb_material_efficiency me
      from qi.esi_corporation_blueprints
      where ecb_quantity=-2 and ecb_location_id in (
       select eca_item_id
       from qi.esi_corporation_assets
       where
        eca_corporation_id=98677876 and
        (eca_name like '[prod]%' or
         eca_name like '[order]%' or
         eca_name like '.[prod]%')
      )
      group by 1,3,4
      union
      select ecj_product_type_id, sum(ecj_runs), ecj_licensed_runs, coalesce(ecb.me,10)
      from qi.esi_corporation_industry_jobs
       left outer join (
        select ecb_item_id id,ecb_material_efficiency me
        from qi.esi_corporation_blueprints
       ) ecb on (ecb.id=ecj_blueprint_id)
      where
       ecj_corporation_id=98677876 and
       ecj_activity_id=5 and
       ecj_end_date>CURRENT_TIMESTAMP AT TIME ZONE 'GMT' and
       ecj_output_location_id in (
        select eca_item_id 
        from qi.esi_corporation_assets
        where
         eca_corporation_id=98677876 and
         (eca_name like '[prod]%' or
          eca_name like '[order]%' or
          eca_name like '.[prod]%')
       )
      group by 1,3,4
     ) x
     --group by 1,3,4
    ) bpc
     -- материалы, из которых производится продукция по чертежу
     left outer join qi.eve_sde_blueprint_materials mat on (mat.sdebm_activity=1 and mat.sdebm_blueprint_type_id=bpc.t)
   ) x
   group by 1
  ) y
 ) needs on (needs.t=stock.t)
order by 6 desc, 10 desc, 9 desc, 7, 4, 5, 3;
EOD;
    $materials_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $materials = pg_fetch_all($materials_cursor);
    //---
    $query = <<<EOD
select
 -- bp1.sdebp_blueprint_type_id bp1_in,
 -- bp1.sdebp_product_id bp1_out,
 -- (select sdet_type_name  from qi.eve_sde_type_ids where sdet_type_id=bp1.sdebp_product_id),
 array(select sdebm_material_id from qi.eve_sde_blueprint_materials where sdebm_blueprint_type_id=bp1.sdebp_product_id and sdebm_activity=1) bp2_in,
 bp2.sdebp_product_id bp2_out,
 -- (select sdet_type_name  from qi.eve_sde_type_ids where sdet_type_id=bp2.sdebp_product_id),
 co.sale,
 co.sold
from
 qi.eve_sde_blueprint_products bp1,
 qi.eve_sde_type_ids,
 qi.eve_sde_blueprint_products bp2,
 ( select
    ecor_type_id,
    sum(case when ecor_history then 0 else ecor_volume_remain end) sale,
    sum(ecor_volume_total-ecor_volume_remain) as sold
   from qi.esi_corporation_orders
   where
    not ecor_is_buy_order and
    ecor_corporation_id=98677876 and
    ecor_issued > (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '30 days')
   group by 1
 ) co
where
 bp1.sdebp_activity=8 and
 bp1.sdebp_blueprint_type_id=sdet_type_id and sdet_published and
 bp2.sdebp_blueprint_type_id=bp1.sdebp_product_id and
 co.ecor_type_id=bp2.sdebp_product_id;
EOD;
    $sale_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $sale = pg_fetch_all($sale_cursor);
    //---
    pg_close($conn);
?>
<div class="container-fluid">
<h2>Industry' Stock</h2>
<?php __dump_materials_tree($materials, $sale); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>

<?php __dump_copy_to_clipboard_javascript() ?>
