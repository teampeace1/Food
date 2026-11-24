# -*- coding: utf-8 -*-
"""生成 5 个可拖拽的菜单 Widget 蓝图（主菜单/暂停/设置/确认/结局）。

用法：-run=pythonscript -script=build_menu_widgets.py
结果：/Game/UI/Widgets/Menus/WBP_*，并输出 Saved/build_menu_widgets.json

命名约定（C++ 端按名字取）：
  Btn_*  UButton / Txt_*  UTextBlock / Slider_*  USlider / Img_*  UImage

布局基准 1920x1080，锚点全部左上，改位置直接改 pos。
"""
import json
import os
import traceback

import unreal

eal = unreal.EditorAssetLibrary
helper = unreal.MCPythonHelper
MENU_DIR = "/Game/UI/Widgets/Menus"

ART = {
    "bg": "/Game/UI/Art/Backgrounds/T_MainMenuBackground",
    "plaque": "/Game/UI/Art/Backgrounds/T_MenuTitlePlaque",
    "title": "/Game/UI/Art/Backgrounds/T_MenuTitleText",
    "button": "/Game/UI/Art/Buttons/T_MenuButton",
    "label_start": "/Game/UI/Art/Buttons/T_Label_start",
    "label_settings": "/Game/UI/Art/Buttons/T_Label_settings",
    "label_quit": "/Game/UI/Art/Buttons/T_Label_quit",
    "frame": "/Game/UI/Art/Frames/T_WoodParchmentFrame",
}

errors = []
log = []


def slate_color(rgba):
    c = unreal.SlateColor()
    c.set_editor_property("specified_color",
                          unreal.LinearColor(float(rgba[0]), float(rgba[1]),
                                             float(rgba[2]), float(rgba[3])))
    return c


def linear_color(rgba):
    return unreal.LinearColor(float(rgba[0]), float(rgba[1]),
                              float(rgba[2]), float(rgba[3]))


def paint_brush(b, tex_path, size=None, uv=None):
    """只设置能可靠写入的字段：贴图 + 绘制方式（尺寸由 slot 决定）。"""
    b.set_editor_property("resource_object", eal.load_asset(tex_path))
    b.set_editor_property("draw_as", unreal.SlateBrushDrawType.IMAGE)
    return b


