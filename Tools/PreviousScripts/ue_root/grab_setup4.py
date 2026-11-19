# -*- coding: utf-8 -*-
"""第四批：把出生点放到最空旷处，并在其周围环形找空位摆放测试道具。"""
import math
import traceback

import unreal

LOG = r"D:\ue\grab4_log.txt"
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


EAL = unreal.EditorAssetLibrary
LEVEL_PATH = "/Game/0Input/map/Kitchen_white"
CUBE = "/Engine/BasicShapes/Cube.Cube"

log("===== GRAB SETUP 4 =====")

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL_PATH)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = eas.get_all_level_actors()

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
log("占用矩形 %d 个" % len(rects))

xs = [r[0] for r in rects] + [r[1] for r in rects]
ys = [r[2] for r in rects] + [r[3] for r in rects]
minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
cx, cy = (minx + maxx) / 2.0, (miny + maxy) / 2.0


def clearance(x, y):
    best = 1e9
    for (x0, x1, y0, y1, _l2) in rects:
        dx = max(x0 - x, 0.0, x - x1)
        dy = max(y0 - y, 0.0, y - y1)
        best = min(best, math.hypot(dx, dy))
    return best


# ---- 找最空旷点
best, best_c = None, -1
x = minx + 40
while x <= maxx - 40:
    y = miny + 40
    while y <= maxy - 40:
        c = clearance(x, y)
        if c > best_c:
            best_c, best = c, (x, y)
        y += 20
    x += 20
sx, sy = best
log("最空旷点 (%.0f, %.0f) 净空 %.0f cm" % (sx, sy, best_c))

# ---- 放出生点
for a in list(actors):
    if a.get_class().get_name() == "PlayerStart":
        log("移除旧 PlayerStart")
        eas.destroy_actor(a)

yaw = math.degrees(math.atan2(cy - sy, cx - sx))
ps = eas.spawn_actor_from_class(
    unreal.PlayerStart, unreal.Vector(sx, sy, 110.0),
    unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw))
ps.set_actor_label("PlayerStart")
log("PlayerStart @ (%.0f, %.0f, 110) yaw %.0f" % (sx, sy, yaw))

# ---- 环形找空位放道具
cands = []
r = 110
while r <= 280:
    ang = 0
    while ang < 360:
        px = sx + r * math.cos(math.radians(ang))
        py = sy + r * math.sin(math.radians(ang))
        if clearance(px, py) >= 22:
            cands.append((r, ang, px, py))
        ang += 10
    r += 20
cands.sort(key=lambda t: (t[0], abs(((t[1] - yaw + 180) % 360) - 180)))
log("可用候选位 %d 个" % len(cands))

picked = []
for (r, ang, px, py) in cands:
    if len(picked) >= 3:
        break
    if all(math.hypot(px - q[0], py - q[1]) > 85 for q in picked):
        picked.append((px, py, r, ang))

cube = unreal.load_asset(CUBE)
for i, (px, py, r, ang) in enumerate(picked):
    a = eas.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(px, py, 50.0), unreal.Rotator())
    a.set_actor_label("TestProp_%02d" % (i + 1))
    comp = a.static_mesh_component
    comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    comp.set_static_mesh(cube)
    a.set_actor_scale3d(unreal.Vector(0.22, 0.22, 0.22))
    a.set_actor_location(unreal.Vector(px, py, 50.0), False, False)
    comp.set_simulate_physics(True)
    try:
        comp.set_mass_override_in_kg(1.5)
    except Exception as e:
        log("  mass override 失败: %s" % e)
    log("  TestProp_%02d @ (%.0f, %.0f)  距出生点 %.0f cm 方向 %.0f°"
        % (i + 1, px, py, r, ang))

log("save_current_level -> %s" % les.save_current_level())
log("===== DONE =====")
