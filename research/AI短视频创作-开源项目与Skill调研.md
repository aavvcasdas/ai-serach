# AI 短视频创作：开源项目 + Skill 市场调研

**调研时间**：2026-10-14（UTC） · **筛选硬条件**：① 近 3 个月有更新（pushed ≥ 2026-07-14）；② star 高；③ **不需要 API Key**、画面靠**代码渲染**（不是调视频生成模型的接口）；④ 有能跑的成片/实测。

> 数据来源：GitHub Search/REST API（star、许可证、pushed 时间均为当日实抓）+ skills.sh 安装量榜 + 公开文章交叉验证。
> 文中每个项目都标了 **★ / 最近更新 / 是否要 API**，可以直接照着抄。

---

## 0. 一句话结论

| 你的需求 | 直接抄这一个 |
| --- | --- |
| **「一张图 + 一句文案」→ 竖屏成片**（情感语录、图文、带货） | [`xianyu110/ecommerce-video-skills`](https://github.com/xianyu110/ecommerce-video-skills)：13 个 skill，edge-tts 配音**免 Key**，`scripts/assemble.py` 本地 ffmpeg 渲染，**明确不需要任何 API Key** |
| **AI 科普 / 知识类**（原理、数据、概念动画） | [`3b1b/manim`](https://github.com/3b1b/manim)（95k★）+ [`ManimCommunity/manim`](https://github.com/ManimCommunity/manim)（41.5k★）；要"现代感 + HTML/GSAP"就上 [`heygen-com/hyperframes`](https://github.com/heygen-com/hyperframes)（63k★，skill 安装量 95 万+） |
| **要"剪映生态"（花字、模板、爆款模仿）** | [`GuanYixuan/pyJianYingDraft`](https://github.com/GuanYixuan/pyJianYingDraft)（4.5k★）或 [`luoluoluo22/jianying-editor-skill`](https://github.com/luoluoluo22/jianying-editor-skill)（3.9k★）——代码生成**剪映草稿**，再在剪映里二次创作 |
| **全流程（选题→脚本→成片→发布）** | [`ymybxx/SoloMCN`](https://github.com/ymybxx/SoloMCN)（一人 MCN，只用 Claude 订阅，**不需要 AI API Key**）；一键出片看 [`harry0703/MoneyPrinterTurbo`](https://github.com/harry0703/MoneyPrinterTurbo)（130k★，但成片可走本地链路） |
| **本报告已落地的可跑成果** | 本仓库 [`starter-kit/`](../starter-kit)：**生图 → 加字 → 竖屏成片**，纯 ffmpeg + PIL，无 API，已实测渲染出两条 1080×1920 成片 |

**要认清的一件事**：Skill 市场（skills.sh 等）里"视频"类安装量最高的那几个，**恰恰是 API 路线**（例如 `ai-video-generation` 755 万安装，背后是 inference.sh CLI 调 Veo 等模型）。真正"代码渲染、不烧 API"的，集中在 **Manim / Remotion / HyperFrames / ffmpeg 系**这几条线，下面第 2 节按这个标准筛。

---

## 1. Skill 市场现状（2026-10-14 实抓）

skills.sh 是 Vercel 2026-01-20 上线的 agent skill 目录 + 安装量排行（覆盖 19 个 agent：Claude Code / Codex / Cursor / Copilot / OpenClaw 等）。

**视频/动画类安装量榜（All Time，实抓）**

| 排名 | Skill | 仓库 | 安装量 | 渲染方式 |
| --- | --- | --- | --- | --- |
| 7 | `hyperframes-cli` | heygen-com/hyperframes | 998.4K | **代码渲染**（HTML→MP4，本地/Lambda） |
| 11 | `hyperframes` | 同上 | 956.4K | 代码渲染 |
| 16 | `media-use` | 同上 | 879.6K | 素材/字幕/音频 |
| 17 | `hyperframes-animation` | 同上 | 847.6K | 代码渲染 |
| 21 | `hyperframes-core` | 同上 | 800.2K | 时序契约 |
| 26 | `hyperframes-creative` | 同上 | 772.4K | 设计/旁白规划 |
| 49 | `ai-video-generation` | 101-skills/superpowers | 755.3K | ⚠️ **API**（inference.sh 调 40+ 视频模型） |
| 66 | `remotion-best-practices` | remotion-dev/skills | 614.4K | **代码渲染**（React 逐帧） |
| 69 | `general-video` | heygen-com/hyperframes | 565.2K | 代码渲染 |
| 90 | `ai-image-generation` | magentosh/superpowers | 506.0K | ⚠️ API |
| 106 | `product-launch-video` | heygen-com/hyperframes | 465.0K | 代码渲染 |
| 130 | `faceless-explainer` | heygen-com/hyperframes | 450.4K | 代码渲染（无脸讲解，SoloMCN 就用的它） |

**市场结论**
1. **HyperFrames 家族一家独大**（前 30 名里占 7 席，合计约 610 万次安装）。它是 HeyGen 开源的 Apache-2.0 框架：视频写成 HTML，GSAP 控动画，`data-*` 标时序，最后渲染 MP4。**不用 API、本地渲染**，是目前"agent 做视频"最正统的路。
2. 榜单**只有"热度"维度，没有"近 3 个月更新"过滤**——所以我用 GitHub API 的 `pushed` 字段做了第二层硬筛（本文所有项目均已核验）。
3. 安装量 ≠ 可信。skills.sh 是开放上架，有报道指出其存在恶意/刷量 skill 的风险；安装前建议看仓库源码 + 安全审计标签（skills.sh 每个 skill 有 Socket / Snyk / Agent Trust Hub 三项审计）。

---

## 2. A 组｜AI 科普 / 知识类：代码渲染、无 API

> 这一组是"讲清楚一件事"的赛道：数学、物理、算法、AI 原理、数据结论。

| 项目 | ★ | 最近更新 | 许可 | 要 API？ | 为什么值得用 |
| --- | --- | --- | --- | --- | --- |
| [3b1b/manim](https://github.com/3b1b/manim) | 95,047 | 2026-09-09 | MIT | ❌ 无 | 3Blue1Brown 本尊：数学/原理动画的事实标准，公式排版（LaTeX）+ 逐帧确定性渲染 |
| [ManimCommunity/manim](https://github.com/ManimCommunity/manim) | 41,509 | 2026-10-12 | MIT | ❌ 无 | 社区版 ManimCE，工程化更好、文档更全，**做科普优先用这个** |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | 63,052 | 2026-10-14 | Apache-2.0 | ❌ 无 | HTML+GSAP 写视频，agent 友好；有 CLI（init/lint/preview/render）和组件库 |
| [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | 63,951 | 2026-10-14 | 自定义(免费额度) | ❌ 无 | React 写视频，数据图表/UI 演示类最强；配套 skill `remotion-best-practices` |
| [Vincentwei1021/anything2explainer](https://github.com/Vincentwei1021/anything2explainer) | 2,474 | 2026-09-18 | — | ❌ 无（默认 edge-tts 中文配音是免费端点） | **话题进、旁白讲解出**：黑底板 + 卡片的"讲解体"，中文本地配音 |
| [Vincentwei1021/video-talkcraft](https://github.com/Vincentwei1021/video-talkcraft) | 1,562 | 2026-10-12 | PolyForm NC | ⚠️ 可选（Fish Audio 更省事，默认本机对齐） | 旁白驱动的动效讲解，108 张"手法卡"分类法，可当**花字/节奏词典**读 |
| [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) | 11,807 | 2026-10-13 | Apache-2.0 | ❌ 无 | 152 张镜头配方卡：电影感产品/科技镜头，Remotion 渲染 |
| [Agents365-ai/video-podcast-maker](https://github.com/Agents365-ai/video-podcast-maker) | 1,674 | 2026-10-01 | MIT | ❌ 无（本地 edge/azure TTS） | 话题 → 4K 讲解片；**明确"本地 TTS、无需 key"**，适配 B站/抖音/小红书/视频号 |
| [iart-ai/motion-skills](https://github.com/iart-ai/motion-skills) | 805 | 2026-09-30 | MIT | ❌ 无 | 50 个动效 skill：动态字卡、kinetic typography——**"加字"这一环的正规军** |
| [Remocn/remocn](https://github.com/Remocn/remocn) | 1,599 | 2026-10-11 | MIT | ❌ 无 | Remotion 生产级转场/背景/场景库，省得自己写转场 |
| [digitalsamba/claude-code-video-toolkit](https://github.com/digitalsamba/claude-code-video-toolkit) | 2,222 | 2026-10-12 | MIT | ❌ 无（hello-world **明确"no API keys needed"**） | 一整套 skill：remotion / ffmpeg / playwright 录屏 / moviepy，含开场即渲染的示例 |
| [liuzhaowei1/Digital-OPUS-VIDEO-SKILL](https://github.com/liuzhaowei1/Digital-OPUS-VIDEO-SKILL) | 0（新） | 2026-10-08 | MIT | ❌ 无（生图/TTS 可选） | **方法论最扎实**：11 类视频类型 + 37 条手法 + 参考片拆帧流程；做"照着爆款做"必读 |
| [Yusuke710/manim-skill](https://github.com/Yusuke710/manim-skill) | 171 | 2026-10-07 | — | ❌ 无 | 一份 SKILL.md 教 agent 写 Manim，轻量 |
| [HarleyCoops/Math-To-Manim](https://github.com/HarleyCoops/Math-To-Manim) | 2,769 | 2026-10-13 | — | ⚠️ 需 LLM | 自然语言 → Manim 代码；想法参考，别当生产链路 |
| [marcelo-earth/generative-manim](https://github.com/marcelo-earth/generative-manim) | 933 | 2026-09-17 | — | ⚠️ 需 LLM | 同上，"GPT for video generation" |

**带实测/榜单背书的第三方交叉验证**：[zhuyansen/awesome-claude-video-skills](https://github.com/zhuyansen/awesome-claude-video-skills)（606★，2026-10-13）把 **290 个"让 agent 做视频"的仓库按类型分级 + 端到端实测**，其中 `claude-code-video-toolkit` 4/4 检查通过、5.5 分钟出片；`hyperframes` 自成一派（23.5 分钟）。这是目前最省时间的"选型目录"。

---

## 3. B 组｜情感 / 图文「生图 + 加字」：最贴你需求的一组

> 你的场景 = **模型生图 → 图上加字 → 配乐成片 → 发抖音**。这一组就是干这个的。

| 项目 | ★ | 最近更新 | 要 API？ | 要点 |
| --- | --- | --- | --- | --- |
| [xianyu110/ecommerce-video-skills](https://github.com/xianyu110/ecommerce-video-skills) | 70（新） | 2026-10-05 | **❌ 一张图也不需要 Key** | **13 个 skill 拆得最清楚**：3 秒钩子 → 15/30/60 秒分镜 `storyboard.json` → edge-tts 逐句配音 → Ken Burns 运镜 → xfade 转场 → **ASS 字幕/花字（4 种样式 + 安全区）** → BGM 自动闪避 → 两遍响度标准化（-14 LUFS）→ MP4+SRT；还有**封面标题 A/B**、抖音/小红书/淘宝多规格导出。实测 27 秒出片 |
| [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI) | 137,391 | 2026-10-14 | ❌ 无（本地推理） | **本地生图底座**，情感图/插画/封面全部本地出，不花一分钱 |
| [Comfy-Org/ComfyUI-Manager](https://github.com/Comfy-Org/ComfyUI-Manager) | 16,444 | 2026-10-11 | ❌ 无 | 装节点/模型，本地生图必备 |
| [LingyiChen-AI/comfyui-workflow-skill](https://github.com/LingyiChen-AI/comfyui-workflow-skill) | 430 | 2026-04-09（旧） | ❌ 无 | 自然语言 → ComfyUI 工作流 JSON（34 模板 / 360+ 节点）。**注意：原 `twwch/...` 已 301 迁移，仓库本身停留在 4 月，用前先自己验一遍** |
| [uniwell9797/tripod-panel](https://github.com/uniwell9797/tripod-panel) | 0（新） | 2026-10-03 | ❌ 无（本机推理，不联网） | 把本机 ComfyUI 包成中文明白面板：出图/换装/抠图/**照片动起来→加字幕配乐→配音** 一条界面走完 |
| [GuanYixuan/pyJianYingDraft](https://github.com/GuanYixuan/pyJianYingDraft) | 4,558 | 2026-09-26 | ❌ 无 | **Python 生成剪映草稿**（含 10.8 特性、关键帧、字幕、素材替换）。想蹭剪映的花字/贴纸/模板库，这是最优解 |
| [luoluoluo22/jianying-editor-skill](https://github.com/luoluoluo22/jianying-editor-skill) | 3,991 | 2026-09-11 | ❌ 无 | 让 agent 直接操作剪映的 skill（加字幕、自动配乐、批量替换） |
| [mcncarl/jianying-headless](https://github.com/mcncarl/jianying-headless) | 3,072 | 2026-10-12 | ❌ 无 | 剪映草稿的无头编辑/导出 + 独立 Agent SDK（源码预览态） |
| [Hommy-master/capcut-mate](https://github.com/Hommy-master/capcut-mate) | 1,961 | 2026-10-13 | ❌ 无 | 开源剪映小助手：草稿生成 + 下载，可当扣子插件 |
| [renezander030/capcut-cli](https://github.com/renezander030/capcut-cli) | 886 | 2026-10-14 | ❌ 无 | 独立的剪映/CapCut CLI：字幕、时间轴、速度调整 |
| [ArcReel/ArcReel](https://github.com/ArcReel/ArcReel) | 5,488 | 2026-10-14 | ⚠️ 模型可选 | 小说/剧本 → 角色场景资产 → 分镜 → 视频 → **剪映草稿**，跨镜头一致性 |
| [davepoon/buildwithclaude](https://github.com/davepoon/buildwithclaude) | 3,633 | 2026-10-14 | — | skill/marketplace 聚合目录，找"生图 + 图文"类 skill 的入口 |
| [momozi1996/awesome-ai-persona-skills](https://github.com/momozi1996/awesome-ai-persona-skills) | 924 | 2026-09-02 | ❌ 无 | 100+ 人格蒸馏 skill（**含情感全品类**）：写"情感感悟"文案时，换人格就是换语气 |
| [jnMetaCode/agency-agents-zh](https://github.com/jnMetaCode/agency-agents-zh) | 21,241 | 2026-10-08 | ❌ 无 | 277 个中文专家角色（含 64 个中国市场原创），选题/文案/运营岗位化 |

**"图片加字"这类 skill 的能力清单**（`subtitles-and-text-effects` 最全，可直接抄它的做法）：
- **花字**：关键词高亮（黄/金）、分行、`**词**` 语法、贴纸、CTA 按钮、安全区约束；
- **字幕**：ASS 样式、逐句对齐、免手动对时间轴（镜头时长 = 配音时长 + 0.15s 前导）；
- **封面 A/B**：用渲染过程留下的**干净底图**（不带字幕）叠新标题，避免两套字打架；
- **多平台规格**：9:16 抖音 / 3:4 小红书 / 1:1 淘宝。

---

## 3.5 诚实说明：那条抖音链接

你给的 `v.douyin.com/xajkS4Frn7c/`，我打开后解析到的是抖音 PC 播放页（视频 ID `7689228703817306234`），
**正文、字幕、画面都拿不到**（登录墙 + 反爬，只返回了"服务器出现问题"的空壳页 + 登录二维码）。

所以我没有办法逐帧拆解那条视频，也不会假装拆过。下面给的是**可核验的爆款结构 + 工具映射**，
配合第 2/3 节的项目，你自己 15 分钟就能复刻同类节奏：

| 那类视频的结构（"笑点一层叠一层"） | 代码/工具怎么实现 |
| --- | --- |
| **0–3s 钩子**：一句话把冲突甩脸上 | `hook-3s-script`（9 种钩子类型，一次出 6–10 版 + 广告法自检）；≤18 汉字 |
| **节奏密**：每 1–2 秒一个信息/笑点 | 镜头 1.2–2.5s 一切；转场 0.2–0.5s `xfade`；花字 0.6–1.2s 一闪 |
| **花字强化笑点** | 关键词高亮 + 放大 8% + 描边阴影（我们的 `textimg.py` 就是这么做的） |
| **情绪反差**：一本正经 → 突然破功 | 两套主题切换（`warm` 毛笔楷 ↔ `funny` 快乐体），画面配色跟着切 |
| **结尾留态度 + 话题标签** | 最后一镜用 `title` 只留一句态度；标签照抄你给的：#人生感悟 #我的长长长假 #搞笑日常 #剪映 |
| **同款可批量** | 同一份 `script.json` 只改文案与图，就能出第 2、3、4 条（这就是"分层叠加"能连更的原因） |

---

## 4. C 组｜全流程与发布（选题 → 成片 → 多平台）

| 项目 | ★ | 最近更新 | 要 API？ | 要点 |
| --- | --- | --- | --- | --- |
| [harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | 130,615 | 2026-10-14 | ⚠️ 需模型 key | 主题/关键词 → 高清短视频（中文圈最出名的"一键出片"），素材与 TTS 可换本地 |
| [ymybxx/SoloMCN](https://github.com/ymybxx/SoloMCN) | 53（新） | 2026-10-12 | **❌ 只要 Claude 订阅** | **一人 MCN**：热榜（抖音/微博/B站/知乎/百度/头条/HN）→ 选题 → 带出处的调研（顺手截网页当素材）→ 分镜 → **HyperFrames 代码成片（配音/字幕/动画）** → 各平台文案封面 → 一键发抖音/小红书/B站/YouTube。人只在选题/审片/发布三处拍板 |
| [sansan0/TrendRadar](https://github.com/sansan0/TrendRadar) | 62,889 | 2026-10-13 | ⚠️ 通知渠道 | 多平台热榜聚合 + 智能提醒：选题雷达 |
| [hypit-ai/hypit](https://github.com/hypit-ai/hypit) | 22,057 | 2026-10-14 | ⚠️ 可选 | "复刻爆款"：换脸、换词、换 B-roll 的整套工作流（DSL/编译器） |
| [ZJU-REAL/Easel](https://github.com/ZJU-REAL/Easel) | 3,588 | 2026-10-12 | ⚠️ 可选 | 社媒 AI agent：发现趋势 → 创作 → 全平台发布 |
| [dreammis/social-auto-upload](https://github.com/dreammis/social-auto-upload) | 15,491 | 2026-09-02 | ❌ 无（浏览器自动化） | 自动上传抖音/小红书/视频号/TikTok/YouTube/B站 |
| [yikart/AiToEarn](https://github.com/yikart/AiToEarn) | 26,506 | 2026-09-18 | ⚠️ 平台接口 | 多平台内容运营/矩阵化工具 |
| [zhouxiaoka/autoclip](https://github.com/zhouxiaoka/autoclip) | 9,399 | 2026-10-14 | ❌ 无（本地模型） | 一个链接一键出片：长视频→短视频 + 字幕/封面/文案 |
| [Huanshere/VideoLingo](https://github.com/Huanshere/VideoLingo) | 18,788 | 2026-09-30 | ❌ 本地模型 | 字幕切割/翻译/对齐/配音，全套本地 |
| [buxuku/SmartSub](https://github.com/buxuku/SmartSub) | 5,683 | 2026-10-14 | ❌ 本地模型 | 视频转字幕/翻译/配音/烧录，桌面端一站式 |
| [JuneYaooo/awesome-ai-media-cn](https://github.com/JuneYaooo/awesome-ai-media-cn) | 297 | 2026-10-02 | — | **中文自媒体工具合集**（150+ 项目，每周更新），选型时先扫这个 |

---

## 5. 三条可落地路线（按门槛从低到高）

### 路线 ①（推荐先跑）：单张图 → 竖屏成片，零模型、零 Key
**用本仓库的 `starter-kit/`**（就是从上面这些项目里提取的"最小可用骨架"，见第 6 节）：

```bash
cd starter-kit
pip install -r requirements.txt
python3 tools/fetch_fonts.py                      # 拉中文花字字体（开源可商用）
python3 tools/make_placeholders.py                # 先出占位图，跑通链路
python3 make_video.py examples/script.gushi.json -o out/demo_gushi.mp4 --srt --cover
```
要配音就 `edge-tts --text "..." --write-media voice/01.mp3`，再把路径填进 `voice` 字段（edge-tts 是免费端点，不需要 key）。

### 路线 ②（想蹭剪映生态）：代码生成草稿 → 剪映里二次创作
`pyJianYingDraft`（Python）或 `jianying-editor-skill`（agent 直接操作剪映）先把**素材、字幕、时间轴、花字**铺好，
人只做最后一层"审美决策"。适合"我的意思是说：图 AI 出，字我自己盯着改"的用法。

### 路线 ③（知识科普 / 高级感）：Manim 或 HyperFrames 代码渲染
- 概念/公式/数据：`ManimCommunity/manim`，一条 `python -m manim -qh scene.py Scene` 出 1080p（竖屏用 `-r 1080,1920`）。
- 现代感卡片/UI/动效：`npx skills add heygen-com/hyperframes`，HTML 写分镜，`npx hyperframes render` 出 MP4。
- 字幕/花字环节**复用本仓库的 `textimg.py`**：中文逐字回退、行首禁则、关键词高亮都处理好了。

---

## 6. 我给这个仓库留下的可跑成果：`starter-kit/`

调研只是材料，能跑才是结果。所以我把上面几个项目里最实用的做法抽出来，重写成了一版**依赖最小、无 API、可直接发布**的流水线：

```
starter-kit/
├── make_video.py     # 主流程：图 → 运镜 → 分批叠字 → 混音 → 1080×1920 成片
├── textimg.py        # 中文「花字/字幕」渲染器（PIL 逐字回退 + 行首禁则 + 关键词高亮）
├── tools/
│   ├── fetch_fonts.py       # npm 上拉开源中文字体（思源黑体/宋体、马善政楷、站酷快乐体），woff2→ttf
│   ├── make_bgm.py          # 用 ffmpeg 现场合成氛围 BGM（零素材、零版权）
│   └── make_placeholders.py # 造占位底图，先跑通链路
├── examples/                # 两个可直接跑的脚本：情感感悟 / AI 科普
├── fonts/                   # 391 个子集字体 + 码点索引（首次跑 fetch_fonts 生成）
└── out/                     # 实测成片、封面、.srt
```

**实测结果（本机 2 核 3.9G 内存，无 GPU）**

| 用例 | 规格 | 时长 | 体积 | 单次渲染耗时 |
| --- | --- | --- | --- | --- |
| `demo_gushi.mp4`（情感感悟，5 镜） | 1080×1920 / 30fps / H.264+AAC | 19.4s | 5.8 MB | ≈77s |
| `demo_kepu.mp4`（AI 科普，4 镜） | 1080×1920 / 30fps / H.264+AAC | 13.8s | 3.9 MB | ≈53s |

**几个踩过的坑（都已修掉，别人再踩就是浪费时间）**
1. **中文豆腐块**：libass 走 fontconfig 找字体，在无桌面的机器上扫不到我们的子集字体 → 屏幕全是方块。改法：**绕开 libass，用 PIL 渲染成透明 PNG 再 overlay**，顺带拿到了描边/阴影/高亮/字距的完全控制权。
2. **文字层整层透明**：单帧 PNG 直接喂 `overlay` 时，`fade`/`enable` 里的 `t` 只在第 0 帧求值 → 文字永远不出现。改法：`-loop 1 -framerate <fps> -t <总时长>` 把 PNG 展开成逐帧流。
3. **小内存机器 `Cannot allocate memory`**：一次把十几个 PNG 塞进同一个 `filter_complex`，每路都要维护帧队列。改法：**分批 overlay（每批 ≤3 层）**，逐批把结果当下批输入。
4. **音频输入编号错位**：叠字后视频输入变成 0 号，音频 `[N:a]` 全部要顺移；最后一趟只 copy 视频流，不重编码画面。

---

## 7. 给"自媒体 agent"的 15 天排期（可直接执行）

| 天数 | 动作 | 用到的东西 |
| --- | --- | --- |
| D1–D2 | 装 ComfyUI + 一个中文友好底模，跑通"一句话出图"，建自己的风格 LoRA/参考图集 | ComfyUI / ComfyUI-Manager |
| D3 | 跑通 `starter-kit`，产 3 条**无配音**的情感图文，纯看节奏与花字 | 本仓库 |
| D4 | 接 edge-tts 配音；把镜头时长改成"配音时长 + 0.15s" | 路线 ① |
| D5–D7 | 日更 3 条，同一模板换文案/图；封面各做 A/B 两版 | `cover-title-ab` 思路 |
| D8 | 做一条科普：Manim 讲一个反常识结论（30–45s） | ManimCE |
| D9–D11 | 把表现最好的那条**拆成模板**（钩子/节奏/花字位置），代码化成 `script.json` | `video-talkcraft` 手法卡 |
| D12–D14 | 接发布：浏览器自动化或 `social-auto-upload`；选题接 TrendRadar | C 组 |
| D15 | 复盘：只留 2 个爆款模板 + 1 个选题来源 | — |

**红线提醒**：① 文案不编数据、科普标来源；② 用别人的爆款只学**结构**，不要搬运素材；③ 字体/音乐要可商用——`starter-kit` 拉的四种字体都是 OFL 开源许可（LICENSE 随包落下），BGM 是现场合成、无版权问题。

---

## 附：本次调研的抓取口径（可复现）

```bash
# 近 3 个月有更新的、star 靠前的相关仓库
gh search repos "ai video stars:>3000 pushed:>2026-07-14" --sort stars --limit 15
gh search repos "topic:remotion pushed:>2026-07-14" --sort stars --limit 15
gh search repos "claude skills in:name,description stars:>300 pushed:>2026-07-14" --sort stars
# 逐个仓库核验 star / 许可证 / 最近推送
gh api repos/{owner}/{repo} --jq '[.stargazers_count,.pushed_at,(.license.spdx_id)]'
# skill 安装量榜（视频/动画相关条目）
curl -s https://www.skills.sh/ | grep -oE "hyperframes[a-z-]*|remotion-best-practices"
```

原始抓取数据在 `research/raw/`（GitHub 搜索 JSON + 仓库元数据 + README）。
