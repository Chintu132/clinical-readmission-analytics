"""Run full ETL pipeline: Extract → Transform → Load."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from etl.extract import load_all
from etl.transform import (transform_patients, build_readmission_flag, build_encounter_summary,
                            build_comorbidity_count, build_medication_count, build_vitals_summary)
from etl.load import load_all as load_warehouse

def run():
    start = time.time()
    print("=" * 60)
    print("CLINICAL READMISSION ANALYTICS \u2014 ETL PIPELINE")
    print("=" * 60)

    print("\n[1/3] EXTRACT")
    tables = load_all()

    print("\n[2/3] TRANSFORM")
    patients = transform_patients(tables['patients'])
    readmissions = build_readmission_flag(tables['encounters'])
    enc_summary = build_encounter_summary(tables['encounters'], patients)
    comorbidity = build_comorbidity_count(tables['conditions'])
    med_counts = build_medication_count(tables['medications'])
    vitals = build_vitals_summary(tables['observations'])

    print("\n[3/3] LOAD")
    load_warehouse({
        'dim_patient': patients,
        'fact_readmission': readmissions,
        'patient_encounter_summary': enc_summary,
        'patient_comorbidity': comorbidity,
        'patient_medications': med_counts,
        'patient_vitals': vitals,
    })

    print(f"\nPipeline completed in {time.time() - start:.1f}s")
    print("=" * 60)

if __name__ == '__main__':
    run()
