import os
import yaml
from Sensor.cfg_handler import RadarConfigHandler


def gen_cfg(model, input_yaml_path, output_cfg_path, sub_frame_enabled) -> RadarConfigHandler:
    config_inst = RadarConfigHandler(model)

    with open(input_yaml_path, "rt") as file:
        config_data = yaml.safe_load(file)

    config_inst.sub_frame_enabled = sub_frame_enabled
    config_inst.calcParams(config_data)
    if isinstance(config_data, dict):
        for key in config_data:
            config_inst.config[key] = config_inst.parseLine(config_data[key], key)

    with open(output_cfg_path, "wt") as file:
        config_inst.genCfgFile(file)

    return config_inst


if __name__ == "__main__":
    model = "AWR1843"
    input_yaml_name = "/Sensor/config/radar_config.yml"
    output_file_name = f"/Sensor/config/{model}_custom.cfg"
    sub_frame_enabled = 0

    gen_cfg(model, input_yaml_name, output_file_name, sub_frame_enabled)
