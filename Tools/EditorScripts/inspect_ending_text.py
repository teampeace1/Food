# -*- coding: utf-8 -*-
"""Read-only: inspect the Content text block of WBP_ChefEnding."""
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
    for prop in ("text", "font", "auto_wrap_text", "justification", "color_and_opacity",
                 "visibility", "slot"):
        try:
            out[prop] = json.loads(helper.umg_get_widget_property(bp, "Content", prop))
        except Exception as exc:  # noqa: BLE001
            out[prop] = "ERR %r" % (exc,)
    for prop in ("brush", "brush_color", "padding"):
        try:
            out["backdrop_" + prop] = json.loads(helper.umg_get_widget_property(bp, "Backdrop", prop))
        except Exception as exc:  # noqa: BLE001
            out["backdrop_" + prop] = "ERR %r" % (exc,)

saved_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
target = os.path.join(saved_dir, "ending_inspect.json")
with open(target, "w", encoding="utf-8") as handle:
    json.dump(out, handle, ensure_ascii=False, indent=1)
print("INSPECT_ENDING_DONE -> %s" % target)
