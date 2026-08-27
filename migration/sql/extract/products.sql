-- Product variants with their current cost. Cost is company-dependent and
-- therefore lives in ir_property, not on the product table.
SELECT
    pp.id                                   AS source_id,
    pt.id                                   AS template_id,
    pp.default_code                         AS default_code,
    pp.barcode                              AS barcode,
    {{TR(pt.name)}}                         AS name,
    pt.type                                 AS product_type,
    {{TR(uom.name)}}                        AS uom,
    pt.list_price                           AS list_price,
    COALESCE(cost.value_float, 0)           AS standard_price,
    {{TR(pc.complete_name)}}                AS categ_name,
    pp.active                               AS active
FROM product_product pp
JOIN product_template pt        ON pt.id = pp.product_tmpl_id
LEFT JOIN uom_uom uom           ON uom.id = pt.uom_id
LEFT JOIN product_category pc   ON pc.id = pt.categ_id
LEFT JOIN ir_property cost
       ON cost.name = 'standard_price'
      AND cost.res_id = 'product.product,' || pp.id
      AND (cost.company_id = %(company_id)s OR cost.company_id IS NULL)
ORDER BY pp.id
