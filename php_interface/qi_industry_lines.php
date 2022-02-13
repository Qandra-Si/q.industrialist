<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include_once '.settings.php';


if (!isset($MAIN_PILOT_CAPTION))
    $MAIN_PILOT_CAPTION = "??? ??? ???";
if (!isset($PILOT_IDs))
    $PILOT_IDs = array(2119358878); // Qandra Si


$html_style = <<<EOD
<style type="text/css">
body {
 background-color: #162326;
 color: #c5c8c9;
}
.progress {
 height: 8px;
 margin-bottom: 0px;
 background-color: #232e31;
 border-radius: 0px;
}
.page-header { border-bottom: 1px solid #1d3231; }
#tbl thead tr th { padding: 4px; border-bottom: 1px solid #1d3231; }
#tbl tbody tr td { padding: 4px; border-top: none; }
#tbl tbody tr td:nth-child(1) { width: 24px; }
#tbl tbody tr td:nth-child(3) { text-align: right; font-size: large; vertical-align: middle; }
#tbl tbody tr td:nth-child(4) { text-align: right; }
#tbl tbody tr td:nth-child(5) { text-align: left; vertical-align: middle; }
#tbl tbody tr td:nth-child(6) { text-align: left; vertical-align: middle; }
#tbl tbody tr td:nth-child(7) { text-align: right; vertical-align: middle; }
#tbl tbody tr td:nth-child(3),
#tbl tbody tr td:nth-child(4),
#tbl tbody tr td:nth-child(5),
#tbl tbody tr td:nth-child(6),
#tbl tbody tr td:nth-child(7) { border-left: 1px solid #1d3231; }
.activity1 { background-color: #ff9900; }
.activity3,
.activity4,
.activity5,
.activity7,
.activity8 { background-color: #3371b6; }
.activity9,
.activity11 { background-color: #0a7f6f; }
.label-summary {
 font-size: 66%;
 font-weight: unset;
}
mark {
 background-color: #1a302e;
 color: #d8dada;
 padding: .3em .3em .3em;
}
</style>
EOD;


function __dump_pilots_involved(&$active_jobs, &$industry_stat)
{
    if ($industry_stat)
    {
        ?><p>The information is current as of: <mark><?=$industry_stat[0]['dt1']?> (MSK)</mark> &times; <?=$industry_stat[0]['dt2']?></p><?php
    }
    $pilots = array();
    if ($active_jobs)
        foreach ($active_jobs as &$job)
        {
            $found = false;
            foreach($pilots as &$pilot)
            {
                if ($pilot[0] == $job['inm'])
                {
                    if (!is_null($job['aid']))
                        switch ($job['aid'])
                        {
                        case 1: $pilot[1]++; break;
                        case 3: case 4: case 5: case 7: case 8: $pilot[2]++; break;
                        case 9: case 11: $pilot[3]++; break;
                        }
                    $found = true;
                    break;
                }
            }
            if (!$found)
            {
                $p = array($job['inm'], 0, 0, 0);
                if (!is_null($job['aid']))
                    switch ($job['aid'])
                    {
                    case 1: $p[1]++; break;
                    case 3: case 4: case 5: case 7: case 8: $p[2]++; break;
                    case 9: case 11: $p[3]++; break;
                    }
                array_push($pilots, $p);
            }
        }
    asort($pilots);
    foreach($pilots as &$pilot)
    {
        ?>
        <h4><?=$pilot[0]?>
            <span class="label label-summary <?=($pilot[1]==0)?'label-default':'activity1'?>">manufacturing <span style="font-weight: 1000;">&times; <?=$pilot[1]?></span></span>
            <span class="label label-summary <?=($pilot[2]==0)?'label-default':'activity5'?>">science <span style="font-weight: 1000;">&times; <?=$pilot[2]?></span></span>
            <span class="label label-summary <?=($pilot[3]==0)?'label-default':'activity9'?>">reaction <span style="font-weight: 1000;">&times; <?=$pilot[3]?></span></span></h4>
        <?php
    }
}

function __dump_industry_jobs(&$active_jobs) { ?>
<table class="table table-condensed" style="padding:1px;font-size:smaller;" id="tbl">
<thead>
 <tr>
  <th colspan="2"></th>
  <th style="text-align:right;">Pilot</th>
  <th style="text-align:right;">Left time</th>
  <th style="text-align:left;">Blueprint</th>
  <th style="text-align:left;">Output</th>
  <th style="text-align:right;">Finish time (MSK)</th>
 </tr>
</thead>
<tbody>
<?php
    if ($active_jobs)
        foreach ($active_jobs as &$job)
        {
            if (is_null($job['aid'])) continue;
            $progress = 100.0 * $job['sec2'] / $job['sec1'];
            ?>
<tr>
 <td><img class="icn32" src="<?=__get_img_src($job['pid'],32,FS_RESOURCES)?>" width="32px" height="32px"></td>
 <td><?=$job['pnm']?><br><span class="text-muted"><?=$job['pid']?></span></td>
 <td><?=$job['inm']?></td>
 <td><?=$job['left']?><br><div class="progress"><div class="progress-bar activity<?=$job['aid']?>" role="progressbar" aria-valuenow="<?=round($progress)?>" aria-valuemin="0" aria-valuemax="100" style="width: <?=round($progress,1)?>%;"></div></div></td>
 <td><?=$job['abnm']?></td>
 <td><?=$job['aonm']?></td>
 <td><?=$job['edt']?></td>
</tr>
            <?php
        }
?>
</tbody>
</table>
<?php
}



    __dump_header($MAIN_PILOT_CAPTION."' Industry", FS_RESOURCES, $html_style);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
select
 date_trunc('seconds', j.udt+'3:00:00') as dt1,
 date_trunc('seconds', CURRENT_TIMESTAMP AT TIME ZONE 'GMT'-j.udt) as dt2
from (
 select max(ecj_updated_at) udt
 from esi_corporation_industry_jobs
 where ecj_corporation_id = 98677876
) j;
EOD;
    $industry_stat_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $industry_stat = pg_fetch_all($industry_stat_cursor);
    //---
    $query = <<<EOD
select
 -- iids.id,
 -- ecj_installer_id as iid,
 c.ech_name as inm,
 -- ecj_facility_id,
 ecj_activity_id as aid,
 -- ecj_blueprint_type_id,
 ab.eca_name as abnm, -- ecj_blueprint_location_id,
 ao.eca_name as aonm, -- ecj_output_location_id,
 ecj_product_type_id as pid,
 tp.sdet_type_name as pnm,
 date_trunc('seconds', ecj_end_date+'3:00:00') as edt,
 date_trunc('seconds', ecj_end_date-CURRENT_TIMESTAMP AT TIME ZONE 'GMT') as left,
 extract(epoch from ecj_end_date-ecj_start_date)::int as sec1,
 extract(epoch from ecj_end_date-CURRENT_TIMESTAMP AT TIME ZONE 'GMT')::int as sec2,
 ecj_status as st
from (
 select distinct ecj_installer_id as id
 from esi_corporation_industry_jobs
 where
  ecj_end_date > (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '7 days') and
  ecj_installer_id = any($1)
 ) iids
  left outer join esi_corporation_industry_jobs j on (
   j.ecj_installer_id=iids.id and
   j.ecj_status <> 'delivered'and
   j.ecj_end_date > CURRENT_TIMESTAMP AT TIME ZONE 'GMT')
  left outer join esi_characters c on (iids.id=c.ech_character_id)
  left outer join esi_corporation_assets ab on (ecj_blueprint_location_id=ab.eca_item_id)
  left outer join esi_corporation_assets ao on (ecj_output_location_id=ao.eca_item_id)
  left outer join eve_sde_type_ids tp on (ecj_product_type_id=tp.sdet_type_id)
order by ecj_end_date;
EOD;
    $params = array('{'.implode(',',$PILOT_IDs).'}');
    $industry_jobs_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $industry_jobs = pg_fetch_all($industry_jobs_cursor);
    //---
    pg_close($conn);
?>
<div class="container-fluid">
<h2>Pilots involved in Industry</h2>
<?php __dump_pilots_involved($industry_jobs, $industry_stat); ?>
<h2>Industry jobs list</h2>
<?php __dump_industry_jobs($industry_jobs); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>

<?php __dump_copy_to_clipboard_javascript() ?>
