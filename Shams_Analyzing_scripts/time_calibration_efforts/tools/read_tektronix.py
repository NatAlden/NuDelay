import csv
import numpy as np

def read_scope_cvs(filename, col_t=3, col_v=4, Verbose=False, fastFrame=False):
    '''
    read scope data in cvs format. specify columns in argument
    '''

    f = open(filename)
    csv_f = csv.reader(f)
    
    t = []
    wave = []

    #get metadata
    num_events = 1
    record_length = 0
    trigger_time = 0.0
    horz_offset = 0.0
   
    for row in csv_f:
        if row[0]=="Record Length":
            record_length = int(row[1])
        if row[0]=="Trigger Time":
            trigger_time = float(row[1])
        if row[0]=="Horizontal Offset":
            horz_offset = float(row[1])
        if row[0]=="FastFrame Count" and fastFrame==True:
            num_events = int(row[1])
        t.append(float(row[col_t]) * 1.e9)
        wave.append(row[col_v])   

    if Verbose:
        print('scope sampling dt:', t[2]-t[1], 'ns')
        print('full data record length:', len(t), 'samples')
        #print 'full data record length:', len(wave), 'samples'

    if fastFrame==True:
        return np.array(t[0:record_length], dtype=float), \
        np.reshape(np.array(wave,dtype=float), (num_events, record_length))
    else:
        return np.array(t[0:record_length], dtype=float), \
            np.array(wave,dtype=float)
