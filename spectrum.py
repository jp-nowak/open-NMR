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
    
    def __init__(self, ft_rl, ft_im, info, path, spectrum=None):
        # init shall not be format-specific
        
        # private variables
        self._ft_rl = ft_rl
        self._ft_im = ft_im
        
        # public variables
        self.info = info # shall contain info about spectrum which may be displayed,
        # such us experiment type, date, samplename, etc.
        
        # self.spectrum shall contain ready-to-draw spectrum as its y-values, 
        # information about x-values shall be contained in info (spectrum is usually uniformly sampled)
        if spectrum is None:
            self.spectrum = self.generate_absorption_mode_spectrum()
        else:
            self.spectrum = spectrum
            
        # string containing path to file from which object was created
        self.path = path
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
        
        ft_rl = np.fft.fft(np.real(fid[0]))
        ft_im = np.fft.fft(np.imag(fid[0]))
        
        return cls(ft_rl, ft_im, info, path)
    
    
    def generate_power_mode_spectrum(self):
        # simplified spectrum not suitable for anything, 
        # though good for display prototyping
        pow_spectr = [(i*i + j*j) for i, j in zip(
            np.real(self._ft_rl[:len(self._ft_rl)//2]), np.imag(self._ft_im[:len(self._ft_im)//2]))]
        return pow_spectr
    
    def generate_absorption_mode_spectrum(self):
        # first prototype

        rl_ft_rl = np.real(self._ft_rl)

        im_ft_im = np.imag(self._ft_im)
        length = len(rl_ft_rl)
        
        spectrum_left = [i-j for i,j in zip(rl_ft_rl[:length//2], im_ft_im[:length//2])]
        spectrum_left = spectrum_left[::-1]
        
        spectrum_rigth = [i+j for i,j in zip(rl_ft_rl[:length//2], im_ft_im[:length//2])]

        # consider other half of fid

        
        return np.array(spectrum_left + spectrum_rigth)
    
if __name__ == "__main__":
    path = "./example_fids/agilent_example1H.fid"
    widmo = Spectrum_1D.create_from_file(path)
    
    