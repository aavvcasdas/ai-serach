// 备选路线试制: Node + Skia(@napi-rs/canvas) 矢量渲染, 无浏览器, 逐块配音帧锚点
import { createCanvas, GlobalFonts } from '@napi-rs/canvas';
import { spawn, execSync } from 'child_process';
import fs from 'fs';
GlobalFonts.registerFromPath('fonts/NotoSansSC-Bold.otf', 'NSB');
GlobalFonts.registerFromPath('fonts/NotoSansSC-Medium.otf', 'NSM');
const FF = execSync(`python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"`).toString().trim();
const W = 1280, H = 720, FPS = 24;
const BEATS = [
  '神经网络，是怎么认出一只猫的？',
  '它先看最简单的东西：边缘、纹路、颜色。',
  '再把这些拼起来：耳朵、眼睛、胡须。',
  '最后综合判断：这是一只猫。',
  '所谓训练，就是让它看几百万张图，把内部的旋钮，慢慢调准。',
];
const dur = f => { const o = execSync(`${FF} -i ${f} 2>&1 || true`).toString(); const m = o.match(/Duration: (\d+):(\d+):([\d.]+)/); return +m[1]*3600 + +m[2]*60 + +m[3]; };
const DURS = BEATS.map((_, i) => dur(`assets/b${i+1}.mp3`));
const GAP = 10/FPS, LEAD = .45, TAIL = 1.2, starts = []; let tt = LEAD;
DURS.forEach(d => { starts.push(tt); tt += d + GAP; });
const TOTAL = tt - GAP + TAIL;
console.log('beats', starts.map(x=>x.toFixed(2)), 'total', TOTAL.toFixed(1));

