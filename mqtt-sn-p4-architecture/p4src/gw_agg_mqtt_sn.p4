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

/*Flags QoS Level*/
const bit<2> FLAGS_QOS_LEVEL_0 = 0b00;
const bit<2> FLAGS_QOS_LEVEL_1 = 0b01;
const bit<2> FLAGS_QOS_LEVEL_2 = 0b10;
const bit<2> FLAGS_QOS_LEVEL_MINUS1 = 0b11;

/*Segment UDP*/
const bit<8> TYPE_UDP = 0x11; // 17
const bit<16> UDP_PORT = 1884;

/*Packet IP*/
const bit<16> TYPE_IPV4 = 0x800; // 2048

/*************************************************************************
*********************** T Y P E D E F S  *********************************
*************************************************************************/

/*Packet IP*/
typedef bit<32> ipv4Addr_t;

/*Frame Ethernet*/
typedef bit<48> macAddr_t;

/*Generic Port*/
typedef bit<9>  egressSpec_t; // representa a porta de saída do switch com 9 bits

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

/*Message MQTT-SN variable header DISCONNECT*/
// Uma mensagem DISCONNECT com um campo Duração é enviada por um cliente quando este deseja entrar no estado "suspenso".
// O recebimento desta mensagem também é confirmado pelo gateway por meio de uma mensagem DISCONNECT (sem um campo de duração).
// Veja a seção 6.14 Support of sleeping clients
header MQTTSN_disconnect_h {
    //bit<16> duration; // (opcional) ficará para implementações futuras
}

/*Message MQTT-SN variable header PINGREQ*/
// Veja a seção 6.14 Support of sleeping clients
header MQTTSN_pingreq_h {
    // bit<184> clientId; // (opcional) ficará para implementações futuras e deverá ser extraído dinamicamente.
}

