from flask import Flask, request, render_template_string, send_file, redirect, url_for
import qrcode, io, os

app = Flask(__name__)

# =====================
# 데이터: 블렌딩 팩터
# =====================
TOP = {"레몬": 6, "스윗오렌지": 7, "버가못": 7, "그린애플": 3}
MIDDLE_FLORAL = {"로즈제라늄": 3, "일랑일랑": 4, "네롤리": 3, "로즈": 1}
MIDDLE_HERB = {"라벤더": 7, "로즈마리": 4, "클라리세이지": 3, "스피어민트": 3}
BASE = {"로즈우드": 5, "시더우드": 7, "패출리": 4, "통카빈": 1}

# 한글 → 영문 라벨 (기존 그대로 두기)
EN_LABEL = {
    "레몬": "Lemon", "스윗오렌지": "Sweet Orange", "버가못": "Bergamot", "그린애플": "Green Apple",
    "로즈제라늄": "Rose Geranium", "일랑일랑": "Ylang Ylang", "네롤리": "Neroli", "로즈": "Rose",
    "라벤더": "Lavender", "로즈마리": "Rosemary", "클라리세이지": "Clary Sage", "스피어민트": "Spearmint",
    "로즈우드": "Rosewood", "시더우드": "Cedarwood", "패출리": "Patchouli", "통카빈": "Tonka Bean",
}

# 🔁 이미지 경로 딕셔너리 (변수명 IMAGES 로 통일)
IMAGES = {
    "레몬": "images/lemon.jpg",
    "스윗오렌지": "images/sweet_orange.jpg",
    "버가못": "images/bergamot.jpeg",
    "그린애플": "images/green_apple.jpeg",
    "로즈제라늄": "images/rose_geranium.jpg",
    "일랑일랑": "images/ylangylang.jpg",
    "네롤리": "images/neroli.jpg",
    "로즈": "images/rose.png",
    "라벤더": "images/lavender.png",
    "로즈마리": "images/rosemary.png",
    "클라리세이지": "images/clary_sage.jpg",
    "스피어민트": "images/spearmint.jpg",
    "로즈우드": "images/rosewood.jpg",
    "시더우드": "images/cedarwood.jpeg",
    "패출리": "images/patchouli.jpeg",
    "통카빈": "images/tonka_bean.jpg",
}


