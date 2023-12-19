import subprocess, time, json, os
import Utils.logging
from DCA1000 import dca1000_cmd
from Radar import sensor_cmd

radar_config_port = "/dev/ttyACM0"
radar_data_port = "/dev/ttyACM1"

radar_config_file = "Radar/config/1843_profile_2d.cfg"
DCA1000_config_file = "DCA1000/config/configFile.json"

log_dir = "Log"

record_duration_s = 3

if __name__ == "__main__":
    # debug info
    Utils.logging.DEBUG_ON = 1
    os.makedirs("Log", exist_ok=True)
    os.makedirs("Data", exist_ok=True)

    # modify data recorded path in DCA1000 json config file
    with open(DCA1000_config_file, "r") as file:
        dca1000_json_data = json.load(file)
    dca1000_json_data["DCA1000Config"]["captureConfig"]["fileBasePath"] = os.path.join(
        os.getcwd(), "Data"
    )
    with open(DCA1000_config_file, "w") as file:
        json.dump(dca1000_json_data, file, indent=2)

    # USB device permission
    permission_command = f"sudo chmod 777 {radar_config_port} {radar_data_port}"
    subprocess.run(permission_command, shell=True)

    # config DCA1000EVM
    dca1000 = dca1000_cmd.dca1000_ethernet(
        configFile=DCA1000_config_file, logDir=log_dir
    )
    dca1000.initialize()
    time.sleep(2)

    # config radar and sensor start
    sensor = sensor_cmd.SensorSerial(
        configFile=radar_config_file,
        cfgPort=radar_config_port,
        dataPort=radar_data_port,
        logDir=log_dir,
    )
    sensor.sensor_initialize()
    sensor.sensor_start()
    time.sleep(2)

    # ts
    with open(DCA1000_config_file, "r") as file:
        dca1000_json_data = json.load(file)
    dca1000_json_data["DCA1000Config"]["captureConfig"]["filePrefix"] = time.time()
    with open(DCA1000_config_file, "w") as new_file:
        json.dump(dca1000_json_data, new_file, indent=2)

    # DCA1000EVM start record
    dca1000.start_record()

    if (
        dca1000_json_data["DCA1000Config"]["captureConfig"]["captureStopMode"]
        == "infinite"
    ):
        print(f"duration: {record_duration_s} s")
        time.sleep(record_duration_s)
    elif (
        dca1000_json_data["DCA1000Config"]["captureConfig"]["captureStopMode"]
        == "duration"
    ):
        time.sleep(
            dca1000_json_data["DCA1000Config"]["captureConfig"]["durationToCapture_ms"]
            / 1000
            + 2
        )
    else:
        time.sleep(record_duration_s)

    # DCA1000EVM stop record && sensor stop collection
    dca1000.stop_record()
    sensor.sensor_stop()
    sensor.serial_close()

    # kill shell
    time.sleep(1)
    x = (
        os.popen(
            f"lsof -t -i:{dca1000_json_data['DCA1000Config']['ethernetConfig']['DCA1000ConfigPort']}"
        )
        .read()
        .strip()
    )
    os.system(f"sudo kill -9 {x}")
    print(f"pid: {x} killed. mmWave cli control closed successfully!")

    print(f"Data Recorded in {os.getcwd() + '/Data'}")
