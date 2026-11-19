# -*- coding: utf-8 -*-
"""在指定屏幕坐标滚动鼠标滚轮。用法: python wheel.py <pid> <x> <y> <count>  (count 负数=向下/缩小)"""
import ctypes
import sys
import time
from ctypes import wintypes

u = ctypes.windll.user32
u.SetProcessDPIAware()

pid = int(sys.argv[1])
x, y = int(sys.argv[2]), int(sys.argv[3])
count = int(sys.argv[4])

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
if hits:
    h = hits[0][0]
    u.ShowWindow(h, 3)
    u.SetWindowPos(h, wintypes.HWND(-1), 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0040)
    u.SetForegroundWindow(h)
    time.sleep(0.8)

u.SetCursorPos(x, y)
time.sleep(0.3)
MOUSEEVENTF_WHEEL = 0x0800
for _ in range(abs(count)):
    delta = -120 if count < 0 else 120
    u.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, ctypes.c_ulong(delta & 0xFFFFFFFF).value, 0)
    time.sleep(0.12)
print("wheel done at (%d,%d) x%d" % (x, y, count))
