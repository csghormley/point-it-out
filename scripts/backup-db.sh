#!/bin/bash

# do not run unless running from project root
[ -e scripts/bootstrap.sh ] || { echo "This script must be run from the project root directory."; exit 1; }

# Exit on error, undefined variables, and pipe failures
set -euo pipefail

# usage:
# ./scripts/backup-db.sh [container] [db] [server-name] [ssh-port]
# example command line:
# ./scripts/backup-db.sh postgis17 mapbe myserver.net 2222
#
# Environment variables (optional):
#   SSH_KEY_PATH - Path to SSH key for remote backup (default: /root/.ssh/id_rsa_backup)
#   SSH_USER - SSH user for remote backup (default: backups)
#   SSH_SERVER - Remote server for backup upload
#   SSH_PORT - SSH port for remote backup (default: 22)
#   BACKUP_DIR - Local directory for backups (default: postgis_data/pgdata)

# Parse command-line arguments (container and database are required)
if [ -z "${1:-}" ]; then
    echo "ERROR: Container name is required" >&2
    echo "Usage: $0 <container> <database> [ssh-server] [ssh-port]" >&2
    exit 1
fi

if [ -z "${2:-}" ]; then
    echo "ERROR: Database name is required" >&2
    echo "Usage: $0 <container> <database> [ssh-server] [ssh-port]" >&2
    exit 1
fi

export CONT="$1"
export DB="$2"
export SSH_SERVER="${3:-${SSH_SERVER:-}}"
export SSH_PORT="${4:-${SSH_PORT:-22}}"

# Other configuration with environment variable fallbacks
export SSH_KEY_PATH="${SSH_KEY_PATH:-/root/.ssh/id_rsa_backup}"
export SSH_USER="${SSH_USER:-backups}"
export BACKUP_DIR="${BACKUP_DIR:-postgis_data/pgdata}"

# Generate timestamps and backup filename
export TS=$(date +%s)
export DATESTAMP=$(date +%Y%m%d-%H%M%S)
export BACKUP_FILE="$DB-backup-$DATESTAMP.sql.gz"
export TEMP_SCRIPT="tmp-backup-${TS}-$$.sh"

echo "=== Database Backup Script (postgres running inside docker container) ==="
echo "Container: $CONT"
echo "Database: $DB"
echo "Backup file: $BACKUP_FILE"

# Cleanup function to remove temp files on exit
cleanup() {
    if [ -f "$TEMP_SCRIPT" ]; then
        rm -f "$TEMP_SCRIPT"
    fi
}
trap cleanup EXIT

# Define a function to pull the first matching container ID
# from running container lists
get_container_id() {
    if [ -n "$1" ]; then
        local matches=$(docker ps --format "{{.Names}} {{.ID}}" | grep "$1" | wc -l)
        # only return for unique output
        if [ "$matches" -eq 1 ]; then
            docker ps --format "{{.Names}} {{.ID}}" | grep "$1" | awk '{print $2}'
        elif [ "$matches" -gt 1 ]; then
            echo "ERROR: Multiple containers match '$1'" >&2
            exit 1
        else
            echo ""
        fi
    fi
}

# Wait for container to be running
wait_for_container() {
    local name="$1"
    local timeout=30
    local count=0

    echo "Waiting for container '$name' to be running..."
    while [ $count -lt $timeout ]; do
        if docker ps | grep -q "$name"; then
            echo "Container '$name' is running"
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done

    echo "ERROR: Timeout waiting for container '$name'" >&2
    return 1
}

# Wait for db in a container to be online
wait_for_db() {
    local container="$1"
    local db="$2"
    local timeout=30
    local count=0

    local container_id=$(get_container_id "$container")

    if [ -z "$container_id" ]; then
        echo "ERROR: Could not find container ID for '$container'" >&2
        return 1
    fi

    echo "Waiting for database '$db' to be ready..."
    while [ $count -lt $timeout ]; do
        if docker exec -i -u root "$container_id" runuser -u postgres -- psql -l 2>/dev/null | grep -q "$db"; then
            echo "Database '$db' is ready"
            return 0
        fi
        echo "Waiting... ($count/$timeout)"
        sleep 1
        count=$((count + 1))
    done

    echo "ERROR: Timeout waiting for database '$db' in container '$container'" >&2
    return 1
}

