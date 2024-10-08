#!/bin/bash
# Create a systemd service that autostarts & manages a docker-compose instance in the current directory
# by Uli Köhler - https://techoverflow.net
# Licensed as CC0 1.0 Universal
SERVICENAME=docker.mapsurvey
SERVICEFILE=/etc/systemd/system/${SERVICENAME}.service
DOCKER=$(which docker)

echo "Creating systemd service... ${SERVICEFILE}"

# check to make sure the docker-compose file exists
if [ ! -f docker-compose.yml ]; then
    echo "ERROR: Missing docker-compose.yml. Run from correct context."
    exit 1
fi

# check to make sure the docker binary exists
if [ -z "$DOCKER" ]; then
    echo "ERROR: Missing docker binary. Check your environment."
    exit 1
fi

# Create systemd service file
echo $SERVICEFILE
cat > $SERVICEFILE <<EOF
[Unit]
Description=$SERVICENAME
Requires=docker.service
After=docker.service

[Service]
Restart=always
User=root
Group=docker
TimeoutStopSec=15
WorkingDirectory=$(pwd)
# Shutdown container (if running) when unit is started
ExecStartPre=$DOCKER compose -f docker-compose.yml down
# Start container when unit is started
ExecStart=$DOCKER compose -f docker-compose.yml up
# Stop container when unit is stopped
ExecStop=$DOCKER compose -f docker-compose.yml down

[Install]
WantedBy=multi-user.target
EOF

echo "Enabling & starting $SERVICENAME"
# Autostart systemd service
sudo systemctl enable $SERVICENAME.service
# Start systemd service now
sudo systemctl start $SERVICENAME.service
