"""只读体检：搞清 4 个灰色方块是什么、供应点蓝图内部怎么挂模型。

不写盘、不改任何东西。输出到 Saved/LevelDumps/inspect_supply_<ts>.json
"""

import os
import json
import time
import traceback
import unreal

MAP_PATH = "/Game/0Input/map/Kitchen_white_final"
BP_GUESS = "/Game/FoodGameplay/BP_IngredientSupply"
OUT_DIR = os.path.join(unreal.Paths.project_saved_dir(), "LevelDumps")
KEYWORDS = ["pars", "onio", "dough", "season", "salt", "pepper", "fish", "shrimp",
            "qingcai", "调料", "面团", "欧芹", "洋葱", "鱼", "供应"]

CTX = {"handle": None, "ticks": 0, "done": False, "quit_at": None,
       "phase": 0, "load_tick": 0, "loaded": False}


def log(m):
    unreal.log("[inspect] " + str(m))


def warn(m):
    unreal.log_warning("[inspect] " + str(m))


def act_mesh(a):
    try:
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        if c is None:
            return None
        m = c.get_editor_property("static_mesh")
        return m.get_path_name() if m else None
    except Exception:
        return None


def comps_of(a):
    out = []
    try:
        comps = a.get_components_by_class(unreal.StaticMeshComponent)
    except Exception:
        comps = []
    for c in comps:
        try:
            m = c.get_editor_property("static_mesh")
            mesh = m.get_path_name() if m else None
        except Exception:
            mesh = None
        mats = []
        try:
            for i in range(c.get_num_materials()):
                mm = c.get_material(i)
                mats.append(mm.get_path_name() if mm else None)
        except Exception:
            pass
        loc = c.get_world_location()
        try:
            vis = c.is_visible()
        except Exception:
            vis = None
        out.append({"comp": c.get_name(), "mesh": mesh, "mats": mats,
                    "visible": vis,
                    "world": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)]})
    return out


def nearby(actors, pos, radius):
    out = []
    for a in actors:
        p = a.get_actor_location()
        d = ((p.x - pos.x) ** 2 + (p.y - pos.y) ** 2 + (p.z - pos.z) ** 2) ** 0.5
        if d <= radius:
            out.append({"label": a.get_actor_label(), "name": a.get_name(),
                        "class": a.get_class().get_name(),
                        "mesh": act_mesh(a), "dist": round(d, 1),
                        "at": [round(p.x, 1), round(p.y, 1), round(p.z, 1)]})
    out.sort(key=lambda r: r["dist"])
    return out


def candidates():
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    try:
        filt = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "StaticMesh")],
                               recursive_paths=True, package_paths=["/Game"])
        assets = ar.get_assets(filt)
    except Exception:
        warn("AssetRegistry 查询失败: %s" % traceback.format_exc())
        return {}
    buckets = {}
    for a in assets:
        nm = str(a.asset_name)
        low = nm.lower()
        for k in KEYWORDS:
            if k.lower() in low:
                buckets.setdefault(k, []).append(
                    {"name": nm, "path": str(a.package_name)})
    return buckets


