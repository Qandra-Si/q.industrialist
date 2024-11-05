--------------------------------------------------------------------------------
-- обновляет содержимое предварительно рассчитанного кеша с результатами
-- информации о производстве по conveyor-формулам
--------------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE qi.cfc_full_calculus()
LANGUAGE sql
AS $procedure$
  INSERT INTO qi.conveyor_formula_calculus(
   cfc_formula,
   cfc_products_per_single_run,
   cfc_products_num,
   cfc_industry_hub,
   cfc_trade_hub,
   cfc_trader_corp,
   cfc_buying_brokers_fee,
   cfc_sales_brokers_fee,
   cfc_sales_tax,
   cfc_fuel_price_isk,
   cfc_materials_cost,
   cfc_materials_cost_with_fee,
   cfc_purchase_volume,
   cfc_materials_transfer_cost,
   cfc_jobs_cost,
   cfc_ready_volume,
   cfc_ready_transfer_cost,
   cfc_products_recommended_price,
   cfc_products_sell_fee_and_tax,
   cfc_single_product_price_wo_fee_tax,
   cfc_total_gross_cost,
   cfc_single_product_cost,
   cfc_product_mininum_price,
   cfc_single_product_profit,
   cfc_created_at,
   cfc_updated_at)
      SELECT
       formula,
       products_per_single_run,
       products_per_single_run * customized_runs,
       industry_hub,
       trade_hub,
       trader_corp,
       buying_brokers_fee,
       sales_brokers_fee,
       sales_tax,
       fuel_price_isk,
       coalesce(materials_cost,0) materials_cost,
       coalesce(materials_cost_with_fee,0) materials_cost_with_fee,
       purchase_volume,
       materials_transfer_cost,
       jobs_cost,
       ready_volume,
       ready_transfer_cost,
       products_recommended_price,
       products_sell_fee_and_tax,
       single_product_price_wo_fee_tax,
       coalesce(total_gross_cost,0) total_gross_cost,
       coalesce(single_product_cost,0) single_product_cost,
       coalesce(product_mininum_price,0) product_mininum_price,
       single_product_profit,
       CURRENT_TIMESTAMP AT TIME ZONE 'GMT',
       CURRENT_TIMESTAMP AT TIME ZONE 'GMT'
      FROM qi.conveyor_formulas_industry_costs
      --WHERE materials_cost <= 0.01 or materials_cost is null
      --WHERE formula=1782
  ON CONFLICT ON CONSTRAINT pk_cfc DO UPDATE SET
   --pk:cfc_formula = excluded.cfc_formula,
   cfc_products_per_single_run = excluded.cfc_products_per_single_run,
   cfc_products_num = excluded.cfc_products_num,
   --pk:cfc_industry_hub = excluded.cfc_industry_hub,
   --pk:cfc_trade_hub = excluded.cfc_trade_hub,
   --pk:cfc_trader_corp = excluded.cfc_trader_corp,
   cfc_buying_brokers_fee = excluded.cfc_buying_brokers_fee,
   cfc_sales_brokers_fee = excluded.cfc_sales_brokers_fee,
   cfc_sales_tax = excluded.cfc_sales_tax,
   cfc_fuel_price_isk = excluded.cfc_fuel_price_isk,
   cfc_materials_cost = excluded.cfc_materials_cost,
   cfc_materials_cost_with_fee = excluded.cfc_materials_cost_with_fee,
   cfc_purchase_volume = excluded.cfc_purchase_volume,
   cfc_materials_transfer_cost = excluded.cfc_materials_transfer_cost,
   cfc_jobs_cost = excluded.cfc_jobs_cost,
   cfc_ready_volume = excluded.cfc_ready_volume,
   cfc_ready_transfer_cost = excluded.cfc_ready_transfer_cost,
   cfc_products_recommended_price = excluded.cfc_products_recommended_price,
   cfc_products_sell_fee_and_tax = excluded.cfc_products_sell_fee_and_tax,
   cfc_single_product_price_wo_fee_tax = excluded.cfc_single_product_price_wo_fee_tax,
   cfc_total_gross_cost = excluded.cfc_total_gross_cost,
   cfc_single_product_cost = excluded.cfc_single_product_cost,
   cfc_product_mininum_price = excluded.cfc_product_mininum_price,
   cfc_single_product_profit = excluded.cfc_single_product_profit,
   --once:cfc_created_at = excluded.cfc_created_at,
   cfc_updated_at = CASE WHEN
     conveyor_formula_calculus.cfc_products_per_single_run = excluded.cfc_products_per_single_run and
     conveyor_formula_calculus.cfc_products_num = excluded.cfc_products_num and
     conveyor_formula_calculus.cfc_buying_brokers_fee = excluded.cfc_buying_brokers_fee and
     conveyor_formula_calculus.cfc_sales_brokers_fee = excluded.cfc_sales_brokers_fee and
     conveyor_formula_calculus.cfc_sales_tax = excluded.cfc_sales_tax and
     conveyor_formula_calculus.cfc_fuel_price_isk = excluded.cfc_fuel_price_isk and
     conveyor_formula_calculus.cfc_materials_cost = excluded.cfc_materials_cost and
     conveyor_formula_calculus.cfc_materials_cost_with_fee = excluded.cfc_materials_cost_with_fee and
     conveyor_formula_calculus.cfc_purchase_volume = excluded.cfc_purchase_volume and
     conveyor_formula_calculus.cfc_materials_transfer_cost = excluded.cfc_materials_transfer_cost and
     conveyor_formula_calculus.cfc_jobs_cost = excluded.cfc_jobs_cost and
     conveyor_formula_calculus.cfc_ready_volume = excluded.cfc_ready_volume and
     conveyor_formula_calculus.cfc_ready_transfer_cost = excluded.cfc_ready_transfer_cost and
     conveyor_formula_calculus.cfc_products_recommended_price = excluded.cfc_products_recommended_price and
     conveyor_formula_calculus.cfc_products_sell_fee_and_tax = excluded.cfc_products_sell_fee_and_tax and
     conveyor_formula_calculus.cfc_single_product_price_wo_fee_tax = excluded.cfc_single_product_price_wo_fee_tax and
     conveyor_formula_calculus.cfc_total_gross_cost = excluded.cfc_total_gross_cost and
     conveyor_formula_calculus.cfc_single_product_cost = excluded.cfc_single_product_cost and
     conveyor_formula_calculus.cfc_product_mininum_price = excluded.cfc_product_mininum_price and
     conveyor_formula_calculus.cfc_single_product_profit = excluded.cfc_single_product_profit
   THEN conveyor_formula_calculus.cfc_updated_at ELSE excluded.cfc_updated_at END;
  --- --- ---
  UPDATE qi.conveyor_formula_calculus
  SET cfc_best_choice = false;
  --- --- ---
  UPDATE qi.conveyor_formula_calculus
  SET cfc_best_choice = true
  FROM (
   SELECT best_formula.formula
   FROM
    -- поиск минимальных цен на продукты в разных хабах
    (SELECT
      c.cfc_trade_hub trade_hub,
      c.cfc_trader_corp trader_corp,
      f.cf_product_type_id product_type_id,
      min(c.cfc_single_product_cost) min_product_cost
     FROM
      qi.conveyor_formula_calculus c,
      qi.conveyor_formulas f
     WHERE f.cf_formula=c.cfc_formula
     GROUP BY c.cfc_trade_hub, c.cfc_trader_corp, f.cf_product_type_id
    ) min_price
     -- поиск формулы с минимальной стоимостью производства
     LEFT OUTER JOIN (
      SELECT
       f.cf_formula formula,
       c.cfc_trade_hub trade_hub,
       c.cfc_trader_corp trader_corp,
       f.cf_product_type_id product_type_id,
       c.cfc_single_product_cost product_cost
      FROM
       qi.conveyor_formula_calculus c,
       qi.conveyor_formulas f
      WHERE f.cf_formula=c.cfc_formula
     ) best_formula ON (min_price.trade_hub=best_formula.trade_hub AND min_price.trader_corp=best_formula.trader_corp AND min_price.min_product_cost=best_formula.product_cost)
  ) best_formula
  WHERE cfc_formula = best_formula.formula;
$procedure$
;
--------------------------------------------------------------------------------
