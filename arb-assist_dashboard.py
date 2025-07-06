# ╔══════════════════════════════════════════════════════════════╗
# ║      ARB-ASSIST LOG ➜ SMB CONFIG • COMPLETE DASHBOARD       ║
# ║  Paste into ONE Colab / Jupyter cell and run.               ║
# ║  – uploads:  arb-assist-log.csv                             ║
# ║  – outputs:  filter_thresholds block, tables, plots, html   ║
# ╚══════════════════════════════════════════════════════════════╝
!pip -q install pandas numpy toml tabulate matplotlib seaborn ydata_profiling

import math
import textwrap
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import toml
from tabulate import tabulate
from ydata_profiling import ProfileReport

# ───────────────────────── USER CONFIG ───────────────────────── #
# You can connect drive and use /content/drive/MyDrive/arb-assist/intermint_log_2025-07-04.csv
CSV_PATH = Path("/content/intermint_log_2025-07-04.csv")   # ← change path to the updated daily logs
# ──────────────────────────────────────────────────────────────── #

# ─────────────────────── 1 ▸ CLEAN LOADER ────────────────────── #
NUMERIC_COLS = [
    "total_profit", "profit_per_arb", "roi", "arbs", "fails",
    "net_vol", "tot_vol", "liquidity", "turnover", "imbalance",
    "cu_price_25p", "cu_price_50p", "cu_price_75p", "cu_price_95p",
    "jito_tip_25p", "jito_tip_50p", "jito_tip_75p", "jito_tip_95p",
]

def str_to_num(series: pd.Series) -> pd.Series:
    """Remove underscores/commas and cast to float."""
    cleaned = series.str.replace(r"[_ ,]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")

raw = pd.read_csv(CSV_PATH, dtype=str)
for col in NUMERIC_COLS:
    if col in raw.columns:
        raw[col] = str_to_num(raw[col])

raw["timestamp"] = pd.to_datetime(raw["timestamp"], errors="coerce")
snap = raw.loc[raw.timestamp == raw.timestamp.max()].copy()
snap["success_rate"] = snap["arbs"] / (snap["arbs"] + snap["fails"] + 1e-9)

# ───────────────────── 2 ▸ QUANTILE TABLE ───────────────────── #
Q = snap[NUMERIC_COLS].quantile(
    [0.25, 0.50, 0.75, 0.90, 0.95, 0.98, 0.995]
).T
Q.columns = ["q25", "q50", "q75", "q90", "q95", "q98", "q995"]

print("\n≈ KPI distribution (latest snapshot)\n")
print(tabulate(Q.reset_index(), headers="keys", floatfmt=".3g"))

# ───── 3 ▸ AUTO-BUILD FILTER TIERS (with clamps & rounding) ──── #
TIERS = [
    dict(tag="Scout", q=0.50),
    dict(tag="Warm",  q=0.75),
    dict(tag="Hot",   q=0.90),
    dict(tag="Nuke",  q=0.98),
]

FLOOR_PROFIT          = 5_000_000      # 0.005 SOL
FLOOR_PROFIT_PER_ARB  = 500_000        # 0.0005 SOL
FLOOR_ROI, MAX_ROI    = 0.05, 1.5
FLOOR_TXNS            = 1

def clamp(val, lo=None, hi=None):
    if lo is not None and val < lo:
        return lo
    if hi is not None and val > hi:
        return hi
    return val

rlamports = lambda x: int(round(x / 10_000)) * 10_000
q = lambda m, qstr: 0 if m not in Q.index else Q.loc[m, qstr]

filter_levels = []
for tier in TIERS:
    qstr = f"q{int(tier['q']*100)}"
    level = dict(
        min_profit           = rlamports(clamp(q("total_profit",      qstr)*0.8,
                                               lo=FLOOR_PROFIT)),
        min_profit_per_arb   = rlamports(clamp(q("profit_per_arb",    qstr)*0.8,
                                               lo=FLOOR_PROFIT_PER_ARB)),
        min_roi              = clamp(round(q("roi", qstr)*0.6, 2),
                                               lo=FLOOR_ROI, hi=MAX_ROI),
        min_txns             = clamp(int(q("arbs", qstr)), lo=FLOOR_TXNS),
        min_fails            = 0,
        min_net_volume       = rlamports(q("net_vol",  qstr)),
        min_total_volume     = rlamports(q("tot_vol",  qstr)),
        min_imbalance_ratio  = 0.0,
        max_imbalance_ratio  = 1.0,
        min_liquidity        = 0,
        min_turnover         = 0.0,
        min_volatility       = 0.0,
    )
    filter_levels.append(level)

