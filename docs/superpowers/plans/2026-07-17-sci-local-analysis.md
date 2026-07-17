# SCI Yerel Analiz Katmanı Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hocanın istediği makale analizlerinin yerelde yapılabilir kısmını üretmek: per-segment tahmin kaydı, effect size + gün-bazlı bootstrap CI, saatlik/kırılım hata analizleri, trip-progress figürü, additive ablation (C0–C3) ve rolling-origin CV — hepsi hat 502, `route_502_features_v2.csv`'den türetilmiş v3 feature'larıyla.

**Architecture:** `improved_ml.py` tek eğitim scripti kalır; ona `--feature-set`, `--save-preds`, `--train-end-day/--test-days`, `--core-only` eklenir ve historical feature'lar leakage-safe olacak şekilde her koşumda kendi train penceresinden yeniden hesaplanır. Eğitim çıktıları `results/predictions/*.csv` (satır bazlı) + `results/tables/*.csv` (özet) olur; üç bağımsız analiz scripti (significance, error-slices, trip-progress) yalnızca predictions dosyalarını okur. Driver scriptler (ablation, CV) improved_ml.py'ı subprocess ile çağırır.

**Tech Stack:** Python venv (`.venv`), pandas, numpy, scikit-learn, xgboost, scipy, matplotlib, pytest. (torch YOK — LSTM işleri bu planın dışında, sunucu/v4 verisi geldiğinde ayrı plan.)

## Global Constraints

