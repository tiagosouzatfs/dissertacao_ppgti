#!/usr/bin/env python3
import socket
import struct
import random
import time
import os
import csv

# Constantes
MQTTSN_CONNECT, MQTTSN_CONNACK = 0x04, 0x05
MQTTSN_REGISTER, MQTTSN_REGACK = 0x0A, 0x0B
MQTTSN_PUBLISH, MQTTSN_PUBACK = 0x0C, 0x0D
MQTTSN_PUBREC, MQTTSN_PUBREL = 0x0F, 0x10
MQTTSN_PUBCOMP, MQTTSN_DISCONNECT = 0x0E, 0x18
QOS_M1, QOS_0, QOS_1, QOS_2 = 0b11, 0b00, 0b01, 0b10
GW_IP, GW_PORT = "10.0.0.1", 1884
PREDEFINED_TOPIC_ID = 10

class MQTTSNBenchmark:
    def __init__(self, client_ip):
        self.client_ip = client_ip

    def run_test(self, qos, retain, iteration):
        # Para QoS 2, ClientID consistente ajuda o Broker a não se perder
        client_id_rand = f"sn_{iteration}_{random.randint(1000, 9999)}"
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.client_ip, 0))
        sock.settimeout(2.5)
        
        # ID de mensagem estável para o handshake
        msg_id = (iteration + (qos * 100)) % 0xFFFF
        data_str = "MQTT_SN_PLAIN_DATA".ljust(62, "*")[:62].encode()
        current_topic_id = PREDEFINED_TOPIC_ID
        topic_type = 0x01 # Pre-defined por padrão

        if qos != QOS_M1:
            # AJUSTE QoS 2: Clean Session = 0 (False) para garantir persistência do estado da transação
            clean_session = 0x00 if qos == QOS_2 else 0x04
            conn_payload = struct.pack('>BBH', clean_session, 0x01, 60) + client_id_rand.encode()
            sock.sendto(struct.pack('>BB', len(conn_payload)+2, MQTTSN_CONNECT) + conn_payload, (GW_IP, GW_PORT))
            
            try: 
                sock.recvfrom(1024) # CONNACK
                # Se não for QoS 0 (sem retain), registramos um tópico dinâmico
                if not (qos == QOS_0 and retain == 0):
                    reg_pkt = struct.pack('>BBHH', 15, MQTTSN_REGISTER, 0x0000, msg_id) + b"benchmark"
                    sock.sendto(reg_pkt, (GW_IP, GW_PORT))
                    regack_data, _ = sock.recvfrom(1024)
                    current_topic_id = struct.unpack('>H', regack_data[4:6])[0]
                    topic_type = 0x00 # Normal Topic ID
            except: 
                pass

        # --- INÍCIO DO TIMING ---
        t_start_pub = time.perf_counter()
        
        # Flags: QoS (bits 5-6), Retain (bit 4), TopicIdType (bits 0-1)
        flags = ((qos & 0x03) << 5) | ((retain & 0x01) << 4) | (topic_type & 0x03)
        header = struct.pack('>BHH', flags, current_topic_id, msg_id)
        sock.sendto(struct.pack('>BB', len(header) + len(data_str) + 2, MQTTSN_PUBLISH) + header + data_str, (GW_IP, GW_PORT))
        
        t_end_pub = time.perf_counter() # Tempo apenas do envio do pacote

        # --- HANDSHAKE ---
        if qos == QOS_1:
            try: sock.recvfrom(1024) # PUBACK
            except: pass
        elif qos == QOS_2:
            try:
                # 1. Recebe PUBREC
                rec_data, _ = sock.recvfrom(1024)
                if rec_data[1] == MQTTSN_PUBREC:
                    # 2. Envia PUBREL
                    sock.sendto(struct.pack('>BBH', 4, MQTTSN_PUBREL, msg_id), (GW_IP, GW_PORT))
                    # 3. Recebe PUBCOMP
                    sock.recvfrom(1024)
            except: 
                pass
        
        t_end_total = time.perf_counter() # Tempo do fluxo completo
        
        if qos != QOS_M1: 
            sock.sendto(struct.pack('>BB', 2, MQTTSN_DISCONNECT), (GW_IP, GW_PORT))
        
        sock.close()

        # Formatação para o CSV
        q_label = -1 if qos == 0b11 else qos
        qos_csv = f"{q_label} sem retain" if q_label == 0 and retain == 0 else (f"0 com retain" if q_label == 0 else str(q_label))
        
        print(f"[{iteration}/100] QoS: {q_label} | Retain: {retain} | Total: {round((t_end_total - t_start_pub)*1000, 2)}ms")

        return {
            "cenario": "mqttsn", 
            "qos": qos_csv, 
            "cliente_id": client_id_rand,
            "t_fluxo_publish_ms": round((t_end_pub - t_start_pub)*1000, 4),
            "t_fluxo_total_ms": round((t_end_total - t_start_pub)*1000, 4)
        }

if __name__ == "__main__":

    client = MQTTSNBenchmark("10.0.0.2") 
    if not os.path.exists('results'): os.makedirs('results')
    
    test_cases = [(QOS_M1, 0), (QOS_0, 0), (QOS_0, 1), (QOS_1, 0), (QOS_2, 0)]
    
    with open('results/mqtt-sn.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["cenario", "qos", "cliente_id", "t_fluxo_publish_ms", "t_fluxo_total_ms"])
        writer.writeheader()
        
        for qos, ret in test_cases:
            print(f"\nIniciando testes para QoS {qos} | Retain {ret}")
            for i in range(1, 101):
                writer.writerow(client.run_test(qos, ret, i))
                
    print("\n[SUCESSO] Arquivo results/mqtt-sn.csv gerado.")