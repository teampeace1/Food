# -*- coding: utf-8 -*-
"""Read-only: dump structure/props of the toast + popup widgets."""
import json
import os

import unreal

helper = unreal.MCPythonHelper
ASSETS = [
    "/Game/UI/Widgets/HUD/WBP_MemoryToast",
    "/Game/UI/Widgets/HUD/WBP_AchievementPopup",
]

out = {}
for path in ASSETS:
    bp = unreal.load_asset(path)
    entry = {"widgets": []}
    if not bp:
        entry["error"] = "missing"
        out[path] = entry
        continue
    info = json.loads(helper.umg_get_widget_info(bp))
    for item in info.get("widgets", []):
        name = item["name"]
        rec = dict(item)
        w = helper.umg_find_widget(bp, name)
        if w:
            for prop in ("text", "font", "visibility", "padding", "width_override",
                         "height_override", "auto_size", "auto_wrap_text", "brush_color"):
                try:
                    rec[prop] = str(w.get_editor_property(prop))
                except Exception:  # noqa: BLE001
                    pass
            try:
                slot = w.get_editor_property("slot")
                if slot:
                    for prop in ("layout_data", "auto_size", "padding", "z_order"):
                        try:
                            rec["slot_" + prop] = str(slot.get_editor_property(prop))
                        except Exception:  # noqa: BLE001
                            pass
            except Exception:  # noqa: BLE001
                pass
        entry["widgets"].append(rec)
    out[path] = entry

saved_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
with open(os.path.join(saved_dir, "toast_widgets.json"), "w", encoding="utf-8") as handle:
    json.dump(out, handle, ensure_ascii=False, indent=1)
print("TOAST_DUMP_DONE")
