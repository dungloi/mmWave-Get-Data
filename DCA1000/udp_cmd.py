import struct
import os, time
import socket
import Utils.logging

# CMD format: Header(2) CommandCode(2) DataSize(2) Data(0 - 504) Footer(2)
UDP_CMD = {
    "HEADER": 0xA55A,
    "FOOTER": 0xEEAA,
    "RECORD_START": 0x05,
    "RECORD_STOP": 0x06,
}

MAX_PACKET_SIZE = 1466  # 4 + 6 + 1456, error in "DCA1000EVM Data Capture Card User Guide"
MAX_PACKET_DATA_SIZE = MAX_PACKET_SIZE - 10


class DCA1000Udp:
    def __init__(self, local_ip, address_ip, udp_cfg_port, udp_data_port, data_path, timeout_s):
        self.LOCAL_IP = local_ip
        self.ADDR_IP = address_ip
        self.CFG_PORT = udp_cfg_port
        self.DTA_PORT = udp_data_port
        self.data_path = data_path
        self.f_udp = None
        self.data_bytes_cnt = 0
        self.timeout_s = timeout_s
        self.last_seq_num = 0
        # cmd
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind((self.LOCAL_IP, self.CFG_PORT))
        # data
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client.bind((self.LOCAL_IP, self.DTA_PORT))
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, MAX_PACKET_SIZE * 10 * 6000)
        self.client.settimeout(self.timeout_s)

    def _paddingLostPackets(self, last_seq_num, curr_seq_num):
        zero_padding_len = (curr_seq_num - last_seq_num - 1) * MAX_PACKET_DATA_SIZE
        self.f_udp.write(b"\x00" * zero_padding_len)

    def writeTimestamp(self, seq_num, ts):
        f_ts = open(self.data_path + "_ts.txt", "at")
        info = f"packet {seq_num} time stamp: {str(ts)}"
        f_ts.write(info + "\n")
        if Utils.logging.DEBUG_ON:
            print(info)

    def rcvOnePacket(self):
        try:
            udp_packet, _ = self.client.recvfrom(MAX_PACKET_SIZE)

            # DATA format: SequenceNum(4) ByteCnt(6) RawData(48 - 1462)
            seq_num = int.from_bytes(udp_packet[0:4], byteorder="little")
            bytes_cnt = int.from_bytes(udp_packet[4:10], byteorder="little")
            raw_data = udp_packet[10:]
            self.data_bytes_cnt = bytes_cnt
            self.writeTimestamp(seq_num, time.time())
            return seq_num, raw_data

        except Exception as e:
            if isinstance(e, socket.timeout):
                print(f"No LVDS data in transmission for {self.timeout_s} seconds")
                return 0, None
            else:
                print(f"error: {e}")

    def isToBreak(self, start_ts, stop_mode, stop_mode_param):
        # break when time is up (duration or infinite mode)
        # or when data meets the required length (bytes mode)
        return (stop_mode == "bytes" and self.data_bytes_cnt > stop_mode_param) or (
            (stop_mode == "infinite" or stop_mode == "duration") and time.time() - start_ts > stop_mode_param + 0.01
        )  # a little delay for complete frames

    def handleOneFramePackets(self) -> int:
        with open(self.data_path + "_raw_udp_packets.bin", "ab") as file:
            self.f_udp = file
            while True:  # until finish one frame
                try:
                    seq_num, raw_data = self._rcvOnePacket()
                    if not seq_num:
                        raise TimeoutError("Device timeout. Frame ended")
                    elif seq_num != self.last_seq_num + 1:
                        # padding when packets get lost
                        print(
                            f"{seq_num - self.last_seq_num - 1} packets lost from {self.last_seq_num + 1} to {seq_num - 1}, padded with 0x00"
                        )
                        self._paddingLostPackets(self.last_seq_num, seq_num)
                    # save data to .bin
                    self.f_udp.write(raw_data)
                    self.last_seq_num = seq_num
                except Exception as e:
                    print(f"{e}")
                    break

    def handlePackets(self, start_ts, stop_mode, stop_mode_param):
        last_seq_num = 0
        with open(self.data_path + "_raw_udp_packets.bin", "wb") as file:
            self.f_udp = file
            # clear ts file
            _ = open(self.data_path + "_ts.txt", "wt")
            while True:  # until the time to break or enough bytes
                try:
                    if self.isToBreak(start_ts, stop_mode, stop_mode_param):
                        break

                    seq_num, raw_data = self.rcvOnePacket()
                    if not seq_num:
                        raise TimeoutError("Device timeout!! Record ended")
                    elif seq_num != last_seq_num + 1:
                        # padding when packets get lost
                        print(
                            f"{seq_num - last_seq_num - 1} packets lost from {last_seq_num + 1} to {seq_num - 1}, padded with 0x00"
                        )
                        self._paddingLostPackets(last_seq_num, seq_num)
                    # save data to .bin
                    self.f_udp.write(raw_data)
                    last_seq_num = seq_num

                except Exception as e:
                    print(f"{e}")
                    break

    def startRecord(self):
        cmd = struct.pack("<HHHH", UDP_CMD["HEADER"], UDP_CMD["RECORD_START"], 0, UDP_CMD["FOOTER"])
        if Utils.logging.DEBUG_ON:
            print("Record start cmd to send:", str(cmd))
        self.server.sendto(cmd, (self.ADDR_IP, self.CFG_PORT))

    def stopRecord(self):
        cmd = struct.pack("<HHHH", UDP_CMD["HEADER"], UDP_CMD["RECORD_STOP"], 0, UDP_CMD["FOOTER"])
        if Utils.logging.DEBUG_ON:
            print("Record stop cmd to send:", str(cmd))
        self.server.sendto(cmd, (self.ADDR_IP, self.CFG_PORT))

    def __del__(self):
        self.client.close()
        self.server.close()
