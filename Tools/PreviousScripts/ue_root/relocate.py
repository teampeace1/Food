# -*- coding: utf-8 -*-
"""把出生点和测试道具挪到厨房内部（以场景里已有角色位置为锚点）。"""
import math

import unreal

LOG = r"D:\ue\relocate_log.txt"
_l = []


def log(s):
    s = str(s)
    _l.append(s)
    try:
        with open(LOG, "w", encoding="utf-8") as f:
            f.write("\n".join(_l) + "\n")
    except Exception:
        pass
    print(s)


les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level("/Game/0Input/map/Kitchen_white")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = eas.get_all_level_actors()

# ---- 锚点：场景里已有的第三人称角色
anchor = None
for a in actors:
    if "ThirdPersonCharacter" in a.get_class().get_name():
        anchor = a.get_actor_location()
        log("锚点(BP_ThirdPersonCharacter) = (%.0f, %.0f, %.0f)" % (anchor.x, anchor.y, anchor.z))
if anchor is None:
    anchor = unreal.Vector(1400, 400, 0)
    log("没找到参照角色，用场景中心 (1400,400)")

# ---- 占地矩形
rects = []
for a in actors:
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    try:
        org, ext = a.get_actor_bounds(False)
    except Exception:
        continue
    if ext.x * ext.y < 100 or ext.x > 1500 or ext.y > 1500:
        continue
    rects.append((org.x - ext.x, org.x + ext.x, org.y - ext.y, org.y + ext.y, a.get_actor_label()))
log("占地矩形 %d 个" % len(rects))


def clearance(x, y):
    best = 1e9
    for (x0, x1, y0, y1, _l2) in rects:
        dx = max(x0 - x, 0.0, x - x1)
        dy = max(y0 - y, 0.0, y - y1)
        best = min(best, math.hypot(dx, dy))
    return best


# ---- 离锚点最近、且净空 >= 55cm 的点
best, best_d = None, 1e9
for pad in (55, 45, 35, 25):
    x = anchor.x - 700
    while x <= anchor.x + 700:
        y = anchor.y - 700
        while y <= anchor.y + 700:
            if clearance(x, y) >= pad:
                d = math.hypot(x - anchor.x, y - anchor.y)
                if d < best_d:
                    best_d, best = d, (x, y)
            y += 10
        x += 10
    if best:
        log("用 pad=%.0f 找到点 (%.0f, %.0f)，距锚点 %.0f cm" % (pad, best[0], best[1], best_d))
        break

if best is None:
    raise RuntimeError("锚点附近找不到空地")
sx, sy = best

# ---- 清理旧的出生点与道具
for a in list(actors):
    lb = a.get_actor_label()
    if a.get_class().get_name() == "PlayerStart" or lb.startswith("TestProp"):
        eas.destroy_actor(a)
log("已清理旧的 PlayerStart / TestProp")

yaw = math.degrees(math.atan2(anchor.y - sy, anchor.x - sx))
ps = eas.spawn_actor_from_class(
    unreal.PlayerStart, unreal.Vector(sx, sy, 110.0),
    unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw))
ps.set_actor_label("PlayerStart")
log("PlayerStart @ (%.0f, %.0f, 110) yaw %.0f" % (sx, sy, yaw))

# ---- 正前方 110~160cm 摆三个方块
cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
fwd = unreal.Vector(math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), 0.0)
right = unreal.Vector(-fwd.y, fwd.x, 0.0)
placed = 0
for i, (dd, side) in enumerate([(140, 0), (190, -70), (190, 70)]):
    px = sx + fwd.x * dd + right.x * side
    py = sy + fwd.y * dd + right.y * side
    c = clearance(px, py)
    if c < 18:
        # 换个方向再试
        px = sx - fwd.x * dd + right.x * side
        py = sy - fwd.y * dd + right.y * side
        c = clearance(px, py)
        if c < 18:
            log("  TestProp_%02d 无空位，跳过" % (i + 1))
            continue
    a = eas.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(px, py, 12.0), unreal.Rotator())
    a.set_actor_label("TestProp_%02d" % (i + 1))
    comp = a.static_mesh_component
    comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    comp.set_static_mesh(cube)
    a.set_actor_scale3d(unreal.Vector(0.22, 0.22, 0.22))
    a.set_actor_location(unreal.Vector(px, py, 12.0), False, False)
    comp.set_simulate_physics(True)
    try:
        comp.set_mass_override_in_kg("", 1.5, True)
    except Exception as e:
        log("  质量设置失败: %s" % e)
    placed += 1
    log("  TestProp_%02d @ (%.0f, %.0f) z=12 净空 %.0f" % (i + 1, px, py, c))

log("save -> %s" % les.save_current_level())
log("完成：props=%d" % placed)
