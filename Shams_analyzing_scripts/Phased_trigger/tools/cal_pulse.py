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
     #readout_time_stat_sec =numpy.array(numpy.array(status_dict['readout_time'])-min(status_dict['readout_time']), dtype=float)
     #full_readout_time_status=readout_time_stat_sec+numpy.array(status_dict['readout_time_ns'], dtype=float)*1.e-9

     full_readout_time_status=numpy.array(numpy.array(status_dict['readout_time'])-min(status_dict['readout_time']), dtype=float)
     
     return full_readout_time_status

def getEventReadoutTime(event_dict):
    #readout_time_event_sec=numpy.array(numpy.array(event_dict['readout_time'])-min(event_dict['readout_time']), dtype=float)
    #full_readout_time_event =readout_time_event_sec+numpy.array(event_dict['readout_time_ns'], dtype=float)*1.e-9

    full_readout_time_event=numpy.array(numpy.array(event_dict['readout_time'])-min(event_dict['readout_time']), dtype=float)

    return full_readout_time_event

def getCalPulses(event_dict, status_dict=None, outfile=None, mode='time', correct_trig_time=False):
    '''
    get dictionary of cal pulse events from json event/header info
    mode = 'gate' or 'time'. 
    If 'time', this looks for events proximate to latched pps time, and requires json file for status info
    If 'mode', this simply looks for gated events -> only useful for runs after ~2/22/2018 nuphase01 firmware upgrade

    '''
    if mode is not 'time' and mode is not 'gate':
        print 'mode needs to be set to \'time\' or \'gate\''
        return 1
   
    full_readout_time_status = getStatusReadoutTime(status_dict)

    full_readout_time_event=getEventReadoutTime(event_dict)

    new_trig_time = event_dict['trig_time']
    
    #fix trig time 
    if correct_trig_time:
        '''
        due to sw bug, earlier runs also had an issue w/ the trig_time rolling over at 32 bits. The following unrolls these times:
        '''
        new_trig_time=[]
        add_value=0
    
        for i in range(len(event_dict['trig_time'])):
            if i > 1 and ((event_dict['trig_time'][i][0]+add_value) < (event_dict['trig_time'][i-1][0]+add_value)):
                add_value=add_value+pow(2,32)
            new_trig_time.append(event_dict['trig_time'][i][0]+add_value)

    new_trig_time_sec =(numpy.array(new_trig_time)*1./FPGA_CLK_FREQ_GHZ) * 1.e-9 

    #still an issue with the latched pps time as of 03/27/18
    new_pps_time=[]
    add_value=0
    for i in range(len(status_dict['latched_pps_time'])):
         if i > 1 and ((status_dict['latched_pps_time'][i]+add_value) < (status_dict['latched_pps_time'][i-1]+add_value)):
              add_value=add_value+pow(2,32)
         new_pps_time.append(status_dict['latched_pps_time'][i]+add_value)

    new_pps_time_sec = (numpy.array(new_pps_time)*1./FPGA_CLK_FREQ_GHZ) * 1.e-9
    
    #the cal pulser dict to save
    find_cal_pulser={}
    find_cal_pulser['trig_time']=[]
    find_cal_pulser['readout_time']=[]
    #find_cal_pulser['snr']=[]
    find_cal_pulser['event_num']=[]
    #find_cal_pulser['have_wfm']=[] # filtered data, is wfm in dataset?

    if status_dict is not None:
        find_cal_pulser['glob_gated_scaler']=[]
        find_cal_pulser['beam_gated_scaler']=[]
        find_cal_pulser['readout_time_status']=[]

    cal_pulse_found=False

    for i in range(1,len(event_dict['event_number'])):

        #check for cal pulse
        if mode=='gate':
            if event_dict['gate_flag'][i] == 1:
                cal_pulse_found=True
            else:
                cal_pulse_found=False
        else:
            if status_dict is None:
                print 'need to load status dict in order to find cal pulsers'
                return 1
           
        if status_dict is not None:
            status_index=numpy.where(full_readout_time_status < full_readout_time_event[i])[0]

            if len(status_index) == len(new_pps_time):
                break

            if mode == 'time':
                 if abs(new_pps_time_sec[status_index[-1]+1] - new_trig_time_sec[i]) < PPS_TO_PULSE_TIME_INTERVAL:
                      cal_pulse_found=True
                 else:
                      cal_pulse_found=False

        #insert values into dict if found
        if cal_pulse_found:
            if mode=='gate':
                find_cal_pulser['trig_time'].append(event_dict['trig_time'][i])
            else:
                find_cal_pulser['trig_time'].append(new_trig_time[i])
            find_cal_pulser['readout_time'].append(full_readout_time_event[i])
            #find_cal_pulser['snr'].append(numpy.array(event_dict['wave_snr_vpp'][i]).tolist())
            find_cal_pulser['event_num'].append(event_dict['event_number'][i])

            #if event_dict['hd_event_num'][i] == event_dict['ev_event_num'][i]:
            #     find_cal_pulser['have_wfm'].append(True)
            #else:
            #     find_cal_pulser['have_wfm'].append(False)

            if status_dict is not None:
                find_cal_pulser['glob_gated_scaler'].append(status_dict['global_scalers'][status_index[-1]+1][1])
                find_cal_pulser['beam_gated_scaler'].append(status_dict['beam_scalers'][status_index[-1]+1][1])
                find_cal_pulser['readout_time_status'].append(full_readout_time_status[status_index[-1]+1])
                
    print 'found',len(find_cal_pulser['event_num']), 'cal pulser events'
    
    if outfile is not None:
        with open(outfile, 'w') as f:
            json.dump(find_cal_pulser, f)

    #plt.plot(find_cal_pulser['readout_time'], (numpy.array(find_cal_pulser['trig_time'])*1./FPGA_CLK_FREQ_GHZ) * 1.e-9 % 1.0 )
    #plt.show()

    return find_cal_pulser

