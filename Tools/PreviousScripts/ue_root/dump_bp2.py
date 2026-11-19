# -*- coding: utf-8 -*-
import unreal

LOG = r"D:\ue\dump_bp_log.txt"
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


def owner_name(pin):
    try:
        return str(pin.get_editor_property("owning_node").get_name())
    except Exception:
        return "?"


def dump(graph, label):
    log("")
    log("=" * 78)
    log("GRAPH: %s  (%s)" % (label, graph.get_name()))
    try:
        nodes = graph.get_editor_property("nodes")
    except Exception as e:
        log("  read fail: %s" % e)
        return
    log("nodes: %d" % len(nodes))
    for n in nodes:
        try:
            title = BEL.get_node_title(n)
        except Exception:
            title = "?"
        cls = n.get_class().get_name()
        try:
            px = int(n.get_editor_property("node_pos_x"))
            py = int(n.get_editor_property("node_pos_y"))
        except Exception:
            px = py = -1
        log("")
        log("- %-40s | %-28s | (%d,%d)" % (title, cls, px, py))
        try:
            pins = n.get_editor_property("pins")
        except Exception:
            continue
        for p in pins:
            try:
                pname = str(p.get_editor_property("pin_name"))
                links = p.get_editor_property("linked_to")
            except Exception:
                continue
            if not links:
                continue
            out = []
            for lk in links:
                try:
                    out.append("%s.%s" % (owner_name(lk), lk.get_property_name()))
                except Exception:
                    out.append("?")
            log("      %s  ->  %s" % (pname, " | ".join(out)))


for g in BEL.list_graphs(bp):
    if g.get_name() in ("EventGraph",):
        dump(g, "EventGraph")

log("")
log("=== DONE ===")
