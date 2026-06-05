# Plan: Cold-Start Resolution and DL Statistical Significance Testing

**Project Type:** BACKEND (Machine Learning Pipeline)

## Success Criteria
- LSTM model retrained with corrected cold-start features (MAE $\le 0.41$ minutes, ideally lower).
- ML models retrained with corrected cold-start features (MAE $\le 0.47$ minutes).
- `notebooks/evaluation.ipynb` successfully integrates `LSTM` (and `GRU` if available) predictions into paired statistical tests.
- Re-generated results tables and plots saved in `results/`.

## Tech Stack
- Python 3.x
- PyTorch (Deep Learning)
- Scikit-learn, XGBoost (Traditional ML)
- Pandas, NumPy (Data Processing)
- Jupyter (Notebook Evaluation)

## Task Breakdown

### Task 1: Cold-Start Feature Refinement in LSTM Training Pipeline
- **Agent:** `backend-specialist`
- **Skills:** `python-patterns`, `clean-code`
- **Priority:** P0
- **Dependencies:** None
- **INPUT:** `collected_data/route_502_features_v4.csv` & `scripts/improved_lstm.py`
- **OUTPUT:** Retrained `models/improved_lstm.pt` using corrected features.
- **VERIFY:** Run `python scripts/improved_lstm.py` and verify that `prev_travel_time_min` values of `0.0` are filled with `scheduled_travel_minutes` during training, and the model saves successfully with MAE $\le 0.41$.

### Task 2: Cold-Start Feature Refinement in ML Training Pipeline
- **Agent:** `backend-specialist`
- **Skills:** `python-patterns`, `clean-code`
- **Priority:** P0
- **Dependencies:** None
- **INPUT:** `collected_data/route_502_features_v4.csv` & `scripts/improved_ml.py`
- **OUTPUT:** Retrained ML results.
- **VERIFY:** Run `python scripts/improved_ml.py` and verify models train successfully.

### Task 3: Statistical Significance Integration in Evaluation Notebook
- **Agent:** `backend-specialist`
- **Skills:** `python-patterns`, `clean-code`
- **Priority:** P1
- **Dependencies:** Task 1, Task 2
- **INPUT:** `notebooks/evaluation.ipynb` & `models/improved_lstm.pt`
- **OUTPUT:** Modified `notebooks/evaluation.ipynb` with deep learning models included in testing.
- **VERIFY:** Run the notebook cells and verify that `results/tables/statistical_tests.csv` and `results/tables/all_model_results.csv` contain `LSTM` statistical significance metrics.

---

## Phase X: Verification Checklist
- [ ] Retrain LSTM: `python scripts/improved_lstm.py` ✅ Pass
- [ ] Retrain ML: `python scripts/improved_ml.py` ✅ Pass
- [ ] Run evaluation: Execute all cells in `notebooks/evaluation.ipynb` ✅ Pass
- [ ] Verify metrics: Check that all CSVs in `results/tables/` are successfully updated.
