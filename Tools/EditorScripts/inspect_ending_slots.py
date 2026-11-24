# -*- coding: utf-8 -*-
"""Read-only: dump canvas slot geometry of WBP_ChefEnding children."""
import json
import os

import unreal

ASSET = "/Game/UI/Widgets/Panels/WBP_ChefEnding"
helper = unreal.MCPythonHelper
out = {}

bp = unreal.load_asset(ASSET)
if not bp:
    out = {"error": "asset not found"}
else:
    for name in ("Backdrop", "Content"):
        w = helper.umg_find_widget(bp, name)
        info = {}
        if w:
            slot = w.get_editor_property("slot")
            info["slot_class"] = slot.get_class().get_name() if slot else None
            try:
                info["props"] = [p for p in dir(slot) if not p.startswith("_")]
            except Exception as exc:  # noqa: BLE001
                info["props"] = repr(exc)
            for prop in ("layout", "layout_data", "anchors", "offsets", "alignment",
                         "auto_size", "position", "size", "z_order"):
                try:
                    info[prop] = str(slot.get_editor_property(prop))
                except Exception:  # noqa: BLE001
                    pass
        out[name] = info

saved_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
with open(os.path.join(saved_dir, "ending_slots.json"), "w", encoding="utf-8") as handle:
    json.dump(out, handle, ensure_ascii=False, indent=1)
print("SLOTS_DONE")
