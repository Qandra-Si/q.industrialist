<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include_once '.settings.php';


const TABLE_COLUMNS = 7;

function __dump_new_items_tree(&$new_items) { ?>
<style type="text/css">
#tbl tbody tr td:nth-child(1) { width: 40px; }
#tbl tbody tr td:nth-child(4) { text-align: right; }
#tbl tbody tr td:nth-child(5) { text-align: right; }
#tbl tbody tr td:nth-child(6) { text-align: right; }
#tbl tbody tr td:nth-child(7) { text-align: right; }
</style>
<table class="table table-condensed" style="padding:1px;font-size:smaller;" id="tbl">
<thead>
 <tr>
  <th style="width:40px;"></th>
  <th>Items</th>
  <th colspan="<?=TABLE_COLUMNS-2?>" width="66%">Details</th>
 </tr>
 <tr>
  <th colspan="2"></th>
  <th style="text-align:center;">added</th>
  <th style="text-align:center;">published</th>
  <th style="text-align:center;">packed volume</th>
  <th style="text-align:right;">Jita sell<br>Jita buy</th>
  <th style="text-align:right;">Amarr sell<br>Amarr buy</th>
 </tr>
</thead>
<tbody>
<?php
    $prev_market_group = null;
    $market_group_names = array(null, null, null, null, null, null, null, null, null, null);
    $market_group_shown = false;
    if ($new_items)
        foreach ($new_items as &$itm)
        {
            // market group info
            $market_group_depth = $itm['mgd'];
            if ($market_group_depth == 1) continue; // уровень c корневыми наименованиями пропускаем (в нём нет элементов)
            $market_group_name = $itm['mgn'];
            $market_group_id = ($itm['mgi']>=0) ? $itm['mgi'] : null;
            // item info
            $item_type_id = $itm['tid'];
            $item_name = $itm['name'];
            $item_tech = $itm['tech'];

            if ($prev_market_group != $market_group_name)
            {
                $prev_market_group = $market_group_name;
                $market_group_names[$market_group_depth-2] = $market_group_name;
                $market_group_shown = false;
            }

            // если в этом разделе нет элементов (это корневая группа), то пропуск вывода подробностей
            if (is_null($item_type_id)) continue;

            if ($market_group_shown == false)
            {
                $market_group_shown = true;
                ?><tr><td class="active" colspan="<?=TABLE_COLUMNS?>"><strong><?=str_pad('', ($market_group_depth-2)*7, '&nbsp; ', STR_PAD_LEFT)?><?php
                if ($market_group_depth > 2)
                {
                    ?><span class="text-muted"><?php
                    for ($i = 0, $cnt = $market_group_depth - 2; $i < $cnt; ++$i)
                    {
                        ?><?=$market_group_names[$i]?> &raquo; <?php
                    }
                    ?></span><?php
                }
                ?><?=$market_group_name?><?php if (!is_null($market_group_id)) { ?> <span class="text-muted">(<?=$market_group_id?>)</span><?php } ?></strong></td></tr><?php
            }
            ?>
<tr>
 <td><img class="icn32" src="<?=__get_img_src($item_type_id,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
 <td><?=$item_name?><br><span class="text-muted"><?=$item_type_id?></span><?php if (!is_null($item_tech) && ($item_tech != 1)) { ?><span class="label label-warning">tech <?=$$item_tech?></span><?php } ?></td>
 <td><?=$itm['at']?></td>
 <td><?=($itm['pub'] == 't')?"yes":"no"?></td>
 <td><?=$itm['pv']?></td>
 <td><?=is_null($itm['js'])?'':number_format($itm['js'],2,'.',',')?><br><?=is_null($itm['jb'])?'':number_format($itm['jb'],2,'.',',')?></td>
 <td><?=is_null($itm['as'])?'':number_format($itm['as'],2,'.',',')?><br><?=is_null($itm['ab'])?'':number_format($itm['ab'],2,'.',',')?></td>
</tr>
            <?php
        }
?>
</tbody>
</table>
<?php
}



    __dump_header("New Items", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
select
  -- rpad('          ',(rrr.depth-1)*2)||rrr.name as tree, -- market group name 
  rrr.depth as mgd, -- tree depth
  rrr.name as mgn, -- market group name
  rrr.id as mgi, -- market group id
  x.tid, -- type id
  x.name, -- name
  x.tech, -- tech-level
  x.pub, -- published
  x.pv, -- packed volume
  x.at, -- date added
  jita.sell as js,
  jita.buy as jb,
  amarr.sell as as,
  amarr.buy as ab
from (
  select
    rr.*,
    row_number() OVER () as rnum
  from (
    with recursive r as (
      select
        sdeg_group_id as id,
        sdeg_parent_id as parent,
        sdeg_group_name as name,
        1 as depth,
        sdeg_group_name::varchar(255) as sort_str
      from qi.eve_sde_market_groups
      where sdeg_parent_id is null -- and sdeg_group_id = 2
      union all
      select
        branch.sdeg_group_id,
        branch.sdeg_parent_id,
        branch.sdeg_group_name,
        r.depth+1,
        (r.sort_str || '|' || branch.sdeg_group_name)::varchar(255)
      from qi.eve_sde_market_groups as branch
        join r on branch.sdeg_parent_id = r.id
    )
    select r.id, r.parent, r.name, r.depth from r
    --select r.* from r
    order by r.sort_str
  ) rr
  union
  select -2, null, 'Unknown Market Group', 1, 1000000
  union
  select -1, -2, 'Items with unknown Market Group', 2, 1000001
) rrr
 -- новые элементы в системе
 left outer join (
  select
    sdet_type_id as tid,
    sdet_type_name as name,
    sdet_published as pub,
    coalesce(sdet_market_group_id,-1) as mg,
    sdet_tech_level as tech,
    sdet_packaged_volume as pv,
    sdet_created_at::date as at
   from eve_sde_type_ids
   where sdet_created_at >= (current_timestamp at time zone 'GMT' - interval '14 days')
 ) x on (x.mg = rrr.id)
 -- цены в жите прямо сейчас
 left outer join (
  select ethp_type_id, ethp_sell as sell, ethp_buy as buy
  from esi_trade_hub_prices
  where ethp_location_id = 60003760
 ) jita on (x.tid = jita.ethp_type_id)
 -- цены в амарре прямо сейчас
 left outer join (
  select ethp_type_id, ethp_sell as sell, ethp_buy as buy
  from esi_trade_hub_prices
  where ethp_location_id = 60008494
 ) amarr on (x.tid = amarr.ethp_type_id)
where x.tid is not null
order by rrr.rnum;
EOD;
    $new_items_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $new_items = pg_fetch_all($new_items_cursor);
    //---
    pg_close($conn);
?>
<div class="container-fluid">
<h2>New items added in the last two weeks </h2>
<?php __dump_new_items_tree($new_items); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>

<?php __dump_copy_to_clipboard_javascript() ?>
