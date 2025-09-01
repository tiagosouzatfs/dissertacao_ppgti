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

/*Segment TCP*/
// const bit<8> TYPE_TCP = 0x06;
// const bit<16> TCP_PORT = 1883;

/*Packet IP*/
const bit<16> TYPE_IPV4 = 0x800;

/*************************************************************************
*********************** T Y P E D E F S  *********************************
*************************************************************************/

/*Packet IP*/
typedef bit<32> ipv4Addr;

/*Frame Ethernet*/
typedef bit<48> macAddr;

/*Generic Port*/
typedef bit<9> egressPort;

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

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
/* GWINFO short (only gwId) */
header MQTTSN_gwinfo_short_h {
    bit<8> gwId;
}

/*Message MQTT-SN variable header GWINFO*/
/* GWINFO full (gwId + gwAdd) */
header MQTTSN_gwinfo_full_h {
    bit<8> gwId;
    bit<32> gwAdd; // IPv4 address gw (only present if message is sent by a client)
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

/*Message MQTT-SN variable header WILLTOPICREQ*/
header MQTTSN_willtopicreq_h {
    bit<8> reserved; // Não há outros campos além do header fixo
}

/*Message MQTT-SN variable header WILLTOPIC*/
header MQTTSN_willtopic_h {
   // bit<32> willTopic; // Removido willTopic fixo. Será extraído dinamicamente.
}

/*Message MQTT-SN variable header WILLMSGREQ*/
header MQTTSN_willmsgreq_h {
    bit<8> reserved; // Não há outros campos além do header fixo
}

/*Message MQTT-SN variable header WILLMSG*/
header MQTTSN_willmsg_h {
    bit<32> willMsg; 
}

/*Message MQTT-SN variable header REGISTER*/
header MQTTSN_register_h {
    bit<16> topicId;
    bit<16> msgId;
    // bit<32> topicName; // Removido topicName fixo. Será extraído dinamicamente.
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
    // bit<32> data; // Removido data fixo. Será extraído dinamicamente.
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

/*Message MQTT-SN variable header SUBSCRIBE*/
header MQTTSN_subscribe_h {
    bit<16> msgId;
    bit<16> topicId;
    // bit<32> topicName; // Removido topicName fixo. Será extraído dinamicamente.
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
    bit<16> topicId;
    // bit<32> topicName; // Removido topicName fixo. Será extraído dinamicamente.
}

/*Message MQTT-SN variable header UNSUBACK*/
header MQTTSN_unsuback_h {
    bit<16> msgId;
}

/*Message MQTT-SN variable header PINGREQ*/
header MQTTSN_pingreq_h {
    // bit<184> clientId; // Removido clientId fixo. Será extraído dinamicamente.
    bit<8> reserved; // Não há outros campos além do header fixo
}

/*Message MQTT-SN variable header PINGRESP*/
header MQTTSN_pingresp_h {  
    bit<8> reserved; // Não há outros campos além do header fixo
}

/*Message MQTT-SN variable header DISCONNECT*/
header MQTTSN_disconnect_h {
    bit<16> duration; // (opcional)
}

/*Message MQTT-SN variable header WILLTOPICUPD*/
header MQTTSN_willtopicupd_h {
    // bit<32> willTopic; // Removido willTopic fixo. Será extraído dinamicamente.
}

/*Message MQTT-SN variable header WILLMSGUPD*/
header MQTTSN_willmsgupd_h {
    // bit<32> willMsg; // Removido willMsg fixo. Será extraído dinamicamente.
}

/*Message MQTT-SN variable header WILLTOPICRESP*/
header MQTTSN_willtopicresp_h {
    bit<8> returnCode;
}

/*Message MQTT-SN variable header WILLMSGRESP*/
header MQTTSN_willmsgresp_h {
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
    bit<2> topicIdType;
    bit<2> reserved;
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
    ipv4Addr srcAddr;
    ipv4Addr dstAddr;
}

/////////////////// ETHERNET Header //////////////////////

/*Frame Ethernet*/
header Ethernet_h {
    macAddr dstAddr;
    macAddr srcAddr;
    bit<16> ethertype;
}

//////////////////// HEADERS /////////////////////////

struct headers {
    Ethernet_h ethernet;
    IPv4_h ipv4;
    UDP_h udp;
    MQTTSN_fixed_h mqttsn_fixed;
    MQTTSN_advertise_h mqttsn_advertise;
    MQTTSN_searchgw_h mqttsn_searchgw;
    MQTTSN_gwinfo_short_h mqttsn_gwinfo_short;
    MQTTSN_gwinfo_full_h mqttsn_gwinfo_full;
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
    MQTTSN_variable_field_h mqttsn_variable_field; // Para campos variáveis
    // Adicionar os headers das mensagens MQTT
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

    // UDP
    UDPIncorrectLength,

    // MQTT-SN
    MQTT_SN_InvalidLength,
    MQTT_SN_UnsupportedMessageType,
    MQTT_SN_InvalidFlags,

    // Parsing geral
    MalformedPacket,
    UnknownProtocol
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
            MQTTSN_ADVERTISE:     parse_mqttsn_advertise;
            MQTTSN_SEARCHGW:      parse_mqttsn_searchgw;
            MQTTSN_GWINFO:        parse_mqttsn_gwinfo;
            MQTTSN_CONNECT:       parse_mqttsn_connect;
            MQTTSN_CONNACK:       parse_mqttsn_connack;
            MQTTSN_WILLTOPICREQ:  parse_mqttsn_willtopicreq;
            MQTTSN_WILLTOPIC:     parse_mqttsn_willtopic;
            MQTTSN_WILLMSGREQ:    parse_mqttsn_willmsgreq;
            MQTTSN_WILLMSG:       parse_mqttsn_willmsg;
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
        verify(hdr.mqttsn_fixed.length >= 3, error.MQTT_SN_InvalidLength);
        transition select(hdr.mqttsn_fixed.length) {
            3: parse_mqttsn_gwinfo_short;
            7: parse_mqttsn_gwinfo_full;
            default: accept;
        }
    }

    state parse_mqttsn_gwinfo_short {
        packet.extract(hdr.mqttsn_gwinfo_short);
        transition accept;
    }

    state parse_mqttsn_gwinfo_full {
        packet.extract(hdr.mqttsn_gwinfo_full);
        transition accept;
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
        packet.extract(hdr.mqttsn_variable_field, (bit<16>)((hdr.mqttsn_fixed.length - 6) * 8));
        transition accept;
    }

    state parse_mqttsn_connack {
        packet.extract(hdr.mqttsn_connack);
        verify(hdr.mqttsn_fixed.length == 3, error.MQTT_SN_InvalidLength);
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
        packet.extract(hdr.mqttsn_variable_field, (bit<16>)((hdr.mqttsn_fixed.length - 3) * 8));
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
        packet.extract(hdr.mqttsn_variable_field, (bit<16>)((hdr.mqttsn_fixed.length - 2) * 8));
        transition accept;
    }

    state parse_mqttsn_register {
        packet.extract(hdr.mqttsn_register);
        // O topicName é um campo variável. Comprimento = hdr.mqttsn_fixed.length - (fixed_h + register_h)
        // MQTTSN_fixed_h (2 bytes) + MQTTSN_register_h (4 bytes) = 6 bytes
        // O comprimento mínimo para REGISTER é 6 bytes (fixos) + 1 byte de topicName = 7 bytes
        verify(hdr.mqttsn_fixed.length >= 7, error.MQTT_SN_InvalidLength);
        packet.extract(hdr.mqttsn_variable_field, (bit<16>)((hdr.mqttsn_fixed.length - 6) * 8));
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
        packet.extract(hdr.mqttsn_variable_field, (bit<16>)((hdr.mqttsn_fixed.length - 7) * 8));
        verify(hdr.mqttsn_fixed.length >= 7, error.MQTT_SN_InvalidLength);
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

    state parse_mqttsn_subscribe {
        packet.extract(hdr.mqttsn_flags_subscribe);
        packet.extract(hdr.mqttsn_subscribe);
        // O topicName é um campo variável. Comprimento = hdr.mqttsn_fixed.length - (fixed_h + flags_subscribe_h + subscribe_h)
        // MQTTSN_fixed_h (2 bytes) + MQTTSN_flags_subscribe_h (1 byte) + MQTTSN_subscribe_h (4 bytes) = 7 bytes
        packet.extract(hdr.mqttsn_variable_field, (bit<16>)((hdr.mqttsn_fixed.length - 7) * 8));
        verify(hdr.mqttsn_fixed.length >= 7, error.MQTT_SN_InvalidLength);
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
        packet.extract(hdr.mqttsn_variable_field, (bit<16>)((hdr.mqttsn_fixed.length - 7) * 8));
        verify(hdr.mqttsn_fixed.length >= 7, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_unsuback {
        packet.extract(hdr.mqttsn_unsuback);
        verify(hdr.mqttsn_fixed.length == 4, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_pingreq {
        // O clientId é um campo variável. Comprimento = hdr.mqttsn_fixed.length - fixed_h
        // MQTTSN_fixed_h (2 bytes)
        packet.extract(hdr.mqttsn_pingreq);
        packet.extract(hdr.mqttsn_variable_field, (bit<16>)((hdr.mqttsn_fixed.length - 2) * 8));
        verify(hdr.mqttsn_fixed.length >= 2, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_pingresp {
        packet.extract(hdr.mqttsn_pingresp);
        verify(hdr.mqttsn_fixed.length == 2, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_disconnect {
        packet.extract(hdr.mqttsn_disconnect);
        verify(hdr.mqttsn_fixed.length >= 2, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_willtopicupd {
        packet.extract(hdr.mqttsn_flags_willtopicupd);
        // O willTopic é um campo variável. Comprimento = hdr.mqttsn_fixed.length - (fixed_h + flags_willtopicupd_h)
        // MQTTSN_fixed_h (2 bytes) + MQTTSN_flags_willtopicupd_h (1 byte) = 3 bytes
        packet.extract(hdr.mqttsn_variable_field, (bit<16>)((hdr.mqttsn_fixed.length - 3) * 8));
        verify(hdr.mqttsn_fixed.length >= 3, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_willmsgupd {
        // O willMsg é um campo variável. Comprimento = hdr.mqttsn_fixed.length - fixed_h
        // MQTTSN_fixed_h (2 bytes)
        packet.extract(hdr.mqttsn_variable_field, (bit<16>)((hdr.mqttsn_fixed.length - 2) * 8));
        verify(hdr.mqttsn_fixed.length >= 2, error.MQTT_SN_InvalidLength);
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

//////////////////// LIMITAÇÕES DO GATEWAY P4 ////////////////////////
/* 
1 - Este gateway não suporta as mensagens do tipo will (WILLTOPICREQ, WILLTOPIC, WILLMSGREQ e WILLMSG)!!!
2 - Veja a seção 6.2 da versão 1.2 da documentação do MQTT-SN. Inicialmente será criada apenas a condição de:
CleanSession=true, Will=false: The GW will delete all subscriptions and Will data related to the client, and returns CONNACK 
(no prompting for Will topic and Will message). Então, outros parâmetros de CleanSession e Will ficam
para projetos futuros.
3 - O returnCode MQTTSN_RETURNCODE_REJECTED_CONGESTION é usada quando o gateway está congestionado
e não pode aceitar novas conexões. Como não é possível contar o número de conexões ativas, ou seja, registros na tabela via 
data plane, então essa ação fica para projetos futuros.
4 - QoS = 2 não foi implementado.
5 - Este gateway não suporta as mensagens PUBREC, PUBREL, PUBCOMP, pois são somente para QoS = 2.
6 - Este gateway não suporta TopicName, apenas TopicId.
7 - Procedimento de publicação por parte do gateway, conforme documentação do protocolo mqttsn na seção
"6.10 Gateway’s Publish Procedure", em que isso acontece quando um cliente desconecta sem habilitar 
CleanSession=true ou foi desinscrito de topicos nomeados com caracteres wildcard.
8 - Este gateway não suporta "6.14 Support of sleeping clients", é um mecanismo de economia de bateria para IoT, mas que 
adiciona complexidade ao gateway (fila de mensagens, timers, estado por cliente).
9 - Este gateway não verifica se um client caiu inesperadamente, ou seja, saiu sem avisar ao gateway
com a mensagem disconnect.
10 - Este gateway não suporta:
    * WILLTOPICUPD:
        Quem envia: Cliente.
        Função: Atualizar o tópico do Will armazenado no gateway.
        Caso especial: Se enviada sem Flags e sem WillTopic (só 2 bytes) → significa remover o Will do gateway.
    * WILLMSGUPD:
        Quem envia: Cliente.
        Função: Atualizar o conteúdo da mensagem Will armazenada no gateway.
        Exemplo de uso: Cliente pode atualizar a mensagem para refletir uma nova condição
    * WILLTOPICRESP
        Quem envia: Gateway.
        Função: Responder a um WILLTOPICUPD.
        Campo ReturnCode: indica se o update foi aceito ou rejeitado.
    * WILLMSGRESP
        Quem envia: Gateway.
        Função: Responder a um WILLMSGUPD.
        Campo ReturnCode: igual, aceito ou rejeitado.
Essas mensagens não são obrigatórias em toda sessão. Só aparecem se 1 - o cliente quiser alterar 
dinamicamente seu Will, ou 2 - se quiser removê-lo.
11 - Todas as mensatgens em que há algum campo variável, foi definido tamanho máximo de 32 bits para remover o packet.advanced().
12 - A mensagem MQTTSN_gwinfo já vem com gwId e gwAdd
*/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    ///////////////// SET NEW ADDRESS //////////////////////

    /* helper: set IPv4/UDP lengths and zero checksums before compute stage */
    action set_l3_l4_lengths(bit<16> mqttsn_len) {
        hdr.udp.length = (bit<16>)(mqttsn_len + 8); // UDP header (8) + payload
        hdr.ipv4.ihl = 5;
        hdr.ipv4.totalLen = (bit<16>)( (bit<16>)hdr.ipv4.ihl * 4 + hdr.udp.length );
        hdr.ipv4.ttl = 64;
        hdr.ipv4.protocol = TYPE_UDP;
        hdr.ipv4.hdrChecksum = 0;
        hdr.udp.checksum = 0;
    }

    action prepare_response_unicast() {
        // swap eth
        macAddr eth_tmp = hdr.ethernet.srcAddr;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = eth_tmp;

        // swap ipv4
        ipv4Addr ip_tmp = hdr.ipv4.srcAddr;
        hdr.ipv4.srcAddr = hdr.ipv4.dstAddr;
        hdr.ipv4.dstAddr = ip_tmp;

        // swap udp ports
        bit<16> p_tmp = hdr.udp.srcPort;
        hdr.udp.srcPort = hdr.udp.dstPort;
        hdr.udp.dstPort = p_tmp;

        // reset checksums
        hdr.ipv4.hdrChecksum = 0;
        hdr.udp.checksum = 0;
    }

    ///////////////// ADVERTISE //////////////////////

    action send_advertise(bit<8> gwId, bit<16> duration) {
        hdr.mqttsn_advertise.setValid();
        hdr.mqttsn_fixed.msgType = MQTTSN_ADVERTISE;
        hdr.mqttsn_fixed.length = 5;
        hdr.mqttsn_advertise.gwId = gwId;
        hdr.mqttsn_advertise.duration = duration;

        set_l3_l4_lengths((bit<16>)hdr.mqttsn_fixed.length);
        // Envia a mensagem ADVERTISE para todos os clientes. Broadcast (porta 511 no BMv2).
        standard_metadata.egress_spec = (egressPort)511;
    }
    ///////////////// SEARCHGW & GWINFO //////////////////////

    action send_gwinfo_response(bit<8> gwId, bit<32> gwAdd) {
        hdr.mqttsn_gwinfo_full.setValid();
        hdr.mqttsn_fixed.msgType = MQTTSN_GWINFO;
        hdr.mqttsn_fixed.length = 7;
        hdr.mqttsn_gwinfo_full.gwId = gwId;
        hdr.mqttsn_gwinfo_full.gwAdd = gwAdd;

        set_l3_l4_lengths((bit<16>)hdr.mqttsn_fixed.length);
        prepare_response_unicast();
        standard_metadata.egress_spec = standard_metadata.ingress_port;
    }

    ///////////////// CONNECT & CONNACK //////////////////////

    table client_registry {
        key = {
            hdr.ipv4.srcAddr : exact;
            hdr.udp.srcPort  : exact;
        }
        actions = {
            send_connack_response_accept_connection;
            send_connack_response_reject_invalid_id;
        }
        // Suporta até 1024 entradas (clientes registrados).
        size = 1024;
        /* Ação padrão se não encontrar o clientId registrado na tabela.
        Aqui estou usando o MQTTSN_RETURNCODE_REJECTED_INVALID_TOPIC_ID (0x02) 
        para clientes não registrados. Tecnicamente o código 0x02 significa 
        Invalid Topic Id, não invalid clientId. Não existe returnCode 
        específico para clientId inválido, então usar 0x02 como fallback 
        é aceitável. Será que não vale a pena essa sugestão de melhoria
        para o protocolo MQTT-SN, criando essa mensagem de resposta?*/
        default_action = send_connack_response_reject_invalid_id();
    }

    action send_connack_response_accept_connection() {
        /* Antes de setar o novo header, para evitar pacotes 
        “com dois headers MQTT-SN válidos” ao mesmo tempo,
        usei o invalid.*/
        hdr.mqttsn_flags_connect.setInvalid();
        hdr.mqttsn_connect.setInvalid();
        hdr.mqttsn_connack.setValid();
        hdr.mqttsn_fixed.msgType = MQTTSN_CONNACK;
        hdr.mqttsn_fixed.length = 3;
        hdr.mqttsn_connack.returnCode = MQTTSN_RETURNCODE_ACCEPTED;

        set_l3_l4_lengths((bit<16>)hdr.mqttsn_fixed.length);
        prepare_response_unicast();
        standard_metadata.egress_spec = standard_metadata.ingress_port;
    }

    // Não utilizada!!!
    /*
    action send_connack_response_reject_congestion() {}
    */

    action send_connack_response_reject_invalid_id() {
        hdr.mqttsn_flags_connect.setInvalid();
        hdr.mqttsn_connect.setInvalid();
        hdr.mqttsn_connack.setValid();
        hdr.mqttsn_fixed.msgType = MQTTSN_CONNACK;
        hdr.mqttsn_fixed.length = 3;
        hdr.mqttsn_connack.returnCode = MQTTSN_RETURNCODE_REJECTED_INVALID_TOPIC_ID;

        set_l3_l4_lengths((bit<16>)hdr.mqttsn_fixed.length);
        prepare_response_unicast();
        standard_metadata.egress_spec = standard_metadata.ingress_port;
    }

    action send_connack_response_reject_not_supported() {
        hdr.mqttsn_flags_connect.setInvalid();
        hdr.mqttsn_connect.setInvalid();
        hdr.mqttsn_connack.setValid();
        hdr.mqttsn_fixed.msgType = MQTTSN_CONNACK;
        hdr.mqttsn_fixed.length = 3;
        hdr.mqttsn_connack.returnCode = MQTTSN_RETURNCODE_REJECTED_NOT_SUPPORTED;

        set_l3_l4_lengths((bit<16>)hdr.mqttsn_fixed.length);
        prepare_response_unicast();
        standard_metadata.egress_spec = standard_metadata.ingress_port;
    }

    ///////////////// REGISTER & REGACK //////////////////////

    table topic_registry {
        key = {
            hdr.mqttsn_variable_field.data : exact; // Agora usa o campo variável
        }
        actions = {
            send_regack_response_accept;
            send_regack_response_reject_invalid;
        }
        size = 1024;
        default_action = send_regack_response_reject_invalid();
    }

    action send_regack_response_accept(bit<16> topicId) {
        hdr.mqttsn_register.setInvalid();
        hdr.mqttsn_variable_field.setInvalid(); // Invalidar o campo variável após uso
        hdr.mqttsn_regack.setValid();
        hdr.mqttsn_fixed.msgType = MQTTSN_REGACK;
        hdr.mqttsn_fixed.length = 7;
        hdr.mqttsn_regack.topicId = topicId; // atribuído pelo gateway (vai vir da tabela)
        hdr.mqttsn_regack.msgId = hdr.mqttsn_register.msgId;
        hdr.mqttsn_regack.returnCode = MQTTSN_RETURNCODE_ACCEPTED;

        set_l3_l4_lengths((bit<16>)hdr.mqttsn_fixed.length);
        prepare_response_unicast();
        standard_metadata.egress_spec = standard_metadata.ingress_port;
    }

    action send_regack_response_reject_invalid() {
        hdr.mqttsn_register.setInvalid();
        hdr.mqttsn_variable_field.setInvalid(); // Invalidar o campo variável após uso
        hdr.mqttsn_regack.setValid();
        hdr.mqttsn_fixed.msgType = MQTTSN_REGACK;
        hdr.mqttsn_fixed.length = 7;
        hdr.mqttsn_regack.topicId = 0x0000;
        hdr.mqttsn_regack.msgId = hdr.mqttsn_register.msgId;
        hdr.mqttsn_regack.returnCode = MQTTSN_RETURNCODE_REJECTED_INVALID_TOPIC_ID;

        set_l3_l4_lengths((bit<16>)hdr.mqttsn_fixed.length);
        prepare_response_unicast();
        standard_metadata.egress_spec = standard_metadata.ingress_port;
    }

    ///////////////// PUBLISH & PUBACK //////////////////////

    table publish_qos{
        key = {
            hdr.mqttsn_flags_publish.qos : exact;
        }
        actions = {
            publish_qos_minus1;
            publish_qos0;
            send_puback_response;
        }
        size = 1024;
        // Se não souber tratar o tópico, manda rejeição
        default_action = send_puback_response(MQTTSN_RETURNCODE_REJECTED_INVALID_TOPIC_ID);
    }

    /*
    Regras de QoS no MQTT-SN:
    * QoS = -1 → fire and forget → não tem nem msgId. É usado em broadcasts sem garantia.
    O QoS -1 é específico do MQTT-SN (não existe no MQTT clássico).
        1 - Ele permite que clientes enviem PUBLISH mensagens “fire and forget”:
        2 - Não há ACK.
        3 - Não precisa nem de conexão ativa (CONNECT).
        4 - Ideal para sensores muito limitados (energia/memória).
    * QoS = 0 → at most once → entrega sem ACK, só repassa para quem estiver inscrito.
    * QoS = 1 → at least once → exige PUBACK. O switch precisa gerar e enviar PUBACK ao cliente.
    */

    action publish_qos_minus1() {
        set_l3_l4_lengths((bit<16>)hdr.mqttsn_fixed.length); 
        prepare_response_unicast();
        standard_metadata.egress_spec = (egressPort)511;
    }

    action publish_qos0() {
        set_l3_l4_lengths((bit<16>)hdr.mqttsn_fixed.length); 
        prepare_response_unicast();
        standard_metadata.egress_spec = (egressPort)511;
    }

    // Para qos = 1
    action send_puback_response(bit<8> returnCode) {
        hdr.mqttsn_flags_publish.setInvalid();
        hdr.mqttsn_publish.setInvalid();
        hdr.mqttsn_variable_field.setInvalid(); // Invalidar o campo variável após uso
        hdr.mqttsn_puback.setValid();
        hdr.mqttsn_fixed.msgType = MQTTSN_PUBACK;
        hdr.mqttsn_fixed.length  = 7;
        hdr.mqttsn_puback.topicId = hdr.mqttsn_publish.topicId;
        hdr.mqttsn_puback.msgId   = hdr.mqttsn_publish.msgId;
        hdr.mqttsn_puback.returnCode = returnCode;

        set_l3_l4_lengths((bit<16>)hdr.mqttsn_fixed.length); 
        prepare_response_unicast();
        standard_metadata.egress_spec = standard_metadata.ingress_port;
    }

    ///////////////// SUBSCRIBE & SUBACK //////////////////////

    table topic_registry_subscribe {
        key = {
            hdr.mqttsn_subscribe.topicId : exact;
        }
        actions = {
            send_suback_accept;
            send_suback_reject;
        }
        size = 1024;
        default_action = send_suback_reject(0);
    }

    action send_suback_accept(bit<16> topicId, bit<16> msgId) {
        hdr.mqttsn_flags_subscribe.setInvalid();
        hdr.mqttsn_subscribe.setInvalid();
        hdr.mqttsn_variable_field.setInvalid(); // Invalidar o campo variável após uso
        hdr.mqttsn_suback.setValid();
        hdr.mqttsn_fixed.msgType = MQTTSN_SUBACK;
        hdr.mqttsn_fixed.length = 8;
        hdr.mqttsn_suback.topicId = topicId;
        hdr.mqttsn_suback.msgId = msgId;
        hdr.mqttsn_suback.returnCode = MQTTSN_RETURNCODE_ACCEPTED;

        set_l3_l4_lengths((bit<16>)hdr.mqttsn_fixed.length);
        prepare_response_unicast();
        standard_metadata.egress_spec = standard_metadata.ingress_port;
    }

    action send_suback_reject(bit<16> msgId) {
        hdr.mqttsn_flags_subscribe.setInvalid();
        hdr.mqttsn_subscribe.setInvalid();
        hdr.mqttsn_variable_field.setInvalid(); // Invalidar o campo variável após uso
        hdr.mqttsn_suback.setValid();
        hdr.mqttsn_fixed.msgType = MQTTSN_SUBACK;
        hdr.mqttsn_fixed.length = 8;
        hdr.mqttsn_suback.topicId = 0x0000;
        hdr.mqttsn_suback.msgId = msgId;
        hdr.mqttsn_suback.returnCode = MQTTSN_RETURNCODE_REJECTED_INVALID_TOPIC_ID;

        set_l3_l4_lengths((bit<16>)hdr.mqttsn_fixed.length);
        prepare_response_unicast();
        standard_metadata.egress_spec = standard_metadata.ingress_port;
    }

    ///////////////// REGISTER & REGACK //////////////////////

    table topic_registry_subscribe {
        key = {
            hdr.mqttsn_subscribe.topicId : exact;
        }
        actions = {
            send_suback_accept;
            send_suback_reject;
        }
        size = 1024;
        default_action = send_suback_reject(0);
    }

    action send_suback_accept(bit<16> topicId, bit<16> msgId) {
        hdr.mqttsn_suback.setValid();
        hdr.mqttsn_fixed.msgType = MQTTSN_SUBACK;
        hdr.mqttsn_fixed.length = 8;
        hdr.mqttsn_suback.topicId = topicId;
        hdr.mqttsn_suback.msgId = msgId;
        hdr.mqttsn_suback.returnCode = MQTTSN_RETURNCODE_ACCEPTED;

        set_l3_l4_lengths((bit<16>)hdr.mqttsn_fixed.length);
        prepare_response_unicast();
        standard_metadata.egress_spec = standard_metadata.ingress_port;
    }

    action send_suback_reject(bit<16> msgId) {
        hdr.mqttsn_suback.setValid();
        hdr.mqttsn_fixed.msgType = MQTTSN_SUBACK;
        hdr.mqttsn_fixed.length = 8;
        hdr.mqttsn_suback.topicId = 0x0000;
        hdr.mqttsn_suback.msgId = msgId;
        hdr.mqttsn_suback.returnCode = MQTTSN_RETURNCODE_REJECTED_INVALID_TOPIC_ID;

        set_l3_l4_lengths((bit<16>)hdr.mqttsn_fixed.length);
        prepare_response_unicast();
        standard_metadata.egress_spec = standard_metadata.ingress_port;
    }

    ///////////////// UNSUBSCRIBE & UNSUBACK //////////////////////

    table topic_registry_unsubscribe {
        key = { 
            hdr.mqttsn_unsubscribe.topicId : exact; 
        }
        actions = {
            send_unsuback_accept;
            send_unsuback_reject;
        }
        size = 1024;
        default_action = send_unsuback_reject(0x0000);
    }

    action send_unsuback_accept(bit<16> msgId) {
        hdr.mqttsn_flags_unsubscribe.setInvalid();
        hdr.mqttsn_unsubscribe.setInvalid();
        hdr.mqttsn_variable_field.setInvalid(); // Invalidar o campo variável após uso
        hdr.mqttsn_unsuback.setValid();
        hdr.mqttsn_fixed.msgType = MQTTSN_UNSUBACK;
        hdr.mqttsn_fixed.length = 4;
        hdr.mqttsn_unsuback.msgId = msgId;

        set_l3_l4_lengths((bit<16>)hdr.mqttsn_fixed.length);
        prepare_response_unicast();
        standard_metadata.egress_spec = standard_metadata.ingress_port;
    }

    action send_unsuback_reject(bit<16> msgId) {
        hdr.mqttsn_flags_unsubscribe.setInvalid();
        hdr.mqttsn_unsubscribe.setInvalid();
        hdr.mqttsn_variable_field.setInvalid(); // Invalidar o campo variável após uso
        hdr.mqttsn_unsuback.setValid();
        hdr.mqttsn_fixed.msgType = MQTTSN_UNSUBACK;
        hdr.mqttsn_fixed.length = 4;
        hdr.mqttsn_unsuback.msgId = msgId;

        set_l3_l4_lengths((bit<16>)hdr.mqttsn_fixed.length);
        prepare_response_unicast();
        // não há ReturnCode no UNSUBACK, apenas confirma a remoção
        standard_metadata.egress_spec = standard_metadata.ingress_port;
    }
    ///////////////// PINGREQ & PINGRESP //////////////////////

    table ping_handler {
        key = {
            hdr.mqttsn_fixed.msgType : exact;
        }
        actions = {
            send_pingresp;
            send_pingreq;
            NoAction;
        }
        size = 4;
        default_action = NoAction();
    }


    action send_pingresp() {
        hdr.mqttsn_pingreq.setInvalid();
        hdr.mqttsn_variable_field.setInvalid(); // Invalidar o campo variável após uso
        hdr.mqttsn_pingresp.setValid();
        hdr.mqttsn_fixed.msgType = MQTTSN_PINGRESP;
        hdr.mqttsn_fixed.length = 2;

        set_l3_l4_lengths((bit<16>)hdr.mqttsn_fixed.length);
        prepare_response_unicast();
        standard_metadata.egress_spec = standard_metadata.ingress_port;
    }

    action send_pingreq() {
        hdr.mqttsn_pingresp.setInvalid();
        hdr.mqttsn_pingreq.setValid();
        hdr.mqttsn_fixed.msgType = MQTTSN_PINGREQ;
        hdr.mqttsn_fixed.length  = 2; // PINGREQ sem clientId tem length 2
        // Se for para enviar clientId, precisaria de um mecanismo para obtê-lo e emitir o campo variável.

        set_l3_l4_lengths((bit<16>)hdr.mqttsn_fixed.length);
        prepare_response_unicast();
        standard_metadata.egress_spec = standard_metadata.ingress_port;
    }


    ///////////////// DISCONNECT //////////////////////

    table disconnect_handler {
        key = {
            hdr.mqttsn_fixed.msgType : exact;
        }
        actions = {
            send_disconnect_ack;
            NoAction;
        }
        size = 4;
        default_action = NoAction();
    }

    // Ação: enviar DISCONNECT simples (ack)
    action send_disconnect_ack() {
        hdr.mqttsn_disconnect.setInvalid();
        hdr.mqttsn_fixed.msgType = MQTTSN_DISCONNECT;
        hdr.mqttsn_fixed.length = 2;

        set_l3_l4_lengths((bit<16>)hdr.mqttsn_fixed.length);
        prepare_response_unicast();
        standard_metadata.egress_spec = standard_metadata.ingress_port;
    }

    ///////////////// APPLY ACTIONS //////////////////////

    apply {
        if (hdr.mqttsn_fixed.isValid()) {
            if (hdr.mqttsn_fixed.msgType == MQTTSN_ADVERTISE) {
                send_advertise(1, 60);
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_SEARCHGW) {
                // A resposta padrão do gateway é um GWINFO.
                if (hdr.mqttsn_searchgw.isValid()) {
                    // Envia a resposta GWINFO para o cliente que enviou o SEARCHGW.
                    if (hdr.mqttsn_searchgw.radius == 0x00) {
                        send_gwinfo_response(2, 0x0A000002);
                    }
                } else {
                    // Se não houver um header válido.
                    mark_to_drop();
                }
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_CONNECT) {
                if (hdr.mqttsn_connect.isValid()) {
                    if (hdr.mqttsn_connect.protocolId == 0x01) {
                        if ((hdr.mqttsn_flags_connect.cleanSession == 1) && (hdr.mqttsn_flags_connect.will == 0)) {
                            client_registry.apply();
                        } else {
                            send_connack_response_reject_not_supported();
                        }
                    } else {
                        send_connack_response_reject_not_supported();
                    }
                } else {
                    // Se não houver um header válido.
                    mark_to_drop();
                }
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_REGISTER) {
                if (hdr.mqttsn_register.isValid()) {
                    // Aplica a tabela de registro de tópicos
                    topic_registry.apply();
                } else {
                    // Se não houver um header válido.
                    mark_to_drop();
                }
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_PUBLISH) {
                if (hdr.mqttsn_publish.isValid()) {
                    publish_qos.apply();
                } else {
                    // Se não houver um header válido.
                    mark_to_drop();
                }
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_SUBSCRIBE) {
                if (hdr.mqttsn_subscribe.isValid()) {
                    if (hdr.mqttsn_flags_subscribe.topicIdType == TOPICIDTYPE_TOPICNAME) {
                        // Topic Name
                        topic_registry.apply(); // lookup pelo nome
                    } 
                    else if (hdr.mqttsn_flags_subscribe.topicIdType == TOPICIDTYPE_PREDEFINEDTOPIC) {
                        // Pre-defined TopicId
                        send_suback_accept(hdr.mqttsn_subscribe.topicId, hdr.mqttsn_subscribe.msgId);
                    } 
                    else if (hdr.mqttsn_flags_subscribe.topicIdType == TOPICIDTYPE_SHORTTOPICNAME) {
                        // Short Topic Name
                        // lookup na tabela de short names, se existir
                        topic_registry.apply();
                    } else {
                        // TOPICIDTYPE_RESERVED: Reserved
                        send_suback_reject(hdr.mqttsn_subscribe.msgId);
                    }
                } else {
                    // Se não houver um header válido.
                    mark_to_drop();
                }
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_UNSUBSCRIBE) {
                if (hdr.mqttsn_unsubscribe.isValid()) {
                    if (hdr.mqttsn_flags_unsubscribe.topicIdType == TOPICIDTYPE_TOPICNAME) {
                        // Topic Name
                        topic_registry.apply(); // lookup pelo nome
                    } 
                    else if (hdr.mqttsn_flags_unsubscribe.topicIdType == TOPICIDTYPE_PREDEFINEDTOPIC) {
                        // Pre-defined TopicId
                        send_unsuback_accept(hdr.mqttsn_unsubscribe.msgId);
                    } 
                    else if (hdr.mqttsn_flags_unsubscribe.topicIdType == TOPICIDTYPE_SHORTTOPICNAME) {
                        // Short Topic Name
                        // lookup na tabela de short names, se existir
                        topic_registry.apply();
                    } else {
                        // TOPICIDTYPE_RESERVED: Reserved
                        send_unsuback_reject(hdr.mqttsn_unsubscribe.msgId);
                    }
                } else {
                    // Se não houver um header válido.
                    mark_to_drop();
                }
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_PINGREQ) {
                if (hdr.mqttsn_pingreq.isValid()) {
                    ping_handler.apply();
                } else {
                    // Se não houver um header válido.
                    mark_to_drop();
                }
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_PINGRESP) {
                if (hdr.mqttsn_pingresp.isValid()) {
                    // Se o gateway receber um ping resp, não precisa fazer nada.
                } else {
                    // Se não houver um header válido.
                    mark_to_drop();
                }
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_DISCONNECT) {
                if (hdr.mqttsn_disconnect.isValid()) {
                    disconnect_handler.apply();
                } else {
                    // Se não houver um header válido.
                    mark_to_drop();
                }
            }
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
        packet.emit(hdr.mqttsn_advertise);
        packet.emit(hdr.mqttsn_searchgw);
        packet.emit(hdr.mqttsn_gwinfo_short);
        packet.emit(hdr.mqttsn_gwinfo_full);
        packet.emit(hdr.mqttsn_connect);
        packet.emit(hdr.mqttsn_connack);
        packet.emit(hdr.mqttsn_willtopicreq);
        packet.emit(hdr.mqttsn_willtopic);
        packet.emit(hdr.mqttsn_willmsgreq);
        packet.emit(hdr.mqttsn_willmsg);
        packet.emit(hdr.mqttsn_register);
        packet.emit(hdr.mqttsn_regack);
        packet.emit(hdr.mqttsn_publish);
        packet.emit(hdr.mqttsn_puback);
        packet.emit(hdr.mqttsn_pubrec);
        packet.emit(hdr.mqttsn_pubrel);
        packet.emit(hdr.mqttsn_pubcomp);
        packet.emit(hdr.mqttsn_subscribe);
        packet.emit(hdr.mqttsn_suback);
        packet.emit(hdr.mqttsn_unsubscribe);
        packet.emit(hdr.mqttsn_unsuback);
        packet.emit(hdr.mqttsn_pingreq);
        packet.emit(hdr.mqttsn_pingresp);
        packet.emit(hdr.mqttsn_disconnect);
        packet.emit(hdr.mqttsn_willtopicupd);
        packet.emit(hdr.mqttsn_willmsgupd);
        packet.emit(hdr.mqttsn_willtopicresp);
        packet.emit(hdr.mqttsn_willmsgresp);
        packet.emit(hdr.mqttsn_flags_connect);
        packet.emit(hdr.mqttsn_flags_willtopic);
        packet.emit(hdr.mqttsn_flags_publish);
        packet.emit(hdr.mqttsn_flags_subscribe);
        packet.emit(hdr.mqttsn_flags_suback);
        packet.emit(hdr.mqttsn_flags_unsubscribe);
        packet.emit(hdr.mqttsn_flags_willmsgupd);
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

// docker run -dit --name=p4 --rm ramonfontes/bmv2:latest
// docker cp mqtt-sn-p4-architecture/p4src p4:/tmp/
// docker exec -it p4 bash
// cd /tmp/p4src
// p4c --target bmv2 --arch v1model gw_agg_mqtt_sn.p4