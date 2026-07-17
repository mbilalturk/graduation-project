"""
Trip-progress hata egrisi (hoca madde 2): MAE vs segments_into_trip.
Full model + C0 (baglamsiz) + C1 (+GTFS) egrileri ust uste:
cold-start bolgesinde hatanin neden yuksek oldugu ve baglamin
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

# Palet (dataviz skill; kategorik slot sirasi sabit)
C_FULL = "#2a78d6"   # slot 1 mavi
C_C0   = "#1baf7a"   # slot 2 aqua
C_C1   = "#eda100"   # slot 3 sari
C_ZONE = "#e34948"   # cold-start golgesi (kirmizi, dusuk alpha)


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
ax.axvspan(-0.5, 1.5, alpha=0.10, color=C_ZONE,
           label="cold-start zone (lag features empty)")
ax.plot(x, tab["mae_xgb_c0"], "s--", color=C_C0, linewidth=2, markersize=6,
        label="C0: no context (temporal+spatial)")
ax.plot(x, tab["mae_xgb_c1"], "^--", color=C_C1, linewidth=2, markersize=6,
        label="C1: + GTFS schedule")
ax.plot(x, tab["mae_xgb_full"], "o-", color=C_FULL, linewidth=2, markersize=6,
        label="Full model")
ax.fill_between(x, tab["mae_ci_lo"], tab["mae_ci_hi"], alpha=0.18, color=C_FULL,
                linewidth=0)
ax.set_xlabel("Segments into trip")
ax.set_ylabel("MAE (minutes)")
ax.set_title("Prediction error vs. trip progress (XGBoost, route 502)", fontsize=11)
labels = [str(int(v)) if v < MAX_POS else f"{MAX_POS}+" for v in x]
ax.set_xticks(x); ax.set_xticklabels(labels)
ax.legend(frameon=False)
ax.grid(axis="y", alpha=0.25, linewidth=0.8)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig_path = os.path.join(PROJECT_ROOT, "results", "figures", "error_by_trip_progress.png")
fig.savefig(fig_path, dpi=200); plt.close(fig)
print(f"-> {fig_path}")
