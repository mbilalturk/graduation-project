"""
Demo dashboard uretici (iki dilli: EN + TR). Gercek sonuc CSV'lerinden ve
route_502_features_v4.csv'den veri cekip self-contained (tek dosya, sunucusuz)
dashboard uretir:  demo/index.html (EN)  ve  demo/index_tr.html (TR).

Kullanim:
    python demo/build_demo.py
"""
import os, json
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TBL  = os.path.join(ROOT, "results", "tables")
V4   = os.path.join(ROOT, "collected_data", "route_502_features_v4.csv")
DEMO = os.path.join(ROOT, "demo")


def read_csv(name):
    p = os.path.join(TBL, name)
    return pd.read_csv(p) if os.path.exists(p) else None


# ── 1) Genel ozet ─────────────────────────────────────────────────────────────
ds = read_csv("data_summary.csv")
summary = {
    "segments": int(ds["Toplam segment"][0]),
    "buses":    int(ds["Benzersiz otobus"][0]),
    "days":     int(ds["Benzersiz gun"][0]),
    "mean_travel": float(ds["Ortalama travel_minutes"][0]),
}

# ── 2) Model karsilastirma (adil) — isimler dil-notr (EN) ────────────────────
fc = read_csv("full_comparison_table.csv")
name_map = {
    "XGBoost (Improved)": "XGBoost",
    "LSTM": "LSTM",
    "Random Forest (Improved)": "Random Forest",
    "Historical Avg": "Historical Average",
    "Naive (GTFS)": "Naive (GTFS)",
}
models = []
for _, r in fc.iterrows():
    if r["Model"] in name_map:
        models.append({"name": name_map[r["Model"]],
                       "mae": round(float(r["MAE (dk)"]), 4),
                       "r2": round(float(r["R2"]), 3)})
models.sort(key=lambda m: m["mae"])

# ── 3) Kosul bazli analiz (ham etiketler; JS'te cevrilir) ────────────────────
ca = read_csv("condition_analysis.csv")
def cond_rows(col, kosul):
    out = []
    sub = ca[ca["Kosul Tipi"] == kosul] if "Kosul Tipi" in ca.columns else ca
    for _, r in sub.iterrows():
        label = r.get(col)
        if pd.isna(label):
            continue
        out.append({"label": str(label), "n": int(r["N"]),
                    "mae": round(float(r["XGBoost (Improved) MAE"]), 3)})
    return out
conditions = {
    "direction": cond_rows("Yon_Label", "Yon"),
    "time":      cond_rows("Zaman Dilimi", "Zaman Dilimi"),
    "weather":   cond_rows("Hava Durumu", "Hava Durumu"),
    "zone":      cond_rows("Durak Bolge", "Durak Pozisyonu"),
}

# ── 4) Coklu hat genelleme ────────────────────────────────────────────────────
mr = read_csv("multi_route_comparison.csv")
multiroute = [{"route": str(r["Hat"]).split(" ")[0],
               "segments": int(r["Segment (N)"]),
               "mae": round(float(r["XGBoost MAE (dk)"]), 4),
               "r2": round(float(r["XGBoost R2"]), 3)} for _, r in mr.iterrows()]

# ── 5) Makale kiyasi ──────────────────────────────────────────────────────────
paper = {"ours": round(models[0]["mae"], 3), "paper": 2.97}

# ── 6) Interaktif tahmin: segment bazli tarihsel medyan (yon=0) ───────────────
df = pd.read_csv(V4, usecols=["yon", "from_stop_seq", "to_stop_seq",
                              "from_stop_name", "to_stop_name", "time_block",
                              "travel_time_min", "scheduled_travel_min"])
d0 = df[df["yon"] == 0]
segs = {}
for (fseq, fname, tname), g in d0.groupby(["from_stop_seq", "from_stop_name", "to_stop_name"]):
    per_tb = {}
    for tb in range(4):
        sub = g[g["time_block"] == tb]
        if len(sub) >= 3:
            per_tb[str(tb)] = {"travel": round(float(sub["travel_time_min"].median()), 2),
                               "sched": round(float(sub["scheduled_travel_min"].median()), 2),
                               "n": int(len(sub))}
    if per_tb:
        segs[str(int(fseq))] = {"from": str(fname), "to": str(tname),
                                "all_travel": round(float(g["travel_time_min"].median()), 2),
                                "all_sched": round(float(g["scheduled_travel_min"].median()), 2),
                                "tb": per_tb}
