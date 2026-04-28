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
        print(f"Iniciando msgs QoS {label}...")
        payload_base = b"MQTTSN_DATA_BENCHMARK"

        # --- CASO ESPECIAL: QoS -1 ---
        if current_qos == QOS_M1:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((CLIENT_IP, 0))
            sock.settimeout(TIMEOUT)
            
            try:
                # CONNECT com Keep Alive de 360 segundos
                client_id = f"mqttsn_persistent_m1_{random.randint(1000, 9999)}"
                conn = struct.pack('>BBH', 0x04, 0x01, 360) + client_id.encode()
                sock.sendto(struct.pack('>BB', len(conn)+2, MQTTSN_CONNECT) + conn, (GW_IP, GW_PORT))
                
                resp, _ = sock.recvfrom(1024)
                if resp[1] == MQTTSN_CONNACK:
                    print(f"   Sessão QoS -1 ativa (KeepAlive 360s). Enviando {msgs_per_qos} mensagens...")

                for i in range(msgs_per_qos):
                    payload = payload_base + f"_{i}_{time.time()}".encode()
                    # PUBLISH (msg_id 0x0000 para QoS -1)
                    flags = (QOS_M1 << 5) | TOPICIDTYPE_PREDEFINED
                    header = struct.pack('>BB BHH', len(payload) + 7, MQTTSN_PUBLISH, flags, PREDEFINED_TOPIC_ID, 0x0000)
                    sock.sendto(header + payload, (GW_IP, GW_PORT))
                    
                    time.sleep(0.001)

                # DISCONNECT
                sock.sendto(struct.pack('>BB', 2, MQTTSN_DISCONNECT), (GW_IP, GW_PORT))
                sock.recvfrom(1024)
                print("   Sessão QoS -1 finalizada.")

            except Exception as e:
                print(f"Erro no fluxo QoS -1: {e}")
            finally:
                sock.close()

        # --- CASO PADRÃO: QoS 0 (CONEXÃO EFÊMERA POR MENSAGEM) ---
        else:
            for i in range(msgs_per_qos):
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind((CLIENT_IP, 0))
                sock.settimeout(TIMEOUT)
                
                try:
                    payload = payload_base + f"_{i}_{time.time()}".encode()
                    # CONNECT
                    client_id = f"mqttsn_client_0_{i}_{random.randint(1000, 9999)}"
                    conn = struct.pack('>BBH', 0x04, 0x01, 60) + client_id.encode()
                    sock.sendto(struct.pack('>BB', len(conn)+2, MQTTSN_CONNECT) + conn, (GW_IP, GW_PORT))
                    
                    resp, _ = sock.recvfrom(1024)
                    if resp[1] != MQTTSN_CONNACK: raise Exception("Sem CONNACK")
                    
                    time.sleep(0.001)

                    # PUBLISH
                    msg_id = random.randint(1, 0xFFFF)
                    flags = (QOS_0 << 5) | TOPICIDTYPE_PREDEFINED
                    header = struct.pack('>BB BHH', len(payload) + 7, MQTTSN_PUBLISH, flags, PREDEFINED_TOPIC_ID, msg_id)
                    sock.sendto(header + payload, (GW_IP, GW_PORT))

                    time.sleep(0.001)

                    # DISCONNECT
                    sock.sendto(struct.pack('>BB', 2, MQTTSN_DISCONNECT), (GW_IP, GW_PORT))
                    sock.recvfrom(1024) # Espera DISCONNECT

                    time.sleep(0.001)

                except Exception as e:
                    print(f"Erro no loop QoS 0, msg {i}: {e}")
                finally:
                    sock.close()

if __name__ == "__main__":

    # Testes Gerais
    MSGS_POR_QOS = 500 # 500 QoS -1 + 500 QoS 0 = 1k total
    # MSGS_POR_QOS = 2500 # 2.500 QoS -1 + 2.500 QoS 0 = 5k total
    # MSGS_POR_QOS = 5000 # 5.000 QoS -1 + 5.000 QoS 0 = 10k total

    print(f"--- INICIANDO BENCHMARK MQTTSN ---")

    run_benchmark_mqttsn(MSGS_POR_QOS)

    print("\n[SUCESSO] BENCHMARK MQTTSN finalizado.")