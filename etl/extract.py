"""ETL Extract — Load raw EHR CSVs."""
import pandas as pd, os
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'synthea')
TABLES = ['patients', 'encounters', 'conditions', 'medications', 'observations']

def load_all():
    tables = {}
    for t in TABLES:
        fp = os.path.join(DATA_DIR, f'{t}.csv')
        if os.path.exists(fp):
            tables[t] = pd.read_csv(fp)
            print(f"  Loaded {t}: {len(tables[t]):,} rows")
    return tables

if __name__ == '__main__':
    load_all()
