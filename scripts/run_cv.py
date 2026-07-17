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
