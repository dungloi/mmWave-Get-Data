import math


class RadarConfigHandler:
    def __init__(self, model: str) -> None:
        if model[3] == "1":
            self.model = "xWR18xx"
            self.carrier_frequency = 77
        elif model[3] == "6":
            self.model = "xWR68xx"
            self.carrier_frequency = 60
        self.config = {}
        self.params = {}
        self.params["c"] = 3 * 10**8
        self.sub_frame_enabled = 0

    def parseLine(self, cfg_line, cfg_key) -> str:
        result_string = ""
        if isinstance(cfg_line, dict):
            for key, value in cfg_line.items():
                if not isinstance(value, (float, int)):  # cfg_key has value which is nested
                    # first time acquire the config key
                    if self.config.get(f"{cfg_key}_count", 0) == 0:
                        self.config[f"{cfg_key}_count"] = 0
                    # the profile need to be write repeatedly
                    self.config[f"{cfg_key}_count"] += 1
                # recursion
                nested_result = self.parseLine(cfg_line[key], 0)
                result_string += f" {nested_result}"
        else:
            result_string += f" {cfg_line}"
        return result_string.strip()

    def calcParams(self, cfg_obj) -> None:
        self.params["Carrier frequency  GHz"] = self.carrier_frequency
        self.params["Ramp Slope  MHz/us"] = cfg_obj["profileCfg"]["profile_0"]["freqSlopeConst"]
        self.params["Num ADC Samples"] = cfg_obj["profileCfg"]["profile_0"]["numAdcSamples"]
        self.params["ADC Sampling Rate Msps"] = cfg_obj["profileCfg"]["profile_0"]["digOutSampleRate"] / 1000.0

        self.params["ADC Collection Time  us"] = self.params["Num ADC Samples"] / self.params["ADC Sampling Rate Msps"]
        self.params["Extra ramp time required (start time)  us"] = cfg_obj["profileCfg"]["profile_0"]["adcStartTime"]
        self.params["Chirp time (end time - start time)  us"] = (
            cfg_obj["profileCfg"]["profile_0"]["rampEndTime"] - self.params["Extra ramp time required (start time)  us"]
        )
        self.params["Chirp duration (end time)  us"] = cfg_obj["profileCfg"]["profile_0"]["rampEndTime"]

        self.params["Sweep BW (useful) MHz"] = (
            self.params["ADC Collection Time  us"] * self.params["Ramp Slope  MHz/us"]
        )
        self.params["Total BW  MHz"] = self.params["Chirp duration (end time)  us"] * self.params["Ramp Slope  MHz/us"]

        self.params["Max beat freq (80% of ADC sampling rate)  MHz"] = self.params["ADC Sampling Rate Msps"] * 0.8
        self.params["Max distance (80%)  m"] = (
            self.params["c"]
            / 10**6
            / 2
            * self.params["Max beat freq (80% of ADC sampling rate)  MHz"]
            / self.params["Ramp Slope  MHz/us"]
        )
        self.params["Max beat freq (80% of ADC sampling rate)  MHz"] = self.params["ADC Sampling Rate Msps"] * 0.8
        self.params["Range resolution  m"] = self.params["c"] / 10**6 / 2 / self.params["Sweep BW (useful) MHz"]
        self.params["Range resolution (meter per 1D-FFT bin)  m/bin"] = self.params["Range resolution  m"]

        self.params["Inter-chirp duration  us"] = cfg_obj["profileCfg"]["profile_0"]["idleTime"]
        self.params["Number of chirp intervals in frame"] = (
            cfg_obj["frameCfg"]["chirpEndIdx"] - cfg_obj["frameCfg"]["chirpStartIdx"] + 1
        ) * cfg_obj["frameCfg"]["numLoops"]
        tx_bin = bin(cfg_obj["channelCfg"]["txChannelEn"])[2:]
        rx_bin = bin(cfg_obj["channelCfg"]["rxChannelEn"])[2:]
        self.params["Number of TX (TDM MIMO)"] = tx_bin.count("1")
        self.params["Number of Tx elevation antennas"] = tx_bin[-2:-1]
        self.params["Number of RX channels"] = rx_bin.count("1")

        self.params["lambda"] = self.params["c"] / (
            self.carrier_frequency * 10**9 + self.params["Total BW  MHz"] * 10**6 / 2
        )
        self.params["Max umambiguous relative velocity  m/s"] = (
            self.params["lambda"]
            / 4
            / (
                (self.params["Inter-chirp duration  us"] + self.params["Chirp duration (end time)  us"])
                * 10**-6
                * self.params["Number of TX (TDM MIMO)"]
            )
        )
        self.params["Max extended relative velocity  m/s"] = (
            self.params["Max umambiguous relative velocity  m/s"] * 2 / cfg_obj["frameCfg"]["numLoops"]
        )

        self.params["Frame time (total)  ms"] = (
            self.params["Number of chirp intervals in frame"]
            * (self.params["Inter-chirp duration  us"] + self.params["Chirp duration (end time)  us"])
        ) / 1000
        self.params["Frame time (active)  ms "] = (
            self.params["Number of chirp intervals in frame"] * self.params["Chirp duration (end time)  us"]
        ) / 1000
        self.params["Range FFT size"] = self.params["Max distance (80%)  m"] / 0.8 / self.params["Range resolution  m"]
        self.params["Doppler FFT size"] = self.params["Number of chirp intervals in frame"] / 2
        self.params["Angle FFT size"] = (
            self.params["Number of RX channels"] * self.params["Number of TX (TDM MIMO)"] * math.pi / 2.0
        )

        self.params["Bytes per frame"] = (
            self.params["Number of chirp intervals in frame"]
            * self.params["Number of RX channels"]
            * 2
            * 2
            * self.params["Num ADC Samples"]
        )

    def genCfgFile(self, file) -> None:
        file.write("%% customized by user\n")
        for key, value in self.params.items():
            if key == "c":
                continue
            file.write(f"% {key.ljust(50)} {value}\n")
        file.write("%%\n")

        for key, value in self.config.items():
            try:
                if key == "profileCfg" and (float(list(value.split())[1]) != float(self.carrier_frequency)):
                    raise ValueError("profileCfg")

                if (
                    key[-6:] == "_count"
                    or (key == "bpmCfg" and self.model == "xWR18xx")
                    or (self.sub_frame_enabled == 0 and (key == "advFrameCfg" or key == "subFrameCfg"))
                ):
                    continue

                if key[:6] == "sensor" or key == "flushCfg":
                    file.write(f"{key}\n")
                elif key == "chirpCfg" or key == "cfarCfg" or key == "cfarFovCfg":
                    # write times depends on the sub-line count
                    string_to_items = list(value.split())
                    item_cnt = self.config[f"{key}_count"]
                    substr_len = len(string_to_items) // item_cnt

                    for i in range(item_cnt):
                        data_str = ""
                        for x in string_to_items[i * substr_len : (i + 1) * substr_len]:
                            data_str += f"{float(x) if '.' in x else int(x)} "
                        file.write(f"{key} {data_str}\n")
                else:
                    file.write(f"{key} {value}\n")

            except Exception as e:
                print(f"Invalid carrier_frequency!!! {e}")
