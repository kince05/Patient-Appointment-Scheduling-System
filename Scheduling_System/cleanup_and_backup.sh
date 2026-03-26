#!/bin/bash
# cleanup_and_backup.sh - Backup DB and clean old logs

BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M)

mkdir -p "$BACKUP_DIR"

# Backup database with timestamp
if [ -f "appointments.db" ]; then
    cp "appointments.db" "${BACKUP_DIR}/appointments_${TIMESTAMP}.db"
    echo "Database backed up to ${BACKUP_DIR}/appointments_${TIMESTAMP}.db"
else
    echo "No database to backup."
fi

# Clean old log files (>7 days) using find and pipe
echo "Cleaning old logs..."
find . -name "*.log" -mtime +7 | xargs -I {} rm -v {} 2>/dev/null || echo "No old logs to clean."

echo "Cleanup and backup completed."
