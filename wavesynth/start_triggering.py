import serial, time

def send_command(ser, command, loud=True):
    ser.write(str.encode(command+'\n'))
    line = ser.readline()
    if loud:
        print(str(line))

if __name__ == "__main__":
    ser = serial.Serial(port = "/dev/ttyUSB0", baudrate=38400, timeout = 1, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)

    ser.close()
    ser.open()

    if ser.isOpen():
        print('Serial is open!')
        send_command(ser, 'TRigger Pos')
        #send_command(ser, 'AD 1n')
        #send_command(ser, 'BD 0n')
        #send_command(ser, 'CD 0n')
        #send_command(ser, 'DD 0n')
        #send_command(ser, 'DW 2u')
        #send_command(ser, 'AW 10n')
        send_command(ser, 'DSET')
        send_command(ser, 'CSET')
        send_command(ser, 'ASET')
        send_command(ser, 'BSET')
ser.close()
