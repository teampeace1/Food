"""把 6 个供应点的引擎方块（/Engine/BasicShapes/Cube）换成名字对应的真实食材网格。

只改三样东西：StaticMesh、Actor 缩放（按模型真实尺寸）、Actor 位置（底部贴回原台面高度）。
IngredientName、蓝图逻辑、碰撞预设、旋转、标签全部保持原样。

产物另存为 Kitchen_white_final_supply，原 Kitchen_white_final 不动。
"""

import os
import json
import time
import traceback
import unreal

MAP_PATH = "/Game/0Input/map/Kitchen_white_final"
OUT_PATH = "/Game/0Input/map/Kitchen_white_final_supply"
OUT_DIR = os.path.join(unreal.Paths.project_saved_dir(), "LevelDumps")

# 顺序敏感：鱼头必须排在鱼前面
MAPPING = [
    ("欧芹", "/Game/modularkitchen/modular-kitchen/kitchen/props/parsley"),
    ("洋葱", "/Game/modularkitchen/modular-kitchen/kitchen/props/onion"),
    ("调料", "/Game/modularkitchen/modular-kitchen/kitchen/props/condiment-bottle"),
    ("面团", "/Game/modularkitchen/modular-kitchen/kitchen/props/sourdough"),
    ("鱼头", "/Game/Food/Meshes/SM_Sardine_Half_1"),
    ("鱼", "/Game/Food/Meshes/SM_Sardine"),
]

MAX_DIM_CM = 60.0      # 超过就等比缩小
MIN_DIM_CM = 5.0       # 小于就等比放大到 8cm
AUTO_QUIT = True
MIN_OK = 5             # 至少成功 5 个才写盘

CTX = {"handle": None, "ticks": 0, "done": False, "quit_at": None,
       "phase": 0, "load_tick": 0}


def log(m):
    unreal.log("[fuse] " + str(m))


def warn(m):
    unreal.log_warning("[fuse] " + str(m))


def ckey(a):
    n = a.get_class().get_name()
    return n[:-2] if n.endswith("_C") else n


def bbox_of(mesh):
    try:
        b = mesh.get_bounding_box()
        return (b.min.x, b.min.y, b.min.z), (b.max.x, b.max.y, b.max.z)
    except Exception:
        return None


def target_for(label):
    for kw, path in MAPPING:
        if kw in label:
            return kw, path
    return None, None


