# -*- coding: utf-8 -*-
"""导出新菜单蓝图的控件树 + canvas 坐标，便于快速核对。"""
import json
import os

import unreal

ASSETS = [
    "/Game/UI/Widgets/Menus/WBP_MainMenu",
    "/Game/UI/Widgets/Menus/WBP_PauseMenu",
    "/Game/UI/Widgets/Menus/WBP_SettingsMenu",
    "/Game/UI/Widgets/Menus/WBP_ConfirmDialog",
    "/Game/UI/Widgets/Menus/WBP_EndingMenu",
]

out = {}
for path in ASSETS:
    bp = unreal.EditorAssetLibrary.load_asset(path)
    if not bp:
        out[path] = {"error": "missing"}
        continue
    info = json.loads(unreal.MCPythonHelper.umg_get_widget_info(bp))
    rows = []
    for w in info.get("widgets", []):
        row = {"name": w.get("name"), "type": w.get("type"), "parent": w.get("parent")}
        widget = unreal.MCPythonHelper.umg_find_widget(bp, w.get("name"))
        if widget:
            try:
                slot = widget.slot
                if isinstance(slot, unreal.CanvasPanelSlot):
                    pos = slot.get_position()
                    size = slot.get_size()
                    row["pos"] = [round(pos.x, 1), round(pos.y, 1)]
                    row["size"] = [round(size.x, 1), round(size.y, 1)]
            except Exception:  # noqa: BLE001
                pass
            try:
                txt = widget.get_editor_property("text")
                if txt is not None:
                    row["text"] = str(txt)
            except Exception:  # noqa: BLE001
                pass
        rows.append(row)
    out[path.rsplit("/", 1)[-1]] = rows

path = os.path.join(unreal.Paths.project_saved_dir(), "menu_tree.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=2)
unreal.log("[dump_menu_tree] written")
