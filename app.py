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
# 스타일 (모바일 2열, 이미지 1:1 cover, 표 중앙정렬)
# =====================
STYLE = """
<style>
  body { 
    font-family: system-ui, -apple-system, Segoe UI, Roboto, Noto Sans, Helvetica, Arial, sans-serif; 
    margin: 8px;               /* ⬅️ 좌우 여백 크게 줄임 */
    padding: 0;
    font-size: 20px;           /* ⬅️ 기본 글씨 크기 키움 */
    line-height: 1.6;
  }
  .wrap { 
    max-width: 100%;           /* ⬅️ 화면 전체 너비 활용 */
    margin: 0 auto; 
    padding: 0 4px;
  }
  h1, h3 { 
    font-size: 28px;           /* ⬅️ 제목 크게 */
    text-align: center; 
    margin-bottom: 12px;
  }
  p, label { 
    font-size: 22px;           /* ⬅️ 본문 글씨 크게 */
  }
  .btn { 
    font-size: 22px;           /* ⬅️ 버튼 글씨 크게 */
    padding: 16px 20px;        /* ⬅️ 버튼 자체도 크게 */
    border-radius: 12px;
    background: #3a7a3a;       /* 진한 초록 */
    color: #fff; 
    font-weight: 700; 
    cursor: pointer; 
    border: none; 
    width: 100%;               /* ⬅️ 버튼 가로 전체 */
    margin-top: 12px;
  }
  input[type="number"] {
    font-size: 24px;           /* ⬅️ 총량 입력칸 크게 */
    padding: 12px;
    width: 100%;
    border: 2px solid #3a7a3a;
    border-radius: 8px;
    text-align: center;
  }
  .grid { 
    display: grid; 
    grid-template-columns: repeat(2, 1fr);  /* ⬅️ 항상 2열 */
    gap: 12px; 
    margin-top: 12px; 
  }
  .card { 
    border: 2px solid #3a7a3a;
    border-radius: 12px; 
    padding: 12px; 
    text-align: center; 
    background: #f8fff8;
  }
  .thumb { 
    width: 100%; 
    aspect-ratio: 1 / 1; 
    border-radius: 12px; 
    overflow: hidden; 
    display: flex; 
    align-items: center; 
    justify-content: center; 
    margin-bottom: 8px;
  }
  .thumb img { 
    width: 100%; 
    height: 100%; 
    object-fit: contain; 
  }
  table { 
    width: 100%; 
    border-collapse: collapse; 
    margin-top: 16px; 
    font-size: 20px; 
  }
  th, td { 
    border-bottom: 1px solid #ccc; 
    text-align: center; 
    padding: 12px; 
  }
</style>

"""

CHECK_ICON = """
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""

# 공통 JS: 선택 개수 카운터 & 버튼 활성화
COMMON_SCRIPTS = """
<script>
function setupSelection(groupName, counterId, submitId){
  const form = document.querySelector('form');
  const boxes = form.querySelectorAll('input[name="'+groupName+'"]');
  const counter = document.getElementById(counterId);
  const submit = document.getElementById(submitId);

  function refresh(){
    const checked = form.querySelectorAll('input[name="'+groupName+'"]:checked').length;
    if(counter) counter.textContent = checked;
    if(submit) submit.disabled = (checked < 1);
  }
  boxes.forEach(b => b.addEventListener('change', refresh));
  refresh();
}

function validateChecked(form, groupName){
  const boxes = form.querySelectorAll('input[name="'+groupName+'"]:checked');
  if(boxes.length < 1){
    alert("최소 1개 이상 선택해 주세요.");
    return false;
  }
  return true;
}
</script>
"""

# =====================
# 템플릿들 (체크박스 선택형)
# =====================
AMOUNT_START_HTML = f"""
<!doctype html><html lang=ko><head><meta charset=utf-8><title>총량 입력</title>{STYLE}</head>
<body><div class=wrap>
  <h1>총량 입력</h1>
  <form method=post action="{{{{ url_for('top') }}}}">
    <p class=muted>오늘 만들 에센셜 오일의 총량을 입력하세요.</p>
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
  <div class="toolbar">
    <p class=muted>Top에서 최소 1개 이상 선택</p>
    <span class="count-badge">선택: <span id="cnt-top">0</span></span>
  </div>
  <form method=post action="{{{{ url_for('middle_floral') }}}}" onsubmit="return validateChecked(this,'top')">
    <input type="hidden" name="total_amount" value="{{{{ total_amount }}}}">
    <div class=grid>
      {{% for name in top_items.keys() %}}
      <label class=card>
        <input type="checkbox" name="top" value="{{{{name}}}}">
        <span class=thumb><img src="{{{{ url_for('static', filename=images.get(name)) }}}}" alt="{{{{name}}}}"></span>
        <span class=name>{{{{name}}}}</span>
        <span class=en>{{{{ en[name] }}}}</span>
        <div class=select-wrap><span class=select-pill>{CHECK_ICON} 선택</span></div>
      </label>
      {{% endfor %}}
    </div>
    <p style="margin-top:12px;">
      <button id="btn-next-top" class=btn type=submit disabled>다음 (Middle–Floral)</button>
    </p>
  </form>
  <script>setupSelection('top','cnt-top','btn-next-top');</script>
