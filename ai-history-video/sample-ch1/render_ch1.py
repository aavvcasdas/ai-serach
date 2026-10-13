#!/usr/bin/env python3
"""第一章样片: 逐块配音->块首帧精确锚点; 单镜头; Hero主角; 按SHOTBOOK逐拍实现"""
import math, os, random, re, subprocess, sys
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
INK, SUB, DIM = (240, 244, 255), (175, 188, 215), (105, 118, 150)
PUR, CYN, PNK, GRN = (160, 120, 255), (70, 200, 255), (255, 110, 180), (80, 230, 170)

BLOCKS = [
    ("一九五零年，英国数学家图灵提出了一个问题：", "c1.mp3"),
    ("机器，能思考吗？", "c2.mp3"),
    ("他设计了著名的图灵测试：", "c3.mp3"),
    ("如果你分不清屏幕对面是人还是机器，", "c4.mp3"),
    ("那么机器，就算是会思考了。", "c5.mp3"),
    ("这个问题，点燃了人工智能七十多年的故事。", "c6.mp3"),
]
def dur(p):
    o = subprocess.run([FF, "-i", p], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", o); return int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))

LEAD, GAP, TAIL = 0.45, 10/FPS, 1.35
starts, t = [], LEAD
for txt, f in BLOCKS:
    d = dur(os.path.join(ROOT, "assets", f)); starts.append(t); t += d + GAP
TOTAL = t - GAP + TAIL
DURS = [dur(os.path.join(ROOT, "assets", f)) for _, f in BLOCKS]
print("blocks:", [round(x,2) for x in starts], "total", round(TOTAL,1), flush=True)

random.seed(42)
bg = Image.new("RGB", (W, H), (7, 11, 20)); bd = ImageDraw.Draw(bg, "RGBA")
for y in range(H): bd.line([(0, y), (W, y)], fill=(60, 40, 110, int(26*(y/H)**2)))
stars = [(random.randint(0, W-1), random.randint(0, H-1), random.choice([1,1,2]), random.random()*6.28) for _ in range(170)]
for x, y, r, _ in stars: bd.ellipse([x, y, x+r, y+r], fill=(200, 215, 255, 130))
bg = bg.filter(ImageFilter.GaussianBlur(0.4))

def ease(t): return 1-(1-max(0,min(1,t)))**3
def clamp(t): return max(0.0, min(1.0, t))
def rr(d, b, r, **k): d.rounded_rectangle(b, radius=r, **k)

def glow(base, cx, cy, rad, col, alpha):
    layer = Image.new("RGBA", (W, H), (0,0,0,0)); gd = ImageDraw.Draw(layer)
    gd.ellipse([cx-rad, cy-rad, cx+rad, cy+rad], fill=col+(alpha,))
    base.paste(Image.alpha_composite(base.convert("RGBA"), layer.filter(ImageFilter.GaussianBlur(45))).convert("RGB"), (0,0))
    return base

def draw(tg):
    # current block
    bi = 0
    for i, st in enumerate(starts):
        if tg >= st: bi = i
    st = starts[bi]; p = clamp((tg-st)/DURS[bi]) if tg >= st else 0
    img = bg.copy()
    # B4起主角柔光
    if bi >= 4: img = glow(img, 640, 300, 190, (110, 60, 220), 70)
    d = ImageDraw.Draw(img, "RGBA")
    for x, y, r, ph in stars:
        d.ellipse([x, y, x+r, y+r], fill=(200,215,255, int(90+60*math.sin(tg*2+ph))))
    # HUD
    hud = "人工智能发展史 · 第一章样片"
    rr(d, [44, 34, 44+d.textlength(hud, font=font(FM,20))+34, 70], 18, fill=(255,255,255,16), outline=(255,255,255,40))
    d.text((61, 52), hud, font=font(FM,20), fill=SUB, anchor="lm")
    d.text((1236, 52), "起源 · 图灵", font=font(FM,20), fill=CYN, anchor="rm")
    fade = min(clamp(tg/.4), clamp((TOTAL-tg)/.42))

    if bi == 0:
        # 年份计数 1900->1950
        yr = int(1900 + 50*ease(p*1.4))
        d.text((150, 300), str(yr), font=font(FB, 120), fill=CYN, anchor="lm")
        if p > .25:
            a = ease((p-.25)*3)
            rr(d, [152, 392, 152+300*a, 452], 12, fill=(255,255,255, int(14*a)), outline=PUR+(int(160*a),))
            d.text((172, 422), "图灵  Turing", font=font(FB, 30), fill=INK, anchor="lm")
        d.text((150, 478), "《计算机器与智能》", font=font(FM, 24), fill=SUB, anchor="lm")
        # 预埋屏幕框 draw-on
        pr = clamp(p*1.2); x0,y0,x1,y1 = 760,190,1140,470; L=(x1-x0)*2+(y1-y0)*2; ln = L*pr
        pts=[(x0,y0),(x1,y0),(x1,y1),(x0,y1),(x0,y0)]; drawn=0
        for i in range(4):
            seg = math.dist(pts[i], pts[i+1])
            if drawn+seg <= ln: d.line([pts[i], pts[i+1]], fill=CYN, width=3)
            elif drawn < ln:
                q=(ln-drawn)/seg; d.line([pts[i], (pts[i][0]+(pts[i+1][0]-pts[i][0])*q, pts[i][1]+(pts[i+1][1]-pts[i][1])*q)], fill=CYN, width=3)
            drawn+=seg
    elif bi == 1:
        # Hero ? GlitchIn 12帧 + 光圈 + 思考脉冲
        n = (tg-st)*FPS
        cx, cy = 640, 315
        for i in range(3):
            r_ = 90 + ((tg*45+i*60) % 170)
            d.ellipse([cx-r_, cy-r_, cx+r_, cy+r_], outline=CYN+(int(80*(1-r_/270)),), width=3)
        scale = 1.0
        # 说到"思考"(约p .45-.75)脉冲
        if .4 < p < .95:
            q = (p-.4)/.55; scale = 1 + .11*math.sin(q*math.pi)
        size = int(215*scale*ease(min(1, n/10)))
        if n < 12 and int(n) % 3 == 0:  # glitch切片感: 偏移副本
            d.text((cx+7, cy), "?", font=font(FB, size), fill=PNK+(150,), anchor="mm")
            d.text((cx-7, cy), "?", font=font(FB, size), fill=CYN+(150,), anchor="mm")
        d.text((cx, cy), "?", font=font(FB, size), fill=INK, anchor="mm")
        d.text((cx, cy+168), "机器，能思考吗？", font=font(FB, 34), fill=SUB, anchor="mm")
    elif bi in (2, 3):
        # 屏幕主角; B2: ?承接缩小到屏幕上方; B3: 双框互换
        cx, cy = 640, 310
        move = ease(((tg-st)*FPS)/16) if bi == 2 else 1
        qsize = int(215 - 145*move) if bi == 2 else 70
        qy = int(315 - 205*move) if bi == 2 else 110
        d.text((cx, qy), "?", font=font(FB, qsize), fill=PUR, anchor="mm")
        rr(d, [350, 170, 930, 480], 18, outline=CYN, width=3, fill=(16, 22, 40, 255))
        d.rectangle([350, 170, 930, 208], fill=(30, 40, 66))
        for j, col in enumerate([(255,95,86),(255,189,46),(39,201,63)]):
            d.ellipse([368+j*26, 182, 382+j*26, 196], fill=col)
        label = "图灵测试 TURING TEST"
        typed = label[:int(len(label)*clamp(p*1.6))] if bi == 2 else label
        d.text((640, 189), typed, font=font(FM, 20), fill=INK, anchor="mm")
        if bi == 2:
            d.text((640, 330), "屏幕对面，是谁？", font=font(FB, 40), fill=SUB, anchor="mm")
        else:
            # 双框: 说到 分不清(p~.35) 起互换
            swap = ease((p-.35)/.3) if p > .35 else 0
            boxes = []
            for j, (lab, col) in enumerate([("人 类", CYN), ("机 器", PUR)]):
                bx = 410 + j*250 + (250-500*j)*swap
                lab2 = "？ ？" if swap > .6 else lab
                rr(d, [bx, 245, bx+180, 385], 16, fill=(255,255,255,14), outline=col, width=3)
                d.ellipse([bx+68, 272, bx+112, 316], outline=INK, width=3)
                d.arc([bx+55, 315, bx+125, 375], 180, 360, fill=INK, width=3)
                d.text((bx+90, 358), lab2, font=font(FB, 27), fill=INK, anchor="mm")
                boxes.append(bx)
            if swap > .6:
                d.text((640, 432), "分不清！", font=font(FB, 34), fill=PNK, anchor="mm")
    elif bi == 4:
        cx, cy = 640, 290
        d.text((cx, 118), "?", font=font(FB, 66), fill=PUR, anchor="mm")
        rr(d, [350, 170, 930, 470], 18, outline=CYN, width=3, fill=(16, 22, 40, 255))
        # 对勾 draw-on
        pr = clamp(p*2.2)
        pts = [(520, 320), (610, 405), (770, 235)]; total = math.dist(pts[0],pts[1])+math.dist(pts[1],pts[2]); ln = total*pr; drawn=0
        for i in range(2):
            seg = math.dist(pts[i], pts[i+1])
            if drawn+seg <= ln: d.line([pts[i], pts[i+1]], fill=GRN, width=14, joint="curve")
            elif drawn < ln:
                q=(ln-drawn)/seg; d.line([pts[i], (pts[i][0]+(pts[i+1][0]-pts[i][0])*q, pts[i][1]+(pts[i+1][1]-pts[i][1])*q)], fill=GRN, width=14)
            drawn += seg
        if p > .45:
            a = ease((p-.45)*2.5)
            sz = int(64*(0.7+0.3*a))
            d.text((640, 505), "会思考", font=font(FB, sz), fill=(INK[0],INK[1],INK[2],int(255*a)), anchor="mm")
    else:  # B5 时间线点燃
        d.text((640, 128), "?", font=font(FB, 60), fill=PUR, anchor="mm")
        d.text((640, 195), "一个问题，点燃了……", font=font(FB, 36), fill=SUB, anchor="mm")
        y = 385; x0, x1 = 170, 1110; pr = ease(p*1.15)
        d.line([x0, y, x1, y], fill=(70,80,105), width=4)
        d.line([x0, y, x0+(x1-x0)*pr, y], fill=CYN, width=5)
        yrs = [(1950,"图灵"),(1956,"诞生"),(2012,"深度学习"),(2017,"Transformer"),(2022,"大模型"),(2026,"今天")]
        for j, (yv, lab) in enumerate(yrs):
            frac = j / (len(yrs) - 1)
            x = x0 + (x1-x0)*frac
            on = frac <= pr
            if on:
                pop = 1 + .5*max(0, 1-abs(pr-frac)*8)
                d.ellipse([x-8*pop, y-8*pop, x+8*pop, y+8*pop], fill=PUR if j==0 else CYN)
                d.text((x, y-42), str(yv), font=font(FB, 23), fill=INK, anchor="mm")
                d.text((x, y+38), lab, font=font(FM, 20), fill=SUB, anchor="mm")
        # 火花
        sx = x0+(x1-x0)*pr
        for k in range(8):
            ang = k*0.785 + tg*3; rad = 8+6*math.sin(tg*9+k)
            d.ellipse([sx+rad*math.cos(ang)-3, y+rad*math.sin(ang)-3, sx+rad*math.cos(ang)+3, y+rad*math.sin(ang)+3], fill=(255,200,90))
        if p > .7:
            a = ease((p-.7)*3)
            d.text((640, 520), "人工智能 70+ 年的故事，由此开始", font=font(FB, 32), fill=(INK[0],INK[1],INK[2],int(255*a)), anchor="mm")
    # 运镜: B3 推近 40帧 1->1.13, 之后保持; 其余 1.0->1.04 慢推
    if bi == 3: zoom = 1.04 + .09*ease(((tg-st)*FPS)/40)
    elif bi > 3: zoom = 1.13
    else: zoom = 1 + .04*clamp(tg/TOTAL)
    # 字幕 karaoke + 块进度刻度
    say = BLOCKS[bi][0]
    if tg >= st:
        spoken = int(len(say)*p) if bi < 5 or True else len(say)
        f = font(FB, 34); tw = d.textlength(say, font=f); x = (W-tw)/2; yy = 618
        for j, ch in enumerate(say):
            col = INK if j < spoken else (115,128,158)
            d.text((x, yy), ch, font=f, fill=col, anchor="lm", stroke_width=4, stroke_fill=(0,0,0))
            x += d.textlength(ch, font=f)
    # 底部: 6块刻度进度
    seg = (W-128)/6
    for j in range(6):
        x = 64 + j*seg
        rr(d, [x, 682, x+seg-10, 688], 3, fill=(255,255,255,26))
        fw = seg-10 if j < bi else ((seg-10)*p if j == bi else 0)
        if fw: rr(d, [x, 682, x+fw, 688], 3, fill=CYN if j<5 else PUR)
    if zoom > 1.001:
        zw, zh = int(W*zoom), int(H*zoom)
        img = img.resize((zw, zh), Image.LANCZOS).crop(((zw-W)//2, (zh-H)//2, (zw+W)//2, (zh+H)//2))
    if fade < 1: img = Image.blend(Image.new("RGB", (W,H), (0,0,0)), img, fade)
    return img

def main():
    # 旁白: 逐块按起始采样点拼 (adelay精确)
    filters, labels = [], []
    for i, st in enumerate(starts):
        ms = int(st*1000)
        filters.append(f"[{i}:a]adelay={ms}|{ms},apad[a{i}]"); labels.append(f"[a{i}]")
    fc = ";".join(filters) + ";" + "".join(labels) + f"amix=inputs={len(starts)}:duration=first,atrim=0:{TOTAL}[a]"
    args = [FF, "-y"]
    for _, f in BLOCKS: args += ["-i", os.path.join(ROOT, "assets", f)]
    args += ["-filter_complex", fc, "-map", "[a]", "-ar", "44100", os.path.join(ROOT, "narration.wav")]
    subprocess.run(args, capture_output=True, check=True)
    proc = subprocess.Popen([FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium", os.path.join(ROOT, "_s.mp4")], stdin=subprocess.PIPE)
    total = int(TOTAL*FPS)
    for fr in range(total):
        proc.stdin.write(draw(fr/FPS).tobytes())
        if fr % 240 == 0: print(f"{fr}/{total}", flush=True)
    proc.stdin.close(); proc.wait()
    out = os.path.join(ROOT, "第一章-图灵之问-样片.mp4")
    subprocess.run([FF, "-y", "-i", os.path.join(ROOT, "_s.mp4"), "-i", os.path.join(ROOT, "narration.wav"), "-i", os.path.join(ROOT, "..", "music.wav"),
        "-filter_complex", "[2:a]volume=0.45[m];[1:a][m]amix=inputs=2:duration=first[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", out], capture_output=True, check=True)
    os.remove(os.path.join(ROOT, "_s.mp4")); print("DONE", out, flush=True)

if __name__ == "__main__":
    main()
