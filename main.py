import tkinter as tk  # Or your chosen GUI framework
import numpy as np
from collections import deque
import time

from RFMserial import RFMserial
from channel import Channel, convert_int_to_channel
from plotwindow import PlotWindow

SERIAL_ON = False
PLOT_ON = True

# graphic constants
COLUMNNUM = 3
COLUMNWIDTH = 235
HEIGHT = 385
FONT_SIZE = 15
SWITCH_XOFFSET = 10
SWITCH_YOFFSET = 240
SWITCH_WIDTH = 100
SWITCH_HEIGHT = 30
RESET_XOFFSET = 120
RESET_YOFFSET = 5
RESET_WIDTH = 50
RESET_HEIGHT = 15
PLOT_XOFFSET = RESET_XOFFSET + 60
PLOT_YOFFSET = RESET_YOFFSET
PLOT_WIDTH = RESET_WIDTH
PLOT_HEIGHT = RESET_HEIGHT
MINITOGGLE_XOFFSET = 175
MINITOGGLE_YOFFSET = 40
MINITOGGLE_WIDTH = 50
MINITOGGLE_HEIGHT = 20
MINIHEIGHT = 130

# color constant
COLOR_WHITE = "white"
COLOR_BLACK = "black"
COLOR_HIGHLIGHTED = "gray"

# highlighed entry enum
ENTRY_HIGHLIGHTED_NONE = 0
ENTRY_HIGHLIGHTED_FLOWSET_L = 1
ENTRY_HIGHLIGHTED_FLOWSET_M = 2
ENTRY_HIGHLIGHTED_FLOWSET_R = 3
ENTRY_HIGHLIGHTED_CH_L = 4
ENTRY_HIGHLIGHTED_CH_M = 5
ENTRY_HIGHLIGHTED_CH_R = 6

# toggleStateStrings constant
TOGGLE_STATE_ON = "  ON"
TOGGLE_STATE_OFF = "  OFF"
TOGGLE_STATE_SELECT_CHANNEL = "SelectChannel"

# max length of data queue
MAXLEN = 100

