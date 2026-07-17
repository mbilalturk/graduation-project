"""
Improved ML Models — Bus Travel Time Prediction
================================================
Random Forest + XGBoost uzerindeki iyilestirmeler:

  1. Log-transform (log1p)       — Hedef degiskeni normalize eder -> MAPE dusuror, R2 artar
  2. Daha iyi hiperparametreler  — Daha fazla agac, daha derin, daha az min_samples_leaf
  3. Yeni ozellikler             — v3 verisi varsa: cumul_deviation, rolling_3_deviation,
                                   stop_hist_median, prev_speed_mpm, stop_hist_ratio
  4. Segment bazli modeller      — Baslangic/orta/bitis duraklar icin ayri RF modeli
                                   (baslangic duraklarinda hata 2x daha yuksek!)

Kullanim:
    # Once ilgili hat icin feature setini olustur (v2+v3+v4 tek script):
    python build_features_route.py --route 502

    # Sonra bu scripti calistir:
    python improved_ml.py --route 502
"""

import os
import argparse
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

try:
    from xgboost import XGBRegressor
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print("XGBoost bulunamadi — RF sonuclari gosterilecek")

# ── Hat parametresi ───────────────────────────────────────────────────────────
_ap = argparse.ArgumentParser()
_ap.add_argument("--route", type=int, default=502, help="route_id (502, 268, 565)")
_ap.add_argument("--target", choices=["travel", "deviation"], default="travel",
                 help="Hedef: travel=log1p(travel_time), deviation=travel-scheduled")
_ap.add_argument("--coldstart", choices=["scheduled", "none", "hist"], default="none",
                 help="Trip-basi prev_travel_time_min=0 doldurma (default: none — Adim 5 kazanani)")
_ap.add_argument("--no-tripstart-feat", dest="tripstart_feat", action="store_false",
                 help="is_trip_start bayragini EKLEME (default: ekli)")
_ap.add_argument("--feature-set", choices=["c0", "c1", "c2", "c3", "c4", "full"],
                 default="full", help="Additive ablation konfigurasyonu (default: full)")
_ap.add_argument("--save-preds", action="store_true",
                 help="Test seti per-segment tahminlerini results/predictions/ altina yaz")
_ap.add_argument("--train-end-day", type=int, default=None,
                 help="CV: train = ilk N gun (kronolojik). Verilmezse %%80/20 satir spliti")
_ap.add_argument("--test-days", type=int, default=9,
                 help="CV: test = train sonrasi M gun (default 9)")
_ap.add_argument("--core-only", action="store_true",
                 help="Sadece RF Improved + XGBoost (baseline RF ve MoE atlanir)")
_ap.set_defaults(tripstart_feat=True)
_args, _ = _ap.parse_known_args()
ROUTE_ID = _args.route
TARGET_MODE = _args.target
COLDSTART = _args.coldstart
TRIPSTART_FEAT = _args.tripstart_feat
FEATURE_SET = _args.feature_set

# ── Yollar ────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
CSV_V4       = os.path.join(PROJECT_ROOT, "collected_data", f"route_{ROUTE_ID}_features_v4.csv")
CSV_V3       = os.path.join(PROJECT_ROOT, "collected_data", f"route_{ROUTE_ID}_features_v3.csv")
CSV_V2       = os.path.join(PROJECT_ROOT, "collected_data", f"route_{ROUTE_ID}_features_v2.csv")
RESULTS_DIR  = os.path.join(PROJECT_ROOT, "results")

os.makedirs(os.path.join(RESULTS_DIR, "tables"), exist_ok=True)

print("=" * 65)
print("Improved ML Models — Bus Travel Time Prediction")
print("=" * 65)

# ── Veri yukle ────────────────────────────────────────────────────────────────
if os.path.exists(CSV_V4):
    CSV_PATH = CSV_V4
    print(f"Veri: v4 (dwell_time_sec + v3 ozellikleri mevcut)")
elif os.path.exists(CSV_V3):
    CSV_PATH = CSV_V3
    print(f"Veri: v3 (v4/dwell icin: build_features_route.py --route {ROUTE_ID})")