seg_list = [{"seq": int(k), "from": v["from"], "to": v["to"]}
            for k, v in sorted(segs.items(), key=lambda kv: int(kv[0]))]

DATA = {"summary": summary, "models": models, "conditions": conditions,
        "multiroute": multiroute, "paper": paper, "segs": segs, "seg_list": seg_list}

# ── Dile bagli UI metinleri ───────────────────────────────────────────────────
UI = {
 "en": {
  "lang":"en",
  "PAGE_TITLE":"Bus Arrival Time Prediction — Demo",
  "H1":"🚌 Prediction of Bus Arrival Times in Public Transportation",
  "SUB":"Context-aware machine learning for inter-stop travel-time prediction on the İzmir ESHOT network",
  "META":"Muhammed Bilal Türk &nbsp;·&nbsp; Ömer Faruk Koç &nbsp;|&nbsp; Supervisor: Prof. Dr. Didem Gözüpek &nbsp;|&nbsp; Gebze Technical University · 2026",
  "S1H2":"Dataset (Route 502)",
  "S2H2":"Model Comparison","S2TAG":"same test set",
  "S2LEAD":"All models are compared row-aligned on the same test set. Mean Absolute Error (minutes) — lower is better.",
  "S2FIND":"<b>Finding:</b> XGBoost ≈ LSTM &gt; Random Forest. XGBoost and LSTM are statistically <b>equivalent</b> (p=0.38); both significantly outperform Random Forest. <b>XGBoost is the most practical single model</b> — lowest error, no extra complexity.",
  "S3H2":"Live Prediction","S3LEAD":"Pick a stop segment and a time of day; see the model's data-driven estimate and the GTFS scheduled time.",
  "S3SEGLABEL":"Stop segment (Route 502)",
  "TB0":"Morning peak","TB1":"Daytime","TB2":"Evening peak","TB3":"Night","UNIT":"minutes",
  "S4H2":"Condition-Based Analysis","CDIRH":"BY DIRECTION","CTIMEH":"BY TIME OF DAY","CWXH":"BY WEATHER","CZONEH":"BY STOP ZONE",
  "S5H2":"Generalization (3 Routes)","S5LEAD":"The same method, unchanged, works consistently on two additional routes with different traffic profiles.",
  "THROUTE":"Route","THSEG":"Segments","THMAE":"MAE (min)","THR2":"R²",
  "S6H2":"Comparison with the Reference Study","PILLOURS":"Ours (segment):","PILLPAPER":"Reference (Kaya &amp; Kalay, 2025):",
  "S6LEAD":"Much lower MAE; but an <b>honest note:</b> we predict short inter-stop segments (~1.2 min) while the reference predicts full-route arrivals — the scales differ.",
  "S7H2":"Methodological Findings",
  "FIND1":"<b>1. Measurement floor:</b> the ~26-second error is bounded by the 30-second GPS polling interval — better accuracy needs denser data, not a more complex model.",
  "FIND2":"<b>2. Simpler is not worse:</b> fewer features, a simple target, and a classical XGBoost all matched or beat their more complex alternatives.",
  "FIND3":"<b>3. Fair evaluation:</b> a same-test-set comparison corrected an earlier “deep learning is best” impression — it was a test-set artifact.",
  "FOOTER":"İzmir ESHOT · Route 502 (Cengizhan–Halkapınar Metro) · All results are reproducible (seed=42)",
  "STSEG":"segments","STDAYS":"days of data","STBUSES":"buses","STMEAN":"avg. travel","STBESTMAE":"best MAE",
  "CMPSCHED":"GTFS scheduled time","CMPDEV":"deviation","CMPNOTE":"data-driven estimate",
 },
 "tr": {
  "lang":"tr",
  "PAGE_TITLE":"Otobüs Varış Süresi Tahmini — Demo",
  "H1":"🚌 Toplu Taşımada Otobüs Varış Süresi Tahmini",
  "SUB":"Bağlam duyarlı makine öğrenmesi ile İzmir ESHOT ağında duraklar arası seyahat süresi tahmini",
  "META":"Muhammed Bilal Türk &nbsp;·&nbsp; Ömer Faruk Koç &nbsp;|&nbsp; Danışman: Prof. Dr. Didem Gözüpek &nbsp;|&nbsp; Gebze Teknik Üniversitesi · 2026",
  "S1H2":"Veri Kümesi (Hat 502)",
  "S2H2":"Model Karşılaştırması","S2TAG":"aynı test seti",
  "S2LEAD":"Tüm modeller aynı test kümesinde, satır-hizalı karşılaştırıldı. Ortalama Mutlak Hata (dakika) — düşük olan iyi.",
  "S2FIND":"<b>Bulgu:</b> XGBoost ≈ LSTM &gt; Random Forest. XGBoost ile LSTM istatistiksel olarak <b>eşdeğer</b> (p=0.38); ikisi de Random Forest'tan anlamlı şekilde daha iyi. <b>XGBoost en pratik tek model</b> — en düşük hata, ek karmaşıklık gerektirmez.",
  "S3H2":"Canlı Tahmin Denemesi","S3LEAD":"Bir durak segmenti ve zaman dilimi seçin; modelin tarihsel veriye dayalı tahminini ve GTFS tarife süresini görün.",
  "S3SEGLABEL":"Durak segmenti (Hat 502)",
  "TB0":"Sabah zirvesi","TB1":"Gündüz","TB2":"Akşam zirvesi","TB3":"Gece","UNIT":"dakika",
  "S4H2":"Koşul Bazlı Analiz","CDIRH":"YÖNE GÖRE","CTIMEH":"ZAMAN DİLİMİNE GÖRE","CWXH":"HAVA DURUMUNA GÖRE","CZONEH":"DURAK BÖLGESİNE GÖRE",
  "S5H2":"Genelleme (3 Hat)","S5LEAD":"Aynı yöntem, değiştirmeden, farklı trafik profiline sahip iki ek hatta da tutarlı çalışıyor.",
  "THROUTE":"Hat","THSEG":"Segment","THMAE":"MAE (dk)","THR2":"R²",
  "S6H2":"Referans Makale Karşılaştırması","PILLOURS":"Bizim (segment):","PILLPAPER":"Makale (Kaya &amp; Kalay, 2025):",
  "S6LEAD":"MAE'de çok daha düşük; ancak <b>dürüst not:</b> biz kısa duraklar-arası segmentleri (~1.2 dk), makale tüm-rota varışlarını tahmin ediyor — ölçekler farklı.",
  "S7H2":"Metodolojik Bulgular",
  "FIND1":"<b>1. Ölçüm tabanı:</b> ~26 saniyelik hata, 30 saniyelik GPS örnekleme aralığının dayattığı sınıra dayanıyor — daha karmaşık model değil, daha yoğun veri gerekir.",
  "FIND2":"<b>2. Daha sofistike ≠ daha iyi:</b> Feature sayısını azaltmak, basit hedef ve klasik XGBoost; hepsi karmaşık alternatiflerini yakaladı ya da geçti.",
  "FIND3":"<b>3. Adil değerlendirme:</b> Aynı test setinde karşılaştırma, “derin öğrenme en iyi” izlenimini düzeltti — bu bir test-seti artefaktıydı.",
  "FOOTER":"İzmir ESHOT · Hat 502 (Cengizhan–Halkapınar Metro) · Tüm sonuçlar tekrarlanabilir (seed=42)",
  "STSEG":"segment","STDAYS":"gün veri","STBUSES":"otobüs","STMEAN":"ort. seyahat","STBESTMAE":"en iyi MAE",
  "CMPSCHED":"GTFS tarife süresi","CMPDEV":"sapma","CMPNOTE":"tarihsel veriye dayalı tahmin",
 },
}

