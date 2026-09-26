# -*- coding: utf-8 -*-
"""生成两份独立前端脚本（主题 / 壁纸已拆成两个独立插件）：

    js/pg_theme_patch.js   → ComfyUI-Sidebar-Themes  插件：9 套主题运行时注册
    js/pg_wallpaper.js     → ComfyUI-Sidebar-Wallpaper 插件：壁纸 + 位置调整 + 服务端持久化

背景：直接改 comfy.settings.json 会被 ComfyUI 前端/服务端整体写回覆盖（只要改的时机
撞上运行中的实例就会丢）。改用升级免疫方式：独立补丁 JS 在页面里运行时，
通过 app.ui.settings 正规通道把主题合并进 Comfy.CustomColorPalettes，
由前端自己持久化 → 服务端后续写回也会带上它，永不丢失。

配色来源：前端 bundle 内置 light / dark 方案原样克隆（node_slot 不动画面接线颜色），
再按 THEMES 里的配色表覆盖 comfy_base（界面）+ litegraph_base（画布与节点）。
调色板 schema: {id, name, colors, light_theme?}，light_theme 决定 Vue 界面按浅色渲染。

用法：python gen_palette_patch.py
输出：本目录 js/ 下两份 js，并同步到 custom_nodes 运行副本（若存在）。
"""
import json
import re
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BUNDLE = Path(r'D:/Comfyui/FUXIAO/python/Lib/site-packages/comfyui_frontend_package/static/assets/settingStore-DDHzGrHr.js')
HERE = Path(__file__).resolve().parent
REPO_THEME_JS = HERE / 'js' / 'pg_sidebar_themes.js'
REPO_WALL_JS = HERE / 'js' / 'pg_wallpaper.js'
# 运行时同步目标（插件已在 custom_nodes 里时顺手更新；不存在就跳过）
THEME_SYNC = [
    Path(r'D:/Comfyui/FUXIAO/ComfyUI/custom_nodes/ComfyUI-Sidebar-Themes/js/pg_sidebar_themes.js'),
]
WALL_SYNC = [
    Path(r'D:/Comfyui/FUXIAO/ComfyUI/custom_nodes/ComfyUI-Sidebar-Wallpaper/js/pg_wallpaper.js'),
    Path(r'D:/Comfyui/FUXIAO/MyNodes/ComfyUI-Sidebar-Wallpaper/js/pg_wallpaper.js'),
]

# ───────────────── 主题配色表 ─────────────────
# base: 'light' | 'dark' → 以内置方案为底，未覆盖的字段沿用默认值
# comfy_base: 界面（菜单 / 面板 / 输入框 / 文字）
# litegraph_base: 画布与节点（标题、边框、控件、连线）


def comfy(fg, bg, menu, menu_hover, menu2, input_bg, input_text, descrip, drag,
          error, border, tr_even, tr_odd, content_bg, content_fg, content_hover,
          content_hover_fg, bar_shadow):
    return {
        'fg-color': fg, 'bg-color': bg, 'comfy-menu-bg': menu,
        'comfy-menu-hover-bg': menu_hover, 'comfy-menu-secondary-bg': menu2,
        'comfy-input-bg': input_bg, 'input-text': input_text,
        'descrip-text': descrip, 'drag-text': drag, 'error-text': error,
        'border-color': border, 'tr-even-bg-color': tr_even, 'tr-odd-bg-color': tr_odd,
        'content-bg': content_bg, 'content-fg': content_fg,
        'content-hover-bg': content_hover, 'content-hover-fg': content_hover_fg,
        'bar-shadow': bar_shadow,
    }


def litegraph(clear, title, sel_title, text, node_bg, node_title_bg, outline,
              widget_bg, widget_outline, widget_text, widget_second, link,
              box=None, disabled=None, badge_bg=None):
    d = {
        'CLEAR_BACKGROUND_COLOR': clear,
        'NODE_TITLE_COLOR': title,
        'NODE_SELECTED_TITLE_COLOR': sel_title,
        'NODE_TEXT_COLOR': text,
        'NODE_DEFAULT_COLOR': node_bg,          # 节点主体
        'NODE_DEFAULT_BGCOLOR': node_title_bg,  # 节点标题栏
        'NODE_BOX_OUTLINE_COLOR': outline,      # 选中框
        'WIDGET_BGCOLOR': widget_bg,
        'WIDGET_OUTLINE_COLOR': widget_outline,
        'WIDGET_TEXT_COLOR': widget_text,
        'WIDGET_SECONDARY_TEXT_COLOR': widget_second,
        'LINK_COLOR': link,
    }
    if box:
        d['NODE_DEFAULT_BOXCOLOR'] = box
    if disabled:
        d['WIDGET_DISABLED_TEXT_COLOR'] = disabled
    if badge_bg:
        d['BADGE_BG_COLOR'] = badge_bg
    return d


