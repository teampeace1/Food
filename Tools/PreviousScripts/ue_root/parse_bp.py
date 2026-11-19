# -*- coding: utf-8 -*-
import re
import io

SRC = r"D:\ue\bp_clip.txt"
OUT = r"D:\ue\bp_graph.txt"

txt = io.open(SRC, encoding="utf-8", errors="ignore").read()

obj_re = re.compile(r'Begin Object Class=([\w\./]+) Name="([^"]+)"(.*?)\nEnd Object', re.S)
pin_re = re.compile(r'CustomProperties Pin \((.*?)\)\n', re.S)

nodes = []
for m in obj_re.finditer(txt):
    cls = m.group(1).split(".")[-1]
    name = m.group(2)
    body = m.group(3)
    nodes.append((cls, name, body))

name2title = {}
for cls, name, body in nodes:
    title = cls
    for key in ("MemberName", "MacroGraphReference", "NodeComment"):
        pass
    mm = re.search(r'MemberName="([^"]*)"', body)
    ev = re.search(r'EventReference=\(([^)]*)\)', body)
    vr = re.search(r'VariableReference=\(([^)]*)\)', body)
    dr = re.search(r'DelegatePropertyName="([^"]*)"', body)
    if cls == "K2Node_CallFunction" and mm:
        title = mm.group(1)
    elif cls == "K2Node_Event" and ev:
        m2 = re.search(r'MemberName="([^"]*)"', ev.group(1))
        title = "EVENT:" + (m2.group(1) if m2 else "?")
    elif cls == "K2Node_VariableGet" and vr:
        m2 = re.search(r'MemberName="([^"]*)"', vr.group(1))
        title = "GET:" + (m2.group(1) if m2 else "?")
    elif cls == "K2Node_VariableSet" and vr:
        m2 = re.search(r'MemberName="([^"]*)"', vr.group(1))
        title = "SET:" + (m2.group(1) if m2 else "?")
    elif cls == "K2Node_IfThenElse":
        title = "Branch"
    elif cls == "K2Node_Knot":
        title = "Reroute"
    elif cls == "K2Node_MacroInstance" and mm:
        title = "MACRO:" + mm.group(1)
    elif cls == "K2Node_DynamicCast":
        m2 = re.search(r'TargetType=([^,\)]+)', body)
        title = "CAST:" + (m2.group(1) if m2 else "?")
    elif cls == "K2Node_ExecutionSequence":
        title = "Sequence"
    elif cls == "K2Node_MultiGate":
        title = "MultiGate"
    elif cls == "K2Node_CommutativeAssociativeBinaryOperator" and mm:
        title = mm.group(1)
    name2title[name] = "%s [%s]" % (title, name)

# 解析引脚连线
edges = []
for cls, name, body in nodes:
    for pm in pin_re.finditer(body):
        p = pm.group(1)
        pn = re.search(r'PinName="([^"]*)"', p)
        dr = re.search(r'Direction="(\w+)"', p)
        lk = re.search(r'LinkedTo=\((.*?)\)', p, re.S)
        if not (pn and lk):
            continue
        if dr and dr.group(1) == "EGPD_Input":
            continue
        for tgt in re.finditer(r'([\w]+) ([0-9A-F]{32})', lk.group(1)):
            edges.append((name, pn.group(1), tgt.group(1)))

with io.open(OUT, "w", encoding="utf-8") as fh:
    fh.write("nodes: %d\n\n" % len(nodes))
    for cls, name, body in nodes:
        fh.write("%-52s %s\n" % (name2title[name], cls))
    fh.write("\n---- edges ----\n")
    seen = set()
    for src, pin, dst in sorted(edges):
        k = (src, pin, dst)
        if k in seen:
            continue
        seen.add(k)
        fh.write("%-40s .%-22s ->  %s\n" % (
            name2title.get(src, src), pin, name2title.get(dst, dst)))

print("done", len(nodes), "nodes", len(seen), "edges")
