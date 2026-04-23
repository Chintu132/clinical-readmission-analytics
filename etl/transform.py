"""
ETL Transform — Clean, conform, and build analytical features from EHR data.
Produces the 30-day readmission flag which is the core analytical target.
"""
import pandas as pd
import numpy as np


def transform_patients(df):
    """Clean patient demographics."""
    df = df.copy()
    df['age_group'] = pd.cut(df['age'], bins=[0, 18, 40, 55, 65, 75, 120],
                              labels=['0-17', '18-39', '40-54', '55-64', '65-74', '75+'])
    print(f"  dim_patient: {len(df):,} rows")
    return df


def build_readmission_flag(encounters_df):
    """
    Build the 30-day readmission flag — THE key metric.
    For each inpatient discharge, check if the same patient
    has another inpatient or ED encounter within 30 days.
    """
    df = encounters_df.copy()
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['end_date'] = pd.to_datetime(df['end_date'])

    # Focus on inpatient discharges
    inpatient = df[df['encounter_type'] == 'inpatient'].sort_values(['patient_id', 'end_date']).copy()

    # All acute encounters (inpatient + ED) for readmission check
    acute = df[df['encounter_type'].isin(['inpatient', 'emergency'])].copy()

    readmission_flags = []
    for _, discharge in inpatient.iterrows():
        pid = discharge['patient_id']
        discharge_date = discharge['end_date']

        # Look for any acute encounter within 30 days after discharge
        future = acute[
            (acute['patient_id'] == pid) &
            (acute['start_date'] > discharge_date) &
            (acute['start_date'] <= discharge_date + pd.Timedelta(days=30)) &
            (acute['encounter_id'] != discharge['encounter_id'])
        ]

        readmission_flags.append({
            'encounter_id': discharge['encounter_id'],
            'patient_id': pid,
            'discharge_date': discharge_date,
            'length_of_stay': discharge['length_of_stay'],
            'discharge_disposition': discharge['discharge_disposition'],
            'readmitted_30d': 1 if len(future) > 0 else 0,
            'days_to_readmission': (future['start_date'].min() - discharge_date).days if len(future) > 0 else None,
        })

    result = pd.DataFrame(readmission_flags)
    rate = result['readmitted_30d'].mean() * 100
    print(f"  fact_readmission: {len(result):,} rows (30-day readmission rate: {rate:.1f}%)")
    return result


def build_encounter_summary(encounters_df, patients_df):
    """Summarize encounter history per patient for feature engineering."""
    df = encounters_df.copy()
    df['start_date'] = pd.to_datetime(df['start_date'])

    summary = df.groupby('patient_id').agg(
        total_encounters=('encounter_id', 'count'),
        inpatient_count=('encounter_type', lambda x: (x == 'inpatient').sum()),
        ed_count=('encounter_type', lambda x: (x == 'emergency').sum()),
        outpatient_count=('encounter_type', lambda x: (x == 'outpatient').sum()),
        avg_los=('length_of_stay', 'mean'),
        max_los=('length_of_stay', 'max'),
        first_encounter=('start_date', 'min'),
        last_encounter=('start_date', 'max'),
    ).reset_index()

    summary['avg_los'] = summary['avg_los'].round(1)
    print(f"  patient_encounter_summary: {len(summary):,} rows")
    return summary


def build_comorbidity_count(conditions_df):
    """Count distinct condition categories per patient (simplified Charlson-like index)."""
    comorbidity = (conditions_df
        .groupby('patient_id')
        .agg(
            condition_count=('condition_id', 'count'),
            distinct_categories=('category', 'nunique'),
            has_diabetes=('category', lambda x: int('Diabetes' in x.values)),
            has_heart_failure=('category', lambda x: int('Heart Failure' in x.values)),
            has_copd=('category', lambda x: int('COPD' in x.values)),
            has_ckd=('category', lambda x: int('CKD' in x.values)),
            has_depression=('category', lambda x: int('Depression' in x.values)),
            max_risk_factor=('readmission_risk_factor', 'max'),
        )
        .reset_index()
    )
    print(f"  patient_comorbidity: {len(comorbidity):,} rows")
    return comorbidity


def build_medication_count(medications_df):
    """Count active medications per patient (polypharmacy indicator)."""
    active = medications_df[medications_df['is_active'] == 1]
    med_count = (active
        .groupby('patient_id')
        .agg(active_med_count=('medication_id', 'count'))
        .reset_index()
    )
    print(f"  patient_medications: {len(med_count):,} rows")
    return med_count


def build_vitals_summary(observations_df):
    """Aggregate latest vitals per patient."""
    df = observations_df.copy()
    df['date'] = pd.to_datetime(df['date'])

    # Get latest observation per patient per type
    latest = df.sort_values('date').drop_duplicates(
        subset=['patient_id', 'description'], keep='last'
    )

    pivot = latest.pivot_table(
        index='patient_id', columns='description',
        values='value', aggfunc='last'
    ).reset_index()

    # Rename columns
    col_map = {'BMI': 'latest_bmi', 'Systolic BP': 'latest_sbp',
               'Heart Rate': 'latest_hr', 'Glucose': 'latest_glucose',
               'HbA1c': 'latest_a1c'}
    pivot = pivot.rename(columns=col_map)

    keep = ['patient_id'] + [v for v in col_map.values() if v in pivot.columns]
    result = pivot[keep].copy()
    print(f"  patient_vitals: {len(result):,} rows")
    return result
