<?php
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
 Расчёт стоимости производства товаров в сравнении с ценами на материалы (только первый уровень производства).<br>
 <a class="btn btn-primary" href="/qi_industry_cost.php" role="button">Industry Cost</a>
 </p>

 <p>
 Отслеживание занятости производственных линий.<br>
 <a class="btn btn-default" href="/qi_industry_ash.php" role="button">Ash Hakoke</a>
 <a class="btn btn-default" href="/qi_industry_qandra.php" role="button">Qandra Si</a>
 <a class="btn btn-default" href="/qi_industry_glorden.php" role="button">Samurai Fruitblow</a>
 <a class="btn btn-default" href="/qi_industry_imine.php" role="button">Imine Mc'Gowan</a>
 <a class="btn btn-default" href="/qi_industry_alicegrimsdottier.php" role="button">Alice Grimsdottier</a>
 <a class="btn btn-default" href="/qi_industry_svintus.php" role="button">VanoEG</a>
 <a class="btn btn-default" href="/qi_industry_malorik.php" role="button">Antonuo Audeles</a>
 <a class="btn btn-default" href="/qi_industry_xsen.php" role="button">xsen</a>
 </p>

<h2>Специальные алгоритмы и специфические задачи</h2>
 <p>
 Текущее состояние рынка в <strong>Querious</strong> и <strong>Nisuwa</strong>. Список продаваемых товаров, оценка количества в операциях закупки (ежедневно и на недельном интервале), отслеживание стоимости товаров по ценам в Jita, в Amarr, и в University, расчёт профита. Учёт количества товаров, имеющихся на складе, не выствленных на продажу.<br>
 <a class="btn btn-success" disabled href="/qi_market_querious.php" role="button">Querious Market</a>
 <a class="btn btn-success" disabled href="/qi_querious_industry_request.php" role="button">Querious Industry</a><br>
 <br>
 Все наши маркеты (ларьки) одной таблицей:<br>
 <a class="btn btn-success" href="/qi_market_hubs.php" role="button">Market Hubs</a><br>
 <br>
 Все наши маркеты (ларьки) с индивидуальными торговыми терминалами:<br>
 <a class="btn btn-danger" href="/qi_market_jita.php" role="button">Jita</a>
 <a class="btn btn-success" href="/qi_market_nisuwa.php" role="button">Nisuwa Market</a>
 <a class="btn btn-success" href="/qi_market_nsimw.php" role="button">NSI-MW Market</a>
 <a class="btn btn-success" href="/qi_market_4hwwf.php" role="button">4H-WWF Market</a>
 <a class="btn btn-success" href="/qi_market_fhttc.php" role="button">FH-TTC Market</a>
 <a class="btn btn-success" href="qi_market_mj5f9.php" role="button">MJ-5F9 Market</a>
 <a class="btn btn-success" href="qi_market_b2j5n.php" role="button">B2J-5N Market</a>
 <a class="btn btn-success" href="qi_market_f9fuv.php" role="button">F9-FUV Market</a>
 <a class="btn btn-success" href="qi_market_p3xtn.php" role="button">P3X-TN Market</a>
 <a class="btn btn-success" href="qi_market_w5205.php" role="button">W5-205 Market</a><br>
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
 Учёт наличия материалов в стоке в <strong>Malpais</strong>, автоматический расчёт достаточности их количества. Поиск потерянных товаров, случайно оказавшихся в стоке, поиск товаров, которые не используются в работах иди которые надо уварить, потратить или продать.<br>
 <a class="btn btn-success" href="/qi_obsolete_stock.php" role="button">Obsolete Stock</a>
 <a class="btn btn-success" href="/qi_industry_needs.php" role="button">Needs of Industry</a>
 <a class="btn btn-success" href="/qi_industry_stock.php" role="button">Stock of Industry</a>
 </p>

 <p>
 Искалочка всевозможных предметов, работ, ордеров, коробок, фабрик, торговых хабов, действий персонажей по числовым идентификаторам<br>
 <a class="btn btn-warning" href="/qi_google.php?id=34,11396,11399" role="button">Googler</a>
 <a class="btn btn-default" href="/qi_google.php?id=1042" role="button">Планетарка</a>
 <a class="btn btn-default" href="/qi_google.php?id=60003760" role="button">Jita 4-4</a>
 <a class="btn btn-default" href="/qi_google.php?id=1036612408249" role="button">..stock ALL</a>
 <a class="btn btn-default" href="/qi_google.php?id=37296,41073,41068,37290" role="button">Big Bada Boom</a>
 <a class="btn btn-default" href="/qi_google.php?id=29987,29991,29989,29985,29986,29990,29988,29984" role="button">Strategic Cruiser</a>
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
