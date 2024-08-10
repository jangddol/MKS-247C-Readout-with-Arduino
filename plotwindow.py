import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import random
import time
from collections import deque
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import gc

class PlotWindow:
    def __init__(self, mother, columnnum):
        self.mother = mother
        self.COLUMNNUM = columnnum
        self.root = None
        self.figure = None
        self.ax = None
        self.canvas = None
        self.lines = []
        self.setup_plot()  # Figure와 axes를 미리 생성

    def create_window(self):
        if self.root and self.root.winfo_exists():
            self.root.lift()
            self.root.focus_force()
            return

        self.root = tk.Toplevel(self.mother)
        self.root.iconbitmap("MFC.ico")
        self.root.title("Plot Window")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def setup_plot(self):
        self.figure = Figure(figsize=(8, 6))
        self.ax = self.figure.add_subplot(111)
        
        LABELS = ["Tip", "Shield", "Vent"]
        COLORS = ["red", "blue", "green"]
        
        for i in range(self.COLUMNNUM):
            line, = self.ax.plot([], [], label=LABELS[i], color=COLORS[i], marker='o')
            self.lines.append(line)
        
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Flow Rate")
        self.ax.set_title("Flow Rate vs Time")
        self.ax.legend(loc='lower left')
        self.ax.grid(True)
        
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M"))
        self.ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
        self.figure.autofmt_xdate()

    def on_close(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        if self.root:
            self.root.destroy()
        self.root = None
        self.canvas = None
        gc.collect()

    def update_plot(self, data):
        if self.root is None or not self.root.winfo_exists():
            return

        if len(data[0]) < 2:
            return

        timestamps = [datetime.fromtimestamp(ts) for ts in data[-1]]
        
        for i in range(self.COLUMNNUM):
            self.lines[i].set_data(timestamps, data[i])
        
        self.ax.relim()
        self.ax.autoscale_view()
        
        self.canvas.draw()
        
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