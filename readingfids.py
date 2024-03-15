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
   'scale, status, index, mode, ctcount, lpval, rpval, lvl, tlt, number')
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

def read_agilent_fid(file_content):
    """
    Function used to read data from agilent type .fid file

    Parameters
    ----------
    file_content : object created by following:
        with open(file.fid, "rb") as file:
            file_content = file.read()

    Returns
    -------
    headers : list starting with one DataFileHead object proceeded by one
    or multiple DataBlockHead objects
    In case of 1D spectrum it should contain one DataFileHead and one DataBlockHead
    
    
    fids : list of numpy arrays filled with csingle or int16 or int32 type variables,
    In case of 1D spectrum it should only contain one array. Those arrays contain
    raw free induction decay data.
       

    """
    ptr = 0
    header0 = DataFileHead(*struct.unpack(">llllllhhl", file_content[ptr:ptr+32]))
    headers = [header0]
    ptr += 32
    #TO BE REDONE FOR OTHER EL TYPES
    el_specifier = ">ff"
    el_type = np.csingle
    el_size = 2 * header0.ebytes if el_type == np.csingle else header0.ebytes
    bl_el_number = header0.np // 2 if el_type == np.csingle else header0.np
    # to be done: rewrite in such way that bl_el_number will be taken from appr. block header not file header
    fids = []
    def read_element(element):
        # i am not really sure which part is real in fid
        a, b = element
        result = a + b*1j
        return result
        
    for i1 in range(header0.nblocks):
        for i2 in range(header0.nbheaders):
            headers.append(DataBlockHead(*struct.unpack(">hhhhlffff", file_content[ptr:ptr+28]), i2))
            ptr += 28
        for i3 in range(header0.ntraces):
            fid = np.zeros(bl_el_number, dtype = el_type)
            for i4 in range(bl_el_number):
                #print(struct.unpack(el_specifier, file_content[ptr:ptr+el_size]))
                fid[i4] = read_element(struct.unpack(el_specifier, file_content[ptr:ptr+el_size]))
                ptr += el_size
            fids.append(fid)     
    return headers, fids


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
    fid = read_bruker_fid_1D(fid_content, info)
    return info, fid


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
        "number_of_data_points" : "$TD"
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
    
    return info

def read_bruker_fid_1D(file_content, info):
    ptr = 48
    el_specifier = "<ff" if info["byte_order"] == 0 else ">ff"
    fid = np.zeros(int(info["number_of_data_points"]), dtype=np.csingle)
    el_size = 8
    def read_element(element):
        # i am not really sure which part is real in fid
        a, b = element
        result = a + b*1j
        return result
    for i in range(0, int(info["number_of_data_points"])):
        fid[i] = read_element(struct.unpack(el_specifier, file_content[ptr:ptr+el_size]))
    
    return fid


def read_fid_1D(file_content, ptr, el_number, primary_type, quadrature=True, big_endian=True):
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
        if primary_type == np.int16 or primary_type == np.int32 or primary_type == np.int32:
            el_type = np.csingle
        elif primary_type == np.int64 or primary_type == np.float64:
            el_type = np.cdouble
        def read_element(element):
            a, b = element
            result = a + b*1j
            return result
        el_specifier += el_specifier[1]
        el_size *= 2
    else:
        el_type = primary_type
        def read_element(element):
            return 
    
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
    
    