print("\n##########   paste into arb-assist.toml   ##########\n")
print(textwrap.indent(toml.dumps({"filter_thresholds": filter_levels}), "  "))

# ──────────────── 4 ▸ TOP-N & BAD SUCCESS TABLES ─────────────── #
print("\nTop-10 mints by TOTAL PROFIT")
display(snap.sort_values("total_profit", ascending=False)
        [["mint","total_profit","profit_per_arb","arbs","fails","roi"]].head(10))

print("\nHigh PROFIT but poor SUCCESS-RATE (<2 %)")
bad = snap.query("total_profit > 1e8 and success_rate < .02")
display(bad[["mint","total_profit","success_rate","arbs","fails"]])

# ───────────────────── 5 ▸ DISTRIBUTION PLOTS ────────────────── #
plt.style.use("default")
fig, axs = plt.subplots(2, 3, figsize=(15, 8))
axs = axs.ravel()

sns.histplot(snap["total_profit"]/1e9, bins=40, ax=axs[0])
axs[0].set_title("Profit (SOL)")

sns.histplot(snap["profit_per_arb"]/1e9, bins=40, ax=axs[1])
axs[1].set_title("Profit per arb (SOL)")

sns.histplot(snap["roi"], bins=40, ax=axs[2])
axs[2].set_title("ROI")

sns.histplot(snap["success_rate"], bins=40, ax=axs[3])
axs[3].set_title("Success-rate")

sns.histplot(snap["cu_price_95p"], bins=40, ax=axs[4])
axs[4].set_title("CU price 95-pctl (µSOL/CU)")

sns.histplot(snap["jito_tip_95p"], bins=40, ax=axs[5])
axs[5].set_title("Jito tip 95-pctl (µSOL)")

plt.tight_layout()
plt.show()

# ─────────────── 6 ▸ TIME-SERIES PROFIT (5-min) ──────────────── #
raw["bucket"] = raw["timestamp"].dt.floor("5min")
ts = (raw.groupby("bucket")["total_profit"]
          .sum()
          .div(1e9)          # → SOL
          .rename("profit_SOL")
          .reset_index())

plt.figure(figsize=(10, 3))
plt.plot(ts["bucket"], ts["profit_SOL"])
plt.title("Total profit per 5 min (SOL)")
plt.grid(True); plt.xlabel("UTC time"); plt.ylabel("profit (SOL)")
plt.show()

# ───────────── 7 ▸ OPTIONAL INTERACTIVE PROFILE HTML ─────────── #
print("\nBuilding interactive ydata-profile (15 % sample)…")
ProfileReport(raw.sample(frac=0.15, random_state=1),
              title="Arb-assist profile").to_file("profile.html")
print("✓ profile.html saved – download if needed.")

# ───────────── 8 ▸ MARKDOWN SUMMARY FOR SLACK / NOTION ───────── #
summary_md = f"""
### Arb-assist snapshot – {datetime.utcnow():%Y-%m-%d %H:%M} UTC

| KPI | p50 | p75 | p90 | p95 |
| --- | --- | --- | --- | --- |
| **Profit (L)** | {int(Q.loc['total_profit','q50']):,} | {int(Q.loc['total_profit','q75']):,} | {int(Q.loc['total_profit','q90']):,} | {int(Q.loc['total_profit','q95']):,} |
| **ROI** | {Q.loc['roi','q50']:.2f} | {Q.loc['roi','q75']:.2f} | {Q.loc['roi','q90']:.2f} | {Q.loc['roi','q95']:.2f} |
| **Success-rate** | {snap['success_rate'].median()*100:.1f}% | – | – | – |

Top-5 mints by profit:
"""
print("\n" + summary_md)
