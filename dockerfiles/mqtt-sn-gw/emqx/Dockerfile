FROM emqx/emqx:5.8.6

USER root

RUN apt-get update && apt-get install ethtool net-tools iproute2 iputils-ping -y

USER emqx

EXPOSE 1884 18084

# docker build -t mqtt-sn-gw:latest .