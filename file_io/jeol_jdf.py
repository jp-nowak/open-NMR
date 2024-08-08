import struct
import numpy as np

from file_io.general import parse_by_specification, read_value, read_array
from spectrum_classes.spectrum_info import SpectrumInfo


spec = """group,position,type,array_size,name
file_info,0,string,8,filetype
file_info,8,int8,0,endian
file_info,9,uint8,0,major_version
file_info,10,uint16,0,minot_version
file_info,12,uint8,0,data_dimension_number
file_info,13,byte,0,data_dimension_exist
file_info,14,byte,0,control_byte
file_info,15,int8,0,instrument_type
axis_info,16,uint8,8,translate
axis_info,24,uint8,8,data_axis_type
axis_info,32,byte,16,axis_units
experiment_info,48,string,124,title
axis_info,172,byte,4,x_axis_type
axis_info,176,uint32,8,element_number
axis_info,208,uint32,8,offset_start
axis_info,240,uint32,8,offset_end
axis_info,272,float64,8,axis_start
axis_info,336,float64,8,axis_end
experiment_info,400,byte,4,experiment_date
experiment_info,404,byte,4,revision_date
experiment_info,408,string,16,node_name
experiment_info,424,string,128,site
experiment_info,552,string,128,author
experiment_info,680,string,128,comment
axis_info,808,string,256,axis_titles
axis_info,1064,float64,8,base_freq
axis_info,1128,float64,8,zero_point
axis_info,1192,byte,8,reversed
file_info,1203,byte,0,annotation_ok
file_info,1204,uint32,0,history_used
file_info,1208,uint32,0,history_length
file_info,1212,uint32,0,param_start
file_info,1216,uint32,0,param_length
axis_info,1220,uint32,8,list_start
axis_info,1252,uint32,8,list_length
file_info,1284,uint32,0,data_start
file_info,1288,uint64,0,data_length
file_info,1296,uint64,0,context_start
file_info,1304,uint32,0,context_length
file_info,1308,uint64,0,annote_start
file_info,1316,uint32,0,annote_length
file_info,1320,uint64,0,total_size
axis_info,1328,uint32,8,unit_location
"""

prefix_table = {
  -8: 'Yotta',
  -6: 'Exa',
  -7: 'Zetta',
  -5: 'Pecta',
  -4: 'Tera',
  -3: 'Giga',
  -2: 'Mega',
  -1: 'Kilo',
  0: 'None',
  1: 'Milli',
  2: 'Micro',
  3: 'Nano',
  4: 'Pico',
  5: 'Femto',
  6: 'Atto',
  7: 'Zepto',
}

unit_table = {
  0: 'None',
  1: 'Abundance',
  2: 'Ampere',
  3: 'Candela',
  4: 'Celsius',
  5: 'Coulomb',
  6: 'Degree',
  7: 'Electronvolt',
  8: 'Farad',
  9: 'Sievert',
  10: 'Gram',
  11: 'Gray',
  12: 'Henry',
  13: 'Hertz',
  14: 'Kelvin',
  15: 'Joule',
  16: 'Liter',
  17: 'Lumen',
  18: 'Lux',
  19: 'Meter',
  20: 'Mole',
  21: 'Newton',
  22: 'Ohm',
  23: 'Pascal',
  24: 'Percent',
  25: 'Point',
  26: 'Ppm',
  27: 'Radian',
  28: 'Second',
  29: 'Siemens',
  30: 'Steradian',
  31: 'Tesla',
  32: 'Volt',
  33: 'Watt',
  34: 'Weber',
  35: 'Decibel',
  36: 'Dalton',
  37: 'Thompson',
  38: 'Ugeneric', 
  39: 'LPercent ', 
  40: 'PPT', 
  41: 'PPB ', 
  42: 'Index',
}

value_type_table = {
  0: 'String',
  1: 'Integer',
  2: 'Float',
  3: 'Complex',
  4: 'Infinity',
}