# =====================
# 공통 스타일 (연두/초록 톤)
# =====================
STYLE = """
  <style>
    :root { --fg:#0b3d1b; --muted:#557166; --bd:#d6f5d6; --sel:#16a34a; --bg:#f0fff0; --pill:#dcfce7; }
    * { box-sizing: border-box; }
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Noto Sans, Helvetica, Arial, sans-serif; margin: 24px; color: var(--fg); background:#fff; }
    .wrap { max-width: 960px; margin: 0 auto; }
    header { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
    .qr { border: 1px solid var(--bd); border-radius: 12px; padding: 8px; background: var(--bg); }
    .muted { color: var(--muted); font-size: 14px; }
    h1 { font-size: 40px; margin: 8px 0 16px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; margin-top: 16px; }
    /* 카드: 하단 패딩을 넉넉하게 */
    .card {
      position: relative;
      border: 2px solid #e6f5e6;
      border-radius: 16px;
      padding: 12px 12px 84px;   /* ← 기존 48px 정도였다면 84px로 늘리기 */
      background:#fff;
      transition: transform .06s ease, box-shadow .16s ease, border-color .16s ease;}
    /* 이미지 아래 여백 조금 추가 */
    .thumb { 
       width:100%; aspect-ratio: 1/1; border-radius: 12px; overflow:hidden; 
       background: var(--bg); display:flex; align-items:center; justify-content:center; 
       border:1px solid var(--bd);
       margin-bottom: 10px;          /* ← 추가 */
      }

      /* 한글/영문 라벨의 줄 간격과 아래 여백 */
      .name { display:block; margin-top:6px; line-height:1.25; font-weight:800; }
      .en   { display:block; margin-top:4px; margin-bottom:8px; line-height:1.2;
        font-size:13px; color:#2e7d32; font-weight:600; letter-spacing:.2px; }

      /* 선택 pill은 카드 하단에서 살짝 더 내려줌 */
      .select-wrap { 
      position:absolute; left:0; right:0; bottom:12px;   /* ← 10px → 12px */
        display:flex; justify-content:center; 
      }        
    .select-pill { display:inline-flex; align-items:center; gap:6px; background: var(--pill); color:#065f46; border:1px solid #b7efc5; padding:8px 12px; border-radius:999px; font-weight:700; }
    .select-pill svg { width:18px; height:18px; }
    .card input[type="radio"] { position:absolute; opacity:0; pointer-events:none; }
    .card:has(input[type="radio"]:checked) { border-color: var(--sel); box-shadow: 0 0 0 4px rgba(22,163,74,.10) inset; }
    .card:has(input[type="radio"]:checked) .select-pill { background:#16a34a; color:#fff; border-color:#16a34a; }
    .btn { padding: 12px 16px; border-radius: 10px; background: var(--sel); color: #fff; font-weight: 800; cursor: pointer; border: none; }
    .btn:disabled { opacity:.6; cursor:not-allowed; }
    .section { margin-top: 20px; padding: 12px; border-radius: 12px; background: var(--bg); border:1px solid var(--bd); }
    table { width: 100%; border-collapse: collapse; margin-top: 16px; }
    th, td { border-bottom: 1px solid #e6f5e6; text-align: left; padding: 10px; }
    thead th { background:#f6fff6; }
    .t-thumb { width:56px; height:56px; border-radius:10px; object-fit:cover; border:1px solid var(--bd); }
    input[type="number"] { padding: 10px; border: 1px solid #bfe8bf; border-radius: 8px; width: 160px; }
    a.btn { text-decoration: none; display: inline-block; }
    @media (max-width:560px){ .grid{grid-template-columns: repeat(2, 1fr);} }
  </style>
"""

# 체크 아이콘 SVG
CHECK_ICON = """
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""

# =====================
# 템플릿들 (이미지 경로는 모두 url_for('static', filename=...) 사용)
# =====================
TOP_HTML = f"""
<!doctype html><html lang=ko><head><meta charset=utf-8><title>Top note 선택</title>{STYLE}</head>
<body><div class=wrap>
  <header>
    <h1>Top note 선택</h1>
    <div class=qr><img src="{{{{ url_for('qr_png') }}}}" width=110 height=110 alt="QR"></div>
  </header>
  <p class=muted>레몬 / 스윗오렌지 / 버가못 / 그린애플 중 1개 선택</p>
  <form method=post action="{{{{ url_for('middle') }}}}">
    <div class=grid>
      {{% for name in top_items.keys() %}}
      <label class=card>
        <input type=radio name=top value="{{{{name}}}}" required>
        <span class=thumb><img src="{{{{ url_for('static', filename=images.get(name)) }}}}" alt="{{{{name}}}}"></span>
        <span class=name>{{{{name}}}}</span>
        <span class=en>{{{{ en[name] }}}}</span>
        <div class=select-wrap><span class=select-pill> {CHECK_ICON} 선택 </span></div>
      </label>
      {{% endfor %}}
    </div>
    <p style="margin-top:16px;"><button class=btn type=submit>다음 (Middle)</button></p>
  </form>
