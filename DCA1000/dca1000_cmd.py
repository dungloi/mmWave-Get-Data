import subprocess
import os, signal
from Utils.logging import Logger


class dca1000_ethernet():
    
    def __init__(self, configFile = "DCA1000/CLI/configFile.json", logDir = "Log"):
        self.ws_path = os.getcwd()
        
        self.cli_path = os.path.join(self.ws_path, "DCA1000/CLI")                         
        self.cli_control = os.path.join(self.ws_path, "DCA1000/CLI/DCA1000EVM_CLI_Control")
        self.config = os.path.join(self.ws_path, configFile) 
        
        self.log = Logger("DCA1000EVM_CLI_Ethernet", logDir).logger


    def config_fpga(self):
        result = subprocess.Popen(self.cli_control + " fpga " + self.config,
                                stdin=subprocess.PIPE,
                                stderr=subprocess.PIPE, 
                                stdout=subprocess.PIPE, 
                                universal_newlines=True,
                                shell=True)
        output, error = result.communicate()
        
        self.log.debug(output)
        if error:
            self.log.error(error)

        
    def config_eeprom(self):
        result = subprocess.Popen(self.cli_control + " eeprom " + self.config,
                                stdin=subprocess.PIPE,
                                stderr=subprocess.PIPE, 
                                stdout=subprocess.PIPE, 
                                universal_newlines=True,
                                shell=True)
        output, error = result.communicate()
        
        self.log.debug(output)
        if error:
            self.log.error(error)
            
            
    def reset_fpga(self):
        result = subprocess.Popen(self.cli_control + " reset_fpga " + self.config,
                                stdin=subprocess.PIPE,
                                stderr=subprocess.PIPE, 
                                stdout=subprocess.PIPE, 
                                universal_newlines=True,
                                shell=True)
        output, error = result.communicate()
        
        self.log.debug(output)
        if error:
            self.log.error(error)
        
              
    def reset_ar_device(self):
        result = subprocess.Popen(self.cli_control + " reset_ar_device " + self.config,
                                stdin=subprocess.PIPE,
                                stderr=subprocess.PIPE, 
                                stdout=subprocess.PIPE, 
                                universal_newlines=True,
                                shell=True)
        output, error = result.communicate()
        
        self.log.debug(output)
        if error:
            self.log.error(error)
            
            
    def start_record(self):
        os.chdir(self.cli_path)
        
        result = subprocess.Popen(self.cli_control + " start_record " + self.config,
                                stdin=subprocess.PIPE,
                                stderr=subprocess.PIPE, 
                                stdout=subprocess.PIPE, 
                                universal_newlines=True,
                                shell=True)
        output, error = result.communicate()
        self.record_process = result
        
        # self.log.debug(output)
        if error:
            self.log.error(error)
        else:
            print("Record Started")
            
        os.chdir(self.ws_path)
            
            
    def stop_record(self):
        os.chdir(self.cli_path)
        
        result = subprocess.Popen(self.cli_control + " stop_record " + self.config,
                                stdin=subprocess.PIPE,
                                stderr=subprocess.PIPE, 
                                stdout=subprocess.PIPE, 
                                universal_newlines=True,
                                shell=True)
        output, error = result.communicate()
        
        # self.log.debug(output)
        if error:
            self.log.error(error)
        else:
            print("Record Ended")
            
        self.record_process.send_signal(signal.SIGKILL)
        self.record_process = None
            
        os.chdir(self.ws_path)
        
            
    def config_record_delay(self):
        result = subprocess.Popen(self.cli_control + " record " + self.config,
                                stdin=subprocess.PIPE,
                                stderr=subprocess.PIPE, 
                                stdout=subprocess.PIPE, 
                                universal_newlines=True,
                                shell=True)
        output, error = result.communicate()
        
        self.log.debug(output)
        if error:
            self.log.error(error)
            
            
    def get_dll_version(self):
        result = subprocess.Popen(self.cli_control + " dll_version " + self.config,
                                stdin=subprocess.PIPE,
                                stderr=subprocess.PIPE, 
                                stdout=subprocess.PIPE, 
                                universal_newlines=True,
                                shell=True)
        output, error = result.communicate()
        
        self.log.debug(output)
        if error:
            self.log.error(error)
            
            
    def get_fpga_version(self):
        result = subprocess.Popen(self.cli_control + " fpga_version " + self.config,
                                stdin=subprocess.PIPE,
                                stderr=subprocess.PIPE, 
                                stdout=subprocess.PIPE, 
                                universal_newlines=True,
                                shell=True)
        output, error = result.communicate()
        
        self.log.debug(output)
        if error:
            self.log.error(error)
            
            
    def get_cli_version(self):
        result = subprocess.Popen(self.cli_control + " cli_version " + self.config,
                                stdin=subprocess.PIPE,
                                stderr=subprocess.PIPE, 
                                stdout=subprocess.PIPE, 
                                universal_newlines=True,
                                shell=True)
        output, error = result.communicate()
        
        self.log.debug(output)
        if error:
            self.log.error(error)
            
            
    def query_status(self):
        result = subprocess.Popen(self.cli_control + " query_status " + self.config,
                                stdin=subprocess.PIPE,
                                stderr=subprocess.PIPE, 
                                stdout=subprocess.PIPE, 
                                universal_newlines=True,
                                shell=True)
        output, error = result.communicate()
        
        self.log.debug(output)
        if error:
            self.log.error(error)
            
            
    def query_sys_status(self):
        result = subprocess.Popen(self.cli_control + " query_sys_status " + self.config,
                                stdin=subprocess.PIPE,
                                stderr=subprocess.PIPE, 
                                stdout=subprocess.PIPE, 
                                universal_newlines=True,
                                shell=True)
        output, error = result.communicate()
        
        self.log.debug(output)
        if error:
            self.log.error(error)
            

    def help(self):
        result = subprocess.Popen(self.cli_control + " -h " + self.config,
                                stdin=subprocess.PIPE,
                                stderr=subprocess.PIPE, 
                                stdout=subprocess.PIPE, 
                                universal_newlines=True,
                                shell=True)
        output, error = result.communicate()
        
        self.log.debug(output)
        if error:
            self.log.error(error)
            
            
    def initialize(self):
        # config
        self.config_fpga()
        self.config_record_delay()
        # self.config_eeprom()

        # get version
        self.get_dll_version()
        self.get_fpga_version()
        self.get_cli_version()
        
        
    def reset(self):
        # config
        self.reset_fpga()
        self.reset_ar_device()
        self.config_fpga()
        self.config_record_delay()
        
        # get version
        self.get_dll_version()
        self.get_fpga_version()
        self.get_cli_version()
