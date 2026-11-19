# -*- coding: utf-8 -*-
"""确认测试道具的物理是否开启，并把它们放到地面上。"""
import unreal

LOG = r"D:\ue\fixprops_log.txt"
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

log("===== TEST PROPS =====")
for a in eas.get_all_level_actors():
    lb = a.get_actor_label()
    if not lb.startswith("TestProp"):
        continue
    comp = a.static_mesh_component
    bi = comp.get_editor_property("body_instance")
    sim = bi.get_editor_property("simulate_physics") if bi else None
    log("%s  bSimulatePhysics(直接读) = %s" % (lb, sim))
    if sim is False or sim is None:
        comp.set_simulate_physics(True)
        bi = comp.get_editor_property("body_instance")
        log("   已开启，重读 = %s" % bi.get_editor_property("simulate_physics"))
    # 质量
    try:
        comp.set_mass_override_in_kg("", 1.5, True)
        log("   质量覆盖 = 1.5 kg")
    except Exception as e:
        log("   质量设置失败: %s" % e)
    # 贴地：立方体 22cm，中心放 z=12
    loc = a.get_actor_location()
    a.set_actor_location(unreal.Vector(loc.x, loc.y, 12.0), False, False)
    log("   放到 z=12")

log("save -> %s" % les.save_current_level())
log("===== DONE =====")
