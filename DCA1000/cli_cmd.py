import subprocess
import os, time
from Utils.logging import Logger


class DCA1000Cli:
    def __init__(self, config_file="DCA1000/CLI/configFile.json", log_dir="Log"):
        self.cli_control = os.path.join(os.getcwd(), "DCA1000/CLI/DCA1000EVM_CLI_Control")
        self.config = os.path.join(os.getcwd(), config_file)
        self.log = Logger("DCA1000EVM_CLI_Ethernet", log_dir).logger

    def configFpga(self):
        result = subprocess.Popen(
            self.cli_control + " fpga " + self.config,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
        )
        output, error = result.communicate()

        self.log.debug(output)
        if error:
            self.log.error(error)

    def configEeprom(self):
        result = subprocess.Popen(
            self.cli_control + " eeprom " + self.config,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
        )
        output, error = result.communicate()

        self.log.debug(output)
        if error:
            self.log.error(error)

    def resetFpga(self):
        result = subprocess.Popen(
            self.cli_control + " reset_fpga " + self.config,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
        )
        output, error = result.communicate()

        self.log.debug(output)
        if error:
            self.log.error(error)

    def resetArDevice(self):
        result = subprocess.Popen(
            self.cli_control + " reset_ar_device " + self.config,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
        )
        output, error = result.communicate()

        self.log.debug(output)
        if error:
            self.log.error(error)

    def startRecord(self):
        result = subprocess.Popen(
            self.cli_control + " start_record " + self.config,
            cwd=os.path.join(os.getcwd(), "DCA1000/CLI"),
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
        )
        output, error = result.communicate()
        self.record_process = result

        self.log.debug(output)
        if error:
            self.log.error(error)
        else:
            print("Record Started")

    def stopRecord(self):
        result = subprocess.Popen(
            self.cli_control + " stop_record " + self.config,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
        )
        output, error = result.communicate()

        self.log.debug(output)
        if error:
            self.log.error(error)
        else:
            print("Record Ended")

    def configRecordDelay(self):
        result = subprocess.Popen(
            self.cli_control + " record " + self.config,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
        )
        output, error = result.communicate()

        self.log.debug(output)
        if error:
            self.log.error(error)

    def getDllVersion(self):
        result = subprocess.Popen(
            self.cli_control + " dll_version " + self.config,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
        )
        output, error = result.communicate()

        self.log.debug(output)
        if error:
            self.log.error(error)

    def getFpgaVersion(self):
        result = subprocess.Popen(
            self.cli_control + " fpga_version " + self.config,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
        )
        output, error = result.communicate()

        self.log.debug(output)
        if error:
            self.log.error(error)

    def getCliVersion(self):
        result = subprocess.Popen(
            self.cli_control + " cli_version " + self.config,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
        )
        output, error = result.communicate()

        self.log.debug(output)
        if error:
            self.log.error(error)

    def queryStatus(self):
        result = subprocess.Popen(
            self.cli_control + " query_status " + self.config,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
        )
        output, error = result.communicate()

        self.log.debug(output)
        if error:
            self.log.error(error)

    def querySysStatus(self):
        result = subprocess.Popen(
            self.cli_control + " query_sys_status " + self.config,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
        )
        output, error = result.communicate()

        self.log.debug(output)
        if error:
            self.log.error(error)

    def help(self):
        result = subprocess.Popen(
            self.cli_control + " -h " + self.config,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
        )
        output, error = result.communicate()

        self.log.debug(output)
        if error:
            self.log.error(error)

    def initialize(self):
        # get version
        self.getDllVersion()
        self.getCliVersion()

        # config
        self.resetArDevice()
        self.resetFpga()
        self.configFpga()
        self.configEeprom()
        self.configRecordDelay()

        time.sleep(0.2)

    def closeControl(self, record_port):
        # kill shell
        x = os.popen(f"lsof -t -i:{record_port}").read().strip()
        if x:
            os.system(f"sudo kill -9 {x}")
            print(f"pid: {x} killed. mmWave cli control closed successfully!")
