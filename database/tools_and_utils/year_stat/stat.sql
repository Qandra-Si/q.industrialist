select 'industry_jobs', j.*
from (
  select j.installer_id as installer_id, count(1) as qty
  from corporation_industry_jobs j
  where
    j.start_date >= '2021-01-01' and j.start_date < '2022-01-01' and
    j.corporation_id in (98615601,98553333,98677876,98150545,98650099)
  group by 1
) j
union
select 'contracts', c.*
from (
  select c.issuer_id as issuer_id, count(1) as qty
  from contract_details c
  where
    c.date_issued >= '2021-01-01' and c.date_issued < '2022-01-01' and
    c.issuer_corporation_id in (98615601,98553333,98677876,98150545,98650099)
  group by 1
) c
union
select 'orders', o.*
from (
  select o.issued_by as issued_by, count(1) as qty
  from corporation_orders o
  where
    o.issued >= '2021-01-01' and o.issued < '2022-01-01' and
    o.corporation_id in (98615601,98553333,98677876,98150545,98650099)
  group by 1
) o;

--------------------------------------------------------------

select x.nm, count(x.installer_id)
from (
select 'industry_jobs' nm, j.*
from (
  select j.installer_id as installer_id, count(1) as qty
  from corporation_industry_jobs j
  where
    j.start_date >= '2021-01-01' and j.start_date < '2022-01-01' and
    j.corporation_id in (98615601,98553333,98677876,98150545,98650099)
  group by 1
) j
union
select 'contracts', c.*
from (
  select c.issuer_id as issuer_id, count(1) as qty
  from contract_details c
  where
    c.date_issued >= '2021-01-01' and c.date_issued < '2022-01-01' and
    c.issuer_corporation_id in (98615601,98553333,98677876,98150545,98650099)
  group by 1
) c
union
select 'orders', o.*
from (
  select o.issued_by as issued_by, count(1) as qty
  from corporation_orders o
  where
    o.issued >= '2021-01-01' and o.issued < '2022-01-01' and
    o.corporation_id in (98615601,98553333,98677876,98150545,98650099)
  group by 1
) o
) x
 group by 1;

--------------------------------------------------------------

select count(1) from ( select distinct x.installer_id
from (
select 'industry_jobs' nm, j.*
from (
  select j.installer_id as installer_id, count(1) as qty
  from corporation_industry_jobs j
  where
    j.start_date >= '2021-01-01' and j.start_date < '2022-01-01' and
    j.corporation_id in (98615601,98553333,98677876,98150545,98650099)
  group by 1
) j
union
select 'contracts', c.*
from (
  select c.issuer_id as issuer_id, count(1) as qty
  from contract_details c
  where
    c.date_issued >= '2021-01-01' and c.date_issued < '2022-01-01' and
    c.issuer_corporation_id in (98615601,98553333,98677876,98150545,98650099)
  group by 1
) c
union
select 'orders', o.*
from (
  select o.issued_by as issued_by, count(1) as qty
  from corporation_orders o
  where
    o.issued >= '2021-01-01' and o.issued < '2022-01-01' and
    o.corporation_id in (98615601,98553333,98677876,98150545,98650099)
  group by 1
) o
) x
-- group by 1
) y;

--------------------------------------------------------------

SELECT sum(s.total_sp + s.unallocated_sp)
FROM character_info_skills s, corporation_members m
where m.character_id = s.character_id AND 
  m.corporation_id in (98615601,98553333,98677876,98150545,98650099);

--------------------------------------------------------------

SELECT count(1) market_transaction
FROM corporation_wallet_journals x
WHERE
  x.corporation_id in (98615601,98553333,98677876,98150545,98650099) and
  x.date >= '2021-01-01' and x.date < '2022-01-01' and
  x.ref_type = 'market_transaction';

--------------------------------------------------------------

SELECT x.is_buy, sum(x.unit_price*x.quantity)
FROM seat.corporation_wallet_transactions x
WHERE corporation_id in (98615601,98553333,98677876,98150545,98650099) and
  x.date >= '2021-01-01' and x.date < '2022-01-01'
group by 1;

--------------------------------------------------------------

SELECT sum(abs(x.amount))
FROM corporation_wallet_journals x
WHERE
  x.corporation_id in (98615601,98553333,98677876,98150545,98650099) and
  x.date >= '2021-01-01' and x.date < '2022-01-01'
  and x.ref_type in ('market_transaction','transaction_tax','market_escrow','contract_price','contract_deposit_refund',
 'contract_sales_tax','brokers_fee');

--------------------------------------------------------------

SELECT
  sum(x.runs),
  count(1)
FROM
 seat.corporation_industry_jobs x
WHERE x.corporation_id in (98615601,98553333,98677876,98150545,98650099) and
  x.start_date >= '2021-01-01' and x.start_date < '2022-01-01';

--------------------------------------------------------------

SELECT
  -- x.successful_runs ,
  -- x.activity_id ,
  -- x.product_type_id,
  sum(x.successful_runs*p.sdebp_quantity)
FROM
 seat.corporation_industry_jobs x,
 seat._qi_eve_sde_blueprint_products p
WHERE x.corporation_id in (98615601,98553333,98677876,98150545,98650099) and
  x.start_date >= '2021-01-01' and x.start_date < '2022-01-01' and
  x.status = 'delivered' and
  x.product_type_id = p.sdebp_product_id and x.activity_id = p.sdebp_activity;
  

--------------------------------------------------------------

SELECT
  -- x.successful_runs ,
  -- x.activity_id ,
  -- x.product_type_id,
  -- sum(p.sdebp_quantity),
  sum(x.successful_runs*p.sdebp_quantity*m.average_price),
  sum(m.adjusted_price)
FROM
 seat.corporation_industry_jobs x 
   left outer join seat.market_prices m on (m.type_id = x.product_type_id and x.activity_id in (1,9,11)),
 seat._qi_eve_sde_blueprint_products p
WHERE x.corporation_id in (98615601,98553333,98677876,98150545,98650099) and
  x.start_date >= '2021-01-01' and x.start_date < '2022-01-01' and
  x.status = 'delivered' and
  x.product_type_id = p.sdebp_product_id and x.activity_id = p.sdebp_activity;

--------------------------------------------------------------

select
x.activity_id,
sum(x.successful_runs)
from seat.corporation_industry_jobs x
where x.corporation_id in (98615601,98553333,98677876,98150545,98650099) and
  x.start_date >= '2021-01-01' and x.start_date < '2022-01-01'
group by 1;

--------------------------------------------------------------

select
x.activity_id,
sum(x.successful_runs)
from seat.corporation_industry_jobs x
where x.corporation_id in (98615601,98553333,98677876,98150545,98650099) and
  x.start_date >= '2021-01-01' and x.start_date < '2022-01-01'
group by 1;

--------------------------------------------------------------

