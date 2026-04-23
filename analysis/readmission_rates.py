"""
30-Day Readmission Rate Analysis
==================================
Calculates readmission rates by condition, age group, payer, and discharge disposition.
These are the same metrics CMS tracks for the Hospital Readmissions Reduction Program.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import pandas as pd, numpy as np, sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def load():
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'data', 'warehouse.db'))
    readm = pd.read_sql("SELECT * FROM fact_readmission", conn)
    patients = pd.read_sql("SELECT * FROM dim_patient", conn)
    conn.close()
    # Also load conditions from raw
    cond = pd.read_csv(os.path.join(os.path.dirname(__file__), '..', 'data', 'synthea', 'conditions.csv'))
    return readm, patients, cond

def readmission_by_condition(readm, cond):
    """30-day readmission rate by primary condition category."""
    # Get primary condition per encounter (first listed)
    primary = cond.drop_duplicates(subset='encounter_id', keep='first')[['encounter_id', 'category']]
    merged = readm.merge(primary, on='encounter_id', how='left')
    merged['category'] = merged['category'].fillna('Unknown')

    rates = (merged.groupby('category')
        .agg(discharges=('encounter_id', 'count'), readmitted=('readmitted_30d', 'sum'))
        .reset_index())
    rates['readmission_rate'] = (rates['readmitted'] / rates['discharges'] * 100).round(1)
    rates = rates.sort_values('readmission_rate', ascending=False)

    return rates[rates['discharges'] >= 10]

def readmission_by_demographics(readm, patients):
    """Readmission by age group, gender, payer."""
    merged = readm.merge(patients[['patient_id', 'age_group', 'gender', 'payer', 'race']], on='patient_id', how='left')

    results = {}
    for col in ['age_group', 'gender', 'payer', 'race']:
        r = (merged.groupby(col)
            .agg(discharges=('encounter_id', 'count'), readmitted=('readmitted_30d', 'sum'))
            .reset_index())
        r['readmission_rate'] = (r['readmitted'] / r['discharges'] * 100).round(1)
        results[col] = r

    return results

def plot_by_condition(rates, out_dir):
    fig, ax = plt.subplots(figsize=(10, 7))
    top = rates.head(12).sort_values('readmission_rate')
    colors = ['#d7191c' if r > 20 else '#fdae61' if r > 15 else '#1a9641' for r in top['readmission_rate']]
    bars = ax.barh(top['category'], top['readmission_rate'], color=colors)
    for bar, n in zip(bars, top['discharges']):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2, f'n={n:,}', va='center', fontsize=8)
    ax.axvline(x=15, color='red', linestyle='--', alpha=0.4, label='CMS benchmark ~15%')
    ax.set_xlabel('30-Day Readmission Rate (%)', fontsize=11)
    ax.set_title('30-Day Readmission Rate by Condition', fontsize=14, fontweight='bold')
    ax.legend(); ax.grid(True, alpha=0.3, axis='x'); plt.tight_layout()
    fp = os.path.join(out_dir, 'readmission_by_condition.png')
    plt.savefig(fp, dpi=150); plt.close()
    print(f"  Chart: {fp}")

def plot_by_demographics(demo_results, out_dir):
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    for ax, (col, df) in zip(axes, [('age_group', demo_results.get('age_group')),
                                      ('payer', demo_results.get('payer')),
                                      ('gender', demo_results.get('gender'))]):
        if df is None: continue
        s = df.sort_values('readmission_rate')
        ax.barh(s[col].astype(str), s['readmission_rate'], color='#0066CC')
        ax.set_xlabel('Readmission Rate (%)')
        ax.set_title(f'By {col.replace("_"," ").title()}', fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
    plt.suptitle('30-Day Readmission by Demographics', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    fp = os.path.join(out_dir, 'readmission_by_demographics.png')
    plt.savefig(fp, dpi=150, bbox_inches='tight'); plt.close()
    print(f"  Chart: {fp}")

if __name__ == '__main__':
    print("=" * 60); print("30-DAY READMISSION RATE ANALYSIS"); print("=" * 60)
    out = os.path.join(os.path.dirname(__file__), '..', 'dashboards', 'screenshots'); os.makedirs(out, exist_ok=True)
    readm, patients, cond = load()
    overall = readm['readmitted_30d'].mean() * 100
    print(f"\nOverall 30-day readmission rate: {overall:.1f}%")
    print(f"Total inpatient discharges: {len(readm):,}")
    print(f"Readmitted within 30 days: {readm['readmitted_30d'].sum():,}")

    print("\nBy Condition:")
    rates = readmission_by_condition(readm, cond)
    print(rates.to_string(index=False))
    plot_by_condition(rates, out)

    print("\nBy Demographics:")
    demo = readmission_by_demographics(readm, patients)
    for k, v in demo.items():
        print(f"\n  {k}:"); print(v.to_string(index=False))
    plot_by_demographics(demo, out)
    print("\nDone.")
