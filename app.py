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
# 스타일 (QR은 결과 페이지에서만 사용)
# =====================
STYLE = """
  <style>
    :root {
      --fg:#0b3d1b; --muted:#4f665c; --bd:#cceccc; --sel:#166534; --bg:#f6fff6;
    }
    body { margin:4px; font-family:system-ui; background:#fff; color:var(--fg); font-size:18px; }
    .wrap { max-width:480px; margin:0 auto; }
    h1 { font-size:28px; margin:8px 0; text-align:center; }
    .btn { background:var(--sel); color:#fff; padding:14px; border-radius:10px; font-size:20px; border:none; width:100%; }
    .grid { display:grid; grid-template-columns:repeat(2,1fr); gap:10px; }
    .card { border:1px solid var(--bd); border-radius:10px; padding:6px; }
    table { width:100%; border-collapse:collapse; margin-top:12px; font-size:17px; }
    th,td { border:1px solid #ddd; padding:8px; text-align:center; }
    .qr-fixed { position:fixed; top:10px; right:10px; width:90px; height:90px; }
    .qr-fixed img { width:100%; height:100%; }
  </style>
"""

# =====================
# 템플릿
# =====================
AMOUNT_START_HTML = f"""
<!doctype html><html><head>{STYLE}</head><body>
<div class=wrap>
  <h1>총량 입력</h1>
  <form method=post action="{{{{ url_for('top') }}}}">
    <input type=number name=total_amount step=0.1 min=0.1 required placeholder="예) 10.0"> ml
    <p><button class=btn type=submit>다음 (Top 선택)</button></p>
  </form>
</div>
</body></html>
"""

TOP_HTML = f"""
<!doctype html><html><head>{STYLE}</head><body>
<div class=wrap>
  <h1>Top 선택</h1>
  <form method=post action="{{{{ url_for('middle_floral') }}}}">
    <input type=hidden name=total_amount value="{{{{ total_amount }}}}">
    {{% for name in top_items.keys() %}}
      <label><input type=checkbox name=top value="{{{{name}}}}"> {{{{name}}}}</label><br>
    {{% endfor %}}
    <p><button class=btn type=submit>다음 (Middle–Floral)</button></p>
  </form>
</div>
</body></html>
"""

MIDDLE_FLORAL_HTML = f"""
<!doctype html><html><head>{STYLE}</head><body>
<div class=wrap>
  <h1>Middle – Floral</h1>
  <form method=post action="{{{{ url_for('middle_herb') }}}}">
    <input type=hidden name=total_amount value="{{{{ total_amount }}}}">
    {{% for t in top_selected %}}<input type=hidden name=top value="{{{{t}}}}">{{% endfor %}}
    {{% for name in floral.keys() %}}
      <label><input type=checkbox name=floral value="{{{{name}}}}"> {{{{name}}}}</label><br>
    {{% endfor %}}
    <p><button class=btn type=submit>다음 (Middle–Herb)</button></p>
  </form>
</div>
</body></html>
"""

MIDDLE_HERB_HTML = f"""
<!doctype html><html><head>{STYLE}</head><body>
<div class=wrap>
  <h1>Middle – Herb</h1>
  <form method=post action="{{{{ url_for('base') }}}}">
    <input type=hidden name=total_amount value="{{{{ total_amount }}}}">
    {{% for t in top_selected %}}<input type=hidden name=top value="{{{{t}}}}">{{% endfor %}}
    {{% for f in floral_selected %}}<input type=hidden name=floral value="{{{{f}}}}">{{% endfor %}}
    {{% for name in herb.keys() %}}
      <label><input type=checkbox name=herb value="{{{{name}}}}"> {{{{name}}}}</label><br>
    {{% endfor %}}
    <p><button class=btn type=submit>다음 (Base)</button></p>
  </form>
</div>
</body></html>
"""

