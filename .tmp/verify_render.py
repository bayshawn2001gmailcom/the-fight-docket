import re, sys, asyncio
from pathlib import Path
from playwright.sync_api import sync_playwright

src = Path("newsletter_2026-08-24.html")
html = src.read_text(encoding="utf-8")

# Beehiiv worst case: style block stripped, outer container removed, white page
body = re.sub(r"<style>.*?</style>", "", html, flags=re.S)
inner = re.search(r"<body[^>]*>(.*)</body>", body, flags=re.S).group(1)
inner = re.sub(r'<div style="max-width:680px;[^"]*">', "", inner, count=1)
test = "<body style='background:#fff; margin:0'>" + inner + "</body>"
out = Path(".tmp/worstcase_0824.html")
out.write_text(test, encoding="utf-8")

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": 700, "height": 1200})
    pg.goto(out.resolve().as_uri(), wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(9000)
    res = pg.evaluate("""() => {
        const i=[...document.images];
        return {total:i.length, ok:i.filter(x=>x.naturalWidth>0).length,
                broken:i.filter(x=>x.naturalWidth===0).map(x=>x.alt)};
    }""")
    print("images:", res)
    # sample the computed color of body paragraphs against their painted background
    txt = pg.evaluate("""() => {
        const out=[];
        document.querySelectorAll('p').forEach((p,idx)=>{
            const c=getComputedStyle(p).color;
            let el=p, bg='rgba(0, 0, 0, 0)';
            while(el){ const b=getComputedStyle(el).backgroundColor;
                       if(b && b!=='rgba(0, 0, 0, 0)'){bg=b;break;} el=el.parentElement; }
            out.push({i:idx, color:c, bg:bg, t:(p.textContent||'').trim().slice(0,32)});
        });
        return out;
    }""")
    def lum(s):
        m=re.findall(r'\d+', s)[:3]
        if len(m)<3: return None
        r,g,bl=[int(x)/255 for x in m]
        return 0.2126*r+0.7152*g+0.0722*bl
    bad=[]
    for row in txt:
        lc, lb = lum(row["color"]), lum(row["bg"])
        if lc is None or lb is None: continue
        contrast=(max(lc,lb)+0.05)/(min(lc,lb)+0.05)
        if contrast < 3.0:
            bad.append((round(contrast,2), row["color"], row["bg"], row["t"]))
    print(f"paragraphs checked: {len(txt)}, low-contrast: {len(bad)}")
    for x in bad[:12]: print("  LOW:", x)
    pg.screenshot(path=".tmp/worstcase_0824.png", full_page=True)
    b.close()
print("screenshot: .tmp/worstcase_0824.png")
