# -*- coding: utf-8 -*-
"""探测 UE5.8 是否能通过 Toolset / 其它接口在蓝图图表里建节点。"""
import unreal

LOG = r"D:\ue\probe5_log.txt"
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


log("===== PROBE TOOLSET =====")
for n in ["ToolsetRegistry", "BlueprintToolset", "ActorToolset", "AssetToolset",
          "MaterialToolset", "DataTableToolset", "ObjectTools"]:
    log("hasattr(unreal, %-20s) = %s" % (n, hasattr(unreal, n)))

if hasattr(unreal, "BlueprintToolset"):
    log("\nBlueprintToolset 方法:")
    for m in dir(unreal.BlueprintToolset):
        if not m.startswith("_"):
            log("    " + m)

if hasattr(unreal, "ToolsetRegistry"):
    log("\nToolsetRegistry 方法:")
    for m in dir(unreal.ToolsetRegistry):
        if not m.startswith("_"):
            log("    " + m)
    try:
        ts = unreal.ToolsetRegistry.get_toolset(unreal.BlueprintToolset)
        log("\nget_toolset -> %r" % (ts,))
        if ts:
            log("实例方法:")
            for m in dir(ts):
                if not m.startswith("_"):
                    log("    " + m)
    except Exception as e:
        log("get_toolset 失败: %s" % e)

log("\n===== 其它可能的建节点接口 =====")
for n in ["K2Node_CallFunction", "K2Node_Event", "K2Node_VariableGet",
          "BlueprintEditorLibrary", "EditorLevelLibrary"]:
    log("hasattr(unreal, %-24s) = %s" % (n, hasattr(unreal, n)))

if hasattr(unreal, "BlueprintEditorLibrary"):
    log("\nBlueprintEditorLibrary 方法:")
    for m in dir(unreal.BlueprintEditorLibrary):
        if not m.startswith("_"):
            log("    " + m)

log("===== DONE =====")