THEMES = [
    # ── 浅色 ──
    {
        'id': 'gallery_light', 'name': '画廊浅色', 'base': 'light', 'light_theme': True,
        'comfy_base': comfy(
            fg='#1f2733', bg='#eef0f4', menu='#ffffff', menu_hover='#e8edf6',
            menu2='#f7f8fa', input_bg='#ffffff', input_text='#1f2733',
            descrip='#6b7280', drag='#4b5563', error='#dc2626', border='#d8dee8',
            tr_even='#f7f8fa', tr_odd='#ffffff', content_bg='#ffffff', content_fg='#1f2733',
            content_hover='#e8edf6', content_hover_fg='#1f2733',
            bar_shadow='rgba(15, 23, 42, 0.18) 0 0 0.5rem'),
        'litegraph_base': litegraph(
            clear='#eef0f4', title='#2f3a4a', sel_title='#3b6ad3', text='#4b5563',
            node_bg='#ffffff', node_title_bg='#e6ebf5', outline='#3b6ad3',
            widget_bg='#ffffff', widget_outline='#d8dee8', widget_text='#1f2733',
            widget_second='#6b7280', link='#8aa7d6', box='#c9d3e6', disabled='#a3adbb',
            badge_bg='#e6ebf5'),
    },
    {
        'id': 'cloud_white', 'name': '云端白', 'base': 'light', 'light_theme': True,
        'comfy_base': comfy(
            fg='#1b2733', bg='#f4f7fb', menu='#ffffff', menu_hover='#eaf1fa',
            menu2='#f8fafc', input_bg='#ffffff', input_text='#1b2733',
            descrip='#64748b', drag='#475569', error='#dc2626', border='#e2e8f0',
            tr_even='#f8fafc', tr_odd='#ffffff', content_bg='#ffffff', content_fg='#1b2733',
            content_hover='#eaf1fa', content_hover_fg='#0f172a',
            bar_shadow='rgba(15, 23, 42, 0.10) 0 0 0.5rem'),
        'litegraph_base': litegraph(
            clear='#f4f7fb', title='#334155', sel_title='#2563eb', text='#475569',
            node_bg='#ffffff', node_title_bg='#eaf1fa', outline='#2563eb',
            widget_bg='#ffffff', widget_outline='#e2e8f0', widget_text='#1b2733',
            widget_second='#64748b', link='#93b4df', box='#cfdcec', disabled='#9aa8bb',
            badge_bg='#eaf1fa'),
    },
    {
        'id': 'cream_amber', 'name': '暖阳奶油', 'base': 'light', 'light_theme': True,
        'comfy_base': comfy(
            fg='#3a3229', bg='#f7f2e9', menu='#fffdf7', menu_hover='#f4ead9',
            menu2='#fbf6ee', input_bg='#ffffff', input_text='#3a3229',
            descrip='#6f6152', drag='#6b5b45', error='#c0392b', border='#e8dcc7',
            tr_even='#fbf6ee', tr_odd='#fffdf7', content_bg='#fffdf7', content_fg='#3a3229',
            content_hover='#f4ead9', content_hover_fg='#2b2419',
            bar_shadow='rgba(60, 45, 25, 0.18) 0 0 0.5rem'),
        'litegraph_base': litegraph(
            clear='#f7f2e9', title='#5b4a35', sel_title='#b45309', text='#6b5b45',
            node_bg='#fffdf7', node_title_bg='#f4ead9', outline='#b45309',
            widget_bg='#ffffff', widget_outline='#e8dcc7', widget_text='#3a3229',
            widget_second='#8a7a63', link='#c9a97a', box='#e0d2b8', disabled='#b3a68f',
            badge_bg='#f4ead9'),
    },
    {
        'id': 'sage_mint', 'name': '薄荷浅绿', 'base': 'light', 'light_theme': True,
        'comfy_base': comfy(
            fg='#21332a', bg='#eef4f0', menu='#ffffff', menu_hover='#e3f0e8',
            menu2='#f6faf7', input_bg='#ffffff', input_text='#21332a',
            descrip='#50705e', drag='#41584b', error='#d1453b', border='#d5e3d9',
            tr_even='#f6faf7', tr_odd='#ffffff', content_bg='#ffffff', content_fg='#21332a',
            content_hover='#e3f0e8', content_hover_fg='#16261d',
            bar_shadow='rgba(20, 45, 32, 0.16) 0 0 0.5rem'),
        'litegraph_base': litegraph(
            clear='#eef4f0', title='#33513f', sel_title='#2f8f5b', text='#4a6355',
            node_bg='#ffffff', node_title_bg='#e3f0e8', outline='#2f8f5b',
            widget_bg='#ffffff', widget_outline='#d5e3d9', widget_text='#21332a',
            widget_second='#5f7a6a', link='#84b79b', box='#c6dcd0', disabled='#9bb3a5',
            badge_bg='#e3f0e8'),
    },
    # ── 深色 ──
    {
        'id': 'midnight_blue', 'name': '午夜蓝', 'base': 'dark', 'light_theme': False,
        'comfy_base': comfy(
            fg='#e6edf7', bg='#0f1520', menu='rgba(17, 24, 36, .92)', menu_hover='#1b2637',
            menu2='#16202e', input_bg='#16202e', input_text='#dbe4f0',
            descrip='#93a2b8', drag='#b9c6d8', error='#ff6b6b', border='#26344a',
            tr_even='#16202e', tr_odd='#1b2637', content_bg='#22304a', content_fg='#e6edf7',
            content_hover='#1b2637', content_hover_fg='#ffffff',
            bar_shadow='rgba(2, 6, 14, 0.6) 0 0 0.5rem'),
        'litegraph_base': litegraph(
            clear='#0f1520', title='#a9bcd6', sel_title='#5b9bff', text='#c3d0e2',
            node_bg='#16202e', node_title_bg='#1e2b3f', outline='#5b9bff',
            widget_bg='#131c29', widget_outline='#2a3a52', widget_text='#dbe4f0',
            widget_second='#93a2b8', link='#6d8cc4', box='#3a4c68', disabled='#5c6b80',
            badge_bg='#0f1b2e'),
    },
    {
        'id': 'forest_pine', 'name': '松林绿', 'base': 'dark', 'light_theme': False,
        'comfy_base': comfy(
            fg='#e2f0e6', bg='#101914', menu='rgba(16, 26, 20, .92)', menu_hover='#1a2a20',
            menu2='#16231b', input_bg='#16231b', input_text='#d6e8dc',
            descrip='#92ab99', drag='#b6cdbf', error='#ff7b6b', border='#24382b',
            tr_even='#16231b', tr_odd='#1a2a20', content_bg='#213528', content_fg='#e2f0e6',
            content_hover='#1a2a20', content_hover_fg='#ffffff',
            bar_shadow='rgba(2, 12, 6, 0.6) 0 0 0.5rem'),
        'litegraph_base': litegraph(
            clear='#101914', title='#a6c1ad', sel_title='#4ea87a', text='#c1d8c8',
            node_bg='#16231b', node_title_bg='#1e2d23', outline='#4ea87a',
            widget_bg='#131f18', widget_outline='#273a2d', widget_text='#d6e8dc',
            widget_second='#92ab99', link='#6ea283', box='#375043', disabled='#5d7266',
            badge_bg='#0f1f15'),
    },
    {
        'id': 'violet_night', 'name': '暗紫夜', 'base': 'dark', 'light_theme': False,
        'comfy_base': comfy(
            fg='#ece6f7', bg='#14101d', menu='rgba(22, 17, 32, .92)', menu_hover='#241c36',
            menu2='#1d1730', input_bg='#1d1730', input_text='#ded6f0',
            descrip='#a396bd', drag='#c6b8de', error='#ff6f8b', border='#2e2542',
            tr_even='#1d1730', tr_odd='#241c36', content_bg='#31264a', content_fg='#ece6f7',
            content_hover='#241c36', content_hover_fg='#ffffff',
            bar_shadow='rgba(8, 4, 16, 0.6) 0 0 0.5rem'),
        'litegraph_base': litegraph(
            clear='#14101d', title='#b9a9d6', sel_title='#a97bff', text='#cfc3e6',
            node_bg='#1d1730', node_title_bg='#271f3d', outline='#a97bff',
            widget_bg='#191327', widget_outline='#33284c', widget_text='#ded6f0',
            widget_second='#a396bd', link='#8f7cc0', box='#463a63', disabled='#6d5f87',
            badge_bg='#170f26'),
    },
    {
        'id': 'graphite', 'name': '石墨灰', 'base': 'dark', 'light_theme': False,
        'comfy_base': comfy(
            fg='#e8e8ea', bg='#161616', menu='rgba(24, 24, 26, .92)', menu_hover='#262629',
            menu2='#1d1d20', input_bg='#1d1d20', input_text='#dcdce0',
            descrip='#9a9aa2', drag='#c2c2c8', error='#ff5f56', border='#33333a',
            tr_even='#1d1d20', tr_odd='#262629', content_bg='#33333a', content_fg='#e8e8ea',
            content_hover='#262629', content_hover_fg='#ffffff',
            bar_shadow='rgba(0, 0, 0, 0.55) 0 0 0.5rem'),
        'litegraph_base': litegraph(
            clear='#161616', title='#b4b4ba', sel_title='#d8d8de', text='#c4c4ca',
            node_bg='#1d1d20', node_title_bg='#27272b', outline='#d8d8de',
            widget_bg='#191919', widget_outline='#35353b', widget_text='#dcdce0',
            widget_second='#9a9aa2', link='#8b8b92', box='#43434a', disabled='#61616a',
            badge_bg='#111114'),
    },
    {
        'id': 'cyber_neon', 'name': '赛博霓虹', 'base': 'dark', 'light_theme': False,
        'comfy_base': comfy(
            fg='#d9f6ff', bg='#0b0f14', menu='rgba(12, 17, 24, .92)', menu_hover='#16222e',
            menu2='#121a22', input_bg='#121a22', input_text='#cfeaf5',
            descrip='#7fa6b8', drag='#a8d8e8', error='#ff5c8a', border='#1e2b36',
            tr_even='#121a22', tr_odd='#16222e', content_bg='#1b2b38', content_fg='#d9f6ff',
            content_hover='#16222e', content_hover_fg='#ffffff',
            bar_shadow='rgba(0, 0, 0, 0.65) 0 0 0.5rem'),
        'litegraph_base': litegraph(
            clear='#0b0f14', title='#7fe3ff', sel_title='#ff4fd8', text='#a9d6e6',
            node_bg='#121a22', node_title_bg='#182a37', outline='#00e5ff',
            widget_bg='#0f1620', widget_outline='#223744', widget_text='#cfeaf5',
            widget_second='#7fa6b8', link='#00e5ff', box='#2b4a5c', disabled='#4f6c7c',
            badge_bg='#081520'),
    },
]

