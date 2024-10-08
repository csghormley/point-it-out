if [ -z $1 ]; then
    echo "parameter missing"
    exit
fi

if [ -n $2 ]; then
    STACK=$2
else
    STACK=teststack
fi


if [ $1 = "start" ]; then
    cat docker-compose.yml | docker stack deploy --compose-file - $STACK

elif [ $1 = "restart" ]; then
    docker stack rm teststack
    cat docker-compose.yml | docker stack deploy --compose-file - $STACK

elif [ $1 = "stop" ]; then
    docker stack rm $STACK
fi

sleep 1 && docker ps
