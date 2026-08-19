# BACKUP KEY CUSTODY

Referenced by `docs/runbooks/BACKUP_RESTORE.md` § 3 and `OPS-012`.

Open question Q4 — this document is a placeholder until the offsite destination and custody model are decided.

## Requirements

- The decryption key is stored outside production, in a different failure domain from the backups.
- At least two named people can retrieve it. A single-custodian key is a single point of failure.
- Retrieval is possible using only the written procedure, by someone who did not create the key.
- Verified at every restore drill.

## Custody register

| Holder | Location / mechanism | Retrieval procedure | Last verified |
|---|---|---|---|
| TBD | | | |
| TBD | | | |

## Rotation

- Rotation frequency: TBD
- Procedure: TBD
- Re-encryption of retained backups on rotation: TBD — old backups must remain restorable for their full retention period.
