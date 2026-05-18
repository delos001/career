---
specialty: data-science
last_researched: 2026-05
---

# Data Science - CV Framing Rules

**Used by:** cv_targeted, axis-classifier

## Capability vocabulary

- Statistical programming for analytical purposes (R, Python, SQL, SAS where applicable)
- Statistical methods (descriptive, inferential, hypothesis testing, distribution analysis, correlation, regression)
- Time-series analysis and forecasting (ARIMA, exponential smoothing, state-space methods)
- Anomaly and outlier detection (z-score, MAD, IQR, distribution-based testing)
- Exploratory data analysis (programmatic and visual)
- Predictive modeling using classical ML (regression, classification, clustering, association learning, dimensionality reduction)
- Applied modeling in research/POC mode (NLP, association mining, custom algorithm development) where the deliverable is analytic insight rather than a production system
- Quantitative modeling outside pure statistics (Earned Value Management analogs, simulation, optimization, decision-support modeling)
- Causal inference and observational study methods (propensity scoring, A/B test design, difference-in-differences) where applicable
- Analytic application development (dashboards, surveillance tools, decision instruments) where the deliverable carries an analytical method or pattern-surfacing layer
- Custom data validation and quality-check programming applied to clinical, operational, or business datasets
- Findings communication and analytic storytelling for technical and non-technical stakeholders
- Cross-functional analytical delivery
- Code review, validation testing, and reproducibility for analytical deliverables

## Terminology

Cross-domain practice terminology below. Sector-specific terms for clinical-operations and quality-compliance live in their own files; pharma-sector terms live in `rules/industries/pharma.md`.

- Statistics: descriptive vs inferential, hypothesis testing, p-values, confidence intervals, effect size; parametric vs non-parametric
- Distribution and pattern methods: z-score, MAD, IQR, percentile-based outlier detection, Kolmogorov-Smirnov, Shapiro-Wilk
- Time series: ARIMA, SARIMA, exponential smoothing, decomposition, stationarity, autocorrelation
- Classical ML: linear/logistic regression, decision trees, random forests, gradient boosting (XGBoost, LightGBM), k-means, hierarchical clustering, PCA, association rule learning (Apriori, FP-Growth)
- NLP (applied analytical use): tokenization, TF-IDF, n-grams, named entity recognition, topic modeling (LDA), embeddings used as analysis input rather than production system
- Causal methods: A/B test design, propensity score matching, difference-in-differences, observational study design
- Operations research: simulation, optimization, sensitivity analysis, Earned Value Management
- Languages and environments: R (tidyverse, data.table, R-TERR), Python (pandas, NumPy, scikit-learn, statsmodels, SciPy), SQL, Jupyter, RStudio, PySpark/SparkR when used analytically
- Visualization and analytic-application platforms: Spotfire, Tableau, Power BI, Plotly/Dash, Shiny, Streamlit, ggplot2, matplotlib, seaborn
- Notebook and reproducibility: Jupyter, RMarkdown, Quarto; Git for analytical code
- Validation and reproducibility: validation test scripts, peer code review, reproducible reporting

## Knowledge-transfer mode

- Training delivery, curriculum design, and adoption coaching on this specialty's capabilities, methods, tools, or artifacts, when concurrently practicing the specialty in the role.

## Adjacency

Translation signal for entries tagged with adjacent specialties:

- **data-engineering**: when an analytical capability rests on infrastructure (warehouse, pipeline, schema) the candidate built or extended, the infrastructure work reads as data-engineering depth. Reverse: when a data-engineering deliverable was extended to surface analytical insight (custom checks, anomaly methods, statistical tests), that layer reads as data-science.
- **ai-engineering**: when applied modeling moved into production deployment (served as a system, integrated into a product, with monitoring and drift detection), the production layer is ai-engineering and the prototype/research layer is data-science. Both can co-tag when the candidate carried the work across both stages.
