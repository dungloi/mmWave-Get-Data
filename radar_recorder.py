import argparse
import subprocess, time, json, os
import Utils.logging
from DCA1000.cli_cmd import DCA1000Cli
from DCA1000.udp_cmd import DCA1000Udp
from Sensor.hardware_trigger import HardwareTrigger
from Sensor.sensor_cmd import SensorSerial
import Sensor.cfg_gen as cfg_gen
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
        self.radar_cfg_obj = cfg_gen.cfg_gen(
            self.MODEL,
            yaml_path,
            cfg_path,
            self.radar_sub_frame_enabled,
        )
        self.sensor_trigger_mode = "SW" if int(self.radar_cfg_obj.config["frameCfg"].split(" ")[-2]) == 1 else "HW"
        self.frame_duration = float(self.radar_cfg_obj.config["frameCfg"].split(" ")[-3]) * 0.001
        self.frame_size = self.radar_cfg_obj.params["Bytes per frame"]
        print(f"Frame size: {self.frame_size} Bytes")

        # Configure USB Ports and grant device permissions
        if self.MODEL[3] == "1":
            self.serial_port_type = "ACM"
        elif self.MODEL[3] == "6":
            self.serial_port_type = "USB"
        self.serial_cfg_port = f"/dev/tty{self.serial_port_type}0"
        self.serial_dta_port = f"/dev/tty{self.serial_port_type}1"
        permission_command = f"sudo chmod 777 {self.serial_cfg_port} {self.serial_dta_port}"
        subprocess.run(permission_command, shell=True)

    def recordDataCLI(self, record_duration):
        # config and start sensor and initialize DCA1000
        sensor = SensorSerial(radar_config_file, self.serial_cfg_port, self.serial_dta_port, log_dir)
        sensor_thread = threading.Thread(target=sensor.sensorInitialize)
        sensor_thread.start()
        dca1000 = DCA1000Cli(dca1000_config_json, log_dir)
        dca1000_thread = threading.Thread(target=dca1000.initialize)
        dca1000_thread.start()

        # start DCA1000 to record and stop in specified duration
        sensor_thread.join()
        dca1000_thread.join()
        dca1000.startRecord()

        print(f"duration: {record_duration} s")
        time.sleep(record_duration + 0.01)

        dca1000.stopRecord()
        dca1000.closeControl(self.ethernet_cfg_port)
        sensor.sensorStop()
        sensor.serialClose()

    def recordDataSocket(self, stop_mode, stop_mode_param):
        # start DCA1000
        dca1000_obj = DCA1000Cli(dca1000_config_json, log_dir)
        dca1000_obj.initialize()
        dca1000_socket_obj = DCA1000Udp(
            self.local_ip,
            self.dca1000_ip,
            self.ethernet_cfg_port,
            self.ethernet_dta_port,
            os.path.join(self.data_path, data_name_prefix),
            self.frame_duration,
        )
        dca1000_socket_obj.startRecord()

        # config and start sensor
        sensor_obj = SensorSerial(radar_config_file, self.serial_cfg_port, self.serial_dta_port, log_dir)
        sensor_obj.sensorInitialize()

        # clear file
        _ = open(dca1000_socket_obj.data_path + "_raw_udp_packets.bin", "wb")
        _ = open(dca1000_socket_obj.data_path + "_ts.txt", "wt")
        if self.sensor_trigger_mode == "HW":
            dca1000_socket_obj.setTimeout(0.005)  # packets interval

            # set up hardware trigger thread
            hw_trigger_obj = HardwareTrigger(DCA1000_TRIGGER_HIGH_DUR, self.frame_duration)
            trigger_event = threading.Event()
            trigger_thread = threading.Thread(
                target=lambda: hw_trigger_obj.trigger(trigger_event, dca1000_socket_obj.writeTimestamp)
            )
            trigger_thread.start()

            start_ts = time.time()
            while True:
                if dca1000_socket_obj.isToBreak(start_ts, stop_mode, stop_mode_param):
                    break
                # trigger one frame
                if time.time() > start_ts + dca1000_socket_obj.data_frames_cnt * self.frame_duration:
                    trigger_event.set()
                    print(f"Trigger frame {dca1000_socket_obj.data_frames_cnt}")
                    # save raw data
                    dca1000_socket_obj.handleOneFramePackets()
        elif self.sensor_trigger_mode == "SW":
            dca1000_socket_obj.setTimeout(self.frame_duration)
            start_ts = time.time()
            dca1000_socket_obj.handlePackets(start_ts, stop_mode, stop_mode_param)

        dca1000_socket_obj.handleLastPacket()
        dca1000_socket_obj.stopRecord()
        sensor_obj.sensorStop()
        sensor_obj.serialClose()

    def record(self, cmd_mode, args):
        # parse arguments
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
        elif getattr(args, "frames") is not None:
            record_frames = args.frames
            record_duration = record_frames * self.frame_duration
            stop_mode = "frames"
            stop_mode_param = int(args.frames)
            self.dca1000_json_data["DCA1000Config"]["captureConfig"]["framesToCapture"] = stop_mode_param
        else:
            stop_mode = "infinite"
            stop_mode_param = record_duration = DEFAULT_RECORD_DURATION

        # start record
        if cmd_mode == "CLI":
            # config json file for DCA1000EVM(CLI control mode)
            if stop_mode == "frames":
                print("Unsupported mode for CLI!!!")
                return
            self.dca1000_json_data["DCA1000Config"]["captureConfig"]["captureStopMode"] = stop_mode
            with open(self.json_path, "wt") as file:
                json.dump(self.dca1000_json_data, file, indent=4)
            self.recordDataCLI(record_duration)
        elif cmd_mode == "SOCKET":
            self.recordDataSocket(stop_mode, stop_mode_param)

        print(
            f"\nIf tookits worked properly, the raw data was recorded in: {os.path.join(os.getcwd(), self.data_path)}"
        )

    def paramsParser():
        parser = argparse.ArgumentParser()
        parser.add_argument("-d", "--duration", type=float, help="Record duration in second", required=False)
        parser.add_argument("-b", "--bytes", type=float, help="Record bytes", required=False)
        parser.add_argument("-f", "--frames", type=float, help="Record frames", required=False)
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
        return args


Utils.logging.DEBUG_ON = 0
DEFAULT_RECORD_DURATION = 10
DCA1000_TRIGGER_HIGH_DUR = 4e-6  # 5ns to 4us

if __name__ == "__main__":
    sensor_model = "AWR1843"
    dca1000_cmd_mode = "SOCKET"  # "CLI" or "SOCKET"

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
    # parse arguments
    args = radar_record_obj.paramsParser()
    # Start record
    radar_record_obj.record(dca1000_cmd_mode, args)
