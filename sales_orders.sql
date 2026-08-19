-- Sales orders. Reference/history data, and the basis for the order-count and
-- sales-total reconciliation checks.
SELECT
    so.id                                   AS source_id,
    so.name                                 AS name,
    so.partner_id                           AS partner_id,
    so.date_order::date                     AS date_order,
    so.state                                AS state,
    rc.name                                 AS currency,
    so.amount_untaxed                       AS amount_untaxed,
    so.amount_tax                           AS amount_tax,
    so.amount_total                         AS amount_total
FROM sale_order so
LEFT JOIN res_currency rc ON rc.id = so.currency_id
WHERE so.company_id = %(company_id)s
  AND so.date_order::date <= %(as_of)s
  AND so.state NOT IN ('draft', 'cancel')
ORDER BY so.date_order, so.id
