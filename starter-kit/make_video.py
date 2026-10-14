#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_video.py —— 「生图 → 加字 → 竖屏成片」的最小可跑流水线（纯 ffmpeg + PIL，无 API Key）

它做的事，正好是抖音上「人生感悟 / 情感语录 / 图文成片」那一类视频的骨架：

    几张图（本机 ComfyUI 生图、AI 生图工具导出的图、或自己拍的图）
      → 缓慢推拉运镜（Ken Burns，画面不"死"）
      → 花字标题 + 底部字幕（关键词自动高亮，中文逐字回退渲染）
      → 一层自己合成出来的 BGM（零版权、零素材）
      → 1080×1920 / 30fps / H.264 成片，可直接发抖音 / 视频号 / 小红书

全程不联网、不调任何 API、不需要剪映。
实现要点（都是踩过坑才改的）：
  * 花字/字幕不用 libass 烧，而是 PIL 渲染成透明 PNG 再 overlay：
    中文子集字体在无桌面机器上 fontconfig 常常扫不到，libass 会直接出"豆腐块"；
    自己渲染则可以精确控制描边、阴影、高亮、字距和换行（含中文的行首禁则）。
  * 叠字**分批**做（每批 ≤3 层），避免小内存机器上 filter graph 报
    "Cannot allocate memory"。
  * 音频最后单独封装（视频流 copy），不重编码画面。

依赖：
    pip install imageio-ffmpeg pillow fonttools brotli
    python3 tools/fetch_fonts.py        # 首次跑一次，拉中文字体

用法：
    python3 make_video.py script.example.json -o out/demo.mp4 --srt --cover
    python3 make_video.py script.json -o out/x.mp4 --bgm out/bgm_sad.m4a
    python3 make_video.py script.json -o out/x.mp4 --no-bgm        # 只要画面
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

try:
    import imageio_ffmpeg

    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:  # pragma: no cover
    FFMPEG = "ffmpeg"

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "tools"))

from textimg import FontBook, render_text, save_png  # noqa: E402

# ------------------------------------------------------------------ 主题
# 情感/感悟：毛笔楷花字 + 暖金高亮；搞笑/日常：快乐体；AI 科普：黑体，冷静留白
THEMES = {
    "warm": {
        "title_family": "ma-shan-zheng-400", "body_family": "noto-sans-sc-700",
        "title_colour": (255, 252, 246, 255), "hi_colour": (255, 214, 138, 255),
        "title_stroke": (40, 28, 24, 235), "body_colour": (255, 255, 255, 255),
        "body_stroke": (18, 16, 20, 235),
    },
    "funny": {
        "title_family": "zcool-kuaile-400", "body_family": "noto-sans-sc-700",
        "title_colour": (255, 255, 255, 255), "hi_colour": (255, 233, 122, 255),
        "title_stroke": (120, 40, 32, 235), "body_colour": (255, 255, 255, 255),
        "body_stroke": (18, 16, 20, 235),
    },
    "tech": {
        "title_family": "noto-sans-sc-700", "body_family": "noto-sans-sc-400",
        "title_colour": (245, 248, 255, 255), "hi_colour": (140, 224, 255, 255),
        "title_stroke": (18, 40, 56, 235), "body_colour": (255, 255, 255, 255),
        "body_stroke": (14, 20, 26, 235),
    },
}


def run(cmd: list[str]) -> None:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        print("ffmpeg 失败：\n" + " ".join(cmd) + "\n" + p.stderr[-3000:], file=sys.stderr)
        raise SystemExit(p.returncode)


# ------------------------------------------------------------------ 单镜头
def render_clip(img: str, out: str, dur: float, size: tuple[int, int], fps: int, motion: str) -> None:
    """一张图 → 一段带推拉运镜的竖屏镜头（Ken Burns）。"""
    w, h = size
    sw, sh = int(w * 1.5), int(h * 1.5)          # 先放大 1.5 倍再裁，运镜不糊
    n = max(2, int(round(dur * fps)))
    k = min(0.16, 14.0 / n)                       # 整段最多推 16%，长短镜头观感一致
    if motion in ("in", "zoom_in"):
        z, x, y = f"1+{k:.4f}*on", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif motion in ("out", "zoom_out"):
        z, x, y = f"{1 + k:.4f}-{k:.4f}*on", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif motion == "pan_left":
        z, x, y = "1.14", f"(iw-iw/zoom)*(1-on/{n})", "ih/2-(ih/zoom/2)"
    elif motion == "pan_right":
        z, x, y = "1.14", f"(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"
    else:                                          # static
        z, x, y = "1", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    vf = (
        f"scale={sw}:{sh}:force_original_aspect_ratio=increase,"
        f"crop={sw}:{sh},setsar=1,"
        f"zoompan=z='{z}':x='{x}':y='{y}':d=1:s={w}x{h}:fps={fps},"
        f"format=yuv420p"
    )
    run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
         "-loop", "1", "-framerate", str(fps), "-t", f"{dur:.3f}", "-i", img,
         "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", out])


