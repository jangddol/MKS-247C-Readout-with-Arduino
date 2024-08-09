import serial
import enum
from channel import Channel
import time

class CMD(enum.Enum):
    # serial command dictionary constant
    # U means UNKNOWN
    CMD_SET_CH_L1MU = "t"
    CMD_SET_CH_L1M1 = "y"
    CMD_SET_CH_L1M2 = "u"
    CMD_SET_CH_L1M3 = "i"
    CMD_SET_CH_L1M4 = "o"
    CMD_SET_CH_L2MU = "p"
    CMD_SET_CH_L2M1 = "g"
    CMD_SET_CH_L2M2 = "h"
    CMD_SET_CH_L2M3 = "j"
    CMD_SET_CH_L2M4 = "k"
    CMD_SET_CH_L3MU = "l"
    CMD_SET_CH_L3M1 = "b"
    CMD_SET_CH_L3M2 = "n"
    CMD_SET_CH_L3M3 = "m"
    CMD_SET_CH_L3M4 = "Q"
    CMD_SET_CH_L4MU = "W"
    CMD_SET_CH_L4M1 = "E"
    CMD_SET_CH_L4M2 = "R"
    CMD_SET_CH_L4M3 = "T"
    CMD_SET_CH_L4M4 = "Y"
    CMD_SET_CH_LUM1 = "U"
    CMD_SET_CH_LUM2 = "I"
    CMD_SET_CH_LUM3 = "O"
    CMD_SET_CH_LUM4 = "P"
    CMD_SET_CH1_ON = "z"
    CMD_SET_CH2_ON = "x"
    CMD_SET_CH3_ON = "c"
    CMD_SET_CH4_ON = "v"
    CMD_SET_CH1_OFF = "a"
    CMD_SET_CH2_OFF = "s"
    CMD_SET_CH3_OFF = "d"
    CMD_SET_CH4_OFF = "f"
    CMD_SET_FLOW_SETPOINT_CH1 = "q"
    CMD_SET_FLOW_SETPOINT_CH2 = "w"
    CMD_SET_FLOW_SETPOINT_CH3 = "e"
    CMD_SET_FLOW_SETPOINT_CH4 = "r"
    CMD_RESET = "B"


