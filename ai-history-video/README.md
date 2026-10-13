# 《人工智能发展史》科普视频 — 纯代码渲染（零 API）

成片：`人工智能发展史.mp4`（1280×720 / 24fps / 2分47秒 / 中文配音+字幕+BGM）

## 内容（7 章）
1950 图灵之问 → 1956 达特茅斯诞生 → 两次寒冬 → 2012 深度学习 → AlphaGo 与 Transformer → 2022 大模型爆发 → 未来

## 管线（对应调研报告的落地流水线）
- 画面：`render.py` 用 Pillow 逐帧程序化绘制（星野黑底、每章专属动效、要点卡、章节进度条、逐句字幕），管道直喂 FFmpeg(libx264) 编码，无素材、无文生图/视频 API
- 配音：平台语音合成（voice-00），按章切片，字幕按旁白标点切分并按字数比例对时
- BGM：numpy 本地合成氛围垫，FFmpeg 混音（人声优先）
- 字体：Noto Sans SC（Git 方式取自 notofonts/noto-cjk）

## 复现 / 换选题
改 `render.py` 顶部 `SCENES` 的 year/title/bullets/narration 与 visual 类型，替换 `assets/voice/s*.mp3` 后运行：
```bash
pip install pillow numpy imageio-ffmpeg
python3 render.py
```
visual 可选：question / birth / winter / chart / go / chat / future

## 沙箱踩坑记录
- edge-tts 端点与 GitHub Release 模型文件在本沙箱网络被拦 → 配音改用平台语音；在本机跑时可切回 edge-tts/Kokoro 本地 TTS
- 中文字体不要用 raw 链接拉（拿到 HTML 错误页），用 git sparse-checkout 取 OTF
