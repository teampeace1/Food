# -*- coding: utf-8 -*-
"""生成“手记更新”提示条与“成就达成”弹窗两个控件蓝图。

用法：-run=pythonscript -script=build_toast_widgets.py
结果：/Game/UI/Widgets/HUD/WBP_MemoryToast、WBP_AchievementPopup
输出：Saved/build_toast_widgets.json

C++ 端按控件名取用：
  WBP_MemoryToast   -> Title / Body
  WBP_AchievementPopup -> Bg / Medal / Sparkle / Caption / Name / Desc
布局基准 1920x1080，位置与尺寸都可以在设计师里直接拖。
"""
import json
import os
import traceback

import unreal

eal = unreal.EditorAssetLibrary
helper = unreal.MCPythonHelper
DIR = "/Game/UI/Widgets/HUD"

ART = {
    "frame": "/Game/UI/Art/Frames/T_WoodParchmentFrame",
}

errors = []
log = []


def slate_color(rgba):
    c = unreal.SlateColor()
    c.set_editor_property("specified_color", linear_color(rgba))
    return c


def linear_color(rgba):
    return unreal.LinearColor(float(rgba[0]), float(rgba[1]),
                              float(rgba[2]), float(rgba[3]))


def paint_brush(b, tex_path=None, draw_type=None):
    if tex_path:
        b.set_editor_property("resource_object", eal.load_asset(tex_path))
        b.set_editor_property("draw_as", unreal.SlateBrushDrawType.IMAGE)
    if draw_type is not None:
        b.set_editor_property("draw_as", draw_type)
    return b


