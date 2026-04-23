# Methodology

## 30-Day Readmission Definition
A patient is considered readmitted if they have any acute encounter (inpatient or ED) within 30 calendar days of an inpatient discharge. This follows CMS Hospital Readmissions Reduction Program definitions.

## Feature Engineering
Clinical features are extracted from five EHR tables (patients, encounters, conditions, medications, observations) and joined at the patient level. Key features include age, comorbidity count (simplified Charlson proxy), medication count (polypharmacy indicator), prior ED visits, length of stay, discharge disposition, and latest vital signs.

## Model Selection
Logistic Regression is the primary model due to interpretability requirements in clinical decision support. Random Forest is trained as a comparison model. Both use balanced class weights to handle the imbalanced readmission target. Evaluation uses AUC-ROC, precision, recall, and F1 on a held-out 20% test set.

## Risk Stratification
Patients are stratified into Low/Medium/High risk tiers using a composite score: (distinct condition categories × 2) + active medication count + (age > 65 × 3). Thresholds are calibrated to produce clinically meaningful tier sizes.
