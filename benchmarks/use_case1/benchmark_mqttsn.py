#!/usr/bin/env python3
import socket
import struct
import random
import time
import os
import csv

# =============================================================================
# Constantes MQTT-SN Padrão
# =============================================================================
MQTTSN_CONNECT, MQTTSN_CONNACK = 0x04, 0x05
MQTTSN_PUBLISH, MQTTSN_PUBACK = 0x0C, 0x0D
MQTTSN_PUBREC, MQTTSN_PUBREL = 0x0F, 0x10
MQTTSN_PUBCOMP, MQTTSN_DISCONNECT = 0x0E, 0x18

QOS_M1, QOS_0, QOS_1, QOS_2 = 0b11, 0b00, 0b01, 0b10
TOPICIDTYPE_PREDEFINED = 0b01

GW_IP, GW_PORT = "10.0.0.1", 1884
CLIENT_IP = "10.0.0.2"
TIMEOUT = 5.0
PREDEFINED_TOPIC_ID = 10

# =============================================================================
# Classe de Benchmark MQTT-SN (Standard)
# =============================================================================
class MQTTSNBenchmark:
    def __init__(self, client_ip):
        self.client_ip = client_ip

    def run_iteration(self, qos, retain, iteration):
        client_id = f"sn_{iteration}_{random.randint(100, 999)}"
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.client_ip, 0))
        sock.settimeout(TIMEOUT)
        
        msg_id = (iteration + (qos * 100)) % 0xFFFF
        # Payload de texto simples (sem criptografia)
        data_str = "MQTTSN_STANDARD_DATA_BENCHMARK"
        payload = data_str.encode()
        
        t_end_flow = 0
        
        try:
            # 1. SETUP (Fora da medição do fluxo de publicação)
            if qos != QOS_M1:
                # CONNECT (Mensagem de 6 bytes + ID do cliente)
                conn = struct.pack('>BBH', 0x04, 0x01, 60) + client_id.encode()
                sock.sendto(struct.pack('>BB', len(conn)+2, MQTTSN_CONNECT) + conn, (GW_IP, GW_PORT))
                sock.recvfrom(1024)

            # --- INÍCIO DA MEDIÇÃO DO FLUXO ---
            t_start_flow = time.perf_counter()
            
            flags = ((qos & 0x03) << 5) | ((retain & 0x01) << 4) | TOPICIDTYPE_PREDEFINED
            
            # Cabeçalho PUBLISH padrão (sem Salt/OTP): Length(1), MsgType(1), Flags(1), TopicID(2), MsgID(2)
            # Nota: Se o payload for grande (>255), o cabeçalho MQTT-SN muda, mas aqui usamos 1 byte para o tamanho.
            header = struct.pack('>BB BHH', len(payload)+7, MQTTSN_PUBLISH, flags, PREDEFINED_TOPIC_ID, msg_id)
            sock.sendto(header + payload, (GW_IP, GW_PORT))
            
            # --- HANDSHAKES ---
            if qos == QOS_0 or qos == QOS_M1:
                t_end_flow = time.perf_counter()
            
            elif qos == QOS_1:
                sock.recvfrom(1024) # Espera PUBACK
                t_end_flow = time.perf_counter()
                
            elif qos == QOS_2:
                rec, _ = sock.recvfrom(1024) # Espera PUBREC
                if rec[1] == MQTTSN_PUBREC:
                    # Envia PUBREL
                    sock.sendto(struct.pack('>BBH', 4, MQTTSN_PUBREL, msg_id), (GW_IP, GW_PORT))
                    # Espera PUBCOMP
                    sock.recvfrom(1024)
                t_end_flow = time.perf_counter()
            # --- FIM DA MEDIÇÃO DO FLUXO ---

            if qos != QOS_M1:
                sock.sendto(struct.pack('>BB', 2, MQTTSN_DISCONNECT), (GW_IP, GW_PORT))

        except (socket.timeout, Exception):
            t_start_flow = t_end_flow = 0
        finally:
            sock.close()

        flow_ms = (t_end_flow - t_start_flow) * 1000 if t_end_flow > 0 else 0
        q_label = -1 if qos == 0b11 else qos
        print(f"[{iteration:03}/100] QoS: {q_label} | Retain: {retain} | Flow: {round(flow_ms, 4)}ms")

        return {
            "cenario": "mqttsn",
            "qos": qos,
            "retain": retain,
            "t_flow_ms": round(flow_ms, 4)
        }

if __name__ == "__main__":
    bench = MQTTSNBenchmark(CLIENT_IP)
    if not os.path.exists('results'): os.makedirs('results')
    
    test_cases = [(QOS_M1, 0), (QOS_0, 0), (QOS_0, 1), (QOS_1, 0), (QOS_2, 0)]
    
    with open('results/mqttsn_std.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["cenario", "qos", "retain", "t_flow_ms"])
        writer.writeheader()
        
        for qos, ret in test_cases:
            print(f"\n>>> Bateria MQTT-SN Padrão: QoS {qos} | Retain {ret}")
            time.sleep(1)
            for i in range(1, 101):
                writer.writerow(bench.run_iteration(qos, ret, i))
                time.sleep(0.05)

    print(f"\n[SUCESSO] CSV results/mqttsn_std.csv gerado.")