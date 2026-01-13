#!/bin/bash
# Database backup script for Karunodaya Platform

set -e

# Configuration
BACKUP_DIR="/home/karunodaya/backups"
APP_DIR="/home/karunodaya/app"
DB_FILE="$APP_DIR/production_db.sqlite3"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/karunodaya_backup_$TIMESTAMP.sqlite3"
KEEP_DAYS=30  # Keep backups for 30 days

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup database
echo "$(date): Starting database backup..."
cp "$DB_FILE" "$BACKUP_FILE"

# Compress backup
echo "$(date): Compressing backup..."
gzip "$BACKUP_FILE"

# Delete old backups (older than KEEP_DAYS)
echo "$(date): Cleaning up old backups..."
find "$BACKUP_DIR" -name "karunodaya_backup_*.sqlite3.gz" -mtime +$KEEP_DAYS -delete

# Count backups
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/karunodaya_backup_*.sqlite3.gz 2>/dev/null | wc -l)
echo "$(date): Backup complete. Total backups: $BACKUP_COUNT"

# Set permissions
chmod 640 "$BACKUP_DIR"/karunodaya_backup_*.sqlite3.gz
chown karunodaya:karunodaya "$BACKUP_DIR"/karunodaya_backup_*.sqlite3.gz

echo "$(date): Backup saved to $BACKUP_FILE.gz"
