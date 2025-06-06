FROM emqx/emqx:5.9

USER root

# Instalar o bash para evitar a falha do net.addDocker() 
#   "no such file /bin/bash" no containernet, pois essa imagem
#    do eclipse-mosquitto só possui /bin/sh
RUN apt update && apt install bash

# docker build -t mqtt-sn-gw:latest .