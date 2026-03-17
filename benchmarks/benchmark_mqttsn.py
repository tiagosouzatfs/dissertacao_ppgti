#!/usr/bin/env python3
import socket
import struct
import random
import time
import os
import csv

# =============================================================================
# Constantes MQTT-SN
# =============================================================================
MQTTSN_CONNECT      = 0x04
MQTTSN_CONNACK      = 0x05
MQTTSN_REGISTER     = 0x0A
MQTTSN_REGACK       = 0x0B
MQTTSN_PUBLISH      = 0x0C
MQTTSN_PUBACK       = 0x0D
MQTTSN_PUBREC       = 0x0F
MQTTSN_PUBREL       = 0x10
MQTTSN_PUBCOMP      = 0x0E
MQTTSN_DISCONNECT   = 0x18

QOS_M1 = 0b11
QOS_0  = 0b00
QOS_1  = 0b01
QOS_2  = 0b10

TOPICIDTYPE_TOPICNAME       = 0b00
TOPICIDTYPE_PREDEFINEDTOPIC = 0b01

GW_IP = "10.0.0.1"
GW_PORT = 1884
CLIENT_IP = "10.0.0.2"
SERVER_ADDRESS = (GW_IP, GW_PORT)
TIMEOUT = 5.0

class MQTTSNBenchmark:
    def __init__(self, client_ip):
        self.client_ip = client_ip

    def build_packet(self, msg_type, payload):
        return struct.pack('>BB', len(payload) + 2, msg_type) + payload

    def run_iteration(self, qos, retain, iteration):
        client_id = f"bench_{iteration}_{random.randint(100, 999)}"
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.client_ip, 0))
        sock.settimeout(TIMEOUT)
        
        msg_id = (iteration + (qos * 100)) % 0xFFFF
        data_str = "MQTT_SN_PURE_DATA_BENCHMARK".ljust(62, "*")[:62]
        
        t_start_flow = time.perf_counter()
        t_start_pub = 0
        t_end_total = 0
        
        try:
            # Lógica Híbrida de Tópico
            # QoS -1 OU (QoS 0 e SEM Retain) -> Predefined ID 10
            use_predefined = (qos == QOS_M1) or (qos == QOS_0 and retain == 0)

            if qos != QOS_M1:
                # CONNECT
                conn_payload = struct.pack('>BBH', 0x04, 0x01, 60) + client_id.encode()
                sock.sendto(self.build_packet(MQTTSN_CONNECT, conn_payload), SERVER_ADDRESS)
                sock.recvfrom(1024) 

                if not use_predefined:
                    # REGISTER para "benchmark"
                    reg_payload = struct.pack('>HH', 0x0000, msg_id) + b"benchmark"
                    sock.sendto(self.build_packet(MQTTSN_REGISTER, reg_payload), SERVER_ADDRESS)
                    regack, _ = sock.recvfrom(1024)
                    topic_id = struct.unpack('>H', regack[2:4])[0]
                    topic_type = TOPICIDTYPE_TOPICNAME
                else:
                    topic_id = 10
                    topic_type = TOPICIDTYPE_PREDEFINEDTOPIC
            else:
                # QoS -1 usa sempre Predefined
                topic_id = 10
                topic_type = TOPICIDTYPE_PREDEFINEDTOPIC

            # --- PUBLISH ---
            t_start_pub = time.perf_counter()
            
            retain_bit = (retain & 0x01) << 4 if qos != QOS_M1 else 0
            flags = ((qos & 0x03) << 5) | (topic_type & 0x03) | retain_bit
            pub_header = struct.pack('>BHH', flags, topic_id, msg_id)
            sock.sendto(self.build_packet(MQTTSN_PUBLISH, pub_header + data_str.encode()), SERVER_ADDRESS)
            
            t_end_pub = time.perf_counter()

            # --- HANDSHAKES ---
            if qos == QOS_1:
                sock.recvfrom(1024) # PUBACK
            elif qos == QOS_2:
                resp, _ = sock.recvfrom(1024)
                if resp[1] == MQTTSN_PUBREC:
                    sock.sendto(self.build_packet(MQTTSN_PUBREL, struct.pack('>H', msg_id)), SERVER_ADDRESS)
                    sock.recvfrom(1024) # PUBCOMP
            
            t_end_total = time.perf_counter()

            if qos != QOS_M1:
                sock.sendto(self.build_packet(MQTTSN_DISCONNECT, b""), SERVER_ADDRESS)

        except (socket.timeout, Exception):
            t_start_pub = t_end_pub = t_end_total = t_start_flow
        finally:
            sock.close()

        total_ms = (t_end_total - t_start_flow) * 1000 if t_end_total > t_start_flow else 0
        status = "OK" if total_ms > 0 or qos == QOS_M1 else "FAIL"
        print(f"[{iteration:03}/100] QoS: {qos} | Retain: {retain} | {status} | {round(total_ms, 2)}ms")

        return {
            "cenario": "mqttsn", "qos": qos, "retain": retain,
            "t_publish_ms": round((t_end_pub - t_start_pub)*1000, 4) if t_end_pub > 0 else 0,
            "t_total_ms": round(total_ms, 4)
        }

if __name__ == "__main__":
    bench = MQTTSNBenchmark(CLIENT_IP)
    if not os.path.exists('results'): os.makedirs('results')
    
    test_cases = [(QOS_M1, 0), (QOS_0, 0), (QOS_0, 1), (QOS_1, 0), (QOS_2, 0)]
    
    with open('results/mqttsn.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["cenario", "qos", "retain", "t_publish_ms", "t_total_ms"])
        writer.writeheader()
        
        for qos, ret in test_cases:
            print(f"\n>>> Bateria: QoS {qos} | Retain {ret}")
            time.sleep(2)
            for i in range(1, 101):
                writer.writerow(bench.run_iteration(qos, ret, i))
                time.sleep(0.05)