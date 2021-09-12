﻿<?php
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

<h2>Специальные алгоритмы и специфические задачи</h2>
 <p>
 Текущее состояние рынка в <strong>Querious</strong>. Список продаваемых товаров, оценка количества в операциях закупки (ежедневно и на недельном интервале), отслеживание стоимости товаров по ценам в Jita, в Amarr, и в University, расчёт профита. Учёт количества товаров, имеющихся на складе, не выствленных на продажу.
 <br><a class="btn btn-success" href="/qi_querious.php" role="button">Querious Market</a>
 </p>

 <p>
 Учёт наличия материалов в стоке в <strong>Malpais</strong>, автоматический расчёт достаточности их количества. Поиск потерянных товаров, случайно оказавшихся в стоке, поиск товаров, которые не используются в работах иди которые надо уварить, потратить или продать.
 <br><a class="btn btn-success" href="/qi_obsolete_stock.php" role="button">Obsolete Stock</a>
 </p>

 <p>
 Текущий список закупок и продаж по всем корпорациям, объёмы реализации, сравнение цен.<br>
 <a class="btn btn-success" href="/qi_market_orders.php" role="button">Market Orders (без Querious)</a>
 <a class="btn btn-success" href="/qi_market_orders.php?buy_only=1" role="button">Buy Market Orders</a>
 <a class="btn btn-success" href="/qi_market_orders.php?sell_only=1" role="button">Sell Market Orders</a> 
 <a class="btn btn-success" href="/qi_market_orders.php?querious_sales=1" role="button" style="background-color:#90ca90; border-color:#90ca90;">Market Orders (с Querious)</a>
 </p>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>
