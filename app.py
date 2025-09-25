from flask import Flask, request, render_template_string, send_file
import qrcode, io, os

app = Flask(__name__)

# =====================
# 데이터 (총 16개)
# =====================
TOP = {"레몬": 6, "스윗오렌지": 7, "버가못": 7, "그린애플": 1}
MIDDLE_FLORAL = {"로즈제라늄": 3, "일랑일랑": 4, "네롤리": 3, "로즈": 1.5}
MIDDLE_HERB   = {"라벤더": 7, "로즈마리": 4, "클라리세이지": 3, "스피어민트": 3}
BASE          = {"로즈우드": 5, "시더우드": 6, "패출리": 4, "통카빈": 1}

EN_LABEL = {
    "레몬": "Lemon", "스윗오렌지": "Sweet Orange", "버가못": "Bergamot", "그린애플": "Green Apple",
    "로즈제라늄": "Rose Geranium", "일랑일랑": "Ylang Ylang", "네롤리": "Neroli", "로즈": "Rose",
    "라벤더": "Lavender", "로즈마리": "Rosemary", "클라리세이지": "Clary Sage", "스피어민트": "Spearmint",
    "로즈우드": "Rosewood", "시더우드": "Cedarwood", "패출리": "Patchouli", "통카빈": "Tonka Bean",
}

IMAGES = {
    # Top
    "레몬": "images/lemon.jpg",
    "스윗오렌지": "images/sweet_orange.jpg",
    "버가못": "images/bergamot.jpeg",
    "그린애플": "images/green_apple.jpeg",
    # Floral
    "로즈제라늄": "images/rose_geranium.jpg",
    "일랑일랑": "images/ylangylang.jpg",
    "네롤리": "images/neroli.jpg",
    "로즈": "images/rose.png",
    # Herb
    "라벤더": "images/lavender.png",
    "로즈마리": "images/rosemary.png",
    "클라리세이지": "images/clary_sage.jpg",
    "스피어민트": "images/spearmint.jpg",
    # Base
    "로즈우드": "images/rosewood.jpg",
    "시더우드": "images/cedarwood.jpeg",
    "패출리": "images/patchouli.jpeg",
    "통카빈": "images/tonka_bean.jpg",
}