else:
    CSV_PATH = CSV_V2
    print(f"Veri: v2 (tum ozellikler icin: build_features_route.py --route {ROUTE_ID})")

df = pd.read_csv(CSV_PATH)
print(f"Yuklendi: {len(df)} satir, {len(df.columns)} kolon")
print(f"Hedef (travel_time_min): min={df['travel_time_min'].min():.2f}  "
      f"max={df['travel_time_min'].max():.2f}  "
      f"mean={df['travel_time_min'].mean():.2f}  "
      f"std={df['travel_time_min'].std():.2f}")

# ── Kronolojik siralama ───────────────────────────────────────────────────────
df = df.sort_values(["date", "trip_start_time", "from_stop_seq"]).reset_index(drop=True)

# ── Cold-start stratejisi (Adim 5 A/B: scheduled | none | hist) ───────────────
if "prev_travel_time_min" in df.columns:
    mask0 = df["prev_travel_time_min"] == 0.0
    n0 = int(mask0.sum())
    if COLDSTART == "scheduled":
        df.loc[mask0, "prev_travel_time_min"] = df.loc[mask0, "scheduled_travel_min"]
    elif COLDSTART == "hist" and "stop_hist_median" in df.columns:
        df.loc[mask0, "prev_travel_time_min"] = df.loc[mask0, "stop_hist_median"]
    # "none": trip-basi 0 olarak birakilir (model is_trip_start ile ayirt eder)
    print(f"  Cold-start [{COLDSTART}]: {n0} trip-basi prev_travel_time_min islendi")

if "prev_speed_mpm" in df.columns and "distance_m" in df.columns:
    df["prev_speed_mpm"] = (
        df["distance_m"] / df["prev_travel_time_min"].clip(lower=0.01)
    ).clip(upper=2000)

TARGET = "travel_time_min"

# ── Ozellik listesi (Adim 2: ablation-destekli feature selection) ─────────────
# 29 -> 16 feature. Cikarilanlar ve gerekceleri:
#   (b) Fazlalik zaman kodlamasi: time_block, hour_sin/cos, dow_sin/cos, day_type
#       — sin/cos sinir agi icindir; agac modelleri ham hour/day_of_week'i zaten boler.
#   (c) Hava: temperature, humidity, precipitation, wind_speed, visibility,
#       weather_cat_enc — ablation: yagissiz veride gurultu, MAE'yi kotulestiriyor.
#   (c) Trafik: congestion_ratio — seyrek (cogu 1.0 dolgu), onem ~0.
LEAN_FEATURES = [
    # Zaman (ham — agac modelleri icin yeterli)
    "hour", "day_of_week",
    # Mekansal
    "from_stop_seq", "to_stop_seq", "distance_m", "stop_progress",
    # Lag / sapma
    "prev_travel_time_min", "prev_deviation",
    "cumul_deviation", "rolling_3_deviation",
    # Tarihsel (train'den)
    "stop_hist_median", "stop_hist_ratio", "prev_speed_mpm",
    # Dwell (v4, GPS turevli)
    "dwell_time_sec", "prev_dwell_time_sec",
    # GTFS imza feature (ablation'da en kritik)
    "scheduled_travel_min",
]

try:
    from scripts.feature_sets import FEATURE_SETS
except ImportError:
    from feature_sets import FEATURE_SETS

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
#    (CSV'deki degerler %80 splitten; CV fold'larinda leakage olurdu)
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

# ── Hedef donusumu (Adim 4: travel vs deviation A/B) ──────────────────────────
#   travel    : log1p(travel)     -> egitim;  expm1(pred)           -> tahmin
#   deviation : travel - scheduled -> egitim; scheduled + pred(clip) -> tahmin
#   Gerekce: scheduled baz cizgiyi tasir; sapma sifir-merkezli, daha duragan.
def to_target(y_raw, s_raw):
    return (y_raw - s_raw) if TARGET_MODE == "deviation" else np.log1p(y_raw)