class Panel(object):
    def __init__(self, name):
        self.name = name
        self.path = "%s/%s" % (DIR, name)
        self.bp = None
        self.root = None

    def create(self):
        if eal.does_asset_exist(self.path):
            eal.delete_asset(self.path)
        factory = unreal.WidgetBlueprintFactory()
        factory.set_editor_property("parent_class", unreal.UserWidget)
        self.bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            self.name, DIR, unreal.WidgetBlueprint, factory)
        if not self.bp:
            errors.append("create failed: %s" % self.path)
            return False
        info = json.loads(helper.umg_get_widget_info(self.bp))
        self.root = info.get("root_widget") or ""
        if not self.root:
            res = json.loads(helper.umg_add_widget(self.bp, "CanvasPanel", "Root", ""))
            if not res.get("success"):
                errors.append("root failed: %s" % res)
                return False
            self.root = "Root"
        self.set_prop(self.root, "visibility", unreal.SlateVisibility.HIT_TEST_INVISIBLE)
        log.append("%s root=%s" % (self.name, self.root))
        return True

    def find(self, name):
        return helper.umg_find_widget(self.bp, name)

    def add(self, wtype, name, parent=None):
        parent_name = parent or self.root
        res = json.loads(helper.umg_add_widget(self.bp, wtype, name, parent_name))
        if not res.get("success"):
            errors.append("add %s/%s: %s" % (self.name, name, res))
            return None
        return self.find(name)

    def set_prop(self, name, prop, value):
        w = self.find(name)
        if not w:
            errors.append("missing %s/%s" % (self.name, name))
            return
        try:
            w.set_editor_property(prop, value)
        except Exception as exc:  # noqa: BLE001
            errors.append("%s/%s.%s: %r" % (self.name, name, prop, exc))

    def slot(self, name):
        w = self.find(name)
        return w.slot if w else None

    def canvas(self, name, anchor, align, offset, size=None, auto_size=False):
        """anchor/align/offset 都是 (x, y)；size=None 表示自动尺寸。"""
        s = self.slot(name)
        if not s:
            errors.append("no slot %s/%s" % (self.name, name))
            return
        try:
            helper.umg_set_slot_layout(
                self.bp, name,
                float(anchor[0]), float(anchor[1]), float(anchor[0]), float(anchor[1]),
                float(offset[0]), float(offset[1]),
                float(size[0]) if size else 0.0, float(size[1]) if size else 0.0)
            s.set_alignment(unreal.Vector2D(float(align[0]), float(align[1])))
            s.set_editor_property("auto_size", bool(auto_size))
        except Exception as exc:  # noqa: BLE001
            errors.append("canvas %s/%s: %r" % (self.name, name, exc))

    def box_slot(self, name, pad=None, align=None, fill=0.0):
        s = self.slot(name)
        if not s:
            errors.append("no slot %s/%s" % (self.name, name))
            return
        try:
            if pad is not None:
                s.set_editor_property("padding", unreal.Margin(*[float(v) for v in pad]))
        except Exception as exc:  # noqa: BLE001
            errors.append("pad %s/%s: %r" % (self.name, name, exc))
        try:
            if align is not None:
                s.set_editor_property("horizontal_alignment", align)
        except Exception:  # noqa: BLE001
            pass
        if fill > 0.0:
            try:
                scs = unreal.SlateChildSize()
                scs.set_editor_property("size_rule", unreal.SlateSizeRule.FILL)
                scs.set_editor_property("value", float(fill))
                s.set_editor_property("size", scs)
            except Exception as exc:  # noqa: BLE001
                errors.append("fill %s/%s: %r" % (self.name, name, exc))

    def text(self, name, value, size=18, color=(1.0, 1.0, 1.0, 1.0), bold=False,
             wrap=False, justify=None, shadow=False):
        w = self.find(name)
        if not w:
            errors.append("no text %s/%s" % (self.name, name))
            return
        try:
            w.set_editor_property("text", unreal.Text.cast(str(value)))
            f = w.get_editor_property("font")
            f.set_editor_property("size", int(size))
            try:
                f.set_editor_property("typeface_font_name",
                                      unreal.Name("Bold" if bold else "Regular"))
            except Exception:  # noqa: BLE001
                pass
            w.set_editor_property("font", f)
            w.set_editor_property("color_and_opacity", slate_color(color))
            try:
                w.set_editor_property("auto_wrap_text", bool(wrap))
            except Exception:  # noqa: BLE001
                pass
            if justify is not None:
                w.set_editor_property("justification", justify)
            if shadow:
                w.set_editor_property("shadow_offset", unreal.Vector2D(1.0, 1.0))
                w.set_editor_property("shadow_color_and_opacity",
                                      linear_color((0.0, 0.0, 0.0, 0.55)))
        except Exception as exc:  # noqa: BLE001
            errors.append("text %s/%s: %r" % (self.name, name, exc))

    def brush(self, name, tex_path=None, color=None):
        w = self.find(name)
        if not w:
            errors.append("no widget %s/%s" % (self.name, name))
            return
        # UBorder 的画笔叫 background，UImage 叫 brush
        prop = "background" if isinstance(w, unreal.Border) else "brush"
        try:
            b = w.get_editor_property(prop)
            paint_brush(b, tex_path)
            w.set_editor_property(prop, b)
            if color is not None:
                w.set_editor_property("brush_color", linear_color(color))
        except Exception as exc:  # noqa: BLE001
            errors.append("brush %s/%s: %r" % (self.name, name, exc))

    def size_override(self, name, width=None, height=None):
        """SizeBox 的覆盖必须走 SetWidthOverride/SetHeightOverride，直接写数值不会置启用标记。"""
        w = self.find(name)
        if not w:
            errors.append("no sizebox %s/%s" % (self.name, name))
            return
        try:
            if width is not None:
                w.set_width_override(float(width))
            if height is not None:
                w.set_height_override(float(height))
        except Exception as exc:  # noqa: BLE001
            errors.append("size_override %s/%s: %r" % (self.name, name, exc))

    def save(self):
        try:
            helper.compile_blueprint(self.bp)
        except Exception as exc:  # noqa: BLE001
            errors.append("compile %s: %r" % (self.name, exc))
        eal.save_asset(self.path, only_if_is_dirty=False)


