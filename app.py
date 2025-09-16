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
# 스타일 (모바일 2열, contain, 표 중앙정렬)
# =====================
STYLE = """
  <style>
    :root { --fg:#0b3d1b; --muted:#557166; --bd:#d6f5d6; --sel:#16a34a; --bg:#f0fff0; --pill:#dcfce7; }
    * { box-sizing: border-box; }
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Noto Sans, Helvetica, Arial, sans-serif; margin: 16px; color: var(--fg); background:#fff; }
    .wrap { max-width: 480px; margin: 0 auto; }  /* 모바일 폭 기준 */
    header { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
    .qr { border: 1px solid var(--bd); border-radius: 10px; padding: 6px; background: var(--bg); }
    .muted { color: var(--muted); font-size: 13px; }
    h1 { font-size: 28px; margin: 6px 0 10px; }
    h3 { margin: 8px 0; }
    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 12px; } /* 2열 고정 */
    .card { position: relative; border: 2px solid #e6f5e6; border-radius: 14px; padding: 10px 10px 70px; background:#fff; }
    .thumb { width:100%; aspect-ratio: 1/1; border-radius: 10px; overflow:hidden; background: var(--bg);
             display:flex; align-items:center; justify-content:center; border:1px solid var(--bd);
             margin-bottom:8px; padding:6px; }
    .thumb img { width:100%; height:100%; object-fit: contain; object-position: center; display:block; }
    .name { display:block; margin-top:4px; line-height:1.2; font-weight:800; }
    .en   { display:block; margin-top:3px; margin-bottom:6px; line-height:1.15; font-size:12px; color:#2e7d32; font-weight:600; letter-spacing:.2px; }

    .qty-wrap { position:absolute; left:0; right:0; bottom:8px; display:flex; justify-content:center; gap:8px; align-items:center; }
    .qty { display:inline-flex; align-items:center; gap:8px; background: var(--pill); border:1px solid #b7efc5; border-radius:999px; padding:6px 10px; }
    .qty button { width:28px; height:28px; border-radius:999px; border:1px solid #a7e8b5; background:#fff; color:#065f46; font-weight:800; }
    .qty input { width:48px; text-align:center; border:1px solid #bfe8bf; border-radius:6px; padding:4px; }

    .btn { padding: 12px 14px; border-radius: 10px; background: var(--sel); color: #fff; font-weight: 800; cursor: pointer; border: none; width: 100%; }
    .section { margin-top: 14px; padding: 10px; border-radius: 10px; background: var(--bg); border:1px solid var(--bd); }

    table { width: 100%; border-collapse: collapse; margin-top: 12px; }
    th, td { border-bottom: 1px solid #e6f5e6; text-align: center; padding: 8px; font-size: 14px; }
    thead th { background:#f6fff6; text-align: center; }
    .t-thumb { width:44px; height:44px; border-radius:8px; object-fit:cover; border:1px solid var(--bd); }

    input[type="number"] { padding: 8px; border: 1px solid #bfe8bf; border-radius: 8px; width: 140px; }
    a.btn { text-decoration: none; display: inline-block; }
  </style>
"""

# 공통 수량 위젯(마이너스/플러스)
QTY_WIDGET = """
<div class="qty-wrap">
  <div class="qty">
    <button type="button" onclick="stepQty(this,-1)">−</button>
    <input type="number" min="0" step="1" name="{input_name}" value="{value}">
    <button type="button" onclick="stepQty(this,1)">＋</button>
  </div>
</div>
"""

# 공통 JS (합계 검증용)
COMMON_SCRIPTS = """
<script>
function stepQty(btn, delta){
  const wrap = btn.closest('.qty');
  const input = wrap.querySelector('input[type="number"]');
  const v = parseInt(input.value||'0',10) + delta;
  input.value = Math.max(0, v);
}

function validateCategory(form, prefix){
  // prefix_ 로 시작하는 input 들의 합 >= 1
  const inputs = form.querySelectorAll('input[name^="'+prefix+'_"]');
  let sum = 0;
  inputs.forEach(i => { sum += parseInt(i.value||'0',10); });
  if(sum < 1){
    alert("해당 카테고리에서 최소 1개 이상 선택해 주세요.");
    return false;
  }
  return true;
}
</script>
"""

