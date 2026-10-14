# ai-serach — AI 短视频创作：开源项目 & Agent Skill 调研

一份「能直接抄」的调研 + 一套**能直接跑**的本地渲染流水线。全部结论都基于 2026-10-14 对 GitHub API 与 skill 市场的实抓数据。

## 目录

| 内容 | 位置 |
| --- | --- |
| **调研报告**（选型 + 路线 + 排期 + 抓取口径） | [`research/AI短视频创作-开源项目与Skill调研.md`](research/AI短视频创作-开源项目与Skill调研.md) |
| **成果预览页**（两条实测成片可直接播放） | [`index.html`](index.html) |
| **可跑流水线：生图 → 加字 → 竖屏成片**（无 API） | [`starter-kit/`](starter-kit/) |
| **Agent Skill 清单**（给 Claude Code / Codex 用） | [`starter-kit/SKILL.md`](starter-kit/SKILL.md) |
| 原始抓取数据（GitHub 搜索 / 仓库元数据 / README） | [`research/raw/`](research/raw/) |

## 30 秒上手

```bash
cd starter-kit
pip install -r requirements.txt
python3 tools/fetch_fonts.py            # 开源中文字体（OFL，可商用）
python3 tools/make_placeholders.py      # 占位底图，先跑通
python3 make_video.py examples/script.gushi.json -o out/demo_gushi.mp4 --srt --cover
```

产出：1080×1920 / 30fps / H.264+AAC 竖屏成片 + 外挂 `.srt` + 封面图。
**全程不联网调用任何生成 API**：画面来自你给的图（本机 ComfyUI 生图或自己拍），花字/字幕用 PIL 渲染，BGM 用 ffmpeg 现场合成。

## 调研的三条核心结论

1. **「一张图 + 一句文案」类**（情感语录/图文）最优解是 [`xianyu110/ecommerce-video-skills`](https://github.com/xianyu110/ecommerce-video-skills)：13 个 skill、edge-tts 免 Key、本地 ffmpeg 渲染、含花字样式与封面 A/B。
2. **AI 科普类**认 Manim（原理动画）/ HyperFrames（HTML+GSAP 写视频，skill 安装量 95 万+）/ Remotion（React 逐帧）。skill 市场里更热的 `ai-video-generation`（755K 安装）是 API 路线，不符合"不烧接口"的要求。
3. **要蹭剪映生态**就用 `pyJianYingDraft` / `jianying-editor-skill` 生成剪映草稿，人只做最后一次审美决策。

> 说明：你给的那条抖音链接（`v.douyin.com/xajkS4Frn7c/`）解析到的是登录墙后的 PC 播放页，正文与画面无法获取，因此报告中没有逐帧拆解，改为给出可核验的爆款结构 + 工具映射。
