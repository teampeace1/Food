"""Inspect BP_Pie: CDO properties, component hierarchy, and visible state of the bowl shell."""
import json
import os
import unreal

MAP_PATH = "/Game/0Input/map/Kitchen_white_final_supply"
out = {}


def vec(v):
    return [round(v.x, 1), round(v.y, 1), round(v.z, 1)]


world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)

# --- blueprint defaults -------------------------------------------------
for bp_path, key in (("/Game/FoodGameplay/BP_Pie", "BP_Pie"),
                     ("/Game/FoodGameplay/BP_Ingredient", "BP_Ingredient"),
                     ("/Game/FoodGameplay/BP_IngredientSupply", "BP_IngredientSupply"),
                     ("/Game/FoodGameplay/BP_FillingBowl", "BP_FillingBowl")):
    rec = {}
    out[key] = rec
    try:
        bp = unreal.EditorAssetLibrary.load_asset(bp_path)
        cdo = unreal.get_default_object(bp.generated_class())
        props = {}
        for prop in cdo.get_class().get_properties():
            name = prop.get_editor_property("name") if hasattr(prop, "get_editor_property") else None
            try:
                pname = prop.get_name()
            except Exception:
                pname = str(prop)
            low = pname.lower()
            if any(token in low for token in ("ingredient", "mesh", "head", "filling", "pie", "name", "slot", "count", "filled")):
                try:
                    props[pname] = str(cdo.get_editor_property(pname))
                except Exception as exc:
                    props[pname] = "ERR " + str(exc)[:60]
        rec["props"] = props
        rec["components"] = []
        for comp in cdo.get_components_by_class(unreal.ActorComponent):
            row = {"name": comp.get_name(), "class": comp.get_class().get_name()}
            for attr in ("static_mesh", "skeletal_mesh"):
                try:
                    m = comp.get_editor_property(attr)
                    if m:
                        row[attr] = m.get_path_name()
                except Exception:
                    pass
            rec["components"].append(row)
    except Exception as exc:
        rec["error"] = str(exc)[:200]

# --- placed actors ------------------------------------------------------
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
pie_rows, bowl_rows, shell_rows = [], [], []
for actor in actors:
    cls = actor.get_class().get_name()
    if cls == "BP_Pie_C":
        comps = []
        for comp in actor.get_components_by_class(unreal.ActorComponent):
            row = {"name": comp.get_name(), "class": comp.get_class().get_name()}
            if isinstance(comp, unreal.SceneComponent):
                row["world"] = vec(comp.get_world_location())
            if isinstance(comp, unreal.StaticMeshComponent):
                m = comp.get_editor_property("static_mesh")
                row["mesh"] = m.get_path_name() if m else None
                try:
                    row["visible"] = comp.get_editor_property("visible")
                except Exception:
                    row["visible"] = "n/a"
            row["parent"] = comp.get_attach_parent().get_name() if isinstance(comp, unreal.SceneComponent) and comp.get_attach_parent() else None
            comps.append(row)
        pie_rows.append({"label": actor.get_actor_label(), "loc": vec(actor.get_actor_location()), "components": comps})
    elif cls == "BP_FillingBowl_C":
        comps = []
        for comp in actor.get_components_by_class(unreal.ActorComponent):
            row = {"name": comp.get_name(), "class": comp.get_class().get_name()}
            if isinstance(comp, unreal.StaticMeshComponent):
                m = comp.get_editor_property("static_mesh")
                row["mesh"] = m.get_path_name() if m else None
                try:
                    row["visible"] = comp.get_editor_property("visible")
                except Exception:
                    row["visible"] = "n/a"
                try:
                    row["visible_in_game"] = comp.get_editor_property("visible_in_game")
                except Exception:
                    pass
            comps.append(row)
        bowl_rows.append({"label": actor.get_actor_label(), "loc": vec(actor.get_actor_location()), "components": comps})
    elif isinstance(actor, unreal.SkeletalMeshActor):
        shell_rows.append({"label": actor.get_actor_label(),
                           "loc": vec(actor.get_actor_location()),
                           "parent": actor.get_attach_parent_actor().get_actor_label() if actor.get_attach_parent_actor() else None})

out["placed_pies"] = pie_rows
out["placed_bowls"] = bowl_rows
out["skeletal_actors"] = shell_rows

path = os.path.join(unreal.Paths.project_saved_dir(), "inspect_pie_bp.json")
with open(path, "w", encoding="utf-8") as handle:
    json.dump(out, handle, ensure_ascii=False, indent=2)
unreal.log("INSPECT_PIE " + path)
unreal.SystemLibrary.quit_editor()
