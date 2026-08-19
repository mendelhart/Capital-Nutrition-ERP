-- On-hand quantity and value in internal locations.
--
-- IMPORTANT (spec: Inventory): this is REFERENCE data. Opening operational
-- inventory comes from the approved physical count at cutover, never from this
-- query. It is extracted so the count can be compared against the system and
-- so inventory value can be reconciled.
SELECT
    sq.id                                   AS source_id,
    sq.product_id                           AS product_id,
    pp.default_code                         AS product_code,
    sq.location_id                          AS location_id,
    sl.complete_name                        AS location_name,
    (sl.usage = 'internal')                 AS internal,
    sq.quantity                             AS quantity,
    COALESCE(cost.value_float, 0)           AS unit_cost,
    (sq.quantity * COALESCE(cost.value_float, 0)) AS value
FROM stock_quant sq
JOIN stock_location sl          ON sl.id = sq.location_id
JOIN product_product pp         ON pp.id = sq.product_id
LEFT JOIN ir_property cost
       ON cost.name = 'standard_price'
      AND cost.res_id = 'product.product,' || pp.id
      AND (cost.company_id = %(company_id)s OR cost.company_id IS NULL)
WHERE sq.company_id = %(company_id)s
  AND sl.usage = 'internal'
  AND sq.quantity <> 0
ORDER BY pp.default_code, sl.complete_name
