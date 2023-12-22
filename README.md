# Collecting ADC Raw Data from xWR68xx / xWR18xx

  - Use serial port to send cfg parameters to xWR68xx / xWR18xx
  - Support using both DCA1000EVM_CLI_Control executable file and UDP packets through ethernet to send commands

## Quick Start for Linux

### Setup

```
pip install -r requirements.txt
cd ./DCA1000_SDK && make clean && make && cd ..
cp ./DCA1000_SDK/Release/DCA1000EVM_CLI_* ./DCA1000_SDK/Release/libRF_API.so ./DCA1000/CLI
```
add the path ```/{your_ws}/DCA1000/CLI``` to ```$LD_LIBRARY_PATH``` in ```~/.bashrc```, like this:
 ```gedit ~/.bashrc```, add new lines(replace {your_ws} with your workspace path):

```
export LD_LIBRARY_PATH=/{your_ws}/DCA1000/CLI:$LD_LIBRARY_PATH
```

### Customize Your Params

- modify ```Sensor/config/*.cfg``` (If needed), but must ensure the parameter “lvdsStreamCfg -1 0 1 0”
- modify ```DCA1000/CLI/configFile.json``` (If needed), notice that the data path, capture mode and data prefix (if enable timestamp record) will be automatically set
- modify serial port in ```/dev/tty*``` format, * = ACM (xWR18xx) or USB (xWR68xx) 

### Start Collection

run the scripts like this: ```python3 radar_recprd.py -d 10```

```
usage: radar_recorder.py [-h] [-d DURATION] [-b BYTES] [-i INFINITE]
optional arguments:
  -h, --help            show this help message and exit
  -d DURATION, --duration DURATION
                        Record duration in second
  -b BYTES, --bytes BYTES
                        Record bytes
  -i INFINITE, --infinite INFINITE
                        Infinite recording mode with max duration 1 s
```
If no arguments are provided, the code will default to an infinite record mode. The default max duration can be set by user in radar_recorder.py.

### Attention

The data will be transmitted in Q-in-LSB and I-in-MSB order, and cannot be modified. This format is opposite to the data collected by default configuration in mmWave Studio, and requires special handling.

## Acknowledgement

[xWR6843_dataCollection](https://github.com/fanl0228/xWR6843_dataCollection)