# Etiket cevirisi (kosul + model isimleri), dile gore
LABELS = {
 "en": {"clear":"Clear","cloudy":"Cloudy","rainy":"Rainy","morning_peak":"Morning peak",
   "off_peak":"Daytime","evening_peak":"Evening peak","night":"Night",
   "Baslangic (0-33%)":"Start (0–33%)","Orta (33-66%)":"Middle (33–66%)","Bitis (66-100%)":"End (66–100%)",
   "Halkapinar->Cengizhan":"Halkapınar → Cengizhan","Cengizhan->Halkapinar":"Cengizhan → Halkapınar"},
 "tr": {"clear":"Açık","cloudy":"Bulutlu","rainy":"Yağışlı","morning_peak":"Sabah zirvesi",
   "off_peak":"Gündüz","evening_peak":"Akşam zirvesi","night":"Gece",
   "Baslangic (0-33%)":"Başlangıç (0–33%)","Orta (33-66%)":"Orta (33–66%)","Bitis (66-100%)":"Bitiş (66–100%)",
   "Halkapinar->Cengizhan":"Halkapınar → Cengizhan","Cengizhan->Halkapinar":"Cengizhan → Halkapınar",
   "Historical Average":"Tarihsel Ortalama","Naive (GTFS)":"Naive (Tarife)"},
}

