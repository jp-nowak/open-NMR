import numpy as np
import math

def data_prep(data, width, height, rang):
    data = data[round(len(data)*rang[0]):round(len(data)*rang[1])]
    data = np.column_stack((np.linspace(0, 1, len(data)), data))
    # normalize
    ymax = max(data[:, 1])
    ymin = min(data[:, 1])
    data[:, 1] = -(data[:, 1]-ymin)/(ymax-ymin)+1
    data = data*(width, height)
    new_method = True
    if not new_method:
        # downsampling, bad method, we need one for nmr spectra specifically
        pointperpixel = 100
        sample = max(len(data)//(pointperpixel*width), 1)
        # scaling to image size
        resampled = data[::sample]
        return resampled
    if new_method:
        resampled = []
        sample = int(len(data)//(width*2))
        if sample < 4:
            return data
        for pix in range(int(math.ceil(len(data)/sample))):
            start = pix*sample
            end = min((pix+1)*sample-1, len(data)-1)
            if start == end:
                resampled.append(data[-1])
                break
            if abs(max(data[start:end, 1])-min(data[start:end, 1])) > 1:
                resampled.extend(data[start:end])
            else:
                resampled.extend([data[start], data[end]])
        return resampled

def rearrange(boxlis):
    """
    rearranges boxlike (position,width) entities on a scale of 0,1 so that they don't overlap
    fast, unrealiable, cheap and cumbersome, also known as fucc
    """
    for n in range(30):
        tempboxlis = boxlis.copy()
        for i in range(len(boxlis)):
            for j in range(len(boxlis)):
                if i==j:continue
                diff = boxlis[i][0]-boxlis[j][0]
                if abs(diff)<1.5*(boxlis[i][1]/2+boxlis[j][1]/2):
                    tempboxlis[i][0] += 0.2*np.sign(diff)*abs(diff)
        boxlis = tempboxlis
    return boxlis