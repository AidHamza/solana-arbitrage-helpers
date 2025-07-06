#!/usr/bin/env python3
"""
CLI helper – generates [[filter_thresholds]] TOML from arb-assist log.

Usage:
    python tiers_builder.py arb-assist-log.csv > tiers.toml
"""

import argparse, re, toml, math, pandas as pd, numpy as np
from pathlib import Path

DEF_NUMS = [
    "total_profit","profit_per_arb","roi","arbs","fails",
    "net_vol","tot_vol","liquidity","turnover","imbalance"
]

def str_to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.str.replace(r"[_ ,]", "", regex=True), errors="coerce")

def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    for c in DEF_NUMS:
        if c in df.columns:
            df[c] = str_to_num(df[c])
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df

def rlamports(x: float) -> int:          # round to nearest 10k L
    return int(round(x / 10_000)) * 10_000

def clamp(v, lo=None, hi=None):
    if lo is not None and v < lo: return lo
    if hi is not None and v > hi: return hi
    return v

def build_tiers(df: pd.DataFrame):
    snap = df[df.timestamp == df.timestamp.max()]
    Q = snap[DEF_NUMS].quantile([.5,.75,.9,.98]).T
    tiers = [.5,.75,.9,.98]
    levels = []
    for q in tiers:
        name = f"q{int(q*100)}"
        lvl = dict(
            min_profit           = rlamports(clamp(Q.loc['total_profit',name]*0.8, lo=5_000_000)),
            min_profit_per_arb   = rlamports(clamp(Q.loc['profit_per_arb',name]*0.8, lo=500_000)),
            min_roi              = clamp(round(Q.loc['roi',name]*0.6,2), lo=.05, hi=1.5),
            min_txns             = max(int(Q.loc['arbs',name]),1),
            min_fails            = 0,
            min_net_volume       = rlamports(Q.loc['net_vol',name]),
            min_total_volume     = rlamports(Q.loc['tot_vol',name]),
            min_imbalance_ratio  = 0.0,
            max_imbalance_ratio  = 1.0,
            min_liquidity        = 0,
            min_turnover         = 0.0,
            min_volatility       = 0.0,
        )
        levels.append(lvl)
    return levels

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path, help="arb-assist log CSV")
    args = ap.parse_args()

    df = load_csv(args.csv)
    tiers = build_tiers(df)
    print(toml.dumps({"filter_thresholds": tiers}))
