#!/usr/bin/env python3
"""
Benchmark runner for MQTT-SN over SECSN + P4 switch.
"""

import socket, struct, time, random, argparse, csv, os
from concurrent.futures import ThreadPoolExecutor, as_completed

# --------------------------
# Constants (copied/adapted)
# --------------------------
MQTTSN_CONNECT = 0x04
MQTTSN_CONNACK = 0x05
MQTTSN_REGISTER = 0x0A
MQTTSN_REGACK = 0x0B
MQTTSN_PUBLISH = 0x0C
MQTTSN_PUBACK = 0x0D
MQTTSN_PUBCOMP = 0x0E
MQTTSN_PUBREC = 0x0F
MQTTSN_PUBREL = 0x10
MQTTSN_DISCONNECT = 0x18

TYPE_SECSN = 0x3F7A
SECRET_KEY_SECSN = 0xA5C3F27B
SECRET_MASK_DATA_SECSN = 0xB37A94C4E18F2761A5F9C0B48D37ACD2E0B3C4D15A7F823BE6A2FDFE41C967A0F2E37B5C1DA4EF092B8D5C67A93F04D1B7E2C8A59431DE0A87B1F2C49E03D56A

# Mapping used in code: keep numeric QoS representation for flag bits
QOS_M1 = 0b11
QOS_0  = 0b00
QOS_1  = 0b01
QOS_2  = 0b10

TOPICIDTYPE_NORMAL = 0b00

# default timeouts (seconds)
RECV_TIMEOUT = 5.0
CONNECT_TIMEOUT = 5.0
REGISTER_TIMEOUT = 5.0
PUBLISH_TIMEOUT = 5.0
PUBREL_TIMEOUT = 5.0
DISCONNECT_TIMEOUT = 3.0

# --------------------------
# Helper functions (SECSN / MQTT-SN)
# --------------------------
def ip_to_int_local(ip):
    return struct.unpack("!I", bytes(map(int, ip.split('.'))))[0]

def generate_auth_authX(src_ip, dst_ip, src_port, dst_port, msg_type, secret_key=SECRET_KEY_SECSN):
    src_ip_int = ip_to_int_local(src_ip) & 0xFFFFFFFF
    dst_ip_int = ip_to_int_local(dst_ip) & 0xFFFFFFFF
    src_port &= 0xFFFF
    dst_port &= 0xFFFF
    msg_type &= 0xFF
    secret_key &= 0xFFFFFFFF

    op1 = (((src_ip_int & 0xFFFF) ^ (dst_ip_int >> 16)) + src_port) & 0xFFFF
    op2 = (((dst_port ^ msg_type) << 2) + (secret_key & 0xFFFF)) & 0xFFFF

    h = 0
    h = (h ^ src_ip_int) & 0xFFFFFFFF
    h = (((h << 5) | (h >> 27)) & 0xFFFFFFFF)
    h = (h + dst_ip_int) & 0xFFFFFFFF
    h = (h ^ (((src_port << 16) | dst_port) & 0xFFFFFFFF)) & 0xFFFFFFFF
    h = (h + ((msg_type << 8) & 0xFFFFFFFF)) & 0xFFFFFFFF
    h = (h ^ (((op1 << 16) | op2) & 0xFFFFFFFF)) & 0xFFFFFFFF
    h = (h + secret_key) & 0xFFFFFFFF
    return h & 0xFFFF

def build_secsn_packet(mqttsn_payload, client_ip, src_port, gw_ip, gw_port):
    """
    Prepend the simplified SECSN header used in your environment:
    [TYPE_SECSN(2 bytes), authX(2 bytes)] + mqttsn_payload
    """
    msg_type = mqttsn_payload[1]
    authX = generate_auth_authX(client_ip, gw_ip, src_port, gw_port, msg_type)
    secsn_header = struct.pack('>HH', TYPE_SECSN, authX)
    return secsn_header + mqttsn_payload

def xor_data(data_str, mask_int):
    data_bytes = data_str.encode("utf-8")
    mask_bytes = mask_int.to_bytes(64, 'big')
    return bytes([b ^ mask_bytes[i % len(mask_bytes)] for i, b in enumerate(data_bytes)])

# MQTT-SN packet builders (length + type + payload)
def build_connect(client_id, duration=60):
    flags = 0x02
    protocol_id = 0x01
    payload = struct.pack('>BBH', flags, protocol_id, duration) + client_id.encode('utf-8')
    mqttsn_packet = struct.pack('>BB', len(payload) + 2, MQTTSN_CONNECT) + payload
    return mqttsn_packet

