#!/usr/bin/env python3
"""
HyperFrames AI科普 Demo - 纯代码渲染 fallback (无Chrome环境)
使用 Pillow + imageio-ffmpeg 生成MP4，模拟HyperFrames的GSAP动画
"""
import math, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".venv" / "lib" / "python3.11" / "site-packages"))
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
WIDTH, HEIGHT = 1920, 1080
FPS = 30
DURATION = 12
TOTAL_FRAMES = DURATION * FPS
OUT = Path(__file__).parent / "output.mp4"
OUT.parent.mkdir(exist_ok=True)

def get_font(size, bold=False):
    base = Path(__file__).parent.parent.parent
    candidates = [
        str(base / "assets" / "fonts" / "SourceHanSansSC-Bold.otf") if bold else str(base / "assets" / "fonts" / "SourceHanSansSC-Regular.otf"),
        str(base / "assets" / "fonts" / "SourceHanSansSC-Medium.otf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except: pass
    return ImageFont.load_default()

def ease_out_back(t):
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t-1,3) + c1 * pow(t-1,2)

def ease_out_power3(t):
    return 1 - pow(1-t,3)

def ease_out_power2(t):
    return 1 - pow(1-t,2)

def lerp(a,b,t): return a + (b-a)*t

def draw_scene1(draw, frame, W, H):
    # background radial
    # create gradient image
    progress = frame / (4*FPS)  # 0-1 in scene1
    # bg
    for y in range(H):
        # simple vertical gradient dark
        r = int(10 + (30-10)* (y/H) * 0.5)
        g = int(10 + (41-10)* (y/H) * 0.5)
        b = int(10 + (59-10)* (y/H) * 0.5)
        draw.line([(0,y),(W,y)], fill=(r,g,b))
    # title animation
    t_title = min(1, max(0, (frame - 0.2*FPS) / (0.9*FPS)))
    t_title_e = ease_out_power3(t_title)
    y_offset = lerp(80, 0, t_title_e)
    alpha = t_title_e
    # Title text
    font_title = get_font(110, bold=True)
    font_sub = get_font(36, bold=False)
    font_badge = get_font(22, bold=True)
    # Center
    lines = ["AI科普", "Transformer", "注意力机制"]
    # draw with shadow
    base_y = H//2 - 120 + y_offset
    for i, line in enumerate(lines):
        # measure
        bbox = draw.textbbox((0,0), line, font=font_title)
        w = bbox[2]-bbox[0]
        h = bbox[3]-bbox[1]
        x = (W - w)//2
        y = base_y + i*120
        # glow
        draw.text((x+2, y+2), line, font=font_title, fill=(0,0,0, int(100*alpha)))
        draw.text((x, y), line, font=font_title, fill=(248,250,252, int(255*alpha)) if hasattr(draw, 'text') else (248,250,252))
    # sub
    t_sub = min(1, max(0, (frame - 0.8*FPS) / (0.6*FPS)))
    t_sub_e = ease_out_power2(t_sub)
    sub = "Attention Is All You Need · 纯代码渲染演示"
    bbox = draw.textbbox((0,0), sub, font=font_sub)
    w = bbox[2]-bbox[0]
    draw.text(((W-w)//2, base_y+380 + lerp(30,0,t_sub_e)), sub, font=font_sub, fill=(148,163,184))
    # badge
    t_badge = min(1, max(0, (frame - 1.2*FPS) / (0.5*FPS)))
    badge_text = "HYPERFRAMES · NO API · 100% CODE"
    bbox = draw.textbbox((0,0), badge_text, font=font_badge)
    bw = bbox[2]-bbox[0] + 56
    bh = 44
    bx = (W-bw)//2
    by = base_y+440
    # badge bg
    draw.rounded_rectangle([bx, by, bx+bw, by+bh], radius=22, fill=(34,197,94))
    draw.text((bx+28, by+10), badge_text, font=font_badge, fill=(5,46,22))

def draw_scene2(draw, img, frame, W, H):
    # scene 2 is frames 4*FPS to 8*FPS
    local = frame - 4*FPS
    progress = local / (4*FPS)
    # bg
    for y in range(H):
        r = int(15 + (2-15)*(y/H))
        g = int(23 + (6-23)*(y/H))
        b = int(42 + (23-42)*(y/H))
        draw.line([(0,y),(W,y)], fill=(r,g,b))
    # grid
    grid_alpha = min(1, local / (0.8*FPS)) * 0.15
    # draw grid lines light
    for x in range(0, W, 80):
        draw.line([(x,0),(x,H)], fill=(51,65,85, int(255*grid_alpha)), width=1)
    for y in range(0, H, 80):
        draw.line([(0,y),(W,y)], fill=(51,65,85, int(255*grid_alpha)), width=1)
    # Q K V boxes
    boxes = [
        ("Q", (96,165,250), "QUERY 查询", -80, 0.2),
        ("K", (244,114,182), "KEY 键", 0, 0.4),
        ("V", (52,211,153), "VALUE 值", 80, 0.6),
    ]
    center_x = W//2
    center_y = H//2 - 50
    box_w, box_h = 280, 280
    gap = 60
    total_w = 3*box_w + 2*gap + 120  # plus x symbols
    start_x = (W - total_w)//2 + 100
    font_qkv = get_font(84, bold=True)
    font_label = get_font(22, bold=False)
    for i, (letter, color, label, x_offset, t_start) in enumerate(boxes):
        t = min(1, max(0, (local - t_start*FPS) / (0.7*FPS)))
        te = ease_out_back(t) if t<1 else 1
        # position
        bx = start_x + i*(box_w+gap+60)  # extra for x
        by = center_y - box_h//2
        # animated offset
        if i==0:
            bx += lerp(x_offset, 0, te)
        elif i==2:
            bx += lerp(x_offset, 0, te)
        else:
            by += lerp(80, 0, te)
        # draw rounded rect with gradient approx
        draw.rounded_rectangle([bx, by, bx+box_w, by+box_h], radius=32, fill=color)
        # letter
        bbox = draw.textbbox((0,0), letter, font=font_qkv)
        lw = bbox[2]-bbox[0]
        lh = bbox[3]-bbox[1]
        draw.text((bx+(box_w-lw)//2, by+(box_h-lh)//2 - 20), letter, font=font_qkv, fill=(255,255,255))
        # label
        bbox2 = draw.textbbox((0,0), label, font=font_label)
        lw2 = bbox2[2]-bbox2[0]
        draw.text((bx+(box_w-lw2)//2, by+box_h+12), label, font=font_label, fill=(226,232,240))
        # x or arrow
        if i<2:
            sym = "×" if i==0 else "→"
            sx = bx+box_w+20
            sy = by+box_h//2
            font_sym = get_font(64, bold=False)
            draw.text((sx, sy-30), sym, font=font_sym, fill=(71,85,105))
    # formula
    t_form = min(1, max(0, (local - 1.2*FPS) / (0.6*FPS)))
    t_form_e = ease_out_power2(t_form)
    formula = "Attention(Q,K,V) = softmax(QK^T/√dk)V"
    font_form = get_font(48, bold=True)
    bbox = draw.textbbox((0,0), formula, font=font_form)
    fw = bbox[2]-bbox[0]
    fy = center_y + 220 + lerp(40,0,t_form_e)
    draw.text(((W-fw)//2, fy), formula, font=font_form, fill=(226,232,240))

def draw_scene3(draw, frame, W, H):
    local = frame - 8*FPS
    # bg radial
    for y in range(H):
        # gradient from #1e1b4b to #020617
        t = y/H
        r = int(30 + (2-30)*t)
        g = int(27 + (6-27)*t)
        b = int(75 + (23-75)*t)
        draw.line([(0,y),(W,y)], fill=(r,g,b))
    font_title = get_font(88, bold=True)
    font_point_title = get_font(26, bold=True)
    font_point_desc = get_font(20, bold=False)
    # title
    t_title = min(1, max(0, (local - 0.2*FPS) / (0.8*FPS)))
    te = ease_out_power3(t_title)
    title_lines = ["代码即视频", "可复现·可版本控制·零成本"]
    base_y = H//2 - 260 + lerp(60,0,te)
    for i, line in enumerate(title_lines):
        bbox = draw.textbbox((0,0), line, font=font_title)
        w = bbox[2]-bbox[0]
        draw.text(((W-w)//2, base_y + i*100), line, font=font_title, fill=(248,250,252))
    # points
    points = [
        ("1", "纯代码渲染", "HTML+GSAP+FFmpeg，无需调用任何AI视频API，本地确定性渲染"),
        ("2", "Agent友好", "LLM天生擅长写HTML，21个Skills自动路由，批量生成100条"),
        ("3", "科普利器", "公式、图表、动画精确可控，适合AI原理可视化"),
    ]
    point_w, point_h = 420, 180
    gap = 32
    total_w = 3*point_w + 2*gap
    start_x = (W - total_w)//2
    start_y = base_y + 260
    for idx, (num, title, desc) in enumerate(points):
        t = min(1, max(0, (local - (0.8+idx*0.15)*FPS) / (0.7*FPS)))
        te = ease_out_power3(t)
        bx = start_x + idx*(point_w+gap)
        by = start_y + lerp(80,0,te)
        # bg
        draw.rounded_rectangle([bx, by, bx+point_w, by+point_h], radius=24, fill=(255,255,255,15), outline=(255,255,255,26))
        # num
        draw.rounded_rectangle([bx+20, by+20, bx+68, by+68], radius=12, fill=(248,250,252))
        font_num = get_font(20, bold=True)
        draw.text((bx+34, by+28), num, font=font_num, fill=(2,6,23))
        # title
        draw.text((bx+20, by+90), title, font=font_point_title, fill=(241,245,249))
        # desc wrap
        # simple wrap
        words = desc
        # draw with textwrap
        draw.text((bx+20, by+125), desc[:20], font=font_point_desc, fill=(148,163,184))
        draw.text((bx+20, by+150), desc[20:], font=font_point_desc, fill=(148,163,184))

def main():
    print(f"Rendering {TOTAL_FRAMES} frames {WIDTH}x{HEIGHT} @{FPS}fps -> {OUT}")
    # Use ffmpeg pipe
    cmd = [
        FFMPEG, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "fast",
        str(OUT)
    ]
    import subprocess
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(TOTAL_FRAMES):
        img = Image.new("RGB", (WIDTH, HEIGHT), (10,10,10))
        draw = ImageDraw.Draw(img, "RGBA")
        if f < 4*FPS:
            draw_scene1(draw, f, WIDTH, HEIGHT)
        elif f < 8*FPS:
            draw_scene2(draw, img, f, WIDTH, HEIGHT)
        else:
            draw_scene3(draw, f, WIDTH, HEIGHT)
        # convert to bytes
        proc.stdin.write(img.tobytes())
        if f % 30 == 0:
            print(f"  frame {f}/{TOTAL_FRAMES} ({f/FPS:.1f}s)")
    proc.stdin.close()
    proc.wait()
    print(f"Done: {OUT} {OUT.stat().st_size/1024/1024:.2f} MB")

if __name__ == "__main__":
    main()
