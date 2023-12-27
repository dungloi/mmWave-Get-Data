import argparse
import subprocess, time, json, os
import Utils.logging
from DCA1000.cli_cmd import DCA1000Cli
from DCA1000.udp_cmd import DCA1000Udp
from Sensor.hardware_trigger import HardwareTrigger
from Sensor.sensor_cmd import SensorSerial
import Sensor.gen_cfg as gen_cfg
import threading


class RadarRecorder:
    def __init__(
        self, model, yaml_path, cfg_path, json_path, log_path, data_path, data_name_prefix, radar_sub_frame_enabled
    ) -> None:
        self.MODEL = model
        self.log_path = log_path
        self.json_path = json_path
        self.data_path = data_path
        self.radar_sub_frame_enabled = radar_sub_frame_enabled
        os.makedirs(f"{self.log_path}", exist_ok=True)
        os.makedirs(f"{self.data_path}", exist_ok=True)
        # modify json
        with open(json_path, "rt") as file:
            self.dca1000_json_data = json.load(file)
            self.dca1000_json_data["DCA1000Config"]["captureConfig"]["fileBasePath"] = os.path.join(
                os.getcwd(), f"{data_dir}"
            )
            self.dca1000_json_data["DCA1000Config"]["captureConfig"]["filePrefix"] = data_name_prefix
            self.capture_stop_mode = self.dca1000_json_data["DCA1000Config"]["captureConfig"]["captureStopMode"]
            self.ethernet_cfg_port = self.dca1000_json_data["DCA1000Config"]["ethernetConfig"]["DCA1000ConfigPort"]
            self.ethernet_dta_port = self.dca1000_json_data["DCA1000Config"]["ethernetConfig"]["DCA1000DataPort"]
            self.local_ip = self.dca1000_json_data["DCA1000Config"]["ethernetConfigUpdate"]["systemIPAddress"]
            self.dca1000_ip = self.dca1000_json_data["DCA1000Config"]["ethernetConfig"]["DCA1000IPAddress"]
        with open(json_path, "wt") as file:
            json.dump(self.dca1000_json_data, file, indent=4)

        # gen config (.cfg) and read trigger mode
        self.radar_cfg_obj = gen_cfg.gen_cfg(
            self.MODEL,
            yaml_path,
            cfg_path,
            self.radar_sub_frame_enabled,
        )
        self.sensor_trigger_mode = "SW" if int(self.radar_cfg_obj.config["frameCfg"].split(" ")[-2]) == 1 else "HW"
        self.frame_duration = float(self.radar_cfg_obj.config["frameCfg"].split(" ")[-3]) * 0.001

        # Configure USB Ports and grant device permissions
        if self.MODEL[3] == "1":
            self.serial_port_type = "ACM"
        elif self.MODEL[3] == "6":
            self.serial_port_type = "USB"
        self.serial_cfg_port = f"/dev/tty{self.serial_port_type}0"
        self.serial_dta_port = f"/dev/tty{self.serial_port_type}1"
        permission_command = f"sudo chmod 777 {self.serial_cfg_port} {self.serial_dta_port}"
        subprocess.run(permission_command, shell=True)

    def getDataCli(self, dca1000_cli_obj: DCA1000Cli, record_duration):
        dca1000_cli_obj.startRecord()

        print(f"duration: {record_duration} s")
        time.sleep(record_duration + 0.01)

        dca1000_cli_obj.stopRecord()

    def getDataSocket(self, stop_mode, stop_mode_param):
        timeout_duration_s = 0.1  # s
        dca1000_socket_obj = DCA1000Udp(
            self.local_ip,
            self.dca1000_ip,
            self.ethernet_cfg_port,
            self.ethernet_dta_port,
            os.path.join(self.data_path, data_name_prefix),
            timeout_duration_s,
        )
        dca1000_socket_obj.startRecord()

        if self.sensor_trigger_mode == "HW":
            dca1000_socket_obj.client.settimeout(0.001)  # one packet in a frame
            _ = open(dca1000_socket_obj.data_path + "_raw_udp_packets.bin", "wb")

            # set up hardware trigger thread
            hw_trigger_obj = HardwareTrigger(DCA1000_TRIGGER_HIGH_DUR, self.frame_duration)
            trigger_event = threading.Event()
            trigger_thread = threading.Thread(
                target=lambda: hw_trigger_obj.trigger(trigger_event, dca1000_socket_obj.writeTimestamp)
            )
            trigger_thread.start()

            frame_cnt = 0
            start_ts = time.time()
            while True:
                if dca1000_socket_obj.isToBreak(start_ts, stop_mode, stop_mode_param):
                    break
                # trigger one frame
                if time.time() > start_ts + frame_cnt * self.frame_duration:
                    trigger_event.set()
                    print(f"Trigger frame {frame_cnt}\n")
                    # save raw data
                    dca1000_socket_obj.handleOneFramePackets()
                    frame_cnt += 1
        elif self.sensor_trigger_mode == "SW":
            start_ts = time.time()
            dca1000_socket_obj.handlePackets(start_ts, stop_mode, stop_mode_param)

        dca1000_socket_obj.stopRecord()

    def record(self, cmd_mode, args):
        # config and start sensor
        sensor = SensorSerial(radar_config_file, self.serial_cfg_port, self.serial_dta_port, log_dir)
        sensor_thread = threading.Thread(target=sensor.sensorInitialize)
        sensor_thread.start()

        # config DCA1000EVM
        if getattr(args, "duration") is not None:
            record_duration = args.duration
            stop_mode = "duration"
            stop_mode_param = record_duration * 1000
            self.dca1000_json_data["DCA1000Config"]["captureConfig"]["durationToCapture_ms"] = stop_mode_param
        elif getattr(args, "bytes") is not None:
            record_frames = args.bytes / self.radar_cfg_obj.params["Bytes per frame"]
            record_duration = record_frames * self.frame_duration
            stop_mode = "bytes"
            stop_mode_param = int(args.bytes)
            self.dca1000_json_data["DCA1000Config"]["captureConfig"]["bytesToCapture"] = stop_mode_param
        else:
            stop_mode = "infinite"
            stop_mode_param = record_duration = DEFAULT_RECORD_DURATION
        self.dca1000_json_data["DCA1000Config"]["captureConfig"]["captureStopMode"] = stop_mode
        with open(self.json_path, "wt") as file:
            json.dump(self.dca1000_json_data, file, indent=4)

        dca1000 = DCA1000Cli(dca1000_config_json, log_dir)
        dca1000_thread = threading.Thread(target=dca1000.initialize)
        dca1000_thread.start()

        # start DCA1000 to record and stop in specified duration
        sensor_thread.join()
        dca1000_thread.join()
        if cmd_mode == "CLI":
            self.getDataCli(dca1000, record_duration)
        elif cmd_mode == "SOCKET":
            self.getDataSocket(stop_mode, stop_mode_param)

        dca1000.closeControl(self.ethernet_cfg_port)
        sensor.sensorStop()
        sensor.serialClose()
        print(f"\nIf tookits worked properly, the raw data was recorded in: ./{self.data_path}")


Utils.logging.DEBUG_ON = 1
DEFAULT_RECORD_DURATION = 10
DCA1000_TRIGGER_HIGH_DUR = 3e-6  # 5ns to 4us

if __name__ == "__main__":
    sensor_model = "AWR1843"
    dca1000_cmd_mode = "CLI"

    # Recorder Config
    radar_config_yaml = "Sensor/config/radar_config.yml"
    radar_config_file = f"Sensor/config/{sensor_model}_custom.cfg"
    radar_sub_frame_enabled = 0
    dca1000_config_json = "DCA1000/config/configFile.json"
    log_dir = "Log"
    data_dir = "Data"
    data_name_prefix = "test"

    radar_record_obj = RadarRecorder(
        sensor_model,
        radar_config_yaml,
        radar_config_file,
        dca1000_config_json,
        log_dir,
        data_dir,
        data_name_prefix,
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
        print(f"Set to default infinite record mode, with default max duration {DEFAULT_RECORD_DURATION} s")

    # Start record
    radar_record_obj.record(dca1000_cmd_mode, args)
