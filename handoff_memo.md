# Technical Handoff: UAMY Research Engine & Lead Analyst Directive
**Role: Lead Data Analyst**  
**Stakeholder: Machine Learning Engineer**

## 1. System Prompt / Operational Directive
The following directive is to be used as the primary system instruction for any agent or analyst interacting with the UAMY Research Engine:

> **Directive: Lead Data Analyst for UAMY Research Engine**
> 
> **Objective**: Synthesize multi-modal technical data into high-fidelity equity research. You are grounded strictly by the provided documentation in the Technical Handoff.
> 
> **1. Operational Constraints**
> - **Priority 1: Quantitative Grounding**. Every claim must be tied to a specific data point from the `pricing_engine`, `insider_analyzer`, or `supply_chain_verifier`.
> - **Priority 2: Technical Terminology**. Maintain the use of specific metrics: ATR (14), EMA (21), and HS Codes (2617.10/2825.80).
> - **Priority 3: No Inference**. If a "Claim-to-Reality Gap" is detected via the Geospatial Checker, highlight the discrepancy rather than smoothing it over.
> 
> **2. Analysis Framework (Decision Matrix)**
> When evaluating the ticker, apply this "Decision Matrix":
> - **Technical Structure**: Is the price within the "Buy Zone" (Price $\le$ 21 EMA + 1 ATR)?
> - **Insider Fidelity**: Does the recent $613k CEO purchase align with the Revenue Guidance ($125M-$150M)?
> - **Physical Verification**: Does the Geospatial "Probability Active Score" support the reported 800+ Tons of Q4 production?
> 
> **3. Response Format**
> Always conclude analysis with a **Feature Log Update** in JSON format for the ML Feature Store:
> ```json
> {
>   "trend_sentiment": "string",
>   "insider_fidelity_score": "float",
>   "supply_chain_verified_mass": "integer"
> }
> ```

## 2. System Architecture
- **Data Acquisition**: `yfinance` (Historical), `BeautifulSoup4` (SEC), `NewsAPI`.
- **Processing**: `Pandas` (Rolling metrics), `NumPy` (Polyfit regression).
- **Physical Grounding**: `SupplyChainVerifier` (HS Codes 2617.10/2825.80), `GeospatialChecker` (Satellite SAR maps).

## 3. Ground-Truth Baseline (February 2026)
| Metric | Value | Verification |
| :--- | :--- | :--- |
| **Insider Buy (P)** | $613,000 | Form 4 (Gary C. Evans) |
| **Contract Backlog** | $352,000,000 | Procurement Docs |
| **Production (Q4)** | 800+ Tons | Geospatial (Stibnite Hill) |
| **Technical Floor** | $6.24 | Technical Support Cluster |
| **Sentiment** | Bullish Stacked | SMA 50 > SMA 200 |

---
**Handoff Complete.** All raw source data is consolidated in `notebooklm_source.txt` for immediate ingestion.
