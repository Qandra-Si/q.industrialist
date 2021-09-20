<?php
include 'qi_render_html.php';
include_once '.settings.php';


$product_requirements = array(
    array( 'id' =>  2329, 'q' => 72000 ), // Biocells
    array( 'id' =>  3828, 'q' => 66120 ), // Construction Blocks
    array( 'id' =>  9836, 'q' => 26280 ), // Consumer Electronics
    array( 'id' =>  9832, 'q' => 26280 ), // Coolant
    array( 'id' =>    44, 'q' => 36000 ), // Enriched Uranium
    array( 'id' =>  3693, 'q' => 66120 ), // Fertilizer
    array( 'id' => 15317, 'q' => 36000 ), // Genetically Enhanced Livestock
    array( 'id' =>  3725, 'q' => 66120 ), // Livestock
    array( 'id' =>  2327, 'q' => 72000 ), // Microfiber Shielding
    array( 'id' =>  9842, 'q' => 39840 ), // Miniature Electronics
    array( 'id' =>  2463, 'q' => 62280 ), // Nanites
    array( 'id' =>  2321, 'q' => 72000 ), // Polyaramids
    array( 'id' =>  3695, 'q' => 39840 ), // Polytextiles
    array( 'id' =>  2398, 'q' => 79680 ), // Reactive Metals
    array( 'id' =>  9830, 'q' => 36000 ), // Rocket Fuel
    array( 'id' =>  3697, 'q' => 72000 ), // Silicate Glass
    array( 'id' =>  9838, 'q' => 39840 ), // Superconductors
    array( 'id' =>  2312, 'q' => 72000 ), // Supertensile Plastics
    array( 'id' =>  3691, 'q' => 66120 ), // Synthetic Oil
    array( 'id' =>  2319, 'q' => 62280 ), // Test Cultures
    array( 'id' =>  9840, 'q' => 72000 ), // Transmitter
    array( 'id' =>  3775, 'q' => 39840 ), // Viral Agent
    array( 'id' =>  3645, 'q' => 79680 ), // Water
    array( 'id' =>  2328, 'q' => 62280 ), // Water-Cooled CPU
);
$show_debug = 0;


function get_clipboard_copy_button($data_copy) {
    return ' <a data-target="#" role="button" data-copy="'.$data_copy.'" class="qind-copy-btn" data-toggle="tooltip" data-original-title="" title=""><span class="glyphicon glyphicon-copy" aria-hidden="true"></a>';
}


function get_market_group_id_name($market_group_id) {
    switch ($market_group_id)
    {
    case 1333: return "Raw Planetary Materials (P0)";
    case 1334: return "Processed Planetary Materials (P1)";
    case 1335: return "Refined Planetary Materials (P2)";
    case 1336: return "Specialized Planetary Materials (P3)";
    case 1337: return "Advanced Planetary Materials (P4)";
    default: return "Unknown";
    }
}


