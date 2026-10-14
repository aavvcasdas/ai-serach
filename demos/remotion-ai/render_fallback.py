#!/usr/bin/env python3
"""
Remotion AI科普 Demo - 纯代码渲染 fallback
模拟 Remotion 的 useCurrentFrame + interpolate + spring 逻辑
"""
import os, sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".venv" / "lib" / "python3.11" / "site-packages"))
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg, subprocess

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 1920, 1080
FPS = 30
DURATION = 10
TOTAL = DURATION*FPS
OUT = Path(__file__).parent / "output.mp4"

def font(sz, bold=False):
    from pathlib import Path
    base = Path(__file__).parent.parent.parent
    cands = [
        str(base / "assets" / "fonts" / "SourceHanSansSC-Bold.otf") if bold else str(base / "assets" / "fonts" / "SourceHanSansSC-Regular.otf"),
        str(base / "assets" / "fonts" / "SourceHanSansSC-Medium.otf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in cands:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, sz)
            except: pass
    return ImageFont.load_default()

def spring(frame, fps, from_v, to_v, duration=25):
    # simple spring approx
    t = min(1, frame/duration)
    # damping 100 approx -> ease out back
    c1 = 1.70158
    c3 = c1+1
    e = 1 + c3*pow(t-1,3) + c1*pow(t-1,2)
    return from_v + (to_v-from_v)*e

def interp(frame, in_range, out_range):
    a,b = in_range
    c,d = out_range
    if frame<=a: return c
    if frame>=b: return d
    t = (frame-a)/(b-a)
    return c + (d-c)*t

def lerp(a,b,t): return a+(b-a)*t

def scene1(draw, f):
    # bg
    for y in range(H):
        r = int(10 + (30-10)*(y/H)*0.5)
        g = int(10 + (41-10)*(y/H)*0.5)
        b = int(10 + (59-10)*(y/H)*0.5)
        draw.line([(0,y),(W,y)], fill=(r,g,b))
    ft_title = font(90, True)
    ft_sub = font(32)
    ft_badge = font(20, True)
    ty = spring(f, FPS, 80, 0, 25)
    op = interp(f, (0,20), (0,1))
    lines = ["AI科普", "大语言模型", "如何思考？"]
    base = H//2 - 160 + ty
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0,0), line, font=ft_title)
        w = bbox[2]-bbox[0]
        draw.text(((W-w)//2, base+i*110), line, font=ft_title, fill=(248,250,252))
    sub = "从 Token 到 Attention · 纯代码渲染"
    bbox = draw.textbbox((0,0), sub, font=ft_sub)
    draw.text(((W-(bbox[2]-bbox[0]))//2, base+360), sub, font=ft_sub, fill=(148,163,184))
    badge = "REMOTION · NO API · 100% REACT CODE"
    bbox = draw.textbbox((0,0), badge, font=ft_badge)
    bw = bbox[2]-bbox[0]+56
    bh=44
    bx=(W-bw)//2
    by=base+420
    draw.rounded_rectangle([bx,by,bx+bw,by+bh], radius=22, fill=(34,197,94))
    draw.text((bx+28, by+10), badge, font=ft_badge, fill=(5,46,22))

def scene2(draw, f):
    # f local 0-90
    for y in range(H):
        r = int(15 + (2-15)*(y/H))
        g = int(23 + (6-23)*(y/H))
        b = int(42 + (23-42)*(y/H))
        draw.line([(0,y),(W,y)], fill=(r,g,b))
    # grid
    for x in range(0,W,80):
        draw.line([(x,0),(x,H)], fill=(51,65,85,38), width=1)
    for y in range(0,H,80):
        draw.line([(0,y),(W,y)], fill=(51,65,85,38), width=1)
    ft_qkv = font(70, True)
    ft_label = font(20)
    boxes = [("Q",(96,165,250)), ("K",(244,114,182)), ("V",(52,211,153))]
    total_w = 3*220 + 2*50 + 120
    start_x = (W-total_w)//2 + 80
    cy = H//2 - 50
    for i,(letter,color) in enumerate(boxes):
        delay = [5,10,15][i]
        prog = spring(max(0,f-delay), FPS, 0,1,20)
        bx = start_x + i*(220+50+60)
        by = cy - 110
        if i==0:
            bx += -80*(1-prog)
        elif i==2:
            bx += 80*(1-prog)
        else:
            by += 80*(1-prog)
        draw.rounded_rectangle([bx,by,bx+220,by+220], radius=28, fill=color)
        bbox = draw.textbbox((0,0), letter, font=ft_qkv)
        draw.text((bx+(220-(bbox[2]-bbox[0]))//2, by+(220-(bbox[3]-bbox[1]))//2 -10), letter, font=ft_qkv, fill=(255,255,255))
        if i<2:
            sx = bx+220+20
            sym = "×" if i==0 else "→"
            draw.text((sx, by+80), sym, font=font(50), fill=(71,85,105))
    # text
    ft_form = font(38, True)
    txt = "Token之间通过注意力权重互相看见"
    bbox = draw.textbbox((0,0), txt, font=ft_form)
    draw.text(((W-(bbox[2]-bbox[0]))//2, cy+200), txt, font=ft_form, fill=(226,232,240))
    # tokens
    tokens = ["我","爱","学习","AI"]
    for idx, t in enumerate(tokens):
        active = interp(f, (70+idx*5, 80+idx*5), (0,1))
        bx = W//2 - 200 + idx*110
        by = cy+280
        # bg
        alpha = int(25 + active*50)
        draw.rounded_rectangle([bx,by,bx+90,by+50], radius=12, fill=(34,211,238,alpha), outline=(34,211,238,int(76+active*179)))
        bbox = draw.textbbox((0,0), t, font=font(20,True))
        draw.text((bx+(90-(bbox[2]-bbox[0]))//2, by+12), t, font=font(20,True), fill=(34,211,238))

def scene3(draw, f):
    for y in range(H):
        t = y/H
        r = int(30 + (2-30)*t)
        g = int(27 + (6-27)*t)
        b = int(75 + (23-75)*t)
        draw.line([(0,y),(W,y)], fill=(r,g,b))
    ft_title = font(72, True)
    title = ["Remotion = React组件", "就是视频帧"]
    base = H//2 - 240
    for i, line in enumerate(title):
        bbox = draw.textbbox((0,0), line, font=ft_title)
        draw.text(((W-(bbox[2]-bbox[0]))//2, base+i*90), line, font=ft_title, fill=(248,250,252))
    points = [
        ("1","useCurrentFrame()","当前帧号，驱动所有动画"),
        ("2","interpolate()","帧号映射到透明度位移"),
        ("3","spring()","物理弹簧动画丝滑"),
    ]
    for idx,(n,t,d) in enumerate(points):
        prog = interp(f, (10+idx*8, 25+idx*8), (0,1))
        bx = W//2 - 540 + idx*380
        by = base+260 + int(80*(1-prog))
        draw.rounded_rectangle([bx,by,bx+360,by+160], radius=20, fill=(255,255,255,15), outline=(255,255,255,26))
        draw.rounded_rectangle([bx+20,by+20,bx+60,by+60], radius=10, fill=(248,250,252))
        draw.text((bx+30,by+26), n, font=font(20,True), fill=(2,6,23))
        draw.text((bx+20,by+90), t, font=font(22,True), fill=(241,245,249))
        draw.text((bx+20,by+120), d, font=font(16), fill=(148,163,184))

def main():
    print(f"Remotion fallback render {TOTAL} frames -> {OUT}")
    cmd = [FFMPEG,"-y","-f","rawvideo","-vcodec","rawvideo","-s",f"{W}x{H}","-pix_fmt","rgb24","-r",str(FPS),"-i","-","-c:v","libx264","-pix_fmt","yuv420p","-crf","18","-preset","fast",str(OUT)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(TOTAL):
        img = Image.new("RGB",(W,H),(10,10,10))
        draw = ImageDraw.Draw(img,"RGBA")
        if f<90:
            scene1(draw,f)
        elif f<180:
            scene2(draw,f-90)
        else:
            scene3(draw,f-180)
        proc.stdin.write(img.tobytes())
        if f%30==0:
            print(f" frame {f}/{TOTAL}")
    proc.stdin.close()
    proc.wait()
    print(f"Done {OUT.stat().st_size/1024/1024:.2f} MB")

if __name__=="__main__":
    main()
