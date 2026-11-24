# -*- coding: utf-8 -*-
"""Read-only: dump WBP_ChefEnding's widget tree via the C++ UMG helper.

Usage: -run=pythonscript -script=dump_ending_tree.py
Result: Saved/ending_tree.json
"""
import json
import os

import unreal

ASSET = "/Game/UI/Widgets/Panels/WBP_ChefEnding"

out = {}
bp = unreal.load_asset(ASSET)
if not bp:
    out = {"error": "asset not found"}
else:
    try:
        raw = unreal.MCPythonHelper.umg_get_widget_info(bp)
        out = json.loads(raw)
    except Exception as exc:  # noqa: BLE001
        out = {"error": repr(exc)}

saved_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
target = os.path.join(saved_dir, "ending_tree.json")
with open(target, "w", encoding="utf-8") as handle:
    json.dump(out, handle, ensure_ascii=False, indent=1)
print("DUMP_ENDING_DONE -> %s" % target)
