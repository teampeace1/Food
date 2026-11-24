"""Dump pie / filling bowl / ingredient actors from the kitchen map to Saved/diag_pie_bowl.json.

Run with the editor CLOSED:
  UnrealEditor-Cmd.exe Food.uproject -ExecutePythonScript="Tools/EditorScripts/diag_pie_bowl.py" -unattended -nosplash -nullrhi
"""
import json
import os
import unreal

MAP_PATH = "/Game/0Input/map/Kitchen_white_final_supply"

out = {"map": MAP_PATH, "pies": [], "bowls": [], "skeletal": [], "ingredients": [], "cubes": []}


def vec(v):
    return [round(v.x, 1), round(v.y, 1), round(v.z, 1)]


def safe(actor, prop, default=None):
    try:
        return actor.get_editor_property(prop)
    except Exception:
        return default


def bounds_of(actor):
    try:
        origin, extent = actor.get_actor_bounds(False)
        return {"origin": vec(origin), "extent": vec(extent)}
    except Exception as exc:
        return {"error": str(exc)[:80]}


def components_of(actor):
    rows = []
    for comp in actor.get_components_by_class(unreal.ActorComponent):
        row = {
            "name": comp.get_name(),
            "class": comp.get_class().get_name(),
            "visible": safe(comp, "visible_in_game"),
        }
        if isinstance(comp, (unreal.StaticMeshComponent, unreal.SkeletalMeshComponent)):
            mesh = safe(comp, "static_mesh") or safe(comp, "skeletal_mesh")
            row["mesh"] = mesh.get_path_name() if mesh else None
            row["rel_loc"] = vec(safe(comp, "relative_location")) if safe(comp, "relative_location") else None
        rows.append(row)
    return rows


world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()

for actor in actors:
    cls = actor.get_class().get_name()
    label = actor.get_actor_label()
    loc = vec(actor.get_actor_location())

    if "BP_Pie" in cls:
        out["pies"].append({
            "label": label, "class": cls, "loc": loc, "bounds": bounds_of(actor),
            "components": components_of(actor),
            "scale": vec(actor.get_actor_scale3d()),
        })
    elif "FillingBowl" in cls:
        out["bowls"].append({
            "label": label, "class": cls, "loc": loc, "bounds": bounds_of(actor),
            "components": components_of(actor),
            "children": [c.get_actor_label() + " | " + c.get_class().get_name()
                         for c in actor.get_attached_actors()],
        })
    elif isinstance(actor, unreal.SkeletalMeshActor):
        mesh = None
        try:
            mesh = actor.skeletal_mesh_component.get_editor_property("skeletal_mesh")
        except Exception:
            pass
        out["skeletal"].append({
            "label": label, "loc": loc, "mesh": mesh.get_path_name() if mesh else None,
            "attached_to": actor.get_attach_parent_actor().get_actor_label() if actor.get_attach_parent_actor() else None,
        })
    elif "BP_Ingredient" in cls:
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        mesh = comp.get_editor_property("static_mesh") if comp else None
        out["ingredients"].append({
            "label": label, "class": cls, "loc": loc,
            "name": str(safe(actor, "IngredientName", "")),
            "mesh": mesh.get_path_name() if mesh else None,
        })

    # Anything still rendering an engine cube is a grey block candidate.
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if comp:
        mesh = safe(comp, "static_mesh")
        if mesh and "/Engine/BasicShapes/" in mesh.get_path_name():
            out["cubes"].append({"label": label, "class": cls, "loc": loc, "mesh": mesh.get_path_name()})

path = os.path.join(unreal.Paths.project_saved_dir(), "diag_pie_bowl.json")
with open(path, "w", encoding="utf-8") as handle:
    json.dump(out, handle, ensure_ascii=False, indent=2)
unreal.log("DIAG_PIE_BOWL " + path)
unreal.SystemLibrary.quit_editor()