</div></body></html>
"""

MIDDLE_FLORAL_HTML = f"""
<!doctype html><html lang=ko><head><meta charset=utf-8><title>Middle–Floral</title>{STYLE}{COMMON_SCRIPTS}</head>
<body><div class=wrap>
  <h1>Middle – Floral</h1>
  <div class="toolbar">
    <p class=muted>Floral에서 최소 1개 이상 선택</p>
    <span class="count-badge">선택: <span id="cnt-floral">0</span></span>
  </div>
  <form method=post action="{{{{ url_for('middle_herb') }}}}" onsubmit="return validateChecked(this,'floral')">
    <input type=hidden name=total_amount value="{{{{ total_amount }}}}">
    {{% for t in top_selected %}}<input type=hidden name="top" value="{{{{t}}}}">{{% endfor %}}
    <div class=grid>
      {{% for name in floral.keys() %}}
      <label class=card>
        <input type="checkbox" name="floral" value="{{{{name}}}}">
        <span class=thumb><img src="{{{{ url_for('static', filename=images.get(name)) }}}}"></span>
        <span class=name>{{{{name}}}}</span>
        <span class=en>{{{{ en[name] }}}}</span>
        <div class=select-wrap><span class=select-pill>{CHECK_ICON} 선택</span></div>
      </label>
      {{% endfor %}}
    </div>
    <p style="margin-top:12px;">
      <button id="btn-next-floral" class=btn type=submit disabled>다음 (Middle–Herb)</button>
    </p>
  </form>
  <script>setupSelection('floral','cnt-floral','btn-next-floral');</script>
</div></body></html>
"""

MIDDLE_HERB_HTML = f"""
<!doctype html><html lang=ko><head><meta charset=utf-8><title>Middle–Herb</title>{STYLE}{COMMON_SCRIPTS}</head>
<body><div class=wrap>
  <h1>Middle – Herb</h1>
  <div class="toolbar">
    <p class=muted>Herb에서 최소 1개 이상 선택</p>
    <span class="count-badge">선택: <span id="cnt-herb">0</span></span>
  </div>
  <form method=post action="{{{{ url_for('base') }}}}" onsubmit="return validateChecked(this,'herb')">
    <input type=hidden name=total_amount value="{{{{ total_amount }}}}">
    {{% for t in top_selected %}}<input type=hidden name="top" value="{{{{t}}}}">{{% endfor %}}
    {{% for f in floral_selected %}}<input type=hidden name="floral" value="{{{{f}}}}">{{% endfor %}}
    <div class=grid>
      {{% for name in herb.keys() %}}
      <label class=card>
        <input type="checkbox" name="herb" value="{{{{name}}}}">
        <span class=thumb><img src="{{{{ url_for('static', filename=images.get(name)) }}}}"></span>
        <span class=name>{{{{name}}}}</span>
        <span class=en>{{{{ en[name] }}}}</span>
        <div class=select-wrap><span class=select-pill>{CHECK_ICON} 선택</span></div>
      </label>
      {{% endfor %}}
    </div>
    <p style="margin-top:12px;">
      <button id="btn-next-herb" class=btn type=submit disabled>다음 (Base)</button>
    </p>
  </form>
  <script>setupSelection('herb','cnt-herb','btn-next-herb');</script>
</div></body></html>
"""

BASE_HTML = f"""
<!doctype html><html lang=ko><head><meta charset=utf-8><title>Base 선택</title>{STYLE}{COMMON_SCRIPTS}</head>
<body><div class=wrap>
  <h1>Base 선택</h1>
  <div class="toolbar">
    <p class=muted>Base에서 최소 1개 이상 선택</p>
    <span class="count-badge">선택: <span id="cnt-base">0</span></span>
  </div>
  <form method=post action="{{{{ url_for('result') }}}}" onsubmit="return validateChecked(this,'base')">
    <input type=hidden name=total_amount value="{{{{ total_amount }}}}">
    {{% for t in top_selected %}}<input type=hidden name="top" value="{{{{t}}}}">{{% endfor %}}
    {{% for f in floral_selected %}}<input type=hidden name="floral" value="{{{{f}}}}">{{% endfor %}}
    {{% for h in herb_selected %}}<input type=hidden name="herb" value="{{{{h}}}}">{{% endfor %}}
    <div class=grid>
      {{% for name in base_items.keys() %}}
      <label class=card>
        <input type="checkbox" name="base" value="{{{{name}}}}">
        <span class=thumb><img src="{{{{ url_for('static', filename=images.get(name)) }}}}"></span>
        <span class=name>{{{{name}}}}</span>
        <span class=en>{{{{ en[name] }}}}</span>
        <div class=select-wrap><span class=select-pill>{CHECK_ICON} 선택</span></div>
      </label>
      {{% endfor %}}
    </div>
    <p style="margin-top:12px;">
      <button id="btn-next-base" class=btn type=submit disabled>결과 보기</button>
    </p>
  </form>
  <script>setupSelection('base','cnt-base','btn-next-base');</script>
