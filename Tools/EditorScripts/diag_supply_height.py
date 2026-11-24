# -*- coding: utf-8 -*-
"""Measure how far supply points and loose ingredients float above the surface under them.

For every candidate we take the bottom of its bounds and compare it with the surface height
estimated from small props nearby (median of their bottoms) - the same estimator that was used
when the supply points were lifted onto the counter.
"""
import json
import os
import statistics

import unreal

MAP = "/Game/0Input/map/Kitchen_white_final_supply"
OUT = os.path.join(unreal.Paths.project_saved_dir(), "diag_supply_height.json")

SKIP_KEYWORDS = (
    "BP_Ingredient",
    "BP_FillingBowl",
    "BP_Pie",
    "BP_FirstPerson",
    "Light",
    "Sky",
    "Fog",
    "PostProcess",
    "ExponentialHeightFog",
    "SkyAtmosphere",
    "SkyLight",
    "DirectionalLight",
    "PlayerStart",
    "NavMesh",
    "RecastNavMesh",
    "Brush",
    "WorldSettings",
    "WorldDataLayers",
)


def is_candidate_prop(actor):
    cls = actor.get_class().get_name()
    label = actor.get_actor_label()
    for key in SKIP_KEYWORDS:
        if key in cls or key in label:
            return False
    if not isinstance(actor, unreal.StaticMeshActor):
        return False
    return True


def bounds_of(actor):
    origin, extent = actor.get_actor_bounds(False)
    return {
        "center": [round(origin.x, 1), round(origin.y, 1), round(origin.z, 1)],
        "bottom": round(origin.z - extent.z, 1),
        "top": round(origin.z + extent.z, 1),
        "size": [round(extent.x * 2, 1), round(extent.y * 2, 1), round(extent.z * 2, 1)],
    }


def surface_near(actor, props, radius=180.0):
    loc = actor.get_actor_location()
    bottoms = []
    for prop in props:
        if prop == actor:
            continue
        ploc = prop.get_actor_location()
        if abs(ploc.x - loc.x) > radius or abs(ploc.y - loc.y) > radius:
            continue
        if abs(ploc.z - loc.z) > 260:
            continue
        b = bounds_of(prop)
        if b["size"][2] > 45:  # ignore tall things: walls, cabinets, shelves
            continue
        bottoms.append(b["bottom"])
    if not bottoms:
        return None, 0
    return round(statistics.median(bottoms), 1), len(bottoms)


def mesh_name(actor):
    try:
        comp = actor.static_mesh_component
        mesh = comp.get_editor_property("static_mesh")
        if mesh:
            return mesh.get_name()
    except Exception:
        pass
    return ""


world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
actors = [a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
          if isinstance(a, unreal.Actor)]

props = [a for a in actors if is_candidate_prop(a)]

supplies = []
ingredients = []
for actor in actors:
    cls = actor.get_class().get_name()
    if "IngredientSupply" in cls:
        supplies.append(actor)
    elif cls == "BP_Ingredient_C":
        ingredients.append(actor)


def describe(actor, kind):
    b = bounds_of(actor)
    surface, samples = surface_near(actor, props)
    row = {
        "kind": kind,
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "loc": [round(v, 1) for v in (actor.get_actor_location().x,
                                      actor.get_actor_location().y,
                                      actor.get_actor_location().z)],
        "mesh": mesh_name(actor),
        "bounds": b,
        "surface_z": surface,
        "samples": samples,
    }
    row["gap"] = round(b["bottom"] - surface, 1) if surface is not None else None
    parent = actor.get_attach_parent_actor()
    row["parent"] = parent.get_actor_label() if parent else None
    return row


out = {
    "supplies": [describe(a, "supply") for a in supplies],
    "ingredients": [describe(a, "ingredient") for a in ingredients],
}

with open(OUT, "w", encoding="utf-8") as handle:
    json.dump(out, handle, ensure_ascii=False, indent=1)
unreal.log_warning("DIAG_SUPPLY_OK")
