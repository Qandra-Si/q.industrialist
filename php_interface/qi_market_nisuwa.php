<?php
$SHOW_ONLY_RI4_SALES = 0; // признак отображения информации по ордерам, которые выставлены не нами
$DO_NOT_SHOW_RAW_MATERIALS = 1; // не показывать метариалы, закуп которых выполняется для производственных работ (фильтрация спекуляции и закупа для производства, например минералов)
$IMPORT_PRICE_TO_TRADE_HUB = 62; // null; // например, цена импорта 1куб.м. из Jita в Querious была 866 ISK
$MIN_PROFIT = 0.05; // 5%
$DEFAULT_PROFIT = 0.1; // 10%
$MAX_PROFIT = 0.25; // 25%
$BROKERS_FEE = 0.0048; // брокерская комиссия
$TRADE_HUB_TAX = 0.036; // sales tax, налог на структуре
$CORPORATION_ID = 98553333; // R Initiative 4: 98615601, R Strike: 98553333, R Industry: 98677876
$TRADE_HUB_ID = 60015073; // PZ: 1034323745897, Nisuwa: 60015073, 4-HWWF: 1035466617946, NSI-MW: 1022822609240
$TRADER_ID = 874053567; // Xatul' Madan: 95858524, DarkFman: 874053567, Zed Ostus: 2116422143

include_once 'qi_trade_hub.php';
?>