def run():
    res = {"map": MAP_PATH, "ts": time.strftime("%Y%m%d_%H%M%S")}
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = eas.get_all_level_actors()
    res["total"] = len(actors)

    sup, cubes = [], []
    for a in actors:
        cls = a.get_class().get_name()
        lab = a.get_actor_label()
        if "Ingredient" in cls or "供应" in lab:
            p = a.get_actor_location()
            sup.append({"label": lab, "name": a.get_name(), "class": cls,
                        "at": [round(p.x, 1), round(p.y, 1), round(p.z, 1)],
                        "comps": comps_of(a),
                        "tags": [str(t) for t in (a.get_editor_property("tags") or [])]})
        m = act_mesh(a)
        if m and ("立方体" in m or "/Cube" in m or "polySurface" in m or "acb666d3" in m):
            p = a.get_actor_location()
            cubes.append({"label": lab, "name": a.get_name(), "class": cls, "mesh": m,
                          "at": [round(p.x, 1), round(p.y, 1), round(p.z, 1)]})
    res["supply"] = sup
    res["cube_like_total"] = len(cubes)
    res["cube_like_near_supply"] = [c for c in cubes if any(
        abs(c["at"][0] - s["at"][0]) < 400 and abs(c["at"][1] - s["at"][1]) < 400 for s in sup)]

    if sup:
        p0 = sup[0]["at"]
        res["near_first_supply"] = nearby(actors, unreal.Vector(p0[0], p0[1], p0[2]), 260.0)

    # 蓝图自身结构
    bp_info = {}
    try:
        bp = unreal.EditorAssetLibrary.load_asset(BP_GUESS)
        if bp:
            gen = bp.generated_class()
            cdo = unreal.get_default_object(gen)
            bp_info["class"] = gen.get_name()
            bp_info["cdo_comps"] = comps_of(cdo) if cdo else []
            props = []
            for name in ("ingredient_mesh", "IngredientMesh", "mesh", "Mesh",
                         "ingredient_name", "IngredientName", "ingredient_id"):
                try:
                    v = cdo.get_editor_property(name)
                    props.append({name: str(v)})
                except Exception:
                    pass
            bp_info["guess_props"] = props
            try:
                comp_names = [c.get_name() for c in cdo.get_components_by_class(unreal.ActorComponent)]
                bp_info["all_comps"] = comp_names
            except Exception:
                pass
        else:
            bp_info["error"] = "load failed"
    except Exception:
        bp_info["error"] = traceback.format_exc()
    res["bp"] = bp_info
    res["candidates"] = candidates()

    os.makedirs(OUT_DIR, exist_ok=True)
    fp = os.path.join(OUT_DIR, "inspect_supply_%s.json" % res["ts"])
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)

    log("供应点 %d 个" % len(sup))
    for s in sup:
        log("  %s @%s comps=%d" % (s["label"], s["at"], len(s["comps"])))
        for c in s["comps"]:
            log("     - %s mesh=%s mats=%s" % (c["comp"], c["mesh"], c["mats"]))
    log("疑似方块 %d 个，其中靠近供应点的 %d 个" % (len(cubes), len(res["cube_like_near_supply"])))
    for c in res["cube_like_near_supply"][:12]:
        log("  cube %-14s %-18s %s %s" % (c["label"], c["class"], c["at"], (c["mesh"] or "")[-40:]))
    log("蓝图: %s" % json.dumps(bp_info.get("cdo_comps", []), ensure_ascii=False)[:600])
    for k, v in res["candidates"].items():
        log("  候选[%s] %d 个: %s" % (k, len(v), ", ".join(x["name"] for x in v[:8])))
    log("报告: %s" % fp)


def _tick(_dt):
    CTX["ticks"] += 1
    try:
        if CTX["quit_at"] is not None and CTX["ticks"] >= CTX["quit_at"]:
            _stop()
            log("退出编辑器")
            try:
                unreal.SystemLibrary.quit_editor()
            except Exception:
                pass
            return
        if CTX["done"]:
            return
        if CTX["ticks"] < 3:
            return
        if CTX["phase"] == 0:
            log("加载 %s" % MAP_PATH)
            CTX["phase"] = 1
            CTX["load_tick"] = CTX["ticks"]
            try:
                unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
            except Exception:
                warn("load_map 失败:\n" + traceback.format_exc())
            return
        if CTX["ticks"] - CTX["load_tick"] < 6:
            return
        lvl = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).get_current_level()
        if lvl is None:
            return
        try:
            if unreal.AssetRegistryHelpers.get_asset_registry().is_loading_assets():
                return
        except Exception:
            pass
        if not CTX["loaded"] and len(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()) < 100:
            return
        CTX["loaded"] = True
        CTX["done"] = True
        run()
        CTX["quit_at"] = CTX["ticks"] + 40
    except Exception:
        warn("异常:\n" + traceback.format_exc())
        CTX["done"] = True
        CTX["quit_at"] = CTX["ticks"] + 40


def _stop():
    if CTX["handle"] is not None:
        try:
            unreal.unregister_slate_post_tick_callback(CTX["handle"])
        except Exception:
            pass
        CTX["handle"] = None


CTX["handle"] = unreal.register_slate_post_tick_callback(_tick)
log("已排队，等待编辑器就绪…")