def from_pred(pred, s_raw):
    out = (s_raw + pred) if TARGET_MODE == "deviation" else np.expm1(pred)
    return np.clip(out, 0, None)

y_train_t = to_target(y_train, sched_train)

print(f"Hedef modu : {TARGET_MODE}")
print(f"Train: {len(y_train)}  Test: {len(y_test)}")

# ── Metrik fonksiyonu ─────────────────────────────────────────────────────────
def evaluate(y_true, y_pred, name):
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2   = r2_score(y_true, y_pred)
    mask = y_true > 0.01
    mape = (np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
            if mask.sum() > 0 else float("nan"))
    return {
        "model"    : name,
        "MAE (dk)" : round(mae,  4),
        "RMSE (dk)": round(rmse, 4),
        "MAPE (%)" : round(mape, 2),
        "R2"       : round(r2,   4),
    }

results = []

# ═══════════════════════════════════════════════════════════════════
if not _args.core_only:
    print(f"\n{'='*65}")
    print("1. BASELINE: Random Forest (orijinal parametreler, log-transform YOK)")
    print(f"{'='*65}")

    rf_base = RandomForestRegressor(
        n_estimators=100, max_depth=10, min_samples_leaf=2,
        random_state=42, n_jobs=-1
    )
    rf_base.fit(X_train, y_train)
    y_pred_base = rf_base.predict(X_test)
    r_base = evaluate(y_test, y_pred_base, "RF Baseline (orijinal)")
    results.append(r_base)
    print(f"MAE={r_base['MAE (dk)']:.4f}  MAPE={r_base['MAPE (%)']:.2f}%  R2={r_base['R2']:.4f}")

# ═══════════════════════════════════════════════════════════════════
print(f"\n{'='*65}")
print("2. IMPROVED: Random Forest (daha iyi parametreler + log-transform)")
print(f"{'='*65}")
print("  n_estimators: 100 -> 300")
print("  max_depth   : 10  -> 15")
print("  min_samples : 2   -> 1")
print("  Hedef       : y   -> log1p(y)")

rf_imp = RandomForestRegressor(
    n_estimators=300,     # 100 -> 300
    max_depth=15,         # 10  -> 15
    min_samples_leaf=1,   # 2   -> 1
    max_features="sqrt",
    random_state=42,
    n_jobs=-1,
)
rf_imp.fit(X_train, y_train_t)
y_pred_rf = from_pred(rf_imp.predict(X_test), sched_test)

r_rf = evaluate(y_test, y_pred_rf, "RF Improved (log-transform)")
results.append(r_rf)
print(f"MAE={r_rf['MAE (dk)']:.4f}  MAPE={r_rf['MAPE (%)']:.2f}%  R2={r_rf['R2']:.4f}")

# Feature importances (top 10)
importances = pd.Series(
    rf_imp.feature_importances_, index=available_features
).sort_values(ascending=False)
print("\n  Top 10 Ozellik Onem Sirasi:")
for feat, imp in importances.head(10).items():
    bar = "#" * int(imp * 50)
    print(f"    {feat:30s} {imp:.4f}  {bar}")

# ═══════════════════════════════════════════════════════════════════
if HAS_XGB:
    print(f"\n{'='*65}")
    print("3. IMPROVED: XGBoost (daha iyi parametreler + log-transform)")
    print(f"{'='*65}")
    print("  n_estimators  : 200 -> 500")
    print("  max_depth     : 6   -> 8")
    print("  learning_rate : 0.05 -> 0.03")
    print("  min_child_wt  : 3   -> 1")
    print("  subsample     : yok -> 0.8")
    print("  Hedef         : y   -> log1p(y)")

    xgb_imp = XGBRegressor(
        n_estimators=500,        # 200 -> 500
        max_depth=8,             # 6   -> 8
        learning_rate=0.03,      # 0.05 -> 0.03
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=1,      # 3   -> 1
        random_state=42,
        verbosity=0,
    )
    xgb_imp.fit(X_train, y_train_t)
    y_pred_xgb = from_pred(xgb_imp.predict(X_test), sched_test)

    r_xgb = evaluate(y_test, y_pred_xgb, "XGBoost Improved (log-transform)")
    results.append(r_xgb)
    print(f"MAE={r_xgb['MAE (dk)']:.4f}  MAPE={r_xgb['MAPE (%)']:.2f}%  R2={r_xgb['R2']:.4f}")

    # Cold-start kirilim: ilk %33 durak (stop_progress<0.33) vs kalan
    sp_test = df["stop_progress"].values[test_mask]
    cs = sp_test < 0.33
    if cs.sum() > 0 and (~cs).sum() > 0:
        cs_mae   = mean_absolute_error(y_test[cs],  y_pred_xgb[cs])
        rest_mae = mean_absolute_error(y_test[~cs], y_pred_xgb[~cs])
        print(f"  Cold-start kirilim: ilk%33 MAE={cs_mae:.4f} (n={int(cs.sum())}) | "
              f"kalan MAE={rest_mae:.4f} | oran={cs_mae/rest_mae:.2f}x")

