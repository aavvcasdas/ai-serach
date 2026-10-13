#!/usr/bin/env python3
"""v2 语义拍同步版 — 学 video-talkcraft: 字级同步锚点 + SHOTBOOK分镜 + 反PPT运镜
每句旁白=一个语义拍: 拍开始的瞬间, 对应卡片弹出/对应动效触发/关键词放大;
拍内字幕逐字染色(karaoke); 静默点(silencedetect)吸附拍边界; 全程极缓推镜, 无静止帧。
"""
import math, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1280, 720, 24
FF = subprocess.check_output([sys.executable, "-c", "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"]).decode().strip()
FB, FM = [os.path.join(ROOT, "assets", f"NotoSansSC-{n}.otf") for n in ("Bold", "Medium")]
_fc = {}
def font(p, s):
    if (p, s) not in _fc: _fc[(p, s)] = ImageFont.truetype(p, s)
    return _fc[(p, s)]
INK, SUB, DIM = (240, 244, 255), (175, 188, 215), (110, 124, 155)
PUR, CYN, PNK, GRN, YEL, BLU = (150, 110, 255), (70, 200, 255), (255, 110, 180), (80, 230, 170), (255, 200, 90), (120, 170, 255)

# 每拍: (说的话, 同步弹出的卡, 右侧舞台关键词)
SCENES = [
 dict(year="1950", ch="第一章 · 起源", title="机器，能思考吗？", accent=CYN, beats=[
   ("一九五零年，英国数学家图灵提出了一个问题：", "1950 · 图灵发问", "图灵"),
   ("机器，能思考吗？", "机器，能思考吗？", "？"),
   ("他设计了著名的图灵测试：如果你分不清屏幕对面是人还是机器，", "图灵测试", "人  VS  机器"),
   ("那么机器，就算是会思考了。", "分不清 = 会思考", "PASS"),
   ("这个问题，点燃了人工智能七十多年的故事。", "点燃七十年", "1950 → 2026")]),
 dict(year="1956", ch="第二章 · 诞生", title="人工智能，正式命名", accent=PUR, beats=[
   ("一九五六年，达特茅斯会议上，人工智能这个词正式诞生。", "达特茅斯会议 · AI 诞生", "AI"),
   ("科学家们无比乐观，甚至预言：二十年内，机器就能做人能做的一切。", "预言：20 年无所不能", "20 年"),
   ("早期的人工智能靠的是符号和规则：", "路线：符号 + 规则", "规则"),
   ("把人类的知识一条条写进程序，让机器照着推理。", "知识 → 程序 → 推理", "IF → THEN")]),
 dict(year="1974—1993", ch="第三章 · 寒冬", title="两次跌入寒冬", accent=BLU, beats=[
   ("但现实很快泼来冷水。", "现实泼来冷水", "冷水"),
   ("机器连简单的常识都学不会，承诺一再落空，经费被砍，人工智能在七十年代跌入第一次寒冬。", "第一次寒冬", "↓ 经费"),
   ("八十年代，专家系统短暂回暖，却又因为维护成本太高，", "专家系统短暂回暖", "短暂回暖"),
   ("在九十年代迎来第二次寒冬。教机器学规则这条路，走到了尽头。", "第二次寒冬 · 规则走到尽头", "尽头")]),
 dict(year="2012", ch="第四章 · 转折", title="深度学习引爆", accent=GRN, beats=[
   ("转机藏在另一个方向：不是人教机器规则，而是让机器自己从数据里找规律，这就是机器学习。", "新路线：机器自学", "数据 → 规律"),
   ("二零一二年，深度学习模型AlexNet在图像识别比赛中一举夺冠，错误率大幅领先。", "AlexNet 夺冠", "错误率 ↓"),
   ("从那一刻起，人工智能的引擎，从规则，换成了数据加算力。", "引擎：规则 → 数据+算力", "数据 × 算力")]),
 dict(year="2016—2017", ch="第五章 · 突破", title="AlphaGo 与 Transformer", accent=YEL, beats=[
   ("二零一六年，AlphaGo击败围棋世界冠军李世石，", "AlphaGo vs 李世石", "4 : 1"),
   ("全世界第一次直观感受到：机器真的在变聪明。", "机器真的在变聪明", "聪明"),
   ("紧接着二零一七年，谷歌提出Transformer架构。", "2017 · Transformer", "Transformer"),
   ("正是它，成了后来所有大模型的共同地基。", "所有大模型的共同地基", "地基")]),
 dict(year="2022", ch="第六章 · 爆发", title="大模型时代开启", accent=PNK, beats=[
   ("二零二二年底，ChatGPT发布，", "ChatGPT 发布", "ChatGPT"),
   ("短短两个月，用户破亿，成为史上增长最快的产品。", "两个月用户破亿", "1 亿用户"),
   ("人工智能不再是实验室里的论文，它走进每个人的手机：写文案、写代码、画画、对话。", "走进每个人的手机", "手机里的 AI"),
   ("大模型时代，正式开启。", "大模型时代开启", "爆发")]),
 dict(year="2026 →", ch="终章 · 未来", title="下一个十年", accent=CYN, beats=[
   ("从图灵的一个问题，到今天的大模型，人工智能七十多年，走过了诞生、寒冬、复兴和爆发。", "诞生 · 寒冬 · 复兴 · 爆发", "70 年"),
   ("规律其实很清晰：每一次跃升，都来自新方法、数据和算力的相遇。", "跃升 = 方法 × 数据 × 算力", "×"),
   ("下一个十年会怎样？答案不在机器手里，而在我们，如何使用它。", "答案在我们手里", "？"),
   ("关注我，下一期，我们聊聊大模型到底是怎么学会说话的。", "下期：大模型如何学会说话", "下期见")]),
]

