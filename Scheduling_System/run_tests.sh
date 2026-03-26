#!/bin/bash
# run_tests.sh - Automate basic testing and logging for the appointment system

DB_FILE="appointments.db"
LOG_FILE="run_log_$(date +%Y%m%d_%H%M).txt"

echo "=== Starting Appointment System Checks ===" | tee -a "$LOG_FILE"

# Check if DB exists
if [ -f "$DB_FILE" ]; then
    echo "Database found: $DB_FILE" | tee -a "$LOG_FILE"
    ls -l "$DB_FILE" | tee -a "$LOG_FILE"
else
    echo "Warning: Database not found. It will be created on first run." | tee -a "$LOG_FILE"
fi

# Run the app and capture output/errors
echo "Launching application..." | tee -a "$LOG_FILE"
python3 main.py 2>&1 | tee -a "$LOG_FILE" | grep -E "(Error|Success|Exception)"

echo "Run completed. Log saved to $LOG_FILE"
