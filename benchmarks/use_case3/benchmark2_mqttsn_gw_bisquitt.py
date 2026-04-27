import socket
import struct
import random
import time

# Configurações de Rede
GW_IP, GW_PORT = "10.0.0.2", 1884
CLIENT_IP = "10.0.0.3"
PREDEFINED_TOPIC_ID = 20
TIMEOUT = 5.0

# Constantes MQTT-SN
MQTTSN_CONNECT, MQTTSN_DISCONNECT = 0x04, 0x18
MQTTSN_CONNACK = 0x05
MQTTSN_PUBLISH = 0x0C
QOS_M1, QOS_0 = 0b11, 0b00
TOPICIDTYPE_PREDEFINED = 0b01

# Lógica de Publicação
def run_benchmark_mqttsn(msgs_per_qos):
    # Lista de QoS para iterar
    test_qos = [QOS_M1, QOS_0]

    for current_qos in test_qos:
        label = "-1" if current_qos == QOS_M1 else "0"
        print(f"Iniciando msgs QoS {label} (Fluxo Completo)...")
        payload = b"MQTTSN_DATA_BENCHMARK" + f"_{time.time()}".encode()

        for i in range(msgs_per_qos):
            # CRIAR NOVO SOCKET PARA CADA ITERAÇÃO (Evita lixo no buffer e pacotes fantasma)
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((CLIENT_IP, 0)) # Porta 0 permite que o SO escolha uma porta efêmera livre
            sock.settimeout(TIMEOUT)
            
            try:
                # CONNECT 
                client_id = f"cli_qos{label}_{i}_{random.randint(1000, 9999)}"
                conn = struct.pack('>BBH', 0x04, 0x01, 60) + client_id.encode()
                sock.sendto(struct.pack('>BB', len(conn)+2, MQTTSN_CONNECT) + conn, (GW_IP, GW_PORT))
                
                # Validação robusta do CONNACK
                resp, _ = sock.recvfrom(1024)
                if resp[1] != MQTTSN_CONNACK:
                    # Se receber algo que não é CONNACK, aborta esta iteração
                    raise Exception(f"Pacote inesperado: {hex(resp[1])}")

                time.sleep(0.001)

                # PUBLISH
                msg_id = random.randint(1, 0xFFFF) if current_qos != QOS_M1 else 0x0000
                flags = (current_qos << 5) | TOPICIDTYPE_PREDEFINED
                header = struct.pack('>BB BHH', len(payload) + 7, MQTTSN_PUBLISH, flags, PREDEFINED_TOPIC_ID, msg_id)
                sock.sendto(header + payload, (GW_IP, GW_PORT))

                time.sleep(0.001)

                # DISCONNECT
                sock.sendto(struct.pack('>BB', 2, MQTTSN_DISCONNECT), (GW_IP, GW_PORT))
                sock.recvfrom(1024) 

            except Exception as e:
                print(f"Erro no loop QoS {label}, msg {i}: {e}")
                # Em caso de erro, tentamos enviar um disconnect cego para limpar o gateway
                try:
                    sock.sendto(struct.pack('>BB', 2, MQTTSN_DISCONNECT), (GW_IP, GW_PORT))
                except:
                    pass
            
            finally:
                sock.close() # Garante o fechamento para liberar a porta no SO

            # Pequena pausa entre mensagens para estabilidade do switch bmv2
            time.sleep(0.01)

if __name__ == "__main__":

    # Testes Gerais
    # MSGS_POR_QOS = 500 # 500 QoS -1 + 500 QoS 0 = 1k total
    MSGS_POR_QOS = 2500 # 2.500 QoS -1 + 2.500 QoS 0 = 5k total
    # MSGS_POR_QOS = 5000 # 5.000 QoS -1 + 5.000 QoS 0 = 10k total

    print(f"--- INICIANDO BENCHMARK MQTTSN ---")

    run_benchmark_mqttsn(MSGS_POR_QOS)
    
    print("\n[SUCESSO] BENCHMARK MQTTSN finalizado.")
