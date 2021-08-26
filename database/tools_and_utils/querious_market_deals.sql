select
  jt.solar_system_name as system,
  jt.ecwj_date as date,
  jt.pilot_name,
  jt.deal,
  jt.sum_amount,
  nm.sden_name as type_name,
  jt.ecwt_quantity,
  round((jt.ecwt_price / jt.ecwt_quantity)::numeric, 2) as avg_unit_price
from (
  select
    -- c.eco_name,
    ks.solar_system_name,
    jt.ecwj_date::date as ecwj_date,
    COALESCE(jt.ech_name, 'Xatul'' Madan') as pilot_name,
    CASE WHEN sign(jt.ecwj_amount) < 0 THEN 'buy'
                                       ELSE 'sell'
                                       END as deal,
    sum(jt.ecwj_amount) as sum_amount,
    jt.ecwt_type_id,
    --jt.ecwt_unit_price,
    --jt.ecwt_quantity
    -- ,jt.ecwt_is_buy,
    sum(jt.ecwt_unit_price*jt.ecwt_quantity) as ecwt_price,
    sum(jt.ecwt_quantity) as ecwt_quantity
  from (
    select
      j.ecwj_corporation_id,
      j.ecwj_date,
      p.ech_name,
      j.ecwj_amount,
      t.ecwt_type_id,
      t.ecwt_location_id,
      t.ecwt_unit_price,
      t.ecwt_quantity,
      t.ecwt_is_buy
      --, j.*, t.*
    from
      qi.esi_corporation_wallet_journals j
        left outer join qi.esi_corporation_wallet_transactions t on (j.ecwj_context_id = t.ecwt_transaction_id) -- (j.ecwj_reference_id = t.ecwt_journal_ref_id)
        left outer join qi.esi_characters p on (j.ecwj_second_party_id = p.ech_character_id)
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
    ) jt
    left outer join qi.esi_corporations c on (jt.ecwj_corporation_id = c.eco_corporation_id)
    left outer join qi.esi_known_stations ks on (jt.ecwt_location_id = ks.location_id)
  group by 1, 2, 3, 4, 6
  ) jt
  left outer join qi.eve_sde_names nm on (nm.sden_category = 1 and jt.ecwt_type_id = nm.sden_id)
order by jt.ecwj_date desc, jt.deal, nm.sden_name
