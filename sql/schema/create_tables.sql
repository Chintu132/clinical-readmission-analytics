-- Clinical Readmission Analytics — Warehouse Schema
CREATE TABLE IF NOT EXISTS dim_patient (
    patient_id TEXT PRIMARY KEY, birth_date TEXT, gender TEXT, race TEXT,
    county TEXT, payer TEXT, age INTEGER, age_group TEXT
);
CREATE TABLE IF NOT EXISTS fact_readmission (
    encounter_id TEXT, patient_id TEXT, discharge_date DATE,
    length_of_stay INTEGER, discharge_disposition TEXT,
    readmitted_30d INTEGER, days_to_readmission INTEGER
);
CREATE TABLE IF NOT EXISTS patient_encounter_summary (
    patient_id TEXT PRIMARY KEY, total_encounters INTEGER, inpatient_count INTEGER,
    ed_count INTEGER, outpatient_count INTEGER, avg_los REAL, max_los INTEGER
);
CREATE TABLE IF NOT EXISTS patient_comorbidity (
    patient_id TEXT PRIMARY KEY, condition_count INTEGER, distinct_categories INTEGER,
    has_diabetes INTEGER, has_heart_failure INTEGER, has_copd INTEGER,
    has_ckd INTEGER, has_depression INTEGER, max_risk_factor REAL
);
CREATE TABLE IF NOT EXISTS patient_medications (
    patient_id TEXT PRIMARY KEY, active_med_count INTEGER
);
CREATE TABLE IF NOT EXISTS patient_vitals (
    patient_id TEXT PRIMARY KEY, latest_bmi REAL, latest_sbp REAL,
    latest_hr REAL, latest_glucose REAL, latest_a1c REAL
);
CREATE TABLE IF NOT EXISTS etl_log (
    table_name TEXT, rows_loaded INTEGER, loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
