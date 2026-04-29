#!/usr/bin/env python3
import socket
import struct
import random
import time
import csv

# Constantes e Segurança P4SSN
MQTTSN_CONNECT, MQTTSN_PUBLISH = 0x04, 0x0C
MQTTSN_CONNACK = 0x05
MQTTSN_PUBREC, MQTTSN_PUBREL = 0x0F, 0x10
MQTTSN_DISCONNECT = 0x18
QOS_M1, QOS_0, QOS_1, QOS_2 = 0b11, 0b00, 0b01, 0b10
TOPICIDTYPE_PREDEFINED = 0b01
PREDEFINED_TOPIC_ID = 10

GW_IP, GW_PORT = "10.0.0.2", 1884
CLIENT_IP = "10.0.0.3"
TIMEOUT = 5.0

class MQTTSNBenchmark:
    def __init__(self, client_ip):
        self.client_ip = client_ip

    def run_iteration(self, qos, retain, iteration, existing_sock=None):

        is_persistent = existing_sock is not None
        sock = existing_sock if is_persistent else socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        if not is_persistent:
            sock.bind((self.client_ip, 0))
            sock.settimeout(TIMEOUT)
        
        client_id = f"mqttsn_cli_{iteration}_{random.randint(100, 999)}"
        msg_id = (iteration + (qos * 100)) % 0xFFFF if qos != QOS_M1 else 0x0000
        payload = "MQTTSN_DATA_BENCHMARK".encode()
        
        t_start_flow = time.perf_counter()
        t_end_total = 0
        
        try:
            # --- CONNECT ---
            if not is_persistent:
                conn = struct.pack('>BBH', 0x04, 0x01, 60) + client_id.encode()
                sock.sendto(struct.pack('>BB', len(conn)+2, MQTTSN_CONNECT) + conn, (GW_IP, GW_PORT))
                resp, _ = sock.recvfrom(1024)
                if resp[1] != MQTTSN_CONNACK:
                    raise Exception("Erro CONNACK")
                time.sleep(0.001)

            # --- PUBLISH ---
            flags = ((qos & 0x03) << 5) | ((retain & 0x01) << 4) | TOPICIDTYPE_PREDEFINED
            header = struct.pack('>BB BHH', len(payload)+7, MQTTSN_PUBLISH, flags, PREDEFINED_TOPIC_ID, msg_id)
            sock.sendto(header + payload, (GW_IP, GW_PORT))
            
            if qos == QOS_1:
                sock.recvfrom(1024)
            elif qos == QOS_2:
                rec, _ = sock.recvfrom(1024)
                if rec[1] == MQTTSN_PUBREC:
                    sock.sendto(struct.pack('>BBH', 4, MQTTSN_PUBREL, msg_id), (GW_IP, GW_PORT))
                    sock.recvfrom(1024)

            # --- DISCONNECT ---
            if not is_persistent:
                time.sleep(0.001)
                sock.sendto(struct.pack('>BB', 2, MQTTSN_DISCONNECT), (GW_IP, GW_PORT))
                sock.recvfrom(1024) # DISCONNECT Gateway
                t_end_total = time.perf_counter()

            t_end_total = time.perf_counter()

        except (socket.timeout, Exception):
            t_start_flow = t_end_total = 0
        finally:
            if not is_persistent:
                sock.close()

        total_ms = (t_end_total - t_start_flow) * 1000 if t_end_total > 0 else 0
        q_label = -1 if qos == 0b11 else qos
        status = "OK" if total_ms > 0 else "FAIL"
        print(f"[{iteration:03}/100] MQTTSN | QoS: {q_label} | {status} | {round(total_ms, 2)}ms")

        return {"cenario": "mqttsn", "qos": qos, "retain": retain, "t_flow_ms": round(total_ms, 4)}

if __name__ == "__main__":
    bench = MQTTSNBenchmark(CLIENT_IP)
    test_cases = [(QOS_M1, 0), (QOS_0, 0), (QOS_1, 0), (QOS_2, 0)]
    
    with open('/app/mqtt-sn/mqttsn.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["cenario", "qos", "retain", "t_flow_ms"])
        writer.writeheader()
        
        for qos, ret in test_cases:
            print(f"\n### Benchmark MQTT-SN: QoS {qos} | Retain {ret}")
            time.sleep(1)
            
            # --- Lógica Especial para QoS -1 ---
            if qos == QOS_M1:
                p_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                p_sock.bind((CLIENT_IP, 0))
                p_sock.settimeout(TIMEOUT)
                
                # CONNECT 360s
                c_id = f"mqttsn_m1_{random.randint(100,999)}"
                conn_pkt = struct.pack('>BBH', 0x04, 0x01, 360) + c_id.encode()
                p_sock.sendto(struct.pack('>BB', len(conn_pkt)+2, MQTTSN_CONNECT) + conn_pkt, (GW_IP, GW_PORT))
                p_sock.recvfrom(1024) # Espera CONNACK
                
                for i in range(1, 101):
                    writer.writerow(bench.run_iteration(qos, ret, i, existing_sock=p_sock))
                    time.sleep(0.01)
                
                # DISCONNECT Final
                p_sock.sendto(struct.pack('>BB', 2, MQTTSN_DISCONNECT), (GW_IP, GW_PORT))
                p_sock.recvfrom(1024)
                p_sock.close()
            
            # --- Lógica Padrão para QoS 0, 1, 2 (Efêmero) ---
            else:
                for i in range(1, 101):
                    writer.writerow(bench.run_iteration(qos, ret, i))
                    time.sleep(0.05)