"""Generate characters.html - a gallery of every suspect in the pack.

The manifest is inlined rather than fetched: a page opened over file:// cannot
XHR a sibling JSON file in Chrome, so an embedded payload is the only way this
works by double-clicking it. Re-run after any roster change to refresh.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAR = os.path.join(ROOT, "character")
ART = os.path.join(ROOT, "art")
OUT = os.path.join(ROOT, "characters.html")


def skull_stats():
    """Derived landmarks, parsed from the same file the art is generated from."""
    src = open(os.path.join(ART, "roster.lua"), encoding="utf-8").read()
    starts = [(m.start(), m.group(1)) for m in re.finditer(r"n='(\w+)'", src)]
    out = {}
    for i, (pos, name) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(src)
        body = src[pos:end]
        prof = re.search(r"prof=\{(.*?)\}\s*,\s*\n", body, re.S)
        if not prof:
            continue
        pts = [(int(a), float(b)) for a, b in re.findall(r"\{(\d+),\s*([\d.]+)\}", prof.group(1))]
        inside = [(y, w) for y, w in pts if w > 0]
        if not inside:
            continue
        wide = max(inside, key=lambda p: p[1])
        out[name] = {
            "top": min(y for y, _ in pts),
            "wideY": wide[0],
            "wideW": wide[1],
            "faceEnd": max(y for y, _ in pts),
            "chin": next((w for y, w in reversed(pts) if w > 0), 0),
            "hairStyle": (re.search(r"hair_style='(\w+)'", body) or [None, "?"])[1],
            "smooth": (re.search(r"smooth=(\d+)", body) or [None, "?"])[1],
        }
    return out


def main():
    manifest = json.load(open(os.path.join(CHAR, "pack.json"), encoding="utf-8"))
    stats = skull_stats()
    data = []
    for e in manifest["characters"]:
        s = stats.get(e["name"], {})
        data.append({
            "name": e["name"],
            "label": e["name"].capitalize(),
            "primary": e["primary"],
            "palette": e["palette"],
            "slug": e["name"],
            **s,
        })
    data.sort(key=lambda d: d["label"])

    payload = json.dumps(data, ensure_ascii=False)
    css_scale = "1"
    html = TEMPLATE.replace("__DATA__", payload).replace("__COUNT__", str(len(data))) \
                   .replace("__SCALE__", css_scale)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"characters.html written with {len(data)} characters")
    missing = [f"character/{d['slug']}_avatar.png" for d in data
               if not os.path.exists(os.path.join(ROOT, "character", f"{d['slug']}_avatar.png"))]
    if missing:
        print("WARNING missing assets:", missing)
        return 1
    return 0


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Suspects · __COUNT__</title>
<style>
  :root{
    --paper:#F2F0F7; --card:#F8F7FB; --ink:#191922; --muted:#7A7F92;
    --line:rgba(25,25,34,.14);
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--paper);color:var(--ink);
    font:15px/1.5 "Segoe UI",system-ui,-apple-system,"Helvetica Neue",Arial,sans-serif}
  .wrap{max-width:1180px;margin:0 auto;padding:32px 20px 64px}
  header{display:flex;flex-wrap:wrap;align-items:baseline;gap:12px 18px;margin-bottom:6px}
  h1{font-size:30px;margin:0;letter-spacing:-.01em}
  .sub{color:var(--muted);font-size:14px}
  .bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:22px 0 26px}
  input[type=search]{padding:9px 12px;border:2px solid var(--ink);border-radius:0;
    background:#fff;font:inherit;min-width:220px}
  input[type=search]:focus{outline:2px solid var(--muted);outline-offset:1px}
  .seg{display:flex;border:2px solid var(--ink)}
  .seg button{padding:8px 13px;border:0;background:#fff;font:inherit;cursor:pointer;color:var(--ink)}
  .seg button+button{border-left:2px solid var(--ink)}
  .seg button[aria-pressed=true]{background:var(--ink);color:#fff}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(258px,1fr));gap:18px}
  .card{background:var(--card);border:2px solid var(--ink);display:flex;flex-direction:column;
    position:relative;overflow:hidden}
  .accent{height:8px;flex:none}
  .card .body{padding:16px 16px 14px;display:flex;gap:14px;align-items:flex-start}
  .px{image-rendering:pixelated;image-rendering:crisp-edges;background:
    repeating-conic-gradient(rgba(25,25,34,.05) 0% 25%, transparent 0% 50%) 0 0/12px 12px}
  .av{width:128px;height:128px;flex:none}
  .meta{min-width:0;flex:1}
  .nm{font-size:19px;font-weight:650;margin:0 0 2px;word-break:break-word}
  .hex{font:12px/1.4 ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--muted)}
  .tk{width:64px;height:64px;margin-top:10px}
  .row{display:flex;align-items:center;gap:10px}
  .chips{display:flex;flex-wrap:wrap;gap:4px;margin-top:12px}
  .chip{width:22px;height:22px;border:2px solid var(--ink);position:relative;cursor:default}
  .chip[data-tip]:hover::after{content:attr(data-tip);position:absolute;left:50%;bottom:130%;
    transform:translateX(-50%);background:var(--ink);color:#fff;padding:2px 6px;
    font:11px ui-monospace,monospace;white-space:nowrap;z-index:5}
  .stats{border-top:2px solid var(--ink);background:#fff;padding:9px 16px;
    font:11px/1.6 ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--muted);
    display:flex;flex-wrap:wrap;gap:2px 12px}
  .stats b{color:var(--ink);font-weight:600}
  h2{font-size:15px;text-transform:uppercase;letter-spacing:.09em;color:var(--muted);
    margin:44px 0 12px;font-weight:600}
  .strip{display:flex;flex-wrap:wrap;gap:14px;align-items:flex-end;background:var(--card);
    border:2px solid var(--ink);padding:18px}
  .strip figure{margin:0;text-align:center}
  .strip figcaption{font:11px ui-monospace,monospace;color:var(--muted);margin-top:6px}
  .empty{color:var(--muted);padding:40px 0;font-size:15px}
  footer{margin-top:40px;color:var(--muted);font-size:12.5px}
  code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Suspects</h1>
    <span class="sub">__COUNT__ 个角色 · 头像 / 指示物 / 色卡 · 由 <code>art/roster.lua</code> 生成</span>
  </header>

  <div class="bar">
    <input type="search" id="q" placeholder="搜索名字 / 发型 / 主色…" aria-label="搜索">
    <div class="seg" role="group" aria-label="头像缩放">
      <button data-s="1" aria-pressed="false">1×</button>
      <button data-s="2" aria-pressed="true">2×</button>
      <button data-s="4" aria-pressed="false">4×</button>
    </div>
    <span class="sub" id="shown"></span>
  </div>

  <div class="grid" id="grid"></div>
  <p class="empty" id="empty" hidden>没有匹配的角色。</p>

  <h2>实际尺寸检查 · 1×</h2>
  <div class="strip" id="strip1"></div>

  <h2>指示物 · 1×</h2>
  <div class="strip" id="stript"></div>

  <footer>
    主色 = 衣服色，色卡首格与指示物外圈、卡片色条同源（<code>character/pack.json</code>）。
    改完花名册跑 <code>python art/make_character_page.py</code> 重新生成本页。
  </footer>
</div>

<script>
const DATA = __DATA__;
const grid = document.getElementById('grid');
const q = document.getElementById('q');
const shown = document.getElementById('shown');
let scale = 2;

function card(d){
  const el = document.createElement('article');
  el.className = 'card';
  el.dataset.hay = [d.name, d.hairStyle, d.primary, d.smooth].join(' ').toLowerCase();
  const px = 64 * scale;
  el.innerHTML = `
    <div class="accent" style="background:${d.primary}"></div>
    <div class="body">
      <img class="px av" width="${px}" height="${px}" style="width:${px}px;height:${px}px"
           src="character/${d.slug}_avatar.png" alt="${d.label} 头像">
      <div class="meta">
        <p class="nm">${d.label}</p>
        <p class="hex">${d.primary}</p>
        <img class="px tk" src="character/${d.slug}_token.png" width="64" height="64"
             style="width:32px;height:32px" alt="${d.label} 指示物">
        <div class="chips">${d.palette.map(c =>
          `<span class="chip" style="background:${c}" data-tip="${c}"></span>`).join('')}</div>
      </div>
    </div>
    <div class="stats">
      <span>发型 <b>${d.hairStyle || '?'}</b></span>
      <span>最宽 <b>y${d.wideY ?? '?'}</b></span>
      <span>脸长 <b>${d.faceEnd ?? '?'}</b></span>
      <span>下巴 <b>${d.chin ?? '?'}</b></span>
      <span>圆滑 <b>${d.smooth ?? '?'}</b></span>
    </div>`;
  return el;
}

function render(){
  const t = q.value.trim().toLowerCase();
  grid.innerHTML = '';
  let n = 0;
  for (const d of DATA){
    const el = card(d);
    if (t && !el.dataset.hay.includes(t)) continue;
    grid.appendChild(el);
    n++;
  }
  document.getElementById('empty').hidden = n > 0;
  shown.textContent = `显示 ${n} / ${DATA.length}`;
}

function strips(){
  const s1 = document.getElementById('strip1'), st = document.getElementById('stript');
  for (const d of DATA){
    const f1 = document.createElement('figure');
    f1.innerHTML = `<img class="px" src="character/${d.slug}_avatar.png" width="64" height="64"
      alt="${d.label}"><figcaption>${d.label}</figcaption>`;
    s1.appendChild(f1);
    const f2 = document.createElement('figure');
    f2.innerHTML = `<img class="px" src="character/${d.slug}_token.png" width="32" height="32"
      alt="${d.label} token"><figcaption>${d.label}</figcaption>`;
    st.appendChild(f2);
  }
}

q.addEventListener('input', render);
document.querySelectorAll('.seg button').forEach(b => b.addEventListener('click', () => {
  scale = +b.dataset.s;
  document.querySelectorAll('.seg button').forEach(x =>
    x.setAttribute('aria-pressed', String(x === b)));
  render();
}));

strips();
render();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    sys.exit(main())
