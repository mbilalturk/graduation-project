"""
Feature Engineering v4 — Dwell Time
=====================================
route_502_features_v3.csv -> route_502_features_v4.csv

Yeni eklenen özellikler:
  - dwell_time_sec   : Otobüsün bu durağa varışından ayrılışına kadar geçen süre (saniye).
                       bus_positions tablosunda aynı durakta (distance <= DWELL_RADIUS_M)
                       ardışık GPS kayıtlarının toplam süresi olarak hesaplanır.
  - prev_dwell_time_sec : Trip içindeki bir önceki durağın dwell süresi.
                          Sıradaki segmentin tahminine katkı sağlar.

Hesaplama yöntemi:
  - GPS polling aralığı ~30-32 saniye.
  - Otobüs durağa DWELL_RADIUS_M (50m) mesafede olduğu sürece "durağında" sayılır.
  - İlk ve son GPS kaydı arasındaki süre dwell_time_sec olarak alınır.
  - 10 saniyeden kısa bekleme "geçiş" sayılarak 0 atanır (stop-express hatlar).
  - 600 saniyeden (10 dk) uzun bekleme uç değer olarak 600'e kırpılır.

Kullanım:
    cd scripts
    python add_dwell_features.py
"""

import os
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# --- Yapılandırma ---
DWELL_RADIUS_M = 50       # Bu mesafe içindeyse "durakta" sayılır
MIN_DWELL_SEC  = 10       # Bunun altı geçiş kabul edilir → 0
MAX_DWELL_SEC  = 600      # Aykırı değer kırpma üst sınırı (~10 dk)

# --- Dosya yolları ---
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DB_PATH      = os.path.join(PROJECT_ROOT, "data_collector", "collected_data", "route_502_realtime.db")
CSV_V3       = os.path.join(PROJECT_ROOT, "collected_data", "route_502_features_v3.csv")
CSV_V4       = os.path.join(PROJECT_ROOT, "collected_data", "route_502_features_v4.csv")

print("=" * 60)
print("Feature Engineering v4 — Dwell Time")
print("=" * 60)
print(f"Veritabanı : {DB_PATH}")
print(f"Kaynak     : {CSV_V3}")
print(f"Hedef      : {CSV_V4}")


# ---------------------------------------------------------------------------
# 1. bus_positions'dan dwell time tablosu hesapla
# ---------------------------------------------------------------------------

def compute_dwell_table(db_path: str) -> pd.DataFrame:
    """
    bus_positions tablosundan her (otobus_id, durak_seq, tarih, saat) için
    dwell_time_sec hesaplar.

    Döndürülen DataFrame kolonları:
        otobus_id, nearest_stop_seq, date, approx_hour, dwell_time_sec
    """
    print("\n[1/4] bus_positions tablosu okunuyor...")
    conn = sqlite3.connect(db_path)
    df_pos = pd.read_sql_query(
        """
        SELECT timestamp, otobus_id, nearest_stop_seq, distance_to_nearest_m
        FROM bus_positions
        WHERE distance_to_nearest_m <= ?
        ORDER BY otobus_id, timestamp
        """,
        conn,
        params=(DWELL_RADIUS_M,),
    )
    conn.close()
    print(f"  {len(df_pos):,} kayıt yüklendi (distance <= {DWELL_RADIUS_M}m).")

    df_pos["timestamp"] = pd.to_datetime(df_pos["timestamp"])
    df_pos["date"] = df_pos["timestamp"].dt.date.astype(str)

    # --- Her (bus, durak, gün) için ardışık oturumları bul ---
    # Ardışık kayıtlar arasında 3 dakikadan fazla boşluk varsa yeni oturum
    GAP_SEC = 180
    records = []

    print("[2/4] Dwell oturumları hesaplanıyor...")
    groups = df_pos.groupby(["otobus_id", "nearest_stop_seq", "date"], sort=False)
    for (bus_id, stop_seq, date), grp in groups:
        grp = grp.sort_values("timestamp")
        timestamps = grp["timestamp"].values

        if len(timestamps) == 0:
            continue

        session_start = timestamps[0]
        session_end   = timestamps[0]

        for i in range(1, len(timestamps)):
            diff = (timestamps[i] - session_end) / np.timedelta64(1, "s")
            if diff <= GAP_SEC:
                session_end = timestamps[i]
            else:
                # Oturumu kaydet
                dwell = (session_end - session_start) / np.timedelta64(1, "s")
                if dwell >= MIN_DWELL_SEC:
                    dwell = min(dwell, MAX_DWELL_SEC)
                    approx_hour = pd.Timestamp(session_start).hour
                    records.append({
                        "otobus_id":      bus_id,
                        "from_stop_seq":  stop_seq,
                        "date":           date,
                        "approx_hour":    approx_hour,
                        "dwell_time_sec": round(float(dwell), 1),
                    })
                # Yeni oturum
                session_start = timestamps[i]
                session_end   = timestamps[i]

        # Son oturumu kapat
        dwell = (session_end - session_start) / np.timedelta64(1, "s")
        if dwell >= MIN_DWELL_SEC:
            dwell = min(dwell, MAX_DWELL_SEC)
            approx_hour = pd.Timestamp(session_start).hour
            records.append({
                "otobus_id":      bus_id,
                "from_stop_seq":  stop_seq,
                "date":           date,
                "approx_hour":    approx_hour,
                "dwell_time_sec": round(float(dwell), 1),
            })

    dwell_df = pd.DataFrame(records)
    print(f"  {len(dwell_df):,} dwell oturumu tespit edildi.")
    return dwell_df


