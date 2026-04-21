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

    # Definindo variáveis para inicialização automática do EMQX Gateway
    emqx_env_bk = {
        "DISPLAY": ":{}".format(DISPLAY_ID),
    
        # 1. Define o SQL da regra (Escuta no tópico que vem do Gateway)
        "EMQX_RULE_ENGINE__RULES__republish_to_gw__SQL": "SELECT * FROM \"#\"",
        "EMQX_RULE_ENGINE__RULES__republish_to_gw__ENABLE": "true",

        # 2. Define a função da Action como "republish" (Padrão nativo do EMQX)
        "EMQX_RULE_ENGINE__RULES__republish_to_gw__ACTIONS__1__FUNCTION": "republish",

        # 3. Define os argumentos (Onde a mensagem será enviada de volta)
        # Tópico de destino que o gateway estará escutando
        "EMQX_RULE_ENGINE__RULES__republish_to_gw__ACTIONS__1__ARGS__TOPIC": "${topic}",
        "EMQX_RULE_ENGINE__RULES__republish_to_gw__ACTIONS__1__ARGS__QOS": "${qos}",
        "EMQX_RULE_ENGINE__RULES__republish_to_gw__ACTIONS__1__ARGS__RETAIN": "${flags.retain}",
        
        # Encaminha o mesmo payload original recebido
        "EMQX_RULE_ENGINE__RULES__republish_to_gw__ACTIONS__1__ARGS__PAYLOAD": "${payload}",
        
        # Evita que a mensagem entre em loop infinito no broker (Boa prática v5)
        "EMQX_RULE_ENGINE__RULES__republish_to_gw__ACTIONS__1__ARGS__DIRECT_DISPATCH": "true"
    }

    debug('Adicionando Broker MQTT\n')
    bk = net.addDocker(
        'bk', 
        ip='10.0.0.1/8',
        mac="00:00:00:00:00:01", 
        dimage='mqtt-sn-gw',
        dcmd="emqx foreground",
        environment=emqx_env_bk
    )

    # Equivale a: /home/vboxuser/dissertacao_ppgti
    project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    client_pub_path = "/benchmarks/use_case1/publisher_mqttsn.py"
    pub_path = project_path + "/" + client_pub_path

    client_pub_benchmark1_path = "/benchmarks/use_case2/benchmark1_mqttsn.py"
    pub_benchmark1_path = project_path + "/" + client_pub_benchmark1_path

    client_pub_results_benchmark1_path = "/benchmarks/use_case2/mqttsn.csv"
    pub_results_benchmark1_path = project_path + "/" + client_pub_results_benchmark1_path

    client_pub_benchmark2_path = "/benchmarks/use_case3/benchmark2_mqttsn.py"
    pub_benchmark2_path = project_path + "/" + client_pub_benchmark2_path

    debug("Adicionando sensor publisher\n")
    pb = net.addDocker(
        'pb',
        ip='10.0.0.3/8',
        mac="00:00:00:00:00:03",
        dimage="mqtt-sn-client-python",
        volumes=['/tmp/.X11-unix:/tmp/.X11-unix:rw', 
                 pub_path + ':/root/publisher_p4ssn.py',
                 pub_benchmark1_path + ':/root/benchmark1_mqttsn.py',
                 pub_benchmark2_path + ':/root/benchmark2_mqttsn.py',
                 pub_results_benchmark1_path + ':/root/mqttsn.csv'
                ],
        environment={'DISPLAY':":{}".format(DISPLAY_ID)}
    )

    client_sub1_path = "/subscribers/subscriber_mqttsn1.py"
    sub1_path = project_path + "/" + client_sub1_path

    client_sub1_time_publication_path = "/benchmarks/use_case3/time_publication_mqttsn1.csv"
    sub1_time_publication_path = project_path + "/" + client_sub1_time_publication_path

    debug("Adicionando subscriber 1\n")
    ss1 = net.addDocker(
        'ss1', 
        ip='10.0.0.4/8',
        mac="00:00:00:00:00:04", 
        dimage="mqtt-sn-client-python",
        volumes=['/tmp/.X11-unix:/tmp/.X11-unix:rw', 
                 sub1_path + ':/root/subscriber_mqttsn1.py',
                 sub1_time_publication_path + ':/root/time_publication_mqttsn1.csv'],
        environment={'DISPLAY':":{}".format(DISPLAY_ID)}
    )

    client_sub2_path = "/subscribers/subscriber_mqttsn2.py"
    sub2_path = project_path + "/" + client_sub2_path

    client_sub2_time_publication_path = "/benchmarks/use_case3/time_publication_mqttsn2.csv"
    sub2_time_publication_path = project_path + "/" + client_sub2_time_publication_path

    debug("Adicionando subscriber 2\n")
    ss2 = net.addDocker(
        'ss2', 
        ip='10.0.0.5/8',
        mac="00:00:00:00:00:05", 
        dimage="mqtt-sn-client-python",
        volumes=['/tmp/.X11-unix:/tmp/.X11-unix:rw',
                 sub2_path + ':/root/subscriber_mqttsn2.py',
                 sub2_time_publication_path + ':/root/time_publication_mqttsn2.csv'],
        environment={'DISPLAY':":{}".format(DISPLAY_ID)}
    )

    client_sub3_path = "/subscribers/subscriber_mqttsn3.py"
    sub3_path = project_path + "/" + client_sub3_path

    client_sub3_time_publication_path = "/benchmarks/use_case3/time_publication_mqttsn3.csv"
    sub3_time_publication_path = project_path + "/" + client_sub3_time_publication_path

    debug("Adicionando subscriber 3\n")
    ss3 = net.addDocker(
        'ss3', 
        ip='10.0.0.6/8',
        mac="00:00:00:00:00:06", 
        dimage="mqtt-sn-client-python",
        volumes=['/tmp/.X11-unix:/tmp/.X11-unix:rw',
                 sub3_path + ':/root/subscriber_mqttsn3.py',
                 sub3_time_publication_path + ':/root/time_publication_mqttsn3.csv'],
        environment={'DISPLAY':":{}".format(DISPLAY_ID)}
    )

    client_sub4_path = "/subscribers/subscriber_mqttsn4.py"
    sub4_path = project_path + "/" + client_sub4_path

    client_sub4_time_publication_path = "/benchmarks/use_case3/time_publication_mqttsn4.csv"
    sub4_time_publication_path = project_path + "/" + client_sub4_time_publication_path

    debug("Adicionando subscriber 4\n")
    ss4 = net.addDocker(
        'ss4', 
        ip='10.0.0.7/8',
        mac="00:00:00:00:00:07", 
        dimage="mqtt-sn-client-python",
        volumes=['/tmp/.X11-unix:/tmp/.X11-unix:rw',
                 sub4_path + ':/root/subscriber_mqttsn4.py',
                 sub4_time_publication_path + ':/root/time_publication_mqttsn4.csv'],
        environment={'DISPLAY':":{}".format(DISPLAY_ID)}
    )

    client_sub5_path = "/subscribers/subscriber_mqttsn5.py"
    sub5_path = project_path + "/" + client_sub5_path

    client_sub5_time_publication_path = "/benchmarks/use_case3/time_publication_mqttsn5.csv"
    sub5_time_publication_path = project_path + "/" + client_sub5_time_publication_path

    debug("Adicionando subscriber 5\n")
    ss5 = net.addDocker(
        'ss5', 
        ip='10.0.0.8/8',
        mac="00:00:00:00:00:08", 
        dimage="mqtt-sn-client-python",
        volumes=['/tmp/.X11-unix:/tmp/.X11-unix:rw',
                 sub5_path + ':/root/subscriber_mqttsn5.py',
                 sub5_time_publication_path + ':/root/time_publication_mqttsn5.csv'],
        environment={'DISPLAY':":{}".format(DISPLAY_ID)}
    )

    # Definindo variáveis para inicialização automática do EMQX Gateway
    emqx_env_gw = {
        "DISPLAY": ":{}".format(DISPLAY_ID),

        # Gateway
        "EMQX_GATEWAY__MQTTSN__ENABLE": "true",
        "EMQX_GATEWAY__MQTTSN__GATEWAY_ID": "1",
        "EMQX_GATEWAY__MQTTSN__LISTENERS__UDP__DEFAULT__BIND": "1884",
        "EMQX_GATEWAY__MQTTSN__PREDEFINED": '[{"id": 10, "topic": "temperatura"}, {"id": 20, "topic": "umidade"}]',

        # Desabilita listeners mqtt
        "EMQX_LISTENERS__TCP__DEFAULT__ENABLE": "false",
        "EMQX_LISTENERS__SSL__DEFAULT__ENABLE": "false",
        "EMQX_LISTENERS__WS__DEFAULT__ENABLE": "false",
        "EMQX_LISTENERS__WSS__DEFAULT__ENABLE": "false",
        
        # CONNECTOR (Note o nome 'broker' em minúsculo)
        "EMQX_CONNECTORS__MQTT__BROKER__SERVER": "10.0.0.1:1883",
        "EMQX_CONNECTORS__MQTT__BROKER__RECONNECT_INTERVAL": "5s",
        
        # ACTION
        "EMQX_ACTIONS__MQTT__SEND_BROKER__CONNECTOR": "broker",
        "EMQX_ACTIONS__MQTT__SEND_BROKER__PARAMETERS__TOPIC": "${topic}",
        "EMQX_ACTIONS__MQTT__SEND_BROKER__PARAMETERS__QOS": "${qos}",
        "EMQX_ACTIONS__MQTT__SEND_BROKER__PARAMETERS__PAYLOAD": "${payload}",
        "EMQX_ACTIONS__MQTT__SEND_BROKER__PARAMETERS__RETAIN": "${flags.retain}",
        
        # RULE
        # Define o SQL da regra (Enviar todas as publicações para o broker)
        "EMQX_RULE_ENGINE__RULES__SEND_BROKER__SQL": "SELECT * FROM \"#\"",
        # Associa o nome da Action existente a essa regra
        "EMQX_RULE_ENGINE__RULES__SEND_BROKER__ACTIONS__1": "mqtt:send_broker"
    }

    debug('Adicionando Gateway MQTT-SN\n')
    gw = net.addDocker(
        'gw', 
        ip='10.0.0.2/8',
        mac="00:00:00:00:00:02", 
        dimage='mqtt-sn-gw',
        volumes=['/tmp/.X11-unix:/tmp/.X11-unix:rw'],
        dcmd="emqx foreground",
        environment=emqx_env_gw
    )

    path = os.path.dirname(os.path.abspath(__file__))
    json_file = '/root/mqtt-sn.json'
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

    #debug("Iniciando broker\n")
    #makeTerm(bk)

    #debug("Iniciando gateway\n")
    #makeTerm(gw)

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