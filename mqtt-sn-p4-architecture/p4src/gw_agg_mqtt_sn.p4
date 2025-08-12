/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

/*************************************************************************
*********************** C O N S T S **************************************
*************************************************************************/

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

/*Vou deixar aqui para testar o uso do header mqttsn_flags_t,
se der certo, pode apagar essas consts*/
/*Message MQTT-SN flags*/
const bit<1> MQTTSN_FLAG_DUP0 = 0;
const bit<1> MQTTSN_FLAG_DUP1 = 1;
const bit<2> MQTTSN_FLAG_QOS0 = 0b00;
const bit<2> MQTTSN_FLAG_QOS1 = 0b01;
const bit<2> MQTTSN_FLAG_QOS2 = 0b10;
const bit<2> MQTTSN_FLAG_QOSminus1 = 0b11;
const bit<1> MQTTSN_FLAG_RETAIN0 = 0; // true
const bit<1> MQTTSN_FLAG_RETAIN1 = 1; // false
const bit<1> MQTTSN_FLAG_WILL0 = 0; // true
const bit<1> MQTTSN_FLAG_WILL1 = 1; // false
const bit<1> MQTTSN_FLAG_CLEANSESSION0 = 0; // true
const bit<1> MQTTSN_FLAG_CLEANSESSION1 = 1; // false
const bit<2> MQTTSN_FLAG_TOPICIDTYPE0 = 0b00; // Normal topicId
const bit<2> MQTTSN_FLAG_TOPICIDTYPE1 = 0b01; // Pre-defined topicId
const bit<2> MQTTSN_FLAG_TOPICIDTYPE2 = 0b10; // Short topicName
//const bit<2> MQTTSN_FLAG_TOPICIDTYPE3 = 0b11; // Reserved

/*Message MQTT-SN return codes*/
const bit<8> MQTTSN_RETURNCODE_ACCEPTED = 0x00;
const bit<8> MQTTSN_RETURNCODE_REJECTED_CONGESTION = 0x01;
const bit<8> MQTTSN_RETURNCODE_REJECTED_INVALID_TOPIC_ID = 0x02;
const bit<8> MQTTSN_RETURNCODE_REJECTED_NOT_SUPPORTED = 0x03;
//const bit<8> MQTTSN_RETURNCODE_???? = 0x04-0xFF; // Reserved

/*Segment UDP*/
const bit<8> TYPE_UDP = 0x11;
const bit<16> UDP_PORT = 1884;

/*Segment TCP*/
const bit<8> TYPE_TCP = 0x06;
const bit<16> TCP_PORT = 1883;

/*Packet IP*/
const bit<16> TYPE_IPV4 = 0x800;

/*************************************************************************
*********************** T Y P E D E F S  *********************************
*************************************************************************/

/*Packet IP*/
typedef bit<32> ipv4Addr;

/*Frame Ethernet*/
typedef bit<48> macAddr;

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

//////////////////// MQTT Headers ////////////////////

/*Message MQTT fixed header*/
header MQTT_fixed_h {
    bit<4> controlPacketType;
    bit<4> flagsPacketType;
    bit<8> remainingLength;
}

// Adicionar os headers das mensagens MQTT
header MQTT_ {
    /* empty */
}

//////////////////// MQTT-SN Headers ////////////////////

/*Message MQTT-SN fixed header*/
header MQTTSN_fixed_h {
    bit<8>  length;
    //varbit<24>      length;
    bit<8>  msgType;
}

/*Message MQTT-SN variable header ADVERTISE*/
header MQTTSN_advertise_h {
    bit<8>   gwId;
    bit<16>  duration;
}

/*Message MQTT-SN variable header SEARCHGW*/
header MQTTSN_searchgw_h {
    bit<8>  radius;
}

/*Message MQTT-SN variable header GWINFO*/
header MQTTSN_gwinfo_h {
    bit<8>   gwId;
    bit<32>  gwAdd; // IPv4 address gw (only present if message is sent by a client)
}

