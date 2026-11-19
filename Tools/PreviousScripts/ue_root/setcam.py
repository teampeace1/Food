# -*- coding: utf-8 -*-
"""启动后等关卡稳定，把视口相机摆到能看清整个后厨的机位（越过前墙俯视）。"""
import unreal

_state = {"ticks": 0, "handle": None, "done": False}

# 机位：房间正前方 6.5m、高 8.5m，看向后方台面，俯角约 -38°
LOC = unreal.Vector(600.0, 90.0, 168.0)
ROT = unreal.Rotator(roll=0.0, pitch=-6.0, yaw=90.0)


def setcam():
    ok = False
    try:
        les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        les.set_level_viewport_camera_info(LOC, ROT)
        ok = True
        print("=== CAMERA SET via LevelEditorSubsystem ===")
    except Exception as e:
        print("LevelEditorSubsystem failed: %s" % e)
    if not ok:
        try:
            unreal.EditorLevelLibrary.set_level_viewport_camera_info(LOC, ROT)
            print("=== CAMERA SET via EditorLevelLibrary ===")
        except Exception as e:
            print("EditorLevelLibrary failed: %s" % e)


def tick(dt):
    if _state["done"]:
        return
    _state["ticks"] += 1
    if _state["ticks"] < 120:
        return
    _state["done"] = True
    try:
        unreal.unregister_slate_post_tick_callback(_state["handle"])
    except Exception:
        pass
    setcam()


_state["handle"] = unreal.register_slate_post_tick_callback(tick)
print("camera script armed")
