#!/usr/bin/python

import os

from containernet.net import Containernet
from containernet.node import DockerP4Switch
from containernet.cli import CLI
from containernet.term import makeTerm

from mininet.log import debug, info, setLogLevel


def topology():
    
    DISPLAY_ID = 0
    os.system('sudo xhost +local:docker')
    os.system('export DISPLAY=:{}'.format(DISPLAY_ID))

    net = Containernet()

    debug('Adicionando Broker MQTT\n')
    bk = net.addDocker('bk', ip='10.0.0.1/8', mac="00:00:00:00:00:01", dimage='mqtt-broker')

    debug('Adicionando Gateway MQTT-SN\n')
    gw = net.addDocker('gw', ip='10.0.0.2/8', mac="00:00:00:00:00:02", dimage='mqtt-sn-gw')

    debug("Adicionando sensores publishers\n")
    pb1 = net.addDocker(
        'pb1', 
        ip='10.0.0.3/8', 
        mac="00:00:00:00:00:03", 
        dimage="mqtt-sn-client", 
        volumes=['/tmp/.X11-unix:/tmp/.X11-unix:rw'],
        environment={'DISPLAY':":{}".format(DISPLAY_ID)}
    )

    debug("Adicionando subscriber\n")
    ss1 = net.addDocker(
        'ss1', 
        ip='10.0.0.4/8', 
        mac="00:00:00:00:00:04", 
        dimage="mqtt-sn-client", 
        volumes=['/tmp/.X11-unix:/tmp/.X11-unix:rw'],
        environment={'DISPLAY':":{}".format(DISPLAY_ID)}
    )

    path = os.path.dirname(os.path.abspath(__file__))
    json_file = '/root/gw_agg_mqtt_sn.json' # container directory
    config = path + '/rules/static_forwarding.txt'
    args = {'json': json_file, 'switch_config': config}

    debug('*** Adding P4 Switch\n')
    # IPBASE: subnet from eth0 interface,
    s1 = net.addSwitch(
        's1', 
        cls=DockerP4Switch,
        volumes=[path + "/:/root"],
        dimage="ramonfontes/bmv2", 
        cpu_shares=20,
        netcfg=True, 
        thriftport=50001,
        IPBASE="172.17.0.0/16",
        loglevel="debug",
        **args
    )
    
    debug('Adicionando links\n')
    net.addLink(bk, s1, txo=False, rxo=False)
    net.addLink(gw, s1, txo=False, rxo=False)
    net.addLink(pb1, s1, txo=False, rxo=False)
    net.addLink(ss1, s1, txo=False, rxo=False)

    debug('*** Starting network\n')
    net.build()
    s1.start([])
    net.staticArp()

    debug("Iniciando broker mqtt\n")
    #makeTerm(bk)

    debug("Iniciando gateway\n")
    makeTerm(gw)

    debug("Iniciando publisher\n")
    makeTerm(pb1)

    debug("Iniciando subscriber\n")
    makeTerm(ss1)

    debug("CLI containernet\n")
    CLI(net)

    debug("Encerrando a rede")
    net.stop()


if __name__ == '__main__':
    setLogLevel('debug')
    topology()
    