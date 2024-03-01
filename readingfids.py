import struct
import collections
import os
import numpy as np
import itertools
import matplotlib.pyplot as plt
import math

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
    el_specifier = ">ff"
    el_type = np.csingle
    el_size = 2 * header0.ebytes if el_type == np.csingle else header0.ebytes
    bl_el_number = header0.np // 2 if el_type == np.csingle else header0.np
    fids = []
    def read_element(element):
        #print(element)
        rl, im = element
        #print(rl)
        result = rl + im*1j
        return result
        
    for i1 in range(header0.nblocks):
        print("block number:", i1, end="  ")
        for i2 in range(header0.nbheaders):
            headers.append(DataBlockHead(*struct.unpack(">hhhhlffff", file_content[ptr:ptr+28]), i2))
            ptr += 28
            print("header in block: ", i2)
        for i3 in range(header0.ntraces):
            fid = np.zeros(bl_el_number, dtype = el_type)
            print("trace in block:", i3)
            print("fid start:", ptr)
            for i4 in range(bl_el_number):
                #print(struct.unpack(el_specifier, file_content[ptr:ptr+el_size]))
                fid[i4] = read_element(struct.unpack(el_specifier, file_content[ptr:ptr+el_size]))
                ptr += el_size
            fids.append(fid)
            print("fid end:", ptr)
    print("koniec")       
    return headers, fids

if __name__ == "__main__":
    nmr_file_path = "fid"
    with open(nmr_file_path, "rb") as file:
        file_content = file.read()

    headers, fids = read_agilent_fid(file_content)

    ft_rl = np.fft.fft(np.real(fids[0]))
    ft_im = np.fft.fft(np.imag(fids[0]))
    print("ft")
    # simplified spectrum not suitable for anything, 
    # though good for display prototyping
    pow_spectr = [(i*i + j*j) for i, j in zip(
        np.real(ft_rl[:len(ft_rl)//2]), np.imag(ft_im[:len(ft_im)//2]))]

    fig, ax = plt.subplots(dpi = 1200)
    ax.plot(pow_spectr, linewidth=0.2, color='red')
    fig.savefig("spektrum.png")
