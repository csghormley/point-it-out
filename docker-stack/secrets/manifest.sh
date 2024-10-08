FILES="app_db_password django_secret_key email_host_password root_db_password"

for f in $FILES; do
    if [ ! -f "$f.txt" ]; then
        echo "$f" > $f.txt;
    else
        echo "file $f.txt exists"
    fi
done
