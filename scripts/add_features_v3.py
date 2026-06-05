"""
Feature Engineering v3
=======================
route_502_features_v2.csv -> route_502_features_v3.csv

Yeni eklenen ozellikler (R2 ve MAPE iyilestirmesi icin):
  - deviation_minutes      : gercek sure - planlanmis sure
  - cumul_deviation        : trip icinde o ana kadarki kumulatif sapma (simdiki segment haric)
  - rolling_3_deviation    : son 3 segmentin ortalama sapmasi (simdiki haric)
  - stop_hist_median       : (durak, yon) bazli tarihsel medyan sure (egitim verisinden)
  - stop_hist_ratio        : (durak, yon) bazli gercek/planlanmis sure orani medyani
  - prev_speed_mpm         : bir onceki segmentin ortalama hizi (metre/dakika)

Kullanim:
    cd scripts
    python add_features_v3.py
"""

import os
import pandas as pd
import numpy as np

# --- Yollar ---
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
CSV_V2       = os.path.join(PROJECT_ROOT, "collected_data", "route_502_features_v2.csv")
CSV_V3       = os.path.join(PROJECT_ROOT, "collected_data", "route_502_features_v3.csv")

print("=" * 60)
print("Feature Engineering v3")
print("=" * 60)
print(f"Kaynak : {CSV_V2}")
print(f"Hedef  : {CSV_V3}")

if not os.path.exists(CSV_V2):
    raise FileNotFoundError(f"v2 CSV bulunamadi: {CSV_V2}")

# --- Veri yukle ---
df = pd.read_csv(CSV_V2)
print(f"\nYuklendi: {len(df)} satir, {len(df.columns)} kolon")

# --- 1. Kronolojik siralama (baseline ile ayni) ---
df = df.sort_values(["date", "trip_start_time", "from_stop_seq"]).reset_index(drop=True)

# --- 2. deviation_minutes ---
if "deviation_minutes" not in df.columns:
    df["deviation_minutes"] = df["travel_time_min"] - df["scheduled_travel_min"]
print("  deviation_minutes: tamamlandi")

# --- 3. Egitim/test ayirimi (data leakage'i onlemek icin stop istatistikleri
#         yalnizca egitim bolumunden hesaplanir) ---
split_idx = int(len(df) * 0.8)
train_df  = df.iloc[:split_idx].copy()
print(f"  Train bolumu: {split_idx} satir (istatistikler buradan hesaplanir)")

# --- 4. Durak bazli tarihsel medyan sure ---
stop_med = (
    train_df.groupby(["from_stop_seq", "yon"])["travel_time_min"]
    .median()
    .reset_index()
    .rename(columns={"travel_time_min": "stop_hist_median"})
)
global_med = train_df["travel_time_min"].median()
df = df.merge(stop_med, on=["from_stop_seq", "yon"], how="left")
df["stop_hist_median"] = df["stop_hist_median"].fillna(global_med)
print(f"  stop_hist_median: tamamlandi (global medyan={global_med:.3f})")

# --- 5. Durak bazli gercek/planlanmis sure orani ---
train_df["_ratio"] = (
    train_df["travel_time_min"] / train_df["scheduled_travel_min"].clip(lower=0.01)
)
stop_ratio = (
    train_df.groupby(["from_stop_seq", "yon"])["_ratio"]
    .median()
    .reset_index()
    .rename(columns={"_ratio": "stop_hist_ratio"})
)
df = df.merge(stop_ratio, on=["from_stop_seq", "yon"], how="left")
df["stop_hist_ratio"] = df["stop_hist_ratio"].fillna(1.0)
print("  stop_hist_ratio: tamamlandi")

# --- 6. Trip bazli ozellikler ---
# Trip icinde siralamayi from_stop_seq'e gore yapiyoruz
df = df.sort_values(["date", "bus_id", "yon", "trip_start_time", "from_stop_seq"])
trip_grp = df.groupby(["date", "bus_id", "yon", "trip_start_time"], sort=False)

# Kumulatif sapma (bir onceki segmente kadar — shift(1) ile simdiki haric tutulur)
df["cumul_deviation"] = trip_grp["deviation_minutes"].transform(
    lambda x: x.shift(1).fillna(0).cumsum()
)

# Son 3 segmentin ortalama sapmasi (rolling, simdiki haric)
df["rolling_3_deviation"] = trip_grp["deviation_minutes"].transform(
    lambda x: x.shift(1).rolling(3, min_periods=1).mean().fillna(0)
)
print("  cumul_deviation & rolling_3_deviation: tamamlandi")

# --- 7. Bir onceki segmentin hiz tahmini (metre/dakika) ---
df["prev_speed_mpm"] = (
    df["distance_m"] / df["prev_travel_time_min"].clip(lower=0.01)
).clip(upper=2000)          # Max ~120 km/h = 2000 m/dk ile sinirla
print("  prev_speed_mpm: tamamlandi")

# --- 8. Kronolojik siraya geri don ---
df = df.sort_values(["date", "trip_start_time", "from_stop_seq"]).reset_index(drop=True)

# --- NaN kontrolu ---
new_feats = ["deviation_minutes", "cumul_deviation", "rolling_3_deviation",
             "stop_hist_median", "stop_hist_ratio", "prev_speed_mpm"]
print("\nYeni ozellik ozeti:")
for col in new_feats:
    nan_count = df[col].isna().sum()
    print(f"  {col:30s}  mean={df[col].mean():8.4f}  std={df[col].std():8.4f}  NaN={nan_count}")
    if nan_count > 0:
        df[col] = df[col].fillna(0)
        print(f"    -> {nan_count} NaN deger 0 ile dolduruldu")

# --- Kaydet ---
df.to_csv(CSV_V3, index=False)
print(f"\nKaydedildi: {CSV_V3}")
print(f"Boyut     : {df.shape[0]} satir x {df.shape[1]} kolon")
print(f"Eklenen kolon sayisi: {df.shape[1] - (df.shape[1] - len(new_feats))} (toplam {len(new_feats)} yeni ozellik)")
