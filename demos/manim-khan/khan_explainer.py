#!/usr/bin/env python3
"""
Manim / Khan-explainer Demo - 纯代码渲染，无API
模拟可汗学院风格：黑板 + 手写笔迹 + 公式推导
主题：AI科普 - 梯度下降 Gradient Descent

风格特点：
- 黑色板书背景 + 粉笔质感
- 手写动画：逐笔画出
- 公式高亮
- 语音同步占位（字幕）

This mimics:
- adithya-s-k/manim_skill (3Blue1Brown style)
- khan-explainer skill (Khan Academy style, pen draws while voice explains)
"""
import os, sys, math, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".venv" / "lib" / "python3.11" / "site-packages"))
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg, subprocess

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 1920, 1080
FPS = 30
DURATION = 12
TOTAL = DURATION*FPS
OUT = Path(__file__).parent / "output.mp4"

def font(sz, bold=False, mono=False):
    from pathlib import Path
    base = Path(__file__).parent.parent.parent
    candidates = []
    if mono:
        candidates.append("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
    if bold:
        candidates.append(str(base / "assets" / "fonts" / "SourceHanSansSC-Bold.otf"))
    candidates.append(str(base / "assets" / "fonts" / "SourceHanSansSC-Regular.otf"))
    candidates.append(str(base / "assets" / "fonts" / "SourceHanSansSC-Medium.otf"))
    if bold:
        candidates.append("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    candidates.append("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except: pass
    return ImageFont.load_default()

def ease_out(t): return 1 - pow(1-t,3)
def lerp(a,b,t): return a + (b-a)*t

# Simulate handwriting by drawing text with progressive reveal and slight wobble
def draw_handwritten_text(draw, text, x, y, font_obj, fill, progress, wobble=2):
    # progress 0-1 : how much of text is revealed
    if progress <=0:
        return
    n_chars = int(len(text)*progress)
    if n_chars==0:
        return
    visible = text[:n_chars]
    # add wobble
    for i, ch in enumerate(visible):
        # measure char width
        bbox = draw.textbbox((0,0), ch, font=font_obj)
        cw = bbox[2]-bbox[0]
        # wobble offset
        wx = random.uniform(-wobble, wobble) * 0.3
        wy = random.uniform(-wobble, wobble) * 0.3
        # color variation for chalk
        r,g,b = fill
        variation = random.randint(-15,15)
        col = (max(0,min(255,r+variation)), max(0,min(255,g+variation)), max(0,min(255,b+variation)))
        draw.text((x+wx, y+wy), ch, font=font_obj, fill=col)
        x += cw
        # small kerning
        if ch in [' ', ',']:
            x+=4

def draw_formula_with_highlight(draw, formula, x, y, font_obj, progress, highlight_range=None):
    # highlight_range = (start_idx, end_idx)
    if progress<=0:
        return 0
    n = int(len(formula)*progress)
    visible = formula[:n]
    cur_x = x
    for i,ch in enumerate(visible):
        bbox = draw.textbbox((0,0), ch, font=font_obj)
        cw = bbox[2]-bbox[0]
        is_highlight = highlight_range and highlight_range[0] <= i < highlight_range[1]
        if is_highlight:
            # yellow chalk highlight bg
            draw.rounded_rectangle([cur_x-4, y-4, cur_x+cw+4, y+bbox[3]-bbox[1]+8], radius=6, fill=(250,204,21,60))
            fill = (250,204,21)
        else:
            fill = (240,240,240)
        # wobble
        wx = random.uniform(-1,1)
        wy = random.uniform(-1,1)
        draw.text((cur_x+wx, y+wy), ch, font=font_obj, fill=fill)
        cur_x += cw
    return cur_x

def draw_graph(draw, cx, cy, w, h, progress, loss_progress):
    # draw axes
    ax = 2
    draw.line([(cx-w//2, cy+h//2), (cx+w//2, cy+h//2)], fill=(100,100,100), width=ax)
    draw.line([(cx-w//2, cy-h//2), (cx-w//2, cy+h//2)], fill=(100,100,100), width=ax)
    # grid
    for i in range(1,5):
        gx = cx - w//2 + i*w//5
        draw.line([(gx, cy-h//2), (gx, cy+h//2)], fill=(50,50,50,80), width=1)
    # loss curve: y = (x^2) simplified
    points = []
    for i in range(0, w):
        x_norm = (i - w//2) / (w//2) * 2  # -2 to 2
        y_norm = x_norm*x_norm * 0.8
        px = cx - w//2 + i
        py = cy + h//2 - int(y_norm * h//2 * 0.8) - 20
        points.append((px, py))
    # draw progressive
    n = int(len(points)*progress)
    if n>1:
        draw.line(points[:n], fill=(34,211,238), width=4, joint="curve")
    # gradient descent ball
    if loss_progress>0:
        # ball moves along curve
        idx = int(lerp(0, len(points)-1, loss_progress))
        if idx < len(points):
            bx, by = points[idx]
            # glow
            draw.ellipse([bx-18, by-18, bx+18, by+18], fill=(34,211,238,40))
            draw.ellipse([bx-10, by-10, bx+10, by+10], fill=(34,211,238))
            # arrow showing gradient
            if idx+20 < len(points):
                nx, ny = points[idx+20]
                # tangent approx
                draw.line([(bx, by), (bx + (nx-bx)*0.5, by)], fill=(250,204,21), width=3)
                # label
                draw.text((bx+20, by-30), "∇", font=font(28,True), fill=(250,204,21))

def main():
    print(f"Khan-explainer style render {TOTAL} frames -> {OUT}")
    cmd = [FFMPEG,"-y","-f","rawvideo","-vcodec","rawvideo","-s",f"{W}x{H}","-pix_fmt","rgb24","-r",str(FPS),"-i","-","-c:v","libx264","-pix_fmt","yuv420p","-crf","18","-preset","fast",str(OUT)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    random.seed(42)
    for f in range(TOTAL):
        # background: blackboard with slight texture
        img = Image.new("RGB", (W,H), (18,18,18))
        draw = ImageDraw.Draw(img, "RGBA")
        # texture noise
        for _ in range(300):
            x = random.randint(0,W-1)
            y = random.randint(0,H-1)
            v = random.randint(20,35)
            draw.point((x,y), fill=(v,v,v,30))
        # border
        draw.rounded_rectangle([40,40,W-40,H-40], radius=24, outline=(60,60,60,80), width=2)
        # progress per scene
        # Scene 1: 0-4s title + formula intro
        # Scene 2: 4-8s graph + gradient descent
        # Scene 3: 8-12s conclusion
        if f < 4*FPS:
            local = f
            p = local / (4*FPS)
            # Title
            ft_title = font(82, True)
            ft_sub = font(32)
            title = "梯度下降 Gradient Descent"
            # handwritten
            draw_handwritten_text(draw, title, 120, 120, ft_title, (245,245,245), ease_out(min(1, local/(1.5*FPS))), wobble=1.5)
            # subtitle
            if local > 1.5*FPS:
                sub = "AI如何从错误中学习？"
                draw_handwritten_text(draw, sub, 120, 240, ft_sub, (160,160,160), ease_out(min(1, (local-1.5*FPS)/(1*FPS))), wobble=1)
            # formula: θ = θ - α∇J(θ)
            if local > 2.5*FPS:
                ft_form = font(64, True, mono=True)
                formula = "θ := θ - α · ∇J(θ)"
                draw_formula_with_highlight(draw, formula, 120, 340, ft_form, ease_out(min(1, (local-2.5*FPS)/(1*FPS))), highlight_range=(8,11) if local>3.2*FPS else None)
            # explanation
            if local > 3.0*FPS:
                ft_exp = font(28)
                lines = [
                    "· θ : 模型参数 (Model Parameters)",
                    "· α : 学习率 (Learning Rate)",
                    "· ∇J(θ) : 损失函数的梯度 (Gradient)",
                ]
                for i, line in enumerate(lines):
                    t = min(1, max(0, (local - (3.0+i*0.2)*FPS)/(0.6*FPS)))
                    draw_handwritten_text(draw, line, 120, 460+i*50, ft_exp, (180,180,180), ease_out(t), wobble=1)
        elif f < 8*FPS:
            local = f - 4*FPS
            # keep title small top
            ft_small = font(36, True)
            draw.text((120, 80), "梯度下降 · 可视化", font=ft_small, fill=(120,120,120))
            # graph
            graph_progress = ease_out(min(1, local/(1.5*FPS)))
            loss_prog = ease_out(min(1, max(0, (local-1.5*FPS)/(2.5*FPS))))
            draw_graph(draw, W//2, H//2+40, 1000, 500, graph_progress, loss_prog)
            # annotations
            if local > 1.0*FPS:
                ft_ann = font(26)
                draw_handwritten_text(draw, "损失 Loss J(θ)", W//2+380, H//2-180, ft_ann, (100,100,100), ease_out(min(1,(local-1*FPS)/(0.8*FPS))))
            if local > 2.0*FPS:
                ft_ann2 = font(28, True)
                txt = "沿着梯度反方向，一步步走向最低点"
                draw_handwritten_text(draw, txt, 120, H-180, ft_ann2, (34,211,238), ease_out(min(1,(local-2*FPS)/(1*FPS))), wobble=1)
            if local > 3.0*FPS:
                ft_code = font(24, mono=True)
                code_lines = [
                    "for epoch in range(100):",
                    "    grad = compute_gradient(loss, theta)",
                    "    theta -= lr * grad  # 更新参数",
                ]
                for i, cl in enumerate(code_lines):
                    draw_handwritten_text(draw, cl, 1200, H//2-100+i*40, ft_code, (160,160,160), ease_out(min(1,(local-(3+i*0.3)*FPS)/(0.5*FPS))), wobble=0.5)
        else:
            local = f - 8*FPS
            # conclusion
            ft_title = font(72, True)
            draw_handwritten_text(draw, "代码即黑板", 120, 140, ft_title, (245,245,245), ease_out(min(1, local/(1*FPS))), wobble=1.5)
            ft_sub = font(36)
            draw_handwritten_text(draw, "纯代码渲染 · 零API · 可复现", 120, 250, ft_sub, (150,150,150), ease_out(min(1, max(0,(local-0.8*FPS)/(0.8*FPS)))), wobble=1)
            # three points like khan
            points = [
                ("✦", "Manim风格：矢量公式，精确可控，3Blue1Brown同款引擎"),
                ("✦", "Khan风格：手写笔迹，边写边讲，学习体验最佳"),
                ("✦", "本地渲染：Pillow + FFmpeg，无需API，成本为零"),
            ]
            for i,(icon, txt) in enumerate(points):
                t = min(1, max(0, (local - (1.2+i*0.6)*FPS)/(0.8*FPS)))
                y = 360 + i*120
                # icon
                draw.text((120, y), icon, font=font(36,True), fill=(250,204,21))
                draw_handwritten_text(draw, txt, 180, y+5, font(32), (220,220,220), ease_out(t), wobble=1)
            # final formula highlight
            if local > 3.2*FPS:
                ft_final = font(48, True, mono=True)
                final = "θ* = argmin J(θ)  →  AI学会了"
                draw_formula_with_highlight(draw, final, 120, H-160, ft_final, ease_out(min(1,(local-3.2*FPS)/(0.8*FPS))), highlight_range=(0,2))
        # pen cursor simulation
        if f % 3 ==0:
            # small dot as pen tip near last drawn position
            pass
        proc.stdin.write(img.tobytes())
        if f%30==0:
            print(f" frame {f}/{TOTAL}")
    proc.stdin.close()
    proc.wait()
    print(f"Done {OUT.stat().st_size/1024/1024:.2f} MB")

if __name__=="__main__":
    main()
