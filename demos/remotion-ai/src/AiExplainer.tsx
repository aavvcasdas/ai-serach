import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";

export const AiExplainer: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Scene timing: 0-90 (0-3s), 90-180 (3-6s), 180-300 (6-10s)
  const scene = frame < 90 ? 1 : frame < 180 ? 2 : 3;
  const localFrame = scene === 1 ? frame : scene === 2 ? frame - 90 : frame - 180;

  // Animations
  const titleY = spring({ frame: localFrame, fps, from: 80, to: 0, durationInFrames: 25, config: { damping: 100 } });
  const titleOpacity = interpolate(localFrame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  
  const subtitleOpacity = interpolate(localFrame, [15, 35], [0, 1], { extrapolateRight: "clamp" });
  
  // QKV animation for scene 2
  const qProgress = spring({ frame: Math.max(0, localFrame - 5), fps, from: 0, to: 1, config: { damping: 80 } });
  const kProgress = spring({ frame: Math.max(0, localFrame - 10), fps, from: 0, to: 1, config: { damping: 80 } });
  const vProgress = spring({ frame: Math.max(0, localFrame - 15), fps, from: 0, to: 1, config: { damping: 80 } });

  if (scene === 1) {
    return (
      <AbsoluteFill style={{ background: "radial-gradient(1200px 800px at 30% 20%, #1e293b 0%, #0a0a0a 60%)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
        <div style={{ transform: `translateY(${titleY}px)`, opacity: titleOpacity, textAlign: "center" }}>
          <div style={{ fontSize: 110, fontWeight: 900, color: "#f8fafc", lineHeight: 0.9, letterSpacing: "-0.04em" }}>
            AI科普<br />大语言模型<br />如何思考？
          </div>
        </div>
        <div style={{ marginTop: 30, fontSize: 32, color: "#94a3b8", opacity: subtitleOpacity, transform: `translateY(${interpolate(localFrame, [15, 35], [20, 0], { extrapolateRight: "clamp" })}px)` }}>
          从 Token 到 Attention · 纯代码渲染
        </div>
        <div style={{ marginTop: 30, padding: "10px 28px", borderRadius: 999, background: "#22c55e", color: "#052e16", fontWeight: 700, fontSize: 20, opacity: interpolate(localFrame, [30, 50], [0, 1], { extrapolateRight: "clamp" }) }}>
          REMOTION · NO API · 100% REACT CODE
        </div>
      </AbsoluteFill>
    );
  }

  if (scene === 2) {
    return (
      <AbsoluteFill style={{ background: "linear-gradient(180deg,#0f172a 0%,#020617 100%)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
        {/* Grid */}
        <div style={{ position: "absolute", inset: 0, opacity: 0.15, backgroundImage: `linear-gradient(#334155 1px, transparent 1px), linear-gradient(90deg,#334155 1px, transparent 1px)`, backgroundSize: "80px 80px" }} />
        
        <div style={{ display: "flex", gap: 50, alignItems: "center", zIndex: 1 }}>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", transform: `translateX(${-80 * (1 - qProgress)}px) scale(${qProgress})`, opacity: qProgress }}>
            <div style={{ width: 220, height: 220, borderRadius: 28, background: "linear-gradient(135deg,#60a5fa,#3b82f6)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 70, fontWeight: 800, color: "white", boxShadow: "0 20px 60px rgba(0,0,0,0.5)" }}>Q</div>
            <div style={{ marginTop: 12, color: "#e2e8f0", fontWeight: 600 }}>QUERY</div>
          </div>
          <div style={{ fontSize: 50, color: "#475569" }}>×</div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", transform: `translateY(${80 * (1 - kProgress)}px) scale(${kProgress})`, opacity: kProgress }}>
            <div style={{ width: 220, height: 220, borderRadius: 28, background: "linear-gradient(135deg,#f472b6,#ec4899)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 70, fontWeight: 800, color: "white" }}>K</div>
            <div style={{ marginTop: 12, color: "#e2e8f0", fontWeight: 600 }}>KEY</div>
          </div>
          <div style={{ fontSize: 50, color: "#475569" }}>→</div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", transform: `translateX(${80 * (1 - vProgress)}px) scale(${vProgress})`, opacity: vProgress }}>
            <div style={{ width: 220, height: 220, borderRadius: 28, background: "linear-gradient(135deg,#34d399,#10b981)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 70, fontWeight: 800, color: "white" }}>V</div>
            <div style={{ marginTop: 12, color: "#e2e8f0", fontWeight: 600 }}>VALUE</div>
          </div>
        </div>
        
        <div style={{ marginTop: 60, fontSize: 42, color: "#e2e8f0", fontWeight: 600, opacity: interpolate(localFrame, [40, 60], [0, 1], { extrapolateRight: "clamp" }), transform: `translateY(${interpolate(localFrame, [40, 60], [20, 0], { extrapolateRight: "clamp" })}px)` }}>
          Token之间通过 <span style={{ color: "#22d3ee" }}>注意力权重</span> 互相看见
        </div>

        {/* Token visualization */}
        <div style={{ marginTop: 40, display: "flex", gap: 16, opacity: interpolate(localFrame, [60, 80], [0, 1], { extrapolateRight: "clamp" }) }}>
          {["我","爱","学习","AI"].map((t, i) => {
            const active = interpolate(localFrame, [70 + i*5, 80 + i*5], [0, 1], { extrapolateRight: "clamp" });
            return (
              <div key={i} style={{ padding: "12px 20px", borderRadius: 12, background: `rgba(34,211,238,${0.1 + active*0.2})`, border: `1px solid rgba(34,211,238,${0.3 + active*0.7})`, color: "#22d3ee", fontWeight: 700, transform: `scale(${0.8 + active*0.2})` }}>
                {t}
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    );
  }

  // Scene 3
  const pointProgress = (idx: number) => interpolate(localFrame, [10 + idx*8, 25 + idx*8], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: "radial-gradient(1000px 600px at 70% 30%, #1e1b4b 0%, #020617 70%)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
      <div style={{ fontSize: 72, fontWeight: 900, color: "#f8fafc", textAlign: "center", lineHeight: 1.1, opacity: interpolate(localFrame, [0, 20], [0, 1], { extrapolateRight: "clamp" }), transform: `translateY(${interpolate(localFrame, [0, 20], [40, 0], { extrapolateRight: "clamp" })}px)` }}>
        Remotion = React组件<br />就是视频帧
      </div>
      
      <div style={{ display: "flex", gap: 24, marginTop: 50 }}>
        {[
          { n: "1", t: "useCurrentFrame()", d: "当前帧号，驱动所有动画，确定性渲染" },
          { n: "2", t: "interpolate()", d: "帧号映射到透明度、位移、缩放" },
          { n: "3", t: "spring()", d: "物理弹簧动画，丝滑自然" },
        ].map((p, i) => {
          const prog = pointProgress(i);
          return (
            <div key={i} style={{ width: 360, padding: "28px 24px", borderRadius: 20, background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)", transform: `translateY(${80 * (1 - prog)}px)`, opacity: prog }}>
              <div style={{ width: 40, height: 40, borderRadius: 10, background: "#f8fafc", color: "#020617", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 900 }}>{p.n}</div>
              <div style={{ marginTop: 16, fontSize: 22, fontWeight: 700, color: "#f1f5f9" }}>{p.t}</div>
              <div style={{ marginTop: 8, fontSize: 16, color: "#94a3b8", lineHeight: 1.5 }}>{p.d}</div>
            </div>
          );
        })}
      </div>

      <div style={{ marginTop: 40, fontSize: 18, color: "#64748b", opacity: interpolate(localFrame, [50, 70], [0, 1], { extrapolateRight: "clamp" }) }}>
        63.6k Stars · 5M月下载 · 纯代码 · 无需API · 本地渲染MP4
      </div>
    </AbsoluteFill>
  );
};