# =====================
# 템플릿들 (수량 입력형)
# =====================

AMOUNT_START_HTML = f"""
<!doctype html><html lang=ko><head><meta charset=utf-8><title>총량 입력</title>{STYLE}</head>
<body><div class=wrap>
  <h1>총량 입력</h1>
  <form method=post action="{{{{ url_for('top') }}}}">
    <p class=muted>모든 카테고리에서 최소 1개 이상 수량을 입력하세요. (중복 선택/수량 허용)</p>
    <input type=number name=total_amount step=0.1 min=0.1 required placeholder="예) 10.0"> ml
    <p style="margin-top:12px;"><button class=btn type=submit>다음 (Top 선택)</button></p>
  </form>
</div></body></html>
"""

TOP_HTML = f"""
<!doctype html><html lang=ko><head><meta charset=utf-8><title>Top 선택</title>{STYLE}{COMMON_SCRIPTS}</head>
<body><div class=wrap>
  <header>
    <h1>Top 선택</h1>
    <div class=qr><img src="{{{{ url_for('qr_png') }}}}" width=90 height=90 alt="QR"></div>
  </header>
  <p class=muted>Top에서 최소 1개 이상 수량을 입력하세요.</p>
  <form method=post action="{{{{ url_for('middle_floral') }}}}" onsubmit="return validateCategory(this,'top');">
    <input type="hidden" name="total_amount" value="{{{{ total_amount }}}}">
    <div class=grid>
      {{% for name in top_items.keys() %}}
      <div class=card>
        <span class=thumb><img src="{{{{ url_for('static', filename=images.get(name)) }}}}" alt="{{{{name}}}}"></span>
        <span class=name>{{{{name}}}}</span>
        <span class=en>{{{{ en[name] }}}}</span>
        {QTY_WIDGET.replace("{input_name}","top_"+ "{{name}}").replace("{value}","0")}
      </div>
      {{% endfor %}}
    </div>
    <p style="margin-top:12px;"><button class=btn type=submit>다음 (Middle–Floral)</button></p>
  </form>
</div></body></html>
"""

MIDDLE_FLORAL_HTML = f"""
<!doctype html><html lang=ko><head><meta charset=utf-8><title>Middle–Floral</title>{STYLE}{COMMON_SCRIPTS}</head>
<body><div class=wrap>
  <h1>Middle – Floral</h1>
  <form method=post action="{{{{ url_for('middle_herb') }}}}" onsubmit="return validateCategory(this,'floral');">
    <input type=hidden name=total_amount value="{{{{ total_amount }}}}">
    {{% for k,v in top_qty.items() %}}<input type=hidden name="top_{{{{k}}}}" value="{{{{v}}}}">{{% endfor %}}
    <div class=grid>
      {{% for name in floral.keys() %}}
      <div class=card>
        <span class=thumb><img src="{{{{ url_for('static', filename=images.get(name)) }}}}"></span>
        <span class=name>{{{{name}}}}</span>
        <span class=en>{{{{ en[name] }}}}</span>
        {QTY_WIDGET.replace("{input_name}","floral_"+ "{{name}}").replace("{value}","0")}
      </div>
      {{% endfor %}}
    </div>
    <p style="margin-top:12px;"><button class=btn type=submit>다음 (Middle–Herb)</button></p>
  </form>
</div></body></html>
"""

MIDDLE_HERB_HTML = f"""
<!doctype html><html lang=ko><head><meta charset=utf-8><title>Middle–Herb</title>{STYLE}{COMMON_SCRIPTS}</head>
<body><div class=wrap>
  <h1>Middle – Herb</h1>
  <form method=post action="{{{{ url_for('base') }}}}" onsubmit="return validateCategory(this,'herb');">
    <input type=hidden name=total_amount value="{{{{ total_amount }}}}">
    {{% for k,v in top_qty.items() %}}<input type=hidden name="top_{{{{k}}}}" value="{{{{v}}}}">{{% endfor %}}
    {{% for k,v in floral_qty.items() %}}<input type=hidden name="floral_{{{{k}}}}" value="{{{{v}}}}">{{% endfor %}}
    <div class=grid>
      {{% for name in herb.keys() %}}
      <div class=card>
        <span class=thumb><img src="{{{{ url_for('static', filename=images.get(name)) }}}}"></span>
        <span class=name>{{{{name}}}}</span>
        <span class=en>{{{{ en[name] }}}}</span>
        {QTY_WIDGET.replace("{input_name}","herb_"+ "{{name}}").replace("{value}","0")}
      </div>
      {{% endfor %}}
    </div>
    <p style="margin-top:12px;"><button class=btn type=submit>다음 (Base)</button></p>
  </form>
</div></body></html>
"""

