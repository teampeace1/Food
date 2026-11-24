# -*- coding: utf-8 -*-
"""Dump a blueprint's event graphs as text: node class, title, pins and their default values.

Blueprint logic is binary, but the pins carry the literal constants (e.g. BakeQuality = "Success"),
which is enough to see how a station decides its quality values.
"""
import json
import os
import sys
import unreal

TARGETS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["/Game/FoodGameplay/BP_Oven"]

out = {}
for path in TARGETS:
    bp = unreal.EditorAssetLibrary.load_asset(path)
    rec = {"graphs": [], "error": None}
    out[path] = rec
    if bp is None:
        rec["error"] = "not found"
        continue
    try:
        raw_names = [str(g) for g in unreal.BlueprintEditorLibrary.list_graphs(bp)]
        # list_graphs hands back object reprs like "<Object '/Game/...:BP_Oven:EventGraph' ...>";
        # find_graph wants the plain graph name.
        graph_names = []
        for raw in raw_names:
            name = raw
            if "'" in raw:
                name = raw.split("'")[1]
            if ":" in name:
                name = name.rsplit(":", 1)[1]
            graph_names.append(name)
        rec["graph_names"] = graph_names
        for name in graph_names:
            graph = unreal.BlueprintEditorLibrary.find_graph(bp, name)
            if graph is None:
                rec["graphs"].append({"name": name, "error": "graph not found"})
                continue
            entry = {"name": name, "nodes": []}
            try:
                nodes = graph.get_editor_property("nodes")
            except Exception as exc:
                entry["error"] = "nodes: " + str(exc)[:100]
                nodes = []
            for node in nodes:
                row = {"class": node.get_class().get_name()}
                for attr in ("node_pos_x", "node_pos_y"):
                    pass
                try:
                    row["title"] = str(node.get_editor_property("node_title"))[:60]
                except Exception:
                    pass
                pins = []
                try:
                    all_pins = list(node.get_editor_property("pins"))
                except Exception:
                    all_pins = []
                for pin in all_pins:
                    try:
                        pname = pin.get_editor_property("pin_name")
                        pdir = str(pin.get_editor_property("direction"))
                        ptype = str(pin.get_editor_property("pin_type"))
                        default = pin.get_editor_property("default_value")
                        linked = pin.get_editor_property("linked_to")
                    except Exception:
                        continue
                    pins.append({
                        "name": str(pname),
                        "dir": pdir.split(".")[-1],
                        "type": ptype.split("'")[1] if "'" in ptype else ptype,
                        "default": str(default),
                        "links": len(linked) if linked else 0,
                    })
                row["pins"] = pins
                entry["nodes"].append(row)
            rec["graphs"].append(entry)
    except Exception as exc:
        rec["error"] = str(exc)[:200]

target = os.path.join(unreal.Paths.project_saved_dir(), "bp_graph_dump.json")
with open(target, "w", encoding="utf-8") as handle:
    json.dump(out, handle, ensure_ascii=False, indent=1)
unreal.log("DUMP_BP_GRAPH " + target)
unreal.SystemLibrary.quit_editor()