/*Message MQTT-SN variable header CONNECT*/
header MQTTSN_connect_h {
    bit<8>    flags;
    bit<8>    protocolId;
    bit<16>   duration;
    bit<184>  clientId; // max 23 caracteres * 1 byte (8 bits) = 184 bits
}

/*Message MQTT-SN variable header CONNACK*/
header MQTTSN_connack_h {
    bit<8>  returnCode;
}

/*Message MQTT-SN variable header WILLTOPICREQ*/
header MQTTSN_willtopicreq_h {
    /* empty */
}

/*Message MQTT-SN variable header WILLTOPIC*/
header MQTTSN_willtopic_h {
    bit<8>    flags;
    bit<256>  willTopic; // Verificar tamanho!!!
}

/*Message MQTT-SN variable header WILLMSGREQ*/
header MQTTSN_willmsgreq_h {
    /* empty */
}

/*Message MQTT-SN variable header WILLMSG*/
header MQTTSN_willmsg_h {
    bit<256>  willMsg; // Verificar tamanho!!!
}

/*Message MQTT-SN variable header REGISTER*/
header MQTTSN_register_h {
    bit<16>      topicId;
    bit<16>      msgId;
    bit<256>  topicName; // Verificar tamanho!!!
}

/*Message MQTT-SN variable header REGACK*/
header MQTTSN_regack_h {
    bit<16>  topicId;
    bit<16>  msgId;
    bit<8>   returnCode;
}

/*Message MQTT-SN variable header PUBLISH*/
header MQTTSN_publish_h {
    bit<8>    flags;
    bit<16>   topicId;
    bit<16>   msgId;
    bit<256>  data; // Verificar tamanho!!!
}

/*Message MQTT-SN variable header PUBACK*/
header MQTTSN_puback_h {
    bit<16>  topicId;
    bit<16>  msgId;
    bit<8>   returnCode;
}

/*Message MQTT-SN variable header PUBREC*/
header MQTTSN_pubrec_h {
    bit<16>  msgId;
}

/*Message MQTT-SN variable header PUBREL*/
header MQTTSN_pubrel_h {
    bit<16>  msgId;
}

/*Message MQTT-SN variable header PUBCOMP*/
header MQTTSN_pubcomp_h {
    bit<16>  msgId;
}

/*Message MQTT-SN variable header SUBSCRIBE*/
header MQTTSN_subscribe_h {
    bit<8>    flags;
    bit<16>   msgId;
    bit<16>   topicId;
    bit<256>  topicName; // (opcional) Verificar tamanho!!!
}

/*Message MQTT-SN variable header SUBACK*/
header MQTTSN_suback_h {
    bit<8>   flags;
    bit<16>  topicId;
    bit<16>  msgId;
    bit<8>   returnCode;
}

/*Message MQTT-SN variable header UNSUBSCRIBE*/
header MQTTSN_unsubscribe_h {
    bit<8>    flags;
    bit<16>   msgId;
    bit<16>   topicId;
    bit<256>  topicName; // (opcional) Verificar tamanho!!!
}

/*Message MQTT-SN variable header UNSUBACK*/
header MQTTSN_unsuback_h {
    bit<16>  msgId;
}

/*Message MQTT-SN variable header PINGREQ*/
header MQTTSN_pingreq_h {
    bit<184>  clientId; // (opcional) max 23 caracteres * 1 byte (8 bits) = 184 bits
}

/*Message MQTT-SN variable header PINGRESP*/
header MQTTSN_pingresp_h {  
    /* empty */
}

/*Message MQTT-SN variable header DISCONNECT*/
header MQTTSN_disconnect_h {
    bit<16>  duration; // (opcional)
}

/*Message MQTT-SN variable header WILLTOPICUPD*/
header MQTTSN_willtopicupd_h {
    bit<8>    flags;
    bit<256>  willTopic; // Verificar tamanho!!!
}

