"""Align BP_Pie with the filling bowl: seat the pie disc inside the pan and pull the
seven HeadPoint slots down onto the pie surface (they were 85cm in the air).

Run with the editor CLOSED:
  UnrealEditor-Cmd.exe Food.uproject -ExecutePythonScript="Tools/EditorScripts/fix_pie_placement.py" -unattended -nosplash -nullrhi
"""
import json
import math
import os
import unreal

MAP_PATH = "/Game/0Input/map/Kitchen_white_final_supply"
log_rows = []


def note(text):
    log_rows.append(text)
    unreal.log("[FIX_PIE] " + text)


def vec(v):
    return [round(v.x, 2), round(v.y, 2), round(v.z, 2)]


world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()

pie = None
shell = None
bowl_actor = None
for actor in actors:
    cls = actor.get_class().get_name()
    label = actor.get_actor_label()
    if cls == "BP_Pie_C":
        pie = actor
    elif cls == "BP_FillingBowl_C":
        bowl_actor = actor
    elif isinstance(actor, unreal.SkeletalMeshActor) and "壳" in label:
        shell = actor

if pie is None or shell is None:
    note("missing actor: pie=%s shell=%s" % (pie is not None, shell is not None))
else:
    shell_origin, shell_extent = shell.get_actor_bounds(False)
    pan_bottom = shell_origin.z - shell_extent.z
    pan_top = shell_origin.z + shell_extent.z
    pan_inner = min(shell_extent.x, shell_extent.y) * 2.0 * 0.78
    note("pan center=%s bottom=%.1f top=%.1f inner_diameter=%.1f" % (
        vec(shell_origin), pan_bottom, pan_top, pan_inner))

    comps = {comp.get_name(): comp for comp in pie.get_components_by_class(unreal.StaticMeshComponent)}
    disc = comps.get("PieDisc")
    if disc is None:
        note("PieDisc not found")
    else:
        mesh = disc.get_editor_property("static_mesh")
        local_extent = mesh.get_bounds().box_extent
        source_diameter = 2.0 * max(local_extent.x, local_extent.y)
        target_scale = pan_inner / source_diameter if source_diameter > 0 else 1.0
        pie_height = 2.0 * local_extent.z * target_scale
        # Sit the pie on the rim of the pan, not sunk inside it: the bowl is the stand, the pie is on top.
        pie_bottom = pan_top - 3.0
        pie_center_z = pie_bottom + pie_height / 2.0

        # The actor origin was buried 126cm under the table, which breaks every distance check
        # ("press E near the bowl" measured from here). Move it onto the pie centre first.
        pie.set_actor_location(unreal.Vector(shell_origin.x, shell_origin.y, pie_center_z), False, False)
        note("pie actor origin -> %s" % vec(pie.get_actor_location()))

        disc.set_world_scale3d(unreal.Vector(target_scale, target_scale, target_scale))
        disc.set_world_location(unreal.Vector(shell_origin.x, shell_origin.y, pie_center_z), False, False)
        note("disc mesh=%s source_diameter=%.1f -> scale=%.3f diameter=%.1f height=%.1f center_z=%.1f" % (
            mesh.get_path_name(), source_diameter, target_scale, pan_inner, pie_height, pie_center_z))

        # Place the seven head slots on the pie surface, evenly spread inside the crust.
        scene_comps = {c.get_name(): c for c in pie.get_components_by_class(unreal.SceneComponent)}
        slots = [scene_comps.get("HeadPoint%d" % i) for i in range(1, 8)]
        radius = pan_inner * 0.32
        head_z = pie_bottom + pie_height * 0.85
        for index, point in enumerate(slots):
            if point is None:
                continue
            angle = math.radians(index * 360.0 / 7.0)
            point.set_world_location(unreal.Vector(
                shell_origin.x + math.cos(angle) * radius,
                shell_origin.y + math.sin(angle) * radius,
                head_z), False, False)
            note("HeadPoint%d -> %s" % (index + 1, vec(point.get_world_location())))

    if bowl_actor is not None:
        note("bowl actor at %s" % vec(bowl_actor.get_actor_location()))

    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
    note("saved " + MAP_PATH)

path = os.path.join(unreal.Paths.project_saved_dir(), "fix_pie_placement.txt")
with open(path, "w", encoding="utf-8") as handle:
    handle.write("\n".join(log_rows))
unreal.log("[FIX_PIE] report -> " + path)
unreal.SystemLibrary.quit_editor()
