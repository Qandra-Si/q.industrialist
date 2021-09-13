﻿<?php
include 'qi_render_html.php';
include_once '.settings.php';

$product_requirements = array(
    array('id' =>  2329, 'name' => 'Biocells',                       'quantity' => 72000),
    array('id' =>  3828, 'name' => 'Construction Blocks',            'quantity' => 66120),
    array('id' =>  9836, 'name' => 'Consumer Electronics',           'quantity' => 26280),
    array('id' =>  9832, 'name' => 'Coolant',                        'quantity' => 26280),
    array('id' =>    44, 'name' => 'Enriched Uranium',               'quantity' => 36000),
    array('id' =>  3693, 'name' => 'Fertilizer',                     'quantity' => 66120),
    array('id' => 15317, 'name' => 'Genetically Enhanced Livestock', 'quantity' => 36000),
    array('id' =>  3725, 'name' => 'Livestock',                      'quantity' => 66120),
    array('id' =>  2327, 'name' => 'Microfiber Shielding',           'quantity' => 72000),
    array('id' =>  9842, 'name' => 'Miniature Electronics',          'quantity' => 39840),
    array('id' =>  2463, 'name' => 'Nanites',                        'quantity' => 62280),
    array('id' =>  2321, 'name' => 'Polyaramids',                    'quantity' => 72000),
    array('id' =>  3695, 'name' => 'Polytextiles',                   'quantity' => 39840),
    array('id' =>  2398, 'name' => 'Reactive Metals',                'quantity' => 79680),
    array('id' =>  9830, 'name' => 'Rocket Fuel',                    'quantity' => 36000),
    array('id' =>  3697, 'name' => 'Silicate Glass',                 'quantity' => 72000),
    array('id' =>  9838, 'name' => 'Superconductors',                'quantity' => 39840),
    array('id' =>  2312, 'name' => 'Supertensile Plastics',          'quantity' => 72000),
    array('id' =>  3691, 'name' => 'Synthetic Oil',                  'quantity' => 66120),
    array('id' =>  2319, 'name' => 'Test Cultures',                  'quantity' => 62280),
    array('id' =>  9840, 'name' => 'Transmitter',                    'quantity' => 72000),
    array('id' =>  3775, 'name' => 'Viral Agent',                    'quantity' => 39840),
    array('id' =>  3645, 'name' => 'Water',                          'quantity' => 79680),
    array('id' =>  2328, 'name' => 'Water-Cooled CPU',               'quantity' => 62280),
);
?>


<?php function __dump_jita_prices($jita) { ?>
<button class="btn btn-default" type="button" data-toggle="modal" data-target="#showJitaPrices">Цены в Jita</button>
<!-- Modal -->
<div class="modal fade" id="showJitaPrices" tabindex="-1" role="dialog" aria-labelledby="showJitaPricesLabel">
 <div class="modal-dialog" role="document">
  <div class="modal-content">
   <div class="modal-header">
     <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
     <h4 class="modal-title" id="showJitaPricesLabel">Цены в Jita на планетарку</h4>
   </div>
   <div class="modal-body">
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th></th>
  <th>Items</th>
  <th style="text-align: right;">Jita Sell</mark></th>
  <th style="text-align: right;">Jita Buy</th>
 </tr>
</thead>
<tbody>
<?php
    $last_market_group_id = 0;
    if ($jita)
        foreach ($jita as $product)
        {
            $market_group_id = $product['mgid'];
            $tid = $product['id'];
            $nm = $product['name'];
            $jita_sell = $product['js'];
            $jita_buy = $product['jb'];

            if ($last_market_group_id != $market_group_id)
            {
                $last_market_group_id = $market_group_id;
                switch ($market_group_id)
                {
                case 1333: $market_group_name = "Raw Planetary Materials"; break;
                case 1334: $market_group_name = "Processed Planetary Materials"; break;
                case 1335: $market_group_name = "Refined Planetary Materials"; break;
                case 1336: $market_group_name = "Specialized Planetary Materials"; break;
                case 1337: $market_group_name = "Advanced Planetary Materials"; break;
                default: $market_group_name = "Unknown";
                }
                ?>
                <tr><td class="active" colspan="4"><strong><?=$market_group_name?></strong></tr>
                <?php
            }
?>
<tr>
 <td><img class="icn24" src="<?=__get_img_src($tid,32,FS_RESOURCES)?>" width="24px" height="24px"></td>
 <td><?=$nm?> <a data-target="#" role="button" data-copy="<?=$nm?>" class="qind-copy-btn" data-source="table" data-toggle="tooltip" data-original-title="" title=""><span class="glyphicon glyphicon-copy" aria-hidden="true"></span></a>
 </td>
 <td align="right"><?=number_format($jita_sell,2,'.',',')?></td>
 <td align="right"><?=number_format($jita_buy,2,'.',',')?></td>
</tr>
<?php
        }
?>
</tbody>
</table>
   </div>
   <div class="modal-footer">
    <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
   </div>
  </div>
 </div>
</div>
<!-- Modal -->
<?php } ?>


