import struct
import collections
import os
from dataclasses import dataclass
import numpy as np

# self.info - guaranteed keys:
    # "solvent"        : string
    # "samplename"     : string
    # "nucleus"        : string - observed nucleus e.g.: H1, C13 etc.
    # "spectral_width" : float - [Hz] width of spectrum
    # "obs_nucl_freq"  : float - [MHz] Larmor frequency of observed nucleus
    # "plot_begin"     : float - [Hz] beginning of plot
    # "plot_end"       : float - [Hz] end of plot
    # "plot_ppm"       : float - [ppm] beginning of plot
    # "plot_ppm"       : float - [ppm] end of plot
    # "quadrature"     : bool: true - fid as complex numbers
    # "vendor"         : string - producer of spectrometer
    # "acquisition_time" : float - [s] time of acquisition (fid recording time for single scan)
    # "frequency_increment" : float - [Hz] distance in Hz between data points of spectrum   
    # "dwell_time" : float [s] time between data points of fid



@dataclass
class SpectrumInfo:
    plot_begin : float # [Hz] beginning of spectrum
    plot_end : float # [Hz] end of spectrum
    plot_begin_ppm : float # [ppm] beginning of spectrum
    plot_end_ppm : float # [ppm] end of spectrum
    spectral_width : float # [Hz] width of spectrum 
    acquisition_time : float # [s] aquisition time
    dwell_time : float # [s] time between data points of fid
    vendor : str # producer of spectrometer


class EmptyClass:
    pass

specifiers = { # dictionary mapping types to python struct specifiers
    np.int8  : "b",
    np.int16 : "h",
    np.int32 : "i",
    np.int64 : "q",
    np.uint8  : "B",
    np.uint16 : "H",
    np.uint32 : "I",
    np.uint64 : "Q",
    np.single : "f",
    np.double : "d",
    "int8"    : "b",
    "int16"   : "h",
    "int32"   : "i",
    "int64"   : "q",
    "uint8"   : "B",
    "uint16"  : "H",
    "uint32"  : "I",
    "uint64"  : "Q",
    "float32" : "f",
    "float64" : "d",
    }

sizes = { # dictionary mapping types to their sizes in bytes
    np.int8  : 1,
    np.int16 : 2,
    np.int32 : 4,
    np.int64 : 8,
    np.uint8  : 1,
    np.uint16 : 2,
    np.uint32 : 4,
    np.uint64 : 8,
    np.single : 4,
    np.double : 8,
    "int8"    : 1,
    "int16"   : 2,
    "int32"   : 4,
    "int64"   : 8,
    "uint8"   : 1,
    "uint16"  : 2,
    "uint32"  : 4,
    "uint64"  : 8,
    "float32" : 4,
    "float64" : 8,
    }

types = {
    "int8"    : np.int8,
    "int16"   : np.int16,
    "int32"   : np.int32,
    "int64"   : np.int64,
    "uint8"   : np.uint8,
    "uint16"  : np.uint16,
    "uint32"  : np.uint32,
    "uint64"  : np.uint64,
    "float32" : np.single,
    "float64" : np.double,
    }

def parse_by_specification(buffer, start, big_endian, spec):
    spec = spec.split()[1:]
    parsed_file = EmptyClass()
    
    for line in spec:
        line = line.split(",")
        
        group = line[0]
        ptr = start + int(line[1])
        value_type = line[2]
        array_size = int(line[3])
        name = line[4]
        
        if not hasattr(parsed_file, group):
            setattr(parsed_file, group, EmptyClass())
        group = getattr(parsed_file, group)
        value = read_value(buffer, ptr, big_endian, value_type, array_size)
        setattr(group, name, value)

    return parsed_file

def read_value(buffer, ptr, big_endian, value_type, array_size):
    endian = ">" if big_endian else "<"
    
    
    if value_type == "string":
        specifier = endian + str(array_size) + "s"
        value = struct.unpack_from(specifier, buffer, ptr)[0]
        value = value.decode()
        value = value[:value.find("\x00")]
        # print(ptr, array_size, value_type, specifier, value)
        return value
    
    if value_type == "byte":
        if array_size == 0:
            array_size = 1
        specifier = endian + str(array_size) + "s"
        value = struct.unpack_from(specifier, buffer, ptr)[0]
        # print(ptr, array_size, value_type, specifier, value)
        return value
        
    if array_size == 0:
        specifier = endian + specifiers[value_type]
        value = struct.unpack_from(specifier, buffer, ptr)[0]
        # print(ptr, array_size, value_type, specifier, value)
        return value
    
    
    value = read_array(buffer, ptr, array_size, types[value_type], False, big_endian, big_endian)
    return value

def read_array(file_content, ptr, el_number, primary_type, complex_values, big_endian, reverse):
    """
    Function to read a continous binary array of properties stated in parameters

    Parameters
    ----------
    file_content : binary 
        content of file in which array is located. created by:
        with open(fid_path, "rb") as file:
             fid_content = file.read()
    ptr : positive integer
        first byte of file part to be read.
    el_number : positive integer
        number of elements to be read, if it is an array of complex data points it is a number of complex data points not their components.
    primary_type : numpy type class e.g. np.int32
        type of simple elements e.g. if array contains complex numbers build from int32 components type is np.int32. If array is not of complex numbers it is simply type of elements
    complex_values : bool
        True if fid consists of array of complex numbers.
    big_endian : bool
        True if binary is in big endian notation.
    reverse : bool
        True if imaginary part is first, False if second.
        only matters if complex_values==True

    Raises
    ------
    NotImplementedError
        error raised if there is no implemented processing for given fid type.

    Returns
    -------
    np.array
        extracted FID. type of elements can be deduced from table beneath the function definition

    """
    el_specifier = str()
    
    if big_endian:
        el_specifier += ">"
    else:
        el_specifier += "<"
    
    try:
        el_specifier += specifiers[primary_type]
        el_size = sizes[primary_type]
    except KeyError:
        raise NotImplementedError(f"not implemented primary type{primary_type}")
            
    if complex_values:
        if primary_type in (np.uint8, np.uint16, np.uint32):
            raise NotImplementedError("complex unsigned values not supported")
        elif primary_type in (np.int8, np.int16, np.int32, np.single):
            el_type = np.csingle
        elif primary_type == np.int64 or primary_type == np.double:
            el_type = np.cdouble
        if reverse:
            def read_element(element):
                b, a = element
                result = a + b*1j
                return result
        else:
            def read_element(element):
                a, b = element
                result = a + b*1j
                return result
        
        el_specifier += el_specifier[1]
        el_size *= 2
    else:
        el_type = primary_type
        def read_element(element):
            element = element[0]
            return element
    # print(ptr, el_number, primary_type, complex_values, big_endian, el_specifier, el_size, el_type, sep=" : ")
    
    fid = np.zeros(el_number, dtype=el_type)
    
    for i in range(el_number):
        fid[i] = read_element(struct.unpack(el_specifier, file_content[ptr:ptr+el_size]))
        ptr += el_size
        
        
    return fid

# primary_type | int16       int32       int64       float32       float64
# C type       | short       int         long long   float         double 
# -------------|
# complex_values   |
#              |
# True         | csingle    csingle     cdouble      csingle      cdouble
#              | ("hh")     ("ii")      ("qq")       ("ff")       ("dd")
#              |
# False        | int32       int32       int64        single       double
#              | ("h")       ("i")       ("q")        ("f")        ("d")

#------------------------------------------------------------------------------