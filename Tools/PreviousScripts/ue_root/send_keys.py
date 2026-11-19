# -*- coding: utf-8 -*-
"""向 UE 窗口发送按键。用法: python send_keys.py <pid> alt+p|esc"""
import ctypes
import sys
import time
from ctypes import wintypes

u = ctypes.windll.user32
u.SetProcessDPIAware()

pid = int(sys.argv[1])
combo = sys.argv[2] if len(sys.argv) > 2 else "alt+p"

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
u.ShowWindow(h, 3)
u.BringWindowToTop(h)
u.SetForegroundWindow(h)
time.sleep(1.2)

KEYUP = 0x0002
VK = {"alt": 0x12, "ctrl": 0x11, "shift": 0x10,
      "p": 0x50, "esc": 0x1B, "f": 0x46, "j": 0x4A, "g": 0x47, "home": 0x24,
      "a": 0x41, "c": 0x43, "s": 0x53, "z": 0x5A}

parts = combo.lower().split("+")
mods = [VK[p] for p in parts[:-1]]
key = VK[parts[-1]]

for m in mods:
    u.keybd_event(m, 0, 0, 0)
    time.sleep(0.04)
time.sleep(0.05)
u.keybd_event(key, 0, 0, 0)
time.sleep(0.06)
u.keybd_event(key, 0, KEYUP, 0)
for m in reversed(mods):
    time.sleep(0.04)
    u.keybd_event(m, 0, KEYUP, 0)
print("sent", combo)
