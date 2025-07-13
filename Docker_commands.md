#install Docker
curl https://get.docker.com/ | bash


#Docker Commands
for I in {1..10};do
docker un -d nginx:latest
done

-----------------
#stop_all_the_containers

docker stop $(docker ps -aq)
DOCKER rm $(docker ps -aq)