</div></body></html>
"""

MIDDLE_HTML = f"""
<!doctype html><html lang=ko><head><meta charset=utf-8><title>Middle note 선택</title>{STYLE}</head>
<body><div class=wrap>
  <h1>Middle note 선택</h1>
  <form method=post action="{{{{ url_for('base') }}}}">
    <input type=hidden name=top value="{{{{top}}}}">
    <div class=section>
      <h3>플로랄</h3>
      <div class=grid>
        {{% for name in floral.keys() %}}
        <label class=card>
          <input type=radio name=middle value="{{{{name}}}}" required>
          <span class=thumb><img src="{{{{ url_for('static', filename=images.get(name)) }}}}" alt="{{{{name}}}}"></span>
          <span class=name>{{{{name}}}}</span>
          <span class=en>{{{{ en[name] }}}}</span>
          <div class=select-wrap><span class=select-pill> {CHECK_ICON} 선택 </span></div>
        </label>
        {{% endfor %}}
      </div>
    </div>

    <div class=section>
      <h3>허브</h3>
      <div class=grid>
        {{% for name in herb.keys() %}}
        <label class=card>
          <input type=radio name=middle value="{{{{name}}}}" required>
          <span class=thumb><img src="{{{{ url_for('static', filename=images.get(name)) }}}}" alt="{{{{name}}}}"></span>
          <span class=name>{{{{name}}}}</span>
          <span class=en>{{{{ en[name] }}}}</span>
          <div class=select-wrap><span class=select-pill> {CHECK_ICON} 선택 </span></div>
        </label>
        {{% endfor %}}
      </div>
    </div>
    <p style="margin-top:16px;"><button class=btn type=submit>다음 (Base)</button></p>
  </form>
</div></body></html>
"""

BASE_HTML = f"""
<!doctype html><html lang=ko><head><meta charset=utf-8><title>Base note 선택</title>{STYLE}</head>
<body><div class=wrap>
  <h1>Base note 선택</h1>
  <form method=post action="{{{{ url_for('amount') }}}}">
    <input type=hidden name=top value="{{{{top}}}}">
    <input type=hidden name=middle value="{{{{middle}}}}">
    <div class=grid>
      {{% for name in base_items.keys() %}}
      <label class=card>
        <input type=radio name=base value="{{{{name}}}}" required>
        <span class=thumb><img src="{{{{ url_for('static', filename=images.get(name)) }}}}" alt="{{{{name}}}}"></span>
        <span class=name>{{{{name}}}}</span>
        <span class=en>{{{{ en[name] }}}}</span>
        <div class=select-wrap><span class=select-pill> {CHECK_ICON} 선택 </span></div>
      </label>
      {{% endfor %}}
    </div>
    <p style="margin-top:16px;"><button class=btn type=submit>다음 (총량 입력)</button></p>
  </form>
</div></body></html>
"""

AMOUNT_HTML = f"""
<!doctype html><html lang=ko><head><meta charset=utf-8><title>총량 입력</title>{STYLE}</head>
<body><div class=wrap>
  <h1>총량 입력</h1>
  <form method=post action="{{{{ url_for('result') }}}}">
    <input type=hidden name=top value="{{{{top}}}}">
    <input type=hidden name=middle value="{{{{middle}}}}">
    <input type=hidden name=base value="{{{{base}}}}">
    <p>최종으로 넣을 총 용량(ml)을 입력하세요:</p>
    <input type=number name=total_amount step=0.1 min=0.1 required> ml
    <p style="margin-top:16px;"><button class=btn type=submit>결과 보기</button></p>
  </form>
