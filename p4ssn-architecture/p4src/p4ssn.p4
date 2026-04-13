/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

// https://github.com/nsg-ethz/p4-learning/wiki/BMv2-Simple-Switch
#define PKT_INSTANCE_TYPE_INGRESS_RECIRC 4

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

/*Flags QoS Level*/
const bit<2> FLAGS_QOS_LEVEL_0 = 0b00;
const bit<2> FLAGS_QOS_LEVEL_1 = 0b01;
const bit<2> FLAGS_QOS_LEVEL_2 = 0b10;
const bit<2> FLAGS_QOS_LEVEL_MINUS1 = 0b11;

/*Segment UDP*/
const bit<8> TYPE_UDP = 0x11;
const bit<16> UDP_PORT_SVC_GW = 1884;

/*Segment TCP*/
const bit<8> TYPE_TCP = 0x06;
const bit<16> TCP_PORT_SVC_BK = 1883;

/*Packet IP*/
const bit<16> TYPE_IPV4 = 0x0800;

/*ICMP*/
const bit<8> TYPE_ICMP = 0x01;

/*Secrets Publish*/
const bit<16> SECRET_TOPIC_ID = 0xB7A3;

/*************************************************************************
*********************** T Y P E D E F S  *********************************
*************************************************************************/

/*Packet IP*/
typedef bit<32> ipv4Addr_t;

/*Frame Ethernet*/
typedef bit<48> macAddr_t;

/*Generic Port*/
typedef bit<9> egressSpec_t; // representa a porta de saída do switch com 9 bits

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

/////////////////// ETHERNET Header //////////////////////

