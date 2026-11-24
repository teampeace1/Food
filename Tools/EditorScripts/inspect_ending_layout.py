# -*- coding: utf-8 -*-
"""Read-only: inspect WBP_ChefEnding layout props (slot, wrap, font, brush)."""
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
    for name in ("Root", "Backdrop", "Content"):
        w = helper.umg_find_widget(bp, name)
        info = {"class": w.get_class().get_name() if w else None}
        if w:
            for prop in ("auto_wrap_text", "wrap_text_at", "justification", "font",
                         "color_and_opacity", "shadow_offset", "shadow_color_and_opacity",
                         "brush", "brush_color", "padding"):
                try:
                    info[prop] = str(w.get_editor_property(prop))
                except Exception as exc:  # noqa: BLE001
                    info[prop] = "N/A"
            try:
                slot = w.get_editor_property("slot")
                info["slot_class"] = slot.get_class().get_name() if slot else None
                if slot:
                    for prop in ("layout", "z_order"):
                        try:
                            info[prop] = str(slot.get_editor_property(prop))
                        except Exception:  # noqa: BLE001
                            pass
            except Exception as exc:  # noqa: BLE001
                info["slot"] = "ERR %r" % (exc,)
        out[name] = info

saved_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
target = os.path.join(saved_dir, "ending_inspect2.json")
with open(target, "w", encoding="utf-8") as handle:
    json.dump(out, handle, ensure_ascii=False, indent=1)
print("INSPECT2_DONE")
