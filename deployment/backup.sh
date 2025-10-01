# Create dir and script
sudo mkdir -p /opt/plc-data-collector /var/backups/plc-data-collector
sudo tee /opt/plc-data-collector/backup.sh >/dev/null <<'BASH'
#!/usr/bin/env bash
set -euo pipefail

# Config discovery
CONF_FILES=(
  /etc/plc-data-collector.conf
  /etc/default/plc-data-collector
  /opt/plc-data-collector/.env
)
DB_PATH=""
for f in "${CONF_FILES[@]}"; do
  if [ -f "$f" ]; then
    # Accept DB_PATH=/path or SQLITE_DB=/path
    DB_PATH="$(grep -E '^(DB_PATH|SQLITE_DB)=' "$f" | tail -n1 | cut -d= -f2- || true)"
    [ -n "${DB_PATH}" ] && break
  fi
done

# Fallbacks if not configured
if [ -z "${DB_PATH}" ]; then
  for p in \
    /var/lib/plc-data-collector/plc.db \
    /var/lib/plc-data-collector/data.db \
    /opt/plc-data-collector/data.db \
    /opt/plc-data-collector/plc.db
  do
    [ -f "$p" ] && DB_PATH="$p" && break
  done
fi

if [ -z "${DB_PATH}" ] || [ ! -f "${DB_PATH}" ]; then
  echo "ERROR: SQLite DB file not found. Set DB_PATH=/full/path/to.db in /etc/plc-data-collector.conf" >&2
  exit 1
fi

BACKUP_DIR=${BACKUP_DIR:-/var/backups/plc-data-collector}
mkdir -p "$BACKUP_DIR"

ts="$(date +%F_%H%M%S)"
base="$(basename "$DB_PATH" .db)"
dst="$BACKUP_DIR/${base}_${ts}.db"

# Hot backup (safe while DB is in use)
sqlite3 "$DB_PATH" ".backup '$dst'"

# Optional: verify backup isn't empty
[ -s "$dst" ] || { echo "ERROR: Backup file is empty: $dst" >&2; exit 2; }

# Keep last 14, delete older
ls -1t "$BACKUP_DIR"/*.db 2>/dev/null | tail -n +15 | xargs -r rm -f

echo "OK: Backed up $DB_PATH -> $dst"
BASH

# Permissions (root + service group)
sudo chown root:plc-collector /opt/plc-data-collector/backup.sh
sudo chmod 0750 /opt/plc-data-collector/backup.sh
