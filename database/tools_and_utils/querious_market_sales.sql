select ecwj_date::date, ceil(sum(ecwj_amount)) as type_id --, 'j'::char as type
from qi.esi_corporation_wallet_journals j
  left outer join qi.esi_corporation_wallet_transactions t on (ecwj_context_id = ecwt_transaction_id)
where
  (ecwj_date > '2021-08-15') and
  (ecwj_context_id_type = 'market_transaction_id') and
  ( ( ecwj_corporation_id in (98615601) and -- R Initiative 4
      ecwj_second_party_id in (2116129465,2116746261,2116156168) and -- Qandra Si, Kekuit Void, Qunibbra Do
      ecwj_amount > 0 and
      ( ecwt_location_id in (1036927076065,1034323745897) and not ecwt_is_buy or
        ecwt_location_id not in (1036927076065,1034323745897) and ecwt_is_buy) and -- станка рынка
      ecwj_division = 1)
  )
group by 1
order by 1 desc
limit 5