BASE_HTML = f"""
<!doctype html><html lang=ko><head><meta charset=utf-8><title>Base 선택</title>{STYLE}{COMMON_SCRIPTS}</head>
<body><div class=wrap>
  <h1>Base 선택</h1>
  <p class=muted>Base에서 최소 1개 이상 수량을 입력하세요.</p>
  <form method=post action="{{{{ url_for('result') }}}}" onsubmit="return validateCategory(this,'base');">
    <input type=hidden name=total_amount value="{{{{ total_amount }}}}">
    {{% for k,v in top_qty.items() %}}<input type=hidden name="top_{{{{k}}}}" value="{{{{v}}}}">{{% endfor %}}
    {{% for k,v in floral_qty.items() %}}<input type=hidden name="floral_{{{{k}}}}" value="{{{{v}}}}">{{% endfor %}}
    {{% for k,v in herb_qty.items() %}}<input type=hidden name="herb_{{{{k}}}}" value="{{{{v}}}}">{{% endfor %}}
    <div class=grid>
      {{% for name in base_items.keys() %}}
      <div class=card>
        <span class=thumb><img src="{{{{ url_for('static', filename=images.get(name)) }}}}"></span>
        <span class=name>{{{{name}}}}</span>
        <span class=en>{{{{ en[name] }}}}</span>
        {QTY_WIDGET.replace("{input_name}","base_"+ "{{name}}").replace("{value}","0")}
      </div>
      {{% endfor %}}
    </div>
    <p style="margin-top:12px;"><button class=btn type=submit>결과 보기</button></p>
  </form>
</div></body></html>
"""

RESULT_HTML = f"""
<!doctype html><html lang=ko><head><meta charset=utf-8><title>블렌딩 결과</title>{STYLE}</head>
<body><div class=wrap>
  <header>
    <h1 style="text-align:center;">블렌딩 결과</h1>
    <div class=qr><img src="{{{{ url_for('qr_png') }}}}" width=90 height=90 alt="QR"></div>
  </header>
  <p class=muted style="text-align:center;">입력한 총량을 비율에 따라 각 선택 수량 × 블렌딩 팩터로 배분합니다.</p>

  <table>
    <thead><tr><th>구분</th><th>이미지</th><th>카드</th><th>영문</th><th>수량</th><th>팩터</th><th>비율(%)</th><th>ml</th></tr></thead>
    <tbody>
      {{% for row in rows %}}
      <tr>
        <td>{{{{row.category}}}}</td>
        <td><img class="t-thumb" src="{{{{ url_for('static', filename=row.img) }}}}"></td>
        <td>{{{{row.name}}}}</td>
        <td>{{{{row.en}}}}</td>
        <td>{{{{row.qty}}}}</td>
        <td>{{{{row.factor}}}}</td>
        <td>{{{{row.pct}}}}</td>
        <td>{{{{row.ml}}}}</td>
      </tr>
      {{% endfor %}}
      <tr><th colspan=5>합계</th><th>{{{{total_weight}}}}</th><th>100.0</th><th>{{{{total_amount}}}}</th></tr>
    </tbody>
  </table>

  <p style="margin-top:12px; text-align:center;"><a class=btn href="{{{{ url_for('index') }}}}">처음부터 다시</a></p>
</div></body></html>
"""

# =====================
# 유틸
# =====================
def get_qty_from_form(prefix: str, options: dict):
    """폼에서 prefix_키 형태로 넘어온 수량을 dict로 반환 (0 이상 정수)."""
    res = {}
    for name in options.keys():
        try:
            v = int(request.form.get(f"{prefix}_{name}", 0))
        except ValueError:
            v = 0
        if v < 0: v = 0
        res[name] = v
    return res