TEMPLATE = r"""<!DOCTYPE html>
<html lang="__LANG__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__PAGE_TITLE__</title>
<style>
  :root{--bg:#0f172a;--card:#1e293b;--card2:#273449;--txt:#e2e8f0;--mut:#94a3b8;
    --acc:#38bdf8;--acc2:#34d399;--warn:#fbbf24;--line:#334155;}
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Segoe UI',system-ui,Arial,sans-serif;background:var(--bg);color:var(--txt);line-height:1.5;padding-bottom:60px}
  .wrap{max-width:1100px;margin:0 auto;padding:0 22px}
  header{background:linear-gradient(135deg,#0ea5e9,#6366f1);padding:38px 0 30px;box-shadow:0 4px 24px rgba(0,0,0,.4)}
  header h1{font-size:30px;font-weight:800;letter-spacing:.3px}
  header .sub{color:#e0f2fe;margin-top:8px;font-size:15px}
  header .meta{color:#bae6fd;margin-top:14px;font-size:13.5px}
  section{margin-top:34px}
  h2{font-size:21px;margin-bottom:6px;display:flex;align-items:center;gap:9px}
  h2 .dot{width:10px;height:10px;border-radius:50%;background:var(--acc)}
  .lead{color:var(--mut);margin-bottom:16px;font-size:14.5px;max-width:760px}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px}
  .stat{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px}
  .stat .v{font-size:26px;font-weight:800;color:var(--acc)}
  .stat .l{color:var(--mut);font-size:12.5px;margin-top:4px}
  .panel{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:22px;margin-top:14px}
  .bar-row{display:flex;align-items:center;gap:12px;margin:9px 0}
  .bar-row .nm{width:140px;font-size:13.5px;flex-shrink:0}
  .bar-wrap{flex:1;background:var(--card2);border-radius:8px;height:30px;overflow:hidden;position:relative}
  .bar{height:100%;border-radius:8px;display:flex;align-items:center;justify-content:flex-end;padding-right:10px;
    font-size:12.5px;font-weight:700;color:#0f172a;background:linear-gradient(90deg,#38bdf8,#34d399);transition:width .6s}
  .bar.best{background:linear-gradient(90deg,#34d399,#10b981)}
  .bar.weak{background:linear-gradient(90deg,#64748b,#475569);color:#e2e8f0}
  .tag{display:inline-block;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:700;background:rgba(56,189,248,.16);color:#38bdf8}
  table{width:100%;border-collapse:collapse;font-size:13.5px}
  th,td{padding:10px 12px;text-align:left;border-bottom:1px solid var(--line)}
  th{color:var(--mut);font-weight:600;font-size:12.5px}
  td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
  .mini h4{font-size:13px;color:var(--mut);margin-bottom:8px;font-weight:600}
  .mini .row{display:flex;justify-content:space-between;font-size:13px;padding:5px 0;border-bottom:1px solid var(--line)}
  select{width:100%;background:var(--card2);color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:11px;font-size:14px}
  .tb-btns{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
  .tb-btns button{flex:1;min-width:90px;background:var(--card2);color:var(--txt);border:1px solid var(--line);
    border-radius:10px;padding:10px;font-size:13px;cursor:pointer}
  .tb-btns button.on{background:var(--acc);color:#0f172a;border-color:var(--acc);font-weight:700}
  .result{margin-top:18px;text-align:center}
  .result .big{font-size:46px;font-weight:800;color:var(--acc2)}
  .result .unit{font-size:18px;color:var(--mut)}
  .result .cmp{color:var(--mut);font-size:13.5px;margin-top:6px}
  .find{background:var(--card);border-left:4px solid var(--warn);border-radius:0 12px 12px 0;padding:15px 18px;margin-top:12px}
  .find b{color:var(--warn)}
  footer{margin-top:40px;color:var(--mut);font-size:12.5px;text-align:center}
  .pill{display:inline-flex;gap:7px;align-items:center;background:var(--card);border:1px solid var(--line);
    border-radius:30px;padding:7px 15px;font-size:13px;margin:4px 6px 0 0}
</style>
</head>
<body>
<header><div class="wrap">
  <h1>__H1__</h1>
  <div class="sub">__SUB__</div>
  <div class="meta">__META__</div>
</div></header>
<div class="wrap">
  <section><h2><span class="dot"></span>__S1H2__</h2><div class="cards" id="stats"></div></section>

  <section><h2><span class="dot"></span>__S2H2__ <span class="tag">__S2TAG__</span></h2>
    <p class="lead">__S2LEAD__</p>
    <div class="panel"><div id="bars"></div></div>
    <div class="find">__S2FIND__</div></section>

  <section><h2><span class="dot"></span>__S3H2__</h2>
    <p class="lead">__S3LEAD__</p>
    <div class="panel">
      <label style="font-size:13px;color:var(--mut)">__S3SEGLABEL__</label>
      <select id="segsel"></select>
      <div class="tb-btns" id="tbbtns">
        <button data-tb="0">__TB0__</button><button data-tb="1" class="on">__TB1__</button>
        <button data-tb="2">__TB2__</button><button data-tb="3">__TB3__</button></div>
      <div class="result"><div><span class="big" id="pred">–</span> <span class="unit">__UNIT__</span></div>
        <div class="cmp" id="cmp"></div></div></div></section>

  <section><h2><span class="dot"></span>__S4H2__</h2><div class="grid2">
    <div class="panel mini"><h4>__CDIRH__</h4><div id="c_dir"></div></div>
    <div class="panel mini"><h4>__CTIMEH__</h4><div id="c_time"></div></div>
    <div class="panel mini"><h4>__CWXH__</h4><div id="c_wx"></div></div>
    <div class="panel mini"><h4>__CZONEH__</h4><div id="c_zone"></div></div></div></section>

  <section><h2><span class="dot"></span>__S5H2__</h2><p class="lead">__S5LEAD__</p>
    <div class="panel"><table id="mr"><thead><tr><th>__THROUTE__</th><th class="num">__THSEG__</th>
      <th class="num">__THMAE__</th><th class="num">__THR2__</th></tr></thead><tbody></tbody></table></div></section>

  <section><h2><span class="dot"></span>__S6H2__</h2><div class="panel">
    <div class="pill">__PILLOURS__ <b id="ourmae" style="margin-left:5px;color:var(--acc2)"></b> __UNIT__</div>
    <div class="pill">__PILLPAPER__ <b style="margin-left:5px">2.97</b> __UNIT__</div>
    <p class="lead" style="margin-top:14px">__S6LEAD__</p></div></section>

  <section><h2><span class="dot"></span>__S7H2__</h2>
    <div class="find">__FIND1__</div><div class="find">__FIND2__</div><div class="find">__FIND3__</div></section>

  <footer>__FOOTER__</footer>
</div>
<script>
const DEMO = __DATA__;
const LBL = __LABELS__;
const T = __TXT__;
function trl(s){return LBL[s]||s;}
const S=DEMO.summary;
document.getElementById('stats').innerHTML=[
 [S.segments.toLocaleString('__LANG__'),T.STSEG],[S.days,T.STDAYS],[S.buses,T.STBUSES],
 [S.mean_travel.toFixed(2)+' '+T.UNIT,T.STMEAN],[DEMO.models[0].mae.toFixed(3)+' '+T.UNIT,T.STBESTMAE],
].map(s=>`<div class="stat"><div class="v">${s[0]}</div><div class="l">${s[1]}</div></div>`).join('');
const maxMae=Math.max(...DEMO.models.map(m=>m.mae));
document.getElementById('bars').innerHTML=DEMO.models.map((m,i)=>{
 const w=Math.max(8,m.mae/maxMae*100);const cls=i===0?'best':(m.mae>0.6?'weak':'');
 return `<div class="bar-row"><div class="nm">${trl(m.name)}</div><div class="bar-wrap">
   <div class="bar ${cls}" style="width:${w}%">${m.mae.toFixed(3)} ${T.UNIT} &nbsp;·&nbsp; R²=${m.r2}</div></div></div>`;}).join('');
function condHtml(a){return a.map(c=>`<div class="row"><span>${trl(c.label)} <span style="color:var(--mut)">(n=${c.n.toLocaleString('__LANG__')})</span></span><b>${c.mae.toFixed(3)} ${T.UNIT}</b></div>`).join('');}
document.getElementById('c_dir').innerHTML=condHtml(DEMO.conditions.direction);
document.getElementById('c_time').innerHTML=condHtml(DEMO.conditions.time);
document.getElementById('c_wx').innerHTML=condHtml(DEMO.conditions.weather);
document.getElementById('c_zone').innerHTML=condHtml(DEMO.conditions.zone);
document.querySelector('#mr tbody').innerHTML=DEMO.multiroute.map(r=>
 `<tr><td><b>${r.route}</b></td><td class="num">${r.segments.toLocaleString('__LANG__')}</td><td class="num">${r.mae.toFixed(4)}</td><td class="num">${r.r2}</td></tr>`).join('');
document.getElementById('ourmae').textContent=DEMO.paper.ours.toFixed(3);
const sel=document.getElementById('segsel');
sel.innerHTML=DEMO.seg_list.map(s=>`<option value="${s.seq}">${s.from} → ${s.to}</option>`).join('');
let curTb='1';
function predict(){
 const seg=DEMO.segs[sel.value];if(!seg)return;
 const d=(seg.tb&&seg.tb[curTb])?seg.tb[curTb]:{travel:seg.all_travel,sched:seg.all_sched,n:0};
 document.getElementById('pred').textContent=d.travel.toFixed(2);
 const dev=d.travel-d.sched;
 document.getElementById('cmp').innerHTML=
  `${T.CMPSCHED}: <b>${d.sched.toFixed(2)} ${T.UNIT}</b> &nbsp;·&nbsp; ${T.CMPDEV}: <b>${dev>=0?'+':''}${dev.toFixed(2)} ${T.UNIT}</b><br>`+
  `<span style="font-size:12px">${T.CMPNOTE}${d.n?` (n=${d.n})`:''}</span>`;}
sel.addEventListener('change',predict);
document.querySelectorAll('#tbbtns button').forEach(b=>b.addEventListener('click',()=>{
 document.querySelectorAll('#tbbtns button').forEach(x=>x.classList.remove('on'));
 b.classList.add('on');curTb=b.dataset.tb;predict();}));
predict();
</script>
</body></html>
"""

for lang, out_name in [("en", "index.html"), ("tr", "index_tr.html")]:
    html = TEMPLATE
    for key, val in UI[lang].items():
        html = html.replace("__" + key.upper() + "__", str(val))
    html = html.replace("__DATA__", json.dumps(DATA, ensure_ascii=False))
    html = html.replace("__LABELS__", json.dumps(LABELS[lang], ensure_ascii=False))
    html = html.replace("__TXT__", json.dumps(UI[lang], ensure_ascii=False))
    with open(os.path.join(DEMO, out_name), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Olusturuldu: demo/{out_name} ({lang.upper()})")

print(f"  {len(seg_list)} segment, {len(models)} model, {len(multiroute)} hat")
