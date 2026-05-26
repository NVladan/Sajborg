#!/bin/bash
################################################################################
# Sajborg.com Database Backup Script
# Creates timestamped SQLite backup and removes backups older than 30 days.
#
# Usage: ./backup_db.sh
# Cron example (daily at 2 AM):
#   0 2 * * * /var/www/Sajborg/backup_db.sh >> /var/log/sajborg_backup.log 2>&1
################################################################################

set -e

APP_DIR="/var/www/Sajborg"
DB_PATH="$APP_DIR/instance/pcshop.db"
BACKUP_DIR="$APP_DIR/backups"
RETENTION_DAYS=30

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/pcshop_${TIMESTAMP}.db"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "[$(date)] ERROR: Database file not found at $DB_PATH"
    exit 1
fi

# Create backup using SQLite's built-in .backup command (safe for live databases)
sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"

# Verify backup was created and is not empty
if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "[$(date)] OK: Backup created: $BACKUP_FILE ($BACKUP_SIZE)"
else
    echo "[$(date)] ERROR: Backup failed or file is empty"
    exit 1
fi

# Remove backups older than retention period
DELETED=$(find "$BACKUP_DIR" -name "pcshop_*.db" -mtime +$RETENTION_DAYS -delete -print | wc -l)
if [ "$DELETED" -gt 0 ]; then
    echo "[$(date)] Removed $DELETED backup(s) older than $RETENTION_DAYS days"
fi
