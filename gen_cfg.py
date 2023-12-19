import os
import yaml
import Radar.cfg_handler as hdl

MODEL = "AWR1843"
INPUT_YAML_NAME = "radar_config.yml"
OUTPUT_FILE_NAME = "awr1843_custom.cfg"

SUB_FRAME_ENABLED = 0

if __name__ == "__main__":
    config_inst = hdl.RadarConfigHandler(MODEL)

    yml_file_path = os.getcwd() + f"/{INPUT_YAML_NAME}"
    cfg_file_path = os.getcwd() + f"/Radar/config//{OUTPUT_FILE_NAME}"
    with open(yml_file_path, "rt") as file:
        config_data = yaml.safe_load(file)

    config_inst.sub_frame_enabled = SUB_FRAME_ENABLED
    config_inst.calcParams(config_data)
    if isinstance(config_data, dict):
        for key in config_data:
            config_inst.config[key] = config_inst.parseLine(config_data[key], key)

    with open(cfg_file_path, "wt") as file:
        config_inst.genCfgFile(file)
