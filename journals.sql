-- Journals.
SELECT
    aj.id                                   AS source_id,
    aj.code                                 AS code,
    {{TR(aj.name)}}                         AS name,
    aj.type                                 AS journal_type,
    rc.name                                 AS currency
FROM account_journal aj
LEFT JOIN res_currency rc ON rc.id = aj.currency_id
WHERE aj.company_id = %(company_id)s
ORDER BY aj.code
