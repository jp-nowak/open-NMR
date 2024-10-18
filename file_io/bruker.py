import os
from dataclasses import dataclass
import numpy as np

from file_io.general import read_array
from spectrum_classes.spectrum_info import SpectrumInfo

@dataclass
class FidInfo:
    big_endian : bool
    data_type : object
    elements_number : int

def open_experiment_folder_bruker(path):
    # to be merged with agilent version into universal file opener
    fid_path = os.path.join(path, "fid")
    acqus_path = os.path.join(path,"acqus")
    with open(fid_path, "rb") as file:
        fid_content = file.read()
    acqus_lines = []
    with open(acqus_path, "r") as file:
        for line in file:
            acqus_lines.append(line)
    subfolder_path = [i.path for i in os.scandir(path) if i.is_dir()][0]
    subfolder_path = [i.path for i in os.scandir(subfolder_path) if i.is_dir()][0]
    samplename = ""
    with open(os.path.join(subfolder_path, "title")) as file:
        for line in file:
            samplename += line.strip() + ' '
    return fid_content, acqus_lines, samplename

def bruker_wrapper(path):
    fid_content, acqus_lines, samplename = open_experiment_folder_bruker(path)
    params = read_bruker_acqus(acqus_lines)
    info, fid_info = bruker_info(params)
    fid = read_bruker_fid(fid_content, info, fid_info)
    info.samplename = samplename
    return info, fid

def read_bruker_fid(fid_content, info, fid_info):
    quadrature = True
        
    fid = read_array(fid_content, 0, fid_info.elements_number, fid_info.data_type, 
                      quadrature, fid_info.big_endian, reverse=fid_info.big_endian)
    fid = np.roll(fid, -int(info.group_delay))
    return [fid]
    
# def read_bruker_acqus(acqus_lines):
#     params = dict()
#     key = "error"
#     params[key] = []
#     for line in acqus_lines:
#         words = line.split()
#         if words[0][0:2] == "##":
#             key = words[0][2:-1]
#             params[key] = [words[1:]]
#         else:
#             params[key].append(words)
#     return params

def read_bruker_acqus(acqus_lines):
    params = dict()
    key = "error"
    params[key] = []
    for line in acqus_lines:
        words = line.split()
        if words[0][0:2] == "##":
            key = words[0][2:-1]
            params[key] = [words[1:]]
        else:
            params[key].append(words)
    return {i : j[0][0] for i,j in params.items() if j and j[0]}

# def bruker_info(params):
#     info = dict()
#     params_keywords = {
#         "solvent" : "$SOLVENT",
#         "spectral_width" : "$SW_h",
#         "spectral_width_ppm" : "$SW",
#         "nucleus" : "$NUC1",
#         "spectral_center" : "$O1", # [Hz]
#         "obs_nucl_freq" : "$BF1", # [MHz]
#         "byte_order" : "$BYTORDA", # 0-little endian or 1-big endian
#         "date" : "$DATE", # unknown format - unix?
#         "number_of_scans" : "$NS",
#         "number_of_data_points" : "$TD", # number of complex points = number_of_data_points/2
#         "data_type" : "$DTYPA",
#         "group_delay" : "$GRPDLY",
#         "acquisition_time" : "$AT",
#         "irradiation_freq" : "$SFO1" # [s]
#         }
#     for i, j in params_keywords.items():
#         try:
#             value = params[j][0][0]
#             value = float(value) if value.replace('.','',1).replace('-','',1).isdigit() else value[1:-1]
#         except KeyError:
#             value = None
#         info[i] = value
        
#     # calculation of plot edges x values
#     info["plot_end"] = info["spectral_center"] + info["spectral_width"]/2
#     info["plot_begin"] = info["spectral_center"] - info["spectral_width"]/2  
#     info["plot_begin_ppm"] = info["plot_begin"] / info["obs_nucl_freq"]
#     info["plot_end_ppm"] = info["plot_end"] / info["obs_nucl_freq"]
    
#     info["number_of_data_points"] = int(info["number_of_data_points"])//2
#     info["vendor"] = "bruker"
    
#     # calculation of acquisition time
#     info["dwell_time"] = 1/(info["spectral_width_ppm"]*info["irradiation_freq"])
#     if not info["acquisition_time"]:
#         info["acquisition_time"] = info["number_of_data_points"]*info["dwell_time"]
    
#     info["frequency_increment"] = info["spectral_width"] / info["number_of_data_points"]
    
#     return info

def bruker_info(params):
    centrum_of_spectrum_Hz = float(params["$O1"])
    spectral_width = float(params["$SW_h"])
    obs_nucl_freq = float( params["$BF1"])
    plot_begin = centrum_of_spectrum_Hz - spectral_width / 2
    plot_end = centrum_of_spectrum_Hz + spectral_width / 2
    elements_number = int(params["$TD"]) // 2
    irradiation_frequency = float(params["$SFO1"])
    dwell_time = 1/(float(params["$SW"]) * irradiation_frequency)
    if float(params["$DTYPA"]) == 0:
        data_type = np.int32
    elif float(params["$DTYPA"]) == 2:
        data_type = np.double
    else:
        raise NotImplementedError("unknown primary data type")
    
    return (
        SpectrumInfo(
            plot_begin = plot_begin,
            plot_end = plot_end,
            plot_begin_ppm = plot_begin / obs_nucl_freq,
            plot_end_ppm = plot_end / obs_nucl_freq,
            spectral_width = spectral_width,
            acquisition_time = elements_number*dwell_time,
            obs_nucl_freq = obs_nucl_freq,
            dwell_time = dwell_time,
            frequency_increment = spectral_width / elements_number,
            group_delay = float(params["$GRPDLY"]),
            trimmed = 0.0,
            vendor = "bruker",
            solvent = params["$SOLVENT"][1:-1],
            samplename = "",
            nucleus = params["$NUC1"][1:-1],
            ), 
        FidInfo(
            big_endian = bool(int(params["$BYTORDA"])),
            data_type = data_type,
            elements_number = elements_number)
        ) 
