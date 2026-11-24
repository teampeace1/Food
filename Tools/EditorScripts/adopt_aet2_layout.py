"""按 AET2 场景对齐位姿：把队友摆好的每一个物件位置/旋转/缩放套到你的图上。

做法（不改任何蓝图、不重建任何 Actor）：
    底图 = Kitchen_white_new_props（你的 658 个 + 已加的 49 个道具）
    取料 = Kitchen_white_team_7e（AET2 的 681 个 Actor）
    * 同名同类的 Actor        -> 直接 set_actor_transform 成 AET2 的位姿
    * AET2 独有的 new_units 橱柜 -> 抄网格/材质/位姿补进来
    * 你独有的玩法 Actor        -> 完全不碰，留在原位

安全闸门（全部通过才写盘）：
    * 位姿变更数 20..80
    * 单件位移 <= 3000 cm
    * 补件数 <= 20
    * 保存后回读：变更件位姿 == AET2 值，原有 Actor 总数不减

用法：
    编辑器内: py "C:/Users/38606/Documents/GitHub/Food/Tools/EditorScripts/adopt_aet2_layout.py"
    命令行  : UnrealEditor.exe Food.uproject -ExecutePythonScript=".../adopt_aet2_layout.py"
"""

import os
import json
import math
import time
import traceback
import unreal

BASE_PATH = "/Game/0Input/map/Kitchen_white_new_props"
SRC_PATH = "/Game/0Input/map/Kitchen_white_team_7e"
OUT_PATH = "/Game/0Input/map/Kitchen_white_aet2scene"

DRY_RUN = False
AUTO_QUIT = True          # 命令行跑完后自动关编辑器

# 这些类不参与位姿对齐（玩法/系统物件，位置由你自己定）
SKIP_CLASSES = {
    "PlayerStart", "WorldSettings", "Brush", "DefaultPhysicsVolume",
    "GameModeBase", "PlayerController", "LevelScriptActor",
}
# 类名前缀命中也不动（你的玩法蓝图）
SKIP_CLASS_PREFIX = ("BP_Sink", "BP_ChoppingBoard", "BP_Workstation", "BP_Ingredient",
                     "BP_FillingBowl", "BP_RollingStation", "BP_Oven", "BP_Pie",
                     "BP_Tray", "BP_Recipe", "BP_Player", "BP_FirstPerson")

MAX_SHIFT_CM = 3000.0
MIN_MOVED, MAX_MOVED = 20, 80
MAX_ADD = 20
WAIT_TICKS = 1800

CTX = {"phase": 0, "ticks": 0, "handle": None, "sub": None, "sub_level": None,
       "base": {}, "base_paths": set(), "src": {}, "quit_at": None}


def schedule_quit():
    if AUTO_QUIT:
        CTX["quit_at"] = CTX["ticks"] + 60


def log(m):
    unreal.log("[adopt] " + str(m))


def warn(m):
    unreal.log_warning("[adopt] " + str(m))


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


def skipped(cls):
    if cls in SKIP_CLASSES:
        return True
    return any(cls.startswith(p) for p in SKIP_CLASS_PREFIX)


def xf(a):
    l = a.get_actor_location()
    r = a.get_actor_rotation()
    s = a.get_actor_scale3d()
    return (round(l.x, 2), round(l.y, 2), round(l.z, 2),
            round(r.pitch, 2), round(r.yaw, 2), round(r.roll, 2),
            round(s.x, 4), round(s.y, 4), round(s.z, 4))


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
    for cls in (unreal.StaticMeshComponent, unreal.SkeletalMeshComponent):
        try:
            comps = a.get_components_by_class(cls)
            if not comps:
                continue
            c = comps[0]
            return [(c.get_material(i).get_path_name().split(".")[0] if c.get_material(i) else "")
                    for i in range(c.get_num_materials())]
        except Exception:
            continue
    return []


def snap(actors):
    return {(ckey(a), a.get_name()): {"xf": xf(a), "label": a.get_actor_label(),
                                      "mesh": mesh_path(a), "path": opath(a)}
            for a in actors}


def shift(b, s):
    return math.sqrt(sum((s[i] - b[i]) ** 2 for i in range(3)))


def phase_prepare():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    w = world()
    if w is None:
        warn("没有打开的世界")
        return False

    base_name = BASE_PATH.split("/")[-1]
    if w.get_name() != base_name:
        log("切到 底图 %s（当前 %s）" % (base_name, w.get_name()))
        if not les.load_level(BASE_PATH):
            warn("底图打不开")
            return False
        w = world()

    base_actors = eas().get_all_level_actors()
    CTX["base"] = snap(base_actors)
    CTX["base_paths"] = {opath(a) for a in base_actors}
    log("底图 %d 个 Actor" % len(base_actors))

    sub = None
    for cls in ("LevelStreamingDynamic", "LevelStreamingKismet", "LevelStreaming"):
        try:
            sub = unreal.EditorLevelUtils.add_level_to_world(w, SRC_PATH, getattr(unreal, cls))
            log("已挂载取料图 (%s)" % cls)
            break
        except Exception as e:
            warn("挂载失败(%s): %s" % (cls, e))
    if sub is None:
        return False
    CTX["sub"] = sub
    try:
        CTX["sub_level"] = sub.get_loaded_level()
    except Exception:
        pass
    return True


