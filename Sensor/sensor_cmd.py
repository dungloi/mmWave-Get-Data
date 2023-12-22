import time
import serial
import serial.tools.list_ports
from Utils.logging import Logger


class SensorSerial:
    def __init__(
        self,
        configFile="Sensor/config/default.cfg",
        cfg_port="/dev/ttyUSB0",
        data_port="/dev/ttyUSB1",
        log_dir="Log",
    ):
        self.log = Logger("serial", log_dir).logger
        self.config = configFile
        self.cfg_port = cfg_port
        self.data_port = data_port
        self.cfg_port_obj = None
        self.data_port_obj = None

    def getCfgPort(self):
        return self.cfg_port_obj

    def getDataPort(self):
        return self.data_port_obj

    def serialOpen(self):
        # support check serial port
        self._SerialCheckPort()

        # Open the serial ports for the configuration and the data ports
        try:
            # CLI port cannot have timeout because the stream is user-programmed
            self.cfg_port_obj = serial.Serial(
                self.cfg_port,
                115200,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.2,
            )
            if not self.cfg_port_obj.isOpen():
                self.log.error("Cfg port is not open: {}".format(self.cfg_port))

            self.data_port_obj = serial.Serial(
                self.data_port,
                921600,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.025,
            )
            if not self.data_port_obj.isOpen():
                self.log.error("Data Port is not open: {}}".format(self.data_port))

        except serial.SerialException as se:
            self.serial_close()
            raise Exception("Serial Port Occupied, error = " + str(se))

        # Read the configuration file and send it to the board
        config = [line.rstrip("\r\n") for line in open(self.config)]
        print("waiting for config for several seconds...")
        for line in config:
            if not line.startswith("%"):
                self.cfg_port_obj.write((line + "\r").encode())
                time.sleep(0.1)
        cli_result = self.cfg_port_obj.read(self.cfg_port_obj.in_waiting).decode(errors="replace")
        self.log.debug(cli_result)  # CLI output of the board

    def serialClose(self):
        self.cfg_port_obj.close()
        self.data_port_obj.close()

    def serialClearBuffer(self):
        self.cfg_port_obj.reset_input_buffer()
        self.cfg_port_obj.reset_output_buffer()
        self.data_port_obj.reset_input_buffer()
        self.data_port_obj.reset_output_buffer()

    def sensorStart(self):
        self.cfg_port_obj.write(("sensorStart \n").encode())
        result = self.cfg_port_obj.read(self.cfg_port_obj.in_waiting).decode()
        self.log.debug(result)
        time.sleep(0.1)

    def sensorStop(self):
        self.cfg_port_obj.write(("sensorStop \n").encode())
        result = self.cfg_port_obj.read(self.cfg_port_obj.in_waiting).decode()
        self.log.debug(result)
        time.sleep(0.1)

    def sensorInitialize(self):
        self.serialOpen()
        self.serialClearBuffer()

    def _SerialCheckPort(self):
        port_list = list(serial.tools.list_ports.comports())
        for com in port_list:
            des = com.description
            if -1 != des.rfind("Enhanced", 0, len(com.description) - len("Enhanced")):
                # com is not config port
                if self.cfg_port != com.device:
                    self.log.error("Please Check xWR Cfg Port is: " + com.device)

            if -1 != des.rfind("Standard", 0, len(com.description) - len("Standard")):
                # com is not data port
                if self.data_port != com.device:
                    self.log.error("Please Check xWR Data Port is: " + com.device)