# =====================
# 스타일 (일반 문자열)
# =====================
STYLE = """
  <style>
    :root {
      --fg:#0b3d1b; --muted:#4f665c; --bd:#cceccc; --sel:#166534;
      --bg:#f6fff6; --pill:#eaffef; --white:#ffffff;
    }
    * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    body {
      font-family: system-ui, Apple SD Gothic Neo, -apple-system, Segoe UI, Roboto, Noto Sans, Helvetica, Arial, sans-serif;
      margin: 0; padding: 0; color: var(--fg); background:#fff;
      font-size: 19px; line-height: 1.55;
    }

    .wrap {
      max-width: 600px;
      margin: 0 auto;
      padding: 10px 5px 5px;
      min-height: 300dvh;
      display: flex; flex-direction: column; gap: 14px;
    }

    h1 { font-size: 30px; margin: 2px 0 6px; text-align:center; }
    .muted { color: var(--muted); font-size: 16px; text-align:center; }

    .hero {
      border: 2px solid var(--bd); border-radius: 16px; background: var(--bg);
      padding: 16px 14px 18px; box-shadow: 0 4px 18px rgba(20,83,45,.06);
    }

    .amount-input { position: relative; width: 100%; margin-top: 8px; }
    .amount-box {
      font-size: 28px; font-weight: 800; text-align: center;
      width: 100%; height: 68px; border: 2px solid var(--sel); border-radius: 14px;
      padding: 10px 60px 10px 14px; background:#fff;
    }
    .unit-inside {
      position: absolute; right: 18px; top: 50%; transform: translateY(-50%);
      color: #166534; font-size: 18px; font-weight: 800; pointer-events: none;
    }

    .chips { display:flex; gap:10px; justify-content: center; margin: 12px 0 4px; flex-wrap: wrap; }
    .chip {
      border: 1.5px solid #b7efc5; background:#eaffef; color:#065f46;
      padding: 8px 12px; border-radius: 999px; font-weight: 800; font-size: 15px;
    }
    .chip:active { transform: scale(.98); }

    .btn {
      font-size: 22px; padding: 18px 20px; border-radius: 14px;
      background: var(--sel); color: #fff; font-weight: 800; cursor: pointer; border: none; width: 100%;
    }

    .toolbar { display:flex; justify-content: center; align-items:center; margin-top: 4px; gap:10px; }
    .count-badge { background:#16a34a; color:#fff; font-weight:800; padding:6px 10px; border-radius:999px; font-size:12px; }

    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 10px; }

    .card {
      position: relative; border: 2px solid var(--bd); border-radius: 14px;
      padding: 10px 10px 70px; background:#ffffff;
      transition: border-color .16s ease, box-shadow .16s ease, background .16s ease, color .16s ease;
      text-align: left; user-select: none; -webkit-user-select: none;
    }
    .card:hover { box-shadow: 0 6px 20px rgba(20,83,45,.10); }

    .thumb {
      width:100%; aspect-ratio: 1/1; border-radius: 10px; overflow:hidden;
      background: var(--bg); display:flex; align-items:center; justify-content:center;
      border:1px solid var(--bd); margin-bottom:8px;
    }
    .thumb img { width:100%; height:100%; object-fit: cover; object-position: center; display:block; }

    .name { display:block; margin-top:4px; line-height:1.2; font-weight:900; font-size:18px; }
    .en   { display:block; margin-top:2px; margin-bottom:6px; line-height:1.15; font-size:12px; color:#2e7d32; font-weight:700; letter-spacing:.2px; }

    .select-wrap { position:absolute; left:0; right:0; bottom:10px; display:flex; justify-content:center; }
    .select-pill {
      display:inline-flex; align-items:center; gap:6px; background: var(--pill); color:#065f46;
      border:1px solid #b7efc5; padding:8px 12px; border-radius:999px; font-weight:800;
      box-shadow: inset 0 0 0 1px rgba(255,255,255,.5);
    }

    .card input[type="checkbox"] { position:absolute; inset:0; opacity:0; cursor:pointer; }
    .card:has(input[type="checkbox"]:checked) { background: var(--sel); border-color: var(--sel); color: var(--white); box-shadow: 0 0 0 3px rgba(34,197,94,.25) inset; }
    .card:has(input[type="checkbox"]:checked) .en { color: #e6ffe6; }
    .card:has(input[type="checkbox"]:checked) .thumb { border-color: rgba(255,255,255,.35); background: rgba(0,0,0,.08); }
    .card:has(input[type="checkbox"]:checked) .select-pill { background: rgba(255,255,255,.15); color:#fff; border-color: rgba(255,255,255,.6); }

    table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 18px; }
    th, td { border-bottom: 1px solid #e6f5e6; text-align: center; padding: 10px; }
    thead th { background:#f6fff6; text-align: center; }
    .t-thumb { width:64px; height:64px; border-radius:10px; object-fit:cover; border:1px solid var(--bd); }

    /* 결과 페이지만 QR 고정 */
    .qr-fixed {
      position: fixed; top: 10px; right: 10px; width: 90px; height: 90px; z-index: 1000;
      display: flex; align-items: center; justify-content: center;
      border: 1px solid var(--bd); border-radius: 10px; padding: 6px; background: var(--bg);
    }
    .qr-fixed img { width: 100%; height: 100%; object-fit: contain; }
  </style>
"""

# =====================
# 공통 스크립트 (선택 카운터/검증: 0개도 통과)
# =====================
COMMON_SCRIPTS = """
<script>
function setupSelection(groupName, counterId) {
  const form = document.querySelector('form');
  if (!form) return;
  const counter = document.getElementById(counterId);
  function refresh() {
    const checked = form.querySelectorAll('input[name="'+groupName+'"]:checked').length;
    if(counter) counter.textContent = checked;
  }
  form.querySelectorAll('input[name="'+groupName+'"]').forEach(b => b.addEventListener('change', refresh));
  refresh();
}
// 0개 선택도 허용
function validateChecked() { return true; }

// 빠른 선택칩
function pick(val) {
  const inp = document.getElementById("total_amount");
  if(inp) { inp.value = val; inp.focus(); }
}
</script>
"""

