-- Approved POs that still have something outstanding to receive or to bill.
-- Draft and cancelled POs are not migrated (spec: "approved open POs").
SELECT
    po.id                                   AS source_id,
    po.name                                 AS name,
    po.partner_id                           AS partner_id,
    po.date_order::date                     AS date_order,
    po.state                                AS state,
    rc.name                                 AS currency,
    po.amount_untaxed                       AS amount_untaxed,
    po.amount_total                         AS amount_total
FROM purchase_order po
LEFT JOIN res_currency rc ON rc.id = po.currency_id
WHERE po.company_id = %(company_id)s
  AND po.state IN ('purchase', 'done')
  AND po.date_order::date <= %(as_of)s
  AND EXISTS (
        SELECT 1
        FROM purchase_order_line pol
        WHERE pol.order_id = po.id
          AND (pol.product_qty - COALESCE(pol.qty_received, 0)) > 0
      )
ORDER BY po.id