</div></body></html>
"""

RESULT_HTML = f"""
<!doctype html><html lang=ko><head><meta charset=utf-8><title>블렌딩 결과</title>{STYLE}</head>
<body><div class=wrap>
  <header>
    <h1 style="text-align:center;">블렌딩 결과</h1>
    <div class=qr><img src="{{{{ url_for('qr_png') }}}}" width=90 height=90 alt="QR"></div>
  </header>
  <p class=muted style="text-align:center;">선택한 카드들의 블렌딩 팩터 합을 기준으로 총량을 배분합니다.</p>

  <table>
    <thead>
      <tr>
        <th>구분</th>
        <th>이미지</th>
        <th>카드</th>
        <th>팩터</th>
        <th>비율(%)</th>
        <th>ml</th>
      </tr>
    </thead>
    <tbody>
      {{% for row in rows %}}
      <tr>
        <td>{{{{row.category}}}}</td>
        <td><img class="t-thumb" src="{{{{ url_for('static', filename=row.img) }}}}"></td>
        <td>{{{{row.name}}}}</td>
        <td>{{{{row.factor}}}}</td>
        <td>{{{{row.pct}}}}</td>
        <td>{{{{row.ml}}}}</td>
      </tr>
      {{% endfor %}}
      <tr>
        <th colspan=3>합계</th>
        <th>{{{{total_weight}}}}</th>
        <th>100.0</th>
        <th>{{{{total_amount}}}}</th>
      </tr>
    </tbody>
  </table>

  <p style="margin-top:12px; text-align:center;">
    <a class=btn href="{{{{ url_for('index') }}}}">처음부터 다시</a>
  </p>
</div></body></html>
"""


# =====================
# 유틸
# =====================
def get_checked_list(param_name: str, allowed: dict):
    """체크박스로 넘어온 값 목록(문자열)을 허용 키로 필터링."""
    vals = request.form.getlist(param_name)
    return [v for v in vals if v in allowed]

def build_rows(total_amount, top_sel, floral_sel, herb_sel, base_sel):
    """결과 테이블 행 구성."""
    items = []  # (category, name, factor)
    for name in top_sel:    items.append(("Top", name, TOP[name]))
    for name in floral_sel: items.append(("Middle–Floral", name, MIDDLE_FLORAL[name]))
    for name in herb_sel:   items.append(("Middle–Herb", name, MIDDLE_HERB[name]))
    for name in base_sel:   items.append(("Base", name, BASE[name]))

    total_weight = sum(f for (_,_,f) in items)
    if total_weight <= 0:
        total_weight = 1

    rows = []
    for cat, name, factor in items:
        pct = round(factor * 100.0 / total_weight, 1)
        ml  = round(factor * total_amount / total_weight, 1)
        rows.append({
            "category": cat,
            "name": name,
            "en": EN_LABEL[name],
            "img": IMAGES[name],
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
    top_selected = get_checked_list("top", TOP)
    if len(top_selected) < 1:
        return redirect(url_for("top"))
    return render_template_string(MIDDLE_FLORAL_HTML,
                                  floral=MIDDLE_FLORAL, images=IMAGES, en=EN_LABEL,
                                  total_amount=round(total_amount,1), top_selected=top_selected)

@app.post("/middle_herb")
def middle_herb():
    total_amount = float(request.form.get("total_amount", 0))
    top_selected = get_checked_list("top", TOP)
    floral_selected = get_checked_list("floral", MIDDLE_FLORAL)
    if len(floral_selected) < 1:
        return redirect(url_for("middle_floral"))
    return render_template_string(MIDDLE_HERB_HTML,
                                  herb=MIDDLE_HERB, images=IMAGES, en=EN_LABEL,
                                  total_amount=round(total_amount,1),
                                  top_selected=top_selected, floral_selected=floral_selected)

@app.post("/base")
def base():
    total_amount = float(request.form.get("total_amount", 0))
    top_selected = get_checked_list("top", TOP)
    floral_selected = get_checked_list("floral", MIDDLE_FLORAL)
    herb_selected = get_checked_list("herb", MIDDLE_HERB)
    if len(herb_selected) < 1:
        return redirect(url_for("middle_herb"))
    return render_template_string(BASE_HTML,
                                  base_items=BASE, images=IMAGES, en=EN_LABEL,
                                  total_amount=round(total_amount,1),
                                  top_selected=top_selected, floral_selected=floral_selected, herb_selected=herb_selected)

@app.post("/result")
def result():
    total_amount = float(request.form.get("total_amount", 0))
    top_selected    = get_checked_list("top", TOP)
    floral_selected = get_checked_list("floral", MIDDLE_FLORAL)
    herb_selected   = get_checked_list("herb", MIDDLE_HERB)
    base_selected   = get_checked_list("base", BASE)

    if len(base_selected) < 1:
        return redirect(url_for("base"))

    rows, total_weight = build_rows(total_amount, top_selected, floral_selected, herb_selected, base_selected)
    return render_template_string(
        RESULT_HTML,
        rows=rows,
        total_weight=total_weight,
        total_amount=round(total_amount,1)
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
