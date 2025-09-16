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

# =====================
# 한글 → 영문 라벨
# =====================
EN_LABEL = {
    # Top
    "레몬": "Lemon", "스윗오렌지": "Sweet Orange", "버가못": "Bergamot", "그린애플": "Green Apple",
    # Middle Floral
    "로즈제라늄": "Rose Geranium", "일랑일랑": "Ylang Ylang", "네롤리": "Neroli", "로즈": "Rose",
    # Middle Herb
    "라벤더": "Lavender", "로즈마리": "Rosemary", "클라리세이지": "Clary Sage", "스피어민트": "Spearmint",
    # Base
    "로즈우드": "Rosewood", "시더우드": "Cedarwood", "패출리": "Patchouli", "통카빈": "Tonka Bean",
}


# =====================
# 공통 스타일 (그린 톤 + 정사각 카드 + 체크 아이콘)
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
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; margin-top: 16px; }

    .card { position: relative; border: 2px solid #e6f5e6; border-radius: 16px; padding: 10px 10px 44px; background:#fff; transition: transform .06s ease, box-shadow .16s ease, border-color .16s ease; }
    .card:hover { transform: translateY(-2px); box-shadow: 0 8px 28px rgba(20,83,45,.12); }
    .thumb { width:100%; aspect-ratio: 1 / 1; border-radius: 12px; overflow:hidden; background: var(--bg); display:flex; align-items:center; justify-content:center; }
    .thumb img { width:100%; height:100%; object-fit: cover; display:block; }
    .name { display:block; margin-top:10px; font-weight:800; }
    .en { display:block; margin-top:2px; font-size:13px; color:#2e7d32; font-weight:600; letter-spacing:.2px; }

    /* 선택 체크(하단 중앙) */
    .select-wrap { position:absolute; left:0; right:0; bottom:10px; display:flex; justify-content:center; }
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

# =====================
# 페이지 템플릿들 (카드에 한/영 라벨, 선택 체크 아이콘)
# =====================
CHECK_ICON = """
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""
TOP_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Top note 선택</title>
</head>
<body>
  <h1>Top note 선택</h1>
  {% for name, eng in options %}
    <div class="card">
      <img src="{{ url_for('static', filename=images.get(name)) }}" alt="{{name}}">
      <p>{{ name }}<br>{{ eng }}</p>
      <button onclick="select('{{name}}')">선택</button>
    </div>
  {% endfor %}
</body>
</html>
"""

MIDDLE_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Middle note 선택</title>
</head>
<body>
  <h1>Middle note 선택</h1>
  {% for name, eng in options %}
    <div class="card">
      <img src="{{ url_for('static', filename=images.get(name)) }}" alt="{{name}}">
      <p>{{ name }}<br>{{ eng }}</p>
      <button onclick="select('{{name}}')">선택</button>
    </div>
  {% endfor %}
</body>
</html>
"""

BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Base note 선택</title>
</head>
<body>
  <h1>Base note 선택</h1>
  {% for name, eng in options %}
    <div class="card">
      <img src="{{ url_for('static', filename=images.get(name)) }}" alt="{{name}}">
      <p>{{ name }}<br>{{ eng }}</p>
      <button onclick="select('{{name}}')">선택</button>
    </div>
  {% endfor %}
</body>
</html>
"""

RESULT_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>결과</title>
</head>
<body>
  <h1>선택 결과</h1>
  <table>
    <tr>
      <td><img class="t-thumb" src="{{ url_for('static', filename=images[top]) }}" alt="Top"></td>
      <td>{{ top }}</td>
    </tr>
    <tr>
      <td><img class="t-thumb" src="{{ url_for('static', filename=images[middle]) }}" alt="Middle"></td>
      <td>{{ middle }}</td>
    </tr>
    <tr>
      <td><img class="t-thumb" src="{{ url_for('static', filename=images[base]) }}" alt="Base"></td>
      <td>{{ base }}</td>
    </tr>
  </table>
</body>
</html>
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
    return render_template_string(TOP_HTML, top_items=TOP, images=IMAGE_URL, en=EN_LABEL)

@app.post("/middle")
def middle():
    top = request.form.get("top", "")
    if not top:
        return redirect(url_for("index"))
    return render_template_string(MIDDLE_HTML, top=top, floral=MIDDLE_FLORAL, herb=MIDDLE_HERB, images=IMAGE_URL, en=EN_LABEL)

@app.post("/base")
def base():
    top = request.form.get("top", "")
    middle = request.form.get("middle", "")
    if not (top and middle):
        return redirect(url_for("index"))
    return render_template_string(BASE_HTML, top=top, middle=middle, base_items=BASE, images=IMAGE_URL, en=EN_LABEL)

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
    top = request.form.get("top"); middle = request.form.get("middle"); base_name = request.form.get("base")
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
        images=IMAGE_URL, en=EN_LABEL,
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
