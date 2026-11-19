# -*- coding: utf-8 -*-
"""让 PlayerStart 面朝三个测试方块。"""
import math

import unreal

LOG = r"D:\ue\face_log.txt"
_l = []


def log(s):
    s = str(s)
    _l.append(s)
    with open(LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(_l) + "\n")
    print(s)


les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level("/Game/0Input/map/Kitchen_white")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

ps = None
props = []
for a in eas.get_all_level_actors():
    lb = a.get_actor_label()
    if a.get_class().get_name() == "PlayerStart":
        ps = a
    elif lb.startswith("TestProp"):
        props.append(a.get_actor_location())

if ps is None or not props:
    log("缺少 PlayerStart 或道具")
else:
    pl = ps.get_actor_location()
    cx = sum(p.x for p in props) / len(props)
    cy = sum(p.y for p in props) / len(props)
    yaw = math.degrees(math.atan2(cy - pl.y, cx - pl.x))
    ps.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw), False)
    log("PlayerStart (%.0f, %.0f) 改为朝向道具 (%.0f, %.0f)，yaw=%.1f"
        % (pl.x, pl.y, cx, cy, yaw))
    log("save -> %s" % les.save_current_level())