# =====================
# 템플릿 (일반 문자열, STYLE/JS는 |safe 로 삽입)
# =====================
AMOUNT_START_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<title>에센셜 오일 부향률 계산 프로그램</title>{{ STYLE|safe }}{{ COMMON_SCRIPTS|safe }}
</head>
<body>
  <div class=wrap>
    <h1>총량 입력</h1>
    <div class="hero">
      <form method=post action="{{ url_for('top') }}">
        <p class=muted>오늘 만들 에센셜 오일의 총량을 입력하세요.</p>
        <div class="amount-input">
          <input id="total_amount" class="amount-box" type=number name=total_amount step=0.1 min=0.1 required placeholder="예) 3.0">
          <span class="unit-inside">ml</span>
        </div>
        <div class="chips">
          <button class="chip" type="button" onclick="pick(3.0)">3.0 ml</button>
          <button class="chip" type="button" onclick="pick(4.5)">4.5 ml</button>
          <button class="chip" type="button" onclick="pick(6.0)">6.0 ml</button>
        </div>
        <!-- 버튼 위쪽 여백 추가 -->
        <button class=btn type=submit style="margin-top:28px;">다음 (Top 선택)</button>
      </form>
    </div>
  </div>
</body></html>
"""


TOP_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<title>에센셜 오일 부향률 계산 프로그램</title>{{ STYLE|safe }}{{ COMMON_SCRIPTS|safe }}</head>
<body>
  <div class=wrap>
    <h1>Top 선택</h1>
    <div class="toolbar">
      <span class="count-badge">선택: <span id="cnt-top">0</span></span>
    </div>
    <form method=post action="{{ url_for('middle_floral') }}" onsubmit="return validateChecked()">
      <input type="hidden" name="total_amount" value="{{ total_amount }}">
      <div class=grid>
        {% for name in top_items.keys() %}
        <label class=card>
          <input type="checkbox" name="top" value="{{name}}">
          <span class=thumb><img src="{{ url_for('static', filename=images.get(name)) }}" alt="{{name}}"></span>
          <span class=name>{{name}}</span>
          <span class=en>{{ en[name] }}</span>
          <div class=select-wrap><span class=select-pill>✔ 선택</span></div>
        </label>
        {% endfor %}
      </div>
      <p style="margin-top:12px;"><button class=btn type=submit>다음 (Middle–Floral)</button></p>
    </form>
    <script>setupSelection('top','cnt-top');</script>
  </div>
</body></html>
"""

MIDDLE_FLORAL_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<title>에센셜 오일 부향률 계산 프로그램</title>{{ STYLE|safe }}{{ COMMON_SCRIPTS|safe }}</head>
<body>
  <div class=wrap>
    <h1>Middle – Floral</h1>
    <div class="toolbar">
      <span class="count-badge">선택: <span id="cnt-floral">0</span></span>
    </div>
    <form method=post action="{{ url_for('middle_herb') }}" onsubmit="return validateChecked()">
      <input type=hidden name=total_amount value="{{ total_amount }}">
      {% for t in top_selected %}<input type=hidden name="top" value="{{t}}">{% endfor %}
      <div class=grid>
        {% for name in floral.keys() %}
        <label class=card>
          <input type="checkbox" name="floral" value="{{name}}">
          <span class=thumb><img src="{{ url_for('static', filename=images.get(name)) }}"></span>
          <span class=name>{{name}}</span>
          <span class=en>{{ en[name] }}</span>
          <div class=select-wrap><span class=select-pill>✔ 선택</span></div>
        </label>
        {% endfor %}
      </div>
      <p style="margin-top:12px;"><button class=btn type=submit>다음 (Middle–Herb)</button></p>
    </form>
    <script>setupSelection('floral','cnt-floral');</script>
  </div>
