"""纯增量合并：只把队友场景里「新出现」的 Actor 加到你现在的图上，其余一律不动。

身份判定：以 (类, Actor 名, 变换) 逐个比对底图
    * 底图没有的         -> 新增，搬过来
    * 底图有、变换一致    -> 同一物件，跳过
    * 底图有、变换不一致  -> 队友挪过位置，只报告不动

安全闸门（全部通过才写盘）：
    * 新增数量 5..80
    * 每个新增都带静态网格，且网格在 /Game/Food、/Game/0Input/mesh、/Game/Medieval_Props_Kitchen 下
    * 无同名冲突
未通过只出报告，不保存。

用法：
    编辑器内:  py "C:/Users/38606/Documents/GitHub/Food/Tools/EditorScripts/add_new_props.py"
    命令行  :  UnrealEditor.exe Food.uproject -ExecutePythonScript=".../add_new_props.py"
"""

import os
import json
import time
import traceback
import unreal

BASE_PATH = "/Game/0Input/map/Kitchen_white_new"
SRC_PATH = "/Game/0Input/map/Kitchen_white_team_7e"
OUT_PATH = "/Game/0Input/map/Kitchen_white_new_plus_props"

DRY_RUN = False
# 只搬"道具"：食物/餐具、杂项网格(qingcai/鱼/立方体…)、欧芹这类食材道具、木箱
# 不含 modularkitchen/new_units 的新橱柜（家具，且位于 1167,3544 另一处）
ALLOW_MESH_ROOTS = (
    "/Game/Food/",
    "/Game/0Input/mesh/",
    "/Game/modularkitchen/modular-kitchen/kitchen/props/",
    "/Game/industrial_area/meshes/interior_props/",
)
MIN_NEW, MAX_NEW = 20, 70

SKIP_CLASSES = {
    "PlayerStart", "WorldSettings", "Brush", "DefaultPhysicsVolume",
    "GameModeBase", "PlayerController", "LevelScriptActor",
}

WAIT_TICKS = 1800        # 等子关卡流式加载的上限（约 30 秒）


def log(m):
    unreal.log("[add] " + str(m))


def warn(m):
    unreal.log_warning("[add] " + str(m))


def world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def eas():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def opath(a):
    try:
        return unreal.SystemLibrary.get_path_name(a)
    except Exception:
        return a.get_name()


def ckey(a):
    n = a.get_class().get_name()
    return n[:-2] if n.endswith("_C") else n


def xf(a):
    l = a.get_actor_location()
    r = a.get_actor_rotation()
    s = a.get_actor_scale3d()
    return (round(l.x, 2), round(l.y, 2), round(l.z, 2),
            round(r.pitch, 1), round(r.yaw, 1), round(r.roll, 1),
            round(s.x, 3), round(s.y, 3), round(s.z, 3))


def mesh_path(a):
    for cls, prop in ((unreal.StaticMeshComponent, "static_mesh"),
                      (unreal.SkeletalMeshComponent, "skeletal_mesh")):
        try:
            for comp in a.get_components_by_class(cls):
                m = comp.get_editor_property(prop)
                if m:
                    return m.get_path_name().split(".")[0]
        except Exception:
            continue
    return ""


def mats(a):
    """按槽位取出当前材质路径（用于迁移后复原材质覆盖）"""
    for cls in (unreal.StaticMeshComponent, unreal.SkeletalMeshComponent):
        try:
            comps = a.get_components_by_class(cls)
            if not comps:
                continue
            c = comps[0]
            out = []
            for i in range(c.get_num_materials()):
                m = c.get_material(i)
                out.append(m.get_path_name().split(".")[0] if m else "")
            return out
        except Exception:
            continue
    return []


def snapshot(actors):
    return {(ckey(a), a.get_name()): {"xf": xf(a), "label": a.get_actor_label()} for a in actors}


CTX = {"phase": 0, "ticks": 0, "handle": None, "sub": None, "base": None, "base_paths": None}


def phase_prepare():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    w = world()
    if w is None:
        warn("没有打开的世界，终止")
        return False

    base_name = BASE_PATH.split("/")[-1]
    if w.get_name() != base_name:
        log("当前关卡 %s，切到底图 %s" % (w.get_name(), base_name))
        if not les.load_level(BASE_PATH):
            warn("底图打不开，终止")
            return False
        w = world()

    base_actors = eas().get_all_level_actors()
    CTX["base"] = snapshot(base_actors)
    CTX["base_paths"] = {opath(a) for a in base_actors}
    # 持久关卡：优先用 World.PersistentLevel，取不到就取底图第一个 Actor 的 Outer
    lvl = None
    try:
        lvl = w.get_editor_property("persistent_level")
    except Exception:
        pass
    if lvl is None and base_actors:
        lvl = base_actors[0].get_outer()
    CTX["dest_level"] = lvl
    log("底图 %d 个 Actor，持久关卡=%s"
        % (len(base_actors), lvl.get_name() if lvl else "?"))

    sub = None
    for junk in (OUT_PATH, OUT_PATH + "_v2"):
        try:
            if unreal.EditorAssetLibrary.does_asset_exist(junk):
                unreal.EditorAssetLibrary.delete_asset(junk)
                log("清理上一次的失败产物: %s" % junk)
        except Exception as e:
            warn("清理失败 %s: %s" % (junk, e))

    for cls in ("LevelStreamingDynamic", "LevelStreamingKismet", "LevelStreaming"):
        try:
            sub = unreal.EditorLevelUtils.add_level_to_world(w, SRC_PATH, getattr(unreal, cls))
            log("已挂载取料图: %s (%s)" % (SRC_PATH, cls))
            break
        except Exception as e:
            warn("挂载失败(%s): %s" % (cls, e))
    if sub is None:
        return False
    CTX["sub"] = sub
    lvl = None
    try:
        lvl = sub.get_loaded_level()
    except Exception:
        pass
    CTX["sub_level"] = lvl
    return True


