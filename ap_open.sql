-- Open AP, derived from the payable lines. Mirror image of ar_open.sql.
SELECT
    aml.id                                  AS source_id,
    am.name                                 AS number,
    am.move_type                            AS move_type,
    aml.partner_id                          AS partner_id,
    rp.ref                                  AS partner_ref,
    aml.date                                AS date,
    aml.date_maturity                       AS due_date,
    COALESCE(rc.name, cc.name)              AS currency,
    (aml.credit - aml.debit)                AS amount_total,
    (-aml.amount_residual)                  AS amount_residual,
    aa.code                                 AS account_code,
    am.state                                AS state
FROM account_move_line aml
JOIN account_move am        ON am.id = aml.move_id
JOIN account_account aa     ON aa.id = aml.account_id
LEFT JOIN res_partner rp    ON rp.id = aml.partner_id
LEFT JOIN res_currency rc   ON rc.id = aml.currency_id
JOIN res_company comp       ON comp.id = am.company_id
JOIN res_currency cc        ON cc.id = comp.currency_id
WHERE am.company_id = %(company_id)s
  AND am.state = 'posted'
  AND aml.date <= %(as_of)s
  AND aa.account_type = 'liability_payable'    -- Odoo <= 14: internal_type = 'payable'
  AND aml.amount_residual <> 0
ORDER BY aml.partner_id, aml.date_maturity, aml.id
