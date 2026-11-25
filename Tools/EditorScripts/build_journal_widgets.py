# -*- coding: utf-8 -*-
"""生成厨房手记面板与勋章行两个控件蓝图。

用法：-run=pythonscript -script=build_journal_widgets.py
结果：/Game/UI/Widgets/Panels/WBP_Journal、/Game/UI/Widgets/Panels/WBP_MedalRow
输出：Saved/build_journal_widgets.json

C++ 端按控件名取用：
  WBP_Journal  -> Scroll（键盘上下滚动）、Head0..Head6 / Body0..Body6（7 条回忆）
                  MedalList（勋章行容器）
  WBP_MedalRow -> Medal / Lock / Name / Desc
回忆正文直接写在蓝图里，代码只在“尚未解锁”时把它盖成占位文字。
"""
import json
import os
import traceback

import unreal

eal = unreal.EditorAssetLibrary
helper = unreal.MCPythonHelper
DIR = "/Game/UI/Widgets/Panels"

ART = {
    "frame": "/Game/UI/Art/Frames/T_WoodParchmentFrame",
}

# 标题 / 正文都写进蓝图，改字不用再编译
MEMORIES = [
    ("开篇", "餐馆的最后一天，想再做一次仰望星空派。要是有人愿意一起动手，就更好了。"),
    ("面团", "第一次擀面时，我们把厨房弄得像下了一场雪。面皮不够圆，大家却笑了很久。"),
    ("食材", "有人喜欢切得细一些，有人总是偷偷尝一口。那时候，准备食材也像一场聚会。"),
    ("馅料", "把不同的味道拌在一起，是大家最期待的一步。每个人都说自己知道最好的配方。"),
    ("鱼头", "我们把鱼头朝向天空，开玩笑说，这样它们就能看见海上的星星。"),
    ("烘烤", "炉火需要耐心。等香味慢慢传出来时，总有人已经搬好椅子，坐在桌边。"),
    ("同行", "今天，厨房里又有人和我一起做了仰望星空派。谢谢你陪我走过餐馆的最后一天。"),
]

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
        # 画布本身不挡输入，只有里面的面板接收点击/滚轮
        self.set_prop(self.root, "visibility", unreal.SlateVisibility.SELF_HIT_TEST_INVISIBLE)
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

    def box_slot(self, name, pad=None, align=None, fill=0.0, valign=None):
        s = self.slot(name)
        if not s:
            errors.append("no slot %s/%s" % (self.name, name))
            return
        if pad is not None:
            try:
                s.set_editor_property("padding", unreal.Margin(*[float(v) for v in pad]))
            except Exception as exc:  # noqa: BLE001
                errors.append("pad %s/%s: %r" % (self.name, name, exc))
        try:
            if align is not None:
                s.set_editor_property("horizontal_alignment", align)
            if valign is not None:
                s.set_editor_property("vertical_alignment", valign)
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
             wrap=False, justify=None):
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

    def fill_image(self, name):
        """Image 默认按贴图原始尺寸，需要显式铺满父容器。"""
        s = self.slot(name)
        if not s:
            errors.append("no slot %s/%s" % (self.name, name))
            return
        try:
            s.set_editor_property("horizontal_alignment", unreal.HorizontalAlignment.H_ALIGN_FILL)
            s.set_editor_property("vertical_alignment", unreal.VerticalAlignment.V_ALIGN_FILL)
        except Exception as exc:  # noqa: BLE001
            errors.append("fill_image %s/%s: %r" % (self.name, name, exc))

    def save(self):
        try:
            helper.compile_blueprint(self.bp)
        except Exception as exc:  # noqa: BLE001
            errors.append("compile %s: %r" % (self.name, exc))
        eal.save_asset(self.path, only_if_is_dirty=False)


