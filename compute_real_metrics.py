"""
compute_real_metrics.py
Run this on your Mac inside ~/github/semdriftbd to get REAL measured
Precision / Recall / F1 for every method.

USAGE:
    cd ~/github/semdriftbd && source venv/bin/activate
    python3 compute_real_metrics.py
"""

import os, json
import numpy as np
import pandas as pd

# ── GROUND TRUTH ──────────────────────────────────────────────────────────────
# Edit this set. These are the pairs YOU consider true drift events.
# Your paper documents Pair 9 (May 2017 entertainment surge).
# The others below are based on your alert list — verify each one.
GROUND_TRUTH_DRIFT_PAIRS = {
    4,   # Feb-Mar 2017
    5,   # Mar 2017
    8,   # Apr-May 2017
    9,   # May 2017 - PEAK - entertainment surge (BERTopic documented)
    16,  # Aug 2017
    24,  # Dec 2017
    32,  # Apr 2018
}
TOTAL_PAIRS = 36

def get_adaptive_alerts(scores, pair_nums, z_mult=2.0, w=5):
    alerts = set()
    rolling = []
    for i, s in enumerate(scores):
        if len(rolling) >= 3:
            prev = rolling[-w:]
            mu, sigma = np.mean(prev), np.std(prev)
            thr = mu + z_mult * sigma
            if s > thr and sigma > 1e-3:
                alerts.add(int(pair_nums[i]))
        rolling.append(s)
    return alerts

def metrics(pred_set, truth_set, total):
    tp = sorted(pred_set & truth_set)
    fp = sorted(pred_set - truth_set)
    fn = sorted(truth_set - pred_set)
    P  = len(tp)/(len(tp)+len(fp)) if (len(tp)+len(fp)) else 0.0
    R  = len(tp)/(len(tp)+len(fn)) if (len(tp)+len(fn)) else 0.0
    F1 = 2*P*R/(P+R) if (P+R) else 0.0
    return {"TP":tp,"FP":fp,"FN":fn,"n_TP":len(tp),"n_FP":len(fp),"n_FN":len(fn),
            "precision":round(P,3),"recall":round(R,3),"f1":round(F1,3)}

def main():
    print("="*70)
    print("REAL EVALUATION METRICS — SemDriftBD")
    print("="*70)
    print(f"\nGround-truth pairs ({len(GROUND_TRUTH_DRIFT_PAIRS)}): {sorted(GROUND_TRUTH_DRIFT_PAIRS)}")
    print(f"Total pairs: {TOTAL_PAIRS}\n")

    df_wkcs = pd.read_csv("data/drift_scores_with_alerts.csv").sort_values("pair").reset_index(drop=True)
    df_base = pd.read_csv("data/baseline_comparison.csv").sort_values("pair").reset_index(drop=True)
    pair_nums = df_base["pair"].values

    method_scores = {
        "Cosine Distance":  df_base["cosine"].values,
        "Wasserstein-only": df_base["wasserstein_only"].values,
        "KL-only":          df_base["kl_only"].values,
        "WKCS (ours)":      df_wkcs["wkcs"].values,
    }

    # Show existing alert column
    existing = set(df_wkcs[df_wkcs["alert"]==True]["pair"].values.tolist())
    print(f"Existing WKCS alerts (alert==True column): {sorted(existing)}\n")

    rows = []
    hitlists = {}
    for name, scores in method_scores.items():
        alerts = get_adaptive_alerts(scores, pair_nums)
        m = metrics(alerts, GROUND_TRUTH_DRIFT_PAIRS, TOTAL_PAIRS)
        hitlists[name] = m
        print(f"{'─'*60}")
        print(f"METHOD: {name}")
        print(f"  Alerts fired : {sorted(alerts)}")
        print(f"  TP (correct) : {m['TP']}")
        print(f"  FP (wrong)   : {m['FP']}")
        print(f"  FN (missed)  : {m['FN']}")
        print(f"  Precision={m['precision']}  Recall={m['recall']}  F1={m['f1']}")
        rows.append({"Method":name,"Alerts":len(alerts),"TP":m["n_TP"],
                     "FP":m["n_FP"],"FN":m["n_FN"],"Precision":m["precision"],
                     "Recall":m["recall"],"F1":m["f1"]})

    print(f"\n{'='*70}")
    print("SUMMARY TABLE — paste into paper Table V")
    print(f"{'='*70}")
    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    out.to_csv("data/real_metrics.csv", index=False)
    with open("data/real_metrics_hitlists.json","w") as f:
        json.dump(hitlists, f, indent=2)
    print(f"\nSaved: data/real_metrics.csv")
    print(f"Saved: data/real_metrics_hitlists.json")

    # Correlation
    print(f"\n{'='*70}")
    print("WKCS CORRELATION WITH BASELINES")
    wkcs_sc = df_wkcs["wkcs"].values[:len(pair_nums)]
    for name, scores in method_scores.items():
        if name=="WKCS (ours)": continue
        r = np.corrcoef(wkcs_sc, scores[:len(wkcs_sc)])[0,1]
        print(f"  WKCS vs {name:<25}: r = {r:.4f}")

    # Weight sensitivity
    ws_path = "data/weight_sensitivity.csv"
    if os.path.exists(ws_path):
        print(f"\n{'='*70}")
        print("WEIGHT SENSITIVITY (CV + F1 per alpha combination)")
        df_ws = pd.read_csv(ws_path)
        for (alpha, beta, name), grp in df_ws.groupby(["alpha","beta","name"]):
            vals = grp["wkcs"].values
            cv = np.std(vals)/np.mean(vals)
            a_set = get_adaptive_alerts(vals, grp["pair"].values)
            m = metrics(a_set, GROUND_TRUTH_DRIFT_PAIRS, TOTAL_PAIRS)
            marker = " ◄ SELECTED" if alpha==0.6 else ""
            print(f"  α={alpha} β={beta} ({name:<20}): CV={cv:.3f} "
                  f"P={m['precision']} R={m['recall']} F1={m['f1']}{marker}")

if __name__ == "__main__":
    main()