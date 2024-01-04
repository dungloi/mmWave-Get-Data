# Collecting ADC Raw Data from xWR68xx / xWR18xx

  - Use serial port to send cfg parameters to xWR68xx(not fully tested) / xWR18xx(well tested).
  - Support using both DCA1000EVM_CLI_Control executable file and UDP packets through ethernet to send commands and collect data.

## Quick Start for Linux

### Setup

```
pip install -r requirements.txt
cd ./DCA1000_SDK && make clean && make && cd ..
cp ./DCA1000_SDK/Release/DCA1000EVM_CLI_* ./DCA1000_SDK/Release/libRF_API.so ./DCA1000/CLI
```

- cmd: ```gedit ~/.bashrc``` (```gedit ~/.zshrc```)
- add a new line (replace <your_ws> with your workspace path): ```export LD_LIBRARY_PATH=/<your_ws>/DCA1000/CLI:$LD_LIBRARY_PATH```

### Customize Your Params

- modify ```Sensor/config/*.yml``` (If needed), but must ensure the parameter “lvdsStreamCfg -1 0 1 0”.
- modify ```DCA1000/CLI/configFile.json``` (If needed), notice that the data path, capture mode and data prefix (if enable timestamp record) will be automatically set.
- modify serial port in ```/dev/tty*``` format, ```*``` = ```ACM ```(xWR18xx) or ```USB``` (xWR68xx) .

### Config UDP Max Recv Buffer Size

Set receive buffer to e.g. 12582912 Bytes:

- cmd: ```sudo gedit /etc/sysctl.conf```
- add a new line: ```net.core.rmem_max = 6291456```
- cmd: ```sudo sysctl -p```
- check: ```cat /proc/sys/net/core/rmem_max```

### Start Collection

run the scripts like this: ```python3 radar_recorder.py -d 10```

```
usage: radar_recorder.py [-h] [-d DURATION] [-b BYTES] [-f FRAMES] [-i INFINITE]

optional arguments:
  -h, --help            show this help message and exit
  -d DURATION, --duration DURATION
                        Record duration in second
  -b BYTES, --bytes BYTES
                        Record bytes
  -f FRAMES, --frames FRAMES
                        Record frames
  -i INFINITE, --infinite INFINITE
                        Infinite recording mode with max duration (*) s
```
If no arguments are provided, the code will default to an infinite record mode. The default max duration (*) can be set by user in ```radar_recorder.py```.

Besides, the password for current user account will be needed to provide permission for serial port configuration.

### Timestamp Sync between mmWave Radar and LiDAR

#### Radar Hardware Trigger

```specifically tested on NVIDIA Jetson Orin NX and AWR1843 & DCA1000EVM```

If the ```SOCKET``` command mode and ```HW``` trigger mode are enabled, the  host device  will output PWM to trigger the Radar sensor. The time stamp of the trigger is aligned with the system time of the host device.

Thus, if this feature is enabled, installation of package ```Jetson.GPIO``` is required (on NVIDIA Jetson platform).

#### LiDAR PTP Synchronizer 

```specifically tested on NVIDIA Jetson Orin NX and Livox MID-360```

If the time stamp synchronize mode is enabled, we will use PTP(Precision Time Protocol) for software clock synchronization. The timestamp is aligned with the system time of the host device. To install and use PTP, please run the following command:

```
sudo apt-get install ptpd ethtool
ifconfig  # to find the available ethernet interface, e.g. enp7s0
ethtool -T enp7s0         # check if the interface support time stamp
sudo ptpd -M -i enp7s0 -C # start PTP as the MASTER clock source
```

### Attention

1. The data will be transmitted in Q-in-LSB and I-in-MSB order, and cannot be modified. This format is opposite to the data collected by default configuration in mmWave Studio, and requires special handling.

2. ```UDP Related```  Please note that each frame trigger corresponds to a continuous transmission of UDP data packets, which do not include several bytes determined by "data size % packet size" (remainder). As a result, there will be some data from the previous frame transmitted together with the data of the new frame in one packet. Approximately 2 seconds after the trigger is finally stopped, the last data packet will be transmitted, and all the data packets form the complete collected data. Therefore, special attention is required when processing the data in real-time, as the first UDP packet corresponding to each frame trigger does not align perfectly with the start of that frame's data.

## Acknowledgement

[xWR6843_dataCollection](https://github.com/fanl0228/xWR6843_dataCollection)