const cv = createCanvas(W, H), x = cv.getContext('2d');
const INK='#eef2ff', SUB='#aebad7', DIM='#6d7a9c', CY='#6ee7ff', PU='#b79cff', PK='#ff8ac2', GN='#5ff0b0', YL='#ffd166';
const clamp=t=>Math.max(0,Math.min(1,t)), ease=t=>1-Math.pow(1-clamp(t),3);
function rr(c,a,b,w,h,r){c.beginPath();c.roundRect(a,b,w,h,r);}
function txt(s,cx,cy,size,col,f='NSB',align='center'){x.fillStyle=col;x.font=`${size}px ${f}`;x.textAlign=align;x.textBaseline='middle';x.fillText(s,cx,cy);}
// 猫头线稿: stage决定画哪些部件 (0轮廓 1边缘强化 2部件拼合 3完整)
function cat(cx,cy,s,p,stage,bf){
  x.save(); x.translate(cx,cy); x.scale(s,s); x.lineWidth=5; x.lineCap='round';
  const drawPart=(fn,on,a=1)=>{ if(!on)return; x.save(); x.globalAlpha=a; fn(); x.restore(); };
  // 耳朵
  drawPart(()=>{x.strokeStyle=CY;x.beginPath();x.moveTo(-78,-52);x.lineTo(-92,-128);x.lineTo(-28,-92);x.closePath();x.stroke();
    x.beginPath();x.moveTo(78,-52);x.lineTo(92,-128);x.lineTo(28,-92);x.closePath();x.stroke();}, stage>=2?bf>.05:true);
  // 头轮廓
  drawPart(()=>{x.strokeStyle=INK;x.beginPath();x.ellipse(0,0,105,92,0,0,Math.PI*2*clamp(p));x.stroke();}, true);
  // 纹路
  drawPart(()=>{x.strokeStyle=PU;x.lineWidth=4;[-38,0,38].forEach((dx,i)=>{x.beginPath();x.moveTo(dx,-88);x.lineTo(dx+8,-58);x.stroke();});}, stage>=1&&bf>.33);
  // 眼睛
  drawPart(()=>{x.fillStyle=GN;x.beginPath();x.ellipse(-42,-8,11,17,0,0,7);x.fill();x.beginPath();x.ellipse(42,-8,11,17,0,0,7);x.fill();}, stage>=2?bf>.3:true);
  // 鼻+嘴
  drawPart(()=>{x.fillStyle=PK;x.beginPath();x.moveTo(-10,26);x.lineTo(10,26);x.lineTo(0,38);x.closePath();x.fill();
    x.strokeStyle=INK;x.lineWidth=3.5;x.beginPath();x.moveTo(0,38);x.quadraticCurveTo(-4,50,-18,48);x.moveTo(0,38);x.quadraticCurveTo(4,50,18,48);x.stroke();}, stage>=2?bf>.55:true);
  // 胡须
  drawPart(()=>{x.strokeStyle=YL;x.lineWidth=3.5;[-1,1].forEach(sd=>{[14,30,46].forEach((dy,i)=>{x.beginPath();x.moveTo(sd*52,dy-8);x.lineTo(sd*132,dy-16+i*13);x.stroke();});});}, stage>=2?bf>.75:true);
  x.restore();
}
function frame(tg){
  let bi = starts.findLastIndex(s=>tg>=s); if(bi<0) bi=0;
  const p = tg>=starts[bi] ? clamp((tg-starts[bi])/DURS[bi]) : 0;
  const g = x.createLinearGradient(0,0,W,H); g.addColorStop(0,'#0a1024'); g.addColorStop(.6,'#0b0f1e'); g.addColorStop(1,'#170f2e');
  x.fillStyle=g; x.fillRect(0,0,W,H);
  // 光晕
  const rg = x.createRadialGradient(880,330,40,880,330,380); rg.addColorStop(0,'rgba(120,90,255,.20)'); rg.addColorStop(1,'rgba(120,90,255,0)');
  x.fillStyle=rg; x.fillRect(0,0,W,H);
  txt('备选路线试制 · Node/Skia 矢量渲染', 48, 42, 20, SUB, 'NSM', 'left');
  txt('神经网络认猫', 1232, 42, 20, CY, 'NSM', 'right');
  const fade = Math.min(clamp(tg/.4), clamp((TOTAL-tg)/.4));
  x.globalAlpha = fade;
  if(bi===0){
    txt('神经网络', 300, 250, 64, INK); txt('是怎么认出一只猫的？', 300, 325, 40, PU);
    cat(890, 330, 1.15, ease(p*1.3), 0, p);
    if(p>.45) txt('？', 890, 120, 66, PK);
  } else if(bi===1){
    txt('第一步：看零件', 300, 190, 44, INK);
    [['边缘', CY], ['纹路', PU], ['颜色', PK]].forEach(([s,c],i)=>{
      const on = p > i/3, a = on? ease((p-i/3)*4):0;
      x.globalAlpha = fade*(0.25+0.75*a);
      rr(x, 130, 250+i*92, 340, 66, 14); x.fillStyle='rgba(255,255,255,.06)'; x.fill(); x.strokeStyle=c; x.lineWidth=on?2.5:1; x.stroke();
      txt(s, 175, 284+i*92, 30, on?INK:DIM, 'NSB', 'left'); x.globalAlpha=fade;
    });
    cat(890, 330, 1.15, 1, 1, p);
  } else if(bi===2){
    txt('第二步：拼特征', 300, 190, 44, INK);
    ['耳朵','眼睛','胡须'].forEach((s,i)=>{ const on=p>i/3; txt((on?'✓ ':'· ')+s, 175, 290+i*80, 32, on?GN:DIM, 'NSB', 'left'); });
    cat(890, 330, 1.15, 1, 2, p);
  } else if(bi===3){
    cat(760, 320, 1.05, 1, 2, 1);
    [['猫', .92, GN], ['狗', .05, YL], ['兔子', .03, PK]].forEach(([s,v,c],i)=>{
      txt(s, 1000, 225+i*72, 26, INK, 'NSB', 'left');
      rr(x, 1000, 248+i*72, 240, 16, 8); x.fillStyle='rgba(255,255,255,.08)'; x.fill();
      rr(x, 1000, 248+i*72, Math.max(16, 240*v*ease(p*1.6-i*.25)), 16, 8); x.fillStyle=c; x.fill();
      if(i===0) txt(Math.round(92*ease(p*1.6))+'%', 1150, 225, 26, GN, 'NSB', 'left');
    });
    txt('综合判断 → 是猫 ✓', 640, 545, 36, GN);
  } else {
    txt('训练 = 调旋钮', 640, 120, 46, INK);
    for(let rI=0;rI<3;rI++){
      const y0 = 200+rI*82; rr(x, 240, y0, 800, 54, 27); x.fillStyle='rgba(255,255,255,.05)'; x.fill(); x.strokeStyle='rgba(255,255,255,.15)'; x.stroke();
      const u = clamp(0.5 + 0.4*Math.sin(p*Math.PI*2*(rI+1)+rI*2) * ease(Math.min(1,p*1.4+0.3)));
      const gx = x.createLinearGradient(240+720*u-24,0,240+720*u+24,0); gx.addColorStop(0,CY); gx.addColorStop(1,PU);
      x.fillStyle=gx; x.beginPath(); x.arc(240+720*u, y0+27, 24, 0, 7); x.fill();
    }
    // loss曲线
    x.strokeStyle=PK; x.lineWidth=4; x.beginPath();
    for(let i=0;i<=60;i++){ const px=240+800*i/60, py=470+110*(1-ease(i/60))*(0.75+0.25*Math.sin(i/3))* (1) - 60*(1-i/60); const yy=560-120*Math.exp(-i/14)+ (i? 6*Math.sin(i/2.2)*Math.exp(-i/18):0); i?x.lineTo(px,yy):x.moveTo(px,yy); }
    x.stroke();
    txt('错误率（loss）', 260, 448, 22, PK, 'NSM', 'left');
    txt(`已看图：${Math.round(300*ease(p*1.15))} 万张`, 1030, 452, 26, CY, 'NSB', 'right');
  }
  // karaoke字幕
  const say = BEATS[bi], spoken = Math.floor(say.length*p);
  x.font='34px NSB'; const tw = x.measureText(say).width; let sx=(W-tw)/2;
  x.textAlign='left';
  [...say].forEach((ch,i)=>{ x.fillStyle = i<spoken?INK:'#5d6a8c'; x.fillText(ch, sx, 640); sx += x.measureText(ch).width; });
  // 块进度
  const seg=(W-128)/BEATS.length;
  BEATS.forEach((_,j)=>{ rr(x, 64+j*seg, 682, seg-10, 6, 3); x.fillStyle='rgba(255,255,255,.14)'; x.fill();
    const fw = j<bi?seg-10:(j===bi?(seg-10)*p:0); if(fw>0){ rr(x,64+j*seg,682,fw,6,3); x.fillStyle=CY; x.fill(); } });
  x.globalAlpha=1;
  return cv.encodeSync('png');
}
// 旁白拼接
let fc=[],labels=[];
starts.forEach((s,i)=>{ fc.push(`[${i}:a]adelay=${Math.round(s*1000)}|${Math.round(s*1000)},apad[a${i}]`); labels.push(`[a${i}]`); });
const args=['-y']; BEATS.forEach((_,i)=>args.push('-i',`assets/b${i+1}.mp3`));
args.push('-filter_complex', fc.join(';')+';'+labels.join('')+`amix=inputs=${BEATS.length}:duration=first,atrim=0:${TOTAL}[a]`, '-map','[a]','-ar','44100','narration.wav');
execSync(`${FF} ${args.map(a=>`"${a}"`).join(' ')}`, {stdio:'pipe'});
const enc = spawn(FF, ['-y','-f','image2pipe','-vcodec','png','-r',String(FPS),'-i','-','-an','-c:v','libx264','-pix_fmt','yuv420p','-crf','19','-preset','medium','_s.mp4']);
const total = Math.floor(TOTAL*FPS);
for(let f=0; f<total; f++){ enc.stdin.write(frame(f/FPS)); if(f%120===0) console.log(f+'/'+total); }
enc.stdin.end(); await new Promise(r=>enc.on('close',r));
execSync(`${FF} -y -i _s.mp4 -i narration.wav -i music.wav -filter_complex "[2:a]volume=0.45[m];[1:a][m]amix=inputs=2:duration=first[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 160k -shortest 神经网络认猫-Skia试制.mp4`, {stdio:'pipe'});
fs.unlinkSync('_s.mp4'); console.log('DONE');
