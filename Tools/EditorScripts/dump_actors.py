# -*- coding: utf-8 -*-
"""List every gameplay actor (and anything sink/board related) with its bounds."""
import json
import os

import unreal

MAP = "/Game/0Input/map/Kitchen_white_final_supply"
OUT = os.path.join(unreal.Paths.project_saved_dir(), "dump_actors.json")

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
actors = [a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
          if isinstance(a, unreal.Actor)]

rows = []
for actor in actors:
    cls = actor.get_class().get_name()
    label = actor.get_actor_label()
    origin, extent = actor.get_actor_bounds(False)
    rows.append({
        "label": label,
        "class": cls,
        "loc": [round(origin.x, 1), round(origin.y, 1), round(origin.z, 1)],
        "bottom": round(origin.z - extent.z, 1),
        "top": round(origin.z + extent.z, 1),
        "size": [round(extent.x * 2, 1), round(extent.y * 2, 1), round(extent.z * 2, 1)],
    })

with open(OUT, "w", encoding="utf-8") as handle:
    json.dump(rows, handle, ensure_ascii=False, indent=1)
unreal.log_warning("DUMP_ACTORS_OK %d" % len(rows))
