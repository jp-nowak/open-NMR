from dataclasses import dataclass, replace

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
    trimmed : float # [% of points] to be cut from edges of ft transformed spectrum
    # to ensure that it has correct positions in respect to x axis
    # used in ugly workaround for jeol spectra
    
    vendor : str # producer of spectrometer
    solvent : str # solvent in which spectrum was measured
    samplename : str # samplename
    nucleus : str # observed nucleus
    
    def __getitem__(self, key):
        return getattr(self, key)
    
    def copy(self):
        return replace(self)
    
if __name__ == "__main__":
    info = SpectrumInfo(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "", "", "", "")
    