THEME_JS_TEMPLATE = r'''/** pg_sidebar_themes.js — 运行时注册 9 套 ComfyUI 前端自定义配色方案（独立插件）
 * 升级免疫：不改前端源码，通过 app.ui.settings 正规通道合并进
 * Comfy.CustomColorPalettes，由前端持久化 → 不会再被服务端写回覆盖。
 * 由 gen_palette_patch.py 生成（配色以前端内置 light / dark 方案为底）。
 * 壁纸功能在 ComfyUI-Sidebar-Wallpaper 插件（js/pg_wallpaper.js），互不依赖。
 */
(function () {
  'use strict';
  if (window.__pgThemesLoaded) return;
  window.__pgThemesLoaded = true;

  var PALETTES = __PALETTES__;

  function log() {
    try { console.info.apply(console, ['[pg_theme]'].concat([].slice.call(arguments))); } catch (e) {}
  }
  log('pg_theme v20260926j 已加载（9 套主题运行时注册）');
  function needUpdate(cur) {
    for (var i = 0; i < PALETTES.length; i++) {
      var p = PALETTES[i];
      var mine = cur[p.id];
      if (!mine || mine.name !== p.name || mine.light_theme !== p.light_theme) return true;
    }
    return false;
  }

  function tryRegister() {
    try {
      var s = window.app && window.app.ui && window.app.ui.settings;
      if (!s || typeof s.getSettingValue !== 'function' || typeof s.setSettingValue !== 'function') return false;

      // 设置未加载完成前 getSettingValue 会返回默认值，直接写入会清掉已有自定义主题
      var cur = s.getSettingValue('Comfy.CustomColorPalettes', null);
      if (!cur || typeof cur !== 'object') return 'wait';

      if (!needUpdate(cur)) return 'ok';

      for (var i = 0; i < PALETTES.length; i++) cur[PALETTES[i].id] = PALETTES[i];
      var r = s.setSettingValue('Comfy.CustomColorPalettes', cur);
      if (r && typeof r.then === 'function') {
        r.then(function () {
          log('已注册 ' + PALETTES.length + ' 套主题并持久化');
          // 首次注册后自动刷新一次，让主题菜单立刻出现新方案（sessionStorage 防循环）
          try {
            if (!sessionStorage.getItem('__pgPaletteReloaded')) {
              sessionStorage.setItem('__pgPaletteReloaded', '1');
              location.reload();
            }
          } catch (e) { /* 拿不到 sessionStorage 时忽略 */ }
        }).catch(function (e) { log('持久化失败', e); });
      } else {
        log('已注册 ' + PALETTES.length + ' 套主题');
      }
      return 'ok';
    } catch (e) {
      log('注册异常，重试', e);
      return false;
    }
  }

  var n = 0;
  (function poll() {
    var r = tryRegister();
    if (r === 'ok' || r === true) return;
    if (++n > 300) { log('等待 app.ui.settings 超时，放弃本轮'); return; }
    setTimeout(poll, 200);
  })();

  // ── 画廊浅色专属：侧边栏文字用主题蓝（取自用户参考按钮色 #4975d6，
  //    压深到 #3d67c9 使白底 5.3:1 / 页底 4.6:1，全部过 WCAG AA 正文线）──
  try {
    var st = document.createElement('style');
    st.id = 'pg-palette-style';
    st.textContent =      'html[data-pgpal="gallery_light"] .comfyui-body-left,' +
      'html[data-pgpal="gallery_light"] .comfyui-body-left *{color:#3d67c9 !important}' +
      // 修 ComfyUI 浅色主题下「未保存圆点 / 标签关闭 ×」对比度不足的问题：
      // × 写死 #8a8a8a，白底标签上约 3:1 几乎隐形；这里让它们跟随主题文字色
      'html[data-pgpal] .workflow-tab .close-button{color:var(--fg-color) !important}' +
      'html[data-pgpal] .workflow-tab .close-button:hover{background-color:var(--content-hover-bg) !important}' +
      'html[data-pgpal] .workflow-tab [data-testid="workflow-dirty-indicator"],' +
      'html[data-pgpal] .workflow-tab [data-testid="agent-modified-indicator"]{background-color:var(--fg-color) !important}' +
    document.head.appendChild(st);
    setInterval(function () {
      try {
        var s2 = window.app && window.app.ui && window.app.ui.settings;
        if (!s2 || typeof s2.getSettingValue !== 'function') return;
        var pal = s2.getSettingValue('Comfy.ColorPalette', '');
        var el = document.documentElement;
        if (pal) { el.setAttribute('data-pgpal', pal); } else { el.removeAttribute('data-pgpal'); }
      } catch (e) {}
    }, 800);
  } catch (e) { log('注入侧边栏配色失败', e); }

})();
'''
WALLPAPER_JS_TEMPLATE = r'''/** pg_wallpaper.js — 侧边栏壁纸：上传 / 遮挡 / 位置调整 / 服务端持久化（独立插件）
 * 独立于主题插件：不依赖主题注册表，明暗自适应直接读页面文字颜色亮度（任何主题通用）。
 * 由 gen_palette_patch.py 生成；后端路由在 __init__.py（/pgwallpaper/*）。
 */
(function () {
  'use strict';
  if (window.__pgWallpaperLoaded) return;
  window.__pgWallpaperLoaded = true;

  function log() {
    try { console.info.apply(console, ['[pg_wallpaper]'].concat([].slice.call(arguments))); } catch (e) {}
  }
  log('pg_wallpaper v20260926l 已加载（壁纸 + 位置调整 + 启动重试拉取）');

  // ── 壁纸相关样式：图标栏/面板/内容容器透明透出父容器的图 + 按钮弹窗样式 ──
  try {
    var st = document.createElement('style');
    st.id = 'pg-wallpaper-style';
    st.textContent =      // 侧边栏背景图相关样式（壁纸贴在父容器 .comfyui-body-left 上，
      // 图标栏 nav / 展开面板 / 内容容器全部透明透出父容器的图）
      '.side-tool-bar-container{position:relative}' +
      'html[data-pg-bgimg] .comfyui-body-left nav,' +
      'html[data-pg-bgimg] .comfyui-body-left .sidebar-item-group,' +
      'html[data-pg-bgimg] .comfyui-body-left .side-tool-bar-container.connected-sidebar,' +
      'html[data-pg-bgimg] .side-bar-panel,' +
      'html[data-pg-bgimg] .side-bar-panel .sidebar-content-container,' +
      // 面板内部的头部条/工具条自带 bg-comfy-menu-bg（如节点库的「节点」标题+搜索区），
      // 不透明会把壁纸盖住 → 属性子串匹配同时兜住 bg-comfy-menu-bg 与 bg-[var(--comfy-menu-bg)]
      'html[data-pg-bgimg] .side-bar-panel [class*="comfy-menu-bg"]{background-color:transparent !important}' +
      '.pgbg-btn{position:fixed;z-index:10000;width:28px;height:28px;border-radius:50%;border:1px solid var(--border-color);background:var(--comfy-menu-bg);color:var(--fg-color);opacity:.6;cursor:pointer;display:flex;align-items:center;justify-content:center;padding:0;box-shadow:0 1px 6px rgba(0,0,0,.25)}' +
      '.pgbg-btn:hover{opacity:1}' +
      '.pgbg-pop{position:fixed;z-index:10000;width:230px;background:var(--comfy-menu-bg);color:var(--fg-color);border:1px solid var(--border-color);border-radius:10px;padding:12px;font-size:13px;box-shadow:0 6px 24px rgba(0,0,0,.25)}' +
      '.pgbg-pop h4{margin:0 0 8px;font-size:13px;font-weight:500}' +
      '.pgbg-row{display:flex;align-items:center;gap:8px;margin:8px 0}' +
      '.pgbg-pop .pgbg-act{border:1px solid var(--border-color);background:var(--comfy-input-bg);color:var(--fg-color);border-radius:6px;padding:3px 10px;cursor:pointer;font-size:12px}' +
      '.pgbg-pop .pgbg-act:hover{background:var(--content-hover-bg)}' +
      '.pgbg-pop input[type=range]{flex:1}' +
      '.pgbg-hint{font-size:11px;color:var(--descrip-text);margin-top:6px;line-height:1.5}';
    document.head.appendChild(st);
  } catch (e) { log('注入壁纸样式失败', e); }
  // ── 侧边栏背景图设置：小按钮 + 弹窗（上传图片 / 遮挡强度 / 恢复默认）──
  // 图片经 canvas 压到最长边 1600px 的 JPEG 后存 localStorage；背景上叠一层
  // 与主题明暗自适应的遮罩，保证树文字可读。全部运行时注入，升级免疫。
  try {
    var BG_KEY = 'pg_sidebar_bg_v1';
    var bgCfg = { img: null, alpha: 0.78, posX: 0, posY: 50, iw: 0, ih: 0 };
    try {
      var savedBg = JSON.parse(localStorage.getItem(BG_KEY) || 'null');
      if (savedBg && typeof savedBg === 'object') {
        if (typeof savedBg.img === 'string') bgCfg.img = savedBg.img;
        if (typeof savedBg.alpha === 'number') bgCfg.alpha = savedBg.alpha;
        if (typeof savedBg.posX === 'number') bgCfg.posX = savedBg.posX;
        if (typeof savedBg.posY === 'number') bgCfg.posY = savedBg.posY;
        if (typeof savedBg.iw === 'number') bgCfg.iw = savedBg.iw;
        if (typeof savedBg.ih === 'number') bgCfg.ih = savedBg.ih;
      }
    } catch (e) {}

    // 服务端同步：存在插件后端时壁纸存磁盘（换端口/清缓存都不丢），
    // 后端不存在（仅前端脚本）则纯 localStorage，静默降级
    function bgServerAvailable() { return typeof fetch === 'function'; }
    function bgPush(cfg) {
      if (!bgServerAvailable()) return;
      try {
        fetch('/pgwallpaper/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(cfg)
        }).then(function (r) { return r.ok ? r.json() : null; })
          .then(function (j) {
            // 上传后后端返回稳定 URL，把 localStorage 里的大 dataURL 换成它
            if (j && j.img && bgCfg.img && bgCfg.img.indexOf('data:') === 0) {
              bgCfg.img = j.img;
              try { localStorage.setItem(BG_KEY, JSON.stringify(bgCfg)); } catch (e) {}
              try { applyBg(true); } catch (e) {}
            }
          }).catch(function () {});
      } catch (e) {}
    }
    function saveBg() {
      try { localStorage.setItem(BG_KEY, JSON.stringify(bgCfg)); }
      catch (e) { log('背景图保存失败（可能超出 localStorage 容量）', e); alert('背景图太大保存失败，换一张小一点的图试试'); }
      if (bgCfg.img && bgCfg.img.indexOf('data:') === 0) {
        bgPush({ img: bgCfg.img, alpha: bgCfg.alpha, posX: bgCfg.posX, posY: bgCfg.posY });
      } else {
        bgPush({ alpha: bgCfg.alpha, posX: bgCfg.posX, posY: bgCfg.posY });   // 图已存服务端，只同步遮挡/位置
      }
    }
    // 启动时从服务端拉壁纸配置。曾经只在启动时拉一次，但 ComfyUI 重启后
    // 打开页面的瞬间插件路由可能尚未就绪（或被前端 SPA 兜底路由用 200+HTML
    // 接住，json() 解析失败），失败又被静默吞掉 → 整个会话都没壁纸。
    // 因此改成带重试的轮询：没拉到有效配置就一直每 2s 重试（最多 60 次），
    // 拉到或确认服务端无壁纸（显式 img:null 的 JSON）才停。
    var bgPullTries = 0;
    function bgPull() {
      if (!bgServerAvailable() || bgPullTries >= 60) return;
      bgPullTries++;
      try {
        fetch('/pgwallpaper/config')
          .then(function (r) { return r.ok ? r.json() : null; })
          .then(function (j) {
            if (!j) throw new Error('bad response');
            if (!j.img) { bgPullTries = 60; return; }   // 服务端明确无壁纸，停止重试
            bgCfg.img = j.img;
            if (typeof j.alpha === 'number') bgCfg.alpha = j.alpha;
            if (typeof j.posX === 'number') bgCfg.posX = j.posX;
            if (typeof j.posY === 'number') bgCfg.posY = j.posY;
            try { localStorage.setItem(BG_KEY, JSON.stringify(bgCfg)); } catch (e) {}
            try { applyBg(true); } catch (e) {}
            log('从服务端加载壁纸成功（第 ' + bgPullTries + ' 次尝试）');
            bgPullTries = 60;   // 成功后停止重试
          }).catch(function () {
            setTimeout(function () { try { bgPull(); } catch (e) {} }, 2000);
          });
      } catch (e) { setTimeout(function () { try { bgPull(); } catch (e2) {} }, 2000); }
    }
    function isLightTheme() {
      // 独立插件：不读主题注册表，直接看页面文字颜色亮度 ——
      // 浅色主题文字是深色、深色主题文字是浅色，对内置/自定义主题都成立
      try {
        var m = getComputedStyle(document.body).color.match(/(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/);
        if (m) return (0.299 * m[1] + 0.587 * m[2] + 0.114 * m[3]) < 128;
      } catch (e) {}
      return false;   // 量不到按深色处理（ComfyUI 默认深色主题）
    }

    var lastAppliedBg = '', lastCount = -1;
    function findNav() {
      // 不依赖 .comfyui-body-left（不同前端版本该类名可能对不上），
      // 直接找侧栏 nav 元素本身
      return document.querySelector('nav.side-tool-bar-container') ||
             document.querySelector('.side-tool-bar-container');
    }
    function setBgStyle(el, tint, sizeCss) {
      if (tint) {
        el.style.backgroundImage = tint + ',url("' + bgCfg.img + '")';
        // fixed：背景相对视口定位 —— 图标栏与展开面板虽是不同元素，
        // 用同一张图 + fixed 后两块拼起来仍是连续的一张图，无缝
        el.style.backgroundAttachment = 'fixed';
        el.style.backgroundSize = sizeCss || 'cover';
        // 位置百分比相对视口（fixed 附着）：0%=贴左/上，50%=居中，100%=贴右/下。
        // 注意：CSS 规定某方向「无溢出」时该方向百分比被钳住（拖不动），
        // 所以 applyBg 里按图片宽高算了保证双向都溢出的尺寸再传进来
        el.style.backgroundPosition = (Number(bgCfg.posX) || 0) + '% ' + (Number(bgCfg.posY) || 0) + '%';
        el.style.backgroundRepeat = 'no-repeat';
        el.style.backgroundColor = 'transparent';
      } else {
        el.style.backgroundImage = '';
        el.style.backgroundAttachment = '';
        el.style.backgroundSize = '';
        el.style.backgroundPosition = '';
        el.style.backgroundRepeat = '';
        el.style.backgroundColor = '';
      }
    }
    function collectTargets() {
      // 图标栏的父容器 + 所有展开面板都要贴图。
      // 关键事实：展开面板 .side-bar-panel 并不在 .comfyui-body-left 里面
      // （它在主布局的分离器组件里），只贴父容器时面板透出的会是页面底色。
      // 两处都贴 + background-attachment:fixed → 视觉上仍是连续一张图。
      var t = [];
      try {
        var left = document.querySelector('.comfyui-body-left');
        if (left) t.push(left);
      } catch (e) {}
      try {
        var panels = document.querySelectorAll('.side-bar-panel');
        for (var i = 0; i < panels.length; i++) {
          if (t.indexOf(panels[i]) === -1) t.push(panels[i]);
        }
      } catch (e) {}
      if (!t.length) {
        var n = findNav();
        if (n) t.push(n);
      }
      return t;
    }
    function applyBg(force) {
      var nav = findNav();
      var targets = collectTargets();
      // 设置按钮挂在 body 上、fixed 定位，不放进侧栏容器（它自带 overflow-hidden，
      // 收起时 max-width:0 会把内部元素裁没）。按钮永远显示：能量到侧栏就贴在
      // 侧栏右缘，量不到就退到固定位置，保证任何布局下都看得见
      if (!bgBtn && document.body) {
        try { document.body.appendChild(makeBgBtn()); } catch (e) {}
      }
      if (bgBtn && !bgBtn.isConnected && document.body) {
        try { document.body.appendChild(bgBtn); } catch (e) {} // 被外层脚本/Vue 清掉后自动补回
      }
      if (bgBtn) {
        var r = null;
        try { r = nav ? nav.getBoundingClientRect() : null; } catch (e) {}
        bgBtn.style.display = 'flex';
        if (r && r.width >= 20) {
          bgBtn.style.left = Math.max(2, r.right - 14) + 'px';
          bgBtn.style.bottom = '60px';
        } else {
          bgBtn.style.left = '64px';   // 量不到侧栏时的兜底位置（图标栏右侧）
          bgBtn.style.bottom = '130px';
        }
      }
      var vw = 0, vh = 0;
      try { vw = window.innerWidth || 0; vh = window.innerHeight || 0; } catch (e) {}
      var sig = (bgCfg.img ? '1' : '0') + ':' + bgCfg.alpha + ':' + bgCfg.posX + ',' + bgCfg.posY +
                ':' + bgCfg.iw + 'x' + bgCfg.ih + ':' + vw + 'x' + vh + ':' + isLightTheme() + ':' + targets.length;
      if (!force && sig === lastAppliedBg && targets.length === lastCount) return;
      lastAppliedBg = sig; lastCount = targets.length;
      var root = document.documentElement;
      if (!targets.length || !bgCfg.img) {
        root.removeAttribute('data-pg-bgimg');
        for (var c = 0; c < targets.length; c++) setBgStyle(targets[c], null);
        return;
      }
      root.setAttribute('data-pg-bgimg', '1');
      var ov = isLightTheme() ? '255,255,255' : '12,14,20';
      var a = Math.max(0, Math.min(0.95, Number(bgCfg.alpha) || 0.78));
      var tint = 'linear-gradient(rgba(' + ov + ',' + a + '),rgba(' + ov + ',' + a + '))';
      // ── 关键：算一个「双向都溢出视口」的背景尺寸 ──
      // cover 只保证覆盖：比例恰好匹配视口的方向会刚好铺满（无溢出），
      // 该方向的 position 百分比就被 CSS 钳住 → 滑条「没反应」。
      // 这里在 cover 基础上再放大，保证水平/垂直各留至少 50% 移动余量
      // （余量越大滑条可拖的距离越长；20% 时用户反馈移动幅度太小），
      // 两个位置滑条就都永远有效。不知道图片尺寸时先退回 cover（稍后探测补上）。
      var sizeCss = 'cover', needProbe = false;
      if (bgCfg.iw > 0 && bgCfg.ih > 0 && vw > 0 && vh > 0) {
        var sc = Math.max(vw / bgCfg.iw, vh / bgCfg.ih);   // cover 基准
        var zoom = Math.max(1.5 * vw / (bgCfg.iw * sc), 1.5 * vh / (bgCfg.ih * sc), 1);
        sizeCss = Math.round(bgCfg.iw * sc * zoom) + 'px ' + Math.round(bgCfg.ih * sc * zoom) + 'px';
      } else {
        needProbe = true;
      }
      for (var i = 0; i < targets.length; i++) setBgStyle(targets[i], tint, sizeCss);
      // 探测必须放在应用之后：探测完成的回调会立刻重排，
      // 若放在循环前，同步回调会先算好尺寸又被本次循环的 cover 盖回去
      if (needProbe) probeImg();
    }

    // 图片尺寸探测：服务端 URL / 旧数据没记宽高时，偷偷加载一次读出
    // naturalWidth，写回配置后重排 —— 没有它就没法算「双向溢出」的尺寸。
    // probedSrc 记录探测过的图，防止加载失败后每次交互都重新探测
    var probing = false, probedSrc = '';
    function probeImg() {
      if (probing || probedSrc === bgCfg.img || typeof Image !== 'function') return;
      probedSrc = bgCfg.img;
      probing = true;
      try {
        var im = new Image();
        im.onload = function () {
          probing = false;
          var w = im.naturalWidth || im.width || 0;
          var h = im.naturalHeight || im.height || 0;
          if (w > 0 && h > 0) {
            bgCfg.iw = w; bgCfg.ih = h;
            try { localStorage.setItem(BG_KEY, JSON.stringify(bgCfg)); } catch (e) {}
            try { applyBg(true); } catch (e) {}
          }
        };
        im.onerror = function () { probing = false; };
        im.src = bgCfg.img;
      } catch (e) { probing = false; }
    }

    var bgBtn = null, bgPop = null, bgFile = null;
    function makeBgBtn() {
      if (bgBtn) return bgBtn;
      bgBtn = document.createElement('button');
      bgBtn.type = 'button';
      bgBtn.className = 'pgbg-btn';
      bgBtn.title = '侧边栏背景设置';
      bgBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg>';
      bgBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        if (bgPop && bgPop.style.display === 'block') { closeBgPop(); } else { openBgPop(); }
      });
      return bgBtn;
    }

    function closeBgPop() { if (bgPop) bgPop.style.display = 'none'; }
    function openBgPop() {
      if (!bgPop) buildBgPop();
      var r = bgBtn.getBoundingClientRect();
      bgPop.style.display = 'block';
      var top = Math.max(8, r.top - bgPop.offsetHeight - 8);
      var left = Math.min(r.right + 8, window.innerWidth - bgPop.offsetWidth - 8);
      if (top < 8) top = Math.max(8, r.bottom + 8);
      bgPop.style.top = top + 'px';
      bgPop.style.left = Math.max(8, left) + 'px';
    }

    function buildBgPop() {
      bgPop = document.createElement('div');
      bgPop.className = 'pgbg-pop';
      bgPop.style.display = 'none';
      bgPop.innerHTML =
        '<h4>侧边栏背景</h4>' +
        '<div class="pgbg-row"><button type="button" class="pgbg-act pgbg-upload">上传图片</button>' +
        '<button type="button" class="pgbg-act pgbg-clear">清除壁纸</button></div>' +
        '<div class="pgbg-row">遮挡<input type="range" class="pgbg-alpha" min="0.30" max="0.95" step="0.05"></div>' +
        '<div class="pgbg-row">水平<input type="range" class="pgbg-posx" min="0" max="100" step="1"></div>' +
        '<div class="pgbg-row">垂直<input type="range" class="pgbg-posy" min="0" max="100" step="1"></div>' +
        '<div class="pgbg-row"><button type="button" class="pgbg-act pgbg-center">位置回中</button></div>' +
        '<div class="pgbg-hint">遮挡越大文字越清楚、照片越淡；拖「水平/垂直」把照片想看的部分挪进侧栏；位置会保存，下次打开还在。</div>';
      bgFile = document.createElement('input');
      bgFile.type = 'file';
      bgFile.accept = 'image/*';
      bgFile.style.display = 'none';
      bgPop.appendChild(bgFile);
      document.body.appendChild(bgPop);

      bgPop.querySelector('.pgbg-upload').addEventListener('click', function () { bgFile.click(); });
      bgPop.querySelector('.pgbg-clear').addEventListener('click', function () {
        bgCfg.img = null; saveBg(); applyBg(true); closeBgPop();
      });
      var alphaEl = bgPop.querySelector('.pgbg-alpha');
      alphaEl.value = String(bgCfg.alpha);
      alphaEl.addEventListener('input', function () {
        bgCfg.alpha = Number(alphaEl.value) || 0.78;
        saveBg(); applyBg(true);
      });
      // 位置滑条：实时预览（applyBg(true) 强制刷新，不受去重签名影响）
      var posXEl = bgPop.querySelector('.pgbg-posx');
      var posYEl = bgPop.querySelector('.pgbg-posy');
      posXEl.value = String(Math.round(Number(bgCfg.posX) || 0));
      posYEl.value = String(Math.round(Number(bgCfg.posY) || 0));
      function onPosInput() {
        bgCfg.posX = Math.max(0, Math.min(100, Number(posXEl.value) || 0));
        bgCfg.posY = Math.max(0, Math.min(100, Number(posYEl.value) || 0));
        saveBg(); applyBg(true);
      }
      posXEl.addEventListener('input', onPosInput);
      posYEl.addEventListener('input', onPosInput);
      bgPop.querySelector('.pgbg-center').addEventListener('click', function () {
        bgCfg.posX = 0; bgCfg.posY = 50;   // 与旧版默认一致：贴左、垂直居中
        posXEl.value = '0'; posYEl.value = '50';
        saveBg(); applyBg(true);
      });
      bgFile.addEventListener('change', function () {
        var f = bgFile.files && bgFile.files[0];
        if (!f) return;
        var reader = new FileReader();
        reader.onload = function () {
          var im = new Image();
          im.onload = function () {
            bgCfg.iw = im.width || 0; bgCfg.ih = im.height || 0;   // 记下宽高，供双向溢出计算
            try {
              var max = 1600, s = Math.min(1, max / Math.max(im.width, im.height));
              var cv = document.createElement('canvas');
              cv.width = Math.max(1, Math.round(im.width * s));
              cv.height = Math.max(1, Math.round(im.height * s));
              cv.getContext('2d').drawImage(im, 0, 0, cv.width, cv.height);
              bgCfg.img = cv.toDataURL('image/jpeg', 0.85);
            } catch (e) { bgCfg.img = String(reader.result); }
            saveBg(); applyBg(true); closeBgPop();
          };
          im.onerror = function () { alert('这张图读不出来，换一张试试'); };
          im.src = reader.result;
        };
        reader.readAsDataURL(f);
        bgFile.value = '';
      });
      document.addEventListener('click', function (e) {
        if (bgPop && bgPop.style.display === 'block' && !bgPop.contains(e.target) && e.target !== bgBtn) closeBgPop();
      });
      document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeBgPop(); });
    }

    // 初始化时立即挂一次（否则按钮要等 1.2s 才出现），再靠轮询自愈
    var bgTries = 0;
    (function bgBoot() {
      try { applyBg(true); } catch (e) {}
      if (bgBtn && bgBtn.parentNode) {
        var nv = null; try { nv = findNav(); } catch (e) {}
        log('背景设置按钮已挂载（v20260926j），侧栏容器:', nv ? nv.className : '未找到（按钮在兜底位置 left:64）');
        return;
      }
      if (++bgTries > 120) { log('背景设置按钮挂载失败：等不到 document.body'); return; }
      setTimeout(bgBoot, 1000);
    })();
    setInterval(function () { try { applyBg(false); } catch (e) {} }, 1200);
    bgPull();
  } catch (e) { log('侧边栏背景功能初始化失败', e); }

})();
'''


