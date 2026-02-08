const DASHBOARD_DATA = {
    "ticker": "UAMY",
    "name": "United States Antimony Corp",
    "price": 8.61,
    "price_change": "+4.1%",
    "sentiment": "Strong Bullish",
    "technical_stack": {
        "sma_50": 7.01,
        "sma_200": 5.58,
        "ema_21": 8.12,
        "atr": 0.45,
        "buy_zone": "Active",
        "pivots": {
            "R2": 14.22,
            "R1": 11.42,
            "Pivot": 9.16,
            "S1": 6.36,
            "S2": 4.10
        },
        "fibonacci": [
            { "level": "High (100%)", "price": 19.71 },
            { "level": "78.6%", "price": 15.75 },
            { "level": "61.8%", "price": 12.64 },
            { "level": "50%", "price": 10.46 },
            { "level": "38.2%", "price": 8.28 },
            { "level": "23.6%", "price": 5.58 },
            { "level": "Low (0%)", "price": 1.21 }
        ]
    },
    "insider_trades": [
        { "date": "2025-09-26", "insider": "Gary C. Evans", "type": "P", "shares": 100000, "price": 6.13, "value": 613000 },
        { "date": "2024-12-10", "insider": "Gary C. Evans", "type": "P", "shares": 200000, "price": 1.45, "value": 290000 }
    ],
    "verification": {
        "supply_chain": {
            "claims": {
                "330_ton_feedstock": "VERIFIED (Landed April-Dec 2025)",
                "bolivian_ore_jan_2026": "PROBABLE (Customs Logs: 2617.10)",
                "production_guidance": "100-200T/Month (85% Utilized)"
            },
            "gap_analysis": "Primary gap remains in 2026 guidance vs actual throughput. Jan 2026 data suggests a tighter bottleneck at the smelter re-burn stage.",
            "benchmark": 46.7
        },
        "geospatial": {
            "site": "Stibnite Hill, MT",
            "coords": "47.59 N, 115.33 W",
            "score": 0.85,
            "status": "ACTIVE (Bulk Sampling)",
            "timeline": [
                { "date": "Sept 1, 2025", "event": "Baseline", "detail": "Minimal activity. Vegetation override. No sign of mechanized excavation." },
                { "date": "Oct 30, 2025", "event": "Activity", "detail": "MECHANIZED CLEARANCE DETECTED. Consistent with 'Cut and Cover' sampling. 800 tons removal confirmed." },
                { "date": "Feb 2026", "event": "Maintenance", "detail": "Snow-covered site. Infrared signatures suggest perimeter maintenance or sub-surface work." }
            ]
        }
    },
    "headlines": [
        { "title": "FORGE Initiative Launched", "date": "2026-02-04", "summary": "Targets antimony supply chains." },
        { "title": "Nova Minerals Awarded $43.4M", "date": "2026-01-15", "summary": "Domestic antimony supply grant." }
    ],
    "sec_insights": {
        "operations": "Execution of option agreement in Fairbanks, Alaska. Mineral property lease in Preston, Idaho extended 10 years. Philipsburg, MT lease modified for lower payments.",
        "risk_factors": "Fluctuations in market prices (Sb/Zeolite), operational risks in mining, and global labor availability."
    }
};
