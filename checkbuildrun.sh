#!/bin/sh

# usage: ./checkbuildrun.sh [backup]
# If "backup" is provided, triggers database backup after build

# Configuration
DB_CONTAINER="postgis17"
DB_NAME="mapbe"

# Parse arguments
DO_BACKUP=false
if [ "$1" = "backup" ]; then
    DO_BACKUP=true
fi

sudo ./scripts/build.sh && \
    sudo systemctl restart docker.mapsurvey.service

# hacky but it makes things work in this new arrangement
sleep 1

# Run backup if requested
if [ "$DO_BACKUP" = true ]; then
    echo "Running database backup..."
    ./scripts/backup-db.sh "$DB_CONTAINER" "$DB_NAME" || {
        echo "WARNING: Backup failed, but continuing with deployment"
    }
fi

sudo ./scripts/maintenance.sh && \
    ./scripts/status.sh
