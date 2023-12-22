import argparse
import subprocess, time, json, os
import numpy as np
import Utils.logging
from DCA1000.cli_cmd import DCA1000CLI
from Sensor import sensor_cmd
import Sensor.gen_cfg as gen_cfg


class RadarRecorder:
    def __init__(
        self,
        model,
        yaml_path,
        cfg_path,
        json_path,
        log_path,
        data_path,
        radar_sub_frame_enabled,
    ) -> None:
        self.MODEL = model
        self.yaml_path = yaml_path
        self.cfg_path = cfg_path
        self.json_path = json_path
        self.log_path = log_path
        self.data_path = data_path
        self.radar_sub_frame_enabled = radar_sub_frame_enabled

        os.makedirs(f"{self.log_path}", exist_ok=True)
        os.makedirs(f"{self.data_path}", exist_ok=True)

        # modify json
        with open(dca1000_config_json, "rt") as file:
            dca1000_json_data = json.load(file)
            dca1000_json_data["DCA1000Config"]["captureConfig"]["fileBasePath"] = os.path.join(
                os.getcwd(), f"{data_dir}"
            )
            self.capture_stop_mode = dca1000_json_data["DCA1000Config"]["captureConfig"]["captureStopMode"]
            self.ethernet_config_port = dca1000_json_data["DCA1000Config"]["ethernetConfig"]["DCA1000ConfigPort"]
            self.ethernet_data_port = dca1000_json_data["DCA1000Config"]["ethernetConfig"]["DCA1000DataPort"]
        with open(dca1000_config_json, "wt") as file:
            json.dump(dca1000_json_data, file, indent=4)

        # Configure USB Ports and grant device permissions
        if self.MODEL[3] == "1":
            self.port_type = "ACM"
        elif self.MODEL[3] == "6":
            self.port_type = "USB"
        self.CFG_PORT = f"/dev/tty{self.port_type}0"
        self.DTA_PORT = f"/dev/tty{self.port_type}1"
        permission_command = f"sudo chmod 777 {self.CFG_PORT} {self.DTA_PORT}"
        subprocess.run(permission_command, shell=True)

    def getDataCli(self, dca1000_inst: DCA1000CLI, record_duration):
        dca1000_inst.startRecord()
        print(f"duration: {record_duration} s")
        time.sleep(record_duration + 0.5)
        dca1000_inst.stopRecord()

        # kill shell
        x = os.popen(f"lsof -t -i:{self.ethernet_config_port}").read().strip()
        if x:
            os.system(f"sudo kill -9 {x}")
            print(f"pid: {x} killed. mmWave cli control closed successfully!")

    def getDataSocket():
        pass

    def record(self, cmd_mode, args):
        radar_cfg_inst = gen_cfg.gen_cfg(
            self.MODEL,
            self.yaml_path,
            self.cfg_path,
            self.radar_sub_frame_enabled,
        )
        # modify json
        with open(dca1000_config_json, "r") as file:
            dca1000_json_data = json.load(file)

        if getattr(args, "duration") is not None:
            record_duration = args.duration
            dca1000_json_data["DCA1000Config"]["captureConfig"]["captureStopMode"] = "duration"
            dca1000_json_data["DCA1000Config"]["captureConfig"]["durationToCapture_ms"] = int(record_duration * 1000)
        elif getattr(args, "bytes") is not None:
            record_frames = args.bytes / radar_cfg_inst.params["Bytes per frame"]
            record_duration = record_frames * float(radar_cfg_inst.config["frameCfg"].split(" ")[-3]) * 0.001
            dca1000_json_data["DCA1000Config"]["captureConfig"]["captureStopMode"] = "bytes"
            dca1000_json_data["DCA1000Config"]["captureConfig"]["bytesToCapture"] = int(args.bytes)
        else:
            dca1000_json_data["DCA1000Config"]["captureConfig"]["captureStopMode"] = "infinite"
            record_duration = DEFAULT_RECORD_DURATION
        with open(dca1000_config_json, "w") as file:
            json.dump(dca1000_json_data, file, indent=4)

        # config DCA1000EVM
        dca1000 = DCA1000CLI(dca1000_config_json, log_dir)
        dca1000.initialize()

        # config and start sensor
        sensor = sensor_cmd.SensorSerial(radar_config_file, self.CFG_PORT, self.DTA_PORT, log_dir)
        sensor.sensorInitialize()
        sensor.sensorStart()

        # ts
        with open(dca1000_config_json, "r") as file:
            dca1000_json_data = json.load(file)
        dca1000_json_data["DCA1000Config"]["captureConfig"]["filePrefix"] = time.time()
        with open(dca1000_config_json, "w") as new_file:
            json.dump(dca1000_json_data, new_file, indent=2)

        # start DCA1000 to record and stop after specified duration
        if cmd_mode == "CLI":
            self.getDataCli(dca1000, record_duration)
        elif cmd_mode == "SOCKET":
            self.getDataSocket()

        sensor.sensorStop()
        sensor.serialClose()

        print(f"\nIf tookits worked properly, the raw data was recorded in: ./{self.data_path}")


Utils.logging.DEBUG_ON = 1
DEFAULT_RECORD_DURATION = 1

if __name__ == "__main__":
    sensor_model = "AWR1843"
    dca1000_cmd_mode = "CLI"  # "SOCKET"

    # Recorder Config
    radar_config_yaml = "Sensor/config/radar_config.yml"
    radar_config_file = f"Sensor/config/{sensor_model}_custom.cfg"
    radar_sub_frame_enabled = 0
    dca1000_config_json = "DCA1000/config/configFile.json"
    log_dir = "Log"
    data_dir = "Data"

    radar_record_inst = RadarRecorder(
        sensor_model,
        radar_config_yaml,
        radar_config_file,
        dca1000_config_json,
        log_dir,
        data_dir,
        radar_sub_frame_enabled,
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--duration", type=float, help="Record duration in second", required=False)
    parser.add_argument("-b", "--bytes", type=float, help="Record bytes", required=False)
    parser.add_argument(
        "-i",
        "--infinite",
        type=float,
        help=f"Infinite recording mode with max duration {DEFAULT_RECORD_DURATION} s",
        required=False,
    )
    args = parser.parse_args()

    if all(value is None for value in vars(args).values()):
        parser.print_help()
        print("Set to default infinite record mode")

    radar_record_inst.record(dca1000_cmd_mode, args)
