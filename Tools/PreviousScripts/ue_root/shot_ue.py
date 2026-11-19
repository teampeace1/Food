# -*- coding: utf-8 -*-
"""最大化 UE 窗口并等待若干秒后截图。用法: python shot_ue.py <pid> <wait> <out>"""
import ctypes
import sys
import time
from ctypes import wintypes

u = ctypes.windll.user32
u.SetProcessDPIAware()

pid = int(sys.argv[1])
wait = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
out = sys.argv[3] if len(sys.argv) > 3 else r"D:\ue\shot_ue.png"

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
u.ShowWindow(h, 3)          # maximize
u.BringWindowToTop(h)
u.SetForegroundWindow(h)
time.sleep(wait)
from PIL import ImageGrab

im = ImageGrab.grab()
im.save(out)
print("saved", out, im.size)
