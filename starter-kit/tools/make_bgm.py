#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_bgm.py —— 用 ffmpeg 现场合成 BGM（零素材、零版权、零 API）

情感/感悟类视频的「情绪」有一半来自背景音乐。这里不下载任何音频素材，
直接用 ffmpeg 的合成器叠出几种常见氛围垫底音（可当底噪人声/钢琴的替身，
也可以只做「不空耳」的过渡垫），全部由代码生成，永不撞版权。

用法：
  python3 tools/make_bgm.py --seconds 20 --mood warm  -o out/bgm_warm.m4a
  python3 tools/make_bgm.py --seconds 20 --mood sad   -o out/bgm_sad.m4a
  python3 tools/make_bgm.py --seconds 20 --mood tech  -o out/bgm_tech.m4a   # 科普/知识类

mood 说明：
  warm  温暖平和（A 小调 + 五度泛音，慢起慢落）—— 情感/感悟/日常
  sad   低沉孤独（D 小调，慢速震音，低通更重）—— 伤感/回忆
  tech  干净脉冲（等间隔 1/4 拍垫音 + 高通）—— AI 科普/知识口播
注意：这是合成氛围音，不是成品配乐；发布前请确认音量不盖过字幕节奏。
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:  # pragma: no cover
    FFMPEG = "ffmpeg"

# 音高（Hz）：A3=220, C4=261.63, E4=329.63, D4=293.66, F4=349.23, G4=392
MOODS = {
    # warm: Am - F - C - G 的慢速长音铺底
    "warm": ["220.00", "261.63", "329.63", "349.23"],
    "sad": ["146.83", "174.61", "220.00", "293.66"],
    "tech": ["261.63", "392.00", "523.25"],
}


def synth(mood: str, seconds: float) -> str:
    freqs = MOODS.get(mood, MOODS["warm"])
    n = len(freqs)
    # 每个音一条 sine，互相错开相位；再叠一个慢速震音 + 低通 + 回声，做成"垫子"
    parts = []
    for i, f in enumerate(freqs):
        det = 1.0 + (i - n / 2) * 0.0006  # 轻微失谐，让声音更"厚"
        parts.append(
            f"sine=frequency={float(f)*det:.3f}:duration={seconds:.3f}"
            f",volume={0.32/max(1, n-1):.3f}"
            f",tremolo=f=0.12+0.03*{i}:d=0.25"
        )
    graph = ";".join(
        f"[{i}:a]" for i in range(n)
    )
    inputs = []
    for i, f in enumerate(freqs):
        det = 1.0 + (i - n / 2) * 0.0006
        inputs += ["-f", "lavfi", "-i",
                   f"sine=frequency={float(f)*det:.3f}:duration={seconds:.3f}"]
    tone = "".join(f"[{i}:a]" for i in range(n))
    cutoff = {"warm": 2600, "sad": 1400, "tech": 4200}[mood]
    fade_out = max(0.0, seconds - 2.5)
    fc = (
        f"{tone}amix=inputs={n}:normalize=0[pad];"
        f"[pad]volume={0.5/max(1,n-1):.3f},tremolo=f=0.10:d=0.22,"
        f"lowpass=f={cutoff},aecho=0.8:0.85:220|480:0.35|0.22,"
        f"afade=t=in:st=0:d=2.0,afade=t=out:st={fade_out:.2f}:d=2.5,"
        f"alimiter=limit=0.9[out]"
    )
    return inputs, fc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=20.0)
    ap.add_argument("--mood", default="warm", choices=sorted(MOODS))
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    inputs, fc = synth(args.mood, args.seconds)
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error", "-y", *inputs,
           "-filter_complex", fc, "-map", "[out]",
           "-c:a", "aac", "-b:a", "128k", args.out]
    subprocess.run(cmd, check=True)
    print(f"BGM 合成完成（{args.mood} / {args.seconds:.1f}s）：{args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
