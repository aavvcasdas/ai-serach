#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_fonts.py —— 花字/字幕字体准备（全程无 API Key）

做「生图 + 加字」类竖屏短视频，卡人的常常不是模型，而是**中文字体**：
ffmpeg 的 libass 只认 ttf/otf/ttc，而网上的开源中文字体包大多是 woff2 分片。

本脚本直接从 npm 公共仓库（registry.npmjs.org）拉 Fontsource 的中文开源字体包，
把 woff2 分片批量转成 ttf，丢进 starter-kit/fonts/，libass 用 fontsdir 直接读取。

用到的字体（全部开源、可商用，见各包 LICENSE，随包一起落下）：
  * Noto Sans SC（思源黑体简体）  → 字幕/正文
  * Ma Shan Zheng（马善政毛笔楷） → 国风/情感类花字标题
  * ZCOOL KuaiLe（站酷快乐体）    → 搞笑/日常类花字标题
  * Noto Serif SC（思源宋体简体） → 文艺/书摘类正文（可选）

依赖： pip install fonttools brotli
用法： python3 tools/fetch_fonts.py            # 默认拉上面 3 套的常用字重
       python3 tools/fetch_fonts.py --with-serif --weights 400,700,900
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tarfile
import urllib.request

REGISTRY = "https://registry.npmjs.org/"

# 包名 → (输出文件名前缀, 说明)
PACKAGES = {
    "@fontsource/noto-sans-sc": ("noto-sans-sc", "思源黑体简体 / 字幕·正文"),
    "@fontsource/noto-serif-sc": ("noto-serif-sc", "思源宋体简体 / 文艺正文"),
    "@fontsource/ma-shan-zheng": ("ma-shan-zheng", "马善政毛笔楷 / 国风花字"),
    "@fontsource/zcool-kuaile": ("zcool-kuaile", "站酷快乐体 / 搞笑花字"),
}


def http_get(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "starter-kit/fetch_fonts"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def latest_tarball(pkg: str) -> str:
    meta = json.loads(http_get(REGISTRY + pkg.replace("/", "%2F")))
    version = meta["dist-tags"]["latest"]
    return meta["versions"][version]["dist"]["tarball"], version


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts"))
    ap.add_argument("--weights", default="400,700", help="只转这些字重，逗号分隔（越小越快）")
    ap.add_argument("--with-serif", action="store_true", help="额外拉思源宋体（文艺/书摘风格）")
    args = ap.parse_args()

    try:
        from fontTools.ttLib import TTFont  # noqa: F401
    except ImportError:
        print("缺少依赖：pip install fonttools brotli", file=sys.stderr)
        return 2

    weights = {w.strip() for w in args.weights.split(",") if w.strip()}
    os.makedirs(args.out, exist_ok=True)

    pkgs = list(PACKAGES.items())
    if not args.with_serif:
        pkgs = [p for p in pkgs if p[0] != "@fontsource/noto-serif-sc"]

    for pkg, (prefix, desc) in pkgs:
        tarball, version = latest_tarball(pkg)
        print(f"\n[{pkg} v{version}] {desc}\n  下载：{tarball}")
        blob = http_get(tarball, timeout=300)
        print(f"  包大小 {len(blob)/1e6:.1f} MB，开始转换 woff2 → ttf")
        made = 0
        with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
            for m in tar.getmembers():
                name = os.path.basename(m.name)
                if not name.endswith(".woff2"):
                    continue
                # 形如 noto-sans-sc-123-400-normal.woff2 → 字重 = 倒数第二个字段
                parts = name[:-len(".woff2")].split("-")
                if len(parts) < 4 or parts[-1] != "normal" or parts[-2] not in weights:
                    continue
                data = tar.extractfile(m).read()
                font = TTFont(io.BytesIO(data))  # woff2 → sfnt
                out_name = f"{prefix}-{'-'.join(parts[1:])}.ttf"
                font.save(os.path.join(args.out, out_name), reorderTables=False)
                made += 1
        print(f"  完成：{made} 个 ttf → {args.out}")

    total = sum(os.path.getsize(os.path.join(args.out, f)) for f in os.listdir(args.out))
    print(f"\n全部字体合计 {total/1e6:.1f} MB，位置：{args.out}")
    print("下一步：python3 make_video.py script.example.json -o out/demo.mp4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
