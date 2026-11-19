# -*- coding: utf-8 -*-
import unreal

LOG = r"D:\ue\dump_bp_log.txt"


def log(msg):
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(str(msg) + "\n")


def reset():
    with open(LOG, "w", encoding="utf-8") as fh:
        fh.write("")


reset()

BP_PATH = "/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter"
bp = unreal.load_asset(BP_PATH)
log("bp: %s" % (bp,))


def ref_name(node, prop):
    try:
        ref = node.get_editor_property(prop)
        if ref is None:
            return None
        for key in ("member_name", "member_parent", "custom_function_name"):
            try:
                v = ref.get_editor_property(key)
                if v:
                    return str(v)
            except Exception:
                pass
        return str(ref)
    except Exception:
        return None


def title_of(node):
    for prop in ("function_reference", "event_reference", "variable_reference",
                 "macro_reference", "custom_function_name"):
        n = ref_name(node, prop)
        if n:
            return "%s -> %s" % (prop, n)
    return ""


def pin_owner_name(pin):
    try:
        return str(pin.get_editor_property("owning_node").get_name())
    except Exception:
        return "?"


def dump_page(page, label):
    log("")
    log("=" * 70)
    log("PAGE: %s (%s)" % (label, page.get_name()))
    try:
        nodes = page.get_editor_property("nodes")
    except Exception as e:
        log("  cannot read nodes: %s" % e)
        return
    log("node count: %d" % len(nodes))

    names = {}
    for n in nodes:
        try:
            names[n.get_name()] = n
        except Exception:
            pass

    for n in nodes:
        nm = n.get_name()
        cls = n.get_class().get_name()
        try:
            px = n.get_editor_property("node_pos_x")
            py = n.get_editor_property("node_pos_y")
        except Exception:
            px = py = "?"
        log("")
        log("[%s] %s   pos=(%s,%s)" % (nm, cls, px, py))
        t = title_of(n)
        if t:
            log("    title: %s" % t)
        try:
            pins = n.get_editor_property("pins")
        except Exception as e:
            log("    no pins: %s" % e)
            continue
        for p in pins:
            try:
                pname = str(p.get_editor_property("pin_name"))
                pdir = str(p.get_editor_property("direction"))
                plinks = p.get_editor_property("linked_to")
            except Exception:
                continue
            if plinks and len(plinks) > 0:
                targets = []
                for lk in plinks:
                    targets.append("%s.%s" % (pin_owner_name(lk), lk.get_property_name()))
                log("    %s (%s) -> %s" % (
                    pname, "OUT" if "Output" in pdir or "true" in pdir.lower() else "IN",
                    ", ".join(targets)))


try:
    pages = bp.get_editor_property("ubergraph_pages")
    log("ubergraph pages: %d" % len(pages))
    for i, pg in enumerate(pages):
        dump_page(pg, "ubergraph[%d]" % i)
except Exception as e:
    log("ubergraph error: %s" % e)

try:
    for fn in bp.get_editor_property("function_graphs"):
        dump_page(fn, "function")
except Exception as e:
    log("functions error: %s" % e)

log("")
log("=== DUMP OK ===")
