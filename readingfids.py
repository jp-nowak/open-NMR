import os

from file_io.agilent import agilent_wrapper
from file_io.bruker import bruker_wrapper
import file_io.jeol_jdf

def fid_file_type(path):
    if not os.path.isfile(os.path.join(path, "fid")):
        raise FileNotFoundError
    if os.path.isfile(os.path.join(path, "procpar")):
        return "agilent"
    if os.path.isfile(os.path.join(path, "acqus")):
        return "bruker"

def open_experiment(path):
    path = os.path.abspath(path)
    ftype = fid_file_type(path)
    if ftype == "agilent":
        info, fid = agilent_wrapper(path)
    elif ftype == "bruker":
        info, fid = bruker_wrapper(path)
    else:
        raise NotImplementedError("not implemented type")
    
    return info, fid