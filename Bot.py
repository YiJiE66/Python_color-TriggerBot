import ctypes
import time
import PIL.ImageGrab
import mss
from ctypes import Structure, c_long, byref
import tkinter as tk
from tkinter import ttk
import keyboard
from pynput import mouse
from tkinter import simpledialog

COLORS = {
    "红色": {"r": 220, "g": 80, "b": 80},
    "黄色": {"r": 210, "g": 210, "b": 60},
    "紫色": {"r": 200, "g": 120, "b": 200},
}
COLOR_CHOICES = list(COLORS.keys())
TOLERANCE = 40
GRABZONE = 2
KEYBOARD_HOTKEY = 'ctrl'  # 默认键盘热键
S_WIDTH, S_HEIGHT = PIL.ImageGrab.grab().size

class FoundEnemy(Exception):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        super().__init__()

class POINT(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]

class TriggerBot:
    def __init__(self):
        self.toggled = False
        self.target_color = COLOR_CHOICES[0]

    def toggle(self, state):
        self.toggled = state

    def switch_color(self):
        current_index = COLOR_CHOICES.index(self.target_color)
        next_index = (current_index + 1) % len(COLOR_CHOICES)
        self.target_color = COLOR_CHOICES[next_index]

    def approx(self, r, g, b):
        color = COLORS[self.target_color]
        return (
                color['r'] - TOLERANCE < r < color['r'] + TOLERANCE and
                color['g'] - TOLERANCE < g < color['g'] + TOLERANCE and
                color['b'] - TOLERANCE < b < color['b'] + TOLERANCE
        )

    def grab(self):
        with mss.mss() as sct:
            bbox = (
                int(S_WIDTH / 2 - GRABZONE),
                int(S_HEIGHT / 2 - GRABZONE),
                int(S_WIDTH / 2 + GRABZONE),
                int(S_HEIGHT / 2 + GRABZONE),
            )
            sct_img = sct.grab(bbox)
            return PIL.Image.frombytes('RGB', sct_img.size, sct_img.bgra, 'raw', 'BGRX')

    def scan(self):
        pmap = self.grab()
        try:
            grabzone_int = int(GRABZONE)
            for x in range(grabzone_int * 2):
                for y in range(grabzone_int * 2):
                    r, g, b = pmap.getpixel((x, y))
                    if self.approx(r, g, b):
                        raise FoundEnemy(x, y)
        except FoundEnemy as e:
            self.click()

    def click(self):
        ctypes.windll.user32.mouse_event(2, 0, 0, 0, 0)
        ctypes.windll.user32.mouse_event(4, 0, 0, 0, 0)

def toggle_visibility(event=None):
    if root.state() == 'normal':
        root.withdraw()
    else:
        root.deiconify()

root = tk.Tk()
root.title("YJ-Bot  \"Ins\"隐藏/显示")
root.geometry("160x460")
root.configure(bg="#4B0082")
root.resizable(False, False)
root.attributes("-toolwindow", 1)
root.attributes("-topmost", True)

bot = TriggerBot()

ttk.Label(root, text="置信度", background="#4B0082", foreground="white").pack(pady=5)
tolerance_slider = ttk.Scale(root, from_=0, to=100, orient="horizontal")
tolerance_slider.set(TOLERANCE)
tolerance_value_label = ttk.Label(root, text=f"当前值: {int(tolerance_slider.get())}", background="#4B0082",
                                  foreground="white")
tolerance_value_label.pack()
tolerance_slider.pack(pady=5)

ttk.Label(root, text="触发范围", background="#4B0082", foreground="white").pack(pady=5)
grabzone_slider = ttk.Scale(root, from_=0, to=10, orient="horizontal")
grabzone_slider.set(GRABZONE)
grabzone_value_label = ttk.Label(root, text=f"当前值: {int(grabzone_slider.get())}", background="#4B0082",
                                 foreground="white")
grabzone_value_label.pack()
grabzone_slider.pack(pady=5)

toggle_button = ttk.Button(root, text="切换颜色", command=bot.switch_color)
toggle_button.pack(pady=10)

status_label = ttk.Label(root, text="机器人状态: 关闭", background="#4B0082", foreground="white")
status_label.pack(pady=5)

color_label = ttk.Label(root, text=f"当前颜色: {bot.target_color}", background="#4B0082", foreground="white")
color_label.pack(pady=5)

keyboard_hotkey_label = ttk.Label(root, text=f"键盘热键: {KEYBOARD_HOTKEY}", background="#4B0082", foreground="white")
keyboard_hotkey_label.pack(pady=5)

mode_label = ttk.Label(root, text="模式: 键盘热键", background="#4B0082", foreground="white")
mode_label.pack(pady=5)

mode = tk.StringVar(value="hotkey")

def update_global_values():
    global TOLERANCE, GRABZONE, AIM_SPEED
    TOLERANCE = int(tolerance_slider.get())
    GRABZONE = int(grabzone_slider.get())

    tolerance_value_label.config(text=f"当前值: {TOLERANCE}")
    grabzone_value_label.config(text=f"当前值: {GRABZONE}")

    status_label.config(text=f"机器人状态: {'开启' if bot.toggled else '关闭'}")
    color_label.config(text=f"当前颜色: {bot.target_color}")

    root.after(100, update_global_values)

def run_scan():
    if bot.toggled:
        bot.scan()
    root.after(10, run_scan)

def on_keyboard_event(e):
    if mode.get() == "hotkey":
        if e.name == KEYBOARD_HOTKEY:
            if e.event_type == keyboard.KEY_DOWN:
                bot.toggle(True)
            elif e.event_type == keyboard.KEY_UP:
                bot.toggle(False)
        status_label.config(text=f"机器人状态: {'开启' if bot.toggled else '关闭'}")

def set_keyboard_hotkey():
    global KEYBOARD_HOTKEY
    new_hotkey = simpledialog.askstring("输入键盘热键", "请输入新的键盘热键（例如：ctrl+shift）:")
    if new_hotkey:
        KEYBOARD_HOTKEY = new_hotkey
        keyboard_hotkey_label.config(text=f"键盘热键: {KEYBOARD_HOTKEY}")

def toggle_mode():
    if mode.get() == "continuous":
        mode.set("hotkey")
        mode_label.config(text="模式: 键盘热键")
        bot.toggle(False)
    else:
        mode.set("continuous")
        mode_label.config(text="模式: 持续开启")
        bot.toggle(True)

set_keyboard_hotkey_button = ttk.Button(root, text="设置键盘热键", command=set_keyboard_hotkey)
set_keyboard_hotkey_button.pack(pady=5)

toggle_mode_button = ttk.Button(root, text="切换模式", command=toggle_mode)
toggle_mode_button.pack(pady=5)

update_global_values()
run_scan()

keyboard.hook(on_keyboard_event)
keyboard.add_hotkey('insert', toggle_visibility)  # Add global hotkey for Insert key

root.mainloop()