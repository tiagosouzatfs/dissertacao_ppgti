FROM eclipse-mosquitto:2.0.21

# Instalar o bash para evitar a falha do net.addDocker() 
#   "no such file /bin/bash" no containernet, pois essa imagem
#    do eclipse-mosquitto só possui /bin/sh
RUN apk update && apk add --no-cache bash ethtool net-tools

# docker build -t mqtt-broker:latest .