# ═══════════════════════════════════════════════════════════════════
if not _args.core_only:
    print(f"\n{'='*65}")
    print("4. SEGMENT BAZLI MODEL (Mixture of Experts)")
    print(f"{'='*65}")
    print("  Baslangic duraklari (stop_progress < 0.33): ayri RF modeli")
    print("  Orta duraklar (0.33-0.66)                 : ayri RF modeli")
    print("  Bitis duraklari (>0.66)                   : ayri RF modeli")

    test_df  = df[test_mask].reset_index(drop=True)
    train_df = df[train_mask].reset_index(drop=True)

    y_pred_seg = np.zeros(len(y_test))

    segments = [
        ("Baslangic (0-33%)" , 0.00, 0.33),
        ("Orta (33-66%)"     , 0.33, 0.66),
        ("Bitis (66-100%)"   , 0.66, 1.01),
    ]

    for seg_label, lo, hi in segments:
        tr_mask = ((train_df["stop_progress"] >= lo) &
                   (train_df["stop_progress"] <  hi)).values
        te_mask = ((test_df["stop_progress"]  >= lo) &
                   (test_df["stop_progress"]  <  hi)).values

        n_tr = tr_mask.sum()
        n_te = te_mask.sum()

        if n_tr < 20 or n_te == 0:
            print(f"  {seg_label}: yetersiz veri (train={n_tr}, test={n_te}) -> atlaniyor")
            # Fallback: genel modeli kullan
            y_pred_seg[te_mask] = from_pred(rf_imp.predict(X_test[te_mask]), sched_test[te_mask])
            continue

        X_tr_s = X_train[tr_mask];  y_tr_s = y_train_t[tr_mask]
        X_te_s = X_test[te_mask];   y_te_s = y_test[te_mask]

        rf_seg = RandomForestRegressor(
            n_estimators=200, max_depth=12, min_samples_leaf=1,
            random_state=42, n_jobs=-1
        )
        rf_seg.fit(X_tr_s, y_tr_s)

        y_pred_part = from_pred(rf_seg.predict(X_te_s), sched_test[te_mask])
        y_pred_seg[te_mask] = y_pred_part

        seg_mae = mean_absolute_error(y_te_s, y_pred_part)
        seg_r2  = r2_score(y_te_s, y_pred_part)
        print(f"  {seg_label}: n_test={n_te:5d}  MAE={seg_mae:.4f}  R2={seg_r2:.4f}")

    r_seg = evaluate(y_test, y_pred_seg, "RF Segment Bazli (Mixture of Experts)")
    results.append(r_seg)
    print(f"\n  GENEL: MAE={r_seg['MAE (dk)']:.4f}  MAPE={r_seg['MAPE (%)']:.2f}%  R2={r_seg['R2']:.4f}")

# ═══════════════════════════════════════════════════════════════════
print(f"\n{'='*65}")
print("TAM KARSILASTIRMA TABLOSU")
print(f"{'='*65}")

