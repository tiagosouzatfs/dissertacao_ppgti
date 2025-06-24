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

info('Adicionando Broker MQTT\n')
bk = net.addDocker('bk', ip='10.0.0.1', dimage='mqtt-broker')

info('Adicionando Gateway MQTT-SN\n')
gw = net.addDocker('gw', ip='10.0.0.2', dimage='mqtt-sn-gw')

info("Adicionando sensores publishers\n")
pb1 = net.addDocker('pb1', ip='10.0.0.3', dimage="mqtt-sn-client")

info("Adicionando subscriber\n")
ss1 = net.addDocker('ss1', ip='10.0.0.4', dimage="mqtt-sn-client")

info('Adicionando links\n')
net.addLink(bk, s1)
net.addLink(gw, s1)
net.addLink(pb1, s1)
net.addLink(ss1, s1)

info("Iniciando rede\n")
net.start()

info("Iniciando broker\n")
makeTerm(bk)

info("Iniciando gateway\n")
makeTerm(gw)

info("Iniciando publisher\n")
# Temperatura
makeTerm(pb1)

info("Iniciando subscriber\n")
makeTerm(ss1)

info("CLI containernet\n")
CLI(net)

info("Encerrando a rede")
net.stop()