function __dump_jita_prices(&$planetary, &$jita) { ?>
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
  <th style="width:32px"></th>
  <th width="100%">Items</th>
  <th style="text-align: right;">Jita Sell</mark></th>
  <th style="text-align: right;">Jita Buy</th>
 </tr>
</thead>
<tbody>
<?php
    $last_market_group_id = 0;
    if ($planetary && $jita)
        foreach ($planetary as $product)
        {
            $market_group_id = $product['mgid'];
            $tid = $product['id'];
            $nm = $product['name'];

            $found = false;
            foreach ($jita as $j)
            {
                if ($j['id'] != $tid) continue;
                $jita_sell = $j['js'];
                $jita_buy = $j['jb'];
                $found = true;
                break;
            }

            if ($last_market_group_id != $market_group_id)
            {
                $last_market_group_id = $market_group_id;
                ?><tr><td class="active" colspan="4"><strong><?=get_market_group_id_name($market_group_id)?></strong></tr><?php
            }
?>
<tr>
 <td><img class="icn24" src="<?=__get_img_src($tid,32,FS_RESOURCES)?>" width="24px" height="24px"></td>
 <td><?=$nm?><?=get_clipboard_copy_button($nm)?></td>
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
<?php
}


function calculate_market_p2_payments(&$wallet_journals, &$market_payments, &$market_cycles) {
    global $product_requirements;
    global $show_debug;

    $market_dates = array();

    $prev_tid = null;
    $required_quantity = null;
    $current_cycle_quantity = null;
    $current_cycle_payment = null;
    $current_cycle_number = null;
    if ($market_payments)
        foreach ($market_payments as $payment)
        {
            $tid = intval($payment['id']);
            $date = $payment['dt'];
            $sum_buy = intval($payment['sb']);
            $sum_quantity = intval($payment['sc']);

            // определяем, каков план по закупке этого продукта?
            if ($prev_tid != $tid)
            {
                $prev_tid = $tid;
                $current_cycle_quantity = 0;
                $rq_key = array_search($tid, array_column($product_requirements, 'id'));
                if ($rq_key !== false)
                {
                    $required_quantity = $product_requirements[$rq_key]['q'];
                    $current_cycle_quantity = $required_quantity;
                    $current_cycle_payment = 0;
                    $current_cycle_number = 0;
		    if ($show_debug) print('<hr><small>Поиск данных по продукту '.$tid.' с требуемым кол-вом '.$required_quantity.'</small><br>');
                }
                else
                    $required_quantity = null;
            }
            // если нет планов по закупу текущего продукта - пропускаем расчёт по нему
            if (is_null($required_quantity)) continue;

            $avg_sum_buy = $sum_buy / $sum_quantity;

            // суммируем количество закупленного продукта
            // суммируем сумму закупа как усредённое за текущие сутки
            do
            {
                if ($sum_quantity < $current_cycle_quantity)
                {
                    $current_cycle_quantity -= $sum_quantity;
                    $current_cycle_payment += $avg_sum_buy * $sum_quantity;
		    if ($show_debug) print('<small>'.$date.' '.$sum_buy.' '.$sum_quantity.' = <mark>'.number_format($avg_sum_buy,2,'.','').'</mark> '.$current_cycle_quantity.' = <span class="text-danger">'.number_format($current_cycle_payment,2,'.','').'</span></small><br>');
                    $sum_quantity = 0;
                }
                else
                {
                    $current_cycle_payment += $avg_sum_buy * $current_cycle_quantity;
                    if ($show_debug) print('<small><b>'.$date.' '.$sum_buy.' '.$sum_quantity.' = <mark>'.number_format($avg_sum_buy,2,'.','').'</mark> '.($current_cycle_quantity-$sum_quantity).' = <span class="text-danger">'.number_format($current_cycle_payment,2,'.','').'</span></b></small><br>');
                    // сохраняем результат
                    array_push($market_dates, array(intval($tid), intval($current_cycle_number), strtotime($date), intval(ceil($current_cycle_payment)), 0));
                    $current_cycle_number++;
                    // повторяем цикл
                    $sum_quantity -= $current_cycle_quantity;
                    // начинаем сначала
                    $current_cycle_quantity = $required_quantity;
                    $current_cycle_payment = 0;
                }
            } while($sum_quantity > 0);
        }

    if ($wallet_journals && $market_dates)
        foreach ($wallet_journals as $event)
        {
            $type = $event['tp'];
            if ($type != 'f') continue; // комиссия
            $date = $event['dt'];
            $amount = $event['isk'];

            $date_num = strtotime($date);
	    $payments_per_date = 0;
	    foreach ($market_dates as &$md)
	    {
	        if ($md[2] != $date_num) continue;
                $payments_per_date += $md[3];
	    }

            if ($show_debug)  print('<hr><small>'.$date.' комиссия '.number_format(-$amount,2,'.','').' по платежам '.$payments_per_date.'</small><br>');

            $fee_per_date = -$amount / $payments_per_date;
            foreach ($market_dates as &$md)
	    {
	        if ($md[2] != $date_num) continue;
		$md[4] = $fee_per_date * $md[3];
		if ($show_debug) print('<small>'.$md[0].' платёж '.$md[3].' с комиссией '.number_format($md[4],2,'.','').'</small><br>');
	    }
        }

//debug : print(var_dump($market_dates));

    if ($market_dates)
    {
        $market_cycles = array();
        $current_cycle_number = 0;
        $current_cycle_finish = null;
        do
        {
	    if ($show_debug) print('<hr><small>Поиск платежей по циклу '.$current_cycle_number.'</small><br>');
            $current_cycle_payment = 0;
	    $current_cycle_fee = 0;
            $current_cycle_finished = true;
            // для каждого нового цикла считаем его стоимость 
            foreach ($product_requirements as $r)
            {
                $tid = $r['id'];
                foreach($market_dates as $md)
                {
                    if ($tid == $md[0] && $current_cycle_number == $md[1])
                    {
                        $current_cycle_payment += $md[3];
			$current_cycle_fee += $md[4];
                        if ($current_cycle_finish < $md[2])
                            $current_cycle_finish = $md[2];
		        if ($show_debug) print('<small><small>'.$tid.' '.date("Y-m-d", $md[2]).' = '.$md[3].' / '.number_format($md[4],2,'.','').' = <span class="text-danger">'.$current_cycle_payment.' / '.number_format($current_cycle_fee,2,'.','').'</span></small></small><br>');
                        break;
                    }
                    if ($md[0] > $tid)
                    {
                        if ($show_debug) print('<small>'.$tid.' NOT FOUND on '.$md[0].'</small><br>');
                        $current_cycle_finished = false;
                        break;
                    }
                }
            }
            // циклы закончились совсем - нет даже платежей по ним
            if (!$current_cycle_payment) break;
            // выводим результат по каждому из циклов
            if ($show_debug)  print('<small><b>cycle#'.$current_cycle_number.' buy='.number_format($current_cycle_payment,0,'.','').' fee='.number_format($current_cycle_fee,0,'.','').' at '.date("Y-m-d", $current_cycle_finish).'</b></small><br>');
            // сохраняем результат
            array_push($market_cycles, array(intval($current_cycle_number), intval($current_cycle_finish), intval($current_cycle_payment), $current_cycle_finished, $current_cycle_fee));
            $current_cycle_number++;
        } while(1);
    }
}


function __dump_wallet_journals(&$wallet_journals, &$market_payments) { ?>
<button class="btn btn-default" type="button" data-toggle="modal" data-target="#showWalletJournals">Бухгалтерия</button>
<!-- Modal -->
<div class="modal fade" id="showWalletJournals" tabindex="-1" role="dialog" aria-labelledby="showWalletJournalsLabel">
 <div class="modal-dialog modal-lg" role="document">
  <div class="modal-content">
   <div class="modal-header">
     <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
     <h4 class="modal-title" id="showWalletJournalsLabel">Финансовая отчётность</h4>
   </div>
   <div class="modal-body">
    <div class="row">
     <div class="col-md-6">
<h3>Ежедневные финансовые операции</h3>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th>Дата</th>
  <th>Операция</th>
  <th style="text-align: right;">Производственный отдел</mark></th>
  <th style="text-align: right;">Финансовый отдел</th>
 </tr>
</thead>
<tbody>
<?php
    $prev_date = null;
    if ($wallet_journals)
        foreach ($wallet_journals as $event)
        {
            $date = $event['dt'];
            $corporation_id = $event['c'];
            $amount = $event['isk'];
            $type = $event['tp'];

            if ($type == 't')
                $type = 'перевод';
            else if ($type == 'f')
                $type = 'комиссия';
            else if ($type == 'e')
                $type = 'эскроу';
            else if ($type == 's')
                $type = 'продажа';
            else if ($type == 'b') {
                $type = 'закупка';
                $amount = -$amount;
            }
?>
<tr>
 <td><?=($prev_date==$date)?'':$date?></td>
 <td><?=$type?></td>
 <?php if ($corporation_id == 2053528477) { ?>
  <td align="right"<?=($amount<0)?' class="text-danger"':''?>><?=number_format($amount,2,'.',',')?></td>
  <td></td>
 <?php } else { ?>
  <td></td>
  <td align="right"<?=($amount<0)?' class="text-danger"':''?>><?=number_format($amount,2,'.',',')?></td>
 <?php }?>
</tr>
<?php
            $prev_date = $date;
        }
?>
</tbody>
</table>
     </div> <!-- col-md-6 -->
     <div class="col-md-6">
<h3>Циклы закупки планетарки</h3>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th>Дата</th>
  <th>Цикл</th>
  <th style="text-align: right;">Стоимость закупки</th>
  <th style="text-align: right;">Комиссия</th>
 </tr>
</thead>
<tbody>
<?php
    $market_cycles = null;
    calculate_market_p2_payments($wallet_journals, $market_payments, $market_cycles);

    if ($market_cycles)
        foreach ($market_cycles as $cycle)
        {
            $cycle_num = $cycle[0];
            $cycle_finish = $cycle[1];
            $cycle_payments = $cycle[2];
            $cycle_finished = $cycle[3];
	    $cycle_fee = $cycle[4];

            $labels = '';
            if ($cycle_finished)
                $labels .= ' <span class="label label-success">finished</span>';
?>
<tr>
 <td><?=date("Y-m-d", $cycle_finish)?></td>
 <td><?=$cycle_num.$labels?></td>
 <td align="right"><?=number_format($cycle_payments,0,'.',',')?></td>
 <td align="right"><?=number_format($cycle_fee,0,'.',',')?></td>
</tr>
<?php
        }
?>
</tbody>
</table>
     </div> <!-- col-md-6 -->
    </div> <!-- row -->
   </div>
   <div class="modal-footer">
    <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
   </div>
  </div>
 </div>
</div>
<!-- Modal -->
<?php
}


function __dump_market_orders(&$active_orders, &$planetary, &$jita) { ?>
<button class="btn btn-default" type="button" data-toggle="modal" data-target="#showMarketOrders">Рыночные сделки</button>
<!-- Modal -->
<div class="modal fade" id="showMarketOrders" tabindex="-1" role="dialog" aria-labelledby="showMarketOrdersLabel">
 <div class="modal-dialog modal-lg" role="document">
  <div class="modal-content">
   <div class="modal-header">
     <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
     <h4 class="modal-title" id="showMarketOrdersLabel">Рыночные сделки</h4>
   </div>
   <div class="modal-body">
    <div class="row">
     <div class="col-md-6">
<h3>Активные ордера на покупку</h3>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th style="width:32px"></th>
  <th width="100%">Планетарка</th>
  <th style="text-align: right;">Кол-во</th>
  <th style="text-align: right;">Закупочная<br>цена</mark></th>
  <th style="text-align: right;">Jita Sell/Buy</mark></th>
 </tr>
</thead>
<tbody>
<?php
    $prev_type_id = 0;
    if ($active_orders)
        foreach ($active_orders as $order)
        {
	    $is_buy = $order['b'] == 't';
	    if ($is_buy == false) continue;
            $tid = intval($order['id']);
            $price = $order['p'];
            $remaining = $order['r'];

            $nm = '';
            foreach ($planetary as $p)
            {
                //$market_group_id = intval($p['mgid']);
                if ($tid != $p['id']) continue;
                $nm = $p['name'];
                break;
            }

            $found = false;
            foreach ($jita as $j)
            {
                if ($j['id'] != $tid) continue;
                $jita_sell = $j['js'];
                $jita_buy = $j['jb'];
                $found = true;
                break;
            }
?>
<tr>
 <?php if ($prev_type_id != $tid) { $prev_type_id = $tid; ?>
  <td><img class="icn24" src="<?=__get_img_src($tid,32,FS_RESOURCES)?>" width="24px" height="24px"></td>
  <td><?=$nm?><?=get_clipboard_copy_button($nm)?></td>
 <?php } else { ?>
  <td colspan="2"></td>
 <?php } ?>
 <td align="right"><?=number_format($remaining,0,'.',',')?></td>
 <td align="right" class="text-<?=($price>$jita_buy)?'danger':(($price==$jita_buy)?'warning':'success')?>"><?=number_format($price,2,'.',',')?></td>
 <td align="right"><?=number_format($jita_sell,2,'.',',')?><br><?=number_format($jita_buy,2,'.',',')?></td>
</tr>
<?php
        }
?>
</tbody>
</table>
     </div> <!-- col-md-6 -->
     <div class="col-md-6">
<h3>Активные ордера на продажу</h3>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th style="width:32px"></th>
  <th width="100%">Планетарка</th>
  <th style="text-align: right;">Кол-во</th>
  <th style="text-align: right;">Продажная<br>цена</mark></th>
  <th style="text-align: right;">Jita Sell/Buy</mark></th>
 </tr>
</thead>
<tbody>
<?php
    $prev_type_id = 0;
    if ($active_orders)
        foreach ($active_orders as $order)
        {
	    $is_buy = $order['b'] == 't';
	    if ($is_buy == true) continue;
            $tid = intval($order['id']);
            $price = $order['p'];
            $remaining = $order['r'];

            $nm = '';
            foreach ($planetary as $p)
            {
                //$market_group_id = intval($p['mgid']);
                if ($tid != $p['id']) continue;
                $nm = $p['name'];
                break;
            }

            $found = false;
            foreach ($jita as $j)
            {
                if ($j['id'] != $tid) continue;
                $jita_sell = $j['js'];
                $jita_buy = $j['jb'];
                $found = true;
                break;
            }
?>
<tr>
 <?php if ($prev_type_id != $tid) { $prev_type_id = $tid; ?>
  <td><img class="icn24" src="<?=__get_img_src($tid,32,FS_RESOURCES)?>" width="24px" height="24px"></td>
  <td><?=$nm?><?=get_clipboard_copy_button($nm)?></td>
 <?php } else { ?>
  <td colspan="2"></td>
 <?php } ?>
 <td align="right"><?=number_format($remaining,0,'.',',')?></td>
 <td align="right" class="text-<?=($price>$jita_sell)?'danger':(($price==$jita_sell)?'warning':'success')?>"><?=number_format($price,2,'.',',')?></td>
 <td align="right"><?=number_format($jita_sell,2,'.',',')?><br><?=number_format($jita_buy,2,'.',',')?></td>
</tr>
<?php
        }
?>
</tbody>
</table>
     </div> <!-- col-md-6 -->
    </div> <!-- row -->
   </div>
   <div class="modal-footer">
    <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
   </div>
  </div>
 </div>
</div>
<!-- Modal -->
<?php
}


function __dump_progress_element($current_num, $max_num) {
    $__progress_factor = 100.0;
    if (!is_null($max_num) && $max_num)
        $__progress_factor = 100.0 * $current_num / $max_num;
    $prcnt = round(($__progress_factor < 100.001) ? $__progress_factor : 100, 1);
    $prcnt100 =
        ($current_num == $max_num) ?
	" progress-bar-success" :
	(   ($current_num > $max_num) ?
	    (   ($current_num > (2*$max_num)) ?
	        " progress-bar-danger" :
		" progress-bar-warning"
	    ) :
	    ""
	);
    if ($max_num == $current_num) { ?>
        <strong><span class="text-warning"><?=number_format($current_num,0,'.',',')?></span></strong>
    <?php } else if ($current_num > $max_num) { ?>
        <?=number_format($max_num,0,'.',',')?> - <strong><span class="text-warning"><?=number_format($current_num,0,'.',',')?></span></strong> = <?=number_format($max_num-$current_num,0,'.',',')?><?=get_clipboard_copy_button(abs($max_num-$current_num))?>
    <?php } else { ?>
        <?=number_format($max_num,0,'.',',')?> - <strong><span class="text-warning"><?=number_format($current_num,0,'.',',')?></span></strong> = <span class="text-danger"><?=number_format($max_num-$current_num,0,'.',',')?></span><?=get_clipboard_copy_button(abs($max_num-$current_num))?>
    <?php } ?>
<br>
<div class="progress" style="margin-bottom:0px"><div class="progress-bar<?=$prcnt100?>" role="progressbar"
     aria-valuenow="<?=$prcnt?>" aria-valuemin="0" aria-valuemax="100" style="width: <?=$prcnt?>%;"><?=number_format($__progress_factor,1,'.',',')?>%</div></div>
<?php }


function __dump_planetary_stock_item($tid, $nm, $calculate_quantities, $quantity, $required_quantity, $volume, $we_buy_it) {
    $warnings = '';
    if (is_null($required_quantity))
        $warnings .= '<span class="label label-danger">not planned for use</span>&nbsp;';
    else if (!$we_buy_it && ($quantity != $required_quantity))
        $warnings .= '<span class="label label-warning">we don&apos;t buy it</span>&nbsp;';
?>
<tr>
 <td><img class="icn32" src="<?=__get_img_src($tid,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
 <td><?=$nm.($calculate_quantities?get_clipboard_copy_button($nm):'').'<br><span class="text-muted">'.$tid.'</span> '.$warnings?></td>
 <td align="right"<?php if (!$calculate_quantities) { ?>><?=number_format($quantity,0,'.',',')?><?php }
 else if ($quantity >= $required_quantity) { ?>><?php __dump_progress_element($quantity, $required_quantity); ?><?php }
 else { ?> quantity="<?=($required_quantity-$quantity)?>"><?php __dump_progress_element($quantity, $required_quantity); ?><?php } ?>
 </td>
 <td align="right"><?=number_format($volume,0,'.',',')?></td>
</tr>
<?php
}


$planetary_stock_header = 0;


function __dump_planetary_stock_header($location_name, $calculated_requirements) {
    global $planetary_stock_header;
    $planetary_stock_header++;
?>
<div class="panel panel-default">
 <div class="panel-heading" role="tab" id="heading<?=$planetary_stock_header?>">
  <h3 class="panel-title">
   <a role="button" data-toggle="collapse" data-parent="#accordion" href="#collapse<?=$planetary_stock_header?>" aria-expanded="true" aria-controls="collapse<?=$planetary_stock_header?>"><?=$location_name?></a>
  </h3>
<?php
    if (!is_null($calculated_requirements)) {
        $prcnt = round($calculated_requirements, 1);
        $prcnt100 =
	    ($calculated_requirements == 100.0) ?
	    " progress-bar-success" :
	    (   ($calculated_requirements > 100.0) ?
	        " progress-bar-warning" :
		""
            );
?>    
<div class="progress" style="margin-bottom:0px"><div class="progress-bar<?=$prcnt100?>" role="progressbar"
     aria-valuenow="<?=$prcnt?>" aria-valuemin="0" aria-valuemax="100" style="width: <?=$prcnt?>%;"><?=number_format($calculated_requirements,1,'.',',')?>%</div></div>
<?php } ?>
 </div>
 <div id="collapse<?=$planetary_stock_header?>" class="panel-collapse collapse" role="tabpanel" aria-labelledby="heading<?=$planetary_stock_header?>">
  <div class="panel-body">
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th style="width:32px"></th>
  <th width="100%">Items</th>
  <th style="text-align:right; min-width:200px">Quantity</mark></th>
  <th style="text-align:right">Volume,&nbsp;m³</mark></th>
 </tr>
</thead>
<tbody>
<?php
}


function __dump_planetary_market_group($market_group_id, $calculate_quantities) { ?>
<tr><td class="active" colspan="4"> <?=get_market_group_id_name($market_group_id)?><?php if ($calculate_quantities) { ?> <a data-target="#" role="button" class="qind-copy-btn" data-source="table" data-toggle="tooltip" data-original-title="" title=""><button type="button" class="btn btn-default btn-xs"><span class="glyphicon glyphicon-copy" aria-hidden="true"></span> Export to multibuy</button></a><?php } ?></tr>
<?php
}


function __dump_planetary_stock_footer($summary_jita_sell, $summary_jita_buy, $summary_volume) { ?>
<tr style="font-weight:bold;">
 <td colspan="2"></td>
 <td align="right">Jita Summary: <?=number_format($summary_jita_sell,0,'.',',').'<br>'.number_format($summary_jita_buy,0,'.',',')?></td>
 <td align="right"><?=number_format($summary_volume,0,'.',',')?>&nbsp;m³</td>
</tr>
</tbody>
</table>
  </div> <!-- panel-body -->
 </div> <!-- panel-collapse -->
</div> <!-- panel -->
<?php
}


function __dump_planetary_stock_location($location_id, &$location_flag, &$products_in_location, &$planetary, &$jita, &$active_orders)
{
    global $product_requirements;

    // debug:print($location_id.' '.$location_flag); var_dump($products_in_location); print('<br><br><br>');

    // для начала надо определиться - выводим ли мы содержимое коробки вразнобой (с учётом
    // недостающих материалов), или же выводим в порядке P0, P1, P2,... и перемещаем вывод
    // материалами, которых нет в коробке?
    $calculate_quantities =
        $location_id == 1037088632771 ||
        $location_id == 1037161379493 ||
        $location_id == 1037088203784 ||
        $location_id == 1037175000957 ||
        $location_id == 1037111988366 ||
        $location_id == 1037199511547;
    // выполняем предвариетьный расчёт достаточности материалов в коробке
    $calculated_requirements = null;
    if ($calculate_quantities)
    {
        $calculated_requirements = 100.0;
	// перебор требований и проверка наличия, расчёт достаточности в %
        $required_quantity = null;
        foreach ($product_requirements as $r)
        {
	    $tid = intval($r['id']);
            $required_quantity = $r['q'];
            $quantity = 0;
            foreach ($products_in_location as $l)
            {
                if ($l[0] != $tid) continue;
                $quantity = $l[1];
                break;
            }
	    if ($quantity == 0)
	    {
	        $calculated_requirements = 0;
		break;
	    }
	    $percent = 100.0 * ($quantity / $required_quantity);
	    if ($percent < $calculated_requirements)
                $calculated_requirements = $percent;
        }
    }

    // поскольку на сервере пока нет сведений о названиях коробок (и они не актуализируются)
    // прописываем дальше их вручную
    $location_name = null;
    switch ($location_id)
    {
    case 1037088632771: $location_name = "Stock planet 1"; break;
    case 1037161379493: $location_name = "Stock planet 2"; break;
    case 1037088203784: $location_name = "Stock planet 3"; break;
    case 1037175000957: $location_name = "Stock planet 4"; break;
    case 1037199511547: $location_name = "Stock planet 5"; break;
    case 1037111988366: $location_name = "Stock"; break;
    case 1030492564838: $location_name = "Ангар №".substr($location_flag, -1)." корпоративного офиса"; break;
    default:
        if ($location_flag == "CorpDeliveries")
            $location_name = $location_flag." в ".$location_id;
        else
            $location_name = "Unknown ".$location_id.' '.$location_flag;
    }

    __dump_planetary_stock_header($location_name, $calculated_requirements);

    // выделяем память для summary-расчётов
    $location_jita_sell = 0;
    $location_jita_buy = 0;
    $location_volume = 0.0;
    // ...и временных переменных
    $prev_market_group_id = 0;

    // элементы в массиве planetary отсортированы в порядке P0, P1, P2, ...
    // в остальных списках они следуют вразонбой
    foreach ($planetary as $product)
    {
        $market_group_id = intval($product['mgid']);
        $tid = intval($product['id']);
        $nm = $product['name'];
        $volume = 0.0;

        // поиск имеющейся в коробке планетарки
        $quantity = 0;
        foreach ($products_in_location as $l)
        {
            if ($l[0] != $tid) continue;
            $quantity = $l[1];
            break;
        }
        // в том случае, если нужного продукта в коробке нет, и считать остатки не надо, - пропускаем шаг
        if ($calculate_quantities == false && $quantity == 0) continue;

        // определяем, выполняется ли закупка этого продукта прямо сейчас?
        $we_buy_it = array_search($tid, array_column($active_orders, 'id')) !== false;

        // поиск сведений о том сколько требуется планетарки в этой коробке?
        $required_quantity = null;
        foreach ($product_requirements as $r)
        {
            if ($r['id'] != $tid) continue;
            $required_quantity = $r['q'];
            break;
        }
        // если считать остатки в коробке надо, но продукт не задан в списке требований, то пропускаем его,
        // если его и нет, иначе если он есть - выводим с маркетом предупреждения
        if ($calculate_quantities == true)
        {
            if ($required_quantity == null && !$quantity) continue;
        }

        // поиск сведений о продукте - название, вес и т.п.
        $nm = '';
        foreach ($planetary as $p)
        {
            if ($p['id'] != $tid) continue;
            $nm = $p['name'];
            $volume = $p['v'];
            break;
        }
        $location_volume += $volume * $quantity;

        if ($prev_market_group_id == 0 || $prev_market_group_id != $market_group_id)
        {
            $prev_market_group_id = $market_group_id;
            __dump_planetary_market_group($market_group_id, $calculate_quantities);
        }
        __dump_planetary_stock_item($tid, $nm, $calculate_quantities, $quantity, $required_quantity, $volume*$quantity, $we_buy_it);

        // поиск сведений о ценах на продукт
        $found = false;
        foreach ($jita as $j)
        {
            if ($j['id'] != $tid) continue;
            $jita_sell = $j['js'];
            $jita_buy = $j['jb'];
            $found = true;
            break;
        }
        // расчёт стоимости всех продуктов в коробке
        if ($found)
        {
            $location_jita_sell += $jita_sell * $quantity;
            $location_jita_buy += $jita_buy * $quantity;
        }
    }

    __dump_planetary_stock_footer($location_jita_sell, $location_jita_buy, $location_volume);
}


function __dump_planetary_stock(&$stock, &$planetary, &$jita, &$active_orders) {
    $summary_jita_sell = 0;
    $summary_jita_buy = 0;
    $location_jita_sell = 0;
    $location_jita_buy = 0;
    $location_requirements = null;
    $calculate_quantities = false;
    if ($stock)
    {
        // собираем группу планетарки, расположенной в одной и той же коробке
        $prev_location_id = 0;
        $prev_location_flag = '';
        $products_in_location = array();
        $stock_size = sizeof($stock) - 1;
        foreach ($stock as $index => &$product)
        {
            $tid = $product['id'];
            $quantity = $product['q'];
            $location_id = intval($product['lid']);
            $location_flag = $product['f'];
            if ($prev_location_id == $location_id && $prev_location_flag == $location_flag)
                array_push($products_in_location, array(intval($tid), intval($quantity)));
            else if ($prev_location_id == 0)
            {
                $prev_location_id = $location_id;
                $prev_location_flag = $location_flag;
                array_push($products_in_location, array(intval($tid), intval($quantity)));
            }
            else
            {
                __dump_planetary_stock_location(
                    $prev_location_id,
                    $prev_location_flag,
                    $products_in_location,
                    $planetary,
                    $jita,
                    $active_orders
                );
                // обнаружена новая группа (новая коробка)
                $prev_location_id = $location_id;
                $prev_location_flag = $location_flag;
                $products_in_location = null;
                $products_in_location = array();
                array_push($products_in_location, array(intval($tid), intval($quantity)));
            }
        }
        __dump_planetary_stock_location(
            $prev_location_id,
            $prev_location_flag,
            $products_in_location,
            $planetary,
            $jita,
            $active_orders
        );
    }
}



    function get_numeric($val) {
        return is_numeric($val) ? ($val + 0) : 0;
    }

    if (isset($_GET['debug'])) {
        $_get_debug = htmlentities($_GET['debug']);
        if (is_numeric($_get_debug))
            $show_debug = get_numeric($_get_debug) ? 1 : 0;
    }

    __dump_header("Professor' Planetary", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
select
 a.eca_type_id as id,
 sum(a.eca_quantity) as q,
 a.eca_location_id as lid,
 a.eca_location_flag as f
from
 qi.esi_corporation_assets as a,
 eve_sde_type_ids as tid
where
 a.eca_corporation_id = 2053528477 and
 a.eca_type_id = tid.sdet_type_id and
 tid.sdet_market_group_id in (1333, 1334, 1335, 1336, 1337) -- планетарка
group by 1, 3, 4
order by 3, 4, 1;
EOD;
    $stock_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $stock = pg_fetch_all($stock_cursor);
    //---
    $query = <<<EOD
select 
 jita.ethp_type_id as id,
 jita.ethp_sell as js,
 jita.ethp_buy as jb 
from
 qi.esi_trade_hub_prices jita,
 qi.eve_sde_type_ids tid
where
 jita.ethp_location_id = 60003760 and
 jita.ethp_type_id = tid.sdet_type_id and
 tid.sdet_market_group_id in (1333, 1334, 1335, 1336, 1337); -- планетарка
EOD;
    $jita_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $jita = pg_fetch_all($jita_cursor);
    //---
    $query = <<<EOD
select
 sdet_type_id as id,
 sdet_type_name as name,
 sdet_volume as v,
 sdet_market_group_id as mgid
from eve_sde_type_ids
where sdet_market_group_id in (1333, 1334, 1335, 1336, 1337) -- планетарка
order by sdet_market_group_id, sdet_type_name;
EOD;
    $planetary_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $planetary = pg_fetch_all($planetary_cursor);
    //---
    $query = <<<EOD
select
  -- ecwj_reference_id,
  ecwj_date::date as dt,
  c,
  round(isk::numeric, 2) as isk,
  tp
from (
 select
  -- ecwj_reference_id,
  ecwj_date,
  ecwj_corporation_id as c,
  ecwj_amount as isk,
  't'::char as tp
 from qi.esi_corporation_wallet_journals
 where
  ecwj_date >= '2021-08-30' and
  ( ( ecwj_corporation_id = 2053528477 and -- Blade of Knowledge
      ecwj_ref_type in ('corporation_account_withdrawal', 'player_donation') and
      ( ecwj_first_party_id in (1077301319, 98150545) or -- glorden, Just A Trade Corp
        ecwj_second_party_id in (1077301319, 98150545) -- glorden, Just A Trade Corp
      )
    ) or
    ( ecwj_corporation_id = 98150545 and -- Just A Trade Corp
      ecwj_ref_type in ('corporation_account_withdrawal', 'player_donation') and
      ( ecwj_first_party_id in (364693619, 2053528477) or -- CHOAM Trader, Blade of Knowledge
        ecwj_second_party_id in (364693619, 2053528477) -- CHOAM Trader, Blade of Knowledge
      )
    ) or
    ecwj_reference_id in (19664726799, 19641484342, 19622083601) -- начальные инвестиции
  )
 union
 select
  -- ecwj_reference_id,
  ecwj_date::date,
  98150545,
  sum(ecwj_amount),
  'f'::char -- fee
 from qi.esi_corporation_wallet_journals
 where
  ecwj_date >= '2021-08-30' and
  ecwj_corporation_id = 98150545 and --  Just A Trade Corp
  ecwj_division = 1 and
  ecwj_context_id_type is null and ecwj_context_id is null and ecwj_ref_type = 'brokers_fee' -- комиссия брокера за market-операцию
 group by 1, 4
 union
  select
  ecwt_date::date,
  98150545,
  sum(ecwt_unit_price * ecwt_quantity),
  case when ecwt_is_buy then 'b'::char else 's'::char end
 from
  qi.esi_corporation_wallet_transactions,
  qi.eve_sde_type_ids
 where
  ecwt_date >= '2021-08-30' and
  ecwt_corporation_id = 98150545 and --  Just A Trade Corp
  ecwt_division = 1 and
  sdet_market_group_id in (1333, 1334, 1335, 1336, 1337) and -- планетарка
  ecwt_type_id = sdet_type_id
 group by 1, 4
 ) j
order by dt desc;
EOD;
    $wallet_journals_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $wallet_journals = pg_fetch_all($wallet_journals_cursor);
    //---
    $query = <<<EOD
select
 -- o.ecor_issued::date as dt,
 o.ecor_type_id as id,
 o.ecor_price as p,
 sum(o.ecor_volume_remain) as r,
 -- o.ecor_history as history,
 -- o.ecor_order_id as order_id
 ecor_is_buy_order as b
from
 qi.eve_sde_type_ids tid,
 esi_corporation_orders o
where
 tid.sdet_market_group_id in (1333, 1334, 1335, 1336, 1337) and -- планетарка
 ecor_type_id = tid.sdet_type_id and
 -- ecor_is_buy_order and
 not ecor_history and
 ecor_issued >= '2021-08-30' and
 ecor_issued_by = 1077301319
group by 1, 2, 4
order by 1, 2 desc;
EOD;
    $active_orders_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $active_orders = pg_fetch_all($active_orders_cursor);
    //---
    $query = <<<EOD
select
 ecwt_type_id as id,
 ecwt_date::date as dt,
 sum(ecwt_unit_price*ecwt_quantity) as sb, -- sum buy
 sum(ecwt_quantity) as sc -- sum quantity
from
 qi.esi_corporation_wallet_transactions,
 qi.eve_sde_type_ids
where
 ecwt_date >= '2021-08-30' and
 ecwt_corporation_id = 98150545 and --  Just A Trade Corp
 ecwt_division = 1 and
 ecwt_is_buy and
 sdet_market_group_id in (1333, 1334, 1335, 1336, 1337) and -- планетарка
 ecwt_type_id = sdet_type_id
group by 1, 2
order by 1, 2
EOD;
    $market_payments_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $market_payments = pg_fetch_all($market_payments_cursor);
    //---
    pg_close($conn);
?>
<div class="container">
 <?php __dump_jita_prices($planetary, $jita); ?>
 <?php __dump_wallet_journals($wallet_journals, $market_payments); ?>
 <?php __dump_market_orders($active_orders, $planetary, $jita); ?>
 <div class="panel-group" id="accordionStock" role="tablist" aria-multiselectable="true">
 <?php __dump_planetary_stock($stock, $planetary, $jita, $active_orders); ?>
 </div>
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
              var td0 = $(this).find('td').eq(0); // ищём <td#0 class='active'>
              if (!(td0.attr('class') === undefined))
                start_row = undefined;
              else {
                //ищём <tr>...<td#1><a data-copy='?'>...
                var td1a = $(this).find('td').eq(1).find('a');
                if (!(td1a === undefined)) {
                  var nm = td1a.attr('data-copy');
                  if (!(nm === undefined)) {
                    var td2q = $(this).find('td').eq(2).attr('quantity');
                    if (!(td2q === undefined) && (td2q > 0)) {
                      if (data_copy) data_copy += "\n"; 
                      data_copy += nm + "\t" + td2q;
                    }
                  }
                }
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
      if (data_copy) {
        if (window.isSecureContext && navigator.clipboard) {
          navigator.clipboard.writeText(data_copy).then(() => {
            $(this).trigger('copied', ['Copied!']);
          }, (e) => {
            $(this).trigger('copied', ['Data not copied!']);
          });
          document.execCommand("copy");
        }
        else {
          var $temp = $("<textarea>");
          $("body").append($temp);
          $temp.val(data_copy).select();
          try {
            success = document.execCommand("copy");
            if (success)
              $(this).trigger('copied', ['Copied!']);
            else
              $(this).trigger('copied', ['Data not copied!']);
          } finally {
            $temp.remove();
          }
        }
      }
      else {
        $(this).trigger('copied', ['Nothing no copy!']);
      }
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
