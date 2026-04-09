#!/usr/bin/python3

import os

from containernet.net import Containernet
from containernet.node import DockerP4Switch
from containernet.cli import CLI
from containernet.term import makeTerm

from mininet.log import debug, setLogLevel


def topology():
    
    DISPLAY_ID = 0
    os.system('sudo xhost +local:docker')
    os.system('export DISPLAY=:{}'.format(DISPLAY_ID))

    net = Containernet()

    # Definindo variáveis no EMQX Broker para inicialização automática do EMQX Gateway
    emqx_env = {
        "DISPLAY": ":{}".format(DISPLAY_ID),
        "EMQX_GATEWAY__MQTTSN__ENABLE": "true",
        "EMQX_GATEWAY__MQTTSN__GATEWAY_ID": "1",
        "EMQX_GATEWAY__MQTTSN__LISTENERS__UDP__DEFAULT__BIND": "1884",
        # Note o uso de aspas duplas escapadas dentro da string para o JSON dos tópicos
        # "EMQX_GATEWAY__MQTTSN__PREDEFINED": '[{"id": 1, "topic": "sensor/temperatura"}, {"id": 2, "topic": "sensor/umidade"}]'
        "EMQX_GATEWAY__MQTTSN__PREDEFINED": '[{"id": 10, "topic": "temperatura"}, {"id": 20, "topic": "umidade"}]'
    }

    debug('Adicionando Gateway/broker MQTT-SN\n')
    gw_bk = net.addDocker(
        'gw_bk', 
        ip='10.0.0.1', 
        mac="00:00:00:00:00:01", 
        dimage='mqtt-sn-gw',
        volumes=['/tmp/.X11-unix:/tmp/.X11-unix:rw'],
        dcmd="emqx foreground",
        environment=emqx_env
    )

    # Equivale a: /home/vboxuser/dissertacao_ppgti
    project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    client_pub_path = "/dockerfiles/mqtt-sn-client/python/publisher_p4ssn.py"
    pub_path = project_path + "/" + client_pub_path

    debug("Adicionando sensores publishers\n")
    pb1 = net.addDocker(
        'pb1', 
        ip='10.0.0.2', 
        mac="00:00:00:00:00:02", 
        dimage="mqtt-sn-client-python", 
        volumes=['/tmp/.X11-unix:/tmp/.X11-unix:rw', pub_path + ':/root/publisher_p4ssn.py'],
        environment={'DISPLAY':":{}".format(DISPLAY_ID)}
    )

    client_sub1_path = "/dockerfiles/mqtt-sn-client/python/subscriber_p4ssn1.py"
    sub_path1 = project_path + "/" + client_sub1_path

    debug("Adicionando subscriber 1\n")
    ss1 = net.addDocker(
        'ss1', 
        ip='10.0.0.3', 
        mac="00:00:00:00:00:03", 
        dimage="mqtt-sn-client-python", 
        volumes=['/tmp/.X11-unix:/tmp/.X11-unix:rw', sub_path1 + ':/root/subscriber_p4ssn1.py'],
        environment={'DISPLAY':":{}".format(DISPLAY_ID)}
    )

    client_sub2_path = "/dockerfiles/mqtt-sn-client/python/subscriber_p4ssn2.py"
    sub_path2 = project_path + "/" + client_sub2_path

    debug("Adicionando subscriber 2\n")
    ss2 = net.addDocker(
        'ss2', 
        ip='10.0.0.4', 
        mac="00:00:00:00:00:04", 
        dimage="mqtt-sn-client-python", 
        volumes=['/tmp/.X11-unix:/tmp/.X11-unix:rw', sub_path2 + ':/root/subscriber_p4ssn2.py'],
        environment={'DISPLAY':":{}".format(DISPLAY_ID)}
    )

    path = os.path.dirname(os.path.abspath(__file__))
    json_file = '/root/p4ssn.json'
    config = path + '/rules/forwarding.txt'
    args = {'json': json_file, 'switch_config': config}

    debug('*** Adding P4 Switch\n')
    # IPBASE: subnet from eth0 interface,
    s1 = net.addSwitch(
        's1', 
        cls=DockerP4Switch,
        volumes=[path + "/:/root"],
        dimage="ramonfontes/bmv2", 
        netcfg=True, 
        thriftport=50001,
        IPBASE="172.17.0.0/16",
        loglevel="debug",
        **args
    )
    
    debug('Adicionando links\n')
    net.addLink(gw_bk, s1, txo=False, rxo=False)
    net.addLink(pb1, s1, txo=False, rxo=False)
    net.addLink(ss1, s1, txo=False, rxo=False)
    net.addLink(ss2, s1, txo=False, rxo=False)

    debug('*** Starting network\n')
    net.build()
    s1.start([])
    net.staticArp()

    debug("Iniciando gateway/broker\n")
    makeTerm(gw_bk)

    debug("Iniciando publisher\n")
    makeTerm(pb1)

    debug("Iniciando subscriber 1\n")
    makeTerm(ss1)

    debug("Iniciando subscriber 2\n")
    makeTerm(ss2)

    debug("CLI containernet\n")
    CLI(net)

    debug("Encerrando a rede")
    net.stop()


if __name__ == '__main__':
    setLogLevel('debug')
    topology()