def getPulseAvgFromTemplate(cal_pulse_dict, event_root_dir, ev_num_prefix, template_pulse, plot=False, xcor_cut=0.6):
    
    volts, rms, num = pulse_processing.makeTimeDomainAveragePulse(event_root_dir, cal_pulse_dict, ev_num_prefix,
                                                                  load_json_file=False,
                                                                  mode='xcor', template=template_pulse,
                                                                  xcor_cut=xcor_cut)
    if plot:
        for j in range(NUPHASE_VPOL_CH):
            plt.plot(volts[NUPHASE_VPOL_CH], volts[j])
        plt.show()

    vpp = numpy.zeros(NUPHASE_VPOL_CH)
    rms_noise = numpy.zeros(NUPHASE_VPOL_CH)
    for j in range(NUPHASE_VPOL_CH):
        vpp[j] = numpy.max(volts[j])-numpy.min(volts[j])
        rms_noise[j] = math.sqrt(rms[j])

    return vpp, rms_noise, num, volts

def binCalPulserEvents(cal_pulse_event_dict, cal_pulse_status_dict, num_steps, interval_sec=60.*15, length=60.*10,
                       wait_for_first_cal_pulse_time = 5.0, outfile=None):

    
    if cal_pulse_event_dict.split('.')[-1] == 'json':
        with open(cal_pulse_event_dict,'r') as f:
            cal_pulse_event_dict  = json.load(f)
   
    full_readout_time_status = getStatusReadoutTime(cal_pulse_status_dict)
    
    bin_cal_pulser={}
    #bin_cal_pulser['snr']=[]
    bin_cal_pulser['gated_glob_scaler']=[]
    bin_cal_pulser['gated_beam_scaler']=[]
    bin_cal_pulser['num_scaler_updates']=[]
    bin_cal_pulser['step']=[]
    bin_cal_pulser['event_num']=[]
    bin_cal_pulser['have_wfm']=[]

    ii=0
    event_readout_time = numpy.array(cal_pulse_event_dict['readout_time'])

    while(ii < num_steps):
        start_time=cal_pulse_event_dict['readout_time'][0]+ wait_for_first_cal_pulse_time+interval_sec*ii
        stop_time =start_time + length

        bin_cal_pulser['step'].append(ii)
        ii = ii + 1

        cal_pulser_index = numpy.where((event_readout_time > start_time) & (event_readout_time < stop_time))
        
        if len(cal_pulser_index) < 1:
             continue

        status_index=numpy.where((full_readout_time_status > start_time) & (full_readout_time_status < stop_time))

        bin_cal_pulser['event_num'].append(numpy.array(cal_pulse_event_dict['event_num'])[cal_pulser_index].tolist())
        #bin_cal_pulser['have_wfm'].append(numpy.array(cal_pulse_event_dict['have_wfm'])[cal_pulser_index].tolist())
        bin_cal_pulser['gated_glob_scaler'].append(numpy.mean(numpy.array(cal_pulse_status_dict['global_scalers'])[status_index,1]))
        bin_cal_pulser['num_scaler_updates'].append(numpy.array(cal_pulse_status_dict['global_scalers'])[status_index,1].shape[1])

        #bin_cal_pulser['gated_beam_scaler'].append(numpy.mean(numpy.array(cal_pulse_status_dict['beam_scalers'])[status_index,1,:], axis=1).tolist())

        #bin_cal_pulser['snr'].append(numpy.mean(numpy.array(cal_pulse_event_dict['snr'])[cal_pulser_index,:], axis=1).tolist())

        #print status_index, len(numpy.array(cal_pulse_status_dict['global_scalers'])[status_index,1])
        #plt.plot(numpy.array(cal_pulse_status_dict['global_scalers'])[status_index,1][0], 'o')
        #plt.show()
    plt.plot(numpy.array(cal_pulse_status_dict['global_scalers'])[:,1], 'o')
    plt.show()
    
    if outfile is not None:
        with open(outfile, 'w') as f:
            json.dump(bin_cal_pulser, f)
        
    return bin_cal_pulser


