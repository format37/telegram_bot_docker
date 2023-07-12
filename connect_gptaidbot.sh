# get id of running container with image name
container_id=$(docker ps | grep telegram_bot_docker_gptaidbot_1 | awk '{print $1}')
echo "container id: $container_id"
# get logs
# sudo docker logs -f $container_id
# connect to container
docker exec -it $container_id /bin/bash