def build_register(topic_name, msg_id):
    topic_id = 0x0000
    payload = struct.pack('>HH', topic_id, msg_id) + topic_name.encode('utf-8')
    mqttsn_packet = struct.pack('>BB', len(payload) + 2, MQTTSN_REGISTER) + payload
    return mqttsn_packet

def build_publish(qos_level, topic_id, msg_id, data):
    flags = ((qos_level & 0x03) << 5) | (TOPICIDTYPE_NORMAL & 0x03)
    msg_id_to_send = msg_id if qos_level != QOS_M1 else 0x0000
    header = struct.pack('>BHH', flags, topic_id, msg_id_to_send)
    payload = data if isinstance(data, (bytes, bytearray)) else data.encode('utf-8')
    length = len(header) + len(payload) + 2
    mqttsn_packet = struct.pack('>BB', length, MQTTSN_PUBLISH) + header + payload
    return mqttsn_packet

def build_pubrel(msg_id):
    payload = struct.pack('>H', msg_id)
    mqttsn_packet = struct.pack('>BB', len(payload) + 2, MQTTSN_PUBREL) + payload
    return mqttsn_packet

def build_disconnect():
    mqttsn_packet = struct.pack('>BB', 2, MQTTSN_DISCONNECT)
    return mqttsn_packet

# --------------------------
# Network send/recv wrappers (SECSN-aware)
# --------------------------
def send_packet(sock, packet_bytes, server_addr):
    sock.sendto(packet_bytes, server_addr)

def recv_mqttsn(sock, timeout=RECV_TIMEOUT):
    sock.settimeout(timeout)
    try:
        data, _ = sock.recvfrom(4096)
    except socket.timeout:
        return None
    if len(data) < 4:
        return None
    # data: [SECSN(4)] + mqtt-sn
    mqttsn_payload = data[4:]
    if len(mqttsn_payload) < 2:
        return None
    return mqttsn_payload

