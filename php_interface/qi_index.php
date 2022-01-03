<?php
include 'qi_render_html.php';
include_once '.settings.php';
?>
<?php __dump_header("Closed Section", FS_RESOURCES); ?>
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

<h2>Производство</h2>
 <p>
 Производство и всё что с ним связано.<br>
 <a class="btn btn-primary" href="/qi_industry_cost.php" role="button">Industry Cost</a>
 </p>

<h2>Специальные алгоритмы и специфические задачи</h2>
 <p>
 Текущее состояние рынка в <strong>Querious</strong> и <strong>Nisuwa</strong>. Список продаваемых товаров, оценка количества в операциях закупки (ежедневно и на недельном интервале), отслеживание стоимости товаров по ценам в Jita, в Amarr, и в University, расчёт профита. Учёт количества товаров, имеющихся на складе, не выствленных на продажу.<br>
 <a class="btn btn-success" href="/qi_querious.php" role="button">Querious Market</a>
 <a class="btn btn-success" href="/qi_querious_industry_request.php" role="button">Querious Industry</a><br>
 <br>
 <a class="btn btn-success" href="/qi_nisuwa.php" role="button">Nisuwa Market</a>
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
 <a class="btn btn-success" href="/qi_trade_hub.php?trade_hub_id=60013945" role="button">Irmaline</a>
 <a class="btn btn-success" href="/qi_trade_hub.php?trade_hub_id=60013990" role="button">Gehi</a>
 <a class="btn btn-success" href="/qi_trade_hub.php?trade_hub_id=60008494" role="button">Amarr</a>
 </p>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>
