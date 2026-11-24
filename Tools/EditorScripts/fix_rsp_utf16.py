# -*- coding: utf-8 -*-
"""Re-encode UBT response files as UTF-16LE.

The local Visual Studio lives under "D:\\新建文件夹", so every .rsp UBT writes contains non-ASCII
paths. cl.exe reads response files as ANSI, which turns those paths into garbage and makes even
<initializer_list> unfindable. UTF-16 (with BOM) is what cl expects for non-ASCII response files.

Covers every .rsp in the project, not just the plugin folder: a SharedPCH response file carries the
same toolchain include paths and fails identically.
"""
import io
import os

ROOTS = ("Intermediate", "Plugins")
SKIP_DIRS = {"__pycache__", ".git"}

converted = []
for root in ROOTS:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if not filename.endswith(".rsp"):
                continue
            path = os.path.join(dirpath, filename)
            raw = io.open(path, "rb").read()
            if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
                continue  # already UTF-16
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = raw.decode("mbcs")
            if text.startswith("\ufeff"):
                text = text[1:]
            io.open(path, "wb").write(b"\xff\xfe" + text.encode("utf-16-le"))
            converted.append(filename)

print("RSP_UTF16 %d files" % len(converted))
