#!/usr/bin/env python3
import socket
import struct
import random
import time
import csv

# Constantes
MQTTSN_CONNECT, MQTTSN_PUBLISH = 0x04, 0x0C
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

    def run_iteration(self, qos, retain, iteration):
        client_id = f"mqttsn_client_{iteration}_{random.randint(100, 999)}"
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.client_ip, 0))
        sock.settimeout(TIMEOUT)
        
        msg_id = (iteration + (qos * 100)) % 0xFFFF
        payload = "MQTTSN_DATA_BENCHMARK".encode()
        
        t_start_flow = time.perf_counter()
        t_end_total = 0
        
        try:
            if qos != QOS_M1:
                # CONNECT
                conn = struct.pack('>BBH', 0x04, 0x01, 60) + client_id.encode()
                sock.sendto(struct.pack('>BB', len(conn)+2, MQTTSN_CONNECT) + conn, (GW_IP, GW_PORT))
                sock.recvfrom(1024)

                time.sleep(0.001)

            # PUBLISH (Tópico 10 Fixo)
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

            time.sleep(0.001)
            
            if qos != QOS_M1:
                # DISCONNECT
                sock.sendto(struct.pack('>BB', 2, MQTTSN_DISCONNECT), (GW_IP, GW_PORT))
                sock.recvfrom(1024) # DISCONNECT Gateway

                time.sleep(0.001)

            t_end_total = time.perf_counter()
        except (socket.timeout, Exception):
            t_start_flow = t_end_total = 0
        finally:
            sock.close()

        total_ms = (t_end_total - t_start_flow) * 1000 if t_end_total > 0 else 0
        q_label = -1 if qos == 0b11 else qos
        status = "OK" if total_ms > 0 or qos == QOS_M1 else "FAIL"
        print(f"[{iteration:03}/100] MQTTSN | QoS: {q_label} | {status} | {round(total_ms, 2)}ms")

        return {"cenario": "mqttsn", "qos": qos, "retain": retain, "t_flow_ms": round(total_ms, 4)}

if __name__ == "__main__":
    bench = MQTTSNBenchmark(CLIENT_IP)
    # test_cases = [(QOS_M1, 0), (QOS_0, 0), (QOS_0, 1), (QOS_1, 0), (QOS_2, 0)] # Se quiser testar com retain
    test_cases = [(QOS_M1, 0), (QOS_0, 0), (QOS_1, 0), (QOS_2, 0)]
    
    with open('/app/mqtt-sn/mqttsn.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["cenario", "qos", "retain", "t_flow_ms"])
        writer.writeheader()

        for qos, ret in test_cases:
            print(f"\n### Benchmark MQTT-SN: QoS {qos} | Retain {ret}")
            time.sleep(1)
            for i in range(1, 101):
                writer.writerow(bench.run_iteration(qos, ret, i))
                time.sleep(0.05)