def probe(path, af=None):
    cmd = [FF, "-i", path] + (["-af", af, "-f", "null", "-"] if af else [])
    return subprocess.run(cmd, capture_output=True, text=True).stderr

for i, s in enumerate(SCENES, 1):
    s["voice"] = os.path.join(ROOT, "assets", "voice", f"s{i}.mp3")
    out = probe(s["voice"]); m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    s["vdur"] = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    s["dur"] = s["vdur"] + 1.0
    # 真实静默点(语音恢复点) -> 拍边界吸附
    sil = probe(s["voice"], "silencedetect=noise=-35dB:d=0.15")
    ends = sorted(set(round(float(x), 2) for x in re.findall(r"silence_end: ([\d.]+)", sil) if float(x) > 0.3))
    s["silence_ends"] = ends
    tot = sum(len(b[0]) for b in s["beats"]); acc_chars, starts = 0, []
    for b in s["beats"]:
        raw = 0.35 + s["vdur"] * acc_chars / tot; acc_chars += len(b[0])
        if starts:
            near = [e + 0.35 for e in ends if abs(e + 0.35 - raw) <= 1.1]
            if near: raw = min(near, key=lambda e: abs(e - raw))
            raw = max(raw, starts[-1] + 0.5)
        starts.append(round(raw, 2))
    s["starts"] = starts
    print(f"scene{i} vdur={s['vdur']:.1f} beats@{starts}", flush=True)
TOTAL = sum(s["dur"] for s in SCENES)

# ---------- 背景 ----------
import random
random.seed(42)
bg = Image.new("RGB", (W, H), (7, 11, 20)); _bd = ImageDraw.Draw(bg, "RGBA")
for y in range(H): _bd.line([(0, y), (W, y)], fill=(60, 40, 110, int(26 * (y / H) ** 2)))
stars = [(random.randint(0, W - 1), random.randint(0, H - 1), random.choice([1, 1, 2]), random.random() * 6.28) for _ in range(190)]
for x, y, r, _ in stars: _bd.ellipse([x, y, x + r, y + r], fill=(200, 215, 255, 140))
bg = bg.filter(ImageFilter.GaussianBlur(0.4))

def ease(t): return 1 - (1 - max(0.0, min(1.0, t))) ** 3
def clamp(t): return max(0.0, min(1.0, t))
def rr(d, box, r, **kw): d.rounded_rectangle(box, radius=r, **kw)