def extract_braced(src: str, start: int):
    depth = 0
    for i in range(start, len(src)):
        if src[i] == '{':
            depth += 1
        elif src[i] == '}':
            depth -= 1
            if depth == 0:
                return src[start + 1:i], i + 1
    raise ValueError('括号不配对')


def parse_obj(src: str):
    out = {}
    i, n = 0, len(src)
    key_re = re.compile(r'[ \n]*"?([A-Za-z0-9_"\-]+)"?[ \n]*:')
    while i < n:
        m = key_re.match(src, i)
        if not m:
            i += 1
            continue
        key = m.group(1).strip('"')
        j = m.end()
        while j < n and src[j] in ' \n':
            j += 1
        if j >= n:
            break
        if src[j] == '`':
            k = src.index('`', j + 1)
            out[key] = src[j + 1:k]
            i = k + 1
            if i < n and src[i] == ',':
                i += 1
        elif src[j] == '{':
            inner, i = extract_braced(src, j)
            out[key] = parse_obj(inner)
        else:
            k = src.find(',', j)
            if k == -1:
                k = n
            out[key] = src[j:k].strip()
            i = k + 1
    return out


def extract_builtin(pid: str):
    s = BUNDLE.read_text(encoding='utf-8')
    m = re.search(r'id:`%s`,name:`[^`]+`' % pid, s)
    if not m:
        raise RuntimeError('bundle 里找不到内置 %s 方案' % pid)
    seg_start = s.index('colors:{', m.start())
    colors_src, _ = extract_braced(s, seg_start + len('colors:'))
    colors = {}
    key_re = re.compile(r'([a-z_]+):\{')
    i = 0
    while True:
        m2 = key_re.search(colors_src, i)
        if not m2:
            break
        body, end = extract_braced(colors_src, m2.end() - 1)
        colors[m2.group(1)] = parse_obj(body)
        i = end
    return colors