class RFMApp:
    def __init__(self, master):
        self.master = master
        self.COLUMNNUM = 3
        self.flowSetPoint_Entry = [""] * self.COLUMNNUM 
        self.flowSetPoints_Shown = ["  Set Channel"] * self.COLUMNNUM
        self.toggleStateStrings = ["  OFF"] * self.COLUMNNUM
        self.flowSetPoints_Sended = [""] * self.COLUMNNUM
        self.channels = [Channel.CH_UNKNOWN] * self.COLUMNNUM
        self.channelsEntry = [""] * self.COLUMNNUM
        self.flowSetPoints_int = [0] * self.COLUMNNUM
        self.flowSetPointBkgColors = [COLOR_BLACK] * self.COLUMNNUM
        self.channelBkgColors = [COLOR_BLACK] * self.COLUMNNUM
        self.highlighted_entry = ENTRY_HIGHLIGHTED_NONE
        self.mn = False
        
        self.lastwidth = 0
        self.lastheight = 0
        self.width = self.COLUMNNUM * COLUMNWIDTH
        self.height = HEIGHT
        self.canvas = tk.Canvas(self.master, width=self.width, height=self.height, bg='black')
        self.canvas.pack()

        self.font = ('Calibri Light', FONT_SIZE)
        
        self.dataqueue_10min = []
        for _ in range(COLUMNNUM + 1):
            self.dataqueue_10min.append(deque(maxlen=MAXLEN))
        self.lasttime = 0
        
        self.plot_window = None
        
        self.setup()
        self.main_loop()

    def on_resize(self, event):
        self.width = event.width
        self.height = event.height
        if self.width != self.lastwidth or self.height != self.lastheight:
            self.draw()
            self.lastwidth = self.width
            self.lastheight = self.height
        # sychronize canvas size with window size
        self.canvas.config(width=self.width, height=self.height)

    def setup(self):
        # Initialize GUI
        self.window = self.master
        # set window size as COLUMNNUM * COLUMNWIDTH x HEIGHT
        self.window.geometry(f"{self.COLUMNNUM * COLUMNWIDTH}x{HEIGHT}")
        # resizable true
        self.window.resizable(True, True)
        self.window.title("RFMv3")
        
        # Setup serial communication
        if SERIAL_ON:
            self.serial = RFMserial("COM3", 9600)
        
        # Add GUI elements (buttons, toggles, text fields)
        self.switchs_toggle = [None] * self.COLUMNNUM
        for i in range(self.COLUMNNUM):
            self.switchs_toggle[i] = tk.Button(self.window, text="OFF", command=lambda index=i: self.on_switch_toggle(index))
            self.switchs_toggle[i].place(x=SWITCH_XOFFSET + i * COLUMNWIDTH, y=SWITCH_YOFFSET, width=SWITCH_WIDTH, height=SWITCH_HEIGHT)
        
        # mini toggle (slide switch)
        self.mini_toggle = tk.Button(self.window, text="Mini", command=self.on_mini_toggle)
        self.mini_toggle.place(x=MINITOGGLE_XOFFSET, y=MINITOGGLE_YOFFSET, width=MINITOGGLE_WIDTH, height=MINITOGGLE_HEIGHT)
        
        # reset button
        self.reset_button = tk.Button(self.window, text="RESET", command=self.on_reset_click)
        self.reset_button.place(x=RESET_XOFFSET, y=RESET_YOFFSET, width=RESET_WIDTH, height=RESET_HEIGHT)
        
        # plot button
        self.plot_button = tk.Button(self.window, text="PLOT", command=self.on_plot_click)
        self.plot_button.place(x=PLOT_XOFFSET, y=PLOT_YOFFSET, width=PLOT_WIDTH, height=PLOT_HEIGHT)
        
        # key bindings
        self.window.bind("<Key>", self.key_pressed)
        self.window.bind("<Button-1>", self.mouse_pressed)
        self.window.bind("<Configure>", self.on_resize)
        
        # save time
        self.lasttime = time.time()

    def main_loop(self):
        self.update()
        self.window.after(100, self.main_loop)  # Schedule next update

    def fillEntryBkgColor(self):
        self.canvas.delete("all")  # 기존 도형 모두 삭제
        if not self.mn:
            for i in range(self.COLUMNNUM):
                # flowSetPointBkgColors 사각형
                x1 = (60 + i * COLUMNWIDTH) * self.width / (self.COLUMNNUM * COLUMNWIDTH)
                y1 = 167 * self.height / HEIGHT
                x2 = x1 + 160 * self.width / (self.COLUMNNUM * COLUMNWIDTH)
                y2 = y1 + 18 * self.height / HEIGHT
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.flowSetPointBkgColors[i], outline="")

                # channelBkgColors 사각형
                y1 = 337 * self.height / HEIGHT
                y2 = y1 + 18 * self.height / HEIGHT
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.channelBkgColors[i], outline="")

    def displayTexts(self):
        COLUMNNAME = ["Tip", "Shield", "Vent"]
        if not self.mn:
            line = '.' * 100
            
            resize_ratio_x = self.width / (self.COLUMNNUM * COLUMNWIDTH)
            resize_ratio_y = self.height / HEIGHT
            resize_ratio_tot = (self.height + self.width) / (self.COLUMNNUM * COLUMNWIDTH + HEIGHT)
            font_size = int(FONT_SIZE * resize_ratio_tot)
            font = ('Calibri Light', font_size)
            
            self.canvas.create_text(0, resize_ratio_y * 125,
                                    text=line, fill='white', font=font, anchor='w')
            self.canvas.create_text(0, resize_ratio_y * 210,
                                    text=line, fill='white', font=font, anchor='w')
            self.canvas.create_text(0, resize_ratio_y * 305,
                                    text=line, fill='white', font=font, anchor='w')

            for i in range(self.COLUMNNUM):
                self.canvas.create_text(resize_ratio_x * (10 + i * COLUMNWIDTH), resize_ratio_y * 20,
                                        text=f"({COLUMNNAME[i]}) Ch  {self.channels[i].value}", fill='white', font=font, anchor='w')
                self.canvas.create_text(resize_ratio_x * (10 + i * COLUMNWIDTH), resize_ratio_y * 55,
                                        text="Sensing Output", fill='white', font=font, anchor='w')
                self.canvas.create_text(resize_ratio_x * (10 + i * COLUMNWIDTH), resize_ratio_y * 150,
                                        text="Setting Input", fill='white', font=font, anchor='w')
                self.canvas.create_text(resize_ratio_x * (10 + i * COLUMNWIDTH), resize_ratio_y * 175,
                                        text=f"Input: {self.flowSetPoint_Entry[i]}", fill='white', font=font, anchor='w')
                self.canvas.create_text(resize_ratio_x * i * COLUMNWIDTH, resize_ratio_y * 200,
                                        text=self.flowSetPoints_Shown[i], fill='white', font=font, anchor='w')
                self.canvas.create_text(resize_ratio_x * (10 + i * COLUMNWIDTH), resize_ratio_y * 325,
                                        text=f"Setting {COLUMNNAME[i]} Ch.", fill='white', font=font, anchor='w')
                self.canvas.create_text(resize_ratio_x * (10 + i * COLUMNWIDTH), resize_ratio_y * 345,
                                        text=f"Input: {self.channelsEntry[i]}", fill='white', font=font, anchor='w')
        else:
            self.master.geometry(f"{self.COLUMNNUM * COLUMNWIDTH}x{MINIHEIGHT}")
            font = ('Calibri Light', FONT_SIZE)
            for i in range(self.COLUMNNUM):
                self.canvas.create_text(10 + i * COLUMNWIDTH, 20,
                                        text=f"({COLUMNNAME[i]}) Ch  {self.channels[i].value}", fill='white', font=font, anchor='w')
                self.canvas.create_text(10 + i * COLUMNWIDTH, 55,
                                        text="Sensing Output", fill='white', font=font, anchor='w')

    def parse_flow_serial_buffer(self, flow_string):
        # 그러한 myString이 존재한다면 100의자리 ~ 10만의 자리까지는 첫 번째 채널의 정보이고,
        # 소수 둘째자리 ~ 10의 자리까지는 두 번째 채널의 정보이므로 myString을 float(소수 숫자)로 한 후
        # 100으로 나누어 준 후 소수자리를 버린후 int(정수)로 저장한다.
        # 100으로 나눈 수 에서 소수자리를 버린 수를 빼서 소수자리만 구한 후 10000을 곱한다.
        # 각각 첫번째, 두번째 채널 정보이고 0-4095의 정보이므로 4095로 나누어 132을 곱해 실제정보를 구한다.
        num = float(flow_string) / 100
        num1 = int(num)
        flow_L = (float(num1) * 99 / 40950)
        flow_R = (1000.000 * (num - num1) * 99 / 4095)
        return [flow_L, flow_R]

    def displayFlowValues(self, flowValues):
        if not self.mn:
            resize_ratio_x = self.width / (self.COLUMNNUM * COLUMNWIDTH)
            resize_ratio_y = self.height / HEIGHT
            resize_ratio_tot = (self.height + self.width) / (self.COLUMNNUM * COLUMNWIDTH + HEIGHT)
            for i in range(self.COLUMNNUM):
                font_size = int(FONT_SIZE * resize_ratio_tot)
                font = ('Calibri Light', font_size)
                self.canvas.create_text(resize_ratio_x * (10 + i * COLUMNWIDTH), resize_ratio_y * 80,
                                        text=flowValues[i], fill='white', font=font, anchor='w')
        else:
            for i in range(self.COLUMNNUM):
                font = ('Calibri Light', FONT_SIZE)
                self.canvas.create_text(10 + i * COLUMNWIDTH, 80,
                                        text=flowValues[i], fill='white', font=font, anchor='w')

    def is_valid_flow_setpoint(self, flow_setpoint):
        return flow_setpoint < 100 and flow_setpoint >= 0
    
    def update_flow_setpoint(self, index):
        if self.channels[index] == Channel.CH_UNKNOWN:
            self.flowSetPoints_Shown[index] = "  Set Channel"
        else:
            if self.is_valid_flow_setpoint(self.flowSetPoints_int[index]):
                self.serial.writeFlowSetpoint_serial(self.flowSetPoint_Entry[index], self.channels[index])
                self.flowSetPoints_Shown[index] = f"  {self.flowSetPoint_Entry[index]}"
                self.flowSetPoints_Sended[index] = self.flowSetPoint_Entry[index]
            else:
                self.flowSetPoints_Shown[index] = "  Input invalid"

    def save_entry_as_integer(self):
        for i in range(self.COLUMNNUM):
            try:
                self.flowSetPoints_int[i] = int(self.flowSetPoint_Entry[i])
            except:
                self.flowSetPoints_int[i] = -1 # just smaller than 0

    def apply_changed_channel(self, index):
        channelEntry_int = 0
        try:
            channelEntry_int = int(self.channelsEntry[index])
        except Exception:
            pass
        self.channelsEntry[index] = ""
        self.channels[index] = convert_int_to_channel(channelEntry_int)
        if self.channels[index] != Channel.CH_UNKNOWN:
            self.flowSetPoints_Sended[index] = ""
            self.flowSetPoints_Shown[index] = "  paused"
            self.serial.setReadingChannel_serial(self.channels)

    def draw(self):
        # background as black
        self.window.configure(bg="black")
        # update width and height from window size
        self.width = self.window.winfo_width()
        self.height = self.window.winfo_height()
        
        self.fillEntryBkgColor()
        self.displayTexts()
        self.replace_toggles()
        self.save_entry_as_integer()
        self.change_highlight_entry_to(self.highlighted_entry)

    def update(self):
        self.draw()

        if not SERIAL_ON:
            return
        
        flow_values = [0] * self.COLUMNNUM
        
        self.serial.setReadingChannel_serial(self.channels)

        serial_buffer = self.serial.readline_serial()
        if serial_buffer:
            temp_flow_values = self.parse_flow_serial_buffer(serial_buffer)
            flow_values[0] = temp_flow_values[0]
            flow_values[1] = temp_flow_values[1]
        

        tempChannels = [Channel.CH_UNKNOWN, self.channels[2]]
        if self.channels[2] == Channel.CH_UNKNOWN:
            flow_values[2] = 0
        else:
            self.serial.setReadingChannel_serial(tempChannels)
            serial_buffer = self.serial.readline_serial()
            if serial_buffer:
                temp_flow_values = self.parse_flow_serial_buffer(serial_buffer)
                flow_values[2] = temp_flow_values[1]
        
        self.displayFlowValues([f"{x:1f}" for x in flow_values])
        
        if time.time() - self.lasttime > 36 and PLOT_ON:
            print("Hello")
            nowtime = time.time()
            self.lasttime = nowtime
            for i in range(self.COLUMNNUM):
                self.dataqueue_10min[i].append(flow_values[i])
            self.dataqueue_10min[-1].append(nowtime)
            if self.plot_window:
                self.plot_window.update_plot(self.dataqueue_10min)
            else:
                print("plot_window is closed")

    def initialize_arrays(self):
        for i in range(self.COLUMNNUM):
            self.flowSetPoint_Entry[i] = ""
            self.flowSetPoints_Shown[i] = "  Set Channel"
            self.toggleStateStrings[i] = TOGGLE_STATE_OFF
            self.flowSetPoints_Sended[i] = ""
            self.channels[i] = Channel.CH_UNKNOWN
            self.channelsEntry[i] = ""
            self.flowSetPoints_int[i] = 0
            self.flowSetPointBkgColors[i] = COLOR_BLACK
            self.channelBkgColors[i] = COLOR_BLACK

    def toggle_switch(self, switch_index, last_switch_state):
        if last_switch_state:
            self.toggleStateStrings[switch_index] = TOGGLE_STATE_OFF
            if self.channels[switch_index] != Channel.CH_UNKNOWN:
                self.flowSetPoints_Shown[switch_index] = "  paused"
                self.flowSetPoint_Entry[switch_index] = ""

            self.serial.writeChannelOff_serial(self.channels[switch_index])
        else:
            if self.channels[switch_index] == Channel.CH_UNKNOWN:
                self.toggleStateStrings[switch_index] = TOGGLE_STATE_SELECT_CHANNEL
            else:
                self.toggleStateStrings[switch_index] = TOGGLE_STATE_ON
                self.flowSetPoints_Shown[switch_index] = "  " + self.flowSetPoints_Sended[switch_index]

            self.serial.writeChannelOn_serial(self.channels[switch_index])

    # Add methods for button clicks, toggles, etc.
    def on_switch_toggle(self, index):
        state = self.switchs_toggle[index].config('relief')[-1] == 'sunken'
        self.toggle_switch(index, state)
        if state:
            self.switchs_toggle[index].config(relief="raised")
            self.switchs_toggle[index].config(text="OFF")
        else:
            self.switchs_toggle[index].config(relief="sunken")
            self.switchs_toggle[index].config(text="ON")

    def on_mini_toggle(self):
        if self.mini_toggle.config('relief')[-1] == 'sunken':
            self.mini_toggle.config(relief="raised")
            self.window.geometry(f"{self.COLUMNNUM * COLUMNWIDTH}x{HEIGHT}")
            self.mn = False
        else:
            self.mini_toggle.config(relief="sunken")
            self.window.geometry(f"{self.COLUMNNUM * COLUMNWIDTH}x{MINIHEIGHT}")
            self.mn = True

    def on_reset_click(self):
        self.initialize_arrays()
        self.serial.reset_serial()

    def on_plot_click(self):
        # make another window by clicking plot button
        if not self.plot_window:
            self.plot_window = PlotWindow(self.master, self.COLUMNNUM)
            if PLOT_ON:
                self.plot_window.update_plot(self.dataqueue_10min)
        else:
            # self.plot_window.root.deiconify()
            self.plot_window = None

    def is_key_code_change_highlight_entry(self, key_code):
        return key_code == 'Tab' or key_code == 'Left' or key_code == 'Right' or key_code == 'Up' or key_code == 'Down'
    
    def change_highlight_entry_using_keycode(self, key_code, highlighted_entry):
        if key_code == 'Tab':
            highlighted_entry = highlighted_entry + 1
        return highlighted_entry

    def key_pressed(self, event):
        if self.is_key_code_change_highlight_entry(event.keysym):
            self.change_highlight_entry_using_keycode(event.keysym, self.highlighted_entry)
        elif event.keysym == 'Return' or event.keysym == 'Enter':
            if self.highlighted_entry == ENTRY_HIGHLIGHTED_FLOWSET_L and self.toggleStateStrings[0] == TOGGLE_STATE_ON:
                self.update_flow_setpoint(0)
            elif self.highlighted_entry == ENTRY_HIGHLIGHTED_FLOWSET_M and self.toggleStateStrings[1] == TOGGLE_STATE_ON:
                self.update_flow_setpoint(1)
            elif self.highlighted_entry == ENTRY_HIGHLIGHTED_FLOWSET_R and self.toggleStateStrings[2] == TOGGLE_STATE_ON:
                self.update_flow_setpoint(2)
            elif self.highlighted_entry == ENTRY_HIGHLIGHTED_CH_L and self.toggleStateStrings[0] == TOGGLE_STATE_OFF:
                self.apply_changed_channel(0)
            elif self.highlighted_entry == ENTRY_HIGHLIGHTED_CH_M and self.toggleStateStrings[1] == TOGGLE_STATE_OFF:
                self.apply_changed_channel(1)
            elif self.highlighted_entry == ENTRY_HIGHLIGHTED_CH_R and self.toggleStateStrings[2] == TOGGLE_STATE_OFF:
                self.apply_changed_channel(2)
        else:
            if self.highlighted_entry == ENTRY_HIGHLIGHTED_FLOWSET_L and self.toggleStateStrings[0] == TOGGLE_STATE_ON:
                self.flowSetPoint_Entry[0] = self.modify_number_string_by_key(self.flowSetPoint_Entry[0], event.keysym, event.char)
            elif self.highlighted_entry == ENTRY_HIGHLIGHTED_FLOWSET_M and self.toggleStateStrings[1] == TOGGLE_STATE_ON:
                self.flowSetPoint_Entry[1] = self.modify_number_string_by_key(self.flowSetPoint_Entry[1], event.keysym, event.char)
            elif self.highlighted_entry == ENTRY_HIGHLIGHTED_FLOWSET_R and self.toggleStateStrings[2] == TOGGLE_STATE_ON:
                self.flowSetPoint_Entry[2] = self.modify_number_string_by_key(self.flowSetPoint_Entry[2], event.keysym, event.char)
            elif self.highlighted_entry == ENTRY_HIGHLIGHTED_CH_L and self.toggleStateStrings[0] == TOGGLE_STATE_OFF:
                self.channelsEntry[0] = self.modify_number_string_by_key(self.channelsEntry[0], event.keysym, event.char)
            elif self.highlighted_entry == ENTRY_HIGHLIGHTED_CH_M and self.toggleStateStrings[1] == TOGGLE_STATE_OFF:
                self.channelsEntry[1] = self.modify_number_string_by_key(self.channelsEntry[1], event.keysym, event.char)
            elif self.highlighted_entry == ENTRY_HIGHLIGHTED_CH_R and self.toggleStateStrings[2] == TOGGLE_STATE_OFF:
                self.channelsEntry[2] = self.modify_number_string_by_key(self.channelsEntry[2], event.keysym, event.char)

    def modify_number_string_by_key(self, number_string, key_code, key):
        if key_code == 'BackSpace' and len(number_string) > 0:
            number_string = number_string[:-1]
        if key.isdigit():
            number_string += key
        return number_string

    def get_column_index_from_mouse(self, mouseX):
        columnwidth = COLUMNWIDTH
        if not self.mn:
            columnwidth = COLUMNWIDTH * self.width / (self.COLUMNNUM * COLUMNWIDTH)
        return np.floor(mouseX / columnwidth)
    
    def get_row_index_from_mouse(self, mouseY):
        SENTINAL_VALUE = -1
        if not self.mn:
            if (mouseY < self.height * 266 / HEIGHT) and (mouseY > 139 * self.height / HEIGHT):
                return 0
            elif mouseY > self.height * 320 / HEIGHT:
                return 1
            else:
                return SENTINAL_VALUE
        else:
            if (mouseY < 266) and (mouseY > 139):
                return 0
            elif mouseY > 320:
                return 1
            else:
                return SENTINAL_VALUE
    
    def get_highlited_entry_from_mouse(self, mouseX, mouseY):
        if self.get_row_index_from_mouse(mouseY) == -1:
            return ENTRY_HIGHLIGHTED_NONE
        return 1 + self.get_column_index_from_mouse(mouseX) + self.COLUMNNUM * self.get_row_index_from_mouse(mouseY)
        
    def mouse_pressed(self, event):
        self.highlighted_entry = self.get_highlited_entry_from_mouse(event.x, event.y)
        self.change_highlight_entry_to(self.highlighted_entry)

    def change_highlight_entry_to(self, entry):
        self.highlighted_entry = entry
        
        if entry == ENTRY_HIGHLIGHTED_FLOWSET_L:
            self.flowSetPointBkgColors[0] = COLOR_HIGHLIGHTED
        else:
            self.flowSetPointBkgColors[0] = COLOR_BLACK
            self.flowSetPoint_Entry[0] = ""
        
        if entry == ENTRY_HIGHLIGHTED_FLOWSET_M:
            self.flowSetPointBkgColors[1] = COLOR_HIGHLIGHTED
        else:
            self.flowSetPointBkgColors[1] = COLOR_BLACK
            self.flowSetPoint_Entry[1] = ""
        
        if entry == ENTRY_HIGHLIGHTED_FLOWSET_R:
            self.flowSetPointBkgColors[2] = COLOR_HIGHLIGHTED
        else:
            self.flowSetPointBkgColors[2] = COLOR_BLACK
            self.flowSetPoint_Entry[2] = ""
        
        if entry == ENTRY_HIGHLIGHTED_CH_L:
            self.channelBkgColors[0] = COLOR_HIGHLIGHTED
        else:
            self.channelBkgColors[0] = COLOR_BLACK
            self.channelsEntry[0] = ""
        
        if entry == ENTRY_HIGHLIGHTED_CH_M:
            self.channelBkgColors[1] = COLOR_HIGHLIGHTED
        else:
            self.channelBkgColors[1] = COLOR_BLACK
            self.channelsEntry[1] = ""
        
        if entry == ENTRY_HIGHLIGHTED_CH_R:
            self.channelBkgColors[2] = COLOR_HIGHLIGHTED
        else:
            self.channelBkgColors[2] = COLOR_BLACK
            self.channelsEntry[2] = ""

    def replace_toggles(self):
        if not self.mn:
            resize_ratio_x = self.width / (self.COLUMNNUM * COLUMNWIDTH)
            resize_ratio_y = self.height / HEIGHT
            for i in range(self.COLUMNNUM):
                self.switchs_toggle[i].place(x=(SWITCH_XOFFSET + i * COLUMNWIDTH) * resize_ratio_x, y=SWITCH_YOFFSET * resize_ratio_y,
                                             width=SWITCH_WIDTH * resize_ratio_x, height=SWITCH_HEIGHT * resize_ratio_y)
            self.reset_button.place(x=RESET_XOFFSET * resize_ratio_x, y=RESET_YOFFSET * resize_ratio_y,
                                    width=RESET_WIDTH * resize_ratio_x, height=RESET_HEIGHT * resize_ratio_y)
            self.plot_button.place(x=PLOT_XOFFSET * resize_ratio_x, y=PLOT_YOFFSET * resize_ratio_y,
                                    width=PLOT_WIDTH * resize_ratio_x, height=PLOT_HEIGHT * resize_ratio_y)
            self.mini_toggle.place(x=MINITOGGLE_XOFFSET * resize_ratio_x, y=MINITOGGLE_YOFFSET * resize_ratio_y,
                                   width=MINITOGGLE_WIDTH * resize_ratio_x, height=MINITOGGLE_HEIGHT * resize_ratio_y)
        else:
            self.reset_button.place(x=RESET_XOFFSET, y=RESET_YOFFSET, width=RESET_WIDTH, height=RESET_HEIGHT)
            self.plot_button.place(x=PLOT_XOFFSET, y=PLOT_YOFFSET, width=PLOT_WIDTH, height=PLOT_HEIGHT)
            self.mini_toggle.place(x=MINITOGGLE_XOFFSET, y=MINITOGGLE_YOFFSET, width=MINITOGGLE_WIDTH, height=MINITOGGLE_HEIGHT)

if __name__ == "__main__":
    master = tk.Tk()
    app = RFMApp(master)
    app.window.mainloop()
