"""ComfyUI-Sidebar-Themes —— 9 套 ComfyUI 前端自定义配色方案（独立插件，纯前端）

功能
    1. 注册 9 套主题（4 浅 5 深），全部通过 WCAG AA 对比度校验（17 项文字/背景配对）
       浅色：画廊浅色 / 云端白 / 暖阳奶油 / 薄荷浅绿
       深色：午夜蓝 / 松林绿 / 暗紫夜 / 石墨灰 / 赛博霓虹
    2. 画廊浅色专属：侧边栏文字用主题蓝（#3d67c9，白底 5.3:1 达标）
    3. 修复浅色主题下工作流标签「未保存圆点 / 关闭 ×」对比度不足看不清的问题

为什么不用「直接改 comfy.settings.json」
    ComfyUI 前端 / 服务端会在运行期间把内存里的设置**整体写回**这个文件，
    只要写入时机撞上运行中的实例，手写的条目就会被静默覆盖掉（实测连续两次）。
    改成运行时注册后，写入走 app.ui.settings 正规通道，由前端自己持久化，
    之后服务端再怎么写回也会带上它 —— 永不丢失。

升级免疫
    不修改 ComfyUI 本体、不修改任何插件源码；只在页面里调用官方设置 API。
    前端包升级后重新跑一次 gen_palette_patch.py 重新提取内置配色即可。

安装
    1. 把整个文件夹复制到 ComfyUI/custom_nodes/ 下
    2. 重启一次 ComfyUI，然后浏览器 Ctrl+F5
    3. 页面会自动刷新一次（首次注册），之后 设置 → 主题 → 列表底部出现 9 套主题

姊妹插件
    ComfyUI-Sidebar-Wallpaper（侧边栏壁纸 + 位置调整），与本插件完全独立、互不依赖。
"""

WEB_DIRECTORY = "./js"

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

__all__ = ["WEB_DIRECTORY", "NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
