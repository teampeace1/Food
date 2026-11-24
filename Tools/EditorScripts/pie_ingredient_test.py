# -*- coding: utf-8 -*-
"""运行时验证：在编辑器世界生成 6 个 BP_Ingredient（带 IngredientName），进 PIE 让子系统跑起来，读回网格与尺寸。"""
import json
import os
import traceback

import unreal

NAMES = ["洋葱", "欧芹", "调料", "面团", "鱼头", "鱼"]
MAP = "/Game/0Input/map/Kitchen_white_final_supply"
OUT = os.path.join(unreal.Paths.project_saved_dir(), "LevelDumps")
PREFIX = "PIETEST_"
CLS = None

rep = {"probe": {}, "spawned": [], "pie": {}, "errors": []}
CTX = {"tick": 0, "stage": "boot", "wait": 0, "handle": None, "made": [], "labels": {}}


def log(m):
    unreal.log("[pie] " + str(m))


def warn(m):
    unreal.log_warning("[pie] " + str(m))


def mesh_path(actor):
    try:
        c = actor.get_static_mesh_component()
        if c is None:
            return "NO_COMPONENT"
        m = c.get_editor_property("static_mesh")
        return m.get_path_name() if m else "None"
    except Exception:
        return "ERR"


def comp_scale(actor):
    try:
        s = actor.get_static_mesh_component().get_editor_property("relative_scale3d")
        return [round(s.x, 3), round(s.y, 3), round(s.z, 3)]
    except Exception:
        return None


def write_report(tag):
    fp = os.path.join(OUT, "pie_ingredient_%s.json" % tag)
    try:
        json.dump(rep, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
        log("报告: %s" % fp)
    except Exception:
        warn("报告失败: %s" % traceback.format_exc()[-200:])


def boot_prepare():
    bp = unreal.EditorAssetLibrary.load_asset("/Game/FoodGameplay/BP_Ingredient")
    if bp is None:
        warn("蓝图载入失败")
        return False
    global CLS
    cls = bp.generated_class()
    CLS = cls
    rep["probe"]["class"] = cls.get_name()
    rep["probe"]["has_subsystem_class"] = hasattr(unreal, "FoodIngredientVisualSubsystem")
    log("蓝图类=%s 子系统类可见=%s" % (cls.get_name(), rep["probe"]["has_subsystem_class"]))

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for i, name in enumerate(NAMES):
        loc = unreal.Vector(0.0, i * 90.0, 60.0)
        a = eas.spawn_actor_from_class(cls, loc, unreal.Rotator(0, 0, 0))
        if a is None:
            warn("生成 %s 失败" % name)
            continue
        a.set_actor_label(PREFIX + name)
        try:
            a.set_editor_property("IngredientName", name)
        except Exception:
            warn("设名字失败 %s: %s" % (name, traceback.format_exc()[-160:]))
        row = {"name": name, "label": a.get_actor_label(),
               "is_static_mesh_actor": isinstance(a, unreal.StaticMeshActor),
               "mesh_before": mesh_path(a),
               "name_set": str(a.get_editor_property("IngredientName")),
               "smc_name": (a.get_static_mesh_component().get_name()
                            if a.get_static_mesh_component() else None)}
        rep["spawned"].append(row)
        CTX["made"].append(a)
        CTX["labels"][PREFIX + name] = name
        log("生成 %-4s label=%s 网格(改前)=%s 名字=%s" %
            (name, row["label"], (row["mesh_before"] or "").split("/")[-1], row["name_set"]))
    return len(CTX["made"]) > 0


def read_pie(world):
    rows = []
    try:
        actors = unreal.GameplayStatics.get_all_actors_of_class(world, CLS)
    except Exception:
        warn("枚举 PIE Actor 失败: %s" % traceback.format_exc()[-160:])
        actors = []
    for a in actors:
        lab = a.get_actor_label()
        if not lab.startswith(PREFIX):
            continue
        name = CTX["labels"].get(lab, lab)
        mp = mesh_path(a)
        try:
            o, e = a.get_actor_bounds(False)
            size = [round(e.x * 2, 1), round(e.y * 2, 1), round(e.z * 2, 1)]
        except Exception:
            size = None
        row = {"name": name, "mesh": (mp or "").split("/")[-1],
               "is_cube": "BasicShapes/Cube" in (mp or ""),
               "scale": comp_scale(a), "size_cm": size}
        for var in ["MeshRaw", "MeshWashed", "MeshCut", "MeshPieBase"]:
            try:
                v = a.get_editor_property(var)
                row[var] = v.get_path_name().split("/")[-1] if v else None
            except Exception:
                row[var] = "MISSING"
        rows.append(row)
        log("%-4s 网格=%-24s scale=%s 尺寸=%s Raw=%s" %
            (name, row["mesh"], row["scale"], size, row["MeshRaw"]))
    rep["pie"]["rows"] = rows
    rep["pie"]["found"] = len(rows)


def cleanup():
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in CTX["made"]:
        try:
            if unreal.SystemLibrary.is_valid(a):
                eas.destroy_actor(a)
        except Exception:
            pass
    log("已清理测试 Actor（未保存）")


def _tick(_dt):
    CTX["tick"] += 1
    CTX["wait"] += 1
    try:
        if CTX["stage"] == "boot":
            ok = boot_prepare()
            CTX["stage"] = "start_pie" if ok else "finish"
            CTX["wait"] = 0
        elif CTX["stage"] == "start_pie":
            try:
                started = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_play_simulate()
            except Exception:
                warn("editor_play_simulate 不可用: %s" % traceback.format_exc()[-200:])
                started = False
            log("启动 PIE Simulate: %s" % started)
            CTX["stage"] = "wait_world"
            CTX["wait"] = 0
        elif CTX["stage"] == "wait_world":
            w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
            if w is not None:
                log("PIE 世界就绪（tick %d）" % CTX["tick"])
                CTX["stage"] = "settle"
                CTX["wait"] = 0
            elif CTX["wait"] > 1500:
                warn("等待 PIE 世界超时")
                CTX["stage"] = "finish"
        elif CTX["stage"] == "settle":
            if CTX["wait"] >= 40:
                w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
                if w is not None:
                    read_pie(w)
                CTX["stage"] = "finish"
        elif CTX["stage"] == "finish":
            try:
                unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
            except Exception:
                pass
            write_report("%d" % CTX["tick"])
            cleanup()
            CTX["stage"] = "done"
            CTX["wait"] = 0
        elif CTX["stage"] == "done":
            if CTX["wait"] > 25:
                if CTX["handle"] is not None:
                    try:
                        unreal.unregister_slate_post_tick_callback(CTX["handle"])
                    except Exception:
                        pass
                log("结束，关闭编辑器")
                unreal.SystemLibrary.quit_editor()
    except Exception:
        warn("tick 异常(%s):\n%s" % (CTX["stage"], traceback.format_exc()))
        CTX["stage"] = "finish"


try:
    if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
        warn("地图加载失败")
    CTX["handle"] = unreal.register_slate_post_tick_callback(_tick)
    log("已排队，等待编辑器就绪")
except Exception:
    warn("启动异常:\n" + traceback.format_exc())
    write_report("boot_fail")