def stage_visual(d, si, bi, bf, t, acc):
    """右侧舞台: 只画'当前拍正在说'的东西, 拍进则入场"""
    cx, cy = 905, 315; pop = ease(min(1.0, bf * 3))
    kw = SCENES[si]["beats"][bi][2]
    # 关键词大字(每拍必变, 说到才出现)
    ks = int(58 * (0.7 + 0.3 * pop)) if len(kw) <= 5 else (44 if len(kw) <= 9 else 34)
    d.text((cx, cy - 105), kw, font=font(FB, ks), fill=acc, anchor="mm")
    prog = (bi + bf) / len(SCENES[si]["beats"])
    if si == 0:  # 图灵: 人/机对框在第3拍亮起
        for j, (lab, col) in enumerate([("人 类", CYN), ("机 器", PUR)]):
            on = bi >= 2 or j == 0; x = cx - 165 + j * 150
            rr(d, [x, cy - 35, x + 130, cy + 45], 14, fill=(255, 255, 255, 14 if on else 6), outline=col if on else DIM, width=2)
            d.text((x + 65, cy + 5), lab, font=font(FB, 27), fill=INK if on else DIM, anchor="mm")
        if bi >= 3: d.text((cx, cy + 85), "分不清 → 判定：会思考 ✓", font=font(FM, 25), fill=GRN, anchor="mm")
    elif si == 1:
        if bi == 2:  # 规则卡堆叠
            for j in range(3):
                y = cy - 40 + j * 48; rr(d, [cx - 150, y, cx + 150, y + 38], 9, fill=(255, 255, 255, 12), outline=acc, width=1)
                d.text((cx, y + 19), ["IF 下雨 THEN 带伞", "IF 发烧 THEN 吃药", "IF … THEN …"][j], font=font(FM, 21), fill=SUB, anchor="mm")
        elif bi >= 3:
            d.text((cx, cy + 10), "知识 ──► 程序 ──► 推理", font=font(FB, 30), fill=INK, anchor="mm")
        else:
            pts = [(cx + 140 * math.cos(a + t * .3), cy + 40 + 85 * math.sin(a + t * .3)) for a in np.linspace(0, 6.28, 7)[:-1]]
            for a in pts: d.ellipse([a[0] - 8, a[1] - 8, a[0] + 8, a[1] + 8], fill=acc)
            d.ellipse([cx - 12, cy + 28, cx + 12, cy + 52], fill=INK)
    elif si == 2:  # 寒冬曲线按说到的进度画
        xs = np.linspace(cx - 170, cx + 170, 80)
        ys = cy - 60 + 140 * ((xs - (cx - 170)) / 340) ** 1.5
        n = max(2, int(80 * prog)); d.line(list(zip(xs[:n], ys[:n])), fill=acc, width=5, joint="curve")
        random.seed(7)
        for j in range(int(10 + 26 * prog)):
            sx = cx - 180 + (j * 53) % 360; sy = (j * 71 + t * 55) % 300 + cy - 130; r = 6
            for ang in (0, 60, 120):
                dx, dy = r * math.cos(math.radians(ang)), r * math.sin(math.radians(ang))
                d.line([sx - dx, sy - dy, sx + dx, sy + dy], fill=(185, 215, 255, 200), width=2)
    elif si == 3:
        if bi == 0:  # 神经网络亮起
            layers = [[(cx - 150, cy - 60 + k * 60) for k in range(3)], [(cx, cy - 90 + k * 60) for k in range(4)], [(cx + 150, cy - 30 + k * 60) for k in range(2)]]
            for li in range(2):
                for a in layers[li]:
                    for b in layers[li + 1]: d.line([a, b], fill=acc + (50,), width=1)
            for li, lay in enumerate(layers):
                for k, a in enumerate(lay):
                    on = (t * 2 + li + k) % 3 < 1.6
                    d.ellipse([a[0] - 11, a[1] - 11, a[0] + 11, a[1] + 11], fill=acc if on else (50, 70, 90))
        else:  # 柱状图逐根长
            for j, v in enumerate([.72, .55, .42, .30, .16]):
                bh = 175 * v * ease(bf * 2 - j * .15 + (1 if bi >= 2 else 0)); x = cx - 165 + j * 72
                rr(d, [x, cy + 80 - bh, x + 46, cy + 80], 7, fill=GRN if j == 4 else (95, 115, 155))
            d.text((cx + 140, cy - 55), "AlexNet", font=font(FB, 22), fill=GRN, anchor="mm")
    elif si == 4:
        if bi <= 1:  # 棋盘按拍落子
            for j in range(7):
                x = cx - 150 + j * 50; d.line([x, cy - 90, x, cy + 210], fill=(90, 100, 130, 160), width=2)
                y = cy - 90 + j * 50; d.line([cx - 150, y, cx + 150, y], fill=(90, 100, 130, 160), width=2)
            random.seed(3); stones = [(random.randint(0, 6), random.randint(0, 6)) for _ in range(22)]
            cnt = int(22 * prog * 1.8)
            for j, (gx, gy) in enumerate(stones[:cnt]):
                x, y = cx - 150 + gx * 50, cy - 90 + gy * 50
                d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=INK if j % 2 else (25, 30, 45), outline=YEL if j == cnt - 1 else None, width=3)
        else:  # Transformer 积木自下而上堆
            for j, lab in enumerate(["注意力 Attention", "编码器 Encoder", "解码器 Decoder"]):
                y = cy + 90 - j * 62; a = ease(bf * 2 - j * .3) if bi == 2 else 1
                if a <= 0: continue
                rr(d, [cx - 155, y, cx + 155, y + 48], 10, fill=(255, 255, 255, int(16 * a)), outline=YEL, width=2)
                d.text((cx, y + 24), lab, font=font(FB, 24), fill=INK, anchor="mm")
    elif si == 5:
        if bi == 1:  # 用户计数滚动
            num = int(100 * ease(bf)); d.text((cx, cy + 20), f"{num} 万→亿", font=font(FB, 30), fill=SUB, anchor="mm")
            d.text((cx, cy + 75), "史上最快破亿产品", font=font(FM, 24), fill=PNK, anchor="mm")
        elif bi >= 2:  # 手机框
            rr(d, [cx - 62, cy - 45, cx + 62, cy + 115], 20, outline=PNK, width=3)
            for j, w_ in enumerate(["写文案", "写代码", "画画", "对话"][:1 + int(bf * 4)]):
                d.text((cx, cy - 10 + j * 32), w_, font=font(FM, 21), fill=INK, anchor="mm")
        else:
            for j, (w_, who) in enumerate([(200, 0), (255, 1)]):
                y = cy - 30 + j * 80; x = cx - 160 if who == 0 else cx + 160 - w_
                rr(d, [x, y, x + w_, y + 52], 15, fill=(52, 68, 108) if who == 0 else (215, 70, 150))
                for jx in range(3): d.ellipse([x + 20 + jx * 20, y + 21, x + 29 + jx * 20, y + 30], fill=INK)
    elif si == 6:
        if bi == 0:  # 70年时间线逐点亮
            yrs = ["1950", "1956", "1974", "2012", "2016", "2022"]
            for j, y_ in enumerate(yrs):
                x = cx - 190 + j * 76; on = bf * len(yrs) > j
                d.ellipse([x - 8, cy + 10, x + 8, cy + 26], fill=acc if on else DIM)
                d.text((x, cy + 48), y_, font=font(FM, 19), fill=INK if on else DIM, anchor="mm")
                if j: d.line([cx - 190 + (j - 1) * 76, cy + 18, x, cy + 18], fill=acc if on else DIM, width=2)
        elif bi == 1:
            for j, lab in enumerate(["新方法", "数 据", "算 力"]):
                bh = 95 * ease(bf * 1.6 - j * .25); x = cx - 140 + j * 105
                rr(d, [x, cy + 95 - bh, x + 62, cy + 95], 8, fill=acc)
                d.text((x + 31, cy + 122), lab, font=font(FB, 22), fill=INK, anchor="mm")
        elif bi == 3:
            rr(d, [cx - 175, cy - 20, cx + 175, cy + 70], 16, fill=(255, 110, 180, 30), outline=PNK, width=2)
            d.text((cx, cy + 25), "下期：大模型如何学会说话", font=font(FB, 26), fill=INK, anchor="mm")

