import json
import numpy
import myplot
import math
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import pulse_processing
from scipy.stats import norm

FPGA_CLK_FREQ_GHZ = 0.09375
PPS_TO_PULSE_TIME_INTERVAL = 5.e-5
NUPHASE_VPOL_CH = 7

def getStatusReadoutTime(status_dict):
     readout_time_stat_sec =numpy.array(numpy.array(status_dict['readout_time'])-min(status_dict['readout_time']), dtype=float)
     full_readout_time_status=readout_time_stat_sec+numpy.array(status_dict['readout_time_ns'], dtype=float)*1.e-9

     return full_readout_time_status

def getEventReadoutTime(event_dict):
    readout_time_event_sec=numpy.array(numpy.array(event_dict['readout_time'])-min(event_dict['readout_time']), dtype=float)
    full_readout_time_event =readout_time_event_sec+numpy.array(event_dict['readout_time_ns'], dtype=float)*1.e-9

    return full_readout_time_event

def getTestPulses(event_dict, status_dict=None, outfile=None, mode='time'):

    if event_dict.split('.')[-1] == 'json':
        with open(event_dict,'r') as f:
            event_dict = json.load(f)

    full_readout_time_event=getEventReadoutTime(event_dict)

    new_trig_time=[]
    add_value=0
    
    for i in range(len(event_dict['trig_time'])):
         if i > 1 and ((event_dict['trig_time'][i]+add_value) < (event_dict['trig_time'][i-1]+add_value)):
              add_value=add_value+pow(2,32)
         new_trig_time.append(event_dict['trig_time'][i]+add_value)
            
    #the cal pulser dict to save
    test_pulser={}
    test_pulser['trig_time']=[]
    test_pulser['readout_time']=[]
    test_pulser['snr']=[]
    test_pulser['event_num']=[]

    vpp_cut = 25
    # simply look for events with high-amplitude pules
    for i in range(len(event_dict['ev_event_num'])):

         if  numpy.max(numpy.array(event_dict['wave_snr_vpp'][i]).tolist()) > vpp_cut:

              test_pulser['trig_time'].append(new_trig_time[i])
              test_pulser['readout_time'].append(full_readout_time_event[i])
              test_pulser['snr'].append(numpy.array(event_dict['wave_snr_vpp'][i]).tolist())
              test_pulser['event_num'].append(event_dict['ev_event_num'][i])

                
    print 'found',len(test_pulser['event_num']), 'test pulse events'
    
    if outfile is not None:
        with open(outfile, 'w') as f:
            json.dump(test_pulser, f)

    return test_pulser

def makePulseAverage(chain, channels=12, wfm_length=512, upsample_factor=60, save=True ):
     
    volts=numpy.zeros((channels+1, wfm_length*upsample_factor))
    num=0
    
    for i in range(chain.GetEntries()):
         pulse = pulse_processing.PulseProcess(buffer_length = 512, channels=channels)
         pulse.getFromROOTTree(chain, i, channels=channels)

         pulse.upsample(upsample_factor)


         #for j in range(12):
         #      plt.figure(100)
         #      plt.plot(pulse.wave[j].voltage-j*30 )
         #plt.show()

         if numpy.max(pulse.wave[0].voltage) < 20:
              continue

         ret=pulse.alignUsingPeak(len(pulse.wave[0].voltage)/2)
         
         if ret==None:
              continue

         num=num+1
         for j in range(channels):
              volts[j] = volts[j] + pulse.wave[j].voltage

         volts[channels] = pulse.wave[0].time


    volts[0:channels] = volts[0:channels] / (num)

    if save:
         numpy.savetxt('test_bench_pulser.txt', volts, delimiter='\t')

    for i in range(channels):
         plt.plot(volts[channels], volts[i]- i * 20)
    plt.show()

    return volts, num

def getTestPulseTime(event_root_dir,  upsample_factor=60):

     chain = pulse_processing.makeROOTChainFromRun(event_root_dir)

     pulse_template = '/home/ejo/nuphase-analysis/data/test_bench_pulser.txt'
     pulse_template = numpy.loadtxt(pulse_template)
     template_pulse = pulse_processing.PulseProcess(data=pulse_template)
     
     time=[]
     #for i in range(chain.GetEntries()):
     for i in range(400):

          pulse = pulse_processing.PulseProcess(buffer_length = 512, channels=12)
          pulse.getFromROOTTree(chain, i, channels=12)

          if numpy.max(pulse.wave[0].voltage) < 20:
               continue
          #for j in range(12):
          #     plt.figure(100)
          #     plt.plot(pulse.wave[j].voltage - j*50)
          #plt.show()
          pulse.upsample(upsample_factor)

          t, cor = pulse.alignUsingCrossCor(len(pulse.wave[0].voltage)/2, template_pulse, corr_cut=0.4)

          if t is not None:
               time.append(numpy.array(t))
               
     return time

def getTimeDifference(time,channels=12):

     t_diff=[]
     for i in range(len(time)):
          _t_diff=[]
          bad=0
          for j in range(channels):
               if time[i][j]-time[i][0] > 5 or  time[i][j]-time[i][0] < -5:
                    bad=1
                    break
               _t_diff.append(time[i][j]-time[i][2])

          if bad == 0:
               t_diff.append(numpy.array(_t_diff))

          
     return t_diff

def histogram(time, subplots_x = 4, subplots_y=3):

     
     fig, ax = plt.subplots(subplots_y, subplots_x)
     
     ax = ax.flatten()

     #label = ['CH1-0','CH2-0','CH3-0','CH4-0','CH5-0','CH6-0','CH7-0','CH8-0','CH9-0','CH10-0','CH11-0']
     label = ['CH0-2','CH1-2','CH2-2','CH3-2','CH4-2','CH5-2','CH6-2','CH7-2','CH8-2','CH9-2','CH10-2','CH11-2']


     for i in range(time.shape[1]):
          (mu, sigma) = norm.fit(time[:,i])
          
          n, bins, patches = ax[i].hist(time[:,i], bins=58, range=(-2.6, 0.6), facecolor='black', alpha=0.5, normed=True)
          y = mlab.normpdf( bins, mu, sigma)
          ax[i].plot(bins, y, 'r--', lw=2)
          ax[i].text(0.05,0.9,label[i], transform=ax[i].transAxes)
          ax[i].text(0.05,0.8,'mn={0:.3f} ns'.format(mu), transform=ax[i].transAxes)
          ax[i].text(0.05,0.7,'sg={0:.3f} ns'.format(sigma), transform=ax[i].transAxes)

          

     
     plt.show()
     
     


if __name__=='__main__':

    directory='../runs/run178/'
    ev_num_prefix = 180000000001
    output_root_dir = '/project/avieregg/nuphase01/pole2018/rootified/'+'run178'+'/event/'

    chain = pulse_processing.makeROOTChainFromRun(output_root_dir)

    #makePulseAverage(chain)
    
    time = getTestPulseTime(output_root_dir)

    time = numpy.array(getTimeDifference(time))


    histogram(time)
    plt.plot(time)
    plt.show()

