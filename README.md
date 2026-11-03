# A/B Testing & Product Feature Conversion Funnel Analysis

A portfolio-ready experimentation analytics project using **Python, SQL, SciPy, Streamlit, Pandas, NumPy, and Plotly**. It compares a Control group (A) with a Variant group (B), evaluates statistical evidence, and identifies conversion funnel drop-offs.

## Business problem
Product teams should not launch a design or checkout change based only on intuition. Controlled experiments quantify whether a variant improves the primary metric while monitoring funnel and guardrail outcomes.

## Features
- Clean event logs and build one-row-per-user experiment outcomes.
- Compare Control and Variant conversion rates.
- Two-proportion chi-square test and p-value.
- Welch independent-samples t-test for revenue per randomized user (including zero revenue).
- 95% confidence interval for absolute conversion-rate difference.
- Funnel analysis: Landing Page → Add to Cart → Checkout → Purchase.
- Device-level conversion breakdown.
- Stakeholder launch / no-launch / inconclusive recommendation.
- Download cleaned event data.
- PostgreSQL SQL examples in `sql/ab_test_analysis.sql`.

## Statistical methodology
- **Null hypothesis:** Control and Variant have the same conversion probability.
- **Alternative hypothesis:** Their conversion probabilities differ.
- **Chi-square test:** tests the 2×2 table of group by converted/not converted.
- **Welch t-test:** compares revenue per randomized user without assuming equal variance.
- **Confidence interval:** normal-approximation 95% interval for Variant minus Control conversion rate.
- Default significance level: α = 0.05, configurable in the dashboard.

A statistically significant result is not automatically a business win. Consider effect size, confidence interval, guardrail metrics, sample size, experiment duration, and practical impact.

## Funnel definitions
Each user is counted at most once at each event stage. The funnel is calculated from users who appear in the selected experiment dataset. Stage conversion is the percentage progressing from the immediately prior stage; overall conversion is relative to landing-page users.

## Project structure
```text
ab-testing-conversion-funnel/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   └── events.csv
├── sql/
│   └── ab_test_analysis.sql
└── docs/
    └── dashboard-preview.png
```

## Run on Windows PowerShell
```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Open the local URL shown in the terminal, usually `http://localhost:8501`.

## Input CSV schema
Required columns:
- `user_id`: stable anonymous user identifier
- `group`: `Control` or `Variant`
- `event_name`: `landing_page`, `add_to_cart`, `checkout`, or `purchase`
- `event_time`: event timestamp
- `revenue`: numeric purchase revenue; zero for non-purchase events

Optional columns: `device`, `country`.

The included dataset is synthetic, with 8,000 randomized users and event-level journey data. It is for portfolio demonstration only.

## SQL
See `sql/ab_test_analysis.sql` for PostgreSQL examples to aggregate user-level funnel flags and produce conversion counts for a 2×2 experiment test.

## Experimentation best practices
- Randomize at the correct unit (usually user/account) and keep assignment sticky.
- Check sample-ratio mismatch and exposure logging before interpreting results.
- Pre-register one primary metric and guardrail metrics.
- Decide sample size and stopping rule before launching; avoid repeated peeking.
- Account for novelty, seasonality, bots, duplicate events, and multiple comparisons.
- Ensure each user is assigned to only one group; reconcile group assignment in event logs.
- Use consented, privacy-safe identifiers and follow applicable data policies.

## Limitations
The dashboard uses a fixed-horizon, independent-user approximation. The confidence interval is a Wald interval and may be less reliable for very small samples or extreme conversion rates. Production experimentation may require sequential methods, stratification, variance reduction, cluster-robust inference, and power analysis.

## Suggested GitHub repository
**Name:** `AB-Testing-Conversion-Funnel-Analysis`

**Description:** Product experimentation project using Python, SQL, hypothesis testing, statistical significance, and conversion funnel analytics.

**Topics:** `ab-testing` `experimentation` `hypothesis-testing` `chi-square-test` `t-test` `conversion-funnel` `product-analytics` `python` `sql` `streamlit`

## Resume description
Built an A/B testing analytics dashboard to compare control and variant conversion, apply chi-square and Welch t-tests, calculate confidence intervals, analyze funnel drop-offs, and provide evidence-based launch recommendations.
