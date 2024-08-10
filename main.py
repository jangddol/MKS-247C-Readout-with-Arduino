import tkinter as tk  # Or your chosen GUI framework
import numpy as np
from collections import deque
import time

from RFMserial import RFMserial
from channel import Channel, convert_int_to_channel
from plotwindow import PlotWindow

SERIAL_ON = True
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
        self.setup_initial_state()
        self.setup_ui()
        self.setup_data_collection()
        self.setup_serial(SERIAL_ON)
        self.main_loop()

    def initialize_arrays(self):
        self.flowSetPoint_Entry = [""] * COLUMNNUM
        self.flowSetPoints_Shown = ["  Set Channel"] * COLUMNNUM
        self.toggleStateStrings = [TOGGLE_STATE_OFF] * COLUMNNUM
        self.flowSetPoints_Sended = [""] * COLUMNNUM
        self.channels = [Channel.CH_UNKNOWN] * COLUMNNUM
        self.channelsEntry = [""] * COLUMNNUM
        self.flowSetPointBkgColors = [COLOR_BLACK] * COLUMNNUM
        self.channelBkgColors = [COLOR_BLACK] * COLUMNNUM

    def setup_initial_state(self):
        self.initialize_arrays()
        self.highlighted_entry = ENTRY_HIGHLIGHTED_NONE
        self.mn = False
        self.lastwidth = 0
        self.lastheight = 0
        self.width = COLUMNNUM * COLUMNWIDTH
        self.height = HEIGHT

    def setup_ui(self):
        self.master.geometry(f"{self.width}x{self.height}")
        self.master.resizable(True, True)
        self.master.title("MFC Readout Reader")
        
        self.canvas = tk.Canvas(self.master, width=self.width, height=self.height, bg='black')
        self.canvas.pack()

        self.font = ('Calibri Light', FONT_SIZE)
        
        self.setup_buttons()
        self.setup_bindings()

    def setup_buttons(self):
        self.switchs_toggle = [
            tk.Button(self.master, text="OFF", command=lambda i=i: self.on_switch_toggle(i))
            for i in range(COLUMNNUM)
        ]
        self.mini_toggle = tk.Button(self.master, text="Mini", command=self.on_mini_toggle)
        self.reset_button = tk.Button(self.master, text="RESET", command=self.on_reset_click)
        self.plot_button = tk.Button(self.master, text="PLOT", command=self.on_plot_click)
        
        self.place_buttons()

    def place_buttons(self):
        if not self.mn:
            resize_ratio_x = self.width / (COLUMNNUM * COLUMNWIDTH)
            resize_ratio_y = self.height / HEIGHT
            for i in range(COLUMNNUM):
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

    def setup_bindings(self):
        self.master.bind("<Key>", self.key_pressed)
        self.master.bind("<Button-1>", self.mouse_pressed)
        self.master.bind("<Configure>", self.on_resize)

    def setup_data_collection(self):
        self.dataqueue_10min = [deque(maxlen=MAXLEN) for _ in range(COLUMNNUM + 1)]
        self.lasttime = time.time()
        self.plot_window = None

    def setup_serial(self, on):
        self.serial = RFMserial(on, "COM3", 9600)

    def main_loop(self):
        self.update()
        self.master.after(100, self.main_loop)  # Schedule next update

    def update(self):
        self.draw()
        
        flow_values = self.read_flow_values()
        self.displayFlowValues([f"{x:.2f}" for x in flow_values])
        
        self.update_plot_data(flow_values)

    def read_flow_values(self):
        flow_values = [0] * COLUMNNUM
        
        self.serial.setReadingChannel_serial(self.channels)

        serial_buffer = self.serial.readline_serial()
        if serial_buffer:
            temp_flow_values = self.parse_flow_serial_buffer(serial_buffer)
            flow_values[0] = temp_flow_values[0]
            flow_values[1] = temp_flow_values[1]
        

        tempChannels = [Channel.CH_UNKNOWN, self.channels[2]]
        if self.channels[2] != Channel.CH_UNKNOWN:
            self.serial.setReadingChannel_serial(tempChannels)
            serial_buffer = self.serial.readline_serial()
            if serial_buffer:
                temp_flow_values = self.parse_flow_serial_buffer(serial_buffer)
                flow_values[2] = temp_flow_values[1]

        return flow_values

    def update_plot_data(self, flow_values):
        if time.time() - self.lasttime > 36 and PLOT_ON:
            nowtime = time.time()
            self.lasttime = nowtime
            for i in range(COLUMNNUM):
                self.dataqueue_10min[i].append(flow_values[i])
            self.dataqueue_10min[-1].append(nowtime)
            if self.plot_window:
                self.plot_window.update_plot(self.dataqueue_10min)

    def draw(self):
        # background as black
        self.master.configure(bg="black")
        # update width and height from window size
        self.width = self.master.winfo_width()
        self.height = self.master.winfo_height()
        
        self.fillEntryBkgColor()
        self.displayTexts()
        self.place_buttons()
        self.change_highlight_entry_to(self.highlighted_entry)

    def on_resize(self, event):
        self.width = event.width
        self.height = event.height
        if self.width != self.lastwidth or self.height != self.lastheight:
            self.draw()
            self.lastwidth = self.width
            self.lastheight = self.height
        self.canvas.config(width=self.width, height=self.height)

    def on_switch_toggle(self, index):
        state = self.switchs_toggle[index].config('relief')[-1] == 'sunken'
        self.toggle_switch(index, state)
        if state:
            self.switchs_toggle[index].config(relief="raised", text="OFF")
        else:
            self.switchs_toggle[index].config(relief="sunken", text="ON")

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

    def on_mini_toggle(self):
        if self.mini_toggle.config('relief')[-1] == 'sunken':
            self.mini_toggle.config(relief="raised")
            self.master.geometry(f"{COLUMNNUM * COLUMNWIDTH}x{HEIGHT}")
            self.mn = False
        else:
            self.mini_toggle.config(relief="sunken")
            self.master.geometry(f"{COLUMNNUM * COLUMNWIDTH}x{MINIHEIGHT}")
            self.mn = True

    def on_reset_click(self):
        self.setup_initial_state()
        self.serial.reset_serial()

    def on_plot_click(self):
        if not hasattr(self, 'plot_window') or self.plot_window is None:
            self.plot_window = PlotWindow(self.master, COLUMNNUM)

        self.plot_window.create_window()
        
        if PLOT_ON:
            self.plot_window.update_plot(self.dataqueue_10min)
        
        self.plot_window.root.lift()
        self.plot_window.root.focus_force()

    def fillEntryBkgColor(self):
        self.canvas.delete("all")  # 기존 도형 모두 삭제
        if not self.mn:
            for i in range(COLUMNNUM):
                # flowSetPointBkgColors 사각형
                x1 = (60 + i * COLUMNWIDTH) * self.width / (COLUMNNUM * COLUMNWIDTH)
                y1 = 167 * self.height / HEIGHT
                x2 = x1 + 160 * self.width / (COLUMNNUM * COLUMNWIDTH)
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
            
            resize_ratio_x = self.width / (COLUMNNUM * COLUMNWIDTH)
            resize_ratio_y = self.height / HEIGHT
            resize_ratio_tot = (self.height + self.width) / (COLUMNNUM * COLUMNWIDTH + HEIGHT)
            font_size = int(FONT_SIZE * resize_ratio_tot)
            font = ('Calibri Light', font_size)
            
            self.canvas.create_text(0, resize_ratio_y * 125,
                                    text=line, fill='white', font=font, anchor='w')
            self.canvas.create_text(0, resize_ratio_y * 210,
                                    text=line, fill='white', font=font, anchor='w')
            self.canvas.create_text(0, resize_ratio_y * 305,
                                    text=line, fill='white', font=font, anchor='w')

            for i in range(COLUMNNUM):
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
            self.master.geometry(f"{COLUMNNUM * COLUMNWIDTH}x{MINIHEIGHT}")
            font = ('Calibri Light', FONT_SIZE)
            for i in range(COLUMNNUM):
                self.canvas.create_text(10 + i * COLUMNWIDTH, 20,
                                        text=f"({COLUMNNAME[i]}) Ch  {self.channels[i].value}", fill='white', font=font, anchor='w')
                self.canvas.create_text(10 + i * COLUMNWIDTH, 55,
                                        text="Sensing Output", fill='white', font=font, anchor='w')

    def parse_flow_serial_buffer(self, flow_string):
        # XXX0Y.YY is the format of the flow sensor data
        # XXX * 99 / 40950 is the first channel's flow value
        # YYY * 99 / 40950 is the second channel's flow value
        # the magic numbers 99 and 40950 are determined by the flow sensor's characteristics
        num = float(flow_string) / 100
        num1 = int(num)
        flow_L = (float(num1) * 99 / 40950)
        flow_R = (10000.000 * (num - num1) * 99 / 40950)
        return [flow_L, flow_R]

    def displayFlowValues(self, flowValues):
        if not self.mn:
            resize_ratio_x = self.width / (COLUMNNUM * COLUMNWIDTH)
            resize_ratio_y = self.height / HEIGHT
            resize_ratio_tot = (self.height + self.width) / (COLUMNNUM * COLUMNWIDTH + HEIGHT)
            for i in range(COLUMNNUM):
                font_size = int(FONT_SIZE * resize_ratio_tot)
                font = ('Calibri Light', font_size)
                self.canvas.create_text(resize_ratio_x * (10 + i * COLUMNWIDTH), resize_ratio_y * 80,
                                        text=flowValues[i], fill='white', font=font, anchor='w')
        else:
            for i in range(COLUMNNUM):
                font = ('Calibri Light', FONT_SIZE)
                self.canvas.create_text(10 + i * COLUMNWIDTH, 80,
                                        text=flowValues[i], fill='white', font=font, anchor='w')

    def is_valid_flow_setpoint(self, flow_setpoint_entry):
        try:
            flow_setpoint = int(flow_setpoint_entry)
        except:
            return False
        return flow_setpoint < 100 and flow_setpoint >= 0
    
    def update_flow_setpoint(self, index):
        if self.channels[index] == Channel.CH_UNKNOWN:
            self.flowSetPoints_Shown[index] = "  Set Channel"
        else:
            if self.is_valid_flow_setpoint(self.flowSetPoint_Entry[index]):
                self.serial.writeFlowSetpoint_serial(self.flowSetPoint_Entry[index], self.channels[index])
                self.flowSetPoints_Shown[index] = f"  {self.flowSetPoint_Entry[index]}"
                self.flowSetPoints_Sended[index] = self.flowSetPoint_Entry[index]
            else:
                self.flowSetPoints_Shown[index] = "  Input invalid"

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
            columnwidth = COLUMNWIDTH * self.width / (COLUMNNUM * COLUMNWIDTH)
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
        return 1 + self.get_column_index_from_mouse(mouseX) + COLUMNNUM * self.get_row_index_from_mouse(mouseY)
        
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

if __name__ == "__main__":
    master = tk.Tk()
    master.iconbitmap("MFC.ico")
    app = RFMApp(master)
    app.master.mainloop()
