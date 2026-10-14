#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
textimg.py —— 中文「花字 / 字幕」渲染器（PIL，逐字回退，不依赖 fontconfig）

为什么不用 libass/ASS 烧字？
  这在无桌面环境的机器上太容易翻车：libass 靠 fontconfig 找字体，
  而我们要用的是从 npm 下来的 391 个中文子集字体，fontconfig 常常扫不到
  （结果是屏幕上全是"豆腐块"）。于是改成：**我们自己把字渲染成透明 PNG**，
  再用 ffmpeg 的 overlay 叠上去。好处：
    1) 字体文件路径写死，跑到哪台机器都一样；
    2) 描边、阴影、关键词高亮、字距、行距全部可控，做「花字」比 ASS 顺手；
    3) 输出的是 PNG，需要的话可以直接拿去给剪映当贴纸素材。

对外只有三个函数：
    FontBook(dir)                # 扫描 fonts/ 里所有 ttf，建"字 → 字体文件"索引
    render_text(...)             # 一段带 **高亮** 的文案 → RGBA 图片
    save_line_png(...)           # 落盘成 out/line_xx.png
"""
from __future__ import annotations

import glob
import json
import os
import re

from PIL import Image, ImageDraw, ImageFilter, ImageFont

_SUPER = 2  # 超采样倍数，边缘更干净


class FontBook:
    """扫描字体目录，建立「码点 → 字体文件」的回退表（中文子集字体必备）。"""

    def __init__(self, fonts_dir: str):
        self.dir = fonts_dir
        self.index_file = os.path.join(fonts_dir, "_glyph_index.json")
        self.index: dict[str, dict[int, str]] = {"__families__": {}}  # type: ignore
        if os.path.exists(self.index_file):
            with open(self.index_file, encoding="utf-8") as f:
                raw = json.load(f)
            self.index = {k: {int(cp): v for cp, v in m.items()} for k, m in raw.items() if isinstance(m, dict)}
        if not self.index or len(self.index) < 2:
            self._build()

    def _family_key(self, path: str) -> str:
        n = os.path.basename(path)
        for fam in ("ma-shan-zheng", "zcool-kuaile", "noto-sans-sc", "noto-serif-sc"):
            if n.startswith(fam):
                weight = "700" if "-700-" in n else "400"
                return f"{fam}-{weight}"
        return "other"

    def _build(self) -> None:
        from fontTools.ttLib import TTFont

        table: dict[str, dict[int, str]] = {}
        for path in sorted(glob.glob(os.path.join(self.dir, "*.ttf"))):
            key = self._family_key(path)
            try:
                font = TTFont(path, lazy=True)
                cmap = font.getBestCmap()
                table.setdefault(key, {})
                for cp in cmap:
                    table[key].setdefault(cp, os.path.basename(path))
                font.close()
            except Exception:
                continue
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump({k: {str(cp): v for cp, v in m.items()} for k, m in table.items()}, f)
        self.index = table  # type: ignore

    def pick(self, ch: str, family: str) -> str | None:
        cp = ord(ch)
        for key in (family, "noto-sans-sc-700", "noto-sans-sc-400"):
            m = self.index.get(key) or {}
            if cp in m:
                return os.path.join(self.dir, m[cp])
        # 兜底：任何字体里有就行
        for m in self.index.values():
            if cp in m:
                return os.path.join(self.dir, m[cp])
        return None


def _segments(text: str, hi_colour, base_colour=None):
    """把 **关键词** 拆成 [(文本, 颜色, 放大倍数)]。"""
    segs, pos = [], 0
    for m in re.finditer(r"\*\*(.+?)\*\*", text):
        if m.start() > pos:
            segs.append((text[pos:m.start()], base_colour, 1.0))
        segs.append((m.group(1), hi_colour, 1.08))
        pos = m.end()
    if pos < len(text):
        segs.append((text[pos:], base_colour, 1.0))
    return segs or [(text, base_colour, 1.0)]


def render_text(text: str, book: FontBook, *, family: str, size: int, colour=(255, 255, 255, 255),
                hi_colour=(255, 214, 138, 255), stroke: int = 0, stroke_colour=(24, 22, 30, 255),
                shadow: int = 0, shadow_alpha: int = 150, max_width: int | None = None,
                line_gap: float = 0.22, spacing: float = 0.0):
    """一段文案 → RGBA 图片（自动换行、逐字选字体、支持 **高亮** 与描边/阴影）。"""
    size *= _SUPER
    stroke, shadow, spacing = int(stroke * _SUPER), int(shadow * _SUPER), spacing * _SUPER
    segs = _segments(text, hi_colour, colour)

    # 1) 先按行切（\n 与自动换行）
    #    中文排版两个坑：①逗号/句号不能落在行首；②最后一行只剩一两个字很难看。
    #    下面先贪心排，再做「行首禁则」回拉 + 尾行平衡。
    PUNCT_NO_START = set("，。！？、；：）】》”’…—·,.!?;:)]}")
    PUNCT_NO_END = set("（【《“‘([{")

    def width_of(ch: str, scale: float) -> float:
        return _char_width(ch, book, family, int(size * scale), spacing)

    raw_lines: list[list[tuple[str, object, float]]] = [[]]
    for seg_text, seg_colour, seg_scale in segs:
        for i, part in enumerate(seg_text.split("\n")):
            if i > 0:
                raw_lines.append([])
            for ch in part:
                width = width_of(ch, seg_scale)
                cur = raw_lines[-1]
                cur_w = sum(width_of(c, sc) for c, _, sc in cur)
                if max_width and cur and cur_w + width > max_width * _SUPER:
                    raw_lines.append([])
                raw_lines[-1].append((ch, seg_colour, seg_scale))

    # 行首禁则：把不小心落到下一行开头的标点挪回上一行
    for li in range(1, len(raw_lines)):
        while raw_lines[li] and raw_lines[li][0][0] in PUNCT_NO_START and raw_lines[li - 1]:
            raw_lines[li - 1].append(raw_lines[li].pop(0))
            if not raw_lines[li]:
                raw_lines.pop(li)
                break
        else:
            continue
        break
    # 避免行尾是左括号
    for li in range(1, len(raw_lines)):
        while raw_lines[li - 1] and raw_lines[li - 1][-1][0] in PUNCT_NO_END and raw_lines[li]:
            raw_lines[li].insert(0, raw_lines[li - 1].pop())
    # 尾行平衡：最后一行太短就从前一行匀几个字过去
    if max_width and len(raw_lines) > 1 and raw_lines[-1]:
        last_w = sum(width_of(c, sc) for c, _, sc in raw_lines[-1])
        while (last_w < max_width * _SUPER * 0.42 and len(raw_lines[-2]) > 2
               and raw_lines[-2][-1][0] not in PUNCT_NO_END):
            ch, col, sc = raw_lines[-2].pop()
            raw_lines[-1].insert(0, (ch, col, sc))
            last_w += width_of(ch, sc)
    lines = [ln for ln in raw_lines if ln]

    line_h = int(size * (1.0 + line_gap))
    w = int(max(1, max((sum(_char_width(c, book, family, int(size * sc), spacing) for c, _, sc in ln)
                        for ln in lines if ln), default=1)))
    h = line_h * len(lines)
    pad = stroke + shadow + 8 * _SUPER
    img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    def draw_all(offset, fill_override=None, draw_stroke=False):
        for li, ln in enumerate(lines):
            x = pad + (w - sum(_char_width(c, book, family, int(size * sc), spacing) for c, _, sc in ln)) / 2.0
            y = pad + li * line_h + line_h * 0.5
            for ch, col, sc in ln:
                fs = int(size * sc)
                path = book.pick(ch, family)
                if path is None:
                    continue
                font = ImageFont.truetype(path, fs)
                asc, desc = font.getmetrics()
                dy = y - (asc + desc) / 2 + offset[1]
                kw = {}
                if draw_stroke and stroke > 0:
                    kw = dict(stroke_width=stroke, stroke_fill=stroke_colour)
                d.text((x + offset[0], dy), ch, font=font, fill=fill_override or col, **kw)
                x += _char_width(ch, book, family, fs, spacing)

    if shadow > 0:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        for li, ln in enumerate(lines):
            x = pad + (w - sum(_char_width(c, book, family, int(size * sc), spacing) for c, _, sc in ln)) / 2.0
            y = pad + li * line_h + line_h * 0.5
            for ch, col, sc in ln:
                fs = int(size * sc)
                path = book.pick(ch, family)
                if path is None:
                    continue
                font = ImageFont.truetype(path, fs)
                asc, desc = font.getmetrics()
                sd.text((x + shadow, y - (asc + desc) / 2 + shadow), ch, font=font,
                        fill=(0, 0, 0, shadow_alpha), stroke_width=stroke, stroke_fill=(0, 0, 0, shadow_alpha))
                x += _char_width(ch, book, family, fs, spacing)
        sh = sh.filter(ImageFilter.GaussianBlur(shadow * 0.7))
        img.alpha_composite(sh)

    draw_all((0, 0), draw_stroke=True)
    img.alpha_composite(layer)
    return img


def _char_width(ch: str, book: FontBook, family: str, size: int, spacing: float) -> float:
    key = (ch, family, size)
    cache = _char_width.__dict__.setdefault("_c", {})
    if key in cache:
        return cache[key] + spacing
    path = book.pick(ch, family)
    if path is None:
        w = size
    else:
        font = ImageFont.truetype(path, size)
        w = font.getlength(ch)
        if w <= 0:
            w = size
    cache[key] = w
    return w + spacing


def save_png(img: Image.Image, path: str) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    img.resize((img.width // _SUPER, img.height // _SUPER), Image.LANCZOS).save(path)
    return path
