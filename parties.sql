-- Customers and vendors. Both live in res_partner; the ranks tell us which.
SELECT
    rp.id                                   AS source_id,
    rp.ref                                  AS ref,
    rp.name                                 AS name,
    rp.is_company                           AS is_company,
    rp.parent_id                            AS parent_id,
    COALESCE(rp.customer_rank, 0)           AS customer_rank,
    COALESCE(rp.supplier_rank, 0)           AS supplier_rank,
    rp.vat                                  AS vat,
    rp.email                                AS email,
    rp.phone                                AS phone,
    rp.street                               AS street,
    rp.street2                              AS street2,
    rp.city                                 AS city,
    rcs.code                                AS state_code,
    rp.zip                                  AS zip,
    rco.code                                AS country_code,
    rp.active                               AS active
FROM res_partner rp
LEFT JOIN res_country_state rcs ON rcs.id = rp.state_id
LEFT JOIN res_country rco       ON rco.id = rp.country_id
WHERE (rp.company_id = %(company_id)s OR rp.company_id IS NULL)
ORDER BY rp.id
