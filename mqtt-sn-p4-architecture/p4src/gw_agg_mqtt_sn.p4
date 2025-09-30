/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

/*************************************************************************
*********************** C O N S T S **************************************
*************************************************************************/

// 0x: correponde a hexadecimal com bit<8>
// 0b: correponde a binário com bit<2>

/*Message MQTT-SN*/ 
const bit<8> MQTTSN_ADVERTISE = 0x00;
const bit<8> MQTTSN_SEARCHGW = 0x01;
const bit<8> MQTTSN_GWINFO = 0x02;
//const bit<8> reserved = 0x03;
const bit<8> MQTTSN_CONNECT = 0x04;
const bit<8> MQTTSN_CONNACK = 0x05;
const bit<8> MQTTSN_WILLTOPICREQ = 0x06;
const bit<8> MQTTSN_WILLTOPIC = 0x07;
const bit<8> MQTTSN_WILLMSGREQ = 0x08;
const bit<8> MQTTSN_WILLMSG = 0x09;
const bit<8> MQTTSN_REGISTER = 0x0A;
const bit<8> MQTTSN_REGACK = 0x0B;
const bit<8> MQTTSN_PUBLISH = 0x0C;
const bit<8> MQTTSN_PUBACK = 0x0D;
const bit<8> MQTTSN_PUBCOMP = 0x0E;
const bit<8> MQTTSN_PUBREC = 0x0F;
const bit<8> MQTTSN_PUBREL = 0x10;
//const bit<8> reserved = 0x11;
const bit<8> MQTTSN_SUBSCRIBE = 0x12;
const bit<8> MQTTSN_SUBACK = 0x13;
const bit<8> MQTTSN_UNSUBSCRIBE = 0x14;
const bit<8> MQTTSN_UNSUBACK = 0x15;
const bit<8> MQTTSN_PINGREQ = 0x16;
const bit<8> MQTTSN_PINGRESP = 0x17;
const bit<8> MQTTSN_DISCONNECT = 0x18;
//const bit<8> reserved = 0x19;
const bit<8> MQTTSN_WILLTOPICUPD = 0x1A;
const bit<8> MQTTSN_WILLTOPICRESP = 0x1B;
const bit<8> MQTTSN_WILLMSGUPD = 0x1C;
const bit<8> MQTTSN_WILLMSGRESP = 0x1D;
//const bit<8> reserved = 0x1E-0xFD;
//const bit<8> Encapsulated message = 0xFE;
//const bit<8> reserved = 0xFF;

/*Message MQTT-SN return codes*/
const bit<8> MQTTSN_RETURNCODE_ACCEPTED = 0x00;
const bit<8> MQTTSN_RETURNCODE_REJECTED_CONGESTION = 0x01;
const bit<8> MQTTSN_RETURNCODE_REJECTED_INVALID_TOPIC_ID = 0x02;
const bit<8> MQTTSN_RETURNCODE_REJECTED_NOT_SUPPORTED = 0x03;
//const bit<8> MQTTSN_RETURNCODE_???? = 0x04-0xFF; // Reserved

/*Topic ID Types*/
const bit<2> TOPICIDTYPE_TOPICNAME = 0b00;
const bit<2> TOPICIDTYPE_PREDEFINEDTOPIC = 0b01;
const bit<2> TOPICIDTYPE_SHORTTOPICNAME = 0b10;
const bit<2> TOPICIDTYPE_RESERVED = 0b11;

/*Segment UDP*/
const bit<8> TYPE_UDP = 0x11;
const bit<16> UDP_PORT = 1884;

/*Packet IP*/
const bit<16> TYPE_IPV4 = 0x800;

/*************************************************************************
*********************** T Y P E D E F S  *********************************
*************************************************************************/

/*Packet IP*/
typedef bit<32> ipv4Addr_t;

/*Frame Ethernet*/
typedef bit<48> macAddr_t;

/*Generic Port*/
typedef bit<9>  egressSpec_t; // representa a porta de saída do switich com 9 bits

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

//////////////////// MQTT-SN Headers ////////////////////

/*Message MQTT-SN fixed header*/
header MQTTSN_fixed_h {
    bit<8> length;
    bit<8> msgType;
}


/*Message MQTT-SN variable header CONNECT*/
header MQTTSN_connect_h {
    bit<8>   protocolId;
    bit<16>  duration;
    // bit<184> clientId; // Removido clientId fixo. Será extraído dinamicamente.
}

/*Message MQTT-SN variable header CONNACK*/
header MQTTSN_connack_h {
    bit<8> returnCode;
}

