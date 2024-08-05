import os
import numpy as np

from file_io.general import read_array

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
    title = ""
    with open(os.path.join(subfolder_path, "title")) as file:
        for line in file:
            title += line.strip() + ' '
    loose_info = dict()
    loose_info['samplename'] = title
    return fid_content, acqus_lines, loose_info

def bruker_wrapper(path):
    fid_content, acqus_lines, loose_info = open_experiment_folder_bruker(path)
    params = read_bruker_acqus(acqus_lines)
    info = bruker_info(params)
    fid = read_bruker_fid(fid_content, info)
    info.update(loose_info)
    return info, fid

def read_bruker_fid(fid_content, info):
    big_endian = bool(info["byte_order"])
    el_number = info["number_of_data_points"]
    quadrature = True

    if info["data_type"] == 0:
        primary_type = np.int32
    elif info["data_type"] == 2:
        primary_type = np.double
    else:
        raise NotImplementedError("unknown primary data type")
        
    fid = read_array(fid_content, 0, el_number, primary_type, 
                      quadrature, big_endian, reverse=big_endian)
    fid = np.roll(fid, -int(info["group_delay"]))
    return [fid]
    
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
    return params

def bruker_info(params):
    info = dict()
    params_keywords = {
        "solvent" : "$SOLVENT",
        "spectral_width" : "$SW_h",
        "spectral_width_ppm" : "$SW",
        "nucleus" : "$NUC1",
        "spectral_center" : "$O1", # [Hz]
        "obs_nucl_freq" : "$BF1", # [MHz]
        "byte_order" : "$BYTORDA", # 0-little endian or 1-big endian
        "date" : "$DATE", # unknown format - unix?
        "number_of_scans" : "$NS",
        "number_of_data_points" : "$TD", # number of complex points = number_of_data_points/2
        "data_type" : "$DTYPA",
        "group_delay" : "$GRPDLY",
        "acquisition_time" : "$AT",
        "irradiation_freq" : "$SFO1" # [s]
        }
    for i, j in params_keywords.items():
        try:
            value = params[j][0][0]
            value = float(value) if value.replace('.','',1).replace('-','',1).isdigit() else value[1:-1]
        except KeyError:
            value = None
        info[i] = value
        
    # calculation of plot edges x values
    info["plot_end"] = info["spectral_center"] + info["spectral_width"]/2
    info["plot_begin"] = info["spectral_center"] - info["spectral_width"]/2  
    info["plot_begin_ppm"] = info["plot_begin"] / info["obs_nucl_freq"]
    info["plot_end_ppm"] = info["plot_end"] / info["obs_nucl_freq"]
    
    info["number_of_data_points"] = int(info["number_of_data_points"])//2
    info["vendor"] = "bruker"
    
    # calculation of acquisition time
    info["dwell_time"] = 1/(info["spectral_width_ppm"]*info["irradiation_freq"])
    if not info["acquisition_time"]:
        info["acquisition_time"] = info["number_of_data_points"]*info["dwell_time"]
    
    info["frequency_increment"] = info["spectral_width"] / info["number_of_data_points"]
    
    return info