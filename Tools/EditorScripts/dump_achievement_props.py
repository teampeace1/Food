# -*- coding: utf-8 -*-
"""List the real UPROPERTY names on the gameplay blueprints the achievement poller reads."""
import json
import os
import unreal

TARGETS = [
    "/Game/FoodGameplay/BP_Ingredient",
    "/Game/FoodGameplay/BP_Pie",
    "/Game/FoodGameplay/BP_Oven",
    "/Game/FoodGameplay/BP_FillingBowl",
    "/Game/FoodGameplay/BP_RollingStation",
    "/Game/FoodGameplay/BP_ChoppingBoard",
    "/Game/FoodGameplay/BP_Sink",
    "/Game/FoodGameplay/BP_Workstation",
]

out = {}
for path in TARGETS:
    rec = {}
    out[path] = rec
    bp = unreal.EditorAssetLibrary.load_asset(path)
    if bp is None:
        rec["error"] = "not found"
        continue
    cdo = unreal.get_default_object(bp.generated_class())
    try:
        names = unreal.BlueprintEditorLibrary.list_member_variable_names(bp)
        rec["variables"] = []
        for name in names:
            entry = {"name": str(name)}
            try:
                entry["type"] = str(unreal.BlueprintEditorLibrary.get_member_variable_type(bp, name))
            except Exception as exc:
                entry["type"] = "? " + str(exc)[:40]
            try:
                entry["default"] = str(cdo.get_editor_property(str(name)))[:80]
            except Exception as exc:
                entry["default"] = "<%s>" % str(exc).splitlines()[0][:50]
            rec["variables"].append(entry)
    except Exception as exc:
        rec["variables_error"] = str(exc)[:160]
    try:
        rec["functions"] = [str(f.get_name()) for f in unreal.BlueprintEditorLibrary.list_functions(bp)]
    except Exception as exc:
        rec["functions_error"] = str(exc)[:160]
    try:
        rec["events"] = [str(f) for f in unreal.BlueprintEditorLibrary.list_events(bp)]
    except Exception as exc:
        rec["events_error"] = str(exc)[:160]

target = os.path.join(unreal.Paths.project_saved_dir(), "achievement_props.json")
with open(target, "w", encoding="utf-8") as handle:
    json.dump(out, handle, ensure_ascii=False, indent=2)
unreal.log("DUMP_ACHIEVEMENT_PROPS " + target)
unreal.SystemLibrary.quit_editor()
