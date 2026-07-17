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
