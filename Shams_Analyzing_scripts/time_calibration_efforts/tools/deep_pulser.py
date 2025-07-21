import json
import numpy
import myplot
import math
import matplotlib.pyplot as plt
import pulse_processing

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

def getDeepPulses(event_dict, status_dict=None, outfile=None, mode='time'):

    if event_dict.split('.')[-1] == 'json':
        with open(event_dict,'r') as f:
            event_dict = json.load(f)

    if status_dict is not None:
        if status_dict.split('.')[-1] == 'json':
            with open(status_dict,'r') as f:
                status_dict = json.load(f)

        full_readout_time_status = getStatusReadoutTime(status_dict)

    full_readout_time_event=getEventReadoutTime(event_dict)

    #fix trig time 
    if mode=='time':
        '''
        due to sw bug, earlier runs also had an issue w/ the trig_time rolling over at 32 bits. The following unrolls these times:
        '''
        new_trig_time=[]
        add_value=0
    
        for i in range(len(event_dict['trig_time'])):
            if i > 1 and ((event_dict['trig_time'][i]+add_value) < (event_dict['trig_time'][i-1]+add_value)):
                add_value=add_value+pow(2,32)
            new_trig_time.append(event_dict['trig_time'][i]+add_value)
            
        new_pps_time=[]
        add_value=0
        for i in range(len(status_dict['latched_pps'])):
            if i > 1 and ((status_dict['latched_pps'][i]+add_value) < (status_dict['latched_pps'][i-1]+add_value)):
                add_value=add_value+pow(2,32)
            new_pps_time.append(status_dict['latched_pps'][i]+add_value)

        new_pps_time_sec = (numpy.array(new_pps_time)*1./FPGA_CLK_FREQ_GHZ) * 1.e-9
        new_trig_time_sec =(numpy.array(new_trig_time)*1./FPGA_CLK_FREQ_GHZ) * 1.e-9 
    

    #the cal pulser dict to save
    find_deep_pulser={}
    find_deep_pulser['trig_time']=[]
    find_deep_pulser['readout_time']=[]
    find_deep_pulser['snr']=[]
    find_deep_pulser['event_num']=[]

    #if status_dict is not None:
    #    find_deep_pulser['glob_gated_scaler']=[]
    #    find_deep_pulser['beam_gated_scaler']=[]
    #    find_deep_pulser['readout_time_status']=[]

    vpp_cut = 50
    # simply look for events with high-amplitude pules
    for i in range(len(event_dict['ev_event_num'])):

         if  numpy.max(numpy.array(event_dict['wave_snr_vpp'][i]).tolist()) > vpp_cut:

              find_deep_pulser['trig_time'].append(new_trig_time[i])
              find_deep_pulser['readout_time'].append(full_readout_time_event[i])
              find_deep_pulser['snr'].append(numpy.array(event_dict['wave_snr_vpp'][i]).tolist())
              find_deep_pulser['event_num'].append(event_dict['ev_event_num'][i])

              #if status_dict is not None:
              #     find_deep_pulser['glob_gated_scaler'].append(status_dict['glob_scalers'][status_index[-1]+1][1])
              #     find_deep_pulser['beam_gated_scaler'].append(status_dict['beam_scalers'][status_index[-1]+1][1])
              #     find_deep_pulser['readout_time_status'].append(full_readout_time_status[status_index[-1]+1])
                
    print 'found',len(find_deep_pulser['event_num']), 'deep pulser events'
    
    if outfile is not None:
        with open(outfile, 'w') as f:
            json.dump(find_deep_pulser, f)

    return find_deep_pulser

