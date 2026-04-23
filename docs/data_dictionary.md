# Data Dictionary

## dim_patient
| Column | Type | Description |
|--------|------|-------------|
| patient_id | TEXT | Unique patient identifier (synthetic) |
| birth_date | TEXT | Date of birth |
| gender | TEXT | M/F |
| race | TEXT | White, Black, Hispanic, Asian, Other |
| county | TEXT | County of residence |
| payer | TEXT | Medicare, Medicaid, Private, Self-Pay |
| age | INT | Age in years |
| age_group | TEXT | Bucketed: 0-17, 18-39, 40-54, 55-64, 65-74, 75+ |

## fact_readmission
| Column | Type | Description |
|--------|------|-------------|
| encounter_id | TEXT | FK to encounter |
| patient_id | TEXT | FK to dim_patient |
| discharge_date | DATE | Date of inpatient discharge |
| length_of_stay | INT | Days from admission to discharge |
| discharge_disposition | TEXT | home, home_health, SNF, rehab, AMA, expired |
| readmitted_30d | INT | 1 if patient had acute encounter within 30 days, 0 otherwise |
| days_to_readmission | INT | Days until readmission (NULL if not readmitted) |

## patient_encounter_summary
| Column | Type | Description |
|--------|------|-------------|
| patient_id | TEXT | FK to dim_patient |
| total_encounters | INT | Lifetime encounter count |
| inpatient_count | INT | Number of inpatient stays |
| ed_count | INT | Number of ED visits |
| avg_los | FLOAT | Average length of stay across inpatient stays |

## patient_comorbidity
| Column | Type | Description |
|--------|------|-------------|
| patient_id | TEXT | FK to dim_patient |
| condition_count | INT | Total conditions diagnosed |
| distinct_categories | INT | Unique condition categories (simplified Charlson proxy) |
| has_diabetes | INT | 1 if diabetes diagnosed |
| has_heart_failure | INT | 1 if heart failure diagnosed |
| has_copd | INT | 1 if COPD diagnosed |
| has_ckd | INT | 1 if chronic kidney disease diagnosed |
| has_depression | INT | 1 if depression diagnosed |
| max_risk_factor | FLOAT | Highest readmission risk factor among conditions |

## patient_medications
| Column | Type | Description |
|--------|------|-------------|
| patient_id | TEXT | FK to dim_patient |
| active_med_count | INT | Number of currently active medications |

## patient_vitals
| Column | Type | Description |
|--------|------|-------------|
| patient_id | TEXT | FK to dim_patient |
| latest_bmi | FLOAT | Most recent BMI reading |
| latest_sbp | FLOAT | Most recent systolic blood pressure |
| latest_hr | FLOAT | Most recent heart rate |
| latest_glucose | FLOAT | Most recent glucose level |
| latest_a1c | FLOAT | Most recent HbA1c level |
