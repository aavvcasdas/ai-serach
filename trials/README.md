# 科普视频备选路线试制报告

> 目的：第一套自研 Pillow 引擎（`ai-history-video/`）已封存为备选一号。本轮实测其他路线能否在当前沙箱跑通、效果如何。

## 试制结果一览

| 路线 | 结果 | 证据/原因 |
|---|---|---|
| ManimCommunity/manim（数理科普天花板） | ❌ 沙箱装不上 | `pip install manim` 失败：pycairo 需系统 pkg-config + libcairo，沙箱无 sudo apt 权限。本机/有 root 的机器上仍是首选 |
| Remotion / HyperFrames（需无头 Chrome） | ❌ 沙箱跑不了 | `npm i puppeteer` 时 Chrome 下载失败（Chrome-for-Testing 分发域名被沙箱网络拦截，`~/.cache/puppeteer` 只留下空目录）。本机可正常用 |
| **Node + Skia（@napi-rs/canvas）** | ✅ **跑通并出片** | npm 预编译二进制免系统依赖；矢量抗锯齿/渐变/圆角/字体开箱即用。试制片见 `node-skia/神经网络认猫-Skia试制.mp4`（25s） |

## Skia 试制片质量自评（vs Pillow 备选一号）

- **画质**：矢量线条（猫头线稿）明显比 Pillow 的位图描边顺滑；渐变光晕、半透明玻璃卡原生支持，不用手搓图层混合
- **同步**：沿用逐块配音（5 块）+ karaoke 字幕 + 块进度条，节拍锚点方法论可平移
- **语义动效**：说「边缘/纹路/颜色」左侧清单逐项点亮、猫脸对应部位同步强化；说「耳朵/眼睛/胡须」部件逐个拼合打勾；概率条按数值生长（猫 92% 计数）；「调旋钮」滑杆动画 + loss 曲线下降 + 看图计数
- **速度**：25s 片约 45s 渲完（PNG 管道），与 Pillow 相当
- **短板**：没有 Remotion 的组件生态和现成动效卡，镜头词汇要自己攒；复杂排版（DOM 级）做不了

## 结论

- **备选一号（已定）**：Pillow 引擎《人工智能发展史》+ 第一章语义拍样片 —— 方法论已验证
- **备选二号（本轮新增）**：Node/Skia —— JS 生态、矢量画质更好，和技能市场里 Remotion/HyperFrames 系 Skill 的知识可迁移；在本机装上 Chrome 后可平滑升级到 Remotion 本体
- **待本机验证**：Manim（数理题材不可替代）、Remotion+talkcraft 卡库（口播电影感上限最高）——沙箱限制而非项目问题

试制片选题《神经网络是怎么认出一只猫的》也可作正片系列的一集。