</div></body></html>
"""

RESULT_HTML = f"""
<!doctype html><html lang=ko><head><meta charset=utf-8><title>블렌딩 결과</title>{STYLE}</head>
<body><div class=wrap>
  <header>
    <h1>블렌딩 결과</h1>
    <div class=qr><img src="{{{{ url_for('qr_png') }}}}" width=110 height=110 alt="QR"></div>
  </header>
  <p class=muted>입력한 총량을 비율에 따라 카드별 ml로 환산합니다.</p>
  <table>
    <thead><tr><th>카테고리</th><th>이미지</th><th>카드</th><th>영문</th><th>블렌딩 팩터</th><th>비율(%)</th><th>실제 ml</th></tr></thead>
    <tbody>
      <tr>
        <td>Top</td>
        <td><img class="t-thumb" src="{{{{ url_for('static', filename=images[top]) }}}}" alt="Top"></td>
        <td>{{{{top}}}}</td><td>{{{{ en[top] }}}}</td>
        <td>{{{{w_top}}}}</td><td>{{{{p_top}}}}</td><td>{{{{ml_top}}}}</td>
      </tr>
      <tr>
        <td>Middle</td>
        <td><img class="t-thumb" src="{{{{ url_for('static', filename=images[middle]) }}}}" alt="Middle"></td>
        <td>{{{{middle}}}}</td><td>{{{{ en[middle] }}}}</td>
        <td>{{{{w_mid}}}}</td><td>{{{{p_mid}}}}</td><td>{{{{ml_mid}}}}</td>
      </tr>
      <tr>
        <td>Base</td>
        <td><img class="t-thumb" src="{{{{ url_for('static', filename=images[base]) }}}}" alt="Base"></td>
        <td>{{{{base}}}}</td><td>{{{{ en[base] }}}}</td>
        <td>{{{{w_base}}}}</td><td>{{{{p_base}}}}</td><td>{{{{ml_base}}}}</td>
      </tr>
      <tr><th colspan=4>합계</th><th>{{{{total}}}}</th><th>100.0</th><th>{{{{total_amount}}}}</th></tr>
    </tbody>
  </table>
  <p style="margin-top:16px;"><a class=btn href="{{{{ url_for('index') }}}}">처음부터 다시</a></p>
</div></body></html>
"""


# =====================
# 유틸 & 라우트
# =====================
def get_weight(category, name):
    if category == "top": return TOP.get(name, 0)
    if category == "middle": return MIDDLE_FLORAL.get(name, 0) or MIDDLE_HERB.get(name, 0)
    if category == "base": return BASE.get(name, 0)
    return 0

@app.get("/")
def index():
    return render_template_string(TOP_HTML, top_items=TOP, images=IMAGES, en=EN_LABEL)

@app.post("/middle")
def middle():
    top = request.form.get("top", "")
    if not top:
        return redirect(url_for("index"))
    return render_template_string(
        MIDDLE_HTML,
        top=top, floral=MIDDLE_FLORAL, herb=MIDDLE_HERB,
        images=IMAGES, en=EN_LABEL
    )

@app.post("/base")
def base():
    top = request.form.get("top", "")
    middle = request.form.get("middle", "")
    if not (top and middle):
        return redirect(url_for("index"))
    return render_template_string(
        BASE_HTML,
        top=top, middle=middle, base_items=BASE,
        images=IMAGES, en=EN_LABEL
    )

@app.post("/amount")
def amount():
    top = request.form.get("top", "")
    middle = request.form.get("middle", "")
    base_name = request.form.get("base", "")
    if not (top and middle and base_name):
        return redirect(url_for("index"))
    return render_template_string(AMOUNT_HTML, top=top, middle=middle, base=base_name)

@app.post("/result")
def result():
    top = request.form.get("top")
    middle = request.form.get("middle")
    base_name = request.form.get("base")
    total_amount = float(request.form.get("total_amount", 0))

    w_top = get_weight("top", top)
    w_mid = get_weight("middle", middle)
    w_base = get_weight("base", base_name)
    total = max(1, w_top + w_mid + w_base)

    pct = lambda w: round(w * 100.0 / total, 1)
    ml  = lambda w: round(w * total_amount / total, 2)

    return render_template_string(
        RESULT_HTML,
        top=top, middle=middle, base=base_name,
        w_top=w_top, w_mid=w_mid, w_base=w_base, total=total,
        p_top=pct(w_top), p_mid=pct(w_mid), p_base=pct(w_base),
        ml_top=ml(w_top), ml_mid=ml(w_mid), ml_base=ml(w_base),
        total_amount=total_amount,
        images=IMAGES, en=EN_LABEL
    )

@app.get("/qr.png")
def qr_png():
    base = request.url_root.rstrip("/")
    img = qrcode.make(f"{base}/")
    buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
    return send_file(buf, mimetype="image/png", download_name="qr.png")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
