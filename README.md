# 🏈 Alpha-Playbooks

> **Opinions are Beta. Data is Alpha.**

Welcome to the **Alpha-Playbooks** repository. This is a collection of beginner-friendly Python scripts designed to help you automate your research and trade with a data-first mindset. 

This repository accompanies the [mphinance Substack](https://mphinance.substack.com)—specifically the **UAMY "War Metal" Research Vault**.

---

## 📊 The Data: [Master Research Dossier](RESEARCH_DOSSIER.md)

This repository includes the **Lead Analyst Directive** and the **Institutional Benchmarks** used for UAMY research. It consolidates technical benchmarks, supply chain data, and regulatory filing references into one source of truth.

---

## 📋 The Offensive Play Card: `alpha_scout.py`

The flagship script in this repo is `alpha_scout.py`. It’s designed to give you a quick "Scouting Report" on any ticker.

### What it does:
1.  **Technical Stack:** Calculates the SMA 50/200, the **21-day EMA**, and the **ATR** (Average True Range).
2.  **Analyzes the Formation:** Determines if the stock is "Bullish Stacked" or "Bearish Stacked."
3.  **The Buy Zone:** Signals if the price is within **1 ATR of the 21 EMA** (the MPH Special).
4.  **Scout Report:** Scrapes the latest headlines directly from the wire.

### How to Run:
1.  **Install Requirements:**
    ```bash
    pip install yfinance pandas
    ```
2.  **Run the Scout:**
    ```bash
    python alpha_scout.py UAMY
    ```

---

## 🏛 The Alpha Intelligence Dashboard (Live)

The interactive **Alpha Intelligence Dashboard** is now hosted via GitHub Pages. It provides a real-time tactical overview of technical levels, geospatial ground truth, and institutional order flow.

**[Launch Live Dashboard ->](https://mphinance.github.io/alpha-playbooks/)**

---

## 🏛 The Research Vault (NotebookLM)

If you want the full deep-dive on UAMY, we’ve built an interactive **Research Vault** using Google NotebookLM. 

![NotebookLM Guide](https://raw.githubusercontent.com/mphinance/alpha-playbooks/main/assets/notebook_ui_guide.png)

**[Access the UAMY Deep Research Vault ->](https://notebooklm.google.com/notebook/db4ee70e-63f0-4234-909e-cd9558c36fab)**

---

## 🏈 Why Python for Traders?
The internet is drowning in opinions. You can get "market sentiment" for free on X or Reddit. Finding the right ones to listen to? That's the hard part.

But curated data? A script that saves you 3 hours of digging through balance sheets? That is **Alpha**. 

## 🔗 Links
- **Substack:** [mphinance.substack.com](https://mphinance.substack.com)
- **Twitter:** [@mphinance](https://twitter.com/mphinance)

---
*Disclaimer: These scripts are for educational purposes. Mining stocks and options are high risk. Always verify the data before making a play.*