/*Message MQTT-SN variable header PINGRESP*/
header MQTTSN_pingresp_h {  
    // Não há outros campos além do header fixo
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

/*Default header to fields variables*/
// Max payload size for Ethernet/IPv4/UDP/MQTT-SN(parte fixa) (1500 - 20 - 8 - 2 = 1470 bytes = 11760 bits)
// O tamanho real será determinado pelo campo length do MQTTSN_fixed_h, pois ainda teria que diminuir
//    os campos que tem tamanho fixo, mas como nem todas as mensagens tem, vou deixar assim.
header MQTTSN_variable_field_h {
    varbit<11760> data;
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

/*Message MQTT-SN flags PUBLISH*/
header MQTTSN_flags_publish_h {
    bit<1> dup;
    bit<2> qos;
    bit<1> retain;
    bit<2> topicIdType;
    bit<2> reserved;
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
    MQTTSN_register_h mqttsn_register;
    MQTTSN_regack_h mqttsn_regack;
    MQTTSN_flags_publish_h mqttsn_flags_publish;
    MQTTSN_publish_h mqttsn_publish;
    MQTTSN_puback_h mqttsn_puback;
    MQTTSN_pubrec_h mqttsn_pubrec;
    MQTTSN_pubrel_h mqttsn_pubrel;
    MQTTSN_pubcomp_h mqttsn_pubcomp;
    MQTTSN_disconnect_h mqttsn_disconnect;
    MQTTSN_pingreq_h mqttsn_pingreq;
    MQTTSN_pingresp_h mqttsn_pingresp;
    MQTTSN_flags_subscribe_h mqttsn_flags_subscribe;
    MQTTSN_subscribe_h mqttsn_subscribe;
    MQTTSN_flags_suback_h mqttsn_flags_suback;
    MQTTSN_suback_h mqttsn_suback;
    MQTTSN_flags_unsubscribe_h mqttsn_flags_unsubscribe;
    MQTTSN_unsubscribe_h mqttsn_unsubscribe;
    MQTTSN_unsuback_h mqttsn_unsuback;
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
        transition select(hdr.udp.srcPort, hdr.udp.dstPort) {
            (UDP_PORT, _) : parse_mqttsn_fixed;   // Para mensagens com srcPort = 1884
            (_, UDP_PORT) : parse_mqttsn_fixed;   // Para mensagens com dstPort = 1884
            default: accept;
        }
    }

    state parse_mqttsn_fixed {
        packet.extract(hdr.mqttsn_fixed);
        verify(hdr.mqttsn_fixed.length >= 2, error.MQTT_SN_InvalidLength);
        transition select(hdr.mqttsn_fixed.msgType) {
            MQTTSN_CONNECT:     parse_mqttsn_connect;
            MQTTSN_CONNACK:     parse_mqttsn_connack;
            MQTTSN_REGISTER:    parse_mqttsn_register;
            MQTTSN_REGACK:      parse_mqttsn_regack;
            MQTTSN_PUBLISH:     parse_mqttsn_publish;
            MQTTSN_PUBACK:      parse_mqttsn_puback;
            MQTTSN_PUBREC:      parse_mqttsn_pubrec;
            MQTTSN_PUBREL:      parse_mqttsn_pubrel;
            MQTTSN_PUBCOMP:     parse_mqttsn_pubcomp;
            MQTTSN_DISCONNECT:  parse_mqttsn_disconnect;
            MQTTSN_PINGREQ:     parse_mqttsn_pingreq;
            MQTTSN_PINGRESP:    parse_mqttsn_pingresp;
            MQTTSN_SUBSCRIBE:   parse_mqttsn_subscribe;
            MQTTSN_SUBACK:      parse_mqttsn_suback;
            MQTTSN_UNSUBSCRIBE: parse_mqttsn_unsubscribe;
            MQTTSN_UNSUBACK:    parse_mqttsn_unsuback;
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
        // calcular tamanho em bits em uma variável bit<32> antes do extract
        bit<32> mqttsn_var_bits;
        mqttsn_var_bits = ((bit<32>)hdr.mqttsn_fixed.length - (bit<32>)7) * (bit<32>)8;
        packet.extract(hdr.mqttsn_variable_field, mqttsn_var_bits);
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
1 - Não suporta as mensagens:
  * ADVERTISE
  * SEARCHGW
  * GWINFO
  * WILLTOPICREQ
  * WILLTOPIC
  * WILLMSGREQ
  * WILLMSG
  * WILLTOPICUPD
  * WILLMSGUPD
  * WILLTOPICRESP
  * WILLMSGRESP
2 - Não suporta sleeping clients, veja a seção 6.14 Support of sleeping clients
3 - Não suporta o TopicIdType “0b01” pre-defined topic id
*/

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
    // APPLY
    //////////////////////////////////////////////////////

    apply {
        if (hdr.mqttsn_fixed.isValid()) {
            if (hdr.mqttsn_fixed.msgType == MQTTSN_CONNECT &&
                hdr.mqttsn_connect.isValid() &&
                hdr.mqttsn_connect.protocolId == 0x01) { // corresponds to the “Protocol Name” and “Protocol Version” of the MQTT CONNECT message.
                if (hdr.udp.dstPort == UDP_PORT &&     // porta 1884
                    hdr.ipv4.dstAddr == 0x0A000002) {  // gateway 10.0.0.2
                        static_forwarding.apply();
                }
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_CONNACK &&
                hdr.mqttsn_connack.isValid()) {
                if (hdr.udp.srcPort == UDP_PORT &&     // porta 1884
                    hdr.ipv4.srcAddr == 0x0A000002) {  // gateway 10.0.0.2
                        static_forwarding.apply();
                }
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_REGISTER &&
                hdr.mqttsn_register.isValid()) {
                if (hdr.mqttsn_register.topicId == 0x0000 && // if sent by a client, it is coded 0x0000 and is not relevant;
                    hdr.udp.dstPort == UDP_PORT &&     // porta 1884
                    hdr.ipv4.dstAddr == 0x0A000002) {  // gateway 10.0.0.2
                        static_forwarding.apply();
                }
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_REGACK &&
                hdr.mqttsn_regack.isValid()) {
                if (hdr.mqttsn_regack.topicId != 0x0000 &&
                    hdr.udp.srcPort == UDP_PORT &&    // porta 1884
                    hdr.ipv4.srcAddr == 0x0A000002) { // gateway 10.0.0.2
                        static_forwarding.apply();
                }
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_PUBLISH &&
                hdr.mqttsn_flags_publish.isValid() &&
                hdr.mqttsn_publish.isValid() &&
                hdr.mqttsn_variable_field.isValid()) {
                // -------- Client -> Gateway --------
                if (hdr.udp.dstPort == UDP_PORT && 
                    hdr.ipv4.dstAddr == 0x0A000002) {
                    // QoS -1
                    if (hdr.mqttsn_flags_publish.qos == FLAGS_QOS_LEVEL_MINUS1 &&
                        hdr.mqttsn_publish.msgId == 0x0000) {
                        static_forwarding.apply();
                    }
                    // QoS 0
                    else if (hdr.mqttsn_flags_publish.qos == FLAGS_QOS_LEVEL_0) {
                         // msgId pode ser 0x0000 ou diferente
                        static_forwarding.apply();
                    }
                    // QoS 1 ou 2
                    else if ((hdr.mqttsn_flags_publish.qos == FLAGS_QOS_LEVEL_1 ||
                        hdr.mqttsn_flags_publish.qos == FLAGS_QOS_LEVEL_2) &&
                        hdr.mqttsn_publish.msgId != 0x0000) {
                            static_forwarding.apply();
                    }
                }
                // -------- Gateway -> Subscriber --------
                else if ((hdr.udp.srcPort == UDP_PORT && 
                    hdr.ipv4.srcAddr == 0x0A000002)) {
                        // Encaminhar sempre, já que o gateway cuidou do QoS
                        static_forwarding.apply();
                }
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_PUBACK && // só há para qos = 1
                hdr.mqttsn_puback.isValid()) {
                    static_forwarding.apply(); // Essa mensagem pode vir de qualquer cliente pub/sub ou do gateway
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_PUBREC && // só há para qos = 2
                hdr.mqttsn_pubrec.isValid()) {
                if (hdr.udp.srcPort == UDP_PORT &&    // porta 1884
                    hdr.ipv4.srcAddr == 0x0A000002) { // gateway 10.0.0.2
                        static_forwarding.apply();
                }
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_PUBREL && // só há para qos = 2
                hdr.mqttsn_pubrel.isValid()) {
                if (hdr.udp.dstPort == UDP_PORT &&    // porta 1884
                    hdr.ipv4.dstAddr == 0x0A000002) { // gateway 10.0.0.2
                        static_forwarding.apply();
                }
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_PUBCOMP && // só há para qos = 2
                hdr.mqttsn_pubcomp.isValid()) {
                if (hdr.udp.srcPort == UDP_PORT &&    // porta 1884
                    hdr.ipv4.srcAddr == 0x0A000002) { // gateway 10.0.0.2
                        static_forwarding.apply();
                }
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_DISCONNECT &&
                hdr.mqttsn_disconnect.isValid()) {
                    static_forwarding.apply(); // Essa mensagem pode vir de qualquer cliente pub/sub ou do gateway
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_PINGREQ &&
                hdr.mqttsn_pingreq.isValid()) {
                    static_forwarding.apply(); // Essa mensagem pode vir de qualquer cliente pub/sub ou do gateway
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_PINGRESP &&
                hdr.mqttsn_pingresp.isValid()) {
                    static_forwarding.apply(); // Essa mensagem pode vir de qualquer cliente pub/sub ou do gateway
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_SUBSCRIBE && // qos = -1 not implemented, only relevant within PUBLISH messages sent by a client
                hdr.mqttsn_flags_subscribe.isValid() &&
                hdr.mqttsn_subscribe.isValid()) {
                if ((hdr.mqttsn_flags_subscribe.topicIdType == TOPICIDTYPE_TOPICNAME ||
                    hdr.mqttsn_flags_subscribe.topicIdType == TOPICIDTYPE_SHORTTOPICNAME) &&
                    (hdr.mqttsn_flags_subscribe.qos == FLAGS_QOS_LEVEL_0 || // para qos = 0, 1 e 2
                    hdr.mqttsn_flags_subscribe.qos == FLAGS_QOS_LEVEL_1 ||
                    hdr.mqttsn_flags_subscribe.qos == FLAGS_QOS_LEVEL_2) && 
                    hdr.udp.dstPort == UDP_PORT &&    // porta 1884
                    hdr.ipv4.dstAddr == 0x0A000002) { // gateway 10.0.0.2
                        static_forwarding.apply();
                }
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_SUBACK &&
                hdr.mqttsn_flags_suback.isValid() &&
                hdr.mqttsn_suback.isValid()) {
                if (hdr.mqttsn_suback.msgId == 0x0000 && // If the client subscribes to a topic name which contains a wildcard character, the returning SUBACK message will contain the topic id value 0x0000
                    hdr.udp.srcPort == UDP_PORT &&    // porta 1884
                    hdr.ipv4.srcAddr == 0x0A000002) { // gateway 10.0.0.2
                        static_forwarding.apply();
                }
                else if ((hdr.mqttsn_flags_suback.qos == FLAGS_QOS_LEVEL_0 ||
                    hdr.mqttsn_flags_suback.qos == FLAGS_QOS_LEVEL_1 ||
                    hdr.mqttsn_flags_suback.qos == FLAGS_QOS_LEVEL_2) && 
                    hdr.mqttsn_suback.msgId != 0x0000 &&  // para qos = 0, 1 e 2
                    hdr.udp.srcPort == UDP_PORT &&    // porta 1884
                    hdr.ipv4.srcAddr == 0x0A000002) { // gateway 10.0.0.2
                        static_forwarding.apply();
                }
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_UNSUBSCRIBE &&
                hdr.mqttsn_flags_unsubscribe.isValid() && 
                hdr.mqttsn_unsubscribe.isValid()) {
                if ((hdr.mqttsn_flags_unsubscribe.topicIdType == TOPICIDTYPE_TOPICNAME ||
                    hdr.mqttsn_flags_unsubscribe.topicIdType == TOPICIDTYPE_SHORTTOPICNAME) && 
                    hdr.udp.dstPort == UDP_PORT &&    // porta 1884
                    hdr.ipv4.dstAddr == 0x0A000002) { // gateway 10.0.0.2
                        static_forwarding.apply();
                }
            }
            else if (hdr.mqttsn_fixed.msgType == MQTTSN_UNSUBACK &&
                hdr.mqttsn_unsuback.isValid()) {
                if (hdr.udp.srcPort == UDP_PORT &&    // porta 1884
                    hdr.ipv4.srcAddr == 0x0A000002) { // gateway 10.0.0.2
                        static_forwarding.apply();
                }
            }
            else { // Se não for nenhuma das mensagens conhecidas pelo ingress do switch, drop
                drop();
            }
        }
        else { // Se a parte fixa da mensagem mqttsn não for válida, drop
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
        packet.emit(hdr.mqttsn_flags_connect);
        packet.emit(hdr.mqttsn_connect);
        packet.emit(hdr.mqttsn_connack);
        packet.emit(hdr.mqttsn_register);
        packet.emit(hdr.mqttsn_regack);
        packet.emit(hdr.mqttsn_flags_publish);
        packet.emit(hdr.mqttsn_publish);
        packet.emit(hdr.mqttsn_puback);
        packet.emit(hdr.mqttsn_pubrec);
        packet.emit(hdr.mqttsn_pubrel);
        packet.emit(hdr.mqttsn_pubcomp);
        packet.emit(hdr.mqttsn_disconnect);
        packet.emit(hdr.mqttsn_pingreq);
        packet.emit(hdr.mqttsn_pingresp);
        packet.emit(hdr.mqttsn_flags_subscribe);
        packet.emit(hdr.mqttsn_subscribe);
        packet.emit(hdr.mqttsn_flags_suback);
        packet.emit(hdr.mqttsn_suback);
        packet.emit(hdr.mqttsn_flags_unsubscribe);
        packet.emit(hdr.mqttsn_unsubscribe);
        packet.emit(hdr.mqttsn_unsuback);
        packet.emit(hdr.mqttsn_variable_field);
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

// mqtt-sn-pub -dddddddddd -q 0 -h 10.0.0.2 -p 1884 -t "teste" -m "teste"
// mqtt-sn-sub -dddddddddd -q 0 -h 10.0.0.2 -p 1884 -t "teste" -v &

// mqtt-sn-pub -dddddddddd -q 1 -h 10.0.0.2 -p 1884 -t "teste" -m "teste"
// mqtt-sn-sub -dddddddddd -q 1 -h 10.0.0.2 -p 1884 -t "teste" -v &

// mqtt-sn-pub -dddddddddd -q -1 -h 10.0.0.2 -p 1884 -t "ta" -m "teste"

// docker stop p4c
// docker stop mn.s1 mn.ss1 mn.pb1 mn.gw mn.bk
// docker rm mn.s1 mn.ss1 mn.pb1 mn.gw mn.bk