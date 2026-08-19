-- Lines of the approved open POs. qty_open is what the target must carry.
SELECT
    pol.id                                          AS source_id,
    pol.order_id                                    AS order_id,
    po.name                                         AS order_name,
    pol.product_id                                  AS product_id,
    pp.default_code                                 AS product_code,
    pol.name                                        AS description,
    pol.product_qty                                 AS qty_ordered,
    COALESCE(pol.qty_received, 0)                   AS qty_received,
    COALESCE(pol.qty_invoiced, 0)                   AS qty_invoiced,
    (pol.product_qty - COALESCE(pol.qty_received, 0)) AS qty_open,
    pol.price_unit                                  AS price_unit,
    pol.price_subtotal                              AS line_total,
    {{TR(uom.name)}}                                AS uom,
    pol.date_planned::date                          AS date_planned
FROM purchase_order_line pol
JOIN purchase_order po          ON po.id = pol.order_id
LEFT JOIN product_product pp    ON pp.id = pol.product_id
LEFT JOIN uom_uom uom           ON uom.id = pol.product_uom
WHERE po.company_id = %(company_id)s
  AND po.state IN ('purchase', 'done')
  AND po.date_order::date <= %(as_of)s
  AND (pol.product_qty - COALESCE(pol.qty_received, 0)) > 0
ORDER BY pol.order_id, pol.id
