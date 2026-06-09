#!/usr/bin/env python3
"""
apply_splash_anim.py — 一次性腳本
把 5 種隨機 Splash 動畫套入 index.html
執行完成後可刪除本腳本。
"""
from pathlib import Path

TARGET = Path(__file__).parent.parent / "index.html"

ANIM_JS = r"""
// ══════════════════════════════════════════════════════
// SPLASH ANIMATIONS — 5 種隨機背景動畫 (Cowork 生成)
// ══════════════════════════════════════════════════════
(function(){
  const canvas = document.getElementById('sp-canvas');
  if(!canvas) return;
  const ctx = canvas.getContext('2d');
  let animId = null;
  function resize(){ canvas.width=window.innerWidth; canvas.height=window.innerHeight; }
  resize(); window.addEventListener('resize', resize);
  window._stopSplashAnim = function(){ if(animId){ cancelAnimationFrame(animId); animId=null; } };
  const W=()=>canvas.width, H=()=>canvas.height;

  // ── 1. Neural Network ──
  function runNeural(){
    const N=90;
    const pts=Array.from({length:N},()=>({x:Math.random(),y:Math.random(),vx:(Math.random()-.5)*.0004,vy:(Math.random()-.5)*.0004,r:.8+Math.random()*1.6}));
    const words=['AI','量子','DNA','宇宙','神經元','深度學習','CRISPR','黑洞','arXiv','基因組','演化','引力波','費米子','暗物質'];
    const floaters=words.map(w=>({text:w,x:.05+Math.random()*.9,y:.05+Math.random()*.9,vx:(Math.random()-.5)*.00018,vy:(Math.random()-.5)*.00018,a:.07+Math.random()*.18,size:10+Math.random()*5}));
    function draw(){
      const w=W(),h=H();
      const g=ctx.createRadialGradient(w/2,h/2,0,w/2,h/2,Math.max(w,h)*.75);
      g.addColorStop(0,'#0d2238');g.addColorStop(1,'#05101e');
      ctx.fillStyle=g;ctx.fillRect(0,0,w,h);
      ctx.lineWidth=.6;
      for(let i=0;i<N;i++) for(let j=i+1;j<N;j++){
        const dx=(pts[i].x-pts[j].x)*w,dy=(pts[i].y-pts[j].y)*h,d=Math.sqrt(dx*dx+dy*dy);
        if(d<130){ctx.strokeStyle=`rgba(90,210,185,${(1-d/130)*.22})`;ctx.beginPath();ctx.moveTo(pts[i].x*w,pts[i].y*h);ctx.lineTo(pts[j].x*w,pts[j].y*h);ctx.stroke();}
      }
      for(const p of pts){
        p.x+=p.vx;p.y+=p.vy;if(p.x<0)p.x=1;if(p.x>1)p.x=0;if(p.y<0)p.y=1;if(p.y>1)p.y=0;
        const px=p.x*w,py=p.y*h,pg=ctx.createRadialGradient(px,py,0,px,py,p.r*4);
        pg.addColorStop(0,'rgba(120,225,200,.9)');pg.addColorStop(1,'rgba(120,225,200,0)');
        ctx.fillStyle=pg;ctx.beginPath();ctx.arc(px,py,p.r*4,0,Math.PI*2);ctx.fill();
      }
      for(const f of floaters){
        f.x+=f.vx;f.y+=f.vy;
        if(f.x<.02)f.vx=Math.abs(f.vx);if(f.x>.98)f.vx=-Math.abs(f.vx);
        if(f.y<.02)f.vy=Math.abs(f.vy);if(f.y>.98)f.vy=-Math.abs(f.vy);
        ctx.font=`${f.size}px Georgia,serif`;ctx.fillStyle=`rgba(140,225,210,${f.a})`;ctx.fillText(f.text,f.x*w,f.y*h);
      }
      animId=requestAnimationFrame(draw);
    }
    draw();
  }

  // ── 2. Galaxy ──
  function runGalaxy(){
    const stars=Array.from({length:220},()=>({x:Math.random(),y:Math.random(),r:.2+Math.random()*1.8,a:.2+Math.random()*.8,twinkle:Math.random()*Math.PI*2,speed:.003+Math.random()*.01}));
    const nebulae=Array.from({length:5},()=>({x:Math.random(),y:Math.random(),r:80+Math.random()*120,hue:160+Math.floor(Math.random()*3)*40}));
    function draw(){
      const w=W(),h=H();
      ctx.fillStyle='rgba(4,8,15,.18)';ctx.fillRect(0,0,w,h);
      for(const n of nebulae){const g=ctx.createRadialGradient(n.x*w,n.y*h,0,n.x*w,n.y*h,n.r);g.addColorStop(0,`hsla(${n.hue},70%,55%,.06)`);g.addColorStop(1,'transparent');ctx.fillStyle=g;ctx.beginPath();ctx.arc(n.x*w,n.y*h,n.r,0,Math.PI*2);ctx.fill();}
      for(const s of stars){
        s.twinkle+=s.speed;s.x-=.00004;if(s.x<0)s.x=1;
        const br=s.a*(.7+.3*Math.sin(s.twinkle)),sx=s.x*w,sy=s.y*h;
        const g=ctx.createRadialGradient(sx,sy,0,sx,sy,s.r*3);
        g.addColorStop(0,`rgba(200,230,255,${br})`);g.addColorStop(1,'transparent');
        ctx.fillStyle=g;ctx.beginPath();ctx.arc(sx,sy,s.r*3,0,Math.PI*2);ctx.fill();
      }
      const band=ctx.createLinearGradient(0,h*.3,w,h*.7);band.addColorStop(0,'transparent');band.addColorStop(.5,'rgba(100,160,200,.06)');band.addColorStop(1,'transparent');ctx.fillStyle=band;ctx.fillRect(0,0,w,h);
      animId=requestAnimationFrame(draw);
    }
    draw();
  }

  // ── 3. Matrix Science ──
  function runMatrix(){
    const SYMS='∑∫αβγδεζηθλμπρσφψω∇∂∞±√∝∈∀∃ΔΩΨhνkTPeVmc'.split('').concat(['DNA','RNA','AI','eV','Hz','mol','ℏ','∮']);
    let cols,drops;
    function initDrops(){cols=Math.floor(W()/20);drops=Array.from({length:cols},()=>({y:-Math.floor(Math.random()*40),speed:.4+Math.random()*.8,bright:Math.random()>.85}));}
    initDrops();window.addEventListener('resize',initDrops);
    function draw(){
      const w=W(),h=H();ctx.fillStyle='rgba(5,15,13,.18)';ctx.fillRect(0,0,w,h);
      for(let i=0;i<drops.length;i++){
        const d=drops[i],sym=SYMS[Math.floor(Math.random()*SYMS.length)],x=i*20+2,y=d.y*20;
        if(d.bright){ctx.fillStyle='rgba(180,255,240,.95)';ctx.font='bold 13px monospace';}
        else{ctx.fillStyle=`rgba(60,190,160,${Math.min(.55,(h-y)/h*2)})`;ctx.font='12px monospace';}
        ctx.fillText(sym,x,y);d.y+=d.speed;if(d.y*20>h+40){d.y=-Math.floor(Math.random()*30);d.bright=Math.random()>.85;}
      }
      animId=requestAnimationFrame(draw);
    }
    draw();
  }

  // ── 4. Wave ──
  function runWave(){
    const SRCS=[{x:.25,y:.4,freq:.022,amp:.6,phase:0},{x:.75,y:.55,freq:.018,amp:.5,phase:Math.PI*.7},{x:.5,y:.2,freq:.025,amp:.4,phase:Math.PI*1.3}];
    const eqs=['E=mc²','ΔxΔp≥ℏ/2','∇²ψ=0','F=ma','∮B·dA=0'].map(e=>({text:e,x:.05+Math.random()*.85,y:.05+Math.random()*.85,vx:(Math.random()-.5)*.00015,vy:(Math.random()-.5)*.00015,a:.1+Math.random()*.1}));
    let t=0;const step=5;
    function draw(){
      t+=.04;const w=W(),h=H();ctx.fillStyle='rgba(7,16,26,.3)';ctx.fillRect(0,0,w,h);
      for(let y=0;y<h;y+=step){for(let x=0;x<w;x+=step){let v=0;for(const s of SRCS){const dx=x/w-s.x,dy=y/h-s.y;v+=s.amp*Math.sin(Math.sqrt(dx*dx+dy*dy)*120-t*s.freq*80+s.phase);}const n=(v/SRCS.length+1)/2,a=Math.max(0,(n-.35)*.22);if(a>.005){ctx.fillStyle=`rgba(60,${160+Math.floor(n*80)},${140+Math.floor(n*60)},${a})`;ctx.fillRect(x,y,step,step);}}}
      for(let r=20;r<Math.max(w,h);r+=65){const a=Math.max(0,.1-.1*(r/Math.max(w,h)))*Math.abs(Math.sin(r/30-t*2));if(a>.004){ctx.beginPath();ctx.arc(w/2,h/2,r,0,Math.PI*2);ctx.strokeStyle=`rgba(80,210,185,${a})`;ctx.lineWidth=1.5;ctx.stroke();}}
      ctx.font='13px Georgia,serif';for(const eq of eqs){eq.x+=eq.vx;eq.y+=eq.vy;if(eq.x<.02)eq.vx=Math.abs(eq.vx);if(eq.x>.92)eq.vx=-Math.abs(eq.vx);if(eq.y<.02)eq.vy=Math.abs(eq.vy);if(eq.y>.97)eq.vy=-Math.abs(eq.vy);ctx.fillStyle=`rgba(150,230,215,${eq.a})`;ctx.fillText(eq.text,eq.x*w,eq.y*h);}
      animId=requestAnimationFrame(draw);
    }
    draw();
  }

  // ── 5. Constellation ──
  function runConstellation(){
    const N=55;
    const stars=Array.from({length:N},()=>({x:.05+Math.random()*.9,y:.05+Math.random()*.9,r:.8+Math.random()*2.2,twinkle:Math.random()*Math.PI*2,speed:.01+Math.random()*.02,hi:Math.random()>.78}));
    const edges=[];
    for(let i=0;i<N;i++){const ds=[];for(let j=0;j<N;j++){if(i===j)continue;const dx=stars[i].x-stars[j].x,dy=stars[i].y-stars[j].y;ds.push({j,d:Math.sqrt(dx*dx+dy*dy)});}ds.sort((a,b)=>a.d-b.d);for(let k=0;k<2;k++){const key=[Math.min(i,ds[k].j),Math.max(i,ds[k].j)].join('-');if(!edges.find(e=>e.key===key)&&ds[k].d<.28)edges.push({i,j:ds[k].j,key});}}
    const labels=['AI','Bio','Phys','Neuro','Space','Chem','Ocean','Health'],lStars=stars.filter(s=>s.hi).slice(0,labels.length);
    let t=0;
    function draw(){
      t+=.005;const w=W(),h=H(),px=Math.sin(t*.3)*w*.01,py=Math.cos(t*.2)*h*.008;
      ctx.fillStyle='rgba(6,13,24,.22)';ctx.fillRect(0,0,w,h);
      for(const e of edges){const a=stars[e.i],b=stars[e.j];ctx.strokeStyle=`rgba(100,200,175,${.06+.04*(.5+.5*Math.sin(t*2+e.i*.3))})`;ctx.lineWidth=.8;ctx.beginPath();ctx.moveTo(a.x*w+px,a.y*h+py);ctx.lineTo(b.x*w+px,b.y*h+py);ctx.stroke();}
      for(const s of stars){s.twinkle+=s.speed;const br=.6+.4*Math.sin(s.twinkle),sx=s.x*w+px,sy=s.y*h+py,color=s.hi?`rgba(200,240,255,${br})`:`rgba(140,210,195,${br*.55})`,gs=s.hi?s.r*5:s.r*3.5,g=ctx.createRadialGradient(sx,sy,0,sx,sy,gs);g.addColorStop(0,color);g.addColorStop(1,'transparent');ctx.fillStyle=g;ctx.beginPath();ctx.arc(sx,sy,gs,0,Math.PI*2);ctx.fill();}
      ctx.font='10px sans-serif';lStars.forEach((s,i)=>{if(labels[i]){ctx.fillStyle='rgba(150,225,210,.45)';ctx.fillText(labels[i],s.x*w+px+8,s.y*h+py-6);}});
      animId=requestAnimationFrame(draw);
    }
    draw();
  }

  const runners=[runNeural,runGalaxy,runMatrix,runWave,runConstellation];
  runners[Math.floor(Math.random()*runners.length)]();
})();
"""

