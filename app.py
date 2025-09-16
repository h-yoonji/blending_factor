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
# 공통 스타일 템플릿
# =====================
STYLE = """
  <style>
    :root { --fg:#111; --muted:#666; --bd:#e5e5e5; }
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Noto Sans, Helvetica, Arial, sans-serif; margin: 32px; color: var(--fg); }
    .wrap { max-width: 800px; margin: 0 auto; }
    header { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
    .qr { border: 1px solid var(--bd); border-radius: 12px; padding: 8px; }
    .muted { color: var(--muted); font-size: 14px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; margin-top: 12px; }
    .card { border: 1px solid #ddd; border-radius: 12px; padding: 12px; }
    .btn { padding: 12px 16px; border-radius: 10px; background: #111; color: #fff; font-weight: 600; cursor: pointer; border: none; }
    .section { margin-top: 10px; padding: 10px; border-radius: 10px; background: #fafafa; }
    table { width: 100%; border-collapse: collapse; margin-top: 16px; }
    th, td { border-bottom: 1px solid #eee; text-align: left; padding: 10px; }
    input[type="number"] { padding: 10px; border: 1px solid #ccc; border-radius: 8px; width: 160px; }
    a.btn { text-decoration: none; display: inline-block; }
  </style>
"""

# =====================
# 페이지 템플릿들
# =====================
TOP_HTML = f"""
<!doctype html><html lang=ko><head><meta charset=utf-8><title>Top note 선택</title>{STYLE}</head>
<body><div class=wrap>
  <header>
    <h1 style="margin:0;">Top note 선택</h1>
    <div class=qr><img src="{{{{ url_for('qr_png') }}}}" width=110 height=110 alt="QR"></div>
  </header>
  <p class=muted>레몬 / 스윗오렌지 / 버가못 / 그린애플 중 1개 선택</p>
  <form method=post action="{{{{ url_for('middle') }}}}">
    <div class=grid>
      {{% for name, w in top_items.items() %}}
      <label class=card>
        <input type=radio name=top value="{{{{name}}}}" required>
        <strong>{{{{name}}}}</strong><br>
        <span class=muted>블렌딩 팩터 = {{{{w}}}}</span>
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
  <h1 style="margin:0;">Middle note 선택</h1>
  <form method=post action="{{{{ url_for('base') }}}}">
    <input type=hidden name=top value="{{{{top}}}}">

    <div class=section>
      <h3>플로랄</h3>
      <div class=grid>
        {{% for name, w in floral.items() %}}
        <label class=card>
          <input type=radio name=middle value="{{{{name}}}}" required>
          <strong>{{{{name}}}}</strong><br>
          <span class=muted>블렌딩 팩터 = {{{{w}}}}</span>
        </label>
        {{% endfor %}}
      </div>
    </div>

    <div class=section>
      <h3>허브</h3>
      <div class=grid>
        {{% for name, w in herb.items() %}}
        <label class=card>
          <input type=radio name=middle value="{{{{name}}}}" required>
          <strong>{{{{name}}}}</strong><br>
          <span class=muted>블렌딩 팩터 = {{{{w}}}}</span>
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
  <h1 style="margin:0;">Base note 선택</h1>
  <form method=post action="{{{{ url_for('amount') }}}}">
    <input type=hidden name=top value="{{{{top}}}}">
    <input type=hidden name=middle value="{{{{middle}}}}">
    <div class=grid>
      {{% for name, w in base_items.items() %}}
      <label class=card>
        <input type=radio name=base value="{{{{name}}}}" required>
        <strong>{{{{name}}}}</strong><br>
        <span class=muted>블렌딩 팩터 = {{{{w}}}}</span>
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
  <h1>블렌딩 결과</h1>
  <p class=muted>입력한 총량을 비율에 따라 카드별 ml로 환산합니다.</p>
  <table>
    <thead><tr><th>카테고리</th><th>카드</th><th>블렌딩 팩터</th><th>비율(%)</th><th>실제 ml</th></tr></thead>
    <tbody>
      <tr><td>Top</td><td>{{{{top}}}}</td><td>{{{{w_top}}}}</td><td>{{{{p_top}}}}</td><td>{{{{ml_top}}}}</td></tr>
      <tr><td>Middle</td><td>{{{{middle}}}}</td><td>{{{{w_mid}}}}</td><td>{{{{p_mid}}}}</td><td>{{{{ml_mid}}}}</td></tr>
      <tr><td>Base</td><td>{{{{base}}}}</td><td>{{{{w_base}}}}</td><td>{{{{p_base}}}}</td><td>{{{{ml_base}}}}</td></tr>
      <tr><th colspan=2>합계</th><th>{{{{total}}}}</th><th>100.0</th><th>{{{{total_amount}}}}</th></tr>
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
    return render_template_string(TOP_HTML, top_items=TOP)

@app.post("/middle")
def middle():
    top = request.form.get("top", "")
    if not top:
        return redirect(url_for("index"))
    return render_template_string(MIDDLE_HTML, top=top, floral=MIDDLE_FLORAL, herb=MIDDLE_HERB)

@app.post("/base")
def base():
    top = request.form.get("top", "")
    middle = request.form.get("middle", "")
    if not (top and middle):
        return redirect(url_for("index"))
    return render_template_string(BASE_HTML, top=top, middle=middle, base_items=BASE)

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
    )

@app.get("/qr.png")
def qr_png():
    # 현재 요청의 퍼블릭 루트 URL 기준으로 QR 생성 (배포/로컬 모두 자동 대응)
    base = request.url_root.rstrip("/")
    img = qrcode.make(f"{base}/")
    buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
    return send_file(buf, mimetype="image/png", download_name="qr.png")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
