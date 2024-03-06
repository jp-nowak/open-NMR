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
    
    def __init__(self, fid, info, path, spectrum=None):
        # init shall not be format-specific
        
        # private variables
        self._fid = fid
        
        # public variables
        self.info = info # shall contain info about spectrum which may be displayed,
        # such us experiment type, date, samplename, etc.
        self.zero_order_phase_corr = 0
        # self.spectrum shall contain ready-to-draw spectrum as its y-values, 
        # information about x-values shall be contained in info (spectrum is usually uniformly sampled)
        
        
        optimal_zero_order_phase_correction = self.opt_zero_order_phase_corr(0, 0.0001)
        self.corr_zero_order_phase(optimal_zero_order_phase_correction)
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
        

        
        return cls(fid[0], info, path)
    
    
    def generate_power_mode_spectrum(self):
        # simplified spectrum not suitable for anything, 
        # though good for display prototyping
        ft_rl = np.fft.fft(np.real(self._fid))
        ft_im = np.fft.fft(np.imag(self._fid))
        pow_spectr = [(i*i + j*j) for i, j in zip(
            np.real(ft_rl[:len(ft_rl)//2]), np.imag(ft_im[:len(ft_im)//2]))]
        return pow_spectr
    
    def generate_absorption_mode_spectrum(self):
        # first prototype
        ft_rl = np.fft.fft(np.real(self._fid))
        ft_im = np.fft.fft(np.imag(self._fid))
        rl_ft_rl = np.real(ft_rl)

        im_ft_im = np.imag(ft_im)
        length = len(rl_ft_rl)
        
        spectrum_left = [i-j for i,j in zip(rl_ft_rl[:length//2], im_ft_im[:length//2])]
        spectrum_left = spectrum_left[::-1]
        
        spectrum_rigth = [i+j for i,j in zip(rl_ft_rl[:length//2], im_ft_im[:length//2])]

        # consider other half of fid

        
        return np.array(spectrum_left + spectrum_rigth)
    
    def corr_zero_order_phase(self, angle):
        # angle is an number of pi*radian by which to "turn" phase. 2 is identity.
        # angle = 2 -> turn by 2 pi radians -> 360 degree
        self.zero_order_phase_corr += angle
        self._fid = self._fid*np.exp(angle*1j*np.pi)
        
    def opt_zero_order_phase_corr(self, start, precision):
        fid = self._fid.copy()
        def spectrum_sum():
            nonlocal fid
            rl_ft_rl = np.real(np.fft.fft(np.real(fid)))
            im_ft_im = np.imag(np.fft.fft(np.imag(fid)))
            length = len(rl_ft_rl)
            spectrum = [i-j for i,j in zip(rl_ft_rl[:length//2], im_ft_im[:length//2])]
            spectrum = spectrum[::-1]
            spectrum = spectrum + [i+j for i,j in zip(rl_ft_rl[:length//2], im_ft_im[:length//2])]
            maximum = sum(spectrum)
            return maximum
        angle = start
        maximum = spectrum_sum()
        step = 1
        i = 0
        while True:
            i += 1
            fid = fid*np.exp(step*1j*np.pi)
            current = spectrum_sum()
            angle += step
            improved = False
            if current > maximum:
                improved = True
                maximum = current
            else:
                angle -= step
                fid = fid*np.exp(-step*1j*np.pi)
                step /= 10
            if step < precision:
                break
            
        if improved == False:
            #TODO counter clockwise correction
            pass
        
        
        return angle
                
            
            
        
        
if __name__ == "__main__":
    path = "./example_fids/agilent_example1H.fid"
    widmo = Spectrum_1D.create_from_file(path)
    
    