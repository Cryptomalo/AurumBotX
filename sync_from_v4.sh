#!/bin/bash

# sync_from_v4.sh - Script to automatically copy critical files from AurumBotX-v4 to AurumBotX

# Variables
SRC_DIR="AurumBotX-v4"
DEST_DIR="AurumBotX"
LOG_FILE="sync_log_$(date +'%Y%m%d_%H%M%S').log"

# Error handling function
handle_error() {
    echo "Error occurred at line $1"
    echo "Check the log file: $LOG_FILE for details"
    exit 1
}

# Logging function
log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

# Create log file
touch $LOG_FILE
log "Sync process started"

# Copying files
COPY_FILES=(
    "${SRC_DIR}/src/wallet_runner_hyperliquid.py"
    "${SRC_DIR}/config/hyperliquid_testnet_10k.json"
    "${SRC_DIR}/scripts/run_bot_loop.sh"
    "${SRC_DIR}/docs/HYPERLIQUID_QUICKSTART.md"
    "${SRC_DIR}/docs/ORACLE_CLOUD_DEPLOYMENT_GUIDE.md"
    "${SRC_DIR}/docs/DEPLOYMENT_SUMMARY.md"
    "${SRC_DIR}/runtime.txt"
    "${SRC_DIR}/requirements.txt"
)

# Loop to copy files
for FILE in "${COPY_FILES[@]}"; do
    cp -f "$FILE" "$DEST_DIR/"
    if [ $? -ne 0 ]; then
        log "Failed to copy $FILE"
        handle_error $LINENO
    else
        log "Copied $FILE successfully"
    fi
done

# Summary report
log "Sync process completed successfully"