def build_journal():
    p = Panel("WBP_Journal")
    if not p.create():
        return
    # 左侧、距左 35 距上 54，高 986（1080 设计稿）；拖 PanelBox 就能整体挪
    p.add("SizeBox", "PanelBox")
    p.canvas("PanelBox", anchor=(0.0, 0.0), align=(0.0, 0.0),
             offset=(35.0, 54.0), size=(430.0, 986.0), auto_size=False)
    p.size_override("PanelBox", width=430.0, height=986.0)

    p.add("Border", "Bg", parent="PanelBox")
    p.brush("Bg", ART["frame"], (1.0, 1.0, 1.0, 1.0))
    p.set_prop("Bg", "padding", unreal.Margin(45.0, 40.0, 45.0, 40.0))

    p.add("VerticalBox", "Stack", parent="Bg")

    p.add("TextBlock", "Title", parent="Stack")
    p.box_slot("Title", pad=(0.0, 0.0, 0.0, 12.0))
    p.text("Title", "厨房手记  ·  成就勋章", size=24, bold=True,
           color=(1.0, 0.87, 0.62, 1.0))

    p.add("ScrollBox", "Scroll", parent="Stack")
    p.box_slot("Scroll", fill=1.0)

    p.add("TextBlock", "SecMemories", parent="Scroll")
    p.box_slot("SecMemories", pad=(8.0, 4.0, 8.0, 4.0))
    p.text("SecMemories", "老厨师的回忆", size=21, bold=True,
           color=(1.0, 0.87, 0.62, 1.0))

    for index, (heading, body) in enumerate(MEMORIES):
        card = "Entry%d" % index
        p.add("Border", card, parent="Scroll")
        p.box_slot(card, pad=(7.0, 4.0, 7.0, 4.0))
        p.brush(card, None, (0.36, 0.22, 0.12, 0.95))
        p.set_prop(card, "padding", unreal.Margin(10.0, 10.0, 10.0, 10.0))

        p.add("VerticalBox", "Stack%d" % index, parent=card)
        p.add("TextBlock", "Head%d" % index, parent="Stack%d" % index)
        p.text("Head%d" % index, heading, size=17, bold=True,
               color=(1.0, 0.87, 0.65, 1.0))
        p.add("TextBlock", "Body%d" % index, parent="Stack%d" % index)
        p.box_slot("Body%d" % index, pad=(0.0, 5.0, 0.0, 0.0))
        p.text("Body%d" % index, body, size=14, wrap=True,
               color=(0.95, 0.88, 0.73, 1.0))

    p.add("TextBlock", "SecMedals", parent="Scroll")
    p.box_slot("SecMedals", pad=(8.0, 12.0, 8.0, 4.0))
    p.text("SecMedals", "成就勋章", size=21, bold=True,
           color=(1.0, 0.87, 0.62, 1.0))

    # 勋章行由代码按解锁状态生成，样式在 WBP_MedalRow 里
    p.add("VerticalBox", "MedalList", parent="Scroll")
    p.box_slot("MedalList", pad=(7.0, 3.0, 7.0, 3.0))

    p.save()


def build_medal_row():
    p = Panel("WBP_MedalRow")
    if not p.create():
        return
    p.add("Border", "Bg")
    p.canvas("Bg", anchor=(0.0, 0.0), align=(0.0, 0.0), offset=(0.0, 0.0),
             auto_size=True)
    p.brush("Bg", None, (0.36, 0.22, 0.12, 0.95))
    p.set_prop("Bg", "padding", unreal.Margin(7.0, 7.0, 7.0, 7.0))

    p.add("HorizontalBox", "Row", parent="Bg")

    p.add("SizeBox", "BadgeBox", parent="Row")
    p.size_override("BadgeBox", width=64.0, height=64.0)

    p.add("Overlay", "BadgeLayer", parent="BadgeBox")
    p.add("Image", "Medal", parent="BadgeLayer")
    p.fill_image("Medal")

    p.add("TextBlock", "Lock", parent="BadgeLayer")
    p.text("Lock", "?", size=30, bold=True, color=(1.0, 0.88, 0.65, 1.0),
           justify=unreal.TextJustify.CENTER)
    try:
        p.find("Lock").slot.set_editor_property(
            "horizontal_alignment", unreal.HorizontalAlignment.H_ALIGN_CENTER)
        p.find("Lock").slot.set_editor_property(
            "vertical_alignment", unreal.VerticalAlignment.V_ALIGN_CENTER)
    except Exception as exc:  # noqa: BLE001
        errors.append("lock slot: %r" % (exc,))

    p.add("VerticalBox", "Texts", parent="Row")
    p.box_slot("Texts", pad=(12.0, 0.0, 0.0, 0.0), fill=1.0,
               valign=unreal.VerticalAlignment.V_ALIGN_CENTER)

    p.add("TextBlock", "Name", parent="Texts")
    p.text("Name", "勋章名称", size=18, bold=True, color=(1.0, 0.87, 0.65, 1.0))

    p.add("TextBlock", "Desc", parent="Texts")
    p.text("Desc", "勋章说明显示在这里。", size=13, wrap=True,
           color=(0.95, 0.88, 0.73, 1.0))

    p.save()


try:
    build_journal()
    build_medal_row()
except Exception:  # noqa: BLE001
    errors.append(traceback.format_exc())

saved_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
target = os.path.join(saved_dir, "build_journal_widgets.json")
with open(target, "w", encoding="utf-8") as handle:
    json.dump({"errors": errors, "log": log}, handle, ensure_ascii=False, indent=1)
print("BUILD_JOURNAL_DONE errors=%d -> %s" % (len(errors), target))
