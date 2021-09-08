select
  o.*,
  tid.sdet_type_name 
from (
  select
   ecor_issued::date,
   ecor_type_id,
   sum(ecor_price),
   sum(ecor_volume_total)
  from qi.esi_corporation_orders
  where ecor_location_id = 1034323745897
  group by 1, 2
) o
    left outer join qi.eve_sde_type_ids tid on (o.ecor_type_id = tid.sdet_type_id);

select
 emrh_date as date,
 emrh_type_id as id,
 tid.sdet_type_name as name,
 ceil(emrh_volume * emrh_average) as "Querious sum price",
 emrh_volume as "Querious sum volume",
 ri4.sum_price as "RI4 sum price",
 ri4.sum_quantity as "RI4 sum volume"
from qi.esi_markets_region_history emrh
  left outer join qi.eve_sde_type_ids tid on (emrh.emrh_type_id = tid.sdet_type_id)
  left outer join (
      select
        ecwt_date::date as date,
        ecwt_type_id as type_id,
        sum(ecwt_unit_price) as sum_price,
        sum(ecwt_quantity) as sum_quantity
        -- ,tid.sdet_type_name as name
      from
        qi.esi_corporation_wallet_journals j
          left outer join qi.esi_corporation_wallet_transactions t on (ecwj_context_id = ecwt_transaction_id) -- (j.ecwj_reference_id = t.ecwt_journal_ref_id)
          -- left outer join qi.eve_sde_type_ids tid on (ecwt_type_id = tid.sdet_type_id)
      where
        not ecwt_is_buy and
        (ecwj_date::date >= '2021-09-05') and (ecwj_date::date < '2021-09-08') and
        (ecwj_context_id_type = 'market_transaction_id') and
        ( ( ecwj_corporation_id in (98615601) and -- R Initiative 4
            ecwj_second_party_id in (2116129465,2116746261,2116156168) and -- Qandra Si, Kekuit Void, Qunibbra Do
            ecwj_division = 1)
        )
      group by 1, 2 --, tid.sdet_type_name
  ) ri4 on (ri4.type_id = emrh.emrh_type_id and ri4.date = emrh.emrh_date)
where (emrh_date >= '2021-09-05') and (emrh_date <= '2021-09-07') and (emrh_region_id = 10000050)
order by emrh_date, tid.sdet_type_name;