# Get xWR6843 Data through DCA1000_CLI

  - Use serial port to send cfg parameters to xWR6843 
  - Use DCA1000EVM_CLI_Control executable file to configure DCA1000 parameters
  - Start/stop DCA1000 to collect data

## Quick Start

### Linux

#### Setup

```
pip install requirements.txt
cd ./DCA1000_SDK && rm -rf release && make && cd ..
cp ./DCA1000_SDK/Release/DCA1000EVM_CLI_* ./DCA1000_SDK/Release/libRF_API.so ./DCA1000/CLI
```
add the path ```/{your_ws}/DCA1000/CLI``` to ```$LD_LIBRARY_PATH``` in ```~/.bashrc```, like this:
 ```gedit ~/.bashrc```, add new lines(replace {your_ws} with your workspace path):

```
export LD_LIBRARY_PATH=/{your_ws}/DCA1000/CLI:$LD_LIBRARY_PATH
```

#### Customize Your Params (IWR6843 Only)

- modify ```xWR6843/config/iwr6843.cfg``` (If needed), but must ensure the parameter “lvdsStreamCfg -1 0 1 0”
- modify ```DCA1000/CLI/configFile.json``` (If needed), notice that the data path will be automatically set
- modify serial port in ```record.py``` in ```/dev/ttyUSB*``` format

#### Start Collection

run

```
python3 record.py
```

## Acknowledgement

[xWR6843_dataCollection](https://github.com/fanl0228/xWR6843_dataCollection)
