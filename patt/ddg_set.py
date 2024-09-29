import serial, time
from ddg_utils import ddg_serial

if __name__ == "__main__":

    ddg = ddg_serial(loud = True)
    ddg.load_calibration()
    ddg.close_serial()

    