<?php function __dump_planetary_stock_item($tid, $nm, $calculate_quantities, $quantity, $required_quantity) {
    $warnings = '';
    if (is_null($required_quantity))
        $warnings .= '<span class="label label-danger">not planned for use</span>&nbsp;';
?>
<tr>
 <td><img class="icn32" src="<?=__get_img_src($tid,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
 <td><?=$nm.'<br><span class="text-muted">'.$tid.'</span> '.$warnings?></td>
 <td align="right"><?php if (!$calculate_quantities) { ?><?=number_format($quantity,0,'.',',')?><?php } else { __dump_progress_element($quantity, $required_quantity); } ?></td>
</tr>
<?php } ?>

 
<?php function __dump_planetary_stock_footer($summary_jita_sell, $summary_jita_buy, $location_requirements) {
    if ($location_requirements)
    {
        foreach ($location_requirements as $x)
            if ($x['quantity'] != 0)
            {
                __dump_planetary_stock_item($x['id'], $x['name'], true, 0, $x['quantity']);
            }
    }
?>
<tr style="font-weight:bold;">
 <td colspan="2"></td>
 <td align="right">Jita Summary: <?=number_format($summary_jita_sell,0,'.',',').'<br>'.number_format($summary_jita_buy,0,'.',',')?></td>
</tr>
<?php } ?>


<?php function __dump_progress_element($current_num, $max_num) {
        $__progress_factor = 100.0;
    if (!is_null($max_num) && $max_num)
        $__progress_factor = 100.0 * $current_num / $max_num;
    $prcnt = ($__progress_factor < 100.001) ? $__progress_factor : 100;
    $prcnt100 = ($current_num == $max_num) ? " progress-bar-success" : (($current_num > $max_num) ? " progress-bar-warning" : "");
    $if_overflow = $current_num < $max_num;
    if ($max_num == $current_num) { ?>
        <strong><span class="text-warning"><?=number_format($current_num,0,'.',',')?></span></strong>
    <?php } else { ?>
        <?=number_format($max_num,0,'.',',')?> - <strong><span class="text-warning"><?=number_format($current_num,0,'.',',')?></span></strong> = <?=$if_overflow?'<span class="text-danger">':''?><?=number_format($max_num-$current_num,0,'.',',')?><?=$if_overflow?'</span>':''?> <a data-target="#" role="button" data-copy="<?=abs($max_num-$current_num)?>" class="qind-copy-btn" data-source="table" data-toggle="tooltip" data-original-title="" title=""><span class="glyphicon glyphicon-copy" aria-hidden="true"></span></a>
    <?php } ?>
<br>
<div class="progress" style="margin-bottom:0px"><div class="progress-bar<?=$prcnt100?>" role="progressbar"
     aria-valuenow="<?=$prcnt?>" aria-valuemin="0" aria-valuemax="100" style="width: <?=$prcnt?>%;"><?=number_format($__progress_factor,1,'.',',')?>%</div></div>
<?php } ?>


<?php function __dump_planetary_stock($planetary, $jita) { ?>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th style="width:32px"></th>
  <th width="100%">Items</th>
  <th style="text-align:right; min-width:200px">Quantity</mark></th>
 </tr>
</thead>
<tbody>
<?php
    global $product_requirements;

    $summary_jita_sell = 0;
    $summary_jita_buy = 0;
    $location_jita_sell = 0;
    $location_jita_buy = 0;
    $location_requirements = null;
    $last_location_id = 0;
    $calculate_quantities = false;
    if ($planetary)
        foreach ($planetary as $product)
        {
            $tid = $product['id'];
            $nm = $product['name'];
            $quantity = $product['q'];
            $location_id = $product['lid'];
            $location_flag = $product['f'];

            $found = false;
            foreach ($jita as $j)
            {
                if ($j['id'] != $tid) continue;
                $jita_sell = $j['js'];
                $jita_buy = $j['jb'];
                $found = true;
                break;
            }
            if ($found)
            {
                $location_jita_sell += $jita_sell * $quantity;
                $location_jita_buy += $jita_buy * $quantity;
                $summary_jita_sell += $jita_sell * $quantity;
                $summary_jita_buy += $jita_buy * $quantity;
            }

            if ($last_location_id != $location_id)
            {
                if ($last_location_id != 0)
                {
                    __dump_planetary_stock_footer(
                        $location_jita_sell,
                        $location_jita_buy,
                        $calculate_quantities ? $location_requirements : null
                    );
                }
                $location_requirements = null;
                $location_requirements = array();
                $location_requirements = $product_requirements;
                $location_jita_sell = 0;
                $location_jita_buy = 0;
                $last_location_id = $location_id;
                switch ($location_id)
                {
                case 1037088632771: $location_name = "Stock planet 1"; break;
                case 1037161379493: $location_name = "Stock planet 2"; break;
                case 1037111988366: $location_name = "Stock"; break;
                case 1030492564838: $location_name = "Ангар №".substr($location_flag, -1)." корпоративного офиса"; break;
                default:
                    if ($location_flag == "CorpDeliveries")
                        $location_name = $location_flag." в ".$location_id;
                    else
                        $location_name = "Unknown".$location_id.' '.$location_flag;
                }
                ?>
                <tr><td class="active" colspan="3"><strong><?=$location_name?></strong></tr>
                <?php
            }

            $calculate_quantities =
                $location_id == 1037088632771 ||
                $location_id == 1037161379493 ||
                $location_id == 1037111988366;
            $required_quantity = null;
            foreach ($location_requirements as &$x)
            {
                if ($x['id'] != $tid) continue;
                $required_quantity = $x['quantity'];
                $x['quantity'] = 0;
                break;
            }
            unset($x);

            __dump_planetary_stock_item($tid, $nm, $calculate_quantities, $quantity, $required_quantity);
        }
    __dump_planetary_stock_footer(
        $location_jita_sell,
        $location_jita_buy,
        $calculate_quantities ? $location_requirements : null
    );
?>
</tbody>
</table>
<?php
} ?>