def build_rows(total_amount, top_qty, floral_qty, herb_qty, base_qty):
    """결과 테이블에 쓸 행 데이터 만들기."""
    items = []  # (category, name, qty, factor)
    for name, q in top_qty.items():
        if q>0: items.append(("Top", name, q, TOP[name]))
    for name, q in floral_qty.items():
        if q>0: items.append(("Middle–Floral", name, q, MIDDLE_FLORAL[name]))
    for name, q in herb_qty.items():
        if q>0: items.append(("Middle–Herb", name, q, MIDDLE_HERB[name]))
    for name, q in base_qty.items():
        if q>0: items.append(("Base", name, q, BASE[name]))

    total_weight = sum(q * f for (_,_,q,f) in items)
    if total_weight <= 0:
        total_weight = 1

    rows = []
    for cat, name, q, factor in items:
        part = q * factor
        pct = round(part * 100.0 / total_weight, 1)
        ml = round(part * total_amount / total_weight, 1)
        rows.append({
            "category": cat,
            "name": name,
            "en": EN_LABEL[name],
            "img": IMAGES[name],
            "qty": q,
            "factor": factor,
            "pct": pct,
            "ml": ml,
        })
    return rows, total_weight

# =====================
# 라우트
# =====================
@app.get("/")
def index():
    return render_template_string(AMOUNT_START_HTML)

@app.post("/top")
def top():
    total_amount = float(request.form.get("total_amount", 0))
    return render_template_string(TOP_HTML, top_items=TOP, images=IMAGES, en=EN_LABEL, total_amount=round(total_amount,1))

@app.post("/middle_floral")
def middle_floral():
    total_amount = float(request.form.get("total_amount", 0))
    top_qty = get_qty_from_form("top", TOP)
    # 유효성: Top 합계 >= 1
    if sum(top_qty.values()) < 1:
        return redirect(url_for("top"))
    return render_template_string(MIDDLE_FLORAL_HTML, floral=MIDDLE_FLORAL, images=IMAGES, en=EN_LABEL,
                                  total_amount=round(total_amount,1), top_qty=top_qty)

@app.post("/middle_herb")
def middle_herb():
    total_amount = float(request.form.get("total_amount", 0))
    top_qty = get_qty_from_form("top", TOP)
    floral_qty = get_qty_from_form("floral", MIDDLE_FLORAL)
    # 유효성: Floral 합계 >= 1
    if sum(floral_qty.values()) < 1:
        return redirect(url_for("middle_floral"))
    return render_template_string(MIDDLE_HERB_HTML, herb=MIDDLE_HERB, images=IMAGES, en=EN_LABEL,
                                  total_amount=round(total_amount,1), top_qty=top_qty, floral_qty=floral_qty)

@app.post("/base")
def base():
    total_amount = float(request.form.get("total_amount", 0))
    top_qty = get_qty_from_form("top", TOP)
    floral_qty = get_qty_from_form("floral", MIDDLE_FLORAL)
    herb_qty = get_qty_from_form("herb", MIDDLE_HERB)
    # 유효성: Herb 합계 >= 1
    if sum(herb_qty.values()) < 1:
        return redirect(url_for("middle_herb"))
    return render_template_string(BASE_HTML, base_items=BASE, images=IMAGES, en=EN_LABEL,
                                  total_amount=round(total_amount,1),
                                  top_qty=top_qty, floral_qty=floral_qty, herb_qty=herb_qty)

@app.post("/result")
def result():
    total_amount = float(request.form.get("total_amount", 0))
    top_qty   = get_qty_from_form("top", TOP)
    floral_qty= get_qty_from_form("floral", MIDDLE_FLORAL)
    herb_qty  = get_qty_from_form("herb", MIDDLE_HERB)
    base_qty  = get_qty_from_form("base", BASE)
    # 유효성: Base 합계 >= 1
    if sum(base_qty.values()) < 1:
        return redirect(url_for("base"))

    rows, total_weight = build_rows(total_amount, top_qty, floral_qty, herb_qty, base_qty)
    return render_template_string(RESULT_HTML,
                                  rows=rows,
                                  total_weight=total_weight,
                                  total_amount=round(total_amount,1))

@app.get("/qr.png")
def qr_png():
    base = request.url_root.rstrip("/")
    img = qrcode.make(f"{base}/")
    buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
    return send_file(buf, mimetype="image/png", download_name="qr.png")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
