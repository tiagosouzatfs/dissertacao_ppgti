FROM alpine:3.22.0

RUN apk update && \
    apk add --no-cache bash && \
    apk add --no-cache mosquitto-clients

# Instalar o bash para evitar a falha do net.addDocker() 
#   "no such file /bin/bash" no containernet, pois essa imagem
#    do alpine só possui /bin/sh

# docker build -t mqtt-client:latest .