<?php
    __dump_header("Professor' Planetary", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
select
 a.eca_type_id as id,
 tid.sdet_type_name as name,
 a.sum_quantity as q,
 a.eca_location_id as lid,
 a.eca_location_flag as f
from (
 select
  eca_type_id,
  eca_location_id,
  eca_location_flag,
  sum(eca_quantity) as sum_quantity
 from qi.esi_corporation_assets
 where eca_corporation_id = 2053528477
 group by 1, 2, 3
) a
 left outer join qi.eve_sde_type_ids tid on (a.eca_type_id = tid.sdet_type_id)
where
 tid.sdet_market_group_id in (1333, 1334, 1335, 1336, 1337) -- планетарка
order by a.eca_location_id, a.eca_location_flag, tid.sdet_market_group_id, tid.sdet_type_name;
EOD;
    $planetary_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $planetary = pg_fetch_all($planetary_cursor);
    //---
    $query = <<<EOD
select 
 tid.sdet_market_group_id as mgid,
 jita.ethp_type_id as id,
 tid.sdet_type_name as name,
 jita.ethp_sell as js,
 jita.ethp_buy as jb 
from qi.esi_trade_hub_prices jita
 left outer join qi.eve_sde_type_ids tid on (jita.ethp_type_id = tid.sdet_type_id)
where
  jita.ethp_location_id = 60003760 and
  tid.sdet_market_group_id in (1333, 1334, 1335, 1336, 1337) -- планетарка
order by 1, 3;
EOD;
    $jita_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $jita = pg_fetch_all($jita_cursor);
    //---
    pg_close($conn);
?>
<div class="container">
 <?php __dump_jita_prices($jita); ?>
 <?php __dump_planetary_stock($planetary, $jita); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>

<script>
  $(document).ready(function(){
    // Working with clipboard
    $('a.qind-copy-btn').each(function() {
      $(this).tooltip();
    })
    $('a.qind-copy-btn').bind('click', function () {
      var data_copy = $(this).attr('data-copy');
      if (data_copy === undefined) {
        var data_source = $(this).attr('data-source');
        if (data_source == 'table') {
          var tr = $(this).parent().parent();
          var tbody = tr.parent();
          var rows = tbody.children('tr');
          var start_row = rows.index(tr);
          data_copy = '';
          rows.each( function(idx) {
            if (!(start_row === undefined) && (idx > start_row)) {
              var td = $(this).find('td').eq(0);
              if (!(td.attr('class') === undefined))
                start_row = undefined;
              else {
                if (data_copy) data_copy += "\n"; 
                data_copy += td.find('a').attr('data-copy') + "\t" + $(this).find('td').eq(1).attr('quantity');
              }
            }
          });
        } else if (data_source == 'span') {
          var div = $(this).parent();
          var spans = div.children('span');
          data_copy = '';
          spans.each( function(idx) {
            var span = $(this);
            if (data_copy) data_copy += "\n";
            var txt = span.text();
            data_copy += txt.substring(txt.indexOf(' x ')+3) + "\t" + span.attr('quantity');
          });
        }
      }
      // var $temp = $("<textarea>");
      // $("body").append($temp);
      // $temp.val(data_copy).select();
      // try {
      //   success = document.execCommand("copy");
      //   if (success) {
      //     $(this).trigger('copied', ['Copied!']);
      //   }
      // } finally {
      //   $temp.remove();
      // }
      navigator.clipboard.writeText(data_copy).then(() => {
        $(this).trigger('copied', ['Copied!']);
      }, (e) => {
        // on error
      });
      document.execCommand("copy");
    });
    $('a.qind-copy-btn').bind('copied', function(event, message) {
      $(this).attr('title', message)
        .tooltip('fixTitle')
        .tooltip('show')
        .attr('title', "Copy to clipboard")
        .tooltip('fixTitle');
    });
    if( /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ) {
      // какой-то код ...
      $('a.qind-copy-btn').each(function() {
        $(this).addClass('hidden');
      })
    }
  });
</script>
