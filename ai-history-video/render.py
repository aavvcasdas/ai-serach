#!/usr/bin/env python3
"""人工智能发展史 — 纯代码渲染科普视频 (Pillow + FFmpeg, 零API)
画面: 1280x720@24fps 黑底星野风; 每章专属程序动效; 字幕按旁白逐句对齐; 底部章节进度条
"""
import math, os, random, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1280, 720, 24
FF = subprocess.check_output([sys.executable, "-c", "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"]).decode().strip()

FB, FM, FR = [os.path.join(ROOT, "assets", f"NotoSansSC-{n}.otf") for n in ("Bold", "Medium", "Regular")]
_fc = {}
def font(path, size):
    k = (path, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]

INK, SUB, DIM = (240, 244, 255), (170, 182, 210), (105, 118, 150)
PUR, CYN, PNK, GRN, YEL = (150, 110, 255), (70, 200, 255), (255, 110, 180), (80, 230, 170), (255, 200, 90)

SCENES = [
 dict(year="1950", ch="第一章 · 起源", title="机器，能思考吗？", visual="question", accent=CYN,
      bullets=["图灵发表《计算机器与智能》", "提出图灵测试：分不清，就是会思考", "一个问题，点燃七十年"],
      narration="一九五零年，英国数学家图灵提出了一个问题：机器，能思考吗？他设计了著名的图灵测试：如果你分不清屏幕对面是人还是机器，那么机器，就算是会思考了。这个问题，点燃了人工智能七十多年的故事。"),
 dict(year="1956", ch="第二章 · 诞生", title="人工智能，正式命名", visual="birth", accent=PUR,
      bullets=["达特茅斯会议：AI 一词诞生", "预言：二十年，机器无所不能", "早期路线：把知识写成规则"],
      narration="一九五六年，达特茅斯会议上，人工智能这个词正式诞生。科学家们无比乐观，甚至预言：二十年内，机器就能做人能做的一切。早期的人工智能靠的是符号和规则：把人类的知识一条条写进程序，让机器照着推理。"),
 dict(year="1974 — 1993", ch="第三章 · 寒冬", title="两次跌入寒冬", visual="winter", accent=(120, 170, 255),
      bullets=["常识学不会，承诺一再落空", "经费锐减：第一次寒冬", "专家系统回暖后，再度崩塌"],
      narration="但现实很快泼来冷水。机器连简单的常识都学不会，承诺一再落空，经费被砍，人工智能在七十年代跌入第一次寒冬。八十年代，专家系统短暂回暖，却又因为维护成本太高，在九十年代迎来第二次寒冬。教机器学规则这条路，走到了尽头。"),
 dict(year="2012", ch="第四章 · 转折", title="深度学习引爆", visual="chart", accent=GRN,
      bullets=["新路线：让机器从数据里自学", "AlexNet 图像识别一举夺冠", "引擎切换：规则 → 数据 + 算力"],
      narration="转机藏在另一个方向：不是人教机器规则，而是让机器自己从数据里找规律，这就是机器学习。二零一二年，深度学习模型AlexNet在图像识别比赛中一举夺冠，错误率大幅领先。从那一刻起，人工智能的引擎，从规则，换成了数据加算力。"),
 dict(year="2016 — 2017", ch="第五章 · 突破", title="AlphaGo 与 Transformer", visual="go", accent=YEL,
      bullets=["AlphaGo 击败李世石", "全世界第一次直观看到「聪明」", "Transformer：大模型的共同地基"],
      narration="二零一六年，AlphaGo击败围棋世界冠军李世石，全世界第一次直观感受到：机器真的在变聪明。紧接着二零一七年，谷歌提出Transformer架构。正是它，成了后来所有大模型的共同地基。"),
 dict(year="2022", ch="第六章 · 爆发", title="大模型时代开启", visual="chat", accent=PNK,
      bullets=["ChatGPT 两个月用户破亿", "史上增长最快的产品", "AI 走出实验室，走进每个人的手机"],
      narration="二零二二年底，ChatGPT发布，短短两个月用户破亿，成为史上增长最快的产品。人工智能不再是实验室里的论文，它走进每个人的手机：写文案、写代码、画画、对话。大模型时代，正式开启。"),
 dict(year="2026 →", ch="终章 · 未来", title="下一个十年", visual="future", accent=CYN,
      bullets=["规律：新方法 × 数据 × 算力", "每一次跃升，都来自三者相遇", "答案不在机器手里，而在我们手里"],
      narration="从图灵的一个问题，到今天的大模型，人工智能七十多年，走过了诞生、寒冬、复兴和爆发。规律其实很清晰：每一次跃升，都来自新方法、数据和算力的相遇。下一个十年会怎样？答案不在机器手里，而在我们，如何使用它。关注我，下一期，我们聊聊大模型到底是怎么学会说话的。"),
]

