# -*- coding: utf-8 -*-
"""列出角色蓝图里已有的图表与事件，判断用户是否已经连过节点。"""
import unreal

LOG = r"D:\ue\probe6_log.txt"
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


BEL = unreal.BlueprintEditorLibrary
bp = unreal.EditorAssetLibrary.load_asset("/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter")

log("===== 蓝图图表 =====")
for g in BEL.list_graphs(bp):
    log("  graph: %s" % g.get_name())

log("===== 事件 =====")
try:
    for e in BEL.list_events(bp):
        log("  event: %s" % e.get_name())
except Exception as ex:
    log("  list_events 失败: %s" % ex)

log("===== 函数 =====")
try:
    for f in BEL.list_functions(bp):
        log("  func: %s" % f.get_name())
except Exception as ex:
    log("  list_functions 失败: %s" % ex)

log("===== 变量 =====")
try:
    for v in BEL.list_member_variable_names(bp):
        log("  var: %s" % v)
except Exception as ex:
    log("  list_member_variable_names 失败: %s" % ex)

log("===== 事件图表里的节点 =====")
try:
    g = BEL.find_event_graph(bp)
    log("event graph = %r" % g)
    if g:
        for n in g.get_editor_property("nodes"):
            log("  node: %-46s %r" % (n.get_class().get_name(), BEL.get_node_title(n)))
except Exception as ex:
    log("  读节点失败: %s" % ex)

log("===== DONE =====")
