# -*- coding: utf-8 -*-
"""启动后把编辑视口相机摆到 PlayerStart 的人眼位置，朝测试方块看。"""
import unreal

_state = {"ticks": 0, "handle": None, "done": False}

LOC = unreal.Vector(556.6, 1672.8, 175.0)
ROT = unreal.Rotator(roll=0.0, pitch=-18.0, yaw=-56.4)


def setcam():
    try:
        les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        les.set_level_viewport_camera_info(LOC, ROT)
        print("=== FOOD CAMERA SET ===")
    except Exception as e:
        print("camera failed: %s" % e)


def tick(dt):
    if _state["done"]:
        return
    _state["ticks"] += 1
    if _state["ticks"] < 150:
        return
    _state["done"] = True
    try:
        unreal.unregister_slate_post_tick_callback(_state["handle"])
    except Exception:
        pass
    setcam()


_state["handle"] = unreal.register_slate_post_tick_callback(tick)
print("food camera script armed")
