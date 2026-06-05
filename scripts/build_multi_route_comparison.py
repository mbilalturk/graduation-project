"""
Multi-Route Karsilastirma Tablosu
=================================
3 hat (502, 268, 565) icin XGBoost Improved + Improved LSTM sonuclarini
tek ozet tabloda birlestirir. Genelleme kanitini gosterir: ayni yontem
farkli hat profillerinde de calisir mi?

Girdi:
  results/tables/improved_ml_results[_route_<RID>].csv
  results/tables/improved_lstm_results[_route_<RID>].csv
  collected_data/route_<RID>_features_v4.csv   (veri profili icin)

Cikti:
  results/tables/multi_route_comparison.csv

Kullanim:
    python build_multi_route_comparison.py
"""

import os
import pandas as pd
import numpy as np

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
TABLES_DIR   = os.path.join(PROJECT_ROOT, "results", "tables")
DATA_DIR     = os.path.join(PROJECT_ROOT, "collected_data")

ROUTES = [502, 268, 565]
ROUTE_LABELS = {
    502: "502 (Cengizhan-Halkapinar)",
    268: "268",
    565: "565",
}

XGB_NAME  = "XGBoost Improved (log-transform)"
LSTM_NAME = "Improved LSTM"


def _suffix(rid):
    return "" if rid == 502 else f"_route_{rid}"


def _get_row(csv_path, model_name):
    if not os.path.exists(csv_path):
        return None
    df = pd.read_csv(csv_path)
    hit = df[df["model"] == model_name]
    return hit.iloc[0] if len(hit) else None


def _data_profile(rid):
    p = os.path.join(DATA_DIR, f"route_{rid}_features_v4.csv")
    if not os.path.exists(p):
        return {"N": np.nan, "mean": np.nan, "std": np.nan, "cv": np.nan}
    df = pd.read_csv(p, usecols=["travel_time_min"])
    m, s = df["travel_time_min"].mean(), df["travel_time_min"].std()
    return {"N": len(df), "mean": round(m, 3), "std": round(s, 3),
            "cv": round(s / m, 3) if m else np.nan}


rows = []
for rid in ROUTES:
    prof = _data_profile(rid)
    ml_csv   = os.path.join(TABLES_DIR, f"improved_ml_results{_suffix(rid)}.csv")
    lstm_csv = os.path.join(TABLES_DIR, f"improved_lstm_results{_suffix(rid)}.csv")

    xgb  = _get_row(ml_csv, XGB_NAME)
    lstm = _get_row(lstm_csv, LSTM_NAME)

    rows.append({
        "Hat":                ROUTE_LABELS[rid],
        "Segment (N)":        prof["N"],
        "Ort. sure (dk)":     prof["mean"],
        "Std (dk)":           prof["std"],
        "CV (std/mean)":      prof["cv"],
        "XGBoost MAE (dk)":   round(xgb["MAE (dk)"], 4)  if xgb  is not None else np.nan,
        "XGBoost MAPE (%)":   round(xgb["MAPE (%)"], 2)  if xgb  is not None else np.nan,
        "XGBoost R2":         round(xgb["R2"], 4)        if xgb  is not None else np.nan,
        "LSTM MAE (dk)":      round(lstm["MAE (dk)"], 4) if lstm is not None else np.nan,
        "LSTM MAPE (%)":      round(lstm["MAPE (%)"], 2) if lstm is not None else np.nan,
        "LSTM R2":            round(lstm["R2"], 4)       if lstm is not None else np.nan,
    })

out_df = pd.DataFrame(rows)
out_path = os.path.join(TABLES_DIR, "multi_route_comparison.csv")
out_df.to_csv(out_path, index=False)

print("=" * 70)
print("Multi-Route Karsilastirma (XGBoost Improved + Improved LSTM)")
print("=" * 70)
print(out_df.to_string(index=False))
print(f"\nKaydedildi: {out_path}")

# Ozet yorum
valid_xgb = out_df["XGBoost R2"].dropna()
if len(valid_xgb) >= 2:
    print(f"\nXGBoost R2 araligi: {valid_xgb.min():.3f} – {valid_xgb.max():.3f}")
    print(f"XGBoost MAE araligi: {out_df['XGBoost MAE (dk)'].min():.3f} – "
          f"{out_df['XGBoost MAE (dk)'].max():.3f} dk")
    print("Yontem 3 hatta da tutarli calisiyorsa -> genelleme kaniti saglanir.")
