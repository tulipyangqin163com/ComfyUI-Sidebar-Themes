/** pg_wallpaper.js — 侧边栏壁纸：上传 / 遮挡 / 位置调整 / 服务端持久化（独立插件）
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