# ---------------------------------------------------------------------------
# 2. Dwell tablosunu features CSV ile eşleştir
# ---------------------------------------------------------------------------

def merge_dwell(df_feat: pd.DataFrame, dwell_df: pd.DataFrame) -> pd.DataFrame:
    """
    features CSV'sindeki her satır için en yakın dwell oturumunu eşleştirir.
    Eşleştirme: (otobus_id, from_stop_seq, date, hour) tam uyumu önce dener,
    gün+durak medyanına geri döner.
    """
    print("[3/4] Dwell feature'ları features CSV ile birleştiriliyor...")

    df_feat = df_feat.copy()
    df_feat["bus_id"] = df_feat["bus_id"].astype(int)
    df_feat["from_stop_seq"] = df_feat["from_stop_seq"].astype(int)

    # --- Tam eşleştirme: bus + durak + gün + saat ---
    dwell_exact = (
        dwell_df
        .groupby(["otobus_id", "from_stop_seq", "date", "approx_hour"])["dwell_time_sec"]
        .mean()
        .reset_index()
        .rename(columns={"otobus_id": "bus_id", "approx_hour": "hour"})
    )
    dwell_exact["bus_id"]        = dwell_exact["bus_id"].astype(int)
    dwell_exact["from_stop_seq"] = dwell_exact["from_stop_seq"].astype(int)
    dwell_exact["dwell_time_sec"] = dwell_exact["dwell_time_sec"].round(1)

    df_feat = df_feat.merge(
        dwell_exact, on=["bus_id", "from_stop_seq", "date", "hour"], how="left"
    )

    # --- Geri dönüş: durak + gün medyanı ---
    stop_day_med = (
        dwell_df
        .groupby(["from_stop_seq", "date"])["dwell_time_sec"]
        .median()
        .reset_index()
        .rename(columns={"dwell_time_sec": "_dwell_day_med"})
    )
    stop_day_med["from_stop_seq"] = stop_day_med["from_stop_seq"].astype(int)
    df_feat = df_feat.merge(stop_day_med, on=["from_stop_seq", "date"], how="left")

    # --- Global medyan ---
    global_dwell_med = dwell_df["dwell_time_sec"].median()
    print(f"  Global dwell medyanı: {global_dwell_med:.1f} sn")

    # Eksik değerleri kademeli doldur
    df_feat["dwell_time_sec"] = (
        df_feat["dwell_time_sec"]
        .fillna(df_feat["_dwell_day_med"])
        .fillna(global_dwell_med)
        .round(1)
    )
    df_feat.drop(columns=["_dwell_day_med"], inplace=True)

    missing_pct = df_feat["dwell_time_sec"].isna().mean() * 100
    print(f"  dwell_time_sec eksik oranı: %{missing_pct:.1f}")

    # --- prev_dwell_time_sec: trip içinde bir önceki durağın dwell süresi ---
    df_feat = df_feat.sort_values(["date", "bus_id", "yon", "trip_start_time", "from_stop_seq"])
    trip_grp = df_feat.groupby(["date", "bus_id", "yon", "trip_start_time"], sort=False)
    df_feat["prev_dwell_time_sec"] = (
        trip_grp["dwell_time_sec"]
        .transform(lambda x: x.shift(1).fillna(global_dwell_med))
        .round(1)
    )

    df_feat = df_feat.sort_values(["date", "trip_start_time", "from_stop_seq"]).reset_index(drop=True)
    return df_feat


# ---------------------------------------------------------------------------
# Ana akış
# ---------------------------------------------------------------------------

if not os.path.exists(CSV_V3):
    raise FileNotFoundError(f"v3 CSV bulunamadı: {CSV_V3}")

df_feat = pd.read_csv(CSV_V3)
print(f"\nv3 CSV yüklendi: {df_feat.shape[0]:,} satır, {df_feat.shape[1]} kolon")

dwell_df = compute_dwell_table(DB_PATH)
df_feat  = merge_dwell(df_feat, dwell_df)

# --- Özet istatistik ---
print("\n[4/4] Yeni özellik özeti:")
for col in ["dwell_time_sec", "prev_dwell_time_sec"]:
    s = df_feat[col]
    print(f"  {col:25s}  mean={s.mean():7.2f}  std={s.std():7.2f}  "
          f"min={s.min():.1f}  max={s.max():.1f}  NaN={s.isna().sum()}")

df_feat.to_csv(CSV_V4, index=False)
print(f"\nKaydedildi : {CSV_V4}")
print(f"Boyut      : {df_feat.shape[0]:,} satır x {df_feat.shape[1]} kolon")
print(f"Eklenen    : dwell_time_sec, prev_dwell_time_sec  (+2 kolon)")