/*Default header to fields variables*/
// Max payload size for Ethernet/IPv4/UDP (1500 - 20 - 8 = 1472 bytes = 11776 bits)
//    Usando um valor um pouco maior para flexibilidade, mas com cuidado.
//    O tamanho real será determinado pelo length do MQTTSN_fixed_h
header MQTTSN_variable_field_h {
    varbit<1504> data;
}

//////////////// MQTT-SN Headers Flags //////////////////

/*Message MQTT-SN flags CONNECT*/
// bit<6> reserved; (Estratégia para completar os 8 bits das flags
//    e não dar erro na compilação): BMv2 target only supports 
//    headers with fields totaling a multiple of 8 bits.
header MQTTSN_flags_connect_h {
    bit<1> will;
    bit<1> cleanSession;
    bit<6> reserved; 
}

///////////////////// UDP Header ////////////////////

/*Segment UDP*/
header UDP_h {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<16> length;
    bit<16> checksum;
}

/////////////////// IPV4 Header ///////////////////////

/*Packet IP*/
header IPv4_h {
    bit<4>   version;
    bit<4>   ihl;
    bit<8>   diffServ;
    bit<16>  totalLen;
    bit<16>  identification;
    bit<3>   flags;
    bit<13>  fragOffset;
    bit<8>   ttl;
    bit<8>   protocol;
    bit<16>  hdrChecksum;
    ipv4Addr_t srcAddr;
    ipv4Addr_t dstAddr;
}

/////////////////// ETHERNET Header //////////////////////

/*Frame Ethernet*/
header Ethernet_h {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16> ethertype;
}

//////////////////// HEADERS /////////////////////////

struct headers {
    Ethernet_h ethernet;
    IPv4_h ipv4;
    UDP_h udp;
    MQTTSN_fixed_h mqttsn_fixed;
    MQTTSN_flags_connect_h mqttsn_flags_connect;
    MQTTSN_connect_h mqttsn_connect;
    MQTTSN_connack_h mqttsn_connack;
    MQTTSN_variable_field_h mqttsn_variable_field; // Para campos variáveis
}

// Metadados
struct metadata { }

// Erros customizados para validação dos headers
error {
    // Ethernet
    UnsupportedEtherType,

    // IPv4
    IPv4IncorrectVersion,
    IPv4HeaderLengthError,
    IPv4ChecksumError,
    IPv4UnsupportedProtocol,
    IPv4OptionsNotSupported,

    // MQTT-SN
    MQTT_SN_InvalidLength,
    MQTT_SN_UnsupportedMessageType,
    MQTT_SN_InvalidFlags
}

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {
    
    state start {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.ethertype) {
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        verify(hdr.ipv4.version == 4, error.IPv4IncorrectVersion);
        transition select(hdr.ipv4.protocol) {
            TYPE_UDP: parse_udp;
            default: accept;
        }
    }

    state parse_udp {
        packet.extract(hdr.udp);
        transition select(hdr.udp.dstPort) {
            UDP_PORT: parse_mqttsn_fixed;
            default: accept;
        }
    }

    state parse_mqttsn_fixed {
        packet.extract(hdr.mqttsn_fixed);
        verify(hdr.mqttsn_fixed.length >= 2, error.MQTT_SN_InvalidLength);
        transition select(hdr.mqttsn_fixed.msgType) {
            MQTTSN_CONNECT: parse_mqttsn_connect;
            // MQTTSN_CONNACK: parse_mqttsn_connack; // Não preciso parsear pois nunca vou receber essa mensagem
            default: accept;
        }
    }

    state parse_mqttsn_connect {
        packet.extract(hdr.mqttsn_flags_connect);
        packet.extract(hdr.mqttsn_connect);
        // O clientId é um campo variável. Extrair o restante do pacote como um campo variável.
        // O comprimento do clientId é o comprimento total da mensagem - (fixed_h + flags_connect_h + connect_h)
        // MQTTSN_fixed_h (2 bytes) + MQTTSN_flags_connect_h (1 byte) + MQTTSN_connect_h (3 bytes) = 6 bytes
        // Comprimento do clientId = hdr.mqttsn_fixed.length - 6
        // O comprimento mínimo para CONNECT é 6 bytes (2 fixos + 1 flags + 3 connect) + 1 byte de clientId = 7 bytes
        verify(hdr.mqttsn_fixed.length >= 7, error.MQTT_SN_InvalidLength);
        // calcular tamanho em bits em uma variável bit<32> antes do extract
        bit<32> mqttsn_var_bits;
        mqttsn_var_bits = ((bit<32>)hdr.mqttsn_fixed.length - (bit<32>)6) * (bit<32>)8;
        packet.extract(hdr.mqttsn_variable_field, mqttsn_var_bits);
        transition accept;
    }

    /*state parse_mqttsn_connack {
        packet.extract(hdr.mqttsn_connack);
        verify(hdr.mqttsn_fixed.length == 3, error.MQTT_SN_InvalidLength);
        transition accept;
    }*/

}