# --------------------------
# Single client sequence with timing (P4SSN style but with fluxos)
# --------------------------
def run_single_client(client_idx, gw_ip, gw_port, client_ip, qos_level, topic_name_param, mode_label, timeout_settings):
    """
    Performs the flow for one publisher client using SECSN encapsulation,
    measuring per-flow times (t_fluxo_*). Returns a dict with those times.
    """
    result = {
        "cenario": "p4ssn",
        "qos": qos_level,
        "modo": mode_label,
        "cliente_id": client_idx,
        "t_fluxo_connect_ms": 0,
        "t_fluxo_register_ms": 0,
        "t_fluxo_publish_ms": 0,
        "t_fluxo_disconnect_ms": 0,
        "t_fluxo_total_ms": 0,
        "sucesso": 0
    }

    # create socket and bind to the provided client_ip ephemeral port
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((client_ip, 0))
    except Exception as e:
        print(f"[client {client_idx}] bind error: {e}")
        sock.close()
        return result
    src_port = sock.getsockname()[1]
    server_addr = (gw_ip, gw_port)

    # select topic according to qos (overrides passed topic_name_param)
    if qos_level == QOS_M1:
        topic_name = "tt"
    elif qos_level == QOS_0:
        topic_name = "topic/teste/qos0"
    elif qos_level == QOS_1:
        topic_name = "topic/teste/qos1"
    else:
        topic_name = "topic/teste/qos2"

    client_id = f"bench_client_{client_idx}_{random.randint(1000,9999)}"
    msg_id = 0x0001
    data_msg = ("payload_for_client_%d" % client_idx).ljust(64, "*")
    # mask payload per SECSN design
    data_masked = xor_data(data_msg, SECRET_MASK_DATA_SECSN)

    start_total = time.perf_counter()

    # If QoS -1: only send PUBLISH and finish (measure only publish)
    if qos_level == QOS_M1:
        pub_start = time.perf_counter()
        mqtt_publish = build_publish(qos_level, 1, msg_id, data_masked)
        pkt_publish = build_secsn_packet(mqtt_publish, client_ip, src_port, gw_ip, gw_port)
        send_packet(sock, pkt_publish, server_addr)
        # give a tiny time for NIC to send
        time.sleep(0.01)
        pub_end = time.perf_counter()
        result["t_fluxo_publish_ms"] = (pub_end - pub_start) * 1000
        result["t_fluxo_total_ms"] = result["t_fluxo_publish_ms"]
        result["sucesso"] = 1
        sock.close()
        return result

    # CONNECT (fluxo)
    conn_start = time.perf_counter()
    pkt_connect = build_secsn_packet(build_connect(client_id), client_ip, src_port, gw_ip, gw_port)
    send_packet(sock, pkt_connect, server_addr)
    connack_payload = recv_mqttsn(sock, timeout=timeout_settings.get("connect", CONNECT_TIMEOUT))
    conn_end = time.perf_counter()
    if connack_payload is None:
        # failed CONNECT flow; return with zeros
        sock.close()
        return result
    result["t_fluxo_connect_ms"] = (conn_end - conn_start) * 1000

    # REGISTER -> REGACK (fluxo)
    reg_start = time.perf_counter()
    pkt_register = build_secsn_packet(build_register(topic_name, msg_id), client_ip, src_port, gw_ip, gw_port)
    send_packet(sock, pkt_register, server_addr)
    regack_payload = recv_mqttsn(sock, timeout=timeout_settings.get("register", REGISTER_TIMEOUT))
    reg_end = time.perf_counter()
    if regack_payload is None:
        sock.close()
        return result
    # extract topic_id if present
    try:
        topic_id = struct.unpack('>H', regack_payload[2:4])[0]
    except Exception:
        topic_id = 0x0001
    result["t_fluxo_register_ms"] = (reg_end - reg_start) * 1000

    # PUBLISH (fluxo: measure from send to final response depending on QoS)
    pub_start = time.perf_counter()
    mqtt_publish = build_publish(qos_level, topic_id, msg_id, data_masked)
    pkt_publish = build_secsn_packet(mqtt_publish, client_ip, src_port, gw_ip, gw_port)
    send_packet(sock, pkt_publish, server_addr)

    if qos_level == QOS_0:
        # no publish ack expected — measure send time as fluxo_publish
        pub_end = time.perf_counter()
        result["t_fluxo_publish_ms"] = (pub_end - pub_start) * 1000

    elif qos_level == QOS_1:
        # wait for PUBACK (SECSN-wrapped)
        puback_payload = recv_mqttsn(sock, timeout=timeout_settings.get("publish", PUBLISH_TIMEOUT))
        puback_time = time.perf_counter()
        if puback_payload is None:
            # failure on publish flow
            result["t_fluxo_publish_ms"] = 0
            # proceed to attempt graceful disconnect
        else:
            result["t_fluxo_publish_ms"] = (puback_time - pub_start) * 1000

    elif qos_level == QOS_2:
        # wait for PUBREC then send PUBREL then wait PUBCOMP
        pubrec_payload = recv_mqttsn(sock, timeout=timeout_settings.get("publish", PUBLISH_TIMEOUT))
        if pubrec_payload is None:
            result["t_fluxo_publish_ms"] = 0
            # attempt graceful disconnect
            pkt_disconnect = build_secsn_packet(build_disconnect(), client_ip, src_port, gw_ip, gw_port)
            send_packet(sock, pkt_disconnect, server_addr)
            result["t_fluxo_total_ms"] = (time.perf_counter() - start_total) * 1000
            sock.close()
            return result
        # send PUBREL
        rel_start = time.perf_counter()
        pkt_pubrel = build_secsn_packet(build_pubrel(msg_id), client_ip, src_port, gw_ip, gw_port)
        send_packet(sock, pkt_pubrel, server_addr)
        pubcomp_payload = recv_mqttsn(sock, timeout=timeout_settings.get("pubrel", PUBREL_TIMEOUT))
        rel_end = time.perf_counter()
        if pubcomp_payload is None:
            result["t_fluxo_publish_ms"] = 0
        else:
            # measure from publish send to final pubcomp
            result["t_fluxo_publish_ms"] = (rel_end - pub_start) * 1000

    # DISCONNECT (fluxo)
    dis_start = time.perf_counter()
    pkt_disconnect = build_secsn_packet(build_disconnect(), client_ip, src_port, gw_ip, gw_port)
    send_packet(sock, pkt_disconnect, server_addr)
    # try to receive an echo or nothing; measure send time anyway
    try:
        _ = recv_mqttsn(sock, timeout=timeout_settings.get("disconnect", DISCONNECT_TIMEOUT))
        dis_end = time.perf_counter()
        result["t_fluxo_disconnect_ms"] = (dis_end - dis_start) * 1000
    except Exception:
        # even if no reply, we record the send duration (very small)
        result["t_fluxo_disconnect_ms"] = (time.perf_counter() - dis_start) * 1000

    # Total fluxo: sum of fluxos
    result["t_fluxo_total_ms"] = (
        result["t_fluxo_connect_ms"] +
        result["t_fluxo_register_ms"] +
        result["t_fluxo_publish_ms"] +
        result["t_fluxo_disconnect_ms"]
    )

    # sucesso: define como publish fluxo > 0 (for -1 we set earlier)
    result["sucesso"] = 1 if result["t_fluxo_publish_ms"] and result["t_fluxo_publish_ms"] > 0 else 0

    sock.close()
    return result

