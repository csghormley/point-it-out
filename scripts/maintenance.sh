#!/bin/sh

echo performing a system update, docker system prune, database backup

# define a function to pull the first matching container ID
# from running container lists
get_container_id() {
    if [ -n "$1" ]; then
        docker ps | grep "$1" | head -1 | cut -d" " -f1
    fi
}

# do a system update
#sudo apt-get update && sudo apt-get upgrade

# clean the docker directory
# --force skips confirmation, nothing drastic
sudo docker system prune --force

# check to make sure processes are running
# check disk space
# rotate logs

# perform a database backup to the data folder - not inside the container
export DB=mapbe
export TS=$(date +%s)

# create a temporary script
cat <<EOF > tmp$TS.sh
runuser -u postgres -- pg_dump -d $DB | gzip -c > /tmp/$DB-backup_`date +%Y%m%d-%H%M%S`.sql.gz
runuser -u postgres -- pg_dump --schema-only -d $DB | gzip -c > /tmp/$DB-schema_`date +%Y%m%d-%H%M%S`.sql.gz
mv /tmp/$DB*.sql.gz /var/lib/postgresql/data/pgdata/
EOF

# run the script, then delete it
docker exec -i -u root $(get_container_id postgis) bash < tmp$TS.sh
rm tmp$TS.sh

# ship database backup to g.net
rsync -avz -e "ssh -p2222 -i /root/.ssh/id_rsa_backup" /opt/mapsurvey/postgis_data/pgdata/mapbe*sql.gz backups@ghormley.net:db_backups/$(hostname)
