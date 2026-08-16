# TOS_DATABASE_BACKUP_GOOGLE_DRIVE_RESTORE_V1

Database-only PostgreSQL backup/restore for TOS, adapted from the THRS backup design for the current TOS ES Modules architecture.

## Features

- Dedicated Google Drive OAuth connection for database backups.
- PostgreSQL `pg_dump` custom-format backup and `pg_restore --list` verification.
- AES-256-GCM encrypted backup files.
- Daily automatic backup with configurable time and IANA timezone (`Africa/Cairo` by default).
- Retains the latest 3 database backups in the configured Drive folder.
- Manual **Backup Now** from TOS Settings.
- Restore preparation validates the selected backup in an isolated temporary database before production restore.
- Explicit `RESTORE` confirmation and maintenance lock during production restore.
- Existing TOS System/Source Backup remains separate and unchanged.

## Source base

Prepared against TOS `main` commit:

`e41bbd7f9132e22761006089e9813fd5846eff2d`

## Rebuild the patch

The patch is segmented only to keep GitHub connector uploads reliable. Concatenate in this exact order:

```bash
cat \
  TOS_DATABASE_BACKUP_GOOGLE_DRIVE_RESTORE_V1.patch.part01 \
  TOS_DATABASE_BACKUP_GOOGLE_DRIVE_RESTORE_V1.patch.part02a \
  TOS_DATABASE_BACKUP_GOOGLE_DRIVE_RESTORE_V1.patch.part02b \
  TOS_DATABASE_BACKUP_GOOGLE_DRIVE_RESTORE_V1.patch.part02c \
  TOS_DATABASE_BACKUP_GOOGLE_DRIVE_RESTORE_V1.patch.part02d \
  TOS_DATABASE_BACKUP_GOOGLE_DRIVE_RESTORE_V1.patch.part03 \
  > TOS_DATABASE_BACKUP_GOOGLE_DRIVE_RESTORE_V1.patch
```

Then verify and apply:

```bash
git apply --check TOS_DATABASE_BACKUP_GOOGLE_DRIVE_RESTORE_V1.patch
git apply TOS_DATABASE_BACKUP_GOOGLE_DRIVE_RESTORE_V1.patch
```

## Required server setup

Generate and securely store a dedicated 32-byte encryption key:

```bash
openssl rand -hex 32
```

Configure it as:

```env
TOS_DB_BACKUP_ENCRYPTION_KEY=<64-hex-characters>
TOS_DB_BACKUP_CONFIG_DIR=/var/lib/tos/database-backups
TOS_DB_BACKUP_TMP_DIR=/var/tmp/tos-db-backups
```

Do not lose or rotate the encryption key without a migration plan: old encrypted backups cannot be restored without the original key.

The runtime must also have PostgreSQL client tools available (`pg_dump`, `pg_restore`, `psql`, `createdb`, `dropdb`).

## Patch size verification

Expected segment sizes in bytes:

- part01: `7502`
- part02a: `5543`
- part02b: `5561`
- part02c: `5561`
- part02d: `3865`
- part03: `6609`
- reconstructed patch total: `34641`
