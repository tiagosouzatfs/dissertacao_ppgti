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
const bit<8> MQTTSN_MQTTSN_WILLMSG = 0x09;
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

/*Message MQTT-SN fixed header*/
header MQTTSN_fixed_h {
    bit<8>      lenght;
    bit<8>      msgType;
}

/*Message MQTT-SN variable header ADVERTISE*/
header MQTTSN_advertise_h {
    bit<8>     gwId;
    bit<16>    duration;
}

/*Message MQTT-SN variable header SEARCHGW*/
header MQTTSN_searchgw_h {
    bit<8>     radius;
}

/*Message MQTT-SN variable header GWINFO*/
header MQTTSN_gwinfo_h {
    bit<8>     gwId;
    bit<16>    gwAdd; // TODO: how to do variable length in P4? // IPv4 address (only present if message is sent by a client)
}

/*Message MQTT-SN variable header CONNECT*/
header MQTTSN_connect_h {
    bit<8>     flags;
    bit<8>     protocolId;
    bit<16>    duration;
    bit<16>    clientId; // TODO: how to do variable length in P4?
}

/*Message MQTT-SN variable header CONNACK*/
header MQTTSN_connack_h {
    bit<8>     returnCode;
}

/*Message MQTT-SN variable header WILLTOPICREQ*/
header MQTTSN_willtopicreq_h {
    /* empty */
}

/*Message MQTT-SN variable header WILLTOPIC*/
header MQTTSN_willtopic_h {
    bit<8>     flags;
    bit<8>     willTopic; // TODO: how to do variable length in P4?
}

/*Message MQTT-SN variable header WILLMSGREQ*/
header MQTTSN_willmsgreq_h {
    /* empty */
}

/*Message MQTT-SN variable header WILLMSG*/
header MQTTSN_willmsg_h {
    bit<8>     willMsg; // TODO: how to do variable length in P4?
}

/*Message MQTT-SN variable header REGISTER*/
header MQTTSN_register_h {
    bit<16>    topicId;
    bit<16>    msgId;
    bit<8>     topicName; // TODO: how to do variable length in P4?
}

/*Message MQTT-SN variable header REGACK*/
header MQTTSN_regack_h {
    bit<16>    topicId;
    bit<16>    msgId;
    bit<8>     returnCode;
}

/*Message MQTT-SN variable header PUBLISH*/
header MQTTSN_publish_h {
    bit<8>     flags;
    bit<16>    topicId;
    bit<16>    msgId;
    bit<8>     data; // TODO: how to do variable length in P4?
}

/*Message MQTT-SN variable header PUBACK*/
header MQTTSN_puback_h {
    bit<16>    topicId;
    bit<16>    msgId;
    bit<8>     returnCode;
}

/*Message MQTT-SN variable header PUBREC*/
header MQTTSN_pubrec_h {
    bit<16>    msgId;
}

/*Message MQTT-SN variable header PUBREL*/
header MQTTSN_pubrel_h {
    bit<16>    msgId;
}

/*Message MQTT-SN variable header PUBCOMP*/
header MQTTSN_pubcomp_h {
    bit<16>    msgId;
}

/*Message MQTT-SN variable header SUBSCRIBE*/
header MQTTSN_subscribe_h {
    bit<8>     flags;
    bit<16>    msgId;
    bit<16>    topicId; 
    // or bit<8>     topicName; // TODO: how to do variable length in P4?
}

/*Message MQTT-SN variable header SUBACK*/
header MQTTSN_suback_h {
    bit<8>     flags;
    bit<16>    topicId;
    bit<16>    msgId;
    bit<8>     returnCode;
}

/*Message MQTT-SN variable header UNSUBSCRIBE*/
header MQTTSN_unsubscribe_h {
    bit<8>     flags;
    bit<16>    msgId;
    bit<16>    topicId;
    // or bit<8>     topicName; // TODO: how to do variable length in P4?
}

/*Message MQTT-SN variable header UNSUBACK*/
header MQTTSN_unsuback_h {
    bit<16>    msgId;
}

/*Message MQTT-SN variable header PINGREQ*/
header MQTTSN_pingreq_h {
    /* empty */
    //bit<8>    clientId; // optional // TODO: how to do variable length in P4?
}

/*Message MQTT-SN variable header PINGRESP*/
header MQTTSN_pingresp_h {  
    /* empty */
}

/*Message MQTT-SN variable header DISCONNECT*/
header MQTTSN_disconnect_h {
    /* empty */
    //bit<16>    duration; // optional
}

/*Message MQTT-SN variable header WILLTOPICUPD*/
header MQTTSN_willtopicupd_h {
    bit<8>     flags;
    bit<8>     willTopic; // TODO: how to do variable length in P4?
}

/*Message MQTT-SN variable header WILLMSGUPD*/
header MQTTSN_willmsgupd_h {
    bit<8>     willMsg; // TODO: how to do variable length in P4?
}

/*Message MQTT-SN variable header WILLTOPICRESP*/
header MQTTSN_willtopicresp_h {
    bit<8>     returnCode;
}

/*Message MQTT-SN variable header WILLMSGRESP*/
header MQTTSN_willmsgresp_h {
    bit<8>     returnCode;
}

/*Segment UDP*/
header UDP_h {
    bit<16>    srcPort;
    bit<16>    dstPort;
    bit<16>    lenght;
    bit<16>    checksum;
}

/*Packet IP*/
header IPv4_h {
    bit<4>     version;
    bit<4>     ihl;
    bit<8>     diffServ;
    bit<16>    totalLen;
    bit<16>    identification;
    bit<3>     flags;
    bit<13>    fragOffset;
    bit<8>     ttl;
    bit<8>     protocol;
    bit<16>    hdrChecksum;
    ipv4Addr   srcAddr;
    ipv4Addr   dstAddr;
}

/*Frame Ethernet*/
header Ethernet_h {
    macAddr    dstAddr;
    macAddr    srcAddr;
    bit<16>    ethertype;
}

struct headers {
    Ethernet_h ethernet;
    IPv4_h     ipv4;
    UDP_h      udp;
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
}

struct metadata {
    /* empty */
}

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {
    
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
    apply {  }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, 
                   in headers hdr) {
    apply {  }
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