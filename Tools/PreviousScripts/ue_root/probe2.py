# -*- coding: utf-8 -*-
"""探测 5.8 的 IMC 映射结构，以及角色蓝图里的组件列表。"""
import unreal
import traceback

LOG = r"D:\ue\probe2_log.txt"
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

log("===== PROBE IMC =====")
imc = EAL.load_asset("/Game/Input/IMC_Default")
names = [a for a in dir(imc) if not a.startswith("_")]
log("IMC 属性/方法:")
for n in names:
    log("    " + n)

for cand in ("default_key_mappings", "default_key_mappings_by_profile"):
    try:
        v = imc.get_editor_property(cand)
        log("\n>>> %s = %r" % (cand, v))
        log("    类型: %s" % type(v))
        if v is not None:
            sub = [a for a in dir(v) if not a.startswith("_")]
            log("    子属性: %s" % sub)
            for s in sub:
                if s in ("set_editor_property", "get_editor_property", "cast",
                         "static_struct", "copy", "equals", "export_text",
                         "import_text", "to_tuple"):
                    continue
                try:
                    log("      %s = %r" % (s, getattr(v, s)))
                except Exception as e:
                    log("      %s -> err %s" % (s, e))
    except Exception as e:
        log("\n>>> %s 读取失败: %s" % (cand, e))

log("\n===== PROBE CHARACTER BP =====")
bp = EAL.load_asset("/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
SDL = unreal.SubobjectDataBlueprintFunctionLibrary


def walk(h, depth=0):
    try:
        obj = SDL.get_object(h)
    except Exception as e:
        obj = None
        log("  " * depth + "get_object err %s" % e)
    name = obj.get_name() if obj else "?"
    cls = obj.get_class().get_name() if obj else "?"
    log("  " * depth + "- %-26s (%s)" % (name, cls))
    try:
        kids = SDL.get_children(h)
    except Exception:
        kids = []
    for k in kids:
        walk(k, depth + 1)


roots = sds.k2_gather_subobject_data_for_blueprint(bp)
for r in roots:
    walk(r)

log("\n===== DONE =====")