# --------------------------
# Runner utilities
# --------------------------
CSV_FIELDS = [
    "cenario","qos","modo","cliente_id",
    "t_fluxo_connect_ms","t_fluxo_register_ms","t_fluxo_publish_ms","t_fluxo_disconnect_ms",
    "t_fluxo_total_ms","sucesso"
]

def append_results_to_csv(filename, rows):
    first = not os.path.exists(filename)
    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if first:
            writer.writeheader()
        for r in rows:
            out = {k: (r.get(k) if r.get(k) is not None else "") for k in CSV_FIELDS}
            writer.writerow(out)

def run_benchmark_for_qos(gw_ip, gw_port, client_ip, qos_level, mode, repetitions=100, topic_name=None, timeout_settings=None):
    results = []
    mode_label = "paralelo" if mode == "parallel" else "serial"
    timeout_settings = timeout_settings or {}

    if mode == "parallel":
        with ThreadPoolExecutor(max_workers=min(200, repetitions)) as ex:
            futures = [ex.submit(run_single_client, i+1, gw_ip, gw_port, client_ip, qos_level, topic_name, mode_label, timeout_settings) for i in range(repetitions)]
            for fut in as_completed(futures):
                try:
                    r = fut.result()
                except Exception as e:
                    print("Exception in future:", e)
                    continue
                results.append(r)
    else:
        for i in range(repetitions):
            r = run_single_client(i+1, gw_ip, gw_port, client_ip, qos_level, topic_name, mode_label, timeout_settings)
            results.append(r)
    return results

# --------------------------
# Main CLI
# --------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gw", required=True, help="Gateway IP")
    parser.add_argument("--port-gw", type=int, required=True, help="Gateway port (SECSN-enabled)")
    parser.add_argument("--client-ip", default="10.0.0.2", help="Local client IP to bind (one IP assumed for all clients)")
    parser.add_argument("--mode", choices=["parallel","serial"], default="parallel", help="parallel or serial")
    parser.add_argument("--reps", type=int, default=100, help="number of publisher clients (default 100)")
    parser.add_argument("--qos", type=int, choices=[-1,0,1,2], help="run only this qos (optional)")
    parser.add_argument("--topic", default=None, help="(ignored) topic name used for REGISTER; topic chosen per QoS automatically")
    parser.add_argument("--out", default="results/p4ssn.csv", help="CSV output file")
    args = parser.parse_args()

    gw_ip = args.gw
    gw_port = args.port_gw
    client_ip = args.client_ip
    mode = args.mode
    repetitions = args.reps
    outfile = args.out

    os.makedirs(os.path.dirname(outfile), exist_ok=True)

    qos_list = [-1,0,1,2] if args.qos is None else [args.qos]

    print("=== Benchmark P4 + SECSN ===")
    print(f"GW: {gw_ip}:{gw_port}  client_ip(bind): {client_ip}  mode: {mode}  reps: {repetitions}")
    print("Running QoS levels:", qos_list)

    for qos in qos_list:
        # select topic name for display / register (function run_single_client will also select proper topic)
        if qos == -1:
            topic_name = "tt"
        elif qos == 0:
            topic_name = "topic/teste/qos0"
        elif qos == 1:
            topic_name = "topic/teste/qos1"
        else:
            topic_name = "topic/teste/qos2"

        print(f"\n--- Running QoS {qos} ({mode}) topic={topic_name} ---")
        qlevel = QOS_M1 if qos==-1 else (QOS_0 if qos==0 else (QOS_1 if qos==1 else QOS_2))
        res = run_benchmark_for_qos(gw_ip, gw_port, client_ip, qlevel, mode, repetitions=repetitions, topic_name=topic_name)
        append_results_to_csv(outfile, res)
        # summary
        times = [r["t_fluxo_total_ms"] for r in res if r["t_fluxo_total_ms"]]
        succ = sum(1 for r in res if r["sucesso"])
        print(f"QoS {qos} results: {len(times)} measurements, success={succ}/{len(res)}")
        if times:
            avg = sum(times)/len(times)
            print(f" avg total time (ms) = {avg:.2f}")

    print("\nFinished. Results appended to", outfile)

if __name__ == "__main__":
    main()
