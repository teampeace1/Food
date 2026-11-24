import json, traceback, unreal

MAP = "/Game/0Input/map/Kitchen_white_final_supply"
OUT = unreal.Paths.project_saved_dir() + "/LevelDumps/diag_surface.json"

def log(m):
    unreal.log("[diag] " + str(m))

try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    acts = eas.get_all_level_actors()
    supplies = [a for a in acts if "IngredientSupply" in a.get_class().get_name()]
    skip = set(a.get_name() for a in supplies)
    rep = []
    for s in supplies:
        c = s.get_component_by_class(unreal.StaticMeshComponent)
        m = c.get_editor_property("static_mesh")
        bb = m.get_bounding_box()
        sw = c.get_world_scale()
        p = s.get_actor_location()
        bottom = p.z + bb.min.z * sw.z
        top = p.z + bb.max.z * sw.z
        cands = []
        for a in acts:
            if a.get_name() in skip:
                continue
            try:
                o, e = a.get_actor_bounds(False)
            except Exception:
                continue
            if e.z < 1: continue
            if abs(p.x - o.x) > e.x + 5 or abs(p.y - o.y) > e.y + 5: continue
            cands.append({"label": a.get_actor_label(), "cls": a.get_class().get_name(),
                          "top": round(o.z + e.z, 1), "bbox": [round(o.x,0), round(o.y,0), round(o.z,0), round(e.x,0), round(e.y,0), round(e.z,0)]})
        cands.sort(key=lambda r: abs(r["top"] - bottom))
        rep.append({"label": s.get_actor_label(), "bottom": round(bottom,1), "top": round(top,1),
                    "at": [round(p.x,1), round(p.y,1), round(p.z,1)], "cands": cands[:6]})
        log("%-12s bottom=%.1f 候选: %s" % (s.get_actor_label(), bottom,
            " | ".join("%s(%s)top=%.1f" % (x["label"][:22], x["cls"][:14], x["top"]) for x in cands[:4])))
    json.dump(rep, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    log("报告: " + OUT)
except Exception:
    log("异常:\n" + traceback.format_exc())
finally:
    try:
        unreal.SystemLibrary.quit_editor()
    except Exception:
        pass