def sub_actors_now():
    bp = CTX["base_paths"]
    return [a for a in eas().get_all_level_actors() if opath(a) not in bp]


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


def build_transform(t):
    loc = unreal.Vector(t[0], t[1], t[2])
    rot = unreal.Rotator(roll=t[5], pitch=t[3], yaw=t[4])
    scl = unreal.Vector(t[6], t[7], t[8])
    return unreal.Transform(location=loc, rotation=rot, scale=scl)


def phase_commit(src_actors):
    base = CTX["base"]
    log("取料图 %d 个 Actor" % len(src_actors))

    moved, add_items, same, collisions, dup_skip = [], [], 0, [], 0

    # 底图已有物件的 (类, 网格) -> 位置表，用于判重（上一轮复制的新道具名字可能不同但位置已在）
    base_index = {}
    for k, v in base.items():
        if v["mesh"]:
            base_index.setdefault((k[0], v["mesh"]), []).append(v["xf"][:3])

    def already_present(c, mp, loc):
        if not mp:
            return False
        for pl in base_index.get((c, mp), ()):
            if shift(pl, loc) < 2.0:
                return True
        return False

    for a in src_actors:
        c = ckey(a)
        if skipped(c):
            continue
        k = (c, a.get_name())
        t = xf(a)
        mp = mesh_path(a)
        bm = base.get(k)

        # 身份 = (类, 名字) 且网格一致；网格不同说明只是自动编号撞名，不是同一物件
        # 蓝图 Actor 不做网格校验：同一蓝图实例换网格属于改动本身，不是撞名
        is_mesh_actor = c in ("StaticMeshActor", "SkeletalMeshActor")
        same_thing = bm is not None and (
            (not is_mesh_actor) or (not mp or not bm["mesh"] or bm["mesh"] == mp))

        if bm is None:
            if already_present(c, mp, t[:3]):
                dup_skip += 1
                continue
            add_items.append((a, {"name": a.get_name(), "label": a.get_actor_label(),
                                  "class": c, "mesh": mp, "at": list(t[:3]),
                                  "xf": t, "mats": mats(a)}))
        elif not same_thing:
            collisions.append({"name": k[1], "class": c, "src_mesh": mp,
                               "base_mesh": bm["mesh"], "at": list(t[:3])})
        elif bm["xf"] != t:
            d = shift(bm["xf"], t)
            moved.append((bm["path"], k, t, d))
        else:
            same += 1

    log("同名位姿差异 %d，AET2 独有待补 %d，完全一致 %d，编号撞名跳过 %d，已在位跳过 %d"
        % (len(moved), len(add_items), same, len(collisions), dup_skip))

    # ---- 闸门 ----
    max_d = max([m[3] for m in moved], default=0.0)
    gates = [
        ("位姿变更数 %d..%d" % (MIN_MOVED, MAX_MOVED), MIN_MOVED <= len(moved) <= MAX_MOVED),
        ("单件最大位移 %.0fcm <= %d" % (max_d, MAX_SHIFT_CM), max_d <= MAX_SHIFT_CM),
        ("补件数 %d <= %d" % (len(add_items), MAX_ADD), len(add_items) <= MAX_ADD),
    ]
    for r, p in gates:
        log("  闸门 %-34s %s" % (r, "通过" if p else "未通过"))

    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "LevelDumps")
    os.makedirs(out_dir, exist_ok=True)
    rep = os.path.join(out_dir, "adopt_%s.json" % time.strftime("%m%d_%H%M%S"))
    report = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "base": BASE_PATH, "src": SRC_PATH, "dry_run": DRY_RUN,
        "base_total": len(base), "src_total": len(src_actors),
        "moved_count": len(moved), "max_shift_cm": round(max_d, 1),
        "identical": same,
        "gates": [{"rule": r, "pass": p} for r, p in gates],
        "moved": [{"name": k[1], "class": k[0], "from": list(base[k]["xf"][:3]),
                   "to": list(t[:3]), "shift_cm": round(d, 1),
                   "mesh": base[k]["mesh"]} for _, k, t, d in moved],
        "collisions": collisions,
        "added": [r for _, r in add_items],
    }

    if DRY_RUN or not all(p for _, p in gates):
        with open(rep, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)
        drop_sub()
        log("未写盘，报告: %s" % rep)
        schedule_quit()
        return

    # ---- 1) 套位姿（此时子关卡还挂着，按底图本体的路径定位后改世界变换） ----
    ok, fail = 0, []
    by_path = {opath(x): x for x in eas().get_all_level_actors()}
    for p, k, t, d in moved:
        target = by_path.get(p)
        if target is None:
            fail.append("%s: 按路径找不到本体" % k[1])
            continue
        try:
            target.set_actor_transform(build_transform(t), False, True)
            ok += 1
        except Exception as e:
            fail.append("%s: %s" % (k[1], e))
    log("位姿已套 %d / %d，失败 %d" % (ok, len(moved), len(fail)))
    if fail:
        warn("失败: %s" % fail[:6])

    # ---- 2) 抄下待补件的网格数据 ----
    recs = []
    for a, r in add_items:
        mob = None
        try:
            rc = a.get_root_component()
            if rc:
                mob = rc.get_editor_property("mobility")
        except Exception:
            pass
        recs.append(dict(r, mob=mob, skeletal=(r["class"] == "SkeletalMeshActor")))

    # ---- 3) 卸子关卡，世界回到只有你的图 ----
    if drop_sub():
        log("子关卡已卸载，世界剩余 %d 个 Actor" % len(eas().get_all_level_actors()))

    # ---- 4) 生成补件 ----
    add_ok, add_fail = 0, []
    for r in recs:
        try:
            asset = unreal.load_asset(r["mesh"])
            if asset is None:
                add_fail.append(r["label"] + ": 网格载入失败")
                continue
            loc = unreal.Vector(*r["xf"][:3])
            rot = unreal.Rotator(roll=r["xf"][5], pitch=r["xf"][3], yaw=r["xf"][4])
            if r["skeletal"]:
                actor = eas().spawn_actor_from_class(unreal.SkeletalMeshActor, loc, rot)
                if actor:
                    comps = actor.get_components_by_class(unreal.SkeletalMeshComponent)
                    if comps:
                        comps[0].set_editor_property("skeletal_mesh", asset)
            else:
                actor = eas().spawn_actor_from_object(asset, loc, rot)
            if actor is None:
                add_fail.append(r["label"] + ": 生成失败")
                continue
            actor.set_actor_scale3d(unreal.Vector(*r["xf"][6:]))
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
            add_ok += 1
        except Exception as e:
            add_fail.append("%s(%s)" % (r["label"], e))
    log("补件生成 %d / %d，失败 %d" % (add_ok, len(recs), len(add_fail)))
    if add_fail:
        warn("补件失败: %s" % add_fail[:6])

    # ---- 5) 另存 ----
    out = OUT_PATH
    if unreal.EditorAssetLibrary.does_asset_exist(out):
        unreal.EditorAssetLibrary.delete_asset(out)
        log("已删除旧产物: %s" % out)
        try:
            unreal.AssetRegistryHelpers.get_asset_registry().scan_paths_synchronous(
                ["/Game/0Input/map"], True, True)
        except Exception as e:
            warn("刷新资产注册表失败: %s" % e)
    if unreal.EditorAssetLibrary.does_asset_exist(out):
        out = "%s_v%d" % (OUT_PATH, int(time.time()) % 1000)
    unreal.EditorLoadingAndSavingUtils.save_map(world(), out)
    log("已另存: %s" % out)

    # ---- 6) 回读校验 ----
    after = eas().get_all_level_actors()
    xf_by_path = {opath(a): xf(a) for a in after}
    by_key = {}
    for a in after:
        by_key[(ckey(a), a.get_name())] = xf(a)
    bad = [k[1] for p, k, t, _ in moved if xf_by_path.get(p) != t]
    lost = [k for k in base if k not in by_key]

    report.update({"saved_as": out, "after_total": len(after), "added_ok": add_ok,
                   "pose_mismatch": bad[:20], "missing_base": lost[:20]})
    with open(rep, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)

    log("---- 校验 ----")
    log("位姿未生效 %d 个" % len(bad))
    log("原有 Actor 丢失 %d 个" % len(lost))
    log("合并后总数 %d（底图 %d + 补件 %d）" % (len(after), len(base), add_ok))
    log("报告: %s" % rep)
    schedule_quit()


def _tick(_dt):
    CTX["ticks"] += 1
    try:
        if CTX["quit_at"] is not None and CTX["ticks"] >= CTX["quit_at"]:
            _stop()
            log("任务结束，自动关闭编辑器")
            try:
                unreal.SystemLibrary.quit_editor()
            except Exception as e:
                warn("退出失败: %s" % e)
            return
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
                warn("子关卡没加载出 Actor，终止（未写盘）")
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
        ready = not unreal.AssetRegistryHelpers.get_asset_registry().is_loading_assets()
    except Exception:
        ready = True
    if ready and world() is not None:
        CTX["phase"] = 0
        _tick(0.0)
    if CTX["handle"] is None and CTX["phase"] < 2:
        log("等待编辑器就绪后执行…")
        CTX["handle"] = unreal.register_slate_post_tick_callback(_tick)


boot()
