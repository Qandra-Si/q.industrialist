<?php
include 'qi_render_html.php';
include_once '.settings.php';
?>

<?php function __dump_industrial_jobs($jobs) {
    $fid = NULL;
    foreach ($jobs as &$job)
    {
        $ptid = $job['ptid'];
        $nm = $job['nm'];
        $cost = $job['cost'];
        $runs = $job['runs'];
        $scost = $cost / $runs;
        if ($fid != $job['fid']) {
            if (!is_null($fid)) echo '</tbody></table>';
            $fid = $job['fid']; ?>
<h3><?=$fid?></h3>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th style="width:32px;"></th>
  <th>Items</th>
  <th style="text-align: right;">Fee &amp; Tax, ISK</th>
  <th style="text-align: right;">Volume, m&sup3;</th>
 </tr>
</thead>
<tbody>
<?php } ?>
<tr><!--<?=$ptid?>-->
 <td><img class="icn32" src="<?=__get_img_src($ptid,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
 <td><strong><?=$runs?>x</strong> <?=$nm?></td>
 <td align="right"><?=number_format($cost,1,'.',',')?><br><mark><span style="font-size: smaller;"><?=number_format($scost,2,'.',',')?></span></mark></td>
 <td align="right">?<br><mark><span style="font-size: smaller;">?</span></mark></td>
</tr>
<?php
    }
?>
</tbody>
</table>
<?php } ?>


<?php
    __dump_header("Industry", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
SELECT
 wij_facility_id AS fid,
 wij_product_tid AS ptid,
 sden_name AS nm,
 sum(wij_cost) AS cost,
 sum(wij_runs) AS runs
FROM
 workflow_industry_jobs
  LEFT OUTER JOIN eve_sde_names
  ON sden_category=1 AND sden_id=wij_product_tid
--WHERE wij_activity_id=1
GROUP BY 1,2,3
ORDER BY 1,3;
EOD;
    $jobs_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $jobs = pg_fetch_all($jobs_cursor);
    //---
    pg_close($conn);
?>
<div class="container-fluid">
<?php __dump_industrial_jobs($jobs); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>