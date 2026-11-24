"""Swap the mesh a supply point shows in the kitchen map (the mesh the player will hold).

The runtime picks the held ingredient mesh from the supply point of the same
IngredientName (see FoodIngredientVisualSubsystem), so changing the supply point
here is enough - no code rebuild needed.

Run with the editor CLOSED:
  set ING_NAME=面团
  set ING_MESH=/Game/Food/Meshes/SM_Pie1
  set ING_MAP=/Game/0Input/map/Kitchen_white_final_supply
  UnrealEditor-Cmd.exe Food.uproject -run=pythonscript -ExecutePythonScript="Tools/EditorScripts/set_supply_mesh.py" -unattended -nosplash -nullrhi

Only ING_NAME is required; ING_MESH defaults to a dry-run report.
"""
import os
import unreal

ING_NAME = os.environ.get("ING_NAME", "").strip()
ING_MESH = os.environ.get("ING_MESH", "").strip()
MAP_PATH = os.environ.get("ING_MAP", "/Game/0Input/map/Kitchen_white_final_supply").strip()

lines = []


def log(text):
    lines.append(text)
    unreal.log("[SET_SUPPLY] " + text)


def report_path():
    return os.path.join(unreal.Paths.project_saved_dir(), "set_supply_mesh.txt")


def flush():
    with open(report_path(), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    unreal.log("[SET_SUPPLY] report -> " + report_path())


world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
supplies = []
for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    cls = actor.get_class().get_name()
    if "BP_IngredientSupply" not in cls:
        continue
    try:
        name = str(actor.get_editor_property("IngredientName"))
    except Exception:
        name = ""
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh = comp.get_editor_property("static_mesh") if comp else None
    supplies.append((actor, name, comp, mesh))
    log("supply %s name=%s mesh=%s scale=%s" % (
        actor.get_actor_label(), name,
        mesh.get_path_name() if mesh else "None",
        comp.get_editor_property("relative_scale3d") if comp else ""))

targets = [row for row in supplies if row[1] == ING_NAME]
if not ING_NAME:
    log("ING_NAME not set - dry run only")
elif not targets:
    log("no supply point named %r" % ING_NAME)
elif not ING_MESH:
    log("ING_MESH not set - dry run only")
else:
    mesh = unreal.EditorAssetLibrary.load_asset(ING_MESH)
    if not isinstance(mesh, unreal.StaticMesh):
        log("not a static mesh: %s" % ING_MESH)
    else:
        for actor, name, comp, _old in targets:
            comp.set_editor_property("static_mesh", mesh)
            log("applied %s -> %s" % (actor.get_actor_label(), mesh.get_path_name()))
        unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
        log("saved " + MAP_PATH)

flush()
unreal.SystemLibrary.quit_editor()
