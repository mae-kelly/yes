#!/bin/bash

# Automated backup system for Scherman Trading System

set -e

BACKUP_DIR="./data/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="scherman_backup_${TIMESTAMP}"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Encryption settings
ENCRYPTION_KEY="${ENCRYPTION_KEY:-$(openssl rand -base64 32)}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${BACKUP_DIR}/backup.log"
}

create_backup() {
    log "Starting backup: $BACKUP_NAME"
    
    # Create backup directory
    mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"
    
    # Backup configuration
    if [ -d "config/" ]; then
        cp -r config/ "${BACKUP_DIR}/${BACKUP_NAME}/config/" 2>/dev/null || true
    fi
    
    # Backup logs (last 30 days)
    if [ -d "logs/" ]; then
        mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}/logs/"
        find logs/ -name "*.log" -mtime -30 -exec cp {} "${BACKUP_DIR}/${BACKUP_NAME}/logs/" \; 2>/dev/null || true
    fi
    
    # Backup data files
    if [ -d "data/" ]; then
        cp -r data/ "${BACKUP_DIR}/${BACKUP_NAME}/data/" 2>/dev/null || true
    fi
    
    # Create backup manifest
    cat > "${BACKUP_DIR}/${BACKUP_NAME}/manifest.txt" << MANIFEST
Scherman Trading System Backup
Created: $(date)
Backup Name: $BACKUP_NAME
Contents:
- Configuration files
- Log files (last 30 days)
- Trading data
- System state
MANIFEST
    
    # Create encrypted archive
    tar -czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" -C "${BACKUP_DIR}" "${BACKUP_NAME}"
    
    # Encrypt if key provided
    if [ -n "$ENCRYPTION_KEY" ]; then
        openssl enc -aes-256-cbc -salt -in "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" \
                    -out "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz.enc" \
                    -k "$ENCRYPTION_KEY"
        rm "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
        log "Backup encrypted: ${BACKUP_NAME}.tar.gz.enc"
    fi
    
    # Cleanup temp directory
    rm -rf "${BACKUP_DIR}/${BACKUP_NAME}"
    
    # Cleanup old backups (keep 30 days)
    find "${BACKUP_DIR}" -name "scherman_backup_*.tar.gz*" -mtime +30 -delete 2>/dev/null || true
    
    log "Backup completed: $BACKUP_NAME"
}

# Run backup
create_backup

