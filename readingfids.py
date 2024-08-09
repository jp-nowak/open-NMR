import os

from file_io.agilent import agilent_wrapper
from file_io.bruker import bruker_wrapper
from file_io.jeol_jdf import jdf_wrapper

def fid_file_type(path):
    pass
        

    if not os.path.isfile(path):
        raise FileNotFoundError
    filename, ext = os.path.splitext(path)
    if ext == ".jdf":
        return "jdf"
    if filename[-3:] == "fid" or os.path.isfile(os.path.join(os.path.dirname(path), "fid")):
        if os.path.isfile(os.path.join(os.path.dirname(path), "procpar")):
            return "agilent"
        if os.path.isfile(os.path.join(os.path.dirname(path), "acqus")):
            return "bruker"
    
    
    # if not os.path.isfile(os.path.join(path, "fid")):
    #     raise FileNotFoundError
    # if os.path.isfile(os.path.join(path, "procpar")):
    #     return "agilent"
    # if os.path.isfile(os.path.join(path, "acqus")):
    #     return "bruker"

def open_experiment(path):
    path = os.path.abspath(path)
    ftype = fid_file_type(path)
    if ftype == "agilent":
        info, fid = agilent_wrapper(os.path.dirname(path))
    elif ftype == "bruker":
        info, fid = bruker_wrapper(os.path.dirname(path))
    elif ftype == "jdf":
        info, fid = jdf_wrapper(path)
    else:
        raise NotImplementedError("not implemented type")
    
    return info, fid