def dur(path):
    out = subprocess.run([FF, "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))

for i, s in enumerate(SCENES, 1):
    s["voice"] = os.path.join(ROOT, "assets", "voice", f"s{i}.mp3")
    s["vdur"] = dur(s["voice"])
    s["dur"] = s["vdur"] + 1.0
    # 字幕切片: 按标点切, 按字数比例分配时间
    parts = [p for p in re.split(r"(?<=[。！？；])", s["narration"]) if p.strip()]
    tot = sum(len(p) for p in parts) or 1
    t = 0.35; s["subs"] = []
    for p in parts:
        d = s["vdur"] * len(p) / tot
        s["subs"].append((t, t + d, p.strip())); t += d

TOTAL = sum(s["dur"] for s in SCENES)
print(f"scenes={len(SCENES)} total={TOTAL:.1f}s voices={[round(s['vdur'],1) for s in SCENES]}", flush=True)

# ---------- 背景: 星野 + 紫雾 ----------
random.seed(42)
bg = Image.new("RGB", (W, H), (7, 11, 20))
_bd = ImageDraw.Draw(bg, "RGBA")
for y in range(H):
    a = int(26 * (y / H) ** 2)
    _bd.line([(0, y), (W, y)], fill=(60, 40, 110, a))
stars = [(random.randint(0, W - 1), random.randint(0, H - 1), random.choice([1, 1, 2]), random.random() * 6.28) for _ in range(190)]
for x, y, r, _p in stars: _bd.ellipse([x, y, x + r, y + r], fill=(200, 215, 255, 140))
bg = bg.filter(ImageFilter.GaussianBlur(0.4))

def ease(t): return 1 - (1 - max(0.0, min(1.0, t))) ** 3
def clamp(t): return max(0.0, min(1.0, t))

def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for ch in text:
        if d.textlength(cur + ch, font=f) > maxw and cur: lines.append(cur); cur = ch
        else: cur += ch
    if cur: lines.append(cur)
    return lines

def rrect(d, box, r, **kw): d.rounded_rectangle(box, radius=r, **kw)

# ---------- 每章专属动效 ----------
def visual(d, kind, t, dur_, acc, seed_pts):
    cx, cy = 900, 330
    p = clamp(t / max(dur_, 0.01))
    if kind == "question":
        for i in range(3):
            r = 60 + ((t * 40 + i * 55) % 165)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=acc + (int(90 * (1 - r / 230)),), width=3)
        d.text((cx, cy - 8), "?", font=font(FB, 130), fill=INK, anchor="mm")
        d.text((cx, cy + 155), "图 灵 测 试", font=font(FM, 26), fill=SUB, anchor="mm")
    elif kind == "birth":
        pts = [(cx + 150 * math.cos(a + t * .3), cy + 105 * math.sin(a + t * .3)) for a in np.linspace(0, 6.28, 7)[:-1]]
        for i, a in enumerate(pts):
            for b in pts[i + 1:]:
                if random.Random(int(a[0] + b[0])).random() > .45: d.line([a, b], fill=acc + (70,), width=2)
        for a in pts: d.ellipse([a[0] - 9, a[1] - 9, a[0] + 9, a[1] + 9], fill=acc)
        d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=INK)
        d.text((cx, cy + 160), "符号主义 · 规则推理", font=font(FM, 26), fill=SUB, anchor="mm")
    elif kind == "winter":
        xs = np.linspace(cx - 170, cx + 170, 60)
        ys = cy - 90 + 150 * ((xs - (cx - 170)) / 340) ** 1.6 + 12 * np.sin(xs / 22 + t)
        d.line(list(zip(xs, ys)), fill=acc, width=5, joint="curve")
        random.seed(7)
        for i in range(36):
            sx = cx - 180 + (i * 53) % 360; sy = (i * 71 + t * 55) % 330 + cy - 165
            r = 7
            for ang in (0, 60, 120):
                dx, dy = r * math.cos(math.radians(ang)), r * math.sin(math.radians(ang))
                d.line([sx - dx, sy - dy, sx + dx, sy + dy], fill=(185, 215, 255, 220), width=2)
            d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(220, 235, 255, 255))
        d.text((cx, cy + 160), "经费锐减 · 期望崩塌", font=font(FM, 26), fill=SUB, anchor="mm")
    elif kind == "chart":
        vals = [.72, .55, .42, .30, .16]
        for i, v in enumerate(vals):
            bh = 200 * v * ease(p * 1.4 - i * .12); x = cx - 160 + i * 78
            col = GRN if i == 4 else (90, 110, 150)
            rrect(d, [x, cy + 110 - bh, x + 48, cy + 110], 7, fill=col)
            if i == 4: d.text((x + 24, cy + 110 - bh - 26), "AlexNet", font=font(FB, 20), fill=GRN, anchor="mm")
        d.line([cx - 180, cy + 110, cx + 210, cy + 110], fill=DIM, width=2)
        d.text((cx, cy + 160), "图像识别错误率 ↓", font=font(FM, 26), fill=SUB, anchor="mm")
    elif kind == "go":
        for i in range(7):
            x = cx - 150 + i * 50; d.line([x, cy - 150, x, cy + 150], fill=(90, 100, 130, 160), width=2)
            y = cy - 150 + i * 50; d.line([cx - 150, y, cx + 150, y], fill=(90, 100, 130, 160), width=2)
        random.seed(3); stones = [(random.randint(0, 6), random.randint(0, 6)) for _ in range(22)]
        for i, (gx, gy) in enumerate(stones):
            if p < i / 22: break
            x, y = cx - 150 + gx * 50, cy - 150 + gy * 50
            col = INK if i % 2 else (25, 30, 45)
            d.ellipse([x - 17, y - 17, x + 17, y + 17], fill=col, outline=YEL if i == 21 else None, width=3)
        d.text((cx, cy + 185), "AlphaGo vs 李世石 · 4 : 1", font=font(FM, 26), fill=SUB, anchor="mm")
    elif kind == "chat":
        for i, (w_, who) in enumerate([(210, 0), (270, 1), (180, 0)]):
            yy = cy - 130 + i * 92; ap = ease(p * 1.6 - i * .25)
            x0 = cx - 180 if who == 0 else cx + 180 - w_
            rrect(d, [x0, yy, x0 + w_ * ap, yy + 58], 16, fill=(40, 50, 80) if who == 0 else acc)
            if ap > .8:
                for jx in range(3): d.ellipse([x0 + 22 + jx * 22, yy + 25, x0 + 32 + jx * 22, yy + 35], fill=INK)
        d.text((cx, cy + 185), "两个月 · 用户破亿", font=font(FM, 26), fill=PNK, anchor="mm")
    elif kind == "future":
        nodes = [(cx + 190 * math.cos(a), cy + 120 * math.sin(a * 1.4 + t * .4)) for a in np.linspace(0, 6.28, 9)]
        for i, a in enumerate(nodes):
            for b in nodes[i + 1:]:
                if (int(a[0]) + int(b[1])) % 3 == 0: d.line([a, b], fill=CYN + (55,), width=1)
        for a in nodes: d.ellipse([a[0] - 6, a[1] - 6, a[0] + 6, a[1] + 6], fill=CYN)
        d.text((cx, cy), "?", font=font(FB, 84), fill=INK, anchor="mm")
        d.text((cx, cy + 185), "方法 × 数据 × 算力", font=font(FM, 26), fill=SUB, anchor="mm")

