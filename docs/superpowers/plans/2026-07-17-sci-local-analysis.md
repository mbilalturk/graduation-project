# SCI Yerel Analiz Katmanı Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hocanın istediği makale analizlerinin tamamını bu makinede üretmek: per-segment tahmin kaydı, effect size + gün-bazlı bootstrap CI + gün-düzeyi significance, saatlik/kırılım hata analizleri (yağmur için fold-içi kontrollü), trip-progress figürü, additive ablation (C0–C4, dwell dahil, 3 hat), LSTM ablation (C2–C4), rolling-origin CV ve trip-level aggregation.

> **Revizyon (2026-07-17):** Plan başlangıçta "yerelde yalnız `route_502_features_v2.csv` var, v4/dwell YOK, torch YOK" varsayımıyla (macOS, `/Users/omerkoc/bus_arrival`) yazılmıştı. Bu makinede (Windows, `C:\Users\Bilal\Desktop\Dersler\CSE496-Graduation-Project`) **üç hattın da v4 CSV'leri (dwell kolonlarıyla) ve torch mevcut** — doğrulandı. Bu revizyonla: c4 ablation + 268/565 tekrarları + LSTM ablation + trip-level aggregation + gün-düzeyi significance + yağmur fold-içi kontrolü plana dahil edildi; yollar Windows'a çevrildi.

**Architecture:** `improved_ml.py` tek klasik eğitim scripti kalır; ona `--feature-set`, `--save-preds`, `--train-end-day/--test-days`, `--core-only` eklenir ve historical feature'lar leakage-safe olacak şekilde her koşumda kendi train penceresinden yeniden hesaplanır. Feature-set tanımları paylaşılan `scripts/feature_sets.py` modülünde tutulur (improved_ml, improved_lstm ve driver'lar aynı kaynaktan okur). `improved_lstm.py`'a aynı `--feature-set` (yalnız c2/c3/c4) + `--save-preds` eklenir. Eğitim çıktıları `results/predictions/*.csv` (satır bazlı) + `results/tables/*.csv` (özet) olur; analiz scriptleri (significance, error-slices, trip-progress, trip-level) yalnızca predictions dosyalarını okur. Driver scriptler (ablation, CV) eğitim scriptlerini subprocess ile çağırır.

**Tech Stack:** Python venv (`.venv`, Windows: `./.venv/Scripts/python.exe`, komutlar Git Bash sözdizimiyle), pandas, numpy, scikit-learn, xgboost, scipy, matplotlib, pytest, torch (LSTM ablation bu plana DAHİL — torch bu makinede kurulu, doğrulandı).

## Global Constraints

