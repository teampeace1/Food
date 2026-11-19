# -*- coding: utf-8 -*-
"""清理关卡里的 TextRender 标注（编辑器中只显示 T 图标，徒增干扰），并保存。"""
import unreal

LOG = r"D:\ue\kitchen_fix.txt"
_out = []


def log(s):
    _out.append(str(s))
    with open(LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(_out) + "\n")
    print(s)


LEVEL = "/Game/Maps/L_Kitchen_Whitebox"
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
log("load_level -> %s" % les.load_level(LEVEL))

n = 0
for a in eas.get_all_level_actors():
    try:
        label = a.get_actor_label()
    except Exception:
        label = ""
    if label.startswith("LBL_"):
        eas.destroy_actor(a)
        n += 1
log("removed %d text labels" % n)
log("save -> %s" % les.save_current_level())
log("total actors -> %d" % len(eas.get_all_level_actors()))
log("=== FIX OK ===")
