SELECT
  -- ei.name,
  tax.date AS date,
  tax.ref_type as payment,
  round(-SUM(tax.tax_paid),2) AS tax_paid
FROM
  ( SELECT
      cwj.character_id AS pilot_id,
      DATE(cwj.date) AS date,
      SUM(cwj.amount) AS tax_paid,
      cwj.ref_type as ref_type
    FROM
      character_wallet_journals as cwj
      -- , planets AS p
      -- , solar_systems AS s
    WHERE
      cwj.ref_type IN ('planetary_construction','planetary_export_tax','planetary_import_tax')
      -- AND cwj.context_id = p.planet_id AND p.system_id = s.system_id
      -- AND s.security <= 0.0
    GROUP BY 1, 2, 4
  ) tax,
  character_infos ei
WHERE
  tax.pilot_id IN (2115210624, 364693619, 1359439269, 233088639) AND
  tax.pilot_id = ei.character_id AND
  tax.date >= '2021-08-30'
GROUP BY
  -- ei.name,
  tax.date, tax.ref_type
ORDER BY tax.date DESC