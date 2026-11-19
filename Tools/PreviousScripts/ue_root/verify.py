# -*- coding: utf-8 -*-
"""核对关卡里的出生点、测试道具、以及周边净空。"""
import math

import unreal

LOG = r"D:\ue\verify_log.txt"
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

log("===== VERIFY =====")
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
log("load_level -> %s" % les.load_level(LEVEL_PATH))
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = eas.get_all_level_actors()

ps = None
props = []
others = []
for a in actors:
    cn = a.get_class().get_name()
    lb = a.get_actor_label()
    loc = a.get_actor_location()
    if cn == "PlayerStart":
        ps = a
    elif lb.startswith("TestProp"):
        props.append((lb, loc, a))
    elif cn == "StaticMeshActor" or "Character" in cn:
        others.append((cn, lb, loc))

log("\nPlayerStart: %r" % (ps.get_actor_location() if ps else None))
if ps:
    r = ps.get_actor_rotation()
    log("  yaw = %.1f" % r.yaw)

for lb, loc, a in props:
    org, ext = a.get_actor_bounds(False)
    try:
        sim = a.static_mesh_component.get_editor_property("simulate_physics")
    except Exception:
        sim = "?"
    log("\n%s: loc=(%.0f, %.0f, %.0f) 尺寸=(%.0f,%.0f,%.0f) simulate_physics=%s"
        % (lb, loc.x, loc.y, loc.z, ext.x * 2, ext.y * 2, ext.z * 2, sim))
    if ps:
        d = math.hypot(loc.x - ps.get_actor_location().x, loc.y - ps.get_actor_location().y)
        log("  距出生点 %.0f cm" % d)

# 出生点净空核对（只算带体积的静态网格）
rects = []
for cn, lb, loc in others:
    pass
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

if ps:
    ploc = ps.get_actor_location()
    near = []
    for (x0, x1, y0, y1, lb) in rects:
        dx = max(x0 - ploc.x, 0.0, ploc.x - x1)
        dy = max(y0 - ploc.y, 0.0, ploc.y - y1)
        d = math.hypot(dx, dy)
        if d < 400:
            near.append((round(d), lb))
    near.sort()
    log("\n出生点 400cm 内的物体（最近 8 个）:")
    for d, lb in near[:8]:
        log("    %4d cm   %s" % (d, lb))

log("\nBP_ThirdPersonCharacter 之类的角色:")
for cn, lb, loc in others:
    if "Character" in cn:
        log("    %-30s %-26s (%.0f, %.0f, %.0f)" % (cn, lb, loc.x, loc.y, loc.z))

log("===== DONE =====")