def draw_frame(tg):
    at, si = 0.0, 0
    for i, s in enumerate(SCENES):
        if tg < at + s["dur"] or i == len(SCENES) - 1: si = i; break
        at += s["dur"]
    s = SCENES[si]; t = tg - at; acc = s["accent"]
    starts = s["starts"] + [s["dur"] + 9]
    bi = max(0, max(i for i in range(len(s["beats"])) if t >= starts[i] - 0.35) if t >= starts[0] - 0.35 else 0)
    bi = min(bi, len(s["beats"]) - 1)
    bstart, bend = starts[bi], min(starts[bi + 1], 0.35 + s["vdur"])
    bf = clamp((t - bstart) / max(.01, bend - bstart))
    img = bg.copy(); d = ImageDraw.Draw(img, "RGBA")
    for x, y, r, ph in stars:
        tw = int(90 + 70 * math.sin(tg * 2 + ph)); d.ellipse([x, y, x + r, y + r], fill=(200, 215, 255, tw))
    fade = min(clamp(t / .4), clamp((s["dur"] - t) / .4))
    hud = f"人工智能发展史  {si+1:02d} / {len(SCENES):02d}"
    rr(d, [44, 34, 44 + d.textlength(hud, font=font(FM, 21)) + 36, 72], 19, fill=(255, 255, 255, 18), outline=(255, 255, 255, 45))
    d.text((62, 53), hud, font=font(FM, 21), fill=SUB, anchor="lm")
    d.text((1236, 53), s["ch"], font=font(FM, 21), fill=acc, anchor="rm")
    d.text((66, 118), s["year"], font=font(FB, 66), fill=acc, anchor="la")
    d.text((68, 196), s["title"], font=font(FB, 42), fill=INK, anchor="la")
    # 同步卡: 说到哪张, 哪张才出现; 当前拍高亮, 过拍变暗
    for j, b in enumerate(s["beats"]):
        if t < starts[j] - 0.35 + 0.35 and j > bi: break
        if j > bi: break
        ap = ease((t - starts[j]) / .35); y = 272 + j * 68
        bright = 1.0 if j == bi else .45
        rr(d, [64, y, 534, y + 52], 11, fill=(255, 255, 255, int(20 * ap * bright + 4)), outline=acc + (int(230 * ap) if j == bi else int(70 * ap),), width=2 if j == bi else 1)
        d.ellipse([82, y + 20, 94, y + 32], fill=acc)
        d.text((108, y + 26), b[1], font=font(FM, 24), fill=(INK[0], INK[1], INK[2], int(255 * ap * bright + 60)), anchor="lm")
    stage_visual(d, si, bi, bf, t, acc)
    # 章节进度条(按真实时间)
    seg_w, gap, x0, y0 = 158, 12, 64, 662
    done_before = sum(x["dur"] for x in SCENES[:si])
    for i in range(len(SCENES)):
        x = x0 + i * (seg_w + gap); rr(d, [x, y0, x + seg_w, y0 + 7], 3, fill=(255, 255, 255, 28))
        fw = seg_w if i < si else (seg_w * clamp(t / s["dur"]) if i == si else 0)
        if fw: rr(d, [x, y0, x + fw, y0 + 7], 3, fill=SCENES[i]["accent"])
    # karaoke 字幕: 已读字=白色, 未读=暗色, 按拍内字数比例推进
    say = s["beats"][bi][0]
    if t >= starts[bi] - 0.35:
        f = font(FB, 33); spoken = int(len(say) * clamp((t - starts[bi] + 0.0) / max(.01, bend - starts[bi])))
        # 分行(<=24字)
        lines, cur = [], ""
        for ch in say:
            if len(cur) >= 24: lines.append(cur); cur = ch
            else: cur += ch
        if cur: lines.append(cur)
        total_w = [d.textlength(ln, font=f) for ln in lines]
        yy = 600 - (len(lines) - 1) * 22; consumed = 0
        for li, ln in enumerate(lines):
            x = (W - total_w[li]) / 2
            for ch in ln:
                col = INK if consumed < spoken else (120, 130, 155)
                d.text((x, yy), ch, font=f, fill=col, anchor="lm", stroke_width=4, stroke_fill=(0, 0, 0))
                x += d.textlength(ch, font=f); consumed += 1
            yy += 44
    # 极缓推镜(反PPT): 全章 1.00->1.055
    zoom = 1 + 0.055 * clamp(t / s["dur"])
    if zoom > 1.001:
        zw, zh = int(W * zoom), int(H * zoom)
        img = img.resize((zw, zh), Image.LANCZOS).crop(((zw - W) // 2, (zh - H) // 2, (zw + W) // 2, (zh + H) // 2))
    if fade < 1: img = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), img, fade)
    return img

