#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preview_server.py —— 本地预览（含 HTTP Range，视频才能拖动进度条）

Python 自带的 http.server 不支持 Range 请求：浏览器虽然能加载 MP4，
但一拖进度条就黑屏/重头放。这个 60 行的服务器补上了 Range、正确的 MIME，
并把 index.html 设为默认页，用来预览本仓库的成片与报告。

用法： python3 tools/preview_server.py [--port 8000] [--root .]
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

EXTRA_TYPES = {
    ".mp4": "video/mp4", ".m4a": "audio/mp4", ".mp3": "audio/mpeg",
    ".md": "text/markdown; charset=utf-8", ".json": "application/json; charset=utf-8",
    ".ttf": "font/ttf", ".woff2": "font/woff2", ".srt": "text/plain; charset=utf-8",
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
}


class Handler(SimpleHTTPRequestHandler):
    def guess_type(self, path):  # noqa: D102
        ext = os.path.splitext(path)[1].lower()
        if ext in EXTRA_TYPES:
            return EXTRA_TYPES[ext]
        return super().guess_type(path)

    def send_head(self):  # noqa: D102  —— 加 Range 支持
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        if not rng or not os.path.isfile(path):
            return super().send_head()
        m = re.match(r"bytes=(\d*)-(\d*)", rng.strip())
        if not m:
            return super().send_head()
        size = os.path.getsize(path)
        start = int(m.group(1)) if m.group(1) else 0
        end = int(m.group(2)) if m.group(2) else size - 1
        if start >= size:
            self.send_error(416, "Requested Range Not Satisfiable")
            return None
        end = min(end, size - 1)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        f = open(path, "rb")
        f.seek(start)
        self._range = (start, end - start + 1)
        return f

    def copyfile(self, source, outputfile):  # noqa: D102
        rng = getattr(self, "_range", None)
        if not rng:
            return super().copyfile(source, outputfile)
        _, remaining = rng
        while remaining > 0:
            chunk = source.read(min(64 * 1024, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)
        self._range = None

    def end_headers(self):  # noqa: D102
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):  # 安静点
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    args = ap.parse_args()
    os.chdir(args.root)
    if not os.path.exists(os.path.join(args.root, "index.html")):
        print(f"提示：{args.root} 下没有 index.html，会退化成文件列表", file=sys.stderr)
    httpd = HTTPServer(("0.0.0.0", args.port), Handler)
    print(f"预览：http://0.0.0.0:{args.port}/  （root={args.root}，支持 Range）")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