def concat_clips(clips: list[str], durs: list[float], out: str, fps: int,
                 transition: dict | None) -> None:
    """拼接镜头：有转场走 xfade，没有就直接拷流。"""
    if not transition or float(transition.get("duration", 0)) <= 0:
        lst = out + ".txt"
        with open(lst, "w", encoding="utf-8") as f:
            for c in clips:
                f.write(f"file '{os.path.abspath(c)}'\n")
        run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
             "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])
        os.remove(lst)
        return

    x = float(transition["duration"])
    kind = transition.get("type", "fade")
    inputs: list[str] = []
    for c in clips:
        inputs += ["-i", c]
    fc, acc, prev = [], durs[0], "[0:v]"
    for i in range(1, len(clips)):
        off = max(0.0, acc - x)
        tag = f"[v{i}]"
        fc.append(f"{prev}[{i}:v]xfade=transition={kind}:duration={x:.3f}:offset={off:.3f}{tag}")
        prev = tag
        acc = acc + durs[i] - x
    run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", *inputs,
         "-filter_complex", ";".join(fc), "-map", prev, "-r", str(fps),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", out])


# ------------------------------------------------------------------ 字幕 / 花字
def build_overlays(script: dict, times: list[tuple[float, float]], work: str,
                   book: FontBook) -> list[dict]:
    """把每条花字/字幕渲染成透明 PNG，并算出它在画面上出现的时间与位置。"""
    w, h = script.get("size", [1080, 1920])
    style = script.get("style", {})
    th = THEMES.get(style.get("theme", "warm"), THEMES["warm"])
    margin_v = int(style.get("sub_margin_v", h * 0.22))
    title_size = int(style.get("title_size", h * 0.082))
    sub_size = int(style.get("sub_size", h * 0.038))
    note_size = int(sub_size * 0.68)
    ovs: list[dict] = []

    for i, (shot, (start, end)) in enumerate(zip(script["shots"], times)):
        if shot.get("title"):
            png = save_png(render_text(
                shot["title"], book, family=th["title_family"], size=title_size,
                colour=th["title_colour"], hi_colour=th["hi_colour"],
                stroke=max(3, title_size // 13), stroke_colour=th["title_stroke"],
                shadow=max(4, title_size // 16), shadow_alpha=140,
                max_width=int(w * 0.86), line_gap=0.16),
                os.path.join(work, f"ov{i:02d}_title.png"))
            a, b = start + 0.10, min(end, start + 0.10 + (end - start) * 0.66)
            ovs.append({"png": png, "anchor": "title", "start": a, "end": b})
        if shot.get("sub"):
            png = save_png(render_text(
                shot["sub"], book, family=th["body_family"], size=sub_size,
                colour=th["body_colour"], hi_colour=th["hi_colour"],
                stroke=max(3, sub_size // 11), stroke_colour=th["body_stroke"],
                shadow=max(2, sub_size // 20), shadow_alpha=150,
                max_width=int(w * 0.84), line_gap=0.30),
                os.path.join(work, f"ov{i:02d}_sub.png"))
            a = start + float(shot.get("sub_delay", 0.18))
            b = max(a + 0.5, end - float(shot.get("sub_hold", 0.24)))
            ovs.append({"png": png, "anchor": "sub", "start": a, "end": b, "margin_v": margin_v})
        if shot.get("note"):
            png = save_png(render_text(
                shot["note"], book, family="noto-sans-sc-400", size=note_size,
                colour=(214, 214, 214, 235), stroke=2, stroke_colour=(20, 20, 20, 200),
                shadow=1, max_width=int(w * 0.8)),
                os.path.join(work, f"ov{i:02d}_note.png"))
            ovs.append({"png": png, "anchor": "note", "start": start + 0.4, "end": end - 0.3,
                        "margin_v": int(h * 0.045)})
    return ovs


def write_srt(script: dict, times: list[tuple[float, float]], path: str) -> None:
    def ts(t: float) -> str:
        ms = int(round(t * 1000))
        return f"{ms // 3600000:02d}:{ms % 3600000 // 60000:02d}:{ms % 60000 // 1000:02d},{ms % 1000:03d}"

    with open(path, "w", encoding="utf-8") as f:
        idx = 1
        for shot, (a, b) in zip(script["shots"], times):
            text = shot.get("sub") or shot.get("title")
            if not text:
                continue
            f.write(f"{idx}\n{ts(a + 0.18)} --> {ts(max(a + 0.6, b - 0.2))}\n"
                    f"{text.replace('**', '').replace(chr(92) + 'n', chr(10))}\n\n")
            idx += 1


# ------------------------------------------------------------------ 叠字（分批）
def compose_video(video_in: str, overlays: list[dict], out: str, h: int, fps: int,
                  total: float, work: str, chunk: int = 3) -> None:
    """把文字层分批 overlay 到画面上（每批 ≤ chunk 层，避免内存爆掉）。"""
    if not overlays:
        run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-i", video_in,
             "-c", "copy", out])
        return
    cur = video_in
    groups = [overlays[i:i + chunk] for i in range(0, len(overlays), chunk)]
    for gi, group in enumerate(groups):
        last = gi == len(groups) - 1
        target = out if last else os.path.join(work, f"pass{gi:02d}.mp4")
        inputs = ["-i", cur]
        for ov in group:
            inputs += ["-loop", "1", "-framerate", str(fps), "-t", f"{total:.3f}", "-i", ov["png"]]
        fc, prev = [], "[0:v]"
        for n, ov in enumerate(group, start=1):
            a, b = ov["start"], ov["end"]
            fade = 0.22
            y_expr = {
                "title": f"{int(h * 0.135)}+34*max(0\\,1-(t-{a:.2f})/0.55)",
                "sub": f"H-{ov.get('margin_v', int(h * 0.22))}-h",
                "note": f"H-{ov.get('margin_v', int(h * 0.045))}-h",
            }[ov["anchor"]]
            fc.append(f"[{n}:v]format=rgba,fade=t=in:st={a:.2f}:d={fade}:alpha=1,"
                      f"fade=t=out:st={max(a, b - fade):.2f}:d={fade}:alpha=1[o{n}]")
            fc.append(f"{prev}[o{n}]overlay=x=(W-w)/2:y='{y_expr}':"
                      f"enable='between(t,{a:.2f},{b:.2f})':format=auto[v{n}]")
            prev = f"[v{n}]"
        print(f"[叠字] 第 {gi + 1}/{len(groups)} 批（{len(group)} 层）")
        run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", *inputs,
             "-filter_complex", ";".join(fc), "-map", prev, "-t", f"{total:.3f}",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "16" if last else "14",
             "-pix_fmt", "yuv420p", target])
        cur = target