BASE_HTML = f"""
<!doctype html><html><head>{STYLE}</head><body>
<div class=wrap>
  <h1>Base 선택</h1>
  <form method=post action="{{{{ url_for('result') }}}}">
    <input type=hidden name=total_amount value="{{{{ total_amount }}}}">
    {{% for t in top_selected %}}<input type=hidden name=top value="{{{{t}}}}">{{% endfor %}}
    {{% for f in floral_selected %}}<input type=hidden name=floral value="{{{{f}}}}">{{% endfor %}}
    {{% for h in herb_selected %}}<input type=hidden name=herb value="{{{{h}}}}">{{% endfor %}}
    {{% for name in base_items.keys() %}}
      <label><input type=checkbox name=base value="{{{{name}}}}"> {{{{name}}}}</label><br>
    {{% endfor %}}
    <p><button class=btn type=submit>결과 보기</button></p>
  </form>
</div>
</body></html>
"""

RESULT_HTML = f"""
<!doctype html><html><head>{STYLE}</head><body>
<div class="qr-fixed"><img src="{{{{ url_for('qr_png') }}}}"></div>
<div class=wrap>
  <h1>블렌딩 결과</h1>
  <table>
    <thead><tr><th>구분</th><th>카드</th><th>비율(%)</th><th>ml</th><th>방울</th></tr></thead>
    <tbody>
      {{% for row in rows %}}
      <tr>
        <td>{{{{row.category}}}}</td>
        <td>{{{{row.name}}}}</td>
        <td>{{{{row.pct}}}}</td>
        <td>{{{{row.ml}}}}</td>
        <td>{{{{row.drops}}}}</td>
      </tr>
      {{% endfor %}}
      <tr><th colspan=2>합계</th><th>100</th><th>{{{{total_amount}}}}</th><th>{{{{total_drops}}}}</th></tr>
    </tbody>
  </table>
  <p><a class=btn href="{{{{ url_for('index') }}}}">처음부터 다시</a></p>
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
    for n in top_sel: items.append(("Top", n, TOP[n]))
    for n in floral_sel: items.append(("Middle–Floral", n, MIDDLE_FLORAL[n]))
    for n in herb_sel: items.append(("Middle–Herb", n, MIDDLE_HERB[n]))
    for n in base_sel: items.append(("Base", n, BASE[n]))
    total_factor = sum(f for _,_,f in items) or 1

    rows = []
    total_drops = 0
    for cat, name, f in items:
        pct = round(f*100/total_factor,1)
        ml = round(f*total_amount/total_factor,1)
        drops = int(round(ml*20))  # 1ml=20방울
        total_drops += drops
        rows.append({"category":cat,"name":name,"pct":pct,"ml":ml,"drops":drops})
    return rows, total_drops

# =====================
# 라우트
# =====================
@app.get("/")
def index(): return render_template_string(AMOUNT_START_HTML)

@app.post("/top")
def top():
    return render_template_string(TOP_HTML, top_items=TOP, total_amount=request.form["total_amount"])

@app.post("/middle_floral")
def middle_floral():
    return render_template_string(MIDDLE_FLORAL_HTML, floral=MIDDLE_FLORAL,
        total_amount=request.form["total_amount"], top_selected=get_checked_list("top", TOP))

@app.post("/middle_herb")
def middle_herb():
    return render_template_string(MIDDLE_HERB_HTML, herb=MIDDLE_HERB,
        total_amount=request.form["total_amount"],
        top_selected=get_checked_list("top", TOP), floral_selected=get_checked_list("floral", MIDDLE_FLORAL))

@app.post("/base")
def base():
    return render_template_string(BASE_HTML, base_items=BASE,
        total_amount=request.form["total_amount"],
        top_selected=get_checked_list("top", TOP),
        floral_selected=get_checked_list("floral", MIDDLE_FLORAL),
        herb_selected=get_checked_list("herb", MIDDLE_HERB))

@app.post("/result")
def result():
    total_amount = float(request.form["total_amount"])
    rows, total_drops = build_rows(total_amount,
                                   get_checked_list("top", TOP),
                                   get_checked_list("floral", MIDDLE_FLORAL),
                                   get_checked_list("herb", MIDDLE_HERB),
                                   get_checked_list("base", BASE))
    return render_template_string(RESULT_HTML, rows=rows,
                                  total_amount=round(total_amount,1),
                                  total_drops=total_drops)

@app.get("/qr.png")
def qr_png():
    img = qrcode.make(request.url_root)
    buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
    return send_file(buf, mimetype="image/png")

if __name__ == "__main__":
    app.run(debug=True)