class Screen(object):
    def __init__(self, name):
        self.name = name
        self.path = "%s/%s" % (MENU_DIR, name)
        self.bp = None
        self.root = None

    # ---------- 构建 ----------
    def create(self):
        if eal.does_asset_exist(self.path):
            eal.delete_asset(self.path)
        factory = unreal.WidgetBlueprintFactory()
        factory.set_editor_property("parent_class", unreal.UserWidget)
        self.bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            self.name, MENU_DIR, unreal.WidgetBlueprint, factory)
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
        log.append("%s root=%s" % (self.name, self.root))
        return True

    def add(self, wtype, name, parent=None, pos=None, size=None, fill=False):
        """添加控件；父级是 CanvasPanel 时才写 canvas 布局。"""
        parent_name = parent or self.root
        res = json.loads(helper.umg_add_widget(self.bp, wtype, name, parent_name))
        if not res.get("success"):
            errors.append("add %s/%s: %s" % (self.name, name, res))
            return None
        widget = self.find(name)
        try:
            on_canvas = widget is not None and isinstance(widget.slot, unreal.CanvasPanelSlot)
        except Exception:  # noqa: BLE001
            on_canvas = False
        if on_canvas:
            if fill:
                helper.umg_set_slot_layout(self.bp, name, 0.0, 0.0, 1.0, 1.0,
                                           0.0, 0.0, 0.0, 0.0)
            elif pos is not None:
                helper.umg_set_slot_layout(self.bp, name, 0.0, 0.0, 0.0, 0.0,
                                           float(pos[0]), float(pos[1]),
                                           float(size[0]), float(size[1]))
        self.hcenter(name)
        return widget

    def center_on_root(self, name, size):
        """按 1920x1080 水平居中放置。"""
        w = self.find(name)
        if not w:
            return
        try:
            w.slot.set_position(unreal.Vector2D((1920.0 - size[0]) / 2.0, 0.0))
        except Exception:  # noqa: BLE001
            pass

    def hcenter(self, name):
        w = self.find(name)
        if not w:
            return
        try:
            slot = w.slot
        except Exception:  # noqa: BLE001
            return
        if slot is None:
            return
        try:
            if isinstance(slot, unreal.CanvasPanelSlot):
                # 保持左上锚点，只把对齐放回 (0,0)，Designer 里按左上角摆
                slot.set_alignment(unreal.Vector2D(0.0, 0.0))
            else:
                slot.set_editor_property("horizontal_alignment",
                                         unreal.HorizontalAlignment.H_ALIGN_CENTER)
                slot.set_editor_property("vertical_alignment",
                                         unreal.VerticalAlignment.V_ALIGN_CENTER)
        except Exception as exc:  # noqa: BLE001
            log.append("align %s/%s failed: %r" % (self.name, name, exc))

    def find(self, name):
        return helper.umg_find_widget(self.bp, name)

    def set_brush(self, name, tex_path, size=None, uv=None):
        w = self.find(name)
        if not w:
            errors.append("no widget %s/%s" % (self.name, name))
            return
        try:
            b = w.get_editor_property("brush")
            w.set_editor_property("brush", paint_brush(b, tex_path, size, uv))
        except Exception as exc:  # noqa: BLE001
            errors.append("brush %s/%s: %r" % (self.name, name, exc))

    def tint(self, name, rgba):
        w = self.find(name)
        if w:
            try:
                w.set_editor_property("color_and_opacity", linear_color(rgba))
            except Exception as exc:  # noqa: BLE001
                errors.append("tint %s/%s: %r" % (self.name, name, exc))

    def button_art(self, name, tex_path, size=(560, 125)):
        w = self.find(name)
        if not w:
            errors.append("no button %s/%s" % (self.name, name))
            return
        style = w.get_editor_property("widget_style")
        for state in ("normal", "hovered", "pressed", "disabled"):
            try:
                b = style.get_editor_property(state)
                paint_brush(b, tex_path)
                style.set_editor_property(state, b)
            except Exception as exc:  # noqa: BLE001
                errors.append("btn style %s/%s/%s: %r" % (self.name, name, state, exc))
        try:
            w.set_editor_property("widget_style", style)
        except Exception as exc:  # noqa: BLE001
            errors.append("btn style set %s/%s: %r" % (self.name, name, exc))

    def text(self, name, value, size=29, color=(1.0, 0.94, 0.76, 1.0), shadow=True):
        w = self.find(name)
        if not w:
            errors.append("no text %s/%s" % (self.name, name))
            return
        try:
            w.set_editor_property("text", unreal.Text.cast(str(value)))
            f = w.get_editor_property("font")
            f.set_editor_property("size", int(size))
            try:
                f.set_editor_property("typeface_font_name", unreal.Name("Bold"))
            except Exception:  # noqa: BLE001
                pass
            w.set_editor_property("font", f)
            w.set_editor_property("color_and_opacity", slate_color(color))
            w.set_editor_property("justification", unreal.TextJustify.CENTER)
            if shadow:
                w.set_editor_property("shadow_offset", unreal.Vector2D(2.0, 2.0))
                w.set_editor_property("shadow_color_and_opacity",
                                      linear_color((0.2, 0.08, 0.02, 1.0)))
        except Exception as exc:  # noqa: BLE001
            errors.append("text %s/%s: %r" % (self.name, name, exc))

    def save(self):
        try:
            helper.compile_blueprint(self.bp)
        except Exception as exc:  # noqa: BLE001
            errors.append("compile %s: %r" % (self.name, exc))
        eal.save_asset(self.path, only_if_is_dirty=False)


def text_button(s, btn, caption, pos, size=(420, 86), font_size=29,
                bg_art=None, label_art=None):
    s.add("Button", btn, pos=pos, size=size)
    if bg_art:
        s.button_art(btn, bg_art, size)
    txt = btn.replace("Btn_", "Txt_")
    img = btn.replace("Btn_", "Img_")
    if label_art:
        # 贴图标签放在按钮内的 canvas 上：有明确尺寸，按钮移动时标签跟着走
        cv = btn.replace("Btn_", "Canvas_")
        s.add("CanvasPanel", cv, parent=btn)
        s.add("Image", img, parent=cv,
              pos=((size[0] - 400) / 2.0, (size[1] - 90) / 2.0), size=(400, 90))
        s.set_brush(img, label_art, (400, 90))
    else:
        s.add("TextBlock", txt, parent=btn)
        s.text(txt, caption, size=font_size)


def panel(s, panel_pos=(635, 190), panel_size=(650, 700)):
    s.add("Image", "Img_Dim", fill=True)
    s.tint("Img_Dim", (0.0, 0.0, 0.0, 0.68))
    s.add("Image", "Img_Panel", pos=panel_pos, size=panel_size)
    s.set_brush("Img_Panel", ART["frame"], panel_size)
    s.tint("Img_Panel", (1.0, 1.0, 1.0, 0.85))


