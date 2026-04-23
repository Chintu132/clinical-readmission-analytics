-- 30-day readmission rate by condition category
SELECT c.category, COUNT(*) AS discharges,
    SUM(r.readmitted_30d) AS readmitted,
    ROUND(SUM(r.readmitted_30d) * 100.0 / COUNT(*), 1) AS readmission_rate_pct
FROM fact_readmission r
LEFT JOIN (SELECT DISTINCT encounter_id, category FROM conditions) c
    ON c.encounter_id = r.encounter_id
GROUP BY c.category HAVING COUNT(*) >= 10
ORDER BY readmission_rate_pct DESC;

-- High-risk patient identification
SELECT p.patient_id, p.age, p.gender, p.payer,
    cm.distinct_categories AS comorbidities, m.active_med_count AS medications,
    es.ed_count, es.inpatient_count,
    r.readmitted_30d, r.length_of_stay
FROM fact_readmission r
JOIN dim_patient p ON p.patient_id = r.patient_id
LEFT JOIN patient_comorbidity cm ON cm.patient_id = r.patient_id
LEFT JOIN patient_medications m ON m.patient_id = r.patient_id
LEFT JOIN patient_encounter_summary es ON es.patient_id = r.patient_id
WHERE cm.distinct_categories >= 4 AND m.active_med_count >= 5
ORDER BY cm.distinct_categories DESC, m.active_med_count DESC;
