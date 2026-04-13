import socket
import struct
import random
import time

# Configurações de Rede
GW_IP, GW_PORT = "10.0.0.2", 1884
CLIENT_IP = "10.0.0.3"
PREDEFINED_TOPIC_ID = 10
TIMEOUT = 5.0

# Constantes MQTT-SN
MQTTSN_CONNECT, MQTTSN_DISCONNECT = 0x04, 0x18
MQTTSN_PUBLISH = 0x0C
QOS_M1, QOS_0 = 0b11, 0b00
TOPICIDTYPE_PREDEFINED = 0b01

# Lógica de Publicação
def run_benchmark_mqttsn(msgs_per_qos):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((CLIENT_IP, 0))
    sock.settimeout(TIMEOUT)
    
    # QoS -1 (Disparo Direto)
    print("Iniciando msgs QoS -1...")
    payload_m1 = b"MQTTSN_DATA_BENCHMARK" + f"_{time.time()}".encode()

    for i in range(msgs_per_qos):
        msg_id = random.randint(1, 0xFFFF)
        flags = (QOS_M1 << 5) | TOPICIDTYPE_PREDEFINED
        # Header padrão: Length(1), Type(1), Flags(1), TopicId(2), MsgId(2) = 7 bytes
        header = struct.pack('>BB BHH', len(payload_m1) + 7, MQTTSN_PUBLISH, flags, PREDEFINED_TOPIC_ID, msg_id)
        sock.sendto(header + payload_m1, (GW_IP, GW_PORT))
        time.sleep(0.0005)

    time.sleep(0.001)

    # QoS 0 (Connect -> Publish -> Disconnect)
    print("Iniciando msgs QoS 0 (Fluxo Completo)...")
    payload_q0 = b"MQTTSN_DATA_BENCHMARK" + f"_{time.time()}".encode()
    
    for i in range(msgs_per_qos):
        try:
            # CONNECT
            client_id = f"mqttsn_client_{i}"
            conn = struct.pack('>BBH', 0x04, 0x01, 60) + client_id.encode()
            sock.sendto(struct.pack('>BB', len(conn)+2, MQTTSN_CONNECT) + conn, (GW_IP, GW_PORT))
            sock.recvfrom(1024) # Espera CONNACK

            time.sleep(0.0005)

            # PUBLISH
            msg_id = random.randint(1, 0xFFFF)
            flags = (QOS_0 << 5) | TOPICIDTYPE_PREDEFINED
            header = struct.pack('>BB BHH', len(payload_q0) + 7, MQTTSN_PUBLISH, flags, PREDEFINED_TOPIC_ID, msg_id)
            sock.sendto(header + payload_q0, (GW_IP, GW_PORT))

            time.sleep(0.0005)

            # DISCONNECT
            sock.sendto(struct.pack('>BB', 2, MQTTSN_DISCONNECT), (GW_IP, GW_PORT))
            sock.recvfrom(1024) # Espera DISCONNECT

            time.sleep(0.0005)

        except Exception as e:
            print(f"Erro: {e}")

    sock.close()

if __name__ == "__main__":

    MSGS_POR_QOS = 100
    # MSGS_POR_QOS = 500 # 500 QoS -1 + 500 QoS 0 = 1k total
    # MSGS_POR_QOS = 2500 # 2500 QoS -1 + 2500 QoS 0 = 5k total
    # MSGS_POR_QOS = 5000 # 5000 QoS -1 + 5000 QoS 0 = 10k total

    print(f"--- INICIANDO BENCHMARK MQTTSN ---")

    run_benchmark_mqttsn(MSGS_POR_QOS)

    print("\n[SUCESSO] BENCHMARK MQTTSN finalizado.")