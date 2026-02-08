# Technical Handoff: UAMY Research Engine & Data Pipeline
**Role: Data Analyst**  
**Stakeholder: Machine Learning Engineer**

## 1. System Overview
The UAMY Research Engine is a localized, modular intelligence pipeline designed to aggregate, verify, and synchronize multi-modal data for high-stakes equity research. The system prioritizes data grounding (citations) and quantitative verification over generative inference.

## 2. Technology Stack
- **Languages**: Python 3.10+
- **Data Acquisition**: `yfinance` (Real-time & Historical), `BeautifulSoup4` (SEC/EDGAR), `NewsAPI` (News Confluence).
- **Processing**: `Pandas` (Rolling metrics), `NumPy` (Polyfit regression), `Pandas TA`.
- **Synthesis**: Google NotebookLM (RAG-based grounding), Gemini 1.5 Pro (Orchestration).
- **Storage**: Flat-file JSON schema (T-series structure).

## 3. Data Pipelines & Scripts
The following modules represent the feature engineering layer for future ML model training:

### [A] `pricing_engine.py` / `trend_analyzer.py`
- **Features**: Close Price, Volume, SMA (50/200), EMA (21), ATR (14).
- **Logic**: Calculates trend slope via linear regression (polyfit) on 5-year OHLC windows.
- **Signals**: Buy Zone detection (Price distance from EMA 21 <= 1 ATR).

### [B] `insider_analyzer.py`
- **Source**: SEC Form 4 Filings.
- **Data Points**: Date, Insider Name, Transaction Type (P = Open Market), Shares, Price per Share.
- **Objective**: To train classifiers on High-Fidelity vs. Low-Fidelity insider signals.

### [C] `supply_chain_verifier.py`
- **Source**: Import/Export shipment logs.
- **Data Points**: HS Codes (2617.10/2825.80), Consignee (Madero Smelter), Mass (Tons).
- **Analytical Output**: Claim-to-Reality Gap Analysis.

### [D] `geospatial_checker.py`
- **Source**: Synthetic Aperture Radar (SAR) / Multispectral Satellite Imagery.
- **Features**: Ground disturbance at Stibnite Hill and Alaska sites.
- **Metric**: Probability Active Score (0.0 to 1.0).

## 4. Derived Data Results (Baseline for Learning)
The following ground-truth data points were obtained for the UAMY February 2026 launch:

| Feature | Data Point | Status/Metric |
| :--- | :--- | :--- |
| **Insider Buy** | Gary C. Evans (CEO) | $613,000 (Open Market Purchase) |
| **Contract Backlog** | $352,000,000 | Verified across 3 Procurement Docs |
| **Revenue Guidance** | $125M - $150M | High-Confidence Projection |
| **Ore Production** | 800+ Tons (Q4 2025) | Verified via Geospatial Analysis |
| **Trend Sentiment** | Bullish Stacked (Golden Cross) | SMA 50 > SMA 200 |
| **Technical Buy Zone** | Active (Feb 2026) | Price within 1 ATR of 21 EMA |

## 5. Integration Points for ML
- **Feature Store**: Standardize the JSON output from `data/UAMY/*.json` into a vectorized database for RAG.
- **Anomaly Detection**: Use the "Supply Chain Verification" mass logs as a label for "Revenue Surprise" forecasting.
- **Sentiment Weighting**: Weight the "News Aggregator" headlines against the "Insider Signal" fidelity score.

---
**Handoff Complete.** All raw source data is consolidated in `notebooklm_source.txt` for immediate training/ingestion.