def getCalPulseSNRSweep(cal_pulse_dict, event_root_dir, ev_num_prefix, template_file,
                        min_num_events=70, outfile=None, xcor_cut=0.4):
    
    cal_pulse_template = numpy.loadtxt(template_file)
    template_pulse = pulse_processing.PulseProcess(data=cal_pulse_template)

    if cal_pulse_dict.split('.')[-1] == 'json':
        with open(cal_pulse_dict,'r') as f:
            cal_dict= json.load(f)
    else:
        cal_dict = loadCalPulseJSON(cal_pulse_json)

    #loop or attenuation steps
    vpp = []
    rms_noise=[]
    num_pulses=[]
    wave=[]
    step=[]
    
    i = 0
    while(i < len(cal_dict['event_num'])):
    
        internal_cal_dict={}
        internal_cal_dict['event_num'] = cal_dict['event_num'][i]
        internal_cal_dict['have_wfm'] = cal_dict['have_wfm'][i]

        i = i+1
        
        if len(internal_cal_dict['event_num']) < min_num_events:
            continue

        _vpp, _rms, num, volts = getPulseAvgFromTemplate(internal_cal_dict, event_root_dir, ev_num_prefix,
                                                         template_pulse, xcor_cut=xcor_cut)

        #if num < min_num_events:
        #     continue

        print 'processing step', i, ' - Number of cal pulses in average:',  num, 'out of', len(internal_cal_dict['event_num']), 'found cal pulses'

        vpp.append(_vpp)
        rms_noise.append(_rms)
        num_pulses.append(numpy.ones(NUPHASE_VPOL_CH) * num)
        wave.append(volts)
        step.append(numpy.ones(NUPHASE_VPOL_CH) * (i-1))

    if outfile is not None:
         numpy.savetxt(outfile, numpy.vstack( (numpy.array(vpp),numpy.array(rms_noise), numpy.array(num_pulses), numpy.array(step) ) ),
                       delimiter='\t')
         #numpy.savetxt(outfile+'.avg_wfms', numpy.array(wave))

    return numpy.array(vpp), numpy.array(rms_noise)

if __name__=='__main__':

    
    #directory='run554_scpedRunAfterFirmUpgrade/'
    directory='run565/'
    event_json_file =  directory+'run565.json'
    #event_json_file =  'run130_spareSystem/run130.json'
    #stat_json_file =  directory+'run554_status.json'

    cal_pulses = getCalPulses(event_json_file, mode='gate')

    plt.figure()
    plt.plot(cal_pulses['readout_time'], cal_pulses['trig_time'], 'o', ms=2)
    plt.show()

    
