from containernet.net import Containernet
from containernet.cli import CLI
from containernet.term import makeTerm

from mininet.node import Controller
from mininet.log import info, setLogLevel


setLogLevel('debug')

net = Containernet(controller=Controller)
info('Adicionando controlador\n')
net.addController('c0')

info('Adicionando switch\n')
s1 = net.addSwitch('s1')

# Definindo variáveis no EMQX Broker para inicialização automática do EMQX Gateway
emqx_env = {
    "EMQX_GATEWAY__MQTTSN__ENABLE": "true",
    "EMQX_GATEWAY__MQTTSN__GATEWAY_ID": "1",
    "EMQX_GATEWAY__MQTTSN__LISTENERS__UDP__DEFAULT__BIND": "1884",
    # Note o uso de aspas duplas escapadas dentro da string para o JSON dos tópicos
    "EMQX_GATEWAY__MQTTSN__PREDEFINED": '[{"id": 10, "topic": "temperatura"}]'
}

info('Adicionando Gateway-Broker MQTT-SN\n')
gw_bk = net.addDocker(
    'gw_bk', 
    ip='10.0.0.1',
    mac="00:00:00:00:00:01", 
    dimage='mqtt-sn-gw',
    dcmd="emqx foreground",
    environment=emqx_env
)

info("Adicionando sensores publishers\n")
pb1 = net.addDocker(
    'pb1',
    ip='10.0.0.2',
    mac="00:00:00:00:00:02",
    dimage="mqtt-sn-client-python"
)

info("Adicionando subscriber 1\n")
ss1 = net.addDocker(
    'ss1', 
    ip='10.0.0.3',
    mac="00:00:00:00:00:03", 
    dimage="mqtt-sn-client-python"
)

info("Adicionando subscriber 2\n")
ss2 = net.addDocker(
    'ss2', 
    ip='10.0.0.4',
    mac="00:00:00:00:00:04", 
    dimage="mqtt-sn-client-python"
)

info('Adicionando links\n')
net.addLink(gw_bk, s1)
net.addLink(pb1, s1)
net.addLink(ss1, s1)
net.addLink(ss2, s1)

info("Iniciando rede\n")
net.start()

info("Iniciando gateway-broker\n")
makeTerm(gw_bk)

info("Iniciando publisher\n")
makeTerm(pb1)

info("Iniciando subscriber 1\n")
makeTerm(ss1)

info("Iniciando subscriber 2\n")
makeTerm(ss2)

info("CLI containernet\n")
CLI(net)

info("Encerrando a rede")
net.stop()