</body></html>
"""

MIDDLE_HERB_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<title>에센셜 오일 부향률 계산 프로그램</title>{{ STYLE|safe }}{{ COMMON_SCRIPTS|safe }}</head>
<body>
  <div class=wrap>
    <h1>Middle – Herb</h1>
    <div class="toolbar">
      <span class="count-badge">선택: <span id="cnt-herb">0</span></span>
    </div>
    <form method=post action="{{ url_for('base') }}" onsubmit="return validateChecked()">
      <input type=hidden name=total_amount value="{{ total_amount }}">
      {% for t in top_selected %}<input type=hidden name="top" value="{{t}}">{% endfor %}
      {% for f in floral_selected %}<input type=hidden name="floral" value="{{f}}">{% endfor %}
      <div class=grid>
        {% for name in herb.keys() %}
        <label class=card>
          <input type="checkbox" name="herb" value="{{name}}">
          <span class=thumb><img src="{{ url_for('static', filename=images.get(name)) }}"></span>
          <span class=name>{{name}}</span>
          <span class=en>{{ en[name] }}</span>
          <div class=select-wrap><span class=select-pill>✔ 선택</span></div>
        </label>
        {% endfor %}
      </div>
      <p style="margin-top:12px;"><button class=btn type=submit>다음 (Base)</button></p>
    </form>
    <script>setupSelection('herb','cnt-herb');</script>
  </div>
</body></html>
"""

BASE_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<title>에센셜 오일 부향률 계산 프로그램</title>{{ STYLE|safe }}{{ COMMON_SCRIPTS|safe }}</head>
<body>
  <div class=wrap>
    <h1>Base 선택</h1>
    <div class="toolbar">
      <span class="count-badge">선택: <span id="cnt-base">0</span></span>
    </div>
    <form method=post action="{{ url_for('result') }}" onsubmit="return validateChecked()">
      <input type=hidden name=total_amount value="{{ total_amount }}">
      {% for t in top_selected %}<input type=hidden name="top" value="{{t}}">{% endfor %}
      {% for f in floral_selected %}<input type=hidden name="floral" value="{{f}}">{% endfor %}
      {% for h in herb_selected %}<input type=hidden name="herb" value="{{h}}">{% endfor %}
      <div class=grid>
        {% for name in base_items.keys() %}
        <label class=card>
          <input type="checkbox" name="base" value="{{name}}">
          <span class=thumb><img src="{{ url_for('static', filename=images.get(name)) }}"></span>
          <span class=name>{{name}}</span>
          <span class=en>{{ en[name] }}</span>
          <div class=select-wrap><span class=select-pill>✔ 선택</span></div>
        </label>
        {% endfor %}
      </div>
      <p style="margin-top:12px;"><button class=btn type=submit>결과 보기</button></p>
    </form>
    <script>setupSelection('base','cnt-base');</script>
  </div>
</body></html>
"""

RESULT_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<title>에센셜 오일 부향률 계산 프로그램</title>{{ STYLE|safe }}</head>
<body>
  <div class="qr-fixed"><img src="{{ url_for('qr_png') }}" alt="QR"></div>
  <div class=wrap>
    <h1>블렌딩 결과</h1>
    <p class=muted>선택한 카드들의 블렌딩 비율로 총량을 배분합니다. (0.1ml = 2방울)</p>
    <table>
      <thead>
        <tr>
          <th>구분</th>
          <th>이미지</th>
          <th>카드</th>
          <th>비율(%)</th>
          <th>ml</th>
          <th>방울 수</th>
        </tr>
      </thead>
      <tbody>
        {% for row in rows %}
        <tr>
          <td>{{row.category}}</td>
          <td><img class="t-thumb" src="{{ url_for('static', filename=row.img) }}"></td>
          <td>{{row.name}}</td>
          <td>{{row.pct}}</td>
          <td>{{row.ml}}</td>
          <td>{{row.drops}}</td>
        </tr>
        {% endfor %}
        <tr>
          <th colspan=3>합계</th>
          <th>100.0</th>
          <th>{{total_amount}}</th>
          <th>{{total_drops}}</th>
        </tr>
      </tbody>
    </table>
    <p style="margin-top:12px; text-align:center;">
      <a class=btn href="{{ url_for('index') }}">처음부터 다시</a>
    </p>
  </div>
</body></html>
"""