/*Message MQTT-SN variable header WILLMSGUPD*/
header MQTTSN_willmsgupd_h {
    bit<256>  willMsg; // Verificar tamanho!!!
}

/*Message MQTT-SN variable header WILLTOPICRESP*/
header MQTTSN_willtopicresp_h {
    bit<8>  returnCode;
}

/*Message MQTT-SN variable header WILLMSGRESP*/
header MQTTSN_willmsgresp_h {
    bit<8>  returnCode;
}

//////////////// MQTT-SN Headers Flags //////////////////

/*Message MQTT-SN flags CONNECT*/
header MQTTSN_flags_connect_h {
    bit<1>  will;
    bit<1>  cleanSession;
    bit<6>  reserved; // (Estratégia para completar os 8 bits das flags e não dar erro na compilação)BMv2 target only supports headers with fields totaling a multiple of 8 bits.
}

/*Message MQTT-SN flags WILLTOPIC*/
header MQTTSN_flags_willtopic_h {
    bit<2>  qos;
    bit<1>  retain;
    bit<5>  reserved;
}

/*Message MQTT-SN flags PUBLISH*/
header MQTTSN_flags_publish_h {
    bit<1>  dup;
    bit<2>  qos;
    bit<1>  retain;
    bit<2>  topicIdType;
    bit<2>  reserved;
}

/*Message MQTT-SN flags SUBSCRIBE*/
header MQTTSN_flags_subscribe_h {
    bit<1>  dup;
    bit<2>  qos;
    bit<2>  topicIdType;
    bit<3>  reserved;
}

/*Message MQTT-SN flags UNSUBSCRIBE*/
header MQTTSN_flags_unsubscribe_h {
    bit<1>  dup;
    bit<2>  qos;
    bit<2>  topicIdType;
    bit<3>  reserved;
}

/*Message MQTT-SN flags SUBACK*/
header MQTTSN_flags_suback_h {
    bit<2>  qos;
    bit<6>  reserved;
}

/*Message MQTT-SN flags WILLTOPICUPD*/
header MQTTSN_flags_willtopicupd_h {
    bit<2>  qos;
    bit<1>  retain;
    bit<5>  reserved;
}

///////////////////// UDP Header ////////////////////

/*Segment UDP*/
header UDP_h {
    bit<16>    srcPort;
    bit<16>    dstPort;
    bit<16>    length;
    bit<16>    checksum;
}

/////////////////// IPV4 Header ///////////////////////

/*Packet IP*/
header IPv4_h {
    bit<4>       version;
    bit<4>       ihl;
    bit<8>       diffServ;
    bit<16>      totalLen;
    bit<16>      identification;
    bit<3>       flags;
    bit<13>      fragOffset;
    bit<8>       ttl;
    bit<8>       protocol;
    bit<16>      hdrChecksum;
    ipv4Addr     srcAddr;
    ipv4Addr     dstAddr;
}

/////////////////// ETHERNET Header //////////////////////

/*Frame Ethernet*/
header Ethernet_h {
    macAddr  dstAddr;
    macAddr  srcAddr;
    bit<16>  ethertype;
}

//////////////////// HEADERS /////////////////////////