- Veri: `collected_data/route_{502,268,565}_features_v4.csv` (dwell kolonları `dwell_time_sec`/`prev_dwell_time_sec` dahil; 502: 81.575 satır, 73 gün, 2026-04-02→06-13). `improved_ml.py` v4'ü otomatik yükler. Bir feature-set için kolon gerçekten eksik/NaN ise script **açık hata ile durmalı** (sessizce eksik feature'la koşmak yasak).
- Ana sonuçlar 502'de; ablation 268 ve 565'te tekrarlanır ("framework hat-bağımsız" genelleme kanıtı).
- Tüm rasgelelik seed=42; mevcut kronolojik %80/20 headline split davranışı değişmemeli (CV argümanları verilmediğinde birebir aynı sonuç).
- CSV veri dosyaları commit edilmez (`/collected_data/` gitignore'da); `results/` çıktıları commit edilir.
- Figür üreten task'lardan önce **dataviz skill'i yükle**; figür etiketleri İngilizce (SCI makalesi için).
- Bootstrap: satır bazlı değil **gün-bazlı blok** (B=1000, seed=42, %95 CI). Significance testleri hem segment- hem **gün-düzeyi** raporlanır — istatistik metodolojisi baştan sona tek ilkeye oturur: **gün = bağımsızlık birimi** (aynı günün segmentleri korele).
- Izgara ilkesi (RQ'nun merkez deneyi): ablation tablosu **model × feature-set ızgarası** olarak raporlanır (satır=model XGB/RF/LSTM, sütun=C0–C4). LSTM×C0 ve LSTM×C1 hücreleri mimari gereği koşulamaz (sequence girdisi doğası gereği lag içerir) — ızgarada "N/A" bırakılır, makalede tek cümleyle açıklanır.

---

### Task 1: Ortam kurulumu

**Files:**
- Modify: `requirements.txt`

**Interfaces:**
- Produces: `./.venv/Scripts/python.exe` ile pandas/sklearn/xgboost/scipy/matplotlib/pytest import edilebilir.

- [ ] **Step 1: mevcut venv'i doğrula, eksik paketi kur**

Bu makinede `.venv` zaten var; pandas/numpy/sklearn/xgboost/scipy/matplotlib/torch kurulu (doğrulandı), eksik olan yalnız pytest:

```bash
cd "C:/Users/Bilal/Desktop/Dersler/CSE496-Graduation-Project"
./.venv/Scripts/python.exe -m pip install pytest
```

Expected: hatasız kurulum.

- [ ] **Step 2: importları doğrula**

```bash
./.venv/Scripts/python.exe -c "import pandas, numpy, sklearn, xgboost, scipy, matplotlib, pytest, torch; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: requirements.txt'i güncelle**

Dosyanın tamamı şöyle olacak:

```
python-dotenv>=1.0.0

# Analiz + model katmani (scripts/ ve tests/)
numpy>=1.26
pandas>=2.1
scikit-learn>=1.4
xgboost>=2.0
scipy>=1.11
matplotlib>=3.8
pytest>=8.0
torch>=2.2
```

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore: analiz katmani bagimliliklarini requirements'a ekle"
```

---

### Task 2: İstatistik yardımcıları (TDD)

**Files:**
- Create: `scripts/stats_utils.py`
- Test: `tests/test_stats_utils.py`

**Interfaces:**
- Produces:
  - `cohens_d_paired(a, b) -> float` — eşleştirilmiş Cohen's d, d = mean(a−b)/std(a−b, ddof=1)
  - `cliffs_delta(a, b) -> float` — P(a>b) − P(a<b), sıralama tabanlı O(n log n)
  - `day_block_bootstrap_ci(df, value_fn, date_col="date", n_boot=1000, alpha=0.05, seed=42) -> (lo, hi)` — gün-bazlı blok bootstrap yüzdelik CI; `value_fn(sub_df) -> float`

- [ ] **Step 1: Failing testleri yaz**

`tests/test_stats_utils.py`:

```python
import numpy as np
import pandas as pd
import pytest

from scripts.stats_utils import cohens_d_paired, cliffs_delta, day_block_bootstrap_ci


def test_cohens_d_paired_known_value():
    a = np.array([2.0, 3.0, 4.0, 5.0])
    b = np.array([1.0, 3.0, 3.0, 5.0])
    # d = a-b = [1,0,1,0]; mean=0.5, std(ddof=1)=0.5774 -> d ~= 0.866
    assert cohens_d_paired(a, b) == pytest.approx(0.866, abs=0.001)


def test_cohens_d_paired_zero_when_identical():
    a = np.array([1.0, 2.0, 3.0])
    assert cohens_d_paired(a, a) == 0.0


def test_cliffs_delta_extremes_and_zero():
    a = np.array([10.0, 11.0, 12.0])
    b = np.array([1.0, 2.0, 3.0])
    assert cliffs_delta(a, b) == 1.0      # a hep buyuk
    assert cliffs_delta(b, a) == -1.0     # a hep kucuk
    assert cliffs_delta(a, a) == 0.0      # ozdes


def test_cliffs_delta_mixed():
    a = np.array([1.0, 3.0])
    b = np.array([2.0, 2.0])
    # ciftler: (1,2)x2 a<b, (3,2)x2 a>b -> delta = (2-2)/4 = 0
    assert cliffs_delta(a, b) == 0.0


def test_day_block_bootstrap_ci_constant_metric():
    df = pd.DataFrame({
        "date": ["d1"] * 3 + ["d2"] * 3 + ["d3"] * 3,
        "err":  [1.0] * 9,
    })
    lo, hi = day_block_bootstrap_ci(df, lambda s: s["err"].mean(), n_boot=200)
    assert lo == pytest.approx(1.0)
    assert hi == pytest.approx(1.0)


def test_day_block_bootstrap_ci_contains_point_estimate():
    rng = np.random.default_rng(0)
    df = pd.DataFrame({
        "date": np.repeat([f"d{i}" for i in range(20)], 50),
        "err":  rng.normal(2.0, 0.5, 1000),
    })
    point = df["err"].mean()
    lo, hi = day_block_bootstrap_ci(df, lambda s: s["err"].mean(), n_boot=300)
    assert lo < point < hi
    assert (hi - lo) < 1.0  # makul genislik
```

- [ ] **Step 2: Testlerin FAIL ettiğini gör**

```bash
cd "C:/Users/Bilal/Desktop/Dersler/CSE496-Graduation-Project" && ./.venv/Scripts/python.exe -m pytest tests/test_stats_utils.py -v
```

Expected: `ModuleNotFoundError: No module named 'scripts.stats_utils'` (collection error). Not: `tests/` ve `scripts/` klasörlerinde `__init__.py` yoksa pytest rootdir'den import için `tests/__init__.py` GEREKMEZ ama `scripts/` paket importu için boş `scripts/__init__.py` oluştur.

- [ ] **Step 3: Implementasyonu yaz**

Boş `scripts/__init__.py` oluştur. `scripts/stats_utils.py`:

```python
"""
Makale istatistikleri icin yardimcilar:
  - cohens_d_paired : eslestirilmis Cohen's d (per-segment |hata| farklari uzerinde)
  - cliffs_delta    : Cliff's delta (siralama tabanli, O(n log n))
  - day_block_bootstrap_ci : gun-bazli blok bootstrap CI
    (ayni gunun segmentleri korele oldugu icin satir-bazli bootstrap KULLANILMAZ)
"""
import numpy as np
import pandas as pd


def cohens_d_paired(a, b):
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    sd = d.std(ddof=1)
    if sd == 0:
        return 0.0
    return float(d.mean() / sd)


def cliffs_delta(a, b):
    a = np.asarray(a, dtype=float)
    b_sorted = np.sort(np.asarray(b, dtype=float))
    n1, n2 = len(a), len(b_sorted)
    lt = np.searchsorted(b_sorted, a, side="left")           # b < a_i sayisi -> a>b ciftleri
    gt = n2 - np.searchsorted(b_sorted, a, side="right")     # b > a_i sayisi -> a<b ciftleri
    return float((lt.sum() - gt.sum()) / (n1 * n2))


def day_block_bootstrap_ci(df, value_fn, date_col="date",
                           n_boot=1000, alpha=0.05, seed=42):
    rng = np.random.default_rng(seed)
    groups = {d: g for d, g in df.groupby(date_col)}
    days = np.array(list(groups.keys()))
    stats = np.empty(n_boot)
    for i in range(n_boot):
        sample_days = rng.choice(days, size=len(days), replace=True)
        sub = pd.concat([groups[d] for d in sample_days], ignore_index=True)
        stats[i] = value_fn(sub)
    lo, hi = np.quantile(stats, [alpha / 2, 1 - alpha / 2])
    return float(lo), float(hi)
```

- [ ] **Step 4: Testlerin PASS ettiğini gör**

```bash
./.venv/Scripts/python.exe -m pytest tests/test_stats_utils.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/__init__.py scripts/stats_utils.py tests/test_stats_utils.py
git commit -m "feat: effect size + gun-bazli blok bootstrap istatistik yardimcilari (TDD)"
```

---

### Task 3: Veri doğrulama (v3 türetme GEREKMİYOR — v4 mevcut)

> **Revizyon notu:** Orijinal plan burada `derive_v3_from_v2.py` yazdırıyordu çünkü hedef makinede yalnız v2 vardı. Bu makinede üç hattın da v3 VE v4 CSV'leri zaten mevcut ve `improved_ml.py` v4'ü otomatik yükler. Script yazılmayacak; task doğrulamaya indirgendi.

**Interfaces:**
- Produces: v4 CSV'lerin (dwell kolonları dahil) üç hat için de eksiksiz olduğunun teyidi.

- [ ] **Step 1: v4 dosyalarını doğrula**

```bash
cd "C:/Users/Bilal/Desktop/Dersler/CSE496-Graduation-Project"
./.venv/Scripts/python.exe -c "
import pandas as pd
for r in [502, 268, 565]:
    df = pd.read_csv(f'collected_data/route_{r}_features_v4.csv')
    need = ['cumul_deviation','rolling_3_deviation','stop_hist_median','stop_hist_ratio',
            'prev_speed_mpm','dwell_time_sec','prev_dwell_time_sec']
    missing = [c for c in need if c not in df.columns or df[c].isna().any()]
    assert not missing, (r, missing)
    print(r, 'OK:', len(df), 'satir')
"
```

Expected: `502 OK: 81575 satir` + 268/565 satır sayıları, hatasız. (NaN'lı kolon çıkarsa durup rapor et — sessizce devam yok.)

---

### Task 4: improved_ml.py — leakage-safe historical + split maskeleri + save-preds + feature-set + CV argümanları

Bu task improved_ml.py'daki tüm değişiklikleri tek seferde yapar (hepsi aynı bölgelere dokunuyor; ayrı task'lar çakışırdı). Headline davranış korunur: argümansız `--route 502` koşumu eski sonuçları (MAE ~0.43-0.44 bandı, dwell'siz v3 verisiyle) vermeli.

**Files:**
- Modify: `scripts/improved_ml.py`
- Create: `scripts/feature_sets.py` (paylaşılan feature-set tanımları — improved_ml, improved_lstm ve driver'lar aynı kaynaktan okur; N_FEATS gibi türevler elle sabitlenmez)

**Interfaces:**
- Produces (CLI):
  - `--feature-set {c0,c1,c2,c3,c4,full}` (default full). c0–c4 için eksik feature → `SystemExit` hata.
  - `--save-preds` → `results/predictions/route_<RID>_test_predictions<suffix>.csv`; kolonlar: `date, arrival_timestamp, hour, day_of_week, day_type, yon, from_stop_seq, to_stop_seq, segments_into_trip, is_trip_start, stop_progress, distance_m, scheduled_travel_min, weather_cat_enc, precipitation, y_true, pred_naive, pred_histavg, [pred_rf_base], pred_rf_improved, [pred_xgb_improved], [pred_rf_moe]`
  - `--train-end-day N --test-days M` → kronolojik gün-bazlı split (ilk N gün train, sonraki M gün test); verilmezse mevcut %80/20.
  - `--core-only` → RF Baseline ve MoE bölümlerini atlar (ablation/CV hızı için).
  - suffix'e ekler: `_fs-<set>` (full değilse), `_cv<N>` (CV ise).
- Consumes: v4 CSV (Task 3'te doğrulanır; `improved_ml.py` v4'ü otomatik yükler).

- [ ] **Step 1: Argümanları ekle**

`_ap.add_argument("--no-tripstart-feat", ...)` bloğundan sonra ekle:

```python
_ap.add_argument("--feature-set", choices=["c0", "c1", "c2", "c3", "c4", "full"],
                 default="full", help="Additive ablation konfigurasyonu (default: full)")
_ap.add_argument("--save-preds", action="store_true",
                 help="Test seti per-segment tahminlerini results/predictions/ altina yaz")
_ap.add_argument("--train-end-day", type=int, default=None,
                 help="CV: train = ilk N gun (kronolojik). Verilmezse %%80/20 satir spliti")
```

DİKKAT: help metninde `%%80/20` (çift yüzde) şart — argparse help string'lere %-format uygular; tek `%` `--help` çağrısında `ValueError: unsupported format character` fırlatır.

```python
_ap.add_argument("--test-days", type=int, default=9,
                 help="CV: test = train sonrasi M gun (default 9)")
_ap.add_argument("--core-only", action="store_true",
                 help="Sadece RF Improved + XGBoost (baseline RF ve MoE atlanir)")
```

ve `TRIPSTART_FEAT = _args.tripstart_feat` satırından sonra:

```python
FEATURE_SET = _args.feature_set
```

- [ ] **Step 2: Feature-set tanımlarını paylaşılan modüle koy ve seçim mantığını değiştir**

Yeni dosya `scripts/feature_sets.py` (tek doğruluk kaynağı — improved_ml, improved_lstm ve run_ablation buradan import eder):

```python
"""
Additive ablation feature setleri (SCI: hoca madde 1).
  c0: baglamsiz taban (temporal + spatial)
  c1: + GTFS tarife       (scheduled_travel_min)
  c2: + sapma/lag baglami (prev/cumul/rolling deviation + is_trip_start)
  c3: + tarihsel          (stop_hist_median/ratio, prev_speed_mpm)
  c4: + dwell             (dwell_time_sec, prev_dwell_time_sec — v4 verisi)
LSTM icin c0/c1 kosulamaz: sequence girdisi dogasi geregi lag icerir
(izgarada N/A birakilir, makalede aciklanir).
"""
FEATURE_SETS = {}
FEATURE_SETS["c0"] = ["hour", "day_of_week",
                      "from_stop_seq", "to_stop_seq", "distance_m", "stop_progress"]
FEATURE_SETS["c1"] = FEATURE_SETS["c0"] + ["scheduled_travel_min"]
FEATURE_SETS["c2"] = FEATURE_SETS["c1"] + ["prev_travel_time_min", "prev_deviation",
                                           "cumul_deviation", "rolling_3_deviation",
                                           "is_trip_start"]
FEATURE_SETS["c3"] = FEATURE_SETS["c2"] + ["stop_hist_median", "stop_hist_ratio",
                                           "prev_speed_mpm"]
FEATURE_SETS["c4"] = FEATURE_SETS["c3"] + ["dwell_time_sec", "prev_dwell_time_sec"]

LSTM_ALLOWED = ("c2", "c3", "c4", "full")
```

`improved_ml.py`'da `LEAN_FEATURES = [...]` bloğundan hemen sonra ekle:

```python
from scripts.feature_sets import FEATURE_SETS
```

Mevcut seçim bloğunu —

```python
available_features = [
    f for f in LEAN_FEATURES
    if f in df.columns and df[f].notna().all()
]
missing = [f for f in LEAN_FEATURES if f not in available_features]
print(f"\nToplam ozellik (lean): {len(available_features)}/{len(LEAN_FEATURES)}")
if missing:
    print(f"  Eksik/NaN feature (atlandi): {missing}")
if TRIPSTART_FEAT and "is_trip_start" in df.columns and df["is_trip_start"].notna().all():
    available_features = available_features + ["is_trip_start"]
    print(f"  + is_trip_start eklendi -> {len(available_features)} feature")
```

— şununla değiştir:

```python
if FEATURE_SET == "full":
    available_features = [
        f for f in LEAN_FEATURES
        if f in df.columns and df[f].notna().all()
    ]
    missing = [f for f in LEAN_FEATURES if f not in available_features]
    print(f"\nToplam ozellik (lean): {len(available_features)}/{len(LEAN_FEATURES)}")
    if missing:
        print(f"  Eksik/NaN feature (atlandi): {missing}")
    if TRIPSTART_FEAT and "is_trip_start" in df.columns and df["is_trip_start"].notna().all():
        available_features = available_features + ["is_trip_start"]
        print(f"  + is_trip_start eklendi -> {len(available_features)} feature")
else:
    wanted = FEATURE_SETS[FEATURE_SET]
    hard_missing = [f for f in wanted if f not in df.columns or not df[f].notna().all()]
    if hard_missing:
        raise SystemExit(
            f"HATA: feature-set '{FEATURE_SET}' icin eksik/NaN feature'lar: {hard_missing}\n"
            f"(Veri dosyasinda bu kolonlar yok ya da NaN iceriyor — dogru versiyonun "
            f"(route_{ROUTE_ID}_features_v4.csv) yuklendigini kontrol et. "
            f"Sessizce eksik feature'la kosulmaz.)")
    available_features = list(wanted)
    print(f"\nFeature set [{FEATURE_SET}]: {len(available_features)} feature")
    print(f"  {available_features}")
```

- [ ] **Step 3: Split'i maske tabanlı yap + historical feature'ları train'den yeniden hesapla**

Mevcut bloğu —

```python
X = df[available_features].values
y = df[TARGET].values
sched = df["scheduled_travel_min"].values   # deviation modu icin baz cizgi

# ── Train / Test bolme ────────────────────────────────────────────────────────
split_idx  = int(len(df) * 0.8)
X_train    = X[:split_idx];       X_test    = X[split_idx:]
y_train    = y[:split_idx];       y_test    = y[split_idx:]
sched_train, sched_test = sched[:split_idx], sched[split_idx:]
```

— şununla değiştir:

```python
# ── Train / Test bolme (once maskeler: historical yeniden-hesap train'e bagli) ─
if _args.train_end_day is not None:
    dates_sorted = np.sort(df["date"].unique())
    n_tr, n_te = _args.train_end_day, _args.test_days
    if n_tr + n_te > len(dates_sorted):
        raise SystemExit(f"HATA: {n_tr}+{n_te} gun > mevcut {len(dates_sorted)} gun")
    tr_dates = set(dates_sorted[:n_tr])
    te_dates = set(dates_sorted[n_tr:n_tr + n_te])
    train_mask = df["date"].isin(tr_dates).values
    test_mask  = df["date"].isin(te_dates).values
    print(f"CV split: train={n_tr} gun ({int(train_mask.sum())} satir)  "
          f"test={n_te} gun ({int(test_mask.sum())} satir)")
else:
    split_idx  = int(len(df) * 0.8)
    train_mask = np.zeros(len(df), dtype=bool); train_mask[:split_idx] = True
    test_mask  = ~train_mask

# ── Historical feature'lari HER KOSUMDA kendi train penceresinden yeniden hesapla
#    (v3 CSV'deki degerler %80 splitten; CV fold'larinda leakage olurdu)
if "stop_hist_median" in df.columns:
    tr = df[train_mask]
    med = (tr.groupby(["from_stop_seq", "yon"])["travel_time_min"].median()
             .rename("stop_hist_median").reset_index())
    gmed = tr["travel_time_min"].median()
    df = df.drop(columns=["stop_hist_median"]).merge(
        med, on=["from_stop_seq", "yon"], how="left")
    df["stop_hist_median"] = df["stop_hist_median"].fillna(gmed)

    tr = df[train_mask]
    tr_ratio = (tr["travel_time_min"] / tr["scheduled_travel_min"].clip(lower=0.01)
                ).rename("stop_hist_ratio")
    rmed = (tr_ratio.groupby([tr["from_stop_seq"], tr["yon"]]).median()
                    .rename("stop_hist_ratio").reset_index())
    df = df.drop(columns=["stop_hist_ratio"]).merge(
        rmed, on=["from_stop_seq", "yon"], how="left")
    df["stop_hist_ratio"] = df["stop_hist_ratio"].fillna(1.0)

X = df[available_features].values
y = df[TARGET].values
sched = df["scheduled_travel_min"].values   # deviation modu icin baz cizgi

X_train    = X[train_mask];       X_test    = X[test_mask]
y_train    = y[train_mask];       y_test    = y[test_mask]
sched_train, sched_test = sched[train_mask], sched[test_mask]
```

ÖNEMLİ: `df.drop(...).merge(...)` satır SIRASINI korur (how="left", tekil anahtar) — maskeler geçerli kalır. Merge sonrası `df` yeniden atandığı için bu blok `X = df[...]` satırlarından ÖNCE olmalı (yukarıdaki sıra zaten öyle).

- [ ] **Step 4: split_idx bağımlılıklarını maskeye çevir**

Üç yer değişecek:

(a) XGBoost cold-start kırılımı —

```python
    sp_test = df["stop_progress"].values[split_idx:]
```

→

```python
    sp_test = df["stop_progress"].values[test_mask]
```

(b) MoE bölümü —

```python
test_df  = df.iloc[split_idx:].reset_index(drop=True)
train_df = df.iloc[:split_idx].reset_index(drop=True)
```

→

```python
test_df  = df[test_mask].reset_index(drop=True)
train_df = df[train_mask].reset_index(drop=True)
```

(c) `--core-only` atlama: `print("1. BASELINE: ...")` bloğunun tamamını (rf_base fit/evaluate/append) şu koşula al:

```python
if not _args.core_only:
    ...mevcut rf_base blogu...
```

ve MoE bölümünü (bölüm 4 başlığından `results.append(r_seg)` dahil sonuna kadar) aynı şekilde `if not _args.core_only:` altına al. `--core-only` verildiğinde 502 referans satır ekleme bloğu (`if ROUTE_ID == 502: results.extend(...)`) de atlansın:

```python
if ROUTE_ID == 502 and not _args.core_only:
```

Ayrıca sondaki "RF Improved iyilesmesi vs RF Baseline" print bloğunu da `if not _args.core_only:` altına al (referans karşılaştırması sadece tam koşumda anlamlı).

- [ ] **Step 5: suffix + baseline tahminler + save-preds bloğu**

Mevcut suffix satırını —

```python
suffix = ("" if ROUTE_ID == 502 else f"_route_{ROUTE_ID}") + mode_suffix + cs_suffix
```

→

```python
fs_suffix = "" if FEATURE_SET == "full" else f"_fs-{FEATURE_SET}"
cv_suffix = "" if _args.train_end_day is None else f"_cv{_args.train_end_day}"
suffix = ("" if ROUTE_ID == 502 else f"_route_{ROUTE_ID}") + mode_suffix + cs_suffix + fs_suffix + cv_suffix
```

Dosyanın sonuna (mevcut `print(f"\nSonuclar kaydedildi: {out_path}")` satırından sonra) ekle:

```python
# ── Per-segment tahmin kaydi (SCI: effect size / CI / kirilim analizleri) ─────
if _args.save_preds:
    META = ["date", "bus_id", "trip_start_time", "arrival_timestamp",
            "hour", "day_of_week", "day_type", "yon",
            "from_stop_seq", "to_stop_seq", "segments_into_trip", "is_trip_start",
            "stop_progress", "distance_m", "scheduled_travel_min",
            "weather_cat_enc", "precipitation"]
    # bus_id + trip_start_time: trip-level aggregation (Task 11) icin trip anahtari
    # trip anahtari = (date, bus_id, yon, trip_start_time)
    pred_df = df.loc[test_mask, [c for c in META if c in df.columns]].copy()
    pred_df["y_true"] = y_test

    # Naive (GTFS) baseline: tahmin = tarife
    pred_df["pred_naive"] = sched_test

    # Historical Average baseline: train'den saat x gun_tipi x durak ortalamasi
    tr = df[train_mask]
    ha = (tr.groupby(["hour", "day_type", "from_stop_seq"])["travel_time_min"]
            .mean().rename("pred_histavg").reset_index())
    pred_df = pred_df.merge(ha, on=["hour", "day_type", "from_stop_seq"], how="left")
    pred_df["pred_histavg"] = pred_df["pred_histavg"].fillna(tr["travel_time_min"].mean())

    if not _args.core_only:
        pred_df["pred_rf_base"] = y_pred_base
    pred_df["pred_rf_improved"] = y_pred_rf
    if HAS_XGB:
        pred_df["pred_xgb_improved"] = y_pred_xgb
    if not _args.core_only:
        pred_df["pred_rf_moe"] = y_pred_seg

    pred_dir = os.path.join(RESULTS_DIR, "predictions")
    os.makedirs(pred_dir, exist_ok=True)
    pred_path = os.path.join(pred_dir, f"route_{ROUTE_ID}_test_predictions{suffix}.csv")
    pred_df.to_csv(pred_path, index=False)
    print(f"Tahminler kaydedildi: {pred_path}  ({len(pred_df)} satir)")
```

DİKKAT: merge satır sırasını koruyor (left, tekil anahtar) ama emin olmak için merge YERİNE map kullan:

```python
    ha = tr.groupby(["hour", "day_type", "from_stop_seq"])["travel_time_min"].mean()
    keys = list(zip(pred_df["hour"], pred_df["day_type"], pred_df["from_stop_seq"]))
    pred_df["pred_histavg"] = pd.Series(keys, index=pred_df.index).map(ha)
    pred_df["pred_histavg"] = pred_df["pred_histavg"].fillna(tr["travel_time_min"].mean())
```

(yukarıdaki merge'li üç satır yerine bu map'li dört satırı kullan).

- [ ] **Step 6: Headline regresyon kontrolü — tam koşum**

```bash
cd "C:/Users/Bilal/Desktop/Dersler/CSE496-Graduation-Project"
PYTHONPATH=. ./.venv/Scripts/python.exe scripts/improved_ml.py --route 502 --save-preds
```

Expected: hatasız biter; "Veri: v4" satırı görünür (improved_ml v4'ü otomatik yükler, dwell dahil); XGBoost Improved MAE **≈0.4327** (raporda yayımlanan değer — headline davranış birebir korunmalı); `results/predictions/route_502_test_predictions.csv` oluşur, 16.315 satır. Kontrol:

```bash
./.venv/Scripts/python.exe -c "
import pandas as pd
p = pd.read_csv('results/predictions/route_502_test_predictions.csv')
assert len(p) == 16315, len(p)
for c in ['y_true','pred_naive','pred_histavg','pred_rf_base','pred_rf_improved','pred_xgb_improved','pred_rf_moe']:
    assert c in p.columns, c
print('preds OK', p.shape)
print((p.y_true - p.pred_xgb_improved).abs().mean())
"
```

- [ ] **Step 7: c4'ün v4 verisiyle koştuğunu doğrula**

> **Revizyon notu:** Orijinal planda bu adım "c4 açık hata vermeli" idi (v4 yoktu). Bu makinede v4 mevcut — c4 artık koşmalı. Açık-hata guard'ı kodda KALIR: kolon gerçekten eksik/NaN olan bir veri setinde SystemExit vermeye devam eder.

```bash
PYTHONPATH=. ./.venv/Scripts/python.exe scripts/improved_ml.py --route 502 --feature-set c4 --core-only 2>&1 | tail -8
```

Expected: hatasız biter; feature listesinde `dwell_time_sec` ve `prev_dwell_time_sec` görünür (17 feature); MAE full koşumla aynı bantta.

- [ ] **Step 8: Commit**

```bash
git add scripts/improved_ml.py
git commit -m "feat: improved_ml'e feature-set/save-preds/CV-split/core-only + leakage-safe historical"
```

---

### Task 5: Additive ablation driver + koşum (C0–C4, 3 hat)

> **Revizyon notu:** Kapsam C0–C3/502'den **C0–C4 × {502, 268, 565}**'e genişletildi — v4 (dwell) verisi üç hat için de yerelde mevcut. c4 adımı makalenin "dwell en bilgilendirici girdiler arasında" iddiasının (Contribution §1.4) doğrudan kanıtı; 268/565 tekrarı "framework hat-bağımsız" genelleme kanıtı.

**Files:**
- Create: `scripts/run_ablation.py`

**Interfaces:**
- Consumes: `improved_ml.py --feature-set cK --core-only --save-preds` (Task 4); `scripts/feature_sets.py` (N_FEATS türetimi)
- Produces: `results/tables/ablation_additive_route_<RID>.csv` (RID ∈ {502, 268, 565}) — kolonlar: `config, n_features, features_added, model, MAE (dk), RMSE (dk), MAPE (%), R2` (model ∈ {XGBoost Improved, RF Improved}); ayrıca her config için `results/predictions/route_<RID>_test_predictions_fs-cK.csv`

- [ ] **Step 1: Driver'ı yaz**

`scripts/run_ablation.py`:

```python
"""
Additive ablation: C0 -> C4 (dwell dahil; v4 verisi yerelde mevcut).
Her konfig improved_ml.py'i subprocess ile calistirir, ozet tabloyu birlestirir.

Kullanim: PYTHONPATH=. python scripts/run_ablation.py --route 502
          (varsayilan configs: c0 c1 c2 c3 c4; 268/565 icin --route ile tekrar)
"""
import os
import sys
import argparse
import subprocess
import pandas as pd

from scripts.feature_sets import FEATURE_SETS

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

ADDED = {
    "c0": "taban: temporal+spatial",
    "c1": "+ scheduled_travel_min (GTFS)",
    "c2": "+ deviation/lag (prev, cumul, rolling, is_trip_start)",
    "c3": "+ historical (stop_hist_median/ratio, prev_speed_mpm)",
    "c4": "+ dwell (dwell_time_sec, prev_dwell_time_sec)",
}
N_FEATS = {k: len(v) for k, v in FEATURE_SETS.items()}   # tek kaynaktan turetilir

ap = argparse.ArgumentParser()
ap.add_argument("--route", type=int, default=502)
ap.add_argument("--configs", nargs="+", default=["c0", "c1", "c2", "c3", "c4"])
args = ap.parse_args()

rows = []
for cfg in args.configs:
    print(f"\n{'='*60}\nABLATION {cfg}: {ADDED[cfg]}\n{'='*60}")
    cmd = [sys.executable, os.path.join(SCRIPT_DIR, "improved_ml.py"),
           "--route", str(args.route), "--feature-set", cfg,
           "--core-only", "--save-preds"]
    env = dict(os.environ, PYTHONPATH=PROJECT_ROOT)
    subprocess.run(cmd, check=True, env=env, cwd=PROJECT_ROOT)

    route_sfx = "" if args.route == 502 else f"_route_{args.route}"
    res = pd.read_csv(os.path.join(
        PROJECT_ROOT, "results", "tables",
        f"improved_ml_results{route_sfx}_fs-{cfg}.csv"))
    for _, r in res.iterrows():
        rows.append({"config": cfg, "n_features": N_FEATS[cfg],
                     "features_added": ADDED[cfg], **r.to_dict()})

out = pd.DataFrame(rows)
out_path = os.path.join(PROJECT_ROOT, "results", "tables",
                        f"ablation_additive_route_{args.route}.csv")
out.to_csv(out_path, index=False)
print(f"\nAblation tablosu: {out_path}")
print(out.to_string(index=False))
```

- [ ] **Step 2: Koş (c0–c4, hat 502) ve sonucu incele**

```bash
cd "C:/Users/Bilal/Desktop/Dersler/CSE496-Graduation-Project"
PYTHONPATH=. ./.venv/Scripts/python.exe scripts/run_ablation.py --route 502
```

Expected: 5 konfig sırayla koşar (~15-25 dk); `ablation_additive_route_502.csv` 10 satır (5 config × 2 model). Beklenen desen: c0 MAE en yüksek; c1'de belirgin düşüş (GTFS katkısı); c2'de tekrar düşüş (deviation katkısı); c3 küçük iyileşme; c4'te küçük ama ölçülebilir iyileşme (dwell katkısı — makale iddiasının kanıtı). Her config için `results/predictions/route_502_test_predictions_fs-cK.csv` oluşmuş olmalı.

- [ ] **Step 3: 268 ve 565'te tekrarla (genelleme kanıtı)**

```bash
PYTHONPATH=. ./.venv/Scripts/python.exe scripts/run_ablation.py --route 268
PYTHONPATH=. ./.venv/Scripts/python.exe scripts/run_ablation.py --route 565
```

Expected: `ablation_additive_route_268.csv` ve `ablation_additive_route_565.csv` (10'ar satır); C0→C4 iyileşme deseni üç hatta da aynı yönde (mutlak MAE'ler farklı olabilir — 268: ~0.37, 565: ~0.30 bandı).

- [ ] **Step 4: Commit**

```bash
git add scripts/run_ablation.py results/tables/ablation_additive_route_*.csv results/tables/improved_ml_results*_fs-*.csv
git commit -m "feat: additive ablation C0-C4 x 3 hat (GTFS/deviation/historical/dwell katki kaniti)"
```

---

### Task 6: Rolling-origin CV driver + koşum

**Files:**
- Create: `scripts/run_cv.py`

**Interfaces:**
- Consumes: `improved_ml.py --train-end-day N --test-days 9 --core-only --save-preds` (Task 4)
- Produces: `results/tables/cv_rolling_origin_route_502.csv` — kolonlar: `fold, train_days, test_days, model, MAE (dk), RMSE (dk), MAPE (%), R2` + son iki satırda `mean`/`std` özetleri (model bazında); fold predictions: `results/predictions/route_502_test_predictions_cv<N>.csv`

- [ ] **Step 1: Driver'ı yaz**

`scripts/run_cv.py`:

```python
"""
Rolling-origin (genisleyen pencere) 5-fold CV — 73 gunluk 502 verisi:
  fold1: train gun 1-28, test 29-37     fold4: train 1-55, test 56-64
  fold2: train 1-37, test 38-46         fold5: train 1-64, test 65-73
  fold3: train 1-46, test 47-55

Kullanim: PYTHONPATH=. python scripts/run_cv.py --route 502
"""
import os
import sys
import argparse
import subprocess
import pandas as pd

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

FOLDS = [(28, 9), (37, 9), (46, 9), (55, 9), (64, 9)]

ap = argparse.ArgumentParser()
ap.add_argument("--route", type=int, default=502)
args = ap.parse_args()

rows = []
for k, (n_tr, n_te) in enumerate(FOLDS, start=1):
    print(f"\n{'='*60}\nCV FOLD {k}: train ilk {n_tr} gun, test sonraki {n_te} gun\n{'='*60}")
    cmd = [sys.executable, os.path.join(SCRIPT_DIR, "improved_ml.py"),
           "--route", str(args.route),
           "--train-end-day", str(n_tr), "--test-days", str(n_te),
           "--core-only", "--save-preds"]
    env = dict(os.environ, PYTHONPATH=PROJECT_ROOT)
    subprocess.run(cmd, check=True, env=env, cwd=PROJECT_ROOT)

    route_sfx = "" if args.route == 502 else f"_route_{args.route}"
    res = pd.read_csv(os.path.join(
        PROJECT_ROOT, "results", "tables",
        f"improved_ml_results{route_sfx}_cv{n_tr}.csv"))
    for _, r in res.iterrows():
        rows.append({"fold": k, "train_days": n_tr, "test_days": n_te, **r.to_dict()})

df = pd.DataFrame(rows)
summ = (df.groupby("model")[["MAE (dk)", "RMSE (dk)", "MAPE (%)", "R2"]]
          .agg(["mean", "std"]).round(4))
print("\nFOLD OZETI (mean/std):")
print(summ.to_string())

out_path = os.path.join(PROJECT_ROOT, "results", "tables",
                        f"cv_rolling_origin_route_{args.route}.csv")
df.to_csv(out_path, index=False)
summ_path = os.path.join(PROJECT_ROOT, "results", "tables",
                         f"cv_rolling_origin_summary_route_{args.route}.csv")
summ.to_csv(summ_path)
print(f"\nCV tablolari: {out_path}\n              {summ_path}")
```

- [ ] **Step 2: Koş ve doğrula**

```bash
cd "C:/Users/Bilal/Desktop/Dersler/CSE496-Graduation-Project"
PYTHONPATH=. ./.venv/Scripts/python.exe scripts/run_cv.py --route 502
```

Expected: 5 fold koşar (~15-25 dk); `cv_rolling_origin_route_502.csv` 10 satır (5 fold × 2 model); MAE fold'lar arası makul bantta (örn. 0.38–0.50 — erken fold'larda train küçük olduğundan biraz yüksek olabilir). 5 fold prediction dosyası oluşur.

- [ ] **Step 3: Commit**

```bash
git add scripts/run_cv.py results/tables/cv_rolling_origin_route_502.csv results/tables/cv_rolling_origin_summary_route_502.csv results/tables/improved_ml_results_cv*.csv
git commit -m "feat: rolling-origin 5-fold CV (hoca madde 5)"
```

---

### Task 7: Significance + CI tabloları

**Files:**
- Create: `scripts/analysis_significance.py`

**Interfaces:**
- Consumes: `results/predictions/route_502_test_predictions.csv` (Task 4); `scripts/stats_utils` (Task 2)
- Produces:
  - `results/tables/statistical_tests_v3.csv` — kolonlar: `comparison, n, n_days, mae_a, mae_b, mae_diff, p_ttest, p_wilcoxon, p_ttest_daily, p_wilcoxon_daily, cohens_d, cliffs_delta`
  - `results/tables/metric_confidence_intervals.csv` — kolonlar: `model, mae, mae_ci_lo, mae_ci_hi, rmse, rmse_ci_lo, rmse_ci_hi`

> **Gün-düzeyi test gerekçesi:** Segment-düzeyi paired testler 16.315 segmenti bağımsız sayar; oysa aynı günün segmentleri korele (hava, trafik, olaylar) → p-value'lar iyimser çıkar. Bootstrap'ta kullanılan "gün = bağımsızlık birimi" ilkesinin aynısı testlere de uygulanır: her karşılaştırma için gün başına ortalama hata farkı hesaplanır (~15 gün-düzeyi değer), test bu değerler üzerinde koşulur. Makalede iki düzey birlikte raporlanır; gün-düzeyi olan muhafazakâr/birincil yorumdur.

- [ ] **Step 1: Scripti yaz**

`scripts/analysis_significance.py`:

```python
"""
Effect size (Cohen's d, Cliff's delta) + gun-bazli bootstrap CI tablolari.
Girdi: improved_ml.py --save-preds ciktisi.

Kullanim: PYTHONPATH=. python scripts/analysis_significance.py \
              --preds results/predictions/route_502_test_predictions.csv
"""
import os
import argparse
import numpy as np
import pandas as pd
from scipy import stats as sps

from scripts.stats_utils import cohens_d_paired, cliffs_delta, day_block_bootstrap_ci

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

MODEL_LABELS = {
    "pred_xgb_improved": "XGBoost (Improved)",
    "pred_rf_improved" : "RF (Improved)",
    "pred_rf_moe"      : "RF MoE",
    "pred_rf_base"     : "RF Baseline",
    "pred_histavg"     : "Historical Avg",
    "pred_naive"       : "Naive (GTFS)",
}
REFERENCE = "pred_xgb_improved"

ap = argparse.ArgumentParser()
ap.add_argument("--preds", required=True)
ap.add_argument("--n-boot", type=int, default=1000)
args = ap.parse_args()

df = pd.read_csv(args.preds)
pred_cols = [c for c in MODEL_LABELS if c in df.columns]
print(f"Yuklendi: {len(df)} satir, modeller: {pred_cols}")

# ── 1) Paired testler + effect size (referans: XGBoost Improved) ──────────────
err = {c: (df["y_true"] - df[c]).abs().values for c in pred_cols}
rows = []
for c in pred_cols:
    if c == REFERENCE:
        continue
    a, b = err[REFERENCE], err[c]     # a=referans hatalari, b=rakip hatalari
    t_p = sps.ttest_rel(a, b).pvalue
    w_p = sps.wilcoxon(a, b).pvalue if not np.allclose(a, b) else 1.0
    # gun-duzeyi kumelenmis test: gun basina ortalama hata farki (~15 deger)
    # (ayni gunun segmentleri korele -> segment-duzeyi p iyimser; bkz. Interfaces notu)
    daily = pd.DataFrame({"date": df["date"].values, "d": a - b}).groupby("date")["d"].mean()
    t_p_daily = sps.ttest_1samp(daily, 0.0).pvalue
    w_p_daily = sps.wilcoxon(daily).pvalue if not np.allclose(daily, 0) else 1.0
    rows.append({
        "comparison"      : f"{MODEL_LABELS[REFERENCE]} vs {MODEL_LABELS[c]}",
        "n"               : len(a),
        "n_days"          : len(daily),
        "mae_a"           : round(a.mean(), 4),
        "mae_b"           : round(b.mean(), 4),
        "mae_diff"        : round(b.mean() - a.mean(), 4),
        "p_ttest"         : t_p,
        "p_wilcoxon"      : w_p,
        "p_ttest_daily"   : t_p_daily,
        "p_wilcoxon_daily": w_p_daily,
        "cohens_d"        : round(cohens_d_paired(a, b), 4),
        "cliffs_delta"    : round(cliffs_delta(a, b), 4),
    })
tests = pd.DataFrame(rows)
tests_path = os.path.join(PROJECT_ROOT, "results", "tables", "statistical_tests_v3.csv")
tests.to_csv(tests_path, index=False)
print(f"\n{tests.to_string(index=False)}\n-> {tests_path}")

# ── 2) Gun-bazli bootstrap CI (MAE + RMSE, model basina) ──────────────────────
ci_rows = []
for c in pred_cols:
    sub = df[["date", "y_true", c]].rename(columns={c: "pred"})
    mae  = (sub["y_true"] - sub["pred"]).abs().mean()
    rmse = np.sqrt(((sub["y_true"] - sub["pred"]) ** 2).mean())
    mae_lo, mae_hi = day_block_bootstrap_ci(
        sub, lambda s: (s["y_true"] - s["pred"]).abs().mean(), n_boot=args.n_boot)
    rmse_lo, rmse_hi = day_block_bootstrap_ci(
        sub, lambda s: float(np.sqrt(((s["y_true"] - s["pred"]) ** 2).mean())),
        n_boot=args.n_boot)
    ci_rows.append({"model": MODEL_LABELS[c],
                    "mae": round(mae, 4), "mae_ci_lo": round(mae_lo, 4),
                    "mae_ci_hi": round(mae_hi, 4),
                    "rmse": round(rmse, 4), "rmse_ci_lo": round(rmse_lo, 4),
                    "rmse_ci_hi": round(rmse_hi, 4)})
cis = pd.DataFrame(ci_rows).sort_values("mae")
ci_path = os.path.join(PROJECT_ROOT, "results", "tables", "metric_confidence_intervals.csv")
cis.to_csv(ci_path, index=False)
print(f"\n{cis.to_string(index=False)}\n-> {ci_path}")
```

- [ ] **Step 2: Koş ve mantık kontrolü**

```bash
cd "C:/Users/Bilal/Desktop/Dersler/CSE496-Graduation-Project"
PYTHONPATH=. ./.venv/Scripts/python.exe scripts/analysis_significance.py \
    --preds results/predictions/route_502_test_predictions.csv
```

Expected: `statistical_tests_v3.csv` 5 satır (XGB vs RF-Imp/MoE/RF-Base/HistAvg/Naive). Mantık kontrolleri: XGB vs Naive'de |cliffs_delta| büyük (>0.3) ve cohens_d negatif-yönlü büyük; XGB vs RF-Improved'da |d| ve |δ| ≈ 0 (ihmal edilebilir). Gün-düzeyi p'ler segment-düzeyinden **büyük** (muhafazakâr) çıkmalı; n_days ≈ 15. XGB vs RF gibi küçük farklar gün-düzeyinde anlamlılığını yitirebilir — bu bir hata değil, dürüst raporlanacak bulgudur ("model ekseni pratik fark yaratmıyor" teziyle tutarlı). CI tablosunda her modelin mae'si kendi CI'ının içinde.

- [ ] **Step 3: Commit**

```bash
git add scripts/analysis_significance.py results/tables/statistical_tests_v3.csv results/tables/metric_confidence_intervals.csv
git commit -m "feat: effect size + gun-bazli bootstrap CI tablolari (hoca madde 3-4)"
```

---

### Task 8: Hata kırılımları (saat, zaman dilimi, hafta sonu, segment uzunluğu, yağmur, yön)

ÖN KOŞUL: Bu task figür üretir — koda başlamadan önce **dataviz skill'ini yükle**.

**Files:**
- Create: `scripts/analysis_error_slices.py`

**Interfaces:**
- Consumes: predictions CSV'leri (birden çok verilebilir — CV fold'ları poollamak için); `scripts/stats_utils` (Task 2)
- Produces:
  - `results/tables/error_slices_route_502.csv` — kolonlar: `dimension, level, n, mae_xgb, mae_ci_lo, mae_ci_hi, mae_rf, mean_y`
  - `results/tables/rain_within_fold_route_502_pooled.csv` — kolonlar: `fold, n_rainy, n_clear, mae_rainy, mae_clear, diff` (yalnız pooled CV modunda; erken-fold/az-train confound'una karşı fold-içi kontrol)
  - `results/figures/error_by_hour.png`, `results/figures/error_by_segment_length.png`, `results/figures/error_by_weather.png`

- [ ] **Step 1: Scripti yaz**

`scripts/analysis_error_slices.py`:

```python
"""
Hata kirilim analizleri (hoca madde 8-9): saatlik egri, zaman dilimi,
hafta ici/sonu, segment uzunlugu ceyrekleri, hava (yagmur), yon.
Birden cok predictions dosyasi verilirse satirlar poollanir
(rolling-origin CV fold'lari ayrik test pencereleri oldugundan gecerli).

Kullanim:
  PYTHONPATH=. python scripts/analysis_error_slices.py \
      --preds results/predictions/route_502_test_predictions.csv
  # yagmur icin genis orneklem (CV fold'lari poollanmis):
  PYTHONPATH=. python scripts/analysis_error_slices.py \
      --preds results/predictions/route_502_test_predictions_cv*.csv --tag pooled
"""
import os
import glob
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from scripts.stats_utils import day_block_bootstrap_ci

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
FIG_DIR      = os.path.join(PROJECT_ROOT, "results", "figures")
TAB_DIR      = os.path.join(PROJECT_ROOT, "results", "tables")

ap = argparse.ArgumentParser()
ap.add_argument("--preds", nargs="+", required=True)
ap.add_argument("--tag", default="")
ap.add_argument("--n-boot", type=int, default=500)
args = ap.parse_args()

paths = []
for p in args.preds:
    paths.extend(sorted(glob.glob(p)))
frames = []
for p in paths:
    f = pd.read_csv(p)
    f["source"] = os.path.basename(p)   # fold-ici kontrol icin kaynak dosya = fold
    frames.append(f)
df = pd.concat(frames, ignore_index=True)
print(f"Poollanan dosya: {len(paths)}  satir: {len(df)}")

df["err_xgb"] = (df["y_true"] - df["pred_xgb_improved"]).abs()
df["err_rf"]  = (df["y_true"] - df["pred_rf_improved"]).abs()

WEATHER = {0: "clear", 1: "cloudy", 2: "rainy", 3: "snowy"}
df["weather"] = df["weather_cat_enc"].map(WEATHER).fillna("clear")
df["weekend"] = np.where(df["day_type"] == 1, "weekend", "weekday")
df["timeblock"] = pd.cut(df["hour"], bins=[5, 10, 16, 20, 23], right=False,
                         labels=["morning (06-10)", "midday (10-16)",
                                 "evening (16-20)", "night (20-23)"])
df["seg_len"] = pd.qcut(df["scheduled_travel_min"], q=4,
                        labels=["Q1 shortest", "Q2", "Q3", "Q4 longest"])
df["direction"] = np.where(df["yon"] == 0,
                           "Halkapinar->Cengizhan", "Cengizhan->Halkapinar")

DIMS = [("hour", "hour"), ("timeblock", "timeblock"), ("weekend", "weekend"),
        ("seg_len", "seg_len"), ("weather", "weather"), ("direction", "direction")]

rows = []
for dim_name, col in DIMS:
    for lvl, g in df.groupby(col, observed=True):
        if len(g) < 30:
            continue
        lo, hi = day_block_bootstrap_ci(
            g, lambda s: s["err_xgb"].mean(), n_boot=args.n_boot)
        rows.append({"dimension": dim_name, "level": str(lvl), "n": len(g),
                     "mae_xgb": round(g["err_xgb"].mean(), 4),
                     "mae_ci_lo": round(lo, 4), "mae_ci_hi": round(hi, 4),
                     "mae_rf": round(g["err_rf"].mean(), 4),
                     "mean_y": round(g["y_true"].mean(), 4)})
slices = pd.DataFrame(rows)
sfx = f"_{args.tag}" if args.tag else ""
tab_path = os.path.join(TAB_DIR, f"error_slices_route_502{sfx}.csv")
slices.to_csv(tab_path, index=False)
print(f"\n{slices.to_string(index=False)}\n-> {tab_path}")

# ── Figurler (tek model: XGBoost; CI bantli) ──────────────────────────────────
def _ci_plot(sub, x_labels, title, xlabel, out_name, rotate=0):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(sub))
    y = sub["mae_xgb"].values
    yerr = np.vstack([y - sub["mae_ci_lo"].values, sub["mae_ci_hi"].values - y])
    ax.errorbar(x, y, yerr=yerr, fmt="o-", capsize=3)
    ax.set_xticks(x); ax.set_xticklabels(x_labels, rotation=rotate)
    ax.set_ylabel("MAE (minutes)"); ax.set_xlabel(xlabel)
    ax.set_title(title); ax.grid(alpha=0.3)
    fig.tight_layout()
    out = os.path.join(FIG_DIR, out_name)
    fig.savefig(out, dpi=200); plt.close(fig)
    print(f"-> {out}")

hour_s = slices[slices.dimension == "hour"].copy()
hour_s["level"] = hour_s["level"].astype(int)
hour_s = hour_s.sort_values("level")
_ci_plot(hour_s, hour_s["level"], "Prediction error by hour of day (XGBoost, 95% CI)",
         "Hour", f"error_by_hour{sfx}.png")

seg_s = slices[slices.dimension == "seg_len"]
_ci_plot(seg_s, seg_s["level"], "Error by scheduled segment length (XGBoost, 95% CI)",
         "Scheduled travel time quartile", f"error_by_segment_length{sfx}.png")

wx_s = slices[slices.dimension == "weather"]
_ci_plot(wx_s, wx_s["level"], "Error by weather condition (XGBoost, 95% CI)",
         "Weather", f"error_by_weather{sfx}.png")

# ── Yagmur fold-ici kontrol (yalniz pooled modda anlamli) ─────────────────────
# Confound: rolling-origin'de erken fold'larin train penceresi kucuk -> hatalari
# yapisal olarak yuksek, ve yagisli gunlerin cogu bu fold'larin test donemine
# dusuyor. Pooled "rainy > clear" farki bu etkiyle karisir. Kontrol: rainy-clear
# farki HER FOLD KENDI ICINDE hesaplanir, sonra fold'lar arasi mean +- std verilir.
if len(paths) > 1:
    fold_rows = []
    for src, g in df.groupby("source"):
        r = g[g["weather"] == "rainy"]
        c = g[g["weather"] == "clear"]
        if len(r) < 30 or len(c) < 30:
            print(f"  fold {src}: yetersiz yagisli ornek (n_rainy={len(r)}) — atlandi")
            continue
        fold_rows.append({"fold": src, "n_rainy": len(r), "n_clear": len(c),
                          "mae_rainy": round(r["err_xgb"].mean(), 4),
                          "mae_clear": round(c["err_xgb"].mean(), 4),
                          "diff": round(r["err_xgb"].mean() - c["err_xgb"].mean(), 4)})
    fw = pd.DataFrame(fold_rows)
    fw_path = os.path.join(TAB_DIR, f"rain_within_fold_route_502{sfx}.csv")
    fw.to_csv(fw_path, index=False)
    print(f"\nYAGMUR FOLD-ICI KONTROL:\n{fw.to_string(index=False)}")
    if len(fw):
        print(f"fold-ici rainy-clear farki: mean={fw['diff'].mean():.4f}  "
              f"std={fw['diff'].std():.4f}  (pozitif ve tutarliysa yagmur etkisi "
              f"train-boyutu confound'undan bagimsiz demektir)")
    print(f"-> {fw_path}")
```

Not: dataviz skill yüklendikten sonra figür stilini (renk, tipografi, grid) skill önerilerine göre bu şablon üzerinde iyileştir — tablo/CSV arayüzü sabit kalsın.

- [ ] **Step 2: Tek split + pooled CV koşumları**

```bash
cd "C:/Users/Bilal/Desktop/Dersler/CSE496-Graduation-Project"
PYTHONPATH=. ./.venv/Scripts/python.exe scripts/analysis_error_slices.py \
    --preds results/predictions/route_502_test_predictions.csv
PYTHONPATH=. ./.venv/Scripts/python.exe scripts/analysis_error_slices.py \
    --preds 'results/predictions/route_502_test_predictions_cv*.csv' --tag pooled
```

Expected: iki slice tablosu + pooled modda `rain_within_fold_route_502_pooled.csv` + 6 PNG. Mantık kontrolleri: sabah bloğu MAE > akşam; rainy MAE > clear (pooled'da rainy n, tek splitten belirgin büyük olmalı); Q1 shortest'ta göreli hata en yüksek. **Yağmur bulgusu makaleye fold-içi kontrolle girer:** pooled toplam farkı değil, fold-içi rainy−clear farkının mean±std'si raporlanır — fark fold'lar arasında tutarlı pozitifse train-boyutu confound'undan bağımsızdır; tutarsızsa yağmur bulgusu "geniş CI'lı gözlem" tonunda kalır (yol haritası §8 riskiyle uyumlu).

- [ ] **Step 3: Commit**

```bash
git add scripts/analysis_error_slices.py results/tables/error_slices_route_502*.csv results/figures/error_by_*.png
git commit -m "feat: hata kirilim analizleri + CI'li figurler (hoca madde 8-9)"
```

---

### Task 9: Trip-progress (cold-start) figürü

ÖN KOŞUL: dataviz skill yüklü olmalı (Task 8'de yüklendiyse yeterli).

**Files:**
- Create: `scripts/analysis_trip_progress.py`

**Interfaces:**
- Consumes: ana predictions + ablation predictions (`_fs-c0`, `_fs-c1`) — c0/c1 eğrileri "schedule bağlamı cold-start'ı nasıl telafi ediyor" katmanı için
- Produces: `results/tables/error_by_trip_progress.csv` (`segments_into_trip, n, mae_xgb_full, mae_ci_lo, mae_ci_hi, mae_xgb_c0, mae_xgb_c1`), `results/figures/error_by_trip_progress.png`

- [ ] **Step 1: Scripti yaz**

`scripts/analysis_trip_progress.py`:

```python
"""
Trip-progress hata egrisi (hoca madde 2): MAE vs segments_into_trip.
Full model + C0 (baglamsiz) + C1 (+GTFS) egrileri ust uste:
cold-start bolgesinde hatanin neden yuksek oldugu ve schedule'in
neden telafi ettigi tek figurde.

Kullanim: PYTHONPATH=. python scripts/analysis_trip_progress.py
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from scripts.stats_utils import day_block_bootstrap_ci

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
PRED_DIR     = os.path.join(PROJECT_ROOT, "results", "predictions")

MAX_POS = 12   # 12+ tek kovada

def load(name):
    df = pd.read_csv(os.path.join(PRED_DIR, name))
    df["pos"] = df["segments_into_trip"].clip(upper=MAX_POS)
    df["err"] = (df["y_true"] - df["pred_xgb_improved"]).abs()
    return df

full = load("route_502_test_predictions.csv")
c0   = load("route_502_test_predictions_fs-c0.csv")
c1   = load("route_502_test_predictions_fs-c1.csv")

rows = []
for pos, g in full.groupby("pos"):
    lo, hi = day_block_bootstrap_ci(g, lambda s: s["err"].mean(), n_boot=500)
    rows.append({"segments_into_trip": int(pos), "n": len(g),
                 "mae_xgb_full": round(g["err"].mean(), 4),
                 "mae_ci_lo": round(lo, 4), "mae_ci_hi": round(hi, 4),
                 "mae_xgb_c0": round(c0[c0.pos == pos]["err"].mean(), 4),
                 "mae_xgb_c1": round(c1[c1.pos == pos]["err"].mean(), 4)})
tab = pd.DataFrame(rows).sort_values("segments_into_trip")
tab_path = os.path.join(PROJECT_ROOT, "results", "tables", "error_by_trip_progress.csv")
tab.to_csv(tab_path, index=False)
print(tab.to_string(index=False), f"\n-> {tab_path}")

fig, ax = plt.subplots(figsize=(8.5, 5))
x = tab["segments_into_trip"].values
ax.axvspan(-0.5, 1.5, alpha=0.12, color="red",
           label="cold-start zone (lag features empty)")
ax.plot(x, tab["mae_xgb_c0"], "s--", label="C0: no context (temporal+spatial)")
ax.plot(x, tab["mae_xgb_c1"], "^--", label="C1: + GTFS schedule")
ax.plot(x, tab["mae_xgb_full"], "o-", label="Full model")
ax.fill_between(x, tab["mae_ci_lo"], tab["mae_ci_hi"], alpha=0.2)
ax.set_xlabel("Segments into trip")
ax.set_ylabel("MAE (minutes)")
ax.set_title("Prediction error vs. trip progress (XGBoost, route 502)")
labels = [str(int(v)) if v < MAX_POS else f"{MAX_POS}+" for v in x]
ax.set_xticks(x); ax.set_xticklabels(labels)
ax.legend(); ax.grid(alpha=0.3)
fig.tight_layout()
fig_path = os.path.join(PROJECT_ROOT, "results", "figures", "error_by_trip_progress.png")
fig.savefig(fig_path, dpi=200); plt.close(fig)
print(f"-> {fig_path}")
```

- [ ] **Step 2: Koş ve doğrula**

```bash
cd "C:/Users/Bilal/Desktop/Dersler/CSE496-Graduation-Project"
PYTHONPATH=. ./.venv/Scripts/python.exe scripts/analysis_trip_progress.py
```

Expected: tablo 13 satır (pos 0..12+); full eğri pos 0-1'de yüksek, sonra düşüp plato; C0 her yerde en üstte; C1 cold-start bölgesinde C0'dan belirgin aşağıda (GTFS telafisi). PNG oluşur.

- [ ] **Step 3: Commit**

```bash
git add scripts/analysis_trip_progress.py results/tables/error_by_trip_progress.csv results/figures/error_by_trip_progress.png
git commit -m "feat: trip-progress cold-start figuru (hoca madde 2)"
```

---

### Task 10: LSTM ablation (C2–C4) — feature-set + save-preds

> **Neden kritik yol:** Research question'ın merkez deneyi model × feature-set ızgarası; "feature ekseni MAE'yi X kadar, model ekseni Y≪X kadar oynatıyor" iddiasının model ekseni ancak klasik-vs-derin (XGB vs LSTM) karşılaştırmasıyla güçlü kanıtlanır — XGB vs RF ikisi de ağaç tabanlı olduğundan tek başına yetmez. torch bu makinede kurulu; koşumlar gecelik planlanır.
>
> **Mimari sınırlılık (makaleye taşınacak):** Dual-input LSTM'in sequence kolu doğası gereği lag (önceki segmentlerin gerçekleşen süreleri) içerir; C0/C1 lag'i dışladığı için LSTM×C0 ve LSTM×C1 dürüstçe koşulamaz. Izgarada bu hücreler "N/A (mimari gereği)" bırakılır ve makale metninde tek cümleyle açıklanır. LSTM ablationu C2'den başlar. Sequence kanalları (lagged travel time, scheduled, distance, progress) C2'den itibaren zaten konfig kapsamında olduğundan, feature-set kısıtı esas olarak **context koluna** (CONTEXT_FEATURES alt kümesi) uygulanır.

**Files:**
- Modify: `scripts/improved_lstm.py`

**Interfaces:**
- Produces (CLI):
  - `--feature-set {c2,c3,c4,full}` (default full) — `scripts/feature_sets.py`'daki `LSTM_ALLOWED` dışı istek (c0/c1) → `SystemExit` açık hata; CONTEXT_FEATURES, ilgili konfigin feature listesiyle kesiştirilir
  - `--save-preds` → `results/predictions/route_<RID>_test_predictions_lstm_fs-<set>.csv` (kolonlar: META + `y_true` + `pred_lstm`; **tam segment-level test seti** üzerinde, mevcut cold-start fallback mantığı korunarak — rapor §5.2'deki "same-test-set" ilkesi). `create_sequences`'a orijinal satır indeksleri eklenir ki tahminler test satırlarıyla hizalanabilsin.
- Produces (tablolar):
  - `results/tables/ablation_additive_lstm_route_502.csv` — kolonlar: `config, model, MAE (dk), RMSE (dk), MAPE (%), R2`
  - `results/tables/ablation_grid_route_502.csv` — birleşik ızgara: satır=model {XGBoost, RF, LSTM}, sütun=config {c0..c4}, hücre=MAE; LSTM×c0/c1 = `NA`

- [ ] **Step 1: `--feature-set` + `--save-preds` argümanlarını ekle** — `LSTM_ALLOWED` kontrolü (c0/c1 → SystemExit, hata mesajında mimari gerekçe); CONTEXT_FEATURES kesişimi; save-preds hizalaması için `create_sequences` dönüşüne satır-id listesi.

- [ ] **Step 2: c2/c3/c4 koşumları** (her biri saatler sürer — gecelik/ardışık planla; seed=42, window=7 sabit):

```bash
cd "C:/Users/Bilal/Desktop/Dersler/CSE496-Graduation-Project"
PYTHONPATH=. ./.venv/Scripts/python.exe scripts/improved_lstm.py --route 502 --feature-set c2 --save-preds
PYTHONPATH=. ./.venv/Scripts/python.exe scripts/improved_lstm.py --route 502 --feature-set c3 --save-preds
PYTHONPATH=. ./.venv/Scripts/python.exe scripts/improved_lstm.py --route 502 --feature-set c4 --save-preds
```

Expected: üç koşum hatasız; c4 (=full feature seti) MAE ≈ 0.4345 (rapor Table 5.1 değeri).

- [ ] **Step 3: Birleşik ızgara tablosunu üret** — Task 5'in `ablation_additive_route_502.csv`'si (XGB/RF satırları) + LSTM sonuçları pandas ile pivot edilip `ablation_grid_route_502.csv` yazılır (küçük tek seferlik script ya da `run_ablation.py`'a `--emit-grid` adımı). Mantık kontrolü: her konfigde |MAE_LSTM − MAE_XGB| farkı, konfigler arası (sütunlar arası) farktan belirgin küçük olmalı — RQ'nun sayısal kanıtı.

- [ ] **Step 4: Commit**

```bash
git add scripts/improved_lstm.py results/tables/ablation_additive_lstm_route_502.csv results/tables/ablation_grid_route_502.csv
git commit -m "feat: LSTM ablation C2-C4 + model x feature-set izgarasi (RQ merkez deneyi)"
```

---

### Task 11: Trip-level aggregation (Kaya & Kalay adil kıyası)

> Segment tahminleri trip boyunca kümülatif toplanarak uçtan uca varış MAE'si üretilir. Referans makale (Kaya & Kalay, MAE 2.97 dk) trip ölçeğinde tahmin yapıyor; bizim segment-MAE'miz (0.43 dk) ile doğrudan kıyas "elma-armut". Bu task kıyası adil kılar ve MAPE %41 eleştirisine ikinci savunma hattıdır (segment hataları kısmen bağımsızsa kümülatif toplamda kancellenir).

**Files:**
- Create: `scripts/analysis_trip_level.py`

**Interfaces:**
- Consumes: `results/predictions/route_502_test_predictions.csv` (Task 4 — META'da `bus_id` ve `trip_start_time` bulunmalı); `scripts/stats_utils` (Task 2)
- Produces:
  - `results/tables/trip_level_mae_route_502.csv` — kolonlar: `horizon_stops, n_trips, mae_xgb, mae_ci_lo, mae_ci_hi, mae_naive` (horizon ∈ {1, 3, 5, 10, trip sonu})
  - `results/figures/trip_level_error_vs_horizon.png`

- [ ] **Step 1: Scripti yaz** — trip anahtarı `(date, bus_id, yon, trip_start_time)`; her trip içinde `from_stop_seq` sırasına dizilir; k durak ilerisi için tahmini kümülatif süre = ilk k segment tahmininin toplamı, gerçek = ilk k `y_true` toplamı; hata = |fark|. Ardışıklığı bozuk tripler (test penceresi trip ortasından kesmiş ya da segment atlanmış) analiz dışı bırakılır ve **atılan trip sayısı loglanır** (sessiz eleme yok). CI: gün-bazlı blok bootstrap. Kıyas kolonu olarak `pred_naive` (GTFS) aynı şekilde toplanır.

- [ ] **Step 2: Koş ve mantık kontrolü**

```bash
cd "C:/Users/Bilal/Desktop/Dersler/CSE496-Graduation-Project"
PYTHONPATH=. ./.venv/Scripts/python.exe scripts/analysis_trip_level.py
```

Expected: kümülatif MAE horizon'la **sub-lineer** büyür (k segmentte k×0.43'ten belirgin küçük — hatalar kısmen kancelleniyor); trip-sonu MAE, Kaya & Kalay'ın 2.97 dk'sıyla aynı ölçekte kıyaslanabilir bir sayı verir. Figürden önce dataviz skill yüklü olmalı (Task 8'de yüklendiyse yeterli).

- [ ] **Step 3: Commit**

```bash
git add scripts/analysis_trip_level.py results/tables/trip_level_mae_route_502.csv results/figures/trip_level_error_vs_horizon.png
git commit -m "feat: trip-level aggregation (referans makaleyle adil kiyas)"
```

---

### Task 12: Yol haritası dokümanını durumla güncelle

**Files:**
- Modify: `reports/sci_makale_yol_haritasi.md`

- [ ] **Step 1: Doküman sonuna "Uygulama Durumu" bölümü ekle**

`## 9. Sonraki Adımlar` bölümünden önce yeni bölüm: hangi analizler üretildi (tablolar/figürler ve dosya yolları), headline sayılar (ablation ızgarası deseni — feature ekseni vs model ekseni farkı, CV mean±std, effect size + gün-düzeyi p özetleri, yağmur fold-içi kontrollü sonucu, trip-level MAE), ve **makale yazımına taşınacak notlar**: (a) ızgarada LSTM×C0/C1 hücrelerinin "N/A — sequence girdisi doğası gereği lag içerir" olarak işaretlenmesi ve metinde tek cümleyle açıklanması, (b) significance metodolojisinin "gün = bağımsızlık birimi" ilkesi üzerinden anlatılması (segment- ve gün-düzeyi p'lerin birlikte raporlanması), (c) yağmur bulgusunun fold-içi kontrollü haliyle sunulması. Kalan işler: LSTM rolling-origin CV (opsiyonel robustluk eki), literatür taraması (teslim öncesi ayrı plan — kullanıcı kararıyla ertelendi). Gerçek sayılarla doldurulacak (koşum çıktılarından).

- [ ] **Step 2: Commit**

```bash
git add reports/sci_makale_yol_haritasi.md
git commit -m "docs: yol haritasina uygulama durumu bolumu (yerel analizler tamamlandi)"
```

---

## Plan dışı (bilinçli ertelenen)

> **Revizyon notu:** Orijinal listede ertelenen c4 ablation + multi-route (Task 5), LSTM ablation (Task 10) ve trip-level aggregation (Task 11) **plana dahil edildi** — erteleme gerekçeleri (v4 verisi yok, torch yok) bu makinede geçersiz çıktı.

- **Literatür taraması ve bibliyografya genişletmesi:** SCI için 30–60 referans gerekir (raporda 5 var); Kaya & Kalay girdisi de eksik bilgiyle duruyor. Kullanıcı kararıyla teslim öncesine ertelendi — ayrı planlanacak, takvimde unutulmamalı.
- **LSTM rolling-origin CV (5 gecelik koşum):** zorunlu değil, robustluk eki; Task 10 ablation'ı bittikten sonra takvim müsaitse `improved_lstm.py`'a `--train-end-day/--test-days` eklenerek koşulur.
- **Yol haritası §7 hoca soruları (RQ onayı, veri toplamayı yeniden başlatma, hedef dergi):** hocanın cevabına bağlı işler; bu plandaki analizler her RQ kurgusunda gerekli olduğundan beklemeden koşulabilir.