def draw_frame(t_global):
    # 定位场景
    acc_t, si = 0.0, 0
    for i, s in enumerate(SCENES):
        if t_global < acc_t + s["dur"] or i == len(SCENES) - 1: si = i; break
        acc_t += s["dur"]
    s = SCENES[si]; t = t_global - acc_t; acc = s["accent"]
    img = bg.copy(); d = ImageDraw.Draw(img, "RGBA")
    for x, y, r, ph in stars:
        tw = int(90 + 70 * math.sin(t_global * 2 + ph))
        d.ellipse([x, y, x + r, y + r], fill=(200, 215, 255, tw))
    fade = min(clamp(t / .45), clamp((s["dur"] - t) / .45))
    # HUD
    hud = f"人工智能发展史  {si+1:02d} / {len(SCENES):02d}"
    rrect(d, [44, 34, 44 + d.textlength(hud, font=font(FM, 21)) + 36, 72], 19, fill=(255, 255, 255, 18), outline=(255, 255, 255, 45))
    d.text((62, 53), hud, font=font(FM, 21), fill=SUB, anchor="lm")
    d.text((1236, 53), s["ch"], font=font(FM, 21), fill=acc, anchor="rm")
    # 年份 + 标题 + 要点
    ya = ease(t / .8)
    d.text((66, 128), s["year"], font=font(FB, 74), fill=acc + (int(255 * ya),), anchor="la")
    d.text((68, 216), s["title"], font=font(FB, 46), fill=INK, anchor="la")
    for i, b in enumerate(s["bullets"]):
        bt = ease((t - .7 - i * .55) / .6)
        if bt <= 0: continue
        y = 306 + i * 76; xoff = int((1 - bt) * -36)
        rrect(d, [64 + xoff, y, 64 + xoff + 470, y + 58], 12, fill=(255, 255, 255, int(14 * bt)), outline=acc + (int(120 * bt),))
        d.ellipse([82 + xoff, y + 23, 94 + xoff, y + 35], fill=acc)
        d.text((108 + xoff, y + 29), b, font=font(FM, 25), fill=(INK[0], INK[1], INK[2], int(255 * bt)), anchor="lm")
    visual(d, s["visual"], t, s["dur"], acc, si)
    # 章节进度条
    seg_w, gap, x0, y0 = 158, 12, 64, 662
    for i in range(len(SCENES)):
        x = x0 + i * (seg_w + gap)
        rrect(d, [x, y0, x + seg_w, y0 + 7], 3, fill=(255, 255, 255, 28))
        fillw = seg_w if i < si else (seg_w * clamp(t / s["dur"]) if i == si else 0)
        if fillw: rrect(d, [x, y0, x + fillw, y0 + 7], 3, fill=SCENES[i]["accent"])
    # 字幕
    sub = next((p for a, b, p in s["subs"] if a <= t - 0.0 < b), "")
    if sub and fade > 0:
        lines = wrap(d, sub, font(FB, 34), 1060)
        yy = 606 - (len(lines) - 1) * 23
        for ln in lines:
            d.text((640, yy), ln, font=font(FB, 34), fill=INK, anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0))
            yy += 46
    if fade < 1:
        ov = Image.new("RGB", (W, H), (0, 0, 0))
        img = Image.blend(ov, img, fade)
    return img