# =====================
# 유틸
# =====================
def get_checked_list(param_name: str, allowed: dict):
    vals = request.form.getlist(param_name)
    return [v for v in vals if v in allowed]

def build_rows(total_amount, top_sel, floral_sel, herb_sel, base_sel):
    items = []
    for n in top_sel:    items.append(("Top", n, TOP[n]))
    for n in floral_sel: items.append(("Middle–Floral", n, MIDDLE_FLORAL[n]))
    for n in herb_sel:   items.append(("Middle–Herb", n, MIDDLE_HERB[n]))
    for n in base_sel:   items.append(("Base", n, BASE[n]))
    total_weight = sum(f for *_, f in items) or 1

    rows, total_drops = [], 0
    for cat, name, factor in items:
        pct   = round(factor * 100.0 / total_weight, 1)
        ml    = round(factor * total_amount / total_weight, 1)
        drops = int(round(ml / 0.1 * 2))  # 0.1ml = 2방울
        total_drops += drops
        rows.append({"category": cat, "name": name, "img": IMAGES[name], "pct": pct, "ml": ml, "drops": drops})
    return rows, total_drops

# =====================
# 라우트
# =====================
@app.get("/")
def index():
    return render_template_string(AMOUNT_START_HTML, STYLE=STYLE, COMMON_SCRIPTS=COMMON_SCRIPTS)

@app.post("/top")
def top():
    total_amount = float(request.form.get("total_amount", 0))
    return render_template_string(
        TOP_HTML,
        STYLE=STYLE, COMMON_SCRIPTS=COMMON_SCRIPTS,
        top_items=TOP, images=IMAGES, en=EN_LABEL,
        total_amount=round(total_amount,1)
    )

@app.post("/middle_floral")
def middle_floral():
    total_amount   = float(request.form.get("total_amount", 0))
    top_selected   = get_checked_list("top", TOP)  # 0개 허용
    return render_template_string(
        MIDDLE_FLORAL_HTML,
        STYLE=STYLE, COMMON_SCRIPTS=COMMON_SCRIPTS,
        floral=MIDDLE_FLORAL, images=IMAGES, en=EN_LABEL,
        total_amount=round(total_amount,1), top_selected=top_selected
    )

@app.post("/middle_herb")
def middle_herb():
    total_amount   = float(request.form.get("total_amount", 0))
    top_selected   = get_checked_list("top", TOP)
    floral_selected= get_checked_list("floral", MIDDLE_FLORAL)  # 0개 허용
    return render_template_string(
        MIDDLE_HERB_HTML,
        STYLE=STYLE, COMMON_SCRIPTS=COMMON_SCRIPTS,
        herb=MIDDLE_HERB, images=IMAGES, en=EN_LABEL,
        total_amount=round(total_amount,1),
        top_selected=top_selected, floral_selected=floral_selected
    )

@app.post("/base")
def base():
    total_amount   = float(request.form.get("total_amount", 0))
    top_selected   = get_checked_list("top", TOP)
    floral_selected= get_checked_list("floral", MIDDLE_FLORAL)
    herb_selected  = get_checked_list("herb", MIDDLE_HERB)      # 0개 허용
    return render_template_string(
        BASE_HTML,
        STYLE=STYLE, COMMON_SCRIPTS=COMMON_SCRIPTS,
        base_items=BASE, images=IMAGES, en=EN_LABEL,
        total_amount=round(total_amount,1),
        top_selected=top_selected, floral_selected=floral_selected, herb_selected=herb_selected
    )

@app.post("/result")
def result():
    total_amount   = float(request.form.get("total_amount", 0))
    top_selected    = get_checked_list("top", TOP)
    floral_selected = get_checked_list("floral", MIDDLE_FLORAL)
    herb_selected   = get_checked_list("herb", MIDDLE_HERB)
    base_selected   = get_checked_list("base", BASE)
    # 모두 0개일 수도 있음 → rows 비어도 합계/총량은 표기
    rows, total_drops = build_rows(total_amount, top_selected, floral_selected, herb_selected, base_selected)
    return render_template_string(
        RESULT_HTML,
        STYLE=STYLE,
        rows=rows, total_amount=round(total_amount,1), total_drops=total_drops
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
