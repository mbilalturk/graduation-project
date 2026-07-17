"""
Hata kirilim analizleri (hoca madde 8-9): saatlik egri, zaman dilimi,
hafta ici/sonu, segment uzunlugu ceyrekleri, hava (yagmur), yon.
Birden cok predictions dosyasi verilirse satirlar poollanir
(rolling-origin CV fold'lari ayrik test pencereleri oldugundan gecerli).

Yagmur fold-ici kontrol (pooled modda): rolling-origin'de erken fold'larin
train penceresi kucuk -> hatalari yapisal olarak yuksek; yagisli gunler de
cogunlukla bu donemde. Pooled rainy-clear farki bu etkiyle karisir; kontrol
olarak fark her fold KENDI ICINDE hesaplanir, fold'lar arasi mean +- std verilir.

Kullanim:
  PYTHONPATH=. python scripts/analysis_error_slices.py \
      --preds results/predictions/route_502_test_predictions.csv
  # yagmur icin genis orneklem (CV fold'lari poollanmis):
  PYTHONPATH=. python scripts/analysis_error_slices.py \
      --preds "results/predictions/route_502_test_predictions_cv*.csv" --tag pooled
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

# Palet (dataviz skill; kategorik slot 1 = mavi, tek seri figurlerde ana renk)
C_BLUE = "#2a78d6"
C_RED  = "#e34948"
GRID   = dict(alpha=0.25, linewidth=0.8)

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

# ── Figurler (tek model: XGBoost; CI bantli; tek seri -> legend gereksiz) ─────
def _ci_plot(sub, x_labels, title, xlabel, out_name, rotate=0):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(sub))
    y = sub["mae_xgb"].values
    yerr = np.vstack([y - sub["mae_ci_lo"].values, sub["mae_ci_hi"].values - y])
    ax.errorbar(x, y, yerr=yerr, fmt="o-", color=C_BLUE, linewidth=2,
                markersize=5, capsize=3, ecolor=C_BLUE, elinewidth=1.2)
    ax.set_xticks(x); ax.set_xticklabels(x_labels, rotation=rotate)
    ax.set_ylabel("MAE (minutes)"); ax.set_xlabel(xlabel)
    ax.set_title(title, fontsize=11)
    ax.grid(axis="y", **GRID)
    ax.spines[["top", "right"]].set_visible(False)
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