/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, 
                         inout metadata meta) {
    apply {  }
}

/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    //////////////////////////////////////////////////////
    // ACTION: DESCARTE AUTOMÁTICO DE PACOTES
    //////////////////////////////////////////////////////

    action drop() {
        mark_to_drop(standard_metadata);
    }

    //////////////////////////////////////////////////////
    // ACTION: ENCAMINHAMENTO ESTÁTICO
    //////////////////////////////////////////////////////

    action forwarding(macAddr_t dstAddr, egressSpec_t port) {
        // o novo mac de origem recebe o mac de destino anterior
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        // o novo mac de destino recebe o mac do próximo dispositivo (tabela de encaminhamento)
        hdr.ethernet.dstAddr = dstAddr;
        // define a porta de do switch para qual o pacote deve ser encaminhado (tabela de encaminhamento)
        standard_metadata.egress_spec = port;
        // decrementar o ttl em 1
        hdr.ipv4.ttl = hdr.ipv4.ttl -1;
    }

    //////////////////////////////////////////////////////
    // TABELA DE ENCAMINHAMENTO ESTÁTICO
    //////////////////////////////////////////////////////

    table static_forwarding {
        key = {
            hdr.ipv4.dstAddr: exact;
        }
        actions = {
            forwarding;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
    }

    //////////////////////////////////////////////////////
    // ACTIONS: CONNECT <-> CONNACK
    //////////////////////////////////////////////////////

    action send_connack_response_accept_connection() {
        // Ethernet
        macAddr_t srcMac = hdr.ethernet.srcAddr;
        const macAddr_t GW_MAC = 0x000000000002; // Tem como pegar esse mac na tabela de encaminhamento?
        hdr.ethernet.srcAddr = GW_MAC;
        hdr.ethernet.dstAddr = srcMac;

        // IPv4
        ipv4Addr_t srcIP = hdr.ipv4.srcAddr;
        hdr.ipv4.srcAddr = hdr.ipv4.dstAddr;
        hdr.ipv4.dstAddr = srcIP;

        hdr.ipv4.ttl = 64;
        hdr.ipv4.version = 4;
        hdr.ipv4.ihl = 5;   // sempre 20 bytes
        hdr.ipv4.identification = 0;
        hdr.ipv4.fragOffset = 0;
        hdr.ipv4.flags = 0;

        // UDP
        bit<16> srcPort = hdr.udp.srcPort;
        hdr.udp.srcPort = hdr.udp.dstPort;
        hdr.udp.dstPort = srcPort;

        // CONNACK payload
        hdr.mqttsn_fixed.setValid();
        hdr.mqttsn_fixed.length  = 3;   // 2 bytes fixed + 1 byte returnCode
        hdr.mqttsn_fixed.msgType = MQTTSN_CONNACK;

        hdr.mqttsn_connack.setValid();
        hdr.mqttsn_connack.returnCode = MQTTSN_RETURNCODE_ACCEPTED;

        // Invalidar CONNECT recebido
        hdr.mqttsn_flags_connect.setInvalid();
        hdr.mqttsn_connect.setInvalid();
        hdr.mqttsn_variable_field.setInvalid();

        // Ajustar comprimentos
        hdr.udp.length    = (bit<16>)(8 + (bit<16>)hdr.mqttsn_fixed.length);
        hdr.ipv4.totalLen = (bit<16>)(((bit<16>)hdr.ipv4.ihl) * 4 + hdr.udp.length);

        // Zerar checksums (recalculados depois)
        hdr.ipv4.hdrChecksum = 0;
        hdr.udp.checksum     = 0;

        // Porta de saída
        standard_metadata.egress_spec = standard_metadata.ingress_port;
    }

    action send_connack_response_reject_not_supported() {
        // Ethernet
        macAddr_t srcMac = hdr.ethernet.srcAddr;
        const macAddr_t GW_MAC = 0x000000000002; // Tem como pegar esse mac na tabela de encaminhamento?
        hdr.ethernet.srcAddr = GW_MAC;
        hdr.ethernet.dstAddr = srcMac;

        // IPv4
        ipv4Addr_t srcIP = hdr.ipv4.srcAddr;
        hdr.ipv4.srcAddr = hdr.ipv4.dstAddr;
        hdr.ipv4.dstAddr = srcIP;

        hdr.ipv4.ttl = 64;
        hdr.ipv4.version = 4;
        hdr.ipv4.ihl = 5;   // sempre 20 bytes
        hdr.ipv4.identification = 0;
        hdr.ipv4.fragOffset = 0;
        hdr.ipv4.flags = 0;

        // UDP
        bit<16> srcPort = hdr.udp.srcPort;
        hdr.udp.srcPort = hdr.udp.dstPort;
        hdr.udp.dstPort = srcPort;

        // CONNACK payload
        hdr.mqttsn_fixed.setValid();
        hdr.mqttsn_fixed.length  = 3;   // 2 bytes fixed + 1 byte returnCode
        hdr.mqttsn_fixed.msgType = MQTTSN_CONNACK;

        hdr.mqttsn_connack.setValid();
        hdr.mqttsn_connack.returnCode = MQTTSN_RETURNCODE_REJECTED_NOT_SUPPORTED;

        // Invalidar CONNECT recebido
        hdr.mqttsn_flags_connect.setInvalid();
        hdr.mqttsn_connect.setInvalid();
        hdr.mqttsn_variable_field.setInvalid();

        // Ajustar comprimentos
        hdr.udp.length    = (bit<16>)(8 + (bit<16>)hdr.mqttsn_fixed.length);
        hdr.ipv4.totalLen = (bit<16>)(((bit<16>)hdr.ipv4.ihl) * 4 + hdr.udp.length);

        // Zerar checksums (recalculados depois)
        hdr.ipv4.hdrChecksum = 0;
        hdr.udp.checksum     = 0;

        // Porta de saída
        standard_metadata.egress_spec = standard_metadata.ingress_port;
    }

    //////////////////////////////////////////////////////
    // APPLY
    //////////////////////////////////////////////////////

    apply {
        if (hdr.mqttsn_fixed.isValid()) {
            if (hdr.mqttsn_fixed.msgType == MQTTSN_CONNECT &&
                hdr.mqttsn_connect.isValid() &&
                hdr.mqttsn_flags_connect.isValid() &&
                hdr.mqttsn_connect.protocolId == 0x01) {
                if (hdr.udp.dstPort == UDP_PORT &&     // porta 1884
                    hdr.ipv4.dstAddr == 0x0A000002) {  // gateway 10.0.0.2
                        send_connack_response_accept_connection();
                } else {
                    send_connack_response_reject_not_supported();
                }
            } else {
                send_connack_response_reject_not_supported();
            }
        } else {
            drop();
        }
    }
}


