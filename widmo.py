from readingfids import *

class Widmo:
    def __init__(self):
        # is it fid
        # type of fid
        # method of reading fid
        self.piki = None
        self.widmo = None
        pass
    def agilent_read(self, fid):
        headers, fids = read_agilent_fid(fid)
        ft_rl = np.fft.fft(np.real(fids[0]))
        ft_im = np.fft.fft(np.imag(fids[0]))
        self.widmo = [(i*i + j*j) for i, j in zip(np.real(ft_rl[:len(ft_rl)//2]), np.imag(ft_im[:len(ft_im)//2]))]
    def integracja(self):
        pass
