import subprocess, time, json, os
import Utils.logging
from DCA1000 import dca1000_cmd
from xWR6843 import xWR6843_cmd

import re

xWR6843_config_port = "/dev/ttyUSB0"
xWR6843_data_port = "/dev/ttyUSB1"

xWR6843_config_file = "xWR6843/config/xwr68xx_profile.cfg"
DCA1000_config_file = "DCA1000/config/configFile.json"

log_dir = "Log"

record_duration_s = 3

if __name__ == '__main__':
    # debug info
    Utils.logging.DEBUG_ON = 1
    os.makedirs('Log', exist_ok=True)
    os.makedirs('Data', exist_ok=True)
    
    # modify data recorded path in DCA1000 json config file
    with open(DCA1000_config_file, 'r') as file:
        dca1000_json_data = json.load(file)
    dca1000_json_data['DCA1000Config']['captureConfig']['fileBasePath'] = os.path.join(os.getcwd(), 'Data')
    with open(DCA1000_config_file, 'w') as file:
        json.dump(dca1000_json_data, file, indent=2)

    # USB device permission
    permission_command = f"sudo chmod 777 {xWR6843_config_port} {xWR6843_data_port}"
    subprocess.run(permission_command, shell=True)
    
    # config DCA1000EVM
    dca1000 = dca1000_cmd.dca1000_ethernet(configFile = DCA1000_config_file, logDir = log_dir)
    dca1000.initialize()
    time.sleep(2)

    # config IWR6843 and sensor start
    iwr6843 = xWR6843_cmd.iwr6843_serial(configFile = xWR6843_config_file,
                                         cfgPort = xWR6843_config_port, dataPort = xWR6843_data_port,
                                         logDir = log_dir)
    iwr6843.sensor_initialize()
    iwr6843.sensor_start()
    time.sleep(2)

    # ts
    dca1000_json_data['DCA1000Config']['captureConfig']['filePrefix'] = time.time()
    json.dump(dca1000_json_data, file, indent=2)   
    # DCA1000EVM start record
    dca1000.start_record()
    
    if dca1000_json_data['DCA1000Config']['captureConfig']['captureStopMode'] == "infinite":
        print(f"duration: {record_duration_s} s")
        time.sleep(record_duration_s)
    elif dca1000_json_data['DCA1000Config']['captureConfig']['captureStopMode'] == "duration":
        time.sleep(dca1000_json_data['DCA1000Config']['captureConfig']['durationToCapture_ms']/1000 + 2)
        
    # DCA1000EVM stop record && iWR6843 stop collection
    dca1000.stop_record()   
    
    # kill shell
    time.sleep(1)
    x = os.popen(f"lsof -t -i:{dca1000_json_data['DCA1000Config']['ethernetConfig']['DCA1000ConfigPort']}").read().strip()
    os.system(f"kill -9 {x}")
    print(f"pid: {x} killed. mmWave cli control closed successfully!")
        
    iwr6843.sensor_stop()
    iwr6843.serial_close()

    print(f"Data Recorded in {os.getcwd() + '/Data'}")