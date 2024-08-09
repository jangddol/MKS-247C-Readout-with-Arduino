import enum

class Channel(enum.Enum):
    CH1 = "1"
    CH2 = "2"
    CH3 = "3"
    CH4 = "4"
    CH_UNKNOWN = "?"

def convert_int_to_channel(ch):
    if ch == 1:
        return Channel.CH1
    if ch == 2:
        return Channel.CH2
    if ch == 3:
        return Channel.CH3
    if ch == 4:
        return Channel.CH4
    return Channel.CH_UNKNOWN