def merge_known(base: dict, override: dict, theme_id: str, valid: set = None):
    """只写入 schema 里合法的键（未知键过不了前端 zod 校验）。

    合法键 = 内置 light / dark 出现过的键的并集：深色底座默认不写
    comfy-menu-hover-bg、interface-panel-* 这些可选键，但 schema 里是允许的。
    """
    allowed = set(base) | (valid or set())
    out = dict(base)
    skipped = [k for k in override if k not in allowed]
    for k in skipped:
        override.pop(k, None)
    if skipped:
        print('  ! %s 忽略未知字段: %s' % (theme_id, ', '.join(skipped)))
    out.update(override)
    return out


def main():
    builtin = {p: extract_builtin(p) for p in ('light', 'dark')}
    print('内置方案:', {k: {g: len(v) for g, v in c.items()} for k, c in builtin.items()})

    # schema 合法键取 light / dark 的并集
    valid_comfy = set(builtin['light']['comfy_base']) | set(builtin['dark']['comfy_base'])
    valid_lite = set(builtin['light']['litegraph_base']) | set(builtin['dark']['litegraph_base'])

    palettes = []
    for t in THEMES:
        base = builtin[t['base']]
        cb = merge_known(base.get('comfy_base', {}), dict(t['comfy_base']), t['id'], valid_comfy)
        lg = merge_known(base.get('litegraph_base', {}), dict(t['litegraph_base']), t['id'], valid_lite)
        palettes.append({
            'id': t['id'],
            'name': t['name'],
            'light_theme': bool(t['light_theme']),
            'colors': {
                'node_slot': base.get('node_slot', {}),
                'litegraph_base': lg,
                'comfy_base': cb,
            },
        })
        print('  ·', t['name'], '(%s)' % t['id'], 'base=%s' % t['base'],
              'comfy=%d lite=%d' % (len(cb), len(lg)))

    theme_js = THEME_JS_TEMPLATE.replace('__PALETTES__', json.dumps(palettes, ensure_ascii=False))
    wall_js = WALLPAPER_JS_TEMPLATE
    REPO_THEME_JS.parent.mkdir(parents=True, exist_ok=True)
    REPO_THEME_JS.write_text(theme_js, encoding='utf-8')
    REPO_WALL_JS.write_text(wall_js, encoding='utf-8')
    print('已生成:', REPO_THEME_JS, '(%d 字符 / %d 套)' % (len(theme_js), len(palettes)))
    print('已生成:', REPO_WALL_JS, '(%d 字符)' % len(wall_js))

    for dst in THEME_SYNC:
        if dst.parent.exists():
            shutil.copy2(REPO_THEME_JS, dst)
            print('已同步:', dst)
    for dst in WALL_SYNC:
        if dst.parent.exists():
            shutil.copy2(REPO_WALL_JS, dst)
            print('已同步:', dst)


if __name__ == '__main__':
    main()
