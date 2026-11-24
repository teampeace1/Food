# -*- coding: utf-8 -*-
"""Read-only: inspect BP graphs for where WBP_ChefEnding is created."""
import json
import os

import unreal

TARGETS = [
    "/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter",
    "/Game/FoodGameplay/BP_Pie",
]

out = {}
for path in TARGETS:
    try:
        out[path] = unreal.FoodGraphTool.inspect_graph(path)
    except Exception as exc:  # noqa: BLE001
        out[path] = "ERR %r" % (exc,)

saved_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
with open(os.path.join(saved_dir, "ending_bp_graph.json"), "w", encoding="utf-8") as handle:
    json.dump(out, handle, ensure_ascii=False, indent=1)
print("BP_GRAPH_DONE")
