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

    debug('Adicionando Broker MQTT\n')
    bk = net.addDocker(
        'bk', 
        ip='10.0.0.1/8',
        mac="00:00:00:00:00:01", 
        dimage='mqtt-bk',
        dcmd="emqx foreground",
        volumes=['/tmp/.X11-unix:/tmp/.X11-unix:rw'],
        environment={'DISPLAY':":{}".format(DISPLAY_ID)}
    )

    # Equivale a: /home/vboxuser/dissertacao_ppgti
    project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


    client_pub_benchmark1_path = "/benchmarks/use_case1/benchmark1_p4sn.py"
    pub_benchmark1_path = project_path + "/" + client_pub_benchmark1_path

    client_pub_results_benchmark1_path = "/benchmarks/use_case1/p4sn.csv"
    pub_results_benchmark1_path = project_path + "/" + client_pub_results_benchmark1_path

    client_pub_benchmark2_path = "/benchmarks/use_case2/benchmark2_p4sn.py"
    pub_benchmark2_path = project_path + "/" + client_pub_benchmark2_path

    debug("Adicionando sensor publisher\n")
    pb = net.addDocker(
        'pb',
        ip='10.0.0.3/8',
        mac="00:00:00:00:00:03",
        dimage="p4sn-client-pub-sub:latest",
        volumes=['/tmp/.X11-unix:/tmp/.X11-unix:rw',
                 pub_benchmark1_path + ':/app/p4sn/benchmark1_p4sn.py',
                 pub_benchmark2_path + ':/app/p4sn/benchmark2_p4sn.py',
                 pub_results_benchmark1_path + ':/app/p4sn/p4sn.csv'
                ],
        environment={'DISPLAY':":{}".format(DISPLAY_ID)}
    )

    client_sub1_path = "/subscribers/subscriber_p4sn1.py"
    sub1_path = project_path + "/" + client_sub1_path

    client_sub1_time_publication_path = "/benchmarks/use_case2/time_publication_p4sn1.csv"
    sub1_time_publication_path = project_path + "/" + client_sub1_time_publication_path

    debug("Adicionando subscriber 1\n")
    ss1 = net.addDocker(
        'ss1', 
        ip='10.0.0.4/8',
        mac="00:00:00:00:00:04", 
        dimage="p4sn-client-pub-sub:latest",
        volumes=['/tmp/.X11-unix:/tmp/.X11-unix:rw',
                 sub1_path + ':/app/p4sn/subscriber_p4sn1.py',
                 sub1_time_publication_path + ':/app/p4sn/time_publication_p4sn1.csv'],
        environment={'DISPLAY':":{}".format(DISPLAY_ID)}
    )

    client_sub2_path = "/subscribers/subscriber_p4sn2.py"
    sub2_path = project_path + "/" + client_sub2_path

    client_sub2_time_publication_path = "/benchmarks/use_case2/time_publication_p4sn2.csv"
    sub2_time_publication_path = project_path + "/" + client_sub2_time_publication_path

    debug("Adicionando subscriber 2\n")
    ss2 = net.addDocker(
        'ss2', 
        ip='10.0.0.5/8',
        mac="00:00:00:00:00:05", 
        dimage="p4sn-client-pub-sub:latest",
        volumes=['/tmp/.X11-unix:/tmp/.X11-unix:rw',
                 sub2_path + ':/app/p4sn/subscriber_p4sn2.py',
                 sub2_time_publication_path + ':/app/p4sn/time_publication_p4sn2.csv'],
        environment={'DISPLAY':":{}".format(DISPLAY_ID)}
    )

    client_sub3_path = "/subscribers/subscriber_p4sn3.py"
    sub3_path = project_path + "/" + client_sub3_path

    client_sub3_time_publication_path = "/benchmarks/use_case2/time_publication_p4sn3.csv"
    sub3_time_publication_path = project_path + "/" + client_sub3_time_publication_path

    debug("Adicionando subscriber 3\n")
    ss3 = net.addDocker(
        'ss3', 
        ip='10.0.0.6/8',
        mac="00:00:00:00:00:06", 
        dimage="p4sn-client-pub-sub:latest",
        volumes=['/tmp/.X11-unix:/tmp/.X11-unix:rw',
                 sub3_path + ':/app/p4sn/subscriber_p4sn3.py',
                 sub3_time_publication_path + ':/app/p4sn/time_publication_p4sn3.csv'],
        environment={'DISPLAY':":{}".format(DISPLAY_ID)}
    )

    client_sub4_path = "/subscribers/subscriber_p4sn4.py"
    sub4_path = project_path + "/" + client_sub4_path

    client_sub4_time_publication_path = "/benchmarks/use_case2/time_publication_p4sn4.csv"
    sub4_time_publication_path = project_path + "/" + client_sub4_time_publication_path

    debug("Adicionando subscriber 4\n")
    ss4 = net.addDocker(
        'ss4', 
        ip='10.0.0.7/8',
        mac="00:00:00:00:00:07", 
        dimage="p4sn-client-pub-sub:latest",
        volumes=['/tmp/.X11-unix:/tmp/.X11-unix:rw',
                 sub4_path + ':/app/p4sn/subscriber_p4sn4.py',
                 sub4_time_publication_path + ':/app/p4sn/time_publication_p4sn4.csv'],
        environment={'DISPLAY':":{}".format(DISPLAY_ID)}
    )

    client_sub5_path = "/subscribers/subscriber_p4sn5.py"
    sub5_path = project_path + "/" + client_sub5_path

    client_sub5_time_publication_path = "/benchmarks/use_case2/time_publication_p4sn5.csv"
    sub5_time_publication_path = project_path + "/" + client_sub5_time_publication_path

    debug("Adicionando subscriber 5\n")
    ss5 = net.addDocker(
        'ss5', 
        ip='10.0.0.8/8',
        mac="00:00:00:00:00:08", 
        dimage="p4sn-client-pub-sub:latest",
        volumes=['/tmp/.X11-unix:/tmp/.X11-unix:rw',
                 sub5_path + ':/app/p4sn/subscriber_p4sn5.py',
                 sub5_time_publication_path + ':/app/p4sn/time_publication_p4sn5.csv'],
        environment={'DISPLAY':":{}".format(DISPLAY_ID)}
    )


    # Definindo variáveis para inicialização automática do Bisquitt Gateway Transparent
    env_gw = {
        "DISPLAY": ":{}".format(DISPLAY_ID),
        "MQTT_HOST": "10.0.0.1",
        "MQTT_PORT": "1883",
        "HOST": "0.0.0.0",
        "PORT": "1884",
        "BISQUITT_USER": "bisquitt",
        "BISQUITT_GROUP": "bisquitt",
        "PREDEFINED_TOPIC": "*;temperatura;10"
        #"PREDEFINED_TOPIC": "*;umidade;20"
        #"PREDEFINED_TOPICS_FILE": "/etc/bisquitt/predefinedTopics.yaml"
    }

    debug('Adicionando Gateway MQTT-SN\n')
    gw = net.addDocker(
        'gw', 
        ip='10.0.0.2/8',
        mac="00:00:00:00:00:02",
        dimage='mqtt-sn-gw',
        volumes=['/tmp/.X11-unix:/tmp/.X11-unix:rw'],
        dcmd="bisquitt --debug",
        environment=env_gw
    )

    path = os.path.dirname(os.path.abspath(__file__))
    json_file = '/root/p4sn.json'
    config = path + '/rules/commands.txt'
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
    net.addLink(bk, s1, txo=False, rxo=False)
    net.addLink(gw, s1, txo=False, rxo=False)
    net.addLink(pb, s1, txo=False, rxo=False)
    net.addLink(ss1, s1, txo=False, rxo=False)
    net.addLink(ss2, s1, txo=False, rxo=False)
    net.addLink(ss3, s1, txo=False, rxo=False)
    net.addLink(ss4, s1, txo=False, rxo=False)
    net.addLink(ss5, s1, txo=False, rxo=False)

    debug('*** Starting network\n')
    net.build()
    s1.start([])
    net.staticArp()

    # --- Configurando grupos de portas ---
    mc_cmds = """
    mc_mgrp_create 100
    mc_node_create 0 1
    mc_node_create 1 2
    mc_node_create 2 3
    mc_node_create 3 4
    mc_node_create 4 5
    mc_node_create 5 6
    mc_node_create 6 7
    mc_node_create 7 8
    mc_node_associate 100 0
    mc_node_associate 100 1
    mc_node_associate 100 2
    mc_node_associate 100 3
    mc_node_associate 100 4
    mc_node_associate 100 5
    mc_node_associate 100 6
    mc_node_associate 100 7
    mc_mgrp_create 20
    mc_node_create 10 4
    mc_node_create 11 5
    mc_node_create 12 6
    mc_node_create 13 7
    mc_node_create 14 8
    mc_node_associate 20 8
    mc_node_associate 20 9
    mc_node_associate 20 10
    mc_node_associate 20 11
    mc_node_associate 20 12
    """
    s1.cmd('simple_switch_CLI --thrift-port 50001 <<< "{}"'.format(mc_cmds))

    debug("Iniciando broker\n")
    makeTerm(bk)

    debug("Iniciando gateway\n")
    makeTerm(gw)

    debug("Iniciando publisher\n")
    makeTerm(pb)

    debug("Iniciando subscriber 1\n")
    makeTerm(ss1)

    debug("Iniciando subscriber 2\n")
    makeTerm(ss2)

    debug("Iniciando subscriber 3\n")
    makeTerm(ss3)

    debug("Iniciando subscriber 4\n")
    makeTerm(ss4)

    debug("Iniciando subscriber 5\n")
    makeTerm(ss5)

    debug("CLI containernet\n")
    CLI(net)

    debug("Encerrando a rede")
    net.stop()


if __name__ == '__main__':
    setLogLevel('debug')
    topology()