#include <core.p4>
#include <v1model.p4>

// Define o cabeçalho Ethernet
header ethernet_t {
    mac_addr dstAddr;
    mac_addr srcAddr;
    bit<16>  etherType;
}

// Define o cabeçalho IPv4
header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4_addr  srcAddr;
    ip4_addr  dstAddr;
}

// Define o cabeçalho UDP
header udp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<16> length;
    bit<16> checksum;
}

// Define o cabeçalho MQTT-SN com suporte a QoS
header mqttsn_t {
    bit<8> length;
    bit<8> msg_type;
    bit<8> flags;       // Contém bits para QoS, DUP, RETAIN, etc.
    bit<16> topic_id;
    bit<16> msg_id;
}

// Struct para armazenar todos os headers
struct headers_t {
    ethernet_t ethernet;
    ipv4_t     ipv4;
    udp_t      udp;
    mqttsn_t   mqttsn;
}

struct metadata_t {}

parser ParserImpl(packet_in pkt, out headers_t hdr, inout metadata_t meta, inout standard_metadata_t standard_metadata) {
    state start {
        pkt.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            0x0800: parse_ipv4;
            default: reject;
        }
    }

    state parse_ipv4 {
        pkt.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol) {
            17: parse_udp; // UDP protocol
            default: reject;
        }
    }

    state parse_udp {
        pkt.extract(hdr.udp);
        transition parse_mqttsn;
    }

    state parse_mqttsn {
        pkt.extract(hdr.mqttsn);
        transition accept;
    }
}

control VerifyChecksumImpl(inout headers_t hdr, inout metadata_t meta) {
    apply { }
}

control IngressImpl(inout headers_t hdr, inout metadata_t meta, inout standard_metadata_t standard_metadata) {
    action set_egress_port(bit<9> port) {
        standard_metadata.egress_spec = port;
    }

    table ipv4_lpm_table {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            set_egress_port;
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
    }

    apply {
        if (hdr.mqttsn.isValid()) {
            // Redireciona mensagens CONNECT (msg_type = 0x04) para porta 2
            if (hdr.mqttsn.msg_type == 0x04) {
                set_egress_port(2);
            }
            // Redireciona mensagens PUBLISH com QoS 0 para porta 3
            else if (hdr.mqttsn.msg_type == 0x0C && (hdr.mqttsn.flags & 0x60) == 0x00) {
                standard_metadata.egress_spec = 3;
            }
            // Redireciona mensagens PUBLISH com QoS 1 para porta 4
            else if (hdr.mqttsn.msg_type == 0x0C && (hdr.mqttsn.flags & 0x60) == 0x20) {
                standard_metadata.egress_spec = 4;
            }
            else {
                standard_metadata.egress_spec = 1;
            }
        }
    }
}

control EgressImpl(inout headers_t hdr, inout metadata_t meta, inout standard_metadata_t standard_metadata) {
    apply { }
}

control ComputeChecksumImpl(inout headers_t hdr, inout metadata_t meta) {
    apply { }
}

control DeparserImpl(packet_out pkt, in headers_t hdr) {
    apply {
        pkt.emit(hdr.ethernet);
        pkt.emit(hdr.ipv4);
        pkt.emit(hdr.udp);
        pkt.emit(hdr.mqttsn);
    }
}

V1Switch(ParserImpl(), VerifyChecksumImpl(), IngressImpl(), EgressImpl(), ComputeChecksumImpl(), DeparserImpl())
