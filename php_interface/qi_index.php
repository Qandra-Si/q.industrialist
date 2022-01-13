﻿<?php
include 'qi_render_html.php';
include_once '.settings.php';


__dump_header("Closed Section", FS_RESOURCES);

if (!extension_loaded('pgsql')) return;
$conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
        or die('pg_connect err: '.pg_last_error());
pg_exec($conn, "SET search_path TO qi");
//---
?>
<div class="container-fluid">
<h2>Настройки работы открытого раздела</h2>
 <p>
 Настройка конвейера, описания фитов и планов производства, выбор производственных структур и контейнеров с чертежами для отслеживания достаточности их инвента.
 <br><a class="btn btn-warning" href="/qi_workflow.php" role="button">Workflow Settings</a>
 </p>

 <p>
 Отслеживаемые фиты регрупа, - задаётся количество предметов или фиты, контролируется наличие заданных товаров на указанных станциях, в ящиках или в ангарах.
 <br><a class="btn btn-warning" href="/qi_regroup.php" role="button">Regroup Settings</a>
 </p>

<h2>Мониторинг состояния закрытого раздела</h2>
 <p>
 Полный список тех материалов, которые производились или инвентились нашими корпорациями. Расчёт стоимости работ и уплаченных налогов на запуск.
 <br><a class="btn btn-info" href="/qi_industry.php" role="button">Industry</a>
 </p>

 <p>
 Отслеживание того, что происходит с чертежами, - инвент и копирка, рассчёт стоимости работ с учётом процента успеха. Выборка включает события за последнюю неделю.
 <br><a class="btn btn-info" href="/qi_blueprint_costs.php" role="button">Blueprint Costs</a>
 </p>

 <p>
 Отслеживание работы алгоритмов получения данных с серверов CCP. Дата и время последней актуализации данных по подключенным корпорациям.
 <br><a class="btn btn-info" href="/qi_lifetime.php" role="button">Lifetime</a>
 </p>

<?php
    $query = <<<EOD
select count(1) as cnt
from eve_sde_type_ids
where sdet_created_at >= (current_timestamp at time zone 'GMT' - interval '14 days');
EOD;
    $items_new_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $items_new = pg_fetch_all($items_new_cursor);
?>

 <p>
 Отслеживание новых предметов, появившихся в игре за последние две недели.
 <br><a class="btn btn-info" href="/qi_items_new.php" role="button">New Items<?php if ($items_new) { ?> <span class="badge"><?=$items_new[0]['cnt']?></span><?php } ?></a>
 </p>

<h2>Производство</h2>
 <p>
 Производство и всё что с ним связано.<br>
 <a class="btn btn-primary" href="/qi_industry_cost.php" role="button">Industry Cost</a>
 </p>

<h2>Специальные алгоритмы и специфические задачи</h2>
 <p>
 Текущее состояние рынка в <strong>Querious</strong> и <strong>Nisuwa</strong>. Список продаваемых товаров, оценка количества в операциях закупки (ежедневно и на недельном интервале), отслеживание стоимости товаров по ценам в Jita, в Amarr, и в University, расчёт профита. Учёт количества товаров, имеющихся на складе, не выствленных на продажу.<br>
 <a class="btn btn-success" href="/qi_market_querious.php" role="button">Querious Market</a>
 <a class="btn btn-success" href="/qi_querious_industry_request.php" role="button">Querious Industry</a><br>
 <br>
 <a class="btn btn-success" href="/qi_market_nisuwa.php" role="button">Nisuwa Market</a>
 <a class="btn btn-success" href="/qi_market_nsimw.php" role="button">Malpais Market</a>
 <a class="btn btn-success" href="/qi_market_4hwwf.php" role="button">4H-WWF Market</a>
 <a class="btn btn-success" href="/qi_market_fhttc.php" role="button">FH-TTC Market</a><br>
 <br>
<?php
    $query = <<<EOD
select distinct
 o.ecor_corporation_id as cid,
 o.ecor_location_id as lid,
 nm.name as nm,
 nm.solar_system_name as sys,
 co.eco_name as co
