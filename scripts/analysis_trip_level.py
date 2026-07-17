"""
Trip-level aggregation (Kaya & Kalay adil kiyasi): segment tahminleri trip
boyunca kumulatif toplanir -> k durak ilerisi icin ucdan uca varis MAE'si.

Yontem notu (makaleye tasinacak): her segment tahmini, o segmente kadarki
GERCEKLESEN gecmisin lag feature'lariyla kosullanmistir (one-step-ahead).
Kumulatif toplam bu yuzden coklu-adim tahminin iyimser (alt sinir) kestirimi
sayilmalidir; ayni kosullar naive (GTFS) icin de gecerli oldugundan kiyas
ic tutarlidir.

Trip anahtari: (date, bus_id, yon, trip_start_time).
Ardisikligi bozuk tripler (test penceresi trip ortasindan kesmis ya da segment
atlanmis: segments_into_trip 0'dan baslamiyor veya ardisik degil) analiz disi
birakilir ve sayisi LOGLANIR (sessiz eleme yok).

Kullanim: PYTHONPATH=. python scripts/analysis_trip_level.py
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

HORIZONS = [1, 3, 5, 10]          # + "end" (trip sonu)
C_BLUE, C_GRAY = "#2a78d6", "#8a8a8a"

df = pd.read_csv(os.path.join(PRED_DIR, "route_502_test_predictions.csv"))
print(f"Yuklendi: {len(df)} test segmenti")

rows = []
n_trips_total = 0
n_dropped = 0
for key, g in df.groupby(["date", "bus_id", "yon", "trip_start_time"]):
    n_trips_total += 1
    g = g.sort_values("segments_into_trip")
    s = g["segments_into_trip"].values
    if s[0] != 0 or not np.array_equal(s, np.arange(len(s))):
        n_dropped += 1          # trip bastan gozlenmemis ya da segment atlanmis
        continue
    cum_true  = g["y_true"].cumsum().values
    cum_xgb   = g["pred_xgb_improved"].cumsum().values
    cum_naive = g["pred_naive"].cumsum().values
    seg_err   = (g["pred_xgb_improved"] - g["y_true"]).abs().values
    for k in HORIZONS:
        if k <= len(g):
            rows.append({"date": key[0], "horizon": str(k),
                         "err_xgb":   abs(cum_xgb[k-1]   - cum_true[k-1]),
                         "err_naive": abs(cum_naive[k-1] - cum_true[k-1]),
                         "cum_true":  cum_true[k-1],
                         "sum_seg_err": seg_err[:k].sum()})
    rows.append({"date": key[0], "horizon": "end",
                 "err_xgb":   abs(cum_xgb[-1]   - cum_true[-1]),
                 "err_naive": abs(cum_naive[-1] - cum_true[-1]),
                 "cum_true":  cum_true[-1],
                 "sum_seg_err": seg_err.sum(),
                 "trip_len": len(g)})

trips = pd.DataFrame(rows)
n_used = n_trips_total - n_dropped
print(f"Trip: {n_trips_total} toplam, {n_dropped} atildi (bastan gozlenmemis/atlamali), "
      f"{n_used} kullanildi")
mean_len = trips[trips.horizon == "end"]["trip_len"].mean()
print(f"Ortalama trip uzunlugu (kullanilan): {mean_len:.1f} segment")
print("NOT: k-horizon alt kumesi = trip'in ILK k segmenti bastan gozlenen tripler; "
      "bu alt kume genelden daha uzun/yavas segmentler icerir (secim etkisi). "
      "Bu yuzden lineer referans, ayni alt kumenin kendi per-segment hatasindan kurulur "
      "(sum_seg_err), genel 0.43'ten degil.")

out_rows = []
for h in [str(k) for k in HORIZONS] + ["end"]:
    sub = trips[trips.horizon == h]
    if len(sub) < 30:
        print(f"  horizon {h}: n={len(sub)} < 30 — atlandi")
        continue
    lo, hi = day_block_bootstrap_ci(sub, lambda s: s["err_xgb"].mean(), n_boot=1000)
    out_rows.append({"horizon_stops": h, "n_trips": len(sub),
                     "mae_xgb": round(sub["err_xgb"].mean(), 4),
                     "mae_ci_lo": round(lo, 4), "mae_ci_hi": round(hi, 4),
                     "mae_naive": round(sub["err_naive"].mean(), 4),
                     # ayni alt kumede kansellasyonsuz ust sinir (per-seg hatalarin toplami)
                     "linear_ref": round(sub["sum_seg_err"].mean(), 4),
                     # gorelilestirme: kumulatif MAE / ortalama gercek varis suresi
                     "mean_true_min": round(sub["cum_true"].mean(), 4),
                     "rel_err_pct": round(100 * sub["err_xgb"].mean()
                                          / sub["cum_true"].mean(), 1)})
tab = pd.DataFrame(out_rows)
tab_path = os.path.join(PROJECT_ROOT, "results", "tables", "trip_level_mae_route_502.csv")
tab.to_csv(tab_path, index=False)
print(f"\n{tab.to_string(index=False)}\n-> {tab_path}")

# ── Figur: MAE vs horizon; lineer referans = ayni alt kumenin per-seg hata toplami
num = tab[tab.horizon_stops != "end"].copy()
num["k"] = num["horizon_stops"].astype(int)
num = num.sort_values("k")

fig, ax = plt.subplots(figsize=(8, 4.8))
ks = num["k"].values
ax.plot(ks, num["linear_ref"], ":", color=C_GRAY, linewidth=1.5,
        label="no-cancellation bound (sum of segment errors)")
ax.plot(ks, num["mae_naive"], "s--", color=C_GRAY, linewidth=2, markersize=6,
        label="Naive (GTFS schedule)")
y = num["mae_xgb"].values
yerr = np.vstack([y - num["mae_ci_lo"].values, num["mae_ci_hi"].values - y])
ax.errorbar(ks, y, yerr=yerr, fmt="o-", color=C_BLUE, linewidth=2,
            markersize=6, capsize=3, label="XGBoost (accumulated)")
ax.set_xlabel("Prediction horizon (stops ahead)")
ax.set_ylabel("Cumulative arrival-time MAE (minutes)")
ax.set_title("Trip-level arrival error vs. horizon (route 502)", fontsize=11)
ax.set_xticks(ks)
ax.legend(frameon=False)
ax.grid(axis="y", alpha=0.25, linewidth=0.8)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig_path = os.path.join(PROJECT_ROOT, "results", "figures",
                        "trip_level_error_vs_horizon.png")
fig.savefig(fig_path, dpi=200); plt.close(fig)
print(f"-> {fig_path}")