def run():
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = eas.get_all_level_actors()
    rep = {"ts": time.strftime("%Y%m%d_%H%M%S"), "map": MAP_PATH,
           "out": OUT_PATH, "total": len(actors), "items": [], "skipped": []}

    supplies = [a for a in actors if "IngredientSupply" in ckey(a)]
    log("供应点 %d 个" % len(supplies))

    for a in supplies:
        label = a.get_actor_label()
        kw, path = target_for(label)
        if not path:
            rep["skipped"].append({"label": label, "why": "名字没匹配到映射"})
            continue
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            rep["skipped"].append({"label": label, "why": "素材不存在: " + path})
            warn("素材不存在: %s" % path)
            continue
        comp = a.get_component_by_class(unreal.StaticMeshComponent)
        if comp is None:
            rep["skipped"].append({"label": label, "why": "没有 StaticMeshComponent"})
            continue

        try:
            ing = a.get_editor_property("ingredient_name")
        except Exception:
            ing = None

        old_mesh = comp.get_editor_property("static_mesh")
        old_path = old_mesh.get_path_name() if old_mesh else None
        old_scale = comp.get_world_scale()
        loc = comp.get_world_location()
        rot = comp.get_world_rotation()

        ob = bbox_of(old_mesh) if old_mesh else None
        if ob is None:
            old_bottom = loc.z
            old_cx, old_cy = loc.x, loc.y
        else:
            omn, omx = ob
            old_bottom = loc.z + omn[2] * old_scale.z
            old_cx = loc.x + (omn[0] + omx[0]) * 0.5 * old_scale.x
            old_cy = loc.y + (omn[1] + omx[1]) * 0.5 * old_scale.y

        new = unreal.EditorAssetLibrary.load_asset(path)
        nb = bbox_of(new)
        if nb is None:
            # 拿不到包围盒就只换网格，缩放不动
            comp.set_editor_property("static_mesh", new)
            rep["items"].append({"label": label, "kw": kw, "mesh": path,
                                 "old_mesh": old_path, "scale": None,
                                 "note": "包围盒读取失败，仅换网格"})
            continue
        nmn, nmx = nb
        size = [nmx[i] - nmn[i] for i in range(3)]
        nat = max(size) if size else 1.0
        s = 1.0
        if nat > MAX_DIM_CM:
            s = MAX_DIM_CM / nat
        elif 0 < nat < MIN_DIM_CM:
            s = 8.0 / nat

        comp.set_editor_property("static_mesh", new)
        a.set_actor_scale3d(unreal.Vector(s, s, s))
        new_loc = unreal.Vector(
            old_cx - (nmn[0] + nmx[0]) * 0.5 * s,
            old_cy - (nmn[1] + nmx[1]) * 0.5 * s,
            old_bottom - nmn[2] * s)
        a.set_actor_location(new_loc, False, False)

        rep["items"].append({
            "label": label, "kw": kw, "ingredient_name": str(ing) if ing is not None else None,
            "old_mesh": old_path, "new_mesh": path,
            "old_at": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)],
            "new_at": [round(new_loc.x, 1), round(new_loc.y, 1), round(new_loc.z, 1)],
            "old_bottom_z": round(old_bottom, 1),
            "new_bottom_z": round(old_bottom, 1),
            "rot": [round(rot.pitch, 1), round(rot.yaw, 1), round(rot.roll, 1)],
            "nat_size_cm": [round(v, 1) for v in size],
            "scale": round(s, 3),
        })
        log("%-14s %s -> %s 尺寸%s 缩放%.3f 底Z%.1f" %
            (label, (old_path or "").split("/")[-1], path.split("/")[-1],
             [round(v) for v in size], s, old_bottom))

    rep["ok_count"] = len(rep["items"])
    if rep["ok_count"] < MIN_OK:
        warn("成功数 %d < %d，放弃写盘" % (rep["ok_count"], MIN_OK))
        rep["saved"] = False
        write_rep(rep)
        return False

    # 保存
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if unreal.EditorAssetLibrary.does_asset_exist(OUT_PATH):
        unreal.EditorAssetLibrary.delete_asset(OUT_PATH)
    ok_save = unreal.EditorLoadingAndSavingUtils.save_map(w, OUT_PATH)
    rep["saved"] = bool(ok_save)
    log("另存为 %s : %s" % (OUT_PATH, ok_save))

    # 读回校验
    after = eas.get_all_level_actors()
    rep["after_total"] = len(after)
    got = {}
    for a in after:
        if "IngredientSupply" in ckey(a):
            c = a.get_component_by_class(unreal.StaticMeshComponent)
            m = c.get_editor_property("static_mesh") if c else None
            got[a.get_actor_label()] = m.get_path_name() if m else None
    rep["verify"] = got
    write_rep(rep)
    return True


def write_rep(rep):
    os.makedirs(OUT_DIR, exist_ok=True)
    fp = os.path.join(OUT_DIR, "fuse_supply_%s.json" % rep["ts"])
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    log("报告: %s" % fp)


def main():
    log("加载 %s" % MAP_PATH)
    ok = False
    try:
        ok = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    except Exception:
        warn("load_map 异常: %s" % traceback.format_exc())
    if not ok:
        try:
            ok = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP_PATH)
        except Exception:
            warn("load_level 异常: %s" % traceback.format_exc())
    if not ok:
        warn("地图加载失败，放弃")
        return
    for _ in range(150):
        try:
            if not unreal.AssetRegistryHelpers.get_asset_registry().is_loading_assets():
                break
        except Exception:
            break
        time.sleep(0.2)
    log("地图就绪，开始换网格")
    run()


try:
    main()
except Exception:
    warn("执行异常:\n" + traceback.format_exc())
finally:
    log("完成，关闭编辑器")
    try:
        unreal.SystemLibrary.quit_editor()
    except Exception:
        pass