def build_toast():
    p = Panel("WBP_MemoryToast")
    if not p.create():
        return
    # 底边居中、距底 70：设计师里直接拖这个 Border 就能改位置
    p.add("Border", "Bg")
    p.canvas("Bg", anchor=(0.5, 1.0), align=(0.5, 1.0), offset=(0.0, -70.0),
             auto_size=True)
    p.brush("Bg", None, (0.16, 0.09, 0.04, 0.0))  # 透明底，换成图片即可
    p.set_prop("Bg", "padding", unreal.Margin(22.0, 10.0, 22.0, 10.0))

    p.add("VerticalBox", "Stack", parent="Bg")
    p.box_slot("Stack", align=unreal.HorizontalAlignment.H_ALIGN_CENTER)

    p.add("TextBlock", "Title", parent="Stack")
    p.box_slot("Title", align=unreal.HorizontalAlignment.H_ALIGN_CENTER)
    p.text("Title", "手记更新", size=15, color=(1.0, 0.80, 0.46, 1.0), bold=True)

    p.add("TextBlock", "Body", parent="Stack")
    p.box_slot("Body", pad=(0.0, 4.0, 0.0, 0.0),
               align=unreal.HorizontalAlignment.H_ALIGN_CENTER)
    p.text("Body", "第一次擀面时，我们把厨房弄得像下了一场雪。", size=18,
           color=(1.0, 0.94, 0.82, 1.0), wrap=True,
           justify=unreal.TextJustify.CENTER)
    p.save()


def build_popup():
    p = Panel("WBP_AchievementPopup")
    if not p.create():
        return
    # 右上角、距右 35 距上 55：固定 430 宽，高度随文字自动
    p.add("SizeBox", "BgBox")
    p.canvas("BgBox", anchor=(1.0, 0.0), align=(1.0, 0.0), offset=(-35.0, 55.0),
             auto_size=True)
    p.size_override("BgBox", width=430.0)

    p.add("Border", "Bg", parent="BgBox")
    p.brush("Bg", ART["frame"], (1.0, 1.0, 1.0, 1.0))
    p.set_prop("Bg", "padding", unreal.Margin(22.0, 22.0, 22.0, 22.0))

    p.add("HorizontalBox", "Row", parent="Bg")

    p.add("SizeBox", "MedalBox", parent="Row")
    p.box_slot("MedalBox")
    p.size_override("MedalBox", width=96.0, height=96.0)

    p.add("Overlay", "MedalLayer", parent="MedalBox")
    p.add("Image", "Medal", parent="MedalLayer")
    # 图片默认按贴图原始大小，必须显式铺满 96x96 的框
    try:
        ms = p.find("Medal").slot
        ms.set_editor_property("horizontal_alignment", unreal.HorizontalAlignment.H_ALIGN_FILL)
        ms.set_editor_property("vertical_alignment", unreal.VerticalAlignment.V_ALIGN_FILL)
    except Exception as exc:  # noqa: BLE001
        errors.append("medal slot: %r" % (exc,))
    p.add("TextBlock", "Sparkle", parent="MedalLayer")
    try:
        sp = p.find("Sparkle")
        sp.slot.set_editor_property("horizontal_alignment",
                                    unreal.HorizontalAlignment.H_ALIGN_RIGHT)
        sp.slot.set_editor_property("vertical_alignment",
                                    unreal.VerticalAlignment.V_ALIGN_TOP)
    except Exception as exc:  # noqa: BLE001
        errors.append("sparkle slot: %r" % (exc,))
    p.text("Sparkle", "✦", size=27, color=(1.0, 0.92, 0.55, 1.0), bold=True)

    p.add("VerticalBox", "Texts", parent="Row")
    p.box_slot("Texts", pad=(12.0, 0.0, 0.0, 0.0), fill=1.0)
    try:
        p.slot("Texts").set_editor_property("vertical_alignment",
                                            unreal.VerticalAlignment.V_ALIGN_CENTER)
    except Exception:  # noqa: BLE001
        pass

    p.add("TextBlock", "Caption", parent="Texts")
    p.text("Caption", "成就达成！", size=16, color=(0.32, 0.13, 0.04, 1.0), bold=True)

    p.add("TextBlock", "Name", parent="Texts")
    p.text("Name", "成就名称", size=24, color=(0.16, 0.07, 0.03, 1.0), bold=True)

    p.add("TextBlock", "Desc", parent="Texts")
    p.text("Desc", "成就说明文字显示在这里，可以在蓝图里改。", size=13,
           color=(0.20, 0.09, 0.04, 1.0), wrap=True)
    p.save()


try:
    build_toast()
    build_popup()
except Exception:  # noqa: BLE001
    errors.append(traceback.format_exc())

saved_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
target = os.path.join(saved_dir, "build_toast_widgets.json")
with open(target, "w", encoding="utf-8") as handle:
    json.dump({"errors": errors, "log": log}, handle, ensure_ascii=False, indent=1)
print("BUILD_TOAST_DONE errors=%d -> %s" % (len(errors), target))