# Baseline metrikleri ekle — referans degerler SADECE 502 icin gecerli
if ROUTE_ID == 502 and not _args.core_only:
    results.extend([
        {"model": "RF Baseline Ref (from notebook)", "MAE (dk)": 0.4695, "RMSE (dk)": 0.8731,
         "MAPE (%)": 50.22, "R2": 0.3325},
        {"model": "LSTM Baseline Ref",               "MAE (dk)": 0.4138, "RMSE (dk)": 0.6914,
         "MAPE (%)": 42.11, "R2": 0.0484},
    ])

results_df = pd.DataFrame(results).sort_values("MAE (dk)")
print(results_df.to_string(index=False))

# En iyi sonuclar
best_r2  = results_df.loc[results_df["R2"].idxmax()]
best_mae = results_df.loc[results_df["MAE (dk)"].idxmin()]
print(f"\nEn yuksek R2  : {best_r2['model']}  -> R2={best_r2['R2']:.4f}")
print(f"En dusuk MAE  : {best_mae['model']} -> MAE={best_mae['MAE (dk)']:.4f}")

# Baseline'a gore iyilesme (RF Improved) — sadece tam kosumda anlamli
if not _args.core_only:
    print(f"\nRF Improved iyilesmesi vs RF Baseline (0.4695, 50.22%, 0.3325):")
    print(f"  MAE  : {0.4695:.4f} -> {r_rf['MAE (dk)']:.4f}  ({r_rf['MAE (dk)'] - 0.4695:+.4f})")
    print(f"  MAPE : {50.22:.2f}% -> {r_rf['MAPE (%)']:.2f}%  ({r_rf['MAPE (%)'] - 50.22:+.2f}%)")
    print(f"  R2   : {0.3325:.4f} -> {r_rf['R2']:.4f}  ({r_rf['R2'] - 0.3325:+.4f})")

# ── Kaydet ───────────────────────────────────────────────────────────────────
# Hat 502 icin geriye-donuk uyumlu isim; diger hatlar icin route'lu isim
mode_suffix = "" if TARGET_MODE == "travel" else "_deviation"
cs_tag = COLDSTART + ("-ts" if TRIPSTART_FEAT else "")
cs_suffix = "" if cs_tag == "none-ts" else f"_cs-{cs_tag}"   # none-ts = Adim 5 default
fs_suffix = "" if FEATURE_SET == "full" else f"_fs-{FEATURE_SET}"
cv_suffix = "" if _args.train_end_day is None else f"_cv{_args.train_end_day}"
suffix = ("" if ROUTE_ID == 502 else f"_route_{ROUTE_ID}") + mode_suffix + cs_suffix + fs_suffix + cv_suffix
out_path = os.path.join(RESULTS_DIR, "tables", f"improved_ml_results{suffix}.csv")
results_df.to_csv(out_path, index=False)
print(f"\nSonuclar kaydedildi: {out_path}")

# ── Per-segment tahmin kaydi (SCI: effect size / CI / kirilim analizleri) ─────
if _args.save_preds:
    META = ["date", "bus_id", "trip_start_time", "arrival_timestamp",
            "hour", "day_of_week", "day_type", "yon",
            "from_stop_seq", "to_stop_seq", "segments_into_trip", "is_trip_start",
            "stop_progress", "distance_m", "scheduled_travel_min",
            "weather_cat_enc", "precipitation"]
    # bus_id + trip_start_time: trip-level aggregation icin trip anahtari
    # trip anahtari = (date, bus_id, yon, trip_start_time)
    pred_df = df.loc[test_mask, [c for c in META if c in df.columns]].copy()
    pred_df["y_true"] = y_test

    # Naive (GTFS) baseline: tahmin = tarife
    pred_df["pred_naive"] = sched_test

    # Historical Average baseline: train'den saat x gun_tipi x durak ortalamasi
    tr = df[train_mask]
    ha = tr.groupby(["hour", "day_type", "from_stop_seq"])["travel_time_min"].mean()
    keys = list(zip(pred_df["hour"], pred_df["day_type"], pred_df["from_stop_seq"]))
    pred_df["pred_histavg"] = pd.Series(keys, index=pred_df.index).map(ha)
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