from esi_corporation_orders o
 left outer join esi_known_stations nm on (nm.location_id=o.ecor_location_id)
 left outer join esi_corporations co on (co.eco_corporation_id=o.ecor_corporation_id)
where not o.ecor_history
order by 4, 5;
EOD;
    $corp_trade_hubs_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $corp_trade_hubs = pg_fetch_all($corp_trade_hubs_cursor);
    //---
    if ($corp_trade_hubs)
        foreach ($corp_trade_hubs as &$hub)
        {
            $corporation_id = $hub['cid'];
            $location_id = $hub['lid'];
            $trade_hub_name = $hub['nm']."\n".$hub['co'];
            $button_caption = $hub['sys'].' &vert; '.$hub['co'];
            ?><a class="btn btn-default" href="/qi_trade_hub.php?hub=<?=$location_id?>&corp=<?=$corporation_id?>&raw_materials=1" role="button" data-toggle="tooltip" data-placement="top" title="<?=$trade_hub_name?>"><?=$button_caption?></a> <?php
        }
?>
 </p>

 <p>
 Учёт наличия материалов в стоке в <strong>Malpais</strong>, автоматический расчёт достаточности их количества. Поиск потерянных товаров, случайно оказавшихся в стоке, поиск товаров, которые не используются в работах иди которые надо уварить, потратить или продать.
 <br><a class="btn btn-success" href="/qi_obsolete_stock.php" role="button">Obsolete Stock</a>
 </p>

 <p>
 Текущий список закупок и продаж по всем корпорациям, объёмы реализации, сравнение цен с Jita.<br>
 <a class="btn btn-success" href="/qi_market_orders.php" role="button">Market Orders (без Querious)</a>
 <a class="btn btn-success" href="/qi_market_orders.php?buy_only=1" role="button">Buy Market Orders</a>
 <a class="btn btn-success" href="/qi_market_orders.php?sell_only=1" role="button">Sell Market Orders</a> 
 <a class="btn btn-default" href="/qi_market_orders.php?querious_sales=1" role="button">Market Orders (с Querious)</a>
 </p>

 <p>
 Профессор вернулся и сразу ворвался в планетарку. Учёт наличия материалов в коробках для запуска процессов на планетах.
 <br><a class="btn btn-success" href="/qi_professor_planetary.php" role="button">Professor' Planetary</a>
 </p>

 <p>
 После амбициозного врывания Профессора в планетарку и недели моих бессонных ночей с перекладыванием БПЦ-шек в Malpais-е для формирования библиотеки в Querious, - принял решение закупить и привезти полную библиотеку чертежей (пока без структур и капиталов). Учёт наличия чертежей, их количества и связанной с ними научки.
 <br><a class="btn btn-success" href="/qi_qandra_blueprints.php" role="button">Qabdra Si' Blueprints</a>
 </p>

<h2>Мониторинг состояния рынка</h2>
 <p>
 Вам скучно и нечем заняться? Есть торговец в Jita или в Amarr, есть фура или простаивает jump-фура? Ознакомьтесь со списком выгодных ордеров в разных солнечных системах.<br>
<?php
    $query = <<<EOD
select distinct th.ethp_location_id as id, nm.name as nm, nm.solar_system_name as sys
from qi.esi_trade_hub_prices th
  left outer join qi.esi_known_stations nm on (nm.location_id=th.ethp_location_id)
where th.ethp_location_id<>60003760
order by 2, 1;
EOD;
    $trade_hubs_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $trade_hubs = pg_fetch_all($trade_hubs_cursor);
    //---
    if ($trade_hubs)
        foreach ($trade_hubs as &$hub)
        {
            $location_id = $hub['id'];
            $trade_hub_name = $hub['nm'];
            $solar_system_name = $hub['sys'];
            ?><a class="btn btn-success" href="/qi_trade_hub_profits.php?trade_hub_id=<?=$location_id?>" role="button" data-toggle="tooltip" data-placement="top" title="<?=$trade_hub_name?>"><?=$solar_system_name?></a> <?php
        }
?>
 </p>
</div> <!--container-fluid-->
<?php
//---
pg_close($conn);
__dump_footer();
?>