# Create a temporary script to execute the backup
cat <<EOF > "$TEMP_SCRIPT"
#!/bin/bash
set -euo pipefail

# Perform database dump
runuser -u postgres -- pg_dumpall | gzip -c > /tmp/$BACKUP_FILE

# Verify backup was created and has content
if [ ! -f /tmp/$BACKUP_FILE ]; then
    echo "ERROR: Backup file was not created" >&2
    exit 1
fi

if [ ! -s /tmp/$BACKUP_FILE ]; then
    echo "ERROR: Backup file is empty" >&2
    exit 1
fi

# Move backup to persistent storage
mv /tmp/$BACKUP_FILE /var/lib/postgresql/data/pgdata/

echo "Backup completed: $BACKUP_FILE"
EOF

# Make sure the container is running before we try to access it
echo "Checking container status..."
export DB_CONTAINER=$(get_container_id "$CONT")

if [ -z "$DB_CONTAINER" ]; then
    echo "ERROR: Container '$CONT' not found" >&2
    exit 1
fi

echo "Found container ID: $DB_CONTAINER"

wait_for_container "$CONT"
wait_for_db "$CONT" "$DB"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Run the backup script in the container
echo "Executing backup in container..."
if docker exec -i -u root "$DB_CONTAINER" bash < "$TEMP_SCRIPT"; then
    echo "Backup created successfully"
else
    echo "ERROR: Backup failed" >&2
    exit 1
fi

# Verify local backup file exists
if [ ! -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found at $BACKUP_DIR/$BACKUP_FILE" >&2
    exit 1
fi

# Get backup file size for reporting
BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
echo "Backup size: $BACKUP_SIZE"

# Create symlink to the latest backup
echo "Creating symlink to latest backup..."
ln -sf "$BACKUP_FILE" "$BACKUP_DIR/$DB-backup-latest.sql.gz"

# Ship database backup to remote server if configured
if [ -n "$SSH_SERVER" ]; then
    echo "Shipping database backup to $SSH_USER@$SSH_SERVER..."

    # Determine base path (try to find the actual full path)
    FULL_BACKUP_PATH="$(cd "$(dirname "$BACKUP_DIR")" && pwd)/$(basename "$BACKUP_DIR")"
    HOSTNAME=$(hostname)

    # Build rsync command with SSH options
    RSYNC_CMD="rsync -avz"

    if [ -f "$SSH_KEY_PATH" ]; then
        RSYNC_CMD="$RSYNC_CMD -e \"ssh -p$SSH_PORT -i $SSH_KEY_PATH\""
    else
        RSYNC_CMD="$RSYNC_CMD -e \"ssh -p$SSH_PORT\""
        echo "WARNING: SSH key not found at $SSH_KEY_PATH, attempting passwordless SSH" >&2
    fi

    # Use eval to properly handle the quoted ssh command
    if eval "$RSYNC_CMD \"$FULL_BACKUP_PATH/$BACKUP_FILE\" \"$SSH_USER@$SSH_SERVER:db_backups/$HOSTNAME/\""; then
        echo "Remote backup successful"
    else
        echo "WARNING: Remote backup failed, but local backup is available" >&2
        exit 0  # Don't fail the script if remote backup fails
    fi
else
    echo "No remote server configured, skipping remote backup"
fi

echo "=== Backup Complete ==="
echo "Local backup: $BACKUP_DIR/$BACKUP_FILE"
[ -n "$SSH_SERVER" ] && echo "Remote backup: $SSH_USER@$SSH_SERVER:db_backups/$(hostname)/$BACKUP_FILE"
