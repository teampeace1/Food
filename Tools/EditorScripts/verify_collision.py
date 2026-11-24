"""Verify collision settings actually landed on the bowl and pie components."""
import json
import os
import unreal

MAP_PATH = "/Game/0Input/map/Kitchen_white_final_supply"


def body_info(comp):
    info = {"name": comp.get_name()}
    try:
        body = comp.get_editor_property("body_instance")
        for attr in ("collision_enabled", "collision_profile_name", "object_type"):
            try:
                info[attr] = str(body.get_editor_property(attr))
            except Exception as exc:
                info[attr] = "ERR " + str(exc)[:50]
    except Exception as exc:
        info["body_error"] = str(exc)[:80]
    try:
        info["profile"] = str(comp.get_collision_profile_name())
    except Exception:
        pass
    return info


world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()

out = {"bowl": [], "pie": [], "bowl_loc": None, "pie_loc": None}
for actor in actors:
    cls = actor.get_class().get_name()
    if cls == "BP_FillingBowl_C":
        out["bowl_loc"] = [round(v, 1) for v in (actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z)]
        out["bowl"] = [body_info(c) for c in actor.get_components_by_class(unreal.StaticMeshComponent)]
    elif cls == "BP_Pie_C":
        out["pie_loc"] = [round(v, 1) for v in (actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z)]
        out["pie"] = [body_info(c) for c in actor.get_components_by_class(unreal.StaticMeshComponent)]

path = os.path.join(unreal.Paths.project_saved_dir(), "verify_collision.json")
with open(path, "w", encoding="utf-8") as handle:
    json.dump(out, handle, ensure_ascii=False, indent=2)
unreal.log("VERIFY_COLLISION " + path)
unreal.SystemLibrary.quit_editor()
