# flask-server-image
## GET: curl -X GET http://<ip>:<port>/frames/<session_id>
## POST: curl -X POST -F "video=@<path>" http://<ip>:<port>/upload

# DOCKER BUILT
  ## docker build -t flask-video-app .
  ## docker run -d -p 8080:80 flask-video-app // mapeando el puerto 8080 de la maquina host al puerto 80 dentro del contenedor de docker
  ## Session iterativa dentro de docker docker ps 
  ## docker exec -it <CONTAINER_ID> /bin/bash
