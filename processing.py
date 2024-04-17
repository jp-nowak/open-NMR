import numpy as np

POWERS_OF_TWO = (1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 
2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288, 
1048576, 2097152, 4194304, 8388608, 16777216, 33554432, 67108864, 
134217728, 268435456, 536870912, 1073741824, 2147483648, 4294967296, 8589934592)

def zero_fill_to_power_of_two(fid):
    if len(fid) in POWERS_OF_TWO:
        return fid
    for i in POWERS_OF_TWO:
        if i > len(fid):
            fid = np.concatenate((fid, np.zeros(i-len(fid), dtype=fid.dtype)))
            return fid

def zero_fill_to_number(fid, number):
    if number < len(fid):
        return fid
    fid = np.concatenate((fid, np.zeros(number-len(fid), dtype=fid.dtype)))
    return fid

class apodize:
    @staticmethod
    def exponential(fid, dwell_time, constant):
        multipliers = np.array([np.exp(-i*dwell_time*constant*np.pi) for i in range(len(fid))])
        for i in range(len(fid)):
            fid[i] = fid[i] * multipliers[i]