def main():
    wavs = []
    for i, s in enumerate(SCENES, 1):
        wv = os.path.join(ROOT, f"_v{i}.wav")
        subprocess.run([FF, "-y", "-i", s["voice"], "-af", "adelay=350|350,apad", "-t", f"{s['dur']}", "-ar", "44100", wv], capture_output=True, check=True)
        wavs.append(wv)
    lst = os.path.join(ROOT, "_list.txt"); open(lst, "w").write("".join(f"file '{w}'\n" for w in wavs))
    subprocess.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, os.path.join(ROOT, "narration.wav")], capture_output=True, check=True)
    proc = subprocess.Popen([FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                             "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium", os.path.join(ROOT, "_silent.mp4")],
                            stdin=subprocess.PIPE)
    total = int(TOTAL * FPS)
    for fr in range(total):
        proc.stdin.write(draw_frame(fr / FPS).tobytes())
        if fr % 480 == 0: print(f"frame {fr}/{total}", flush=True)
    proc.stdin.close(); proc.wait()
    out = os.path.join(ROOT, "人工智能发展史-v2同步版.mp4")
    subprocess.run([FF, "-y", "-i", os.path.join(ROOT, "_silent.mp4"), "-i", os.path.join(ROOT, "narration.wav"), "-i", os.path.join(ROOT, "music.wav"),
                    "-filter_complex", "[2:a]volume=0.5[m];[1:a][m]amix=inputs=2:duration=first[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", out], capture_output=True, check=True)
    for w in wavs: os.remove(w)
    os.remove(lst); print("DONE", out, flush=True)

if __name__ == "__main__":
    main()
