-- Chart of accounts.
SELECT
    aa.id                                   AS source_id,
    aa.code                                 AS code,
    {{TR(aa.name)}}                         AS name,
    aa.account_type                         AS account_type,
    aa.reconcile                            AS reconcile,
    aa.deprecated                           AS deprecated,
    rc.name                                 AS currency
FROM account_account aa
LEFT JOIN res_currency rc ON rc.id = aa.currency_id
WHERE aa.company_id = %(company_id)s
ORDER BY aa.code
