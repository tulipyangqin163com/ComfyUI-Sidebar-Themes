# ComfyUI-Sidebar-Themes

给 ComfyUI 前端注册 **9 套自定义配色方案**（4 浅 5 深，全部通过 WCAG AA 对比度校验）。纯前端插件，无节点、无后端、无依赖。

**安装即用**：整个文件夹放进 `ComfyUI/custom_nodes/`，重启 ComfyUI，浏览器 `Ctrl+F5`。

```
ComfyUI-Sidebar-Themes/
├── __init__.py             仅声明 WEB_DIRECTORY（纯前端补丁节点，不定义任何节点）
├── pyproject.toml          Comfy Registry 发布元数据
├── js/pg_sidebar_themes.js    前端脚本（运行时注入，由生成器产出）
├── gen_palette_patch.py    生成器：从前端 bundle 抽内置配色，产出上面的 js（开发用）
├── check_contrast.py       WCAG 对比度校验（开发用）
└── README.md
```

运行时只用到 `__init__.py`、`js/pg_sidebar_themes.js`、`pyproject.toml`。

## 主题列表

| 浅色 | 深色 |
| --- | --- |
| 画廊浅色 gallery_light | 午夜蓝 midnight_blue |
| 云端白 cloud_white | 松林绿 forest_pine |
| 暖阳奶油 cream_amber | 暗紫夜 violet_night |
| 薄荷浅绿 sage_mint | 石墨灰 graphite / 赛博霓虹 cyber_neon |

安装后：设置 → 主题 → 列表底部多出这 9 套。主题持久化走 ComfyUI 设置本身，不会丢。

## 附带修复

- **画廊浅色专属**：侧边栏文字改主题蓝 `#3d67c9`（白底 5.3:1、页底 4.6:1，过 WCAG AA 正文线）
- **工作流标签**：浅色主题下「未保存圆点 / 关闭 ×」原写死 `#8a8a8a`（白底约 3:1 几乎隐形），改为跟随主题文字色

## 为什么不会被覆盖丢掉

直接改 `comfy.settings.json` 会被前端/服务端整体写回覆盖。本插件在页面运行时通过
`app.ui.settings` 官方通道把配色合并进 `Comfy.CustomColorPalettes`，由前端自己持久化——
服务端后续写回也会带上它，永不丢失；不改 ComfyUI 本体，升级免疫。

## 改配色（开发）

1. 编辑 `gen_palette_patch.py` 顶部的 `THEMES` 表（浅色以内置 `light` 为底，深色以 `dark` 为底）
2. 重新生成：`python gen_palette_patch.py`（自动同步到 custom_nodes 运行副本）
3. 必跑：`python check_contrast.py`（17 项文字/背景配对，WCAG AA：正文 ≥4.5、次要 ≥3.0）
4. 浏览器 Ctrl+F5

前端大版本升级后（bundle 文件名变了），改脚本顶部的 `BUNDLE` 路径重跑即可。

## 姊妹插件

**ComfyUI-Sidebar-Wallpaper**（侧边栏壁纸：上传 / 遮挡 / 位置调整 / 服务端持久化）。
两者完全独立、互不依赖，可单独安装任意一个。

## 卸载

删掉 `custom_nodes/ComfyUI-Sidebar-Themes` 文件夹并重启即可；主题会随 ComfyUI 设置保留（可在设置里手动改回 Light）。