- Veri: `collected_data/route_502_features_v2.csv` (81.575 satır, 73 gün, 2026-04-02→06-13). v4/dwell YOK — `c4` feature seti istenirse script **açık hata ile durmalı** (sessizce eksik feature'la koşmak yasak).
- Tüm rasgelelik seed=42; mevcut kronolojik %80/20 headline split davranışı değişmemeli (CV argümanları verilmediğinde birebir aynı sonuç).
- CSV veri dosyaları commit edilmez (`/collected_data/` gitignore'da); `results/` çıktıları commit edilir.
- Figür üreten task'lardan önce **dataviz skill'i yükle**; figür etiketleri İngilizce (SCI makalesi için).
- Bootstrap: satır bazlı değil **gün-bazlı blok** (B=1000, seed=42, %95 CI).

---

### Task 1: Ortam kurulumu

**Files:**
- Modify: `requirements.txt`

**Interfaces:**
- Produces: `.venv/bin/python` ile pandas/sklearn/xgboost/scipy/matplotlib/pytest import edilebilir.

- [ ] **Step 1: venv oluştur ve paketleri kur**

```bash
cd /Users/omerkoc/bus_arrival
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install numpy pandas scikit-learn xgboost scipy matplotlib pytest
```

Expected: hatasız kurulum. (Python 3.14 wheel sorunu çıkarsa: `brew install python@3.12` ve `python3.12 -m venv .venv` ile tekrar.)

- [ ] **Step 2: importları doğrula**

```bash
.venv/bin/python -c "import pandas, numpy, sklearn, xgboost, scipy, matplotlib; print('OK')"
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
# LSTM islerinde ayrica: torch>=2.2
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
cd /Users/omerkoc/bus_arrival && .venv/bin/python -m pytest tests/test_stats_utils.py -v
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
.venv/bin/python -m pytest tests/test_stats_utils.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/__init__.py scripts/stats_utils.py tests/test_stats_utils.py
git commit -m "feat: effect size + gun-bazli blok bootstrap istatistik yardimcilari (TDD)"
```

---

### Task 3: v3 feature'larını yerel v2 CSV'den türet

**Files:**
- Create: `scripts/derive_v3_from_v2.py`

**Interfaces:**
- Consumes: `build_features_route.add_v3(df)` (mevcut fonksiyon; DB gerektirmez)
- Produces: `collected_data/route_502_features_v3.csv` — v2 kolonları + `deviation_minutes, cumul_deviation, rolling_3_deviation, stop_hist_median, stop_hist_ratio, prev_speed_mpm` (improved_ml.py bunu otomatik bulur: v4 yoksa v3'ü okur)

- [ ] **Step 1: Scripti yaz**

`scripts/derive_v3_from_v2.py`:

```python
"""
Yerelde DB olmadiginda v3 feature'larini v2 CSV'den turetir.
add_v3() saf DataFrame islemi oldugu icin DB gerektirmez.
(v4/dwell raw GPS ister -> sunucudaki DB'den; bu script v4 URETMEZ.)

Kullanim: python scripts/derive_v3_from_v2.py --route 502
"""
import os
import argparse
import pandas as pd

from scripts.build_features_route import add_v3

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

ap = argparse.ArgumentParser()
ap.add_argument("--route", type=int, default=502)
args = ap.parse_args()

v2_path = os.path.join(PROJECT_ROOT, "collected_data", f"route_{args.route}_features_v2.csv")
v3_path = os.path.join(PROJECT_ROOT, "collected_data", f"route_{args.route}_features_v3.csv")

df = pd.read_csv(v2_path)
print(f"v2 yuklendi: {len(df)} satir, {len(df.columns)} kolon")
df = add_v3(df)
df.to_csv(v3_path, index=False)
print(f"-> {v3_path}  ({df.shape[0]} satir, {df.shape[1]} kolon)")
```

Not: `build_features_route` modül seviyesinde `import config` yapar (GTFS'ten durak listesi yükler; `data/bus-eshot-gtfs/` yerelde mevcut). `scripts.build_features_route` importu için Task 2'deki `scripts/__init__.py` yeterli; script'i repo kökünden `PYTHONPATH=. .venv/bin/python scripts/derive_v3_from_v2.py` olarak çalıştır.

- [ ] **Step 2: Çalıştır ve doğrula**

```bash
cd /Users/omerkoc/bus_arrival
PYTHONPATH=. .venv/bin/python scripts/derive_v3_from_v2.py --route 502
.venv/bin/python -c "
import pandas as pd
df = pd.read_csv('collected_data/route_502_features_v3.csv')
need = ['cumul_deviation','rolling_3_deviation','stop_hist_median','stop_hist_ratio','prev_speed_mpm']
assert all(c in df.columns for c in need), df.columns.tolist()
assert len(df) == 81575, len(df)
print('v3 OK:', len(df), 'satir')
"
```

Expected: `v3 OK: 81575 satir`

- [ ] **Step 3: Commit (yalnız script; CSV gitignore'da)**

```bash
git add scripts/derive_v3_from_v2.py
git commit -m "feat: v3 feature'larini yerel v2 CSV'den tureten script"
```

---

### Task 4: improved_ml.py — leakage-safe historical + split maskeleri + save-preds + feature-set + CV argümanları

Bu task improved_ml.py'daki tüm değişiklikleri tek seferde yapar (hepsi aynı bölgelere dokunuyor; ayrı task'lar çakışırdı). Headline davranış korunur: argümansız `--route 502` koşumu eski sonuçları (MAE ~0.43-0.44 bandı, dwell'siz v3 verisiyle) vermeli.

**Files:**
- Modify: `scripts/improved_ml.py`

**Interfaces:**
- Produces (CLI):
  - `--feature-set {c0,c1,c2,c3,c4,full}` (default full). c0–c4 için eksik feature → `SystemExit` hata.
  - `--save-preds` → `results/predictions/route_<RID>_test_predictions<suffix>.csv`; kolonlar: `date, arrival_timestamp, hour, day_of_week, day_type, yon, from_stop_seq, to_stop_seq, segments_into_trip, is_trip_start, stop_progress, distance_m, scheduled_travel_min, weather_cat_enc, precipitation, y_true, pred_naive, pred_histavg, [pred_rf_base], pred_rf_improved, [pred_xgb_improved], [pred_rf_moe]`
  - `--train-end-day N --test-days M` → kronolojik gün-bazlı split (ilk N gün train, sonraki M gün test); verilmezse mevcut %80/20.
  - `--core-only` → RF Baseline ve MoE bölümlerini atlar (ablation/CV hızı için).
  - suffix'e ekler: `_fs-<set>` (full değilse), `_cv<N>` (CV ise).
- Consumes: v3 CSV (Task 3).

- [ ] **Step 1: Argümanları ekle**

`_ap.add_argument("--no-tripstart-feat", ...)` bloğundan sonra ekle:

```python
_ap.add_argument("--feature-set", choices=["c0", "c1", "c2", "c3", "c4", "full"],
                 default="full", help="Additive ablation konfigurasyonu (default: full)")
_ap.add_argument("--save-preds", action="store_true",
                 help="Test seti per-segment tahminlerini results/predictions/ altina yaz")
_ap.add_argument("--train-end-day", type=int, default=None,
                 help="CV: train = ilk N gun (kronolojik). Verilmezse %80/20 satir spliti")
_ap.add_argument("--test-days", type=int, default=9,
                 help="CV: test = train sonrasi M gun (default 9)")
_ap.add_argument("--core-only", action="store_true",
                 help="Sadece RF Improved + XGBoost (baseline RF ve MoE atlanir)")
```

ve `TRIPSTART_FEAT = _args.tripstart_feat` satırından sonra:

```python
FEATURE_SET = _args.feature_set
```

- [ ] **Step 2: Feature-set tanımlarını ekle ve seçim mantığını değiştir**

`LEAN_FEATURES = [...]` bloğundan hemen sonra ekle:

```python
# ── Additive ablation feature setleri (SCI: hoca madde 1) ─────────────────────
#   c0: baglamsiz taban (temporal + spatial)
#   c1: + GTFS tarife       (scheduled_travel_min)
#   c2: + sapma/lag baglami (prev/cumul/rolling deviation + is_trip_start)
#   c3: + tarihsel          (stop_hist_median/ratio, prev_speed_mpm)
#   c4: + dwell             (v4 verisi gerekir — yerelde YOK, sunucudan gelince)
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
            f"(c4 dwell gerektirir -> sunucudan route_{ROUTE_ID}_features_v4.csv alinmali. "
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
    META = ["date", "arrival_timestamp", "hour", "day_of_week", "day_type", "yon",
            "from_stop_seq", "to_stop_seq", "segments_into_trip", "is_trip_start",
            "stop_progress", "distance_m", "scheduled_travel_min",
            "weather_cat_enc", "precipitation"]
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
cd /Users/omerkoc/bus_arrival
PYTHONPATH=. .venv/bin/python scripts/improved_ml.py --route 502 --save-preds
```

Expected: hatasız biter; "Veri: v3" satırı görünür; XGBoost Improved MAE **0.42–0.45 bandında** (dwell'siz v3 ile yayındaki 0.4327'den küçük sapma normal — dwell katkısı ~%1-3); `results/predictions/route_502_test_predictions.csv` oluşur, 16.315 satır. Kontrol:

```bash
.venv/bin/python -c "
import pandas as pd
p = pd.read_csv('results/predictions/route_502_test_predictions.csv')
assert len(p) == 16315, len(p)
for c in ['y_true','pred_naive','pred_histavg','pred_rf_base','pred_rf_improved','pred_xgb_improved','pred_rf_moe']:
    assert c in p.columns, c
print('preds OK', p.shape)
print((p.y_true - p.pred_xgb_improved).abs().mean())
"
```

- [ ] **Step 7: c4'ün açık hata verdiğini doğrula**

```bash
PYTHONPATH=. .venv/bin/python scripts/improved_ml.py --route 502 --feature-set c4 2>&1 | tail -3
```

Expected: `HATA: feature-set 'c4' icin eksik/NaN feature'lar: ['dwell_time_sec', 'prev_dwell_time_sec']` içeren SystemExit mesajı.

- [ ] **Step 8: Commit**

```bash
git add scripts/improved_ml.py
git commit -m "feat: improved_ml'e feature-set/save-preds/CV-split/core-only + leakage-safe historical"
```

---

### Task 5: Additive ablation driver + koşum (C0–C3)

**Files:**
- Create: `scripts/run_ablation.py`

**Interfaces:**
- Consumes: `improved_ml.py --feature-set cK --core-only --save-preds` (Task 4)
- Produces: `results/tables/ablation_additive_route_502.csv` — kolonlar: `config, n_features, features_added, model, MAE (dk), RMSE (dk), MAPE (%), R2` (model ∈ {XGBoost Improved, RF Improved}); ayrıca her config için `results/predictions/route_502_test_predictions_fs-cK.csv`

- [ ] **Step 1: Driver'ı yaz**

`scripts/run_ablation.py`:

```python
"""
Additive ablation: C0 -> C3 (c4 dwell verisi gelince ayni komutla kosulur).
Her konfig improved_ml.py'i subprocess ile calistirir, ozet tabloyu birlestirir.

Kullanim: PYTHONPATH=. python scripts/run_ablation.py --route 502 --configs c0 c1 c2 c3
"""
import os
import sys
import argparse
import subprocess
import pandas as pd

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

ADDED = {
    "c0": "taban: temporal+spatial",
    "c1": "+ scheduled_travel_min (GTFS)",
    "c2": "+ deviation/lag (prev, cumul, rolling, is_trip_start)",
    "c3": "+ historical (stop_hist_median/ratio, prev_speed_mpm)",
    "c4": "+ dwell (dwell_time_sec, prev_dwell_time_sec)",
}
N_FEATS = {"c0": 6, "c1": 7, "c2": 12, "c3": 15, "c4": 17}

ap = argparse.ArgumentParser()
ap.add_argument("--route", type=int, default=502)
ap.add_argument("--configs", nargs="+", default=["c0", "c1", "c2", "c3"])
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

- [ ] **Step 2: Koş (c0–c3) ve sonucu incele**

```bash
cd /Users/omerkoc/bus_arrival
PYTHONPATH=. .venv/bin/python scripts/run_ablation.py --route 502 --configs c0 c1 c2 c3
```

Expected: 4 konfig sırayla koşar (~10-20 dk); `ablation_additive_route_502.csv` 8 satır (4 config × 2 model). Beklenen desen: c0 MAE en yüksek; c1'de belirgin düşüş (GTFS katkısı); c2'de tekrar düşüş (deviation katkısı); c3 küçük iyileşme. Her config için `results/predictions/route_502_test_predictions_fs-cK.csv` oluşmuş olmalı.

- [ ] **Step 3: Commit**

```bash
git add scripts/run_ablation.py results/tables/ablation_additive_route_502.csv results/tables/improved_ml_results_fs-*.csv
git commit -m "feat: additive ablation C0-C3 (GTFS/deviation/historical katki kaniti)"
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
cd /Users/omerkoc/bus_arrival
PYTHONPATH=. .venv/bin/python scripts/run_cv.py --route 502
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
  - `results/tables/statistical_tests_v3.csv` — kolonlar: `comparison, n, mae_a, mae_b, mae_diff, p_ttest, p_wilcoxon, cohens_d, cliffs_delta`
  - `results/tables/metric_confidence_intervals.csv` — kolonlar: `model, mae, mae_ci_lo, mae_ci_hi, rmse, rmse_ci_lo, rmse_ci_hi`

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
    rows.append({
        "comparison"  : f"{MODEL_LABELS[REFERENCE]} vs {MODEL_LABELS[c]}",
        "n"           : len(a),
        "mae_a"       : round(a.mean(), 4),
        "mae_b"       : round(b.mean(), 4),
        "mae_diff"    : round(b.mean() - a.mean(), 4),
        "p_ttest"     : t_p,
        "p_wilcoxon"  : w_p,
        "cohens_d"    : round(cohens_d_paired(a, b), 4),
        "cliffs_delta": round(cliffs_delta(a, b), 4),
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
cd /Users/omerkoc/bus_arrival
PYTHONPATH=. .venv/bin/python scripts/analysis_significance.py \
    --preds results/predictions/route_502_test_predictions.csv
```

Expected: `statistical_tests_v3.csv` 5 satır (XGB vs RF-Imp/MoE/RF-Base/HistAvg/Naive). Mantık kontrolleri: XGB vs Naive'de |cliffs_delta| büyük (>0.3) ve cohens_d negatif-yönlü büyük; XGB vs RF-Improved'da |d| ve |δ| ≈ 0 (ihmal edilebilir). CI tablosunda her modelin mae'si kendi CI'ının içinde.

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
df = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
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
```

Not: dataviz skill yüklendikten sonra figür stilini (renk, tipografi, grid) skill önerilerine göre bu şablon üzerinde iyileştir — tablo/CSV arayüzü sabit kalsın.

- [ ] **Step 2: Tek split + pooled CV koşumları**

```bash
cd /Users/omerkoc/bus_arrival
PYTHONPATH=. .venv/bin/python scripts/analysis_error_slices.py \
    --preds results/predictions/route_502_test_predictions.csv
PYTHONPATH=. .venv/bin/python scripts/analysis_error_slices.py \
    --preds 'results/predictions/route_502_test_predictions_cv*.csv' --tag pooled
```

Expected: iki tablo + 6 PNG. Mantık kontrolleri: sabah bloğu MAE > akşam; rainy MAE > clear (pooled'da rainy n, tek splitten belirgin büyük olmalı); Q1 shortest'ta göreli hata en yüksek.

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
cd /Users/omerkoc/bus_arrival
PYTHONPATH=. .venv/bin/python scripts/analysis_trip_progress.py
```

Expected: tablo 13 satır (pos 0..12+); full eğri pos 0-1'de yüksek, sonra düşüp plato; C0 her yerde en üstte; C1 cold-start bölgesinde C0'dan belirgin aşağıda (GTFS telafisi). PNG oluşur.

- [ ] **Step 3: Commit**

```bash
git add scripts/analysis_trip_progress.py results/tables/error_by_trip_progress.csv results/figures/error_by_trip_progress.png
git commit -m "feat: trip-progress cold-start figuru (hoca madde 2)"
```

---

### Task 10: Yol haritası dokümanını durumla güncelle

**Files:**
- Modify: `reports/sci_makale_yol_haritasi.md`

- [ ] **Step 1: Doküman sonuna "Uygulama Durumu" bölümü ekle**

`## 9. Sonraki Adımlar` bölümünden önce yeni bölüm: hangi analizler üretildi (tablolar/figürler ve dosya yolları), headline sayılar (ablation deseni, CV mean±std, effect size özetleri, yağmur pooled sonucu), ve kalan bloklu işler (c4/dwell + multi-route → sunucudan `route_*_features_v4.csv`; LSTM işleri → torch kurulumu + ayrı plan; LSTM'in C0/C1'i dürüstçe koşamayacağı tasarım notu — sequence girdisi doğası gereği lag içerir, LSTM ablationu C2'den başlar). Gerçek sayılarla doldurulacak (koşum çıktılarından).

- [ ] **Step 2: Commit**

```bash
git add reports/sci_makale_yol_haritasi.md
git commit -m "docs: yol haritasina uygulama durumu bolumu (yerel analizler tamamlandi)"
```

---

## Plan dışı (bilinçli ertelenen)

- **c4 ablation + multi-route (268/565):** sunucudan v4 CSV'ler gelince `run_ablation.py --configs c4` ve `--route 268/565` ile aynı kod koşar.
- **LSTM save-preds/ablation/CV:** torch kurulumu + `create_sequences`'a anahtar kolonları ekleme gerektirir; sunucu verisi geldiğinde LSTM işleriyle birlikte ayrı küçük plan.
- **Trip-level aggregation (Kaya & Kalay adil kıyası):** hoca Soru 6'nın cevabına bağlı.
