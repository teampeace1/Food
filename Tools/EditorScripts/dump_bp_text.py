# -*- coding: utf-8 -*-
"""Dump human-readable strings (UTF-16LE and ANSI) out of a .uasset.

Blueprint graphs are binary, but FText literals are stored as UTF-16LE, so the
player-facing prompts ("只能是洗干净的鱼头") can be recovered and tell us what each
actor actually accepts.
"""
import io
import re
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARGETS = [
    "Content/FoodGameplay/BP_Pie.uasset",
    "Content/FoodGameplay/BP_FillingBowl.uasset",
    "Content/FoodGameplay/BP_Ingredient.uasset",
]
OUT = os.path.join(ROOT, "Saved", "bp_text.txt")

CJK = re.compile(r"[\u4e00-\u9fff]")
GOOD = re.compile(r"^(?:[\u4e00-\u9fff\u3000-\u303f\uff00-\uffefA-Za-z0-9_ .,:;!?()\-]{2,120})$")

lines = []
for rel in TARGETS:
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        lines.append("### MISSING %s" % rel)
        continue
    data = io.open(path, "rb").read()
    found = []
    # Strings can start on either byte parity, so try both.
    for offset in (0, 1):
        text = data[offset:].decode("utf-16-le", "ignore")
        for m in re.finditer(r"[\u4e00-\u9fff][^\x00]{1,80}", text):
            s = m.group().strip()
            if not CJK.search(s):
                continue
            if not GOOD.match(s):
                continue
            found.append(s)
    # ANSI strings as well (property names, enum values).
    ansi = set()
    for m in re.finditer(rb"[ -~]{4,60}", data):
        s = m.group().decode("ascii", "ignore")
        low = s.lower()
        if any(k in low for k in ("accept", "place", "fill", "head", "wash", "clean", "ingredient", "pie", "bowl")):
            ansi.add(s)
    lines.append("=" * 30 + " " + rel)
    lines.append("-- FText --")
    for s in sorted(set(found)):
        lines.append("   " + s)
    lines.append("-- symbols --")
    for s in sorted(ansi):
        lines.append("   " + s)
    lines.append("")

io.open(OUT, "w", encoding="utf-8").write("\n".join(lines))
print("DUMP_OK %s" % OUT)
