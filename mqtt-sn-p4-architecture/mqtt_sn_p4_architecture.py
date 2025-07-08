#!/usr/bin/python

import os

from containernet.net import Containernet
from containernet.node import DockerP4Switch
from containernet.cli import CLI
from containernet.term import makeTerm

from mininet.log import debug, info, setLogLevel


def topology():
    net = Containernet()

    info('Adicionando Broker MQTT\n')
    bk = net.addDocker('bk', ip='10.0.0.1/8', mac="00:00:00:00:00:01", dimage='mqtt-broker')

    info('Adicionando Gateway MQTT-SN\n')
    gw = net.addDocker('gw', ip='10.0.0.2/8', mac="00:00:00:00:00:02", dimage='mqtt-sn-gw')

    info("Adicionando sensores publishers\n")
    pb1 = net.addDocker('pb1', ip='10.0.0.3/8', mac="00:00:00:00:00:03", dimage="mqtt-sn-client")

    info("Adicionando subscriber\n")
    ss1 = net.addDocker('ss1', ip='10.0.0.4/8', mac="00:00:00:00:00:04", dimage="mqtt-sn-client")

    path = os.path.dirname(os.path.abspath(__file__))
    json_file = '/root/mqtt_sn.json' # container directory
    config = path + '/p4src/rules_statics_forward.txt'
    args = {'json': json_file, 'switch_config': config}

    info('*** Adding P4 Switch\n')
    # IPBASE: subnet from eth0 interface,
    s1 = net.addSwitch('s1', cls=DockerP4Switch,
                       volumes=[path + "/p4src:/root"],
                       dimage="ramonfontes/bmv2", cpu_shares=20,
                       netcfg=True, thriftport=50001,
                       IPBASE="172.17.0.0/16", **args)
    
    info('Adicionando links\n')
    net.addLink(bk, s1, txo=False, rxo=False)
    net.addLink(gw, s1, txo=False, rxo=False)
    net.addLink(pb1, s1, txo=False, rxo=False)
    net.addLink(ss1, s1, txo=False, rxo=False)

    info('*** Starting network\n')
    net.build()
    s1.start([])
    net.staticArp()

    info("Iniciando broker mqtt\n")
    makeTerm(bk)

    info("Iniciando gateway mqtt-sn\n")
    makeTerm(gw)

    info("Iniciando publisher\n")
    makeTerm(pb1)

    info("Iniciando subscriber\n")
    makeTerm(ss1)

    info("CLI containernet\n")
    CLI(net)

    info("Encerrando a rede")
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    topology()


# p4c --target bmv2 --arch v1model mqtt_sn.p4