def sub_actors_now():
    base_paths = CTX["base_paths"]
    return [a for a in eas().get_all_level_actors() if opath(a) not in base_paths]


def drop_sub():
    lvl = CTX.get("sub_level")
    if lvl is not None:
        try:
            unreal.EditorLevelUtils.remove_level_from_world(lvl)
            return True
        except Exception as e:
            warn("按 ULevel 卸载失败: %s" % e)
    try:
        unreal.EditorLevelUtils.remove_level_from_world(CTX["sub"])
        return True
    except Exception as e:
        warn("卸载子关卡失败: %s" % e)
    return False


def phase_commit(sub_actors):
    base = CTX["base"]
    log("取料图 %d 个 Actor" % len(sub_actors))

    new_items, same, moved = [], 0, []
    for a in sub_actors:
        c = ckey(a)
        if c in SKIP_CLASSES:
            continue
        k = (c, a.get_name())
        if k not in base:
            new_items.append(a)
        elif base[k]["xf"] != xf(a):
            moved.append({"name": a.get_name(), "class": c,
                          "base_at": list(base[k]["xf"][:3]), "src_at": list(xf(a)[:3])})
        else:
            same += 1

    picked, rejected = [], []
    for a in new_items:
        mp = mesh_path(a)
        rec = {"name": a.get_name(), "label": a.get_actor_label(), "class": ckey(a),
               "mesh": mp, "at": list(xf(a)[:3])}
        (picked if mp.startswith(ALLOW_MESH_ROOTS) else rejected).append((a, rec))

    manifest = [r for _, r in picked]
    rejected_rec = [r for _, r in rejected]

    by_class, by_root = {}, {}
    for m in manifest:
        by_class[m["class"]] = by_class.get(m["class"], 0) + 1
        root = "/".join(m["mesh"].split("/")[:4]) if m["mesh"] else "(无网格)"
        by_root[root] = by_root.get(root, 0) + 1

    log("取料图新增 %d -> 搬运道具 %d，排除 %d（一致跳过 %d，同名被挪动 %d）"
        % (len(new_items), len(picked), len(rejected), same, len(moved)))
    log("搬运构成: %s" % by_root)
    for r in rejected_rec:
        log("  排除: %-16s %s @ %s" % (r["class"], r["mesh"] or "(无网格)", r["at"]))

    gates = [("道具数量在 %d..%d" % (MIN_NEW, MAX_NEW), MIN_NEW <= len(picked) <= MAX_NEW),
             ("无同名冲突", len(picked) == len({r["name"] for r in manifest}))]

    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "LevelDumps")
    os.makedirs(out_dir, exist_ok=True)
    rep = os.path.join(out_dir, "add_props_%s.json" % time.strftime("%m%d_%H%M%S"))
    report = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "base": BASE_PATH, "src": SRC_PATH,
              "dry_run": DRY_RUN, "base_total": len(base), "src_total": len(sub_actors),
              "new_total": len(new_items), "picked": len(picked),
              "identical": same, "moved_same_name": moved,
              "by_mesh_root": by_root,
              "gates": [{"rule": r, "pass": p} for r, p in gates],
              "items": manifest, "rejected": rejected_rec}

    if DRY_RUN or not all(p for _, p in gates):
        with open(rep, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)
        for r, p in gates:
            log("  闸门 %-24s %s" % (r, "通过" if p else "未通过"))
        drop_sub()
        log("未写盘。报告: %s" % rep)
        return

    picked_actors = [a for a, _ in picked]
    if not picked_actors:
        warn("没有可搬运的道具，终止")
        return

    # 1) 先抄下每个道具的数据：网格、材质槽、变换、标签、Mobility
    recs = []
    for a in picked_actors:
        mob = None
        try:
            rc = a.get_root_component()
            if rc:
                mob = rc.get_editor_property("mobility")
        except Exception:
            pass
        recs.append({"mesh": mesh_path(a), "mats": mats(a), "label": a.get_actor_label(),
                     "loc": a.get_actor_location(), "rot": a.get_actor_rotation(),
                     "scl": a.get_actor_scale3d(), "mob": mob,
                     "skeletal": ckey(a) == "SkeletalMeshActor"})
    log("已记录 %d 个道具（含材质槽）" % len(recs))

    # 2) 卸掉子关卡：世界回到只有你的 658 个 Actor，当前关卡即持久关卡
    if drop_sub():
        log("子关卡已卸载，世界剩余 %d 个 Actor" % len(eas().get_all_level_actors()))

    # 3) 逐个生成到持久关卡（此时当前关卡一定是持久关卡）
    ok_cnt, fails = 0, []
    for r in recs:
        try:
            asset = unreal.load_asset(r["mesh"])
            if asset is None:
                fails.append(r["label"] + ": 网格载入失败")
                continue
            if r["skeletal"]:
                actor = eas().spawn_actor_from_class(unreal.SkeletalMeshActor, r["loc"], r["rot"])
                if actor:
                    comps = actor.get_components_by_class(unreal.SkeletalMeshComponent)
                    if comps:
                        comps[0].set_editor_property("skeletal_mesh", asset)
            else:
                actor = eas().spawn_actor_from_object(asset, r["loc"], r["rot"])
            if actor is None:
                fails.append(r["label"] + ": 生成失败")
                continue
            actor.set_actor_scale3d(r["scl"])
            if r["mob"] is not None:
                try:
                    actor.get_root_component().set_editor_property("mobility", r["mob"])
                except Exception:
                    pass
            for i, mp in enumerate(r["mats"]):
                if not mp:
                    continue
                m = unreal.load_asset(mp)
                if not m:
                    continue
                for cls in (unreal.SkeletalMeshComponent, unreal.StaticMeshComponent):
                    comps = actor.get_components_by_class(cls)
                    if comps:
                        try:
                            comps[0].set_material(i, m)
                        except Exception:
                            pass
                        break
            try:
                actor.set_actor_label(r["label"])
            except Exception:
                pass
            ok_cnt += 1
        except Exception as e:
            fails.append("%s(%s)" % (r["label"], e))

    log("生成 %d / %d 个，失败 %d" % (ok_cnt, len(recs), len(fails)))
    if fails:
        warn("失败项: %s" % fails[:8])
    if ok_cnt == 0:
        warn("一个都没生成，终止（未保存）")
        return
    log("当前世界 Actor: %d（预期 %d）"
        % (len(eas().get_all_level_actors()), len(base) + ok_cnt))

    out = OUT_PATH
    if unreal.EditorAssetLibrary.does_asset_exist(out):
        unreal.EditorAssetLibrary.delete_asset(out)
        log("已删除旧产物: %s" % out)
    if unreal.EditorAssetLibrary.does_asset_exist(out):
        out = "%s_v%d" % (OUT_PATH, int(time.time()) % 1000)
    unreal.EditorLoadingAndSavingUtils.save_map(world(), out)
    log("已另存: %s" % out)

    after = eas().get_all_level_actors()
    xf_by_class = {}
    for a in after:
        xf_by_class.setdefault(ckey(a), set()).add(xf(a))
    lost = [k for k, v in base.items() if v["xf"] not in xf_by_class.get(k[0], set())]
    missing = [m for m in manifest
               if tuple(m["at"]) not in {t[:3] for t in xf_by_class.get(m["class"], set())}]

    report.update({"saved_as": out, "after_total": len(after),
                   "base_changed": lost[:20], "new_missing": missing[:20]})
    with open(rep, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)

    log("---- 校验 ----")
    log("底图原有 %d 个 -> 位姿变化 %d 个" % (len(base), len(lost)))
    log("新道具 %d 个 -> 未落位 %d 个" % (len(manifest), len(missing)))
    log("合并后 %d 个（%d + %d）" % (len(after), len(base), len(picked)))
    log("报告: %s" % rep)


