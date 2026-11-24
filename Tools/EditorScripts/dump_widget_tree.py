# -*- coding: utf-8 -*-
"""Dump the widget tree of a UMG blueprint so text/slot problems can be located by data.

Usage: -run=pythonscript -script=dump_widget_tree.py
Result: Saved/widget_tree.json
"""
import json
import os

import unreal

ASSETS = [
    "/Game/UI/Widgets/Panels/WBP_RecipeGuide",
]

out = {}


def safe(widget, prop, default=""):
    try:
        return str(widget.get_editor_property(prop))
    except Exception:
        return default


def slot_info(widget):
    info = {}
    try:
        slot = widget.slot
    except Exception:
        return info
    if not slot:
        return info
    for key in ("padding", "horizontal_alignment", "vertical_alignment", "size", "position",
                "auto_size", "max_desired_width"):
        try:
            info[key] = str(slot.get_editor_property(key))
        except Exception:
            pass
    return info


def walk(widget, depth, records):
    rec = {
        "depth": depth,
        "name": widget.get_name(),
        "class": widget.get_class().get_name(),
        "visible": safe(widget, "visibility"),
        "slot": slot_info(widget),
    }
    if isinstance(widget, unreal.TextBlock):
        rec["text"] = safe(widget, "text")
        rec["font"] = safe(widget, "font")
        rec["color"] = safe(widget, "color_and_opacity")
    if isinstance(widget, unreal.Image):
        rec["brush"] = safe(widget, "brush")
    if isinstance(widget, unreal.CanvasPanelSlot):
        pass
    records.append(rec)
    if isinstance(widget, unreal.PanelWidget):
        for index in range(widget.get_children_count()):
            walk(widget.get_child_at(index), depth + 1, records)


for path in ASSETS:
    bp = unreal.load_asset(path)
    if not bp:
        out[path] = {"error": "asset not found"}
        continue
    try:
        tree = bp.get_editor_property("widget_tree")
        records = []
        walk(tree.get_editor_property("root_widget"), 0, records)
        out[path] = {"widgets": records}
    except Exception as exc:  # noqa: BLE001
        out[path] = {"error": repr(exc)}

saved_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
target = os.path.join(saved_dir, "widget_tree.json")
with open(target, "w", encoding="utf-8") as handle:
    json.dump(out, handle, ensure_ascii=False, indent=1)
print("DUMP_WIDGET_TREE_DONE %s -> %s" % ({path: len(rec.get("widgets", [])) for path, rec in out.items()}, target))