class RFMserial:
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.ser = serial.Serial(port, baudrate, write_timeout=1, xonxoff=False)
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

    def write(self, data):
        self.ser.reset_input_buffer() # 이거 안하면 write_timeout 걸리던데 왜인지는 모름
        self.ser.write((data + '\n').encode('ascii'))
        self.ser.flush() # 다 써지기를 기다림

    def reset_serial(self):
        self.write(CMD.CMD_RESET.value)

    def setReadingChannel_serial(self, channels):
        if channels[0] == Channel.CH1:
            if channels[1] == Channel.CH1:
                self.write(CMD.CMD_SET_CH_L1M1.value)
            elif channels[1] == Channel.CH2:
                self.write(CMD.CMD_SET_CH_L1M2.value)
            elif channels[1] == Channel.CH3:
                self.write(CMD.CMD_SET_CH_L1M3.value)
            elif channels[1] == Channel.CH4:
                self.write(CMD.CMD_SET_CH_L1M4.value)
            elif channels[1] == Channel.CH_UNKNOWN:
                self.write(CMD.CMD_SET_CH_L1MU.value)
        elif channels[0] == Channel.CH2:
            if channels[1] == Channel.CH1:
                self.write(CMD.CMD_SET_CH_L2M1.value)
            elif channels[1] == Channel.CH2:
                self.write(CMD.CMD_SET_CH_L2M2.value)
            elif channels[1] == Channel.CH3:
                self.write(CMD.CMD_SET_CH_L2M3.value)
            elif channels[1] == Channel.CH4:
                self.write(CMD.CMD_SET_CH_L2M4.value)
            elif channels[1] == Channel.CH_UNKNOWN:
                self.write(CMD.CMD_SET_CH_L2MU.value)
        elif channels[0] == Channel.CH3:
            if channels[1] == Channel.CH1:
                self.write(CMD.CMD_SET_CH_L3M1.value)
            elif channels[1] == Channel.CH2:
                self.write(CMD.CMD_SET_CH_L3M2.value)
            elif channels[1] == Channel.CH3:
                self.write(CMD.CMD_SET_CH_L3M3.value)
            elif channels[1] == Channel.CH4:
                self.write(CMD.CMD_SET_CH_L3M4.value)
            elif channels[1] == Channel.CH_UNKNOWN:
                self.write(CMD.CMD_SET_CH_L3MU.value)
        elif channels[0] == Channel.CH4:
            if channels[1] == Channel.CH1:
                self.write(CMD.CMD_SET_CH_L4M1.value)
            elif channels[1] == Channel.CH2:
                self.write(CMD.CMD_SET_CH_L4M2.value)
            elif channels[1] == Channel.CH3:
                self.write(CMD.CMD_SET_CH_L4M3.value)
            elif channels[1] == Channel.CH4:
                self.write(CMD.CMD_SET_CH_L4M4.value)
            elif channels[1] == Channel.CH_UNKNOWN:
                self.write(CMD.CMD_SET_CH_L4MU.value)
        elif channels[0] == Channel.CH_UNKNOWN:
            if channels[1] == Channel.CH1:
                self.write(CMD.CMD_SET_CH_LUM1.value)
            elif channels[1] == Channel.CH2:
                self.write(CMD.CMD_SET_CH_LUM2.value)
            elif channels[1] == Channel.CH3:
                self.write(CMD.CMD_SET_CH_LUM3.value)
            elif channels[1] == Channel.CH4:
                self.write(CMD.CMD_SET_CH_LUM4.value)

    def writeFlowSetpoint_serial(self, flowSetpoint, ch):
        self.write(flowSetpoint)
        if ch == Channel.CH1:
            self.write(CMD.CMD_SET_FLOW_SETPOINT_CH1.value)
        elif ch == Channel.CH2:
            self.write(CMD.CMD_SET_FLOW_SETPOINT_CH2.value)
        elif ch == Channel.CH3:
            self.write(CMD.CMD_SET_FLOW_SETPOINT_CH3.value)
        elif ch == Channel.CH4:
            self.write(CMD.CMD_SET_FLOW_SETPOINT_CH4.value)
    
    def writeChannelOn_serial(self, ch):
        if ch == Channel.CH1:
            self.write(CMD.CMD_SET_CH1_ON.value)
        elif ch == Channel.CH2:
            self.write(CMD.CMD_SET_CH2_ON.value)
        elif ch == Channel.CH3:
            self.write(CMD.CMD_SET_CH3_ON.value)
        elif ch == Channel.CH4:
            self.write(CMD.CMD_SET_CH4_ON.value)
    
    def writeChannelOff_serial(self, ch):
        if ch == Channel.CH1:
            self.write(CMD.CMD_SET_CH1_OFF.value)
        elif ch == Channel.CH2:
            self.write(CMD.CMD_SET_CH2_OFF.value)
        elif ch == Channel.CH3:
            self.write(CMD.CMD_SET_CH3_OFF.value)
        elif ch == Channel.CH4:
            self.write(CMD.CMD_SET_CH4_OFF.value)

    def readline_serial(self):
        lf = b'\n'  # 개행 문자를 바이트로 정의
        # time.sleep(0.01) # 이걸로 딜레이를 주었더니 잘못 받아오는 확률이 더 늘어났음. 그냥 아래처럼 3번 읽는게 맞는거 같음
        self.ser.read_until(expected=lf) # 첫 번째 읽기: 현재 라인의 나머지 부분을 읽고 버립니다
        self.ser.read_until(expected=lf) # 두 번째 읽기: 딜레이를 주기 위한 잉여 읽기
        line = self.ser.read_until(expected=lf).decode('ascii').strip() # 세 번째 읽기: 온전한 새 라인을 읽습니다
        while not line: # 빈 라인이면 다시 읽습니다
            line = self.ser.read_until(expected=lf).decode('ascii').strip()
        try:
            float_value = float(line)
            print(f"Received float: {float_value}")
        except ValueError:
            print(f"Received non-float data")

        return line
    