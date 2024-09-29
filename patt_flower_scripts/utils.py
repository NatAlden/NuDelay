import sys
sys.path.append('/home/rno-g/flowerpy')
import flower_trig, flower
import time
import numpy as np

def get_coinc_rate(n_ave = 10):
    trig = flower_trig.FlowerTrig()
    trig.trigEnable(coinc_trig=1)
    ave_rate = 0
    for i in range(n_ave):
        time.sleep(0.05)
        trig.setScalerOut(3)  #replace 3 by 0 if it doesn't work (it changes with FLOWER firmware updates)
        ave_rate += trig.readSingleScaler()[0]/n_ave
    return ave_rate

def get_coinc_rate_phased(n_ave = 10):
    trig = flower_trig.FlowerTrig()
    trig.trigEnable(phased_trig=1)
    ave_rate = 0
    for i in range(n_ave):
        time.sleep(0.05)
        trig.setScalerOut(18)
        ave_rate += trig.readSingleScaler()[0]/n_ave
    return ave_rate

def get_peak2peak(n_ave = 50):
    dev = flower.Flower()
    trig = flower_trig.FlowerTrig()
    trig.trigEnable(coinc_trig=1)
    
    nchans = 4
    peak2peak = [0, 0, 0, 0]
    for i in range(n_ave):
        dev.bufferClear() 
        time.sleep(0.005)
        dat= dev.readRam(dev.DEV_FLOWER, 0, 256)
        for ch in range(nchans):
            peak2peak[ch] += (np.max(dat[ch]) - np.min(dat[ch]))/n_ave
    
    dev.bufferClear()
    return(peak2peak)

def get_peak2peak_phased(n_ave = 50):
    dev = flower.Flower()
    trig = flower_trig.FlowerTrig()
    trig.trigEnable(phased_trig=1)
    
    nchans = 4
    peak2peak = [0, 0, 0, 0]
    for i in range(n_ave):
        dev.bufferClear() 
        time.sleep(0.005)
        dat= dev.readRam(dev.DEV_FLOWER, 0, 256)
        for ch in range(nchans):
            peak2peak[ch] += (np.max(dat[ch]) - np.min(dat[ch]))/n_ave
    
    dev.bufferClear()
    return(peak2peak)

def get_noise_rms(n_ave = 100):
    dev = flower.Flower()

    nchans = 4
    ave_rms = [0, 0, 0, 0]
    for i in range(n_ave):
        dev.bufferClear()
        dev.softwareTrigger()
        dat= dev.readRam(dev.DEV_FLOWER, 0, 256)
        for ch in range(nchans):
            ave_rms[ch] += np.sqrt(np.mean((np.array(dat[ch])-127)**2))/n_ave
    dev.bufferClear()
    return(ave_rms)

if __name__ == "__main__":
    #print(get_peak2peak_phased())
    #print(get_coinc_rate_phased())
    #print(get_peak2peak())
    print(get_coinc_rate())
    #print(get_noise_rms())

