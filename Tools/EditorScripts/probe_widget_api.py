# -*- coding: utf-8 -*-
"""Probe how to reach the widget tree of a UMG blueprint on this engine build."""
import json
import os

import unreal

bp = unreal.load_asset("/Game/FoodGameplay/WBP_RecipeGuide")
lines = []
lines.append("bp=%s class=%s" % (bp, bp.get_class().get_name() if bp else "none"))
if bp:
    for name in ("widget_tree", "WidgetTree", "widgettree", "RootWidget"):
        try:
            value = bp.get_editor_property(name)
            lines.append("OK %s -> %s" % (name, value))
        except Exception as exc:  # noqa: BLE001
            lines.append("FAIL %s -> %r" % (name, exc))
    attrs = [a for a in dir(bp) if "widget" in a.lower() or "tree" in a.lower()]
    lines.append("dir-widget: %s" % attrs)
    for candidate in ("/Game/FoodGameplay/WBP_RecipeGuide.WBP_RecipeGuide:WidgetTree",
                      "WidgetTree"):
        try:
            obj = unreal.load_object(None, candidate)
            lines.append("load_object %s -> %s" % (candidate, obj))
        except Exception as exc:  # noqa: BLE001
            lines.append("load_object %s failed %r" % (candidate, exc))
    try:
        outer = bp.get_outermost_outer()
        lines.append("outers: %s" % outer)
    except Exception as exc:  # noqa: BLE001
        lines.append("outer failed %r" % exc)
    try:
        names = [n for n in bp.get_class().get_editor_property_names() if "widget" in n.lower() or "tree" in n.lower()]
        lines.append("class-props: %s" % names)
    except Exception as exc:  # noqa: BLE001
        lines.append("class-props failed %r" % exc)

saved = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
with open(os.path.join(saved, "widget_probe.txt"), "w", encoding="utf-8") as handle:
    handle.write("\n".join(lines))
print("PROBE_DONE")