/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    apply {  }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers hdr, 
                          inout metadata meta) {
    apply {
        update_checksum(
            hdr.ipv4.isValid(),
                { hdr.ipv4.version,
                  hdr.ipv4.ihl,
                  hdr.ipv4.diffServ,
                  hdr.ipv4.totalLen,
                  hdr.ipv4.identification,
                  hdr.ipv4.flags,
                  hdr.ipv4.fragOffset,
                  hdr.ipv4.ttl,
                  hdr.ipv4.protocol,
                  hdr.ipv4.srcAddr,
                  hdr.ipv4.dstAddr },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16);
    }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, 
                   in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.udp);
        packet.emit(hdr.mqttsn_fixed);
        //packet.emit(hdr.mqttsn_variable_field);
        //packet.emit(hdr.mqttsn_flags_connect);
        //packet.emit(hdr.mqttsn_connect);
        packet.emit(hdr.mqttsn_connack);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

//switch architecture
V1Switch(
    MyParser(),
    MyVerifyChecksum(),
    MyIngress(),
    MyEgress(),
    MyComputeChecksum(),
    MyDeparser()
) main;

// cd ~/dissertacao_ppgti
// docker run -dit --name=p4c --rm ramonfontes/bmv2:latest
// docker cp mqtt-sn-p4-architecture/p4src p4c:/tmp/
// docker exec -it p4c bash
// cd /tmp/p4src
// p4c --target bmv2 --arch v1model gw_agg_mqtt_sn.p4
// exit
// docker cp p4c:/tmp/p4src/gw_agg_mqtt_sn.json mqtt-sn-p4-architecture/
// sudo python3 mqtt-sn-p4-architecture/mqtt_sn_p4_architecture.py

// docker stop p4c
// docker stop mn.s1 mn.ss1 mn.pb1 mn.gw mn.bk
// docker rm mn.s1 mn.ss1 mn.pb1 mn.gw mn.bk