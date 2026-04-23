"""
Cohort Analysis — Stratified Readmission Analysis
===================================================
Analyzes readmission risk across patient subgroups to identify
which populations need targeted interventions.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import pandas as pd, numpy as np, sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def load():
    db = os.path.join(os.path.dirname(__file__), '..', 'data', 'warehouse.db')
    conn = sqlite3.connect(db)
    readm = pd.read_sql("SELECT * FROM fact_readmission", conn)
    patients = pd.read_sql("SELECT * FROM dim_patient", conn)
    comorbidity = pd.read_sql("SELECT * FROM patient_comorbidity", conn)
    meds = pd.read_sql("SELECT * FROM patient_medications", conn)
    conn.close()
    return readm, patients, comorbidity, meds

def risk_stratification(readm, patients, comorbidity, meds):
    """Build risk tiers based on comorbidity burden + medication count."""
    df = readm.merge(patients[['patient_id', 'age', 'age_group', 'gender', 'payer']], on='patient_id', how='left')
    df = df.merge(comorbidity[['patient_id', 'distinct_categories', 'has_heart_failure', 'has_copd']], on='patient_id', how='left')
    df = df.merge(meds, on='patient_id', how='left')
    df['active_med_count'] = df['active_med_count'].fillna(0)
    df['distinct_categories'] = df['distinct_categories'].fillna(0)

    # Risk tiers
    df['risk_score'] = df['distinct_categories'] * 2 + df['active_med_count'] + (df['age'] > 65).astype(int) * 3
    df['risk_tier'] = pd.cut(df['risk_score'], bins=[-1, 5, 12, 100], labels=['Low', 'Medium', 'High'])

    tier_stats = (df.groupby('risk_tier', observed=True)
        .agg(patients=('patient_id', 'nunique'), discharges=('encounter_id', 'count'),
             readmitted=('readmitted_30d', 'sum'), avg_los=('length_of_stay', 'mean'))
        .reset_index())
    tier_stats['readmission_rate'] = (tier_stats['readmitted'] / tier_stats['discharges'] * 100).round(1)
    tier_stats['avg_los'] = tier_stats['avg_los'].round(1)

    return tier_stats, df

def plot_risk_tiers(tier_stats, out_dir):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    colors = {'Low': '#1a9641', 'Medium': '#fdae61', 'High': '#d7191c'}

    ax1.bar(tier_stats['risk_tier'].astype(str), tier_stats['readmission_rate'],
            color=[colors.get(t, '#999') for t in tier_stats['risk_tier']])
    ax1.set_ylabel('30-Day Readmission Rate (%)'); ax1.set_title('Readmission Rate by Risk Tier', fontweight='bold')
    for i, row in tier_stats.iterrows():
        ax1.text(i, row['readmission_rate'] + 0.3, f"n={row['discharges']:,}", ha='center', fontsize=9)
    ax1.grid(True, alpha=0.3, axis='y')

    ax2.bar(tier_stats['risk_tier'].astype(str), tier_stats['avg_los'],
            color=[colors.get(t, '#999') for t in tier_stats['risk_tier']])
    ax2.set_ylabel('Average Length of Stay (days)'); ax2.set_title('Avg LOS by Risk Tier', fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')

    plt.suptitle('Patient Risk Stratification', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    fp = os.path.join(out_dir, 'risk_stratification.png'); plt.savefig(fp, dpi=150, bbox_inches='tight'); plt.close()
    print(f"  Chart: {fp}")

def plot_readmission_heatmap(df, out_dir):
    """Heatmap: readmission rate by age group × payer."""
    pivot = df.pivot_table(index='age_group', columns='payer', values='readmitted_30d',
                            aggfunc='mean', observed=True) * 100

    fig, ax = plt.subplots(figsize=(9, 5))
    im = ax.imshow(pivot.values, cmap='YlOrRd', aspect='auto')
    ax.set_xticks(range(len(pivot.columns))); ax.set_xticklabels(pivot.columns, fontsize=10)
    ax.set_yticks(range(len(pivot.index))); ax.set_yticklabels(pivot.index, fontsize=10)
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f'{val:.0f}%', ha='center', va='center', fontsize=10,
                        color='white' if val > 15 else 'black')
    ax.set_title('30-Day Readmission Rate: Age Group × Payer', fontsize=13, fontweight='bold')
    plt.colorbar(im, label='Readmission Rate (%)'); plt.tight_layout()
    fp = os.path.join(out_dir, 'readmission_heatmap.png'); plt.savefig(fp, dpi=150); plt.close()
    print(f"  Chart: {fp}")

if __name__ == '__main__':
    print("=" * 60); print("COHORT ANALYSIS"); print("=" * 60)
    out = os.path.join(os.path.dirname(__file__), '..', 'dashboards', 'screenshots'); os.makedirs(out, exist_ok=True)
    readm, patients, comorbidity, meds = load()

    print("\nRisk Stratification:")
    tier_stats, df = risk_stratification(readm, patients, comorbidity, meds)
    print(tier_stats.to_string(index=False))
    plot_risk_tiers(tier_stats, out)
    plot_readmission_heatmap(df, out)
    print("\nDone.")
