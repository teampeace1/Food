# -*- coding: utf-8 -*-
"""探查 python 侧 UMG 相关 API 的真实形态（枚举名/结构体字段类型）。"""
import json
import os

import unreal

out = {}

out["has_HorizontalAlignment"] = hasattr(unreal, "HorizontalAlignment")
if out["has_HorizontalAlignment"]:
    out["HorizontalAlignment"] = [n for n in dir(unreal.HorizontalAlignment) if not n.startswith("_")][:20]
out["has_EHorizontalAlignment"] = hasattr(unreal, "EHorizontalAlignment")

out["Vector2D_attrs"] = [n for n in dir(unreal.Vector2D) if not n.startswith("_")][:8]
out["has_Vector2f"] = hasattr(unreal, "Vector2f")

# SlateBrush 的 ImageSize 到底是什么结构
b = unreal.SlateBrush()
out["brush_type"] = type(b).__name__
for prop in ("image_size", "uv_region", "draw_as", "tint_color"):
    try:
        val = b.get_editor_property(prop)
        out["brush_" + prop] = "%s (%s)" % (val, type(val).__name__)
    except Exception as exc:  # noqa: BLE001
        out["brush_" + prop] = "ERR %r" % (exc,)

# ButtonStyle 的属性
bs = unreal.ButtonStyle()
out["button_style_attrs"] = [n for n in dir(bs) if not n.startswith("_")]

path = os.path.join(unreal.Paths.project_saved_dir(), "api_probe.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=2)
unreal.log("[api_probe] written")
