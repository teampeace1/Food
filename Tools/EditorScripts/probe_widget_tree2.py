# -*- coding: utf-8 -*-
"""Dump WBP_RecipeGuide widgets through the WidgetTree sub-object."""
import json
import os

import unreal

PATH = "/Game/FoodGameplay/WBP_RecipeGuide.WBP_RecipeGuide:WidgetTree"
tree = unreal.load_object(None, PATH)
lines = ["tree=%s" % tree]
if tree:
    for prop in ("root_widget", "RootWidget", "all_widgets", "AllWidgets", "widgets"):
        try:
            value = tree.get_editor_property(prop)
            lines.append("OK %s -> %s (%d)" % (prop, type(value).__name__, len(value) if hasattr(value, "__len__") else -1))
            if prop.lower() in ("all_widgets", "widgets") and hasattr(value, "__len__"):
                for widget in value:
                    try:
                        txt = widget.get_editor_property("text")
                    except Exception:  # noqa: BLE001
                        txt = ""
                    lines.append("   - %-26s %-18s %s" % (widget.get_name(), widget.get_class().get_name(), txt))
        except Exception as exc:  # noqa: BLE001
            lines.append("FAIL %s -> %r" % (prop, exc))

saved = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
with open(os.path.join(saved, "widget_probe2.txt"), "w", encoding="utf-8") as handle:
    handle.write("\n".join(lines))
print("PROBE2_DONE")
