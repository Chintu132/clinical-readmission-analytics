# Clinical Readmission Analytics Platform

An end-to-end healthcare data science pipeline that analyzes hospital readmission risk using synthetic EHR (Electronic Health Record) data. Built to demonstrate clinical data engineering, patient cohort analysis, predictive modeling, and decision support capabilities.

## Problem Statement

Hospital readmissions within 30 days of discharge are a major quality indicator and cost driver in healthcare. CMS (Centers for Medicare & Medicaid Services) penalizes hospitals with excess readmission rates. Identifying patients at high risk of readmission before discharge enables targeted interventions — care coordination, follow-up scheduling, medication reconciliation — that improve outcomes and reduce costs.

This project builds the data pipeline and predictive model that supports those clinical decisions.

## Architecture

```
Synthetic EHR Data → Python ETL → SQLite Warehouse → Feature Engineering → ML Model → Decision Support
```

Pipeline stages: Generate → Extract → Transform → Load → Analyze → Predict → Visualize

## Data

Uses **Synthea-style synthetic patient data** — realistic but fully synthetic EHR records with no PHI (Protected Health Information). Tables mirror real EHR structures:

- `patients` — demographics, birth date, gender, race, county
- `encounters` — hospital visits (inpatient, outpatient, ED, ambulatory)
- `conditions` — diagnoses (ICD-10 style codes mapped to clinical categories)
- `medications` — prescriptions with start/stop dates
- `observations` — vitals and lab results (BMI, blood pressure, glucose, A1C)

## Key Analyses

### 1. 30-Day Readmission Rate by Condition
Calculates readmission rates across clinical categories — heart failure, COPD, diabetes, pneumonia — the same conditions CMS tracks.

### 2. Patient Risk Feature Engineering
Builds clinical features from raw EHR data: Charlson Comorbidity Index, medication count, ED visit frequency, prior admissions, length of stay, and lab value flags.

### 3. Readmission Prediction Model
Logistic regression and Random Forest predicting 30-day readmission. Interpretable coefficients for clinical decision support — which factors drive readmission risk.

### 4. Cohort Analysis
Stratified analysis by age group, gender, comorbidity burden, and payer type — identifying which patient populations face highest readmission risk.

## Key Results

_(Updated after running the pipeline)_

## Tech Stack

Python (Pandas, scikit-learn, Matplotlib) · SQL (SQLite) · Power BI

## How to Run

```bash
pip install -r requirements.txt
python etl/generate_ehr_data.py
python etl/run_pipeline.py
python analysis/readmission_rates.py
python analysis/feature_engineering.py
python analysis/readmission_model.py
python analysis/cohort_analysis.py
```

## Project Structure

```
clinical-readmission-analytics/
├── README.md
├── requirements.txt
├── etl/
│   ├── generate_ehr_data.py    # synthetic EHR data generation
│   ├── extract.py              # load raw CSVs
│   ├── transform.py            # clean, conform, build features
│   ├── load.py                 # populate warehouse
│   └── run_pipeline.py         # orchestrate ETL
├── sql/
│   ├── schema/create_tables.sql
│   └── analytics/              # clinical queries
├── analysis/
│   ├── readmission_rates.py    # 30-day readmission by condition
│   ├── feature_engineering.py  # clinical feature extraction
│   ├── readmission_model.py    # predictive model
│   └── cohort_analysis.py      # stratified population analysis
├── dashboards/screenshots/
└── docs/
    ├── data_dictionary.md
    ├── methodology.md
    └── hipaa_considerations.md
```

## Privacy & Compliance

All data is fully synthetic — no real patient information. See `docs/hipaa_considerations.md` for design notes on how this pipeline would be adapted for real PHI under HIPAA.

## License
MIT
