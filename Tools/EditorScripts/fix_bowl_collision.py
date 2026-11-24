"""Stop the filling bowl's invisible Table/Bowl colliders from swallowing the pie interaction,
and make sure the pie disc itself is traceable.

Run with the editor CLOSED:
  UnrealEditor-Cmd.exe Food.uproject -ExecutePythonScript="Tools/EditorScripts/fix_bowl_collision.py" -unattended -nosplash -nullrhi
"""
import json
import os
import unreal

MAP_PATH = "/Game/0Input/map/Kitchen_white_final_supply"
rows = []


def note(text):
    rows.append(text)
    unreal.log("[BOWL_COLLISION] " + text)


def describe(comp):
    info = {"name": comp.get_name(), "class": comp.get_class().get_name()}
    for attr in ("collision_enabled", "collision_profile_name"):
        try:
            info[attr] = str(comp.get_editor_property(attr))
        except Exception as exc:
            info[attr] = "ERR " + str(exc)[:60]
    try:
        info["visible"] = str(comp.get_editor_property("visible"))
    except Exception:
        pass
    return info


world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()

bowl = next((a for a in actors if a.get_class().get_name() == "BP_FillingBowl_C"), None)
pie = next((a for a in actors if a.get_class().get_name() == "BP_Pie_C"), None)

report = {"bowl": [], "pie": []}

if bowl:
    for comp in bowl.get_components_by_class(unreal.StaticMeshComponent):
        report["bowl"].append(describe(comp))
        if comp.get_name() in ("Table", "Bowl"):
            comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            note("disabled collision on bowl/%s" % comp.get_name())
    for comp in bowl.get_components_by_class(unreal.StaticMeshComponent):
        report["bowl_after"] = report.get("bowl_after", [])
        report["bowl_after"].append(describe(comp))

if pie:
    for comp in pie.get_components_by_class(unreal.StaticMeshComponent):
        row = describe(comp)
        report["pie"].append(row)
        if comp.get_name().startswith("HeadMesh"):
            # Invisible 100cm cube placeholders - they must not eat the interaction trace.
            comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            note("disabled collision on pie/%s" % comp.get_name())
        if comp.get_name() == "PieDisc":
            comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
            try:
                comp.set_collision_profile_name("BlockAllDynamic")
            except Exception as exc:
                note("profile set failed: " + str(exc)[:80])
            note("PieDisc -> QueryOnly / BlockAllDynamic")
    report["pie_after"] = [describe(comp) for comp in pie.get_components_by_class(unreal.StaticMeshComponent)]

if bowl or pie:
    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
    note("saved")
else:
    note("actors not found: bowl=%s pie=%s" % (bowl is not None, pie is not None))

path = os.path.join(unreal.Paths.project_saved_dir(), "fix_bowl_collision.json")
with open(path, "w", encoding="utf-8") as handle:
    json.dump({"log": rows, "report": report}, handle, ensure_ascii=False, indent=2)
unreal.log("[BOWL_COLLISION] report -> " + path)
unreal.SystemLibrary.quit_editor()
