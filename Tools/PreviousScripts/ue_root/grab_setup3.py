# -*- coding: utf-8 -*-
"""第三批：修正出生点选点（剔除大地面），删除错误存档里的出生点，摆道具。"""
import math
import traceback

import unreal

LOG = r"D:\ue\grab3_log.txt"
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


def step(name, fn):
    try:
        r = fn()
        log("[OK]   %-24s -> %r" % (name, r))
        return r
    except Exception as e:
        log("[FAIL] %-24s -> %s" % (name, e))
        log(traceback.format_exc())
        return None


EAL = unreal.EditorAssetLibrary
LEVEL_PATH = "/Game/0Input/map/Kitchen_white"
CUBE = "/Engine/BasicShapes/Cube.Cube"
CH_PATH = "/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter"

log("===== GRAB SETUP 3 =====")


def fix_level():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(LEVEL_PATH)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = eas.get_all_level_actors()

    # ---- 收集物体占地矩形，剔除大地面
    rects = []
    skipped = []
    for a in actors:
        if a.get_class().get_name() != "StaticMeshActor":
            continue
        try:
            org, ext = a.get_actor_bounds(False)
        except Exception:
            continue
        if ext.x * ext.y < 100:
            continue
        if ext.x > 1500 or ext.y > 1500:
            skipped.append((a.get_actor_label(), round(ext.x), round(ext.y)))
            continue
        rects.append((org.x - ext.x, org.x + ext.x,
                      org.y - ext.y, org.y + ext.y, a.get_actor_label()))
    log("占用矩形 %d 个，剔除大地面 %s" % (len(rects), skipped))

    xs = [r[0] for r in rects] + [r[1] for r in rects]
    ys = [r[2] for r in rects] + [r[3] for r in rects]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    log("房间 XY 范围: x %.0f ~ %.0f   y %.0f ~ %.0f" % (minx, maxx, miny, maxy))
    cx, cy = (minx + maxx) / 2.0, (miny + maxy) / 2.0

    def blocked(x, y, pad):
        for (x0, x1, y0, y1, _l2) in rects:
            if x0 - pad <= x <= x1 + pad and y0 - pad <= y <= y1 + pad:
                return True
        return False

    # ---- 在房间内找最靠近中心、且带 70cm 净空的点
    best, best_d = None, 1e9
    pad = 70
    while pad >= 30 and best is None:
        x = minx + 50
        while x <= maxx - 50:
            y = miny + 50
            while y <= maxy - 50:
                if not blocked(x, y, pad):
                    d = math.hypot(x - cx, y - cy)
                    if d < best_d:
                        best_d, best = d, (x, y)
                y += 25
            x += 25
        if best is None:
            log("pad=%.0f 无可用点，放宽" % pad)
            pad -= 20
    if best is None:
        raise RuntimeError("找不到可站立的位置")
    sx, sy = best
    log("选定出生点 (%.0f, %.0f)，距中心 %.0f cm，净空 pad=%d" % (sx, sy, best_d, pad))

    # ---- 清掉之前放错位置的 PlayerStart
    for a in actors:
        if a.get_class().get_name() == "PlayerStart":
            loc = a.get_actor_location()
            far = not (minx - 200 <= loc.x <= maxx + 200 and miny - 200 <= loc.y <= maxy + 200)
            if far:
                log("删除错位 PlayerStart @ (%.0f, %.0f)" % (loc.x, loc.y))
                eas.destroy_actor(a)

    actors = eas.get_all_level_actors()
    ps = None
    for a in actors:
        if a.get_class().get_name() == "PlayerStart":
            ps = a
            break

    yaw = math.degrees(math.atan2(cy - sy, cx - sx))
    loc = unreal.Vector(sx, sy, 110.0)
    rot = unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw)
    if ps is None:
        ps = eas.spawn_actor_from_class(unreal.PlayerStart, loc, rot)
        ps.set_actor_label("PlayerStart")
        log("新建 PlayerStart @ (%.0f, %.0f, 110) yaw %.0f" % (sx, sy, yaw))
    else:
        ps.set_actor_location(loc, False, False)
        ps.set_actor_rotation(rot, False)
        log("复用已有 PlayerStart，移到 (%.0f, %.0f)" % (sx, sy))

    # ---- 出生点前方摆三个可抓取方块
    cube = unreal.load_asset(CUBE)
    fwd = unreal.Vector(math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), 0.0)
    right = unreal.Vector(-fwd.y, fwd.x, 0.0)
    made = 0
    for i, (dd, side) in enumerate([(170, 0), (230, -75), (230, 75)]):
        px = sx + fwd.x * dd + right.x * side
        py = sy + fwd.y * dd + right.y * side
        if blocked(px, py, 25):
            log("  TestProp_%02d 位置被占，跳过" % (i + 1))
            continue
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
        made += 1
        log("  TestProp_%02d @ (%.0f, %.0f)" % (i + 1, px, py))

    ok = les.save_current_level()
    log("save_current_level -> %s" % ok)
    return "spawn=(%.0f,%.0f) props=%d" % (sx, sy, made)


def probe_components():
    bp = EAL.load_asset(CH_PATH)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    SDL = unreal.SubobjectDataBlueprintFunctionLibrary
    roots = sds.k2_gather_subobject_data_for_blueprint(bp)
    out = []

    def walk(h, depth):
        try:
            d = sds.k2_find_subobject_data_from_handle(h)
            o = SDL.get_object(d)
            nm = o.get_name() if o else "?"
            cl = o.get_class().get_name() if o else "?"
            out.append("%s- %s (%s)" % ("  " * depth, nm, cl))
            kids = SDL.get_children(d)
        except Exception as e:
            out.append("%s! %s" % ("  " * depth, e))
            kids = []
        for k in kids:
            walk(k, depth + 1)

    for r in roots:
        walk(r, 0)
    for line in out:
        log(line)
    return len(out)


step("probe_components", probe_components)
step("fix_level", fix_level)
log("===== DONE =====")
