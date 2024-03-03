# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 14:19:35 2024

@author: Jan
"""
import readingfids
import numpy as np



class Spectrum_1D:
    # class will contain only universal methods, if needed they may call format-specific
    # functions from readingfids
    # class instantion should be created via classmethod create_from_file(path, file_type)
    # instantions for testing with specific data may be created directly
    
    def __init__(self, procpar, headers, info, fid, spectrum=None):
        # init shall not be format-specific
        
        # private variables
        self._headers = headers # list of headers starting with file header then block ones
        self._fid = fid[0] # free induction decay data
        self._procpar = procpar # dictionary of processing parameters in raw form, 
        # it may be deleted later if deemed to memory consuming
        
        # public variables
        self.info = info # shall contain info about spectrum which may be displayed,
        # such us experiment type, date, samplename, etc.
        
        # self.spectrum shall contain ready-to-draw spectrum as its y-values, 
        # information about x-values shall be contained in info (spectrum is usually uniformly sampled)
        if not spectrum:
            self.spectrum = self.generate_power_mode_spectrum()
        else:
            self.spectrum = spectrum
        
    @classmethod
    def create_from_file(cls, path):
        #to be considered: open() exceptions 
        
        ftype = readingfids.fid_file_type(path)
        if ftype == "agilent":
            fid_content, procpar_lines = readingfids.open_experiment_folder_agilent(path)
            procpar = readingfids.read_agilent_procpar(procpar_lines)
            headers, fid = readingfids.read_agilent_fid(fid_content)
            info = readingfids.info_agilent(procpar)
        else:
            raise NotImplementedError
        
        return cls(procpar, headers, info, fid)
    
    def generate_power_mode_spectrum(self):
        ft_rl = np.fft.fft(np.real(self._fid))
        ft_im = np.fft.fft(np.imag(self._fid))
        # simplified spectrum not suitable for anything, 
        # though good for display prototyping
        pow_spectr = [(i*i + j*j) for i, j in zip(
            np.real(ft_rl[:len(ft_rl)//2]), np.imag(ft_im[:len(ft_im)//2]))]
        return pow_spectr
    
if __name__ == "__main__":
    path = "./example_fids/agilent_example1H.fid"
    widmo = Spectrum_1D.create_from_file(path)
    
    