# ---------- 背景音乐: 本地合成氛围垫 ----------
def make_music(path):
    sr, n = 44100, int(TOTAL * 44100)
    tt = np.arange(n) / sr
    chords = [(220, 261.6, 329.6), (174.6, 220, 261.6), (196, 246.9, 293.7), (164.8, 196, 246.9)]
    y = np.zeros(n)
    cl = int(8 * sr)
    for i in range(0, n, cl):
        ch = chords[(i // cl) % 4]; seg = min(cl, n - i)
        env = np.minimum(1, np.arange(seg) / (2 * sr)) * np.minimum(1, (seg - np.arange(seg)) / (2 * sr))
        for f in ch: y[i:i + seg] += 0.05 * np.sin(2 * np.pi * f * tt[i:i + seg]) * env
    y += 0.012 * np.sin(2 * np.pi * 55 * tt) * (0.6 + 0.4 * np.sin(2 * np.pi * .125 * tt))
    stereo = np.stack([y, y], 1)
    (stereo * 32767).astype(np.int16).tofile("/tmp/_music.raw")
    subprocess.run([FF, "-y", "-f", "s16le", "-ar", "44100", "-ac", "2", "-i", "/tmp/_music.raw", path],
                   capture_output=True, check=True)

def main():
    make_music(os.path.join(ROOT, "music.wav"))
    # 旁白轨: 每段按场景时长对齐拼接
    wavs = []
    for i, s in enumerate(SCENES, 1):
        wv = os.path.join(ROOT, f"_v{i}.wav")
        subprocess.run([FF, "-y", "-i", s["voice"], "-af", f"adelay=350|350,apad", "-t", f"{s['dur']}", "-ar", "44100", wv],
                       capture_output=True, check=True)
        wavs.append(wv)
    lst = os.path.join(ROOT, "_list.txt")
    open(lst, "w").write("".join(f"file '{w}'\n" for w in wavs))
    narration = os.path.join(ROOT, "narration.wav")
    subprocess.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, narration], capture_output=True, check=True)
    # 渲染帧 -> 管道编码
    silent = os.path.join(ROOT, "_silent.mp4")
    proc = subprocess.Popen([FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                             "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium", silent],
                            stdin=subprocess.PIPE)
    total_frames = int(TOTAL * FPS)
    for f in range(total_frames):
        proc.stdin.write(draw_frame(f / FPS).tobytes())
        if f % 240 == 0: print(f"frame {f}/{total_frames}", flush=True)
    proc.stdin.close(); proc.wait()
    out = os.path.join(ROOT, "人工智能发展史.mp4")
    subprocess.run([FF, "-y", "-i", silent, "-i", narration, "-i", os.path.join(ROOT, "music.wav"),
                    "-filter_complex", "[2:a]volume=0.5[m];[1:a][m]amix=inputs=2:duration=first[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", out],
                   capture_output=True, check=True)
    for w in wavs: os.remove(w)
    os.remove(lst)
    print("DONE", out, f"{os.path.getsize(out)/1e6:.1f}MB", flush=True)

if __name__ == "__main__":
    main()
