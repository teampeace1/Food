# -*- coding: utf-8 -*-
"""导出若干 WBP 的控件树，用于对齐字体/颜色等风格。"""
import json
import os

import unreal

ASSETS = [
    "/Game/UI/Widgets/Panels/WBP_PauseBasic",
    "/Game/UI/Widgets/Panels/WBP_RecipeGuide",
]

out = {}
for a in ASSETS:
    bp = unreal.EditorAssetLibrary.load_asset(a)
    try:
        out[a] = json.loads(unreal.MCPythonHelper.umg_get_widget_info(bp))
    except Exception as exc:  # noqa: BLE001
        out[a] = {"error": repr(exc)}

path = os.path.join(unreal.Paths.project_saved_dir(), "style_probe.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=2)
unreal.log("[style_probe] wrote %s" % path)
