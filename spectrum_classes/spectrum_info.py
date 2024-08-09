from dataclasses import dataclass, replace



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
    
    obs_nucl_freq : float # [MHz] Larmor frequency of observed nucleus
    
    dwell_time : float # [s] time between data points of fid
    frequency_increment : float # [Hz] distance between points of spectrum
    
    group_delay : float # [number of points] delayed by technical aspects of aquisition
    
    vendor : str # producer of spectrometer
    solvent : str # solvent in which spectrum was measured
    samplename : str #
    nucleus : str # observed nucleus
    
    def __getitem__(self, key):
        return getattr(self, key)
    
    def copy(self):
        return replace(self)
    
if __name__ == "__main__":
    info = SpectrumInfo(0, 0, 0, 0, 0, 0, 0, 0, 0, "", "", "", "")
    
