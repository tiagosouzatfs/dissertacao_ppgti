from containernet.net import Containernet
from containernet.cli import CLI
from containernet.term import makeTerm

from mininet.node import Controller
from mininet.log import info, setLogLevel

from time import sleep


setLogLevel('info')

net = Containernet(controller=Controller)
info("Adicionando controlador\n")
net.addController('c0')

info("Adicionando switch\n")
s1 = net.addSwitch('s1')

info("Adicionando broker Mosquitto\n")
'''
# O arquivo "/mosquitto-no-auth.conf" permite o acesso anônimo, ou seja, 
#   sem autenticação ao seviço do broker MQTT.

# Caso queira trabalhar com acesso autenticado, utilize
#   "/mosquitto/config/mosquitto.conf" (já é o padrão de execução da imagem)

# Use a flag "dcmd" abaixo para inciar o serviço do mosquitto ou o comando "makeTerm" mais abaixo

bk = net.addDocker('bk', \
                    ip='10.0.0.10', \
                    dimage="mqtt-broker", \
                    dcmd="/usr/sbin/mosquitto -c /mosquitto-no-auth.conf -v"
)
'''
bk = net.addDocker('bk', ip='10.0.0.10', dimage="mqtt-broker")

info("Adicionando sensores publishers\n")
pb1 = net.addDocker('pb1', ip='10.0.0.11', dimage="mqtt-client")
pb2 = net.addDocker('pb2', ip='10.0.0.12', dimage="mqtt-client")
pb3 = net.addDocker('pb3', ip='10.0.0.13', dimage="mqtt-client")

info("Adicionando subscriber\n")
ss1 = net.addDocker('ss1', ip='10.0.0.14', dimage="mqtt-client")

info("Adicionando links\n")
net.addLink(bk, s1)
net.addLink(pb1, s1)
net.addLink(pb2, s1)
net.addLink(pb3, s1)
net.addLink(ss1, s1)

info("Iniciando rede\n")
net.start()
sleep(5)

info("Iniciando broker\n")
#makeTerm(bk)
makeTerm(bk,
         title='broker',
         cmd="/usr/sbin/mosquitto -c /mosquitto-no-auth.conf -v;"
)

sleep(3)

info("Iniciando subscriber no collector\n")
makeTerm(ss1, 
         title='collector', 
         cmd="bash -c 'mosquitto_sub -h 10.0.0.10 -t sensors/# -v;'"
)
#makeTerm(ss1)

sleep(3)

info("Iniciando sensores publishers com dados variáveis\n")

# Temperatura
makeTerm(pb1, \
         title='pb1', \
         cmd="bash -c 'mosquitto_pub -h 10.0.0.10 -t sensors/temperature -m 20;'"
)
#makeTerm(pb1)

sleep(3)

# Umidade
makeTerm(pb2, \
         title='pb2', \
         cmd="bash -c 'mosquitto_pub -h 10.0.0.10 -t sensors/humidity -m 15%;'"
)
#makeTerm(pb2)

sleep(3)

# Nível de água
makeTerm(pb3, \
         title='pb3', \
         cmd="bash -c 'mosquitto_pub -h 10.0.0.10 -t sensors/waterlevel -m 10;'"
)
#makeTerm(pb3)        

info("CLI containernet\n")
CLI(net)

info("Encerrando a rede")
net.stop()
