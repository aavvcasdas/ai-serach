#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_placeholders.py —— 生成占位底图（先跑通流水线，再换成模型出的图）

很多人卡在第一步：图还没生成，pipeline 就跑不起来。
这个脚本用 PIL 造几张"氛围底的占位图"，尺寸就是 1080×1920，
直接让 make_video.py 跑出成片，用来校验文案节奏、花字位置、时长。

真正发布时，把 examples/images/ 里的图换成：
  * 本机 ComfyUI / Z-Image / Flux 出的图（见 README 的"生图"一节），或
  * 你自己拍的照片、AI 生图的导出图。

用法： python3 tools/make_placeholders.py --out examples/images --kind both
"""
from __future__ import annotations

import argparse
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter


def gradient(w: int, h: int, c1, c2, angle: float = 0.0) -> Image.Image:
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        for_x = y / h
        t = for_x
        d.line([(0, y), (w, y)], fill=tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3)))
    if angle:
        img = img.rotate(angle, resample=Image.BICUBIC, expand=False)
    return img


def blob(img: Image.Image, cx: float, cy: float, r: float, colour, alpha: int = 90) -> None:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=colour + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(r * 0.35))
    img.alpha_composite(layer) if img.mode == "RGBA" else img.paste(
        Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB"), (0, 0))


PALETTES = {
    "gushi": [((34, 38, 66), (96, 68, 112)), ((58, 34, 44), (150, 96, 84)),
              ((22, 34, 46), (72, 104, 120)), ((44, 30, 52), (120, 78, 96)),
              ((26, 30, 40), (86, 86, 108))],
    "kepu": [((10, 18, 32), (18, 62, 92)), ((8, 24, 40), (24, 92, 110)),
             ((12, 14, 28), (48, 60, 120)), ((6, 20, 30), (20, 78, 96))],
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="examples/images")
    ap.add_argument("--kind", default="both", choices=["gushi", "kepu", "both"])
    ap.add_argument("--size", default="1080x1920")
    args = ap.parse_args()
    w, h = (int(x) for x in args.size.lower().split("x"))
    os.makedirs(args.out, exist_ok=True)
    random.seed(7)

    kinds = ["gushi", "kepu"] if args.kind == "both" else [args.kind]
    made = 0
    for kind in kinds:
        for i, (c1, c2) in enumerate(PALETTES[kind], start=1):
            img = gradient(w, h, c1, c2).convert("RGBA")
            # 两三个柔光斑 + 一点颗粒，让底图不那么"塑料"
            for _ in range(3):
                blob(img, random.uniform(0.15, 0.85) * w, random.uniform(0.15, 0.8) * h,
                     random.uniform(0.18, 0.42) * w, random.choice([(255, 235, 210), (150, 200, 255), (255, 200, 170)]),
                     random.randint(50, 95))
            noise = Image.effect_noise((w // 4, h // 4), 18).resize((w, h)).convert("L")
            img = Image.composite(img, Image.new("RGBA", (w, h), (0, 0, 0, 255)), noise.point(lambda v: 255))
            out = os.path.join(args.out, f"{kind}_{i:02d}.jpg")
            img.convert("RGB").save(out, quality=88)
            made += 1
            print(f"  占位图 {out}")
    print(f"\n完成 {made} 张 → {args.out}\n换成真图时保持同名即可，脚本不用改。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
