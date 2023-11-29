import time
import serial
import serial.tools.list_ports
import os
from Utils.logging import Logger


class iwr6843_serial():
    
    def __init__(self, configFile = "xWR6843/config/xwr6843.cfg", 
                 cfgPort = "/dev/ttyUSB0", dataPort = "/dev/ttyUSB1", logDir = "Log"):
        self.log = Logger("serial", logDir).logger
        self.config = configFile
        self.cfgPort = cfgPort
        self.dataPort = dataPort
        self.cfgPort_obj = None
        self.dataPort_obj = None


    def get_cfg_port(self):
        return self.cfgPort_obj


    def get_data_port(self):
        return self.dataPort_obj


    def serial_open(self):
        # support check serial port
        self._serial_check_port()

        # Open the serial ports for the configuration and the data ports
        try:
            # CLI port cannot have timeout because the stream is user-programmed
            self.cfgPort_obj = serial.Serial(self.cfgPort, 115200, parity=serial.PARITY_NONE,
                                              stopbits=serial.STOPBITS_ONE,timeout=0.3)
            if(not self.cfgPort_obj.isOpen()):
                self.log.error("Cfg port is not open: {}".format(self.cfgPort))

            self.dataPort_obj = serial.Serial(self.dataPort, 921600, parity=serial.PARITY_NONE,
                                              stopbits=serial.STOPBITS_ONE, timeout=0.025)
            if(not self.dataPort_obj.isOpen()):
                 self.log.error("Data Port is not open: {}}".format(self.dataPort))

        except serial.SerialException as se:
            self.serial_close()
            raise Exception('Serial Port Occupied, error = ' + str(se))

        # Read the configuration file and send it to the board
        config = [line.rstrip('\r\n') for line in open(self.config)]
        print("waiting for config for several seconds...")
        for line in config:
            if not line.startswith('%'):
                self.cfgPort_obj.write((line + '\r').encode())
                time.sleep(0.2)
        cli_result = self.cfgPort_obj.read(self.cfgPort_obj.in_waiting).decode()
        self.log.debug(cli_result)  # CLI output of the board

        time.sleep(3)


    def serial_close(self):
        self.cfgPort_obj.close()
        self.dataPort_obj.close()


    def serial_clear_buffer(self):
        self.cfgPort_obj.reset_input_buffer()
        self.cfgPort_obj.reset_output_buffer()
        self.dataPort_obj.reset_input_buffer()
        self.dataPort_obj.reset_output_buffer()
        

    def sensor_start(self):
        self.cfgPort_obj.write(('sensorStart \n').encode())
        time.sleep(0.5)
        result = self.cfgPort_obj.read(self.cfgPort_obj.in_waiting).decode()
        self.log.debug(result)


    def sensor_stop(self):
        self.cfgPort_obj.write(('sensorStop \n').encode())
        time.sleep(0.5)
        result = self.cfgPort_obj.read(self.cfgPort_obj.in_waiting).decode()
        self.log.debug(result)


    def sensor_initialize(self):
        self.serial_open()
        self.serial_clear_buffer()
        

    def _serial_check_port(self):
        port_list = list(serial.tools.list_ports.comports())
        for com in port_list:
            des = com.description
            if -1 != des.rfind("Enhanced", 0, len(com.description) - len('Enhanced')):
                # com is not config port
                if self.cfgPort != com.device:
                    self.log.error("Please Check xWR6843 Cfg Port is: " + com.device)

            if -1 != des.rfind("Standard", 0, len(com.description) - len('Standard')):
                # com is not data port
                if self.dataPort != com.device:
                    self.log.error("Please Check xWR6843 Data Port is: " + com.device)