<!-- README.md -->
<h1 align="center">arb-assist logs analysis</h1>

<p align="center">
  <em>Turn raw <code>arb-assist</code> logs into data-driven <code>smb-onchain | notarb</code> configs in one Colab run.</em>
</p>

<p align="center">
  <a href="https://colab.research.google.com/drive/1IfJ-A1Ppu1v2OzpFw_gv1f3Eu9W9aK6K?usp=sharing">
    <img alt="Open in Colab" src="https://img.shields.io/badge/Google%20Colab-%23F9A825.svg?style=for-the-badge&logo=googlecolab&logoColor=white">
  </a>
  &nbsp;
  <a href="LICENSE">
    <img alt="MIT license" src="https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge">
  </a>
</p>

---

## 🔒 Security & disclaimers

* This tool **does not sign or send transactions**, never asks for private keys, and never edits your bot configs directly.  
* Always review generated TOML and Python before execution—**trust but verify**.  
* If something is unclear, lean on AI explanations or static analysis tools before running code in production.  
* Use at your own risk; no warranty is provided.

<br>

## ✨ What it does
* **Reads** yesterday’s `arb-assist-log.csv`.
* **Builds** a full dashboard (quantile table, histograms, 5-min profit curve).
* **Generates** a ready-to-paste **`[[filter_thresholds]]`** block with sane floors/caps.
* **Flags** mints that blow the 128-account limit.
* **Exports** an interactive `profile.html`.
* **Emits** a Markdown KPI snippet you can drop into Discord/Slack.

<br>

## 🚀 Quick start
| use-case | steps |
| --- | --- |
| **Colab (zero local deps)** | 1. open the notebook link<br>2. upload your `arb-assist-log.csv` (left sidebar → Files → Upload)<br>3. **Runtime ▸ Run all**<br>4. copy the printed `filter_thresholds` block → paste into `arb-assist.toml` |
| **CLI (server / cron)** | `python tiers_builder.py path/to/arb-assist-log.csv > tiers.toml` |

<br>

## 📊 Sample output screenshots
![Stats](docs/dashboard_sample.png)

![dashboard](docs/dashboard_sample2.png)

<br>

## 📝 Advice & gotchas

| symptom | fix |
| --- | --- |
| *“Transaction too large”* | lower `top_pool_num`, set `merge_mints = false`, or drop `aluts_per_pool` to ≤ 3 |
| no mints ever pass your tiers | lower `min_profit` & `min_roi` in the **Scout** tier, or set `filter_programs = false` so organic swaps count |
| CU / Jito tips feel random | use the histogram & quantile read-out—map 75 %→90 % to Level-2 and 90 %→99 % to Level-3 |
| want a GUI | open `profile.html` that the notebook saves in the repo root |

<br>

## 🛠 Project layout
```text
.
├─ arb-assist_dashboard.ipynb   ← one-click Colab notebook  
├─ tiers_builder.py             ← CLI helper (same logic, no plots)  
├─ requirements.txt             ← minimal deps for local runs  
├─ docs/                        ← screenshots or extra docs  
├─ .gitignore  
└─ LICENSE                      ← MIT
```

<br>

## 🤝 Contributing
Pull requests welcome—clean code and a short rationale in the PR description, please.

---

> Built and maintained by **Hamza** – full-stack & DevOps engineer, cloud-governance by day, crypto side-projects by night.
