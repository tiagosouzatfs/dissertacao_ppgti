from time import sleep

from containernet.net import Containernet
from containernet.cli import CLI
from containernet.term import makeTerm

from mininet.node import Controller
from mininet.log import info, setLogLevel


setLogLevel('info')

net = Containernet(controller=Controller)
info('Adicionando controlador\n')
net.addController('c0')

info('Adicionando Broker MQTT\n')
bk = net.addDocker('bk', ip='10.0.0.1', dimage='mqtt-broker')

info('Adicionando Gateway MQTT-SN\n')
gw = net.addDocker(
        'gw',
        ip='10.0.0.2',
        dimage='mqtt-sn-gw',
        ports=[1883, 8083, 1884],  # MQTT, WebSocket e MQTT-SN UDP
        port_bindings={
            1883: 1883,     # MQTT TCP
            8083: 8083,     # MQTT WebSocket
            1884: 1884      # MQTT-SN UDP
        },
        environment={
            'EMQX_GATEWAY__MQTTSN__LISTENER__UDP__DEFAULT__ENABLED': 'true',
            'EMQX_LOG__LEVEL': 'debug'
        }
)

info("Adicionando sensores publishers\n")
pb1 = net.addDocker('pb1', ip='10.0.0.3', dimage="mqtt-sn-client")
pb2 = net.addDocker('pb2', ip='10.0.0.4', dimage="mqtt-sn-client")
pb3 = net.addDocker('pb3', ip='10.0.0.5', dimage="mqtt-sn-client")

info("Adicionando subscriber\n")
ss1 = net.addDocker('ss1', ip='10.0.0.6', dimage="mqtt-sn-client")

info('Adicionando os links de modo que o gateway funcione no modo de agregação\n')
net.addLink(gw, bk)
net.addLink(pb1, gw)
net.addLink(pb2, gw)
net.addLink(pb3, gw)
net.addLink(ss1, gw)

info("Iniciando rede\n")
net.start()
sleep(5)

info("Iniciando broker\n")
makeTerm(bk)

sleep(3)

info("Iniciando gateway\n")
makeTerm(gw)

sleep(3)

info("Iniciando subscriber\n")
makeTerm(ss1)

sleep(3)

info("Iniciando sensores publishers\n")

# Temperatura
makeTerm(pb1)

sleep(3)

# Umidade
makeTerm(pb2)

sleep(3)

# Nível de água
makeTerm(pb3)

sleep(3)

info("CLI containernet\n")
CLI(net)

info("Encerrando a rede")
net.stop()