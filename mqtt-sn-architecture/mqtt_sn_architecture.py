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

info('Adicionando Gateway-Broker MQTT-SN\n')
gw_bk = net.addDocker('gw_bk', ip='10.0.0.1', dimage='mqtt-sn-gw')

info("Adicionando sensores publishers\n")
pb1 = net.addDocker('pb1', ip='10.0.0.2', dimage="mqtt-sn-client")

info("Adicionando subscriber\n")
ss1 = net.addDocker('ss1', ip='10.0.0.3', dimage="mqtt-sn-client")

info('Adicionando links\n')
net.addLink(gw_bk, s1)
net.addLink(pb1, s1)
net.addLink(ss1, s1)

info("Iniciando rede\n")
net.start()

info("Iniciando gateway-broker\n")
makeTerm(gw_bk)

info("Iniciando publisher\n")
makeTerm(pb1)

info("Iniciando subscriber\n")
makeTerm(ss1)

info("CLI containernet\n")
CLI(net)

info("Encerrando a rede")
net.stop()