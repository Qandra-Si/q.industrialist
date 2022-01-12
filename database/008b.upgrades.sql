ALTER TABLE qi.esi_corporation_orders
 ALTER COLUMN ecor_range TYPE esi_order_range USING ecor_range::esi_order_range;
