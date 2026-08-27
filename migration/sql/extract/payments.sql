-- Customer and vendor payments, for the payments/refunds reconciliation check.
SELECT
    ap.id                                   AS source_id,
    am.name                                 AS name,
    ap.payment_type                         AS payment_type,
    ap.partner_id                           AS partner_id,
    am.date                                 AS date,
    rc.name                                 AS currency,
    ap.amount                               AS amount,
    aj.code                                 AS journal_code,
    am.state                                AS state
FROM account_payment ap
JOIN account_move am        ON am.id = ap.move_id        -- Odoo <= 13: no move_id, join account_move_line
LEFT JOIN account_journal aj ON aj.id = am.journal_id
LEFT JOIN res_currency rc   ON rc.id = ap.currency_id
WHERE am.company_id = %(company_id)s
  AND am.state = 'posted'
  AND am.date <= %(as_of)s
ORDER BY am.date, ap.id
