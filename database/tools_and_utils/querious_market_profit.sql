select
  nm.sden_name as item_name,
  avg(jt.ecwt_quantity) as wk_volume,
  null as jita_price, -- нужна подгрузка рыночных цен
  null as import_price, -- нужно загрузить в БД сведения о параметрах модулей
  null as "3-fkcz price", -- нужна подгрузка ордеров
  null as markup,
  null as "+10% price",
  null as "+10% profit"
  -- , jt.ecwj_date,
  -- round((jt.ecwt_price / jt.ecwt_quantity)::numeric, 2) as avg_unit_price
from (
  select
    date_trunc('week', j.ecwj_date)::date as ecwj_date,
    t.ecwt_type_id,
    CASE WHEN sign(j.ecwj_amount) < 0 THEN 'buy'
                                      ELSE 'sell'
                                      END as deal,
    sum(t.ecwt_unit_price*t.ecwt_quantity) as ecwt_price,
    sum(t.ecwt_quantity) as ecwt_quantity
  from
    qi.esi_corporation_wallet_journals j
      left outer join qi.esi_corporation_wallet_transactions t on (j.ecwj_context_id = t.ecwt_transaction_id) -- (j.ecwj_reference_id = t.ecwt_journal_ref_id)
  where
    ( ( ecwj_corporation_id in (98615601) and -- R Initiative 4
        ecwj_second_party_id in (2116129465,2116746261) and -- Qandra Si, Kekuit Void
        ecwj_division = 1) or -- главный кошелёк
      ( ecwj_corporation_id in (98553333) and -- R Strike
        ecwj_second_party_id in (95858524) and -- Xatul' Madan
        ecwj_division = 7)
    ) and
    ecwj_context_id_type = 'market_transaction_id' and
    ecwj_date > '2021-08-15'
  group by 1, 2, 3
  ) jt
  left outer join qi.eve_sde_names nm on (nm.sden_category = 1 and jt.ecwt_type_id = nm.sden_id)
where jt.deal = 'sell'
group by 1
order by 1