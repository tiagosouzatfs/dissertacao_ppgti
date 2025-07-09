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
/*const bit<8> reserved = 0x03;*/
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
/*const bit<8> reserved = 0x11;*/
const bit<8> MQTTSN_SUBSCRIBE = 0x12;
const bit<8> MQTTSN_SUBACK = 0x13;
const bit<8> MQTTSN_UNSUBSCRIBE = 0x14;
const bit<8> MQTTSN_UNSUBACK = 0x15;
const bit<8> MQTTSN_PINGREQ = 0x16;
const bit<8> MQTTSN_PINGRESP = 0x17;
const bit<8> MQTTSN_DISCONNECT = 0x18;
/*const bit<8> reserved = 0x19;*/
const bit<8> MQTTSN_WILLTOPICUPD = 0x1A;
const bit<8> MQTTSN_WILLTOPICRESP = 0x1B;
const bit<8> MQTTSN_WILLMSGUPD = 0x1C;
const bit<8> MQTTSN_WILLMSGRESP = 0x1D;
/*const bit<8> reserved = 0x1E-0xFD;*/
/*const bit<8> Encapsulated message = 0xFE;*/
/*const bit<8> reserved = 0xFF;*/

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

/*Message MQTT-SN*/
header MQTTSN_fixed_h {
    bit<8>      lenght;
    bit<8>      msgType;
}

header MQTTSN_variable_h {
    bit<>      clientId; /*has a variable length*/
    bit<>      data; /*has a variable length*/
    bit<16>    duration;
    bit<8>     flags; /*to create fake header? there are a lot flags*/
    bit<>      gwAdd; /*has a variable length*/
    bit<8>     gwId;
    bit<16>    msgId;
    bit<8>     protocolId;
    bit<8>     radius;
    bit<8>     returnCode;
    bit<16>    topicId;
    bit<>      topicName; /*has a variable length*/
    bit<>      willMsg; /*has a variable length*/
    bit<>      willTopic; /*has a variable length*/
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