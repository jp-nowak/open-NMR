# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 14:19:35 2024

@author: Jan
"""
import readingfids
import numpy as np
import os


class Spectrum_1D:
    # class will contain only universal methods, if needed they may call format-specific
    # functions from readingfids
    # class instantion should be created via classmethod create_from_file(path, file_type)
    # instantions for testing with specific data may be created directly
    
    def __init__(self, fid, info, path, spectrum=None):
        # init shall only create instance atributes
        
        # private variables
        
        # np.array of complex32 - raw fid
        self._fid = fid
        
        # float - value used to calculate relative integral values as following:
        # relative_value = real_value/self._integral_rel_one
        self._integral_rel_one = None
        
        # float - minimal y-value for signal to be considered non zero in integration etc.
        self._signal_treshold = None
        
        #--------------------------------------
        # public variables
        
        # string containing path to file from which object was created
        self.path = path
        
        # dictionary - shall contain info about spectrum
        # its guaranteed keys are listed at the end of file
        self.info = info 
        
        # list of calculated integrals, in format:
        # (integral_begin, integral_end, real_value, relative value)
        self.integral_list = []
        
        # float - stores information about applied zero order phase correction [pi rad]
        self.zero_order_phase_corr = 0        
        optimal_zero_order_phase_correction = self.opt_zero_order_phase_corr(0, 1, 0.0001)
        self.corr_zero_order_phase(optimal_zero_order_phase_correction)
        # self.corr_zero_order_phase(0)
        
        # np.array of float - self.spectrum shall contain ready-to-draw spectrum as its y-values, 
        # information about x-values shall be contained in info (spectrum is usually uniformly sampled)
        if spectrum is None:
            self.spectrum = self.generate_absorption_mode_spectrum()
        else:
            self.spectrum = spectrum
        #print(sum(self.spectrum))
        #--------------------------------------
        # setting values of private variables declared earlier
        
        # value to be decided - placeholder currently
        self._signal_treshold = np.average(self.spectrum)/2
    
    @classmethod
    def create_from_file(cls, path):
        #to be considered: open() exceptions 
        path = os.path.abspath(path)
        ftype = readingfids.fid_file_type(path)
        if ftype == "agilent":
            info, fid = readingfids.agilent_wrapper(path)
        elif ftype == "bruker":
            info, fid = readingfids.bruker_wrapper(path)
        else:
            raise NotImplementedError(f"not implemented file format: {ftype}")
        
        
        
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
        # # # 
        ft = np.fft.fft(self._fid)
        left_half = ft[:len(ft)//2][::-1]
        rigth_half = ft[len(ft)//2:][::-1]
        spectrum = np.real(np.concatenate((left_half, rigth_half)))
        
        if self.info["vendor"] == "bruker":
            spectrum = spectrum[::-1]
        
        return spectrum
    
    def integrate(self, begin, end, vtype="fraction"):
        """
        Function to integrate, it appends self.integral_list, and may modify self._integral_rel_one
        as its side effects
        
        Parameters
        ----------
        begin : numeric value [ppm or fraction]
            Start of integral in ppm scale or as fraction of spectrum
        end : numeric value [ppm or fraction]
            End of integral in ppm scale or as fraction of spectrum
        Their order is irrelevant
        If vtype == "fraction" 0 is assumed to mean left edge of spectrum,
        and 1 right edge

        Returns
        -------
        tuple: (begin, end, real_value, relative value)
        
            begin, end: numeric
            same values as arguments though, if arguments are in ppm they are converted 
            to fraction 
            
            real_value: numeric
            value of integration of part of self.spectrum starting
            with begin and ending with end.
            
            relative_value: numeric
            if it is a first integration relative value is equal to one,
            and self.integral_one is set to its real_value
            If it is a next integral it is equal to real_value/self.integral_rel_one
            
        *******
         the same tuple is appended to self.integral_list
        """
        # to be added: checking input validity
        
        # translation of values in ppm or fraction to data points number
        
        if vtype == "ppm":
            if begin < end: 
                begin, end = end , begin
                
            begin = begin - self.info["plot_begin_ppm"]
            begin = begin/(self.info["plot_end_ppm"] - self.info["plot_begin_ppm"])
            begin = 1 - begin
            
            end = end - self.info["plot_begin_ppm"]
            end = end/(self.info["plot_end_ppm"] - self.info["plot_begin_ppm"])
            end = 1 - end
            
        elif vtype == "fraction":
            if begin > end:
                begin, end = end, begin
        else:
            raise ValueError
            
        begin_point = round(begin*len(self.spectrum))
        end_point = round(end*len(self.spectrum))
        
        # setting low values to zero, it allows broad integrals where there are no peaks
        # to be equal to zero
        peak_values = self.spectrum[begin_point:end_point]
        peak_values[peak_values < self._signal_treshold] = 0
        
        # numerical integration - trapezoid rule, 
        # to be considered simpsons rule or simple summation
        real_value = np.trapz(peak_values, dx=0.001)
        
        if not self.integral_list:
            relative_value = 1.0
            self._integral_rel_one = real_value
        else:
            if self._integral_rel_one is None:
                raise ValueError
            relative_value = real_value/self._integral_rel_one
        
        self.integral_list.append((begin, end, real_value, relative_value))
        return (begin, end, real_value, relative_value)
    
    def x_coordinate(self, x_value, vtype, out_type):
        """
        Conversion of x coordinate between different units:
            "ppm" delta scale
            "fraction" fraction of spectrum: 0 - left edge, 1 - right edge
            "Hz" relative frequency of point
            "data_point" only as out_type: number of closest data point from self.spectrum

        Parameters
        ----------
        x_value : numeric
            DESCRIPTION.
        vtype : string
            scale of input.
        out_type : string
            desired output scale.

        Returns
        -------
        x_value : numeric
            x_coordinates in scale specified in out_type.

        """
        
        
        if vtype=="ppm":
            x_value = x_value - self.info["plot_begin_ppm"]
            x_value = x_value/(self.info["plot_end_ppm"] - self.info["plot_begin_ppm"])
            x_value = 1 - x_value
        elif vtype=="fraction":
            pass
        elif vtype=="Hz":
            x_value = x_value - self.info["plot_begin"]
            x_value = x_value/(self.info["plot_end"] - self.info["plot_begin"])
        else:
            raise NotImplementedError
            
        if out_type=="ppm":
            x_value = x_value*(self.info["plot_end_ppm"] - self.info["plot_begin_ppm"])
            x_value = x_value+self.info["plot_begin_ppm"]
        elif out_type=="fraction":
            pass
        elif out_type=="Hz":
            x_value = 1 - x_value
            x_value = x_value*(self.info["plot_end"] - self.info["plot_begin"])
            x_value = x_value + self.info["plot_begin"]
        elif out_type=="data_point":
            x_value = round(x_value*len(self.spectrum))
        
        return x_value
            
            
    
    def corr_zero_order_phase(self, angle):
        # angle is an number of pi*radian by which to "turn" phase. 2 is identity.
        # angle = 2 -> turn by 2 pi radians -> 360 degree
        self.zero_order_phase_corr += angle
        self._fid = self._fid*np.exp(angle*1j*np.pi)
        
        
    def opt_zero_order_phase_corr(self, start, first_step, precision):
        # temporary solution, later proper algorithm will be implemented
        fid = self._fid.copy()
        
        def spectrum_sum():
            nonlocal fid

            ft = np.fft.fft(fid)
            left_half = ft[:len(ft)//2][::-1]
            rigth_half = ft[len(ft)//2:][::-1]
            spectrum = np.real(np.concatenate((left_half, rigth_half)))
            score = 0
            
            for i in spectrum:
                if i > 0:
                    score += i
                else:
                    score += -i*i
            return score
            
        angle = start
        maximum = spectrum_sum()
        step = first_step
        improved = False
        #print(angle, maximum)
        while True:
            fid = fid*np.exp(step*1j*np.pi)
            current = spectrum_sum()
            angle += step
            #print(angle, current)
            if current > maximum:
                maximum = current
                improved = True
                #print("better")
            else:
                #print("not really")
                angle -= step
                fid = fid*np.exp(-step*1j*np.pi)
                step /= 10
            if abs(step) < precision:
                if not improved:
                    #print("reversing!")
                    step = -first_step
                    improved = True
                    continue
                #print("end")
                break
            
        return angle
                
# self.info - guaranteed keys:
    # "solvent"        : string
    # "lock_freq"      : float [MHz] lock (deuterium) frequency of spectrometer
    # "samplename"     : string
    # "nucleus"        : string observed nucleus e.g.: H1, C13 etc.
    # "spectral_width" : float [Hz] width of spectrum
    # "obs_nucl_freq"  : float [MHz] Larmor frequency of observed nucleus
    # "plot_begin"     : float [Hz] beginning of plot
    # "plot_end"       : float [Hz] end of plot
    # "plot_ppm"       : float [ppm] beginning of plot
    # "plot_ppm"       : float [ppm] end of plot
    # "quadrature"     : bool: true - fid as complex numbers
    # "vendor"         : string producer of spectrometer
        
if __name__ == "__main__":
    nmr_file_path = "D:/projekt nmr/open-NMR/example_fids/agilent/agilent_example1H.fid"
    widmo = Spectrum_1D.create_from_file(nmr_file_path)
    widmo.integrate(8.277, 8.044, vtype="ppm")
    widmo.integrate(7.546, 7.409, vtype="ppm")
    widmo.integrate(4.294, 4.148, vtype="ppm")
    widmo.integrate(2.143, 1.964, vtype="ppm")
    widmo.integrate(1.358, 1.207, vtype="ppm")
    
    widmo.integrate(12, 11, vtype="ppm") # there is no peak there
    
    #np.savetxt('widmo.txt', widmo.spectrum, fmt='%4.6f', delimiter=' ')
    print(*widmo.integral_list, sep='\n')
    
    a = widmo.x_coordinate(-1, vtype="ppm", out_type="Hz")
    print(a)
    