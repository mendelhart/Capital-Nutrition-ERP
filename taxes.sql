-- Taxes. Rates are extracted for review only; the target tax configuration is
-- an open question in 03_ACCOUNTING.md and must not be invented here.
SELECT
    at.id                                   AS source_id,
    {{TR(at.name)}}                         AS name,
    at.amount                               AS amount,
    at.amount_type                          AS amount_type,
    at.type_tax_use                         AS type_tax_use,
    at.active                               AS active
FROM account_tax at
WHERE at.company_id = %(company_id)s
ORDER BY at.type_tax_use, at.id
