# -*- coding: utf-8 -*-
"""把 UE 窗口临时置顶后截屏。用法: python grab_top.py <pid> <out> [wait]"""
import ctypes
import sys
import time
from ctypes import wintypes

u = ctypes.windll.user32
u.SetProcessDPIAware()

pid = int(sys.argv[1])
out = sys.argv[2]
wait = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0

HWND_TOPMOST = wintypes.HWND(-1)
HWND_NOTOPMOST = wintypes.HWND(-2)
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_SHOWWINDOW = 0x0040

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
h, title = hits[0]
print("window:", title)

u.ShowWindow(h, 3)
u.SetWindowPos(h, HWND_TOPMOST, 0, 0, 0, 0,
               SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
u.SetForegroundWindow(h)
time.sleep(wait)

from PIL import ImageGrab

im = ImageGrab.grab()
im.save(out)
u.SetWindowPos(h, HWND_NOTOPMOST, 0, 0, 0, 0,
               SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
print("saved", out, im.size)