def _tick(_dt):
    CTX["ticks"] += 1
    try:
        if CTX["phase"] == 0:
            if not phase_prepare():
                _stop()
                return
            CTX["phase"] = 1
            return

        acts = sub_actors_now()
        if acts or CTX["ticks"] > WAIT_TICKS:
            log("子关卡就绪: %d 个 Actor（等待 %d 帧）" % (len(acts), CTX["ticks"]))
            CTX["phase"] = 2
            _stop()
            if not acts:
                warn("子关卡始终没加载出 Actor，终止（未写盘）")
                return
            phase_commit(acts)
    except Exception:
        warn("执行异常:\n" + traceback.format_exc())
        _stop()


def _stop():
    if CTX["handle"] is not None:
        try:
            unreal.unregister_slate_post_tick_callback(CTX["handle"])
        except Exception:
            pass
        CTX["handle"] = None


def boot():
    try:
        reg = unreal.AssetRegistryHelpers.get_asset_registry()
        ready = not reg.is_loading_assets()
    except Exception:
        ready = True
    if ready and world() is not None:
        CTX["phase"] = 0
        _tick(0.0)
    if CTX["handle"] is None and CTX["phase"] < 2:
        log("等待编辑器就绪后执行…")
        CTX["handle"] = unreal.register_slate_post_tick_callback(_tick)


boot()
