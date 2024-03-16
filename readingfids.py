import struct
import collections
import numpy as np
import os

#CONSTANT
DEUTERIUM_EPSILON = 0.1535069

# definition of named tuple class used to store information from file header

DataFileHead = collections.namedtuple("DataFileHead", 
   'nblocks, ntraces, np, ebytes, tbytes, bbytes, vers_id, status, nbheaders' )
# struct datafilehead
# /* Used at start of each data file (FIDs, spectra, 2D) */
# {
# long nblocks;
# /* number of blocks in file */
# long ntraces;
# /* number of traces per block */
# long np;
# /* number of elements per trace */
# long ebytes;
# /* number of bytes per element */
# long tbytes;
# /* number of bytes per trace */
# long bbytes;
# /* number of bytes per block */
# short vers_id;
# /* software version, file_id status bits */
# short status;
# /* status of whole file */
# long nbheaders;
# /* number of block headers per block */
# };


# definition of named tuple class used to store information from file header

DataBlockHead = collections.namedtuple("DataBlockHead",
   'scale, status, index, mode, ctcount, lpval, rpval, lvl, tlt')
# struct datablockhead
# /* Each file block contains the following header */
# {
# short scale;
# /* scaling factor */
# short status;
# /* status of data in block */
# short index;
# /* block index */
# short mode;
# /* mode of data in block */
# long ctcount;
# /* ct value for FID */
# float lpval;
# /* f2 (2D-f1) left phase in phasefile */
# float rpval;
# /* f2 (2D-f1) right phase in phasefile */
# float lvl;
# /* level drift correction */
# float tlt;
# /* tilt drift correction */
# };
# number - number of header in block

def fid_file_type(path):
    print(os.path.join(path, "fid"))
    if not os.path.isfile(os.path.join(path, "fid")):
        raise FileNotFoundError
    if os.path.isfile(os.path.join(path, "procpar")):
        return "agilent"
    if os.path.isfile(os.path.join(path, "acqus")):
        return "bruker"


def read_fid_1D(file_content, ptr, el_number, primary_type, quadrature, big_endian):
    el_specifier = str()
    
    if big_endian:
        el_specifier += ">"
    else:
        el_specifier += "<"
    
    if primary_type == np.int16:
        el_specifier += "h"
        el_size = 2
    elif primary_type == np.int32:
        el_specifier += "i"
        el_size = 4
    elif primary_type == np.int64:
        el_specifier += "q"
        el_size = 8
    elif primary_type == np.single:
        el_specifier += "f"
        el_size = 4
    elif primary_type == np.double:
        el_specifier += "d"
        el_size = 8
    else:
        raise NotImplementedError(f"not implemented primary type{primary_type}")
        
    if quadrature:
        if primary_type == np.int16 or primary_type == np.int32 or primary_type == np.single:
            el_type = np.csingle
        elif primary_type == np.int64 or primary_type == np.double:
            el_type = np.cdouble
        def read_element(element):
            b, a = element
            result = a + b*1j
            return result
        el_specifier += el_specifier[1]
        el_size *= 2
    else:
        el_type = primary_type
        def read_element(element):
            return element
    #print(ptr, el_number, primary_type, quadrature, big_endian, el_specifier, el_size, el_type, sep="\n")
    
    fid = np.zeros(el_number, dtype=el_type)
    
    for i in range(el_number):
        fid[i] = read_element(struct.unpack(el_specifier, file_content[ptr:ptr+el_size]))
        ptr += el_size
        
        
    return fid

# primary_type | int16       int32       int64       float32       float64
# C type       | short       int         long long   float         double 
# -------------|
# quadrature   |
#              |
# True         | csingle    csingle     cdouble      csingle      cdouble
#              | ("hh")     ("ii")      ("qq")       ("ff")       ("dd")
#              |
# False        | int32       int32       int64        single       double
#              | ("h")       ("i")       ("q")        ("f")        ("d")

#------------------------------------------------------------------------------
    
def agilent_wrapper(path):
    # agilent - file header size 32 bytes, block headers 28 bytes
    fid_content, procpar_lines = open_experiment_folder_agilent(path)
    procpar = read_agilent_procpar(procpar_lines)
    info = info_agilent(procpar)
    status_dict, headers, fid = read_agilent_fid(fid_content)
    return info, fid

