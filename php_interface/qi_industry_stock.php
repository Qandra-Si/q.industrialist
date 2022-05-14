<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include_once '.settings.php';


?><style>
table.qind-materials tbody > tr > td:nth-child(1) > img /* material icon (compact view) */
{ margin-top: -2px; margin-bottom: -1px; }

table.qind-materials > tbody > tr > td,
table.qind-materials > tbody > tr > th
{ padding: 1px; font-size: smaller; }

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
table.qind-materials > tbody > tr > td:nth-child(7)
{ text-align: right; }
</style><?php


function __dump_materials_tree(&$materials) { ?>
<table class="table table-condensed table-hover qind-materials" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th></th>
  <th>Material</th>
  <th>Tech Level</th>
  <th>Quantity</th>
  <th>Calculated</th>
  <th>Overstock</th>
  <th>Understock</th>
  <!--<th>Variants</th>-->
 </tr>
</thead>
<tbody>
<?php
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
            $overstock = ($material_qty + $in_progress) - $material_calc;
            ?>
<tr>
 <td><img class="icn24" src="<?=__get_img_src($material_id,32,FS_RESOURCES)?>"></td>
 <td><?php
    /*if ($material_qty > 1) { ?><strong><?=$material_qty?>x</strong> <?php }*/
    ?><?=$material_name?>&nbsp;&nbsp;<span class="text-muted">(<?=$material_id?>)</span><?php
    if ($material_out_off=='t')
    {
        ?>&nbsp;<span class="label label-warning">out off</span><?php
    }
?></td>
 <td><?=$material_tech_level?></td>
 <td><?=$material_qty?><?=($in_progress>0)?'<mark>+'.$in_progress.'</mark>':''?></td>
 <td><?=$material_calc?></td>
 <td><?=($overstock>0)?$overstock:''?></td>
 <td><?=($overstock<0)?-$overstock:''?></td>
</tr>
            <?php
        }
?>
</tbody>
</table>
<?php
}



    __dump_header("Stock for Industry", FS_RESOURCES);
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
 coalesce(jobs.r,0) in_progress
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
order by 6 desc, 7, 4, 5, 3;
EOD;
    $materials_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $materials = pg_fetch_all($materials_cursor);
    //---
    pg_close($conn);
?>
<div class="container-fluid">
<h2>Stock for Industry</h2>
<?php __dump_materials_tree($materials); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>

<?php __dump_copy_to_clipboard_javascript() ?>
