"""
Readmission Prediction Model
==============================
Builds clinical features from EHR data and trains Logistic Regression + Random Forest
to predict 30-day hospital readmission. Designed for interpretability — clinical
decision support requires understanding WHY a patient is high-risk, not just that they are.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import pandas as pd, numpy as np, sqlite3, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score, roc_curve, confusion_matrix
from sklearn.preprocessing import LabelEncoder

def load_data():
    db = os.path.join(os.path.dirname(__file__), '..', 'data', 'warehouse.db')
    conn = sqlite3.connect(db)
    readm = pd.read_sql("SELECT * FROM fact_readmission", conn)
    patients = pd.read_sql("SELECT * FROM dim_patient", conn)
    enc_sum = pd.read_sql("SELECT * FROM patient_encounter_summary", conn)
    comorbidity = pd.read_sql("SELECT * FROM patient_comorbidity", conn)
    meds = pd.read_sql("SELECT * FROM patient_medications", conn)
    vitals = pd.read_sql("SELECT * FROM patient_vitals", conn)
    conn.close()
    return readm, patients, enc_sum, comorbidity, meds, vitals

def build_features(readm, patients, enc_sum, comorbidity, meds, vitals):
    """
    Build the ML feature matrix from multiple EHR tables.
    Features mirror what a real clinical analytics team would extract.
    """
    df = readm.copy()

    # Patient demographics
    pat_feats = patients[['patient_id', 'age', 'gender', 'payer']].copy()
    pat_feats['is_male'] = (pat_feats['gender'] == 'M').astype(int)
    pat_feats['is_medicare'] = (pat_feats['payer'] == 'Medicare').astype(int)
    pat_feats['is_medicaid'] = (pat_feats['payer'] == 'Medicaid').astype(int)
    df = df.merge(pat_feats[['patient_id', 'age', 'is_male', 'is_medicare', 'is_medicaid']], on='patient_id', how='left')

    # Encounter history
    df = df.merge(enc_sum[['patient_id', 'total_encounters', 'inpatient_count', 'ed_count', 'avg_los']], on='patient_id', how='left')

    # Comorbidities
    df = df.merge(comorbidity[['patient_id', 'distinct_categories', 'has_diabetes', 'has_heart_failure',
                                'has_copd', 'has_ckd', 'has_depression', 'max_risk_factor']], on='patient_id', how='left')

    # Medication count
    df = df.merge(meds, on='patient_id', how='left')
    df['active_med_count'] = df['active_med_count'].fillna(0)

    # Vitals
    df = df.merge(vitals, on='patient_id', how='left')

    # Discharge features
    df['discharged_to_snf'] = (df['discharge_disposition'] == 'SNF').astype(int)
    df['discharged_ama'] = (df['discharge_disposition'] == 'AMA').astype(int)

    # Polypharmacy flag (5+ meds)
    df['polypharmacy'] = (df['active_med_count'] >= 5).astype(int)

    # High-risk vital flags
    df['high_bmi'] = (df.get('latest_bmi', pd.Series(dtype=float)) > 35).astype(int)
    df['high_sbp'] = (df.get('latest_sbp', pd.Series(dtype=float)) > 140).astype(int)

    feature_cols = [
        'age', 'is_male', 'is_medicare', 'is_medicaid',
        'length_of_stay', 'total_encounters', 'inpatient_count', 'ed_count', 'avg_los',
        'distinct_categories', 'has_diabetes', 'has_heart_failure', 'has_copd', 'has_ckd', 'has_depression',
        'active_med_count', 'polypharmacy',
        'discharged_to_snf', 'discharged_ama',
        'max_risk_factor',
    ]

    # Add vital columns if they exist
    for vc in ['latest_bmi', 'latest_sbp', 'latest_hr', 'latest_glucose']:
        if vc in df.columns:
            feature_cols.append(vc)

    X = df[feature_cols].copy().fillna(0)
    y = df['readmitted_30d'].copy()

    return X, y, feature_cols

def train_models(X, y, feature_cols):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Logistic Regression
    lr = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
    lr.fit(X_train, y_train)
    lr_proba = lr.predict_proba(X_test)[:, 1]
    lr_auc = roc_auc_score(y_test, lr_proba)

    # Random Forest
    rf = RandomForestClassifier(n_estimators=100, max_depth=8, class_weight='balanced', random_state=42)
    rf.fit(X_train, y_train)
    rf_proba = rf.predict_proba(X_test)[:, 1]
    rf_auc = roc_auc_score(y_test, rf_proba)

    print(f"\n  Logistic Regression AUC: {lr_auc:.3f}")
    print(f"  Random Forest AUC:      {rf_auc:.3f}")

    # Classification report for better model
    best_name = "Random Forest" if rf_auc >= lr_auc else "Logistic Regression"
    best_model = rf if rf_auc >= lr_auc else lr
    best_proba = rf_proba if rf_auc >= lr_auc else lr_proba
    best_auc = max(lr_auc, rf_auc)

    print(f"\n  Best model: {best_name}")
    print(classification_report(y_test, (best_proba > 0.5).astype(int), target_names=['Not Readmitted', 'Readmitted']))

    return lr, rf, X_test, y_test, lr_proba, rf_proba, lr_auc, rf_auc, feature_cols

def plot_roc_comparison(y_test, lr_proba, rf_proba, lr_auc, rf_auc, out_dir):
    fig, ax = plt.subplots(figsize=(8, 6))
    for proba, auc, name, color in [(lr_proba, lr_auc, 'Logistic Regression', '#003366'),
                                      (rf_proba, rf_auc, 'Random Forest', '#CC3333')]:
        fpr, tpr, _ = roc_curve(y_test, proba)
        ax.plot(fpr, tpr, color=color, linewidth=2, label=f'{name} (AUC={auc:.3f})')
    ax.plot([0, 1], [0, 1], 'k--', alpha=0.3, label='Random (AUC=0.500)')
    ax.set_xlabel('False Positive Rate'); ax.set_ylabel('True Positive Rate')
    ax.set_title('Readmission Prediction \u2014 ROC Comparison', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10); ax.grid(True, alpha=0.3); plt.tight_layout()
    fp = os.path.join(out_dir, 'model_roc_comparison.png'); plt.savefig(fp, dpi=150); plt.close()
    print(f"  Chart: {fp}")

def plot_feature_importance(rf_model, feature_cols, out_dir):
    fig, ax = plt.subplots(figsize=(9, 7))
    imp = pd.Series(rf_model.feature_importances_, index=feature_cols).sort_values()
    imp.tail(15).plot(kind='barh', ax=ax, color='#0066CC')
    ax.set_xlabel('Feature Importance (Gini)')
    ax.set_title('Top 15 Readmission Risk Factors \u2014 Random Forest', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x'); plt.tight_layout()
    fp = os.path.join(out_dir, 'feature_importance_rf.png'); plt.savefig(fp, dpi=150); plt.close()
    print(f"  Chart: {fp}")

def plot_lr_coefficients(lr_model, feature_cols, out_dir):
    fig, ax = plt.subplots(figsize=(9, 7))
    coefs = pd.Series(lr_model.coef_[0], index=feature_cols).sort_values()
    colors = ['#d7191c' if c > 0 else '#1a9641' for c in coefs]
    coefs.plot(kind='barh', ax=ax, color=colors)
    ax.set_xlabel('Coefficient (+ = increases readmission risk)')
    ax.set_title('Readmission Risk Factors \u2014 Logistic Regression', fontsize=14, fontweight='bold')
    ax.axvline(x=0, color='black', linewidth=0.5); ax.grid(True, alpha=0.3, axis='x'); plt.tight_layout()
    fp = os.path.join(out_dir, 'lr_coefficients.png'); plt.savefig(fp, dpi=150); plt.close()
    print(f"  Chart: {fp}")

if __name__ == '__main__':
    print("=" * 60); print("READMISSION PREDICTION MODEL"); print("=" * 60)
    out = os.path.join(os.path.dirname(__file__), '..', 'dashboards', 'screenshots'); os.makedirs(out, exist_ok=True)

    readm, patients, enc_sum, comorbidity, meds, vitals = load_data()
    print(f"\nDischarges: {len(readm):,}, Patients: {len(patients):,}")

    print("\nBuilding feature matrix...")
    X, y, feature_cols = build_features(readm, patients, enc_sum, comorbidity, meds, vitals)
    print(f"Features: {X.shape[1]}, Samples: {X.shape[0]:,}")
    print(f"Readmission rate: {y.mean()*100:.1f}%")

    print("\nTraining models...")
    lr, rf, X_test, y_test, lr_p, rf_p, lr_auc, rf_auc, fcols = train_models(X, y, feature_cols)

    print("\nGenerating charts...")
    plot_roc_comparison(y_test, lr_p, rf_p, lr_auc, rf_auc, out)
    plot_feature_importance(rf, feature_cols, out)
    plot_lr_coefficients(lr, feature_cols, out)

    metrics = {'lr_auc': round(lr_auc, 3), 'rf_auc': round(rf_auc, 3), 'features': feature_cols,
               'samples': int(X.shape[0]), 'readmission_rate': round(y.mean()*100, 1)}
    mpath = os.path.join(os.path.dirname(__file__), '..', 'docs', 'model_metrics.json')
    with open(mpath, 'w') as f: json.dump(metrics, f, indent=2)
    print(f"\nMetrics saved: {mpath}")
    print("\nDone.")