def getDeepPulseTime(deep_pulse_dict, event_root_dir, ev_num_prefix, threshold, upsample_factor=60):

     chain = pulse_processing.makeROOTChainFromRun(event_root_dir)

     if isinstance(deep_pulse_dict, basestring):
          if deep_pulse_dict.split('.')[-1] == 'json':
               with open(deep_pulse_dict,'r') as f:
                    deep_pulse_dict = json.load(f)

     num_deep_pulses=len(deep_pulse_dict['event_num'])

     time=[]
     for i in range(num_deep_pulses):
          
          ev=deep_pulse_dict['event_num'][i]-ev_num_prefix
          pulse = pulse_processing.PulseProcess(buffer_length = 768)
          pulse.getFromROOTTree(chain, ev)

          pulse.upsample(upsample_factor)

          #pulse.nullFiberDelays()
          
          for i in range(7):
               #plt.figure(100)
               #plt.plot(pulse.wave[i].voltage - i*100)
               
               above_thresh = numpy.where(pulse.wave[i].voltage > threshold)[0]  

               if len(above_thresh) < 1:
                    continue

               if i == 0:
                    roll_loc_0 = -above_thresh[0]-(len(pulse.wave[i].voltage)/2)
                    pulse.wave[i].voltage = numpy.roll(pulse.wave[i].voltage, roll_loc_0)
               
               else:
                    pulse.wave[i].voltage = numpy.roll(pulse.wave[i].voltage, roll_loc_0)

               #plt.figure(101)
               #plt.plot(pulse.wave[i].voltage - i*100)
          #plt.show()
          _time = pulse.alignUsingThreshold(threshold=threshold, location=None)
          
          if _time is not None:
               time.append(numpy.array(_time))
               
     return time


def getTimeDifference(time):

     t_diff=[]
     for i in range(len(time)):
          _t_diff=[]
          for j in range(7):
               _t_diff.append(time[i][j]-time[i][0])
          t_diff.append(numpy.array(_t_diff))
     return t_diff
          


if __name__=='__main__':

    directory='../runs/run445/'
    event_json_file =  directory+'run445_events.json'
    stat_json_file =  directory+'run445_status.json'

    deep_pulses = getDeepPulses(event_json_file, stat_json_file )

    ev_num_prefix = 445000000001
    output_root_dir = '/project/avieregg/nuphase01/pole2018/rootified/'+'run445'+'/event/'

    #plt.figure()
    #plt.plot(deep_pulses['readout_time'], deep_pulses['snr'], 'o', ms=2)

    #plt.figure()
    time = getDeepPulseTime(deep_pulses, output_root_dir, ev_num_prefix, 40)

    time = numpy.array(getTimeDifference(time))

    plt.figure()
    plt.plot(time)

    #antenna_z = [0,-1,-2,-3,-4,-6,-8]

    antenna_z = [12.135, 11.12, 10.11, 9.09, 8.07, 6.02, 3.98]
    #antenna_z = [0,-1,-3,-4,-5,-7,-9]
    #antenna_z = [13.17, 12.135, 10.11, 9.09, 8.07, 6.02, 3.98]

    mean_time = numpy.mean(time,axis=0)
    #mean_time[1] = mean_time[1] - 0.4
    #mean_time[3] = mean_time[3] - 0.4
    #mean_time[6] = mean_time[6] + 1.8 #- 0.4

    p = numpy.polyfit(antenna_z, mean_time, 1)

    pp = numpy.poly1d(p)

    print pp(antenna_z) - mean_time
    
    plt.figure()
    plt.plot(antenna_z, mean_time, 'o')
    plt.grid(True)
    plt.xlabel('antenna z position')
    plt.ylabel('arrival time - fiber delays not subtracted[ns]')
    plt.ylim([-1,35])

    plt.plot(antenna_z, pp(antenna_z))

    #mean_time = numpy.mean(time,axis=0)
    #mean_time[1] = mean_time[1] - 0.4
    #mean_time[3] = mean_time[3] - 0.4
    mean_time[6] = mean_time[6] + 1.8 #- 0.4
    p = numpy.polyfit(antenna_z, mean_time, 1)

    pp = numpy.poly1d(p)
    print pp(antenna_z) - mean_time

    plt.figure()
    plt.plot(antenna_z, mean_time, 'o', c='black')

    plt.plot(antenna_z, pp(antenna_z)) 

    #plt.ylim([-10,1])
    #plt.xlim([-12,1])

    plt.grid(True)
    plt.xlabel('antenna z position')

    
    #plt.hist(numpy.array(time)[:,1])
    #print numpy.std(numpy.array(time)[:,1])
    plt.show()

    
