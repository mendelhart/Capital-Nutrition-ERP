-- Posted GL lines up to and including the as-of date.
-- This is the source of truth for the opening trial balance. Draft and
-- cancelled moves are excluded: they are not accounting.
SELECT
    aml.id                                  AS source_id,
    aml.move_id                             AS move_id,
    am.name                                 AS move_name,
    aml.date                                AS date,
    aj.code                                 AS journal_code,
    aa.code                                 AS account_code,
    aa.id                                   AS account_id,
    aml.partner_id                          AS partner_id,
    aml.debit                               AS debit,
    aml.credit                              AS credit,
    (aml.debit - aml.credit)                AS balance,
    rc.name                                 AS currency,
    aml.amount_currency                     AS amount_currency,
    aml.name                                AS label
FROM account_move_line aml
JOIN account_move am        ON am.id = aml.move_id
JOIN account_account aa     ON aa.id = aml.account_id
JOIN account_journal aj     ON aj.id = aml.journal_id
LEFT JOIN res_currency rc   ON rc.id = aml.currency_id
WHERE am.company_id = %(company_id)s
  AND am.state = 'posted'
  AND aml.date <= %(as_of)s
ORDER BY aml.date, aml.move_id, aml.id
