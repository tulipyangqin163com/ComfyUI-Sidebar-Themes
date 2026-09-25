# -*- coding: utf-8 -*-
"""校验各主题的文字对比度（WCAG 2.1）。

用法：python check_contrast.py
规则（AA）：正文 ≥ 4.5:1；次要 / 大号文字 ≥ 3:1。
带透明度的背景（如 rgba(...) 菜单）会先与该主题的 bg-color 合成再计算。
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gen_palette_patch import THEMES  # noqa: E402


def parse_color(c):
    c = str(c).strip()
    m = re.match(r'rgba?\(([^)]+)\)', c)
    if m:
        parts = [p.strip() for p in m.group(1).split(',')]
        r, g, b = (int(float(p)) for p in parts[:3])
        a = float(parts[3]) if len(parts) > 3 else 1.0
        return (r, g, b, a)
    if c.startswith('#'):
        h = c[1:]
        if len(h) == 3:
            h = ''.join(ch * 2 for ch in h)
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 1.0)
    raise ValueError('无法解析颜色: %r' % c)


def over(fg, bg):
    """fg（可带 alpha）合成到不透明 bg 上"""
    r, g, b, a = fg
    br, bg_, bb = bg[:3]
    return (round(r * a + br * (1 - a)),
            round(g * a + bg_ * (1 - a)),
            round(b * a + bb * (1 - a)))


def lum(rgb):
    def ch(v):
        v /= 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(text_c, bg_c, page_bg):
    bg = over(parse_color(bg_c), parse_color(page_bg)[:3]) if parse_color(bg_c)[3] < 1 else parse_color(bg_c)[:3]
    fg = over(parse_color(text_c), bg)
    l1, l2 = lum(fg), lum(bg)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


# (标签, 文字键, 背景键, 最低对比度)
CHECKS = [
    ('正文/页面底', ('comfy_base', 'fg-color'), ('comfy_base', 'bg-color'), 4.5),
    ('正文/菜单底', ('comfy_base', 'fg-color'), ('comfy_base', 'comfy-menu-bg'), 4.5),
    ('正文/次级底', ('comfy_base', 'fg-color'), ('comfy_base', 'comfy-menu-secondary-bg'), 4.5),
    ('正文/表格偶', ('comfy_base', 'fg-color'), ('comfy_base', 'tr-even-bg-color'), 4.5),
    ('正文/表格奇', ('comfy_base', 'fg-color'), ('comfy_base', 'tr-odd-bg-color'), 4.5),
    ('输入文字/输入框', ('comfy_base', 'input-text'), ('comfy_base', 'comfy-input-bg'), 4.5),
    ('次要文字/菜单底', ('comfy_base', 'descrip-text'), ('comfy_base', 'comfy-menu-bg'), 4.5),
    ('次要文字/次级底', ('comfy_base', 'descrip-text'), ('comfy_base', 'comfy-menu-secondary-bg'), 4.5),
    ('拖拽提示/页面底', ('comfy_base', 'drag-text'), ('comfy_base', 'bg-color'), 3.0),
    ('错误文字/菜单底', ('comfy_base', 'error-text'), ('comfy_base', 'comfy-menu-bg'), 3.0),
    ('内容文字/内容底', ('comfy_base', 'content-fg'), ('comfy_base', 'content-bg'), 4.5),
    ('内容悬停/悬停底', ('comfy_base', 'content-hover-fg'), ('comfy_base', 'content-hover-bg'), 4.5),
    ('节点标题/标题栏', ('litegraph_base', 'NODE_TITLE_COLOR'), ('litegraph_base', 'NODE_DEFAULT_BGCOLOR'), 4.5),
    ('选中标题/标题栏', ('litegraph_base', 'NODE_SELECTED_TITLE_COLOR'), ('litegraph_base', 'NODE_DEFAULT_BGCOLOR'), 3.0),
    ('节点正文/节点底', ('litegraph_base', 'NODE_TEXT_COLOR'), ('litegraph_base', 'NODE_DEFAULT_COLOR'), 4.5),
    ('控件文字/控件底', ('litegraph_base', 'WIDGET_TEXT_COLOR'), ('litegraph_base', 'WIDGET_BGCOLOR'), 4.5),
    ('控件次要/控件底', ('litegraph_base', 'WIDGET_SECONDARY_TEXT_COLOR'), ('litegraph_base', 'WIDGET_BGCOLOR'), 3.0),
]


def main():
    bad_total = 0
    for t in THEMES:
        page_bg = t['comfy_base']['bg-color']
        rows = []
        bad = 0
        for label, (tg, tk), (bg_g, bk), need in CHECKS:
            txt = t[tg][tk]
            bg = t[bg_g][bk]
            try:
                r = ratio(txt, bg, page_bg)
            except Exception as e:
                rows.append('   ? %s: %s' % (label, e))
                continue
            ok = r >= need
            if not ok:
                bad += 1
            rows.append('   %s %-16s %5.2f:1 (需 %.1f)  %s on %s' % (
                '√' if ok else '×', label, r, need, txt, bg))
        flag = 'OK' if bad == 0 else ('不达标 %d 项' % bad)
        print('【%s】%s  (%s)' % (t['name'], flag, '浅色' if t['light_theme'] else '深色'))
        if bad:
            print('\n'.join(rows))
        bad_total += bad
    print('\n合计不达标:', bad_total, '项')


if __name__ == '__main__':
    main()