def parse_jdf_header(file_content):
    if struct.unpack("8s", file_content[0:8])[0].decode() != "JEOL.NMR":
        raise TypeError("not a nmr file")
        
    header = parse_by_specification(file_content, 0, True, spec)

    header.file_info.big_endian = False if header.file_info.endian else True
    
    if int(header.file_info.control_byte[0] & int("00000001", 2)):
        header.file_info.element_type = np.double
    elif int(header.file_info.control_byte[0] & int("01000000", 2)):
        header.file_info.element_type = np.single
    else:
        raise TypeError("unknown element type")
    
    try:
        header.experiment_info.spectrum_type = {1: '1D', 2: '2D', 12: 'Small_2D',}[int.from_bytes(
                          header.file_info.control_byte) & int("00111111", 2)]
    except KeyError:
        raise NotImplementedError(" more then two dimensions")
    if header.experiment_info.spectrum_type != "1D":
        raise NotImplementedError(" two dimensions")
    
    header.file_info.param_size = read_value(file_content, header.file_info.param_start,
                                                 header.file_info.big_endian, "uint32", 0)
    header.file_info.param_low_index = read_value(file_content, header.file_info.param_start+4,
                                                 header.file_info.big_endian, "uint32", 0)
    header.file_info.param_high_index = read_value(file_content, header.file_info.param_start+8,
                                                 header.file_info.big_endian, "uint32", 0)
    header.file_info.param_total_size = read_value(file_content, header.file_info.param_start+12,
                                                 header.file_info.big_endian, "uint32", 0)
    
    return header 

def parse_jdf_params(file_content, param_number, start, big_endian):
    # parse params of following structure:
    
    # |xxxx||scaler||       unit     ||          value                      || 32 bytes
    # |    type   ||                   name                                 || 32 bytes
    # xxxx - 4 empty bytes
    # scaler - uint16
    # unit(s) - 10 bytes
    # value 16 bytes
    # valuetype uint32
    # name string 28 bytes
    
    ptr = start
    params = {}
    for i in range(param_number):
        # print(i, ptr, end=", ")
        scaler = read_value(file_content, ptr+4, big_endian, "uint16", 0)
        # print(scaler, end=", ")
        units = get_units(file_content, 5, ptr+6, big_endian)
        # print(units, end=", ")
        value_type = value_type_table[read_value(file_content, ptr+32, big_endian, "uint32", 0)]
        # print(value_type, end=", ")
        value_name = read_value(file_content, ptr+36, big_endian, "string", 28)
        value_name = value_name[:value_name.find("\x00")]
        value_name = value_name[:value_name.find(" ")]
        # print(value_name, end=", ")
        if value_type == "String":
            value = read_value(file_content, ptr+16, big_endian, "string", 16)
            value = value[:value.find("\x00")]
            value = value[:value.find("  ")]
        elif value_type == "Integer":
            value = read_value(file_content, ptr+16, big_endian, "int32", 0)
        elif value_type == "Float":
            value = read_value(file_content, ptr+16, big_endian, "float64", 0)
        elif value_type == "Complex":
            a = read_value(file_content, ptr+16, big_endian, "float64", 0)
            b = read_value(file_content, ptr+24, big_endian, "float64", 0)
            value = b+a*1j if big_endian else a+b*1j
        elif value_type == "Infinity":
            value = read_value(file_content, ptr+16, big_endian, "int32", 0)
        # print(value)
        params[value_name] = (scaler, units, value)
        ptr += 64
    return params

def get_units(file_content, number_of_units, start, big_endian):
    ptr = start
    unit_list = []
    for i in range(number_of_units):
        byte = read_value(file_content, ptr, big_endian, "byte", 0)
        # prefix = prefix_table[int.from_bytes(byte[0:1] >> 4)]
        
        prefix = prefix_table.get(int.from_bytes(byte[0:1]) >> 4, "None")
        
        # power = int.from_bytes(byte[0:1] & int("00001111", 2))
        power = int.from_bytes(byte[0:1]) & int("00001111", 2)

        unit = unit_table[read_value(file_content, ptr+1, big_endian, "int8", 0)]
        unit_list.append((prefix, power, unit))
        ptr += 2
    return unit_list

def jdf_info(params, header):
    
    spectrum_center_ppm = params["X_OFFSET"][2]
    spectrum_center_Hz = params["X_FREQ"][2] * spectrum_center_ppm / 1000000
    spectral_width = params["X_SWEEP_CLIPPED"][2]
    plot_end = spectrum_center_Hz - spectral_width / 2
    plot_begin = spectrum_center_Hz + spectral_width / 2
    
    info = SpectrumInfo(
        plot_begin = plot_begin, 
        plot_end = plot_end,
        plot_begin_ppm = plot_begin / params["X_FREQ"][2],
        plot_end_ppm = plot_end / params["X_FREQ"][2],
        spectral_width = spectral_width,
        acquisition_time = params["x_acq_time"][2],
        obs_nucl_freq = params["X_FREQ"][2],
        dwell_time = params["x_acq_time"][2] / header.axis_info.element_number[0],
        frequency_increment = spectral_width / header.axis_info.element_number[0],
        group_delay = 0, # TO BE DONE
        vendor = "jeol",
        solvent = params["solvent"][2],
        samplename = header.experiment_info.title,
        nucleus = params["X_DOMAIN"][2],
        )
    
    return info


        


        
                
    
        
        
        
        
        
        
        