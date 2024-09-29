import serial, time

class ddg_serial():
    def __init__(self, loud = False):
        self.ser = serial.Serial(port = "/dev/ttyUSB0", baudrate=38400, timeout = 1, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)
        self.ser.close()
        self.ser.open()

        self.loud = loud

    def send_command(self, command):
        self.ser.write(str.encode(command+'\n'))
        line = self.ser.readline()
        if self.loud:
            print(str(line))

    def load_calibration(self):
        send_command(ser, 'TRigger Pos')   #Set to trigger on external rising edge

        #Turn all pulsers on
        self.send_command(ser, 'ASET ON')
        self.send_command(ser, 'BSET ON')
        self.send_command(ser, 'CSET ON')
        self.send_command(ser, 'DSET ON')

        #Todo: calibrate time delays once cables are finalized
        #They should all be far enough above zero so that the delays can be shifted in either direction
        self.t_zero_point = 50    #Zero point in units of nanosecond 
        self.send_command(ser, f'ADELAY {self.t_zero_point}n')
        self.send_command(ser, f'BDELAY {self.t_zero_point}n')
        self.send_command(ser, f'CDELAY {self.t_zero_point}n')
        self.send_command(ser, f'DDELAY {self.t_zero_point}n')

        #For uniformity's sake set all the widths to be the same
        self.send_command(ser, 'AWIDTH 50n')
        self.send_command(ser, 'BWIDTH 50n')
        self.send_command(ser, 'CWIDTH 50n')
        self.send_command(ser, 'DWIDTH 50n')

    def angle_deg_to_delay(self, angle, PA_separation, ior = 1.7):
        '''
        Angle defined as the elevation angle in degrees, PA_separation in meters
        Default index of refraction for calculating delay is n = 1.7
        '''
        c = 0.3   #In units of m/ns
        max_delta_T = PA_separation * ior / c
        delta_T = np.sin(np.deg2rad(angle)) * max_delta_T

        if angle > 0:
            self.send_command(ser, f'ADELAY {self.t_zero_point}n')
            self.send_command(ser, f'BDELAY {self.t_zero_point + delta_T}n')
            self.send_command(ser, f'CDELAY {self.t_zero_point + 2*delta_T}n')
            self.send_command(ser, f'DDELAY {self.t_zero_point + 3*delta_T}n')
        else:
            self.send_command(ser, f'ADELAY {self.t_zero_point + 3*delta_T}n')
            self.send_command(ser, f'BDELAY {self.t_zero_point + 2*delta_T}n')
            self.send_command(ser, f'CDELAY {self.t_zero_point + delta_T}n')
            self.send_command(ser, f'DDELAY {self.t_zero_point}n')

    def close_serial(self):
        self.ser.close()

if __name__ == "__main__":

    ddg = ddg_serial(loud = True)
    ddg.load_calibration()
    ddg.close_serial()