def read_agilent_fid(fid_content):
    ptr = 0
    file_header = DataFileHead(*struct.unpack(">llllllh2sl", fid_content[0:32]))
    status_dict = {
        's_data'         : bool(int(file_header.status[1] & int("00000001", 2))),
        's_spec'         : bool(int(file_header.status[1] & int("00000010", 2))),
        's_32'           : bool(int(file_header.status[1] & int("00000100", 2))),
        's_float'        : bool(int(file_header.status[1] & int("00001000", 2))),
        's_complex'      : bool(int(file_header.status[1] & int("00010000", 2))),
        's_hypercomplex' : bool(int(file_header.status[1] & int("00100000", 2))),
        's_acqpar'       : bool(int(file_header.status[1] & int("10000000", 2))),
        
        's_secnd'        : bool(int(file_header.status[0] & int("00000001", 2))),
        's_transf'       : bool(int(file_header.status[0] & int("00000010", 2))),
        's_np'           : bool(int(file_header.status[0] & int("00000100", 2))),
        's_nf'           : bool(int(file_header.status[0] & int("00010000", 2))),
        's_ni'           : bool(int(file_header.status[0] & int("00100000", 2))),
        's_ni2'          : bool(int(file_header.status[0] & int("01000000", 2))),
        }
    ptr += 32
    
    if ((not status_dict["s_data"]) or status_dict["s_spec"] or status_dict["s_hypercomplex"] or
        status_dict["s_secnd"] or status_dict["s_transf"] or status_dict["s_np"] or 
        status_dict["s_nf"] or status_dict["s_ni"] or status_dict["s_ni2"] or status_dict["s_complex"]):
        raise NotImplementedError(f"not implemented spectrum type {status_dict}")
    
    if status_dict["s_float"]:
        primary_type = np.single
    else:
        primary_type = np.int32 if status_dict["s_32"] else np.int16
        
    #quadrature = True if status_dict["s_complex"] else False
    
    quadrature = True
    
    el_number = file_header.np // 2 if quadrature else file_header.np
    
    fids = []
    headers = []
    
    if file_header.nblocks > 1:
        raise NotImplementedError("two dimensional spectra")
    for i1 in range(file_header.nblocks):
        header = DataBlockHead(*struct.unpack(">hhhhlffff", fid_content[ptr:ptr+28]))
        ptr += 28
        headers.append(header)
        if file_header.nbheaders == 1:
            pass
        elif file_header.nbheaders == 2:
            raise NotImplementedError("hypercmplxbhead")
        else:
            raise NotImplementedError("unexpected number of block headers")
        if file_header.ntraces > 1:
            raise NotImplementedError("more then one trace per block")
        for i3 in range(file_header.ntraces):
            fid = read_fid_1D(fid_content, ptr, el_number, primary_type, quadrature, big_endian=True)
        fids.append(fid)
    
    return status_dict, headers, fids
   
def open_experiment_folder_agilent(path):
    fid_path = os.path.join(path, "fid")
    procpar_path = os.path.join(path,"procpar")
    with open(fid_path, "rb") as file:
        fid_content = file.read()
    procpar_lines = []
    with open(procpar_path, "r") as file:
        for line in file:
            procpar_lines.append(line)
    
    return fid_content, procpar_lines

def read_agilent_procpar(procpar_lines):
    params = dict()
    key = "error"
    params[key] = []
    for line in procpar_lines:
        words = line.split()
        if words[0][0].isalpha():
            key = words[0]
            params[key] = [words[1:]]
        else:
            params[key].append(words)
    return params

def info_agilent(params):
    info = dict()
    params_keywords = {
        "solvent" : "solvent",
        "lock_freq" : "lockfreq_", # [MHz] lock (deuterium) frequency of spectrometer
        "samplename" : "samplename",
        "spectrometer_freq" : "h1freq", # [MHz] proton frequency of spectrometer
        "experiment" : "pslabel",
        "experiment_type" : "apptype",
        "nucleus" : "tn", # observed nucleus An np H1, C13 etc.
        "spectral_width" : "sw", # [Hz]
        "studyowner" : "studyowner",
        "operator" : "operator",
        "date" : "time_saved", # string "yyyymmddThhmmss"
        "obs_nucl_freq" : "sfrq", # [MHz]
        "plot_begin" : "sp", # [Hz] beginning of plot
        "points_number" : "np"# number of data points
        }
    
    # import of directly stated params
    for i, j in params_keywords.items():
        try:
            value = params[j][1][1]
            value = float(value) if value.replace('.','',1).replace('-','',1).isdigit() else value[1:-1]
        except KeyError:
            value = None
        info[i] = value
        
    # derived params
    if not info["spectrometer_freq"]:
        info["spectrometer_freq"] = round(info["lock_freq"]/DEUTERIUM_EPSILON)
        
    info["plot_end"] = info["plot_begin"] + info["spectral_width"] # [Hz]
    info["plot_begin_ppm"] = info["plot_begin"] / info["obs_nucl_freq"]
    info["plot_end_ppm"] = info["plot_end"] / info["obs_nucl_freq"]
    
    return info


#------------------------------------------------------------------------------

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

    return fid_content, acqus_lines

def bruker_wrapper(path):
    fid_content, acqus_lines = open_experiment_folder_bruker(path)
    params = read_bruker_acqus(acqus_lines)
    info = bruker_info(params)
    fid = read_bruker_fid(fid_content, info)
    return info, fid

def read_bruker_fid(fid_content, info):
    big_endian = bool(info["byte_order"])
    el_number = info["number_of_data_points"]//2
    quadrature = True
    start_offset = 40 #in bytes, temporary
    if info["data_type"] == 0:
        primary_type = np.int32
        el_number -= start_offset//8
    elif info["data_type"] == 2:
        primary_type = np.double
        el_number -= start_offset//16
    else:
        raise NotImplementedError("unknown primary data type")
    fid = read_fid_1D(fid_content, 40, el_number, primary_type, quadrature, big_endian)
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
        "data_type" : "$DTYPA"
        }
    for i, j in params_keywords.items():
        try:
            value = params[j][0][0]
            value = float(value) if value.replace('.','',1).replace('-','',1).isdigit() else value[1:-1]
        except KeyError:
            value = None
        info[i] = value
        
        
    info["plot_end"] = info["spectral_center"] + info["spectral_width"]/2
    info["plot_begin"] = info["spectral_center"] - info["spectral_width"]/2  
    
    info["plot_begin_ppm"] = info["plot_begin"] / info["obs_nucl_freq"]
    info["plot_end_ppm"] = info["plot_end"] / info["obs_nucl_freq"]
    
    info["number_of_data_points"] = int(info["number_of_data_points"] )
    
    info["samplename"] = "not implemented in bruker format aaaaaaaaaaaaaaaaaaaaaaaaaaa"
    
    return info


if __name__ == "__main__":
    info, fid = agilent_wrapper("C:/Users/Jan Nowak/Desktop/open nmr/open-NMR/example_fids/agilent/agilent_example1H.fid")

    
    
