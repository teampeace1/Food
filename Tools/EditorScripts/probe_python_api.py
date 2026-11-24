# -*- coding: utf-8 -*-
"""Probe which Python APIs are available for listing a blueprint's reflected properties."""
import unreal

lines = []


def dump(label, obj):
    names = [n for n in dir(obj) if not n.startswith("_")]
    lines.append("## " + label + " (%d)" % len(names))
    lines.append("   " + ", ".join(names))


bp = unreal.EditorAssetLibrary.load_asset("/Game/FoodGameplay/BP_Ingredient")
cls = bp.generated_class()
cdo = unreal.get_default_object(cls)

dump("BlueprintEditorLibrary", unreal.BlueprintEditorLibrary)
dump("UClass", cls)
dump("CDO", cdo)

for attr in dir(cdo):
    if any(k in attr.lower() for k in ("quality", "cut", "name", "state", "count")):
        try:
            lines.append("cdo.%s = %s" % (attr, getattr(cdo, attr)))
        except Exception as exc:
            lines.append("cdo.%s ERR %s" % (attr, str(exc)[:60]))

for name in ("get_blueprint_variable_names", "get_blueprint_variables", "list_properties"):
    fn = getattr(unreal.BlueprintEditorLibrary, name, None)
    lines.append("BlueprintEditorLibrary.%s -> %s" % (name, fn))
    if fn and bp:
        try:
            lines.append("   result: %s" % (fn(bp),))
        except Exception as exc:
            lines.append("   ERR %s" % str(exc)[:120])

out = "\n".join(lines)
with open(unreal.Paths.project_saved_dir() + "python_probe.txt", "w", encoding="utf-8") as handle:
    handle.write(out)
unreal.log("PY_PROBE_DONE")
unreal.SystemLibrary.quit_editor()