/*Frame Ethernet*/
header Ethernet_h {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16> etherType;
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

///////////////////// UDP Header ////////////////////

/*Segment UDP*/
header UDP_h {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<16> length;
    bit<16> checksum;
}

///////////////////// TCP Header ////////////////////

/* Segment TCP */
header TCP_h {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<32> seqNo;
    bit<32> ackNo;
    bit<4>  dataOffset; // Indica o tamanho do header (multiplicado por 4 bytes)
    bit<3>  res;        // Bits reservados
    bit<3>  ecn;        // Explicit Congestion Notification
    bit<6>  ctrl;       // Flags de controle (URG, ACK, PSH, RST, SYN, FIN)
    bit<16> window;
    bit<16> checksum;
    bit<16> urgentPtr;
}

//////////////////// MQTT Header Fixed ////////////////////

/* Message MQTT fixed header (Simplificado para mensagens curtas) */
header MQTT_fixed_h {
    bit<4> msgType;   // Bits 7-4: Tipo da mensagem (ex: 0x3 para PUBLISH)
    bit<1> dup;       // Bit 3: Duplicado
    bit<2> qos;       // Bits 2-1: QoS level
    bit<1> retain;    // Bit 0: Retain
    bit<8> remainingLength; // Tamanho restante (simplificado para 1 byte)
}

//////////////////// MQTT-SN Headers ////////////////////

/*Message MQTT-SN fixed header*/
header MQTTSN_fixed_h {
    bit<8> length;
    bit<8> msgType;
}

/*Message MQTT-SN variable header ADVERTISE*/
header MQTTSN_advertise_h {
    bit<8>  gwId;
    bit<16> duration;
}

/*Message MQTT-SN variable header SEARCHGW*/
header MQTTSN_searchgw_h {
    bit<8> radius;
}

/*Message MQTT-SN variable header GWINFO*/
header MQTTSN_gwinfo_h {
    bit<8> gwId;
    //bit<32> gwAdd; // Será extraído dinamicamente.
}

/*Message MQTT-SN variable header CONNECT*/
header MQTTSN_connect_h {
    bit<8>   protocolId;
    bit<16>  duration;
    // bit<184> clientId; // Será extraído dinamicamente.
}

/*Message MQTT-SN variable header CONNACK*/
header MQTTSN_connack_h {
    bit<8> returnCode;
}

/*Message MQTT-SN variable header REGISTER*/
header MQTTSN_register_h {
    bit<16> topicId;
    bit<16> msgId;
    // bit<n> topicName; // Será extraído dinamicamente.
}

/*Message MQTT-SN variable header REGACK*/
header MQTTSN_regack_h {
    bit<16> topicId;
    bit<16> msgId;
    bit<8>  returnCode;
}

/*Message MQTT-SN variable header PUBLISH*/
header MQTTSN_publish_h {
    bit<16> topicId;
    bit<16> msgId;
    // bit<n> data; // Será extraído dinamicamente.
}

/*Message MQTT-SN variable header PUBACK*/
header MQTTSN_puback_h {
    bit<16> topicId;
    bit<16> msgId;
    bit<8>  returnCode;
}

/*Message MQTT-SN variable header PUBREC*/
header MQTTSN_pubrec_h {
    bit<16> msgId;
}

/*Message MQTT-SN variable header PUBREL*/
header MQTTSN_pubrel_h {
    bit<16> msgId;
}

/*Message MQTT-SN variable header PUBCOMP*/
header MQTTSN_pubcomp_h {
    bit<16> msgId;
}

/*Message MQTT-SN variable header DISCONNECT*/
// Veja a seção 6.14 Support of sleeping clients
header MQTTSN_disconnect_h {
    //bit<16> duration; // (opcional) ficará para implementações futuras.
}

/*Message MQTT-SN variable header PINGREQ*/
// Veja a seção 6.14 Support of sleeping clients
header MQTTSN_pingreq_h {
    // bit<184> clientId; // (opcional) ficará para implementações futuras.
}

/*Message MQTT-SN variable header PINGRESP*/
header MQTTSN_pingresp_h {  
    // Não há outros campos além do header fixo
}

/*Message MQTT-SN variable header SUBSCRIBE*/
header MQTTSN_subscribe_h {
    bit<16> msgId;
    bit<16> topicId;
    // bit<n> topicName; // Será extraído dinamicamente.
}

/*Message MQTT-SN variable header SUBACK*/
header MQTTSN_suback_h {
    bit<16> topicId;
    bit<16> msgId;
    bit<8>  returnCode;
}

/*Message MQTT-SN variable header UNSUBSCRIBE*/
header MQTTSN_unsubscribe_h {
    bit<16> msgId;
    bit<16> topicId; // or TopicName
    // bit<n> topicName; // Será extraído dinamicamente.
}

/*Message MQTT-SN variable header UNSUBACK*/
header MQTTSN_unsuback_h {
    bit<16> msgId;
}

/*Message MQTT-SN variable header WILLTOPICREQ*/
header MQTTSN_willtopicreq_h {
    // Não há outros campos além do header fixo
}

/*Message MQTT-SN variable header WILLTOPIC*/
header MQTTSN_willtopic_h {
   // bit<n> willTopic; // Será extraído dinamicamente.
}

/*Message MQTT-SN variable header WILLMSGREQ*/
header MQTTSN_willmsgreq_h {
    // Não há outros campos além do header fixo
}

/*Message MQTT-SN variable header WILLMSG*/
header MQTTSN_willmsg_h {
    // bit<n> willMsg; // Será extraído dinamicamente.
}

/*Message MQTT-SN variable header WILLTOPICUPD*/
header MQTTSN_willtopicupd_h {
    // bit<n> willTopic; // Será extraído dinamicamente.
}

/*Message MQTT-SN variable header WILLMSGUPD*/
header MQTTSN_willmsgupd_h {
    // bit<n> willMsg; // Será extraído dinamicamente.
}

/*Message MQTT-SN variable header WILLTOPICRESP*/
header MQTTSN_willtopicresp_h {
    bit<8> returnCode;
}

/*Message MQTT-SN variable header WILLMSGRESP*/
header MQTTSN_willmsgresp_h {
    bit<8> returnCode;
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

/*Message MQTT-SN flags WILLTOPIC*/
header MQTTSN_flags_willtopic_h {
    bit<2> qos;
    bit<1> retain;
    bit<5> reserved;
}

/*Message MQTT-SN flags PUBLISH*/
header MQTTSN_flags_publish_h {
    bit<1> dup;
    bit<2> qos;
    bit<1> retain;
    bit<2> reserved;
    bit<2> topicIdType;
}

/*Message MQTT-SN flags SUBSCRIBE*/
header MQTTSN_flags_subscribe_h {
    bit<1> dup;
    bit<2> qos;
    bit<2> topicIdType;
    bit<3> reserved;
}

/*Message MQTT-SN flags UNSUBSCRIBE*/
header MQTTSN_flags_unsubscribe_h {
    bit<1> dup;
    bit<2> qos;
    bit<2> topicIdType;
    bit<3> reserved;
}

/*Message MQTT-SN flags SUBACK*/
header MQTTSN_flags_suback_h {
    bit<2> qos;
    bit<6> reserved;
}

/*Message MQTT-SN flags WILLTOPICUPD*/
header MQTTSN_flags_willtopicupd_h {
    bit<2> qos;
    bit<1> retain;
    bit<5> reserved;
}

/*Default header to fields variables*/
// Max payload size for Ethernet/IPv4/UDP/MQTT-SN(parte fixa)/MQTT-SN(parte variável da maior mensagem que tem tamanho fixo -> SUBACK)
// 255(Tamanho total da mensagem mqt-sn / 5.2.1 Length MQTT-SN_spec_v1.2) - 20 - 8 - 2 - 8 = 217 bytes = 1736 bits
header MQTTSN_variable_field_h {
    varbit<1736> data;
}

// 102(P4SSN) - 20 - 8 - 2 - 8 = 64 bytes = 512 bits
header MQTTSN_fixed_data_publish_h {
    bit<512> data;
}

//////////////////// HEADERS /////////////////////////

struct headers {
    Ethernet_h ethernet;
    IPv4_h ipv4;
    TCP_h tcp;
    MQTT_fixed_h mqtt_fixed;
    UDP_h udp;
    MQTTSN_fixed_h mqttsn_fixed;
    MQTTSN_advertise_h mqttsn_advertise;
    MQTTSN_searchgw_h mqttsn_searchgw;
    MQTTSN_gwinfo_h mqttsn_gwinfo;
    MQTTSN_flags_connect_h mqttsn_flags_connect;
    MQTTSN_connect_h mqttsn_connect;
    MQTTSN_connack_h mqttsn_connack;
    MQTTSN_willtopicreq_h mqttsn_willtopicreq;
    MQTTSN_flags_willtopic_h mqttsn_flags_willtopic;
    MQTTSN_willtopic_h mqttsn_willtopic;
    MQTTSN_willmsgreq_h mqttsn_willmsgreq;
    MQTTSN_willmsg_h mqttsn_willmsg;
    MQTTSN_register_h mqttsn_register;
    MQTTSN_regack_h mqttsn_regack;
    MQTTSN_flags_publish_h mqttsn_flags_publish;
    MQTTSN_publish_h mqttsn_publish;
    MQTTSN_puback_h mqttsn_puback;
    MQTTSN_pubrec_h mqttsn_pubrec;
    MQTTSN_pubrel_h mqttsn_pubrel;
    MQTTSN_pubcomp_h mqttsn_pubcomp;
    MQTTSN_flags_subscribe_h mqttsn_flags_subscribe;
    MQTTSN_subscribe_h mqttsn_subscribe;
    MQTTSN_flags_suback_h mqttsn_flags_suback;
    MQTTSN_suback_h mqttsn_suback;
    MQTTSN_flags_unsubscribe_h mqttsn_flags_unsubscribe;
    MQTTSN_unsubscribe_h mqttsn_unsubscribe;
    MQTTSN_unsuback_h mqttsn_unsuback;
    MQTTSN_pingreq_h mqttsn_pingreq;
    MQTTSN_pingresp_h mqttsn_pingresp;
    MQTTSN_disconnect_h mqttsn_disconnect;
    MQTTSN_flags_willtopicupd_h mqttsn_flags_willtopicupd;
    MQTTSN_willtopicupd_h mqttsn_willtopicupd;
    MQTTSN_willmsgupd_h mqttsn_willmsgupd;
    MQTTSN_willtopicresp_h mqttsn_willtopicresp;
    MQTTSN_willmsgresp_h mqttsn_willmsgresp;
    MQTTSN_variable_field_h mqttsn_variable_field;
    MQTTSN_fixed_data_publish_h mqttsn_fixed_data_publish;
}

// Metadados
struct metadata {
    //
}

// Erros customizados para validação dos headers
error {
    // Ethernet
    UnsupportedEtherType,

    // IPv4
    IPv4IncorrectVersion,

    // MQTT-SN
    MQTT_SN_InvalidLength
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
        verify(hdr.ethernet.etherType == TYPE_IPV4, error.UnsupportedEtherType);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        verify(hdr.ipv4.version == 4, error.IPv4IncorrectVersion);
        transition select(hdr.ipv4.protocol) {
            TYPE_UDP: parse_udp;
            TYPE_TCP: parse_tcp;
            TYPE_ICMP: accept;    // Libera o tráfego ICMP para o Ingress
            default: accept;
        }
    }

    state parse_tcp {
        packet.extract(hdr.tcp);
        transition select(hdr.tcp.srcPort, hdr.tcp.dstPort) {
            (TCP_PORT_SVC_BK, _): parse_mqtt_fixed;   // Para mensagens com srcPort = 1883
            (_, TCP_PORT_SVC_BK): parse_mqtt_fixed;   // Para mensagens com dstPort = 1883
            default: accept;
        }
    }

    state parse_mqtt_fixed {
        // packet.extract(hdr.mqtt_fixed);
        transition accept;
    }

    state parse_udp {
        packet.extract(hdr.udp);
        transition select(hdr.udp.srcPort, hdr.udp.dstPort) {
            (UDP_PORT_SVC_GW, _): parse_mqttsn_fixed;   // Para mensagens com srcPort = 1884
            (_, UDP_PORT_SVC_GW): parse_mqttsn_fixed;   // Para mensagens com dstPort = 1884
            default: accept;
        }
    }

    state parse_mqttsn_fixed {
        packet.extract(hdr.mqttsn_fixed);
        verify(hdr.mqttsn_fixed.length >= 2, error.MQTT_SN_InvalidLength);
        transition select(hdr.mqttsn_fixed.msgType) {
            MQTTSN_ADVERTISE:     parse_mqttsn_advertise;
            MQTTSN_SEARCHGW:      parse_mqttsn_searchgw;
            MQTTSN_GWINFO:        parse_mqttsn_gwinfo;
            MQTTSN_CONNECT:       parse_mqttsn_connect;
            MQTTSN_CONNACK:       parse_mqttsn_connack;
            MQTTSN_REGISTER:      parse_mqttsn_register;
            MQTTSN_REGACK:        parse_mqttsn_regack;
            MQTTSN_PUBLISH:       parse_mqttsn_publish;
            MQTTSN_PUBACK:        parse_mqttsn_puback;
            MQTTSN_PUBREC:        parse_mqttsn_pubrec;
            MQTTSN_PUBREL:        parse_mqttsn_pubrel;
            MQTTSN_PUBCOMP:       parse_mqttsn_pubcomp;
            MQTTSN_SUBSCRIBE:     parse_mqttsn_subscribe;
            MQTTSN_SUBACK:        parse_mqttsn_suback;
            MQTTSN_UNSUBSCRIBE:   parse_mqttsn_unsubscribe;
            MQTTSN_UNSUBACK:      parse_mqttsn_unsuback;
            MQTTSN_PINGREQ:       parse_mqttsn_pingreq;
            MQTTSN_PINGRESP:      parse_mqttsn_pingresp;
            MQTTSN_DISCONNECT:    parse_mqttsn_disconnect;
            MQTTSN_WILLTOPICREQ:  parse_mqttsn_willtopicreq;
            MQTTSN_WILLTOPIC:     parse_mqttsn_willtopic;
            MQTTSN_WILLMSGREQ:    parse_mqttsn_willmsgreq;
            MQTTSN_WILLMSG:       parse_mqttsn_willmsg;
            MQTTSN_WILLTOPICUPD:  parse_mqttsn_willtopicupd;
            MQTTSN_WILLMSGUPD:    parse_mqttsn_willmsgupd;
            MQTTSN_WILLTOPICRESP: parse_mqttsn_willtopicresp;
            MQTTSN_WILLMSGRESP:   parse_mqttsn_willmsgresp;
            default: accept;
        }
    }

    state parse_mqttsn_advertise {
        packet.extract(hdr.mqttsn_advertise);
        verify(hdr.mqttsn_fixed.length == 5, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_searchgw {
        packet.extract(hdr.mqttsn_searchgw);
        verify(hdr.mqttsn_fixed.length == 3, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_gwinfo {
        packet.extract(hdr.mqttsn_gwinfo);
        // O gwAdd é um campo fixo e opcional. Extrair o restante do pacote como um campo variável.
        // O comprimento do gwAdd é o comprimento total da mensagem - (fixed_h + gwinfo_h)
        // MQTTSN_fixed_h (2 bytes) + MQTTSN_gwinfo_h (1 byte) = 3 bytes
        verify(hdr.mqttsn_fixed.length >= 3, error.MQTT_SN_InvalidLength);
        // calcular tamanho em bits em uma variável bit<32> antes do extract
        bit<32> mqttsn_var_bits;
        mqttsn_var_bits = ((bit<32>)hdr.mqttsn_fixed.length - (bit<32>)3) * (bit<32>)8;
        packet.extract(hdr.mqttsn_variable_field, mqttsn_var_bits);
        transition accept;
    }

    state parse_mqttsn_connect {
        packet.extract(hdr.mqttsn_flags_connect);
        packet.extract(hdr.mqttsn_connect);
        // O clientId é um campo fixo mas muito grande. Extrair o restante do pacote como um campo variável.
        // O comprimento do clientId é o comprimento total da mensagem - (fixed_h + flags_connect_h + connect_h)
        // MQTTSN_fixed_h (2 bytes) + MQTTSN_flags_connect_h (1 byte) + MQTTSN_connect_h (3 bytes) = 6 bytes
        // Comprimento do clientId = hdr.mqttsn_fixed.length - 6
        // O comprimento mínimo para CONNECT é 6 bytes (2 fixos + 1 flags + 3 connect) + pelo menos 1 byte de clientId = 7 bytes
        verify(hdr.mqttsn_fixed.length >= 7, error.MQTT_SN_InvalidLength);
        // calcular tamanho em bits em uma variável bit<32> antes do extract
        bit<32> mqttsn_var_bits;
        mqttsn_var_bits = ((bit<32>)hdr.mqttsn_fixed.length - (bit<32>)6) * (bit<32>)8;
        packet.extract(hdr.mqttsn_variable_field, mqttsn_var_bits);
        transition accept;
    }

    state parse_mqttsn_connack {
        packet.extract(hdr.mqttsn_connack);
        verify(hdr.mqttsn_fixed.length == 3, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_register {
        packet.extract(hdr.mqttsn_register);
        // O topicName é um campo variável. Comprimento = hdr.mqttsn_fixed.length - (fixed_h + register_h)
        // MQTTSN_fixed_h (2 bytes) + MQTTSN_register_h (4 bytes) = 6 bytes
        // O comprimento mínimo para REGISTER é 6 bytes (fixos) + pelo menos 1 byte de  topicName = 7 bytes
        verify(hdr.mqttsn_fixed.length >= 7, error.MQTT_SN_InvalidLength);
        // calcular tamanho em bits em uma variável bit<32> antes do extract
        bit<32> mqttsn_var_bits;
        mqttsn_var_bits = ((bit<32>)hdr.mqttsn_fixed.length - (bit<32>)6) * (bit<32>)8;
        packet.extract(hdr.mqttsn_variable_field, mqttsn_var_bits);
        transition accept;
    }

    state parse_mqttsn_regack {
        packet.extract(hdr.mqttsn_regack);
        verify(hdr.mqttsn_fixed.length == 7, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_publish {
        packet.extract(hdr.mqttsn_flags_publish);
        packet.extract(hdr.mqttsn_publish);
        // O data é um campo variável. Comprimento = hdr.mqttsn_fixed.length - (fixed_h + flags_publish_h + publish_h)
        // MQTTSN_fixed_h (2 bytes) + MQTTSN_flags_publish_h (1 byte) + MQTTSN_publish_h (4 bytes) = 7 bytes
        verify(hdr.mqttsn_fixed.length >= 7, error.MQTT_SN_InvalidLength);
        packet.extract(hdr.mqttsn_fixed_data_publish);
        transition accept;
    }

    state parse_mqttsn_puback {
        packet.extract(hdr.mqttsn_puback);
        verify(hdr.mqttsn_fixed.length == 7, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_pubrec {
        packet.extract(hdr.mqttsn_pubrec);
        verify(hdr.mqttsn_fixed.length == 4, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_pubrel {
        packet.extract(hdr.mqttsn_pubrel);
        verify(hdr.mqttsn_fixed.length == 4, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_pubcomp {
        packet.extract(hdr.mqttsn_pubcomp);
        verify(hdr.mqttsn_fixed.length == 4, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_disconnect {
        packet.extract(hdr.mqttsn_disconnect);
        verify(hdr.mqttsn_fixed.length >= 2, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_pingreq {
        packet.extract(hdr.mqttsn_pingreq);
        verify(hdr.mqttsn_fixed.length >= 2, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_pingresp {
        packet.extract(hdr.mqttsn_pingresp);
        verify(hdr.mqttsn_fixed.length == 2, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_subscribe {
        packet.extract(hdr.mqttsn_flags_subscribe);
        packet.extract(hdr.mqttsn_subscribe);
        // O topicName é um campo variável. Comprimento = hdr.mqttsn_fixed.length - (fixed_h + flags_subscribe_h + subscribe_h)
        // MQTTSN_fixed_h (2 bytes) + MQTTSN_flags_subscribe_h (1 byte) + MQTTSN_subscribe_h (4 bytes) = 7 bytes
        verify(hdr.mqttsn_fixed.length >= 7, error.MQTT_SN_InvalidLength);
        // calcular tamanho em bits em uma variável bit<32> antes do extract
        bit<32> mqttsn_var_bits;
        mqttsn_var_bits = ((bit<32>)hdr.mqttsn_fixed.length - (bit<32>)7) * (bit<32>)8;
        packet.extract(hdr.mqttsn_variable_field, mqttsn_var_bits);
        transition accept;
    }

    state parse_mqttsn_suback {
        packet.extract(hdr.mqttsn_flags_suback);
        packet.extract(hdr.mqttsn_suback);
        verify(hdr.mqttsn_fixed.length == 8, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_unsubscribe {
        packet.extract(hdr.mqttsn_flags_unsubscribe);
        packet.extract(hdr.mqttsn_unsubscribe);
        // O topicName é um campo variável. Comprimento = hdr.mqttsn_fixed.length - (fixed_h + flags_unsubscribe_h + unsubscribe_h)
        // MQTTSN_fixed_h (2 bytes) + MQTTSN_flags_unsubscribe_h (1 byte) + MQTTSN_unsubscribe_h (4 bytes) = 7 bytes
        verify(hdr.mqttsn_fixed.length >= 7, error.MQTT_SN_InvalidLength);
        // calcular tamanho em bits em uma variável bit<32> antes do extract
        bit<32> mqttsn_var_bits;
        mqttsn_var_bits = ((bit<32>)hdr.mqttsn_fixed.length - (bit<32>)7) * (bit<32>)8;
        packet.extract(hdr.mqttsn_variable_field, mqttsn_var_bits);
        transition accept;
    }

    state parse_mqttsn_unsuback {
        packet.extract(hdr.mqttsn_unsuback);
        verify(hdr.mqttsn_fixed.length == 4, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_willtopicreq {
        packet.extract(hdr.mqttsn_willtopicreq);
        verify(hdr.mqttsn_fixed.length == 2, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_willtopic {
        packet.extract(hdr.mqttsn_flags_willtopic);
        // O willTopic é um campo variável. Comprimento = hdr.mqttsn_fixed.length - (fixed_h + flags_willtopic_h)
        // MQTTSN_fixed_h (2 bytes) + MQTTSN_flags_willtopic_h (1 byte) = 3 bytes
        // O comprimento mínimo para WILLTOPIC é 3 bytes (2 fixos + 1 flags) + 1 byte de willTopic = 4 bytes
        verify(hdr.mqttsn_fixed.length >= 4, error.MQTT_SN_InvalidLength);
        // calcular tamanho em bits em uma variável bit<32> antes do extract
        bit<32> mqttsn_var_bits;
        mqttsn_var_bits = ((bit<32>)hdr.mqttsn_fixed.length - (bit<32>)3) * (bit<32>)8;
        packet.extract(hdr.mqttsn_variable_field, mqttsn_var_bits);
        transition accept;
    }

    state parse_mqttsn_willmsgreq {
        packet.extract(hdr.mqttsn_willmsgreq);
        verify(hdr.mqttsn_fixed.length == 2, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_willmsg {
        // O willMsg é um campo variável. Comprimento = hdr.mqttsn_fixed.length - fixed_h
        // MQTTSN_fixed_h (2 bytes)
        // O comprimento mínimo para WILLMSG é 2 bytes (fixos) + 1 byte de willMsg = 3 bytes
        verify(hdr.mqttsn_fixed.length >= 3, error.MQTT_SN_InvalidLength);
        // calcular tamanho em bits em uma variável bit<32> antes do extract
        bit<32> mqttsn_var_bits;
        mqttsn_var_bits = ((bit<32>)hdr.mqttsn_fixed.length - (bit<32>)2) * (bit<32>)8;
        packet.extract(hdr.mqttsn_variable_field, mqttsn_var_bits);
        transition accept;
    }

    state parse_mqttsn_willtopicupd {
        packet.extract(hdr.mqttsn_flags_willtopicupd);
        // O willTopic é um campo variável. Comprimento = hdr.mqttsn_fixed.length - (fixed_h + flags_willtopicupd_h)
        // MQTTSN_fixed_h (2 bytes) + MQTTSN_flags_willtopicupd_h (1 byte) = 3 bytes
        verify(hdr.mqttsn_fixed.length >= 3, error.MQTT_SN_InvalidLength);
        // calcular tamanho em bits em uma variável bit<32> antes do extract
        bit<32> mqttsn_var_bits;
        mqttsn_var_bits = ((bit<32>)hdr.mqttsn_fixed.length - (bit<32>)3) * (bit<32>)8;
        packet.extract(hdr.mqttsn_variable_field, mqttsn_var_bits);
        transition accept;
    }

    state parse_mqttsn_willmsgupd {
        // O willMsg é um campo variável. Comprimento = hdr.mqttsn_fixed.length - fixed_h
        // MQTTSN_fixed_h (2 bytes)
        verify(hdr.mqttsn_fixed.length >= 2, error.MQTT_SN_InvalidLength);
        // calcular tamanho em bits em uma variável bit<32> antes do extract
        bit<32> mqttsn_var_bits;
        mqttsn_var_bits = ((bit<32>)hdr.mqttsn_fixed.length - (bit<32>)2) * (bit<32>)8;
        packet.extract(hdr.mqttsn_variable_field, mqttsn_var_bits);
        transition accept;
    }

    state parse_mqttsn_willtopicresp {
        packet.extract(hdr.mqttsn_willtopicresp);
        verify(hdr.mqttsn_fixed.length == 3, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_willmsgresp {
        packet.extract(hdr.mqttsn_willmsgresp);
        verify(hdr.mqttsn_fixed.length == 3, error.MQTT_SN_InvalidLength);
        transition accept;
    }

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

/*
/////////////// LIMITAÇÕES: ////////////////
1 - Veja a seção 6.14 Support of sleeping clients.
2 - Mensagens em Broadcast não foram totalmente implementadas neste código e não foram nos clientes python.
3 - Mensagens do tipo WILL não foram totalmente implementadas neste código e não foram nos clientes python.
*/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    //////////////////////////////////////////////////////
    /////// ACTION: DESCARTE AUTOMÁTICO DE PACOTES ///////
    //////////////////////////////////////////////////////

    action drop() {
        mark_to_drop(standard_metadata);
    }

    //////////////////////////////////////////////////////
    /////// ACTION: ENCAMINHAMENTO EM BROADCAST //////////
    //////////////////////////////////////////////////////

    action broadcast() {

        // Trabalhos futuros!

        // Criar grupo de portas no switch BMv2 e enviar
        // o pacote de broadcast para esse grupo de portas.
    }

    //////////////////////////////////////////////////////
    /////////// ACTION: ENCAMINHAMENTO ESTÁTICO //////////
    //////////////////////////////////////////////////////

    action forwarding(macAddr_t dstAddr, egressSpec_t port) {
        // o novo mac de destino recebe o mac do próximo dispositivo (tabela de encaminhamento)
        hdr.ethernet.dstAddr = dstAddr;
        // define a porta de do switch para qual o pacote deve ser encaminhado (tabela de encaminhamento)
        standard_metadata.egress_spec = port;
        // decrementar o ttl em 1
        hdr.ipv4.ttl = hdr.ipv4.ttl-1;

        hdr.ipv4.hdrChecksum = 0;
        hdr.udp.checksum = 0;
    }

    //////////////////////////////////////////////////////
    /////// TABELA DE ENCAMINHAMENTO ESTÁTICO ////////////
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
    /////////// ACTION: ENCAMINHAMENTO ACELERADO //////////
    //////////////////////////////////////////////////////

    action acelerate(macAddr_t macDstAddr, egressSpec_t port, ipv4Addr_t IpDstAddr, bit<16> UdpDstPort) {

        standard_metadata.egress_spec = port;
        hdr.ethernet.dstAddr = macDstAddr;
        hdr.ipv4.dstAddr = IpDstAddr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
        hdr.udp.dstPort = UdpDstPort;

        hdr.ipv4.hdrChecksum = 0;
        hdr.udp.checksum = 0;
    }

    //////////////////////////////////////////////////////
    /////// TABELA DE ENCAMINHAMENTO ACELERADO ////////////
    //////////////////////////////////////////////////////

    table acelerate_forwarding {
        key = {
            hdr.mqttsn_publish.topicId: exact;
        }
        actions = {
            acelerate;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
    }

    //////////////////////////////////////////////////////
    /////// ACTIONS DE CRIPTOGRAFIA REFORÇADA (OTP) //////
    //////////////////////////////////////////////////////

    action otp_decrypt() {
        // O salt é o msgId (que no QoS -1 é um Nonce aleatório do Pub)
        bit<16> salt = hdr.mqttsn_publish.msgId;
        
        // Gerador de OTP dinâmico
        bit<16> otp = (salt << 7) ^ (salt >> 9) ^ 0xA5A5;
        otp = (otp << 3) | (otp >> 13); 

        // 1. Reverte a rotação (Shift para a DIREITA)
        bit<16> val = (hdr.mqttsn_publish.topicId >> 4) | (hdr.mqttsn_publish.topicId << 12);
        
        // 2. Reverte OTP e Segredo Estático
        hdr.mqttsn_publish.topicId = val ^ otp ^ SECRET_TOPIC_ID;
    }

    //////////////////////////////////////////////////////
    /////////////////// APPLY ////////////////////////////
    //////////////////////////////////////////////////////

    apply {

        ///////////////////////////////////////////////////////////////////
        /////////// Proteção contra loop interno (recirculação) ///////////
        ///////////////////////////////////////////////////////////////////

        if (standard_metadata.instance_type == PKT_INSTANCE_TYPE_INGRESS_RECIRC) {
            drop();  // descarta pacote recirculado internamente
        }

        ///////////////////////////////////////////////////////////////////
        /////////////////////// MQTT / ICMP //////////////////////////////
        //////////////////////////////////////////////////////////////////

        if (hdr.tcp.isValid() || hdr.ipv4.protocol == TYPE_ICMP) {
            static_forwarding.apply(); // Encaminha mqtt e ping
        }

        ///////////////////////////////////////////////////////////////////
        ///////////////////////// MQTT-SN ////////////////////////////////
        //////////////////////////////////////////////////////////////////

        else if (hdr.mqttsn_fixed.isValid()) {

            ////// Mensagens que podem vir de qualquer cliente pub/sub ou do Gateway MQTT-SN //////

            // DISCONNECT
            if (hdr.mqttsn_fixed.msgType == MQTTSN_DISCONNECT &&
                hdr.mqttsn_disconnect.isValid()) {
                    static_forwarding.apply();
            }
            // PUBACK
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_PUBACK && // QoS 1
                hdr.mqttsn_puback.isValid()) {
                    static_forwarding.apply();
            }
            // PUBREC
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_PUBREC && // QoS 2
                hdr.mqttsn_pubrec.isValid()) {
                    static_forwarding.apply();
            }
            // PUBREL
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_PUBREL && // QoS 2
                hdr.mqttsn_pubrel.isValid()) {
                    static_forwarding.apply();
            }
            // PUBCOMP
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_PUBCOMP && // QoS 2
                hdr.mqttsn_pubcomp.isValid()) {
                    static_forwarding.apply();
            }
            // PINGREQ
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_PINGREQ &&
                hdr.mqttsn_pingreq.isValid()) {
                    static_forwarding.apply(); 
            }
            // PINGRESP
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_PINGRESP &&
                hdr.mqttsn_pingresp.isValid()) {
                    static_forwarding.apply(); 
            }

            ////// Mensagens dos clientes com destino ao Gateway MQTT-SN //////

            else if (hdr.udp.dstPort == UDP_PORT_SVC_GW) {    // porta 1884

                // CONNECT
                if (hdr.mqttsn_fixed.msgType == MQTTSN_CONNECT &&
                    hdr.mqttsn_flags_connect.isValid() &&
                    hdr.mqttsn_connect.isValid()) {
                        static_forwarding.apply();
                }
                // REGISTER
                else if (hdr.mqttsn_fixed.msgType == MQTTSN_REGISTER &&
                    hdr.mqttsn_register.isValid() &&
                    hdr.mqttsn_variable_field.isValid()) {
                        static_forwarding.apply();
                }
                // PUBLISH
                else if (hdr.mqttsn_fixed.msgType == MQTTSN_PUBLISH &&
                    hdr.mqttsn_flags_publish.isValid() &&
                    hdr.mqttsn_publish.isValid() &&
                    hdr.mqttsn_fixed_data_publish.isValid()) {

                        otp_decrypt();

                        // QoS -1
                        if (hdr.mqttsn_flags_publish.qos == FLAGS_QOS_LEVEL_MINUS1) {
                            acelerate_forwarding.apply();
                        } 
                        // QoS 0 && flag retain = 0 (do not need remember last message, so não should to pass gateway)
                        else if (hdr.mqttsn_flags_publish.qos == FLAGS_QOS_LEVEL_0) {
                            if (hdr.mqttsn_flags_publish.retain == 0 &&
                               (hdr.mqttsn_flags_publish.topicIdType == TOPICIDTYPE_PREDEFINEDTOPIC || 
                                hdr.mqttsn_flags_publish.topicIdType == TOPICIDTYPE_SHORTTOPICNAME)) {
                                acelerate_forwarding.apply();
                            }
                            // QoS 0 && flag retain = 0, but topicIdType == TOPICIDTYPE_TOPICNAME
                            // QoS 0 && flag retain = 1 (remember last message, so should to pass gateway)
                            else {
                                static_forwarding.apply();
                            }
                        }
                        // QoS 1 ou 2
                        else {
                            static_forwarding.apply();
                        }
                }
                // SUBSCRIBE
                else if (hdr.mqttsn_fixed.msgType == MQTTSN_SUBSCRIBE &&
                    hdr.mqttsn_flags_subscribe.isValid() &&
                    hdr.mqttsn_subscribe.isValid() &&
                    hdr.mqttsn_variable_field.isValid()) {
                        static_forwarding.apply();
                }
                // UNSUBSCRIBE
                else if (hdr.mqttsn_fixed.msgType == MQTTSN_UNSUBSCRIBE &&
                    hdr.mqttsn_flags_unsubscribe.isValid() && 
                    hdr.mqttsn_unsubscribe.isValid() &&
                    hdr.mqttsn_variable_field.isValid()) {
                            static_forwarding.apply();
                }
                // WILLTOPIC
                else if (hdr.mqttsn_fixed.msgType == MQTTSN_WILLTOPIC &&
                    hdr.mqttsn_flags_willtopic.isValid() &&
                    hdr.mqttsn_willtopic.isValid() &&
                    hdr.mqttsn_variable_field.isValid()) {
                        static_forwarding.apply();
                }
                // WILLMSG
                else if (hdr.mqttsn_fixed.msgType == MQTTSN_WILLMSG &&
                    hdr.mqttsn_willmsg.isValid() &&
                    hdr.mqttsn_variable_field.isValid()) {
                        static_forwarding.apply();
                }
                // WILLTOPICUPD
                else if (hdr.mqttsn_fixed.msgType == MQTTSN_WILLTOPICUPD &&
                    hdr.mqttsn_flags_willtopicupd.isValid() &&
                    hdr.mqttsn_willtopicupd.isValid() &&
                    hdr.mqttsn_variable_field.isValid()) {
                        static_forwarding.apply();
                }
                // WILLMSGUPD
                else if (hdr.mqttsn_fixed.msgType == MQTTSN_WILLMSGUPD &&
                    hdr.mqttsn_willmsgupd.isValid() &&
                    hdr.mqttsn_variable_field.isValid()) {
                        static_forwarding.apply();
                }
            }

            ///// Mensagens do Gateway MQTT-SN com destino aos clientes //////

            else if (hdr.udp.srcPort == UDP_PORT_SVC_GW) {    // porta 1884

                // CONNACK
                if (hdr.mqttsn_fixed.msgType == MQTTSN_CONNACK &&
                    hdr.mqttsn_connack.isValid()) {
                        static_forwarding.apply();
                }
                // REGACK
                else if (hdr.mqttsn_fixed.msgType == MQTTSN_REGACK &&
                    hdr.mqttsn_regack.isValid()) {
                        static_forwarding.apply();
                }
                // PUBLISH
                else if (hdr.mqttsn_fixed.msgType == MQTTSN_PUBLISH &&
                    hdr.mqttsn_flags_publish.isValid() &&
                    hdr.mqttsn_publish.isValid() &&
                    hdr.mqttsn_fixed_data_publish.isValid()) {
                        // Encaminhar sempre, já que o gateway tratou o QoS ao receber a mensagem
                        // Egress cuidará da re-criptografia do PUBLISH
                        static_forwarding.apply();
                }
                // SUBACK
                else if (hdr.mqttsn_fixed.msgType == MQTTSN_SUBACK &&
                    hdr.mqttsn_flags_suback.isValid() &&
                    hdr.mqttsn_suback.isValid()) {
                        static_forwarding.apply();
                }
                // UNSUBACK
                else if (hdr.mqttsn_fixed.msgType == MQTTSN_UNSUBACK &&
                    hdr.mqttsn_unsuback.isValid()) {
                        static_forwarding.apply();
                }
                // REGISTER (Iniciado pelo Gateway)
                // O Gateway envia isso para informar ao cliente um TopicName <-> TopicId
                else if (hdr.mqttsn_fixed.msgType == MQTTSN_REGISTER &&
                    hdr.mqttsn_register.isValid() &&
                    hdr.mqttsn_variable_field.isValid()) {
                        static_forwarding.apply();
                }
                // WILLTOPICREQ
                else if (hdr.mqttsn_fixed.msgType == MQTTSN_WILLTOPICREQ &&
                    hdr.mqttsn_willtopicreq.isValid()) {
                        static_forwarding.apply();
                }
                // WILLMSGREQ
                else if (hdr.mqttsn_fixed.msgType == MQTTSN_WILLMSGREQ &&
                    hdr.mqttsn_willmsgreq.isValid()) {
                        static_forwarding.apply();
                }
                // WILLTOPICRESP
                else if (hdr.mqttsn_fixed.msgType == MQTTSN_WILLTOPICRESP &&
                    hdr.mqttsn_willtopicresp.isValid()) {
                        static_forwarding.apply();
                }
                // WILLMSGRESP
                else if (hdr.mqttsn_fixed.msgType == MQTTSN_WILLMSGRESP &&
                    hdr.mqttsn_willmsgresp.isValid()) {
                        static_forwarding.apply();
                }
            }

            ///////////////////////// BROADCAST //////////////////////////////

            // Trabalhos futuros //
            // ADVERTISE
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_ADVERTISE &&
                hdr.mqttsn_advertise.isValid()) {
                    broadcast();
            }
            // SEARCHGW
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_SEARCHGW &&
                hdr.mqttsn_searchgw.isValid()) {
                    broadcast();
            }
            // GWINFO
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_GWINFO &&
                hdr.mqttsn_gwinfo.isValid() &&
                hdr.mqttsn_variable_field.isValid())  {
                    broadcast();
            }
        }

        // Se a parte fixa da mensagem mqttsn não for válida, ou
        // Se não for uma mensagem conhecida ao MQTT-SN
        else {
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

    action otp_encrypt() {
        bit<16> salt = hdr.mqttsn_publish.msgId;

        bit<16> otp = (salt << 7) ^ (salt >> 9) ^ 0xA5A5;
        
        otp = (otp << 3) | (otp >> 13); 

        // 1. Aplica Segredo Estático e OTP
        bit<16> val = hdr.mqttsn_publish.topicId ^ SECRET_TOPIC_ID ^ otp;

        // 2. Aplica Rotação (Shift para a ESQUERDA)
        hdr.mqttsn_publish.topicId = (val << 4) | (val >> 12);
    }

    apply {

        if (hdr.mqttsn_fixed.msgType == MQTTSN_PUBLISH) {
            // QoS -1
            if (hdr.mqttsn_flags_publish.qos == FLAGS_QOS_LEVEL_MINUS1) {
                otp_encrypt();
            } 
            // QoS 0 && flag retain = 0 (do not need remember last message, so não should to pass gateway)
            else if (hdr.mqttsn_flags_publish.qos == FLAGS_QOS_LEVEL_0) {
                if (hdr.mqttsn_flags_publish.retain == 0 &&
                    (hdr.mqttsn_flags_publish.topicIdType == TOPICIDTYPE_PREDEFINEDTOPIC || 
                     hdr.mqttsn_flags_publish.topicIdType == TOPICIDTYPE_SHORTTOPICNAME)) {
                    otp_encrypt();
                }
            }
            ///// Mensagens do Gateway MQTT-SN com destino aos clientes //////
            else if (hdr.udp.srcPort == UDP_PORT_SVC_GW) {    // porta 1884
                otp_encrypt();
            }
        }
    }
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
        packet.emit(hdr.tcp);
        packet.emit(hdr.mqtt_fixed);
        packet.emit(hdr.udp);
        packet.emit(hdr.mqttsn_fixed);
        packet.emit(hdr.mqttsn_advertise);
        packet.emit(hdr.mqttsn_searchgw);
        packet.emit(hdr.mqttsn_gwinfo);
        packet.emit(hdr.mqttsn_flags_connect);
        packet.emit(hdr.mqttsn_connect);
        packet.emit(hdr.mqttsn_connack);
        packet.emit(hdr.mqttsn_willtopicreq);
        packet.emit(hdr.mqttsn_flags_willtopic);
        packet.emit(hdr.mqttsn_willtopic);
        packet.emit(hdr.mqttsn_willmsgreq);
        packet.emit(hdr.mqttsn_willmsg);
        packet.emit(hdr.mqttsn_register);
        packet.emit(hdr.mqttsn_regack);
        packet.emit(hdr.mqttsn_flags_publish);
        packet.emit(hdr.mqttsn_publish);
        packet.emit(hdr.mqttsn_puback);
        packet.emit(hdr.mqttsn_pubrec);
        packet.emit(hdr.mqttsn_pubrel);
        packet.emit(hdr.mqttsn_pubcomp);
        packet.emit(hdr.mqttsn_flags_subscribe);
        packet.emit(hdr.mqttsn_subscribe);
        packet.emit(hdr.mqttsn_flags_suback);
        packet.emit(hdr.mqttsn_suback);
        packet.emit(hdr.mqttsn_flags_unsubscribe);
        packet.emit(hdr.mqttsn_unsubscribe);
        packet.emit(hdr.mqttsn_unsuback);
        packet.emit(hdr.mqttsn_pingreq);
        packet.emit(hdr.mqttsn_pingresp);
        packet.emit(hdr.mqttsn_disconnect);
        packet.emit(hdr.mqttsn_flags_willtopicupd);
        packet.emit(hdr.mqttsn_willtopicupd);
        packet.emit(hdr.mqttsn_willmsgupd);
        packet.emit(hdr.mqttsn_willtopicresp);
        packet.emit(hdr.mqttsn_willmsgresp);
        packet.emit(hdr.mqttsn_variable_field);
        packet.emit(hdr.mqttsn_fixed_data_publish);
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