import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import random
import time
from collections import deque
import matplotlib.dates as mdates

class PlotWindow:
    def __init__(self, mother, columnnum):
        self.mother = mother
        self.COLUMNNUM = columnnum
        self.root = tk.Tk()
        self.root.title("Plot Window")
        self.root.geometry("800x600")
        self.label = tk.Label(master=self.root, text="")
        self.label.pack()
        
        plt.rcParams.update({'font.size': 10})
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.label)
    
    def update_plot(self, data):
        if len(data[0]) < 2:
            return # if the number of element is 1, then plt hangs

        # data is a tuples of deque of tuple : dim : [4, < MAX_DATA]
        # last one is time : x axis
        LABELS = ["Tip", "Shield", "Vent"]
        COLORS = ["red", "blue", "green"]
        self.ax.clear()
        
        timestamps = [datetime.fromtimestamp(ts) for ts in data[-1]]
        for i in range(self.COLUMNNUM):
            self.ax.plot(timestamps, data[i], label=LABELS[i], color=COLORS[i], marker='o')
        
        self.ax.set_xlabel("Time")
        # x axis formatter
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M"))
        self.ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
        self.figure.autofmt_xdate()

        self.ax.set_ylabel("Flow Rate")
        self.ax.set_title("Flow Rate vs Time")
        self.ax.legend(loc='lower left')
        self.ax.grid(True)
        
        if self.canvas:
            self.canvas.get_tk_widget().forget()
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()
        
    def start_data_update_for_test(self, data):
        for j in range(3):
            data[j].append(random.random())
        data[-1].append(time.time())
        self.update_plot(data)
        self.root.after(1000, self.start_data_update_for_test, data)  # 1초 후에 다시 호출

if __name__ == "__main__":
    mother = tk.Tk()
    plotwindow = PlotWindow(mother, 3)
    MAX_DATA = 100
    data = [deque(maxlen=MAX_DATA) for _ in range(3)]
    data.append(deque(maxlen=MAX_DATA))

    # 데이터 업데이트 시작
    plotwindow.start_data_update_for_test(data)

    # UI 메인 루프 시작
    mother.mainloop()