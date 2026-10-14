这些字体由 tools/fetch_fonts.py 从 npm 公共仓库的 Fontsource 分发包下载并转成 ttf：

  @fontsource/noto-sans-sc     → Noto Sans SC（思源黑体简体）  OFL-1.1
  @fontsource/noto-serif-sc    → Noto Serif SC（思源宋体简体） OFL-1.1
  @fontsource/ma-shan-zheng    → Ma Shan Zheng（马善政毛笔楷） OFL-1.1
  @fontsource/zcool-kuaile     → ZCOOL KuaiLe（站酷快乐体）    OFL-1.1

全部为 SIL Open Font License 1.1：可免费商用、可再分发，保留本目录下的许可证即可。
每个字体包被切成 ~100 个 woff2 分片（覆盖不同码点区间），fetch_fonts.py 已转成 ttf，
textimg.py 通过 fonts/_glyph_index.json 做「逐字 → 字体文件」回退。
