import numpy as np
def setAttenuation(address, atten_value=0):
    '''
    parallel loading into SKY12347: 6-bit step attenuator up to 31.5dB

    0 = most atten
    63 = least atten
    atten_value is bit-reversed before loading (to match schematic)
    '''
    
    #ret = getOutputRegisterValue(address)
    ret = 0x01
    atten_bits = '{:07b}'.format(atten_value)
    print(f"OG attenuation bits is {atten_bits}")

    pin_mapping_i2c = [0, 1, 2, 3, 4, 5, 6]
    pin_mapping_atten = [3, 2, 1, 0, 4, 5, 6]

    #mapped_atten_bits = atten_bits
    #print(f"{mapped_atten_bits[0]}\n\n")
    mapped_atten_bits = "0" + atten_bits[0:3] + atten_bits[7:2:-1]
    new_reg_value = int(mapped_atten_bits, 2)
    #print(f"OG is {atten_bits}, new is {mapped_atten_bits}")
    print(f"new attenuation bits is {mapped_atten_bits}")
    print(f"actual number is {new_reg_value}, {'{:08b}'.format(new_reg_value)}")

    #sprint(f"reversed bits are {atten_bits}, first bit is {atten_bits[0]}")


if __name__ == "__main__":
    address = 0x03
    setAttenuation(address, atten_value = 74)