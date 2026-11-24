"""Read-only report of pickup and supply Blueprint defaults and graph nodes."""
import json
import os
import traceback
import unreal

out = {}
try:
    unreal.EditorLoadingAndSavingUtils.load_map('/Game/0Input/map/Kitchen_white_final_supply')
    out['supplies'] = []
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if 'BP_IngredientSupply' in actor.get_class().get_name():
            out['supplies'].append({'label': actor.get_actor_label(), 'name': str(actor.get_editor_property('IngredientName'))})
except Exception:
    out['supply_error'] = traceback.format_exc()
for name in ("BP_Ingredient", "BP_IngredientSupply"):
    path = "/Game/FoodGameplay/" + name
    rec = {}
    out[name] = rec
    try:
        bp = unreal.EditorAssetLibrary.load_asset(path)
        rec["asset_class"] = bp.get_class().get_name()
        cls = bp.generated_class()
        cdo = unreal.get_default_object(cls)
        rec["cdo_properties"] = {}
        for attr in ("IngredientName", "Stock", "MeshRaw", "MeshWashed", "MeshCut", "MeshPieBase", "HeldOffset", "ingredient_name", "mesh_raw", "mesh_washed", "mesh_cut", "mesh_pie_base"):
            try:
                v = cdo.get_editor_property(attr)
                rec["cdo_properties"][attr] = str(v)
            except Exception as e:
                rec["cdo_properties"][attr] = "ERR: " + str(e)[:130]
        for attr in dir(cdo):
            if any(s in attr.lower() for s in ("ingredient", "mesh", "spawn", "food", "name", "size", "scale")):
                try:
                    v = cdo.get_editor_property(attr)
                    rec["cdo_properties"][attr] = str(v)
                except Exception:
                    pass
        rec["components"] = []
        for comp in cdo.get_components_by_class(unreal.ActorComponent):
            row = {"name": comp.get_name(), "class": comp.get_class().get_name()}
            if isinstance(comp, unreal.StaticMeshComponent):
                m = comp.get_editor_property("static_mesh")
                row["mesh"] = m.get_path_name() if m else None
            rec["components"].append(row)
        rec["graphs"] = []
        try:
            graphs = bp.get_editor_property("ubergraph_pages")
            for graph in graphs:
                gr = {"name": graph.get_name(), "nodes": []}
                for node in graph.get_editor_property("nodes"):
                    nr = {"class": node.get_class().get_name(), "title": node.get_node_title(unreal.NodeTitleType.FULL_TITLE) if hasattr(unreal, "NodeTitleType") else node.get_name(), "pins": []}
                    for pin in node.get_editor_property("pins"):
                        nr["pins"].append({"name": str(pin.get_editor_property("pin_name")), "default": str(pin.get_editor_property("default_value")), "object": str(pin.get_editor_property("default_object")), "linked": [str(p.get_editor_property("pin_name")) + " @ " + p.get_outer().get_name() for p in pin.get_editor_property("linked_to")]})
                    gr["nodes"].append(nr)
                rec["graphs"].append(gr)
        except Exception:
            rec["graph_error"] = traceback.format_exc()
    except Exception:
        rec["error"] = traceback.format_exc()

fp = os.path.join(unreal.Paths.project_saved_dir(), "pickup_blueprints.json")
with open(fp, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
unreal.log("PICKUP_INSPECT " + fp)
unreal.SystemLibrary.quit_editor()