def build_main():
    s = Screen("WBP_MainMenu")
    if not s.create():
        return
    s.add("Image", "Img_Background", fill=True)
    s.set_brush("Img_Background", ART["bg"], (1920, 1080))
    s.add("Image", "Img_TitlePlaque", pos=(490, 55), size=(940, 430))
    s.set_brush("Img_TitlePlaque", ART["plaque"], (940, 430))
    s.add("TextBlock", "Txt_GameTitle", pos=(560, 268), size=(800, 145))
    s.text("Txt_GameTitle", "烹！膨！嘭！", size=74, color=(1.0, 0.90, 0.64, 1.0))
    text_button(s, "Btn_Start", "开始游戏", (680, 500), (560, 125), 29,
                ART["button"], ART["label_start"])
    text_button(s, "Btn_Settings", "设置", (680, 635), (560, 125), 29,
                ART["button"], ART["label_settings"])
    text_button(s, "Btn_Quit", "退出游戏", (680, 770), (560, 125), 29,
                ART["button"], ART["label_quit"])
    s.save()


def build_pause():
    s = Screen("WBP_PauseMenu")
    if not s.create():
        return
    panel(s)
    s.add("TextBlock", "Txt_Title", pos=(635, 205), size=(650, 60))
    s.text("Txt_Title", "休息一下", size=44, color=(1.0, 0.88, 0.55, 1.0))
    text_button(s, "Btn_Resume", "继续游戏", (750, 315))
    text_button(s, "Btn_Restart", "重新开始", (750, 411))
    text_button(s, "Btn_Settings", "设置", (750, 507))
    text_button(s, "Btn_MainMenu", "返回主菜单", (750, 603))
    s.save()


def build_settings():
    s = Screen("WBP_SettingsMenu")
    if not s.create():
        return
    panel(s)
    s.add("TextBlock", "Txt_Title", pos=(635, 205), size=(650, 60))
    s.text("Txt_Title", "设置", size=44, color=(1.0, 0.88, 0.55, 1.0))
    rows = [
        ("Master", "总音量", 1.0, 1.0),
        ("Environment", "环境音效", 1.0, 1.0),
        ("Effects", "操作和提示音效（最高200%）", 1.0, 0.5),
        ("Music", "背景音乐", 1.0, 0.7),
    ]
    y = 300
    for key, label, max_value, value in rows:
        s.add("TextBlock", "Txt_%s" % key, pos=(745, y), size=(430, 30))
        s.text("Txt_%s" % key, label, size=24, color=(1.0, 0.90, 0.70, 1.0), shadow=False)
        s.add("Slider", "Slider_%s" % key, pos=(745, y + 36), size=(430, 20))
        slider = s.find("Slider_%s" % key)
        if slider:
            try:
                slider.set_editor_property("min_value", 0.0)
                slider.set_editor_property("max_value", float(max_value))
                slider.set_editor_property("value", float(value))
            except Exception as exc:  # noqa: BLE001
                errors.append("slider %s: %r" % (key, exc))
        y += 88
    text_button(s, "Btn_Fullscreen", "切换全屏 / 窗口", (750, 660))
    text_button(s, "Btn_Back", "返回", (750, 756))
    s.save()


def build_confirm():
    s = Screen("WBP_ConfirmDialog")
    if not s.create():
        return
    panel(s)
    s.add("TextBlock", "Txt_Title", pos=(635, 235), size=(650, 70))
    s.text("Txt_Title", "确定离开当前进度？", size=40, color=(1.0, 0.88, 0.55, 1.0))
    text_button(s, "Btn_Confirm", "确定", (750, 430))
    text_button(s, "Btn_Cancel", "取消", (750, 526))
    s.save()


def build_ending():
    s = Screen("WBP_EndingMenu")
    if not s.create():
        return
    panel(s)
    s.add("TextBlock", "Txt_Title", pos=(635, 235), size=(650, 70))
    s.text("Txt_Title", "料理完成！", size=44, color=(1.0, 0.88, 0.55, 1.0))
    text_button(s, "Btn_Again", "再来一次", (750, 430))
    text_button(s, "Btn_MainMenu", "返回主菜单", (750, 526))
    s.save()


def main():
    if not eal.does_directory_exist(MENU_DIR):
        eal.make_directory(MENU_DIR)
    for fn in (build_main, build_pause, build_settings, build_confirm, build_ending):
        try:
            fn()
        except Exception:  # noqa: BLE001
            errors.append("%s:\n%s" % (fn.__name__, traceback.format_exc()))

    out = {"errors": errors, "log": log}
    path = os.path.join(unreal.Paths.project_saved_dir(), "build_menu_widgets.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    unreal.log("[build_menu_widgets] %d errors, wrote %s" % (len(errors), path))


main()