struct headers {
    Ethernet_h ethernet;
    IPv4_h ipv4;
    UDP_h  udp;
    MQTTSN_fixed_h mqttsn_fixed;
    MQTTSN_advertise_h mqttsn_advertise;
    MQTTSN_searchgw_h mqttsn_searchgw;
    MQTTSN_gwinfo_h mqttsn_gwinfo;
    MQTTSN_connect_h mqttsn_connect;
    MQTTSN_connack_h mqttsn_connack;
    MQTTSN_willtopicreq_h mqttsn_willtopicreq;
    MQTTSN_willtopic_h mqttsn_willtopic;
    MQTTSN_willmsgreq_h mqttsn_willmsgreq;
    MQTTSN_willmsg_h mqttsn_willmsg;
    MQTTSN_register_h mqttsn_register;
    MQTTSN_regack_h mqttsn_regack;
    MQTTSN_publish_h mqttsn_publish;
    MQTTSN_puback_h mqttsn_puback;
    MQTTSN_pubrec_h mqttsn_pubrec;
    MQTTSN_pubrel_h mqttsn_pubrel;
    MQTTSN_pubcomp_h mqttsn_pubcomp;
    MQTTSN_subscribe_h mqttsn_subscribe;
    MQTTSN_suback_h mqttsn_suback;
    MQTTSN_unsubscribe_h mqttsn_unsubscribe;
    MQTTSN_unsuback_h mqttsn_unsuback;
    MQTTSN_pingreq_h mqttsn_pingreq;
    MQTTSN_pingresp_h mqttsn_pingresp;
    MQTTSN_disconnect_h mqttsn_disconnect;
    MQTTSN_willtopicupd_h mqttsn_willtopicupd;
    MQTTSN_willmsgupd_h mqttsn_willmsgupd;
    MQTTSN_willtopicresp_h mqttsn_willtopicresp;
    MQTTSN_willmsgresp_h mqttsn_willmsgresp;
    MQTTSN_flags_connect_h mqttsn_flags_connect;
    MQTTSN_flags_willtopic_h mqttsn_flags_willtopic;
    MQTTSN_flags_publish_h mqttsn_flags_publish;
    MQTTSN_flags_subscribe_h mqttsn_flags_subscribe;
    MQTTSN_flags_unsubscribe_h mqttsn_flags_unsubscribe;
    MQTTSN_flags_suback_h mqttsn_flags_suback;
    MQTTSN_flags_willtopicupd_h mqttsn_flags_willtopicupd;
    // Adicionar os headers das mensagens MQTT
    //MQTT_fixed_h mqtt_fixed;
}

struct metadata {
    /* empty */
}

