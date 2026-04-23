"""
Generate Synthetic EHR Data
============================
Creates realistic but fully synthetic Electronic Health Record data
that mirrors structures found in real EHR systems (Epic, Cerner, Encompass).

Tables generated:
- patients: demographics
- encounters: hospital visits (inpatient, outpatient, ED, ambulatory)
- conditions: diagnoses with clinical categories
- medications: prescriptions
- observations: vitals and lab results

No real PHI. All data is randomly generated with clinically plausible distributions.
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'synthea')

# =================================================================
# CLINICAL REFERENCE DATA
# =================================================================

CONDITIONS = [
    # (code, description, category, prevalence_weight, readmission_risk_factor)
    ('I50.9', 'Heart failure, unspecified', 'Heart Failure', 12, 1.8),
    ('J44.1', 'COPD with acute exacerbation', 'COPD', 10, 1.6),
    ('E11.9', 'Type 2 diabetes without complications', 'Diabetes', 18, 1.2),
    ('E11.65', 'Type 2 diabetes with hyperglycemia', 'Diabetes', 8, 1.5),
    ('J18.9', 'Pneumonia, unspecified', 'Pneumonia', 9, 1.4),
    ('I10', 'Essential hypertension', 'Hypertension', 25, 1.0),
    ('I25.10', 'Coronary artery disease', 'CAD', 10, 1.3),
    ('N18.3', 'Chronic kidney disease, stage 3', 'CKD', 7, 1.5),
    ('J45.20', 'Mild intermittent asthma', 'Asthma', 8, 1.1),
    ('F32.1', 'Major depressive disorder, moderate', 'Depression', 10, 1.2),
    ('M17.11', 'Primary osteoarthritis, right knee', 'Osteoarthritis', 6, 0.8),
    ('K21.0', 'GERD with esophagitis', 'GERD', 9, 0.7),
    ('G47.33', 'Obstructive sleep apnea', 'Sleep Apnea', 7, 1.1),
    ('I48.91', 'Atrial fibrillation', 'AFib', 6, 1.4),
    ('E78.5', 'Hyperlipidemia', 'Hyperlipidemia', 20, 0.9),
]

MEDICATIONS = [
    ('Metformin 500mg', 'Diabetes', 0.8),
    ('Lisinopril 10mg', 'Hypertension', 0.7),
    ('Atorvastatin 40mg', 'Hyperlipidemia', 0.7),
    ('Metoprolol 25mg', 'Heart Failure', 0.6),
    ('Furosemide 40mg', 'Heart Failure', 0.5),
    ('Amlodipine 5mg', 'Hypertension', 0.5),
    ('Omeprazole 20mg', 'GERD', 0.6),
    ('Albuterol Inhaler', 'Asthma', 0.7),
    ('Sertraline 50mg', 'Depression', 0.5),
    ('Warfarin 5mg', 'AFib', 0.4),
    ('Insulin Glargine', 'Diabetes', 0.3),
    ('Prednisone 10mg', 'COPD', 0.3),
    ('Aspirin 81mg', 'CAD', 0.6),
    ('Gabapentin 300mg', 'Pain', 0.3),
    ('Hydrochlorothiazide 25mg', 'Hypertension', 0.4),
]

ENCOUNTER_TYPES = ['inpatient', 'outpatient', 'emergency', 'ambulatory']


def generate_patients(n=5000):
    """Generate patient demographics."""
    races = ['White', 'Black', 'Hispanic', 'Asian', 'Other']
    race_weights = [0.58, 0.18, 0.13, 0.06, 0.05]
    genders = ['M', 'F']
    payers = ['Medicare', 'Medicaid', 'Private', 'Self-Pay']
    payer_weights = [0.35, 0.15, 0.40, 0.10]
    counties = ['Richmond', 'Columbia', 'Burke', 'McDuffie', 'Aiken',
                'Edgefield', 'Lincoln', 'Glascock', 'Jefferson', 'Warren']

    patients = []
    for i in range(n):
        birth_year = np.random.randint(1940, 2005)
        age = 2026 - birth_year
        # Older patients more likely to have comorbidities
        patients.append({
            'patient_id': f'P{10000 + i}',
            'birth_date': f'{birth_year}-{np.random.randint(1,13):02d}-{np.random.randint(1,29):02d}',
            'gender': np.random.choice(genders, p=[0.48, 0.52]),
            'race': np.random.choice(races, p=race_weights),
            'county': np.random.choice(counties),
            'payer': np.random.choice(payers, p=payer_weights),
            'age': age,
        })

    df = pd.DataFrame(patients)
    df.to_csv(os.path.join(DATA_DIR, 'patients.csv'), index=False)
    print(f"  patients: {len(df):,} rows")
    return df


def generate_encounters(patients_df, avg_encounters_per_patient=4):
    """Generate hospital encounters with realistic patterns."""
    encounters = []
    enc_id = 100000

    for _, pat in patients_df.iterrows():
        # Older patients have more encounters
        age_factor = max(1, pat['age'] / 40)
        n_enc = max(1, int(np.random.poisson(avg_encounters_per_patient * age_factor)))
        n_enc = min(n_enc, 20)  # cap

        for _ in range(n_enc):
            enc_type = np.random.choice(
                ENCOUNTER_TYPES,
                p=[0.20, 0.40, 0.15, 0.25]
            )

            start = datetime(2023, 1, 1) + timedelta(days=np.random.randint(0, 1000))

            if enc_type == 'inpatient':
                los = max(1, int(np.random.exponential(4.5)))  # avg 4.5 day LOS
            elif enc_type == 'emergency':
                los = max(0, int(np.random.exponential(0.5)))
            else:
                los = 0

            end = start + timedelta(days=los)

            encounters.append({
                'encounter_id': f'E{enc_id}',
                'patient_id': pat['patient_id'],
                'encounter_type': enc_type,
                'start_date': start.strftime('%Y-%m-%d'),
                'end_date': end.strftime('%Y-%m-%d'),
                'length_of_stay': los,
                'discharge_disposition': np.random.choice(
                    ['home', 'home_health', 'SNF', 'rehab', 'AMA', 'expired'],
                    p=[0.65, 0.15, 0.10, 0.05, 0.03, 0.02]
                ) if enc_type == 'inpatient' else 'home',
            })
            enc_id += 1

    df = pd.DataFrame(encounters)
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['end_date'] = pd.to_datetime(df['end_date'])
    df.to_csv(os.path.join(DATA_DIR, 'encounters.csv'), index=False)
    print(f"  encounters: {len(df):,} rows")
    return df


def generate_conditions(patients_df, encounters_df):
    """Generate diagnoses for patients, linked to encounters."""
    conditions = []
    cond_id = 200000

    for _, pat in patients_df.iterrows():
        # Number of conditions correlates with age
        n_conditions = max(1, int(np.random.poisson(max(1, pat['age'] / 20))))
        n_conditions = min(n_conditions, 8)

        weights = np.array([c[3] for c in CONDITIONS], dtype=float)
        weights /= weights.sum()

        selected = np.random.choice(len(CONDITIONS), size=n_conditions, replace=False, p=weights)

        pat_encounters = encounters_df[encounters_df['patient_id'] == pat['patient_id']]
        if len(pat_encounters) == 0:
            continue

        for idx in selected:
            code, desc, category, _, risk = CONDITIONS[idx]
            # Link to a random encounter
            enc = pat_encounters.sample(1).iloc[0]

            conditions.append({
                'condition_id': f'C{cond_id}',
                'patient_id': pat['patient_id'],
                'encounter_id': enc['encounter_id'],
                'code': code,
                'description': desc,
                'category': category,
                'onset_date': enc['start_date'],
                'readmission_risk_factor': risk,
            })
            cond_id += 1

    df = pd.DataFrame(conditions)
    df.to_csv(os.path.join(DATA_DIR, 'conditions.csv'), index=False)
    print(f"  conditions: {len(df):,} rows")
    return df


def generate_medications(patients_df, conditions_df):
    """Generate medication prescriptions based on patient conditions."""
    meds = []
    med_id = 300000

    for _, pat in patients_df.iterrows():
        pat_conditions = conditions_df[conditions_df['patient_id'] == pat['patient_id']]
        pat_categories = set(pat_conditions['category'].values)

        for med_name, med_category, prob in MEDICATIONS:
            if med_category in pat_categories and np.random.random() < prob:
                start = datetime(2023, 1, 1) + timedelta(days=np.random.randint(0, 800))
                meds.append({
                    'medication_id': f'M{med_id}',
                    'patient_id': pat['patient_id'],
                    'medication_name': med_name,
                    'category': med_category,
                    'start_date': start.strftime('%Y-%m-%d'),
                    'end_date': '' if np.random.random() > 0.3 else
                        (start + timedelta(days=np.random.randint(30, 365))).strftime('%Y-%m-%d'),
                    'is_active': 1 if np.random.random() > 0.3 else 0,
                })
                med_id += 1

    df = pd.DataFrame(meds)
    df.to_csv(os.path.join(DATA_DIR, 'medications.csv'), index=False)
    print(f"  medications: {len(df):,} rows")
    return df


def generate_observations(patients_df, encounters_df):
    """Generate vitals and lab results linked to encounters."""
    obs = []
    obs_id = 400000

    for _, enc in encounters_df.iterrows():
        pat = patients_df[patients_df['patient_id'] == enc['patient_id']].iloc[0]
        age = pat['age']

        # BMI
        bmi_base = np.random.normal(28, 6)
        obs.append({
            'observation_id': f'O{obs_id}', 'patient_id': enc['patient_id'],
            'encounter_id': enc['encounter_id'],
            'code': '39156-5', 'description': 'BMI',
            'value': round(max(16, min(55, bmi_base)), 1),
            'unit': 'kg/m2', 'date': enc['start_date'],
        })
        obs_id += 1

        # Systolic BP
        sbp_base = 120 + (age - 40) * 0.5 + np.random.normal(0, 15)
        obs.append({
            'observation_id': f'O{obs_id}', 'patient_id': enc['patient_id'],
            'encounter_id': enc['encounter_id'],
            'code': '8480-6', 'description': 'Systolic BP',
            'value': round(max(90, min(200, sbp_base))),
            'unit': 'mmHg', 'date': enc['start_date'],
        })
        obs_id += 1

        # Heart rate
        hr = np.random.normal(78, 12)
        obs.append({
            'observation_id': f'O{obs_id}', 'patient_id': enc['patient_id'],
            'encounter_id': enc['encounter_id'],
            'code': '8867-4', 'description': 'Heart Rate',
            'value': round(max(50, min(130, hr))),
            'unit': 'bpm', 'date': enc['start_date'],
        })
        obs_id += 1

        # Glucose (random subset)
        if np.random.random() < 0.4:
            glucose = np.random.normal(110, 35)
            obs.append({
                'observation_id': f'O{obs_id}', 'patient_id': enc['patient_id'],
                'encounter_id': enc['encounter_id'],
                'code': '2345-7', 'description': 'Glucose',
                'value': round(max(60, min(400, glucose))),
                'unit': 'mg/dL', 'date': enc['start_date'],
            })
            obs_id += 1

        # HbA1c (less frequent)
        if np.random.random() < 0.15:
            a1c = np.random.normal(6.5, 1.5)
            obs.append({
                'observation_id': f'O{obs_id}', 'patient_id': enc['patient_id'],
                'encounter_id': enc['encounter_id'],
                'code': '4548-4', 'description': 'HbA1c',
                'value': round(max(4.0, min(14.0, a1c)), 1),
                'unit': '%', 'date': enc['start_date'],
            })
            obs_id += 1

    df = pd.DataFrame(obs)
    df.to_csv(os.path.join(DATA_DIR, 'observations.csv'), index=False)
    print(f"  observations: {len(df):,} rows")
    return df


if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    print("Generating synthetic EHR data...")
    patients = generate_patients(5000)
    encounters = generate_encounters(patients)
    conditions = generate_conditions(patients, encounters)
    medications = generate_medications(patients, conditions)
    observations = generate_observations(patients, encounters)
    print(f"\nAll EHR data generated in {DATA_DIR}")
