# -*- coding: utf-8 -*-
"""端到端：用 CDO 默认值给 6 个 BP_Ingredient 注入食材名，进 PIE 让子系统跑，读回实际网格。"""
import json
import os
import traceback

import unreal

NAMES = ["洋葱", "欧芹", "调料", "面团", "鱼头", "鱼"]
PREFIX = "PIETEST_"
MAP = "/Game/0Input/map/Kitchen_white_final_supply"
OUT = os.path.join(unreal.Paths.project_saved_dir(), "LevelDumps")

rep = {"cdo_set": {}, "spawned": [], "pie": {}, "errors": []}
CTX = {"tick": 0, "stage": "boot", "wait": 0, "handle": None, "made": [], "labels": {}, "cdo": None}


def log(m):
    unreal.log("[e2e] " + str(m))


def warn(m):
    unreal.log_warning("[e2e] " + str(m))


def mesh_name(actor):
    try:
        c = actor.get_editor_property("static_mesh_component")
        m = c.get_editor_property("static_mesh")
        return m.get_path_name().split("/")[-1] if m else "None"
    except Exception as e:
        return "ERR:" + str(e)[:40]


def scale_of(actor):
    try:
        s = actor.get_editor_property("static_mesh_component").get_editor_property("relative_scale3d")
        return [round(s.x, 3), round(s.y, 3), round(s.z, 3)]
    except Exception:
        return None


def write_report(tag):
    fp = os.path.join(OUT, "e2e_ingredient_%s.json" % tag)
    try:
        json.dump(rep, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
        log("报告: %s" % fp)
    except Exception:
        warn("报告失败: %s" % traceback.format_exc()[-150:])


def boot():
    bp = unreal.EditorAssetLibrary.load_asset("/Game/FoodGameplay/BP_Ingredient")
    cls = bp.generated_class()
    cdo = unreal.get_default_object(cls)
    CTX["cdo"] = cdo
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    for i, n in enumerate(NAMES):
        try:
            cdo.set_editor_property("IngredientName", n)
            rep["cdo_set"][n] = "ok"
        except Exception:
            rep["cdo_set"][n] = "FAIL:" + traceback.format_exc()[-90:]
            warn("CDO 写 %s 失败" % n)
            continue
        a = eas.spawn_actor_from_class(cls, unreal.Vector(0.0, i * 120.0, 80.0), unreal.Rotator(0, 0, 0))
        if a is None:
            warn("生成 %s 失败" % n)
            continue
        a.set_actor_label(PREFIX + n)
        CTX["made"].append(a)
        CTX["labels"][PREFIX + n] = n
        rep["spawned"].append({"name": n, "label": a.get_actor_label(),
                               "name_now": str(a.get_editor_property("IngredientName")),
                               "mesh": mesh_name(a)})
        log("生成 %-4s 名字=%-4s 网格(改前)=%s" %
            (n, a.get_editor_property("IngredientName"), mesh_name(a)))

    try:
        cdo.set_editor_property("IngredientName", "")
    except Exception:
        pass
    return len(CTX["made"]) > 0


def read_pie(world):
    rows = []
    try:
        actors = unreal.GameplayStatics.get_all_actors_of_class(world, CTX["cdo"].get_class())
    except Exception:
        warn("枚举失败: %s" % traceback.format_exc()[-150:])
        actors = []
    for a in actors:
        lab = a.get_actor_label()
        if not lab.startswith(PREFIX):
            continue
        try:
            o, e = a.get_actor_bounds(False)
            size = [round(e.x * 2, 1), round(e.y * 2, 1), round(e.z * 2, 1)]
        except Exception:
            size = None
        rows.append({"name": CTX["labels"].get(lab, lab), "mesh": mesh_name(a),
                     "scale": scale_of(a), "size_cm": size,
                     "is_cube": "Cube" in mesh_name(a)})
        log("%-4s 网格=%-26s scale=%s 尺寸=%s" % (rows[-1]["name"], rows[-1]["mesh"], rows[-1]["scale"], size))
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
    CTX["made"] = []
    try:
        CTX["cdo"].set_editor_property("IngredientName", "")
    except Exception:
        pass
    log("已清理测试 Actor 并复位 CDO（未保存任何资产）")


def _tick(_dt):
    CTX["tick"] += 1
    CTX["wait"] += 1
    try:
        if CTX["stage"] == "boot":
            CTX["stage"] = "start_pie" if boot() else "finish"
            CTX["wait"] = 0
            if CTX["stage"] == "finish":
                warn("CDO 注入全部失败，跳过 PIE")
        elif CTX["stage"] == "start_pie":
            try:
                started = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_play_simulate()
            except Exception:
                warn("editor_play_simulate 不可用: %s" % traceback.format_exc()[-200:])
                started = False
            log("PIE Simulate: %s" % started)
            CTX["stage"] = "wait_world"
            CTX["wait"] = 0
        elif CTX["stage"] == "wait_world":
            w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
            if w is not None:
                log("PIE 世界就绪（tick %d）" % CTX["tick"])
                CTX["stage"] = "settle"
                CTX["wait"] = 0
            elif CTX["wait"] % 300 == 0:
                log("等待 PIE 世界… tick=%d wait=%d" % (CTX["tick"], CTX["wait"]))
            if CTX["wait"] > 1800:
                warn("等待 PIE 超时")
                CTX["stage"] = "finish"
        elif CTX["stage"] == "settle":
            if CTX["wait"] >= 45:
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
            if CTX["wait"] > 30:
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
    ok = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    w0 = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    log("load_map=%s 当前世界=%s" % (ok, w0.get_name() if w0 else None))
    CTX["handle"] = unreal.register_slate_post_tick_callback(_tick)
    log("已排队")
except Exception:
    warn("启动异常:\n" + traceback.format_exc())
    write_report("boot_fail")
