import socket
import struct
import random
import time
from multiprocessing import Process

# --- Configurações de Rede ---
GW_IP, GW_PORT = "10.0.0.2", 1884
CLIENT_IP = "10.0.0.3"
PREDEFINED_TOPIC_ID = 10
TIMEOUT = 5.0

# --- Constantes MQTT-SN Padrão ---
MQTTSN_CONNECT, MQTTSN_DISCONNECT = 0x04, 0x18
MQTTSN_PUBLISH = 0x0C
QOS_M1, QOS_0 = 0b11, 0b00
TOPICIDTYPE_PREDEFINED = 0b01

# --- Lógica de Disparo ---
def run_stress_mqttsn(worker_id, msgs_per_qos):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((CLIENT_IP, 0))
    sock.settimeout(TIMEOUT)
    
    # 1. Bateria QoS -1 (Disparo Direto - Sem Criptografia)
    print(f"[Worker {worker_id}] Iniciando msgs QoS -1 (MQTTSN Puro)...")
    payload_m1 = b"MQTTSN_STRESS_M1_STANDARD".ljust(64, b"*")[:64]
    
    for i in range(msgs_per_qos):
        msg_id = random.randint(1, 0xFFFF)
        flags = (QOS_M1 << 5) | TOPICIDTYPE_PREDEFINED
        # Header padrão: Length(1), MsgType(1), Flags(1), TopicId(2), MsgId(2)
        header = struct.pack('>BB BHH', len(payload_m1)+7, MQTTSN_PUBLISH, flags, PREDEFINED_TOPIC_ID, msg_id)
        sock.sendto(header + payload_m1, (GW_IP, GW_PORT))
        time.sleep(0.0005)

    # 2. Bateria QoS 0 (Connect -> Publish -> Disconnect - Sem Criptografia)
    print(f"[Worker {worker_id}] Iniciando msgs QoS 0 (MQTTSN Puro - Fluxo Completo)...")
    payload_q0 = b"MQTTSN_STRESS_Q0_STANDARD".ljust(64, b"*")[:64]
    
    for i in range(msgs_per_qos):
        try:
            # CONNECT
            client_id = f"mq_w{worker_id}_i{i}"
            conn = struct.pack('>BBH', 0x04, 0x01, 60) + client_id.encode()
            sock.sendto(struct.pack('>BB', len(conn)+2, MQTTSN_CONNECT) + conn, (GW_IP, GW_PORT))
            sock.recvfrom(1024) # Espera CONNACK

            # PUBLISH (Tópico e Payload em texto claro)
            msg_id = random.randint(1, 0xFFFF)
            flags = (QOS_0 << 5) | TOPICIDTYPE_PREDEFINED
            header = struct.pack('>BB BHH', len(payload_q0)+7, MQTTSN_PUBLISH, flags, PREDEFINED_TOPIC_ID, msg_id)
            sock.sendto(header + payload_q0, (GW_IP, GW_PORT))

            # DISCONNECT
            sock.sendto(struct.pack('>BB', 2, MQTTSN_DISCONNECT), (GW_IP, GW_PORT))
            time.sleep(0.001)
        except:
            pass

    sock.close()

if __name__ == "__main__":
    NUM_CLIENTES = 4
    MSGS_POR_QOS = 10000 # 10k QoS -1 + 10k QoS 0 = 20k por cliente (80k total)
    
    processos = []
    print(f"--- INICIANDO BENCHMARK MQTTSN PADRÃO: 80.000 MENSAGENS ---")
    
    for i in range(NUM_CLIENTES):
        p = Process(target=run_stress_mqttsn, args=(i, MSGS_POR_QOS))
        processos.append(p)
        p.start()

    for p in processos:
        p.join()

    print("\n[SUCESSO] Baseline MQTTSN finalizado.")