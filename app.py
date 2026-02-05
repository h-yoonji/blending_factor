from flask import Flask, send_file, request
import qrcode, io, os

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
  <meta name="theme-color" content="#2B5A3F">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <title>에센셜 오일 블렌딩 계산기</title>
  <link rel="preconnect" href="https://cdn.jsdelivr.net">
  <link href="https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/static/pretendard.min.css" rel="stylesheet">
  <style>
    :root {
      --bg: #F5F2EC;
      --surface: #FFFFFF;
      --primary: #2B5A3F;
      --primary-hover: #1F4830;
      --primary-light: #E3EDE6;
      --primary-pale: #F0F5F1;
      --accent: #C4963A;
      --accent-light: #FDF6E9;
      --text: #1A1D1B;
      --text-2: #5E6B61;
      --text-3: #8A9A8D;
      --border: #D4DDD7;
      --border-light: #E6ECE8;
      --shadow-s: 0 1px 4px rgba(0,0,0,.05);
      --shadow-m: 0 4px 16px rgba(0,0,0,.07);
      --r-s: 8px; --r-m: 14px; --r-l: 20px; --r-full: 999px;
    }

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html { font-size: 16px; -webkit-text-size-adjust: 100%; }

    body {
      font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, 'Noto Sans KR', sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      min-height: 100dvh;
      -webkit-font-smoothing: antialiased;
      touch-action: manipulation;
      overscroll-behavior-y: none;
    }

    #app {
      max-width: 500px;
      margin: 0 auto;
      min-height: 100dvh;
      background: var(--surface);
      position: relative;
      display: flex;
      flex-direction: column;
      box-shadow: 0 0 40px rgba(0,0,0,.06);
    }

    /* ========== LANDING ========== */
    .landing {
      min-height: 100dvh;
      background: linear-gradient(160deg, #142E20 0%, #1E4A33 30%, #2B5A3F 60%, #3A7252 100%);
      display: flex; flex-direction: column;
      align-items: center; justify-content: center;
      text-align: center;
      padding: 48px 28px 40px;
      position: relative;
      overflow: hidden;
    }
    .landing::before {
      content: '';
      position: absolute; inset: 0;
      background: radial-gradient(circle at 30% 20%, rgba(255,255,255,.06) 0%, transparent 50%),
                  radial-gradient(circle at 70% 80%, rgba(255,255,255,.04) 0%, transparent 50%);
      pointer-events: none;
    }
    .l-badge {
      display: inline-flex; align-items: center; gap: 6px;
      background: rgba(255,255,255,.12);
      border: 1px solid rgba(255,255,255,.18);
      color: rgba(255,255,255,.85);
      font-size: 13px; font-weight: 600;
      padding: 7px 16px;
      border-radius: var(--r-full);
      margin-bottom: 28px;
      backdrop-filter: blur(4px);
      animation: fadeIn .6s ease;
    }
    .l-icon {
      font-size: 64px;
      margin-bottom: 20px;
      animation: fadeIn .5s ease;
      filter: drop-shadow(0 4px 12px rgba(0,0,0,.2));
    }
    .l-title {
      font-size: 32px;
      font-weight: 900;
      color: #fff;
      line-height: 1.25;
      letter-spacing: -.02em;
      margin-bottom: 10px;
      animation: fadeIn .6s ease .1s both;
    }
    .l-brand { color: #A8DBBE; }
    .l-sub {
      font-size: 15px;
      color: rgba(255,255,255,.65);
      line-height: 1.6;
      margin-bottom: 40px;
      animation: fadeIn .6s ease .2s both;
    }
    .l-start {
      width: 100%;
      padding: 18px 32px;
      border-radius: var(--r-m);
      border: none;
      background: #fff;
      color: var(--primary);
      font-size: 18px;
      font-weight: 800;
      cursor: pointer;
      transition: transform .12s, box-shadow .2s;
      box-shadow: 0 4px 20px rgba(0,0,0,.15);
      animation: fadeIn .6s ease .3s both;
    }
    .l-start:active { transform: scale(.96); }
    .l-start:hover { box-shadow: 0 6px 28px rgba(0,0,0,.2); }
    .l-divider {
      width: 48px; height: 1px;
      background: rgba(255,255,255,.2);
      margin: 36px auto 28px;
      animation: fadeIn .6s ease .4s both;
    }
    .l-links {
      display: flex;
      gap: 12px;
      width: 100%;
      animation: fadeIn .6s ease .5s both;
    }
    .l-link {
      flex: 1;
      display: flex; flex-direction: column;
      align-items: center; gap: 8px;
      padding: 16px 8px;
      border-radius: var(--r-m);
      background: rgba(255,255,255,.08);
      border: 1px solid rgba(255,255,255,.12);
      text-decoration: none;
      color: #fff;
      font-size: 12px;
      font-weight: 600;
      transition: background .15s, transform .1s;
      backdrop-filter: blur(4px);
    }
    .l-link:active { transform: scale(.95); }
    .l-link:hover { background: rgba(255,255,255,.14); }
    .l-link .l-link-icon {
      width: 40px; height: 40px;
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 18px;
      background: rgba(255,255,255,.15);
    }
    .l-footer {
      margin-top: 32px;
      font-size: 11px;
      color: rgba(255,255,255,.3);
      animation: fadeIn .6s ease .6s both;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    /* ========== Progress ========== */
    .prog-header {
      position: sticky; top: 0; z-index: 100;
      background: var(--surface);
      padding: 14px 20px 10px;
      border-bottom: 1px solid var(--border-light);
    }
    .prog-track { height: 5px; background: var(--border-light); border-radius: 3px; overflow: hidden; }
    .prog-fill { height: 100%; background: linear-gradient(90deg, var(--primary), #3D8B5E); border-radius: 3px; transition: width .45s cubic-bezier(.4,0,.2,1); }
    .prog-info { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; font-size: 13px; font-weight: 600; }
    .prog-counter { color: var(--text-3); }
    .prog-name { color: var(--primary); }

    /* ========== Steps ========== */
    .step-area { flex: 1; overflow-y: auto; -webkit-overflow-scrolling: touch; }
    .step { padding: 28px 20px 110px; opacity: 0; transform: translateY(16px); animation: fadeUp .35s cubic-bezier(.4,0,.2,1) forwards; }
    .step.back { animation: fadeUpBack .35s cubic-bezier(.4,0,.2,1) forwards; }
    @keyframes fadeUp { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }
    @keyframes fadeUpBack { from { opacity:0; transform:translateY(-12px); } to { opacity:1; transform:translateY(0); } }

    .page-title { font-size: 26px; font-weight: 800; letter-spacing: -.02em; line-height: 1.25; }
    .page-sub { font-size: 14px; color: var(--text-2); margin-top: 4px; margin-bottom: 24px; line-height: 1.5; }

    /* ========== Amount ========== */
    .amount-section { display: flex; flex-direction: column; align-items: center; gap: 20px; padding: 36px 0 20px; }
    .amount-visual { width: 68px; height: 68px; background: var(--primary-pale); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 32px; }
    .amount-field { position: relative; width: 100%; max-width: 300px; }
    .amount-input {
      font-size: 36px; font-weight: 800; text-align: center; width: 100%;
      padding: 14px 50px 14px 14px; border: 2px solid var(--border); border-radius: var(--r-m);
      outline: none; background: var(--surface); color: var(--text);
      transition: border-color .2s, box-shadow .2s; -moz-appearance: textfield;
    }
    .amount-input::-webkit-inner-spin-button, .amount-input::-webkit-outer-spin-button { -webkit-appearance: none; }
    .amount-input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(43,90,63,.12); }
    .amount-unit { position: absolute; right: 16px; top: 50%; transform: translateY(-50%); font-size: 16px; font-weight: 700; color: var(--text-3); pointer-events: none; }
    .chips { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; }
    .chip {
      padding: 10px 22px; border-radius: var(--r-full); border: 1.5px solid var(--border);
      background: var(--surface); font-size: 14px; font-weight: 600; cursor: pointer;
      color: var(--text); transition: all .15s;
    }
    .chip:active { transform: scale(.94); }
    .chip:hover, .chip.active { border-color: var(--primary); background: var(--primary-light); color: var(--primary); }

    .prev-sel { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 18px; }
    .prev-pill { font-size: 12px; padding: 5px 12px; border-radius: var(--r-full); background: var(--primary-light); color: var(--primary); font-weight: 600; white-space: nowrap; }
    .sel-row { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; font-size: 14px; color: var(--text-2); }
    .sel-badge { background: var(--primary); color: #fff; font-weight: 700; padding: 2px 11px; border-radius: var(--r-full); font-size: 13px; min-width: 28px; text-align: center; }

    /* ========== Cards ========== */
    .card-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
    .oil-card {
      position: relative; border: 2px solid var(--border-light); border-radius: var(--r-l);
      overflow: hidden; cursor: pointer; transition: border-color .2s, background .2s, box-shadow .2s;
      background: var(--surface); user-select: none; -webkit-user-select: none;
    }
    .oil-card:active { transform: scale(.97); transition: transform .1s; }
    .oil-card.on { border-color: var(--primary); background: var(--primary-light); box-shadow: 0 0 0 1px var(--primary), var(--shadow-m); }
    .oil-card .c-img { width: 100%; aspect-ratio: 1; object-fit: cover; display: block; background: var(--primary-pale); }
    .oil-card .c-body { padding: 10px 12px 14px; }
    .oil-card .c-name { font-size: 16px; font-weight: 700; line-height: 1.3; }
    .oil-card .c-en { font-size: 11.5px; color: var(--text-3); margin-top: 1px; font-weight: 500; }
    .oil-card.on .c-en { color: var(--primary); }
    .oil-card .c-factor { display: inline-flex; align-items: center; gap: 5px; margin-top: 7px; font-size: 12px; font-weight: 700; color: var(--accent); background: var(--accent-light); padding: 3px 10px; border-radius: var(--r-full); }
    .oil-card .c-check { position: absolute; top: 10px; right: 10px; width: 30px; height: 30px; border-radius: 50%; background: var(--primary); display: none; align-items: center; justify-content: center; color: #fff; font-size: 15px; font-weight: 700; box-shadow: var(--shadow-s); }
    .oil-card.on .c-check { display: flex; }

    /* ========== Bottom Nav ========== */
    .bot-nav {
      position: fixed; bottom: 0; left: 50%; transform: translateX(-50%);
      width: 100%; max-width: 500px; background: var(--surface);
      border-top: 1px solid var(--border-light); padding: 10px 20px;
      padding-bottom: max(10px, env(safe-area-inset-bottom));
      display: flex; gap: 10px; z-index: 100;
    }
    .btn {
      flex: 1; padding: 15px 20px; border-radius: var(--r-m); font-size: 16px; font-weight: 700;
      cursor: pointer; border: none; transition: all .12s; text-align: center; text-decoration: none;
      display: inline-flex; align-items: center; justify-content: center; gap: 6px;
    }
    .btn:active { transform: scale(.97); }
    .btn-go { background: var(--primary); color: #fff; }
    .btn-go:hover { background: var(--primary-hover); }
    .btn-back { background: var(--border-light); color: var(--text); flex: 0 0 auto; }

    /* ========== Result ========== */
    .r-card { background: var(--surface); border: 1px solid var(--border-light); border-radius: var(--r-l); padding: 14px 16px; margin-bottom: 10px; display: flex; gap: 14px; align-items: center; box-shadow: var(--shadow-s); }
    .r-card .r-img { width: 52px; height: 52px; border-radius: var(--r-s); object-fit: cover; flex-shrink: 0; border: 1px solid var(--border-light); }
    .r-card .r-info { flex: 1; min-width: 0; }
    .r-card .r-cat { font-size: 11px; color: var(--text-3); font-weight: 600; text-transform: uppercase; letter-spacing: .3px; }
    .r-card .r-name { font-weight: 700; font-size: 15px; line-height: 1.3; }
    .r-bar-track { height: 5px; background: var(--border-light); border-radius: 3px; overflow: hidden; margin-top: 5px; }
    .r-bar-fill { height: 100%; background: linear-gradient(90deg, var(--primary), #4DA66E); border-radius: 3px; transition: width .7s cubic-bezier(.4,0,.2,1); width: 0; }
    .r-nums { text-align: right; flex-shrink: 0; }
    .r-drops { font-size: 20px; font-weight: 800; color: var(--primary); line-height: 1.1; }
    .r-drops small { font-size: 12px; font-weight: 600; }
    .r-ml { font-size: 11px; color: var(--text-3); font-weight: 500; margin-top: 2px; }

    .summary { background: var(--primary); color: #fff; border-radius: var(--r-l); padding: 22px 16px; margin-top: 12px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; text-align: center; }
    .summary .s-val { font-size: 22px; font-weight: 800; line-height: 1.2; }
    .summary .s-lbl { font-size: 11px; opacity: .75; margin-top: 2px; font-weight: 500; }

    .result-actions { display: flex; gap: 10px; margin-top: 20px; }
    .qr-box { text-align: center; margin-top: 28px; padding: 20px; background: var(--primary-pale); border-radius: var(--r-l); }
    .qr-box img { width: 110px; height: 110px; border-radius: var(--r-s); border: 1px solid var(--border-light); }
    .qr-box p { font-size: 12px; color: var(--text-3); margin-top: 8px; }

    .empty-box { text-align: center; padding: 48px 20px; color: var(--text-3); }
    .empty-box .e-icon { font-size: 52px; margin-bottom: 14px; }
    .empty-box p { font-size: 15px; }
    .notice-box { margin-top: 16px; padding: 12px 16px; background: var(--accent-light); border-radius: var(--r-m); font-size: 13px; color: #7A6230; display: flex; gap: 8px; align-items: flex-start; line-height: 1.5; }
    .notice-box .n-icon { flex-shrink: 0; font-size: 16px; }

    .shake { animation: shake .35s; }
    @keyframes shake { 0%,100%{transform:translateX(0)} 20%{transform:translateX(-6px)} 40%{transform:translateX(6px)} 60%{transform:translateX(-4px)} 80%{transform:translateX(4px)} }

    @media (max-width: 370px) {
      .card-grid { gap: 8px; }
      .oil-card .c-body { padding: 8px 10px 12px; }
      .oil-card .c-name { font-size: 15px; }
      .page-title { font-size: 22px; }
      .amount-input { font-size: 30px; }
      .l-title { font-size: 26px; }
    }
  </style>
</head>
<body>
<div id="app">

  <!-- ========== LANDING PAGE ========== -->
  <div class="landing" id="landingPage">
    <span class="l-badge">🌿 VIVACE Aroma Therapy</span>
    <div class="l-icon">⚗️</div>
    <h1 class="l-title">에센셜 오일<br><span class="l-brand">블렌딩 팩터</span> 계산기</h1>
    <p class="l-sub">블렌딩 팩터 비율로 오일별 정확한<br>방울 수를 자동으로 계산해드립니다</p>
    <button class="l-start" onclick="startApp()">블렌딩 팩터 계산하기 →</button>
    <div class="l-divider"></div>
    <div class="l-links">
      <a class="l-link" href="http://pf.kakao.com/_enwks" target="_blank" rel="noopener">
        <div class="l-link-icon">💬</div>
        카카오 채널
      </a>
      <a class="l-link" href="https://www.instagram.com/vivace_aroma_therapy" target="_blank" rel="noopener">
        <div class="l-link-icon">📷</div>
        인스타그램
      </a>
      <a class="l-link" href="https://naver.me/5ssqyvCb" target="_blank" rel="noopener">
        <div class="l-link-icon">📍</div>
        오시는 길
      </a>
    </div>
    <p class="l-footer">© VIVACE Aroma Therapy</p>
  </div>

  <!-- ========== CALCULATOR ========== -->
  <div id="calcWrap" style="display:none; flex-direction:column; min-height:100dvh;">
    <header class="prog-header">
      <div class="prog-track"><div class="prog-fill" id="pFill" style="width:16.7%"></div></div>
      <div class="prog-info">
        <span class="prog-counter" id="pCnt">1 / 6</span>
        <span class="prog-name" id="pName">총량 입력</span>
      </div>
    </header>
    <div class="step-area" id="stepArea"></div>
    <nav class="bot-nav" id="botNav">
      <button class="btn btn-back" id="bBack" onclick="go(-1)" style="display:none">← 이전</button>
      <button class="btn btn-go" id="bNext" onclick="go(1)">다음</button>
    </nav>
  </div>

</div>

<script>
const CATS = [
  { key:'top', title:'Top Note', emoji:'🍋', sub:'시트러스 & 프레시 계열', oils:{
    '레몬':{f:6,en:'Lemon',img:'images/lemon.jpg'},
    '스윗오렌지':{f:7,en:'Sweet Orange',img:'images/sweet_orange.jpg'},
    '버가못':{f:7,en:'Bergamot',img:'images/bergamot.jpeg'},
    '그린애플':{f:1,en:'Green Apple',img:'images/green_apple.jpeg'}
  }},
  { key:'floral', title:'Middle – Floral', emoji:'🌸', sub:'플로랄 계열', oils:{
    '로즈제라늄':{f:3,en:'Rose Geranium',img:'images/rose_geranium.jpg'},
    '일랑일랑':{f:4,en:'Ylang Ylang',img:'images/ylangylang.jpg'},
    '네롤리':{f:3,en:'Neroli',img:'images/neroli.jpg'},
    '로즈':{f:1.5,en:'Rose',img:'images/rose.png'}
  }},
  { key:'herb', title:'Middle – Herb', emoji:'🌿', sub:'허브 계열', oils:{
    '라벤더':{f:7,en:'Lavender',img:'images/lavender.png'},
    '로즈마리':{f:4,en:'Rosemary',img:'images/rosemary.png'},
    '클라리세이지':{f:3,en:'Clary Sage',img:'images/clary_sage.jpg'},
    '스피어민트':{f:3,en:'Spearmint',img:'images/spearmint.jpg'}
  }},
  { key:'base', title:'Base Note', emoji:'🪵', sub:'우디 & 앰버 계열', oils:{
    '로즈우드':{f:5,en:'Rosewood',img:'images/rosewood.jpg'},
    '시더우드':{f:6,en:'Cedarwood',img:'images/cedarwood.jpeg'},
    '패출리':{f:4,en:'Patchouli',img:'images/patchouli.jpeg'},
    '통카빈':{f:1,en:'Tonka Bean',img:'images/tonka_bean.jpg'}
  }}
];

const STEPS = ['총량 입력','Top Note','Middle – Floral','Middle – Herb','Base Note','블렌딩 결과'];
let cur = 0, amt = 0, direction = 1;
const sel = { top:new Set(), floral:new Set(), herb:new Set(), base:new Set() };

function startApp() {
  document.getElementById('landingPage').style.display = 'none';
  document.getElementById('calcWrap').style.display = 'flex';
  render();
}

function goHome() {
  amt = 0;
  for (const k in sel) sel[k] = new Set();
  cur = 0;
  document.getElementById('calcWrap').style.display = 'none';
  document.getElementById('botNav').style.display = '';
  document.getElementById('landingPage').style.display = '';
  window.scrollTo(0,0);
}

function go(dir) {
  if (dir > 0 && cur === 0) {
    const inp = document.getElementById('amtInput');
    const v = parseFloat(inp?.value);
    if (!v || v <= 0) { inp?.focus(); inp?.classList.add('shake'); setTimeout(()=>inp?.classList.remove('shake'),400); return; }
    amt = v;
  }
  const next = cur + dir;
  if (next < 0) { goHome(); return; }
  if (next > 5) return;
  direction = dir;
  cur = next;
  render();
  document.querySelector('.step-area').scrollTo(0,0);
}

function restart() {
  amt = 0;
  for (const k in sel) sel[k] = new Set();
  direction = -1; cur = 0;
  render();
  document.getElementById('botNav').style.display = '';
}

function render() {
  const area = document.getElementById('stepArea');
  const dc = direction < 0 ? 'back' : '';
  if (cur === 0) area.innerHTML = renderAmount(dc);
  else if (cur <= 4) area.innerHTML = renderSel(cur-1, dc);
  else area.innerHTML = renderResult(dc);
  if (cur === 5) requestAnimationFrame(() => {
    document.querySelectorAll('.r-bar-fill[data-w]').forEach(el => { el.style.width = el.dataset.w+'%'; });
  });
  updateUI();
}

function updateUI() {
  const fill=document.getElementById('pFill'), cnt=document.getElementById('pCnt'),
        name=document.getElementById('pName'), back=document.getElementById('bBack'),
        next=document.getElementById('bNext'), nav=document.getElementById('botNav');
  fill.style.width = ((cur+1)/6*100)+'%';
  cnt.textContent = (cur+1)+' / 6';
  name.textContent = STEPS[cur];
  back.style.display = cur < 5 ? '' : 'none';
  back.textContent = cur === 0 ? '← 홈' : '← 이전';
  if (cur === 5) nav.style.display = 'none';
  else { nav.style.display = ''; next.textContent = cur === 4 ? '결과 보기 →' : '다음 →'; }
}

function renderAmount(dc) {
  return `<div class="step ${dc}">
    <h1 class="page-title">🧪 에센셜 오일 블렌딩</h1>
    <p class="page-sub">만들 에센셜 오일의 총 용량(ml)을 입력하세요.<br>블렌딩 팩터 비율로 각 오일의 방울 수를 계산합니다.</p>
    <div class="amount-section">
      <div class="amount-visual">💧</div>
      <div class="amount-field">
        <input class="amount-input" id="amtInput" type="number" step="0.1" min="0.1"
               inputmode="decimal" value="${amt||''}" placeholder="0.0"
               onkeydown="if(event.key==='Enter'){event.preventDefault();go(1)}">
        <span class="amount-unit">ml</span>
      </div>
      <div class="chips">
        <button class="chip" onclick="pickAmt(3)">3.0 ml</button>
        <button class="chip" onclick="pickAmt(4.5)">4.5 ml</button>
        <button class="chip" onclick="pickAmt(6)">6.0 ml</button>
        <button class="chip" onclick="pickAmt(10)">10 ml</button>
      </div>
    </div>
    <div class="notice-box">
      <span class="n-icon">💡</span>
      <span>0.1 ml = 2방울 기준으로 계산됩니다.</span>
    </div>
  </div>`;
}

function renderSel(ci, dc) {
  const cat = CATS[ci];
  let prev = '';
  for (let i=0;i<ci;i++) { const c=CATS[i]; if(sel[c.key].size) prev+=`<span class="prev-pill">${c.emoji} ${[...sel[c.key]].join(', ')}</span>`; }
  const prevHTML = prev ? `<div class="prev-sel">${prev}</div>` : '';
  let cards = '';
  for (const [name,oil] of Object.entries(cat.oils)) {
    const on = sel[cat.key].has(name)?'on':'';
    cards+=`<div class="oil-card ${on}" onclick="toggle('${cat.key}','${name}',this)">
      <img class="c-img" src="/static/${oil.img}" alt="${name}" loading="lazy">
      <div class="c-body"><div class="c-name">${name}</div><div class="c-en">${oil.en}</div><div class="c-factor">⚗ ${oil.f}</div></div>
      <div class="c-check">✓</div></div>`;
  }
  return `<div class="step ${dc}">
    <h1 class="page-title">${cat.emoji} ${cat.title}</h1>
    <p class="page-sub">${cat.sub} — 원하는 오일을 자유롭게 선택하세요 (복수 선택 가능)</p>
    ${prevHTML}
    <div class="sel-row">선택됨 <span class="sel-badge" id="cnt_${cat.key}">${sel[cat.key].size}</span></div>
    <div class="card-grid">${cards}</div></div>`;
}

function renderResult(dc) {
  const items = [];
  for (const cat of CATS) for (const name of sel[cat.key]) { const oil=cat.oils[name]; items.push({cat:cat.title,emoji:cat.emoji,name,f:oil.f,img:oil.img}); }
  const totalW = items.reduce((s,i)=>s+i.f,0)||1;
  let cards='', totalDrops=0;
  for (const it of items) {
    const pct=(it.f/totalW*100).toFixed(1), ml=(it.f*amt/totalW).toFixed(1), dr=Math.round(parseFloat(ml)/0.1*2);
    totalDrops+=dr;
    cards+=`<div class="r-card">
      <img class="r-img" src="/static/${it.img}" alt="${it.name}">
      <div class="r-info"><div class="r-cat">${it.emoji} ${it.cat}</div><div class="r-name">${it.name}</div>
        <div class="r-bar-track"><div class="r-bar-fill" data-w="${pct}" style="width:0"></div></div></div>
      <div class="r-nums"><div class="r-drops">${dr}<small>방울</small></div><div class="r-ml">${ml} ml · ${pct}%</div></div></div>`;
  }
  const empty = items.length===0 ? `<div class="empty-box"><div class="e-icon">🤔</div><p>선택된 오일이 없습니다.<br>이전 단계에서 오일을 선택해주세요.</p></div>` : '';
  const sum = items.length>0 ? `<div class="summary">
    <div><div class="s-val">${items.length}종</div><div class="s-lbl">선택 오일</div></div>
    <div><div class="s-val">${amt} ml</div><div class="s-lbl">총량</div></div>
    <div><div class="s-val">${totalDrops}</div><div class="s-lbl">총 방울 수</div></div></div>` : '';
  return `<div class="step ${dc}">
    <h1 class="page-title">📋 블렌딩 결과</h1>
    <p class="page-sub">블렌딩 팩터 비율로 ${amt} ml를 배분한 결과입니다. (0.1 ml = 2방울)</p>
    ${empty}${cards}${sum}
    <div class="result-actions">
      <button class="btn btn-back" onclick="direction=-1;cur=4;render();document.querySelector('.step-area').scrollTo(0,0);document.getElementById('botNav').style.display=''" style="flex:0 0 auto">← 수정</button>
      <button class="btn btn-go" onclick="restart()">처음부터 다시</button>
    </div>
    <div style="text-align:center;margin-top:16px;">
      <button class="btn btn-back" onclick="goHome()" style="flex:none;width:100%;background:var(--primary-light);color:var(--primary)">🏠 홈으로</button>
    </div>
    <div class="qr-box"><img src="/qr.png" alt="QR" loading="lazy"><p>QR 코드를 스캔하면 바로 접속됩니다</p></div></div>`;
}

function toggle(catKey, name, el) {
  if (sel[catKey].has(name)) { sel[catKey].delete(name); el.classList.remove('on'); }
  else { sel[catKey].add(name); el.classList.add('on'); }
  const b=document.getElementById('cnt_'+catKey); if(b) b.textContent=sel[catKey].size;
}

function pickAmt(v) {
  const inp=document.getElementById('amtInput'); if(inp){inp.value=v;amt=v;}
  document.querySelectorAll('.chip').forEach(c=>{c.classList.toggle('active',parseFloat(c.textContent)===v);});
}
</script>
</body>
</html>"""

@app.get("/")
def index():
    return HTML

@app.get("/qr.png")
def qr_png():
    base_url = request.url_root.rstrip("/")
    img = qrcode.make(f"{base_url}/")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png", download_name="qr.png")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