def main():
    print(f"讀取：{TARGET}")
    html = TARGET.read_text(encoding='utf-8')
    changed = False

    # ── 1. 把 .sp-bg（含 img 或空的）換成 canvas ──
    import re

    # 找 <div id="splash"> 裡的 sp-bg div，替換成 canvas
    sp_bg_patterns = [
        # 有 img 的版本（原始）
        ('  <div class="sp-bg">\r\n    <img src="https://design.canva.ai/2rqd7sW_81Jiny7" alt="每日新知封面"\r\n         onerror="this.parentElement.style.background=\'linear-gradient(135deg,#1a5a54,#4dbdb5)\'"/>\r\n  </div>',
         '  <canvas id="sp-canvas" style="position:absolute;inset:0;width:100%;height:100%;z-index:0"></canvas>'),
        # Linux 換行版
        ('  <div class="sp-bg">\n    <img src="https://design.canva.ai/2rqd7sW_81Jiny7" alt="每日新知封面"\n         onerror="this.parentElement.style.background=\'linear-gradient(135deg,#1a5a54,#4dbdb5)\'"/>\n  </div>',
         '  <canvas id="sp-canvas" style="position:absolute;inset:0;width:100%;height:100%;z-index:0"></canvas>'),
    ]

    for old, new in sp_bg_patterns:
        if old in html:
            html = html.replace(old, new)
            print("✅ Step 1: sp-bg div → canvas")
            changed = True
            break

    if not changed:
        if 'sp-canvas' in html:
            print("✅ Step 1: canvas 已存在，跳過")
            changed = True
        else:
            # 用 regex 嘗試
            html2 = re.sub(
                r'\s*<div class="sp-bg">.*?</div>',
                '\n  <canvas id="sp-canvas" style="position:absolute;inset:0;width:100%;height:100%;z-index:0"></canvas>',
                html, flags=re.DOTALL, count=1
            )
            if html2 != html:
                html = html2
                print("✅ Step 1: sp-bg div → canvas (regex)")
                changed = True
            else:
                print("⚠️  Step 1: 找不到 sp-bg div，請手動在 #splash 裡加 <canvas id='sp-canvas'>")

    # ── 2. 插入動畫 JS（找 setTimeout splash gone） ──
    markers = [
        "setTimeout(()=>document.getElementById('splash').classList.add('gone'), 3550);",
        "setTimeout(()=>document.getElementById('splash').classList.add('gone'), 3800);",
        "setTimeout(()=>document.getElementById('splash').classList.add('gone'),3550);",
        "setTimeout(()=>document.getElementById('splash').classList.add('gone'),3800);",
    ]
    inserted_js = False
    for marker in markers:
        if marker in html and 'runNeural' not in html:
            html = html.replace(marker, marker + '\n' + ANIM_JS)
            print(f"✅ Step 2: Animation JS inserted after setTimeout")
            inserted_js = True
            break

    if not inserted_js:
        if 'runNeural' in html:
            print("✅ Step 2: Animation JS 已存在，跳過")
        else:
            print("⚠️  Step 2: 找不到 setTimeout marker，JS 未插入")

    # ── 3. 更新 splash click handler 加 stopAnim ──
    old_click_crlf = "document.getElementById('splash').addEventListener('click',()=>{\r\n  document.getElementById('splash').classList.add('gone');\r\n});"
    old_click_lf   = "document.getElementById('splash').addEventListener('click',()=>{\n  document.getElementById('splash').classList.add('gone');\n});"
    new_click_crlf = "document.getElementById('splash').addEventListener('click',()=>{\r\n  if(window._stopSplashAnim)window._stopSplashAnim();\r\n  document.getElementById('splash').classList.add('gone');\r\n});"
    new_click_lf   = "document.getElementById('splash').addEventListener('click',()=>{\n  if(window._stopSplashAnim)window._stopSplashAnim();\n  document.getElementById('splash').classList.add('gone');\n});"

    if old_click_crlf in html:
        html = html.replace(old_click_crlf, new_click_crlf)
        print("✅ Step 3: click handler updated")
    elif old_click_lf in html:
        html = html.replace(old_click_lf, new_click_lf)
        print("✅ Step 3: click handler updated (LF)")
    elif '_stopSplashAnim' in html:
        print("✅ Step 3: click handler 已更新，跳過")
    else:
        print("⚠️  Step 3: click handler 未找到")

    TARGET.write_text(html, encoding='utf-8')
    size_kb = TARGET.stat().st_size // 1024
    print(f"\n✅ 完成！已寫回 {TARGET}（{size_kb} KB）")
    print("\n驗證：")
    for check in ['sp-canvas', 'runNeural', 'runGalaxy', 'runMatrix', 'runWave', 'runConstellation']:
        status = '✅' if check in html else '❌'
        print(f"  {status} {check}")

if __name__ == '__main__':
    main()
