import os
from PIL import ImageFont
from pathlib import Path

ROOT = Path(__file__).parent.parent
FONT_DIR = ROOT / "assets" / "fonts"
CANDIDATES_BOLD = [
    str(FONT_DIR / "SourceHanSansSC-Bold.otf"),
    str(FONT_DIR / "SourceHanSansSC-Medium.otf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
CANDIDATES_REG = [
    str(FONT_DIR / "SourceHanSansSC-Regular.otf"),
    str(FONT_DIR / "SourceHanSansSC-Medium.otf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

def get_font(size, bold=False):
    cands = CANDIDATES_BOLD if bold else CANDIDATES_REG
    for p in cands:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception as e:
                print(f"font load fail {p}: {e}")
                continue
    return ImageFont.load_default()
