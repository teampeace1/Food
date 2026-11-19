# -*- coding: utf-8 -*-
"""把 UE 编辑器窗口前置，发送 Ctrl+S 保存全部，再截图确认。"""
import ctypes, time, sys
from ctypes import wintypes

u = ctypes.windll.user32
u.SetProcessDPIAware()

PID = int(sys.argv[1]) if len(sys.argv) > 1 else 0
ACTION = sys.argv[2] if len(sys.argv) > 2 else "save"

hits = []
EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def cb(h, l):
    pid = wintypes.DWORD()
    u.GetWindowThreadProcessId(h, ctypes.byref(pid))
    if pid.value == PID:
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
print("window:", title, hex(h))
u.ShowWindow(h, 9)
u.BringWindowToTop(h)
u.SetForegroundWindow(h)
time.sleep(1.5)

if ACTION in ("save", "save_shot"):
    KEYEVENTF_KEYUP = 0x0002
    VK_CONTROL = 0x11
    VK_S = 0x53
    u.keybd_event(VK_CONTROL, 0, 0, 0)
    time.sleep(0.05)
    u.keybd_event(VK_S, 0, 0, 0)
    time.sleep(0.05)
    u.keybd_event(VK_S, 0, KEYEVENTF_KEYUP, 0)
    u.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
    print("sent ctrl+s")
    time.sleep(6)

if ACTION in ("shot", "save_shot"):
    time.sleep(1.0)
    from PIL import ImageGrab
    path = r"D:\ue\food_before.png"
    ImageGrab.grab().save(path)
    print("shot saved", path)
