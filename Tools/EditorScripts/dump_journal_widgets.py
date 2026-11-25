# -*- coding: utf-8 -*-
"""Read-only: dump structure/props of the journal widgets."""
import json
import os

import unreal

helper = unreal.MCPythonHelper
ASSETS = [
    "/Game/UI/Widgets/Panels/WBP_Journal",
    "/Game/UI/Widgets/Panels/WBP_MedalRow",
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
            for prop in ("text", "visibility", "padding", "width_override",
                         "height_override", "auto_wrap_text", "brush_color"):
                try:
                    rec[prop] = str(w.get_editor_property(prop))
                except Exception:  # noqa: BLE001
                    pass
            try:
                slot = w.get_editor_property("slot")
                if slot:
                    for prop in ("layout_data", "auto_size", "padding"):
                        try:
                            rec["slot_" + prop] = str(slot.get_editor_property(prop))
                        except Exception:  # noqa: BLE001
                            pass
            except Exception:  # noqa: BLE001
                pass
        entry["widgets"].append(rec)
    out[path] = entry

saved_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
with open(os.path.join(saved_dir, "journal_tree.json"), "w", encoding="utf-8") as handle:
    json.dump(out, handle, ensure_ascii=False, indent=1)
print("JOURNAL_DUMP_DONE")