# ------------------------------------------------------------------ 混音
def synthesize_bgm(seconds: float, mood: str, out: str) -> str:
    from make_bgm import synth  # type: ignore

    inputs, fc = synth(mood, seconds)
    run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", *inputs,
         "-filter_complex", fc, "-map", "[out]", "-c:a", "aac", "-b:a", "128k", out])
    return out


# ------------------------------------------------------------------ 主流程
def main() -> int:
    ap = argparse.ArgumentParser(description="生图 → 加字 → 竖屏成片（无 API，纯 ffmpeg + PIL）")
    ap.add_argument("script")
    ap.add_argument("-o", "--out", default="out/video.mp4")
    ap.add_argument("--fonts", default=os.path.join(HERE, "fonts"))
    ap.add_argument("--bgm", default=None, help="自带 BGM 文件；不给就用代码合成的")
    ap.add_argument("--no-bgm", action="store_true")
    ap.add_argument("--srt", action="store_true", help="同时导出 .srt 外挂字幕")
    ap.add_argument("--cover", action="store_true", help="同时导出封面图")
    ap.add_argument("--workdir", default=None, help="中间文件目录（默认输出目录下的 _work）")
    args = ap.parse_args()

    with open(args.script, encoding="utf-8") as f:
        script = json.load(f)
    base = os.path.dirname(os.path.abspath(args.script))
    size = tuple(script.get("size", [1080, 1920]))
    w, h = size
    fps = int(script.get("fps", 30))
    shots = script["shots"]
    work = args.workdir or os.path.join(os.path.dirname(os.path.abspath(args.out)) or ".", "_work")
    os.makedirs(work, exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)

    if not os.path.isdir(args.fonts):
        print("找不到字体目录，先跑：python3 tools/fetch_fonts.py", file=sys.stderr)
        return 2
    book = FontBook(args.fonts)

    # 1) 每个镜头：图 → 带运镜的片段
    clips, durs, times = [], [], []
    t = 0.0
    trans = script.get("transition") or {}
    xf = float(trans.get("duration", 0)) if trans else 0.0
    for i, shot in enumerate(shots):
        dur = float(shot.get("duration", 4.0))
        img = shot["image"]
        if not os.path.isabs(img):
            cand = os.path.join(base, img)
            img = cand if os.path.exists(cand) else img
        if not os.path.exists(img):
            print(f"找不到图片：{shot['image']}", file=sys.stderr)
            return 2
        clip = os.path.join(work, f"clip{i:02d}.mp4")
        print(f"[{i + 1}/{len(shots)}] 运镜 {shot.get('motion', 'in'):<9} {dur:.1f}s  {os.path.basename(img)}")
        render_clip(img, clip, dur, size, fps, shot.get("motion", "in"))
        clips.append(clip)
        durs.append(dur)
        times.append((t, t + dur))
        t += dur - (xf if i < len(shots) - 1 else 0)
    total = t

    # 2) 拼接
    silent = os.path.join(work, "silent.mp4")
    print("[拼接] " + (f"转场 {trans.get('type', 'fade')} {xf:.2f}s" if xf > 0 else "硬切"))
    concat_clips(clips, durs, silent, fps, trans if xf > 0 else None)

    # 3) 花字 + 字幕 → 透明 PNG
    overlays = build_overlays(script, times, work, book)
    print(f"[花字] 渲染 {len(overlays)} 层文字（PIL + 逐字字体回退）")
    if args.srt:
        write_srt(script, times, os.path.splitext(args.out)[0] + ".srt")
        print(f"[字幕] {os.path.splitext(args.out)[0]}.srt")

    # 4) 叠字：分批 overlay（每批最多 3 层）
    #    原因：一次把十几个 PNG 塞进同一个 filter_complex，ffmpeg 要为每一路
    #    维护帧队列，小内存机器上会直接 "Cannot allocate memory" 挂掉。
    #    分批做，逐批把结果作为下一批的输入，稳而且内存占用固定。
    texted = os.path.join(work, "texted.mp4")
    compose_video(silent, overlays, texted, h, fps, total, work)

    # 5) 混音：合成 BGM + 可选配音（单独一遍，只处理音频，很快）
    audio_inputs, audio_filters, mix_tags = [], [], []
    ain = 1   # 最终命令里 0 号输入是叠好字的视频，音频从 1 开始
    bgm_cfg = script.get("bgm", {})
    if not args.no_bgm:
        bgm_file = args.bgm
        if bgm_file is None and bgm_cfg.get("mode", "auto") == "auto":
            bgm_file = os.path.join(work, f"bgm_{bgm_cfg.get('mood', 'warm')}.m4a")
            print(f"[BGM ] 合成氛围垫音（{bgm_cfg.get('mood', 'warm')}，{total + 2:.1f}s）")
            synthesize_bgm(total + 2.0, bgm_cfg.get("mood", "warm"), bgm_file)
        if bgm_file and os.path.exists(bgm_file):
            audio_inputs += ["-i", bgm_file]
            vol = float(bgm_cfg.get("volume", 0.22))
            audio_filters.append(f"[{ain}:a]volume={vol},atrim=0:{total + 0.5:.2f}[bg]")
            mix_tags.append("[bg]")
            ain += 1
    for shot, (start, _) in zip(shots, times):
        v = shot.get("voice")
        if not v:
            continue
        if not os.path.isabs(v):
            cand = os.path.join(base, v)
            v = cand if os.path.exists(cand) else v
        if not os.path.exists(v):
            print(f"警告：配音不存在，已跳过 {shot['voice']}", file=sys.stderr)
            continue
        audio_inputs += ["-i", v]
        ms = int(max(0.0, start + float(shot.get("voice_delay", 0.12))) * 1000)
        audio_filters.append(f"[{ain}:a]volume=1.0,adelay={ms}|{ms}[vo{ain}]")
        mix_tags.append(f"[vo{ain}]")
        ain += 1

    # 6) 封装：视频流直接 copy + 混好的音轨
    print("[成片] 混音 + 封装")
    if mix_tags:
        if len(mix_tags) == 1:
            audio_filters.append(f"{mix_tags[0]}anull[a]")
        else:
            audio_filters.append("".join(mix_tags)
                                 + f"amix=inputs={len(mix_tags)}:normalize=0:dropout_transition=0[a]")
        cmd = [FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-i", texted, *audio_inputs,
               "-filter_complex", ";".join(audio_filters), "-map", "0:v", "-map", "[a]",
               "-t", f"{total:.3f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", args.out]
        run(cmd)
    else:
        run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-i", texted,
             "-t", f"{total:.3f}", "-c", "copy", args.out])

    if args.cover:
        cover = os.path.splitext(args.out)[0] + "_cover.jpg"
        run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
             "-ss", f"{min(1.6, total / 3):.2f}", "-i", args.out,
             "-frames:v", "1", "-update", "1", "-q:v", "2", cover])
        print(f"[封面] {cover}")

    print(f"\n成片：{args.out}  {w}×{h}  {fps}fps  {total:.2f}s  "
          f"{os.path.getsize(args.out) / 1e6:.1f}MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
