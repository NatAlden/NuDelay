import numpy
import math
import scipy.interpolate as spint
import scipy.signal as signal

'''
class to handle and  modify time-domain signals
'''
                 
class Waveform:
    
    def __init__(self, voltage, time=[], sampling_rate=0):
        self.voltage = voltage
        self.n = len(self.voltage)

        if len(time)==0 and sampling_rate != 0:
            self.time = numpy.linspace(0, sampling_rate * self.n, self.n)
        elif sampling_rate == 0 and len(time) == len(voltage):
            self.time = time
        else:
            self.time = numpy.linspace(0, self.n, self.n)
            
        self.dt = self.time[1]-self.time[0]

        #freq domain placeholders, can be assigned later:
        self.ampl = []
        self.freq = []
        self.df   = -1
        #hilbert placeholder
        self.analytic = []
        self.envelope = []

    def meanSubtract(self, base_range=(0,10) ):
        self.voltage = self.voltage - numpy.mean(self.voltage[base_range[0]:base_range[1]])
        
    def medianSubtract(self, base_range=(0,10) ):
        self.voltage = self.voltage - numpy.median(self.voltage[base_range[0]:base_range[1]])

    def zeropad(self, pad_length=1024):

        if pad_length <= self.n:
            return None

        half_pad_length = int(numpy.floor((pad_length - self.n) / 2))

        self.voltage = numpy.hstack((numpy.zeros(half_pad_length), self.voltage, numpy.zeros(half_pad_length)))

        #if pad_length is odd, add extra zeros:
        while(len(self.voltage) < pad_length):
            self.voltage = numpy.hstack((numpy.zeros(1), self.voltage, numpy.zeros(1)))

        self.n = len(self.voltage)
        self.time = numpy.linspace(0, self.n * self.dt, self.n)
        
    def fft(self, window_function=None):

        if window_function == None:
            self.ampl = 2.0*numpy.fft.rfft(self.voltage)

        if self.n % 2 == 0:
            self.freq = numpy.linspace(0, 1 / (2. * self.dt), (self.n / 2) + 1)
        else:
            self.freq = numpy.linspace(0,  (self.n - 1.) / (2. * self.dt * self.n), (self.n + 1) / 2)

        self.df = self.freq[1]-self.freq[0]
        
    def upsampleFreqDomain(self, factor):

        int_factor = int(factor)-1
        self.ampl = numpy.pad(self.ampl, (0, (len(self.ampl)-1)*int_factor), 'constant', constant_values=(0))
        self.freq = numpy.append(self.freq, numpy.arange(self.freq[-1]+self.df, len(self.ampl)*self.df,self.df))

        new_nyquist_ghz = self.freq[-1]
        self.voltage = factor/2.0 * numpy.fft.irfft(self.ampl) 
        self.n = len(self.voltage)
        self.time  = numpy.arange(0., self.n/( 2.*new_nyquist_ghz), 1/( 2.*new_nyquist_ghz))
        self.dt = self.time[1]-self.time[0]

    def timeDerivative(self):
        self.ampl = 1j * self.ampl * 2.0 * numpy.pi * self.freq
        self.voltage = 1./2.0 * numpy.fft.irfft(self.ampl) 

    def upsampleTimeDomain(self, factor, kind='linear'):

        new_time = numpy.arange(self.time[0], 
                                 self.time[self.n-1],
                                 self.dt/factor)
        self.voltage = spint.interp1d(self.time, self.voltage,
                              kind=kind, axis=0)(new_time)
        self.time = new_time
        self.dt = self.time[1]-self.time[0]  
        self.n = len(self.voltage)
            
    def downsampleTimeDomain(self, factor):
        
        self.voltage = self.voltage[::factor]
        self.time = self.time[::factor]
        self.dt = self.time[1]-self.time[0]  
        self.n = len(self.voltage)

    def takeWindow(self, window):
        self.voltage = self.voltage[window[0]:window[1]]
        self.time = self.time[window[0]:window[1]]
        self.n = len(self.voltage)

    def analyticSignal(self):
        self.analytic = signal.hilbert(self.voltage)
        self.envelope = numpy.abs(self.analytic)
        return self.envelope
        
    def autoCorrelate(self):
        autocor = numpy.real(numpy.fft.irfft( self.ampl * numpy.conj(self.ampl) ))
        return autocor

    def crossCorrelate(self, wfm=None, norm=True, shift=True):
        '''
        cross correlate with wfm, another instance of the Waveform class
        wfm=None => autocorrelate
        '''
        if wfm is not None:
            assert self.dt - wfm.dt < 1e-2
            cor = numpy.real(numpy.fft.irfft( self.ampl * numpy.conj(wfm.ampl) ))
            if norm:
                _norm = math.sqrt(max(self.autoCorrelate()) * max(wfm.autoCorrelate()))
                cor = cor / _norm
                
        else:
            cor = numpy.real(numpy.fft.irfft( self.ampl * numpy.conj(self.ampl) ))
            if norm:
                _norm = max(self.autoCorrelate())
                cor = cor / _norm

        if shift:
            return numpy.fft.fftshift(cor)
        else:
            return cor


if __name__=="__main__":
    import tools.myplot
    import matplotlib.pyplot as plt
    
    v= numpy.loadtxt('test_data/impulse_upsampled.txt')
    impulse = Waveform(v[:,1],v[:,0])
    #impulse.downsampleTimeDomain(10)
    #impulse.medianSubtract()
    impulse.fft()

    impulse.time = impulse.time-min(impulse.time) #-- start timebase at t=0
    plt.figure(1)
    plt.plot(impulse.time, impulse.voltage, 's', ms=2)
    
    plt.figure(2)
    plt.plot(impulse.freq, numpy.abs(impulse.ampl), 's', ms=2)

    impulse.upsampleFreqDomain(2)
    
    plt.figure(1)
    plt.plot(impulse.time, impulse.voltage, 'o', ms=1)

    plt.figure(2)
    plt.plot(impulse.freq, numpy.abs(impulse.ampl), 'o', ms=1)    

    #plt.figure(4)
    #plt.plot(impulse.time, numpy.correlate(impulse.voltage, impulse.voltage, "same"))

    plt.show()
    

