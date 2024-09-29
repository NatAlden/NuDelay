import smbus
import math, argparse

bus = smbus.SMBus(2) #i2c2 is used on the BBB

#adr0 = 0x48
#adr1 = 0x3f
#adr2 = 0x18 #tmp sensor

output_reg = 0x01
config_reg = 0x03

def setup(address):
    '''
    on power-on, i2c expanders need to be config'ed as low and outputs
    '''
    write(address, output_reg, 0x00) #set output registers to 0
    write(address, config_reg, 0x00) #set as outputs

def write(i2c_address, register, cmd):
    '''
    8-bit code write, returns state of acknowledge bit (0=ack, 1=no ack)
    '''
    ack = bus.write_byte_data(i2c_address, register, cmd)

    return ack

def read(i2c_address, register):

    read_data = bus.read_byte_data(i2c_address, register)

    return read_data

def getOutputRegisterValue(address):
    '''
    retrieves current setting of expander outputs
    '''
    val = read(address, output_reg)

    return val

def setAttenuation(address, atten_value=0):
    '''
    parallel loading into PE43713: 7-bit step attenuator up to 31.75dB
    
    atten_value = 4 * (attenuation [dB])

    0 = least atten (0 dB)
    127 = most atten (31.75 dB)
    atten_value is adjusted before loading to match schematic
    '''
    
    atten_bits_value = '{:07b}'.format(atten_value)

    #Following the mapping from the schematic and https://www.psemi.com/pdf/datasheets/pe43713ds.pdf
    mapped_atten_bits = "0" + atten_bits_value[0:3] + atten_bits_value[7:2:-1]
    
    #Now turn the string back into an 8-bit binary number
    new_reg_value = int(mapped_atten_bits, 2)    

    ack = write(address, output_reg, new_reg_value)

def setOutput(address):

    ret = getOutputRegisterValue(address)
    #print(ret)
    write(address, output_reg, ret | (0x02)) 

def set_equal_attens(atten_value = 1):
    '''
    set equal attenuation values for all 4 channels
    '''
    adr0 = 0x38
    adr1 = 0x3a
    adr2 = 0x3c
    adr3 = 0x3e

    for address in [adr0, adr1, adr2, adr3]:
        setup(address)
        setOutput(address)
        setAttenuation(address, atten_value)

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--atten", action = "store", type = int,  dest = "atten_value", default = 0)
    args = parser.parse_args()

    set_equal_attens(atten_value=args.atten_value)
    
