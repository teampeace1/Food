# -*- coding: utf-8 -*-
"""点击图表空白处聚焦，然后 Ctrl+A / Ctrl+C 复制节点。用法: python bp_copy.py <pid> <x> <y>"""
import ctypes
import sys
import time
from ctypes import wintypes

u = ctypes.windll.user32
u.SetProcessDPIAware()

pid = int(sys.argv[1])
cx = int(sys.argv[2])
cy = int(sys.argv[3])

hits = []
EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def cb(h, l):
    p = wintypes.DWORD()
    u.GetWindowThreadProcessId(h, ctypes.byref(p))
    if p.value == pid:
        buf = ctypes.create_unicode_buffer(512)
        u.GetWindowTextW(h, buf, 512)
        if u.IsWindowVisible(h) and len(buf.value) > 3:
            hits.append((h, buf.value))
    return True


u.EnumWindows(EnumProc(cb), 0)
if not hits:
    print("window not found")
    sys.exit(1)
h = hits[0][0]
u.ShowWindow(h, 9)
u.BringWindowToTop(h)
u.SetForegroundWindow(h)
time.sleep(1.0)

# 单击空白处，把焦点给图表
u.SetCursorPos(cx, cy)
time.sleep(0.3)
u.mouse_event(0x0002, 0, 0, 0, 0)  # left down
time.sleep(0.06)
u.mouse_event(0x0004, 0, 0, 0, 0)  # left up
time.sleep(0.8)

KEYUP = 0x0002
CTRL, A, C = 0x11, 0x41, 0x43


def combo(key):
    u.keybd_event(CTRL, 0, 0, 0)
    time.sleep(0.05)
    u.keybd_event(key, 0, 0, 0)
    time.sleep(0.08)
    u.keybd_event(key, 0, KEYUP, 0)
    time.sleep(0.05)
    u.keybd_event(CTRL, 0, KEYUP, 0)
    time.sleep(0.4)


combo(A)
combo(C)
print("clicked and copied")