// Erros customizados para validação de headers
error {
    // Ethernet
    UnsupportedEtherType,

    // IPv4
    IPv4IncorrectVersion,
    IPv4HeaderLengthError,
    IPv4ChecksumError,
    IPv4UnsupportedProtocol,

    // UDP
    UDPIncorrectLength,

    // MQTT-SN
    MQTT_SN_InvalidLength,
    MQTT_SN_UnsupportedMessageType,
    MQTT_SN_InvalidFlags,

    // Parsing geral
    //PacketTooShort,
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
        transition select(hdr.ethernet.ethertype){
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
            MQTTSN_ADVERTISE: parse_mqttsn_advertise;
            MQTTSN_SEARCHGW: parse_mqttsn_searchgw;
            MQTTSN_GWINFO: parse_mqttsn_gwinfo;
            MQTTSN_CONNECT: parse_mqttsn_connect;
            MQTTSN_CONNACK: parse_mqttsn_connack;
            MQTTSN_WILLTOPICREQ: parse_mqttsn_willtopicreq;
            MQTTSN_WILLTOPIC: parse_mqttsn_willtopic;
            MQTTSN_WILLMSGREQ: parse_mqttsn_willmsgreq;
            MQTTSN_WILLMSG: parse_mqttsn_willmsg;
            MQTTSN_REGISTER: parse_mqttsn_register;
            MQTTSN_REGACK: parse_mqttsn_regack;
            MQTTSN_PUBLISH: parse_mqttsn_publish;
            MQTTSN_PUBACK: parse_mqttsn_puback;
            MQTTSN_PUBREC: parse_mqttsn_pubrec;
            MQTTSN_PUBREL: parse_mqttsn_pubrel;
            MQTTSN_PUBCOMP: parse_mqttsn_pubcomp;
            MQTTSN_SUBSCRIBE: parse_mqttsn_subscribe;
            MQTTSN_SUBACK: parse_mqttsn_suback;
            MQTTSN_UNSUBSCRIBE: parse_mqttsn_unsubscribe;
            MQTTSN_UNSUBACK: parse_mqttsn_unsuback;
            MQTTSN_PINGREQ: parse_mqttsn_pingreq;
            MQTTSN_PINGRESP: parse_mqttsn_pingresp;
            MQTTSN_DISCONNECT: parse_mqttsn_disconnect;
            MQTTSN_WILLTOPICUPD: parse_mqttsn_willtopicupd;
            MQTTSN_WILLMSGUPD: parse_mqttsn_willmsgupd;
            MQTTSN_WILLTOPICRESP: parse_mqttsn_willtopicresp;
            MQTTSN_WILLMSGRESP: parse_mqttsn_willmsgresp;
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
        verify(hdr.mqttsn_fixed.length >= 3, error.MQTT_SN_InvalidLength);
        transition select(hdr.mqttsn_fixed.length) {
            3: accept; // só gwId
            7: parse_mqttsn_gwinfo_with_ip; // gwId + gwAdd
            default: accept;
        }
    }

    // Estado para tratar o caso em que gwAdd é incluído,
    //   como foi chamado via transition select, não foi necessário
    //   extrair o header mqttsn_gwinfo novamente com outro nome
    state parse_mqttsn_gwinfo_with_ip {
        // Pula os 4 bytes do campo gwAdd finais
        packet.advance((bit<32>)(hdr.mqttsn_fixed.length - 3) * 8);
        transition accept;
    }

    state parse_mqttsn_flags_connect {
        packet.extract(hdr.mqttsn_flags_connect);
        transition parse_mqttsn_connect;
    }

    state parse_mqttsn_connect {
        packet.extract(hdr.mqttsn_connect);
        verify(hdr.mqttsn_fixed.length >= 7, error.MQTT_SN_InvalidLength);
        // Pula a quantidade bits relacionados ao campo clientId
        // Packet advance tem que ser em bits
        packet.advance((bit<32>)(hdr.mqttsn_fixed.length - 6) * 8);
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

    state parse_mqttsn_flags_willtopic {
        packet.extract(hdr.mqttsn_flags_willtopic);
        transition parse_mqttsn_willtopic;
    }

    state parse_mqttsn_willtopic {
        packet.extract(hdr.mqttsn_willtopic);
        verify(hdr.mqttsn_fixed.length >= 3, error.MQTT_SN_InvalidLength);
        transition select(hdr.mqttsn_fixed.length) {
            3: accept; // Mensagem WILLTOPIC vazia
            default: parse_mqttsn_willtopic_extended;
        }
    }

    state parse_mqttsn_willtopic_extended {
        // Pula WillTopic (length - Length(1) - MsgType(1) - Flags(1))
        packet.advance((bit<32>)(hdr.mqttsn_fixed.length - 3) * 8);
        transition accept;
    }

    state parse_mqttsn_willmsgreq {
        packet.extract(hdr.mqttsn_willmsgreq);
        verify(hdr.mqttsn_fixed.length == 2, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_willmsg {
        packet.extract(hdr.mqttsn_willmsg);
        verify(hdr.mqttsn_fixed.length >= 3, error.MQTT_SN_InvalidLength);
        packet.advance((bit<32>)(hdr.mqttsn_fixed.length - 2) * 8);
        transition accept;
    }

    state parse_mqttsn_register {
        packet.extract(hdr.mqttsn_register);
        verify(hdr.mqttsn_fixed.length >= 7, error.MQTT_SN_InvalidLength);
        packet.advance((bit<32>)(hdr.mqttsn_fixed.length - 6) * 8);
        transition accept;
    }

    state parse_mqttsn_regack {
        packet.extract(hdr.mqttsn_regack);
        verify(hdr.mqttsn_fixed.length == 7, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_flags_publish {
        packet.extract(hdr.mqttsn_flags_publish);
        transition parse_mqttsn_publish;
    }

    state parse_mqttsn_publish {
        packet.extract(hdr.mqttsn_publish);
        verify(hdr.mqttsn_fixed.length >= 8, error.MQTT_SN_InvalidLength);
        packet.advance((bit<32>)(hdr.mqttsn_fixed.length - 7) * 8);
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

    state parse_mqttsn_flags_subscribe {
        packet.extract(hdr.mqttsn_flags_subscribe);
        transition parse_mqttsn_subscribe;
    }

    state parse_mqttsn_subscribe {
        packet.extract(hdr.mqttsn_subscribe);
        verify(hdr.mqttsn_fixed.length >= 6, error.MQTT_SN_InvalidLength);
        transition select(hdr.mqttsn_fixed.length) {
            7: accept; // Mensagem com topicId
            default: parse_mqttsn_subscribe_extended;
        }
    }

    state parse_mqttsn_subscribe_extended {
        // Pula o topicName
        packet.advance((bit<32>)(hdr.mqttsn_fixed.length - 5) * 8);
        transition accept;
    }

    state parse_mqttsn_flags_suback {
        packet.extract(hdr.mqttsn_flags_suback);
        transition parse_mqttsn_suback;
    }

    state parse_mqttsn_suback {
        packet.extract(hdr.mqttsn_suback);
        verify(hdr.mqttsn_fixed.length == 8, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_flags_unsubscribe {
        packet.extract(hdr.mqttsn_flags_unsubscribe);
        transition parse_mqttsn_unsubscribe;
    }

    state parse_mqttsn_unsubscribe {
        packet.extract(hdr.mqttsn_unsubscribe);
        verify(hdr.mqttsn_fixed.length >= 6, error.MQTT_SN_InvalidLength);
        transition select(hdr.mqttsn_fixed.length) {
            7: accept; // Mensagem com topicId
            default: parse_mqttsn_unsubscribe_extended;
        }
    }

    state parse_mqttsn_unsubscribe_extended {
        // Pula o topicName
        packet.advance((bit<32>)(hdr.mqttsn_fixed.length - 5) * 8);
        transition accept;
    }

    state parse_mqttsn_unsuback {
        packet.extract(hdr.mqttsn_unsuback);
        verify(hdr.mqttsn_fixed.length == 4, error.MQTT_SN_InvalidLength);
        transition accept;
    }

    state parse_mqttsn_pingreq {
        packet.extract(hdr.mqttsn_pingreq);
        verify(hdr.mqttsn_fixed.length >= 2, error.MQTT_SN_InvalidLength);
        transition select(hdr.mqttsn_fixed.length) {
            2: accept;
            default: parse_mqttsn_pingreq_extended;
        }
    }

    state parse_mqttsn_pingreq_extended {
        // Pula o clientId
        packet.advance((bit<32>)(hdr.mqttsn_fixed.length - 2) * 8);
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

    state parse_mqttsn_flags_willtopicupd {
        packet.extract(hdr.mqttsn_flags_willtopicupd);
        transition parse_mqttsn_willtopicupd;
    }

    state parse_mqttsn_willtopicupd {
        packet.extract(hdr.mqttsn_willtopicupd);
        verify(hdr.mqttsn_fixed.length >= 4, error.MQTT_SN_InvalidLength);
        packet.advance((bit<32>)(hdr.mqttsn_fixed.length - 3) * 8);
        transition accept;
    }

    state parse_mqttsn_willmsgupd {
        packet.extract(hdr.mqttsn_willmsgupd);
        verify(hdr.mqttsn_fixed.length >= 3, error.MQTT_SN_InvalidLength);
        packet.advance((bit<32>)(hdr.mqttsn_fixed.length - 2) * 8);
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

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {
    apply {  }
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
        packet.emit(hdr.mqttsn_gwinfo);
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
        packet.emit(hdr.mqttsn_willmsgupd);
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